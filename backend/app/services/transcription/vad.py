from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import numpy as np

from app.services.transcription.protocol import AudioChunk


class VoiceActivityDetector:
    """Energy + zero-crossing-rate based VAD.

    Simpler and faster than a neural VAD for the realtime path; the
    streaming transcriber performs the real classification. This is used
    for question-boundary heuristics and to avoid sending dead air.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_ms: int = 30,
        energy_threshold: float = 3000.0,
    ) -> None:
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * frame_ms / 1000)
        self.energy_threshold = energy_threshold
        self._buffer = np.zeros(0, dtype=np.float32)

    def process(self, chunk: AudioChunk) -> AsyncIterator[tuple[bytes, bool]]:
        """Yield (pcm_frame, is_speech). 128ms windows for boundary tracking."""
        pcm = np.frombuffer(chunk.data, dtype=np.int16).astype(np.float32)
        self._buffer = np.concatenate([self._buffer, pcm]) if self._buffer.size else pcm
        window = self.sample_rate // 8  # 125ms
        async def _iter():
            while len(self._buffer) >= window:
                frame, self._buffer = self._buffer[:window], self._buffer[window:]
                is_speech = self._is_speech(frame)
                yield frame.astype(np.int16).tobytes(), is_speech
        return _iter()

    def _is_speech(self, frame: np.ndarray) -> bool:
        if len(frame) < 16:
            return False
        rms = float(np.sqrt(np.mean(frame**2) + 1e-10))
        return rms > self.energy_threshold

    @staticmethod
    def silence_duration_ms(last_voice: float | None, now: float) -> float:
        return (now - last_voice) * 1000 if last_voice else 0.0