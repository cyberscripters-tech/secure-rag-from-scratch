"""EP05: parse Word documents into the same blocks as the PDF parser.

- Walks the document body in order, so tables stay where they appear.
- Headings come from Word styles (Heading 1, Heading 2), not from guessing font sizes.
- Lists keep their bullets / numbers.
- Hidden text (font "hidden" / w:vanish) is invisible in Word but present in the file.
  We drop it and report it: it is a classic place to hide prompt injections (see EP12).
"""
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def _rows_text(table):
    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
    header, *body = rows
    return "\n".join(" | ".join(f"{h}: {v}" for h, v in zip(header, row) if v) for row in body)


def parse_docx(path):
    doc = Document(path)
    blocks, warnings, h1, h2, number = [], [], "", "", 0
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[1]
        section = " > ".join(s for s in (h1, h2) if s)
        if tag == "tbl":
            blocks.append({"page": None, "type": "table", "text": _rows_text(Table(child, doc)), "section": section})
            continue
        if tag != "p":
            continue
        p = Paragraph(child, doc)
        hidden = "".join(r.text for r in p.runs if r.font.hidden)
        if hidden.strip():
            warnings.append(f"hidden text dropped: {hidden.strip()!r}")
        text = "".join(r.text for r in p.runs if not r.font.hidden).strip()
        if not text:
            continue
        style = p.style.name
        if style == "Title":
            continue  # the title is stored as metadata
        if style.startswith("Heading"):
            level = int(style.split()[-1]) if style.split()[-1].isdigit() else 1
            h1, h2 = (text, "") if level == 1 else (h1, text)
            blocks.append({"page": None, "type": "heading", "text": text, "section": " > ".join(s for s in (h1, h2) if s)})
            continue
        if style.startswith("List Number"):
            number += 1
            text = f"{number}. {text}"
        else:
            number = 0
            if style.startswith("List Bullet"):
                text = f"• {text}"
        blocks.append({"page": None, "type": "text", "text": text, "section": section})
    return blocks, warnings


if __name__ == "__main__":
    import sys

    blocks, warnings = parse_docx(sys.argv[1])
    for w in warnings:
        print("WARNING", w)
    for b in blocks:
        print(f"{b['type']:<8}[{b['section']}]  {b['text'][:110]}")
