# Priority 3.1: RAG (Retrieval-Augmented Generation) Integration

**Status**: Ready for Implementation
**Estimated Effort**: 3 hours
**Expected Result**: RAG capabilities for document indexing and augmented code generation

---

## Overview

Integrate socratic-rag library to add Retrieval-Augmented Generation (RAG) capabilities. This allows the system to:
- Index documents as reference material
- Retrieve relevant context for code generation
- Augment LLM responses with project-specific knowledge
- Support context-aware code suggestions

---

## Current State

### Available Libraries
- socratic-rag: Provides RAG client, document store, retrieval engine
- socratic-knowledge: Provides knowledge base structure
- Integration points: Already have orchestrator, code generation, learning

### Usage Opportunities
1. **Code Generation**: Use RAG to retrieve relevant code examples before generating
2. **Learning**: Augment learning recommendations with project documentation
3. **Free Session**: Use RAG to provide context for user questions
4. **Knowledge Base**: Index project knowledge for intelligent retrieval

---

## Implementation Plan

### Phase 3.1.1: Add RAGIntegration to models_local.py (45 min)

**File**: `backend/src/socrates_api/models_local.py`

**New Class**: RAGIntegration (~100 lines)

```python
class RAGIntegration:
    """Wrapper around socratic-rag library for retrieval-augmented generation"""
    def __init__(self):
        self.available = False
        self.rag_client = None
        self.document_store = None
        self.retriever = None

        try:
            from socratic_rag import RAGClient, DocumentStore, Retriever
            self.rag_client = RAGClient()
            self.document_store = DocumentStore()
            self.retriever = Retriever()
            self.available = True
            logger.info("socratic-rag library initialized successfully")
        except ImportError:
            logger.warning("socratic-rag library not available - RAG features disabled")
            self.available = False
        except Exception as e:
            logger.warning(f"Failed to initialize socratic-rag: {e}")
            self.available = False

    def index_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        doc_type: str = "text",
        metadata: Dict = None
    ) -> bool:
        """Index document for RAG retrieval"""
        if not self.available or not self.document_store:
            logger.debug(f"RAG unavailable, cannot index document {doc_id}")
            return False

        try:
            self.document_store.add(
                doc_id,
                title=title,
                content=content,
                doc_type=doc_type,
                metadata=metadata or {}
            )
            logger.debug(f"Indexed document in RAG: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index document in RAG: {e}")
            return False

    def retrieve_context(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for context"""
        if not self.available or not self.retriever:
            logger.debug(f"RAG unavailable, cannot retrieve context for: {query}")
            return []

        try:
            results = self.retriever.retrieve(
                query=query,
                limit=limit,
                threshold=threshold
            )
            return results if results else []
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return []

    def augment_prompt(
        self,
        prompt: str,
        context_limit: int = 5,
        include_metadata: bool = True
    ) -> str:
        """Augment prompt with relevant context from knowledge base"""
        if not self.available or not self.retriever:
            return prompt

        try:
            # Retrieve relevant documents
            context_docs = self.retrieve_context(prompt, limit=context_limit)

            if not context_docs:
                return prompt

            # Build augmented prompt
            augmented = f"{prompt}\n\n---\n## Reference Context:\n\n"
            for doc in context_docs:
                title = doc.get("title", "Unknown")
                content = doc.get("content", "")[:500]  # Limit content
                score = doc.get("score", 0)
                augmented += f"**{title}** (relevance: {score:.2f})\n{content}\n\n"

            return augmented
        except Exception as e:
            logger.error(f"Failed to augment prompt: {e}")
            return prompt

    def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents using RAG retriever"""
        if not self.available or not self.retriever:
            return []

        try:
            results = self.retriever.search(query, limit=limit)
            return results if results else []
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []

    def get_status(self) -> Dict[str, bool]:
        """Get RAG integration status"""
        return {
            "available": self.available,
            "rag_client": self.rag_client is not None,
            "document_store": self.document_store is not None,
            "retriever": self.retriever is not None,
        }
```

---

### Phase 3.1.2: Create RAG Router (1 hour)

**File**: `backend/src/socrates_api/routers/rag.py` (NEW)

**Endpoints**:

1. **POST /rag/index** - Index document for RAG
   - Parameters: doc_id, title, content, doc_type, metadata
   - Response: Success with document ID

2. **POST /rag/retrieve** - Retrieve context for prompt
   - Parameters: query, limit, threshold
   - Response: List of relevant documents with scores

3. **POST /rag/augment** - Augment prompt with context
   - Parameters: prompt, context_limit
   - Response: Augmented prompt with context

4. **GET /rag/search** - Search documents
   - Parameters: query, limit
   - Response: Search results

5. **GET /rag/status** - Get RAG system status
   - Response: Available, document_store status, retriever status

6. **DELETE /rag/index/{doc_id}** - Remove document from RAG
   - Parameters: doc_id
   - Response: Success

**Implementation Example**:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from socrates_api.models import APIResponse
from socrates_api.models_local import RAGIntegration

router = APIRouter(prefix="/rag", tags=["RAG"])

class IndexDocumentRequest(BaseModel):
    doc_id: str
    title: str
    content: str
    doc_type: Optional[str] = "text"
    metadata: Optional[Dict] = None

@router.post("/index", response_model=APIResponse)
async def index_document(
    request: IndexDocumentRequest,
    current_user: str = Depends(get_current_user),
):
    """Index document for retrieval-augmented generation"""
    try:
        rag = RAGIntegration()
        if not rag.available:
            raise HTTPException(
                status_code=503,
                detail="RAG integration not available"
            )

        success = rag.index_document(
            doc_id=request.doc_id,
            title=request.title,
            content=request.content,
            doc_type=request.doc_type,
            metadata=request.metadata
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to index document"
            )

        return APIResponse(
            success=True,
            status="created",
            message=f"Document indexed: {request.doc_id}",
            data={"doc_id": request.doc_id, "title": request.title}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing document: {e}")
        raise HTTPException(status_code=500, detail="Operation failed")

@router.post("/retrieve", response_model=APIResponse)
async def retrieve_context(
    query: str,
    limit: int = Query(5, ge=1, le=20),
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    current_user: str = Depends(get_current_user),
):
    """Retrieve relevant documents for context"""
    try:
        rag = RAGIntegration()
        if not rag.available:
            raise HTTPException(status_code=503, detail="RAG not available")

        results = rag.retrieve_context(query, limit, threshold)

        return APIResponse(
            success=True,
            status="success",
            message="Context retrieved",
            data={
                "query": query,
                "count": len(results),
                "documents": results
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        raise HTTPException(status_code=500, detail="Operation failed")

@router.get("/status", response_model=APIResponse)
async def get_rag_status(
    current_user: str = Depends(get_current_user),
):
    """Get RAG system status"""
    try:
        rag = RAGIntegration()
        status_info = rag.get_status()

        return APIResponse(
            success=True,
            status="success",
            message="RAG status retrieved",
            data=status_info
        )
    except Exception as e:
        logger.error(f"Error getting RAG status: {e}")
        raise HTTPException(status_code=500, detail="Operation failed")
```

---

### Phase 3.1.3: Integrate RAG with Code Generation (45 min)

**File**: `backend/src/socrates_api/orchestrator.py`

**Add to LLMClientAdapter**:

```python
def generate_response_with_rag(
    self,
    prompt: str,
    augment_with_context: bool = False,
    context_limit: int = 5,
    **kwargs
) -> str:
    """Generate response, optionally augmented with RAG context"""
    if augment_with_context:
        try:
            from socrates_api.models_local import RAGIntegration
            rag = RAGIntegration()
            if rag.available:
                prompt = rag.augment_prompt(prompt, context_limit=context_limit)
                logger.debug(f"Augmented prompt with RAG context ({context_limit} documents)")
        except Exception as e:
            logger.warning(f"RAG augmentation failed: {e}, using original prompt")

    # Generate response with (potentially augmented) prompt
    return self.generate_response(prompt, **kwargs)
```

**Update code generation to use RAG**:

```python
def generate_code_with_rag(self, project, user_input: str) -> str:
    """Generate code with RAG-augmented context"""
    # Build base prompt
    prompt = self._build_code_generation_prompt(project, user_input)

    # Augment with RAG context
    augmented_prompt = self.llm_client.generate_response_with_rag(
        prompt,
        augment_with_context=True,
        context_limit=5
    )

    return augmented_prompt
```

---

### Phase 3.1.4: Auto-Index Knowledge Documents (30 min)

**Update knowledge_management.py**:

When a knowledge document is added, automatically index it in RAG:

```python
# In add_knowledge_document endpoint

# After adding to KnowledgeManager, also index in RAG
rag = RAGIntegration()
if rag.available:
    rag.index_document(
        doc_id=doc_id,
        title=request.title,
        content=request.content,
        doc_type=request.type or "text",
        metadata={"project_id": project_id, "created_by": current_user}
    )
    logger.debug(f"Indexed knowledge document in RAG: {doc_id}")
```

---

## Integration Diagram

```
Knowledge Management
    ↓
Add Document
    ↓
Store in Project
    ↓
Store in socratic-knowledge
    ↓
Index in RAG ← RAGIntegration
    ↓
Available for retrieval
    ↓
Used in Code Generation
```

---

## API Endpoints

### RAG Endpoints (6 total)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /rag/index | Index document for RAG |
| POST | /rag/retrieve | Retrieve context for query |
| POST | /rag/augment | Augment prompt with context |
| GET | /rag/search | Search indexed documents |
| GET | /rag/status | Get RAG system status |
| DELETE | /rag/index/{doc_id} | Remove document from RAG |

### Usage Examples

**Index a document**:
```bash
curl -X POST "http://localhost:8000/rag/index" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "doc_example",
    "title": "Authentication Pattern",
    "content": "Our project uses JWT tokens...",
    "doc_type": "text",
    "metadata": {"project_id": "proj_123"}
  }'
```

**Retrieve context**:
```bash
curl -X POST "http://localhost:8000/rag/retrieve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "how to implement authentication"}'
```

**Get RAG status**:
```bash
curl -X GET "http://localhost:8000/rag/status" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Testing Strategy

### Unit Tests
```python
test_rag_integration_available()
test_index_document()
test_retrieve_context()
test_augment_prompt()
test_search_documents()
test_rag_graceful_fallback()
```

### Integration Tests
```python
test_knowledge_document_auto_indexes_in_rag()
test_code_generation_uses_rag_context()
test_rag_context_improves_relevance()
test_rag_search_works_across_projects()
```

### E2E Tests
```
1. Create project
2. Add knowledge documents
3. Documents auto-indexed in RAG
4. Query RAG for context
5. Generate code with RAG-augmented prompt
6. Verify code uses knowledge from RAG
```

---

## Success Criteria

- [ ] RAGIntegration class implemented in models_local.py
- [ ] RAG router created with 6 endpoints
- [ ] Knowledge documents auto-indexed in RAG
- [ ] Code generation uses RAG context
- [ ] RAG searches work across documents
- [ ] Graceful fallback if socratic-rag unavailable
- [ ] No performance regression
- [ ] All endpoints tested and working

---

## Files to Create/Modify

1. **backend/src/socrates_api/models_local.py** (add)
   - RAGIntegration class (~100 lines)

2. **backend/src/socrates_api/routers/rag.py** (NEW)
   - 6 endpoints (~200 lines)

3. **backend/src/socrates_api/orchestrator.py** (modify)
   - Add generate_response_with_rag() method
   - Update code generation to use RAG

4. **backend/src/socrates_api/routers/knowledge_management.py** (modify)
   - Auto-index documents in RAG when added

---

## Estimated Breakdown

| Task | Time |
|------|------|
| RAGIntegration class | 45 min |
| RAG router creation | 60 min |
| Orchestrator integration | 45 min |
| Knowledge auto-indexing | 30 min |
| Testing | 30 min |
| **Total** | **3 hours 30 min** |

---

**Ready to implement Priority 3.1: RAG Integration**

Next: Proceed to Priority 3.2 (Workflow Integration) or 3.3 (Analyzer Deep Integration)
