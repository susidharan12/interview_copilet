from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    technology: list[str] | None = None
    document_type: list[str] | None = None
    project: str | None = None
    source: str | None = None
    section: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    filters: SearchFilters = Field(default_factory=SearchFilters)
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    chunk_id: uuid.UUID
    content: str
    score: float
    source: dict[str, Any]
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    query_id: uuid.UUID
    latency_ms: int
    strategy: str