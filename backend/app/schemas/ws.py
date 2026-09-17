from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.session import AnswerMode


class ClientEvent(BaseModel):
    type: str
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AudioChunkPayload(BaseModel):
    data: str
    format: str = "pcm_s16le"
    sample_rate: int = 16000
    timestamp: int | None = None


class ScreenFramePayload(BaseModel):
    data: str
    width: int
    height: int
    timestamp: int | None = None


class ModeSwitchPayload(BaseModel):
    mode: AnswerMode


class FeedbackPayload(BaseModel):
    answer_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ServerEvent(BaseModel):
    type: str
    request_id: str | None = None
    timestamp: str
    payload: dict[str, Any] = Field(default_factory=dict)


class PipelineStatus(BaseModel):
    stage: Literal[
        "listening", "transcribing", "detecting", "classifying",
        "retrieving", "thinking", "validating", "answering",
    ]
    message: str = ""


class TranscriptionSegment(BaseModel):
    text: str
    confidence: float = 0.0
    speaker: str | None = None
    is_final: bool = False