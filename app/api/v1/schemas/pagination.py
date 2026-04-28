"""Shared pagination schemas for list endpoints."""

from __future__ import annotations

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed).")
    size: int = Field(default=20, ge=1, le=100, description="Number of items per page.")

    @property
    def offset(self) -> int:
        """Compute the SQL OFFSET from page and size."""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """Envelope returned by every paginated list endpoint."""

    items: list[T] = Field(description="Page of results.")
    total: int = Field(description="Total number of records matching the query.")
    page: int = Field(description="Current page number (1-indexed).")
    size: int = Field(description="Requested page size.")
    pages: int = Field(description="Total number of pages.")

    @classmethod
    def build(cls, *, items: list[T], total: int, page: int, size: int) -> PaginatedResponse[T]:
        """Construct a paginated response, computing `pages` automatically."""
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=max(1, math.ceil(total / size)),
        )
