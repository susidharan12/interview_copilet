from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import CacheService
from app.core.telemetry import trace_span
from app.models.models import RetrievalTrace
from app.services.retrieval.indexer import EmbeddingService
from app.services.retrieval.reranker import build_reranker
from app.services.retrieval.rrf import RetrievalCandidate, rrf_fuse
from app.services.retrieval.vector import BM25Retriever, VectorRetriever


class RAGPipeline:
    """Hybrid retrieval: BM25 ∥ vector → RRF → rerank → context."""

    def __init__(
        self,
        session: AsyncSession,
        cache: CacheService | None = None,
        embedding: EmbeddingService | None = None,
    ) -> None:
        self.session = session
        self.cache = cache
        self.embedding = embedding or EmbeddingService(cache=cache)
        self.bm25 = BM25Retriever(session, cache)
        self.vector = VectorRetriever(session, cache)
        self.reranker = build_reranker()

    async def retrieve(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        top_k: int = 20,
    ) -> tuple[list[RetrievalCandidate], dict[str, Any]]:
        trace: dict[str, Any] = {"start": time.time()}
        cache_key = f"rag:{_cache_key(query, filters)}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                import json
                trace["cache_hit"] = True
                return _from_json(json.loads(cached)), trace

        embedding = await self.embedding.embed_query(query)

        async with trace_span("rag.retrieve", {"query": query[:80]}) as span:
            bm25_task = self.bm25.retrieve(query, filters, top_k=20)
            vector_task = self.vector.retrieve(embedding, filters, top_k=20)
            bm25_results, vector_results = await asyncio.gather(bm25_task, vector_task)
            span.set_attribute("bm25.count", len(bm25_results))
            span.set_attribute("vector.count", len(vector_results))

        fused = rrf_fuse([bm25_results, vector_results])
        selected = await self.reranker.rerank(query, fused, top_n=settings.rerank_top_n)

        trace.update(
            {
                "bm25_results": [_cand_dict(c) for c in bm25_results[:5]],
                "vector_results": [_cand_dict(c) for c in vector_results[:5]],
                "rrf_results": [_cand_dict(c) for c in fused[:10]],
                "reranked_results": [_cand_dict(c) for c in selected],
                "final_chunk_ids": [c.chunk_id for c in selected],
                "latency_ms": int((time.time() - trace["start"]) * 1000),
            }
        )

        if self.cache:
            await self.cache.set(cache_key, _to_json(selected), ttl_seconds=300)

        return selected, trace

    async def persist_trace(self, question_id: uuid.UUID, query_text: str, trace: dict[str, Any]) -> None:
        if not question_id:
            return
        row = RetrievalTrace(
            question_id=question_id,
            query_text=query_text,
            bm25_results=trace.get("bm25_results", []),
            vector_results=trace.get("vector_results", []),
            rrf_results=trace.get("rrf_results", []),
            reranked_results=trace.get("reranked_results", []),
            final_chunk_ids=trace.get("final_chunk_ids", []),
            latency_ms=trace.get("latency_ms"),
        )
        self.session.add(row)

    def build_context(self, candidates: list[RetrievalCandidate], token_budget: int | None = None) -> str:
        budget = token_budget or settings.rag_token_budget
        parts = []
        used = 0
        for c in candidates:
            tokens = len(c.content.split()) // 1
            if used + tokens > budget:
                break
            parts.append(f"[{_short(c.document_id)}] {c.content}")
            used += tokens
        return "\n\n".join(parts)


def _cache_key(query: str, filters: dict | None) -> str:
    import hashlib
    raw = query + "|" + str(sorted((filters or {}).items()))
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _cand_dict(c: RetrievalCandidate) -> dict[str, Any]:
    return {
        "chunk_id": c.chunk_id,
        "document_id": c.document_id,
        "score": c.score,
        "content_preview": c.content[:200],
    }


def _to_json(cands: list[RetrievalCandidate]) -> list[dict[str, Any]]:
    return [
        {
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "content": c.content,
            "score": c.score,
            "metadata": c.metadata,
        }
        for c in cands
    ]


def _from_json(data: list[dict[str, Any]]) -> list[RetrievalCandidate]:
    return [
        RetrievalCandidate(
            chunk_id=d["chunk_id"],
            document_id=d["document_id"],
            content=d["content"],
            score=d["score"],
            metadata=d.get("metadata", {}),
        )
        for d in data
    ]


def _short(uid: str) -> str:
    return uid.split("-")[0] if uid else "?"