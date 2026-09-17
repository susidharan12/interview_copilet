from __future__ import annotations

import pytest

from app.services.retrieval.rrf import RetrievalCandidate, rrf_fuse


def _c(chunk_id: str, content: str) -> RetrievalCandidate:
    return RetrievalCandidate(
        chunk_id=chunk_id,
        document_id=f"doc-{chunk_id}",
        content=content,
        score=0.0,
    )


def test_rrf_merges_ranked_lists():
    bm25 = [_c("a", "python caching"), _c("b", "java threads"), _c("c", "sql joins")]
    vector = [_c("b", "java threads"), _c("c", "sql joins"), _c("d", "queues")]
    fused = rrf_fuse([bm25, vector])

    assert fused[0].chunk_id == "b"  # present in both lists → highest RRF
    assert {c.chunk_id for c in fused} == {"a", "b", "c", "d"}
    assert fused[0].score > fused[-1].score


def test_backend_router_chooses_fast_model_for_simple() -> None:
    from app.services.router import ModelRouter
    from app.schemas.question import ClassificationResult

    from unittest.mock import AsyncMock, patch

    with patch("app.services.router.settings") as mock_settings:
        mock_settings.default_model = "fast"
        mock_settings.reasoning_model = "slow"
        mock_settings.coding_model = "coder"
        router = ModelRouter()
        simple = ClassificationResult(
            category="technical",
            requires_retrieval=True,
            requires_reasoning=False,
            requires_code_execution=False,
            requires_screen_context=False,
            confidence=0.9,
        )
        decision = asyncio_run(router.route(simple))
        assert decision.tier == "fast"

        complex_q = ClassificationResult(
            category="system_design",
            requires_retrieval=True,
            requires_reasoning=True,
            requires_code_execution=False,
            requires_screen_context=False,
            confidence=0.9,
        )
        decision2 = asyncio_run(router.route(complex_q))
        assert decision2.tier == "reasoning"


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)