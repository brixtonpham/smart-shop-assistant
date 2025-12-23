# Current Sprint Plan

## Sprint Goal
Phase 3: RAG System Implementation

## Active Issues

### Issue #9: RAG Pipeline - Document Chunking
**Branch:** feature/ISSUE-9-rag-chunking
**Status:** Not Started

#### Implementation Plan
- [ ] Create src/rag/chunker.py with chunking strategies
- [ ] Implement section-based chunking for manuals (500 tokens)
- [ ] Implement clause-based chunking for policies (300 tokens)
- [ ] Implement Q&A pair chunking for FAQs (200 tokens)
- [ ] Add metadata extraction (source, section, product_id)

---

### Issue #10: RAG Pipeline - Gemini Embeddings
**Branch:** feature/ISSUE-10-embeddings
**Status:** Not Started

#### Implementation Plan
- [ ] Create src/rag/embedder.py for embedding generation
- [ ] Integrate Google Gemini gemini-embedding-001 model
- [ ] Implement task_type switching (RETRIEVAL_DOCUMENT vs RETRIEVAL_QUERY)
- [ ] Add rate limiting and retry logic
- [ ] Handle batch embedding for efficiency

---

### Issue #11: Qdrant Vector Store Integration
**Branch:** feature/ISSUE-11-qdrant
**Status:** Not Started

#### Implementation Plan
- [ ] Create src/rag/vector_store.py for Qdrant operations
- [ ] Implement collection management (create, delete)
- [ ] Implement document upsert with metadata
- [ ] Implement similarity search with filters
- [ ] Add connection pooling and error handling

---

### Issue #12: Knowledge MCP Server
**Branch:** feature/ISSUE-12-knowledge-server
**Status:** Not Started

#### Implementation Plan
- [ ] Create src/mcp_servers/knowledge_server.py
- [ ] Implement search_knowledge tool
- [ ] Implement get_product_manual tool
- [ ] Implement get_policy tool
- [ ] Add resources: knowledge://manuals, knowledge://policies

---

## Previously Completed (Phase 1 & 2)

### Issue #1: Project Setup and Configuration
**Branch:** feature/ISSUE-1-project-setup
**Status:** Complete

#### Implementation Plan
- [x] Initialize project with `uv init`
- [x] Configure pyproject.toml with dependencies
- [x] Create .env.example with required variables
- [x] Set up docker-compose.yml for Qdrant
- [x] Create CLAUDE.md with project instructions
- [x] Create README.md with setup instructions

#### Notes
- Dependencies listed in pyproject.toml

#### Files to Modify
- pyproject.toml
- docker-compose.yml
- .env.example
- CLAUDE.md
- README.md

---

### Issue #2: Database Schema Design
**Branch:** feature/ISSUE-2-database-schema
**Status:** Complete

#### Implementation Plan
- [x] Create SQLAlchemy models in src/database/models.py
- [x] Implement connection management in src/database/connection.py
- [x] Create migration script in scripts/setup_db.py
- [x] Add sample data seeding in scripts/seed_data.py
- [x] Document schema in docs/architecture.md

#### Notes
- Use async SQLAlchemy with aiosqlite
- Tables: products, customers, orders, order_items, reservations

#### Files to Modify
- src/database/models.py
- src/database/connection.py
- scripts/setup_db.py
- scripts/seed_data.py
- docs/architecture.md

---

### Issue #3: Pydantic Schemas
**Branch:** feature/ISSUE-3-pydantic-schemas
**Status:** Complete

#### Implementation Plan
- [x] Create src/schemas/products.py
- [x] Create src/schemas/orders.py
- [x] Create src/schemas/shipping.py
- [x] Create src/schemas/common.py

#### Notes
- 22 schemas implemented with Pydantic v2 syntax
- Validators for price, quantity, stock fields
- Field examples for OpenAPI documentation

---

### Issue #4: Configuration Management
**Branch:** feature/ISSUE-4-configuration
**Status:** Complete

#### Implementation Plan
- [x] Create src/config.py with Settings class
- [x] Support .env file loading
- [x] Add Qdrant, Gemini, MCP, RAG settings
- [x] Document all config options in .env.example

#### Notes
- Using Pydantic v2 SettingsConfigDict
- Cached settings via @lru_cache
- Validators for log_level, chunk_overlap

---

## Completed This Sprint
- [x] Issue #1: Project Setup and Configuration
- [x] Issue #2: Database Schema Design
- [x] Issue #3: Pydantic Schemas
- [x] Issue #4: Configuration Management
- [x] Issue #5: Inventory MCP Server
- [x] Issue #6: Order MCP Server
- [x] Issue #7: Shipping MCP Server
- [x] Issue #8: MCP Integration Testing (104 tests, 94% coverage)

**Phase 1: Foundation - COMPLETE**
**Phase 2: MCP Servers - COMPLETE**

## Blockers
- None

## Learnings
- Hatchling build requires `[tool.hatch.build.targets.wheel] packages = ["src"]` when using src/ layout
- Async SQLAlchemy with aiosqlite requires `greenlet` dependency
- Use `Mapped[T]` syntax for type-safe column definitions
- Pydantic v2 uses `model_config` dict instead of `class Config`
- Use SettingsConfigDict for pydantic-settings v2
