# EP08: One ingestion pipeline

| File | What it does |
|---|---|
| [`ingest.py`](ingest.py) | One run for every source under `data/acme`. A **manifest** (`index/manifest.json`) stores the SHA-256 and chunk IDs of every file: unchanged files are skipped, changed files are re-embedded and their old chunks deleted, deleted files lose their chunks. Byte-identical attachments are indexed once. Every chunk carries **provenance** (`path`, `sha256`, `ingested_at`). Slack uses the EP07 sync. `--full` rebuilds, `--every N` keeps syncing |
| [`evaluate.py`](evaluate.py) | All 53 test questions (PDF, email, Slack) against the unified index, **as a normal employee** (private channels filtered out) |
| [`evaluation_review.md`](evaluation_review.md) | Every top-1 miss, reviewed by hand |
| [`ask.py`](ask.py) | Same as EP07 |

```bash
python ep08/ingest.py --full        # first run
python ep08/ingest.py               # later runs: only what changed
python ep08/ingest.py --every 900   # keep syncing every 15 minutes
python ep08/evaluate.py
```

Or with cron: `*/15 * * * * cd ~/secure-rag-from-scratch && python ep08/ingest.py >> ingest.log 2>&1`

## Results on our sample data (mxbai-embed-large, 2-core test VM)

| run | result |
|---|---|
| full (`slack_update/` moved aside) | 24 files + 21 Slack messages → 74 chunks in 42.1 s; 2 duplicate attachments indexed once (EP07: 81 chunks); 2 hidden injections quarantined |
| again, nothing changed | 0 chunks, 0.0 s |
| pricing memo edited, phishing email deleted, 1 new Slack message | 1 changed, 1 deleted, 5 chunks embedded, 4 removed, 1.9 s |

On a fresh clone `--full` also picks up `slack_update/`: 22 messages, 75 chunks. The evaluation numbers are the same either way.

Evaluation (`evaluation.json`):

| set | questions | hit@1 | hit@4 |
|---|---|---|---|
| pdf | 31 | 77% | 90% |
| email | 12 | 58% | 92% |
| slack | 10 | 60% | 100% |
| **all** | 53 | **70%** | **92%** |

PDF hit@1 drops from 94% (EP04, PDFs alone) to 77%: more sources compete for the top spot. 5 of the 16 misses are correct answers from another source (adjusted hit@1: 79%). The real misses are stale information, exact identifiers (`INV-2026-0418`) and short messages: the motivation for EP09 (hybrid search, re-ranking, recency).

Building the evaluator also caught a bug: without the permission filter, a salary question returned `#hr-private`.
