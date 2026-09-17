from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RetrievalCandidate:
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict = field(default_factory=dict)
    source: str = ""


def rrf_fuse(
    ranked_lists: list[list[RetrievalCandidate]],
    k: int = 60,
) -> list[RetrievalCandidate]:
    """Reciprocal Rank Fusion over multiple ranked lists.

    RRF(d) = Σ 1/(k + rank(d)). Deterministic, parameter-light, and works
    well with uncalibrated scores from BM25 and vector search.
    """
    scores: dict[str, float] = {}
    items: dict[str, RetrievalCandidate] = {}
    for ranked in ranked_lists:
        for rank, cand in enumerate(ranked):
            key = cand.chunk_id
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            items.setdefault(key, cand)
    merged = []
    for key, score in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
        cand = items[key]
        cand.score = round(score, 6)
        merged.append(cand)
    return merged