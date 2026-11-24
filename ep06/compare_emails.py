"""EP06: naive email indexing vs clean per-message chunks.

naive = the whole email text (quotes, signatures, disclaimers, hidden HTML) in 800-char windows (EP02 style)
clean = one chunk per message: quotes, signatures and hidden HTML removed, header with sender + date
thread = one chunk per thread: the clean messages in order, each labelled with sender + date

Retrieval is scored two ways:
  message level - the top chunk comes from the email that actually stated the fact (naive/clean only)
  thread level  - the top chunk comes from the right conversation

    python ep06/compare_emails.py
"""
import json
import re
from collections import Counter
from email import policy
from email.parser import BytesParser
from pathlib import Path

import numpy as np
import ollama
from bs4 import BeautifulSoup

from email_parser import build_threads, parse_eml
from store import EMBED_MODEL

FOLDER = Path("data/acme/emails")
EVAL = [json.loads(line) for line in open("data/acme/eval/email_retrieval.jsonl")]


def naive_chunks():
    out = []
    for p in sorted(FOLDER.glob("*.eml")):
        msg = BytesParser(policy=policy.default).parse(open(p, "rb"))
        part = msg.get_body(preferencelist=("plain", "html"))
        text = part.get_content() if part else ""
        if part is not None and part.get_content_subtype() == "html":
            text = BeautifulSoup(text, "html.parser").get_text("\n")   # everything, hidden or not
        text = f"Subject: {msg['Subject']}\nFrom: {msg['From']}\n\n{text}"
        for start in range(0, len(text), 650):
            if piece := text[start:start + 800].strip():
                out.append({"source": p.name, "text": piece})
    return out


def clean_chunks():
    msgs = [parse_eml(p) for p in sorted(FOLDER.glob("*.eml"))]
    build_threads(msgs)
    return [{"source": Path(m["file"]).name,
             "text": f"[email · thread: {m['thread_subject']} · from {m['from_name']} · {m['date']:%Y-%m-%d}]\n{m['body']}",
             "msg": m}
            for m in msgs]


def thread_chunks(max_chars=2400):
    msgs = [parse_eml(p) for p in sorted(FOLDER.glob("*.eml"))]
    out = []
    for thread in build_threads(msgs):
        parts = [f"--- {m['from_name']} · {m['date']:%Y-%m-%d}\n{m['body']}" for m in thread]
        cur, files = f"[email thread: {thread[0]['thread_subject']}]", []
        for m, part in zip(thread, parts):
            if len(cur) + len(part) > max_chars and files:
                out.append({"source": files, "text": cur})
                cur, files = f"[email thread: {thread[0]['thread_subject']} (cont.)]", []
            cur += "\n" + part
            files.append(Path(m["file"]).name)
        out.append({"source": files, "text": cur})
    return out


def thread_of(name):
    m = re.search(r"_(t\d+)m\d+\.", name)
    return m.group(1) if m else name


def embed(texts):
    v = np.array(ollama.embed(model=EMBED_MODEL, input=texts)["embeddings"])
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def stats(chunks):
    sentences = Counter()
    for c in chunks:
        for s in set(re.split(r"(?<=[.!?])\s+", " ".join(c["text"].replace(">", " ").split()))):
            if len(s) > 40:
                sentences[s] += 1
    total = sum(sentences.values())
    repeated = sum(n for n in sentences.values() if n > 1)
    return {"chunks": len(chunks), "chars": sum(len(c["text"]) for c in chunks),
            "repeated_sentence_share": repeated / total if total else 0}


def evaluate(chunks):
    docs, qv = embed([c["text"] for c in chunks]), embed([q["question"] for q in EVAL])
    res = {"msg_hit1": 0, "thread_hit1": 0, "thread_hit4": 0, "misses": []}
    for q, v in zip(EVAL, qv):
        ranked = [chunks[i]["source"] for i in np.argsort(docs @ v)[::-1]]
        files = lambda s: s if isinstance(s, list) else [s]
        want_t = {m[:3] for m in q["messages"]}
        res["msg_hit1"] += any(f"_{m}." in f for f in files(ranked[0]) for m in q["messages"]) \
            and not isinstance(ranked[0], list)
        tr = [r for r, s in enumerate(ranked) if any(thread_of(f) in want_t for f in files(s))]
        res["thread_hit1"] += bool(tr) and tr[0] == 0
        res["thread_hit4"] += bool(tr) and tr[0] < 4
        if not (tr and tr[0] == 0):
            res["misses"].append({"question": q["question"], "expected": q["messages"], "got": ranked[0]})
    n = len(EVAL)
    return {k: (v / n if k != "misses" else v) for k, v in res.items()}


if __name__ == "__main__":
    out = {}
    for name, make in [("naive", naive_chunks), ("clean", clean_chunks), ("thread", thread_chunks)]:
        chunks = make()
        out[name] = {**stats(chunks), **evaluate(chunks)}
        r = out[name]
        msg = f"{r['msg_hit1']:>6.0%}" if name != "thread" else "     -"
        print(f"{name:<7}{r['chunks']:>4} chunks {r['chars']:>7} chars  repeated sentences {r['repeated_sentence_share']:>4.0%}"
              f"   message hit@1 {msg}   thread hit@1 {r['thread_hit1']:>4.0%}   thread hit@4 {r['thread_hit4']:>4.0%}")
    json.dump(out, open("ep06/email_comparison.json", "w"), indent=1)
