from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import authenticate_ws
from app.core.database import async_session_factory
from app.core.redis import CacheService, get_redis
from app.schemas.ws import ClientEvent
from app.services.detection import QuestionDetector
from app.services.pipeline import InterviewPipeline
from app.services.transcription.mock_transcriber import MockTranscriptionService
from app.services.transcription.openai_transcriber import OpenAITranscriptionService
from app.services.transcription.protocol import AudioChunk, TranscriptionSegment

router = APIRouter()

PIPELINE_STAGES = {
    "listening", "transcribing", "detecting", "classifying",
    "retrieving", "thinking", "validating", "answering",
}


class InterviewConnection:
    """Holds a live WebSocket + its pipeline, serializing writes."""

    def __init__(self, websocket: WebSocket, session_id: str, cache: CacheService) -> None:
        self.websocket = websocket
        self.session_id = session_id
        self.cache = cache
        self.write_lock = asyncio.Lock()
        self.pipeline: InterviewPipeline | None = None
        self.detector = QuestionDetector()
        self.transcribe_task: asyncio.Task | None = None

    async def send(self, event_type: str, payload: dict[str, Any]) -> None:
        async with self.write_lock:
            try:
                await self.websocket.send_text(
                    json.dumps(
                        {
                            "type": event_type,
                            "timestamp": time.time(),
                            "payload": payload,
                        },
                        default=str,
                    )
                )
            except Exception:
                pass

    async def emitter(self, event_type: str, payload: dict[str, Any]) -> None:
        await self.send(event_type, payload)

    async def handle_event(self, event: dict[str, Any]) -> None:
        try:
            client_event = ClientEvent.model_validate(event)
        except Exception:
            await self.send("error", {"code": "bad_message", "message": "Invalid message format", "recoverable": True})
            return

        handler = getattr(self, f"_on_{client_event.type.replace('.', '_')}", None)
        if handler is None:
            await self.send("error", {"code": "unknown_event", "message": f"Unhandled type: {client_event.type}", "recoverable": True})
            return
        await handler(client_event)

    async def _on_client_hello(self, event: ClientEvent) -> None:
        await self.send("server.hello", {"session_id": self.session_id, "server_version": "0.1.0"})

    async def _on_audio_chunk(self, event: ClientEvent) -> None:
        payload = event.payload
        data = payload.get("data", "")
        if not data:
            return
        import base64

        raw = base64.b64decode(data)
        self.detector.feed(TranscriptionSegment(text="", is_final=False))  # keep boundary state warm
        if self.pipeline and self.pipeline.transcriber:
            await self.pipeline.transcriber.feed_audio(
                AudioChunk(data=raw, sample_rate=int(payload.get("sample_rate", 16000) or 16000))
            )

    async def _on_audio_stop(self, event: ClientEvent) -> None:
        if self.pipeline and self.pipeline.transcriber:
            await self.pipeline.transcriber.stop()
        final = self.detector.flush()
        if final and self.pipeline:
            result = await self.pipeline.process_question(final)
            await self._emit_done(result)

    async def _on_question_text(self, event: ClientEvent) -> None:
        text = (event.payload.get("text") or "").strip()
        if not text:
            await self.send("error", {"code": "empty_question", "message": "Question text is empty", "recoverable": True})
            return
        if not self.pipeline:
            await self.send("error", {"code": "no_pipeline", "message": "Pipeline not ready", "recoverable": True})
            return

        from app.services.detection import DetectedQuestion

        await self.send("transcription.final", {"text": text, "confidence": 1.0, "speaker": "user", "duration_ms": None})
        question = DetectedQuestion(
            text=text,
            confidence=1.0,
            starts_at=0.0,
            ends_at=0.0,
            boundary_reason="typed",
        )
        result = await self.pipeline.process_question(question)
        await self._emit_done(result)

    async def _on_mode_switch(self, event: ClientEvent) -> None:
        from app.schemas.session import AnswerMode

        try:
            mode = AnswerMode(event.payload.get("mode", "interview"))
        except ValueError:
            await self.send("error", {"code": "bad_mode", "message": f"Unknown mode: {event.payload.get('mode')}", "recoverable": True})
            return
        if self.pipeline:
            await self.pipeline.set_mode(mode)
        await self.send("mode.switched", {"mode": mode.value})

    async def _on_interrupt(self, event: ClientEvent) -> None:
        await self.send("interrupted", {})

    async def _emit_done(self, result) -> None:
        await self.send(
            "answer.done",
            {
                "answer_id": str(uuid.uuid4()),
                "full_text": result.answer,
                "mode": result.classification.category,
                "sources": result.sources,
                "validation": result.validation,
                "latency_ms": result.latency_ms,
            },
        )


async def _transcribe_loop(conn: InterviewConnection) -> None:
    """Consume transcriber segments and feed them into the pipeline."""
    if not conn.pipeline or not conn.pipeline.transcriber:
        return
    async for segment in conn.pipeline.transcriber.stream():
        if not conn.pipeline:
            break
        result = await conn.pipeline.feed_transcript(segment)
        if result:
            await conn._emit_done(result)


async def _build_connection(
    websocket: WebSocket,
    session_id: str,
    cache: CacheService,
) -> InterviewConnection:
    conn = InterviewConnection(websocket, session_id, cache)

    session_id_uuid = None
    try:
        session_id_uuid = uuid.UUID(session_id)
    except ValueError:
        session_id_uuid = uuid.uuid4()

    async with async_session_factory() as db:
        from app.models.models import InterviewSession

        session = await db.get(InterviewSession, session_id_uuid)
        if session is None:
            session = InterviewSession(id=session_id_uuid, status="active", mode="interview")
            db.add(session)
            await db.commit()
        default_mode = session.mode

    async with async_session_factory() as db:
        from app.core.config import settings
        from app.schemas.session import AnswerMode

        transcriber: MockTranscriptionService | OpenAITranscriptionService
        if settings.openai_api_key:
            transcriber = OpenAITranscriptionService()
        else:
            transcriber = MockTranscriptionService()
        conn.pipeline = InterviewPipeline(
            session=db,
            cache=cache,
            transcriber=transcriber,
            mode=AnswerMode(default_mode or "interview"),
        )
        conn.pipeline.set_emitter(conn.emitter)
        await transcriber.start()
    conn.transcribe_task = asyncio.create_task(_transcribe_loop(conn))
    return conn


@router.websocket("/ws/interview/{session_id}")
async def interview_ws(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    await authenticate_ws(websocket)

    cache = await get_redis()
    conn = await _build_connection(websocket, session_id, cache)

    await conn.send("server.hello", {"session_id": session_id, "server_version": "0.1.0"})

    try:
        while True:
            raw = await websocket.receive_text()
            event = json.loads(raw)
            await conn.handle_event(event)
    except WebSocketDisconnect:
        if conn.pipeline:
            await conn.pipeline.shutdown()
    except Exception as exc:
        await conn.send("error", {"code": "internal", "message": str(exc), "recoverable": True})
    finally:
        if conn.transcribe_task:
            conn.transcribe_task.cancel()
        if conn.pipeline:
            await conn.pipeline.shutdown()