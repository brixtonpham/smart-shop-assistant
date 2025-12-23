"""Database connection and session management.

This module provides async database connection and session factory
for SQLAlchemy with aiosqlite.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings
from src.database.models import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """Get database URL from settings.

    Returns:
        Database URL in SQLAlchemy format for aiosqlite.
    """
    db_path = Path(settings.database_path)
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to async SQLite URL
    return f"sqlite+aiosqlite:///{db_path.absolute()}"


async def get_engine() -> AsyncEngine:
    """Get or create the async database engine.

    Returns:
        AsyncEngine instance for database operations.
    """
    global _engine

    if _engine is None:
        database_url = get_database_url()
        logger.info(f"Creating async database engine: {database_url}")

        _engine = create_async_engine(
            database_url,
            echo=settings.debug,  # Log SQL statements in debug mode
            future=True,
            pool_pre_ping=True,  # Verify connections before using
            connect_args={
                "check_same_thread": False,  # Required for async SQLite
            },
        )

    return _engine


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory.

    Returns:
        Session factory for creating database sessions.
    """
    global _async_session_factory

    if _async_session_factory is None:
        engine = await get_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Keep objects usable after commit
            autoflush=False,  # Manually control flushing
            autocommit=False,  # Use explicit transactions
        )

    return _async_session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session as a context manager.

    Yields:
        AsyncSession for database operations.

    Example:
        async with get_db_session() as session:
            result = await session.execute(select(Product))
            products = result.scalars().all()
    """
    session_factory = await get_session_factory()

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables.

    This should be called during application initialization.
    """
    engine = await get_engine()
    logger.info("Creating database tables...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created successfully")


async def drop_tables() -> None:
    """Drop all database tables.

    WARNING: This will delete all data. Use only for testing or reset.
    """
    engine = await get_engine()
    logger.warning("Dropping all database tables...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    logger.info("Database tables dropped successfully")


async def close_engine() -> None:
    """Close the database engine and cleanup connections.

    This should be called during application shutdown.
    """
    global _engine, _async_session_factory

    if _engine is not None:
        logger.info("Closing database engine...")
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        logger.info("Database engine closed")
