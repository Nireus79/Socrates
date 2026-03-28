# Direct Mode Analysis & Implementation Plan

**Status**: Bug Found & Fix Ready
**Date**: 2026-03-28

---

## The Problem

Direct Mode in `projects_chat.py` (send_message endpoint) tries to call:

```python
# Line 707
answer = orchestrator.claude_client.generate_response(
    prompt, user_auth_method=user_auth_method, user_id=current_user
)

# Line 733
insights = orchestrator.claude_client.extract_insights(
    combined_text,
    project,
    user_auth_method=user_auth_method,
    user_id=current_user
)
```

**Issue**: `orchestrator.claude_client` doesn't exist!
- The orchestrator has `self.llm_client` (LLMClient from socrates_nexus)
- There is no `claude_client` attribute on orchestrator
- Direct Mode is completely broken and cannot generate responses

**Impact**:
- Users cannot use Direct Mode at all
- Any attempt to use Direct Mode fails
- Specs extraction doesn't work
- No responses are generated

---

## How Direct Mode Should Work

### Current Intent (from code):
1. User asks a question in Direct Mode
2. System generates direct answer (not Socratic)
3. System extracts specs from question + answer
4. User can save specs to project
5. Response includes extracted specs

### What Actually Happens:
1. User asks a question in Direct Mode
2. Code tries to call `orchestrator.claude_client.generate_response()`
3. **AttributeError: 'APIOrchestrator' object has no attribute 'claude_client'**
4. Request fails with 500 error
5. User gets error message, no response

---

## The Solution

### Step 1: Fix the Direct Mode Implementation

Replace direct calls to non-existent `claude_client` with proper orchestrator handler.

**File**: `projects_chat.py` lines 707-738

**Replace This**:
```python
answer = orchestrator.claude_client.generate_response(
    prompt, user_auth_method=user_auth_method, user_id=current_user
)

# ... later ...

insights = orchestrator.claude_client.extract_insights(
    combined_text,
    project,
    user_auth_method=user_auth_method,
    user_id=current_user
)
```

**With This**:
```python
# Use orchestrator to generate direct answer
result = orchestrator.process_request(
    "direct_chat",
    {
        "action": "generate_answer",
        "prompt": prompt,
        "user_id": current_user,
        "project": project,
    }
)

if result.get("status") != "success":
    raise HTTPException(status_code=500, detail=result.get("message", "Failed to generate answer"))

answer = result.get("data", {}).get("answer", "")

# Extract insights from answer
insights = None
try:
    insights_result = orchestrator.process_request(
        "direct_chat",
        {
            "action": "extract_insights",
            "text": f"User Input:\n{request.message}\n\nAssistant Answer:\n{answer}",
            "project": project,
            "user_id": current_user,
        }
    )

    if insights_result.get("status") == "success":
        insights = insights_result.get("data", {})
except Exception as e:
    logger.warning(f"Failed to extract insights: {e}")
    insights = None
```

### Step 2: Add Direct Chat Handler to Orchestrator

**File**: `orchestrator.py`

Add new method `_handle_direct_chat()` to process Direct Mode requests.

**Handler Features**:
- Generate answer to user question
- Use per-user API key (like Socratic Mode does)
- Fall back to global API key
- Extract insights from Q&A
- Return formatted response

### Step 3: Integrate Per-User API Keys

Direct Mode should use the same per-user API key infrastructure as Socratic Mode:
- Look up user's API key from database
- Create per-user LLMClient if available
- Fall back to server key
- Proper error handling

---

## Implementation Details

### What Needs to Be Added

**File: orchestrator.py**

Add handler:
```python
def _handle_direct_chat(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle direct chat mode requests"""
    action = request_data.get("action", "")

    if action == "generate_answer":
        # Generate direct answer using user's API key if available
        # Similar to socratic question generation

    elif action == "extract_insights":
        # Extract specs from text using user's API key if available
        # Return: goals, requirements, tech_stack, constraints

    else:
        return {"status": "error", "message": f"Unknown action: {action}"}
```

Add to `process_request()` method:
```python
elif router_name == "direct_chat":
    return self._handle_direct_chat(request_data)
```

**File: projects_chat.py**

Update lines 707-738 to use orchestrator handlers instead of direct calls.

---

## Why This Matters

1. **User Experience**: Direct Mode is currently completely broken
2. **API Key Support**: Direct Mode will now respect per-user API keys
3. **Consistency**: Direct Mode will work the same way as Socratic Mode
4. **Robustness**: Proper error handling and fallbacks
5. **Maintainability**: Single source of truth for LLM calls

---

## Testing Plan

### Unit Tests Needed
1. Generate answer with user API key
2. Generate answer without user API key (fallback)
3. Extract insights from text
4. Error handling for invalid input
5. Integration with per-user API keys

### Manual Tests
1. User in Direct Mode with their own API key
2. User in Direct Mode without API key (uses server)
3. Specs extraction works
4. Save specs to project works
5. No 500 errors

---

## Code Changes Summary

| File | Changes | Lines |
|------|---------|-------|
| orchestrator.py | Add _handle_direct_chat() | ~80 |
| projects_chat.py | Update Direct Mode to use handlers | ~30 |
| **Total** | | **~110** |

---

## Implementation Order

1. ✅ Add `_handle_direct_chat()` method to orchestrator
2. ✅ Integrate per-user API key lookup
3. ✅ Create LLMClient for user if key available
4. ✅ Generate answer and extract insights
5. ✅ Update projects_chat.py to use handler
6. ✅ Add error handling
7. ✅ Test everything
8. ✅ Commit changes

---

## Before vs After

### Before (Broken)
```
User asks in Direct Mode
  ↓
Code calls orchestrator.claude_client (doesn't exist)
  ↓
AttributeError
  ↓
500 Server Error
  ↓
User sees error
```

### After (Fixed)
```
User asks in Direct Mode
  ↓
Code calls orchestrator.process_request("direct_chat", {...})
  ↓
Handler looks up user's API key
  ↓
Creates per-user LLMClient or uses server key
  ↓
Generates answer and extracts specs
  ↓
Returns formatted response
  ↓
User gets answer + specs
```

---

## Success Criteria

- ✅ Direct Mode generates answers (no 500 errors)
- ✅ Uses per-user API keys when available
- ✅ Falls back to server key when needed
- ✅ Extracts specs from Q&A
- ✅ All tests pass
- ✅ No breaking changes
- ✅ Backward compatible

---

**Ready to implement!**
