from __future__ import annotations

import uuid
from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import CacheService, get_redis
from app.core.security import decode_access_token

DbSession = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[CacheService, Depends(get_redis)]


async def get_current_user_id(authorization: str | None = None) -> uuid.UUID | None:
    """Resolve user id from bearer token. In dev, allow anonymous."""
    from app.core.config import settings

    if settings.is_development:
        return None
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        payload = decode_access_token(authorization.removeprefix("Bearer "))
        return uuid.UUID(payload.sub)
    except Exception:
        return None


async def authenticate_ws(websocket: WebSocket) -> uuid.UUID | None:
    token = websocket.query_params.get("token")
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        return uuid.UUID(payload.sub)
    except Exception:
        return None


def require_user(user_id: uuid.UUID | None) -> uuid.UUID:
    from app.core.config import settings

    if settings.is_development:
        return user_id or uuid.UUID("00000000-0000-0000-0000-000000000000")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user_id