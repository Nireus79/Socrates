# Method Call Mismatch Audit - Critical

**Status**: 🔴 CRITICAL - Method calls don't match Monolithic-Socrates pattern
**Date**: 2026-04-20

---

## Summary

The code is calling methods directly on agents, but Monolithic-Socrates uses **action-based dispatch through `process()`** for ALL agent communications.

**Direct method calls that should go through process()**:
- ❌ `counselor.generate_answer_suggestions()` - Should use `process({"action": "generate_answer_suggestions", ...})`
- ❌ `detector.detect()` - Should use `process({"action": "detect_conflicts", ...})`

---

## Mismatch #1: counselor.generate_answer_suggestions()

**Location**: `orchestrator.py:2188`
**Severity**: 🔴 CRITICAL

**Current Code**:
```python
counselor = self._get_agent("socratic_counselor")
if counselor and hasattr(counselor, "generate_answer_suggestions"):
    suggestions_response = counselor.generate_answer_suggestions(
        question=question.get("question", ""),
        project_context=self._get_extracted_specs(project),
        phase=context["phase"],
        user_role=context["user_role"],
        recent_messages=context.get("recent_messages", []),
        diversity_emphasis=True,
    )
```

**Problem**:
- Calling direct method `generate_answer_suggestions()` on counselor
- This method doesn't exist in Monolithic-Socrates pattern
- In Monolithic-Socrates, it's accessed through: `counselor.process({"action": "generate_answer_suggestions", ...})`
- Current code will get `AttributeError: 'SocraticCounselor' object has no attribute 'generate_answer_suggestions'`

**Monolithic-Socrates Implementation**:
```python
def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
    action = request.get("action")

    # ...
    elif action == "generate_answer_suggestions":
        return self._generate_answer_suggestions(request)  # Private method!

    return {"status": "error", "message": "Unknown action"}
```

**Correct Code Should Be**:
```python
counselor = self._get_agent("socratic_counselor")
if counselor:
    suggestions_response = counselor.process({
        "action": "generate_answer_suggestions",
        "current_question": question.get("question", ""),
        "project": project,
        "current_user": user_id,
    })
```

---

## Mismatch #2: detector.detect()

**Location**: `orchestrator.py:2988`
**Severity**: 🔴 CRITICAL

**Current Code**:
```python
detector_result = detector.detect({
    "specs": high_confidence_specs,
    "existing_goals": getattr(project, "goals", []),
    "existing_requirements": getattr(project, "requirements", []),
    "existing_tech_stack": getattr(project, "tech_stack", []),
    "context": project
})
```

**Problem**:
- Calling direct method `detect()` on detector
- This method doesn't exist in Monolithic-Socrates pattern
- In Monolithic-Socrates, it's accessed through: `detector.process({"action": "detect_conflicts", ...})`
- Current code will get `AttributeError: 'ConflictDetector' object has no attribute 'detect'`

**Monolithic-Socrates Implementation**:
```python
def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
    action = request.get("action")

    if action == "detect_conflicts":
        return self._detect_conflicts(request)
    elif action == "resolve_conflict":
        return self._resolve_conflict(request)
    elif action == "get_suggestions":
        return self._get_conflict_suggestions(request)

    return {"status": "error", "message": "Unknown action"}
```

**Correct Code Should Be**:
```python
detector_result = detector.process({
    "action": "detect_conflicts",
    "new_insights": high_confidence_specs,
    "project": project,
    "current_user": current_user,
})
```

---

## Agent Interface Pattern (Monolithic-Socrates)

### ALL agents follow this pattern:

```python
class SomeAgent(Agent):
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to action handlers"""
        action = request.get("action")

        if action == "action_one":
            return self._action_one(request)
        elif action == "action_two":
            return self._action_two(request)
        # ... more actions ...

        return {"status": "error", "message": "Unknown action"}

    def _action_one(self, request):
        # Private implementation
        pass
```

### Key Rules:

1. **NO public methods** - All agent methods are private (prefixed with `_`)
2. **ALL communication goes through `process()`** - Agents only have one public method
3. **Every call must include "action" key** - Tells agent which handler to invoke
4. **Request structure varies by action** - Each action expects different parameters

---

## All Supported Actions by Agent Type

### SocraticCounselor.process() Actions:
```
✓ generate_question
✓ process_response
✓ extract_insights_only
✓ advance_phase
✓ rollback_phase
✓ explain_document
✓ generate_hint
✓ toggle_dynamic_questions
✓ answer_question
✓ skip_question
✓ reopen_question
✓ generate_answer_suggestions    ← Line 2188 tries direct method
```

### ConflictDetector.process() Actions:
```
✓ detect_conflicts              ← Line 2988 tries detector.detect()
✓ resolve_conflict
✓ get_suggestions
```

---

## Files Affected

### `orchestrator.py`

| Line | Current Call | Type | Fix |
|------|--------------|------|-----|
| 2188 | `counselor.generate_answer_suggestions(...)` | Direct method | Change to `process()` |
| 2988 | `detector.detect(...)` | Direct method | Change to `process()` |

---

## Verification Against Monolithic-Socrates

**Monolithic-Socrates Implementation Check**:
✅ SocraticCounselor - All methods private (_generate_question, _extract_insights_only, etc.)
✅ ConflictDetector - All methods private (_detect_conflicts, _resolve_conflict, etc.)
✅ All agent communication through `process()` with "action" dispatch
✅ No direct public method calls on agents

---

## Architecture: Why This Pattern?

```
┌─ AGENT INTERNAL STATE
│  ├─ Settings
│  ├─ Cache
│  └─ Initialized resources
│
├─ process() METHOD (Public)
│  │  ├─ Validates request
│  │  ├─ Dispatches to action handler
│  │  └─ Returns standardized response
│  │
│  └─ Private action methods (_handler_one, _handler_two, ...)
│     ├─ Each handles one action
│     └─ Can access internal state
│
└─ EXTERNAL CALLERS
   ├─ MUST use process()
   ├─ MUST include "action" key
   └─ CANNOT call private methods
```

This pattern ensures:
- **Encapsulation** - Internal state protected
- **Consistent interface** - All agents work the same way
- **Action dispatch** - Easy to extend with new actions
- **Error handling** - Centralized in process()

---

## Impact

These method call mismatches will cause:

1. **Line 2188**: `AttributeError` when suggesting answers
   - Suggestions feature completely broken
   - Will fail with: "SocraticCounselor has no attribute 'generate_answer_suggestions'"

2. **Line 2988**: `AttributeError` when detecting conflicts
   - Conflict detection completely broken
   - Will fail with: "ConflictDetector has no attribute 'detect'"

Both are CRITICAL failures that prevent core functionality.

---

## Root Cause

Master branch was written against a different interface where agents had public methods. When integrating with Monolithic-Socrates (which uses action-based dispatch), these direct method calls became invalid.

---

## Prevention

**For all agent calls**:
1. Check the agent's `process()` method signature in Monolithic-Socrates
2. Get the list of supported actions
3. Call `agent.process({"action": "action_name", ...})`
4. NEVER call methods directly on agents

**No direct method calls** - Only `process()` dispatch is allowed.

