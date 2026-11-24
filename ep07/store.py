"""Shared settings for the EP03 vector store."""
import json
import os
from pathlib import Path

import ollama
from qdrant_client import QdrantClient

try:  # read EMBED_MODEL etc. from .env, same as llm.py
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

EMBED_MODEL = os.getenv("EMBED_MODEL", "mxbai-embed-large")
DB_PATH = Path("index/qdrant")      # Qdrant runs embedded: no server, just files on disk
META = Path("index/meta.json")      # remembers which model built the index
COLLECTION = "acme"


def embed(texts):
    return ollama.embed(model=EMBED_MODEL, input=texts)["embeddings"]


def open_db():
    return QdrantClient(path=str(DB_PATH))


def save_meta(dims):
    META.write_text(json.dumps({"embed_model": EMBED_MODEL, "dims": dims}))


def check_meta():
    """Vectors from different models live in different spaces: never mix them."""
    meta = json.loads(META.read_text())
    if meta["embed_model"] != EMBED_MODEL:
        raise SystemExit(f"Index was built with {meta['embed_model']}, but EMBED_MODEL={EMBED_MODEL}. "
                         "Re-run index.py with the same model.")
