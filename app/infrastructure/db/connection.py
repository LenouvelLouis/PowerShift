"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel  # noqa: F401 — re-exported so seed.py can use SQLModel.metadata

from app.infrastructure.secrets.settings import get_settings


def _make_engine():
    from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

    url = get_settings().DATABASE_URL
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and fill it in."
        )

    # asyncpg doesn't accept libpq params (sslmode, channel_binding).
    # Convert sslmode=require → ssl=require and drop unsupported params.
    parsed = urlparse(url)
    scheme = parsed.scheme
    if scheme in ("postgresql", "postgres"):
        scheme = "postgresql+asyncpg"
    params = parse_qs(parsed.query, keep_blank_values=True)
    ssl_val = None
    if "sslmode" in params:
        sslmode = params.pop("sslmode")[0]
        if sslmode in ("require", "verify-ca", "verify-full"):
            ssl_val = "require"
    params.pop("channel_binding", None)
    if ssl_val:
        params["ssl"] = [ssl_val]
    new_query = urlencode({k: v[0] for k, v in params.items()})
    url = urlunparse((scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    return create_async_engine(
        url,
        pool_pre_ping=True,   # handles NeonDB idle connection drops
        echo=get_settings().DEBUG,
    )


# Lazily created so tests can override settings before first import
_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = _make_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,  # prevents DetachedInstanceError in async context
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an AsyncSession, auto-commits or rolls back."""
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
