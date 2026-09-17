from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import CacheService
from app.core.telemetry import trace_span
from app.schemas.question import ClassificationResult
from app.schemas.session import AnswerMode
from app.services.composer import AnswerComposer
from app.services.detection import DetectedQuestion, QuestionDetector
from app.services.engines.answer_engine import AnswerEngine
from app.services.memory import ConversationMemory, Turn
from app.services.retrieval.hybrid import RAGPipeline
from app.services.retrieval.rrf import RetrievalCandidate
from app.services.router import ModelRouter
from app.services.transcription.protocol import TranscriptionSegment, TranscriptionService
from app.services.validation import AnswerValidator


@dataclass
class PipelineResult:
    question: DetectedQuestion
    classification: ClassificationResult
    answer: str
    sources: list[dict]
    validation: dict[str, Any]
    latency_ms: int
    first_token_ms: int


class InterviewPipeline:
    """End-to-end interview pipeline orchestrator.

    Listens for transcription segments → detects questions → classifies →
    parallel RAG + memory → engine → validation → composition, streaming
    each stage through an emit callback (WebSocket / SSE / tests).
    """

    def __init__(
        self,
        session: AsyncSession,
        cache: CacheService | None = None,
        transcriber: TranscriptionService | None = None,
        classifier=None,
        rag: RAGPipeline | None = None,
        memory: ConversationMemory | None = None,
        router: ModelRouter | None = None,
        engine: AnswerEngine | None = None,
        validator: AnswerValidator | None = None,
        composer: AnswerComposer | None = None,
        mode: AnswerMode = AnswerMode.INTERVIEW,
    ) -> None:
        from app.services.classification import QuestionClassifier

        self.session = session
        self.cache = cache
        self.transcriber = transcriber
        self.detector = QuestionDetector()
        self.classifier = classifier or QuestionClassifier()
        self.rag = rag or RAGPipeline(session, cache)
        self.memory = memory or ConversationMemory(cache)
        self.router = router or ModelRouter()
        self.engine = engine or AnswerEngine()
        self.validator = validator or AnswerValidator()
        self.composer = composer or AnswerComposer()
        self.mode = mode
        self._emit: Callable[[str, dict[str, Any]], Any] | None = None

    def set_emitter(self, emit: Callable[[str, dict[str, Any]], Any]) -> None:
        self._emit = emit

    async def _send(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._emit:
            await self._emit(event_type, payload)

    async def set_mode(self, mode: AnswerMode) -> None:
        self.mode = mode

    async def feed_transcript(self, segment: TranscriptionSegment) -> PipelineResult | None:
        await self._send("pipeline.status", {"stage": "transcribing", "message": "Listening…"})
        question = self.detector.feed(segment)
        if question is None:
            return None
        return await self.process_question(question)

    async def process_question(self, question: DetectedQuestion) -> PipelineResult:
        started = time.monotonic()
        await self._send("pipeline.status", {"stage": "detecting", "message": "Question detected"})
        await self._send("question.detected", self._question_payload(question))

        await self.memory.set_question(question.text)

        async with trace_span("pipeline.process_question") as span:
            classification = await self.classifier.classify(question.text)
            span.set_attribute("category", classification.category)

            route = await self.router.route(classification)
            await self._send("pipeline.status", {"stage": "classifying", "message": f"→ {classification.category} ({classification.difficulty})"})
            await self._send("pipeline.status", {"stage": "retrieving", "message": f"Searching knowledge base… ({route.model})"})

            memory_snap = await self.memory.snapshot()

            context_candidates: list[RetrievalCandidate] = []
            retrieved_context = ""
            if classification.requires_retrieval:
                retrieval_task = self.rag.retrieve(
                    question.text, filters=_derive_filters(classification), top_k=10
                )
                profile_task = classification.category in ("resume", "project", "behavioral")
                if profile_task:
                    profile_frag = await self._load_profile_fragment()
                else:
                    profile_frag = ""
                candidates, trace = await retrieval_task
                context_candidates = candidates
                retrieved_context = self.rag.build_context(candidates)
                if trace.get("final_chunk_ids"):
                    await self.rag.persist_trace(question_id=uuid.uuid4(), query_text=question.text, trace=trace)
            else:
                profile_frag = ""

            await self._send("sources.updated", {"sources": [_src(c) for c in context_candidates[:4]]})

            await self._send("pipeline.status", {"stage": "thinking", "message": "Reasoning…"})
            final_answer = await self._generate(
                question.text,
                classification,
                retrieved_context,
                memory_snap.to_prompt_fragment(),
                profile_frag,
            )

            await self._send("pipeline.status", {"stage": "validating", "message": "Validating…"})
            validation = await self.validator.validate(
                final_answer,
                context_candidates,
                profile_text=profile_frag,
                conversation=memory_snap.to_prompt_fragment(),
            )

            composed = await self.composer.compose(
                final_answer,
                self.mode,
                sources=[_src(c) for c in context_candidates[:4]],
                validation=validation,
            )

        await self.memory.add_turn(Turn(role="interviewer", content=question.text))
        await self.memory.add_turn(Turn(role="candidate", content=composed.content))

        total_ms = int((time.monotonic() - started) * 1000)
        return PipelineResult(
            question=question,
            classification=classification,
            answer=composed.content,
            sources=composed.sources,
            validation=validation,
            latency_ms=total_ms,
            first_token_ms=total_ms,
        )

    async def _generate(
        self,
        question: str,
        classification: ClassificationResult,
        context: str,
        memory_fragment: str,
        profile_fragment: str,
    ) -> str:
        from app.services.engines.prompts import EngineInput

        inp = EngineInput(
            question=question,
            category=classification.category,
            mode=self.mode,
            context=context,
            memory_fragment=memory_fragment,
            profile_fragment=profile_fragment,
            technology=classification.technology,
            difficulty=classification.difficulty,
        )
        route = await self.router.route(classification)
        buffer: list[str] = []

        async for token in self.engine.stream(inp, route.model):
            buffer.append(token)
            await self._send("answer.delta", {"token": token, "mode": self.mode.value})

        return "".join(buffer)

    async def _load_profile_fragment(self) -> str:
        try:
            from sqlalchemy import select

            from app.models.models import Profile

            result = await self.session.execute(select(Profile).limit(1))
            profile = result.scalars().first()
            if profile is None:
                return ""
            return (
                f"Name: {profile.name}\nSummary: {profile.resume_summary or 'N/A'}\n"
                f"Skills: {', '.join(profile.skills or [])}\n"
                f"Experience: {profile.experience_years or 0} years\n"
                f"Target role: {profile.target_role or 'N/A'}"
            )
        except Exception:
            return ""

    @staticmethod
    def _question_payload(q: DetectedQuestion) -> dict[str, Any]:
        return {"text": q.text, "confidence": q.confidence, "boundary_reason": q.boundary_reason}

    async def shutdown(self) -> None:
        if self.transcriber:
            await self.transcriber.stop()


def _derive_filters(classification: ClassificationResult) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    roles = {"resume", "project", "behavioral"}
    docs = {"technical", "project", "resume"}
    if classification.category in roles:
        filters["document_type"] = ["resume", "project", "notes", "technical"]
    if classification.technology:
        filters["technology"] = [classification.technology]
    return filters


def _src(c: RetrievalCandidate) -> dict[str, Any]:
    return {
        "chunk_id": c.chunk_id,
        "document_id": c.document_id,
        "content_preview": c.content[:160],
        "score": c.score,
    }