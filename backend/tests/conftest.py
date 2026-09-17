from __future__ import annotations

from typing import AsyncGenerator, TypeVar

import pytest

T = TypeVar("T")


@pytest.fixture
def make_session():
    """Injection point for a real async DB session factory.

    Pure-logic tests do not require a database. Integration tests that need
    PostgreSQL + pgvector can supply this fixture (see infra/dev-db).
    """
    class DummySession:
        async def execute(self, *a, **k):
            raise RuntimeError("Dummy session is not a real DB; run integration tests with PostgreSQL.")

        async def add(self, *a, **k):
            pass

        async def commit(self):
            pass

        async def refresh(self, *a, **k):
            pass

        async def rollback(self):
            pass

    async def _factory() -> AsyncGenerator:
        yield DummySession()

    return _factory