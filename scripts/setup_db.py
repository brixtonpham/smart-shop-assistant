"""Database setup and migration script.

Usage:
    uv run python scripts/setup_db.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import create_tables, get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def setup_database() -> None:
    """Set up the database by creating all tables.

    This script will:
    1. Create the database file if it doesn't exist
    2. Create all tables defined in the models
    3. Create indexes and constraints
    """
    try:
        database_url = get_database_url()
        logger.info(f"Setting up database at: {database_url}")

        # Create tables
        await create_tables()

        logger.info("✓ Database setup completed successfully!")

    except Exception as e:
        logger.error(f"✗ Database setup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_database())
