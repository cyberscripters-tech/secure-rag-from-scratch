# Acme Robotics sample data (fictional)

Everything here is invented for the CyberScripters RAG series. Any resemblance to real companies or people is coincidental.

| Path | Used in | Contents |
|---|---|---|
| `pdfs/handbook.pdf` | EP02+ | 15-page employee & customer policy handbook (refunds on page 12) |
| `pdfs/ax200_spec.pdf` | EP04+ | 2-page product data sheet with three tables |
| `pdfs/scanned_invoice.pdf` | EP04+ | image-only "scanned" invoice (needs OCR) |
| `docs/legal_terms.docx` | EP05+ | enterprise contract terms: numbered clauses, a table |
| `docs/pricing_memo.docx` | EP05+ | Sept 2026 memo that changes the handbook's discount rules (a deliberate conflict) |
| `docs/sales_kickoff_notes.docx` | EP05+ | meeting notes with a **hidden-text prompt injection** (for testing) |
| `eval/handbook_retrieval.jsonl` | EP03 | 25 questions with known pages |
| `eval/pdf_retrieval.jsonl` | EP04 | 31 questions across all three PDFs |

Generators live in [`tools/`](../../tools). More sources (email threads, Slack exports) arrive in later episodes.
