"""Pydantic schemas for data validation."""

# Common schemas
from src.schemas.common import (
    ErrorResponse,
    PaginatedResponse,
    Pagination,
    SuccessResponse,
)

# Order schemas
from src.schemas.orders import (
    Order,
    OrderBase,
    OrderCreate,
    OrderItem,
    OrderItemBase,
    OrderItemCreate,
    OrderWithDiscount,
)

# Product schemas
from src.schemas.products import (
    Product,
    ProductBase,
    ProductCreate,
    ProductList,
    Reservation,
    StockCheck,
)

# Shipping schemas
from src.schemas.shipping import (
    DeliveryEstimate,
    Shipment,
    ShippingOption,
    TrackingEvent,
    TrackingStatus,
)

__all__ = [
    # Common
    "ErrorResponse",
    "PaginatedResponse",
    "Pagination",
    "SuccessResponse",
    # Orders
    "Order",
    "OrderBase",
    "OrderCreate",
    "OrderItem",
    "OrderItemBase",
    "OrderItemCreate",
    "OrderWithDiscount",
    # Products
    "Product",
    "ProductBase",
    "ProductCreate",
    "ProductList",
    "Reservation",
    "StockCheck",
    # Shipping
    "DeliveryEstimate",
    "Shipment",
    "ShippingOption",
    "TrackingEvent",
    "TrackingStatus",
]
