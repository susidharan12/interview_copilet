from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.session import AnswerMode


class AnswerGenerateRequest(BaseModel):
    session_id: uuid.UUID
    question_text: str = Field(min_length=1)
    classification: dict[str, Any] | None = None
    mode: AnswerMode = AnswerMode.INTERVIEW
    stream: bool = True


class SourceRef(BaseModel):
    chunk_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    filename: str | None = None
    section: str | None = None
    score: float | None = None


class AnswerOut(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    content: str
    mode: str
    model_used: str
    token_count: int
    sources: list[dict[str, Any]]
    validation_result: dict[str, Any] | None
    confidence: float | None
    latency_ms: int | None
    first_token_ms: int | None