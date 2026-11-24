"""EP06: turn .eml files into clean messages and threads.

What naive "dump the whole email" indexing gets wrong, and what we do instead:
  1. Quoted replies: every reply repeats the whole conversation -> we cut at the quote marker.
  2. Signatures + disclaimers: identical boilerplate in every message -> we cut at "-- " / sign-offs.
  3. HTML: tags, styles and HIDDEN elements -> we convert to text and drop hidden elements (and report them).
  4. Threads: rebuilt from Message-ID / In-Reply-To / References, falling back to the subject line.
  5. Attachments: returned as files, so the PDF/DOCX parsers from EP04/EP05 can handle them.
"""
import re
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime

from bs4 import BeautifulSoup

QUOTE_MARKERS = [
    re.compile(r"^On .{5,120} wrote:\s*$"),            # Gmail / Apple Mail
    re.compile(r"^-{2,}\s*Original Message\s*-{2,}"),   # Outlook
    re.compile(r"^From: .+@.+$"),                      # Outlook without the dashed line
    re.compile(r"^>"),                                 # plain quoting
]
SIGNOFF = re.compile(r"^(best|kind|warm)?\s*(regards|thanks|thank you|cheers),?\s*$", re.I)
HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0|opacity\s*:\s*0", re.I)


def html_to_text(html):
    """Visible text only. Returns (text, hidden_texts)."""
    soup = BeautifulSoup(html, "html.parser")
    hidden = []
    for el in soup.find_all(style=HIDDEN_STYLE):
        hidden.append(" ".join(el.get_text(" ").split()))
        el.decompose()
    for el in soup(["script", "style", "head"]):
        el.decompose()
    for a in soup.find_all("a", href=True):          # keep link targets: for phishing, the domain matters
        a.replace_with(f"{a.get_text(' ', strip=True)} ({a['href']})")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    text = "\n\n".join(" ".join(p.get_text("").split("\x00")).strip() for p in soup.find_all(["p", "li", "div"])
                       if p.get_text(strip=True))
    return text or soup.get_text("\n"), hidden


def strip_quotes(text):
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if any(m.match(line.strip()) for m in QUOTE_MARKERS):
            return "\n".join(lines[:i]).rstrip()
    return text.rstrip()


def signature_role(text):
    """'-- / Ananya Rao / Chief Financial Officer | Acme Robotics' -> 'Chief Financial Officer'.
    We strip signatures from the body, but the sender's role is useful context: keep it as metadata."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.rstrip() in ("--", "-- ") and i + 2 < len(lines):
            return lines[i + 2].split("|")[0].strip() or None
    return None


def strip_signature(text):
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.rstrip() in ("--", "-- "):
            lines = lines[:i]
            break
    # a sign-off ("Best regards,") followed by at most 3 short lines (the name) ends the message
    for i in range(len(lines) - 1, max(-1, len(lines) - 6), -1):
        if SIGNOFF.match(lines[i].strip()):
            tail = [l for l in lines[i + 1:] if l.strip()]
            if len(tail) <= 3 and all(len(l) < 40 for l in tail):
                lines = lines[:i]
            break
    return "\n".join(lines).strip()


def parse_eml(path):
    msg = BytesParser(policy=policy.default).parse(open(path, "rb"))
    body_part = msg.get_body(preferencelist=("plain", "html"))
    raw = body_part.get_content() if body_part else ""
    hidden = []
    if body_part is not None and body_part.get_content_subtype() == "html":
        raw, hidden = html_to_text(raw)
    attachments = [(a.get_filename(), a.get_content()) for a in msg.iter_attachments() if a.get_filename()]
    sender = getaddresses([msg["From"] or ""])[0]
    return {
        "file": str(path),
        "message_id": (msg["Message-ID"] or "").strip(),
        "in_reply_to": (msg["In-Reply-To"] or "").strip(),
        "references": (msg["References"] or "").split(),
        "subject": msg["Subject"] or "",
        "from_name": sender[0], "from_addr": sender[1].lower(),
        "to": [a for _, a in getaddresses(msg.get_all("To", []))],
        "date": parsedate_to_datetime(msg["Date"]),
        "raw_text": raw,
        "body": strip_signature(strip_quotes(raw)),
        "sender_role": signature_role(strip_quotes(raw)),
        "hidden": hidden,
        "attachments": attachments,
    }


def normalize_subject(s):
    return re.sub(r"^((re|fwd?|aw|wg)\s*:\s*)+", "", s.strip(), flags=re.I).lower()


def build_threads(messages):
    """Union messages that reference each other; then merge leftovers by normalized subject."""
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    by_id = {m["message_id"]: m for m in messages}
    for m in messages:
        for ref in m["references"] + ([m["in_reply_to"]] if m["in_reply_to"] else []):
            if ref in by_id:
                union(m["message_id"], ref)
    first_by_subject = {}
    for m in sorted(messages, key=lambda m: m["date"]):
        key = normalize_subject(m["subject"])
        if key in first_by_subject and not m["in_reply_to"]:
            union(m["message_id"], first_by_subject[key])   # fallback for replies without headers
        first_by_subject.setdefault(key, m["message_id"])
    threads = {}
    for m in messages:
        threads.setdefault(find(m["message_id"]), []).append(m)
    out = []
    for msgs in threads.values():
        msgs.sort(key=lambda m: m["date"])
        tid = "thread-" + str(abs(hash(msgs[0]["message_id"])) % 10 ** 8)
        for m in msgs:
            m["thread_id"], m["thread_subject"] = tid, re.sub(r"^((re|fwd?)\s*:\s*)+", "", msgs[0]["subject"], flags=re.I)
        out.append(msgs)
    return sorted(out, key=lambda t: t[0]["date"])


if __name__ == "__main__":
    import sys
    from pathlib import Path

    msgs = [parse_eml(p) for p in sorted(Path(sys.argv[1]).glob("*.eml"))]
    for thread in build_threads(msgs):
        print(f"== {thread[0]['thread_subject']}  ({len(thread)} messages)")
        for m in thread:
            extra = f"  +{len(m['attachments'])} attachment(s)" if m["attachments"] else ""
            warn = f"  ! {len(m['hidden'])} hidden HTML element(s)" if m["hidden"] else ""
            print(f"   {m['date']:%Y-%m-%d} {m['from_name']:<16} raw {len(m['raw_text']):>5} -> clean {len(m['body']):>4} chars{extra}{warn}")
