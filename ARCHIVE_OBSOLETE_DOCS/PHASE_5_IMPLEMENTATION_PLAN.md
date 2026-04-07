# Phase 5 Implementation Plan - Knowledge Base Integration

## Overview

Phase 5 implements comprehensive Knowledge Base integration to make question generation intelligent, context-aware, and document-driven. The system will understand documents, extract relevant information, identify gaps, and use this intelligence to generate focused, KB-informed questions.

---

## Architecture

```
User uploads Documents
    ↓
Vector Database (ChromaDB)
    ├─ Store embeddings
    ├─ Index documents
    └─ Enable semantic search
    ↓
Document Understanding Service
    ├─ Analyze relationships
    ├─ Extract key concepts
    ├─ Identify gaps
    └─ Score relevance
    ↓
KB-Aware Question Generator
    ├─ Use document gaps
    ├─ Reference KB chunks
    ├─ Generate focused questions
    └─ Track coverage
    ↓
User Answers Questions
    ├─ Extracts specifications
    ├─ Updates document relevance
    └─ Identifies new gaps
```

---

## Phase 5a: Vector Database & Document Understanding (Days 1-5)

### Task 1: Create Knowledge Service Layer

**File**: `socrates_api/services/knowledge_service.py` (NEW)

**Purpose**: Centralize all KB operations

**Key Classes**:
```python
class KnowledgeService:
    """Service for knowledge base operations"""

    def __init__(self, vector_db, document_repo):
        self.vector_db = vector_db
        self.docs = document_repo

    def search_documents(
        self,
        query: str,
        project_id: str,
        top_k: int = 5,
        relevance_threshold: float = 0.7
    ) -> List[DocumentResult]:
        """
        Search documents with relevance filtering.

        Returns:
        - Documents ranked by relevance
        - Similarity scores
        - Metadata
        """

    def get_document_chunks(
        self,
        document_id: str,
        chunk_size: int = 500,
        overlap: int = 100
    ) -> List[DocumentChunk]:
        """Split document into overlapping chunks"""

    def analyze_document_relationships(
        self,
        documents: List[Document],
        project_id: str
    ) -> DocumentRelationshipMap:
        """
        Analyze relationships between documents.

        Returns:
        - Cross-references
        - Conflicts
        - Complementary documents
        - Coverage gaps
        """
```

**Effort**: 8 hours

---

### Task 2: Enhance Vector Database Operations

**File**: `socrates_api/services/knowledge_service.py`

**Enhancements**:
```python
class VectorDBService:
    """Optimized vector database operations"""

    def hybrid_search(
        self,
        query: str,
        documents: List[Document],
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[DocumentChunk]:
        """
        Hybrid search combining:
        - Semantic similarity (vector search)
        - Keyword matching (BM25)
        - Combined ranking
        """

    def get_optimal_chunks(
        self,
        query: str,
        project_id: str,
        phase: str,
        question_number: int
    ) -> List[DocumentChunk]:
        """
        Get KB chunks optimized for current context.

        Uses:
        - Phase-specific strategy (snippet vs full)
        - Relevance scoring
        - Coverage gaps
        - User role filtering
        """

    def calculate_relevance_score(
        self,
        query: str,
        document: Document,
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score (0-1) with context weighting.

        Factors:
        - Semantic similarity
        - Keyword match
        - Phase relevance
        - User role match
        - Document quality
        """
```

**Effort**: 10 hours

---

### Task 3: Improve Document Understanding

**File**: `socrates_api/services/knowledge_service.py`

**New Capabilities**:
```python
class DocumentUnderstandingService:
    """Advanced document understanding"""

    def extract_concepts(
        self,
        document: Document
    ) -> List[Concept]:
        """
        Extract key concepts from document.

        Returns:
        - Technical terms
        - Business concepts
        - Requirements
        - Constraints
        """

    def identify_gaps(
        self,
        documents: List[Document],
        project_specs: Dict[str, Any]
    ) -> List[SpecificationGap]:
        """
        Identify specification gaps not covered by documents.

        Returns:
        - Missing topics
        - Underspecified areas
        - Conflicting information
        - Unclear sections
        """

    def analyze_relationships(
        self,
        documents: List[Document]
    ) -> DocumentRelationshipGraph:
        """
        Build relationship graph between documents.

        Returns:
        - Cross-references
        - Dependencies
        - Conflicts
        - Overlaps
        - Hierarchy
        """

    def score_document_quality(
        self,
        document: Document
    ) -> QualityScore:
        """
        Score document quality (0-100).

        Factors:
        - Completeness
        - Clarity
        - Consistency
        - Relevance
        - Recency
        """
```

**Effort**: 12 hours

---

## Phase 5b: KB-Aware Question Generation (Days 6-10)

### Task 4: Integrate KB into Question Generation

**File**: `orchestrator.py`

**Enhancement**: `_orchestrate_question_generation()`

**New Logic**:
```python
def _orchestrate_question_generation(self, project, user_id, force_refresh=False):
    """
    PHASE 5: Enhanced question generation using KB.

    Process:
    1. Identify gaps from KB documents
    2. Get most relevant KB chunks
    3. Build KB-specific prompt
    4. Generate focused questions
    5. Track KB coverage
    """

    # 1. Identify gaps from KB
    kb_gaps = self._identify_knowledge_gaps(project)

    # 2. Get optimal KB chunks
    kb_chunks = self._get_optimal_kb_chunks(
        project,
        phase=project.phase,
        gaps=kb_gaps,
        question_number=self._get_question_count(project)
    )

    # 3. Build enhanced context with KB
    context = self._gather_question_context(project, user_id)
    context["kb_chunks"] = kb_chunks
    context["kb_gaps"] = kb_gaps
    context["kb_coverage"] = self._calculate_kb_coverage(project)

    # 4. Generate KB-aware question
    result = orchestrator.generate_dynamic_question(context)

    # 5. Track which gaps were addressed
    question = result["question"]
    question["kb_gaps_addressed"] = self._extract_gaps_from_question(question)

    return result
```

**Effort**: 12 hours

---

### Task 5: Implement Gap-Driven Prioritization

**File**: `orchestrator.py`

**New Method**:
```python
def _prioritize_by_kb_gaps(
    self,
    project: ProjectContext,
    potential_questions: List[Dict]
) -> List[Dict]:
    """
    Prioritize questions that address high-value KB gaps.

    Scoring factors:
    - Gap importance (severity)
    - Gap frequency (how often mentioned)
    - Gap impact (affects other specs)
    - Coverage potential (can question address it)

    Returns:
    - Questions ranked by gap-addressing value
    """
```

**Effort**: 8 hours

---

## Phase 5c: Context Relevance & Polish (Days 11-14)

### Task 6: Implement Context-Aware Relevance

**File**: `knowledge_service.py`

**Enhancement**:
```python
def calculate_contextual_relevance(
    self,
    document: Document,
    context: Dict[str, Any]
) -> float:
    """
    Calculate relevance with full context awareness.

    Context factors:
    - Phase (what info is needed)
    - User role (what they care about)
    - Project type (domain-specific)
    - Question history (avoid repeats)
    - Specification gaps (priority areas)

    Returns: 0-1 relevance score
    """
```

**Effort**: 10 hours

---

### Task 7: Testing & Optimization

**What to Test**:
- [ ] Document upload and indexing
- [ ] Vector search accuracy
- [ ] Gap identification
- [ ] Relationship analysis
- [ ] KB-aware question generation
- [ ] Relevance scoring accuracy
- [ ] Multi-document scenarios
- [ ] Performance (query time)
- [ ] Edge cases

**Effort**: 12 hours

---

## API Endpoints (New/Enhanced)

### New Endpoints

#### GET `/projects/{project_id}/knowledge/gaps`
Returns specification gaps not covered by KB.

**Response**:
```json
{
  "gaps": [
    {
      "gap_id": "gap_1",
      "topic": "Security Requirements",
      "severity": "high",
      "mentioned_in_docs": [],
      "priority_score": 0.85,
      "suggestion": "Define authentication and authorization requirements"
    }
  ],
  "total_gaps": 5,
  "coverage_percentage": 72
}
```

#### GET `/projects/{project_id}/knowledge/analysis`
Returns comprehensive KB analysis.

**Response**:
```json
{
  "documents": 8,
  "total_chunks": 245,
  "coverage": {
    "percentage": 72,
    "strong_areas": ["Architecture", "Design"],
    "weak_areas": ["Security", "Testing"],
    "not_covered": ["Deployment", "Monitoring"]
  },
  "relationships": {
    "cross_references": 12,
    "conflicts": 2,
    "complementary_docs": 4
  },
  "quality_score": 0.78
}
```

#### POST `/projects/{project_id}/knowledge/find-gaps`
Identify specific gaps for a specification type.

**Request**:
```json
{
  "spec_type": "security",
  "context": "authentication"
}
```

**Response**:
```json
{
  "gaps": [...],
  "questions_to_ask": [
    "What authentication mechanisms will you use?",
    "How will sessions be managed?",
    "What encryption standards apply?"
  ]
}
```

---

## Data Structures

### DocumentChunk
```python
{
    "chunk_id": "chunk_1",
    "document_id": "doc_1",
    "content": "...",
    "section": "Architecture",
    "position": 0,
    "embedding": [...],  # Vector
    "metadata": {
        "relevance_score": 0.92,
        "quality": 0.85,
        "concepts": ["API", "REST"],
        "related_specs": ["req_1", "req_2"]
    }
}
```

### SpecificationGap
```python
{
    "gap_id": "gap_1",
    "category": "security",
    "topic": "Authentication",
    "severity": "high",  # critical, high, medium, low
    "priority_score": 0.85,
    "mentioned_documents": [],
    "impact_on_specs": ["spec_1", "spec_3"],
    "suggested_question": "What authentication...",
    "related_chunks": []
}
```

### DocumentRelationshipGraph
```python
{
    "documents": [...],
    "edges": [
        {
            "source": "doc_1",
            "target": "doc_2",
            "relationship_type": "cross_reference",
            "strength": 0.8
        }
    ],
    "conflicts": [...],
    "clusters": [...]  # Document groupings
}
```

---

## Integration Points

### With Phase 2 (Orchestration)
- KB context added to `_gather_question_context()`
- KB chunks included in question generation
- Gap information influences question topic

### With Phase 3 (Conflict Resolution)
- Document conflicts detected and tracked
- KB used to resolve spec conflicts
- Document relationship analysis helps conflict resolution

### With Phase 4 (Phase Advancement)
- KB coverage used in maturity calculation
- Document completion influences phase readiness
- Gap closure tracked as progress metric

---

## Success Metrics

### Primary Metrics
- [ ] KB-informed questions: > 80% of questions reference KB
- [ ] Relevance score: Average > 0.85
- [ ] Gap identification: > 90% accuracy
- [ ] Multi-document support: Working with 10+ documents
- [ ] Query performance: < 500ms for chunk retrieval

### Secondary Metrics
- [ ] Document relationship detection: > 80% accuracy
- [ ] Quality scoring: Correlation with user ratings > 0.75
- [ ] Coverage tracking: Accurate to within 5%
- [ ] Test coverage: > 85%

---

## Timeline

```
Phase 5a (Foundations)
Days 1-5
├─ Days 1-2: Knowledge Service Layer
├─ Days 2-4: Vector DB Enhancement
└─ Days 4-5: Document Understanding

Phase 5b (Integration)
Days 6-10
├─ Days 6-8: KB-Aware Question Gen
└─ Days 8-10: Gap Prioritization

Phase 5c (Polish)
Days 11-14
├─ Days 11-12: Context Relevance
├─ Days 13: Testing & Optimization
└─ Day 14: Documentation & Cleanup
```

---

## Rollback Strategy

If Phase 5 causes issues:
1. **Feature Flag**: KB-awareness can be disabled
2. **Fallback Logic**: Falls back to Phase 4 questions
3. **Gradual Rollout**: Enable for 10% → 50% → 100% of users
4. **Performance Revert**: If vector DB too slow, revert to simple search

---

## Ready to Proceed?

Phase 5 is ready to begin when:
- ✅ Investigation complete
- ✅ Plan approved
- ✅ All prerequisites met
- ✅ Team ready to implement

**Estimated Effort**: 63 hours
**Estimated Duration**: 2 weeks
**Current Status**: READY TO START

