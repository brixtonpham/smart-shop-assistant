"""Integration tests for Inventory MCP Server.

Tests all tools and resources with a test database.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from src.database.connection import get_db_session
from src.database.models import Product, Reservation
from src.mcp_servers.inventory_server import (
    check_stock as _check_stock_tool,
    get_all_products as _get_all_products_tool,
    get_categories as _get_categories_tool,
    get_product_by_id as _get_product_by_id_tool,
    list_products as _list_products_tool,
    low_stock_report as _low_stock_report_tool,
    release_stock as _release_stock_tool,
    reserve_stock as _reserve_stock_tool,
)

# Extract underlying functions from FastMCP tools
check_stock = _check_stock_tool.fn
get_all_products = _get_all_products_tool.fn
get_categories = _get_categories_tool.fn
get_product_by_id = _get_product_by_id_tool.fn
list_products = _list_products_tool.fn
low_stock_report = _low_stock_report_tool.fn
release_stock = _release_stock_tool.fn
reserve_stock = _reserve_stock_tool.fn


@pytest.fixture
async def test_product():
    """Create a test product in the database."""
    async with get_db_session() as session:
        product = Product(
            name="Test Wireless Mouse",
            category="Electronics",
            price=Decimal("29.99"),
            stock=100,
            sku="TEST-WM-001",
            description="A test wireless mouse",
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product


@pytest.fixture
async def low_stock_product():
    """Create a low stock test product."""
    async with get_db_session() as session:
        product = Product(
            name="Low Stock Item",
            category="Electronics",
            price=Decimal("19.99"),
            stock=5,
            sku="TEST-LOW-001",
            description="A low stock test item",
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product


class TestCheckStock:
    """Test check_stock tool."""

    async def test_check_stock_available(self, test_product):
        """Test checking stock for product with available stock."""
        result = await check_stock(str(test_product.id))

        assert result.product_id == test_product.id
        assert result.available is True
        assert result.quantity == 100
        assert result.reserved == 0

    async def test_check_stock_with_reservation(self, test_product):
        """Test stock check with existing reservation."""
        # Create reservation
        async with get_db_session() as session:
            reservation = Reservation(
                product_id=test_product.id,
                quantity=10,
                expires_at=datetime.now(UTC) + timedelta(minutes=15),
            )
            session.add(reservation)
            await session.commit()

        result = await check_stock(str(test_product.id))

        assert result.available is True
        assert result.quantity == 90  # 100 - 10 reserved
        assert result.reserved == 10

    async def test_check_stock_invalid_id(self):
        """Test check_stock with invalid product ID."""
        with pytest.raises(ValueError, match="Invalid product_id format"):
            await check_stock("invalid-id")

    async def test_check_stock_not_found(self):
        """Test check_stock with non-existent product."""
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Product not found"):
            await check_stock(non_existent_id)


class TestListProducts:
    """Test list_products tool."""

    async def test_list_all_products(self, test_product):
        """Test listing all products."""
        result = await list_products()

        assert result.total >= 1
        assert len(result.items) >= 1
        assert result.page == 1
        assert result.limit == 10

    async def test_list_products_by_category(self, test_product):
        """Test filtering products by category."""
        result = await list_products(category="Electronics")

        assert result.total >= 1
        for product in result.items:
            assert product.category == "Electronics"

    async def test_list_products_search(self, test_product):
        """Test searching products by name."""
        result = await list_products(search="Wireless")

        assert result.total >= 1
        assert any("Wireless" in p.name for p in result.items)

    async def test_list_products_pagination(self, test_product):
        """Test product pagination."""
        result = await list_products(page=1, limit=5)

        assert result.page == 1
        assert result.limit == 5
        assert len(result.items) <= 5

    async def test_list_products_invalid_page(self):
        """Test list_products with invalid page number."""
        with pytest.raises(ValueError, match="page must be >= 1"):
            await list_products(page=0)

    async def test_list_products_invalid_limit(self):
        """Test list_products with invalid limit."""
        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            await list_products(limit=101)


class TestReserveStock:
    """Test reserve_stock tool."""

    async def test_reserve_stock_success(self, test_product):
        """Test successful stock reservation."""
        now_utc = datetime.now(UTC)
        result = await reserve_stock(
            product_id=str(test_product.id),
            quantity=10,
            duration_minutes=15,
        )

        assert result.product_id == test_product.id
        assert result.quantity == 10
        # Pydantic converts to naive datetime, so compare with timezone-aware datetime properly
        # The expires_at should be approximately 15 minutes from now
        if result.expires_at.tzinfo is None:
            # If naive, make now naive too for comparison
            assert result.expires_at > now_utc.replace(tzinfo=None)
        else:
            assert result.expires_at > now_utc

        # Verify reservation in database
        async with get_db_session() as session:
            stmt = select(Reservation).where(Reservation.id == result.id)
            db_result = await session.execute(stmt)
            reservation = db_result.scalar_one_or_none()

            assert reservation is not None
            assert reservation.quantity == 10

    async def test_reserve_stock_insufficient(self, test_product):
        """Test reservation with insufficient stock."""
        with pytest.raises(ValueError, match="Insufficient stock"):
            await reserve_stock(
                product_id=str(test_product.id),
                quantity=200,  # More than available
                duration_minutes=15,
            )

    async def test_reserve_stock_invalid_quantity(self, test_product):
        """Test reservation with invalid quantity."""
        with pytest.raises(ValueError, match="quantity must be greater than 0"):
            await reserve_stock(
                product_id=str(test_product.id),
                quantity=0,
                duration_minutes=15,
            )

    async def test_reserve_stock_invalid_duration(self, test_product):
        """Test reservation with invalid duration."""
        with pytest.raises(ValueError, match="duration_minutes must be greater than 0"):
            await reserve_stock(
                product_id=str(test_product.id),
                quantity=10,
                duration_minutes=0,
            )


class TestReleaseStock:
    """Test release_stock tool."""

    async def test_release_stock_success(self, test_product):
        """Test successful stock release."""
        # First create a reservation
        reservation_result = await reserve_stock(
            product_id=str(test_product.id),
            quantity=10,
            duration_minutes=15,
        )

        # Now release it
        result = await release_stock(str(reservation_result.id))

        assert result is True

        # Verify reservation is deleted
        async with get_db_session() as session:
            stmt = select(Reservation).where(Reservation.id == reservation_result.id)
            db_result = await session.execute(stmt)
            reservation = db_result.scalar_one_or_none()

            assert reservation is None

    async def test_release_stock_not_found(self):
        """Test releasing non-existent reservation."""
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Reservation not found"):
            await release_stock(non_existent_id)

    async def test_release_stock_invalid_id(self):
        """Test release_stock with invalid ID format."""
        with pytest.raises(ValueError, match="Invalid reservation_id format"):
            await release_stock("invalid-id")


class TestLowStockReport:
    """Test low_stock_report tool."""

    async def test_low_stock_report(self, test_product, low_stock_product):
        """Test generating low stock report."""
        result = await low_stock_report(threshold=10)

        assert result.total >= 1

        # Low stock product should be in results
        low_stock_ids = [p.id for p in result.items]
        assert low_stock_product.id in low_stock_ids

        # All products should be below threshold
        for product in result.items:
            assert product.stock <= 10

    async def test_low_stock_report_custom_threshold(self, low_stock_product):
        """Test low stock report with custom threshold."""
        result = await low_stock_report(threshold=3)

        # Product with stock=5 should not appear
        product_ids = [p.id for p in result.items]
        assert low_stock_product.id not in product_ids

    async def test_low_stock_report_invalid_threshold(self):
        """Test low stock report with invalid threshold."""
        with pytest.raises(ValueError, match="threshold must be >= 0"):
            await low_stock_report(threshold=-1)


class TestResources:
    """Test MCP resources."""

    async def test_get_all_products(self, test_product):
        """Test inventory://products resource."""
        result = await get_all_products()

        assert isinstance(result, str)
        assert "items" in result
        assert test_product.sku in result

    async def test_get_product_by_id(self, test_product):
        """Test inventory://product/{id} resource."""
        result = await get_product_by_id(str(test_product.id))

        assert isinstance(result, str)
        assert str(test_product.id) in result
        assert test_product.sku in result

    async def test_get_product_by_id_not_found(self):
        """Test getting non-existent product."""
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Product not found"):
            await get_product_by_id(non_existent_id)

    async def test_get_categories(self, test_product):
        """Test inventory://categories resource."""
        result = await get_categories()

        assert isinstance(result, str)
        assert "Electronics" in result


class TestStockReservationFlow:
    """Test complete stock reservation workflow."""

    async def test_reserve_check_release_flow(self, test_product):
        """Test full reservation lifecycle."""
        # Check initial stock
        initial_check = await check_stock(str(test_product.id))
        assert initial_check.quantity == 100
        assert initial_check.reserved == 0

        # Reserve stock
        reservation = await reserve_stock(
            product_id=str(test_product.id),
            quantity=25,
            duration_minutes=15,
        )

        # Check stock after reservation
        after_reserve = await check_stock(str(test_product.id))
        assert after_reserve.quantity == 75  # 100 - 25
        assert after_reserve.reserved == 25

        # Release reservation
        released = await release_stock(str(reservation.id))
        assert released is True

        # Check stock after release
        after_release = await check_stock(str(test_product.id))
        assert after_release.quantity == 100
        assert after_release.reserved == 0
