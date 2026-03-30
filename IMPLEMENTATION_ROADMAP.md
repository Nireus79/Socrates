# SOCRATES IMPLEMENTATION ROADMAP
**Target**: Restore core dialogue functionality
**Strategy**: Fix Tier 1 critical issues first, then implement missing features
**Debug Mode**: OPTION B - Inline Annotations

---

## ROADMAP OVERVIEW

```
PHASE 1: UNBLOCK SYSTEM (Critical Fixes)
├─ 1.1: Fix claude_client attribute mismatch (6 locations)
├─ 1.2: Implement socratic_counselor.process_response() handler
├─ 1.3: Implement spec extraction + conflict detection
└─ 1.4: Wire conflict resolution flow

PHASE 2: RESTORE DIALOGUE (Complete Flows)
├─ 2.1: Implement /hint endpoint (suggestions system)
├─ 2.2: Fix NLU dialogue (depends on 1.1)
├─ 2.3: Implement debug mode (inline annotations)
└─ 2.4: Fix free session specs detection

PHASE 3: ENHANCE FEATURES (Quality Improvements)
├─ 3.1: Implement question caching
├─ 3.2: Implement phase completion detection
├─ 3.3: Add conflict history tracking
└─ 3.4: Improve context analysis
```

---

## PHASE 1: UNBLOCK SYSTEM

### Task 1.1: Fix `claude_client` Attribute Mismatch

**Severity**: CRITICAL - Blocks 3 routers
**Complexity**: TRIVIAL
**Time**: < 5 minutes
**Status**: ✅ COMPLETE

---

### Task 1.2: Implement Socratic Counselor `process_response()` Handler

**Severity**: CRITICAL - Core dialogue broken
**Complexity**: HIGH
**Time**: 1-2 hours
**Status**: ✅ COMPLETE

---

### Task 1.3: Wire Debug Mode - Inline Annotations

**Severity**: HIGH - Critical for usability
**Complexity**: MEDIUM
**Time**: 1 hour
**Status**: ✅ COMPLETE

---

### Task 1.4: Implement Conflict Resolution Flow

**Severity**: HIGH - Needed for spec management
**Complexity**: MEDIUM
**Time**: 1.5 hours
**Status**: ✅ COMPLETE

---

## PHASE 2: RESTORE DIALOGUE

### Task 2.1: Implement Hints/Suggestions Endpoint

**Severity**: HIGH - User-facing feature
**Complexity**: MEDIUM
**Time**: 1.5 hours
**Status**: ✅ COMPLETE

---

### Task 2.2: Fix NLU Dialogue (Depends on Task 1.1)

**Severity**: MEDIUM - Free-form dialogue mode
**Complexity**: MEDIUM
**Time**: 1 hour
**Status**: ✅ COMPLETE

---

### Task 2.3: Implement Full Debug Mode (Depends on Tasks 1.2, 1.3)

**Severity**: MEDIUM - Developer/admin feature
**Complexity**: MEDIUM
**Time**: 1.5 hours
**Status**: ✅ COMPLETE

---

### Task 2.4: Fix Free Session Specs Detection (Depends on Task 1.2)

**Severity**: MEDIUM - Free tier feature
**Complexity**: LOW
**Time**: 30 minutes
**Status**: ✅ COMPLETE

---

## PHASE 3: ENHANCE FEATURES

All Phase 1 & 2 tasks completed. Phase 3 enhancements ready for implementation.

---

### Task 3.1: Implement Question Caching for Performance

**Priority**: HIGH
**Complexity**: Medium
**Estimated Impact**: 50%+ reduction in LLM API calls

#### Current State
- Questions generated on-demand every request
- No caching mechanism exists
- Expensive LLM calls for every question
- Duplicate questions possible

#### Implementation

**1. Add question_cache table to database**
- File: `backend/src/socrates_api/database.py`
- Schema:
  ```sql
  CREATE TABLE question_cache (
    cache_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    phase TEXT,
    category TEXT,
    question_text TEXT NOT NULL,
    created_at TEXT,
    used_count INTEGER DEFAULT 0,
    last_used_at TEXT,
    INDEX (project_id, phase, category)
  )
  ```

**2. Add cache lookup in orchestrator**
- File: `backend/src/socrates_api/orchestrator.py`
- Method: `_get_cached_question(project_id, phase, category)`
- Check cache before LLM call
- Return cached question if not recently used (within last 3 questions)
- Increment usage counter

**3. Implement cache population**
- Method: `_cache_question(project_id, phase, category, question)`
- Store LLM-generated questions in cache
- Limit cache size per project (max 50 questions)

**4. Add cache invalidation**
- Clear cache when phase changes
- Clear cache when project description changes
- Manual endpoint: `DELETE /projects/{project_id}/cache/questions`

**Files to Modify:**
- `backend/src/socrates_api/database.py` (add table, methods)
- `backend/src/socrates_api/orchestrator.py` (line 1147+, add cache logic to `_handle_socratic_counselor`)
- `backend/src/socrates_api/routers/projects.py` (add cache invalidation endpoint)

**Success Criteria:**
- 70%+ cache hit rate
- LLM calls reduced by 60%+
- No duplicate questions within 5 questions
- Response time improved 50%+

---

### Task 3.2: Phase Completion Detection

**Priority**: HIGH
**Complexity**: Medium
**Estimated Impact**: Better user workflow guidance

#### Current State
- Phase maturity scores exist (70% = ready, 95% = complete)
- Manual phase advancement only
- No automatic detection or suggestions
- No completion notifications

#### Implementation

**1. Add phase readiness detection**
- File: `backend/src/socrates_api/orchestrator.py` (near `_handle_socratic_counselor`)
- Method: `_check_phase_readiness(project)`
- Calculate maturity score for current phase
- Check category coverage (goals, requirements, tech_stack, constraints)
- Return readiness status with recommendations

**2. Add completion notifications**
- File: `backend/src/socrates_api/routers/projects_chat.py` (line 900+)
- After processing user response, check phase readiness
- If maturity >= 95%, include completion notification
- Suggest advancing to next phase

**3. Add phase readiness endpoint**
- Endpoint: `GET /projects/{project_id}/phase/readiness`
- Returns: current maturity, readiness status, recommendations

**4. Optional auto-advance**
- Project setting: `auto_advance_phases` (boolean)
- If enabled and phase >= 95%, auto-advance

**Files to Modify:**
- `backend/src/socrates_api/orchestrator.py` (readiness detection)
- `backend/src/socrates_api/routers/projects_chat.py` (completion notifications, line 900+)
- `backend/src/socrates_api/routers/projects.py` (readiness endpoint)
- `backend/src/socrates_api/models_local.py` (add auto_advance_phases field)

**Success Criteria:**
- Phase readiness accurate (±5%)
- Users notified when ready to advance
- Recommendations help complete weak categories
- Auto-advance works without errors

---

### Task 3.3: Conflict History Tracking

**Priority**: MEDIUM
**Complexity**: Medium
**Estimated Impact**: Better conflict management and pattern detection

#### Current State
- Conflicts stored with basic metadata
- Missing: resolved_at, resolved_by, resolution_approach
- No recurring conflict detection
- No conflict analytics

#### Database Schema Enhancement
- File: `socratic_system/database/project_db.py` OR `backend/src/socrates_api/database.py`
- Add columns to conflicts table:
  ```sql
  ALTER TABLE conflicts ADD COLUMN resolved_at TEXT;
  ALTER TABLE conflicts ADD COLUMN resolved_by TEXT;
  ALTER TABLE conflicts ADD COLUMN resolution_approach TEXT;
  ```

#### Implementation

**1. Enhance conflict table schema**
- Add: `resolved_at`, `resolved_by`, `resolution_approach`
- Update: `update_conflict_status()` to capture metadata

**2. Track resolution metadata**
- File: `backend/src/socrates_api/routers/projects_chat.py` (line 2081+)
- In conflict resolution endpoint, capture:
  - Timestamp when resolved
  - User who resolved it
  - Resolution approach (keep/replace/skip/manual)

**3. Add conflict history endpoint**
- File: `backend/src/socrates_api/routers/conflicts.py` (line 220+)
- Endpoint: `GET /conflicts/history/{project_id}`
- Currently stub - implement full functionality

**4. Add recurring conflict detection**
- File: `backend/src/socrates_api/orchestrator.py`
- Method: `_check_recurring_conflicts(project_id, field, conflict_type)`
- Query database for previous conflicts on same field
- If found within 30 days, flag as recurring

**5. Add conflict analytics**
- Endpoint: `GET /conflicts/analytics/{project_id}`
- Return metrics: total, resolution rate, avg time, most conflicted fields
- Pattern analysis: recurring conflicts, resolution approaches

**Files to Modify:**
- `socratic_system/database/project_db.py` (schema update)
- `backend/src/socrates_api/routers/projects_chat.py` (line 2081+, capture metadata)
- `backend/src/socrates_api/routers/conflicts.py` (line 220+, implement endpoints)
- `backend/src/socrates_api/orchestrator.py` (recurring detection)

**Success Criteria:**
- All resolutions tracked with full metadata
- History queryable by project
- Recurring conflicts flagged automatically
- Analytics provide actionable insights

---

### Task 3.4: Context Analysis Improvements

**Priority**: MEDIUM
**Complexity**: High
**Estimated Impact**: Better spec extraction accuracy

#### Current State
- Spec extraction uses 3-tier fallback (ContextAnalyzer → LLM → hardcoded)
- No accuracy tracking
- No confidence scores
- No learning from corrections

#### Implementation

**1. Add confidence scoring**
- File: `backend/src/socrates_api/orchestrator.py` (line 1526+)
- Modify `_extract_insights_fallback()` to return confidence scores (0-1):
  - ContextAnalyzer: confidence = 0.9
  - LLM fallback: confidence = 0.7
  - Hardcoded fallback: confidence = 0.3

**2. Track extraction accuracy**
- File: `backend/src/socrates_api/analytics/spec_extraction_analytics.py` (new)
- Table: `spec_extraction_log`
- Track: attempts, successes, method, confidence, accuracy

**3. Add user feedback mechanism**
- File: `backend/src/socrates_api/routers/projects_chat.py`
- Endpoint: `POST /projects/{project_id}/specs/feedback`
- Allow users to mark extracted specs as correct/incorrect
- Store feedback for improvement

**4. Improve prompts based on feedback**
- Analyze feedback patterns
- Adjust LLM prompts for better accuracy
- Prioritize high-confidence extractions

**Files to Create:**
- `backend/src/socrates_api/analytics/spec_extraction_analytics.py`

**Files to Modify:**
- `backend/src/socrates_api/orchestrator.py` (line 1526+, confidence scoring)
- `backend/src/socrates_api/routers/projects_chat.py` (feedback endpoint)
- `backend/src/socrates_api/database.py` (extraction log table)

**Success Criteria:**
- Confidence scores correlate with accuracy (±10%)
- Extraction accuracy tracked per method
- User feedback captured and stored
- Insights available for improvements

---

## IMPLEMENTATION PRIORITY

**Phase 3A (Week 1 - High Priority):**
1. Task 3.1: Question Caching
2. Task 3.2: Phase Completion Detection

**Phase 3B (Week 2 - Medium Priority):**
3. Task 3.3: Conflict History Tracking
4. Task 3.4: Context Analysis Improvements

---

## SUMMARY TABLE

| Phase | Task | Severity | Complexity | Time | Status |
|-------|------|----------|-----------|------|--------|
| **1** | 1.1: Fix claude_client | CRITICAL | TRIVIAL | 5m | ✅ COMPLETE |
| | 1.2: Implement process_response | CRITICAL | HIGH | 2h | ✅ COMPLETE |
| | 1.3: Wire debug mode | HIGH | MEDIUM | 1h | ✅ COMPLETE |
| | 1.4: Conflict resolution flow | HIGH | MEDIUM | 1.5h | ✅ COMPLETE |
| **2** | 2.1: Hints endpoint | HIGH | MEDIUM | 1.5h | ✅ COMPLETE |
| | 2.2: Fix NLU dialogue | MEDIUM | MEDIUM | 1h | ✅ COMPLETE |
| | 2.3: Full debug mode | MEDIUM | MEDIUM | 1.5h | ✅ COMPLETE |
| | 2.4: Free session specs | MEDIUM | LOW | 30m | ✅ COMPLETE |
| **3** | 3.1: Question caching | HIGH | MEDIUM | 2h | 🔄 READY |
| | 3.2: Phase completion | HIGH | MEDIUM | 2h | 🔄 READY |
| | 3.3: Conflict history | MEDIUM | MEDIUM | 2h | 🔄 READY |
| | 3.4: Context analysis | MEDIUM | HIGH | 2.5h | 🔄 READY |

**Phases 1-2 Status**: ✅ COMPLETE (960+ lines implemented, 8 files modified)
**Phase 3 Status**: 🔄 READY FOR IMPLEMENTATION (8.5 hours estimated)

---

## SUCCESS METRICS

**Phase 3 Overall Goals:**
- 50% reduction in LLM API calls (via caching)
- 95% phase completion detection accuracy
- 100% conflict resolution tracking coverage
- 80% spec extraction confidence correlation
- 40% average performance improvement

---

## TESTING STRATEGY

### Unit Tests
- Question cache CRUD operations
- Phase readiness calculation accuracy
- Conflict history retrieval
- Spec extraction confidence scoring

### Integration Tests
- Question caching end-to-end
- Phase completion detection with real projects
- Conflict resolution with history tracking
- Multi-tier spec extraction with fallbacks

### Performance Tests
- Cache hit rate measurement
- Response time improvements
- Database query performance
- LLM call reduction metrics
