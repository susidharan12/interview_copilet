from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

redis_client: aioredis.Redis | None = None


async def get_redis() -> CacheService:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return CacheService(redis_client)


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


class CacheService:
    def __init__(self, client: aioredis.Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> None:
        await self._client.set(key, value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self._client.exists(key))

    async def increment(self, key: str, ttl_seconds: int = 60) -> int:
        val = await self._client.incr(key)
        if val == 1:
            await self._client.expire(key, ttl_seconds)
        return val

    async def hash_set(self, name: str, mapping: dict[str, Any]) -> None:
        await self._client.hset(name, mapping=mapping)

    async def hash_get(self, name: str, key: str) -> str | None:
        return await self._client.hget(name, key)
