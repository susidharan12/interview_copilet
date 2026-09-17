# RAG Pipeline — Design Document

## Overview

Hybrid retrieval-augmented generation combining lexical (BM25), semantic (vector), fusion (RRF), and reranking for high-quality, low-latency retrieval from the user's knowledge base.

## Pipeline

```
Query
  │
  ▼
┌──────────────────┐
│ Query Normalizer  │ ← Expand, correct, extract entities
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│  BM25  │ │ Vector │ ← Parallel retrieval
│ Index  │ │ Search │
└───┬────┘ └───┬────┘
    └────┬─────┘
         ▼
┌──────────────────┐
│  RRF Fusion      │ ← Reciprocal Rank Fusion
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Reranker       │ ← Cross-encoder scoring
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Context Selector │ ← Budget-aware selection + dedup
└────────┬─────────┘
         │
         ▼
    Ranked Context
```

## Components

### Query Normalizer
- Extract technology entities
- Expand abbreviations (k8s → kubernetes)
- Detect query type (factual, code, how-to, comparison)
- Preserve original query for metadata filtering

### BM25 Retrieval
- PostgreSQL full-text search with tsvector/tsquery
- Weighted fields: title (3x), content (1x), tags (2x)
- Language-specific stemming
- Configurable top-K (default 20)

### Vector Retrieval
- pgvector with cosine similarity
- Embedding model: text-embedding-3-small (1536d)
- Metadata filters applied at query time
- Configurable top-K (default 20)
- Similarity threshold: 0.7

### Reciprocal Rank Fusion
- Formula: RRF(d) = Σ 1/(k + rank_i(d)) for each retrieval list
- k = 60 (standard constant)
- Combines BM25 + vector scores
- Produces unified ranking

### Reranker
- Cross-encoder model for query-document relevance scoring
- Applied to top candidates (max 40)
- Produces final relevance score per chunk
- Falls back to RRF score if reranker unavailable

### Context Selector
- Token budget management (configurable, default 4000 tokens)
- MMR (Maximal Marginal Relevance) for diversity
- Deduplication of overlapping chunks
- Source attribution tracking

## Metadata Schema

Every chunk carries metadata:

```json
{
  "user_id": "uuid",
  "document_id": "uuid",
  "document_type": "resume|project|notes|jd|technical|other",
  "technology": ["python", "kubernetes"],
  "project": "project-name",
  "source": "filename.md",
  "section": "experience|skills|projects|education",
  "interview_role": "senior-backend",
  "created_at": "ISO8601",
  "chunk_index": 0
}
```

## Chunking Strategies

| Document Type | Strategy | Chunk Size | Overlap |
|---------------|----------|------------|---------|
| Resume | Section-based | Whole sections | N/A |
| Technical docs | Paragraph | 512 tokens | 50 tokens |
| Project code | File + docstring | 1024 tokens | 100 tokens |
| Notes | Paragraph | 512 tokens | 50 tokens |
| Job description | Section-based | Whole sections | N/A |

## Caching

- Embedding cache: hash(query) → embedding vector
- Retrieval cache: hash(query + filters) → chunk IDs (TTL: 5min)
- Frequent queries: LRU cache for repeated interview patterns

## Evaluation Metrics

- **Recall@K**: Are relevant documents in top-K?
- **MRR**: Mean Reciprocal Rank of first relevant result
- **NDCG**: Normalized Discounted Cumulative Gain
- **Retrieval latency**: p50, p95, p99
- **Answer attribution**: % of answer claims backed by retrieved context
