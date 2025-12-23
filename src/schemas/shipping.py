"""Shipping-related Pydantic schemas.

Schemas:
    - ShippingOption: Available shipping method
    - DeliveryEstimate: Estimated delivery date
    - Shipment: Created shipment details
    - TrackingStatus: Package tracking info
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ShippingOption(BaseModel):
    """Available shipping method.

    Attributes:
        method: Shipping method name
        cost: Shipping cost
        estimated_days: Estimated delivery time in days
    """

    method: str = Field(
        min_length=1,
        description="Shipping method name",
        examples=["Standard", "Express", "Overnight"],
    )
    cost: Decimal = Field(
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Shipping cost (must be non-negative)",
        examples=[Decimal("5.99")],
    )
    estimated_days: int = Field(
        ge=1,
        description="Estimated delivery time in days (must be at least 1)",
        examples=[3],
    )

    @field_validator("cost")
    @classmethod
    def validate_cost(cls, v: Decimal) -> Decimal:
        """Validate cost is non-negative."""
        if v < 0:
            raise ValueError("Shipping cost cannot be negative")
        return v

    @field_validator("estimated_days")
    @classmethod
    def validate_estimated_days(cls, v: int) -> int:
        """Validate estimated days is positive."""
        if v < 1:
            raise ValueError("Estimated delivery time must be at least 1 day")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "method": "Standard",
                    "cost": "5.99",
                    "estimated_days": 3,
                }
            ]
        }
    }


class DeliveryEstimate(BaseModel):
    """Estimated delivery information.

    Attributes:
        method: Shipping method used
        estimated_date: Estimated delivery date
        cost: Shipping cost
    """

    method: str = Field(
        min_length=1,
        description="Shipping method used",
        examples=["Standard"],
    )
    estimated_date: datetime = Field(
        description="Estimated delivery date",
        examples=["2024-01-18T00:00:00Z"],
    )
    cost: Decimal = Field(
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Shipping cost",
        examples=[Decimal("5.99")],
    )

    @field_validator("cost")
    @classmethod
    def validate_cost(cls, v: Decimal) -> Decimal:
        """Validate cost is non-negative."""
        if v < 0:
            raise ValueError("Shipping cost cannot be negative")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "method": "Standard",
                    "estimated_date": "2024-01-18T00:00:00Z",
                    "cost": "5.99",
                }
            ]
        }
    }


class Shipment(BaseModel):
    """Created shipment details.

    Attributes:
        id: Unique shipment identifier
        order_id: Associated order identifier
        tracking_number: Tracking number for package
        carrier: Shipping carrier name
        status: Shipment status
        created_at: Timestamp when shipment was created
    """

    id: UUID = Field(
        description="Unique shipment identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    order_id: UUID = Field(
        description="Associated order identifier",
        examples=["789e0123-e89b-12d3-a456-426614174000"],
    )
    tracking_number: str = Field(
        min_length=1,
        description="Tracking number for package",
        examples=["1Z999AA10123456784"],
    )
    carrier: str = Field(
        min_length=1,
        description="Shipping carrier name",
        examples=["UPS", "FedEx", "USPS", "DHL"],
    )
    status: str = Field(
        min_length=1,
        description="Shipment status",
        examples=["in_transit", "delivered", "pending"],
    )
    created_at: datetime = Field(
        description="Timestamp when shipment was created",
        examples=["2024-01-15T10:30:00Z"],
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "order_id": "789e0123-e89b-12d3-a456-426614174000",
                    "tracking_number": "1Z999AA10123456784",
                    "carrier": "UPS",
                    "status": "in_transit",
                    "created_at": "2024-01-15T10:30:00Z",
                }
            ]
        },
    }


class TrackingEvent(BaseModel):
    """Individual tracking event.

    Attributes:
        timestamp: Event timestamp
        status: Event status
        location: Event location
        description: Event description
    """

    timestamp: datetime = Field(
        description="Event timestamp",
        examples=["2024-01-15T10:30:00Z"],
    )
    status: str = Field(
        min_length=1,
        description="Event status",
        examples=["in_transit", "out_for_delivery", "delivered"],
    )
    location: str | None = Field(
        default=None,
        description="Event location",
        examples=["Chicago, IL", "New York, NY"],
    )
    description: str = Field(
        min_length=1,
        description="Event description",
        examples=["Package received by carrier", "Out for delivery"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "timestamp": "2024-01-15T10:30:00Z",
                    "status": "in_transit",
                    "location": "Chicago, IL",
                    "description": "Package received by carrier",
                }
            ]
        }
    }


class TrackingStatus(BaseModel):
    """Package tracking information with history.

    Attributes:
        tracking_number: Tracking number
        status: Current shipment status
        location: Current location
        updated_at: Last update timestamp
        history: List of tracking events
    """

    tracking_number: str = Field(
        min_length=1,
        description="Tracking number",
        examples=["1Z999AA10123456784"],
    )
    status: str = Field(
        min_length=1,
        description="Current shipment status",
        examples=["in_transit", "delivered"],
    )
    location: str | None = Field(
        default=None,
        description="Current location",
        examples=["Chicago, IL"],
    )
    updated_at: datetime = Field(
        description="Last update timestamp",
        examples=["2024-01-15T10:30:00Z"],
    )
    history: list[TrackingEvent] = Field(
        default_factory=list,
        description="List of tracking events (ordered chronologically)",
        examples=[[]],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tracking_number": "1Z999AA10123456784",
                    "status": "in_transit",
                    "location": "Chicago, IL",
                    "updated_at": "2024-01-15T10:30:00Z",
                    "history": [
                        {
                            "timestamp": "2024-01-15T08:00:00Z",
                            "status": "picked_up",
                            "location": "New York, NY",
                            "description": "Package picked up",
                        },
                        {
                            "timestamp": "2024-01-15T10:30:00Z",
                            "status": "in_transit",
                            "location": "Chicago, IL",
                            "description": "Package in transit",
                        },
                    ],
                }
            ]
        }
    }
