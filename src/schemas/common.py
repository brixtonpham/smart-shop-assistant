"""Common Pydantic schemas used across the application.

Schemas:
    - Pagination: Pagination parameters
    - PaginatedResponse: Generic paginated response
    - ErrorResponse: Standard error format
    - SuccessResponse: Standard success format
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class Pagination(BaseModel):
    """Pagination request parameters.

    Attributes:
        page: Current page number (1-indexed)
        limit: Number of items per page
    """

    page: int = Field(
        default=1,
        ge=1,
        description="Current page number (1-indexed)",
        examples=[1],
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of items per page (max 100)",
        examples=[10],
    )

    model_config = {"json_schema_extra": {"examples": [{"page": 1, "limit": 10}]}}


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.

    Attributes:
        items: List of items for current page
        total: Total number of items across all pages
        page: Current page number
        limit: Items per page
        pages: Total number of pages
    """

    items: list[T] = Field(description="List of items for current page")
    total: int = Field(ge=0, description="Total number of items across all pages")
    page: int = Field(ge=1, description="Current page number")
    limit: int = Field(ge=1, le=100, description="Items per page")
    pages: int = Field(ge=0, description="Total number of pages")

    @field_validator("pages", mode="before")
    @classmethod
    def calculate_pages(cls, v: int | None, info) -> int:
        """Calculate total pages from total and limit if not provided."""
        if v is not None:
            return v
        # Access values dict to get total and limit
        total = info.data.get("total", 0)
        limit = info.data.get("limit", 1)
        return (total + limit - 1) // limit if limit > 0 else 0

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [],
                    "total": 100,
                    "page": 1,
                    "limit": 10,
                    "pages": 10,
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response format.

    Attributes:
        code: Error code (e.g., 'VALIDATION_ERROR', 'NOT_FOUND')
        message: Human-readable error message
        details: Optional additional error details
    """

    code: str = Field(
        description="Error code",
        examples=["VALIDATION_ERROR", "NOT_FOUND", "INTERNAL_ERROR"],
    )
    message: str = Field(
        description="Human-readable error message",
        examples=["The requested resource was not found"],
    )
    details: dict[str, Any] | None = Field(
        default=None,
        description="Optional additional error details",
        examples=[{"field": "email", "issue": "Invalid email format"}],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": {"field": "price", "issue": "Must be greater than 0"},
                }
            ]
        }
    }


class SuccessResponse(BaseModel):
    """Standard success response format.

    Attributes:
        success: Success flag (always True)
        message: Human-readable success message
        data: Optional response data
    """

    success: bool = Field(
        default=True,
        description="Success flag (always True)",
        examples=[True],
    )
    message: str = Field(
        description="Human-readable success message",
        examples=["Operation completed successfully"],
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Optional response data",
        examples=[{"id": "123e4567-e89b-12d3-a456-426614174000"}],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Order created successfully",
                    "data": {"order_id": "123e4567-e89b-12d3-a456-426614174000"},
                }
            ]
        }
    }
