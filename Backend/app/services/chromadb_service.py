"""ChromaDB service — local persistent vector store for competitor signals.

Collection naming: f"competitor_{competitor_id}"
All chromadb calls are synchronous; wrapped in asyncio.to_thread().
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        import chromadb
        _client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
        logger.info("ChromaDB client initialised at %s", settings.CHROMADB_PATH)
    return _client


def _collection_name(competitor_id: str) -> str:
    # ChromaDB collection names: letters, numbers, hyphens, underscores only
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in competitor_id)
    return f"competitor_{safe}"


async def get_or_create_collection(competitor_id: str):
    client = _get_client()
    name = _collection_name(competitor_id)
    return await asyncio.to_thread(lambda: client.get_or_create_collection(name))


async def add_signals(competitor_id: str, signals: list[dict[str, Any]]) -> None:
    """Embed and store signals in the competitor's ChromaDB collection."""
    if not signals:
        return
    try:
        collection = await get_or_create_collection(competitor_id)

        documents = [
            f"{s.get('type', '')} | {s.get('title', '')} | {s.get('description', '')}"
            for s in signals
        ]
        ids = [str(s.get("id", i)) for i, s in enumerate(signals)]
        metadatas = [
            {
                "type": str(s.get("type", "")),
                "intent_score": int(s.get("intent_score", 0)),
                "source": str(s.get("source", "")),
            }
            for s in signals
        ]

        def _add():
            # Upsert to avoid duplicate-id errors on re-runs
            collection.upsert(
                documents=documents,
                ids=ids,
                metadatas=metadatas,
            )

        await asyncio.to_thread(_add)
        logger.debug("ChromaDB: stored %d signals for competitor %s", len(signals), competitor_id)

    except Exception as exc:
        logger.warning("ChromaDB add_signals failed for %s: %s", competitor_id, exc)


async def query_similar(
    competitor_id: str,
    query: str,
    n_results: int = 5,
) -> list[str]:
    """Return document strings most similar to query."""
    try:
        collection = await get_or_create_collection(competitor_id)
        results = await asyncio.to_thread(
            lambda: collection.query(query_texts=[query], n_results=n_results)
        )
        docs = results.get("documents", [[]])[0]
        return docs
    except Exception as exc:
        logger.warning("ChromaDB query failed for %s: %s", competitor_id, exc)
        return []


async def delete_collection(competitor_id: str) -> None:
    try:
        client = _get_client()
        name = _collection_name(competitor_id)
        await asyncio.to_thread(lambda: client.delete_collection(name))
    except Exception as exc:
        logger.warning("ChromaDB delete_collection failed for %s: %s", competitor_id, exc)
