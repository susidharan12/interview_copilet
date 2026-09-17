from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.question import ClassificationResult

CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": [
                "technical", "coding", "debugging", "system_design", "architecture",
                "scenario", "behavioral", "project", "resume", "sql", "follow_up",
                "clarification", "unknown",
            ],
        },
        "technology": {"type": "string"},
        "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
        "requires_retrieval": {"type": "boolean"},
        "requires_reasoning": {"type": "boolean"},
        "requires_code_execution": {"type": "boolean"},
        "requires_screen_context": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "category", "requires_retrieval", "requires_reasoning",
        "requires_code_execution", "requires_screen_context", "confidence",
    ],
    "additionalProperties": False,
}


class QuestionClassifier:
    """Classifies question type via structured output from the LLM.

    Uses OpenAI structured outputs (JSON schema enforcement). Falls back to
    a deterministic keyword classifier when no API key is configured, so the
    pipeline remains testable offline.
    """

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self._client = client or self._maybe_client()

    @staticmethod
    def _maybe_client() -> AsyncOpenAI | None:
        if settings.openai_api_key:
            return AsyncOpenAI(api_key=settings.openai_api_key)
        return None

    async def classify(self, question: str, previous: list[str] | None = None) -> ClassificationResult:
        if self._client is None:
            return await self._deterministic_classify(question, previous or [])
        try:
            response = await self._client.chat.completions.create(
                model=settings.default_model,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "question_classification",
                        "schema": CLASSIFICATION_SCHEMA,
                        "strict": True,
                    },
                },
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You classify interview questions. Output only the JSON object "
                            "matching the schema. Use previously asked questions to detect follow-ups."
                        ),
                    },
                    {
                        "role": "user",
                        "content": question
                        + (f"\nPrevious questions: {previous}" if previous else ""),
                    },
                ],
            )
            raw = response.choices[0].message.content
            return ClassificationResult.model_validate_json(raw or "{}")
        except Exception:
            return await self._deterministic_classify(question, previous or [])

    async def _deterministic_classify(
        self, question: str, previous: list[str]
    ) -> ClassificationResult:
        from app.schemas.question import QuestionCategory

        q = question.lower()
        coding_kw = ["write a function", "implement", "code", "algorithm", "leetcode",
                     "time complexity", "two sum", "sort", "binary search", "dynamic programming"]
        sql_kw = ["sql", "query", "database query", "join", "index", "normalization"]
        scenario_kw = ["what would you do", "how would you handle", "what do you do",
                       "imagine", "production database", "incident", "outage",
                       "users can't", "users cannot", "api is returning"]
        design_kw = ["design", "architecture", "system design", "scale", "distributed"]
        behavioral_kw = ["tell me about a time", "describe a situation", "experience", "team",
                         "conflict", "leadership"]
        deictic_followup = ["that solution", "that approach", "that design", "that system",
                            "that code", "scale that", "extend this", "build on this",
                            "improve on this", "instead"]

        category: str
        if previous and _refers_to_previous(q, previous, deictic_followup):
            category = "follow_up"
        elif any(k in q for k in coding_kw):
            category = "coding"
        elif any(k in q for k in sql_kw):
            category = "sql"
        elif any(k in q for k in scenario_kw):
            category = "scenario"
        elif any(k in q for k in design_kw):
            category = "system_design"
        elif any(k in q for k in behavioral_kw):
            category = "behavioral"
        elif q.startswith("can you clarify") or q.startswith("what do you mean"):
            category = "clarification"
        elif previous:
            category = "follow_up"
        else:
            category = "technical"

        complex_categories = {"coding", "system_design", "scenario", "architecture"}
        difficulty = "hard" if category in ("system_design", "scenario") else (
            "medium" if category in complex_categories else "easy"
        )
        return ClassificationResult(
            category=QuestionCategory(category),
            technology=self._extract_technology(q),
            difficulty=difficulty,
            requires_retrieval=category in ("project", "resume", "technical", "follow_up"),
            requires_reasoning=category in complex_categories,
            requires_code_execution=category == "coding",
            requires_screen_context=False,
            confidence=0.8,
        )

    @staticmethod
    def _extract_technology(q: str) -> str | None:
        known = ["python", "java", "kotlin", "javascript", "typescript", "c++", "go", "rust",
                 "react", "node", "docker", "kubernetes", "k8s", "postgres", "redis", "sql",
                 "mysql", "mongodb", "aws", "gcp", "azure", "spark", "kafka", "graphql"]
        for t in known:
            if t in q:
                return t.replace("k8s", "kubernetes")
        return None


def _refers_to_previous(q: str, previous: list[str], deictic: list[str]) -> bool:
    """True when the question references an earlier question (follow-up)."""
    for prev in previous[:2]:
        p_lower = prev.lower()
        if p_lower and p_lower in q:
            return True
    if len(q.split()) <= 25 and any(d in q for d in deictic):
        return True
    return False