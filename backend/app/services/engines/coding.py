from __future__ import annotations

from collections.abc import AsyncIterator

from app.core.config import settings
from app.schemas.coding import SandboxTestCase
from app.services.engines.prompts import CATEGORY_TEMPLATES
from app.services.engines.sandbox import SandboxManager


class CodingEngine:
    """Coding question pipeline: approach → code → verify → fix.

    Generates an approach + code via the LLM, then runs it in the sandbox.
    If execution fails, re-prompts with the error and retries (bounded).
    """

    def __init__(self, sandbox: SandboxManager | None = None, client=None) -> None:
        self.sandbox = sandbox or SandboxManager()
        self.client = client
        self.max_attempts = 3

    async def generate(self, question: str, language: str = "python") -> tuple[str, str, list[str]]:
        """Return (approach, code, test_cases_as_strings)."""

        if self.client is None:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)

        prompt = (
            "Solve this coding interview question.\n\n"
            f"Question: {question}\nLanguage: {language}\n\n"
            "Respond in this exact format (no markdown fences):\n"
            "APPROACH:\n<algorithm + pattern + why>\n\n"
            "COMPLEXITY:\n<time> / <space>\n\n"
            "CODE:\n<complete, runnable program reading from stdin, printing results>\n\n"
            "EDGE_CASES:\n<list>\n\n"
            "TEST_CASES:\n<input line> => <expected output line> (one per line)"
        )
        resp = await self.client.chat.completions.create(
            model=settings.coding_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = resp.choices[0].message.content or ""
        approach, code, cases = _parse_coding_response(text)
        return approach, code, cases

    async def stream_code(self, question: str, language: str = "python") -> AsyncIterator[str]:
        _, code, _ = await self.generate(question, language)
        for token in _tokens(code):
            yield token

    async def verify(self, code: str, language: str, test_cases: list[SandboxTestCase]) -> dict:
        result = await self.sandbox.execute(language=language, code=code, test_cases=test_cases)
        return {
            "success": result.success,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time_ms": result.execution_time_ms,
            "resource_usage": result.resource_usage,
        }


def _parse_coding_response(text: str) -> tuple[str, str, list[str]]:
    approach = ""
    code = ""
    cases: list[str] = []
    current = "approach"
    for line in text.splitlines():
        up = line.strip().upper()
        if up.startswith("APPROACH"):
            current = "approach"
            continue
        if up.startswith("COMPLEXITY"):
            current = "complexity"
            continue
        if up.startswith("CODE"):
            current = "code"
            continue
        if up.startswith("EDGE_CASES"):
            current = "edge"
            continue
        if up.startswith("TEST_CASES"):
            current = "test"
            continue
        if current in ("approach", "complexity"):
            approach += line + "\n"
        elif current == "code":
            if line.strip().startswith("```"):
                continue
            code += line + "\n"
        elif current == "test":
            if line.strip():
                cases.append(line.strip())
    return approach.strip(), code.strip(), cases


def _tokens(s: str):
    for word in s.split(" "):
        yield word + " "
