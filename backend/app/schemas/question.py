from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class QuestionCategory(str, Enum):
    TECHNICAL = "technical"
    CODING = "coding"
    DEBUGGING = "debugging"
    SYSTEM_DESIGN = "system_design"
    ARCHITECTURE = "architecture"
    SCENARIO = "scenario"
    BEHAVIORAL = "behavioral"
    PROJECT = "project"
    RESUME = "resume"
    SQL = "sql"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"
    UNKNOWN = "unknown"


class QuestionContext(BaseModel):
    session_id: uuid.UUID | None = None
    previous_questions: list[str] = []
    technologies_discussed: list[str] = []


class ClassificationResult(BaseModel):
    category: QuestionCategory
    technology: str | None = None
    difficulty: str | None = None
    requires_retrieval: bool = True
    requires_reasoning: bool = True
    requires_code_execution: bool = False
    requires_screen_context: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ClassifyRequest(BaseModel):
    question_text: str = Field(min_length=1)
    context: QuestionContext = Field(default_factory=QuestionContext)


class QuestionOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    text: str
    category: str
    technology: str | None
    difficulty: str | None
    requires_retrieval: bool
    requires_reasoning: bool
    requires_code_execution: bool
    requires_screen_context: bool
    confidence: float
    classification_metadata: dict[str, Any]
    created_at: Any = None