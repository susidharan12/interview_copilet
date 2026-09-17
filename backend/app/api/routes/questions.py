from __future__ import annotations

from fastapi import APIRouter

from app.schemas.question import ClassifyRequest, ClassificationResult
from app.services.classification import QuestionClassifier

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/classify", response_model=ClassificationResult)
async def classify(body: ClassifyRequest) -> ClassificationResult:
    classifier = QuestionClassifier()
    return await classifier.classify(
        body.question_text,
        previous=body.context.previous_questions,
    )