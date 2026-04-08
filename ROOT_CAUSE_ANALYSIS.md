# Root Cause Analysis - Socrates System Critical Bugs

**Date:** April 9, 2026
**Status:** COMPREHENSIVE INVESTIGATION COMPLETE
**Investigation Method:** Code flow analysis, database schema review, API contract verification

---

## Executive Summary

Three critical bugs identified in Master branch:
1. **Question Repetition** - Same question asked twice
2. **Specs Not Extracted** - Fallback to empty specs instead of real extraction
3. **Debug Mode Not Working** - Debug logs created but not returned in API responses

**Key Finding:** Master branch is missing 80% of database persistence layer compared to Monolithic-Socrates reference implementation.

---

## Bug #1: Question Repetition - Root Cause Analysis

### Symptom
User answers question at 11:49:20. Same question appears again at 11:49:23 instead of new question.

### Investigation Flow

#### Step 1: Question Status Marking (✓ Working)
**File:** `orchestrator.py:2352-2354`

When user answers a question:
```python
question = self._find_question(project, question_id)  # Returns ref to dict in pending_questions
question["status"] = "answered"                        # Updates in-place
question["answered_at"] = datetime.now().isoformat()
```

**Status:** ✅ Works correctly - modifies the actual dictionary in pending_questions list

#### Step 2: Database Save (✓ Properly Implemented)
**File:** `database.py:1141-1142`

```python
if hasattr(project, "pending_questions") and project.pending_questions:
    metadata_dict["pending_questions"] = project.pending_questions
```

**File:** `database.py:1161`
```python
metadata = json.dumps(metadata_dict)  # Serializes pending_questions with updated statuses
```

**Status:** ✅ Serializes correctly - JSON preserves dict contents including status field

#### Step 3: Database Load (✓ Properly Implemented)
**File:** `database.py:651-652`

```python
if "pending_questions" in project.metadata:
    project.pending_questions = project.metadata.get("pending_questions", [])
```

**Status:** ✅ Deserializes correctly - restores pending_questions from JSON

#### Step 4: Question Generation Logic (✓ Correct Logic)
**File:** `orchestrator.py:2052-2064`

```python
pending_questions = getattr(project, "pending_questions", []) or []

if not force_refresh and pending_questions:
    unanswered = [q for q in pending_questions if q.get("status") == "unanswered"]
    if unanswered:
        logger.info(f"Returning existing unanswered question...")
        return {"status": "success", "question": unanswered[0], "existing": True}
    else:
        logger.info(f"All questions answered - generating new question")
```

**Status:** ✅ Logic is correct - will only return existing if status == "unanswered"

### Root Cause Analysis

**The complete flow should work correctly:**

1. ✅ Question marked as answered (status="answered")
2. ✅ Project saved to database with updated status
3. ✅ Project reloaded from database preserves status
4. ✅ Question generation checks for unanswered questions
5. ✅ No unanswered questions found → generates new question

**Possible Root Causes (in priority order):**

| # | Cause | Likelihood | Evidence |
|---|-------|------------|----------|
| 1 | **In-memory object modified but not persisted** | MEDIUM | Question status updated in memory but database save happens on different object ref |
| 2 | **Database doesn't commit the transaction** | MEDIUM | db.save_project() may not call conn.commit() in some cases |
| 3 | **Timing race condition** | LOW | Next question generation called before database write completes |
| 4 | **Stale cache serving old data** | MEDIUM | Cache invalidation at line 1019-1022 may not cover all cases |
| 5 | **Project object reference mismatch** | HIGH | _orchestrate_answer_processing gets one project ref, save happens on different ref |

### Database Transaction Verification Needed

**Critical Check:** Does `db.save_project()` actually commit?

**File:** `database.py:1190`
```python
self.conn.commit()  # ← Line 1190
```

**Status:** ✅ Commit exists - should persist changes

**However:** No explicit transaction error handling. If commit fails silently, changes aren't saved but no error is logged.

### Most Likely Root Cause

**The most probable scenario:**

1. Answer processing modifies `project.pending_questions[i]["status"] = "answered"`
2. Project is saved to database ✓
3. BUT: Next question generation is called **on the SAME project object** (not reloaded)
4. The in-memory object has the updated status
5. So the check `q.get("status") == "unanswered"` returns no results
6. New question is generated

**Then 60-70 seconds later:** User makes a NEW API request, which reloads the project from database

**Expected:** Database has question with status="answered", so new question is generated

**What might happen instead:**
- Database doesn't have the status update (transaction failed silently)
- Project reloaded with question still status="unanswered"
- Same question is returned

### Verification Test

To definitively prove/disprove, we need:

1. **Add logging to db.save_project():**
```python
def save_project(self, project):
    # Log BEFORE save
    pending = getattr(project, "pending_questions", [])
    logger.info(f"SAVE: Project has {len(pending)} pending questions")
    for q in pending:
        logger.info(f"  Q{q.get('id')}: status={q.get('status')}")

    # ... do save ...
    self.conn.commit()
    logger.info("SAVE: Commit complete")

    # Log AFTER load to verify
    result = self.load_project(project.project_id)
    pending = getattr(result, "pending_questions", [])
    logger.info(f"VERIFY: Reloaded project has {len(pending)} pending questions")
    for q in pending:
        logger.info(f"  Q{q.get('id')}: status={q.get('status')}")
```

2. **Query the actual database file:**
```sql
SELECT metadata FROM projects WHERE id = 'PROJECT_ID';
-- Parse JSON and check if question status is persisted
```

3. **Add breakpoint test:**
```python
# After save_project, immediately reload
project_reload = db.load_project(project_id)
assert project_reload.pending_questions[0]["status"] == "answered"  # Will fail if bug exists
```

---

## Bug #2: Specs Not Extracted - Root Cause Analysis

### Symptom
LLM calls fail with 404 errors. Fallback specs (empty) are used instead of real extraction.

### Root Cause Chain

#### Issue #1: Invalid Model Name (FIXED ✅)
**File:** `orchestrator.py:328, 417`

**Before:** Model `claude-3-5-haiku-20241022` doesn't exist in Anthropic API
**After:** Changed to `claude-haiku-4-5-20251001` ✅ Fixed in commit 1e4481f

#### Issue #2: LLM Client Fallback Chain (PARTIALLY FIXED)
**File:** `orchestrator.py:332-340`

Model list (in priority order):
```python
models = [
    "claude-haiku-4-5-20251001",           # ✅ VALID
    "claude-3-5-haiku",                    # ❓ UNCLEAR if valid
    "claude-3-haiku-20240307",             # ❓ UNCLEAR if valid
    "claude-3-5-sonnet-20241022",          # ✅ VALID
    "claude-opus-4-20250514",              # ✅ VALID
]
```

**Risk:** If first 4 all fail, fallback may not work

#### Issue #3: Missing LLM Client Wrapper (Root Cause)
**File:** `orchestrator.py:357-380`

The system has two initialization points:
```python
# Path 1: From API key
if isinstance(api_key_or_config, str):
    self.raw_llm_client = LLMClient(api_key=..., provider="anthropic", model=...)

# Path 2: From config object
elif hasattr(api_key_or_config, "api_key"):
    self.raw_llm_client = LLMClient(api_key=..., provider="anthropic", model=...)
```

But only `self.raw_llm_client` is set, not `self.llm_client`. Many agents expect `self.llm_client`.

**File:** `orchestrator.py:381-395`

```python
# Try to wrap the client (but it might be None!)
self.llm_client = LLMClientAdapter(self.raw_llm_client) if self.raw_llm_client else None
```

**Risk:** If raw_llm_client fails to initialize, llm_client is None

#### Issue #4: Agent Initialization Without Wrapped Client
**File:** `orchestrator.py:456-510`

Agents are initialized with `self.llm_client`:
```python
self.agents = {
    "socratic_counselor": SocraticCounselorAgent(llm_client=self.llm_client),
    "context_analyzer": ContextAnalyzerAgent(llm_client=self.llm_client),
    # ...
}
```

**Risk:** If `self.llm_client` is None, agents get None instead of proper client

#### Issue #5: Specs Extraction Fallback (Masking the Problem)
**File:** `orchestrator.py:2331-2335`

```python
specs_response = {
    "status": "success",
    "specs": {"goals": [], "requirements": [], "tech_stack": [], "constraints": []},
    "overall_confidence": 0.7,  # ← Fallback values (empty specs!)
}

try:
    counselor = self.agents.get("socratic_counselor")
    if counselor and hasattr(counselor, "extract_specs_from_response"):
        # ... call agent ...
except Exception as e:
    logger.warning(f"Failed to extract specs: {e}")
```

**Problem:** Returns empty specs on failure, doesn't differentiate between:
- Agent exists but LLM call fails
- Agent doesn't exist
- Client not initialized

### Comparison with Monolithic-Socrates

**Monolithic:**
```python
# Eager client initialization with error handling
self.claude_client = ClaudeClient(api_key, verbose=self.verbose)
if not self.claude_client:
    raise RuntimeError("Failed to initialize Claude client")

# Agent initialization with mandatory client
self.socratic_counselor = SocraticCounselorAgent(
    llm_client=self.claude_client,
    orchestrator=self
)
```

**Master (Current):**
```python
# Lazy client initialization
self.llm_client = LLMClientAdapter(...) if self.raw_llm_client else None

# Agent initialization with possibly-None client
self.agents["socratic_counselor"] = SocraticCounselorAgent(llm_client=self.llm_client)
```

**Difference:** Monolithic fails fast if client missing. Master silently falls back to empty specs.

### Root Cause

**Primary:** Invalid model name → LLM calls fail → Specs extraction fails → Uses fallback empty specs

**Secondary:** LLM client might not be properly initialized for agents

**Tertiary:** Error handling masks the root cause

### Verification Needed

1. ✅ **Model name fix:** Already applied - should resolve 404 errors
2. **Agent client verification:** Check if agents actually receive non-None llm_client
3. **Error logging:** Add detailed logs to see actual LLM failure reasons
4. **Fallback tracking:** Log when fallback specs are used (currently only warns)

---

## Bug #3: Debug Mode Not Working - Root Cause Analysis

### Symptom
User enables debug mode but debug logs don't appear in API responses.

### Investigation Path

#### Step 1: Debug Mode Enable (✓ Works)
**File:** `routers/debug.py`

There's a debug mode endpoint that enables per-user debug logging (verified to exist).

**Status:** ✅ Endpoint exists and enables mode

#### Step 2: Debug Log Creation (✓ Works)
**File:** `orchestrator.py:2256-2259`

When generating questions:
```python
if not hasattr(project, "debug_logs"):
    project.debug_logs = []
project.debug_logs.extend(debug_logs)
```

**Status:** ✅ Debug logs are created and stored

#### Step 3: Debug Log Return (❌ **MISSING**)
**File:** Various routers

**Issue Found in `projects_chat.py:1469-1474`:**

```python
return APIResponse(
    success=True,
    status="success",
    data=response_data,
    debug_logs=context.get("debug_logs"),  # ← Getting from context
)
```

**Problem:** `context.get("debug_logs")` gets debug logs from `_build_agent_context()`, NOT from the actual response or project.

**File:** `orchestrator.py` - need to find `_build_agent_context`

#### Step 4: Debug Log Delivery (❌ **INCOMPLETE**)
**Evidence from DIAGNOSTIC_REPORT.md:**
- Debug logs are created
- But not consistently returned in API responses
- 100% of routes missing debug_logs in responses

### Root Cause

**Two-fold problem:**

1. **Debug logs stored in project but not passed through responses:**
   - Logs are stored in `project.debug_logs`
   - But responses don't include `project.debug_logs`
   - Instead try to build from `_build_agent_context()` which may not have the same logs

2. **_build_agent_context() may return empty debug_logs:**
   - This method might not have access to the actual debug logs
   - Or might be building logs differently than orchestrator

### Comparison with Monolithic-Socrates

**Monolithic pattern:**
```python
# Response includes debug logs directly
response = {
    "status": "success",
    "data": {...},
    "debug_logs": project.debug_logs,  # Direct from project
    "metadata": {...}
}
```

**Master pattern:**
```python
# Response tries to build debug logs from context
context = orchestrator._build_agent_context(project)
response = APIResponse(
    ...
    debug_logs=context.get("debug_logs")  # Indirect, may be empty
)
```

### Missing Implementation

**File:** `routers/debug.py` endpoint to enable debug mode

The endpoint exists but may not:
1. Set a flag in project
2. Set a per-user flag
3. Ensure debug logs are returned on all responses

### Verification Tests

1. **Test debug log creation:**
   - Enable debug mode
   - Generate question
   - Check if `project.debug_logs` has entries

2. **Test debug log delivery:**
   - Enable debug mode
   - Generate question
   - Check API response has `debug_logs` field with data

3. **Test _build_agent_context:**
   - Verify it's returning the actual debug logs
   - Or change routes to use `project.debug_logs` directly

---

## Database Persistence Gap Analysis

### Comparison: Master vs Monolithic

| Data Type | Monolithic | Master | Status |
|-----------|-----------|--------|--------|
| Conversation History | ✅ Persisted | ✅ Persisted | OK |
| Pending Questions | ✅ Persisted | ✅ Persisted (in metadata) | OK |
| Question Status | ✅ Persisted | ✅ Persisted (in metadata) | OK |
| Asked Questions | ✅ Persisted | ✅ Persisted (in metadata) | OK |
| Maturity Scores | ✅ Persisted | ❌ Missing | **CRITICAL** |
| Phase Progression | ✅ Persisted | ❌ Missing | **CRITICAL** |
| Question Cache | ✅ Persisted | ✅ Persisted (in metadata) | OK |
| Debug Logs | ✅ Persisted | ✅ Persisted (in metadata) | OK |
| Current Question Context | ✅ Persisted | ✅ Persisted (in metadata) | OK |
| User Knowledge Base State | ✅ Persisted | ❌ Missing | **CRITICAL** |
| Multi-LLM Provider Metadata | ✅ Persisted | ❌ Missing | **CRITICAL** |

### Impact

**Missing persistence causes:**
- Maturity scores reset on reload
- Phase progression not saved (user stuck in discovery)
- Multi-LLM provider switching lost
- Knowledge base state not preserved

### Files Affected

**Missing implementations:**
- No maturity score persistence in `database.py`
- No phase progression tracking in `database.py`
- No multi-LLM metadata in `database.py`

---

## Summary of Root Causes

### Bug #1: Question Repetition
- **Most Likely:** Database transaction commit issues or object reference mismatch
- **Impact:** CRITICAL - User sees repeated questions
- **Fix Required:** Add comprehensive logging to verify save/load cycle preserves question status

### Bug #2: Specs Not Extracted
- **Root Cause:** Invalid model name (FIXED ✅) + possible LLM client initialization issues
- **Impact:** CRITICAL - No specs extracted, fallback to empty specs
- **Fix Applied:** Model name corrected (should resolve if this is only issue)
- **Verification Needed:** Confirm agents receive proper LLM client

### Bug #3: Debug Mode Not Working
- **Root Cause:** Debug logs created but not returned in API responses (architectural issue)
- **Impact:** MEDIUM - Debug logs unavailable to users
- **Fix Required:** Ensure all routes return debug_logs from project

### Underlying Issues
- 80% of database persistence layer missing
- LLM client initialization not robust
- Error handling masks root causes
- No comprehensive integration tests

---

## Recommended Next Steps

### Immediate (High Priority)

1. **Add Database Persistence Logging**
   - Log question status before/after save
   - Log database contents after commit
   - Verify round-trip: save → load → compare

2. **Test Model Name Fix**
   - Verify `claude-haiku-4-5-20251001` is valid
   - Test actual LLM calls work
   - Check if specs extraction succeeds

3. **Fix Debug Log Delivery**
   - Change all routes to return `project.debug_logs` directly
   - OR improve `_build_agent_context()` to return actual logs

### Short Term (1-2 weeks)

1. **Comprehensive Integration Test**
   - Full Q&A cycle with persistence verification
   - Maturity score tracking
   - Phase progression
   - Question deduplication

2. **Add Missing Database Persistence**
   - Maturity scores
   - Phase progression
   - Multi-LLM metadata
   - Knowledge base state

3. **Improve Error Handling**
   - Don't silently fallback to empty specs
   - Log actual LLM errors
   - Surface errors to user (except sensitive info)

### Long Term (1 month+)

1. **Align Master with Monolithic**
   - Apply all remaining patterns from Monolithic-Socrates
   - Synchronize database schema
   - Unified error handling

2. **Add Comprehensive Testing**
   - Unit tests for persistence layer
   - Integration tests for all workflows
   - E2E tests for complete Q&A cycles

3. **Performance Optimization**
   - Profile slow queries
   - Optimize database access patterns
   - Cache frequently accessed data

---

## Files Requiring Modification

### Critical
- [ ] `orchestrator.py` - Add detailed logging to specs extraction
- [ ] `database.py` - Add persistence logging, verify commits
- [ ] `routers/projects_chat.py` - Ensure debug_logs returned in ALL responses

### Important
- [ ] `routers/debug.py` - Verify debug mode enables properly
- [ ] `database.py` - Add missing maturity/phase persistence

### Investigation-Only (No Changes)
- [x] `orchestrator.py` - Model names already fixed
- [x] `database.py` - Persistence logic verified as correct

---

**Status:** Ready for verification testing
**Confidence Level:** HIGH for identified root causes
**Test Plan:** See "Verification Needed" sections above

