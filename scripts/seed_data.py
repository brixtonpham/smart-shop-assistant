"""Database seed data script.

Usage:
    uv run python scripts/seed_data.py
"""

import asyncio
import logging
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from src.database.connection import get_db_session
from src.database.models import Customer, Order, OrderItem, OrderStatus, Product, Reservation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Sample product data
PRODUCTS = [
    # Electronics
    {
        "name": "Wireless Bluetooth Headphones",
        "category": "Electronics",
        "price": Decimal("79.99"),
        "stock": 50,
        "sku": "ELEC-WBH-001",
        "description": "Premium noise-cancelling wireless headphones with 30-hour battery life.",
    },
    {
        "name": "4K Smart TV 55 inch",
        "category": "Electronics",
        "price": Decimal("599.99"),
        "stock": 15,
        "sku": "ELEC-TV-055",
        "description": "Ultra HD 4K Smart TV with HDR and built-in streaming apps.",
    },
    {
        "name": "Laptop Stand Aluminum",
        "category": "Electronics",
        "price": Decimal("39.99"),
        "stock": 100,
        "sku": "ELEC-LS-001",
        "description": "Ergonomic aluminum laptop stand with adjustable height.",
    },
    {
        "name": "Wireless Mouse",
        "category": "Electronics",
        "price": Decimal("24.99"),
        "stock": 200,
        "sku": "ELEC-WM-001",
        "description": "Precision wireless mouse with ergonomic design and long battery life.",
    },
    {
        "name": "USB-C Hub 7-in-1",
        "category": "Electronics",
        "price": Decimal("49.99"),
        "stock": 75,
        "sku": "ELEC-HUB-007",
        "description": "Multi-port USB-C hub with HDMI, USB 3.0, and SD card reader.",
    },
    {
        "name": "Mechanical Keyboard RGB",
        "category": "Electronics",
        "price": Decimal("129.99"),
        "stock": 40,
        "sku": "ELEC-KB-RGB",
        "description": "Premium mechanical keyboard with RGB backlighting and tactile switches.",
    },
    # Home & Kitchen
    {
        "name": "Coffee Maker 12-Cup",
        "category": "Home & Kitchen",
        "price": Decimal("89.99"),
        "stock": 30,
        "sku": "HOME-CM-012",
        "description": "Programmable coffee maker with thermal carafe and auto-shutoff.",
    },
    {
        "name": "Air Fryer 5.8 Quart",
        "category": "Home & Kitchen",
        "price": Decimal("119.99"),
        "stock": 25,
        "sku": "HOME-AF-058",
        "description": "Digital air fryer with 8 preset cooking functions and non-stick basket.",
    },
    {
        "name": "Blender 1000W",
        "category": "Home & Kitchen",
        "price": Decimal("69.99"),
        "stock": 45,
        "sku": "HOME-BL-1000",
        "description": "High-powered blender with multiple speed settings and pulse function.",
    },
    {
        "name": "Knife Set 15-Piece",
        "category": "Home & Kitchen",
        "price": Decimal("149.99"),
        "stock": 20,
        "sku": "HOME-KS-015",
        "description": "Professional stainless steel knife set with wooden block.",
    },
    {
        "name": "Vacuum Cleaner Cordless",
        "category": "Home & Kitchen",
        "price": Decimal("299.99"),
        "stock": 18,
        "sku": "HOME-VC-CORD",
        "description": "Lightweight cordless vacuum with HEPA filtration and 60-min runtime.",
    },
    # Clothing
    {
        "name": "Men's Cotton T-Shirt",
        "category": "Clothing",
        "price": Decimal("19.99"),
        "stock": 150,
        "sku": "CLTH-MTS-001",
        "description": "Classic fit cotton t-shirt available in multiple colors.",
    },
    {
        "name": "Women's Yoga Pants",
        "category": "Clothing",
        "price": Decimal("49.99"),
        "stock": 80,
        "sku": "CLTH-WYP-001",
        "description": "High-waist yoga pants with moisture-wicking fabric.",
    },
    {
        "name": "Unisex Hoodie",
        "category": "Clothing",
        "price": Decimal("59.99"),
        "stock": 60,
        "sku": "CLTH-UH-001",
        "description": "Comfortable fleece hoodie with kangaroo pocket.",
    },
    {
        "name": "Running Shoes",
        "category": "Clothing",
        "price": Decimal("89.99"),
        "stock": 70,
        "sku": "CLTH-RS-001",
        "description": "Lightweight running shoes with cushioned sole and breathable mesh.",
    },
    # Books
    {
        "name": "Python Programming Guide",
        "category": "Books",
        "price": Decimal("39.99"),
        "stock": 35,
        "sku": "BOOK-PY-001",
        "description": "Comprehensive guide to Python programming for beginners and experts.",
    },
    {
        "name": "The Art of Clean Code",
        "category": "Books",
        "price": Decimal("44.99"),
        "stock": 28,
        "sku": "BOOK-CC-001",
        "description": "Best practices for writing maintainable and clean code.",
    },
    {
        "name": "Data Science Handbook",
        "category": "Books",
        "price": Decimal("54.99"),
        "stock": 22,
        "sku": "BOOK-DS-001",
        "description": "Complete handbook for data science with Python and R.",
    },
    # Sports & Outdoors
    {
        "name": "Yoga Mat Premium",
        "category": "Sports & Outdoors",
        "price": Decimal("29.99"),
        "stock": 90,
        "sku": "SPRT-YM-001",
        "description": "Non-slip yoga mat with extra cushioning and carrying strap.",
    },
    {
        "name": "Dumbbell Set 20lb",
        "category": "Sports & Outdoors",
        "price": Decimal("79.99"),
        "stock": 40,
        "sku": "SPRT-DB-020",
        "description": "Adjustable dumbbell set with rubberized grip.",
    },
    {
        "name": "Camping Tent 4-Person",
        "category": "Sports & Outdoors",
        "price": Decimal("159.99"),
        "stock": 12,
        "sku": "SPRT-CT-004",
        "description": "Waterproof camping tent with easy setup and ventilation.",
    },
    {
        "name": "Water Bottle Insulated",
        "category": "Sports & Outdoors",
        "price": Decimal("24.99"),
        "stock": 120,
        "sku": "SPRT-WB-001",
        "description": "Stainless steel insulated water bottle keeps drinks cold for 24 hours.",
    },
    # Health & Beauty
    {
        "name": "Electric Toothbrush",
        "category": "Health & Beauty",
        "price": Decimal("69.99"),
        "stock": 55,
        "sku": "HLTH-ET-001",
        "description": "Rechargeable electric toothbrush with 3 cleaning modes.",
    },
    {
        "name": "Facial Cleanser Set",
        "category": "Health & Beauty",
        "price": Decimal("34.99"),
        "stock": 65,
        "sku": "HLTH-FC-001",
        "description": "Complete facial cleanser set with moisturizer and toner.",
    },
    {
        "name": "Massage Gun",
        "category": "Health & Beauty",
        "price": Decimal("149.99"),
        "stock": 30,
        "sku": "HLTH-MG-001",
        "description": "Percussion massage gun with 6 speed levels and multiple attachments.",
    },
]

# Sample customer data
CUSTOMERS = [
    {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "address": "123 Main St, New York, NY 10001",
    },
    {
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "address": "456 Oak Ave, Los Angeles, CA 90001",
    },
    {
        "name": "Bob Johnson",
        "email": "bob.johnson@example.com",
        "address": "789 Pine Rd, Chicago, IL 60601",
    },
    {
        "name": "Alice Williams",
        "email": "alice.williams@example.com",
        "address": "321 Elm St, Houston, TX 77001",
    },
    {
        "name": "Charlie Brown",
        "email": "charlie.brown@example.com",
        "address": "654 Maple Dr, Phoenix, AZ 85001",
    },
]


async def seed_products() -> list[Product]:
    """Seed product data into the database.

    Returns:
        List of created Product instances.
    """
    logger.info("Seeding products...")

    async with get_db_session() as session:
        # Check if products already exist
        result = await session.execute(select(Product))
        existing_products = result.scalars().all()

        if existing_products:
            logger.info(f"Products already exist ({len(existing_products)} found). Skipping...")
            return existing_products

        # Create products
        products = [Product(**product_data) for product_data in PRODUCTS]
        session.add_all(products)
        await session.commit()

        logger.info(f"✓ Created {len(products)} products")
        return products


async def seed_customers() -> list[Customer]:
    """Seed customer data into the database.

    Returns:
        List of created Customer instances.
    """
    logger.info("Seeding customers...")

    async with get_db_session() as session:
        # Check if customers already exist
        result = await session.execute(select(Customer))
        existing_customers = result.scalars().all()

        if existing_customers:
            logger.info(f"Customers already exist ({len(existing_customers)} found). Skipping...")
            return existing_customers

        # Create customers
        customers = [Customer(**customer_data) for customer_data in CUSTOMERS]
        session.add_all(customers)
        await session.commit()

        logger.info(f"✓ Created {len(customers)} customers")
        return customers


async def seed_orders(customers: list[Customer], products: list[Product]) -> None:
    """Seed sample orders into the database.

    Args:
        customers: List of Customer instances
        products: List of Product instances
    """
    logger.info("Seeding orders...")

    async with get_db_session() as session:
        # Check if orders already exist
        result = await session.execute(select(Order))
        existing_orders = result.scalars().all()

        if existing_orders:
            logger.info(f"Orders already exist ({len(existing_orders)} found). Skipping...")
            return

        # Create sample orders
        # Order 1: John Doe - Completed order
        order1 = Order(
            customer_id=customers[0].id,
            status=OrderStatus.DELIVERED,
            total=Decimal("209.97"),
        )
        order1_items = [
            OrderItem(
                order=order1,
                product_id=products[0].id,  # Wireless Headphones
                quantity=2,
                price_each=products[0].price,
            ),
            OrderItem(
                order=order1,
                product_id=products[3].id,  # Wireless Mouse
                quantity=2,
                price_each=products[3].price,
            ),
        ]
        session.add(order1)
        session.add_all(order1_items)

        # Order 2: Jane Smith - Processing order
        order2 = Order(
            customer_id=customers[1].id,
            status=OrderStatus.PROCESSING,
            total=Decimal("719.98"),
        )
        order2_items = [
            OrderItem(
                order=order2,
                product_id=products[1].id,  # 4K Smart TV
                quantity=1,
                price_each=products[1].price,
            ),
            OrderItem(
                order=order2,
                product_id=products[10].id,  # Vacuum Cleaner
                quantity=1,
                price_each=products[10].price,
            ),
        ]
        session.add(order2)
        session.add_all(order2_items)

        # Order 3: Bob Johnson - Pending order
        order3 = Order(
            customer_id=customers[2].id,
            status=OrderStatus.PENDING,
            total=Decimal("149.97"),
        )
        order3_items = [
            OrderItem(
                order=order3,
                product_id=products[11].id,  # Men's T-Shirt
                quantity=3,
                price_each=products[11].price,
            ),
            OrderItem(
                order=order3,
                product_id=products[13].id,  # Unisex Hoodie
                quantity=1,
                price_each=products[13].price,
            ),
        ]
        session.add(order3)
        session.add_all(order3_items)

        await session.commit()
        logger.info("✓ Created 3 sample orders with items")


async def seed_reservations(products: list[Product]) -> None:
    """Seed sample stock reservations.

    Args:
        products: List of Product instances
    """
    logger.info("Seeding reservations...")

    async with get_db_session() as session:
        # Check if reservations already exist
        result = await session.execute(select(Reservation))
        existing_reservations = result.scalars().all()

        if existing_reservations:
            logger.info(
                f"Reservations already exist ({len(existing_reservations)} found). Skipping..."
            )
            return

        # Create sample reservations (expiring in 15 minutes)
        expires_at = datetime.now(UTC) + timedelta(minutes=15)

        reservations = [
            Reservation(
                product_id=products[0].id,  # Wireless Headphones
                quantity=5,
                expires_at=expires_at,
            ),
            Reservation(
                product_id=products[5].id,  # Mechanical Keyboard
                quantity=2,
                expires_at=expires_at,
            ),
        ]

        session.add_all(reservations)
        await session.commit()

        logger.info(f"✓ Created {len(reservations)} sample reservations")


async def seed_database() -> None:
    """Seed the database with sample data."""
    try:
        logger.info("Starting database seeding...")

        # Seed in order due to relationships
        products = await seed_products()
        customers = await seed_customers()
        await seed_orders(customers, products)
        await seed_reservations(products)

        logger.info("✓ Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"✗ Database seeding failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_database())
