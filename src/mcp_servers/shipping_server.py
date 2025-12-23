"""Shipping MCP Server - Delivery and shipment management.

Tools:
    - estimate_delivery: Get delivery time estimate
    - get_shipping_options: Get available shipping methods
    - create_shipment: Create a shipment for an order
    - track_package: Track package status

Resources:
    - shipping://rates
    - shipping://carriers
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, TypedDict
from uuid import UUID, uuid4

from fastmcp import FastMCP

from src.schemas.shipping import (
    DeliveryEstimate,
    Shipment,
    ShippingOption,
    TrackingEvent,
    TrackingStatus,
)


class RateInfo(TypedDict):
    """Shipping rate information."""

    base_cost: Decimal
    free_threshold: Decimal | None
    estimated_days: int


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server with SSE transport
mcp = FastMCP(
    name="shipping-server",
    instructions="Shipping and delivery management server for Smart Shop Assistant",
)

# Mock data for shipping rates
SHIPPING_RATES: dict[str, RateInfo] = {
    "standard": {
        "base_cost": Decimal("5.99"),
        "free_threshold": Decimal("50.00"),
        "estimated_days": 6,  # 5-7 days average
    },
    "express": {
        "base_cost": Decimal("14.99"),
        "free_threshold": None,
        "estimated_days": 3,  # 2-3 days average
    },
    "overnight": {
        "base_cost": Decimal("34.99"),
        "free_threshold": None,
        "estimated_days": 1,
    },
}

# Mock carriers
CARRIERS = ["UPS", "FedEx", "USPS", "DHL"]

# Mock shipment tracking data (keyed by tracking number)
MOCK_SHIPMENTS: dict[str, dict[str, Any]] = {}


def estimate_delivery_impl(address: str, method: str = "standard") -> DeliveryEstimate:
    """Get delivery time estimate for a given address and shipping method.

    Args:
        address: Delivery address (street, city, state, zip)
        method: Shipping method (standard, express, overnight). Defaults to "standard"

    Returns:
        DeliveryEstimate: Estimated delivery date and cost

    Raises:
        ValueError: If shipping method is not recognized
    """
    logger.info(f"Estimating delivery for address: {address}, method: {method}")

    method_lower = method.lower()
    if method_lower not in SHIPPING_RATES:
        raise ValueError(
            f"Invalid shipping method: {method}. Valid methods: {', '.join(SHIPPING_RATES.keys())}"
        )

    rate_info = SHIPPING_RATES[method_lower]

    # Calculate cost (free shipping for standard if threshold met)
    # For estimation purposes, assume order total of $0 (user can provide actual total later)
    cost = rate_info["base_cost"]

    # Calculate estimated delivery date
    estimated_days = rate_info["estimated_days"]
    estimated_date = datetime.now() + timedelta(days=estimated_days)

    logger.info(f"Estimated delivery: {estimated_date}, cost: ${cost}")

    return DeliveryEstimate(
        method=method,
        estimated_date=estimated_date,
        cost=cost,
    )


def get_shipping_options_impl(weight: float, destination: str) -> list[ShippingOption]:
    """Get available shipping methods for a package.

    Args:
        weight: Package weight in pounds
        destination: Destination address or ZIP code

    Returns:
        list[ShippingOption]: List of available shipping options with costs and estimates
    """
    logger.info(f"Getting shipping options for weight: {weight}lb, destination: {destination}")

    options: list[ShippingOption] = []

    # Weight surcharge for heavy packages (over 50 lbs)
    weight_surcharge = Decimal("0.00")
    if weight > 50:
        weight_surcharge = Decimal("10.00")
        logger.info(f"Heavy package surcharge applied: ${weight_surcharge}")

    for method, rate_info in SHIPPING_RATES.items():
        cost = rate_info["base_cost"] + weight_surcharge

        option = ShippingOption(
            method=method.capitalize(),
            cost=cost,
            estimated_days=rate_info["estimated_days"],
        )
        options.append(option)

    logger.info(f"Found {len(options)} shipping options")
    return options


def create_shipment_impl(order_id: str, method: str) -> Shipment:
    """Create a shipment for an order.

    This is a mock implementation that generates shipment details.

    Args:
        order_id: Order UUID
        method: Shipping method (standard, express, overnight)

    Returns:
        Shipment: Created shipment with tracking number

    Raises:
        ValueError: If shipping method is invalid or order_id is not a valid UUID
    """
    logger.info(f"Creating shipment for order: {order_id}, method: {method}")

    # Validate order_id is a valid UUID
    try:
        order_uuid = UUID(order_id)
    except ValueError as e:
        logger.error(f"Invalid order ID format: {order_id}")
        raise ValueError(f"Invalid order ID: {order_id}. Must be a valid UUID") from e

    method_lower = method.lower()
    if method_lower not in SHIPPING_RATES:
        raise ValueError(
            f"Invalid shipping method: {method}. Valid methods: {', '.join(SHIPPING_RATES.keys())}"
        )

    # Generate shipment details
    shipment_id = uuid4()
    tracking_number = f"1Z{uuid4().hex[:16].upper()}"

    # Select carrier based on method (mock logic)
    carrier_mapping = {
        "standard": "USPS",
        "express": "FedEx",
        "overnight": "UPS",
    }
    carrier = carrier_mapping.get(method_lower, "UPS")

    created_at = datetime.now()

    shipment = Shipment(
        id=shipment_id,
        order_id=order_uuid,
        tracking_number=tracking_number,
        carrier=carrier,
        status="pending",
        created_at=created_at,
    )

    # Store mock shipment data for tracking
    MOCK_SHIPMENTS[tracking_number] = {
        "shipment": shipment,
        "events": [
            TrackingEvent(
                timestamp=created_at,
                status="pending",
                location=None,
                description="Shipment created, awaiting pickup",
            )
        ],
    }

    logger.info(f"Created shipment: {shipment_id}, tracking: {tracking_number}")
    return shipment


def track_package_impl(tracking_number: str) -> TrackingStatus:
    """Track package status using tracking number.

    This is a mock implementation that returns simulated tracking data.

    Args:
        tracking_number: Package tracking number

    Returns:
        TrackingStatus: Current status and tracking history

    Raises:
        ValueError: If tracking number is not found
    """
    logger.info(f"Tracking package: {tracking_number}")

    # Check if we have mock data for this tracking number
    if tracking_number in MOCK_SHIPMENTS:
        mock_data = MOCK_SHIPMENTS[tracking_number]
        events = mock_data["events"]
        latest_event = events[-1]

        tracking_status = TrackingStatus(
            tracking_number=tracking_number,
            status=latest_event.status,
            location=latest_event.location,
            updated_at=latest_event.timestamp,
            history=events,
        )

        logger.info(f"Found tracking data: status={latest_event.status}")
        return tracking_status

    # Generate mock tracking data for unknown tracking numbers
    logger.info(f"Generating mock tracking data for: {tracking_number}")

    now = datetime.now()
    events = [
        TrackingEvent(
            timestamp=now - timedelta(days=2),
            status="picked_up",
            location="New York, NY",
            description="Package picked up by carrier",
        ),
        TrackingEvent(
            timestamp=now - timedelta(days=1),
            status="in_transit",
            location="Chicago, IL",
            description="Package in transit to sorting facility",
        ),
        TrackingEvent(
            timestamp=now,
            status="out_for_delivery",
            location="Los Angeles, CA",
            description="Out for delivery",
        ),
    ]

    latest_event = events[-1]

    return TrackingStatus(
        tracking_number=tracking_number,
        status=latest_event.status,
        location=latest_event.location,
        updated_at=latest_event.timestamp,
        history=events,
    )


def get_shipping_rates_impl() -> dict[str, dict[str, Any]]:
    """Get current shipping rates for all methods.

    Returns:
        dict: Shipping rates configuration
    """
    logger.info("Fetching shipping rates")

    # Convert Decimal to string for JSON serialization
    rates = {
        method: {
            "base_cost": str(info["base_cost"]),
            "free_threshold": str(info["free_threshold"]) if info["free_threshold"] else None,
            "estimated_days": info["estimated_days"],
        }
        for method, info in SHIPPING_RATES.items()
    }

    return rates


def get_carriers_impl() -> list[str]:
    """Get list of available shipping carriers.

    Returns:
        list[str]: List of carrier names
    """
    logger.info("Fetching available carriers")
    return CARRIERS


# Register tools with MCP server
@mcp.tool()
def estimate_delivery(address: str, method: str = "standard") -> DeliveryEstimate:
    """Get delivery time estimate for a given address and shipping method.

    Args:
        address: Delivery address (street, city, state, zip)
        method: Shipping method (standard, express, overnight). Defaults to "standard"

    Returns:
        DeliveryEstimate: Estimated delivery date and cost

    Raises:
        ValueError: If shipping method is not recognized
    """
    return estimate_delivery_impl(address, method)


@mcp.tool()
def get_shipping_options(weight: float, destination: str) -> list[ShippingOption]:
    """Get available shipping methods for a package.

    Args:
        weight: Package weight in pounds
        destination: Destination address or ZIP code

    Returns:
        list[ShippingOption]: List of available shipping options with costs and estimates
    """
    return get_shipping_options_impl(weight, destination)


@mcp.tool()
def create_shipment(order_id: str, method: str) -> Shipment:
    """Create a shipment for an order.

    This is a mock implementation that generates shipment details.

    Args:
        order_id: Order UUID
        method: Shipping method (standard, express, overnight)

    Returns:
        Shipment: Created shipment with tracking number

    Raises:
        ValueError: If shipping method is invalid or order_id is not a valid UUID
    """
    return create_shipment_impl(order_id, method)


@mcp.tool()
def track_package(tracking_number: str) -> TrackingStatus:
    """Track package status using tracking number.

    This is a mock implementation that returns simulated tracking data.

    Args:
        tracking_number: Package tracking number

    Returns:
        TrackingStatus: Current status and tracking history

    Raises:
        ValueError: If tracking number is not found
    """
    return track_package_impl(tracking_number)


@mcp.resource("shipping://rates")
def get_shipping_rates() -> dict[str, dict[str, Any]]:
    """Get current shipping rates for all methods.

    Returns:
        dict: Shipping rates configuration
    """
    return get_shipping_rates_impl()


@mcp.resource("shipping://carriers")
def get_carriers() -> list[str]:
    """Get list of available shipping carriers.

    Returns:
        list[str]: List of carrier names
    """
    return get_carriers_impl()


if __name__ == "__main__":
    logger.info("Starting Shipping MCP Server on http://localhost:8001")
    mcp.run(host="localhost", port=8001)
