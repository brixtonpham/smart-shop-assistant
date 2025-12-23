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


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_estimate_delivery_empty_address(self) -> None:
        """Test estimate_delivery with empty address."""
        # Should still work as address is just stored, not validated
        result = estimate_delivery(address="", method="standard")
        assert result.method == "standard"

    def test_get_shipping_options_zero_weight(self) -> None:
        """Test shipping options with zero weight."""
        # Should still work, no weight surcharge
        options = get_shipping_options(weight=0.0, destination="90210")
        assert len(options) == 3

    def test_get_shipping_options_exactly_50_lbs(self) -> None:
        """Test shipping options at weight threshold."""
        options = get_shipping_options(weight=50.0, destination="90210")
        # At exactly 50, no surcharge
        assert any(option.cost == Decimal("5.99") for option in options)

    def test_get_shipping_options_just_over_threshold(self) -> None:
        """Test shipping options just over weight threshold."""
        options = get_shipping_options(weight=50.1, destination="90210")
        # Over 50, surcharge applied
        assert all(option.cost >= Decimal("15.99") for option in options)

    def test_create_shipment_generates_unique_tracking(self) -> None:
        """Test that each shipment gets unique tracking number."""
        order_id = str(uuid4())
        shipment1 = create_shipment(order_id=order_id, method="standard")

        order_id2 = str(uuid4())
        shipment2 = create_shipment(order_id=order_id2, method="standard")

        assert shipment1.tracking_number != shipment2.tracking_number
        assert shipment1.id != shipment2.id

    def test_track_package_multiple_events(self) -> None:
        """Test tracking package returns history with multiple events."""
        # Create shipment first
        order_id = str(uuid4())
        shipment = create_shipment(order_id=order_id, method="express")

        # Track it
        tracking = track_package(tracking_number=shipment.tracking_number)

        assert len(tracking.history) >= 1
        assert all(isinstance(event.timestamp, datetime) for event in tracking.history)

    def test_estimate_delivery_dates_are_future(self) -> None:
        """Test that estimated delivery dates are in the future."""
        now = datetime.now()

        standard = estimate_delivery(address="123 Main St", method="standard")
        express = estimate_delivery(address="123 Main St", method="express")
        overnight = estimate_delivery(address="123 Main St", method="overnight")

        assert standard.estimated_date > now
        assert express.estimated_date > now
        assert overnight.estimated_date > now

    def test_estimate_delivery_ordering(self) -> None:
        """Test that faster methods have earlier delivery dates."""
        standard = estimate_delivery(address="123 Main St", method="standard")
        express = estimate_delivery(address="123 Main St", method="express")
        overnight = estimate_delivery(address="123 Main St", method="overnight")

        # Overnight should arrive before express, express before standard
        assert overnight.estimated_date < express.estimated_date
        assert express.estimated_date < standard.estimated_date

    def test_carrier_assignment_by_method(self) -> None:
        """Test that carriers are assigned based on shipping method."""
        order_id = str(uuid4())

        standard = create_shipment(order_id=order_id, method="standard")
        assert standard.carrier == "USPS"

        order_id2 = str(uuid4())
        express = create_shipment(order_id=order_id2, method="express")
        assert express.carrier == "FedEx"

        order_id3 = str(uuid4())
        overnight = create_shipment(order_id=order_id3, method="overnight")
        assert overnight.carrier == "UPS"


class TestShippingCostCalculation:
    """Test shipping cost calculations."""

    def test_standard_base_cost(self) -> None:
        """Test standard shipping base cost."""
        result = estimate_delivery(address="123 Main St", method="standard")
        assert result.cost == Decimal("5.99")

    def test_express_base_cost(self) -> None:
        """Test express shipping base cost."""
        result = estimate_delivery(address="123 Main St", method="express")
        assert result.cost == Decimal("14.99")

    def test_overnight_base_cost(self) -> None:
        """Test overnight shipping base cost."""
        result = estimate_delivery(address="123 Main St", method="overnight")
        assert result.cost == Decimal("34.99")

    def test_heavy_package_standard(self) -> None:
        """Test heavy package cost for standard shipping."""
        options = get_shipping_options(weight=60.0, destination="90210")
        standard = next(opt for opt in options if opt.method == "Standard")
        assert standard.cost == Decimal("15.99")  # 5.99 + 10.00 surcharge

    def test_heavy_package_express(self) -> None:
        """Test heavy package cost for express shipping."""
        options = get_shipping_options(weight=60.0, destination="90210")
        express = next(opt for opt in options if opt.method == "Express")
        assert express.cost == Decimal("24.99")  # 14.99 + 10.00 surcharge

    def test_heavy_package_overnight(self) -> None:
        """Test heavy package cost for overnight shipping."""
        options = get_shipping_options(weight=60.0, destination="90210")
        overnight = next(opt for opt in options if opt.method == "Overnight")
        assert overnight.cost == Decimal("44.99")  # 34.99 + 10.00 surcharge


class TestTrackingStatus:
    """Test tracking status functionality."""

    def test_tracking_status_structure(self) -> None:
        """Test tracking status has correct structure."""
        tracking = track_package(tracking_number="1ZTEST123456789")

        assert tracking.tracking_number == "1ZTEST123456789"
        assert tracking.status in ["picked_up", "in_transit", "out_for_delivery", "delivered", "pending"]
        assert isinstance(tracking.updated_at, datetime)
        assert isinstance(tracking.history, list)
        assert len(tracking.history) > 0

    def test_tracking_event_structure(self) -> None:
        """Test tracking events have correct structure."""
        tracking = track_package(tracking_number="1ZTEST123456789")

        for event in tracking.history:
            assert isinstance(event.timestamp, datetime)
            assert isinstance(event.status, str)
            assert isinstance(event.description, str)
            # location can be None or str
            assert event.location is None or isinstance(event.location, str)

    def test_created_shipment_tracking_status(self) -> None:
        """Test tracking status for newly created shipment."""
        order_id = str(uuid4())
        shipment = create_shipment(order_id=order_id, method="standard")

        tracking = track_package(tracking_number=shipment.tracking_number)

        assert tracking.status == "pending"
        assert len(tracking.history) == 1
        assert tracking.history[0].status == "pending"
