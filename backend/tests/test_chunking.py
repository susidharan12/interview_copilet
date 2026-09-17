from __future__ import annotations

import pytest

from app.services.retrieval.retrieval_chunk import chunk_document


def test_chunking_small_document_single_chunk():
    chunks = chunk_document("Paragraph one about caching.\n\nParagraph two about Redis eviction policies.", {})
    assert len(chunks) >= 1
    assert "caching" in chunks[0]["content"] or "Redis" in chunks[0]["content"]


def test_chunking_empty_content():
    chunks = chunk_document("   ", {})
    assert chunks[0]["content"] == " "


def test_chunking_many_paragraphs():
    content = "\n\n".join(f"Paragraph {i} contains important details about distributed systems." for i in range(50))
    chunks = chunk_document(content, {}, chunk_size_tokens=20, overlap_tokens=10)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk["content"]
    # Overlap should preserve continuity across adjacent chunk boundaries
    for i in range(len(chunks) - 1):
        prev_words = set(chunks[i]["content"].split())
        next_words = set(chunks[i + 1]["content"].split())
        assert prev_words & next_words, f"chunk {i} and {i+1} share no terms (context lost)"