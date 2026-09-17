from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

import httpx
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import CacheService
from app.models.models import DocumentChunk
from app.services.retrieval.rrf import RetrievalCandidate


class EmbeddingService:
    """Embedding provider with a deterministic cache layer.

    Caches query embeddings by (text hash) in Redis so repeated questions
    (common in interviews) avoid re-embedding.
    """

    def __init__(self, client: AsyncOpenAI | None = None, cache: CacheService | None = None) -> None:
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self.cache = cache

    async def embed_query(self, text: str) -> list[float]:
        key = f"emb:q:{self._hash(text)}"
        if self.cache:
            cached = await self.cache.get(key)
            if cached:
                return json.loads(cached)
        try:
            resp = await self._client.embeddings.create(
                model=settings.embedding_model,
                input=text,
            )
            vec = resp.data[0].embedding
        except Exception:
            vec = self._fallback_embedding(text)
        if self.cache:
            await self.cache.set(key, json.dumps(vec), ttl_seconds=3600)
        return vec

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            resp = await self._client.embeddings.create(
                model=settings.embedding_model,
                input=texts[:100],
            )
            return [d.embedding for d in resp.data]
        except Exception:
            return [self._fallback_embedding(t) for t in texts]

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    @staticmethod
    def _fallback_embedding(text: str) -> list[float]:
        """Deterministic feature-hashed mock embedding for offline dev/tests."""
        dim = settings.embedding_dimensions
        vec = [0.0] * dim
        for token in text.lower().split():
            h = int(hashlib.sha256(token.encode()).hexdigest(), 16)
            vec[h % dim] += 1.0
        norm = (sum(v * v for v in vec) ** 0.5) or 1.0
        return [v / norm for v in vec]


class ChunkIndexer:
    """Builds chunks + embeddings for a document and writes to the DB."""

    def __init__(self, session: AsyncSession, embedding: EmbeddingService) -> None:
        self.session = session
        self.embedding = embedding

    async def index(
        self,
        document_id: uuid.UUID,
        chunks: list[dict[str, Any]],
        metadata_template: dict[str, Any],
    ) -> int:
        texts = [c["content"] for c in chunks]
        vectors = await self.embedding.embed_documents(texts)
        for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
            meta = dict(metadata_template)
            meta.update(chunk.get("metadata", {}))
            row = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                content=chunk["content"],
                embedding=vec,
                metadata_json=meta,
                token_count=len(chunk["content"].split()),
            )
            self.session.add(row)
        await self.session.flush()
        return len(chunks)


def estimate_tokens(text: str) -> int:
    return len(text) // 4