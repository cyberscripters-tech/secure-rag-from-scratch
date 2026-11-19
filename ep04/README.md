# EP04: PDFs done right

EP02/EP03 used `page.extract_text()` and fixed 800-character windows. That keeps headers and footers, loses headings, flattens tables, cuts sentences in half, and can't read scanned pages at all. EP04 fixes all five.

| File | What it does |
|---|---|
| [`pdf_parser.py`](pdf_parser.py) | pdfplumber-based parser: drops repeated headers/footers, detects headings (bold + font size), extracts tables row by row ("Header: value"), OCRs scanned pages with Tesseract (+ a median filter against speckles) |
| [`chunker.py`](chunker.py) | Structure-aware chunks: never mixes sections, never cuts a paragraph or table row, prefixes every chunk with `[source · section path]` |
| [`index.py`](index.py) / [`ask.py`](ask.py) | Index every PDF in a folder into Qdrant, then ask |
| [`compare_chunking.py`](compare_chunking.py) | Retrieval test: naive vs structured chunks (31 questions) |
| [`answer_check.py`](answer_check.py) | Answer test: the EP02 refund question ×5 with each chunking |

## Setup

Tesseract is a system package:

```bash
# Ubuntu/Debian: sudo apt install tesseract-ocr     macOS: brew install tesseract
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
pip install -r requirements.txt
```

## Run

```bash
python ep04/pdf_parser.py data/acme/pdfs/ax200_spec.pdf     # see the blocks
python ep04/chunker.py data/acme/pdfs/handbook.pdf          # see the chunks
python ep04/index.py data/acme/pdfs/*.pdf
python ep04/ask.py "How fast can the last wrist joint rotate?"
```

## Results on our sample data (llama3.2 3B, mxbai-embed-large, 2-core test VM)

Retrieval, hit@1 (31 questions):

| source | questions | naive | structured |
|---|---|---|---|
| handbook.pdf | 25 | 92% | 92% |
| ax200_spec.pdf | 4 | 75% | 100% |
| scanned_invoice.pdf | 2 | 0% | 100% |
| **all** | 31 | 84% | 94% |

hit@4: 94% → 100%.

Answers: "What's the refund policy for enterprise customers?" ×5. Naive chunks applied the Business plan's 90-day rule to Enterprise in **2/5** answers; structured chunks in **0/5**. We read every answer; `answer_check.py`'s automatic check matched that review.

OCR on the scanned invoice (15 key fields): raw image **4/15** correct, with a median filter **15/15**, binarised **12/15**.

Five runs is a small sample. LLM output varies, so your numbers may differ.
