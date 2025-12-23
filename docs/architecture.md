# Smart Shop Assistant - Architecture

## Overview

Multi-agent e-commerce system with RAG capabilities using the MCP protocol.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI / Client                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator Agent                          │
│  - Intent recognition                                            │
│  - Agent routing                                                 │
│  - Response synthesis                                            │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Inventory   │     │     Order     │     │   Shipping    │
│    Agent      │     │    Agent      │     │    Agent      │
└───────────────┘     └───────────────┘     └───────────────┘
        │                     │                       │
        ▼                     ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Inventory   │     │    Order      │     │   Shipping    │
│  MCP Server   │     │  MCP Server   │     │  MCP Server   │
└───────────────┘     └───────────────┘     └───────────────┘
        │                     │                       │
        └─────────────────────┼───────────────────────┘
                              ▼
                    ┌───────────────┐
                    │    SQLite     │
                    │   Database    │
                    └───────────────┘

                    ┌───────────────┐
                    │   Knowledge   │
                    │    Agent      │
                    └───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Knowledge   │
                    │  MCP Server   │
                    └───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Qdrant     │
                    │  Vector DB    │
                    └───────────────┘
```

## Components

### MCP Servers

| Server | Domain | Tools |
|--------|--------|-------|
| Inventory | Stock management | check_stock, list_products, reserve_stock, release_stock |
| Order | Order processing | create_order, get_order, apply_coupon, cancel_order |
| Shipping | Delivery | estimate_delivery, get_shipping_options, track_package |
| Knowledge | RAG | search_knowledge, get_product_manual, get_policy |

### Agents

| Agent | Responsibility |
|-------|---------------|
| Orchestrator | Intent routing, multi-agent coordination |
| Inventory | Stock availability, alternatives |
| Order | Checkout, coupons, order history |
| Shipping | Delivery estimates, tracking |
| Knowledge | Product info, policies, troubleshooting |

### Data Storage

- **SQLite**: Transactional data (products, orders, customers)
- **Qdrant**: Vector embeddings for RAG (manuals, policies, FAQs)

## RAG Pipeline

```
Documents → Chunker → Embedder → Qdrant
                          ↑
                    Gemini API
                    (embedding)

Query → Embedder → Qdrant Search → Top-K Results → Response
```

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastMCP
- **Vector DB**: Qdrant
- **Embeddings**: Google Gemini (gemini-embedding-001)
- **Database**: SQLite + SQLAlchemy
- **Validation**: Pydantic
