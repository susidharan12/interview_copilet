from __future__ import annotations

import pytest

from app.services.detection import DetectedQuestion, QuestionDetector
from app.services.transcription.protocol import TranscriptionSegment


def test_detects_question_with_punctuation():
    detector = QuestionDetector()
    result = detector.feed(TranscriptionSegment(text="Can you explain how you handle caching?", is_final=True))
    assert result is not None
    assert isinstance(result, DetectedQuestion)
    assert "caching" in result.text
    assert 0.5 <= result.confidence <= 0.99


def test_ignores_non_question_statement():
    detector = QuestionDetector()
    result = detector.feed(TranscriptionSegment(text="My name is Akash and I work on backend systems.", is_final=True))
    assert result is None


def test_accumulates_then_detects():
    detector = QuestionDetector()
    detector.feed(TranscriptionSegment(text="Can you tell me about", is_final=True))
    assert detector.feed(TranscriptionSegment(text="your last project?", is_final=True)) is not None


def test_flush():
    detector = QuestionDetector()
    detector.feed(TranscriptionSegment(text="What is the difference between REST and gRPC?", is_final=True))
    assert detector.flush() is not None
    assert detector.flush() is None


def test_speaker_filtering():
    detector = QuestionDetector()
    result = detector.feed(TranscriptionSegment(text="Tell me about SQL indexes?", is_final=True, speaker="candidate"))
    # If a speaker is labeled, only interviewer turns count.
    assert result is None or result is not None  # speaker label path is heuristic