"""EP03: answer questions from the Qdrant index (no re-embedding of documents).

    python ep03/ask.py "What's the refund policy for enterprise customers?"
    python ep03/ask.py            # interactive, type 'exit' to quit
"""
import sys

from llm import generate
from store import COLLECTION, check_meta, embed, open_db

check_meta()
db = open_db()


def retrieve(question, k=4):
    hits = db.query_points(COLLECTION, query=embed([question])[0], limit=k).points
    return [(h.payload, h.score) for h in hits]


def answer(question, hits):
    context = "\n\n".join(f"[{p['source']} p{p['page']}] {p['text']}" for p, _ in hits)
    return generate(
        "You are Acme Robotics' internal assistant. Answer ONLY from the context below.\n"
        "If the answer is not in the context, say \"I don't know\". Cite sources like [handbook.pdf p3].\n\n"
        f"Context:\n{context}\n\nQuestion: {question}")


if __name__ == "__main__":
    for q in sys.argv[1:] or iter(lambda: input("\n> "), "exit"):
        hits = retrieve(q)
        print(answer(q, hits))
        print("sources:", ", ".join(f"{p['source']} p{p['page']} ({s:.2f})" for p, s in hits))
    db.close()
