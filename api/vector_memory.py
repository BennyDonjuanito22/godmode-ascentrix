"""Vector memory built on Qdrant with OpenAI embeddings fallback."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - allow running without openai package
    OpenAI = None  # type: ignore

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

ROOT = Path(__file__).resolve().parent.parent
DESIGN_DOCS_DIR = ROOT / "design_docs"
NOTES_PATH = ROOT / "memory" / "notes.jsonl"
INDEX_PATH = ROOT / "memory" / "vector_index.jsonl"

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "memory_chunks")
EMBEDDING_MODEL = os.getenv("MEMORY_EMBEDDINGS_MODEL", "text-embedding-3-small")

_openai_client: "OpenAI" | None = None
_qdrant_client: QdrantClient | None = None


def _get_openai() -> OpenAI:
    global _openai_client
    if OpenAI is None:
        raise RuntimeError("OpenAI package is not installed or unavailable")
    global _openai_client
    if _openai_client is None:
        # OpenAI client will pick up API key from env in most modern SDKs
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set")
        _openai_client = OpenAI()
    return _openai_client


def _get_qdrant() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=QDRANT_URL)
    return _qdrant_client


def chunk_text(text: str, words_per_chunk: int = 200) -> Iterable[str]:
    words = text.split()
    if not words:
        return []
    for i in range(0, len(words), words_per_chunk):
        yield " ".join(words[i : i + words_per_chunk])


def iter_design_docs() -> Iterable[Tuple[str, str]]:
    if not DESIGN_DOCS_DIR.exists():
        return []
    for path in DESIGN_DOCS_DIR.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for idx, chunk in enumerate(chunk_text(text)):
            yield (f"design_doc::{path.relative_to(DESIGN_DOCS_DIR)}::{idx}", chunk)


def iter_notes() -> Iterable[Tuple[str, str]]:
    if not NOTES_PATH.exists():
        return []
    with NOTES_PATH.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = data.get("text", "")
            if not text:
                continue
            yield (f"note::{line_no}", text)


def _embed_batch(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    # Use OpenAI embeddings when configured; otherwise produce deterministic
    # lightweight fallback embeddings so local runs still function.
    if os.getenv("OPENAI_API_KEY") and OpenAI is not None:
        client = _get_openai()
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]

    # Fallback: deterministic hash-based embeddings (size=64)
    import hashlib

    vec_size = int(os.getenv("FALLBACK_EMBED_SIZE", "64"))
    out: List[List[float]] = []
    for t in texts:
        h = hashlib.sha256(t.encode("utf-8")).digest()
        # Expand digest to desired size by repeating
        rep = (h * ((vec_size * 4) // len(h) + 1))[: vec_size * 4]
        vals: List[float] = []
        for i in range(0, len(rep), 4):
            chunk = rep[i : i + 4]
            val = int.from_bytes(chunk, "big") / (2 ** 32)
            vals.append(val * 2.0 - 1.0)
            if len(vals) >= vec_size:
                break
        out.append(vals)
    return out


def build_index() -> Dict[str, int]:
    records: List[Dict[str, str]] = []
    for source, iterator in (("design_doc", iter_design_docs()), ("note", iter_notes())):
        for item_id, text in iterator:
            records.append({"id": item_id, "source": source, "text": text})

    if not records:
        return {"records": 0}

    # Attempt to build embeddings and upload to Qdrant; if Qdrant or OpenAI
    # are not available, fall back to writing a local JSONL index for searching.
    vectors = []
    batch_size = 16
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        vectors.extend(_embed_batch([item["text"] for item in batch]))

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        client = _get_qdrant()
        vector_size = len(vectors[0]) if vectors else 0
        client.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )

        points = []
        for record, vector in zip(records, vectors):
            points.append(
                qmodels.PointStruct(
                    id=record["id"],
                    vector=vector,
                    payload={"source": record["source"], "text": record["text"]},
                )
            )
        if points:
            client.upsert(collection_name=QDRANT_COLLECTION, wait=True, points=points)

        # Keep JSONL as fallback/reference.
        with INDEX_PATH.open("w", encoding="utf-8") as handle:
            for record, vector in zip(records, vectors):
                data = {**record, "embedding": vector}
                handle.write(json.dumps(data) + "\n")
    except Exception:
        # Qdrant or network not available — write JSONL without attempting upload.
        with INDEX_PATH.open("w", encoding="utf-8") as handle:
            for record, vector in zip(records, vectors):
                data = {**record, "embedding": vector}
                handle.write(json.dumps(data) + "\n")

    return {"records": len(records)}


def _fallback_search(query: str, limit: int) -> List[Dict[str, str]]:
    if not INDEX_PATH.exists():
        return []
    try:
        query_vector = _embed_batch([query])[0]
    except Exception:
        return []
    results: List[Dict[str, str]] = []
    with INDEX_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            embedding = data.get("embedding")
            if not embedding:
                continue
            # cosine similarity
            dot = sum(a * b for a, b in zip(query_vector, embedding))
            results.append(
                {"id": data["id"], "source": data["source"], "text": data["text"], "similarity": dot}
            )
    results.sort(key=lambda item: item["similarity"], reverse=True)
    return results[:limit]


def search_index(query: str, limit: int = 5) -> List[Dict[str, str]]:
    if not query.strip():
        return []
    try:
        qdrant = _get_qdrant()
        embedding = _embed_batch([query])[0]
        search_result = qdrant.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=embedding,
            limit=limit,
            with_payload=True,
        )
        return [
            {
                "id": point.id,
                "source": point.payload.get("source"),
                "text": point.payload.get("text"),
                "similarity": point.score,
            }
            for point in search_result
        ]
    except Exception:
        return _fallback_search(query, limit)
