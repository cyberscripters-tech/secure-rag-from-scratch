"""EP08: one ingestion pipeline for every source, incremental and idempotent.

    python ep08/ingest.py                      # sync everything under data/acme
    python ep08/ingest.py --full               # wipe and rebuild
    python ep08/ingest.py --every 900          # keep syncing every 15 minutes

How it works:
  - every source folder has a loader: PDF, Word, email (with attachments), Slack export
  - index/manifest.json stores, per file, a SHA-256 hash and the IDs of its chunks
  - new or changed file   -> parse, chunk, embed, replace its old chunks
  - unchanged file        -> skipped (no embedding cost)
  - deleted file          -> its chunks are deleted from Qdrant
  - identical content     -> indexed once (e.g. an email attachment that is also in pdfs/)
  - Slack                 -> incremental by message timestamp (EP07 sync)
  - every chunk carries provenance: source path, content hash, ingested_at
"""
import argparse
import hashlib
import json
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from qdrant_client import models

from chunker import chunk_blocks
from docx_parser import parse_docx
from email_parser import build_threads, parse_eml
from metadata import doc_metadata
from pdf_parser import parse_pdf
from store import COLLECTION, EMBED_MODEL, META, embed, open_db, save_meta
from sync_slack import STORE, sync

DATA = Path("data/acme")
MANIFEST = Path("index/manifest.json")
INTERNAL_DOMAIN = "acme-robotics.example"
DOC_PARSERS = {".pdf": lambda p: (parse_pdf(p), []), ".docx": parse_docx}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def point_id(key, i):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{key}#{i}"))


# ---------------------------------------------------------------- loaders: file -> chunks
def load_document(path, label, meta, report):
    blocks, warnings = DOC_PARSERS[path.suffix.lower()](path)
    report["quarantined"] += [f"{label}: {w}" for w in warnings]
    chunks = chunk_blocks(blocks, label, title=meta["title"])
    for c in chunks:
        c.update(meta)
    return chunks


def load_email(path, threads_by_file, known_hashes, report):
    m = threads_by_file[path.name]
    external = not m["from_addr"].endswith("@" + INTERNAL_DOMAIN)
    report["quarantined"] += [f"{path.name}: hidden HTML dropped: {h[:60]!r}…" for h in m["hidden"]]
    meta = {"doc_type": "email", "title": m["thread_subject"], "author": f"{m['from_name']} <{m['from_addr']}>",
            "modified": m["date"].date().isoformat(), "thread_id": m["thread_id"], "external": external}
    role = f", {m['sender_role']}" if m.get("sender_role") else ""
    header = (f"[email · thread: {m['thread_subject']} · from {m['from_name']}{role} <{m['from_addr']}>"
              f"{' (EXTERNAL)' if external else ''} · {m['date']:%Y-%m-%d}]")
    chunks = [{"source": path.name, "page": None, "section": m["subject"], "types": ["email"],
               "text": f"{header}\n{m['body']}", **meta}]
    for name, data in m["attachments"]:
        h = sha256(data)
        if h in known_hashes:
            report["duplicates"].append(f"{name} in {path.name} = {known_hashes[h]} (indexed once)")
            continue
        if Path(name).suffix.lower() in DOC_PARSERS:
            with tempfile.TemporaryDirectory() as d:
                tmp = Path(d) / name
                tmp.write_bytes(data)
                chunks += load_document(tmp, f"{name} (attachment of {path.name})",
                                        {**meta, "doc_type": tmp.suffix.lstrip("."), "title": name}, report)
            known_hashes[h] = f"{path.name}/{name}"
    return chunks


# ---------------------------------------------------------------- the pipeline
def discover():
    """Every file the pipeline is responsible for, in dependency order (documents before emails)."""
    files = sorted(p for d in ("pdfs", "docs") for p in (DATA / d).glob("*") if p.suffix.lower() in DOC_PARSERS)
    return files + sorted((DATA / "emails").glob("*.eml"))


def run(full=False):
    t0 = time.time()
    report = {"new": [], "changed": [], "unchanged": 0, "deleted": [], "duplicates": [], "quarantined": [],
              "embedded_chunks": 0, "deleted_chunks": 0}
    db = open_db()
    if full or not MANIFEST.exists() or not db.collection_exists(COLLECTION):
        if db.collection_exists(COLLECTION):
            db.delete_collection(COLLECTION)
        MANIFEST.unlink(missing_ok=True)
        STORE.unlink(missing_ok=True)
        dims = len(embed(["dimension probe"])[0])
        db.create_collection(COLLECTION, vectors_config=models.VectorParams(size=dims, distance=models.Distance.COSINE))
        save_meta(dims)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"files": {}}
    files = discover()
    hashes = {str(p): sha256(p.read_bytes()) for p in files}
    known = {}  # content hash -> where it was indexed (for duplicate detection)
    for p in files:
        known.setdefault(hashes[str(p)], str(p.relative_to(DATA)))

    # threads need every email header, but only changed emails get re-embedded
    emails = [parse_eml(p) for p in files if p.suffix == ".eml"]
    by_file = {Path(m["file"]).name: m for t in build_threads(emails) for m in t}

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for p in files:
        key, h = str(p.relative_to(DATA)), hashes[str(p)]
        old = manifest["files"].get(key)
        if old and old["hash"] == h:
            report["unchanged"] += 1
            continue
        if known[h] != key:  # same bytes as a file we already index
            report["duplicates"].append(f"{key} = {known[h]} (indexed once)")
            chunks = []
        elif p.suffix == ".eml":
            chunks = load_email(p, by_file, {k: v for k, v in known.items()}, report)
        else:
            chunks = load_document(p, p.name, doc_metadata(p), report)
        if old:
            db.delete(COLLECTION, points_selector=models.PointIdsList(points=old["ids"]))
            report["deleted_chunks"] += len(old["ids"])
        ids = [point_id(key, i) for i in range(len(chunks))]
        if chunks:
            vectors = embed([c["text"] for c in chunks])
            keys = ("source", "page", "section", "types", "text", "doc_type", "title", "author", "modified",
                    "thread_id", "external")
            db.upsert(COLLECTION, points=[models.PointStruct(id=i, vector=v, payload={
                **{k: c.get(k) for k in keys}, "visibility": "public", "members": [],
                "provenance": {"path": key, "sha256": h, "ingested_at": now}})
                for i, c, v in zip(ids, chunks, vectors)])
        report["changed" if old else "new"].append(key)
        report["embedded_chunks"] += len(chunks)
        manifest["files"][key] = {"hash": h, "ids": ids, "ingested_at": now}

    for key in sorted(set(manifest["files"]) - {str(p.relative_to(DATA)) for p in files}):
        ids = manifest["files"].pop(key)["ids"]
        db.delete(COLLECTION, points_selector=models.PointIdsList(points=ids))
        report["deleted"].append(key)
        report["deleted_chunks"] += len(ids)

    slack_roots = [r for r in (DATA / "slack", DATA / "slack_update") if r.exists()]
    new_msgs, slack_chunks, _ = sync(db, *slack_roots)
    report["slack_new_messages"], report["embedded_chunks"] = new_msgs, report["embedded_chunks"] + slack_chunks

    MANIFEST.parent.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1))
    report["points_in_index"] = db.count(COLLECTION).count
    db.close()
    report["seconds"] = round(time.time() - t0, 1)
    return report


def print_report(r):
    print(f"new {len(r['new'])} · changed {len(r['changed'])} · unchanged {r['unchanged']} · deleted {len(r['deleted'])}"
          f" · slack +{r['slack_new_messages']} msgs")
    print(f"embedded {r['embedded_chunks']} chunks · removed {r['deleted_chunks']} · index now {r['points_in_index']} "
          f"points · {r['seconds']}s with {EMBED_MODEL}")
    for d in r["duplicates"]:
        print(f"  = duplicate: {d}")
    for q in r["quarantined"]:
        print(f"  ! {q}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="wipe the index and rebuild everything")
    ap.add_argument("--every", type=int, help="keep running, syncing every N seconds")
    args = ap.parse_args()
    while True:
        print_report(run(full=args.full))
        if not args.every:
            break
        args.full = False
        time.sleep(args.every)
