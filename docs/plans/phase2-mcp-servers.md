# Phase 2: MCP Servers

**Duration:** Week 3-4
**Goal:** Build domain-specific MCP servers

## Issues

### Issue #5: Inventory MCP Server
- [ ] Create src/mcp_servers/inventory_server.py
- [ ] Implement tool: check_stock
- [ ] Implement tool: list_products
- [ ] Implement tool: reserve_stock
- [ ] Implement tool: release_stock
- [ ] Implement tool: low_stock_report
- [ ] Implement resource: inventory://products
- [ ] Implement resource: inventory://product/{id}
- [ ] Implement resource: inventory://categories
- [ ] Test with MCP Inspector

### Issue #6: Order MCP Server
- [ ] Create src/mcp_servers/order_server.py
- [ ] Implement tool: create_order
- [ ] Implement tool: get_order
- [ ] Implement tool: apply_coupon
- [ ] Implement tool: cancel_order
- [ ] Implement tool: order_history
- [ ] Implement resource: orders://pending
- [ ] Implement resource: orders://order/{id}
- [ ] Test with MCP Inspector

### Issue #7: Shipping MCP Server
- [ ] Create src/mcp_servers/shipping_server.py
- [ ] Implement tool: estimate_delivery
- [ ] Implement tool: get_shipping_options
- [ ] Implement tool: create_shipment
- [ ] Implement tool: track_package
- [ ] Implement resource: shipping://rates
- [ ] Implement resource: shipping://carriers
- [ ] Create shipping_rates.json with mock data

### Issue #8: MCP Server Integration Testing
- [ ] Set up test fixtures with sample data
- [ ] Test Inventory server tools
- [ ] Test Order server tools
- [ ] Test Shipping server tools
- [ ] Test cross-server workflows
- [ ] Document API in docs/api-reference.md

## Acceptance Criteria
- All 3 MCP servers work in MCP Inspector
- Cross-server workflows tested
- API documented
