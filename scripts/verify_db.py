"""Verify database setup and query sample data.

Usage:
    uv run python scripts/verify_db.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from src.database.connection import get_db_session
from src.database.models import Customer, Order, OrderItem, Product, Reservation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def verify_database() -> None:
    """Verify database setup by querying sample data."""
    try:
        logger.info("Verifying database...")

        async with get_db_session() as session:
            # Count products
            result = await session.execute(select(Product))
            products = result.scalars().all()
            logger.info(f"✓ Products: {len(products)} total")

            # Show sample products by category
            electronics = [p for p in products if p.category == "Electronics"]
            logger.info(f"  - Electronics: {len(electronics)}")
            if electronics:
                logger.info(f"    Example: {electronics[0].name} (${electronics[0].price})")

            # Count customers
            result = await session.execute(select(Customer))
            customers = result.scalars().all()
            logger.info(f"✓ Customers: {len(customers)} total")

            # Count orders
            result = await session.execute(select(Order))
            orders = result.scalars().all()
            logger.info(f"✓ Orders: {len(orders)} total")

            # Show order details with relationships
            for order in orders:
                logger.info(f"  Order {order.id}")
                logger.info(f"    Customer: {order.customer.name}")
                logger.info(f"    Status: {order.status.value}")
                logger.info(f"    Total: ${order.total}")
                logger.info(f"    Items: {len(order.order_items)}")

            # Count order items
            result = await session.execute(select(OrderItem))
            order_items = result.scalars().all()
            logger.info(f"✓ Order Items: {len(order_items)} total")

            # Count reservations
            result = await session.execute(select(Reservation))
            reservations = result.scalars().all()
            logger.info(f"✓ Reservations: {len(reservations)} total")

            logger.info("\n✓ Database verification completed successfully!")

    except Exception as e:
        logger.error(f"✗ Database verification failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(verify_database())
