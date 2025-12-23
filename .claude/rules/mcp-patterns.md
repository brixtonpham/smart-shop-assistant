# MCP Development Rules

## Server Structure
- One server per domain (inventory, orders, shipping, knowledge)
- Use FastMCP for server implementation
- Tools return structured Pydantic models

## Tool Guidelines
- Tool names should be verb_noun format (check_stock, create_order)
- All tools must have docstrings
- Parameters must have type hints
- Return types must be Pydantic models

## Resource Guidelines
- Use URI patterns: `domain://resource/{id}`
- Resources are read-only
- Return JSON-serializable data

## Transport
- Use SSE (Server-Sent Events) transport for HTTP-based communication
- Configure server host and port in settings
- Handle connection errors and reconnection gracefully
- Support CORS for cross-origin requests

## Error Handling
- Return structured error responses
- Include error codes and messages
- Log errors with context
