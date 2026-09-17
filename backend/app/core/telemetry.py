from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

from app.core.config import settings

_tracer_provider: TracerProvider | None = None


def init_telemetry() -> None:
    global _tracer_provider
    if _tracer_provider is not None:
        return
    _tracer_provider = TracerProvider()
    _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(_tracer_provider)


def get_tracer(name: str = "interview-copilot") -> trace.Tracer:
    return trace.get_tracer(name)


@asynccontextmanager
async def trace_span(name: str, attributes: dict[str, str] | None = None) -> AsyncGenerator[trace.Span, None]:
    tracer = get_tracer()
    with tracer.start_as_current_span(name, attributes=attributes) as span:
        yield span
