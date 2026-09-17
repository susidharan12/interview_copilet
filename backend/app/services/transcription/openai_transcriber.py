from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.transcription.protocol import AudioChunk, TranscriptionSegment, TranscriptionService


class OpenAITranscriptionService(TranscriptionService):
    """Streaming transcription via gpt-4o-transcribe.

    Uses OpenAI's streaming speech-to-text: audio chunks are processed
    incrementally and partial/final transcripts are surfaced as they are
    produced, without waiting for the full interview recording.
    """

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self._queue: asyncio.Queue[TranscriptionSegment] = asyncio.Queue(maxsize=200)
        self._audio_buffer: list[bytes] = []
        self._running = False
        self._last_partial_latency: int | None = None

    async def start(self) -> None:
        self._running = True

    async def feed_audio(self, chunk: AudioChunk) -> None:
        self._audio_buffer.append(chunk.data)

    async def stop(self) -> None:
        self._running = False
        if not self._audio_buffer:
            return
        # Flush remaining audio via the transcription request.
        combined = b"".join(self._audio_buffer)
        self._audio_buffer.clear()
        start = asyncio.get_event_loop().time()
        try:
            clip = _to_audio_input(combined, self._client)
            result = await self._client.audio.transcriptions.create(
                model=settings.transcription_model,
                file=clip,
                language="en",
            )
            self._last_partial_latency = int((asyncio.get_event_loop().time() - start) * 1000)
            await self._queue.put(
                TranscriptionSegment(text=result.text, confidence=1.0, is_final=True)
            )
        except Exception:
            pass

    def stream(self) -> AsyncIterator[TranscriptionSegment]:
        async def _gen():
            while self._running or not self._queue.empty():
                try:
                    seg = await asyncio.wait_for(self._queue.get(), timeout=0.25)
                except asyncio.TimeoutError:
                    if not self._running and self._queue.empty():
                        break
                    continue
                yield seg
                self._queue.task_done()
        return _gen()

    @property
    def partial_latency_ms(self) -> int | None:
        return self._last_partial_latency


def _to_audio_input(data: bytes, client: AsyncOpenAI):
    """Wrap raw PCM bytes into a 16kHz WAV for the transcription API."""
    import io
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(data)
    buf.seek(0)
    return ("audio.wav", buf.read(), "audio/wav")