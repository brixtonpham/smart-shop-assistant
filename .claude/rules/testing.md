# Testing Requirements

## Unit Tests
- Test all public functions
- Use pytest-asyncio for async tests
- Mock external services (Qdrant, Gemini API)
- Aim for 80%+ coverage

## Integration Tests
- Test MCP server tools with MCP Inspector
- Test database operations with test database
- Test RAG pipeline end-to-end

## Test Structure
```
tests/
├── unit/
│   ├── test_schemas.py
│   ├── test_database.py
│   └── test_chunker.py
├── integration/
│   ├── test_inventory_server.py
│   ├── test_order_server.py
│   └── test_rag_pipeline.py
└── conftest.py
```

## Fixtures
- Use conftest.py for shared fixtures
- Create test database in memory
- Mock API responses

## Running Tests
```bash
uv run pytest                    # All tests
uv run pytest tests/unit         # Unit tests only
uv run pytest -v --tb=short      # Verbose with short traceback
uv run pytest --cov=src          # With coverage
```
