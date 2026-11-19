"""EP04: naive chunks (EP02/EP03) vs structured chunks (EP04), same embedding model.

    python ep04/compare_chunking.py
"""
import json
from pathlib import Path

import numpy as np
import ollama
from pypdf import PdfReader

from chunker import chunk_blocks
from pdf_parser import parse_pdf
from store import EMBED_MODEL

PDFS = sorted(Path("data/acme/pdfs").glob("*.pdf"))
EVAL = [json.loads(line) for line in open("data/acme/eval/pdf_retrieval.jsonl")]


def naive_chunks(path, size=800, overlap=150):
    out = []
    for page_no, page in enumerate(PdfReader(path).pages, start=1):
        text = page.extract_text() or ""
        for start in range(0, len(text), size - overlap):
            if piece := text[start:start + size].strip():
                out.append({"source": path.name, "page": page_no, "text": piece})
    return out


def embed(texts):
    v = np.array(ollama.embed(model=EMBED_MODEL, input=texts)["embeddings"])
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def evaluate(chunks):
    docs, qv = embed([c["text"] for c in chunks]), embed([q["question"] for q in EVAL])
    per_source = {}
    for q, v in zip(EVAL, qv):
        ranked = np.argsort(docs @ v)[::-1]
        ok = [r for r, i in enumerate(ranked) if chunks[i]["source"] == q["source"] and chunks[i]["page"] in q["pages"]]
        s = per_source.setdefault(q["source"], {"n": 0, "hit1": 0, "hit4": 0})
        s["n"] += 1
        s["hit1"] += bool(ok) and ok[0] == 0
        s["hit4"] += bool(ok) and ok[0] < 4
    return per_source


if __name__ == "__main__":
    results = {}
    for name, make in [("naive", naive_chunks), ("structured", lambda p: chunk_blocks(parse_pdf(p), p.name))]:
        chunks = [c for p in PDFS for c in make(p)]
        results[name] = {"chunks": len(chunks), "per_source": evaluate(chunks)}
    print(f"{'source':<22}{'questions':>10}{'naive hit@1':>14}{'struct hit@1':>14}{'naive hit@4':>14}{'struct hit@4':>14}")
    for src in results["naive"]["per_source"]:
        n, s = results["naive"]["per_source"][src], results["structured"]["per_source"][src]
        print(f"{src:<22}{n['n']:>10}{n['hit1'] / n['n']:>14.0%}{s['hit1'] / s['n']:>14.0%}"
              f"{n['hit4'] / n['n']:>14.0%}{s['hit4'] / s['n']:>14.0%}")
    tot = lambda r, k: sum(v[k] for v in r["per_source"].values()) / len(EVAL)
    print(f"{'ALL':<22}{len(EVAL):>10}{tot(results['naive'], 'hit1'):>14.0%}{tot(results['structured'], 'hit1'):>14.0%}"
          f"{tot(results['naive'], 'hit4'):>14.0%}{tot(results['structured'], 'hit4'):>14.0%}")
    json.dump(results, open("ep04/chunking_comparison.json", "w"), indent=1)
