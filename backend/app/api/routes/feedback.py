from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.models import Answer, Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackOut

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
async def create_feedback(body: FeedbackCreate, db: DbSession) -> FeedbackOut:
    answer = await db.get(Answer, body.answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Answer not found")
    fb = Feedback(
        answer_id=body.answer_id,
        user_id="00000000-0000-0000-0000-000000000000",
        rating=body.rating,
        comment=body.comment,
        tags=body.tags,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return FeedbackOut(
        id=fb.id,
        answer_id=fb.answer_id,
        user_id=fb.user_id,
        rating=fb.rating,
        comment=fb.comment,
        tags=fb.tags,
        created_at=str(fb.created_at),
    )