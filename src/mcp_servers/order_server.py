"""Order MCP Server - Order processing and management.

This module implements an MCP server for order operations including
order creation, retrieval, coupon application, cancellation, and order history.

Tools:
    - create_order: Create a new order with items
    - get_order: Retrieve order details by ID
    - apply_coupon: Apply discount coupon to order
    - cancel_order: Cancel an existing order
    - order_history: Get paginated order history for customer

Resources:
    - orders://pending: List of pending orders
    - orders://order/{id}: Single order by ID

Coupon Codes:
    - SAVE10: 10% discount
    - SAVE20: 20% discount
    - FLAT5: $5 off

Usage:
    uv run mcp dev src/mcp_servers/order_server.py
"""

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastmcp import FastMCP
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.config import settings
from src.database.connection import get_db_session
from src.database.models import Customer, OrderStatus, Product
from src.database.models import Order as OrderModel
from src.database.models import OrderItem as OrderItemModel
from src.schemas.common import PaginatedResponse
from src.schemas.orders import Order, OrderCreate, OrderItem, OrderWithDiscount

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("order-server")

# Coupon configuration
COUPONS: dict[str, dict[str, Any]] = {
    "SAVE10": {"type": "percentage", "value": Decimal("0.10"), "description": "10% off"},
    "SAVE20": {"type": "percentage", "value": Decimal("0.20"), "description": "20% off"},
    "FLAT5": {"type": "fixed", "value": Decimal("5.00"), "description": "$5 off"},
}


def _convert_order_to_schema(order_model: OrderModel) -> Order:
    """Convert SQLAlchemy Order model to Pydantic schema.

    Args:
        order_model: SQLAlchemy Order instance with loaded relationships

    Returns:
        Pydantic Order schema with all fields populated

    Raises:
        ValueError: If required relationships are not loaded
    """
    # Build order items list
    order_items: list[OrderItem] = []
    for item in order_model.order_items:
        order_items.append(
            OrderItem(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_each=item.price_each,
                product_name=item.product.name if item.product else None,
                product_sku=item.product.sku if item.product else None,
            )
        )

    # Build order schema
    return Order(
        id=order_model.id,
        customer_id=order_model.customer_id,
        status=order_model.status,
        total=order_model.total,
        items=order_items,
        customer_name=order_model.customer.name if order_model.customer else None,
        customer_email=order_model.customer.email if order_model.customer else None,
        created_at=order_model.created_at,
        updated_at=order_model.updated_at,
    )


def _calculate_discount(total: Decimal, coupon_code: str) -> tuple[Decimal, Decimal]:
    """Calculate discount amount and final total for a coupon code.

    Args:
        total: Original order total
        coupon_code: Coupon code to apply (case-insensitive)

    Returns:
        Tuple of (discount_amount, final_total)

    Raises:
        ValueError: If coupon code is invalid
    """
    coupon_code_upper = coupon_code.upper()

    if coupon_code_upper not in COUPONS:
        raise ValueError(f"Invalid coupon code: {coupon_code}")

    coupon = COUPONS[coupon_code_upper]
    coupon_value = Decimal(str(coupon["value"]))

    if coupon["type"] == "percentage":
        discount_amount = total * coupon_value
    else:  # fixed
        discount_amount = min(coupon_value, total)  # Can't discount more than total

    # Round to 2 decimal places
    discount_amount = discount_amount.quantize(Decimal("0.01"))
    final_total = max(Decimal("0.00"), total - discount_amount)

    return discount_amount, final_total


@mcp.tool()
async def create_order(customer_id: str, items: list[dict[str, Any]]) -> Order:
    """Create a new order with items.

    This tool creates a new order for a customer with the specified items.
    It validates the customer exists, creates order items, and calculates
    the total amount.

    Args:
        customer_id: UUID of the customer placing the order
        items: List of order items, each with:
            - product_id (str): UUID of the product
            - quantity (int): Quantity to order (must be > 0)
            - price_each (str|float): Price per unit (must be > 0)

    Returns:
        Order: Created order with all details and items

    Raises:
        ValueError: If customer not found, items list empty, or validation fails
        RuntimeError: If database operation fails

    Example:
        >>> await create_order(
        ...     customer_id="abc12345-e89b-12d3-a456-426614174000",
        ...     items=[
        ...         {
        ...             "product_id": "123e4567-e89b-12d3-a456-426614174000",
        ...             "quantity": 2,
        ...             "price_each": "29.99"
        ...         }
        ...     ]
        ... )
    """
    logger.info(f"Creating order for customer {customer_id} with {len(items)} items")

    # Validate input
    if not items:
        raise ValueError("Order must have at least one item")

    try:
        customer_uuid = UUID(customer_id)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid customer_id format: {customer_id}") from e

    # Parse items to OrderCreate schema for validation
    from src.schemas.orders import OrderItemCreate

    try:
        parsed_items = [
            OrderItemCreate(
                product_id=UUID(item["product_id"]),
                quantity=int(item["quantity"]),
                price_each=Decimal(str(item["price_each"])),
            )
            for item in items
        ]
        order_data = OrderCreate(
            customer_id=customer_uuid,
            items=parsed_items,
        )
    except (KeyError, ValueError, TypeError) as e:
        raise ValueError(f"Invalid item data: {e}") from e

    async with get_db_session() as session:
        # Verify customer exists
        customer_result = await session.execute(
            select(Customer).where(Customer.id == customer_uuid)
        )
        customer = customer_result.scalar_one_or_none()

        if not customer:
            raise ValueError(f"Customer not found: {customer_id}")

        # Verify all products exist
        product_ids = [item.product_id for item in order_data.items]
        products_result = await session.execute(select(Product).where(Product.id.in_(product_ids)))
        products = {p.id: p for p in products_result.scalars().all()}

        missing_products = set(product_ids) - set(products.keys())
        if missing_products:
            raise ValueError(f"Products not found: {missing_products}")

        # Calculate total
        total = sum(Decimal(str(item.quantity)) * item.price_each for item in order_data.items)

        # Create order
        new_order = OrderModel(
            customer_id=customer_uuid,
            status=OrderStatus.PENDING,
            total=total,
        )
        session.add(new_order)
        await session.flush()  # Get order ID

        # Create order items
        for item_data in order_data.items:
            order_item = OrderItemModel(
                order_id=new_order.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price_each=item_data.price_each,
            )
            session.add(order_item)

        await session.commit()

        # Reload order with relationships
        result = await session.execute(
            select(OrderModel)
            .options(
                selectinload(OrderModel.customer),
                selectinload(OrderModel.order_items).selectinload(OrderItemModel.product),
            )
            .where(OrderModel.id == new_order.id)
        )
        created_order = result.scalar_one()

        logger.info(f"Order created successfully: {created_order.id}")
        return _convert_order_to_schema(created_order)


@mcp.tool()
async def get_order(order_id: str) -> Order:
    """Retrieve order details by ID.

    This tool retrieves complete order information including items,
    customer details, and current status.

    Args:
        order_id: UUID of the order to retrieve

    Returns:
        Order: Complete order details with items and customer info

    Raises:
        ValueError: If order_id format is invalid or order not found

    Example:
        >>> await get_order("789e0123-e89b-12d3-a456-426614174000")
    """
    logger.info(f"Retrieving order: {order_id}")

    try:
        order_uuid = UUID(order_id)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid order_id format: {order_id}") from e

    async with get_db_session() as session:
        result = await session.execute(
            select(OrderModel)
            .options(
                selectinload(OrderModel.customer),
                selectinload(OrderModel.order_items).selectinload(OrderItemModel.product),
            )
            .where(OrderModel.id == order_uuid)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order not found: {order_id}")

        logger.info(f"Order retrieved: {order_id}")
        return _convert_order_to_schema(order)


@mcp.tool()
async def apply_coupon(order_id: str, code: str) -> OrderWithDiscount:
    """Apply discount coupon to an order.

    This tool applies a valid coupon code to a pending order and
    calculates the discounted total. Only pending orders can have
    coupons applied.

    Valid coupons:
        - SAVE10: 10% discount
        - SAVE20: 20% discount
        - FLAT5: $5 off

    Args:
        order_id: UUID of the order
        code: Coupon code to apply (case-insensitive)

    Returns:
        OrderWithDiscount: Order with discount details and final total

    Raises:
        ValueError: If order not found, invalid coupon, or order not pending

    Example:
        >>> await apply_coupon(
        ...     order_id="789e0123-e89b-12d3-a456-426614174000",
        ...     code="SAVE10"
        ... )
    """
    logger.info(f"Applying coupon {code} to order {order_id}")

    try:
        order_uuid = UUID(order_id)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid order_id format: {order_id}") from e

    # Validate coupon code
    code_upper = code.upper()
    if code_upper not in COUPONS:
        raise ValueError(f"Invalid coupon code: {code}. Valid codes: {', '.join(COUPONS.keys())}")

    async with get_db_session() as session:
        result = await session.execute(
            select(OrderModel)
            .options(
                selectinload(OrderModel.customer),
                selectinload(OrderModel.order_items).selectinload(OrderItemModel.product),
            )
            .where(OrderModel.id == order_uuid)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order not found: {order_id}")

        if order.status != OrderStatus.PENDING:
            raise ValueError(
                f"Cannot apply coupon to order with status: {order.status.value}. "
                "Only pending orders can have coupons applied."
            )

        # Calculate discount
        discount_amount, final_total = _calculate_discount(order.total, code_upper)

        # Convert to schema
        order_schema = _convert_order_to_schema(order)

        # Create OrderWithDiscount response
        order_with_discount = OrderWithDiscount(
            **order_schema.model_dump(),
            discount_amount=discount_amount,
            final_total=final_total,
            coupon_code=code_upper,
        )

        logger.info(
            f"Coupon {code_upper} applied to order {order_id}: "
            f"discount=${discount_amount}, final=${final_total}"
        )
        return order_with_discount


@mcp.tool()
async def cancel_order(order_id: str, reason: str) -> bool:
    """Cancel an order.

    This tool cancels a pending or processing order. Orders that are
    already shipped, delivered, or cancelled cannot be cancelled.

    Args:
        order_id: UUID of the order to cancel
        reason: Reason for cancellation (required for audit trail)

    Returns:
        bool: True if cancellation successful

    Raises:
        ValueError: If order not found or cannot be cancelled

    Example:
        >>> await cancel_order(
        ...     order_id="789e0123-e89b-12d3-a456-426614174000",
        ...     reason="Customer requested cancellation"
        ... )
    """
    logger.info(f"Cancelling order {order_id}: {reason}")

    try:
        order_uuid = UUID(order_id)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid order_id format: {order_id}") from e

    if not reason or not reason.strip():
        raise ValueError("Cancellation reason is required")

    async with get_db_session() as session:
        result = await session.execute(select(OrderModel).where(OrderModel.id == order_uuid))
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order not found: {order_id}")

        # Check if order can be cancelled
        non_cancellable_statuses = {
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        }

        if order.status in non_cancellable_statuses:
            raise ValueError(
                f"Cannot cancel order with status: {order.status.value}. "
                f"Only pending or processing orders can be cancelled."
            )

        # Update order status
        order.status = OrderStatus.CANCELLED
        await session.commit()

        logger.info(f"Order {order_id} cancelled successfully. Reason: {reason}")
        return True


@mcp.tool()
async def order_history(customer_id: str, page: int = 1, limit: int = 10) -> dict[str, Any]:
    """Get paginated order history for a customer.

    This tool retrieves a customer's order history with pagination support.
    Orders are returned in reverse chronological order (newest first).

    Args:
        customer_id: UUID of the customer
        page: Page number (1-indexed, default: 1)
        limit: Items per page (1-100, default: 10)

    Returns:
        dict: Paginated response with:
            - items (list[Order]): List of orders for current page
            - total (int): Total number of orders
            - page (int): Current page number
            - limit (int): Items per page
            - pages (int): Total number of pages

    Raises:
        ValueError: If customer not found or invalid pagination parameters

    Example:
        >>> await order_history(
        ...     customer_id="abc12345-e89b-12d3-a456-426614174000",
        ...     page=1,
        ...     limit=10
        ... )
    """
    logger.info(f"Retrieving order history for customer {customer_id} (page={page}, limit={limit})")

    try:
        customer_uuid = UUID(customer_id)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid customer_id format: {customer_id}") from e

    # Validate pagination
    if page < 1:
        raise ValueError("Page must be >= 1")
    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")

    async with get_db_session() as session:
        # Verify customer exists
        customer_result = await session.execute(
            select(Customer).where(Customer.id == customer_uuid)
        )
        customer = customer_result.scalar_one_or_none()

        if not customer:
            raise ValueError(f"Customer not found: {customer_id}")

        # Get total count
        count_result = await session.execute(
            select(func.count(OrderModel.id)).where(OrderModel.customer_id == customer_uuid)
        )
        total = count_result.scalar_one()

        # Get paginated orders
        offset = (page - 1) * limit
        orders_result = await session.execute(
            select(OrderModel)
            .options(
                selectinload(OrderModel.customer),
                selectinload(OrderModel.order_items).selectinload(OrderItemModel.product),
            )
            .where(OrderModel.customer_id == customer_uuid)
            .order_by(OrderModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        orders = orders_result.scalars().all()

        # Convert to schemas
        order_schemas = [_convert_order_to_schema(order) for order in orders]

        # Calculate pages
        pages = (total + limit - 1) // limit if limit > 0 else 0

        # Create paginated response
        response = PaginatedResponse[Order](
            items=order_schemas,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )

        logger.info(
            f"Retrieved {len(order_schemas)} orders for customer {customer_id} "
            f"(total={total}, page={page}/{pages})"
        )
        return response.model_dump()


@mcp.resource("orders://pending")
async def get_pending_orders() -> str:
    """Resource: Get all pending orders.

    Returns:
        str: JSON string of pending orders list

    Example URI:
        orders://pending
    """
    logger.info("Fetching pending orders resource")

    async with get_db_session() as session:
        result = await session.execute(
            select(OrderModel)
            .options(
                selectinload(OrderModel.customer),
                selectinload(OrderModel.order_items).selectinload(OrderItemModel.product),
            )
            .where(OrderModel.status == OrderStatus.PENDING)
            .order_by(OrderModel.created_at.desc())
        )
        orders = result.scalars().all()

        # Convert to schemas
        order_schemas = [_convert_order_to_schema(order) for order in orders]

        logger.info(f"Found {len(order_schemas)} pending orders")
        return str([order.model_dump() for order in order_schemas])


@mcp.resource("orders://order/{order_id}")
async def get_order_resource(order_id: str) -> str:
    """Resource: Get single order by ID.

    Args:
        order_id: UUID of the order

    Returns:
        str: JSON string of order details

    Raises:
        ValueError: If order not found

    Example URI:
        orders://order/789e0123-e89b-12d3-a456-426614174000
    """
    logger.info(f"Fetching order resource: {order_id}")

    # Call the get_order function's underlying implementation
    order = await get_order.fn(order_id)  # type: ignore[attr-defined]
    return str(order.model_dump())


if __name__ == "__main__":
    # Run the MCP server
    logger.info(
        f"Starting Order MCP Server on {settings.mcp_server_host}:{settings.mcp_server_port}"
    )
    mcp.run()
