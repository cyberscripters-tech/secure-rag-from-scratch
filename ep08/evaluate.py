"""EP08: one evaluation across every source, against the live Qdrant index.

Uses all test sets so far (PDF pages, email threads, Slack conversations) and reports
hit@1 / hit@4 per source type. Run after ingest.py.

    python ep08/evaluate.py
"""
import json
import re
from collections import defaultdict

from qdrant_client import models

from store import COLLECTION, embed, open_db

# evaluate as a normal employee: private channels must not show up (they did before this filter!)
PUBLIC = models.Filter(must=[models.FieldCondition(key="visibility", match=models.MatchValue(value="public"))])

SETS = {
    "pdf": "data/acme/eval/pdf_retrieval.jsonl",
    "email": "data/acme/eval/email_retrieval.jsonl",
    "slack": "data/acme/eval/slack_retrieval.jsonl",
}


def is_hit(kind, q, p):
    if kind == "pdf":
        return p.get("source") == q["source"] and p.get("page") in q["pages"]
    if kind == "email":
        m = re.search(r"_(t\d+)m\d+\.eml", p.get("source") or "")
        return p.get("doc_type") == "email" and m is not None and m.group(1) in {x[:3] for x in q["messages"]}
    return p.get("conv_key") == f"{q['channel']}:{q['thread_ts']}"


def main():
    db = open_db()
    results = defaultdict(lambda: {"n": 0, "hit1": 0, "hit4": 0})
    for kind, path in SETS.items():
        questions = [json.loads(line) for line in open(path)]
        vectors = embed([q["question"] for q in questions])
        for q, v in zip(questions, vectors):
            hits = [h.payload for h in db.query_points(COLLECTION, query=v, limit=4, query_filter=PUBLIC).points]
            ranks = [i for i, p in enumerate(hits) if is_hit(kind, q, p)]
            r = results[kind]
            r["n"] += 1
            r["hit1"] += bool(ranks) and ranks[0] == 0
            r["hit4"] += bool(ranks)
    db.close()
    total = {k: sum(r[k] for r in results.values()) for k in ("n", "hit1", "hit4")}
    for kind, r in list(results.items()) + [("ALL", total)]:
        print(f"{kind:<6}{r['n']:>4} questions   hit@1 {r['hit1'] / r['n']:>5.0%}   hit@4 {r['hit4'] / r['n']:>5.0%}")
    json.dump({k: dict(v) for k, v in results.items()}, open("ep08/evaluation.json", "w"), indent=1)


if __name__ == "__main__":
    main()
