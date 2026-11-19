"""EP04: does better chunking change the ANSWERS? Same question, same model, both chunkings.

For the refund question we count answers that wrongly attach the Business plan's
90-day rule to Enterprise customers. (We also read every answer by hand: the check
below matched the manual review on our runs.)

    python ep04/answer_check.py [runs]
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

from compare_chunking import PDFS, embed, naive_chunks
from chunker import chunk_blocks
from llm import generate
from pdf_parser import parse_pdf

RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
PROMPT = ("You are Acme Robotics' internal assistant. Answer ONLY from the context below.\n"
          "If the answer is not in the context, say \"I don't know\". Cite sources like [handbook.pdf p3].\n\n"
          "Context:\n{context}\n\nQuestion: {question}")
REFUND = "What's the refund policy for enterprise customers?"
OTHERS = ["How fast can the last wrist joint of the AX-200 rotate?",
          "When is payment due for invoice INV-2026-0418, and how much is due?"]


def wrong_refund(answer):
    """A sentence that mentions the 90-day rule is wrong if it ties it to Enterprise or never says Business."""
    return any("90" in s and ("Enterprise" in s or "Business" not in s)
               for s in re.split(r"(?<=[.!?])\s+|\n", answer))


def top4(chunks, docs, question):
    q = embed([question])[0]
    return [chunks[i] for i in np.argsort(docs @ q)[::-1][:4]]


def ask(chunks, docs, question):
    ctx = "\n\n".join(f"(source: {c['source']} p{c['page']})\n{c['text']}" for c in top4(chunks, docs, question))
    return generate(PROMPT.format(context=ctx, question=question))


if __name__ == "__main__":
    out = {}
    for name, make in [("naive", naive_chunks), ("structured", lambda p: chunk_blocks(parse_pdf(p), p.name))]:
        chunks = [c for p in PDFS for c in make(p)]
        docs = embed([c["text"] for c in chunks])
        refunds = [ask(chunks, docs, REFUND) for _ in range(RUNS)]
        wrong = [a for a in refunds if wrong_refund(a)]
        out[name] = {"refund_answers": refunds, "refund_wrong": len(wrong),
                     "others": {q: ask(chunks, docs, q) for q in OTHERS}}
        print(f"{name:<11} refund answers that apply the 90-day Business rule to Enterprise: {len(wrong)}/{RUNS}", flush=True)
    json.dump(out, open("ep04/answer_check.json", "w"), indent=1)
