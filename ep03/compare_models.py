"""EP03: which embedding model finds the right page most often?

Runs every question in data/acme/eval/handbook_retrieval.jsonl against the
handbook with several Ollama embedding models and reports:
  hit@1  - the top chunk is from the correct page
  hit@4  - a correct page is somewhere in the top 4 (what the LLM sees)
  MRR    - mean reciprocal rank of the first correct chunk (1.0 = always first)

    python ep03/compare_models.py
"""
import json
import time

import numpy as np
import ollama

from pdf import chunk, load_pdf

PDF = "data/acme/pdfs/handbook.pdf"
EVAL = "data/acme/eval/handbook_retrieval.jsonl"

# (model, document prefix, query prefix): some models are trained with task prefixes
MODELS = [
    ("all-minilm", "", ""),
    ("nomic-embed-text", "", ""),
    ("nomic-embed-text", "search_document: ", "search_query: "),
    ("mxbai-embed-large", "", ""),
    ("mxbai-embed-large", "", "Represent this sentence for searching relevant passages: "),
    ("bge-m3", "", ""),
]


def embed(model, texts):
    v = np.array(ollama.embed(model=model, input=texts)["embeddings"])
    return v / np.linalg.norm(v, axis=1, keepdims=True)  # normalise: dot product == cosine


def evaluate(model, doc_prefix, query_prefix, chunks, questions):
    embed(model, ["warm-up"])  # load the model first so timing only measures embedding
    t0 = time.time()
    docs = embed(model, [doc_prefix + c["text"] for c in chunks])
    index_s = time.time() - t0
    qv = embed(model, [query_prefix + q["question"] for q in questions])
    hit1 = hit4 = rr = 0.0
    for q, v in zip(questions, qv):
        ranked = np.argsort(docs @ v)[::-1]
        ranks = [r for r, i in enumerate(ranked) if chunks[i]["page"] in q["pages"]]
        first = ranks[0] if ranks else None
        hit1 += first == 0
        hit4 += first is not None and first < 4
        rr += 1 / (first + 1) if first is not None else 0
    n = len(questions)
    return {"model": model, "prefix": bool(doc_prefix or query_prefix), "dims": docs.shape[1],
            "hit1": hit1 / n, "hit4": hit4 / n, "mrr": rr / n, "index_seconds": round(index_s, 1)}


if __name__ == "__main__":
    chunks = chunk(load_pdf(PDF))
    questions = [json.loads(line) for line in open(EVAL)]
    print(f"{len(chunks)} chunks, {len(questions)} questions\n")
    print(f"{'model':<22}{'prefix':<8}{'dims':>6}{'hit@1':>8}{'hit@4':>8}{'MRR':>7}{'index s':>9}")
    results = []
    for m, dp, qp in MODELS:
        r = evaluate(m, dp, qp, chunks, questions)
        results.append(r)
        print(f"{r['model']:<22}{'yes' if r['prefix'] else 'no':<8}{r['dims']:>6}"
              f"{r['hit1']:>8.0%}{r['hit4']:>8.0%}{r['mrr']:>7.2f}{r['index_seconds']:>9}")
    json.dump(results, open("ep03/model_comparison.json", "w"), indent=1)
