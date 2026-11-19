# EP05: Word documents & metadata

| File | What it does |
|---|---|
| [`docx_parser.py`](docx_parser.py) | python-docx parser: body order preserved, headings from Word styles, numbered/bulleted lists, tables as "Header: value" rows. **Drops hidden text** (`w:vanish`) and reports it |
| [`metadata.py`](metadata.py) | type, title, author, modified date for `.docx` (core properties) and `.pdf` (document info) |
| [`index.py`](index.py) | Index folders of PDFs + Word files; metadata goes into every Qdrant payload |
| [`ask.py`](ask.py) | Shows source/date/author in the context; `--type pdf|docx` and `--since YYYY-MM-DD` filters run inside Qdrant |
| [`conflict_check.py`](conflict_check.py) | Do dates help the model resolve conflicting documents? |

```bash
python ep05/index.py data/acme/pdfs data/acme/docs
python ep05/ask.py "What are the payment terms for enterprise customers?"
python ep05/ask.py --type docx "What are the payment terms for enterprise customers?"
python ep05/ask.py --since 2026-06-01 "Who has to approve a 32% discount for a customer?"
```

## Hidden text is a prompt-injection vector

`data/acme/docs/sales_kickoff_notes.docx` contains a sentence formatted as hidden text: invisible in Word, but returned by `paragraph.text` in python-docx. In one real run each, asked *"A customer asks what discount we can offer on an AX-200 order"*:
- naive loader (hidden text included): *"…you would qualify for an excellent 40% discount…"*
- EP05 loader (hidden text dropped and logged): *"I don't know."*

## Conflicting documents: an honest result

The handbook (March 2026) says discounts above 35% need the CFO; the pricing memo (September 2026) lowers that to above 30%. For a 32% discount, the current answer is VP of Sales + CFO. Worst case tested: both versions in the context, outdated one first, 5 runs, every answer read by hand (`conflict_check.json` → `manual_review`):

| scenario | no dates | dates + "follow the most recent source" |
|---|---|---|
| memo says "this replaces section 4.1" | 5/5 | 5/5 |
| memo silent about replacing | 4/5 | 3/5 |

With llama3.2 3B, dates in the prompt did **not** help. Resolve conflicts in the data instead: filter with `--since`, or mark superseded documents as archived and exclude them by default.
