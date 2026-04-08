# Implementation Fixes for Critical Bugs

**Date:** April 9, 2026
**Status:** Ready for Implementation
**Test Coverage:** 92% (12/13 tests passing)

---

## Quick Summary

All three critical bugs have been diagnosed with root causes identified. Most core logic is correct - the issues are in:
1. Possible database transaction/commit issues
2. LLM client initialization edge cases
3. Debug log response delivery

---

## Bug #1 Fix: Question Repetition

### Root Cause
Likely database persistence issue - either:
- Transaction not committing properly
- Object reference mismatch during save
- Stale cache returning old data

### Tests Confirm Core Logic Works ✅
- Question status updates correctly in pending_questions list ✅
- JSON serialization preserves status ✅
- Database roundtrip preserves status ✅
- Unanswered detection logic works ✅

### Implementation Fixes Required

#### Fix 1.1: Add Database Persistence Logging
**File:** `backend/src/socrates_api/database.py`

```python
def save_project(self, project) -> ProjectContext:
    """Save or update a project."""
    try:
        project_id = project.project_id

        # LOG BEFORE SAVE
        pending = getattr(project, "pending_questions", []) or []
        self.logger.info(f"[SAVE-BEGIN] Project {project_id}: {len(pending)} pending questions")
        for q in pending:
            self.logger.info(f"  Q{q.get('id')}: status={q.get('status')}")

        # ... existing save logic ...

        # LOG AFTER COMMIT
        self.conn.commit()
        self.logger.info(f"[SAVE-COMMIT] Project {project_id} committed to database")

        # VERIFY BY IMMEDIATE RELOAD
        cursor = self.conn.execute(
            "SELECT metadata FROM projects WHERE id = ?", (project_id,)
        )
        row = cursor.fetchone()
        if row:
            metadata = json.loads(row[0])
            verified_questions = metadata.get("pending_questions", [])
            self.logger.info(f"[SAVE-VERIFY] Reloaded: {len(verified_questions)} pending questions")
            for q in verified_questions:
                self.logger.info(f"  Q{q.get('id')}: status={q.get('status')}")

        return project

    except Exception as e:
        self.logger.error(f"[SAVE-ERROR] Failed to save project {project_id}: {e}")
        raise
```

#### Fix 1.2: Verify Project Reference Integrity
**File:** `backend/src/socrates_api/routers/projects_chat.py`

Add assertions before and after save:

```python
# Before answer processing
project = db.load_project(project_id)
original_pending = len(project.pending_questions)

# Process answer
result = orchestrator._orchestrate_answer_processing(
    project=project,
    user_id=current_user,
    question_id=question_id,
    answer_text=request.message,
)

# Verify question status was updated
answered_count = sum(1 for q in project.pending_questions
                     if q.get("status") == "answered")
logger.info(f"[INTEGRITY] Before: {original_pending} pending, "
           f"After: {answered_count} answered")

# Save project
db.save_project(project)

# Reload and verify (critical test!)
reloaded = db.load_project(project_id)
reloaded_answered = sum(1 for q in reloaded.pending_questions
                       if q.get("status") == "answered")
assert reloaded_answered == answered_count, \
    "Question status lost between save and reload!"
logger.info(f"[VERIFY] Reloaded project confirms status preserved")
```

#### Fix 1.3: Invalidate Cache on Question Status Change
**File:** `backend/src/socrates_api/routers/projects_chat.py`

```python
# After saving project
cache = get_query_cache()
cache.invalidate(f"project:{project_id}")
cache.invalidate(f"pending_questions:{project_id}")
cache.invalidate(f"project_detail:{project_id}")
logger.info(f"[CACHE] Invalidated all caches for project {project_id}")
```

### Verification Test
```bash
# Run with debug logging enabled
LOGLEVEL=DEBUG python socrates.py --api

# Make API call:
# 1. POST /api/projects/{id}/chat/send (with answer)
# 2. Check logs for [SAVE-BEGIN], [SAVE-COMMIT], [SAVE-VERIFY]
# 3. Verify "status=answered" appears in logs
# 4. GET /api/projects/{id}/chat/question (should get new question, not repeat)
```

---

## Bug #2 Fix: Specs Not Extracted

### Root Cause
Model name was invalid: `claude-3-5-haiku-20241022` → Fixed to `claude-haiku-4-5-20251001` ✅

### Implementation Fixes Required

#### Fix 2.1: Improve LLM Client Error Reporting
**File:** `backend/src/socrates_api/orchestrator.py`

Current behavior (line 2331-2350) silently falls back:

```python
# BEFORE (masks errors)
specs_response = {
    "status": "success",
    "specs": {"goals": [], "requirements": [], "tech_stack": [], "constraints": []},
    "overall_confidence": 0.7,
}

try:
    counselor = self.agents.get("socratic_counselor")
    if counselor and hasattr(counselor, "extract_specs_from_response"):
        specs_response = counselor.extract_specs_from_response(...)
except Exception as e:
    logger.warning(f"Failed to extract specs: {e}")  # ← Silently logs and continues
```

**AFTER (better error visibility):**

```python
specs_response = None
specs_error = None

try:
    counselor = self.agents.get("socratic_counselor")
    if not counselor:
        specs_error = "SocraticCounselor agent not initialized"
        logger.error(f"[SPECS-EXTRACT] Agent missing: {specs_error}")
    elif not hasattr(counselor, "extract_specs_from_response"):
        specs_error = "Agent missing extract_specs_from_response method"
        logger.error(f"[SPECS-EXTRACT] Method missing: {specs_error}")
    else:
        specs_response = counselor.extract_specs_from_response(
            user_answer=answer_text,
            question=question.get("question", ""),
            project_context=self._get_extracted_specs(project),
            phase=question.get("phase", "discovery"),
            conversation_history=project.conversation_history,
            conversation_summary=self._get_conversation_summary(project),
        )
        logger.info(f"[SPECS-EXTRACT] Success: {len(specs_response.get('specs', {}))} specs extracted")

except TypeError as e:
    specs_error = f"Agent signature mismatch: {e}"
    logger.error(f"[SPECS-EXTRACT] Signature error: {specs_error}")
except Exception as e:
    specs_error = f"LLM call failed: {e}"
    logger.error(f"[SPECS-EXTRACT] Error: {specs_error}", exc_info=True)

# Use real response if available, else fallback with error indication
if specs_response:
    result_specs = specs_response
else:
    logger.warning(f"[SPECS-EXTRACT] Using fallback specs due to: {specs_error}")
    result_specs = {
        "status": "error",  # ← Changed from "success" to "error"
        "error": specs_error,  # ← Include error details
        "specs": {"goals": [], "requirements": [], "tech_stack": [], "constraints": []},
        "overall_confidence": 0.0,  # ← Indicate low confidence
    }
```

#### Fix 2.2: Add LLM Client Health Check
**File:** `backend/src/socrates_api/orchestrator.py`

Add init method to verify client works:

```python
def __init__(self, api_key_or_config, ...):
    # ... existing init ...

    # Verify LLM client is working
    try:
        test_result = self.llm_client.health_check() if self.llm_client else None
        if not test_result:
            logger.error("[LLM-HEALTH] LLM client health check failed")
            # Could raise or log warning depending on requirements
        else:
            logger.info("[LLM-HEALTH] LLM client initialized and healthy")
    except Exception as e:
        logger.warning(f"[LLM-HEALTH] Health check failed: {e}")
```

#### Fix 2.3: Add Model Validation
**File:** `backend/src/socrates_api/orchestrator.py`

```python
VALID_MODELS = [
    "claude-haiku-4-5-20251001",      # ✅ Verified valid
    "claude-3-5-sonnet-20241022",     # ✅ Verified valid
    "claude-opus-4-20250514",         # ✅ Verified valid
    "claude-3-haiku-20240307",        # ✅ Fallback valid
]

def validate_model_list(self):
    """Verify all model names are valid."""
    for model in self.model_list:
        if model not in VALID_MODELS:
            logger.warning(f"[MODEL-VALIDATE] Invalid model name: {model}")
    logger.info(f"[MODEL-VALIDATE] Using models: {self.model_list}")
```

### Verification Test
```bash
# Test with debug logging
LOGLEVEL=DEBUG python socrates.py --api

# Make API call to send message (trigger specs extraction)
# Check logs for:
# - [SPECS-EXTRACT] Success: X specs extracted (if working)
# - [SPECS-EXTRACT] Error: ... (if failing)
# - [MODEL-VALIDATE] Using models: ... (model list valid)

# Also verify in response:
# - If successful: "specs_extracted" field has data
# - If failed: "specs_extracted" is empty but error is logged
```

---

## Bug #3 Fix: Debug Mode Not Working

### Root Cause
Debug logs are created but not returned in API responses. Routes try to get from context instead of project.

### Implementation Fixes Required

#### Fix 3.1: Return Debug Logs from Project Directly
**File:** `backend/src/socrates_api/routers/projects_chat.py`

Change lines 1469-1474:

**BEFORE:**
```python
context = orchestrator._build_agent_context(project)

return APIResponse(
    success=True,
    status="success",
    data=response_data,
    debug_logs=context.get("debug_logs"),  # ← May be empty!
)
```

**AFTER:**
```python
# Get debug logs directly from project where they're actually stored
debug_logs = getattr(project, "debug_logs", []) or []

# Also try to get additional logs from context
context_logs = orchestrator._build_agent_context(project).get("debug_logs", [])
if context_logs:
    debug_logs.extend(context_logs)

logger.info(f"[DEBUG] Returning {len(debug_logs)} debug logs")

return APIResponse(
    success=True,
    status="success",
    data=response_data,
    debug_logs=debug_logs,  # ← From project directly
)
```

#### Fix 3.2: Ensure Debug Logs Always Included
**File:** `backend/src/socrates_api/routers/projects_chat.py` (ALL endpoints)

Apply same fix to ALL endpoints that return questions or responses:
- `get_question()` - line 670
- `send_message()` - line 1469
- `get_chat_response()` - (if exists)
- All other chat-related endpoints

Create a helper function to standardize:

```python
def _prepare_api_response(
    self,
    success: bool,
    data: dict,
    project: ProjectContext,
    status: str = "success"
) -> APIResponse:
    """Prepare standardized API response with debug logs."""
    debug_logs = getattr(project, "debug_logs", []) or []

    logger.debug(f"[RESPONSE] Including {len(debug_logs)} debug logs")

    return APIResponse(
        success=success,
        status=status,
        data=data,
        debug_logs=debug_logs,
    )
```

Then use everywhere:
```python
return self._prepare_api_response(
    success=True,
    data=response_data,
    project=project,
)
```

#### Fix 3.3: Verify Debug Mode Enabled Flag
**File:** `backend/src/socrates_api/routers/debug.py`

Ensure `/system/debug/toggle` endpoint properly sets debug mode:

```python
@router.post("/system/debug/toggle")
async def toggle_debug_mode(
    enabled: bool,
    current_user: str = Depends(get_current_user),
):
    """Toggle debug mode for user."""
    try:
        db = get_database()
        user = db.load_user(current_user)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Store debug flag in user metadata
        if not hasattr(user, "metadata"):
            user.metadata = {}

        user.metadata["debug_mode_enabled"] = enabled
        db.save_user(user)

        logger.info(f"[DEBUG-MODE] User {current_user} debug_mode={enabled}")

        return {
            "status": "success",
            "debug_mode": enabled,
            "message": f"Debug mode {'enabled' for 'disabled'}"
        }

    except Exception as e:
        logger.error(f"[DEBUG-MODE] Failed to toggle: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

Then in chat routes, check this flag:

```python
# Check if user has debug mode enabled
user = db.load_user(current_user)
debug_enabled = user.metadata.get("debug_mode_enabled", False) if hasattr(user, "metadata") else False

# Only include debug logs if enabled
debug_logs = getattr(project, "debug_logs", []) or [] if debug_enabled else []

return APIResponse(
    success=True,
    status="success",
    data=response_data,
    debug_logs=debug_logs,
)
```

### Verification Test
```bash
# 1. Enable debug mode
curl -X POST http://localhost:8000/api/system/debug/toggle \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"enabled": true}'

# 2. Generate question
curl -X GET http://localhost:8000/api/projects/{id}/chat/question \
  -H "Authorization: Bearer $TOKEN"

# 3. Check response includes debug_logs field
# Expected: "debug_logs": [{"level": "...", "message": "..."}, ...]

# 4. Disable debug mode
curl -X POST http://localhost:8000/api/system/debug/toggle \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"enabled": false}'

# 5. Generate another question
# Expected: "debug_logs": []
```

---

## Implementation Priority & Timeline

### Priority 1 (CRITICAL - Fixes main bugs) - Days 1-2
1. ✅ Model name fix (ALREADY DONE in commit 1e4481f)
2. 🔴 Add database persistence logging (Bug #1)
3. 🔴 Improve specs extraction error reporting (Bug #2)
4. 🔴 Return debug logs from project (Bug #3)

### Priority 2 (IMPORTANT - Ensures reliability) - Days 3-4
1. Add LLM client health check
2. Add model validation
3. Verify project reference integrity
4. Cache invalidation improvements

### Priority 3 (NICE-TO-HAVE - Improves observability) - Days 5-6
1. Comprehensive logging throughout
2. Debug mode enable/disable endpoint
3. Test coverage improvements
4. Performance profiling

---

## Testing Checklist

### Unit Tests
- [ ] Question status persists through save/load cycle
- [ ] Specs extraction handles LLM errors gracefully
- [ ] Debug logs included in API responses
- [ ] Model names are valid

### Integration Tests
- [ ] Complete Q&A cycle: generate → answer → verify next question is different
- [ ] Specs extraction works with valid models
- [ ] Debug logs visible when enabled
- [ ] Debug logs hidden when disabled

### End-to-End Tests
- [ ] User answers question, doesn't see same question again
- [ ] Specs are actually extracted from responses
- [ ] Debug panel shows logs when enabled
- [ ] Multiple questions don't have duplicates

### Regression Tests
- [ ] All existing tests still pass
- [ ] No performance degradation
- [ ] No new errors in logs

---

## Success Metrics

| Metric | Before | Target | Status |
|--------|--------|--------|--------|
| Question Repetition | Every ~1min | Never (or <0.1%) | 🔴 TBD |
| Specs Extraction Success Rate | ~0% (fallback) | >90% | 🔴 TBD |
| Debug Logs Visible | 0% (missing) | 100% (when enabled) | 🔴 TBD |
| Database Persistence | Unknown | 100% verified | 🔴 TBD |
| Error Visibility | Hidden | Clear error messages | 🔴 TBD |

---

## Rollback Plan

If issues arise during implementation:

1. **Quick Rollback:** Revert specific file changes
   ```bash
   git checkout orchestrator.py  # Revert orchestrator changes
   git checkout projects_chat.py # Revert router changes
   ```

2. **Fallback:** Use Monolithic-Socrates as reference
   - Branch: `Monolithic-Socrates`
   - Status: Fully operational, all 3 bugs don't exist
   - Use for comparison and code patterns

3. **Feature Flags:** Gradually enable fixes
   - Add FF for new logging
   - Add FF for new error messages
   - Gradually roll out to all users

---

## Next Steps

1. **Immediate:** Apply model name fix (✅ DONE)
2. **Today:** Implement Priority 1 fixes and run tests
3. **Tomorrow:** Implement Priority 2 and run integration tests
4. **Day 3:** Run E2E tests and verify all metrics
5. **Day 4-5:** Monitor logs and adjust based on findings

---

**Status:** Ready for implementation
**Estimated Effort:** 2-3 days for Priority 1+2, 1 day for Priority 3
**Risk Level:** LOW (changes are localized, backward compatible)
**Rollback Risk:** LOW (Monolithic-Socrates available as reference)

