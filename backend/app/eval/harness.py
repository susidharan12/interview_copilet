from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.schemas.question import ClassificationResult
from app.services.classification import QuestionClassifier
from app.services.retrieval.hybrid import RAGPipeline


@dataclass
class EvalItem:
    id: str
    category: str
    question: str
    expected: str
    technology: str | None = None
    difficulty: str | None = None


@dataclass
class EvalReport:
    items_processed: int = 0
    classification_accuracy: float = 0.0
    retrieval_hits: int = 0
    retrieval_total: int = 0
    by_category: dict[str, dict[str, float]] = field(default_factory=dict)


async def load_dataset(path: Path) -> list[EvalItem]:
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            data = json.loads(line)
            items.append(EvalItem(
                id=data["id"],
                category=data["category"],
                question=data["question"],
                expected=data["expected_keywords"][0] if data.get("expected_keywords") else "",
                technology=data.get("technology"),
                difficulty=data.get("difficulty"),
            ))
    return items


async def run_classification_eval(items: list[EvalItem]) -> tuple[int, int, dict[str, int]]:
    classifier = QuestionClassifier()
    correct = 0
    by_cat: dict[str, int] = {}
    for item in items:
        result: ClassificationResult = await classifier.classify(item.question)
        is_correct = result.category == item.category
        correct += int(is_correct)
        by_cat[item.category] = by_cat.get(item.category, 0) + int(is_correct)
    return correct, len(items), by_cat


async def run_retrieval_eval(items: list[EvalItem], session) -> tuple[int, int]:
    rag = RAGPipeline(session)
    hits = 0
    total = 0
    for item in items:
        if not item.expected:
            continue
        candidates, _ = await rag.retrieve(item.question, top_k=10)
        total += 1
        if candidates and item.expected.lower() in candidates[0].content.lower():
            hits += 1
    return hits, total


async def evaluate(session, dataset_path: Path) -> EvalReport:
    items = await load_dataset(dataset_path)
    report = EvalReport(items_processed=len(items))

    correct, total, by_cat = await run_classification_eval(items)
    report.classification_accuracy = correct / total if total else 0.0
    hits, retrieved = await run_retrieval_eval(items, session)
    report.retrieval_hits, report.retrieval_total = hits, retrieved
    report.by_category = {
        cat: {"correct": correct, "total": sum(1 for i in items if i.category == cat)}
        for cat, correct in by_cat.items()
    }
    return report


async def main() -> None:
    from app.core.database import async_session_factory

    dataset = Path(__file__).parent / "datasets" / "sample_questions.jsonl"
    async with async_session_factory() as db:
        report = await evaluate(db, dataset)
    print(json.dumps(report, indent=2, default=str))