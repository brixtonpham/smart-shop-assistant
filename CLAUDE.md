# CLAUDE.md - Smart Shop Assistant

## Project Overview
E-commerce multi-agent system with RAG capabilities using MCP protocol.
- **Language:** Python 3.11+
- **Package Manager:** uv
- **Vector DB:** Qdrant (local Docker)
- **Embeddings:** Google Gemini (gemini-embedding-001)
- **Framework:** FastMCP for MCP servers

## Key Directories
- `src/` - Main source code
- `src/mcp_servers/` - MCP server implementations
- `src/agents/` - AI agent orchestration
- `src/rag/` - RAG pipeline components
- `src/database/` - Database models and migrations
- `docs/` - Architecture and planning documents
- `docs/plans/` - Implementation plans with checkboxes
- `scripts/` - Utility scripts

## Development Commands
- `uv run pytest` - Run tests
- `uv run mcp dev src/mcp_servers/inventory_server.py` - Test MCP server
- `docker compose up -d` - Start Qdrant
- `uv run python scripts/ingest_docs.py` - Ingest documents to RAG

## Git Workflow
- Branch from `develop` for features: `feature/ISSUE-XX-description`
- Commit format: `type(scope): message [#ISSUE]`
- Types: feat, fix, docs, refactor, test, chore
- Always create PR to `develop`, never direct push
- Squash merge for clean history

## Code Standards
- Type hints required on all functions
- Docstrings for public functions (Google style)
- Use Pydantic for data validation
- Async/await for I/O operations
- No print() - use logging module

## MCP Server Patterns
- One server = one domain (inventory, orders, shipping, knowledge)
- Tools return structured Pydantic models
- Resources use URI patterns: `domain://resource/{id}`
- Use SSE transport for HTTP-based communication

## RAG Configuration
- Embedding model: gemini-embedding-001 (3072 dimensions)
- Chunk size: 500 tokens with 50 token overlap
- Collections: product_manuals, policies, specs, faq
- Use task_type="RETRIEVAL_DOCUMENT" for docs, "RETRIEVAL_QUERY" for queries

## Important
- Check GitHub Issues before starting any task
- Update issue status when starting/completing work
- Commit after each logical unit of work
- Update docs/plans/ checkboxes as tasks complete
- Run linter before committing: `uv run ruff check .`

## Reference Files
@docs/architecture.md
@docs/plans/current_sprint.md
@README.md
