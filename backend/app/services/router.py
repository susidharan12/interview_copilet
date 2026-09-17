from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.config import settings
from app.schemas.question import ClassificationResult


@dataclass
class RoutingDecision:
    model: str
    tier: Literal["fast", "reasoning", "coding", "embedding"]
    reason: str


class ModelRouter:
    """Maps a classified question to a model tier.

    Simple/known questions → fast cheap model.
    Complex reasoning/design → strong reasoning model.
    Coding → reasoning model (paired with sandbox validation downstream).
    """

    def __init__(self) -> None:
        self._fast = settings.default_model
        self._reasoning = settings.reasoning_model
        self._coding = settings.coding_model

    async def route(self, classification: ClassificationResult) -> RoutingDecision:
        cat = classification.category
        if classification.requires_code_execution or cat == "coding":
            return RoutingDecision(self._coding, "coding", "requires code execution")
        if cat in ("system_design", "architecture", "scenario") or classification.requires_reasoning:
            return RoutingDecision(self._reasoning, "reasoning", f"complex {cat} reasoning")
        return RoutingDecision(self._fast, "fast", "simple direct answer")