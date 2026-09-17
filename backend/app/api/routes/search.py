from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import DbSession, RedisDep
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from app.services.retrieval.hybrid import RAGPipeline

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(body: SearchRequest, db: DbSession, cache: RedisDep) -> SearchResponse:
    start = time.monotonic()
    rag = RAGPipeline(db, cache)
    candidates, trace = await rag.retrieve(
        body.query,
        filters=body.filters.model_dump(exclude_none=True),
        top_k=body.top_k,
    )
    result_items = [
        SearchResultItem(
            chunk_id=uuid.UUID(c.chunk_id),
            content=c.content,
            score=c.score,
            source={
                "document_id": c.document_id,
                "metadata": c.metadata,
            },
            metadata=c.metadata,
        )
        for c in candidates
    ]
    return SearchResponse(
        results=result_items,
        query_id=uuid.uuid4(),
        latency_ms=int((time.monotonic() - start) * 1000),
        strategy="hybrid_bm25_vector_rrf_rerank",
    )