# Phase 3: RAG System

**Duration:** Week 5-6
**Goal:** Build RAG pipeline with Qdrant and Gemini embeddings

## Issues

### Issue #9: Gemini Embeddings Integration
- [ ] Create src/rag/embeddings.py
- [ ] Implement GeminiEmbedder class
- [ ] Support task_type parameter
- [ ] Implement batch embedding
- [ ] Add caching for repeated embeddings
- [ ] Handle rate limiting

### Issue #10: Document Chunking Pipeline
- [ ] Create src/rag/chunker.py
- [ ] Implement FixedSizeChunker
- [ ] Implement SemanticChunker
- [ ] Implement FAQChunker
- [ ] Add metadata extraction
- [ ] Support markdown, text, JSON formats

### Issue #11: Qdrant Vector Store Integration
- [ ] Create src/rag/retriever.py
- [ ] Implement QdrantStore class
- [ ] Create collections
- [ ] Implement upsert with metadata
- [ ] Implement similarity search with filters
- [ ] Implement hybrid search
- [ ] Add collection management utilities

### Issue #12: Document Ingestion Pipeline
- [ ] Create src/rag/ingestion.py
- [ ] Implement DocumentLoader
- [ ] Create ingestion workflow
- [ ] Create scripts/ingest_docs.py CLI
- [ ] Add progress reporting
- [ ] Handle incremental updates

### Issue #13: Knowledge MCP Server
- [ ] Create src/mcp_servers/knowledge_server.py
- [ ] Implement tool: search_knowledge
- [ ] Implement tool: get_product_manual
- [ ] Implement tool: get_policy
- [ ] Implement tool: search_troubleshooting
- [ ] Implement tool: compare_products
- [ ] Implement resources
- [ ] Test with MCP Inspector

### Issue #14: Create Sample Knowledge Base
- [ ] Create 5 product manuals
- [ ] Create company policies
- [ ] Create product specs
- [ ] Create 20+ FAQ entries
- [ ] Create troubleshooting guides

## Acceptance Criteria
- Knowledge base ingested (100+ chunks)
- Search returns relevant results
- Knowledge MCP server tested
