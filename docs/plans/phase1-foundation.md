# Phase 1: Foundation

**Duration:** Week 1-2
**Goal:** Project setup, database, and configuration

## Issues

### Issue #1: Project Setup and Configuration
- [ ] Create project with `uv init smart-shop-assistant`
- [ ] Configure pyproject.toml with dependencies
- [ ] Create .env.example with required variables
- [ ] Set up docker-compose.yml for Qdrant
- [ ] Create CLAUDE.md with project instructions
- [ ] Create README.md with setup instructions

### Issue #2: Database Schema Design
- [ ] Create SQLAlchemy models in src/database/models.py
- [ ] Implement connection management in src/database/connection.py
- [ ] Create migration script in scripts/setup_db.py
- [ ] Add sample data seeding in scripts/seed_data.py
- [ ] Document schema in docs/architecture.md

### Issue #3: Pydantic Schemas
- [ ] Create src/schemas/products.py
- [ ] Create src/schemas/orders.py
- [ ] Create src/schemas/shipping.py
- [ ] Create src/schemas/common.py

### Issue #4: Configuration Management
- [ ] Create src/config.py with Settings class
- [ ] Support .env file loading
- [ ] Add all required settings
- [ ] Document all config options

## Acceptance Criteria
- `uv sync` installs all dependencies
- `docker compose up -d` starts Qdrant on port 6333
- Database seeded with sample data
- All schemas validated
