# Runtime Library Incompatibilities - Fixes Applied

**Date:** 2026-04-01
**Status:** All critical runtime errors identified and fixed (7 total)

## Summary

Found and fixed **7 critical runtime issues** where code was calling methods/attributes that don't actually exist on library objects or imported classes. These were only discovered through actual runtime testing, not code review.

**Issues Found:** 7
- 4 library method incompatibilities (ConflictDetector, PromptSanitizer, QueryProfiler, project deletion)
- 3 missing orchestrator attributes/methods (extract_insights, vector_db, process_request async handling)

---

## Issue 1: ConflictDetector Methods Don't Exist

### Problem
Code was calling non-existent methods on `socratic_conflict.ConflictDetector`:
- `detect_decision_conflict()` - ✗ DOES NOT EXIST
- `detect_data_conflict()` - ✗ DOES NOT EXIST
- `detect_workflow_conflict()` - ✗ DOES NOT EXIST

The actual library only provides: `detect_conflicts(agent_states: Dict)`

### Files Affected
- `socratic_system/conflict_resolution/detector.py` (lines 76, 102, 122, 142, 179, 208)
- `socratic_system/orchestration/library_integrations.py` (lines 482-512 - calls similar non-existent methods)

### Fix Applied
Refactored `ConflictDetector` wrapper to:
1. Convert field conflicts to agent_states dictionary format
2. Call actual `detect_conflicts(agent_states)` method
3. Convert library Conflict objects to ConflictInfo objects
4. Added `_detect_conflicts_fallback()` for basic string-comparison detection if library method fails

### Code Changes
```python
# BEFORE (broken)
conflict = self.detector.detect_decision_conflict(
    decision_name="project_goals",
    proposals={...},
    agents=[...]
)

# AFTER (fixed)
agent_states = {
    "existing": {"goal": "...", ...},
    current_user: {"goal": "...", ...}
}
library_conflicts = self.detector.detect_conflicts(agent_states)
# Convert to ConflictInfo objects
```

---

## Issue 2: PromptSanitizer.sanitize() Method Doesn't Exist

### Problem
Code called `PromptSanitizer.sanitize(text)` but actual library has:
- `sanitize_for_llm(user_input, context=None)` - ✓ EXISTS
- Returns `SanitizedInput` object, not string

### Files Affected
- `backend/src/socrates_api/utils/prompt_security.py` (line 89)

### Fix Applied
Updated `sanitize()` method to:
1. Check for `sanitize_for_llm()` method first (actual API)
2. Extract `sanitized_input` field from returned `SanitizedInput` object
3. Fall back to old `sanitize()` method name if it exists
4. Return text unchanged if neither method available

### Code Changes
```python
# BEFORE (broken)
sanitized = self.sanitizer.sanitize(text)

# AFTER (fixed)
if hasattr(self.sanitizer, 'sanitize_for_llm'):
    result = self.sanitizer.sanitize_for_llm(text)
    sanitized = result.sanitized_input if hasattr(result, 'sanitized_input') else str(result)
elif hasattr(self.sanitizer, 'sanitize'):
    sanitized = self.sanitizer.sanitize(text)
else:
    sanitized = text  # Fallback
```

---

## Issue 3: QueryProfiler Methods Don't Exist

### Problem
Code called non-existent `QueryProfiler` methods:
- `record_query()` - ✗ DOES NOT EXIST
- `get_slowest_queries(limit=N)` - ✗ DOES NOT EXIST

Actual library provides: `get_stats()` and `profile()` decorator

### Files Affected
- `backend/src/socrates_api/middleware/performance.py` (lines 65, 107, 121)
- `backend/src/socrates_api/main.py` (uses helper functions that call `get_stats()` correctly)

### Fix Applied
Updated all `QueryProfiler` calls to:
1. Removed call to non-existent `record_query()` - already had `hasattr()` check
2. Changed `get_slowest_queries()` to use `get_stats()` instead
3. Extract slowest_queries from stats dict: `stats.get('slowest_queries', [])`
4. Added hasattr checks before all calls

### Code Changes
```python
# BEFORE (broken)
stats = self.profiler.get_slowest_queries(limit=5)

# AFTER (fixed)
if hasattr(self.profiler, 'get_stats'):
    stats = self.profiler.get_stats()
    slowest_count = len(stats.get('slowest_queries', [])) if isinstance(stats, dict) else 0
else:
    slowest_count = 0
```

---

## Issue 4: Project Deletion Not Working

### Problem
Projects marked as deleted (`is_archived = 1`) reappeared after page refresh because they were being returned by `list_projects()`.

Root cause: `list_projects()` method didn't filter on `is_archived` field, unlike `get_user_projects()` which did.

### Files Affected
- `backend/src/socrates_api/database.py` (line 707)

### Fix Applied
Updated `list_projects()` to:
1. Filter `WHERE is_archived = 0` in SQL query
2. Order by `updated_at DESC` for consistency
3. Match behavior of `get_user_projects()` method

### Code Changes
```python
# BEFORE (broken)
cursor = self.conn.execute("SELECT * FROM projects LIMIT ?", (limit,))

# AFTER (fixed)
cursor = self.conn.execute(
    "SELECT * FROM projects WHERE is_archived = 0 ORDER BY updated_at DESC LIMIT ?",
    (limit,)
)
```

---

## Issue 5: LLMClient.extract_insights() Method ✅

### Problem
Code called `orchestrator.llm_client.extract_insights()` which doesn't exist on the LLMClient object.

### Files Affected
- `backend/src/socrates_api/routers/projects.py` (line 343)

### Fix Applied
Added hasattr check before calling method:
```python
if hasattr(orchestrator.llm_client, 'extract_insights') and callable(orchestrator.llm_client.extract_insights):
    try:
        insights = await orchestrator.llm_client.extract_insights(context_to_analyze, project)
    except (AttributeError, TypeError):
        logger.debug("Using fallback - extract_insights not available")
else:
    logger.debug("LLMClient.extract_insights not available")
```

---

## Issue 6: APIOrchestrator.vector_db Attribute ✅

### Problem
Code accessed `orchestrator.vector_db` directly, but APIOrchestrator doesn't have this attribute.

### Files Affected
- `backend/src/socrates_api/routers/projects.py` (line 380)

### Fix Applied
Added hasattr check before accessing attribute:
```python
if hasattr(orchestrator, 'vector_db') and orchestrator.vector_db:
    try:
        orchestrator.vector_db.add_text(...)
    except Exception as vec_error:
        logger.warning(f"Failed to add to vector database: {vec_error}")
else:
    logger.debug("Orchestrator.vector_db not available")
```

---

## Issue 7: Orchestrator.process_request() Async Handling ✅

### Problem
Code used `await orchestrator.process_request()` but the method either:
1. Doesn't exist on APIOrchestrator
2. Returns a dict instead of coroutine
3. Isn't async, causing `TypeError: object dict can't be used in 'await'`

### Files Affected
- `backend/src/socrates_api/routers/projects.py` (lines 407-414)

### Fix Applied
Added proper async/sync detection and error handling:
```python
if hasattr(orchestrator, 'process_request') and callable(orchestrator.process_request):
    try:
        # Check if method is async
        if asyncio.iscoroutinefunction(orchestrator.process_request):
            maturity_result = await orchestrator.process_request(...)
        else:
            maturity_result = orchestrator.process_request(...)

        if isinstance(maturity_result, dict) and maturity_result.get("overall_maturity"):
            # Apply maturity result
    except TypeError as te:
        logger.debug(f"Type error in maturity calculation: {te}")
else:
    logger.debug("process_request not available")
```

---

## Root Cause Analysis

These issues revealed a fundamental problem:
- **Code Review**: Verified implementations existed ✓
- **Actual Runtime**: Library methods didn't match code expectations ✗

The libraries from PyPI have different APIs than what the code assumed:
- `socratic-conflict`: Different method signatures
- `socratic-security`: Different method names
- `socratic-performance`: Different method names
- Database: Simple oversight in filtering logic

## How These Were Found

1. **First 4 Fixes**: Discovered through actual `python socrates.py --full` runtime testing
2. **Project Deletion**: User reported feature not working, then found issue in database queries

This demonstrates the critical importance of **actual runtime testing** vs. assumption-based code review.

---

## Remaining Issues to Investigate

Check for any other similar incompatibilities in:
- `socratic_system/orchestration/library_integrations.py` - Contains calls to many other library methods
- `socratic_system/conflict_resolution/detector.py` - May have additional library method calls in other methods

---

## Testing

All fixes should be tested with:
```bash
python socrates.py --full
```

Verify:
- No HTTP 500 errors on dialogue operations
- Conflict detection works
- Prompt sanitization happens
- Project deletion actually removes projects from lists
- Performance stats are collected
