# MCP Servers

This directory contains Model Context Protocol (MCP) servers for the Smart Shop Assistant.

## Inventory Server

**File:** `inventory_server.py`

**Description:** Stock management and product operations MCP server.

### Tools

| Tool | Description | Parameters | Returns |
|------|-------------|------------|---------|
| `check_stock` | Check stock availability | `product_id: str` | `StockCheck` (available, quantity, reserved) |
| `list_products` | List products with filtering | `category?: str`, `search?: str`, `page: int`, `limit: int` | `ProductList` (paginated) |
| `reserve_stock` | Reserve stock temporarily | `product_id: str`, `quantity: int`, `duration_minutes: int` | `Reservation` |
| `release_stock` | Release a reservation | `reservation_id: str` | `bool` |
| `low_stock_report` | Get low stock products | `threshold: int` | `ProductList` |

### Resources

| URI | Description |
|-----|-------------|
| `inventory://products` | All products (JSON) |
| `inventory://product/{id}` | Single product by ID (JSON) |
| `inventory://categories` | List of categories (JSON) |

### Running the Server

**Development (with MCP Inspector):**
```bash
uv run mcp dev src/mcp_servers/inventory_server.py
```

**Production (SSE transport):**
```bash
uv run python -m src.mcp_servers.inventory_server
```

### Configuration

Server configuration is loaded from environment variables via `src/config.py`:

- `MCP_SERVER_HOST` - Server host (default: `localhost`)
- `MCP_SERVER_PORT` - Server port (default: `8000`)
- `DATABASE_PATH` - SQLite database path (default: `./data/shop.db`)

### Examples

**Check stock availability:**
```python
from src.mcp_servers.inventory_server import check_stock

result = await check_stock("123e4567-e89b-12d3-a456-426614174000")
# Returns: StockCheck(product_id=..., available=True, quantity=95, reserved=5)
```

**Reserve stock:**
```python
from src.mcp_servers.inventory_server import reserve_stock

reservation = await reserve_stock(
    product_id="123e4567-e89b-12d3-a456-426614174000",
    quantity=10,
    duration_minutes=15
)
# Returns: Reservation(id=..., product_id=..., quantity=10, expires_at=...)
```

**List products by category:**
```python
from src.mcp_servers.inventory_server import list_products

products = await list_products(category="Electronics", page=1, limit=10)
# Returns: ProductList(items=[...], total=50, page=1, limit=10, pages=5)
```

## Testing

Integration tests are located in `tests/integration/test_inventory_server.py`.

**Run tests:**
```bash
uv run pytest tests/integration/test_inventory_server.py -v
```

**Run with coverage:**
```bash
uv run pytest tests/integration/test_inventory_server.py --cov=src/mcp_servers --cov-report=html
```

## Architecture Notes

### Stock Reservation System

The inventory server implements a time-based reservation system:

1. **Reserve stock**: Creates a temporary hold on inventory with an expiration time
2. **Expiration**: Reservations automatically expire and don't affect available stock after expiry
3. **Thread-safe**: Uses SQLAlchemy's `with_for_update()` for row-level locking to prevent race conditions
4. **Available quantity calculation**: `available = stock - active_reservations`

### Database Queries

- **Efficient filtering**: Uses SQLAlchemy's `ilike()` for case-insensitive search
- **Pagination**: Offset-based pagination with configurable page size
- **Eager loading**: Uses `selectin` loading strategy for relationships
- **Aggregations**: Uses `func.sum()` and `func.count()` for efficient calculations

### Error Handling

All tools validate inputs and raise `ValueError` with descriptive messages for:
- Invalid UUID formats
- Non-existent products/reservations
- Insufficient stock
- Invalid parameters (negative quantities, invalid page numbers, etc.)
