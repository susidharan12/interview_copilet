from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class AnswerMode(str, Enum):
    QUICK = "quick"
    INTERVIEW = "interview"
    SENIOR = "senior"
    CODING = "coding"
    SCENARIO = "scenario"


class SessionSettings(BaseModel):
    enable_screen_capture: bool = False
    answer_mode: AnswerMode = AnswerMode.INTERVIEW
    language: str = "en"


class SessionCreate(BaseModel):
    job_profile_id: uuid.UUID | None = None
    mode: str = "interview"
    settings: SessionSettings = Field(default_factory=SessionSettings)


class SessionUpdate(BaseModel):
    status: SessionStatus | None = None
    mode: str | None = None
    settings: SessionSettings | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    job_profile_id: uuid.UUID | None
    status: str
    mode: str
    settings: dict[str, Any]
    started_at: datetime
    ended_at: datetime | None
    turn_count: int