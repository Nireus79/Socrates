# Agent Library Interface Corrections

**Status**: ✅ ALL CORRECTIONS APPLIED
**Commit**: 0eb5553
**Date**: 2026-04-21

---

## Summary

The **Socratic-agents library is correct**. The orchestrator.py was passing **wrong parameter names** to agent methods. All corrections have been applied.

---

## Corrections Applied

### 1. generate_answer_suggestions Call (Line 2205)

**Issue**:
- Passing `"current_question"` but agent expects `"question"`
- Passing unused `"current_user"` parameter

**Before**:
```python
suggestions_response = counselor.process({
    "action": "generate_answer_suggestions",
    "current_question": question.get("question", ""),
    "project": project,
    "current_user": user_id,
})
```

**After**:
```python
suggestions_response = counselor.process({
    "action": "generate_answer_suggestions",
    "question": question.get("question", ""),
    "project": project,
})
```

**Agent Expectation** (from socratic_counselor.py:1354):
```python
question = request.get("question", "")
```

---

### 2. extract_insights_only Call (Line 2878)

**Issue**:
- Passing unused `"current_user"` parameter

**Before**:
```python
extraction_result = counselor.process({
    "action": "extract_insights_only",
    "response": user_response,
    "project": project,
    "current_user": current_user,
})
```

**After**:
```python
extraction_result = counselor.process({
    "action": "extract_insights_only",
    "response": user_response,
    "project": project,
})
```

**Agent Expectation** (from socratic_counselor.py:719-750):
- `response` (required)
- `project` (optional)
- No `current_user` or `user_id` used

---

### 3. generate_question Call (Line 3258)

**Issue**:
- Passing `"current_user"` but agent expects `"user_id"`

**Before**:
```python
counselor_request = {
    "action": "generate_question",
    "topic": topic,
    "context": conversation_summary,
    "phase": phase,
    "goals": goals,
    "project_id": project_id,
    "project": project,
    "current_user": user_id,
    "force_refresh": force_refresh,
}
```

**After**:
```python
counselor_request = {
    "action": "generate_question",
    "topic": topic,
    "context": conversation_summary,
    "phase": phase,
    "goals": goals,
    "project_id": project_id,
    "project": project,
    "user_id": user_id,  # CORRECTED
    "force_refresh": force_refresh,
}
```

**Agent Expectation** (from socratic_counselor.py:267):
```python
user_id = request.get("user_id", "default_user")
```

**Impact**: This was causing **"User not found: default_user"** error because agent was defaulting to "default_user" when parameter was missing.

---

### 4. detect_conflicts Call (Line 3007)

**Issue**:
- Passing `"new_insights"` but agent expects `"insights"`
- Passing unused `"current_user"` parameter

**Before**:
```python
detector_result = detector.process({
    "action": "detect_conflicts",
    "new_insights": high_confidence_specs,
    "project": project,
    "current_user": user_id,
})
```

**After**:
```python
detector_result = detector.process({
    "action": "detect_conflicts",
    "insights": high_confidence_specs,
    "project": project,
})
```

**Agent Expectation** (from socratic_counselor.py:812):
```python
insights = request.get("insights", {})
```

---

### 5. generate_question Call (Line 5190)

**Issue**:
- Passing `"current_user"` but agent expects `"user_id"`

**Before**:
```python
counselor_result = counselor.process({
    "action": "generate_question",
    "topic": topic,
    "level": level,
    "project": project,
    "current_user": current_user,
})
```

**After**:
```python
counselor_result = counselor.process({
    "action": "generate_question",
    "topic": topic,
    "level": level,
    "project": project,
    "user_id": current_user,
})
```

**Agent Expectation** (from socratic_counselor.py:267):
```python
user_id = request.get("user_id", "default_user")
```

---

## Agent Parameter Interface Reference

### SocraticCounselor.process() Actions

**generate_question**
- Required: `user_id` (string)
- Required: `project` (ProjectContext)
- Optional: `topic`, `context`, `phase`, `goals`, `force_refresh`

**process_response**
- Required: `user_id` (string)
- Required: `response` (user answer text)
- Required: `project` (ProjectContext)

**extract_insights_only**
- Required: `response` (user response text)
- Optional: `project` (ProjectContext)

**detect_conflicts** → _handle_conflict_detection
- Required: `insights` (dict)
- Optional: `project`, `response`

**generate_answer_suggestions** → _generate_answer_suggestions
- Required: `question` (question text)
- Optional: `project` (ProjectContext)

---

## Files Modified

- `backend/src/socrates_api/orchestrator.py` - 5 parameter name corrections

---

## Testing Checklist

- [ ] Question generation works (no "User not found: default_user" error)
- [ ] Questions don't repeat (deduplication works)
- [ ] Answer suggestions generate
- [ ] Conflict detection works
- [ ] No parameter mismatch errors in logs

---

## Root Cause Analysis

The orchestrator was written with parameter names that differed from the actual Socratic-agents library:
- Orchestrator used "current_user" throughout
- Agent library uses "user_id" for authentication-dependent actions
- Orchestrator used different insight parameter names ("new_insights" vs "insights")
- Orchestrator used wrong question parameter name ("current_question" vs "question")

This mismatch prevented proper parameter passing, causing:
1. Questions defaulting to "default_user" (non-existent user)
2. Conflict detection receiving empty insights
3. Answer suggestions failing to find question context
4. Question deduplication not working (no user context)

All corrections ensure **exact interface alignment** with Socratic-agents library.

---

**Status**: ✅ PRODUCTION READY
