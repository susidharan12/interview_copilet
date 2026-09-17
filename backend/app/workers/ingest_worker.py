from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.redis import get_redis
from app.models.models import Document
from app.services.retrieval.indexer import ChunkIndexer, EmbeddingService
from app.services.retrieval.retrieval_chunk import chunk_document


async def ingest_pending_documents() -> int:
    """Process documents with status=pending. Runs as a background worker loop."""
    processed = 0
    async with async_session_factory() as db:
        result = await db.execute(
            select(Document).where(Document.status == "pending").limit(10)
        )
        docs = list(result.scalars().all())
        if not docs:
            return 0
        indexer = ChunkIndexer(db, EmbeddingService())
        for doc in docs:
            doc.status = "processing"
            await db.flush()
            chunks = chunk_document(
                doc.content or "",
                meta={
                    "document_id": str(doc.id),
                    "filename": doc.filename,
                    "document_type": doc.document_type,
                    "project": doc.project_name,
                    "tags": doc.tags,
                },
            )
            count = await indexer.index(
                document_id=doc.id,
                chunks=chunks,
                metadata_template={
                    "document_id": str(doc.id),
                    "filename": doc.filename,
                    "document_type": doc.document_type,
                    "project": doc.project_name,
                    "tags": doc.tags,
                },
            )
            doc.chunk_count = count
            doc.status = "ready"
            processed += 1
        await db.commit()
    return processed


async def worker_loop(interval_seconds: int = 15) -> None:
    cache = await get_redis()
    while True:
        try:
            count = await ingest_pending_documents()
            if count:
                await cache.set("worker:last_ingest_count", str(count), 5)
        except Exception:
            pass
        await asyncio.sleep(interval_seconds)