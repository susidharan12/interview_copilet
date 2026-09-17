from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "change-me-in-production"
    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/interview_copilot"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_org_id: str = ""
    default_model: str = "gpt-4.1-nano"
    reasoning_model: str = "gpt-4.1"
    coding_model: str = "gpt-4.1"
    embedding_model: str = "text-embedding-3-small"
    transcription_model: str = "gpt-4o-transcribe"

    rate_limit_per_minute: int = 60

    transcript_retention_days: int = 7
    audio_retention_hours: int = 24

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:1420"]

    rag_top_k: int = 20
    rerank_top_n: int = 10
    rag_token_budget: int = 4000
    bm25_weight: float = 0.4
    vector_weight: float = 0.6

    coding_cpu_limit: float = 0.5
    coding_memory_limit: str = "256m"
    coding_timeout_seconds: int = 30

    embedding_dimensions: int = 1536

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
