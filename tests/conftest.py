"""Pytest configuration and shared fixtures."""

import asyncio

import pytest
import pytest_asyncio

from src.database.connection import create_tables, drop_tables


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """Setup test database before each test and clean up after."""
    # Create tables before test
    await create_tables()
    yield
    # Drop tables after test to ensure clean state
    await drop_tables()


@pytest.fixture
def sample_product():
    """Sample product data for testing."""
    return {
        "id": "prod-001",
        "name": "Test Product",
        "category": "electronics",
        "price": 99.99,
        "stock": 100,
        "sku": "TEST-001",
        "description": "A test product for unit testing",
    }


@pytest.fixture
def sample_customer():
    """Sample customer data for testing."""
    return {
        "id": "cust-001",
        "name": "Test Customer",
        "email": "test@example.com",
        "address": "123 Test St, Test City, TC 12345",
    }


@pytest.fixture
def sample_order():
    """Sample order data for testing."""
    return {
        "id": "order-001",
        "customer_id": "cust-001",
        "status": "pending",
        "total": 99.99,
        "items": [{"product_id": "prod-001", "quantity": 1, "price_each": 99.99}],
    }
