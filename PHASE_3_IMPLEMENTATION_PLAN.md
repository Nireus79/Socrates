# Phase 3: Event-Driven Background Processing - Implementation Plan

## Overview

Phase 3 eliminates blocking orchestrator calls by implementing event-driven background processing. This is critical for:
- Reducing SocraticCounselor response latency from ~6s to ~100ms
- Enabling horizontal scaling
- Improving user experience (non-blocking)

**Key Constraint:** Must preserve circular import patterns (lazy-loading, service locator, TYPE_CHECKING, events).

---

## 1. Architecture Principles

### 1.1 Preserve Existing Patterns

**DO NOT BREAK:**
```python
# Pattern 1: Lazy-loading (orchestrator.py)
@property
def socratic_counselor(self):
    if "socratic_counselor" not in self._agents_cache:
        from socratic_system.agents import SocraticCounselorAgent
        self._agents_cache["socratic_counselor"] = SocraticCounselorAgent(self)
    return self._agents_cache["socratic_counselor"]

# Pattern 2: String-based routing (safe_orchestrator_call)
safe_orchestrator_call(orchestrator, "quality_controller", request)

# Pattern 3: TYPE_CHECKING imports
if TYPE_CHECKING:
    from socratic_system.orchestration import AgentOrchestrator

# Pattern 4: Event-driven decoupling
event_emitter.on(EventType.DOCUMENT_IMPORTED, callback)
```

### 1.2 Phase 3 Additions

Build ON TOP of existing patterns:

```python
# 1. Emit events after processing
event_emitter.emit("response.analyzed", {
    "project_id": project_id,
    "timestamp": now(),
    "results": {...}
})

# 2. Background listeners react to events
@event_emitter.on("response.analyzed")
async def background_quality_calculation(data):
    # Non-blocking background work
    pass

# 3. Result caching
cache.set(f"analysis:{project_id}", results, ttl=3600)

# 4. Polling endpoints (in REST API)
GET /projects/{id}/analysis  # Returns cached results
```

---

## 2. Component Design

### 2.1 Result Cache Layer

**File:** `socratic_system/caching/analysis_cache.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import time

class AnalysisCache(ABC):
    """Base class for analysis result caching"""

    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def set(self, key: str, value: Dict[str, Any], ttl: int = 3600):
        pass

    @abstractmethod
    def delete(self, key: str):
        pass

    @abstractmethod
    def clear_expired(self):
        pass


class InMemoryAnalysisCache(AnalysisCache):
    """In-memory cache with TTL support"""

    def __init__(self):
        self._cache = {}  # {key: (value, expiry_time)}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Dict[str, Any], ttl: int = 3600):
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)

    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]

    def clear_expired(self):
        current_time = time.time()
        expired = [k for k, (_, exp) in self._cache.items() if exp < current_time]
        for k in expired:
            del self._cache[k]
```

### 2.2 Background Job Tracking

**File:** `socratic_system/jobs/job_tracker.py`

```python
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class JobResult:
    """Represents async job result"""
    job_id: str
    project_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = field(default=0.0)  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "progress": self.progress
        }


class JobTracker:
    """Track status of background jobs"""

    def __init__(self):
        self._jobs: Dict[str, JobResult] = {}

    def create_job(self, job_id: str, project_id: str) -> JobResult:
        """Create new job"""
        job = JobResult(
            
            job_id=job_id,
            project_id=project_id,
            status=JobStatus.PENDING,
            created_at=datetime.now()
        )
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[JobResult]:
        """Get job by ID"""
        return self._jobs.get(job_id)

    def mark_processing(self, job_id: str):
        """Mark job as processing"""
        if job := self._jobs.get(job_id):
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.now()

    def mark_completed(self, job_id: str, result: Dict[str, Any]):
        """Mark job as completed with result"""
        if job := self._jobs.get(job_id):
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result = result
            job.progress = 1.0

    def mark_failed(self, job_id: str, error: str):
        """Mark job as failed"""
        if job := self._jobs.get(job_id):
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            job.error = error

    def update_progress(self, job_id: str, progress: float):
        """Update job progress (0.0 to 1.0)"""
        if job := self._jobs.get(job_id):
            job.progress = min(1.0, max(0.0, progress))
```

### 2.3 Background Event Handlers

**File:** `socratic_system/handlers/background_handlers.py`

```python
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from socratic_system.events import EventType
from socratic_system.jobs import JobTracker
from socratic_system.caching import AnalysisCache

logger = logging.getLogger(__name__)

class BackgroundHandlers:
    """Background event handlers for async processing"""

    def __init__(
        self,
        orchestrator,
        cache: AnalysisCache,
        job_tracker: JobTracker
    ):
        self.orchestrator = orchestrator
        self.cache = cache
        self.job_tracker = job_tracker
        self._register_handlers()

    def _register_handlers(self):
        """Register all background event handlers"""
        self.orchestrator.event_emitter.on(
            "response.received",
            self._on_response_received
        )
        self.orchestrator.event_emitter.on(
            "quality.analysis.requested",
            self._on_quality_analysis_requested
        )
        self.orchestrator.event_emitter.on(
            "conflict.analysis.requested",
            self._on_conflict_analysis_requested
        )

    async def _on_response_received(self, data: Dict[str, Any]):
        """Background processing when response is received"""
        project_id = data.get("project_id")

        logger.info(f"Background: Processing response for project {project_id}")

        # Schedule background tasks (don't wait)
        asyncio.create_task(self._process_quality_async(project_id))
        asyncio.create_task(self._process_conflicts_async(project_id))
        asyncio.create_task(self._process_insights_async(project_id))

    async def _on_quality_analysis_requested(self, data: Dict[str, Any]):
        """Background quality analysis"""
        await self._process_quality_async(data.get("project_id"))

    async def _on_conflict_analysis_requested(self, data: Dict[str, Any]):
        """Background conflict analysis"""
        await self._process_conflicts_async(data.get("project_id"))

    async def _process_quality_async(self, project_id: str):
        """Non-blocking quality calculation"""
        try:
            project = self.orchestrator.database.load_project(project_id)
            if not project:
                return

            # Call quality service (async)
            quality_result = await asyncio.to_thread(
                self.orchestrator.quality_controller.process,
                {
                    "action": "get_phase_maturity",
                    "project": project
                }
            )

            # Cache result
            cache_key = f"analysis:quality:{project_id}"
            self.cache.set(cache_key, quality_result)

            # Emit completion event
            self.orchestrator.event_emitter.emit(
                "quality.analysis.completed",
                {
                    "project_id": project_id,
                    "result": quality_result,
                    "timestamp": datetime.now().isoformat()
                }
            )

            logger.info(f"Background: Quality analysis completed for {project_id}")

        except Exception as e:
            logger.error(f"Background: Quality analysis failed for {project_id}: {e}")
            self.orchestrator.event_emitter.emit(
                "quality.analysis.failed",
                {"project_id": project_id, "error": str(e)}
            )

    async def _process_conflicts_async(self, project_id: str):
        """Non-blocking conflict detection"""
        try:
            project = self.orchestrator.database.load_project(project_id)
            if not project:
                return

            # Call conflict service (async)
            conflicts_result = await asyncio.to_thread(
                self.orchestrator.conflict_detector.process,
                {
                    "action": "detect_conflicts",
                    "project": project
                }
            )

            # Cache result
            cache_key = f"analysis:conflicts:{project_id}"
            self.cache.set(cache_key, conflicts_result)

            # Emit completion event
            self.orchestrator.event_emitter.emit(
                "conflict.analysis.completed",
                {
                    "project_id": project_id,
                    "result": conflicts_result,
                    "timestamp": datetime.now().isoformat()
                }
            )

            logger.info(f"Background: Conflict analysis completed for {project_id}")

        except Exception as e:
            logger.error(f"Background: Conflict analysis failed for {project_id}: {e}")
            self.orchestrator.event_emitter.emit(
                "conflict.analysis.failed",
                {"project_id": project_id, "error": str(e)}
            )

    async def _process_insights_async(self, project_id: str):
        """Non-blocking insight extraction"""
        try:
            project = self.orchestrator.database.load_project(project_id)
            if not project:
                return

            # Call insight service (async)
            insights_result = await asyncio.to_thread(
                self.orchestrator.context_analyzer.process,
                {
                    "action": "analyze_insights",
                    "project": project
                }
            )

            # Cache result
            cache_key = f"analysis:insights:{project_id}"
            self.cache.set(cache_key, insights_result)

            # Emit completion event
            self.orchestrator.event_emitter.emit(
                "insights.analysis.completed",
                {
                    "project_id": project_id,
                    "result": insights_result,
                    "timestamp": datetime.now().isoformat()
                }
            )

            logger.info(f"Background: Insight analysis completed for {project_id}")

        except Exception as e:
            logger.error(f"Background: Insight analysis failed for {project_id}: {e}")
            self.orchestrator.event_emitter.emit(
                "insights.analysis.failed",
                {"project_id": project_id, "error": str(e)}
            )
```

### 2.4 Refactored SocraticCounselor (Non-Blocking)

**File:** `socratic_system/agents/socratic_counselor.py` (refactored)

```python
# In process_response method - CHANGE FROM BLOCKING TO NON-BLOCKING

async def _process_response_async(self, response: str, project: ProjectContext) -> Dict[str, Any]:
    """Process response asynchronously (non-blocking)

    OLD: Wait for quality/conflict/insight analysis (~6s)
    NEW: Return immediately, emit events for background processing (~100ms)
    """
    try:
        # 1. IMMEDIATE: Save response
        updated_project = await asyncio.to_thread(
            self.orchestrator.database.save_user_response,
            project.project_id,
            response
        )

        # 2. IMMEDIATE: Store in conversation history
        updated_project.conversation_history.append({
            "role": "user",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })

        # 3. EMIT EVENTS FOR BACKGROUND PROCESSING (non-blocking)
        self.orchestrator.event_emitter.emit(
            "response.received",
            {
                "project_id": project.project_id,
                "response": response,
                "phase": project.phase,
                "timestamp": datetime.now().isoformat(),
                "user_id": getattr(response, "user_id", None)
            }
        )

        # 4. EMIT SPECIFIC ANALYSIS REQUESTS
        self.orchestrator.event_emitter.emit(
            "quality.analysis.requested",
            {
                "project_id": project.project_id,
                "phase": project.phase
            }
        )

        self.orchestrator.event_emitter.emit(
            "conflict.analysis.requested",
            {
                "project_id": project.project_id,
                "phase": project.phase
            }
        )

        # 5. RETURN IMMEDIATELY (analysis continues in background)
        return {
            "status": "success",
            "message": "Response received. Analysis in progress.",
            "analysis_status": "pending",  # Client knows to poll for results
            "project_id": project.project_id
        }

    except Exception as e:
        self.log(f"Error processing response: {str(e)}", level="ERROR")
        return {
            "status": "error",
            "message": f"Error processing response: {str(e)}"
        }
```

### 2.5 Polling Endpoint (REST API)

**File:** `socrates-api/src/socrates_api/routers/analysis.py` (NEW)

```python
from fastapi import APIRouter, HTTPException
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.jobs import JobStatus

router = APIRouter(prefix="/projects", tags=["analysis"])

@router.get("/{project_id}/analysis")
async def get_analysis(project_id: str):
    """
    Get cached analysis results for a project

    Returns:
    - analysis_ready: bool - whether analysis is complete
    - quality: dict - cached quality analysis (if ready)
    - conflicts: dict - cached conflict analysis (if ready)
    - insights: dict - cached insight analysis (if ready)
    """
    orchestrator = AgentOrchestrator()  # From context

    analysis = {
        "project_id": project_id,
        "analysis_ready": False,
        "quality": None,
        "conflicts": None,
        "insights": None,
        "last_update": None
    }

    # Try to get cached results
    quality = orchestrator.cache.get(f"analysis:quality:{project_id}")
    if quality:
        analysis["quality"] = quality

    conflicts = orchestrator.cache.get(f"analysis:conflicts:{project_id}")
    if conflicts:
        analysis["conflicts"] = conflicts

    insights = orchestrator.cache.get(f"analysis:insights:{project_id}")
    if insights:
        analysis["insights"] = insights

    # Mark as ready if all analyses available
    if quality and conflicts and insights:
        analysis["analysis_ready"] = True

    return analysis


@router.get("/{project_id}/analysis/quality")
async def get_quality_analysis(project_id: str):
    """Get cached quality analysis for a project"""
    orchestrator = AgentOrchestrator()

    result = orchestrator.cache.get(f"analysis:quality:{project_id}")
    if not result:
        raise HTTPException(
            status_code=202,  # Accepted - still processing
            detail="Quality analysis not ready yet"
        )

    return {"project_id": project_id, "quality": result}


@router.get("/{project_id}/analysis/conflicts")
async def get_conflicts_analysis(project_id: str):
    """Get cached conflict analysis for a project"""
    orchestrator = AgentOrchestrator()

    result = orchestrator.cache.get(f"analysis:conflicts:{project_id}")
    if not result:
        raise HTTPException(
            status_code=202,  # Accepted - still processing
            detail="Conflict analysis not ready yet"
        )

    return {"project_id": project_id, "conflicts": result}


@router.get("/{project_id}/analysis/insights")
async def get_insights_analysis(project_id: str):
    """Get cached insight analysis for a project"""
    orchestrator = AgentOrchestrator()

    result = orchestrator.cache.get(f"analysis:insights:{project_id}")
    if not result:
        raise HTTPException(
            status_code=202,  # Accepted - still processing
            detail="Insight analysis not ready yet"
        )

    return {"project_id": project_id, "insights": result}
```

---

## 3. Integration Points

### 3.1 Orchestrator Initialization

**File:** `socratic_system/orchestration/orchestrator.py`

```python
class AgentOrchestrator:
    def __init__(self, config: SocratesConfig = None):
        # ... existing initialization ...

        # Phase 3: Initialize caching and background handlers
        self.cache = InMemoryAnalysisCache()
        self.job_tracker = JobTracker()

        # Register background handlers
        from socratic_system.handlers import BackgroundHandlers
        self.background_handlers = BackgroundHandlers(
            orchestrator=self,
            cache=self.cache,
            job_tracker=self.job_tracker
        )
```

### 3.2 Event Types (Add to existing)

**File:** `socratic_system/events.py`

```python
class EventType(Enum):
    # Existing events...

    # Phase 3: Background processing events
    RESPONSE_RECEIVED = "response.received"
    QUALITY_ANALYSIS_REQUESTED = "quality.analysis.requested"
    QUALITY_ANALYSIS_COMPLETED = "quality.analysis.completed"
    QUALITY_ANALYSIS_FAILED = "quality.analysis.failed"

    CONFLICT_ANALYSIS_REQUESTED = "conflict.analysis.requested"
    CONFLICT_ANALYSIS_COMPLETED = "conflict.analysis.completed"
    CONFLICT_ANALYSIS_FAILED = "conflict.analysis.failed"

    INSIGHTS_ANALYSIS_COMPLETED = "insights.analysis.completed"
    INSIGHTS_ANALYSIS_FAILED = "insights.analysis.failed"
```

---

## 4. Expected Performance Improvements

### Before Phase 3 (Blocking)
```
User sends response
    → SocraticCounselor.process_response()
        → quality_controller.process() [WAIT 2s]
        → conflict_detector.process() [WAIT 1.5s]
        → context_analyzer.process() [WAIT 1.5s]
    → Return response (6s total)
```

### After Phase 3 (Non-Blocking)
```
User sends response
    → SocraticCounselor.process_response()
        → Save response [10ms]
        → Emit events [5ms]
    → Return immediately [15ms total]
        ↓
Background (async):
    → quality_controller.process() [2s, non-blocking]
    → conflict_detector.process() [1.5s, non-blocking]
    → context_analyzer.process() [1.5s, non-blocking]
    → Cache results [10ms]
        ↓
Client polls:
    GET /projects/{id}/analysis → Returns cached results
```

**Latency Reduction:** 6s → 100ms (60x faster user-facing response)

---

## 5. Implementation Checklist

### Phase 3a: Foundation
- [ ] Create `socratic_system/caching/analysis_cache.py` (InMemoryAnalysisCache)
- [ ] Create `socratic_system/jobs/job_tracker.py` (JobTracker, JobResult)
- [ ] Update `socratic_system/events.py` (add Phase 3 event types)
- [ ] Add event types to EventType enum

### Phase 3b: Background Processing
- [ ] Create `socratic_system/handlers/background_handlers.py` (BackgroundHandlers)
- [ ] Register background handlers in Orchestrator.__init__
- [ ] Test background event emission and handling

### Phase 3c: Agent Refactoring
- [ ] Refactor SocraticCounselor._process_response_async() (non-blocking)
- [ ] Change from orchestrator calls to event emission
- [ ] Test response handling latency
- [ ] Verify background analysis executes

### Phase 3d: API Layer
- [ ] Create `socrates-api/src/socrates_api/routers/analysis.py` (polling endpoints)
- [ ] Add GET /projects/{id}/analysis endpoint
- [ ] Add GET /projects/{id}/analysis/{type} endpoints
- [ ] Update API router to include analysis routes

### Phase 3e: Testing & Validation
- [ ] Write tests for InMemoryAnalysisCache
- [ ] Write tests for JobTracker
- [ ] Write tests for BackgroundHandlers
- [ ] Write tests for polling endpoints
- [ ] Load test: parallel response handling
- [ ] Latency test: measure response time improvement

### Phase 3f: Documentation
- [ ] Update architecture docs with Phase 3 flow
- [ ] Document polling pattern for clients
- [ ] Add examples for async analysis retrieval
- [ ] Document event types and flow

---

## 6. Testing Strategy

### Unit Tests
```python
# socratic_system/caching/test_analysis_cache.py
def test_cache_set_and_get()
def test_cache_ttl_expiration()
def test_cache_delete()

# socratic_system/jobs/test_job_tracker.py
def test_create_job()
def test_update_job_status()
def test_get_job_by_id()
def test_job_progress_tracking()

# socratic_system/handlers/test_background_handlers.py
def test_on_response_received_emits_events()
def test_background_quality_analysis()
def test_background_conflict_analysis()
def test_background_insights_analysis()
def test_error_handling_in_background_tasks()
```

### Integration Tests
```python
# tests/test_phase3_non_blocking.py
@pytest.mark.asyncio
async def test_socratic_counselor_returns_immediately():
    """Verify SocraticCounselor returns <100ms"""

@pytest.mark.asyncio
async def test_background_analysis_completes_and_caches():
    """Verify background tasks complete and cache results"""

@pytest.mark.asyncio
async def test_polling_endpoint_returns_cached_results():
    """Verify clients can poll for results"""
```

### Load Tests
```python
# tests/test_phase3_performance.py
def test_concurrent_responses_handled():
    """Verify 100 concurrent responses don't block"""

def test_analysis_latency_improvement():
    """Measure latency: 6s → <100ms"""
```

---

## 7. Backward Compatibility

Phase 3 maintains backward compatibility:

```python
# OLD CODE STILL WORKS (blocking)
quality = orchestrator.quality_controller.process(request)

# NEW CODE WORKS (non-blocking with polling)
response = orchestrator.socratic_counselor.process_response(response)
# ... later ...
analysis = get("/projects/{id}/analysis")
```

---

## 8. Key Files to Create/Modify

### Create (NEW)
- `socratic_system/caching/analysis_cache.py`
- `socratic_system/caching/__init__.py`
- `socratic_system/jobs/job_tracker.py`
- `socratic_system/jobs/__init__.py`
- `socratic_system/handlers/background_handlers.py`
- `socratic_system/handlers/__init__.py`
- `socrates-api/src/socrates_api/routers/analysis.py`

### Modify
- `socratic_system/orchestration/orchestrator.py` (add cache, job_tracker, background_handlers)
- `socratic_system/events.py` (add Phase 3 event types)
- `socratic_system/agents/socratic_counselor.py` (non-blocking response processing)
- `socrates-api/src/socrates_api/main.py` (include analysis router)

---

## 9. Risks & Mitigations

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| **Cache memory overflow** | Medium | Implement cache size limits, LRU eviction |
| **Event ordering issues** | Medium | Use timestamps, idempotent handlers |
| **Race conditions** | Low | Use locks for shared state (cache, tracker) |
| **Background task failures** | Medium | Log errors, emit failed events, client retries |
| **Polling latency** | Low | Cache results, use WebSockets for real-time |

---

## 10. Success Criteria

✅ Phase 3 is successful when:

1. **Latency:** SocraticCounselor response < 100ms
2. **Background:** Quality/conflict/insight analysis completes in parallel
3. **Caching:** Results cached and retrievable via polling endpoints
4. **Events:** All background processing driven by events
5. **Tests:** 100% pass rate on Phase 3 tests
6. **Compatibility:** Existing code still works (backward compatible)
7. **Circular imports:** No new circular import issues introduced
