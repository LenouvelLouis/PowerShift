"""FastAPI application factory — registers the v1 router and the /health check."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.config import settings
from app.infrastructure.db.init_db import init_db


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
    # Remove non-serializable 'ctx' field from errors
    clean_errors = [
        {k: v for k, v in err.items() if k != "ctx"}
        for err in errors
    ]
    return JSONResponse(status_code=422, content={"detail": clean_errors})


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
