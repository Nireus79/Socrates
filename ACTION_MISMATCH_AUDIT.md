# Action Name Mismatch Audit - Complete

**Status**: 🔴 CRITICAL MISMATCHES FOUND
**Date**: 2026-04-20

---

## Fixed Mismatch

### ✅ Fixed: extract_learning_objectives → extract_insights_only
- **Location**: `orchestrator.py:2746`
- **Status**: FIXED in commit b6004f0
- **Impact**: Answer extraction now works correctly

---

## CRITICAL MISMATCHES FOUND

### 🔴 MISMATCH #1: Missing "action" Key in Question Generation

**Location**: `orchestrator.py:3318`
**Severity**: 🔴 CRITICAL

**Current Code**:
```python
counselor_request = {
    "topic": topic,
    "context": conversation_summary,
    "phase": phase,
    "goals": goals,
    "project_id": project_id,
    "project": project,
    "user_id": user_id,
    "force_refresh": force_refresh,
    # ... more fields ...
}

result = breaker.call(counselor.process, counselor_request)  # ❌ NO ACTION
```

**Problem**:
- Counselor.process() expects `request.get("action")` to match a handler
- This request has NO "action" key
- Counselor will get `action = None` and return `{"status": "error", "message": "Unknown action"}`

**Expected Code**:
```python
counselor_request = {
    "action": "generate_question",  # ✅ MUST HAVE THIS
    "topic": topic,
    "context": conversation_summary,
    ...
}
```

**Fix**: Add `"action": "generate_question"` to counselor_request before passing to counselor.process()

---

### 🔴 MISMATCH #2: Missing "action" Key in Deduplication

**Location**: `orchestrator.py:5165`
**Severity**: 🔴 CRITICAL

**Current Code**:
```python
counselor_result = counselor.process({"topic": topic, "level": level})  # ❌ NO ACTION
```

**Problem**:
- Missing "action" parameter entirely
- Counselor returns error

**Expected Code**:
```python
counselor_result = counselor.process({
    "action": "generate_question",  # ✅ MISSING
    "topic": topic,
    "level": level
})
```

**Fix**: Add `"action": "generate_question"` parameter

---

## Supported Actions (From Monolithic-Socrates)

```python
✓ generate_question        - Generate Socratic question
✓ process_response         - Process user answer
✓ extract_insights_only    - Extract specs without processing
✓ advance_phase            - Move to next phase
✓ rollback_phase           - Return to previous phase
✓ explain_document         - Explain document content
✓ generate_hint            - Generate hint for current question
✓ toggle_dynamic_questions - Enable/disable dynamic mode
✓ answer_question          - Record answer to question
✓ skip_question            - Skip a question
✓ reopen_question          - Recover skipped question
✓ generate_answer_suggestions - Generate answer suggestions
```

---

## All Action Calls in Codebase

### SocraticCounselor Actions (Should Match Supported List)
| Line | Action | Status | Status |
|------|--------|--------|--------|
| 2859 | `extract_insights_only` | ✅ Supported | ✅ CORRECT |
| 3318 | `(missing)` | ❌ Missing | 🔴 CRITICAL |
| 5165 | `(missing)` | ❌ Missing | 🔴 CRITICAL |

### Other Agent Actions (Different Agents)
| Location | Action | Agent | Status |
|----------|--------|-------|--------|
| 767 | `check` | CodeQualityAgent | Unknown |
| 780 | `detect_weak_areas` | CodeAnalyzer | Unknown |
| 1144 | `record` | InteractionTracker | Unknown |
| 1157 | `analyze` | ContextAnalyzer | Unknown |
| 1171 | `create` | ProjectManager | Unknown |
| 1275 | `store` | KnowledgeManager | Unknown |
| 1295 | `search` | KnowledgeSearcher | Unknown |
| 4540 | `analyze` | ContentAnalyzer | Unknown |

---

## Action Pattern Violations

### Pattern: Monolithic-Socrates expects "action" in all counselor.process() calls

❌ **Violations Found**:
1. Line 3318 - counselor.process() called without "action" key
2. Line 5165 - counselor.process() called without "action" key

✅ **Correct Usage**:
1. Line 2859 - `"action": "extract_insights_only"` - CORRECT

---

## Required Fixes

### Fix Mismatch #1: Add action to question generation (Line 3318)

```python
# BEFORE (WRONG):
counselor_request = {
    "topic": topic,
    "context": conversation_summary,
    "phase": phase,
    # ... more fields ...
}
result = breaker.call(counselor.process, counselor_request)

# AFTER (CORRECT):
counselor_request = {
    "action": "generate_question",  # ✅ ADD THIS
    "topic": topic,
    "context": conversation_summary,
    "phase": phase,
    # ... more fields ...
}
result = breaker.call(counselor.process, counselor_request)
```

**Location to insert**: Between line 3229 and 3238 (at start of counselor_request dict creation)

---

### Fix Mismatch #2: Add action to deduplication (Line 5165)

```python
# BEFORE (WRONG):
counselor_result = counselor.process({"topic": topic, "level": level})

# AFTER (CORRECT):
counselor_result = counselor.process({
    "action": "generate_question",  # ✅ ADD THIS
    "topic": topic,
    "level": level
})
```

---

## Why These Are Critical

The counselor.process() method uses this pattern:

```python
def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
    action = request.get("action")  # ← Gets None if not provided

    if action == "generate_question":
        return self._generate_question(request)
    elif action == "process_response":
        return self._process_response(request)
    # ... more actions ...

    return {"status": "error", "message": "Unknown action"}  # ← Returns error
```

When "action" key is missing:
1. `action = request.get("action")` returns `None`
2. None doesn't match any `if/elif` condition
3. Falls through to final `return` with error
4. Calling code gets `{"status": "error", "message": "Unknown action"}`

---

## Prevention Strategy

### For Future Development:

1. **Always verify action exists** before calling agent.process()
2. **Use checklist when calling counselor**:
   - [ ] Is "action" key present?
   - [ ] Is action value one of the supported actions?
   - [ ] Does the request have all required parameters for that action?

3. **Recommended validation function**:
```python
def validate_counselor_request(request: Dict) -> Tuple[bool, str]:
    """Validate counselor request has required action"""
    SUPPORTED_ACTIONS = {
        "generate_question": ["topic", "project"],
        "process_response": ["response", "project"],
        "extract_insights_only": ["text", "project"],
        # ... etc ...
    }

    action = request.get("action")
    if not action:
        return False, "Missing required 'action' key"

    if action not in SUPPORTED_ACTIONS:
        return False, f"Unknown action: {action}"

    required = SUPPORTED_ACTIONS[action]
    for param in required:
        if param not in request:
            return False, f"Missing required parameter: {param}"

    return True, ""
```

---

## Testing Checklist

- [ ] Question generation (Line 3318) works with "action" key
- [ ] Deduplication (Line 5165) works with "action" key
- [ ] No "Unknown action" errors in logs
- [ ] Questions are actually generated (not errors)

---

## Summary

| Mismatch | Type | Location | Severity | Status |
|----------|------|----------|----------|--------|
| extract_learning_objectives | Wrong action name | 2746 | 🔴 CRITICAL | ✅ FIXED |
| Missing action in generate | Missing key | 3318 | 🔴 CRITICAL | ❌ NOT FIXED |
| Missing action in dedup | Missing key | 5165 | 🔴 CRITICAL | ❌ NOT FIXED |

**Total Critical Issues**: 3 (1 fixed, 2 remaining)

