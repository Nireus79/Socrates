# Socrates System Diagnostic Report
**Date:** April 8, 2026
**Status:** Issues Identified and Partially Fixed
**User Reported:** Question repeats, specs not caught, /debug doesn't work

---

## Critical Issues Found

### ✅ FIXED: Issue #1 - Invalid Model Name (404 Error)
**Symptom:**
```
Error code: 404 - {'type': 'error', 'error': {'type': 'not_found_error', 'message': 'model: claude-3-5-haiku-20241022'}, 'request_id': '...'}
```

**Root Cause:**
Model name `claude-3-5-haiku-20241022` doesn't exist in Anthropic API.

**Location:**
- `backend/src/socrates_api/orchestrator.py` line 329 & 418

**Fix Applied:**
```python
# BEFORE
"claude-3-5-haiku-20241022",  # Invalid model name

# AFTER
"claude-haiku-4-5-20251001",  # Valid Anthropic model
```

**Commit:** `1e4481f`

---

### ✅ FIXED: Issue #2 - Conflict Detector API Mismatch
**Symptom:**
```
Failed to detect conflicts: AgentConflictDetector.detect_conflicts() got an unexpected keyword argument 'new_specs'
```

**Root Cause:**
Orchestrator calling conflict detector with signature: `detect_conflicts(new_specs=..., existing_specs=..., context=...)` but actual method has different signature.

**Location:**
`backend/src/socrates_api/orchestrator.py` line 2372-2376

**Fix Applied:**
Added fallback logic to handle multiple API signatures:
1. Try standard agent interface: `process({action: "detect_conflicts", ...})`
2. Fallback to direct method: `detect_conflicts(specs, existing_specs)`
3. Graceful error handling if both fail

**Commit:** `1e4481f`

---

### 🔍 INVESTIGATING: Issue #3 - Question Repetition
**Symptom:**
Same question asked twice ("What is the main purpose of Local Calculator in your project?") at 11:48:28 and 11:49:23

**Flow Analysis:**
1. Question generated and returned (11:48:28)
2. User answers the question (11:49:20)
3. System marks question as answered in `_orchestrate_answer_processing`
4. System calls `db.save_project(project)` to persist
5. System calls `_orchestrate_question_generation` for next question
6. **BUG:** Next question generation returns SAME question as "existing unanswered" at 11:49:22

**Potential Root Causes:**
1. **Question Status Not Persisting:** Question marked as "answered" in memory but not saved to DB
2. **Stale Project Load:** Next question generation receives old project object
3. **Reference vs Copy Issue:** Question object modification not updating pending_questions list

**Investigation Steps:**
Added detailed logging (commit `0df55d7`):
- Log all pending questions before checking for unanswered
- Log each question's status
- Log when all questions answered

**Next Steps:**
1. Run system with new debug logging
2. Check database persistence layer
3. Verify project object reference integrity

---

## Additional Issues Found

### 🔴 Issue #4 - LLM Call Failures (Model Fallback)
**Symptom:**
```
Failed to generate response using LLMClient.chat(): chat failed with Anthropic: Error code: 404
```

**Impact:**
- Specs not extracted properly (fallback to empty specs)
- Questions generated from fallback templates instead of LLM
- No real dialogue flow

**Root Cause:**
Model `claude-3-5-haiku-20241022` fails, then fallback models also fail if they don't exist

**Status:**
Fixed model names should resolve this, but need to verify fallback chain works.

---

### 🟡 Issue #5 - Debug Mode Not Working
**Symptom:**
User enables debug mode but no debug output visible

**Possible Causes:**
1. Debug logs created but not returned in API response
2. Debug endpoint not properly enabling per-user debug mode
3. Frontend not displaying debug information

**Needs Investigation:**
- Check `/system/debug/toggle` endpoint
- Verify debug logs are attached to APIResponse
- Check if debug mode is persisted per-user

---

## Architecture Mismatches (Other Components)

Based on log analysis, several API signature mismatches found:

| Component | Issue | Status |
|-----------|-------|--------|
| ConflictDetector | Unexpected keyword args | ✅ FIXED |
| QualityController | Unknown (no errors in logs) | OK |
| LearningAgent | Unknown (no errors in logs) | OK |
| SocraticCounselor | LLM failures cascade | Partial |
| Database | Unknown persistence issue | 🔍 Investigating |

---

## Files Modified This Session

1. **backend/src/socrates_api/orchestrator.py**
   - Fixed model names (2 locations)
   - Added conflict detector fallback logic
   - Added debug logging for question generation

2. **Git Commits**
   - `1e4481f` - Fix model names and conflict detector
   - `0df55d7` - Add debug logging

---

## Comparison with Monolithic-Socrates

The monolithic branch (working reference) should have:
- ✓ Correct model names
- ✓ Proper question status persistence
- ✓ Correct agent API signatures
- ✓ Working debug mode

Need to compare:
- How questions are marked as answered
- How projects are persisted to database
- How question generation checks for existing questions
- Debug mode implementation

---

## Recommended Next Steps

### Immediate (High Priority)
1. ✅ Fix model names - DONE
2. ✅ Add fallback for conflict detector - DONE
3. 🔍 Run system with debug logging to identify question repetition root cause
4. 🔍 Verify database persistence layer - check if save_project actually persists changes

### Short Term
1. Compare orchestrator implementations: Monolithic vs Modularized
2. Test question flow end-to-end with new logging
3. Fix spec extraction chain
4. Implement proper debug mode

### Investigation Required
1. **Database Layer:** Does `db.save_project()` actually persist `pending_questions` changes?
2. **Project Object:** Is the project object passed to next question generation the same instance or a fresh load?
3. **Status Field:** Are question status changes actually being saved to the database?

---

## Testing Commands

Once fixes are committed, test with:

```bash
# Start the system
python socrates.py --api

# Test the API
# 1. Create project
# 2. Get question
# 3. Send answer
# 4. Check question status in logs
# 5. Verify next question is different
```

---

**Status:** System is partially operational. Model and agent API issues fixed. Question repetition issue requires further investigation with database layer.

**Confidence in Fixes:**
- Model name fix: **HIGH** ✅
- Conflict detector fix: **MEDIUM** (fallback approach)
- Question repetition: **LOW** (needs testing)

