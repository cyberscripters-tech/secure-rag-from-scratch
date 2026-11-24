"""EP07: incremental Slack sync into Qdrant.

Keeps every synced message in index/slack_store.json. On each run it reads one or more
export folders, finds messages it hasn't seen (by ts), rebuilds conversations, and
re-embeds ONLY the threads/windows that changed. Point IDs are stable per conversation,
so an updated thread overwrites its old vector instead of creating a duplicate.

    python ep07/sync_slack.py data/acme/slack            # first sync
    python ep07/sync_slack.py data/acme/slack_update     # later: only new messages
"""
import json
import sys
import time
import uuid
from pathlib import Path

from qdrant_client import models

from slack_parser import conversation_chunks, load_messages, load_workspace
from store import COLLECTION, embed, open_db

STORE = Path("index/slack_store.json")


def sync(db, *roots):
    store = json.loads(STORE.read_text()) if STORE.exists() else {"users": {}, "channels": {}, "messages": {}}
    for root in roots:
        if (Path(root) / "users.json").exists():  # full exports carry users + channels; partial ones may not
            users, channels = load_workspace(root)
            store["users"].update(users)
            store["channels"].update(channels)
    new = [m for m in load_messages(*roots) if m["ts"] not in store["messages"]]
    for m in new:
        store["messages"][m["ts"]] = m
    new_ts = {m["ts"] for m in new}
    msgs = sorted(store["messages"].values(), key=lambda m: float(m["ts"]))
    chunks = [c for c in conversation_chunks(msgs, store["users"], store["channels"]) if new_ts & set(c["ts"])]
    if chunks:
        vectors = embed([c["text"] for c in chunks])
        db.upsert(COLLECTION, points=[
            models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "slack:" + c["key"])), vector=v, payload={
                "source": f"slack #{c['channel']}", "page": None, "section": c["kind"], "types": ["slack"],
                "text": c["text"], "doc_type": "slack", "title": f"#{c['channel']}", "author": "slack",
                "modified": c["modified"], "visibility": c["visibility"], "members": c["members"]})
            for c, v in zip(chunks, vectors)])
    STORE.parent.mkdir(exist_ok=True)
    STORE.write_text(json.dumps(store))
    return len(new), len(chunks), len(store["messages"])


if __name__ == "__main__":
    t0 = time.time()
    db = open_db()
    new, changed, total = sync(db, *sys.argv[1:])
    db.close()
    print(f"{new} new messages -> re-embedded {changed} conversation(s) in {time.time() - t0:.1f}s "
          f"({total} messages synced in total)")
