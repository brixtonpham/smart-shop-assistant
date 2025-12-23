"""Inventory MCP Server - Stock management and product operations.

This MCP server provides tools and resources for managing product inventory,
including stock checks, reservations, and product listings.

Tools:
    - check_stock: Check stock availability for a product
    - list_products: List products with optional filtering
    - reserve_stock: Reserve stock for a pending order
    - release_stock: Release a stock reservation
    - low_stock_report: Get products below threshold

Resources:
    - inventory://products - All products
    - inventory://product/{id} - Single product by ID
    - inventory://categories - List of categories
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastmcp import FastMCP
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database.connection import get_db_session
from src.database.models import Product, Reservation
from src.schemas.products import (
    Product as ProductSchema,
)
from src.schemas.products import (
    ProductList,
    StockCheck,
)
from src.schemas.products import (
    Reservation as ReservationSchema,
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Inventory Management Server")


async def _get_reserved_quantity(session: AsyncSession, product_id: UUID) -> int:
    """Calculate total reserved quantity for a product.

    Args:
        session: Database session
        product_id: Product identifier

    Returns:
        Total quantity currently reserved (excluding expired reservations)
    """
    now = datetime.now(UTC)

    # Query sum of non-expired reservations
    stmt = select(func.sum(Reservation.quantity)).where(
        Reservation.product_id == product_id,
        Reservation.expires_at > now,
    )

    result = await session.execute(stmt)
    reserved = result.scalar_one_or_none()

    return reserved if reserved is not None else 0


async def _get_available_quantity(
    session: AsyncSession,
    product: Product,
) -> int:
    """Calculate available quantity (stock minus reserved).

    Args:
        session: Database session
        product: Product model instance

    Returns:
        Available quantity (stock - reserved)
    """
    reserved = await _get_reserved_quantity(session, product.id)
    return max(0, product.stock - reserved)


@mcp.tool()
async def check_stock(product_id: str) -> StockCheck:
    """Check stock availability for a product.

    Args:
        product_id: UUID of the product to check

    Returns:
        StockCheck with availability status, available quantity, and reserved quantity

    Raises:
        ValueError: If product_id is invalid or product not found
    """
    logger.info(f"Checking stock for product: {product_id}")

    try:
        uuid_product_id = UUID(product_id)
    except ValueError as e:
        logger.error(f"Invalid product_id format: {product_id}")
        raise ValueError(f"Invalid product_id format: {product_id}") from e

    async with get_db_session() as session:
        # Fetch product
        stmt = select(Product).where(Product.id == uuid_product_id)
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if product is None:
            logger.warning(f"Product not found: {product_id}")
            raise ValueError(f"Product not found: {product_id}")

        # Calculate reserved and available quantities
        reserved = await _get_reserved_quantity(session, uuid_product_id)
        available = max(0, product.stock - reserved)

        stock_check = StockCheck(
            product_id=uuid_product_id,
            available=available > 0,
            quantity=available,
            reserved=reserved,
        )

        logger.info(f"Stock check for {product.sku}: available={available}, reserved={reserved}")
        return stock_check


@mcp.tool()
async def list_products(
    category: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> ProductList:
    """List products with optional filtering and pagination.

    Args:
        category: Filter by product category (optional)
        search: Search in product name or description (optional)
        page: Page number (1-indexed, default: 1)
        limit: Items per page (max 100, default: 10)

    Returns:
        ProductList with paginated results and metadata

    Raises:
        ValueError: If page < 1 or limit < 1 or limit > 100
    """
    logger.info(
        f"Listing products: category={category}, search={search}, page={page}, limit={limit}"
    )

    # Validate pagination parameters
    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

    async with get_db_session() as session:
        # Build query with filters
        stmt = select(Product)

        if category:
            stmt = stmt.where(Product.category == category)

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (Product.name.ilike(search_pattern)) | (Product.description.ilike(search_pattern))
            )

        # Count total matching products
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        # Apply pagination
        offset = (page - 1) * limit
        stmt = stmt.order_by(Product.created_at.desc()).offset(offset).limit(limit)

        # Execute query
        result = await session.execute(stmt)
        products = result.scalars().all()

        # Convert to Pydantic schemas
        product_schemas = [ProductSchema.model_validate(p) for p in products]

        # Calculate total pages
        pages = (total + limit - 1) // limit if limit > 0 else 0

        product_list = ProductList(
            items=product_schemas,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )

        logger.info(f"Found {total} products, returning page {page}/{pages}")
        return product_list


@mcp.tool()
async def reserve_stock(
    product_id: str,
    quantity: int,
    duration_minutes: int = 15,
) -> ReservationSchema:
    """Reserve stock for a pending order.

    Creates a temporary reservation that expires after the specified duration.
    Reservations prevent stock from being allocated to other orders.

    Args:
        product_id: UUID of the product to reserve
        quantity: Quantity to reserve (must be > 0)
        duration_minutes: Reservation duration in minutes (default: 15)

    Returns:
        Reservation details with ID, product, quantity, and expiration time

    Raises:
        ValueError: If product_id invalid, product not found, quantity invalid,
                   or insufficient stock available
    """
    logger.info(
        f"Reserving stock: product_id={product_id}, quantity={quantity}, "
        f"duration={duration_minutes}min"
    )

    # Validate inputs
    try:
        uuid_product_id = UUID(product_id)
    except ValueError as e:
        logger.error(f"Invalid product_id format: {product_id}")
        raise ValueError(f"Invalid product_id format: {product_id}") from e

    if quantity <= 0:
        raise ValueError("quantity must be greater than 0")

    if duration_minutes <= 0:
        raise ValueError("duration_minutes must be greater than 0")

    async with get_db_session() as session:
        # Fetch product with row lock to prevent race conditions
        stmt = select(Product).where(Product.id == uuid_product_id).with_for_update()
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if product is None:
            logger.warning(f"Product not found: {product_id}")
            raise ValueError(f"Product not found: {product_id}")

        # Check available stock
        available = await _get_available_quantity(session, product)

        if available < quantity:
            logger.warning(
                f"Insufficient stock for {product.sku}: requested={quantity}, available={available}"
            )
            raise ValueError(
                f"Insufficient stock: requested {quantity}, only {available} available"
            )

        # Create reservation
        expires_at = datetime.now(UTC) + timedelta(minutes=duration_minutes)
        reservation = Reservation(
            product_id=uuid_product_id,
            quantity=quantity,
            expires_at=expires_at,
        )

        session.add(reservation)
        await session.commit()
        await session.refresh(reservation)

        reservation_schema = ReservationSchema.model_validate(reservation)

        logger.info(
            f"Created reservation {reservation.id} for {quantity} units of {product.sku}, "
            f"expires at {expires_at.isoformat()}"
        )
        return reservation_schema


@mcp.tool()
async def release_stock(reservation_id: str) -> bool:
    """Release a stock reservation.

    Cancels an active reservation, making the stock available for other orders.

    Args:
        reservation_id: UUID of the reservation to release

    Returns:
        True if reservation was successfully released

    Raises:
        ValueError: If reservation_id invalid or reservation not found
    """
    logger.info(f"Releasing reservation: {reservation_id}")

    try:
        uuid_reservation_id = UUID(reservation_id)
    except ValueError as e:
        logger.error(f"Invalid reservation_id format: {reservation_id}")
        raise ValueError(f"Invalid reservation_id format: {reservation_id}") from e

    async with get_db_session() as session:
        # Fetch reservation
        stmt = select(Reservation).where(Reservation.id == uuid_reservation_id)
        result = await session.execute(stmt)
        reservation = result.scalar_one_or_none()

        if reservation is None:
            logger.warning(f"Reservation not found: {reservation_id}")
            raise ValueError(f"Reservation not found: {reservation_id}")

        # Delete reservation
        await session.delete(reservation)
        await session.commit()

        logger.info(
            f"Released reservation {reservation_id} "
            f"({reservation.quantity} units of product {reservation.product_id})"
        )
        return True


@mcp.tool()
async def low_stock_report(threshold: int = 10) -> ProductList:
    """Get products with stock below a specified threshold.

    Useful for inventory management and reordering decisions.

    Args:
        threshold: Stock level threshold (default: 10)

    Returns:
        ProductList with products below the threshold, ordered by stock level (lowest first)

    Raises:
        ValueError: If threshold < 0
    """
    logger.info(f"Generating low stock report with threshold: {threshold}")

    if threshold < 0:
        raise ValueError("threshold must be >= 0")

    async with get_db_session() as session:
        # Query products with stock below threshold
        stmt = select(Product).where(Product.stock <= threshold).order_by(Product.stock.asc())

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        # Execute query (no pagination for reports)
        result = await session.execute(stmt)
        products = result.scalars().all()

        # Convert to Pydantic schemas
        product_schemas = [ProductSchema.model_validate(p) for p in products]

        product_list = ProductList(
            items=product_schemas,
            total=total,
            page=1,
            limit=total if total > 0 else 1,
            pages=1,
        )

        logger.info(f"Found {total} products with stock <= {threshold}")
        return product_list


@mcp.resource("inventory://products")
async def get_all_products() -> str:
    """Get all products as a JSON resource.

    Returns:
        JSON string containing all products
    """
    logger.info("Resource requested: inventory://products")

    async with get_db_session() as session:
        stmt = select(Product).order_by(Product.category, Product.name)
        result = await session.execute(stmt)
        products = result.scalars().all()

        product_schemas = [ProductSchema.model_validate(p) for p in products]

        # Return as JSON string
        return ProductList(
            items=product_schemas,
            total=len(product_schemas),
            page=1,
            limit=len(product_schemas) if product_schemas else 1,
            pages=1,
        ).model_dump_json(indent=2)


@mcp.resource("inventory://product/{product_id}")
async def get_product_by_id(product_id: str) -> str:
    """Get a single product by ID as a JSON resource.

    Args:
        product_id: UUID of the product

    Returns:
        JSON string containing product details

    Raises:
        ValueError: If product_id invalid or product not found
    """
    logger.info(f"Resource requested: inventory://product/{product_id}")

    try:
        uuid_product_id = UUID(product_id)
    except ValueError as e:
        logger.error(f"Invalid product_id format: {product_id}")
        raise ValueError(f"Invalid product_id format: {product_id}") from e

    async with get_db_session() as session:
        stmt = select(Product).where(Product.id == uuid_product_id)
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if product is None:
            logger.warning(f"Product not found: {product_id}")
            raise ValueError(f"Product not found: {product_id}")

        product_schema = ProductSchema.model_validate(product)
        return product_schema.model_dump_json(indent=2)


@mcp.resource("inventory://categories")
async def get_categories() -> str:
    """Get list of all product categories as a JSON resource.

    Returns:
        JSON string containing list of unique categories
    """
    logger.info("Resource requested: inventory://categories")

    async with get_db_session() as session:
        # Get distinct categories
        stmt = select(Product.category).distinct().order_by(Product.category)
        result = await session.execute(stmt)
        categories = result.scalars().all()

        return {"categories": list(categories)}.__str__()


def main() -> None:
    """Run the inventory MCP server.

    Starts the server with SSE transport on configured host and port.
    """

    from src.config import configure_logging

    # Configure logging
    configure_logging()

    logger.info("Starting Inventory MCP Server...")
    logger.info(f"Server will run on {settings.mcp_server_host}:{settings.mcp_server_port}")

    # Run server with SSE transport
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
