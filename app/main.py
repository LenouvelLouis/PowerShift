"""FastAPI application factory — registers the v1 router and the /health check."""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.api.v1.router import router as v1_router
from app.config import settings
from app.infrastructure.db.connection import get_db
from app.infrastructure.db.init_db import init_db
from app.infrastructure.logging import request_id_ctx, setup_logging

# ---------------------------------------------------------------------------
# Logging — must be configured before anything else emits logs
# ---------------------------------------------------------------------------
setup_logging(environment=settings.ENVIRONMENT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

_cors_origins: list[str] = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if settings.FRONTEND_URL:
    _cors_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_log = logging.getLogger("app")


# ---------------------------------------------------------------------------
# Request-ID middleware — correlates every log line within one request
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_id_middleware(request: Request, call_next) -> Response:  # noqa: ANN001
    """Attach a unique request_id to every request via contextvars."""
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request_id_ctx.set(rid)
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


# ---------------------------------------------------------------------------
# Rate limiting (slowapi)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

API_V1_PREFIX = "/api/v1"
app.include_router(v1_router, prefix=API_V1_PREFIX)

# ---------------------------------------------------------------------------
# Exception handlers — structured error responses with error codes
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    if errors and all(
        len(err.get("loc", [])) >= 1 and err["loc"][0] == "path"
        for err in errors
    ):
        return JSONResponse(status_code=404, content={"detail": "Not found", "code": "ERR_NOT_FOUND"})
    # Remove non-serializable 'ctx' field from errors
    clean_errors = [
        {k: v for k, v in err.items() if k != "ctx"}
        for err in errors
    ]
    return JSONResponse(status_code=422, content={"detail": clean_errors, "code": "ERR_VALIDATION"})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": f"ERR_HTTP_{exc.status_code}"},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _log.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "ERR_INTERNAL"},
    )


# ---------------------------------------------------------------------------
# Health check — verifies DB connectivity
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Returns the API status and metadata, including database connectivity."""
    base = {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
    try:
        await db.execute(text("SELECT 1"))
        return JSONResponse(content={"status": "ok", "database": "connected", **base})
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "disconnected", **base},
        )
