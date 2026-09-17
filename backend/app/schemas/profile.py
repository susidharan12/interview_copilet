from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    name: str | None = None
    resume_summary: str | None = None
    skills: list[str] | None = None
    experience_years: int | None = None
    target_role: str | None = None
    education: list[dict[str, Any]] | None = None
    certifications: list[str] | None = None


class ProjectInfo(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = []
    highlights: list[str] = []


class ProfileOut(BaseModel):
    user_id: uuid.UUID
    name: str
    resume_summary: str | None = None
    skills: list[str]
    projects: list[ProjectInfo]
    experience_years: int | None = None
    target_role: str | None = None
    education: list[dict[str, Any]]
    certifications: list[str]


class JobProfileCreate(BaseModel):
    company: str
    role: str
    requirements: list[str] = []
    technologies: list[str] = []
    description: str | None = None
    notes: str | None = None


class JobProfileOut(JobProfileCreate):
    id: uuid.UUID
    user_id: uuid.UUID