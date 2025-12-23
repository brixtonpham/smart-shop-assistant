# API Reference

## Inventory MCP Server

### Tools

#### check_stock
Check stock availability for a product.

```python
check_stock(product_id: str) -> StockStatus
```

**Returns:**
```json
{
  "product_id": "prod-001",
  "available": true,
  "quantity": 42,
  "reserved": 5
}
```

#### list_products
List products with optional filtering.

```python
list_products(
    category: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 20
) -> ProductList
```

#### reserve_stock
Reserve stock for a pending order.

```python
reserve_stock(
    product_id: str,
    quantity: int,
    duration_minutes: int = 15
) -> Reservation
```

#### release_stock
Release a stock reservation.

```python
release_stock(reservation_id: str) -> bool
```

### Resources

- `inventory://products` - All products
- `inventory://product/{id}` - Single product
- `inventory://categories` - Product categories

---

## Order MCP Server

### Tools

#### create_order
Create a new order.

```python
create_order(
    customer_id: str,
    items: list[OrderItem]
) -> Order
```

#### get_order
Get order details.

```python
get_order(order_id: str) -> Order
```

#### apply_coupon
Apply discount coupon to order.

```python
apply_coupon(order_id: str, code: str) -> OrderWithDiscount
```

#### cancel_order
Cancel an order.

```python
cancel_order(order_id: str, reason: str) -> bool
```

### Resources

- `orders://pending` - Pending orders
- `orders://order/{id}` - Single order

---

## Shipping MCP Server

### Tools

#### estimate_delivery
Get delivery time estimate.

```python
estimate_delivery(
    address: str,
    method: str = "standard"
) -> DeliveryEstimate
```

#### get_shipping_options
Get available shipping methods.

```python
get_shipping_options(
    weight: float,
    destination: str
) -> list[ShippingOption]
```

#### track_package
Track package status.

```python
track_package(tracking_number: str) -> TrackingStatus
```

### Resources

- `shipping://rates` - Shipping rates
- `shipping://carriers` - Available carriers

---

## Knowledge MCP Server

### Tools

#### search_knowledge
Search knowledge base with semantic similarity.

```python
search_knowledge(
    query: str,
    collection: str | None = None,
    product_id: str | None = None,
    top_k: int = 5
) -> SearchResults
```

#### get_product_manual
Get product manual content.

```python
get_product_manual(
    product_id: str,
    section: str | None = None
) -> ManualContent
```

#### get_policy
Get company policy content.

```python
get_policy(policy_type: str) -> PolicyContent
```

### Resources

- `knowledge://manuals/{product_id}` - Product manual
- `knowledge://policies/{type}` - Policy document
