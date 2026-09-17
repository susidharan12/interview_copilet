from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class SandboxTestCase(BaseModel):
    input: str
    expected: str


class CodeExecuteRequest(BaseModel):
    language: str = Field(pattern="^(python|javascript|typescript|java|kotlin|cpp|sql)$")
    code: str = Field(min_length=1)
    test_cases: list[SandboxTestCase] = []
    timeout_seconds: int = Field(default=10, ge=1, le=60)


class TestResult(BaseModel):
    name: str
    passed: bool
    expected: str | None = None
    actual: str | None = None
    error: str | None = None


class CodeExecuteResponse(BaseModel):
    execution_id: uuid.UUID
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: int
    test_results: list[TestResult] | None = None
    resource_usage: dict[str, Any] | None = None
