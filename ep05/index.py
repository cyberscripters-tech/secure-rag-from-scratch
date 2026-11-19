"""EP05: index PDFs and Word documents, with document metadata in every chunk.

    python ep05/index.py data/acme/pdfs data/acme/docs
"""
import sys
import time
import uuid
from pathlib import Path

from qdrant_client import models

from chunker import chunk_blocks
from docx_parser import parse_docx
from metadata import doc_metadata
from pdf_parser import parse_pdf
from store import COLLECTION, EMBED_MODEL, embed, open_db, save_meta

PARSERS = {".pdf": lambda p: (parse_pdf(p), []), ".docx": parse_docx}

files = sorted(f for arg in map(Path, sys.argv[1:]) for f in ([arg] if arg.is_file() else arg.iterdir())
               if f.suffix.lower() in PARSERS)
t0, chunks = time.time(), []
for path in files:
    meta = doc_metadata(path)
    blocks, warnings = PARSERS[path.suffix.lower()](path)
    for w in warnings:
        print(f"  ! {path.name}: {w}")
    file_chunks = chunk_blocks(blocks, path.name, title=meta["title"])
    for c in file_chunks:
        c.update(meta)
    print(f"{path.name:<26}{meta['doc_type']:<6}{meta['modified']}  {meta['author']:<22}{len(file_chunks):>3} chunks")
    chunks += file_chunks

vectors = embed([c["text"] for c in chunks])
db = open_db()
if db.collection_exists(COLLECTION):
    db.delete_collection(COLLECTION)
db.create_collection(COLLECTION, vectors_config=models.VectorParams(size=len(vectors[0]),
                                                                    distance=models.Distance.COSINE))
keys = ("source", "page", "section", "types", "text", "doc_type", "title", "author", "modified")
db.upsert(COLLECTION, points=[
    models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{c['source']}#{i}")), vector=v,
                       payload={k: c[k] for k in keys})
    for i, (c, v) in enumerate(zip(chunks, vectors))])
save_meta(len(vectors[0]))
db.close()
print(f"Indexed {len(chunks)} chunks from {len(files)} files with {EMBED_MODEL} in {time.time() - t0:.1f}s")
