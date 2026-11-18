# EP02: Your first RAG in under 50 lines

A complete RAG in [`rag.py`](rag.py) (45 lines): load a PDF → chunk → embed → retrieve → answer with page citations.

## Run it

```bash
# from the repo root, with your virtual environment active
pip install -r requirements.txt
ollama pull nomic-embed-text
ollama pull llama3.2

# ask one or more questions
python ep02/rag.py data/acme/pdfs/handbook.pdf "What's the refund policy for enterprise customers?"

# or chat interactively (type 'exit' to quit)
python ep02/rag.py data/acme/pdfs/handbook.pdf
```

## How it works

| Function | What it does |
|---|---|
| `load_pdf()` | Extracts text per page with `pypdf`, keeping page numbers for citations |
| `chunk()` | Sliding window: 800 characters, 150 characters of overlap → 27 chunks for the handbook |
| `embed()` | `nomic-embed-text` via Ollama → one 768-number vector per chunk |
| `retrieve()` | Cosine similarity between the question and every chunk, top 4 |
| `answer()` | Builds the grounded prompt and calls `generate()` from [`llm.py`](llm.py) |

## Use Claude or OpenAI instead

```bash
cp .env.example .env
# edit .env:  LLM_PROVIDER=anthropic  (or openai) and add your API key
python ep02/rag.py data/acme/pdfs/handbook.pdf
```

Embeddings stay local with Ollama. Only the retrieved chunks and your question are sent to the cloud model.

## The mistake we saw in the video

Asked about Enterprise refunds, `llama3.2` (3B) added *"Enterprise annual contracts are refunded pro rata within the first 90 days only"*. That rule belongs to **Business** plans. The naive chunker cut the Business sentence in half right after the Enterprise rules, and the small model attached it to the wrong plan.

Known limits, fixed in later episodes:
- Re-embeds the whole PDF on every start → **EP03** (vector database)
- Fixed-size chunks that split sentences and words, plus footer noise → **EP04**
- One PDF only → **EP05–08** (Word, email, Slack, one pipeline)

LLM output varies between runs and models, so your answers may differ slightly from the video.
