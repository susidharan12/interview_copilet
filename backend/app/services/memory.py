from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.core.redis import CacheService


@dataclass
class Turn:
    role: str  # interviewer | candidate
    content: str
    confidence: float = 1.0


@dataclass
class MemorySnapshot:
    current_question: str = ""
    turns: list[Turn] = field(default_factory=list)
    summary: str = ""
    technologies: list[str] = field(default_factory=list)
    current_topic: str = ""
    token_budget: int = 6000

    def to_prompt_fragment(self) -> str:
        if not self.turns and not self.current_question:
            return ""
        parts = []
        if self.current_question:
            parts.append(f"Current question: {self.current_question}")
        if self.summary:
            parts.append(f"Conversation summary: {self.summary}")
        recent = self.turns[-6:]
        if recent:
            parts.append("Recent exchange:")
            for t in recent:
                parts.append(f"  {t.role}: {t.content}")
        if self.technologies:
            parts.append("Technologies discussed: " + ", ".join(self.technologies))
        return "\n".join(parts)


class ConversationMemory:
    """Three-level memory: L1 current question, L2 conversation, L3 profile.

    L2 uses rolling summaries when the token budget is exceeded so context
    stays bounded and follow-up questions remain understandable.
    """

    def __init__(self, cache: CacheService | None = None) -> None:
        self.cache = cache
        self._l1: str = ""
        self._l2: list[Turn] = []
        self._summary: str = ""
        self._technologies: set[str] = set()
        self._topic: str = ""

    async def set_question(self, question: str) -> None:
        self._l1 = question

    async def add_turn(self, turn: Turn) -> None:
        self._l2.append(turn)
        if len(self._l2) > 30:
            self._roll_summary()
        self._extract_technologies(turn.content)

    async def roll_summary(self) -> None:
        self._roll_summary()

    def _roll_summary(self) -> None:
        if len(self._l2) <= 8:
            return
        kept = self._l2[-8:]
        dropped = self._l2[:-8]
        digest = " ".join(f"{t.role}: {t.content}" for t in dropped)[:1200]
        self._summary = (self._summary + " | " + digest)[:2000]
        self._l2 = kept

    def _extract_technologies(self, text: str) -> None:
        import re
        known = {"python", "java", "kotlin", "go", "rust", "react", "node", "docker",
                 "kubernetes", "postgres", "postgresql", "redis", "sql", "mongodb",
                 "kafka", "graphql", "aws", "spark", "terraform", "ci/cd", "git"}
        for kw in known:
            if re.search(rf"\b{re.escape(kw)}\b", text.lower()):
                self._technologies.add(kw)

    async def snapshot(self) -> MemorySnapshot:
        return MemorySnapshot(
            current_question=self._l1,
            turns=list(self._l2),
            summary=self._summary,
            technologies=sorted(self._technologies),
            current_topic=self._topic,
        )

    async def from_db(self, session, session_id) -> None:
        """Rehydrate L2 from stored interview turns."""
        from sqlalchemy import select

        from app.models.models import InterviewTurn

        stmt = (
            select(InterviewTurn)
            .where(InterviewTurn.session_id == session_id)
            .order_by(InterviewTurn.turn_index.desc())
            .limit(20)
        )
        try:
            result = await session.execute(stmt)
            rows = result.scalars().all()
        except Exception:
            return
        for row in reversed(rows):
            self._l2.append(Turn(role=row.speaker, content=row.content))

    @staticmethod
    async def from_redis(cache: CacheService, key: str) -> "ConversationMemory":
        mem = ConversationMemory(cache=cache)
        raw = await cache.get(key)
        if raw:
            data = json.loads(raw)
            mem._l1 = data.get("l1", "")
            mem._l2 = [Turn(**t) for t in data.get("l2", [])]
            mem._summary = data.get("summary", "")
            mem._technologies = set(data.get("technologies", []))
            mem._topic = data.get("topic", "")
        return mem

    async def save_to_redis(self, key: str, ttl_seconds: int = 21600) -> None:
        if self.cache:
            await self.cache.set(
                key,
                json.dumps(
                    {
                        "l1": self._l1,
                        "l2": [{"role": t.role, "content": t.content, "confidence": t.confidence} for t in self._l2],
                        "summary": self._summary,
                        "technologies": sorted(self._technologies),
                        "topic": self._topic,
                    }
                ),
                ttl_seconds=ttl_seconds,
            )