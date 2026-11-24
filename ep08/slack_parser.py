"""EP07: turn a Slack export into readable conversation chunks.

- resolves <@U123> -> @Maya Pillai, <#C123|sales-ops> -> #sales-ops, <https://x|label> -> label (https://x)
- drops channel joins/leaves and bot messages
- a thread (parent + replies) becomes one chunk; loose messages are grouped into time windows
- every chunk knows its channel, visibility (public/private) and the channel members
"""
import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
SKIP_SUBTYPES = {"channel_join", "channel_leave", "bot_message", "channel_topic", "channel_purpose"}
WINDOW = timedelta(minutes=60)


def load_workspace(root):
    root = Path(root)
    users = {u["id"]: u["real_name"] for u in json.loads((root / "users.json").read_text())}
    channels = {}
    for f in ("channels.json", "groups.json"):
        if (root / f).exists():
            for c in json.loads((root / f).read_text()):
                channels[c["name"]] = {"id": c["id"], "private": c.get("is_private", f == "groups.json"),
                                       "members": [users.get(m, m) for m in c.get("members", [])]}
    return users, channels


def clean_text(text, users, channels_by_id):
    text = re.sub(r"<@(\w+)>", lambda m: "@" + users.get(m.group(1), m.group(1)), text)
    text = re.sub(r"<#(\w+)\|([^>]*)>", lambda m: "#" + (m.group(2) or channels_by_id.get(m.group(1), m.group(1))), text)
    text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"\2 (\1)", text)
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)
    return html.unescape(text)


def load_messages(*roots, users=None, channels=None):
    """All messages from one or more export folders (a full export + later partial exports)."""
    out = []
    for root in map(Path, roots):
        for day_file in sorted(root.glob("*/*.json")):
            channel = day_file.parent.name
            for m in json.loads(day_file.read_text()):
                if m.get("subtype") in SKIP_SUBTYPES:
                    continue
                out.append({**m, "channel": channel})
    return sorted(out, key=lambda m: float(m["ts"]))


def when(ts):
    return datetime.fromtimestamp(float(ts), IST)


def conversation_chunks(messages, users, channels):
    """Threads -> one chunk each; other messages -> windows of messages less than 60 minutes apart."""
    by_id = {c["id"]: name for name, c in channels.items()}
    groups = {}
    for m in messages:
        if m.get("thread_ts"):
            key = (m["channel"], "thread", m["thread_ts"])
        else:
            key = None
            for k, g in reversed(list(groups.items())):
                if k[0] == m["channel"] and k[1] == "window" and when(m["ts"]) - when(g[-1]["ts"]) < WINDOW:
                    key = k
                    break
            key = key or (m["channel"], "window", m["ts"])
        groups.setdefault(key, []).append(m)
    chunks = []
    for (channel, kind, first_ts), msgs in groups.items():
        info = channels.get(channel, {"private": False, "members": []})
        lines = [f"{users.get(m['user'], m['user'])} ({when(m['ts']):%Y-%m-%d %H:%M}){' [edited]' if m.get('edited') else ''}: "
                 f"{clean_text(m['text'], users, by_id)}" for m in msgs]
        starter = users.get(msgs[0]["user"], msgs[0]["user"])
        head = f"[slack · #{channel}{' (private)' if info['private'] else ''} · " \
               f"{'thread started by ' + starter if kind == 'thread' else 'conversation'} · {when(first_ts):%Y-%m-%d}]"
        chunks.append({"key": f"{channel}:{first_ts}", "channel": channel, "kind": kind,
                       "text": head + "\n" + "\n".join(lines), "ts": [m["ts"] for m in msgs],
                       "last_ts": msgs[-1]["ts"], "visibility": "private" if info["private"] else "public",
                       "members": info["members"], "modified": when(msgs[-1]["ts"]).date().isoformat()})
    return chunks


if __name__ == "__main__":
    import sys

    users, channels = load_workspace(sys.argv[1])
    msgs = load_messages(*sys.argv[1:])
    for c in conversation_chunks(msgs, users, channels):
        print(f"--- {c['key']} · {c['kind']} · {c['visibility']} · {len(c['ts'])} msg")
        print(c["text"])
