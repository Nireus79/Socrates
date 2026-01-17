# Suggestions Feature - Debug Analysis

## Problem Summary
The suggestions modal opens and loads the current question, but suggested answers are not being generated. Instead, generic fallback suggestions appear.

## Root Cause Analysis

### Code Flow Diagnosis

#### 1. **Frontend to Backend Call (✓ Working)**
- `AnswerSuggestionsModal.tsx` opens correctly
- API call: `GET /projects/{projectId}/chat/suggestions`
- API endpoint responds with suggestions

#### 2. **Backend Logic (⚠️ Potential Issues)**

**File:** `socrates-api/src/socrates_api/routers/projects_chat.py` (lines 1511-1603)

```python
# Step 1: Check for current unanswered question
if project.pending_questions:
    unanswered = [q for q in project.pending_questions if q.get("status") == "unanswered"]
    if unanswered:
        current_question = unanswered[0].get("question")
```

**Possible Issue #1: Empty pending_questions**
- If `project.pending_questions` is empty or None → returns generic suggestions
- `pending_questions` should be populated when `_generate_question()` is called
- But might not be initialized properly or not saved

**Possible Issue #2: No unanswered questions**
- All questions might be marked as "answered" or "skipped"
- Status tracking might be broken

```python
# Step 2: Call orchestrator to generate suggestions
result = orchestrator.process_request(
    "socratic_counselor",
    {
        "action": "generate_answer_suggestions",
        "project": project,
        "current_question": current_question,
    },
)
```

**Possible Issue #3: Orchestrator doesn't pass user info**
- Request doesn't include `current_user`
- Claude client might fail when loading user auth method
- Exception caught silently, returns generic suggestions

**Possible Issue #4: Claude API call fails**
- `_generate_answer_suggestions()` calls Claude API (line 1615)
- If Claude fails or doesn't respond, exception is caught
- Returns generic suggestions without logging details

**Possible Issue #5: Response parsing fails**
- Claude response parsing (lines 1625-1630) might not match the format Claude returns
- Numbered list parsing might fail if format is different

```python
# Returns generic suggestions if any error occurs
if result.get("status") != "success":
    return APIResponse(
        success=True,
        status="success",
        data={
            "suggestions": [
                "Consider the problem from your target audience's perspective",
                # ... 4 more generic suggestions
            ],
```

**Problem:** Status always shows "success=True" even when generic fallbacks are used
- Frontend can't tell if real or fallback suggestions
- No way to debug what went wrong

## How to Identify the Issue

### Debug Steps

1. **Check if pending_questions exists:**
   ```bash
   # Look at a project's database
   python -c "
   from socratic_system.database import ProjectDatabase
   db = ProjectDatabase()
   p = db.load_project('YOUR_PROJECT_ID')
   print('pending_questions:', p.pending_questions)
   "
   ```

2. **Check server logs for errors:**
   ```bash
   tail -f socratic_logs/socratic.log | grep -i "suggestion\|error"
   ```

3. **Add temporary logging to the API:**
   - Add print statements in `get_answer_suggestions()`
   - Check what `current_question` value is
   - Check what the orchestrator returns

4. **Test the counselor directly:**
   ```python
   from socratic_system.agents import SocraticCounselorAgent
   from socratic_system.orchestration.orchestrator import AgentOrchestrator

   orchestrator = AgentOrchestrator("your-api-key")
   result = orchestrator.socratic_counselor.process({
       "action": "generate_answer_suggestions",
       "project": project,
       "current_question": "What is your project goal?",
       "current_user": "user123"
   })
   print(result)
   ```

## Solutions

### Quick Fix (Short-term)

**Issue:** API endpoint doesn't pass `current_user` to the counselor

**Location:** `socrates-api/src/socrates_api/routers/projects_chat.py` line 1559

**Current Code:**
```python
result = orchestrator.process_request(
    "socratic_counselor",
    {
        "action": "generate_answer_suggestions",
        "project": project,
        "current_question": current_question,  # Missing current_user!
    },
)
```

**Fixed Code:**
```python
result = orchestrator.process_request(
    "socratic_counselor",
    {
        "action": "generate_answer_suggestions",
        "project": project,
        "current_question": current_question,
        "current_user": current_user,  # ADD THIS
    },
)
```

### Better Error Handling (Medium-term)

**Issue:** Errors are silently swallowed, returning generic suggestions

**Add explicit logging:**
```python
# In API endpoint
if result.get("status") != "success":
    logger.error(f"Suggestion generation failed: {result.get('message', 'Unknown error')}")
    # Add flag to response so frontend can detect
    return APIResponse(
        success=True,
        status="success",
        data={
            "suggestions": [...],
            "generated": False,  # NEW: indicates these are fallback suggestions
            "reason": result.get("message", "Generation failed"),
        },
    )
```

**Or in the counselor:**
```python
# In _generate_answer_suggestions
except Exception as e:
    logger.error(f"Claude API call failed: {type(e).__name__}: {e}")  # More detailed
    # Return error instead of silently falling back
    return {
        "status": "error",
        "message": f"Suggestion generation failed: {str(e)}",
        "suggestions": [...]  # Include fallback
    }
```

### Proper Solution (Long-term)

1. **Ensure pending_questions is initialized:**
   - Check that question generation properly adds to `pending_questions`
   - Verify questions are saved to database

2. **Add detailed logging:**
   - Log when suggestions are requested
   - Log what question is found
   - Log Claude API calls and responses
   - Log parsing results

3. **Improve error visibility:**
   - Return proper error responses instead of silent fallbacks
   - Add `generated: boolean` flag to response
   - Include reason/error message in response

4. **Add response validation:**
   - Validate Claude's response format before parsing
   - Better handle edge cases (empty response, malformed numbering, etc.)

## Testing Checklist

- [ ] Verify `pending_questions` is populated after asking a question
- [ ] Check that unanswered questions are found correctly
- [ ] Test Claude API response parsing with various formats
- [ ] Verify `current_user` is passed through the chain
- [ ] Check server logs for errors during suggestion generation
- [ ] Test with both dynamic and static questions
- [ ] Test when no current question exists (should show generic suggestions)
- [ ] Verify suggestion parsing handles different numbering formats

## Files to Check/Fix

1. ✓ `socrates-api/src/socrates_api/routers/projects_chat.py` (line 1559) - **NEEDS FIX**
2. `socratic_system/agents/socratic_counselor.py` (lines 1576-1659) - add logging
3. `socrates-frontend/src/pages/chat/ChatPage.tsx` - optionally show error/fallback indicator
4. Server logs - check for actual errors being thrown

## Recommended Next Steps

1. **First:** Fix the `current_user` parameter not being passed
2. **Then:** Add logging to understand what's happening
3. **Finally:** Improve error handling and response structure
