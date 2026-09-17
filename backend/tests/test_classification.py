from __future__ import annotations

import pytest

from app.services.classification import QuestionClassifier

CASES = [
    ("Write a function to find the two numbers that sum to a target.", "coding"),
    ("Explain the difference between a process and a thread.", "technical"),
    ("Design a distributed rate limiter.", "system_design"),
    ("The API is returning 500s for all users, what do you do?", "scenario"),
    ("Tell me about a time you showed leadership.", "behavioral"),
    ("Write a SQL query to get customers who ordered in the last 30 days.", "sql"),
    ("How would you scale this system to 1000x users?", "system_design"),
]


@pytest.mark.asyncio
async def test_classifier_categories():
    classifier = QuestionClassifier()
    for question, expected in CASES:
        result = await classifier.classify(question)
        assert result.category == expected, f"{question!r}: got {result.category}, expected {expected}"


@pytest.mark.asyncio
async def test_classifier_structured_fields():
    classifier = QuestionClassifier()
    result = await classifier.classify("Design a system that handles millions of requests per day")
    assert result.category in {"system_design", "architecture"}
    assert result.difficulty in {"easy", "medium", "hard"}
    assert isinstance(result.requires_retrieval, bool)
    assert isinstance(result.requires_code_execution, bool)
    assert result.confidence >= 0.0 and result.confidence <= 1.0


@pytest.mark.asyncio
async def test_follow_up_detection():
    classifier = QuestionClassifier()
    result = await classifier.classify(
        "How would you scale that solution?",
        previous=["How would you design a message queue?"],
    )
    assert result.category == "follow_up"