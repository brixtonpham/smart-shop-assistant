# RAG Implementation Guidelines

## Embedding Model
- Use gemini-embedding-001 (3072 dimensions)
- Use task_type="RETRIEVAL_DOCUMENT" for documents
- Use task_type="RETRIEVAL_QUERY" for queries
- Handle rate limiting with exponential backoff

## Chunking Strategy
| Document Type | Strategy | Size |
|--------------|----------|------|
| Manuals | By section | 500 tokens |
| Policies | By clause | 300 tokens |
| Specs | One per product | Variable |
| FAQ | Q&A pairs | 200 tokens |

## Metadata
Always include:
- source_file
- product_id (if applicable)
- section
- chunk_index
- created_at

## Search
- Default top_k: 5
- Use cosine similarity
- Apply metadata filters when available
- Include source citations in responses

## Quality
- Test retrieval accuracy regularly
- Monitor search latency
- Update embeddings when documents change
