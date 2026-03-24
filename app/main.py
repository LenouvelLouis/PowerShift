"""FastAPI application factory — registers the v1 router and the /health check."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
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
