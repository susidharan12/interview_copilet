from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.schemas.coding import CodeExecuteRequest, CodeExecuteResponse
from app.services.engines.sandbox import SandboxManager

router = APIRouter(prefix="/code", tags=["coding"])


@router.post("/execute", response_model=CodeExecuteResponse)
async def execute_code(body: CodeExecuteRequest) -> CodeExecuteResponse:
    sandbox = SandboxManager()
    result = await sandbox.execute(
        language=body.language,
        code=body.code,
        test_cases=body.test_cases,
        timeout_seconds=body.timeout_seconds,
    )
    return CodeExecuteResponse(
        execution_id=uuid.uuid4(),
        success=result.success,
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr=result.stderr,
        execution_time_ms=result.execution_time_ms,
        resource_usage=result.resource_usage,
    )