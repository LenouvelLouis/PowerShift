# Root entry point — re-exports the FastAPI app so `uvicorn main:app --reload` works.
from app.main import app  # noqa: F401

__all__ = ["app"]
