"""FastAPI application factory — registers the v1 router and the /health check."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.config import settings


async def _init_db() -> None:
    """Create all tables on startup (idempotent — safe to run every time)."""
    # Import models so SQLModel.metadata knows about them
    import app.infrastructure.db.models.supply_model  # noqa: F401
    import app.infrastructure.db.models.demand_model  # noqa: F401
    import app.infrastructure.db.models.network_model  # noqa: F401
    import app.infrastructure.db.models.simulation_request_model  # noqa: F401
    import app.infrastructure.db.models.simulation_result_model  # noqa: F401
    import app.infrastructure.db.models.pv_hourly_model  # noqa: F401

    from sqlmodel import SQLModel
    from app.infrastructure.db.connection import get_engine

    from sqlalchemy import text

    async with get_engine().begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        # Idempotent migration: add overrides column if it doesn't exist yet
        await conn.execute(
            text("ALTER TABLE simulation_requests ADD COLUMN IF NOT EXISTS overrides JSONB")
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_V1_PREFIX = "/api/v1"
app.include_router(v1_router, prefix=API_V1_PREFIX)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    if errors and all(
        len(err.get("loc", [])) >= 1 and err["loc"][0] == "path"
        for err in errors
    ):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """Returns the API status and metadata."""
    return JSONResponse(
        content={
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }
    )
