"""EP07: one chunk per raw Slack message vs conversation chunks.

naive = each message's raw text on its own (mentions stay <@U01MAYA>, no channel, no author)
clean = threads + time windows, names resolved, header with channel and who started it

A hit = the top chunk belongs to the expected conversation (thread or message).
Public channels only (the private #hr channel is tested separately with permissions).

    python ep07/compare_slack.py
"""
import json

import numpy as np
import ollama

from slack_parser import conversation_chunks, load_messages, load_workspace
from store import EMBED_MODEL

ROOT = "data/acme/slack"
EVAL = [json.loads(line) for line in open("data/acme/eval/slack_retrieval.jsonl")]


def embed(texts):
    v = np.array(ollama.embed(model=EMBED_MODEL, input=texts)["embeddings"])
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def conv_of(m):
    return m.get("thread_ts") or m["ts"]


def main():
    users, channels = load_workspace(ROOT)
    msgs = [m for m in load_messages(ROOT) if not channels[m["channel"]]["private"]]
    variants = {
        "naive": [{"text": m["text"], "convs": {(m["channel"], conv_of(m))}} for m in msgs],
        "clean": [{"text": c["text"], "convs": {(c["channel"], conv_of(m)) for m in msgs if m["ts"] in c["ts"]}}
                  for c in conversation_chunks(msgs, users, channels)],
    }
    out = {}
    for name, chunks in variants.items():
        docs, qv = embed([c["text"] for c in chunks]), embed([q["question"] for q in EVAL])
        hit1 = hit4 = 0
        misses = []
        for q, v in zip(EVAL, qv):
            order = np.argsort(docs @ v)[::-1]
            ok = [r for r, i in enumerate(order) if (q["channel"], q["thread_ts"]) in chunks[i]["convs"]]
            hit1 += bool(ok) and ok[0] == 0
            hit4 += bool(ok) and ok[0] < 4
            if not (ok and ok[0] == 0):
                misses.append({"question": q["question"], "top": chunks[order[0]]["text"][:120]})
        out[name] = {"chunks": len(chunks), "hit1": hit1 / len(EVAL), "hit4": hit4 / len(EVAL), "misses": misses}
        print(f"{name:<6}{len(chunks):>4} chunks   hit@1 {hit1 / len(EVAL):>4.0%}   hit@4 {hit4 / len(EVAL):>4.0%}")
    json.dump(out, open("ep07/slack_comparison.json", "w"), indent=1)


if __name__ == "__main__":
    main()
