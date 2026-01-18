# ADR-002: Vector Database - ChromaDB

**Date**: January 2026
**Status**: Accepted
**Deciders**: Architecture Team

## Context

Socrates AI needed to store and search project specifications, documentation, and knowledge base entries using semantic similarity, not just keyword matching.

**Requirements**:
- Semantic search across project context
- Fast similarity matching
- Embedded documents support
- Simple, single-machine friendly
- No separate infrastructure needed

## Decision

We chose **ChromaDB** as our vector database because it:
- Requires zero configuration (embedded/local-first)
- Provides semantic search via embeddings
- Handles vector storage and retrieval efficiently
- Supports metadata filtering
- Integrates seamlessly with Python applications
- No separate service to deploy

## ChromaDB Architecture

```
Application
    ↓
SentenceTransformers (Embeddings)
    ↓
ChromaDB
    ├─ Vector Storage
    ├─ Metadata Index
    └─ Chroma DB File
```

## Advantages

✓ **Zero Infrastructure**: No separate database service
✓ **Fast Setup**: Works out of the box
✓ **Semantic Search**: Understand meaning, not just keywords
✓ **Flexible**: Stores both embeddings and metadata
✓ **Portable**: Single directory with all data
✓ **Lightweight**: Minimal dependencies

## Disadvantages

✗ **Single Machine**: Not designed for distributed systems
✗ **Limited Scaling**: Performance degrades with very large collections
✗ **No Query Language**: Limited to similarity search patterns
✗ **Embedded Only**: No multi-client support

## Alternatives Considered

### 1. Pinecone
- Cloud-based vector database
- **Rejected**: Requires external service, additional costs

### 2. Weaviate
- Self-hosted or cloud vector search
- **Rejected**: Overkill for single-machine requirements

### 3. Milvus
- Distributed vector database
- **Rejected**: Complex to deploy and manage

### 4. FAISS (Facebook AI)
- Vector similarity search library
- **Rejected**: Lower-level, requires more implementation

### 5. Elasticsearch
- Full-text + vector search
- **Rejected**: Heavy infrastructure overhead

## Consequences

- Knowledge base is stored locally with projects
- Semantic search is fast for reasonable database sizes
- Scaling to millions of documents requires migration strategy
- No multi-machine sharing without custom infrastructure
- Backup includes vector data automatically

## Implementation Details

**Initialization**:
```python
from socratic_system.database import VectorDatabase

vector_db = VectorDatabase(path="~/.socrates/vector_db")
```

**Add Documents**:
```python
vector_db.add(
    documents=["specification", "requirement"],
    ids=["doc_1", "doc_2"],
    metadatas=[
        {"project": "proj_123", "type": "spec"},
        {"project": "proj_123", "type": "requirement"}
    ]
)
```

**Search**:
```python
results = vector_db.search_similar(
    query="user authentication",
    top_k=5
)
```

## Embedding Model

**Default**: `all-MiniLM-L6-v2` (SentenceTransformers)
- Size: ~22 MB
- Embedding dimension: 384
- Performance: Fast, suitable for CPU inference
- Quality: Good for semantic understanding

**Customizable**:
```python
config = ConfigBuilder("sk-ant-...") \
    .with_embedding_model("all-mpnet-base-v2") \
    .build()
```

## Storage Considerations

**Typical Storage**:
- Empty: ~50 MB
- With 100 projects × 10 docs each: ~200 MB
- With 1,000 documents: ~300-400 MB

**Scaling Limit**: ~100,000 documents before performance concerns

## Monitoring & Maintenance

**Check Size**:
```bash
du -sh ~/.socrates/vector_db
```

**Cleanup Old Collections**:
```python
# List collections
vector_db.list_collections()

# Delete old collection
vector_db.delete_collection("old_collection")
```

## Future Considerations

**v1.4+**: Consider migration path if database grows significantly
**v1.5+**: Multi-machine support if needed
**v2.0+**: Distributed vector database option

## Related ADRs
- ADR-001: Multi-Agent Architecture
- ADR-003: Event-Driven Communication

---

**Decision**: ACCEPTED
**Implementation**: ✓ Complete
**Review Date**: Q4 2026
