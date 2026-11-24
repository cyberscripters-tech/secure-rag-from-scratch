"""EP05: document-level metadata for PDFs and Word files."""
from datetime import datetime
from pathlib import Path

from docx import Document
from pypdf import PdfReader


def doc_metadata(path):
    path = Path(path)
    if path.suffix.lower() == ".docx":
        cp = Document(path).core_properties
        title, author, modified = cp.title, cp.author, cp.modified or cp.created
    else:
        meta = PdfReader(path).metadata or {}
        title, author = meta.get("/Title"), meta.get("/Author")
        modified = getattr(meta, "modification_date", None) or getattr(meta, "creation_date", None)
    return {
        "doc_type": path.suffix.lower().lstrip("."),
        "title": title or path.stem,
        "author": author if author and author != "(anonymous)" else "unknown",
        "modified": (modified or datetime.fromtimestamp(path.stat().st_mtime)).date().isoformat(),
    }


if __name__ == "__main__":
    import sys

    for p in sys.argv[1:]:
        print(Path(p).name, doc_metadata(p))
