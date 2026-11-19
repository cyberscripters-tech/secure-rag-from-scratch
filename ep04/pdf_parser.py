"""EP04: parse PDFs into clean, structured blocks.

What it fixes compared to EP02's `page.extract_text()`:
  1. Headers/footers: lines that repeat on most pages are dropped.
  2. Headings: detected from font size + bold, so every block knows its section.
  3. Tables: extracted as tables; each row becomes "Header: value | Header: value".
  4. Scanned pages: no text layer -> OCR with Tesseract.

parse_pdf(path) -> list of blocks:
  {"page": 3, "type": "heading" | "text" | "table" | "ocr", "text": "...", "section": "2. People > 2.1 Code"}
"""
import re
from collections import Counter

import pdfplumber
import pytesseract
from PIL import ImageFilter

HEADING_MIN_SIZE = 12      # body text in our PDFs is ~10.5 pt
H1_MIN_SIZE = 18
OCR_MIN_CHARS = 20         # fewer characters than this -> treat page as scanned


def _norm(line):
    """'Page 12' and 'Page 13' should count as the same repeated line."""
    return re.sub(r"\d+", "#", line.strip().lower())


def _boilerplate(pdf):
    """Lines that appear on at least half of the pages are headers or footers."""
    if len(pdf.pages) < 2:
        return set()
    counts = Counter()
    for page in pdf.pages:
        counts.update({_norm(l["text"]) for l in page.extract_text_lines()})
    return {line for line, n in counts.items() if n >= max(2, len(pdf.pages) / 2)}


def _table_text(rows):
    header, *body = [[(cell or "").replace("\n", " ").strip() for cell in row] for row in rows]
    return "\n".join(" | ".join(f"{h}: {v}" for h, v in zip(header, row) if v) for row in body)


def _ocr(page):
    image = page.to_image(resolution=300).original.convert("L")
    image = image.filter(ImageFilter.MedianFilter(3))           # remove scanner speckles
    return pytesseract.image_to_string(image, config="--psm 4")  # psm 4: columns of text


def parse_pdf(path):
    blocks, h1, h2 = [], "", ""
    with pdfplumber.open(path) as pdf:
        boiler = _boilerplate(pdf)
        for page_no, page in enumerate(pdf.pages, start=1):
            if len(page.chars) < OCR_MIN_CHARS:
                text = _ocr(page)
                for para in re.split(r"\n\s*\n", text):
                    if para.strip():
                        blocks.append({"page": page_no, "type": "ocr", "text": " ".join(para.split()),
                                       "section": "scanned page (OCR)"})
                continue

            tables = page.find_tables()
            items = [(t.bbox[1], "table", _table_text(t.extract())) for t in tables]
            inside = lambda obj: any(t.bbox[0] <= obj["x0"] and obj["x1"] <= t.bbox[2] and
                                     t.bbox[1] <= obj["top"] and obj["bottom"] <= t.bbox[3] for t in tables)
            for line in page.filter(lambda o: not inside(o) if "x0" in o else True).extract_text_lines():
                if _norm(line["text"]) in boiler:
                    continue
                size = max(c["size"] for c in line["chars"])
                bold = any("Bold" in c["fontname"] for c in line["chars"])
                kind = "heading" if bold and size >= HEADING_MIN_SIZE else "text"
                text = line["text"].replace("(cid:127)", "•")         # bullet glyph without a unicode mapping
                items.append((line["top"], kind, text, size, line["bottom"]))

            prev_bottom = None
            for top, kind, text, *rest in sorted(items, key=lambda i: i[0]):
                if kind == "heading" and blocks and blocks[-1]["type"] == "heading" and blocks[-1]["page"] == page_no \
                        and prev_bottom is not None and top - prev_bottom < 8:
                    text = blocks.pop()["text"] + " " + text    # heading wrapped onto two lines
                if kind == "heading":
                    if rest[0] >= H1_MIN_SIZE:
                        h1, h2 = text, ""
                    else:
                        h2 = text
                section = " > ".join(s for s in (h1, h2) if s)
                if kind == "text" and blocks and blocks[-1]["type"] == "text" and blocks[-1]["page"] == page_no \
                        and prev_bottom is not None and top - prev_bottom < 6:
                    blocks[-1]["text"] += " " + text        # same paragraph: join lines
                else:
                    blocks.append({"page": page_no, "type": kind, "text": text, "section": section})
                prev_bottom = rest[1] if kind != "table" else None
    return blocks


if __name__ == "__main__":
    import sys

    for b in parse_pdf(sys.argv[1]):
        print(f"p{b['page']:<3}{b['type']:<8}[{b['section']}]  {b['text'][:110]}")
