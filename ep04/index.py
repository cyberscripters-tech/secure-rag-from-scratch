"""EP04: parse PDFs properly (tables, OCR, sections) and index them in Qdrant.

    python ep04/index.py data/acme/pdfs/*.pdf
"""
import sys
import time
import uuid
from pathlib import Path

from qdrant_client import models

from chunker import chunk_blocks
from pdf_parser import parse_pdf
from store import COLLECTION, EMBED_MODEL, embed, open_db, save_meta

t0 = time.time()
chunks = []
for path in map(Path, sys.argv[1:]):
    file_chunks = chunk_blocks(parse_pdf(path), path.name)
    print(f"{path.name:<22} {len(file_chunks):>3} chunks  "
          f"({sum('table' in c['types'] for c in file_chunks)} with tables, "
          f"{sum('ocr' in c['types'] for c in file_chunks)} from OCR)")
    chunks += file_chunks

vectors = embed([c["text"] for c in chunks])
db = open_db()
if db.collection_exists(COLLECTION):
    db.delete_collection(COLLECTION)
db.create_collection(COLLECTION, vectors_config=models.VectorParams(size=len(vectors[0]),
                                                                    distance=models.Distance.COSINE))
db.upsert(COLLECTION, points=[
    models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{c['source']}#{i}")), vector=v,
                       payload={k: c[k] for k in ("source", "page", "section", "types", "text")})
    for i, (c, v) in enumerate(zip(chunks, vectors))])
save_meta(len(vectors[0]))
db.close()
print(f"Indexed {len(chunks)} chunks with {EMBED_MODEL} in {time.time() - t0:.1f}s")
