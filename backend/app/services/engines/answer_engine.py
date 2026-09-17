from __future__ import annotations

from collections.abc import AsyncIterator

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from app.core.config import settings
from app.services.engines.prompts import EngineInput, build_system_prompt, build_user_prompt


class AnswerEngine:
    """Streams answers from the LLM for a given engine input + model.

    All specialized engines (technical/scenario/coding/behavioral) share this
    thin streaming wrapper; their identity lives in the prompt templates so
    each stays independently tunable.
    """

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)

    async def stream(self, inp: EngineInput, model: str) -> AsyncIterator[str]:
        stream: AsyncStream[ChatCompletionChunk] = await self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": build_system_prompt(inp)},
                {"role": "user", "content": build_user_prompt(inp)},
            ],
            temperature=0.3,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def complete(self, inp: EngineInput, model: str) -> str:
        resp: ChatCompletion = await self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": build_system_prompt(inp)},
                {"role": "user", "content": build_user_prompt(inp)},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content or ""