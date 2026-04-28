"""API key authentication dependency for FastAPI."""

from __future__ import annotations

from fastapi import HTTPException, Query, Request, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    request: Request,
    header_key: str | None = Security(_api_key_header),
    query_key: str | None = Query(None, alias="api_key", include_in_schema=False),
) -> str | None:
    """Validate the API key from header or query parameter.

    When ``API_KEY`` is empty (default), authentication is skipped entirely
    so that local development stays frictionless.

    Returns the validated key on success, or ``None`` in dev mode.
    """
    expected = settings.API_KEY
    if not expected:
        # Dev mode — no auth required
        return None

    provided = header_key or query_key
    if not provided or provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return provided
