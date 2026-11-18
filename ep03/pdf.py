"""PDF loading + chunking (same as EP02). Proper chunking arrives in EP04."""
from pypdf import PdfReader


def load_pdf(path):  # -> [(page_number, text), ...]
    return [(i + 1, p.extract_text() or "") for i, p in enumerate(PdfReader(path).pages)]


def chunk(pages, size=800, overlap=150):
    chunks = []
    for page, text in pages:
        for start in range(0, len(text), size - overlap):
            if piece := text[start:start + size].strip():
                chunks.append({"page": page, "text": piece})
    return chunks
