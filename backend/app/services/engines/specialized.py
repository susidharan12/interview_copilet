from __future__ import annotations

from app.services.engines.prompts import EngineInput, build_system_prompt, build_user_prompt


class TechnicalEngine:
    """Technical question answerer: direct answer + explanation + example."""

    async def prepare(self, inp: EngineInput) -> tuple[str, str]:
        return build_system_prompt(inp), build_user_prompt(inp)


class ScenarioEngine:
    """Scenario/system-design answerer using an investigation framework."""

    async def prepare(self, inp: EngineInput) -> tuple[str, str]:
        return build_system_prompt(inp), build_user_prompt(inp)


class BehavioralEngine:
    """STAR-structured behavioral answers anchored to the real profile."""

    async def prepare(self, inp: EngineInput) -> tuple[str, str]:
        return build_system_prompt(inp), build_user_prompt(inp)