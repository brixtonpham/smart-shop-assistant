"""Order-related Pydantic schemas.

Schemas:
    - OrderItemBase: Base order item fields
    - OrderItemCreate: For creating order items
    - OrderItem: Individual order line item
    - OrderBase: Base order fields
    - OrderCreate: Order creation request
    - Order: Full order details
    - OrderWithDiscount: Order with applied coupon
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.database.models import OrderStatus


class OrderItemBase(BaseModel):
    """Base order item fields.

    Attributes:
        product_id: Product identifier
        quantity: Quantity ordered
        price_each: Price per unit at time of order
    """

    product_id: UUID = Field(
        description="Product identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    quantity: int = Field(
        gt=0,
        description="Quantity ordered (must be greater than 0)",
        examples=[2],
    )
    price_each: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Price per unit at time of order",
        examples=[Decimal("29.99")],
    )

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("price_each")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price is positive."""
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product_id": "123e4567-e89b-12d3-a456-426614174000",
                    "quantity": 2,
                    "price_each": "29.99",
                }
            ]
        }
    }


class OrderItemCreate(OrderItemBase):
    """Schema for creating an order item.

    Inherits all fields from OrderItemBase.
    """

    pass


class OrderItem(OrderItemBase):
    """Full order item with additional details.

    Attributes:
        id: Unique order item identifier
        order_id: Associated order identifier
        product_name: Name of the product (from Product)
        product_sku: SKU of the product (from Product)
    """

    id: UUID = Field(
        description="Unique order item identifier",
        examples=["456e7890-e89b-12d3-a456-426614174000"],
    )
    order_id: UUID = Field(
        description="Associated order identifier",
        examples=["789e0123-e89b-12d3-a456-426614174000"],
    )
    product_name: str | None = Field(
        default=None,
        description="Name of the product",
        examples=["Wireless Mouse"],
    )
    product_sku: str | None = Field(
        default=None,
        description="SKU of the product",
        examples=["WM-001"],
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "456e7890-e89b-12d3-a456-426614174000",
                    "order_id": "789e0123-e89b-12d3-a456-426614174000",
                    "product_id": "123e4567-e89b-12d3-a456-426614174000",
                    "product_name": "Wireless Mouse",
                    "product_sku": "WM-001",
                    "quantity": 2,
                    "price_each": "29.99",
                }
            ]
        },
    }


class OrderBase(BaseModel):
    """Base order fields.

    Attributes:
        customer_id: Customer identifier
        status: Order status
    """

    customer_id: UUID = Field(
        description="Customer identifier",
        examples=["abc12345-e89b-12d3-a456-426614174000"],
    )
    status: OrderStatus = Field(
        default=OrderStatus.PENDING,
        description="Order status",
        examples=[OrderStatus.PENDING],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "customer_id": "abc12345-e89b-12d3-a456-426614174000",
                    "status": "pending",
                }
            ]
        }
    }


class OrderCreate(BaseModel):
    """Schema for creating a new order.

    Attributes:
        customer_id: Customer identifier
        items: List of order items to create
    """

    customer_id: UUID = Field(
        description="Customer identifier",
        examples=["abc12345-e89b-12d3-a456-426614174000"],
    )
    items: list[OrderItemCreate] = Field(
        min_length=1,
        description="List of order items (at least one required)",
        examples=[
            [
                {
                    "product_id": "123e4567-e89b-12d3-a456-426614174000",
                    "quantity": 2,
                    "price_each": "29.99",
                }
            ]
        ],
    )

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: list[OrderItemCreate]) -> list[OrderItemCreate]:
        """Validate at least one item exists."""
        if not v:
            raise ValueError("Order must have at least one item")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "customer_id": "abc12345-e89b-12d3-a456-426614174000",
                    "items": [
                        {
                            "product_id": "123e4567-e89b-12d3-a456-426614174000",
                            "quantity": 2,
                            "price_each": "29.99",
                        }
                    ],
                }
            ]
        }
    }


class Order(OrderBase):
    """Full order response with items and timestamps.

    Attributes:
        id: Unique order identifier
        total: Order total amount
        items: List of order items
        customer_name: Name of the customer
        customer_email: Email of the customer
        created_at: Timestamp when order was created
        updated_at: Timestamp when order was last updated
    """

    id: UUID = Field(
        description="Unique order identifier",
        examples=["789e0123-e89b-12d3-a456-426614174000"],
    )
    total: Decimal = Field(
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Order total amount",
        examples=[Decimal("59.98")],
    )
    items: list[OrderItem] = Field(
        description="List of order items",
        examples=[[]],
    )
    customer_name: str | None = Field(
        default=None,
        description="Name of the customer",
        examples=["John Doe"],
    )
    customer_email: str | None = Field(
        default=None,
        description="Email of the customer",
        examples=["john.doe@example.com"],
    )
    created_at: datetime = Field(
        description="Timestamp when order was created",
        examples=["2024-01-15T10:30:00Z"],
    )
    updated_at: datetime = Field(
        description="Timestamp when order was last updated",
        examples=["2024-01-15T10:30:00Z"],
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "789e0123-e89b-12d3-a456-426614174000",
                    "customer_id": "abc12345-e89b-12d3-a456-426614174000",
                    "customer_name": "John Doe",
                    "customer_email": "john.doe@example.com",
                    "status": "pending",
                    "total": "59.98",
                    "items": [
                        {
                            "id": "456e7890-e89b-12d3-a456-426614174000",
                            "order_id": "789e0123-e89b-12d3-a456-426614174000",
                            "product_id": "123e4567-e89b-12d3-a456-426614174000",
                            "product_name": "Wireless Mouse",
                            "product_sku": "WM-001",
                            "quantity": 2,
                            "price_each": "29.99",
                        }
                    ],
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            ]
        },
    }


class OrderWithDiscount(Order):
    """Order with discount applied.

    Attributes:
        discount_amount: Discount amount applied
        final_total: Final total after discount
        coupon_code: Applied coupon code
    """

    discount_amount: Decimal = Field(
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Discount amount applied",
        examples=[Decimal("5.99")],
    )
    final_total: Decimal = Field(
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Final total after discount",
        examples=[Decimal("53.99")],
    )
    coupon_code: str | None = Field(
        default=None,
        description="Applied coupon code",
        examples=["SAVE10"],
    )

    @field_validator("discount_amount")
    @classmethod
    def validate_discount(cls, v: Decimal) -> Decimal:
        """Validate discount is non-negative."""
        if v < 0:
            raise ValueError("Discount amount cannot be negative")
        return v

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "789e0123-e89b-12d3-a456-426614174000",
                    "customer_id": "abc12345-e89b-12d3-a456-426614174000",
                    "customer_name": "John Doe",
                    "customer_email": "john.doe@example.com",
                    "status": "pending",
                    "total": "59.98",
                    "discount_amount": "5.99",
                    "final_total": "53.99",
                    "coupon_code": "SAVE10",
                    "items": [
                        {
                            "id": "456e7890-e89b-12d3-a456-426614174000",
                            "order_id": "789e0123-e89b-12d3-a456-426614174000",
                            "product_id": "123e4567-e89b-12d3-a456-426614174000",
                            "product_name": "Wireless Mouse",
                            "product_sku": "WM-001",
                            "quantity": 2,
                            "price_each": "29.99",
                        }
                    ],
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            ]
        },
    }
