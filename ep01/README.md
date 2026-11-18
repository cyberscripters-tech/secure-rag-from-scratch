# EP01: What is RAG and why it matters

Concept episode: no project code yet. This folder has the two snippets shown on screen:

- [`rag_preview.py`](rag_preview.py): the core of RAG in ~20 lines (embed → cosine similarity → top-k → prompt → LLM)
- [`llm_providers.py`](llm_providers.py): one `generate(prompt)` function backed by **Ollama**, **OpenAI** or **Claude**, picked by `LLM_PROVIDER`

Captions for the video: [`../assets/ep01_captions.srt`](../assets/ep01_captions.srt)

**Next:** EP02, where we write a working RAG from an empty folder to answering questions from a PDF.
