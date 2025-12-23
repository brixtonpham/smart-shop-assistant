"""Product-related Pydantic schemas.

Schemas:
    - ProductBase: Base fields for product
    - ProductCreate: For creating products
    - Product: Full product details
    - ProductList: Paginated product list
    - StockCheck: Stock availability response
    - Reservation: Stock reservation details
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.schemas.common import PaginatedResponse


class ProductBase(BaseModel):
    """Base product fields shared across schemas.

    Attributes:
        name: Product name
        category: Product category
        price: Product price
        stock: Current stock quantity
        sku: Stock Keeping Unit (unique identifier)
        description: Optional product description
    """

    name: str = Field(
        min_length=1,
        max_length=200,
        description="Product name",
        examples=["Wireless Mouse"],
    )
    category: str = Field(
        min_length=1,
        max_length=100,
        description="Product category",
        examples=["Electronics"],
    )
    price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Product price (must be greater than 0)",
        examples=[Decimal("29.99")],
    )
    stock: int = Field(
        ge=0,
        description="Current stock quantity (must be non-negative)",
        examples=[100],
    )
    sku: str = Field(
        min_length=1,
        max_length=50,
        description="Stock Keeping Unit (unique identifier)",
        examples=["WM-001"],
    )
    description: str | None = Field(
        default=None,
        description="Optional product description",
        examples=["Ergonomic wireless mouse with USB receiver"],
    )

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price is positive."""
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    @field_validator("stock")
    @classmethod
    def validate_stock(cls, v: int) -> int:
        """Validate stock is non-negative."""
        if v < 0:
            raise ValueError("Stock cannot be negative")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Wireless Mouse",
                    "category": "Electronics",
                    "price": "29.99",
                    "stock": 100,
                    "sku": "WM-001",
                    "description": "Ergonomic wireless mouse with USB receiver",
                }
            ]
        }
    }


class ProductCreate(ProductBase):
    """Schema for creating a new product.

    Inherits all fields from ProductBase.
    """

    pass


class Product(ProductBase):
    """Full product response with timestamps.

    Attributes:
        id: Unique product identifier (UUID)
        created_at: Timestamp when product was created
        updated_at: Timestamp when product was last updated
    """

    id: UUID = Field(
        description="Unique product identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    created_at: datetime = Field(
        description="Timestamp when product was created",
        examples=["2024-01-15T10:30:00Z"],
    )
    updated_at: datetime = Field(
        description="Timestamp when product was last updated",
        examples=["2024-01-15T10:30:00Z"],
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Wireless Mouse",
                    "category": "Electronics",
                    "price": "29.99",
                    "stock": 100,
                    "sku": "WM-001",
                    "description": "Ergonomic wireless mouse with USB receiver",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            ]
        },
    }


class ProductList(PaginatedResponse[Product]):
    """Paginated list of products.

    Inherits pagination fields from PaginatedResponse with Product items.
    """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Wireless Mouse",
                            "category": "Electronics",
                            "price": "29.99",
                            "stock": 100,
                            "sku": "WM-001",
                            "description": "Ergonomic wireless mouse",
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-01-15T10:30:00Z",
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "limit": 10,
                    "pages": 1,
                }
            ]
        }
    }


class StockCheck(BaseModel):
    """Stock availability check response.

    Attributes:
        product_id: Product identifier
        available: Whether product has sufficient stock
        quantity: Current available quantity (stock - reserved)
        reserved: Total quantity currently reserved
    """

    product_id: UUID = Field(
        description="Product identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    available: bool = Field(
        description="Whether product has sufficient stock",
        examples=[True],
    )
    quantity: int = Field(
        ge=0,
        description="Current available quantity (stock - reserved)",
        examples=[95],
    )
    reserved: int = Field(
        ge=0,
        description="Total quantity currently reserved",
        examples=[5],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product_id": "123e4567-e89b-12d3-a456-426614174000",
                    "available": True,
                    "quantity": 95,
                    "reserved": 5,
                }
            ]
        }
    }


class Reservation(BaseModel):
    """Stock reservation details.

    Attributes:
        id: Unique reservation identifier
        product_id: Product being reserved
        quantity: Quantity reserved
        expires_at: Expiration timestamp for reservation
        order_id: Optional associated order identifier
        created_at: Timestamp when reservation was created
    """

    id: UUID = Field(
        description="Unique reservation identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    product_id: UUID = Field(
        description="Product being reserved",
        examples=["456e7890-e89b-12d3-a456-426614174000"],
    )
    quantity: int = Field(
        gt=0,
        description="Quantity reserved (must be greater than 0)",
        examples=[5],
    )
    expires_at: datetime = Field(
        description="Expiration timestamp for reservation",
        examples=["2024-01-15T11:00:00Z"],
    )
    order_id: UUID | None = Field(
        default=None,
        description="Optional associated order identifier",
        examples=["789e0123-e89b-12d3-a456-426614174000"],
    )
    created_at: datetime = Field(
        description="Timestamp when reservation was created",
        examples=["2024-01-15T10:30:00Z"],
    )

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError("Reservation quantity must be greater than 0")
        return v

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "product_id": "456e7890-e89b-12d3-a456-426614174000",
                    "quantity": 5,
                    "expires_at": "2024-01-15T11:00:00Z",
                    "order_id": "789e0123-e89b-12d3-a456-426614174000",
                    "created_at": "2024-01-15T10:30:00Z",
                }
            ]
        },
    }
