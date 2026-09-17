from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.services.retrieval.rrf import RetrievalCandidate


class Reranker(ABC):
    @abstractmethod
    async def rerank(self, query: str, candidates: list[RetrievalCandidate], top_n: int) -> list[RetrievalCandidate]:
        ...


class LexicalReranker(Reranker):
    """Cross-encoder / similarity reranker.

    Default offline implementation that boosts candidates whose content
    shares distinctive terms with the query — used until a production
    cross-encoder is wired in.
    """

    async def rerank(
        self, query: str, candidates: list[RetrievalCandidate], top_n: int
    ) -> list[RetrievalCandidate]:
        q_set = set(self._norm_tokens(query))
        for cand in candidates:
            tokens = self._norm_tokens(cand.content)
            overlap = len(q_set & set(tokens))
            if q_set:
                cand.score += 0.1 * overlap
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:top_n]

    @staticmethod
    def _norm_tokens(text: str) -> list[str]:
        import re
        return re.findall(r"[a-z0-9_+#.]+", text.lower())


def build_reranker(kind: str = "lexical") -> Reranker:
    return LexicalReranker()