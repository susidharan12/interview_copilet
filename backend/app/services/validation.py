from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.retrieval.rrf import RetrievalCandidate


class AnswerValidator:
    """Pre-final answer validation: consistency + unsupported claims.

    Deterministic checks run fast and cheap before an answer is finalized:
    - resume consistency (claims that could reference the candidate's projects)
    - retrieved-context consistency (answers cite or align with retrieved chunks)
    - unsupported claim detection (vague/hallucinatory phrasing)
    """

    async def validate(
        self,
        answer: str,
        retrieved: list[RetrievalCandidate],
        profile_text: str | None = None,
        conversation: str | None = None,
    ) -> dict[str, Any]:
        checks: dict[str, Any] = {}
        checks["answer_length"] = len(answer.split())
        checks["has_context"] = bool(retrieved)

        issues: list[str] = []
        if len(answer.split()) < 10:
            issues.append("answer_too_short")

        lowered = answer.lower()
        for marker in ("i built", "i implemented", "in my project", "my team", "at my company"):
            if marker in lowered:
                claims = _find_claims(answer, marker)
                if claims and not _claims_in_profile(claims, profile_text or ""):
                    issues.append("unsupported_personal_claim")

        if retrieved:
            context_text = " ".join(c.content.lower()[:500] for c in retrieved[:3])
            if context_text and not _any_overlap(lowered, context_text):
                issues.append("no_context_support")

        checks["issues"] = issues
        checks["confidence"] = _confidence(checks, issues)
        checks["passed"] = len(issues) == 0
        return checks


def _find_claims(answer: str, marker: str) -> list[str]:
    claims = []
    for sentence in answer.split(". "):
        if marker in sentence.lower():
            claims.append(sentence.strip())
    return claims


def _claims_in_profile(claims: list[str], profile: str) -> bool:
    if not profile:
        return False
    prof_lower = profile.lower()
    for c in claims:
        for token in c.split():
            token = token.strip(".,!?")
            if len(token) > 4 and token.lower() in prof_lower:
                return True
    return False


def _any_overlap(text: str, context: str) -> bool:
    t_tokens = set(text.split())
    c_tokens = set(context.split())
    common = t_tokens & c_tokens
    return len(common) >= 3


def _confidence(checks: dict[str, Any], issues: list[str]) -> float:
    base = 0.85
    base -= 0.15 * len(issues)
    if checks["has_context"]:
        base += 0.05
    return max(0.2, min(0.98, round(base, 2)))