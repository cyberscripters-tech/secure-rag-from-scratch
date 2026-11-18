"""EP01 sneak peek: the core of RAG in ~20 lines (as shown in the video).

`load_and_chunk` here is a deliberately naive placeholder. We build a proper
loader + chunker for PDFs in episode 4.

Run:  python ep01/rag_preview.py path/to/some.pdf
Needs: pip install ollama numpy pypdf
       ollama pull nomic-embed-text && ollama pull llama3.2
"""
import sys

import numpy as np
import ollama
from pypdf import PdfReader


def load_and_chunk(path, size=800):
    text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return [text[i:i + size] for i in range(0, len(text), size)]


chunks = load_and_chunk(sys.argv[1] if len(sys.argv) > 1 else "handbook.pdf")


def embed(texts):
    r = ollama.embed(model="nomic-embed-text", input=texts)
    return np.array(r["embeddings"])


doc_vecs = embed(chunks)


def ask(question, k=3):
    q = embed([question])[0]
    scores = doc_vecs @ q / (np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(q))
    top = [chunks[i] for i in np.argsort(scores)[::-1][:k]]
    context = "\n\n".join(top)
    prompt = "Answer only from the context. If it isn't there, say you don't know.\n\n"
    prompt += f"Context:\n{context}\n\nQuestion: {question}"
    r = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
    return r["message"]["content"]


print(ask("What's the refund policy for enterprise customers?"))
