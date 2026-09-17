from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class DocumentType(str, Enum):
    RESUME = "resume"
    PROJECT = "project"
    NOTES = "notes"
    JOB_DESCRIPTION = "job_description"
    TECHNICAL = "technical"
    OTHER = "other"


class DocumentCreate(BaseModel):
    filename: str
    document_type: DocumentType = DocumentType.OTHER
    tags: list[str] = []
    project_name: str | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    document_type: str
    status: str
    chunk_count: int
    tags: list[str]
    project_name: str | None
    metadata_json: dict[str, Any]
    created_at: datetime


class DocumentIngestRequest(BaseModel):
    document_id: uuid.UUID


class DocumentIngestResponse(BaseModel):
    document_id: uuid.UUID
    status: str
    chunk_count: int
    queued: bool