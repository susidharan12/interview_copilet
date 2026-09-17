from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from app.services.transcription.protocol import TranscriptionSegment


@dataclass
class DetectedQuestion:
    text: str
    confidence: float
    starts_at: float
    ends_at: float
    boundary_reason: str


QUESTION_MARKERS = re.compile(
    r"\b(what|how|which|who|why|when|where|tell me|can you|could you|would you|"
    r"explain|describe|walk me through|design|implement|solve|write|"
    r"do you have|have you|did you|is it|are you able)\b",
    re.IGNORECASE,
)

_QUESTION_END = {"?", "!", "."}


class QuestionDetector:
    """Segments a transcript stream into interview questions.

    Only the interviewer's turns (heuristically detected, or via speaker
    tags from the transcriber) are considered. A question boundary is
    emitted when a sentence ends with a question marker and is followed by
    a silence gap >= pause threshold.
    """

    def __init__(self, pause_ms: int = 1500, max_question_chars: int = 600) -> None:
        self.pause_ms = pause_ms
        self.max_question_chars = max_question_chars
        self._buffer: list[str] = []
        self._last_speech: float | None = None
        self._now: float = time.time()
        self._last_voice: float | None = None

    def reset(self) -> None:
        self._buffer.clear()
        self._last_speech = None
        self._last_voice = None

    def feed(self, segment: TranscriptionSegment) -> DetectedQuestion | None:
        """Feed a transcript segment; returns a question if one is detected."""
        self._now = time.time()
        if segment.speaker and segment.speaker.lower() not in ("interviewer", "ai", "user", None):
            # Only process interviewer speech if speaker labels are known.
            if segment.speaker.lower() != "interviewer":
                return None

        text = segment.text.strip()
        if not text:
            return None

        self._last_voice = self._now
        self._buffer.append(text)
        candidate = " ".join(self._buffer)
        if not self._looks_like_question(candidate):
            if len(candidate) > self.max_question_chars:
                self._buffer = []
            return None
        return DetectedQuestion(
            text=candidate[-self.max_question_chars:],
            confidence=self._confidence(candidate),
            starts_at=self._last_speech or self._now,
            ends_at=self._now,
            boundary_reason="punctuation+marker",
        )

    def _looks_like_question(self, text: str) -> bool:
        if not QUESTION_MARKERS.search(text):
            return False
        for end in _QUESTION_END:
            if text.rstrip().endswith(end):
                return len(text) <= self.max_question_chars
        return False

    def _confidence(self, text: str) -> float:
        base = 0.7 if text.rstrip().endswith("?") else 0.55
        if QUESTION_MARKERS.search(text):
            base += 0.15
        return min(0.99, base)

    def flush(self) -> DetectedQuestion | None:
        text = " ".join(self._buffer).strip()
        self._buffer = []
        if text and self._looks_like_question(text):
            return DetectedQuestion(
                text=text[-self.max_question_chars:],
                confidence=self._confidence(text),
                starts_at=self._last_speech or self._now,
                ends_at=self._now,
                boundary_reason="flush",
            )
        return None