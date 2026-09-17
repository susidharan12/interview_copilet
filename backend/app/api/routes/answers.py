from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import DbSession, RedisDep
from app.schemas.answer import AnswerGenerateRequest, AnswerOut
from app.schemas.session import AnswerMode
from app.services.composer import AnswerComposer
from app.services.engines.answer_engine import AnswerEngine
from app.services.memory import ConversationMemory
from app.services.pipeline import InterviewPipeline
from app.services.retrieval.hybrid import RAGPipeline
from app.services.transcription.protocol import TranscriptionSegment

router = APIRouter(prefix="/answers", tags=["answers"])


@router.post("/generate")
async def generate_answer(body: AnswerGenerateRequest, db: DbSession, cache: RedisDep):
    """Generate an answer, streaming tokens as an SSE stream."""

    pipeline = InterviewPipeline(
        session=db,
        cache=cache,
        composer=AnswerComposer(),
        engine=AnswerEngine(),
        rag=RAGPipeline(db, cache),
        memory=ConversationMemory(cache),
        mode=body.mode,
    )

    segment = TranscriptionSegment(text=body.question_text, is_final=True, speaker="interviewer")

    async def event_stream():
        yield "data: " + '{"type": "status", "stage": "listening"}\n\n'
        result = await pipeline.process_question(
            pipeline.detector.flush_question(segment) or _fallback_detected(segment)
        )
        import json

        yield (
            "data: "
            + json.dumps(
                {
                    "type": "answer.done",
                    "answer_id": "stream",
                    "full_text": result.answer,
                    "mode": body.mode.value,
                    "sources": result.sources,
                    "validation": result.validation,
                    "latency_ms": result.latency_ms,
                }
            )
            + "\n\n"
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _fallback_detected(segment: TranscriptionSegment):
    from app.services.detection import DetectedQuestion

    return DetectedQuestion(text=segment.text, confidence=1.0, starts_at=0.0, ends_at=0.0, boundary_reason="rest")