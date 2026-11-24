"""EP06: index PDFs, Word files and emails (with their attachments).

    python ep06/index.py data/acme/pdfs data/acme/docs data/acme/emails
"""
import sys
import tempfile
import time
import uuid
from pathlib import Path

from qdrant_client import models

from chunker import chunk_blocks
from docx_parser import parse_docx
from email_parser import build_threads, parse_eml
from metadata import doc_metadata
from pdf_parser import parse_pdf
from store import COLLECTION, EMBED_MODEL, embed, open_db, save_meta

INTERNAL_DOMAIN = "acme-robotics.example"
PARSERS = {".pdf": lambda p: (parse_pdf(p), []), ".docx": parse_docx}


def document_chunks(path, meta, label=None):
    blocks, warnings = PARSERS[path.suffix.lower()](path)
    for w in warnings:
        print(f"  ! {label or path.name}: {w}")
    chunks = chunk_blocks(blocks, label or path.name, title=meta["title"])
    for c in chunks:
        c.update(meta)
    return chunks


def email_chunks(folder):
    msgs = [parse_eml(p) for p in sorted(folder.glob("*.eml"))]
    chunks = []
    for thread in build_threads(msgs):
        for m in thread:
            external = not m["from_addr"].endswith("@" + INTERNAL_DOMAIN)
            for h in m["hidden"]:
                print(f"  ! {Path(m['file']).name}: hidden HTML dropped: {h[:70]!r}…")
            meta = {"doc_type": "email", "title": m["thread_subject"], "author": f"{m['from_name']} <{m['from_addr']}>",
                    "modified": m["date"].date().isoformat(), "thread_id": m["thread_id"], "external": external}
            role = f", {m['sender_role']}" if m.get("sender_role") else ""
            header = (f"[email · thread: {m['thread_subject']} · from {m['from_name']}{role} <{m['from_addr']}>"
                      f"{' (EXTERNAL)' if external else ''} · {m['date']:%Y-%m-%d}]")
            chunks.append({"source": Path(m["file"]).name, "page": None, "section": m["subject"], "types": ["email"],
                           "text": f"{header}\n{m['body']}", **meta})
            for name, data in m["attachments"]:  # attachments go through the normal document parsers
                suffix = Path(name).suffix.lower()
                if suffix not in PARSERS:
                    continue
                with tempfile.TemporaryDirectory() as d:
                    tmp = Path(d) / name
                    tmp.write_bytes(data)
                    label = f"{name} (attachment of {Path(m['file']).name})"
                    chunks += document_chunks(tmp, {**meta, "doc_type": suffix.lstrip("."), "title": name}, label)
    return chunks


if __name__ == "__main__":
    t0, chunks = time.time(), []
    for arg in map(Path, sys.argv[1:]):
        if any(arg.glob("*.eml")):
            before = len(chunks)
            chunks += email_chunks(arg)
            print(f"{arg}: {len(chunks) - before} chunks from emails + attachments")
            continue
        for f in sorted(arg.iterdir()):
            if f.suffix.lower() in PARSERS:
                chunks += document_chunks(f, doc_metadata(f))
        print(f"{arg}: {len(chunks)} chunks so far")
    vectors = embed([c["text"] for c in chunks])
    db = open_db()
    if db.collection_exists(COLLECTION):
        db.delete_collection(COLLECTION)
    db.create_collection(COLLECTION, vectors_config=models.VectorParams(size=len(vectors[0]),
                                                                        distance=models.Distance.COSINE))
    keys = ("source", "page", "section", "types", "text", "doc_type", "title", "author", "modified", "thread_id", "external")
    db.upsert(COLLECTION, points=[
        models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{c['source']}#{i}")), vector=v,
                           payload={k: c.get(k) for k in keys})
        for i, (c, v) in enumerate(zip(chunks, vectors))])
    save_meta(len(vectors[0]))
    db.close()
    print(f"Indexed {len(chunks)} chunks with {EMBED_MODEL} in {time.time() - t0:.1f}s")
