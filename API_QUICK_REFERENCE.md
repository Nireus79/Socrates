# API Endpoint Quick Reference & Status

**Last Updated**: 2026-03-30
**Purpose**: Quick lookup table for endpoint status and next steps

---

## Critical Issues (MUST FIX IMMEDIATELY)

### 1. Undefined `claude_client` - BLOCKING

**Files**:
- `nlu.py` line ~206
- `free_session.py` line ~205

**Error**:
```
NameError: name 'claude_client' is not defined
```

**Fix**:
```python
# BEFORE (broken):
response = claude_client.complete(prompt)

# AFTER (fixed):
from socrates_api.main import get_orchestrator
orchestrator = get_orchestrator()
agent = orchestrator.agents.get("nlu_interpreter")  # or appropriate agent
result = agent.process({"action": "interpret", "input": text})
```

**Estimated Fix Time**: 30 minutes

---

### 2. Response Processing Stub - BLOCKING

**File**: `projects_chat.py` lines 1255-1272

**Current Behavior**: Returns success without doing anything

**Required Implementation**:
```python
def _handle_socratic_counselor(...):
    if action == "process_response":
        # TODO: Implement
        # 1. Validate response against current question
        # 2. Extract specs from response text
        # 3. Calculate confidence score
        # 4. Generate feedback for user
        # 5. Update project context
        # 6. Check phase readiness
        # 7. Return structured response
```

**Estimated Fix Time**: 2 hours

---

### 3. Conflict Detection Stub - BLOCKING

**File**: `conflicts.py` lines 107-161

**Current Behavior**: Always returns empty conflicts list with comment "Simulate conflict detection"

**Required Implementation**:
```python
def detect_conflicts(request: ConflictDetectionRequest):
    # TODO: Implement
    # 1. Load project from database
    # 2. Use AgentConflictDetector from orchestrator
    # 3. Analyze new_values against existing project specs
    # 4. Save detected conflicts to database
    # 5. Return conflict list with severity levels
```

**Estimated Fix Time**: 1.5 hours

---

## Unexamined Endpoints (NEEDS AUDIT)

| File | Endpoint | Status | Notes |
|------|----------|--------|-------|
| code_generation.py | POST /projects/{id}/code/generate | ❓ Unknown | 6+ endpoints total |
| code_generation.py | POST /projects/{id}/code/refactor | ❓ Unknown | Part of code module |
| code_generation.py | POST /projects/{id}/code/validate | ❓ Unknown | Validation endpoint |
| code_generation.py | GET /projects/{id}/code/history | ❓ Unknown | History endpoint |
| skills.py | POST /projects/{id}/skills/generate | ❓ Unknown | Auto-generation endpoint |
| learning.py | POST /projects/{id}/learning/record | ❓ Unknown | Record learning interaction |
| learning.py | GET /projects/{id}/learning/progress | ❓ Unknown | Progress tracking |
| learning.py | POST /projects/{id}/learning/feedback | ❓ Unknown | Feedback recording |
| analysis.py | GET /projects/{id}/analysis | ❓ Unknown | Project analysis |
| analytics.py | GET /projects/{id}/analytics | ❓ Unknown | Analytics data |
| workflow.py | POST /projects/{id}/workflow/execute | ❓ Unknown | Workflow execution |

---

## Working Endpoints (✅ NO ISSUES)

| Endpoint | File | Status | Notes |
|----------|------|--------|-------|
| GET /projects | projects.py | ✅ Working | List projects |
| POST /projects | projects.py | ✅ Working | Create project |
| GET /projects/{id} | projects.py | ✅ Working | Get project details |
| PUT /projects/{id} | projects.py | ✅ Working | Update project |
| DELETE /projects/{id} | projects.py | ✅ Working | Delete project |
| GET /projects/{id}/chat/question | projects_chat.py | ✅ Working | Generate question |
| GET /projects/{id}/maturity | projects.py | ✅ Working | Get maturity scores (Task 3.2) |
| GET /projects/{id}/maturity/{phase} | projects.py | ✅ Working | Get phase maturity (Task 3.2) |
| POST /projects/{id}/skills | skills.py | ✅ Working | Set/update skills |
| GET /projects/{id}/skills | skills.py | ✅ Working | List skills |
| GET /auth/login | auth.py | ✅ Working | User login |
| POST /auth/logout | auth.py | ✅ Working | User logout |

---

## Partial/Incomplete Endpoints (🔶 HAS ISSUES)

| Endpoint | File | Issue | Fix Time |
|----------|------|-------|----------|
| GET /nlu/interpret | nlu.py | Undefined claude_client | 30 min |
| POST /free_session/ask | free_session.py | Undefined claude_client | 30 min |
| POST /projects/{id}/chat/message | projects_chat.py | Stub implementation | 2 hours |
| GET /conflicts/detect | conflicts.py | Stub implementation | 1.5 hours |

---

## Implementation Priority Matrix

### Priority 1: CRITICAL (Must Fix This Week)

```
┌─────────────────────────────────────────┬──────────┐
│ Task                                    │ Time     │
├─────────────────────────────────────────┼──────────┤
│ 1. Fix undefined claude_client          │ 30 min   │
│    - nlu.py line 206                    │          │
│    - free_session.py line 205           │          │
├─────────────────────────────────────────┼──────────┤
│ 2. Implement response processing        │ 2 hours  │
│    - projects_chat.py lines 1255-1272   │          │
│    - Include spec extraction            │          │
│    - Include feedback generation        │          │
├─────────────────────────────────────────┼──────────┤
│ 3. Implement conflict detection         │ 1.5 hours│
│    - conflicts.py lines 107-161         │          │
│    - Use AgentConflictDetector           │          │
│    - Save to database                   │          │
├─────────────────────────────────────────┼──────────┤
│ TOTAL: CRITICAL PATH                    │ 4 hours  │
└─────────────────────────────────────────┴──────────┘
```

### Priority 2: HIGH (Next Week)

```
┌─────────────────────────────────────────┬──────────┐
│ Task                                    │ Time     │
├─────────────────────────────────────────┼──────────┤
│ 1. Audit code_generation.py endpoints   │ 1 hour   │
│    - 6+ endpoints to verify             │          │
│    - Check agent integration            │          │
├─────────────────────────────────────────┼──────────┤
│ 2. Audit learning.py endpoints          │ 1 hour   │
│    - 5+ endpoints to verify             │          │
│    - Check mastery calculation          │          │
├─────────────────────────────────────────┼──────────┤
│ 3. Audit skills generation endpoints    │ 30 min   │
│    - Auto-skill generation              │          │
├─────────────────────────────────────────┼──────────┤
│ 4. Audit analysis.py endpoints          │ 1 hour   │
│    - Project analysis features          │          │
├─────────────────────────────────────────┼──────────┤
│ TOTAL: DISCOVERY PHASE                  │ 3.5 hours│
└─────────────────────────────────────────┴──────────┘
```

### Priority 3: MEDIUM (Phase 4)

```
┌─────────────────────────────────────────┬──────────┐
│ Task                                    │ Time     │
├─────────────────────────────────────────┼──────────┤
│ 1. Enable PromptInjectionDetector       │ 2 hours  │
│    - Security critical                  │          │
│    - Protect all LLM inputs             │          │
├─────────────────────────────────────────┼──────────┤
│ 2. Integrate socratic-analyzer          │ 2 hours  │
│    - Replace duplicate analysis.py      │          │
├─────────────────────────────────────────┼──────────┤
│ 3. Integrate socratic-knowledge         │ 2 hours  │
│    - Replace duplicate knowledge.py     │          │
├─────────────────────────────────────────┼──────────┤
│ 4. Integrate socratic-rag               │ 3 hours  │
│    - Add RAG capabilities               │          │
├─────────────────────────────────────────┼──────────┤
│ 5. Integrate socratic-workflow          │ 3 hours  │
│    - Add workflow execution             │          │
├─────────────────────────────────────────┼──────────┤
│ TOTAL: INTEGRATION PHASE                │ 12 hours │
└─────────────────────────────────────────┴──────────┘
```

---

## File-by-File Checklist

### ✅ Verified Working

- [x] auth.py - Authentication (no issues)
- [x] projects.py - Project CRUD (no issues)
- [x] skills.py - Skill management (mostly working)
- [x] chat_sessions.py - Session management (no issues)
- [x] knowledge.py - Knowledge APIs (no issues)
- [x] database_health.py - Database monitoring (no issues)

### 🔶 Needs Fixes

- [ ] projects_chat.py - Response processing stub (2 hours)
- [ ] conflicts.py - Conflict detection stub (1.5 hours)
- [ ] nlu.py - claude_client undefined (30 min)
- [ ] free_session.py - claude_client undefined (30 min)

### ❓ Needs Audit

- [ ] code_generation.py (6+ endpoints)
- [ ] learning.py (5+ endpoints)
- [ ] analysis.py (multiple endpoints)
- [ ] analytics.py (multiple endpoints)
- [ ] workflow.py (workflow endpoints)
- [ ] library_integrations.py

---

## Quick Debugging Guide

### Problem: claude_client is not defined

**In**: nlu.py, free_session.py

**Root Cause**: Code references a `claude_client` object that was never imported or created

**Quick Fix**:
```python
# Add these imports at top of file
from socrates_api.main import get_orchestrator

# Replace claude_client.complete() calls with:
orchestrator = get_orchestrator()
agent = orchestrator.agents.get("desired_agent")
result = agent.process({"action": "...", "content": "..."})
```

**Verification**:
```bash
# Search for remaining claude_client references
grep -r "claude_client" backend/src/socrates_api/routers/
```

---

### Problem: Endpoint returns empty response

**Endpoints Affected**:
- GET /conflicts/detect
- POST /projects/{id}/chat/message (process_response action)

**Root Cause**: Functions are stubs - they accept request but don't process it

**Example** (conflicts.py:139):
```python
# Current (WRONG):
conflicts: List[ConflictInfo] = []  # Always empty!
return ConflictDetectionResponse(conflicts=conflicts, ...)

# Should be:
detector = get_conflict_detector()
conflicts = detector.detect(new_values, existing_project_context)
db.save_conflict(request.project_id, conflicts)
return ConflictDetectionResponse(conflicts=conflicts, ...)
```

**Verification**:
```python
# Add logging to see what's happening
logger.debug(f"Detected {len(conflicts)} conflicts")
logger.debug(f"Conflicts: {conflicts}")
```

---

## Test Command Reference

### Test a Specific Endpoint

```bash
# Test question generation (should work)
curl -X GET "http://localhost:8000/projects/test-id/chat/question"

# Test response processing (will fail - stub)
curl -X POST "http://localhost:8000/projects/test-id/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"mode": "socratic", "action": "process_response", "response": "test"}'

# Test conflict detection (will fail - stub)
curl -X GET "http://localhost:8000/conflicts/detect" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "test", "new_values": {}}'

# Test NLU (will fail - undefined claude_client)
curl -X POST "http://localhost:8000/nlu/interpret" \
  -H "Content-Type: application/json" \
  -d '{"input": "test"}'
```

---

## Database Tables Ready for Use

### ✅ Already Exist (Task 3.1-3.4)

- `question_cache` - For caching generated questions
- `conflict_history` - For storing conflict history
- `conflict_resolutions` - For tracking resolutions
- `conflict_decisions` - For conflict decision versioning
- `spec_extraction_log` - For tracking spec extractions
- `spec_extraction_patterns` - For extraction patterns

### Available Methods

```python
# Question Cache (Task 3.1)
db.save_cached_question(project_id, phase, category, question_text)
db.get_cached_questions(project_id, phase=None, category=None)
db.increment_question_usage(cache_id)

# Conflict History (Task 3.3)
db.save_conflict(project_id, conflict_type, severity, context)
db.get_conflict_history(project_id, limit=50)
db.save_decision(conflict_id, decision_data, version)
db.get_conflict_decisions(conflict_id)

# Spec Extraction (Task 3.4)
db.log_spec_extraction(project_id, spec_id, extraction_method, confidence)
db.record_extraction_feedback(log_id, success, user_feedback)
db.get_extraction_metrics(project_id)
```

---

## Library Classes Ready to Use

### ✅ Integrated (Recommended)

```python
# Task 3.2 - Phase Maturity
from socrates_maturity import MaturityCalculator
calculator = MaturityCalculator()
maturity = calculator.calculate_phase_maturity(phase_specs, phase)

# Task 3.4 - Confidence Scoring
from socratic_learning import PatternDetector
detector = PatternDetector()
confidence = min(0.95, success_rate)  # Algorithm already used

# Task 3.3 - Conflict Detection
from socratic_agents import AgentConflictDetector
agent = orchestrator.agents["conflict_detector"]
conflicts = agent.detect_conflicts(items)
```

### 🔶 Partially Used (Opportunity)

```python
# Not yet called - available for use
from socratic_conflict import HistoryTracker, ConflictDetector
tracker = HistoryTracker()
tracker.add_conflict(conflict)
tracker.add_decision(decision)
stats = tracker.get_statistics()
```

### ❌ Not Used (Security Gap)

```python
# CRITICAL - Protect LLM inputs
from socratic_security import PromptInjectionDetector, PromptSanitizer
detector = PromptInjectionDetector()
sanitizer = PromptSanitizer()
sanitized = sanitizer.sanitize(user_input)
is_safe = detector.is_safe(sanitized)
```

---

## Next Steps Summary

### Today (Phase 1)

1. ✅ Complete this audit (DONE)
2. [ ] Fix claude_client references (30 min)
3. [ ] Test NLU and free_session endpoints (15 min)
4. [ ] Implement response processing (2 hours)

### Tomorrow (Phase 2)

1. [ ] Implement conflict detection (1.5 hours)
2. [ ] Audit unknown endpoints (3.5 hours)
3. [ ] Fix any broken endpoints found (variable)

### This Week (Phase 3)

1. [ ] Enable PromptInjectionDetector (security)
2. [ ] Add comprehensive testing (4+ hours)
3. [ ] Document all endpoints (2+ hours)

### Next Week (Phase 4)

1. [ ] Integrate remaining libraries
2. [ ] Add OpenAPI documentation
3. [ ] Performance optimization

---

**Document Status**: Ready for implementation
**Total Work Estimated**: 4 hours critical + 3.5 hours audit + 12 hours integration = ~20 hours total
**Critical Path**: 4 hours (fixes must be done before feature development)
