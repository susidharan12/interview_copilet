from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field


@dataclass
class TranscriptionSegment:
    text: str
    confidence: float = 0.0
    speaker: str | None = None
    is_final: bool = False
    duration_ms: int | None = None


@dataclass
class AudioChunk:
    data: bytes
    sample_rate: int = 16000


class TranscriptionService(ABC):
    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def feed_audio(self, chunk: AudioChunk) -> None:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...

    @abstractmethod
    def stream(self) -> AsyncIterator[TranscriptionSegment]:
        ...

    @property
    @abstractmethod
    def partial_latency_ms(self) -> int | None:
        """Latency of last partial result, for observability."""
        ...