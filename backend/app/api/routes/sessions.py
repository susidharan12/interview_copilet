from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, RedisDep, get_current_user_id
from app.models.models import InterviewSession
from app.schemas.session import SessionCreate, SessionOut, SessionUpdate

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(body: SessionCreate, db: DbSession, cache: RedisDep) -> SessionOut:
    user_id = await get_current_user_id()
    session = InterviewSession(
        job_profile_id=body.job_profile_id,
        mode=body.mode,
        settings=body.settings.model_dump(),
        status="active",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    await cache.set(f"session:{session.id}", session.status, ttl_seconds=3600)
    return SessionOut.model_validate(session)


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: uuid.UUID, db: DbSession) -> SessionOut:
    session = await db.get(InterviewSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionOut.model_validate(session)


@router.patch("/{session_id}", response_model=SessionOut)
async def update_session(session_id: uuid.UUID, body: SessionUpdate, db: DbSession) -> SessionOut:
    session = await db.get(InterviewSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if body.status is not None:
        session.status = body.status.value
    if body.mode is not None:
        session.mode = body.mode
    if body.settings is not None:
        session.settings = body.settings.model_dump()
    await db.commit()
    await db.refresh(session)
    return SessionOut.model_validate(session)