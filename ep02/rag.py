"""EP02: your first RAG in under 50 lines. Usage:
    python ep02/rag.py data/acme/pdfs/handbook.pdf               # interactive
    python ep02/rag.py data/acme/pdfs/handbook.pdf "question"    # one question
"""
import sys
import numpy as np
import ollama
from pypdf import PdfReader
from llm import generate  # Ollama, OpenAI or Claude, picked by LLM_PROVIDER

def load_pdf(path):  # -> [(page_number, text), ...]
    return [(i + 1, p.extract_text() or "") for i, p in enumerate(PdfReader(path).pages)]

def chunk(pages, size=800, overlap=150):
    chunks = []
    for page, text in pages:
        for start in range(0, len(text), size - overlap):
            if piece := text[start:start + size].strip():
                chunks.append({"page": page, "text": piece})
    return chunks

def embed(texts):
    return np.array(ollama.embed(model="nomic-embed-text", input=texts)["embeddings"])

def retrieve(question, chunks, vectors, k=4):
    q = embed([question])[0]
    scores = vectors @ q / (np.linalg.norm(vectors, axis=1) * np.linalg.norm(q))
    return [(chunks[i], scores[i]) for i in np.argsort(scores)[::-1][:k]]

def answer(question, hits):
    context = "\n\n".join(f"[page {c['page']}] {c['text']}" for c, _ in hits)
    return generate(
        "You are Acme Robotics' internal assistant. Answer ONLY from the context below.\n"
        "If the answer is not in the context, say \"I don't know\". Cite pages like [page 3].\n\n"
        f"Context:\n{context}\n\nQuestion: {question}")

if __name__ == "__main__":
    chunks = chunk(load_pdf(sys.argv[1]))
    vectors = embed([c["text"] for c in chunks])
    print(f"Indexed {len(chunks)} chunks.")
    questions = sys.argv[2:] or iter(lambda: input("\n> "), "exit")
    for q in questions:
        hits = retrieve(q, chunks, vectors)
        print(answer(q, hits))
        print("sources:", ", ".join(f"p{c['page']} ({s:.2f})" for c, s in hits))
