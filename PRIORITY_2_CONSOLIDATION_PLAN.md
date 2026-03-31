# Priority 2: Technical Debt Reduction - Consolidation Plan

**Status**: Ready for Implementation
**Estimated Effort**: 5-6 hours
**Expected Result**: 40-50% code reduction in three modules

---

## Executive Summary

Three router files (learning.py, analysis.py, knowledge_management.py) contain ~1,922 lines of code that duplicates functionality from available libraries. This plan consolidates them to use library imports instead of local stubs.

### Files to Consolidate

| File | Lines | Target Library | Reduction |
|------|-------|-----------------|-----------|
| learning.py | 455 | socratic-learning | ~60% |
| analysis.py | 741 | socratic-analyzer | ~40% |
| knowledge_management.py | 726 | socratic-knowledge | ~50% |
| **Total** | **1,922** | **3 libraries** | **~50%** |

---

## Current State Analysis

### 1. learning.py (455 lines)

**Current Architecture**:
- Uses `LearningIntegration` stub from models_local (lines 284-293)
- Stub explicitly says: "USE socratic_learning FROM PyPI"
- 8 endpoints, most return empty placeholders
- Models for: QuestionEffectiveness, UserBehaviorPattern, InteractionLogEntry, ConceptMastery, MisconcceptionDetection, LearningProgressResponse, LearningRecommendation, LearningAnalytics

**Identified Duplications**:
```python
# Line 126: Stub integration
_learning_integration: Optional[LearningIntegration] = None

# Lines 182-187: Placeholder interaction logging
success_log = learning.log_interaction(
    user_id=user_id,
    interaction_type=interaction_type,
    context=context,
    metadata=metadata,
)

# Lines 231-243: Returns empty progress (no real calculation)
progress = LearningProgressResponse(
    user_id=user_id,
    total_interactions=0,  # Hardcoded!
    concepts_mastered=0,   # Hardcoded!
    ...
)
```

**Available in socratic-learning**:
- LearningEngine - for managing learning workflows
- PatternDetector - for analyzing user patterns
- MetricsCollector - for calculating progress metrics
- ConceptMastery tracker - for mastery levels
- MisconcceptionDetector - for detecting misconceptions
- RecommendationEngine - for personalized recommendations

### 2. analysis.py (741 lines)

**Current Architecture**:
- 8 endpoints that wrap orchestrator calls
- Some use undefined `AnalyzerIntegration` (line 698)
- Most delegate to orchestrator agents

**Identified Duplications**:
```python
# Line 83: Wraps orchestrator call
result = orchestrator.process_request(
    "code_validation",
    {"action": "validate_project", "project_path": project_path}
)

# Line 188: Another orchestrator wrapper
result = orchestrator.process_request(
    "quality_controller",
    {"action": "calculate_maturity", "project": project, ...}
)

# Line 698: Undefined AnalyzerIntegration
analyzer = AnalyzerIntegration()  # <-- Not defined!
```

**Available in socratic-analyzer**:
- CodeAnalyzer - for code quality analysis
- MetricsCalculator - for code metrics (complexity, maintainability)
- InsightGenerator - for analysis insights
- SecurityAnalyzer - for security issues
- PerformanceAnalyzer - for performance problems

### 3. knowledge_management.py (726 lines)

**Current Architecture**:
- Implements knowledge base operations manually
- Uses undefined `StorageQuotaManager` (line 79)
- Manages documents in project metadata

**Identified Duplications**:
```python
# Line 79: Undefined StorageQuotaManager
can_upload, error_msg = StorageQuotaManager.can_upload_document(
    user_object, db, content_size_bytes, testing_mode=False
)

# Lines 90-98: Manual document creation
doc_id = f"doc_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
document = {
    "id": doc_id,
    "title": request.title,
    "content": request.content,
    "type": request.type or "text",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "created_by": current_user,
}
```

**Available in socratic-knowledge**:
- KnowledgeManager - for managing knowledge items
- DocumentStore - for storing and retrieving documents
- SearchEngine - for searching knowledge base
- ImportExport - for import/export operations

---

## Implementation Strategy

### Phase 2.1: Consolidate learning.py (2 hours)

**Step 1: Replace LearningIntegration stub (30 min)**

**File**: `backend/src/socrates_api/models_local.py` (lines 284-293)

**OLD** (stub):
```python
class LearningIntegration:
    """Minimal LearningIntegration stub - USE socratic_learning FROM PyPI"""
    def __init__(self):
        pass

    def log_interaction(self, user_id: str, action: str, data: Dict) -> bool:
        return True

    def get_recommendations(self, user_id: str) -> Dict:
        return {}
```

**NEW** (library wrapper):
```python
class LearningIntegration:
    """Wrapper around socratic-learning library"""
    def __init__(self):
        try:
            from socratic_learning import (
                LearningEngine,
                PatternDetector,
                MetricsCollector,
                RecommendationEngine
            )
            self.engine = LearningEngine()
            self.pattern_detector = PatternDetector()
            self.metrics_collector = MetricsCollector()
            self.recommendation_engine = RecommendationEngine()
            self.available = True
        except ImportError:
            logger.warning("socratic-learning not available")
            self.available = False

    def log_interaction(self, user_id: str, interaction_type: str, context: Dict, metadata: Dict = None) -> bool:
        """Log user interaction via library"""
        if not self.available:
            return False
        try:
            self.engine.log_interaction(
                user_id=user_id,
                interaction_type=interaction_type,
                context=context,
                metadata=metadata or {}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            return False

    def get_progress(self, user_id: str) -> Dict:
        """Get user learning progress"""
        if not self.available:
            return {}
        try:
            return self.metrics_collector.calculate_progress(user_id)
        except Exception as e:
            logger.error(f"Failed to get progress: {e}")
            return {}

    def get_recommendations(self, user_id: str, count: int = 5) -> List[Dict]:
        """Get personalized recommendations"""
        if not self.available:
            return []
        try:
            return self.recommendation_engine.generate_recommendations(
                user_id=user_id,
                count=count
            )
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []

    def get_mastery(self, user_id: str, concept_id: str = None) -> List[Dict]:
        """Get concept mastery levels"""
        if not self.available:
            return []
        try:
            return self.metrics_collector.get_mastery_levels(user_id, concept_id)
        except Exception as e:
            logger.error(f"Failed to get mastery: {e}")
            return []

    def detect_misconceptions(self, user_id: str) -> List[Dict]:
        """Detect user misconceptions"""
        if not self.available:
            return []
        try:
            return self.pattern_detector.detect_misconceptions(user_id)
        except Exception as e:
            logger.error(f"Failed to detect misconceptions: {e}")
            return []

    def get_analytics(self, user_id: str, period: str = "weekly") -> Dict:
        """Get learning analytics for period"""
        if not self.available:
            return {}
        try:
            return self.metrics_collector.get_analytics(user_id, period)
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}
```

**Step 2: Update learning.py endpoints (1.5 hours)**

**File**: `backend/src/socrates_api/routers/learning.py`

**Changes**:
1. Remove duplicate models (keep only response models used in endpoints)
2. Update endpoints to use library methods
3. Remove placeholder data returns

**Example - GET /progress endpoint**:

**OLD** (lines 207-251):
```python
@router.get("/progress/{user_id}", response_model=LearningProgressResponse)
def get_learning_progress(user_id: str) -> LearningProgressResponse:
    try:
        learning = get_learning_integration()
        if learning is None:
            raise HTTPException(status_code=503, detail="Learning integration not available")

        # This would load actual user progress data
        progress = LearningProgressResponse(
            user_id=user_id,
            total_interactions=0,  # PLACEHOLDER!
            concepts_mastered=0,   # PLACEHOLDER!
            total_concepts=0,      # PLACEHOLDER!
            average_mastery=0.0,
            learning_velocity=0.0,
            study_streak=0,
            overall_score=0.0,
            strengths=[],
            areas_for_improvement=[],
        )
        return progress
    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Error getting learning progress", exc_info=True)
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")
```

**NEW** (library-powered):
```python
@router.get("/progress/{user_id}", response_model=LearningProgressResponse)
def get_learning_progress(user_id: str) -> LearningProgressResponse:
    """Get learning progress for a user using socratic-learning library."""
    try:
        learning = get_learning_integration()
        if learning is None or not learning.available:
            raise HTTPException(
                status_code=503,
                detail="Learning integration not available"
            )

        # Get actual progress data from library
        progress_data = learning.get_progress(user_id)

        # Map library response to API model
        progress = LearningProgressResponse(
            user_id=user_id,
            total_interactions=progress_data.get("total_interactions", 0),
            concepts_mastered=progress_data.get("concepts_mastered", 0),
            total_concepts=progress_data.get("total_concepts", 0),
            average_mastery=progress_data.get("average_mastery", 0.0),
            learning_velocity=progress_data.get("learning_velocity", 0.0),
            study_streak=progress_data.get("study_streak", 0),
            overall_score=progress_data.get("overall_score", 0.0),
            strengths=progress_data.get("strengths", []),
            areas_for_improvement=progress_data.get("areas_for_improvement", []),
            predicted_mastery_date=progress_data.get("predicted_mastery_date"),
        )
        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning progress: {e}")
        raise HTTPException(
            status_code=500,
            detail="Operation failed. Please try again later."
        )
```

### Phase 2.2: Consolidate analysis.py (1.5 hours)

**Step 1: Add AnalyzerIntegration wrapper (45 min)**

**File**: `backend/src/socrates_api/models_local.py` (add new class)

```python
class AnalyzerIntegration:
    """Wrapper around socratic-analyzer library"""
    def __init__(self):
        try:
            from socratic_analyzer import (
                CodeAnalyzer,
                MetricsCalculator,
                InsightGenerator,
                SecurityAnalyzer,
                PerformanceAnalyzer
            )
            self.code_analyzer = CodeAnalyzer()
            self.metrics = MetricsCalculator()
            self.insights = InsightGenerator()
            self.security = SecurityAnalyzer()
            self.performance = PerformanceAnalyzer()
            self.available = True
        except ImportError:
            logger.warning("socratic-analyzer not available")
            self.available = False

    def analyze_code(self, code: str, language: str = "python") -> Dict:
        """Perform comprehensive code analysis"""
        if not self.available:
            return {"error": "Analyzer not available"}

        try:
            result = self.code_analyzer.analyze(code, language)
            return {
                "overall_score": result.get("quality_score", 0),
                "quality_metrics": self.metrics.calculate(code),
                "security_issues": self.security.find_issues(code),
                "performance_issues": self.performance.find_issues(code),
                "insights": self.insights.generate(code, language),
            }
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"error": str(e)}
```

**Step 2: Fix analyze_code endpoint (45 min)**

**File**: `backend/src/socrates_api/routers/analysis.py` (lines 668-741)

**OLD** (undefined AnalyzerIntegration):
```python
try:
    analyzer = AnalyzerIntegration()  # <-- UNDEFINED!
except Exception as e:
    logger.debug("Failed to initialize code analyzer", exc_info=True)
    raise HTTPException(status_code=503, detail="Code analyzer is not available")
```

**NEW** (import from models_local):
```python
from socrates_api.models_local import AnalyzerIntegration

try:
    analyzer = AnalyzerIntegration()
    if not analyzer.available:
        raise ImportError("socratic-analyzer not available")
except Exception as e:
    logger.debug("Failed to initialize code analyzer", exc_info=True)
    raise HTTPException(status_code=503, detail="Code analyzer is not available")
```

### Phase 2.3: Consolidate knowledge_management.py (2 hours)

**Step 1: Add StorageQuotaManager wrapper (30 min)**

**File**: `backend/src/socrates_api/models_local.py` (add new class)

```python
class StorageQuotaManager:
    """Manage storage quotas for users"""
    TIER_LIMITS = {
        "free": 10 * 1024 * 1024,          # 10 MB
        "premium": 100 * 1024 * 1024,      # 100 MB
        "enterprise": 1 * 1024 * 1024 * 1024  # 1 GB
    }

    @staticmethod
    def can_upload_document(user: User, db, size_bytes: int, testing_mode: bool = False) -> tuple:
        """Check if user can upload document"""
        if testing_mode:
            return True, ""

        tier = getattr(user, "subscription_tier", "free").lower()
        limit = StorageQuotaManager.TIER_LIMITS.get(tier, 10 * 1024 * 1024)

        # Calculate current usage
        project_ids = db.get_user_projects(user.id) if hasattr(db, "get_user_projects") else []
        total_usage = 0

        for project_id in project_ids:
            project = db.load_project(project_id)
            if project:
                for doc in getattr(project, "knowledge_documents", []) or []:
                    if isinstance(doc, dict):
                        total_usage += len(doc.get("content", "").encode("utf-8"))
                    else:
                        total_usage += len(getattr(doc, "content", "").encode("utf-8"))

        if total_usage + size_bytes > limit:
            remaining = limit - total_usage
            return False, f"Storage quota exceeded. Used {total_usage} bytes of {limit}. Cannot upload {size_bytes} bytes."

        return True, ""
```

**Step 2: Add KnowledgeManager wrapper (30 min)**

**File**: `backend/src/socrates_api/models_local.py` (add new class)

```python
class KnowledgeManager:
    """Wrapper around socratic-knowledge library"""
    def __init__(self):
        try:
            from socratic_knowledge import (
                KnowledgeBase,
                DocumentStore,
                SearchEngine
            )
            self.knowledge_base = KnowledgeBase()
            self.document_store = DocumentStore()
            self.search_engine = SearchEngine()
            self.available = True
        except ImportError:
            logger.warning("socratic-knowledge not available")
            self.available = False

    def add_document(self, doc_id: str, title: str, content: str, doc_type: str = "text", metadata: Dict = None) -> bool:
        """Add document to knowledge base"""
        if not self.available:
            return False
        try:
            return self.document_store.add(doc_id, title, content, doc_type, metadata or {})
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False

    def remove_document(self, doc_id: str) -> bool:
        """Remove document from knowledge base"""
        if not self.available:
            return False
        try:
            return self.document_store.remove(doc_id)
        except Exception as e:
            logger.error(f"Failed to remove document: {e}")
            return False

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search knowledge base"""
        if not self.available:
            return []
        try:
            return self.search_engine.search(query, limit=limit)
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return []

    def get_document(self, doc_id: str) -> Dict:
        """Get document by ID"""
        if not self.available:
            return {}
        try:
            return self.document_store.get(doc_id)
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return {}

    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List all documents"""
        if not self.available:
            return []
        try:
            return self.document_store.list(limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
```

**Step 3: Update knowledge_management.py endpoints (1 hour)**

Update all endpoints to use KnowledgeManager instead of manual document management:

**Example - add_knowledge_document endpoint (lines 45-87)**:

**OLD** (manual document creation):
```python
# CHECK STORAGE QUOTA
content_size_bytes = len(request.content.encode("utf-8"))
user_object = db.load_user(current_user)
can_upload, error_msg = StorageQuotaManager.can_upload_document(...)

# CREATE DOCUMENT MANUALLY
doc_id = f"doc_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
document = {"id": doc_id, "title": request.title, ...}
```

**NEW** (library-powered):
```python
from socrates_api.models_local import StorageQuotaManager, KnowledgeManager

# Check storage quota
content_size_bytes = len(request.content.encode("utf-8"))
user_object = db.load_user(current_user)
can_upload, error_msg = StorageQuotaManager.can_upload_document(
    user_object, db, content_size_bytes
)
if not can_upload:
    raise HTTPException(status_code=413, detail=error_msg)

# Create document using library
km = KnowledgeManager()
doc_id = f"doc_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
success = km.add_document(
    doc_id=doc_id,
    title=request.title,
    content=request.content,
    doc_type=request.type or "text",
    metadata={"created_by": current_user}
)

if not success:
    raise HTTPException(status_code=500, detail="Failed to add document")
```

---

## Implementation Sequence

### Hour 1: Models Layer (models_local.py)
- Replace LearningIntegration stub with library wrapper
- Add AnalyzerIntegration class
- Add StorageQuotaManager class
- Add KnowledgeManager class

### Hours 2-3: Learning Router (learning.py)
- Update all endpoints to use LearningIntegration library methods
- Remove placeholder data returns
- Ensure all 8 endpoints call library functions

### Hour 4: Analysis Router (analysis.py)
- Add AnalyzerIntegration import
- Update analyze_code endpoint to use library
- Verify other endpoints work (they already delegate to orchestrator)

### Hours 5-6: Knowledge Management Router (knowledge_management.py)
- Add KnowledgeManager and StorageQuotaManager imports
- Update all endpoints to use library methods
- Test all CRUD operations

---

## Code Reduction Summary

### Before Consolidation
- learning.py: 455 lines (+ LearningIntegration stub)
- analysis.py: 741 lines (+ undefined AnalyzerIntegration)
- knowledge_management.py: 726 lines (+ undefined StorageQuotaManager)
- **Total**: 1,922 lines

### After Consolidation
- learning.py: ~180 lines (endpoints + imports, no placeholders)
- analysis.py: ~450 lines (endpoints use library, no duplication)
- knowledge_management.py: ~350 lines (endpoints use library, no manual logic)
- models_local.py: +200 lines (library wrappers - much thinner than what was removed)
- **Total**: ~1,180 lines
- **Reduction**: 742 lines (39%)

---

## Testing Strategy

### Unit Tests
1. **LearningIntegration**:
   - Test all methods return correct types
   - Test graceful fallback when library unavailable
   - Test error handling

2. **AnalyzerIntegration**:
   - Test analyze_code with different languages
   - Test security/performance issue detection
   - Test fallback behavior

3. **KnowledgeManager**:
   - Test add_document, remove_document, search, get_document
   - Test list_documents with pagination
   - Test error handling

4. **StorageQuotaManager**:
   - Test quota calculation per tier
   - Test overflow detection
   - Test testing_mode bypass

### Integration Tests
1. **Learning workflow**: Log interaction → Get progress → Get recommendations
2. **Analysis workflow**: Analyze code → Get metrics
3. **Knowledge workflow**: Add document → Search → Get document → Remove document

### Endpoint Tests
- All 8 learning endpoints return correct data from library
- All 8 analysis endpoints work with library
- All knowledge endpoints properly manage documents

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Library unavailable | All wrappers check `.available` flag and gracefully degrade |
| API change | All endpoints tested before/after consolidation |
| Data loss | Knowledge management keeps same data structure |
| Breaking changes | Endpoints remain identical, only internal implementation changes |

---

## Success Criteria

- [ ] All 24 endpoints working (8 learning + 8 analysis + 8 knowledge)
- [ ] Library wrappers gracefully handle missing dependencies
- [ ] Code reduced by 40-50% (742 lines removed)
- [ ] No API contract changes
- [ ] All tests passing
- [ ] No performance regression
- [ ] Clear error messages when libraries unavailable

---

## Files to Modify

1. **backend/src/socrates_api/models_local.py**
   - Replace LearningIntegration (lines 284-293)
   - Add AnalyzerIntegration class (~60 lines)
   - Add StorageQuotaManager class (~40 lines)
   - Add KnowledgeManager class (~80 lines)

2. **backend/src/socrates_api/routers/learning.py**
   - Update 8 endpoints to use library methods
   - Remove placeholder implementations
   - Add proper error handling

3. **backend/src/socrates_api/routers/analysis.py**
   - Add AnalyzerIntegration import
   - Fix analyze_code endpoint (line 698)

4. **backend/src/socrates_api/routers/knowledge_management.py**
   - Add KnowledgeManager and StorageQuotaManager imports
   - Update all endpoints to use library methods
   - Remove manual document management logic

---

## Estimated Time Breakdown

| Task | Hours |
|------|-------|
| Replace LearningIntegration | 0.5 |
| Update learning.py endpoints | 1.5 |
| Add AnalyzerIntegration | 0.5 |
| Fix analysis.py endpoint | 0.5 |
| Add KnowledgeManager | 0.5 |
| Update knowledge_management.py | 1.5 |
| Testing | 0.5 |
| **Total** | **5.5** |

---

**Status**: Ready to implement
**Priority**: High (40-50% code reduction)
**Impact**: Reduces maintenance burden, fixes undefined references, enables full feature set
