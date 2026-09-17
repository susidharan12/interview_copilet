from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from app.services.transcription.protocol import AudioChunk, TranscriptionSegment, TranscriptionService


class MockTranscriptionService(TranscriptionService):
    """Deterministic transcription used for development and tests.

    Accumulates buffered audio (input ignored) and emits a fixed
    transcript after `stop()` — this exercises the full pipeline without
    an OpenAI key.
    """

    def __init__(self, transcript: str | None = None) -> None:
        self._text = transcript or "Can you explain how you implemented caching in your most recent project?"
        self._buffer: list[bytes] = []
        self._running = False
        self._queue: asyncio.Queue[TranscriptionSegment] = asyncio.Queue(maxsize=50)
        self._last_latency: int | None = 10

    @property
    def partial_latency_ms(self) -> int | None:
        return self._last_latency

    async def start(self) -> None:
        self._running = True

    async def feed_audio(self, chunk: AudioChunk) -> None:
        self._buffer.append(chunk.data)
        # Simulate partial transcripts appearing in near real time.
        if len(self._buffer) % 3 == 0:
            await self._queue.put(
                TranscriptionSegment(text=f"[partial {len(self._buffer) // 3}]", confidence=0.5)
            )

    async def stop(self) -> None:
        self._running = False
        await asyncio.sleep(0.01)
        if self._text:
            await self._queue.put(
                TranscriptionSegment(
                    text=self._text,
                    confidence=0.9,
                    speaker="interviewer",
                    is_final=True,
                    duration_ms=len(b"".join(self._buffer)) // 32,
                )
            )

    def stream(self) -> AsyncIterator[TranscriptionSegment]:
        async def _gen():
            while self._running or not self._queue.empty():
                try:
                    seg = await asyncio.wait_for(self._queue.get(), timeout=0.2)
                except asyncio.TimeoutError:
                    if not self._running and self._queue.empty():
                        break
                    continue
                yield seg
                self._queue.task_done()
        return _gen()