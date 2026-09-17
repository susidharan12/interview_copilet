from __future__ import annotations

from typing import Any

import tiktoken

TOKENIZER_NAME = "cl100k_base"


def num_tokens(text: str) -> int:
    try:
        enc = tiktoken.get_encoding(TOKENIZER_NAME)
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)


def chunk_document(
    content: str,
    meta: dict[str, Any],
    chunk_size_tokens: int = 512,
    overlap_tokens: int = 50,
) -> list[dict[str, Any]]:
    """Token-aware paragraph chunking with overlap.

    Splits content by paragraphs, then greedily packs paragraphs into windows
    of roughly `chunk_size_tokens`, keeping `overlap_tokens` from the previous
    window for context continuity.
    """
    if not content.strip():
        return [{"content": " ", "metadata": {}}]

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    chunks: list[dict[str, Any]] = []
    current: list[str] = []
    current_tokens = 0
    overlap_text = ""

    for para in paragraphs:
        para_tokens = num_tokens(para)
        if current_tokens + para_tokens > chunk_size_tokens and current:
            combined = (overlap_text + "\n".join(current)).strip()
            chunks.append({"content": combined, "metadata": {}})
            overlap_text = _tail(combined, overlap_tokens)
            current = [para]
            current_tokens = para_tokens
        else:
            current.append(para)
            current_tokens += para_tokens

    if current:
        combined = (overlap_text + "\n".join(current)).strip()
        if combined:
            chunks.append({"content": combined, "metadata": {}})

    return chunks or [{"content": " ", "metadata": {}}]


def _tail(text: str, max_tokens: int) -> str:
    tok = text.split()
    budget_tokens = max(1, max_tokens)
    return " ".join(tok[-budget_tokens:]) + "\n"