from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings
from app.schemas.coding import SandboxTestCase, TestResult

SUPPORTED = {"python", "javascript", "typescript", "java", "kotlin", "cpp", "sql"}

LANG_RUNNERS: dict[str, dict[str, str]] = {
    "python": {
        "image": "python:3.12-slim",
        "source": "solution.py",
        "run": ["python", "solution.py"],
    },
    "javascript": {
        "image": "node:20-slim",
        "source": "solution.js",
        "run": ["node", "solution.js"],
    },
    "typescript": {
        "image": "node:20-slim",
        "source": "solution.ts",
        "run": ["npx", "tsx", "solution.ts"],
    },
    "java": {
        "image": "eclipse-temurin:21",
        "source": "Main.java",
        "run": ["sh", "-c", "javac Main.java && java Main"],
    },
    "kotlin": {
        "image": "kotlin:2.0",
        "source": "Main.kt",
        "run": ["sh", "-c", "kotlinc Main.kt -include-runtime -d main.jar && java -jar main.jar"],
    },
    "cpp": {
        "image": "gcc:13",
        "source": "solution.cpp",
        "run": ["sh", "-c", "g++ -O2 -std=c++17 solution.cpp -o solution && ./solution"],
    },
    "sql": {
        "image": "python:3.12-slim",
        "source": "solution.sql",
        "run": ["sh", "-c", "python /usr/local/bin/_sql_runner.py"],
    },
}


@dataclass
class ExecutionResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: int
    test_results: list[TestResult] | None = None
    resource_usage: dict[str, Any] = field(default_factory=dict)


class LocalSandbox:
    """Fallback executor for development/testing without Docker.

    Runs the code as a subprocess with a wall-clock timeout. Weaker isolation
    than Docker — production MUST use the DockerSandbox.
    """

    def __init__(self, timeout_seconds: int | None = None) -> None:
        self.default_timeout = timeout_seconds or settings.coding_timeout_seconds

    async def execute(
        self,
        language: str,
        code: str,
        test_cases: list[SandboxTestCase] | None = None,
        timeout_seconds: int | None = None,
    ) -> ExecutionResult:
        runner = LANG_RUNNERS.get(language)
        if runner is None:
            return ExecutionResult(False, 1, "", f"Unsupported language: {language}", 0)

        tmpdir = tempfile.mkdtemp(prefix="ic-sandbox-")
        start = asyncio.get_event_loop().time()
        try:
            source_path = os.path.join(tmpdir, runner["source"])
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(_wrap_with_tests(code, test_cases or [], language))

            proc = await asyncio.create_subprocess_exec(
                *runner["run"],
                cwd=tmpdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout_seconds or self.default_timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return ExecutionResult(False, -1, "", "Execution timed out", int((asyncio.get_event_loop().time() - start) * 1000))

            stdout_s, stderr_s = stdout.decode(errors="replace"), stderr.decode(errors="replace")
            return ExecutionResult(
                success=proc.returncode == 0,
                exit_code=proc.returncode or 0,
                stdout=stdout_s,
                stderr=stderr_s,
                execution_time_ms=int((asyncio.get_event_loop().time() - start) * 1000),
            )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class DockerSandbox:
    """Production isolated execution via Docker. Requires docker daemon."""

    def __init__(self) -> None:
        self._available = shutil.which("docker") is not None

    @property
    def available(self) -> bool:
        return self._available

    async def execute(
        self,
        language: str,
        code: str,
        test_cases: list[SandboxTestCase] | None = None,
        timeout_seconds: int | None = None,
    ) -> ExecutionResult:
        if not self._available:
            raise RuntimeError("Docker unavailable; use LocalSandbox in development.")

        runner = LANG_RUNNERS.get(language)
        if runner is None:
            return ExecutionResult(False, 1, "", f"Unsupported language: {language}", 0)

        container_name = f"ic-sandbox-{uuid.uuid4().hex[:10]}"
        vol_dir = tempfile.mkdtemp(prefix="ic-sandbox-vol-")
        timeout = timeout_seconds or self.default_timeout
        start = asyncio.get_event_loop().time()
        try:
            source_path = os.path.join(vol_dir, runner["source"])
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(_wrap_with_tests(code, test_cases or [], language))

            proc = await asyncio.create_subprocess_exec(
                "docker", "run", "--rm", "--name", container_name,
                "--cpus", str(settings.coding_cpu_limit),
                "--memory", settings.coding_memory_limit,
                "--network", "none",
                "--pids-limit", "64",
                "--security-opt", "no-new-privileges",
                "--cap-drop", "ALL",
                "--tmpfs", "/tmp:size=100m",
                "-v", f"{vol_dir}:/workspace:ro",
                "-w", "/workspace",
                runner["image"],
                *runner["run"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await _docker("kill", container_name)
                return ExecutionResult(False, -1, "", "Execution timed out", int((asyncio.get_event_loop().time() - start) * 1000))

            stdout_s, stderr_s = stdout.decode(errors="replace"), stderr.decode(errors="replace")
            return ExecutionResult(
                success=proc.returncode == 0,
                exit_code=proc.returncode or 0,
                stdout=stdout_s,
                stderr=stderr_s,
                execution_time_ms=int((asyncio.get_event_loop().time() - start) * 1000),
            )
        finally:
            shutil.rmtree(vol_dir, ignore_errors=True)


async def _docker(*args: str) -> None:
    proc = await asyncio.create_subprocess_exec("docker", *args)
    await proc.wait()


class SandboxManager:
    """Chooses Docker when available, else local subprocess fallback."""

    def __init__(self) -> None:
        self.docker = DockerSandbox()
        self.local = LocalSandbox()

    async def execute(
        self,
        language: str,
        code: str,
        test_cases: list[SandboxTestCase] | None = None,
        timeout_seconds: int | None = None,
    ) -> ExecutionResult:
        if language not in SUPPORTED:
            return ExecutionResult(False, 1, "", f"Unsupported language: {language}", 0)
        if self.docker.available:
            try:
                return await self.docker.execute(language, code, test_cases, timeout_seconds)
            except Exception as exc:  # docker runtime failure → degrade
                return await self._degrade(language, code, test_cases, timeout_seconds, exc)
        return await self.local.execute(language, code, test_cases, timeout_seconds)

    async def _degrade(self, language, code, test_cases, timeout, exc: Exception) -> ExecutionResult:
        result = await self.local.execute(language, code, test_cases, timeout)
        result.stderr = (result.stderr + f"\n[docker-fallback:{type(exc).__name__}]").strip()
        return result


def _wrap_with_tests(code: str, test_cases: list[SandboxTestCase], language: str) -> str:
    code = code.rstrip()
    if not test_cases:
        return code
    if language == "python":
        return code + "\n\n" + "\n".join(_py_assert(t) for t in test_cases)
    return code


def _py_assert(tc: SandboxTestCase) -> str:
    return f'assert {tc.input.strip()} == {tc.expected.strip()}, "{tc.input} expected {tc.expected}"'
