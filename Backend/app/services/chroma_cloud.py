"""Shared Chroma Cloud layer — client, hybrid schema, and search builders.

Every collection is created with a Schema that indexes the document twice:
  • DENSE  — Chroma Cloud Qwen embeddings   (key "#embedding")
  • SPARSE — Chroma Cloud Splade embeddings (key "sparse_embedding")

Queries fuse both rankings with Reciprocal Rank Fusion (RRF) for hybrid
search. Both rag.py (knowledge base, sharded by company) and
chromadb_service.py (per-competitor signal store) build on this module.

All chromadb calls are synchronous, so callers wrap them in asyncio.to_thread().
"""

from __future__ import annotations

import logging
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

# Metadata/index keys.
SPARSE_KEY = "sparse_embedding"
SOURCE_DOC_KEY = "source_document_id"   # for GroupBy chunk dedup
CHUNK_INDEX_KEY = "chunk_index"

# Chroma's hard per-document limit is 16 KiB; chunk well under it.
MAX_DOC_BYTES = 12_000

_client = None
_qwen_ef = None
_splade_ef = None


def _ensure_api_key() -> None:
    if settings.CHROMA_API_KEY:
        os.environ.setdefault("CHROMA_API_KEY", settings.CHROMA_API_KEY)


def get_client():
    """Return a singleton Chroma Cloud client."""
    global _client
    if _client is None:
        import chromadb
        _ensure_api_key()
        if not (settings.CHROMA_TENANT and settings.CHROMA_DATABASE and settings.CHROMA_API_KEY):
            raise RuntimeError(
                "Chroma Cloud not configured — set CHROMA_TENANT, CHROMA_DATABASE, "
                "and CHROMA_API_KEY in .env."
            )
        _client = chromadb.CloudClient(
            tenant=settings.CHROMA_TENANT,
            database=settings.CHROMA_DATABASE,
            api_key=settings.CHROMA_API_KEY,
            cloud_host=settings.CHROMA_HOST or "api.trychroma.com",
        )
        logger.info(
            "Chroma Cloud client initialised (tenant=%s, database=%s, host=%s)",
            settings.CHROMA_TENANT[:8], settings.CHROMA_DATABASE, settings.CHROMA_HOST,
        )
    return _client


def _qwen():
    """Dense embedding function — Chroma Cloud Qwen."""
    global _qwen_ef
    if _qwen_ef is None:
        from chromadb.utils.embedding_functions import ChromaCloudQwenEmbeddingFunction
        from chromadb.utils.embedding_functions.chroma_cloud_qwen_embedding_function import (
            ChromaCloudQwenEmbeddingModel,
        )
        _ensure_api_key()
        _qwen_ef = ChromaCloudQwenEmbeddingFunction(
            model=ChromaCloudQwenEmbeddingModel.QWEN3_EMBEDDING_0p6B,
            task=None,  # general natural-language retrieval
        )
    return _qwen_ef


def _splade():
    """Sparse embedding function — Chroma Cloud Splade."""
    global _splade_ef
    if _splade_ef is None:
        from chromadb.utils.embedding_functions import ChromaCloudSpladeEmbeddingFunction
        _ensure_api_key()
        _splade_ef = ChromaCloudSpladeEmbeddingFunction()
    return _splade_ef


def build_schema():
    """Build a hybrid Schema: dense (Qwen) + sparse (Splade), both from the document."""
    from chromadb import Schema, VectorIndexConfig, SparseVectorIndexConfig, K

    schema = Schema()
    # Dense vector index at the default "#embedding" key, embedded from the document.
    schema.create_index(
        config=VectorIndexConfig(
            space="cosine",
            embedding_function=_qwen(),
            source_key=K.DOCUMENT,
        ),
        key=K.EMBEDDING,
    )
    # Sparse vector index at "sparse_embedding", also embedded from the document.
    schema.create_index(
        config=SparseVectorIndexConfig(
            embedding_function=_splade(),
            source_key=K.DOCUMENT,
        ),
        key=SPARSE_KEY,
    )
    return schema


async def get_or_create(name: str):
    """Get/create a cloud collection with the hybrid schema."""
    import asyncio

    client = get_client()
    schema = build_schema()
    return await asyncio.to_thread(
        lambda: client.get_or_create_collection(name=name, schema=schema)
    )


def build_hybrid_search(
    query: str,
    *,
    limit: int = 8,
    candidate_limit: int = 200,
    group_key: str | None = SOURCE_DOC_KEY,
    weights: tuple[float, float] = (0.7, 0.3),
):
    """Build a hybrid (dense+sparse RRF) Search, optionally de-duped via GroupBy.

    group_key: when set, collapses multiple chunks of the same source document
    to a single best-scoring result.
    """
    from chromadb import Search, K, Knn, Rrf
    from chromadb.execution.expression.operator import GroupBy, MinK

    dense = Knn(query=query, key=K.EMBEDDING, limit=candidate_limit, return_rank=True)
    sparse = Knn(query=query, key=K(SPARSE_KEY), limit=candidate_limit, return_rank=True)
    hybrid = Rrf(ranks=[dense, sparse], weights=list(weights), k=60)

    search = Search().rank(hybrid)

    if group_key:
        search = search.group_by(
            GroupBy(keys=K(group_key), aggregate=MinK(keys=K.SCORE, k=1))
        )
        search = search.limit(limit).select(K.DOCUMENT, K.SCORE, K(group_key))
    else:
        search = search.limit(limit).select(K.DOCUMENT, K.SCORE)

    return search


def chunk_text(text: str, max_bytes: int = MAX_DOC_BYTES) -> list[str]:
    """Line-based chunking for documents over Chroma's 16 KiB limit.

    Accumulates whole lines until the next line would exceed max_bytes, then
    starts a new chunk. Returns [text] unchanged when it already fits.
    """
    if len(text.encode("utf-8")) <= max_bytes:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for line in text.splitlines(keepends=True):
        line_bytes = len(line.encode("utf-8"))
        if size + line_bytes > max_bytes and current:
            chunks.append("".join(current))
            current, size = [], 0
        # A single line longer than the limit — hard-split it.
        if line_bytes > max_bytes:
            raw = line.encode("utf-8")
            for i in range(0, len(raw), max_bytes):
                chunks.append(raw[i : i + max_bytes].decode("utf-8", "ignore"))
            continue
        current.append(line)
        size += line_bytes
    if current:
        chunks.append("".join(current))
    return chunks
