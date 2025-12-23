"""Integration tests for Order MCP Server.

Tests all tools and resources with a test database.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from src.database.connection import get_db_session
from src.database.models import Customer, OrderStatus, Product
from src.database.models import Order as OrderModel
from src.database.models import OrderItem as OrderItemModel
from src.mcp_servers.order_server import (
    apply_coupon as _apply_coupon_tool,
    cancel_order as _cancel_order_tool,
    create_order as _create_order_tool,
    get_order as _get_order_tool,
    get_order_resource as _get_order_resource_tool,
    get_pending_orders as _get_pending_orders_tool,
    order_history as _order_history_tool,
)

# Extract underlying functions from FastMCP tools
apply_coupon = _apply_coupon_tool.fn
cancel_order = _cancel_order_tool.fn
create_order = _create_order_tool.fn
get_order = _get_order_tool.fn
get_order_resource = _get_order_resource_tool.fn
get_pending_orders = _get_pending_orders_tool.fn
order_history = _order_history_tool.fn


@pytest.fixture
async def test_customer():
    """Create a test customer in the database."""
    async with get_db_session() as session:
        customer = Customer(
            name="Test Customer",
            email="test.customer@example.com",
            address="123 Test Street, Test City, TC 12345",
        )
        session.add(customer)
        await session.commit()
        await session.refresh(customer)
        return customer


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
async def second_product():
    """Create a second test product."""
    async with get_db_session() as session:
        product = Product(
            name="Test Keyboard",
            category="Electronics",
            price=Decimal("49.99"),
            stock=50,
            sku="TEST-KB-001",
            description="A test keyboard",
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product


@pytest.fixture
async def test_order(test_customer, test_product):
    """Create a test order in the database."""
    async with get_db_session() as session:
        order = OrderModel(
            customer_id=test_customer.id,
            status=OrderStatus.PENDING,
            total=Decimal("59.98"),
        )
        session.add(order)
        await session.flush()

        order_item = OrderItemModel(
            order_id=order.id,
            product_id=test_product.id,
            quantity=2,
            price_each=Decimal("29.99"),
        )
        session.add(order_item)
        await session.commit()
        await session.refresh(order)
        return order


class TestCreateOrder:
    """Test create_order tool."""

    async def test_create_order_success(self, test_customer, test_product):
        """Test creating a valid order."""
        result = await create_order(
            customer_id=str(test_customer.id),
            items=[
                {
                    "product_id": str(test_product.id),
                    "quantity": 2,
                    "price_each": "29.99",
                }
            ],
        )

        assert result.customer_id == test_customer.id
        assert result.status == OrderStatus.PENDING
        assert result.total == Decimal("59.98")
        assert len(result.items) == 1
        assert result.items[0].quantity == 2
        assert result.items[0].price_each == Decimal("29.99")
        assert result.customer_name == test_customer.name
        assert result.customer_email == test_customer.email

    async def test_create_order_multiple_items(self, test_customer, test_product, second_product):
        """Test creating order with multiple items."""
        result = await create_order(
            customer_id=str(test_customer.id),
            items=[
                {
                    "product_id": str(test_product.id),
                    "quantity": 2,
                    "price_each": "29.99",
                },
                {
                    "product_id": str(second_product.id),
                    "quantity": 1,
                    "price_each": "49.99",
                },
            ],
        )

        assert result.total == Decimal("109.97")  # (2 * 29.99) + (1 * 49.99)
        assert len(result.items) == 2

    async def test_create_order_invalid_customer(self, test_product):
        """Test creating order with non-existent customer."""
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Customer not found"):
            await create_order(
                customer_id=non_existent_id,
                items=[
                    {
                        "product_id": str(test_product.id),
                        "quantity": 1,
                        "price_each": "29.99",
                    }
                ],
            )

    async def test_create_order_invalid_product(self, test_customer):
        """Test creating order with non-existent product."""
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Products not found"):
            await create_order(
                customer_id=str(test_customer.id),
                items=[
                    {
                        "product_id": non_existent_id,
                        "quantity": 1,
                        "price_each": "29.99",
                    }
                ],
            )

    async def test_create_order_empty_items(self, test_customer):
        """Test creating order with no items."""
        with pytest.raises(ValueError, match="Order must have at least one item"):
            await create_order(customer_id=str(test_customer.id), items=[])

    async def test_create_order_invalid_customer_id_format(self, test_product):
        """Test creating order with invalid customer ID format."""
        with pytest.raises(ValueError, match="Invalid customer_id format"):
            await create_order(
                customer_id="not-a-uuid",
                items=[
                    {
                        "product_id": str(test_product.id),
                        "quantity": 1,
                        "price_each": "29.99",
                    }
                ],
            )

    async def test_create_order_invalid_quantity(self, test_customer, test_product):
        """Test creating order with invalid quantity."""
        with pytest.raises(ValueError, match="Invalid item data"):
            await create_order(
                customer_id=str(test_customer.id),
                items=[
                    {
                        "product_id": str(test_product.id),
                        "quantity": 0,  # Invalid
                        "price_each": "29.99",
                    }
                ],
            )

    async def test_create_order_invalid_price(self, test_customer, test_product):
        """Test creating order with invalid price."""
        with pytest.raises(ValueError, match="Invalid item data"):
            await create_order(
                customer_id=str(test_customer.id),
                items=[
                    {
                        "product_id": str(test_product.id),
                        "quantity": 1,
                        "price_each": "-10.00",  # Invalid
                    }
                ],
            )


class TestGetOrder:
    """Test get_order tool."""

    async def test_get_order_success(self, test_order):
        """Test retrieving existing order."""
        result = await get_order(str(test_order.id))

        assert result.id == test_order.id
        assert result.customer_id == test_order.customer_id
        assert result.status == test_order.status
        assert result.total == test_order.total
        assert len(result.items) >= 1

    async def test_get_order_not_found(self):
        """Test retrieving non-existent order."""
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Order not found"):
            await get_order(non_existent_id)

    async def test_get_order_invalid_id(self):
        """Test get_order with invalid ID format."""
        with pytest.raises(ValueError, match="Invalid order_id format"):
            await get_order("invalid-id")


class TestApplyCoupon:
    """Test apply_coupon tool."""

    async def test_apply_coupon_save10(self, test_order):
        """Test applying 10% discount coupon."""
        result = await apply_coupon(order_id=str(test_order.id), code="SAVE10")

        assert result.coupon_code == "SAVE10"
        assert result.discount_amount == Decimal("5.998").quantize(Decimal("0.01"))
        assert result.final_total == Decimal("53.982").quantize(Decimal("0.01"))

    async def test_apply_coupon_save20(self, test_order):
        """Test applying 20% discount coupon."""
        result = await apply_coupon(order_id=str(test_order.id), code="SAVE20")

        assert result.coupon_code == "SAVE20"
        assert result.discount_amount == Decimal("11.996").quantize(Decimal("0.01"))
        assert result.final_total == Decimal("47.984").quantize(Decimal("0.01"))

    async def test_apply_coupon_flat5(self, test_order):
        """Test applying flat $5 discount."""
        result = await apply_coupon(order_id=str(test_order.id), code="FLAT5")

        assert result.coupon_code == "FLAT5"
        assert result.discount_amount == Decimal("5.00")
        assert result.final_total == Decimal("54.98")

    async def test_apply_coupon_case_insensitive(self, test_order):
        """Test coupon code is case insensitive."""
        result = await apply_coupon(order_id=str(test_order.id), code="save10")

        assert result.coupon_code == "SAVE10"

    async def test_apply_coupon_invalid_code(self, test_order):
        """Test applying invalid coupon code."""
        with pytest.raises(ValueError, match="Invalid coupon code"):
            await apply_coupon(order_id=str(test_order.id), code="INVALID")

    async def test_apply_coupon_order_not_found(self):
        """Test applying coupon to non-existent order."""
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Order not found"):
            await apply_coupon(order_id=non_existent_id, code="SAVE10")

    async def test_apply_coupon_non_pending_order(self, test_order):
        """Test applying coupon to non-pending order."""
        # Update order status to SHIPPED
        async with get_db_session() as session:
            stmt = select(OrderModel).where(OrderModel.id == test_order.id)
            result = await session.execute(stmt)
            order = result.scalar_one()
            order.status = OrderStatus.SHIPPED
            await session.commit()

        with pytest.raises(ValueError, match="Cannot apply coupon to order with status"):
            await apply_coupon(order_id=str(test_order.id), code="SAVE10")

    async def test_apply_coupon_invalid_order_id(self):
        """Test apply_coupon with invalid order ID format."""
        with pytest.raises(ValueError, match="Invalid order_id format"):
            await apply_coupon(order_id="invalid-id", code="SAVE10")


class TestCancelOrder:
    """Test cancel_order tool."""

    async def test_cancel_order_pending(self, test_order):
        """Test cancelling pending order."""
        result = await cancel_order(
            order_id=str(test_order.id), reason="Customer requested cancellation"
        )

        assert result is True

        # Verify status in database
        async with get_db_session() as session:
            stmt = select(OrderModel).where(OrderModel.id == test_order.id)
            db_result = await session.execute(stmt)
            order = db_result.scalar_one()
            assert order.status == OrderStatus.CANCELLED

    async def test_cancel_order_processing(self, test_order):
        """Test cancelling processing order."""
        # Update status to PROCESSING
        async with get_db_session() as session:
            stmt = select(OrderModel).where(OrderModel.id == test_order.id)
            result = await session.execute(stmt)
            order = result.scalar_one()
            order.status = OrderStatus.PROCESSING
            await session.commit()

        result = await cancel_order(order_id=str(test_order.id), reason="Test cancellation")

        assert result is True

    async def test_cancel_order_shipped(self, test_order):
        """Test cannot cancel shipped order."""
        # Update status to SHIPPED
        async with get_db_session() as session:
            stmt = select(OrderModel).where(OrderModel.id == test_order.id)
            result = await session.execute(stmt)
            order = result.scalar_one()
            order.status = OrderStatus.SHIPPED
            await session.commit()

        with pytest.raises(ValueError, match="Cannot cancel order with status"):
            await cancel_order(order_id=str(test_order.id), reason="Test")

    async def test_cancel_order_delivered(self, test_order):
        """Test cannot cancel delivered order."""
        # Update status to DELIVERED
        async with get_db_session() as session:
            stmt = select(OrderModel).where(OrderModel.id == test_order.id)
            result = await session.execute(stmt)
            order = result.scalar_one()
            order.status = OrderStatus.DELIVERED
            await session.commit()

        with pytest.raises(ValueError, match="Cannot cancel order with status"):
            await cancel_order(order_id=str(test_order.id), reason="Test")

    async def test_cancel_order_already_cancelled(self, test_order):
        """Test cannot cancel already cancelled order."""
        # Update status to CANCELLED
        async with get_db_session() as session:
            stmt = select(OrderModel).where(OrderModel.id == test_order.id)
            result = await session.execute(stmt)
            order = result.scalar_one()
            order.status = OrderStatus.CANCELLED
            await session.commit()

        with pytest.raises(ValueError, match="Cannot cancel order with status"):
            await cancel_order(order_id=str(test_order.id), reason="Test")

    async def test_cancel_order_not_found(self):
        """Test cancelling non-existent order."""
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Order not found"):
            await cancel_order(order_id=non_existent_id, reason="Test")

    async def test_cancel_order_empty_reason(self, test_order):
        """Test cancelling with empty reason."""
        with pytest.raises(ValueError, match="Cancellation reason is required"):
            await cancel_order(order_id=str(test_order.id), reason="")

    async def test_cancel_order_whitespace_reason(self, test_order):
        """Test cancelling with whitespace-only reason."""
        with pytest.raises(ValueError, match="Cancellation reason is required"):
            await cancel_order(order_id=str(test_order.id), reason="   ")

    async def test_cancel_order_invalid_id(self):
        """Test cancel_order with invalid order ID format."""
        with pytest.raises(ValueError, match="Invalid order_id format"):
            await cancel_order(order_id="invalid-id", reason="Test")


class TestOrderHistory:
    """Test order_history tool."""

    async def test_order_history_single_order(self, test_order):
        """Test retrieving order history with single order."""
        result = await order_history(customer_id=str(test_order.customer_id))

        assert result["total"] >= 1
        assert len(result["items"]) >= 1
        assert result["page"] == 1
        assert result["limit"] == 10

    async def test_order_history_multiple_orders(self, test_customer, test_product):
        """Test order history with multiple orders."""
        # Create multiple orders
        for i in range(3):
            async with get_db_session() as session:
                order = OrderModel(
                    customer_id=test_customer.id,
                    status=OrderStatus.PENDING,
                    total=Decimal("29.99"),
                )
                session.add(order)
                await session.flush()

                order_item = OrderItemModel(
                    order_id=order.id,
                    product_id=test_product.id,
                    quantity=1,
                    price_each=Decimal("29.99"),
                )
                session.add(order_item)
                await session.commit()

        result = await order_history(customer_id=str(test_customer.id))

        assert result["total"] >= 3

    async def test_order_history_pagination(self, test_customer, test_product):
        """Test order history pagination."""
        # Create 15 orders
        for i in range(15):
            async with get_db_session() as session:
                order = OrderModel(
                    customer_id=test_customer.id,
                    status=OrderStatus.PENDING,
                    total=Decimal("29.99"),
                )
                session.add(order)
                await session.flush()

                order_item = OrderItemModel(
                    order_id=order.id,
                    product_id=test_product.id,
                    quantity=1,
                    price_each=Decimal("29.99"),
                )
                session.add(order_item)
                await session.commit()

        # Get first page
        page1 = await order_history(customer_id=str(test_customer.id), page=1, limit=5)
        assert len(page1["items"]) == 5
        assert page1["page"] == 1
        assert page1["total"] >= 15
        assert page1["pages"] >= 3

        # Get second page
        page2 = await order_history(customer_id=str(test_customer.id), page=2, limit=5)
        assert len(page2["items"]) == 5
        assert page2["page"] == 2

        # Ensure different orders on different pages
        page1_ids = {item["id"] for item in page1["items"]}
        page2_ids = {item["id"] for item in page2["items"]}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_order_history_customer_not_found(self):
        """Test order history for non-existent customer."""
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Customer not found"):
            await order_history(customer_id=non_existent_id)

    async def test_order_history_invalid_customer_id(self):
        """Test order_history with invalid customer ID format."""
        with pytest.raises(ValueError, match="Invalid customer_id format"):
            await order_history(customer_id="invalid-id")

    async def test_order_history_invalid_page(self, test_customer):
        """Test order_history with invalid page number."""
        with pytest.raises(ValueError, match="Page must be >= 1"):
            await order_history(customer_id=str(test_customer.id), page=0)

    async def test_order_history_invalid_limit_low(self, test_customer):
        """Test order_history with limit too low."""
        with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
            await order_history(customer_id=str(test_customer.id), limit=0)

    async def test_order_history_invalid_limit_high(self, test_customer):
        """Test order_history with limit too high."""
        with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
            await order_history(customer_id=str(test_customer.id), limit=101)

    async def test_order_history_empty(self, test_customer):
        """Test order history for customer with no orders."""
        # Create a new customer with no orders
        async with get_db_session() as session:
            new_customer = Customer(
                name="New Customer",
                email="new.customer@example.com",
                address="456 New Street",
            )
            session.add(new_customer)
            await session.commit()
            await session.refresh(new_customer)

            result = await order_history(customer_id=str(new_customer.id))

            assert result["total"] == 0
            assert len(result["items"]) == 0


class TestResources:
    """Test MCP resources."""

    async def test_get_pending_orders(self, test_order):
        """Test orders://pending resource."""
        result = await get_pending_orders()

        assert isinstance(result, str)
        assert str(test_order.id) in result

    async def test_get_pending_orders_excludes_non_pending(self, test_order):
        """Test pending orders excludes non-pending orders."""
        # Create a shipped order
        async with get_db_session() as session:
            stmt = select(OrderModel).where(OrderModel.id == test_order.id)
            db_result = await session.execute(stmt)
            order = db_result.scalar_one()
            order.status = OrderStatus.SHIPPED
            await session.commit()

        result = await get_pending_orders()

        # Order should not be in pending results
        assert str(test_order.id) not in result or "shipped" in result.lower()

    async def test_get_order_resource(self, test_order):
        """Test orders://order/{id} resource."""
        result = await get_order_resource(str(test_order.id))

        assert isinstance(result, str)
        assert str(test_order.id) in result

    async def test_get_order_resource_not_found(self):
        """Test getting non-existent order resource."""
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Order not found"):
            await get_order_resource(non_existent_id)


class TestOrderWorkflow:
    """Test complete order workflow."""

    async def test_full_order_lifecycle(self, test_customer, test_product):
        """Test complete order lifecycle from creation to cancellation."""
        # 1. Create order
        created_order = await create_order(
            customer_id=str(test_customer.id),
            items=[
                {
                    "product_id": str(test_product.id),
                    "quantity": 2,
                    "price_each": "29.99",
                }
            ],
        )

        assert created_order.status == OrderStatus.PENDING

        # 2. Retrieve order
        retrieved_order = await get_order(str(created_order.id))
        assert retrieved_order.id == created_order.id

        # 3. Apply coupon
        discounted_order = await apply_coupon(order_id=str(created_order.id), code="SAVE10")
        assert discounted_order.discount_amount > 0

        # 4. Cancel order
        cancelled = await cancel_order(
            order_id=str(created_order.id), reason="Customer changed mind"
        )
        assert cancelled is True

        # 5. Verify cancellation
        final_order = await get_order(str(created_order.id))
        assert final_order.status == OrderStatus.CANCELLED

    async def test_order_history_workflow(self, test_customer, test_product):
        """Test order creation and history retrieval."""
        # Create multiple orders
        order_ids = []
        for i in range(3):
            order = await create_order(
                customer_id=str(test_customer.id),
                items=[
                    {
                        "product_id": str(test_product.id),
                        "quantity": 1 + i,
                        "price_each": "29.99",
                    }
                ],
            )
            order_ids.append(order.id)

        # Get order history
        history = await order_history(customer_id=str(test_customer.id))

        assert history["total"] >= 3
        history_ids = {item["id"] for item in history["items"]}
        for order_id in order_ids:
            assert order_id in history_ids
