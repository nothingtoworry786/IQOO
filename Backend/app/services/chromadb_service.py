"""Per-competitor signal vector store on Chroma Cloud.

Each competitor's signals are sharded into their own cloud collection
("competitor_<id>") built with the shared hybrid schema (Qwen dense + Splade
sparse). Queries use hybrid RRF search. Backed by app.services.chroma_cloud.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.services import chroma_cloud as cc

logger = logging.getLogger(__name__)


def _collection_name(competitor_id: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in competitor_id)
    return f"competitor_{safe}"


async def get_or_create_collection(competitor_id: str):
    return await cc.get_or_create(_collection_name(competitor_id))


async def add_signals(competitor_id: str, signals: list[dict[str, Any]]) -> None:
    """Embed and store signals in the competitor's cloud collection."""
    if not signals:
        return
    try:
        collection = await get_or_create_collection(competitor_id)

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []
        for i, s in enumerate(signals):
            doc_id = str(s.get("id", i))
            text = f"{s.get('type', '')} | {s.get('title', '')} | {s.get('description', '')}"
            # Chunk under the 16 KiB limit (signals are short, usually 1 chunk).
            for idx, chunk in enumerate(cc.chunk_text(text)):
                ids.append(f"{doc_id}::c{idx}")
                documents.append(chunk)
                metadatas.append({
                    "type": str(s.get("type", "")),
                    "intent_score": int(s.get("intent_score", 0) or 0),
                    "source": str(s.get("source", "")),
                    cc.SOURCE_DOC_KEY: doc_id,
                    cc.CHUNK_INDEX_KEY: idx,
                })

        await asyncio.to_thread(
            lambda: collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        )
        logger.debug("Chroma Cloud: stored %d signal chunks for competitor %s",
                     len(ids), competitor_id)

    except Exception as exc:
        logger.warning("Chroma Cloud add_signals failed for %s: %s", competitor_id, exc)


async def query_similar(competitor_id: str, query: str, n_results: int = 5) -> list[str]:
    """Hybrid (dense+sparse) search for signals most similar to the query."""
    try:
        collection = await get_or_create_collection(competitor_id)
        search = cc.build_hybrid_search(query, limit=n_results)
        result = await asyncio.to_thread(lambda: collection.search(search))
        rows = result.rows()
        rows = rows[0] if rows else []
        return [r.get("document") for r in rows if r.get("document")]
    except Exception as exc:
        logger.warning("Chroma Cloud query failed for %s: %s", competitor_id, exc)
        return []


async def delete_collection(competitor_id: str) -> None:
    try:
        client = cc.get_client()
        name = _collection_name(competitor_id)
        await asyncio.to_thread(lambda: client.delete_collection(name))
    except Exception as exc:
        logger.warning("Chroma Cloud delete_collection failed for %s: %s", competitor_id, exc)
