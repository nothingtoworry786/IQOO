#!/usr/bin/env python3
"""
migrate_to_chroma_cloud.py — Copy local persistent Chroma data into Chroma Cloud.

Reads the old local ChromaDB at CHROMADB_PATH and re-indexes every document
into Chroma Cloud, where it is re-embedded with the hybrid Qwen (dense) +
Splade (sparse) schema. Documents over 16 KiB are line-chunked.

Collection mapping:
  • "marketwatch_knowledge"  →  "kb_default"   (RAG default shard)
  • "competitor_<id>"        →  same name      (per-competitor signal store)
  • anything else            →  same name

Run from the Backend directory:
    python migrate_to_chroma_cloud.py
"""

from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
log = logging.getLogger("migrate")


def _target_name(local_name: str) -> str:
    if local_name == "marketwatch_knowledge":
        return "kb_default"
    return local_name


def main() -> None:
    import chromadb
    from app.core.config import settings
    from app.services import chroma_cloud as cc

    log.info("═══ Chroma local → Chroma Cloud migration ═══\n")

    # ── Local source ──────────────────────────────────────────────────────────
    local_path = settings.CHROMADB_PATH
    if not Path(local_path).exists():
        log.warning("No local Chroma data at %s — nothing to migrate.", local_path)
        return

    local = chromadb.PersistentClient(path=local_path)
    local_collections = local.list_collections()
    if not local_collections:
        log.warning("Local Chroma has no collections — nothing to migrate.")
        return

    # ── Cloud target ──────────────────────────────────────────────────────────
    cloud = cc.get_client()

    grand_total = 0
    for lc in local_collections:
        try:
            data = lc.get(include=["documents", "metadatas"])
        except Exception as exc:
            log.warning("  %-32s read failed: %s", lc.name, exc)
            continue

        ids = data.get("ids") or []
        documents = data.get("documents") or []
        metadatas = data.get("metadatas") or [{} for _ in ids]
        if not ids:
            log.info("  %-32s empty — skipped", lc.name)
            continue

        target = _target_name(lc.name)
        cloud_coll = cloud.get_or_create_collection(name=target, schema=cc.build_schema())

        out_ids: list[str] = []
        out_docs: list[str] = []
        out_metas: list[dict] = []
        for doc_id, doc, meta in zip(ids, documents, metadatas):
            if not doc:
                continue
            meta = dict(meta or {})
            for idx, chunk in enumerate(cc.chunk_text(doc)):
                out_ids.append(f"{doc_id}::c{idx}")
                out_docs.append(chunk)
                out_metas.append({
                    **meta,
                    cc.SOURCE_DOC_KEY: str(doc_id),
                    cc.CHUNK_INDEX_KEY: idx,
                })

        # Upsert in batches to respect payload limits.
        BATCH = 100
        for i in range(0, len(out_ids), BATCH):
            cloud_coll.upsert(
                ids=out_ids[i : i + BATCH],
                documents=out_docs[i : i + BATCH],
                metadatas=out_metas[i : i + BATCH],
            )

        log.info("  %-32s → %-28s %d docs → %d chunks",
                 lc.name, target, len(ids), len(out_ids))
        grand_total += len(out_ids)

    log.info("\n═══ Migration complete — %d chunks indexed into Chroma Cloud ═══", grand_total)


if __name__ == "__main__":
    main()
