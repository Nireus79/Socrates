# Modular Architecture Fix Proposal

**Scope**: Fixing context passing and response completeness issues
**Estimated Impact**: Affects 11 router files, 29 route handlers
**Estimated Lines of Change**: ~200-300 lines across the codebase
**Backward Compatibility**: Fully compatible - response envelope change only

---

## Part 1: Orchestrator Enhancements

### 1.1 Add Context Builder Method

**File**: `backend/src/socrates_api/orchestrator.py`

```python
def _build_agent_context(self, project, conversation_only=False):
    """
    Build complete context for agent requests.

    Ensures agents have access to:
    - Full project object
    - Extracted conversation history
    - Conversation summary
    - Debug logs for response inclusion

    Args:
        project: Project object loaded from database
        conversation_only: If True, only return conversation data (for stateless operations)

    Returns:
        Dictionary with keys: project, conversation_history, conversation_summary, debug_logs
    """
    conversation_history = getattr(project, "conversation_history", []) or []
    conversation_summary = self._generate_conversation_summary(project) if conversation_history else ""
    debug_logs = getattr(project, "debug_logs", []) or []

    context = {
        "project": project,
        "conversation_history": conversation_history,
        "conversation_summary": conversation_summary,
        "debug_logs": debug_logs,
    }

    return context if not conversation_only else {
        "conversation_history": conversation_history,
        "conversation_summary": conversation_summary,
    }

def _generate_conversation_summary(self, project):
    """
    Generate a summary of the conversation for agent context.

    This should be fast and non-blocking.
    """
    if not hasattr(project, "conversation_history") or not project.conversation_history:
        return ""

    # Get last 5 exchanges (or less if fewer exist)
    recent = project.conversation_history[-10:] if len(project.conversation_history) > 10 else project.conversation_history

    summary_parts = []
    for item in recent:
        if isinstance(item, dict):
            if "type" in item and item["type"] == "question":
                summary_parts.append(f"Q: {item.get('content', '')[:100]}")
            elif "type" in item and item["type"] == "answer":
                summary_parts.append(f"A: {item.get('content', '')[:100]}")

    return " | ".join(summary_parts)
```

### 1.2 Add Response Wrapper Utility

**File**: `backend/src/socrates_api/utils/response_utils.py` (NEW)

```python
"""Utilities for wrapping agent responses with debug information."""

from typing import Any, Dict, List, Optional


def wrap_agent_response(
    agent_result: Dict[str, Any],
    debug_logs: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Wrap an agent response to include debug information.

    Ensures all API responses have consistent structure:
    - status: success/error
    - data: the actual result
    - debug_logs: list of debug entries
    - metadata: any additional metadata from agent

    Args:
        agent_result: Result dictionary from agent.process()
        debug_logs: Optional list of debug log entries

    Returns:
        Wrapped response with debug_logs included
    """
    return {
        "status": agent_result.get("status", "error"),
        "data": agent_result.get("data", {}),
        "debug_logs": debug_logs or [],
        "metadata": agent_result.get("metadata", {}),
        "message": agent_result.get("message", "")
    }


def extract_debug_logs(context: Dict[str, Any]) -> List[Dict]:
    """
    Extract debug logs from context object.

    Args:
        context: Context dictionary from _build_agent_context

    Returns:
        List of debug log entries
    """
    return context.get("debug_logs", [])
```

### 1.3 Create Handler Method Pattern

**File**: `backend/src/socrates_api/orchestrator.py`

Add these handler methods to the Orchestrator class:

```python
def _handle_socratic_counselor(self, request_data):
    """
    Handle SocraticCounselor requests with full context.

    Ensures:
    - Conversation history is passed
    - Conversation summary is provided
    - Debug logs are tracked
    """
    project = request_data.get("project")
    if not project:
        return {"status": "error", "message": "Project required"}

    # Build complete context
    context = self._build_agent_context(project)

    # Prepare agent request with full context
    agent_request = {
        "action": request_data.get("action", "generate_question"),
        "project": context["project"],
        "conversation_history": context["conversation_history"],
        "conversation_summary": context["conversation_summary"],
        "topic": request_data.get("topic"),
        "current_user": request_data.get("current_user"),
    }

    # Call agent
    counselor = self.agents.get("socratic_counselor")
    if not counselor:
        return {"status": "error", "message": "SocraticCounselor agent not found"}

    try:
        result = counselor.process(agent_request)
        return {
            **result,
            "debug_logs": context["debug_logs"]
        }
    except Exception as e:
        self.logger.error(f"SocraticCounselor error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "debug_logs": context["debug_logs"]
        }

def _handle_context_analyzer(self, request_data):
    """Handle ContextAnalyzer requests with full context."""
    project = request_data.get("project")
    if not project:
        return {"status": "error", "message": "Project required"}

    context = self._build_agent_context(project)

    agent_request = {
        "action": request_data.get("action", "analyze"),
        "project": context["project"],
        "conversation_history": context["conversation_history"],
        "conversation_summary": context["conversation_summary"],
        "content": request_data.get("content"),
    }

    analyzer = self.agents.get("context_analyzer")
    if not analyzer:
        return {"status": "error", "message": "ContextAnalyzer agent not found"}

    try:
        result = analyzer.process(agent_request)
        return {
            **result,
            "debug_logs": context["debug_logs"]
        }
    except Exception as e:
        self.logger.error(f"ContextAnalyzer error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "debug_logs": context["debug_logs"]
        }

# ... Add similar handlers for other agent types
```

---

## Part 2: Route Handler Updates

### 2.1 Update chat.py Routes

**File**: `backend/src/socrates_api/routers/chat.py`

**Before**:
```python
@router.get("/question/{project_id}", response_model=APIResponse)
async def get_next_question(project_id: str, ...):
    project = db.load_project(project_id)

    result = orchestrator.process_request(
        "socratic_counselor",
        {
            "action": "generate_question",
            "project": project,
        }
    )

    return APIResponse(
        success=True,
        data=result,
    )
```

**After**:
```python
@router.get("/question/{project_id}", response_model=APIResponse)
async def get_next_question(project_id: str, ...):
    project = db.load_project(project_id)

    # Build complete context
    context = orchestrator._build_agent_context(project)

    # Request with full context
    result = orchestrator.process_request(
        "socratic_counselor",
        {
            "action": "generate_question",
            "project": project,
            "conversation_history": context["conversation_history"],
            "conversation_summary": context["conversation_summary"],
        }
    )

    # Include debug logs in response
    from socrates_api.utils.response_utils import wrap_agent_response
    wrapped = wrap_agent_response(result, context.get("debug_logs"))

    return APIResponse(
        success=result.get("status") == "success",
        data=wrapped,
    )
```

### 2.2 Update websocket.py Routes

**File**: `backend/src/socrates_api/routers/websocket.py`

**Before**:
```python
# Line 316 - Direct LLM call without context
hint_text = orchestrator.llm_client.generate_suggestions(
    f"Current question context: {message.content}", project
)
```

**After**:
```python
# Replace direct call with handler
context = orchestrator._build_agent_context(project)
result = orchestrator.process_request(
    "context_analyzer",
    {
        "action": "generate_suggestions",
        "project": project,
        "conversation_history": context["conversation_history"],
        "conversation_summary": context["conversation_summary"],
        "context_text": message.content,
    }
)
hint_text = result.get("data", {}).get("suggestions", "No suggestions available")
```

### 2.3 Update nlu.py Routes

**File**: `backend/src/socrates_api/routers/nlu.py`

**Before**:
```python
# Lines 78-84 - Direct agent access without context
agent = orchestrator.agents.get("context_analyzer")
if agent and orchestrator.llm_client:
    try:
        result = agent.process({
            "action": "analyze",
            "content": text
        })
```

**After**:
```python
# Use handler through orchestrator
result = orchestrator._handle_context_analyzer({
    "action": "analyze",
    "project": project,  # Requires project to be passed
    "content": text
})
```

---

## Part 3: Response Wrapper Pattern

### 3.1 Update APIResponse Model

**File**: `backend/src/socrates_api/models.py`

Check if APIResponse includes debug_logs. If not, add:

```python
class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool
    status: Optional[str] = "success"
    message: Optional[str] = None
    data: Any = None
    debug_logs: Optional[List[Dict]] = None  # ← Add this field

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "status": "success",
                "message": "Operation completed",
                "data": {"question": "What is...?"},
                "debug_logs": [
                    {"timestamp": "2026-04-02T10:00:00", "level": "INFO", "message": "Question generated"}
                ]
            }
        }
```

### 3.2 Standard Response Pattern

All routes should follow this pattern:

```python
from socrates_api.utils.response_utils import wrap_agent_response

@router.post("/some-endpoint", response_model=APIResponse)
async def some_endpoint(request: SomeRequest, ...):
    # 1. Load data
    project = db.load_project(...)

    # 2. Build context
    context = orchestrator._build_agent_context(project)

    # 3. Call agent with context
    result = orchestrator.process_request(
        "agent_name",
        {
            "action": "action_name",
            "project": project,
            "conversation_history": context["conversation_history"],
            "conversation_summary": context["conversation_summary"],
            **additional_params
        }
    )

    # 4. Wrap response with debug logs
    wrapped = wrap_agent_response(result, context.get("debug_logs"))

    # 5. Return APIResponse
    return APIResponse(
        success=result.get("status") == "success",
        data=wrapped,
        debug_logs=context.get("debug_logs")
    )
```

---

## Part 4: Implementation Checklist

### Phase 1: Orchestrator Changes (1-2 hours)
- [ ] Add `_build_agent_context()` method
- [ ] Add `_generate_conversation_summary()` method
- [ ] Create `response_utils.py` with wrap functions
- [ ] Test context building with sample project
- [ ] Verify conversation summary generation

### Phase 2: High-Priority Routes (3-4 hours)
- [ ] Update `chat.py` - 2 routes
  - [ ] `GET /chat/question/{id}`
  - [ ] `GET /chat/summary/{id}`
- [ ] Update `projects_chat.py` - verify existing fix + 4 more routes
  - [ ] POST `/send`
  - [ ] GET `/hint`
  - [ ] GET `/summary`
  - [ ] POST `/resolve` (quality controller)

### Phase 3: WebSocket Routes (2-3 hours)
- [ ] Update `websocket.py` - 3 agent calls
  - [ ] Line 316 - suggestions
  - [ ] Line 494 - hints
  - [ ] Line 1125 - context generation

### Phase 4: Remaining Routes (4-5 hours)
- [ ] Update `nlu.py` - 2 routes
- [ ] Update `code_generation.py` - 3 routes
- [ ] Update `analytics.py` - 2 routes
- [ ] Update `knowledge.py` - 5 routes
- [ ] Update `free_session.py` - 3 routes
- [ ] Update `projects.py` - 4 routes

### Phase 5: Testing & Verification (3-4 hours)
- [ ] Unit tests for context building
- [ ] Integration tests for each updated route
- [ ] End-to-end test of conversation flow
- [ ] Debug log verification
- [ ] Performance impact assessment

**Total Estimated Time**: 12-18 hours of development

---

## Part 5: Validation Tests

### Test 1: Context Passing

```python
def test_context_passed_to_agent():
    """Verify conversation history is passed to agents."""
    # Setup
    project = create_test_project(conversation_history=[
        {"type": "q", "content": "What is your goal?"},
        {"type": "a", "content": "Build a web app"},
    ])

    # Execute
    context = orchestrator._build_agent_context(project)

    # Verify
    assert context["conversation_history"] == project.conversation_history
    assert context["conversation_summary"] == "Q: What is your goal? | A: Build a web app"
    assert context["project"] == project
    assert context["debug_logs"] is not None
```

### Test 2: Debug Logs in Response

```python
def test_debug_logs_in_response():
    """Verify debug logs are returned in API responses."""
    # Setup
    project = create_test_project()

    # Execute (actual HTTP call)
    response = client.get(f"/chat/question/{project.id}")

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert "debug_logs" in data.get("data", {})
    assert isinstance(data["data"]["debug_logs"], list)
```

### Test 3: Single Question Flow

```python
def test_single_question_dialogue_flow():
    """Verify questions progress Q1 -> Answer -> Q2 (not stuck on Q1)."""
    # Setup
    project = create_test_project()

    # Execute
    # 1. Get question
    q1_response = get_question(project)
    q1 = q1_response["data"]["question"]

    # 2. Answer question
    answer_response = submit_answer(project, q1, "My answer")

    # 3. Get next question
    q2_response = get_question(project)
    q2 = q2_response["data"]["question"]

    # Verify
    assert q1 != q2  # Should be different questions
    assert "pending" in project.state  # Q1 should no longer be pending
```

---

## Part 6: Rollout Strategy

### Deployment Order

1. **Orchestrator + Utils** (low risk)
   - Deploy orchestrator changes
   - Deploy response_utils
   - No route changes yet
   - No user impact

2. **Testing Routes** (medium risk)
   - Deploy chat.py updates
   - Verify in staging
   - Enable feature flag if available

3. **Critical Routes** (high risk)
   - Deploy projects_chat.py updates
   - Monitor for regressions
   - Verify dialogue works end-to-end

4. **Remaining Routes** (one at a time)
   - Deploy each route file separately
   - Test before moving to next
   - Monitor for issues

### Rollback Plan

If issues occur:
1. Revert the specific route file (don't affect others)
2. Revert orchestrator if needed (but it's backward-compatible)
3. Test old code in staging
4. Re-deploy after fix

---

## Part 7: Monitoring & Verification

### Key Metrics to Track

1. **Context Availability**
   - Percentage of requests with conversation_history provided
   - Average conversation_summary length
   - Missing context errors

2. **Response Completeness**
   - Percentage of responses including debug_logs
   - Average debug_logs per response
   - Routes without debug_logs (should be 0%)

3. **Dialogue Flow**
   - Questions per conversation session
   - Repeat question rate (should be <5%)
   - User completion rate

4. **Performance**
   - API response time impact
   - Context building overhead
   - Summary generation cost

### Alerts

Set up alerts for:
- Response time degradation >10%
- Error rate increase >2%
- Repeat question rate >10%
- Context availability <95%

---

## Summary of Changes

| File | Changes | Lines | Risk |
|------|---------|-------|------|
| orchestrator.py | Add 3 methods | +50 | Low |
| response_utils.py | New file | +30 | Low |
| models.py | Add debug_logs field | +3 | Low |
| chat.py | Context passing | +10 | Medium |
| projects_chat.py | Verify + 4 more routes | +20 | Medium |
| websocket.py | 3 agent calls | +30 | High |
| nlu.py | 2 routes | +15 | Medium |
| code_generation.py | 3 routes | +20 | Medium |
| analytics.py | 2 routes | +15 | Medium |
| knowledge.py | 5 routes | +25 | Medium |
| free_session.py | 3 routes | +20 | Medium |
| projects.py | 4 routes | +20 | Medium |
| **TOTAL** | | **~250-300** | **Medium** |

---

## Conclusion

This proposal provides a concrete, step-by-step approach to fix the context passing and response completeness issues identified in the Modular Architecture Issues Analysis.

The fixes are:
- ✅ **Non-breaking** - Response envelope change is backward-compatible
- ✅ **Testable** - Each change can be tested independently
- ✅ **Deployable** - Can be rolled out route-by-route
- ✅ **Measurable** - Clear metrics to verify success
- ✅ **Reversible** - Each route can be independently reverted

Once implemented, the modular architecture will have the same context-aware, dialogue-enabling properties as the monolithic version, while retaining the benefits of modularization.
