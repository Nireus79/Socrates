# Phase 5 Investigation - Knowledge Base Integration

## Date: April 2, 2026
## Status: Investigation Phase

---

## Overview

Phase 5 focuses on enhancing the Knowledge Base (KB) integration to make question generation more intelligent, context-aware, and document-focused. Currently, KB functionality exists but lacks optimization for document relevance, multi-document handling, and context-aware retrieval.

---

## Current KB Implementation Status

### Existing Infrastructure

**Knowledge Router** (`knowledge.py`): 1,533 lines
- `GET /knowledge/documents` - List documents with filtering
- `GET /knowledge/all-sources` - Get all KB sources
- `GET /knowledge/documents/{doc_id}` - Get document details
- `GET /knowledge/documents/{doc_id}/download` - Download document
- `POST /knowledge/import/file` - Import from file
- `POST /knowledge/import/url` - Import from URL
- `POST /knowledge/import/text` - Import text entry
- `GET /knowledge/search` - Search knowledge base
- `DELETE /knowledge/documents/{doc_id}` - Delete document
- `POST /knowledge/bulk/delete` - Bulk delete
- `POST /knowledge/bulk/import` - Bulk import
- `GET /knowledge/analytics/{doc_id}` - Document analytics
- `POST /knowledge/entry` - Add KB entry
- `GET /knowledge/debug/chunks` - Debug vector DB chunks

**Knowledge Management Router** (`knowledge_management.py`): 752 lines
- Additional KB management features

### Vector Database Integration

**Implementation**: ChromaDB (default vector store)
**Location**: `models_local.py`
```python
class VectorDBManager:
    def __init__(self, vector_db: str = "chromadb"):
        self.vector_db = ChromaDBVectorStore()  # Default to chromadb

    def switch_vector_db(self, new_db: str) -> bool:
        # Switchable vector DB implementation
```

**Status**: ✅ Partially Implemented

---

## Current KB Strategy Implementation

### KB Strategy Selection

**Location**: `orchestrator.py:_determine_kb_strategy()`

**Current Logic**:
```python
def _determine_kb_strategy(self, phase: str, question_number: int) -> str:
    """
    Select KB loading strategy based on phase and question number.

    Strategy:
    - Early phase (Q 1-4): "snippet" (3 chunks)
    - Later phase (Q 5+): "full" (5 chunks)
    - Design/Implementation: Always "full"
    """
    if phase in ["design", "implementation"]:
        return "full"  # Always full for detailed phases

    if question_number <= 4:
        return "snippet"  # 3 chunks for early questions
    else:
        return "full"  # 5 chunks for later questions
```

**Caching**: Per-phase caching implemented

**Status**: ✅ Basic Implementation Ready

---

## Current Document Understanding

**Implementation**: Basic document alignment analysis
**Location**: `orchestrator.py:_get_document_understanding()`

**Features**:
- ✅ Document summary extraction
- ✅ Alignment scoring with project specs
- ✅ Gap identification
- ⏳ Limited multi-document support

**Status**: ⚠️ Partial Implementation

---

## Gaps & Enhancement Opportunities

### 1. Vector Database Optimization

**Current State**:
- Basic ChromaDB integration
- No query optimization
- Simple similarity search

**Needed Enhancements**:
- [ ] Query optimization for relevance
- [ ] Semantic search improvements
- [ ] Hybrid search (keyword + semantic)
- [ ] Vector dimension optimization
- [ ] Similarity threshold tuning

**Priority**: High

---

### 2. Document Understanding Enhancement

**Current State**:
- Basic alignment analysis
- Single document focus

**Needed Enhancements**:
- [ ] Multi-document relationship analysis
- [ ] Document hierarchy understanding
- [ ] Cross-reference resolution
- [ ] Temporal relevance scoring
- [ ] Content quality assessment

**Priority**: High

---

### 3. KB-Aware Question Generation

**Current State**:
- Questions generated independently
- KB used for context only

**Needed Enhancements**:
- [ ] KB chunks directly inform question topics
- [ ] Missing spec identification from KB
- [ ] Document-specific question generation
- [ ] Progressive KB exploration
- [ ] Gap-driven question prioritization

**Priority**: Critical

---

### 4. Multi-Document Analysis

**Current State**:
- Single document handling
- No cross-document relationship

**Needed Enhancements**:
- [ ] Document correlation analysis
- [ ] Conflict detection across documents
- [ ] Information synthesis
- [ ] Document priority ranking
- [ ] Comprehensive coverage verification

**Priority**: High

---

### 5. Context Relevance Scoring

**Current State**:
- Basic relevance via similarity
- No contextual weighting

**Needed Enhancements**:
- [ ] Context-aware relevance weighting
- [ ] Phase-specific relevance scoring
- [ ] User-role-based filtering
- [ ] Temporal relevance decay
- [ ] Popularity-based ranking

**Priority**: Medium

---

## Phase 5 Goals

### Primary Objectives
1. ✅ Enhance vector database query efficiency
2. ✅ Improve document understanding capabilities
3. ✅ Integrate KB into question generation logic
4. ✅ Implement multi-document analysis
5. ✅ Add context-aware relevance scoring

### Success Metrics
- [ ] KB-driven questions generated (vs generic)
- [ ] Multi-document analysis working
- [ ] Relevance scores > 0.85 average
- [ ] Question coverage of documents > 80%
- [ ] User satisfaction with KB integration

---

## Implementation Approach

### Strategy 1: Incremental Enhancement (Recommended)
- **Phases**: 3 sub-phases
- **Duration**: 2 weeks
- **Risk**: Low
- **Complexity**: Medium

### Strategy 2: Complete Rewrite
- **Phases**: 1 big phase
- **Duration**: 3 weeks
- **Risk**: High
- **Complexity**: High

**Recommendation**: Strategy 1 (Incremental)

---

## Proposed Implementation Timeline

### Phase 5a: Vector Database & Document Understanding (Days 1-5)
- [ ] Enhance ChromaDB query optimization
- [ ] Improve document understanding algorithm
- [ ] Add multi-document relationship analysis
- [ ] Implement content quality scoring

### Phase 5b: KB-Aware Question Generation (Days 6-10)
- [ ] Identify gaps from KB documents
- [ ] Generate questions based on KB chunks
- [ ] Implement progressive KB exploration
- [ ] Add gap-driven prioritization

### Phase 5c: Context Relevance & Polish (Days 11-14)
- [ ] Implement context-aware scoring
- [ ] Add relevance weighting
- [ ] Performance optimization
- [ ] Documentation & testing

---

## Key Files to Modify

| File | Purpose | Changes |
|------|---------|---------|
| `orchestrator.py` | KB strategy & context | Enhance KB integration in question generation |
| `knowledge.py` | KB API endpoints | Add advanced search & analysis endpoints |
| `models_local.py` | Vector DB manager | Optimize vector operations |
| `projects_chat.py` | Chat endpoints | Use KB context in responses |
| (New) `knowledge_service.py` | KB service layer | Centralize KB operations |

---

## Dependencies & Prerequisites

### Required Libraries
- ✅ chromadb (existing)
- ✅ langchain (likely existing)
- ⏳ sentence-transformers (may need to install)
- ⏳ numpy (for vector operations)

### Existing Infrastructure
- ✅ Orchestrator with context gathering
- ✅ Document storage
- ✅ Vector database
- ✅ API endpoints

---

## Estimated Effort

| Component | Effort | Hours |
|-----------|--------|-------|
| Vector DB optimization | High | 8 |
| Document understanding | High | 10 |
| KB-aware question gen | Critical | 15 |
| Multi-document analysis | High | 10 |
| Context relevance scoring | Medium | 8 |
| Testing & optimization | Medium | 8 |
| Documentation | Low | 4 |
| **Total** | | **63 hours** |

---

## Risk Assessment

### High Risk Areas
- ⚠️ Changing question generation logic (must not break existing)
- ⚠️ Vector DB performance (need careful optimization)
- ⚠️ Multi-document complexity (combinatorial explosion)

### Mitigation Strategies
- ✅ Incremental approach (test each phase)
- ✅ Feature flags (can enable/disable features)
- ✅ Comprehensive testing
- ✅ Performance monitoring

---

## Next Steps

1. **Finalize Phase 5 Plan** - Get approval on approach
2. **Create Knowledge Service Layer** - Centralize KB operations
3. **Enhance Vector DB** - Optimize queries
4. **Improve Document Understanding** - Better analysis
5. **Integrate KB into Question Generation** - Make questions KB-aware
6. **Testing & Optimization** - Ensure performance
7. **Documentation** - Comprehensive guides

---

## Success Criteria

Phase 5 will be considered complete when:
- ✅ KB information directly influences question generation
- ✅ Multi-document analysis working
- ✅ Relevance scores averaged > 0.85
- ✅ All tests passing
- ✅ Documentation complete
- ✅ Performance optimized (no N+1 queries)

---

## Ready to Proceed?

**Current Status**: Investigation Complete ✅

**Recommended Action**:
1. Approve Phase 5 plan
2. Create detailed sub-phase specifications
3. Begin Phase 5a implementation

**Effort Required**: 63 hours (2 weeks)

