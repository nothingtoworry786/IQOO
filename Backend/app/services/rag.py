"""RAG knowledge base on Chroma Cloud (hybrid dense + sparse search).

Data is SHARDED BY COMPANY — each company's competitive landscape (its own
profile + competitors + signals + predictions) lives in its own cloud
collection ("kb_<company-slug>"), so mutually-exclusive orgs never mix.

Retrieval uses hybrid search: Chroma Cloud Qwen (dense) + Splade (sparse)
fused with RRF, then GroupBy on source_document_id to de-duplicate chunks of
the same source document. Long documents are line-chunked under the 16 KiB
per-document limit.
"""

from __future__ import annotations

import asyncio
import logging
import re

from app.services import chroma_cloud as cc

logger = logging.getLogger(__name__)

DEFAULT_SHARD = "kb_default"


# ── Sharding ────────────────────────────────────────────────────────────────

def shard_name(company: str | None) -> str:
    """Collection name for a company's knowledge shard."""
    if not company or not company.strip():
        return DEFAULT_SHARD
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")
    return f"kb_{slug or 'default'}"


async def _resolve_shard(company: str | None) -> str:
    """Pick the shard to query. With an explicit company, use its shard;
    otherwise choose the most-populated existing kb_ shard."""
    if company and company.strip():
        return shard_name(company)
    try:
        client = cc.get_client()
        cols = await asyncio.to_thread(lambda: client.list_collections())
        kb = [c for c in cols if c.name.startswith("kb_")]
        if not kb:
            return DEFAULT_SHARD
        counts = await asyncio.gather(
            *[asyncio.to_thread(lambda c=c: (c.name, c.count())) for c in kb]
        )
        return max(counts, key=lambda x: x[1])[0]
    except Exception as exc:
        logger.warning("RAG _resolve_shard failed: %s", exc)
        return DEFAULT_SHARD


# ── Indexing ────────────────────────────────────────────────────────────────

async def index_documents(company: str | None, docs: list[dict]) -> int:
    """Upsert documents into a company's shard. Each doc = {id, text, metadata}.

    Documents over the 16 KiB limit are line-chunked; every chunk carries
    source_document_id + chunk_index metadata for GroupBy de-duplication.
    """
    docs = [d for d in docs if (d.get("text") or "").strip()]
    if not docs:
        return 0

    ids: list[str] = []
    texts: list[str] = []
    metas: list[dict] = []

    for d in docs:
        doc_id = str(d["id"])
        base_meta = dict(d.get("metadata") or {})
        chunks = cc.chunk_text(d["text"])
        for idx, chunk in enumerate(chunks):
            ids.append(f"{doc_id}::c{idx}")
            texts.append(chunk)
            metas.append({
                **base_meta,
                cc.SOURCE_DOC_KEY: doc_id,
                cc.CHUNK_INDEX_KEY: idx,
            })

    collection = await cc.get_or_create(shard_name(company))
    await asyncio.to_thread(
        lambda: collection.upsert(ids=ids, documents=texts, metadatas=metas)
    )
    logger.info("RAG: upserted %d chunks (%d docs) into shard '%s'",
                len(ids), len(docs), shard_name(company))
    return len(ids)


async def index_company_context(company: str, profile: dict) -> None:
    """Index the user's own company profile as the anchor 'OUR COMPANY' doc."""
    features = ", ".join(profile.get("key_features", []) or []) or "n/a"
    text = (
        f"OUR COMPANY: {company}. "
        f"Industry: {profile.get('industry', 'n/a')}. "
        f"Category/niche: {profile.get('sub_category', 'n/a')}. "
        f"Target customers: {profile.get('target_customers', 'n/a')}. "
        f"Geographic focus: {profile.get('geographic_focus', 'n/a')}. "
        f"Business model: {profile.get('business_model', 'n/a')}. "
        f"Key features: {features}."
    )
    try:
        await index_documents(company, [{
            "id": "company_context",
            "text": text,
            "metadata": {"kind": "company", "name": company},
        }])
        logger.info("RAG: indexed company context for '%s'", company)
    except Exception as exc:
        logger.warning("RAG index_company_context failed: %s", exc)


async def sync_from_db(company: str | None) -> int:
    """Rebuild a company's shard from competitors + signals + predictions in the DB."""
    from app.models.competitor import Competitor
    from app.models.signal import Signal
    from app.models.prediction import Prediction
    from app.services.database import async_session_factory
    from sqlalchemy import select, desc

    docs: list[dict] = []
    async with async_session_factory() as session:
        comps = (await session.execute(select(Competitor))).scalars().all()
        comp_by_id = {c.id: c for c in comps}

        for c in comps:
            docs.append({
                "id": f"comp_{c.id}",
                "text": (
                    f"COMPETITOR: {c.name}. Industry: {c.industry or 'n/a'}. "
                    f"Market scope: {c.market_scope or 'n/a'}. "
                    f"Website: {c.website or 'n/a'}."
                ),
                "metadata": {"kind": "competitor", "name": c.name},
            })

        signals = (
            await session.execute(select(Signal).order_by(desc(Signal.created_at)).limit(200))
        ).scalars().all()
        for s in signals:
            comp = comp_by_id.get(s.competitor_id)
            cname = comp.name if comp else "Unknown"
            docs.append({
                "id": f"sig_{s.id}",
                "text": (
                    f"SIGNAL [{s.signal_type.value}] about {cname}: {s.title}. "
                    f"{s.description or ''} (impact {s.impact_score:.1f}/10, "
                    f"urgency {s.urgency_score:.1f}/10)"
                ),
                "metadata": {"kind": "signal", "competitor": cname, "type": s.signal_type.value},
            })

        preds = (
            await session.execute(select(Prediction).order_by(desc(Prediction.created_at)).limit(50))
        ).scalars().all()
        for p in preds:
            comp = comp_by_id.get(p.competitor_id)
            cname = comp.name if comp else "Unknown"
            docs.append({
                "id": f"pred_{p.id}",
                "text": (
                    f"PREDICTION about {cname} [threat {p.threat_level}, "
                    f"{p.confidence}% confidence]: {p.prediction}. "
                    f"Reasoning: {p.ai_reasoning or ''}"
                ),
                "metadata": {"kind": "prediction", "competitor": cname},
            })

    n = await index_documents(company, docs)
    logger.info("RAG sync: indexed %d chunks into shard '%s'", n, shard_name(company))
    return n


# ── Retrieval ─────────────────────────────────────────────────────────────--

async def count(company: str | None = None) -> int:
    try:
        collection = await cc.get_or_create(await _resolve_shard(company))
        return await asyncio.to_thread(lambda: collection.count())
    except Exception:
        return 0


async def ensure_knowledge_base(company: str | None = None) -> None:
    """Populate a company's shard from the DB if it's currently empty."""
    try:
        if await count(company) == 0:
            await sync_from_db(company)
    except Exception as exc:
        logger.warning("RAG ensure_knowledge_base failed: %s", exc)


async def query_knowledge(query: str, company: str | None = None, n_results: int = 6) -> list[str]:
    """Hybrid (dense+sparse RRF) retrieval with chunk de-duplication.

    Returns the most relevant document strings for the query.
    """
    try:
        shard = await _resolve_shard(company)
        collection = await cc.get_or_create(shard)
        search = cc.build_hybrid_search(query, limit=n_results)
        result = await asyncio.to_thread(lambda: collection.search(search))

        rows = result.rows()
        rows = rows[0] if rows else []
        docs = [r.get("document") for r in rows if r.get("document")]
        logger.info("RAG query on '%s': %d results for %r", shard, len(docs), query[:60])
        return docs
    except Exception as exc:
        logger.warning("RAG query_knowledge failed: %s", exc)
        return []
