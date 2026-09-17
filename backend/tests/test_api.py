from __future__ import annotations

import pytest

from app.schemas.coding import CodeExecuteRequest, SandboxTestCase
from app.schemas.question import ClassificationResult, ClassifyRequest
from app.schemas.session import SessionCreate, SessionSettings


def test_session_create_schema():
    body = SessionCreate(mode="interview", settings={"answer_mode": "quick"})
    assert body.settings.answer_mode.value == "quick"


def test_classification_schema_validation():
    result = ClassificationResult(
        category="coding",
        technology="python",
        difficulty="medium",
        requires_retrieval=True,
        requires_reasoning=True,
        requires_code_execution=True,
        requires_screen_context=False,
        confidence=0.9,
    )
    assert result.category == "coding"


def test_classification_rejects_bad_category():
    with pytest.raises(Exception):
        ClassificationResult(category="not-a-category")


def test_code_execute_request_language_whitelist():
    assert CodeExecuteRequest(language="python", code="x = 1")
    with pytest.raises(Exception):
        CodeExecuteRequest(language="cobol", code="x")


def test_classify_request_min_length():
    with pytest.raises(Exception):
        ClassifyRequest(question_text="")


def test_testcase_model():
    tc = SandboxTestCase(input="nums=[2,7,11,15], target=9", expected="[0,1]")
    assert tc.input  # non-empty
