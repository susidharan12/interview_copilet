from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import answers, coding, documents, feedback, profile, questions, search, sessions, ws
from app.core.config import settings
from app.core.redis import close_redis
from app.core.telemetry import init_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_telemetry()
    yield
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Interview Copilot API",
        version="0.1.0",
        description="Realtime AI interview support backend.",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(sessions.router, prefix="/api/v1")
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(questions.router, prefix="/api/v1")
    app.include_router(answers.router, prefix="/api/v1")
    app.include_router(coding.router, prefix="/api/v1")
    app.include_router(feedback.router, prefix="/api/v1")
    app.include_router(profile.router, prefix="/api/v1")
    app.include_router(ws.router)

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "app": "interview-copilot",
                "version": "0.1.0",
                "environment": settings.app_env,
            }
        )

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
        log_level="info",
    )