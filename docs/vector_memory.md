# Vector Memory Pipeline Overview

To give God Mode richer recall, the repo now includes a lightweight vector index that ingests design docs and memory notes, chunking the content and storing bag-of-words embeddings in `memory/vector_index.jsonl`.

## Components

- `api/vector_memory.py`
  - `build_index()` reads `design_docs/*.md` and `memory/notes.jsonl`, chunks text (200-word windows), computes normalized term-frequency embeddings, and writes the index.
  - `search_index(query, limit)` loads the index and returns the most similar chunks using cosine similarity.
- API routes (FastAPI):
  - `POST /memory/ingest` – rebuilds the index, returning `{"records": <count>}`.
  - `GET /memory/search?query=...&limit=5` – returns matching snippets with similarity scores and source metadata.
- CLI helper `scripts/ingest_memory.py` triggers the ingest endpoint so operators/agents can refresh the index after editing docs or notes.

## Usage

1. Run `./scripts/ingest_memory.py` (or call `POST /memory/ingest`) whenever design docs or notes change.
2. Query via `GET /memory/search?query=vector memory` to surface relevant snippets (HUD and agents can display these results).
3. Update the HUD Logs/Memory screen to hit the new search endpoint; it currently uses placeholder data.

## Future Enhancements

- Swap bag-of-words embeddings for a real embedding model (OpenAI, local, etc.) and push vectors into Qdrant once GPU or service access is available.
- Include additional sources (logs, code comments) by extending `build_index`.
- Cache metadata (tags, file path) to make HUD filters richer.
- Schedule ingestion via autopilot so the index stays current automatically.
