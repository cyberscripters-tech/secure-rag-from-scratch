"""EP03: embed a PDF once and store the vectors in Qdrant.

    python ep03/index.py data/acme/pdfs/handbook.pdf
"""
import sys
import time
import uuid
from pathlib import Path

from qdrant_client import models

from pdf import chunk, load_pdf
from store import COLLECTION, EMBED_MODEL, DB_PATH, embed, open_db, save_meta

path = Path(sys.argv[1])
t0 = time.time()
chunks = chunk(load_pdf(path))
vectors = embed([c["text"] for c in chunks])

db = open_db()
if db.collection_exists(COLLECTION):
    db.delete_collection(COLLECTION)
db.create_collection(COLLECTION, vectors_config=models.VectorParams(
    size=len(vectors[0]), distance=models.Distance.COSINE))
db.upsert(COLLECTION, points=[
    models.PointStruct(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{path.name}#{i}")),  # same chunk -> same id
        vector=v,
        payload={"source": path.name, "page": c["page"], "text": c["text"]})
    for i, (c, v) in enumerate(zip(chunks, vectors))])
save_meta(len(vectors[0]))
db.close()
print(f"Indexed {len(chunks)} chunks from {path.name} with {EMBED_MODEL} "
      f"({len(vectors[0])} dims) in {time.time() - t0:.1f}s -> {DB_PATH}/")
