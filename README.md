# Smart Shop Assistant

Multi-agent e-commerce system with RAG capabilities using the MCP (Model Context Protocol).

## Features

- **Multi-Agent Architecture**: Orchestrator routes requests to specialist agents (Inventory, Order, Shipping, Knowledge)
- **MCP Servers**: Domain-specific servers with tools and resources
- **RAG Pipeline**: Semantic search over product manuals, policies, and FAQs using Qdrant and Gemini embeddings

## Tech Stack

- **Language**: Python 3.11+
- **Package Manager**: uv
- **MCP Framework**: FastMCP
- **Vector Database**: Qdrant
- **Embeddings**: Google Gemini (gemini-embedding-001)
- **Database**: SQLite + SQLAlchemy
- **Validation**: Pydantic

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (for Qdrant)
- Google Gemini API key

## Quick Start

### 1. Clone and Setup

```bash
cd smart-shop-assistant

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Start Qdrant

```bash
docker compose up -d
```

### 3. Setup Database

```bash
uv run python scripts/setup_db.py
uv run python scripts/seed_data.py
```

### 4. Ingest Knowledge Base

```bash
uv run python scripts/ingest_docs.py --source docs/knowledge_base/
```

### 5. Run the CLI

```bash
uv run python -m src.cli
```

## Project Structure

```
smart-shop-assistant/
├── src/
│   ├── mcp_servers/     # MCP server implementations
│   ├── agents/          # AI agent orchestration
│   ├── rag/             # RAG pipeline components
│   ├── database/        # Database models
│   └── schemas/         # Pydantic schemas
├── docs/
│   ├── plans/           # Implementation plans
│   └── knowledge_base/  # Documents for RAG
├── scripts/             # Utility scripts
└── docker-compose.yml   # Qdrant setup
```

## Development

### Running Tests

```bash
uv run pytest
```

### Linting

```bash
uv run ruff check . --fix
uv run ruff format .
```

### Testing MCP Servers

```bash
uv run mcp dev src/mcp_servers/inventory_server.py
```

## MCP Servers

| Server | Description | Tools |
|--------|-------------|-------|
| Inventory | Stock management | check_stock, list_products, reserve_stock |
| Order | Order processing | create_order, get_order, apply_coupon |
| Shipping | Delivery management | estimate_delivery, track_package |
| Knowledge | RAG search | search_knowledge, get_product_manual |

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Implementation Plans](docs/plans/)

## License

MIT
