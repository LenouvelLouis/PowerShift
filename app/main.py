from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings

# --------------------------------------------------
# Application setup
# --------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Global prefix for all future routers
API_V1_PREFIX = "/api/v1"

# --------------------------------------------------
# Router registration (uncomment as features are added)
# --------------------------------------------------
# from app.routers import network, supply
# app.include_router(network.router, prefix=API_V1_PREFIX)
# app.include_router(supply.router, prefix=API_V1_PREFIX)


# --------------------------------------------------
# Health check
# --------------------------------------------------
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
