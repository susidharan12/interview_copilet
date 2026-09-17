from __future__ import annotations

import asyncio

import pytest

from app.services.pipeline import InterviewPipeline
from app.schemas.session import AnswerMode
from app.services.detection import DetectedQuestion
from app.services.transcription.protocol import TranscriptionSegment, TranscriptionService


class FakeTranscriber(TranscriptionService):
    def __init__(self) -> None:
        self.events = []
        self._partial_latency = 15

    async def start(self) -> None:
        self.events.append("start")

    async def feed_audio(self, chunk) -> None:
        self.events.append("audio")

    async def stop(self) -> None:
        self.events.append("stop")

    def stream(self):
        async def _gen():
            yield TranscriptionSegment(text="What is Redis?", is_final=True)
        return _gen()

    @property
    def partial_latency_ms(self) -> int | None:
        return self._partial_latency


class FakeRAG:
    async def retrieve(self, query, filters=None, top_k=10):
        return [], {"final_chunk_ids": [], "latency_ms": 2}

    async def persist_trace(self, question_id, query_text, trace):
        pass

    def build_context(self, candidates):
        return ""


class FakeClassifier:
    async def classify(self, question, previous=None):
        from app.schemas.question import ClassificationResult

        return ClassificationResult(
            category="technical",
            technology="redis",
            difficulty="easy",
            requires_retrieval=True,
            requires_reasoning=False,
            requires_code_execution=False,
            requires_screen_context=False,
            confidence=0.9,
        )


class FakeRouter:
    async def route(self, classification):
        from app.services.router import RoutingDecision

        return RoutingDecision(model="fake-model", tier="fast", reason="test")


class FakeEngine:
    async def stream(self, inp, model):
        for token in ["Short ", "answer ", "about ", "Redis ", "caching."]:
            yield token


@pytest.mark.asyncio
async def test_full_pipeline_streams_events(make_session):
    async for db in make_session():
        pipeline = InterviewPipeline(
            session=db,
            transcriber=FakeTranscriber(),
            classifier=FakeClassifier(),
            rag=FakeRAG(),  # type: ignore
            router=FakeRouter(),
            engine=FakeEngine(),
            mode=AnswerMode.INTERVIEW,
        )
        emitted: list[tuple[str, dict]] = []

        async def emit(event_type: str, payload: dict) -> None:
            emitted.append((event_type, payload))

        pipeline.set_emitter(emit)
        question = DetectedQuestion("What is Redis?", 0.9, 0.0, 0.0, "test")
        result = await pipeline.process_question(question)

        assert result is not None
        assert "Redis" in result.answer
        assert pipeline.classifier is not None

        types = [e for e, _ in emitted]
        assert "pipeline.status" in types
        assert "answer.delta" in types
        assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_pipeline_handles_transcript_stream(make_session):
    async for db in make_session():
        pipeline = InterviewPipeline(
            session=db,
            transcriber=FakeTranscriber(),
            classifier=FakeClassifier(),
            rag=FakeRAG(),  # type: ignore
            router=FakeRouter(),
            engine=FakeEngine(),
            mode=AnswerMode.QUICK,
        )
        # A non-question statement should not trigger processing.
        result = await pipeline.feed_transcript(
            TranscriptionSegment(text="Thanks for joining, my name is Sam.", is_final=True)
        )
        assert result is None