"""FastAPI application factory — registers the v1 router and the /health check."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

API_V1_PREFIX = "/api/v1"
app.include_router(v1_router, prefix=API_V1_PREFIX)


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
