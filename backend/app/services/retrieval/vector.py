from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import CacheService
from app.models.models import DocumentChunk
from app.services.retrieval.rrf import RetrievalCandidate


class BM25Retriever:
    """Lexical retrieval over document chunks.

    Uses a deterministic bag-of-words BM25 scorer. In production this can be
    swapped for PostgreSQL FTS / tsvector-gin index; the interface stays the
    same so retrieval quality is evaluable offline.
    """

    def __init__(self, session: AsyncSession, cache: CacheService | None = None) -> None:
        self.session = session
        self.cache = cache
        self.k1 = 1.5
        self.b = 0.75
        self._token_cache: dict[str, list[str]] = {}

    async def retrieve(
        self, query: str, filters: dict | None = None, top_k: int = 20
    ) -> list[RetrievalCandidate]:
        q_tokens = self._tokens(query.lower())
        chunks = await self._load_chunks(filters)
        scored = [(self._score(q_tokens, self._tokens(c.content.lower())), c) for c in chunks]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            RetrievalCandidate(
                chunk_id=str(c.id),
                document_id=str(c.document_id),
                content=c.content,
                score=score,
                metadata=c.metadata_json or {},
            )
            for score, c in scored[:top_k]
        ]

    async def _load_chunks(self, filters: dict | None) -> list[DocumentChunk]:
        stmt = select(DocumentChunk).limit(500)
        if filters:
            where = []
            if filters.get("document_type"):
                where.append(
                    text("metadata_json->>'document_type' = ANY(:types)").bindparams(
                        types=filters["document_type"]
                    )
                )
            if filters.get("project"):
                where.append(text("metadata_json->>'project' = :project").bindparams(project=filters["project"]))
            if where:
                stmt = stmt.where(*where)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _tokens(self, text: str) -> list[str]:
        if text not in self._token_cache:
            import re
            self._token_cache[text] = re.findall(r"[a-z0-9_+#.]+", text)
        return self._token_cache[text]

    def _score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        if not doc_tokens:
            return 0.0
        n = len(doc_tokens)
        avgdl = max(n, 1.0)
        score = 0.0
        df: dict[str, int] = {}
        for t in query_tokens:
            df[t] = df.get(t, 0) + 1
        for token in query_tokens:
            freq = doc_tokens.count(token)
            if freq == 0:
                continue
            tf = (freq * (self.k1 + 1)) / (freq + self.k1 * (1 - self.b + self.b * n / avgdl))
            idf = max(0.0, (1 + 1) / (df[token] + 1))  # doc count approximated per token
            score += tf * idf
        return score


class VectorRetriever:
    """Semantic retrieval using pgvector cosine similarity."""

    def __init__(self, session: AsyncSession, cache: CacheService | None = None) -> None:
        self.session = session
        self.cache = cache

    async def retrieve(
        self,
        embedding: list[float],
        filters: dict | None = None,
        top_k: int = 20,
    ) -> list[RetrievalCandidate]:
        from sqlalchemy import text as sa_text

        stmt = (
            select(DocumentChunk)
            .order_by(DocumentChunk.embedding.cosine_distance(embedding).asc())
            .limit(top_k)
        )
        if filters:
            if filters.get("document_type"):
                stmt = stmt.where(
                    sa_text("metadata_json->>'document_type' = ANY(:types)").bindparams(
                        types=filters["document_type"]
                    )
                )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            RetrievalCandidate(
                chunk_id=str(c.id),
                document_id=str(c.document_id),
                content=c.content,
                score=0.0,  # rank-based; absolute similarity assigned at RRF
                metadata=c.metadata_json or {},
            )
            for c in rows
        ]