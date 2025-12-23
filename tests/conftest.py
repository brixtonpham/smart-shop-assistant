"""Pytest configuration and shared fixtures."""

import pytest


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
        "items": [
            {"product_id": "prod-001", "quantity": 1, "price_each": 99.99}
        ],
    }
