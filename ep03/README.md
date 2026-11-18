# EP03: Embeddings & vector databases

Two upgrades over EP02:
1. **Pick the embedding model with data**: a 25-question retrieval test set and a benchmark script.
2. **Store vectors in Qdrant**: index once, then answer questions in about a second without re-embedding.

## 1. Compare embedding models

```bash
ollama pull all-minilm
ollama pull nomic-embed-text
ollama pull bge-m3
ollama pull mxbai-embed-large
python ep03/compare_models.py
```

Our results on the Acme handbook (27 chunks, 25 questions, 2-core test VM, warm models):

| model | prefix | dims | hit@1 | hit@4 | MRR | index s |
|---|---|---|---|---|---|---|
| all-minilm | no | 384 | 72% | 100% | 0.85 | 0.7 |
| nomic-embed-text | no | 768 | 88% | 100% | 0.92 | 6.8 |
| nomic-embed-text | yes | 768 | 88% | 100% | 0.93 | 7.0 |
| mxbai-embed-large | no | 1024 | 96% | 100% | 0.97 | 16.3 |
| mxbai-embed-large | yes | 1024 | 96% | 100% | 0.97 | 15.3 |
| bge-m3 | no | 1024 | 92% | 100% | 0.96 | 17.6 |

- **hit@1**: the top chunk comes from the right page
- **hit@4**: a right page is among the 4 chunks sent to the LLM
- **MRR**: mean of 1 / rank of the first correct chunk

25 questions is a small test (one question = 4%). Run it on **your** documents before choosing. From EP03 on, the default is `EMBED_MODEL=mxbai-embed-large`; set `EMBED_MODEL` to switch.

## 2. Index once, ask fast

```bash
ollama pull mxbai-embed-large
python ep03/index.py data/acme/pdfs/handbook.pdf      # builds index/qdrant/
python ep03/ask.py "What's the refund policy for enterprise customers?"
python ep03/ask.py                                     # interactive
```

| | time to first retrieval (median of 3) |
|---|---|
| EP02 (re-embed on every start) | 7.3 s |
| EP03 (load from Qdrant) | 1.0 s |

- Qdrant runs **embedded** (`QdrantClient(path="index/qdrant")`): no server needed. For production, run `docker run -p 6333:6333 qdrant/qdrant` and use `QdrantClient(url="http://localhost:6333")`.
- Point IDs are deterministic (`uuid5(file#chunk)`), so re-indexing a file overwrites instead of duplicating.
- `index/meta.json` records the embedding model; `ask.py` refuses to run if `EMBED_MODEL` doesn't match.

## Security note

Embeddings are **not** anonymised: embedding-inversion research ([Morris et al., EMNLP 2023](https://arxiv.org/abs/2310.06816)) reconstructed 92% of 32-token inputs exactly. Our payload stores the original text anyway, so protect `index/` like the source documents. It's excluded by `.gitignore`.
