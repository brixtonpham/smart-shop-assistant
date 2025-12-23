"""Unit tests for Shipping MCP Server."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.mcp_servers.shipping_server import (
    create_shipment_impl as create_shipment,
)
from src.mcp_servers.shipping_server import (
    estimate_delivery_impl as estimate_delivery,
)
from src.mcp_servers.shipping_server import (
    get_carriers_impl as get_carriers,
)
from src.mcp_servers.shipping_server import (
    get_shipping_options_impl as get_shipping_options,
)
from src.mcp_servers.shipping_server import (
    get_shipping_rates_impl as get_shipping_rates,
)
from src.mcp_servers.shipping_server import (
    track_package_impl as track_package,
)


class TestEstimateDelivery:
    """Test estimate_delivery tool."""

    def test_standard_shipping(self) -> None:
        """Test standard shipping estimate."""
        result = estimate_delivery(address="123 Main St, City, ST 12345", method="standard")

        assert result.method == "standard"
        assert result.cost == Decimal("5.99")
        assert isinstance(result.estimated_date, datetime)

    def test_express_shipping(self) -> None:
        """Test express shipping estimate."""
        result = estimate_delivery(address="123 Main St, City, ST 12345", method="express")

        assert result.method == "express"
        assert result.cost == Decimal("14.99")
        assert isinstance(result.estimated_date, datetime)

    def test_overnight_shipping(self) -> None:
        """Test overnight shipping estimate."""
        result = estimate_delivery(address="123 Main St, City, ST 12345", method="overnight")

        assert result.method == "overnight"
        assert result.cost == Decimal("34.99")
        assert isinstance(result.estimated_date, datetime)

    def test_invalid_method(self) -> None:
        """Test invalid shipping method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid shipping method"):
            estimate_delivery(address="123 Main St", method="invalid")

    def test_case_insensitive_method(self) -> None:
        """Test shipping method is case insensitive."""
        result = estimate_delivery(address="123 Main St", method="STANDARD")

        assert result.method == "STANDARD"
        assert result.cost == Decimal("5.99")


class TestGetShippingOptions:
    """Test get_shipping_options tool."""

    def test_light_package(self) -> None:
        """Test shipping options for light package."""
        options = get_shipping_options(weight=10.0, destination="90210")

        assert len(options) == 3
        assert all(
            option.cost == Decimal("5.99")
            or option.cost == Decimal("14.99")
            or option.cost == Decimal("34.99")
            for option in options
        )

    def test_heavy_package_surcharge(self) -> None:
        """Test heavy package adds surcharge."""
        options = get_shipping_options(weight=60.0, destination="90210")

        assert len(options) == 3
        # Heavy package surcharge of $10 applied
        assert any(option.cost == Decimal("15.99") for option in options)  # standard + $10
        assert any(option.cost == Decimal("24.99") for option in options)  # express + $10
        assert any(option.cost == Decimal("44.99") for option in options)  # overnight + $10

    def test_all_methods_included(self) -> None:
        """Test all shipping methods are returned."""
        options = get_shipping_options(weight=10.0, destination="90210")

        methods = {option.method for option in options}
        assert methods == {"Standard", "Express", "Overnight"}


class TestCreateShipment:
    """Test create_shipment tool."""

    def test_create_standard_shipment(self) -> None:
        """Test creating a standard shipment."""
        order_id = str(uuid4())
        shipment = create_shipment(order_id=order_id, method="standard")

        assert isinstance(shipment.id, UUID)
        assert shipment.order_id == UUID(order_id)
        assert shipment.carrier == "USPS"
        assert shipment.status == "pending"
        assert shipment.tracking_number.startswith("1Z")

    def test_create_express_shipment(self) -> None:
        """Test creating an express shipment."""
        order_id = str(uuid4())
        shipment = create_shipment(order_id=order_id, method="express")

        assert shipment.carrier == "FedEx"
        assert isinstance(shipment.created_at, datetime)

    def test_create_overnight_shipment(self) -> None:
        """Test creating an overnight shipment."""
        order_id = str(uuid4())
        shipment = create_shipment(order_id=order_id, method="overnight")

        assert shipment.carrier == "UPS"

    def test_invalid_order_id(self) -> None:
        """Test invalid order ID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid order ID"):
            create_shipment(order_id="not-a-uuid", method="standard")

    def test_invalid_shipping_method(self) -> None:
        """Test invalid shipping method raises ValueError."""
        order_id = str(uuid4())
        with pytest.raises(ValueError, match="Invalid shipping method"):
            create_shipment(order_id=order_id, method="invalid")


class TestTrackPackage:
    """Test track_package tool."""

    def test_track_created_shipment(self) -> None:
        """Test tracking a shipment that was created."""
        # Create a shipment first
        order_id = str(uuid4())
        shipment = create_shipment(order_id=order_id, method="standard")

        # Track it
        tracking = track_package(tracking_number=shipment.tracking_number)

        assert tracking.tracking_number == shipment.tracking_number
        assert tracking.status == "pending"
        assert len(tracking.history) >= 1
        assert tracking.history[0].description == "Shipment created, awaiting pickup"

    def test_track_unknown_package(self) -> None:
        """Test tracking an unknown package returns mock data."""
        tracking = track_package(tracking_number="1ZTEST123456789")

        assert tracking.tracking_number == "1ZTEST123456789"
        assert tracking.status in ["picked_up", "in_transit", "out_for_delivery", "delivered"]
        assert len(tracking.history) >= 1
        assert tracking.location is not None


class TestGetShippingRates:
    """Test get_shipping_rates resource."""

    def test_returns_all_rates(self) -> None:
        """Test returns all shipping rates."""
        rates = get_shipping_rates()

        assert "standard" in rates
        assert "express" in rates
        assert "overnight" in rates

    def test_rate_structure(self) -> None:
        """Test rate structure has correct fields."""
        rates = get_shipping_rates()

        for method, info in rates.items():
            assert "base_cost" in info
            assert "free_threshold" in info
            assert "estimated_days" in info
            assert isinstance(info["base_cost"], str)
            assert isinstance(info["estimated_days"], int)


class TestGetCarriers:
    """Test get_carriers resource."""

    def test_returns_carriers(self) -> None:
        """Test returns list of carriers."""
        carriers = get_carriers()

        assert isinstance(carriers, list)
        assert len(carriers) > 0
        assert "UPS" in carriers
        assert "FedEx" in carriers
        assert "USPS" in carriers
        assert "DHL" in carriers
