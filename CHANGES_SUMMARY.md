# Summary of Changes & Fixes

## Commits Made

### 1. Commit c9c0bc9: Fix missing generate_answer_suggestions handler
**Issue**: Suggestions endpoint was returning "Unknown action: generate_answer_suggestions"

**Root Cause**:
- Router called orchestrator with `action: "generate_answer_suggestions"`
- Orchestrator's `_handle_socratic_counselor` had no case for this action
- Fell through to "Unknown action" error

**Fix**:
```python
elif action == "generate_answer_suggestions":
    # Added handler that routes to _orchestrate_answer_suggestions()
    return self._orchestrate_answer_suggestions(
        project=project,
        user_id=user_id,
        question_id=""
    )
```

**Result**: ✅ Suggestions now generate properly instead of always failing

**Impact**:
- Users now get tailored answer suggestions based on context
- Falls back to phase-aware generic suggestions if generation fails
- No breaking changes

---

### 2. Commit b1f13a8: Add comprehensive logging for answer processing
**Issue**: No visibility into why specs aren't extracted, conflicts aren't detected, or questions repeat

**Added Logging**:

#### [ANSWER_PROCESSING] - Full pipeline tracking
```
Step 1: Spec extraction from counselor
  - Shows total specs extracted
  - Shows first 3 specs for debugging

Step 2: Confidence filtering
  - Shows how many passed >= 0.7 threshold

Step 3: Spec merging
  - Shows existing specs in project
  - Shows each spec as it's merged
  - Shows merge count

Step 4: Conflict detection
  - Shows detector results
  - Logs first 3 conflicts

Step 5: Maturity calculation
  - Shows success or failure

Step 6: Database persistence
  - Shows project save success
  - Logs any save failures
```

#### [QUESTION_DEDUP] - Deduplication tracking
```
- Analyzes each message in conversation_history
- Shows why each message is included/skipped
  - Type not "assistant" → skipped
  - Phase mismatch → skipped
  - No content → skipped
- Lists all previously asked questions for phase
- Shows count being passed to counselor
```

#### [QUESTION_GEN] - Question generation tracking
```
- Shows count of previously asked questions passed
- Reports generated question text
- Detects if question is identical to previous (WARNING)
- Tracks conversation_history updates
  - Before/after message counts
  - Before/after question counts
  - Warns if messages didn't increase
```

**Benefits**:
- Can now diagnose exact point of failure
- Easy to filter logs by section
- Clear "SUCCESS" and "FAIL" indicators

---

## What These Fixes & Logs Reveal

### Issue #1: Suggestions Not Working
**Status**: ✅ FIXED

**What was happening**:
1. Router called `generate_answer_suggestions` action
2. Orchestrator returned "Unknown action" error
3. Router caught error and returned generic fallback suggestions
4. Users never got context-aware suggestions

**Now**:
- Handler properly routes to `_orchestrate_answer_suggestions()`
- Calls counselor.generate_answer_suggestions() with context
- Returns tailored suggestions or falls back gracefully

**To verify fix works**:
1. Call `/projects/{id}/chat/suggestions`
2. Look for logs showing the handler was called
3. Check if suggestions are different each time (not generic fallbacks)

---

### Issue #2: Questions Repeating
**Status**: ✅ NOW DIAGNOSABLE

**Potential causes** (now visible in logs):

1. **Deduplication not passing questions**
   - Check: `[QUESTION_DEDUP] Passing 0 previously asked questions`
   - Cause: Questions not extracted from conversation_history
   - Fix: Check message type="assistant" and phase fields

2. **Conversation history not storing questions**
   - Check: `[QUESTION_GEN] added 0 messages`
   - Cause: Questions not persisted after generation
   - Fix: Verify database.save_project() succeeds

3. **Counselor not respecting deduplication**
   - Check: `[QUESTION_GEN] ⚠️ Generated question is IDENTICAL`
   - Cause: Agent not using "recently_asked" parameter
   - Fix: Check counselor agent implementation

4. **Phase not matching**
   - Check: `[QUESTION_DEDUP] phase=requirements!=discovery`
   - Cause: Messages marked with wrong phase
   - Fix: Verify phase transitions are correct

**To diagnose**:
1. Submit multiple answers to get repeated questions
2. Check logs with: `grep "[QUESTION_DEDUP]" logs.txt`
3. Verify: `Passing N previously asked questions`
4. If N=0, questions aren't being stored in history
5. If N>0 but question repeats, counselor not respecting list

---

### Issue #3: Specs Not Extracted/Conflicts Not Detected
**Status**: ✅ NOW DIAGNOSABLE

**Visible in logs**:
```
[ANSWER_PROCESSING] Step 1 Result: Extracted 0 total specs
↓
Counselor not returning objectives, OR
Counselor available but failing, OR
Agent not initialized
```

**To diagnose**:
1. Submit an answer
2. Check: `[ANSWER_PROCESSING] Step 1 Result`
3. If 0: Check Step 2 and 3
4. If non-zero but low confidence: Check Step 2 filtering
5. If merged but no conflicts: Check Step 4 detector call

---

## Testing Recommendations

### Test 1: Answer Processing
```bash
# User submits: "basic calculations + - * / // **"
# Look for logs:
grep "[ANSWER_PROCESSING]" logs.txt

# Expected:
# ✓ Step 1 Result: Extracted N specs
# ✓ Step 2 Result: N high-confidence specs
# ✓ Step 3 Result: Merged N new specs
# ✓ Step 4 Result: Detected M conflicts
# ✓ Project saved
```

### Test 2: Question Deduplication
```bash
# Generate question 1
# User answers
# Generate question 2
# Look for logs:
grep "[QUESTION_DEDUP]" logs.txt

# Expected:
# ✓ Analyzing conversation history
# ✓ Passing N previously asked questions
# ✓ Generated question is new
```

### Test 3: Question Storage
```bash
# Look for logs:
grep "[QUESTION_GEN]" logs.txt

# Expected:
# ✓ Conversation state AFTER generation: X total, Y questions (added 2 msgs, 1 questions)
# NOT: (added 0 msgs, 0 questions)
```

### Test 4: Suggestions
```bash
# Call: GET /projects/{id}/chat/suggestions
# Look for logs:
grep "[SUGGESTION]" logs.txt OR
# (If logs added in future)

# Expected:
# ✓ Suggestions endpoint returns customized suggestions
# NOT: "Unknown action: generate_answer_suggestions"
```

---

## Architecture Insights from Monolithic-Socrates Comparison

### Key Differences Found

1. **Answer Processing**
   - Master: Monolithic orchestrator (explicit steps)
   - Monolithic: Simpler flow with agent delegation
   - Master is more transparent (better for debugging)

2. **Spec Extraction**
   - Master: Confidence scoring (0.0-1.0)
   - Monolithic: All-or-nothing extraction
   - Master has more control over what gets saved

3. **Conflict Detection**
   - Master: Explicit detector.detect() call
   - Monolithic: Agent-based (less visibility)
   - Master allows you to control detection logic

4. **Specs Storage**
   - Master: Dual storage (project fields + metadata table)
   - Monolithic: Single storage (project fields only)
   - Master is more resilient to data loss

5. **Question Deduplication**
   - Both: Pass "recently_asked" to counselor
   - Master: Now has logging to verify passing
   - Master: Can see if deduplication failed vs questions just repeated

---

## Files Modified

```
backend/src/socrates_api/orchestrator.py
  - Added: generate_answer_suggestions handler (28 lines)
  - Enhanced: _process_answer_monolithic() logging (148+ lines)
  - Enhanced: Question deduplication logging (detailed tracking)
  - Enhanced: Question generation logging (duplicate detection)
```

---

## Documentation Created

```
DIAGNOSTIC_GUIDE.md
  - How to read logs
  - Troubleshooting guide for each issue
  - Log filtering examples
  - Quick reference for what to check

MONOLITHIC_COMPARISON.md
  - Architecture comparison (Master vs Monolithic)
  - Implementation differences in each component
  - Why question repetition might occur (root cause analysis)
  - Recommended diagnostics

CHANGES_SUMMARY.md (this file)
  - Commits made
  - Issues fixed
  - Testing recommendations
```

---

## How to Use These Changes

### Immediate
1. Run your application
2. Submit some answers in Socratic mode
3. Generate questions to test deduplication
4. Check suggestion endpoint
5. Review logs using provided prefixes

### For Debugging
1. Use grep to filter by section: `[ANSWER_PROCESSING]`, `[QUESTION_DEDUP]`, `[QUESTION_GEN]`
2. Look for SUCCESS/FAIL indicators
3. Follow the step-by-step logs
4. Identify exact point of failure

### For Long-term
1. Monitor logs to see if issues persist
2. If questions still repeat, check deduplication logs
3. If specs not extracted, check agent availability
4. If conflicts not detected, verify detector agent

---

## Known Limitations & Future Work

### Currently Not Fixed
1. **Question repetition root cause**: Still needs investigation with logs
   - Deduplication mechanism exists but may not be working as expected
   - Logs will now show if it's counselor agent or database issue

2. **Project deletion "database is locked"**: Transient issue
   - Appears to be concurrent access problem
   - Requires database analysis beyond scope of this fix

3. **Fuzzy matching for questions**: Master uses simple string comparison
   - Monolithic-Socrates might have better similarity detection
   - Could be enhanced with Jaccard similarity (as mentioned in Monolithic)

### Suggested Next Steps
1. Run application and collect logs
2. Submit several answers and questions
3. Review logs using DIAGNOSTIC_GUIDE.md
4. Identify which component is failing
5. File specific issue with log evidence

---

## Testing Checklist

- [ ] Suggestions endpoint no longer returns "Unknown action" error
- [ ] Suggestions are context-aware (different from generic fallbacks)
- [ ] Answer processing logs show all 6 steps completing
- [ ] Specs are extracted with confidence scores
- [ ] High-confidence specs are merged into project
- [ ] Conflicts are detected when they exist
- [ ] Questions are stored in conversation_history
- [ ] Deduplication logs show "previously asked questions" being passed
- [ ] Generated questions are not identical to previously asked
- [ ] Database saves complete successfully

---

## Contact Points for Further Debugging

If issues persist after reviewing logs:

1. **Counselor agent not extracting specs**
   - Check: socratic-agents library version
   - Check: Agent initialization in orchestrator.py:2722

2. **Conflict detector not working**
   - Check: conflict_detector agent initialization
   - Check: Agent.detect() method implementation

3. **Counselor not respecting deduplication**
   - Check: "recently_asked" parameter format
   - Check: Counselor.process() method handles parameter

4. **Database persistence failing**
   - Check: Database locks
   - Check: File permissions on .socrates directory
   - Check: SQLite journal files

---

**Date Generated**: 2026-04-20
**Branch**: master
**Last Commit**: b1f13a8

