from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    answer_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
    tags: list[str] = []


class FeedbackOut(BaseModel):
    id: uuid.UUID
    answer_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    comment: str | None
    tags: list[str]
    created_at: str