"""EP04/EP05: structure-aware chunking (EP05 adds a title fallback for text before the first heading).

Rules:
  - A chunk never mixes two sections.
  - Paragraphs and table rows are never cut in half; only a paragraph that is
    longer than max_chars on its own gets split, and then only at sentence ends.
  - Every chunk starts with its section path, so it makes sense on its own:
        "[handbook.pdf · 4. Customer Policies > 4.2 Refunds for subscriptions]"
"""
import re

MAX_CHARS = 900


def _pieces(block, max_chars):
    """Split one block into pieces <= max_chars without breaking sentences or table rows."""
    text = block["text"]
    if len(text) <= max_chars:
        return [text]
    units = text.split("\n") if block["type"] == "table" else re.split(r"(?<=[.!?])\s+", text)
    out, cur = [], ""
    for u in units:
        if cur and len(cur) + len(u) + 1 > max_chars:
            out.append(cur)
            cur = u
        else:
            cur = f"{cur}\n{u}" if (cur and block["type"] == "table") else f"{cur} {u}".strip()
    return out + [cur] if cur else out


def chunk_blocks(blocks, source, title=None, max_chars=MAX_CHARS):
    chunks, cur = [], None
    for b in blocks:
        if b["type"] == "heading":
            continue  # the heading lives on in the section path
        for piece in _pieces(b, max_chars):
            same_section = cur and cur["section"] == b["section"]
            if not same_section or len(cur["body"]) + len(piece) + 2 > max_chars:
                if cur:
                    chunks.append(cur)
                cur = {"source": source, "section": b["section"], "page": b["page"], "body": piece,
                       "types": {b["type"]}}
            else:
                cur["body"] += "\n\n" + piece
                cur["types"].add(b["type"])
    if cur:
        chunks.append(cur)
    for c in chunks:
        c["section"] = c["section"] or title or ""
        c["text"] = f"[{source} · {c['section']}]\n{c['body']}"
        c["types"] = sorted(c["types"])
    return chunks


if __name__ == "__main__":
    import sys
    from pathlib import Path

    from pdf_parser import parse_pdf

    path = Path(sys.argv[1])
    for i, c in enumerate(chunk_blocks(parse_pdf(path), path.name)):
        print(f"--- chunk {i + 1} · p{c['page']} · {len(c['text'])} chars · {','.join(c['types'])}")
        print(c["text"])
