"""
Shared / common Pydantic schemas used across multiple endpoints.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Simple message envelope."""

    message: str
    detail: str | None = None


class HealthCheckResponse(BaseModel):
    """Response model for the /health endpoint."""

    status: str = "ok"
    version: str


class ErrorResponse(BaseModel):
    """Standardised error envelope returned by exception handlers."""

    error_code: str
    message: str
    detail: str | None = None


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Items per page (max 100)"
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
