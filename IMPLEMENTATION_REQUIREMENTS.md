# Implementation Requirements: Replicate Monolithic Orchestration

**Date**: 2026-04-02
**Status**: Analysis Complete - Ready for Implementation
**Effort Estimate**: 20-30 hours (PHASE 1 only)

⚠️ **CRITICAL**: This is Phase 1 (Integrate into Modular Socrates)
**MUST COMPLETE PHASE 0 FIRST**: See LIBRARY_AUDIT_AND_REMEDIATION_PLAN.md

Phase 0 (Fix Libraries): 60 hours
Phase 1 (This document): 20-30 hours
**Total**: 80-90 hours

---

## Summary

The modular Socrates dialogue system requires **complete reimplementation of the orchestration layer** to replicate the monolithic version's full orchestration flow. The PyPI `socratic-agents` package contains only the question generation component; the orchestrator must handle all state management, persistence, and workflow coordination.

---

## Files Requiring Changes

### 1. Orchestrator (`backend/src/socrates_api/orchestrator.py`)

**Methods to enhance or create:**

#### A. `_orchestrate_question_generation()` (CRITICAL - Complete Rewrite)

**Current State**: Partial implementation, missing critical steps

**Required Implementation**:
```python
def _orchestrate_question_generation(self, project, user_id, force_refresh=False):
    """
    STEP 1: Check for existing unanswered question
    - If pending_questions contains unanswered question, return existing
    - Prevents double-generation unless force_refresh=True

    STEP 2: Get or create user
    - Load user from database
    - If not found, auto-create with "pro" tier
    - Save to database

    STEP 3: Validate subscription
    - Check SubscriptionChecker.check_question_limit(user)
    - Return error if limit exceeded

    STEP 4: Gather KB context from vector DB
    - Search vector DB using project context
    - Use adaptive loading strategy (full vs snippet)
    - Cache results per phase to reduce DB calls
    - Extract document understanding analysis

    STEP 5: Call PyPI SocraticCounselor agent
    - Pass full context: topic, level, phase, KB chunks/gaps, conversation_history, etc.
    - Get question back

    STEP 6: Store question in TWO places
    - conversation_history: Full message log with metadata
    - pending_questions: Tracking array with status="unanswered"

    STEP 7: Update metrics
    - Increment user.question_usage_count
    - Save user to database

    STEP 8: Persist to database
    - Save project with updated conversation_history and pending_questions

    RETURN: {"status": "success", "question": question}
    """
```

**Reference**: Monolithic lines 109-200

---

#### B. `_orchestrate_answer_processing()` (CRITICAL - Major Enhancement)

**Current State**: Partial implementation, missing next question generation and several orchestration steps

**Required Implementation**:
```python
def _orchestrate_answer_processing(self, project, user_id, user_response):
    """
    STEP 1: Add to conversation_history
    - Append user response with timestamp, phase, author metadata

    STEP 2: Extract insights
    - Call LLM client to extract insights/specs from response
    - Log extracted items

    STEP 3: CRITICAL - Mark question as answered (BEFORE conflict detection!)
    - Find unanswered question in pending_questions
    - Set status="answered" and answered_at timestamp
    - This must happen BEFORE conflict detection (ordering is critical)

    STEP 4: Conflict detection
    - Call conflict detector on extracted insights
    - If conflicts found:
      - Save project (question already marked answered)
      - Return with conflicts_pending=True
      - Do NOT continue to steps 5-8

    STEP 5: Update project maturity
    - Analyze how response impacts project understanding
    - Update maturity_phase_tracker with new metrics

    STEP 6: Track question effectiveness
    - Record how well this question advanced learning
    - Feed into learning analytics system

    STEP 7: Check phase completion
    - Analyze if current phase is complete (maturity threshold reached)
    - If complete, prepare advancement message

    STEP 8: Generate NEXT question
    - Call _orchestrate_question_generation(force_refresh=True)
    - Get question back

    STEP 9: Persist to database
    - Save project with all changes

    RETURN: {
        "status": "success",
        "insights": insights,
        "next_question": next_question,  # CRITICAL - Must be included
        "phase_complete": phase_complete,
        "completion_message": message if complete else None,
    }
    """
```

**Reference**: Monolithic lines 721-950

**CRITICAL ORDERING**: Step 3 (mark answered) MUST happen before Step 4 (conflict detection). This ensures the question is counted as answered even if conflicts are found.

---

### 2. Projects Chat Router (`backend/src/socrates_api/routers/projects_chat.py`)

**File**: `send_message` endpoint (around line 960-1000)

**Current State**:
```python
# Calls answer processing
next_result = orchestrator._orchestrate_answer_processing(...)
# Returns only insights, missing next question
response_data["insights"] = insights
return response_data
```

**Required Change**:
```python
# 1. Process answer
answer_result = orchestrator._orchestrate_answer_processing(
    project=project,
    user_id=current_user,
    user_response=user_response
)

# 2. Extract results
insights = answer_result.get("insights")
next_question = answer_result.get("next_question")  # Now included
phase_complete = answer_result.get("phase_complete", False)
conflicts = answer_result.get("conflicts", [])

# 3. Prepare response with next question
response_data = {
    "status": "success",
    "message": "Response processed",
    "insights": insights,
    "debug_summary": answer_result.get("debug_summary", ""),
}

# 4. CRITICAL: Include next question
if next_question:
    response_data["next_question"] = next_question
else:
    response_data["error"] = "Failed to generate next question"

# 5. Include other data
if conflicts:
    response_data["conflicts"] = conflicts
    response_data["conflicts_pending"] = True

if phase_complete:
    response_data["phase_complete"] = True
    response_data["completion_message"] = answer_result.get("completion_message")

return response_data
```

---

### 3. Database (`backend/src/socrates_api/database.py`)

**New Methods Needed**:

#### A. Subscription Checking
```python
def check_question_limit(user):
    """
    Check if user has questions remaining in their subscription tier.
    Return (can_ask: bool, error_message: str)
    """
    # Tier-based limits
    limits = {
        "free": 5,
        "pro": 100,
        "enterprise": float('inf')
    }

    tier = user.subscription_tier or "free"
    limit = limits.get(tier, 5)

    # Check if user would exceed limit
    today = datetime.date.today()
    questions_today = len([
        q for q in user.questions
        if q.created_date == today
    ])

    if questions_today >= limit:
        return False, f"Daily limit of {limit} questions reached"

    return True, None
```

#### B. User Auto-Creation
```python
def create_default_user(user_id):
    """
    Create default user for CLI/local usage with pro tier.
    """
    user = User(
        username=user_id,
        email=f"{user_id}@localhost",
        subscription_tier="pro",
        created_at=datetime.datetime.now(),
        projects=[],
    )
    return user
```

#### C. Phase Caching for KB Context
```python
def get_cached_kb_context(project_id, phase):
    """
    Check if KB context for this phase was recently cached.
    Return cached results if available to reduce vector DB calls.
    """
    cache_key = f"{project_id}:{phase}"
    # Check TTL cache or in-memory dict
    # If fresh (< 1 hour old), return cached
    # Otherwise return None to trigger new search
    pass

def cache_kb_context(project_id, phase, context, ttl_seconds=3600):
    """
    Cache KB context for this phase to reduce vector DB load.
    """
    cache_key = f"{project_id}:{phase}"
    # Store in cache with TTL
    pass
```

---

## Implementation Steps

### Phase 1: Core Orchestration (8-10 hours)

#### Step 1.1: Enhance `_orchestrate_question_generation()`
- [ ] Add step 1: Check for existing unanswered questions
- [ ] Add step 2: Get/create user with auto-creation
- [ ] Add step 3: Validate subscription limits
- [ ] Add step 4: Gather KB context from vector DB
- [ ] Add step 5: Call PyPI agent with full context
- [ ] Add step 6: Store in both conversation_history and pending_questions
- [ ] Add step 7: Update user metrics and save
- [ ] Add step 8: Save project to database

**Tests**:
- [ ] Test returns existing unanswered question when available
- [ ] Test generates new question when none unanswered
- [ ] Test subscription limit enforcement
- [ ] Test user auto-creation
- [ ] Test question stored in both places with correct status
- [ ] Test database persistence

#### Step 1.2: Enhance `_orchestrate_answer_processing()`
- [ ] Add step 1: Store response in conversation_history
- [ ] Add step 2: Extract insights via LLM
- [ ] Add step 3: Mark question answered (before conflict detection!)
- [ ] Add step 4: Conflict detection with early return if found
- [ ] Add step 5: Update maturity metrics
- [ ] Add step 6: Track question effectiveness
- [ ] Add step 7: Check phase completion
- [ ] Add step 8: Generate next question via orchestrator call
- [ ] Add step 9: Save project to database

**Tests**:
- [ ] Test response added to history
- [ ] Test insights extracted and returned
- [ ] Test question marked answered before conflict check
- [ ] Test early return on conflict detection
- [ ] Test next question generated and returned
- [ ] Test database persistence
- [ ] Test phase completion detection

#### Step 1.3: Update `projects_chat.py:send_message`
- [ ] Extract next_question from answer_result
- [ ] Include next_question in response_data
- [ ] Test full end-to-end dialogue flow
- [ ] Test response includes all required fields

**Tests**:
- [ ] Test send_message returns next question
- [ ] Test dialogue flow: question → answer → next_question
- [ ] Test error handling if next question generation fails

---

### Phase 2: Knowledge Base Integration (6-8 hours)

#### Step 2.1: Vector DB Integration
- [ ] Implement adaptive knowledge loading strategy
- [ ] Add per-phase caching to reduce DB calls
- [ ] Extract document understanding from KB results
- [ ] Build proper KB context for PyPI agent

**Tests**:
- [ ] Test vector DB search returns relevant results
- [ ] Test caching works (cache hits on second call)
- [ ] Test adaptive strategy (full vs snippet)
- [ ] Test KB context passed to agent

#### Step 2.2: Subscription Management
- [ ] Implement `check_question_limit()` method
- [ ] Implement `create_default_user()` method
- [ ] Test auto-creation for CLI users
- [ ] Test limit enforcement

**Tests**:
- [ ] Test limit enforcement by tier
- [ ] Test auto-creation creates pro users
- [ ] Test save_user persists correctly

---

### Phase 3: State Management (4-6 hours)

#### Step 3.1: Question State Tracking
- [ ] Ensure pending_questions tracked correctly
- [ ] Test status transitions: unanswered → answered
- [ ] Test question_id generation and uniqueness
- [ ] Test duplicate question prevention

**Tests**:
- [ ] Test unanswered question check returns existing
- [ ] Test status transitions work
- [ ] Test answered timestamp recorded

#### Step 3.2: Conversation History
- [ ] Test conversation_history appends correctly
- [ ] Test metadata preserved (phase, author, timestamp)
- [ ] Test history available for context to next question generation

**Tests**:
- [ ] Test conversation history length increases
- [ ] Test metadata complete for each message
- [ ] Test recently_asked extracted from history

---

### Phase 4: Testing & Validation (2-4 hours)

#### Step 4.1: Integration Tests
```python
def test_full_dialogue_flow():
    """Test complete dialogue: question → answer → next_question"""
    # 1. Generate question (should succeed)
    q1_result = orchestrator._orchestrate_question_generation(project, user_id)
    assert q1_result["status"] == "success"
    assert q1_result["question"]

    # 2. Answer question (should extract insights, generate next question)
    a1_result = orchestrator._orchestrate_answer_processing(
        project, user_id, "My answer"
    )
    assert a1_result["status"] == "success"
    assert a1_result["insights"]
    assert a1_result["next_question"]  # CRITICAL
    assert "answered" in project.pending_questions[0]["status"]

    # 3. Answer second question (should continue flow)
    a2_result = orchestrator._orchestrate_answer_processing(
        project, user_id, "My second answer"
    )
    assert a2_result["next_question"]
    assert len(project.conversation_history) == 4  # Q1, A1, Q2, A2

def test_existing_question_not_regenerated():
    """Test that existing unanswered question is returned, not regenerated"""
    # 1. Generate first question
    q1 = orchestrator._orchestrate_question_generation(project, user_id)
    text1 = q1["question"]

    # 2. Call again without answering
    q2 = orchestrator._orchestrate_question_generation(project, user_id)
    text2 = q2["question"]

    # 3. Should return same question
    assert text1 == text2
    assert q2.get("existing") == True

def test_subscription_limit_enforced():
    """Test that subscription limits are checked"""
    # Create free user with 0 questions left today
    user = User(subscription_tier="free")
    user.questions_today = 5  # At limit

    # Should reject next question
    result = orchestrator._orchestrate_question_generation(project, user_id)
    assert result["status"] == "error"
    assert "limit" in result["message"].lower()
```

#### Step 4.2: End-to-End Tests
- [ ] Test full dialogue sequence (10+ turns)
- [ ] Test multiple users in same project
- [ ] Test conflict resolution mid-dialogue
- [ ] Test phase advancement
- [ ] Test database persistence verified by restart

---

## Verification Checklist

### Before Implementation
- [ ] Understand monolithic orchestration flow (read ROOT_CAUSE_ANALYSIS.md)
- [ ] Understand PyPI agent capabilities and limitations
- [ ] Review database schema and available methods

### During Implementation
- [ ] Each step tested individually
- [ ] Code follows existing patterns in orchestrator
- [ ] Error handling comprehensive
- [ ] Logging sufficient for debugging

### After Implementation
- [ ] Integration tests passing (100%)
- [ ] End-to-end dialogue test passing
- [ ] Database persistence verified
- [ ] No regressions in existing functionality
- [ ] Performance acceptable (no slow queries)

### Production Readiness
- [ ] All critical paths tested
- [ ] Error messages user-friendly
- [ ] Database handles concurrent access
- [ ] Rate limiting working
- [ ] Security validated

---

## Risk Mitigation

### Data Consistency Risk
**Issue**: Question marked answered before conflict detection could be inconsistent if exception occurs
**Mitigation**:
- Use database transaction if possible
- At minimum, ensure question is marked answered only on successful save
- Test with simulated exceptions

### Performance Risk
**Issue**: Multiple database calls per question/answer could be slow
**Mitigation**:
- Implement KB context caching per phase
- Profile queries for N+1 issues
- Consider batch operations where possible

### Backward Compatibility Risk
**Issue**: Changing orchestrator could break existing code
**Mitigation**:
- Maintain existing method signatures
- Add new parameters with defaults
- Test all existing endpoints

---

## Success Criteria

✅ **Complete when:**

1. Question generation orchestration fully implemented
   - Checks for existing unanswered questions
   - Validates subscriptions
   - Auto-creates users
   - Stores in both places
   - Persists to database

2. Answer processing orchestration fully implemented
   - Stores response in history
   - Extracts insights
   - Marks question answered
   - Detects conflicts
   - Updates maturity
   - Generates next question

3. Next question appears in API response
   - send_message returns both answer and next_question
   - Dialogue flow works end-to-end

4. All tests passing
   - Integration tests 100%
   - End-to-end dialogue test passing
   - Existing functionality not broken

5. Database persistence verified
   - Conversation history persists
   - Question state persists
   - User metrics persist
   - Data survives restart

---

## Key Files to Modify

| File | Lines | Changes |
|------|-------|---------|
| `orchestrator.py` | 1869-2337 | Complete rewrite of both orchestration methods |
| `projects_chat.py` | 960-1000 | Update send_message to include next_question |
| `database.py` | Various | Add subscription checking, user creation, caching methods |
| `models_local.py` | As needed | Add ProjectContext fields if needed (current_question_id, etc) |

---

## References

- **ROOT_CAUSE_ANALYSIS.md** - Detailed technical comparison
- **Monolithic Source**: `https://github.com/Nireus79/Socrates/tree/Monolithic-Socrates`
- **PyPI Source**: `C:\Users\themi\PycharmProjects\socratic-agents-repo\src\socratic_agents\agents\socratic_counselor.py`
