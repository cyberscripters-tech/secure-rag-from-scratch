"""Stamps realistic creation/modification dates into the generated sample PDFs.

reportlab writes "today" as the PDF date; EP05 uses document dates to resolve
conflicting sources, so each fictional PDF gets the date it was "published".

    python tools/pdf_dates.py
"""
from pathlib import Path

from pypdf import PdfReader, PdfWriter

PDFS = Path(__file__).resolve().parent.parent / "data" / "acme" / "pdfs"
DATES = {"handbook.pdf": "20260302090000", "ax200_spec.pdf": "20260115090000", "scanned_invoice.pdf": "20260914120000"}

if __name__ == "__main__":
    for name, d in DATES.items():
        path = PDFS / name
        reader = PdfReader(path)
        writer = PdfWriter(clone_from=reader)
        meta = dict(reader.metadata or {})
        meta.update({"/CreationDate": f"D:{d}Z", "/ModDate": f"D:{d}Z"})
        writer.add_metadata(meta)
        with open(path, "wb") as f:
            writer.write(f)
        print(name, "->", d[:8])
