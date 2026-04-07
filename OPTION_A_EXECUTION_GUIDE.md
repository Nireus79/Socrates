# Option A Execution Guide: Complete Implementation Plan

**Date Created**: 2026-04-02
**Implementation Start**: In 3 days (when weekly limit resets)
**Duration**: 85-100 hours over 3-4 weeks
**Status**: Ready to execute

---

## Phase Overview

```
PHASE 0: Fix All Libraries (60 hours)
├─ 0a: socratic-agents (15-20 hours) - FOUNDATION
├─ 0b: Audit libraries (3-5 hours)
└─ 0c: Fix remaining libraries (35-40 hours)

PHASE 1: Integration (20-30 hours)
├─ Orchestrator implementation (8-10 hours)
├─ API updates (2-3 hours)
└─ Testing (10-15 hours)

PHASE 2: Production Ready (5-10 hours)
└─ Final validation & deployment

TOTAL: 85-100 hours
```

---

## Pre-Execution Checklist (Do These NOW, before limit resets)

### Setup
- [ ] Clone monolithic-socrates branch locally: `git fetch origin Monolithic-Socrates:Monolithic-Socrates`
- [ ] Verify branch exists: `git branch -a | grep Monolithic`
- [ ] Create working branch: `git checkout -b fix/option-a-remediation`
- [ ] Verify socratic-agents repo is cloned locally

### Documentation
- [ ] Print or bookmark: LIBRARY_AUDIT_AND_REMEDIATION_PLAN.md
- [ ] Print or bookmark: IMPLEMENTATION_REQUIREMENTS.md
- [ ] Have available: ROOT_CAUSE_ANALYSIS.md (code examples)
- [ ] Save: This execution guide (OPTION_A_EXECUTION_GUIDE.md)

### Environment
- [ ] Verify Python environment: `python --version` (3.8+)
- [ ] Verify git: `git --version`
- [ ] Verify you can access both repos
- [ ] Set up IDE/editor for 3-4 week sprint

### Mental Preparation
- [ ] Read: DECISION_FRAMEWORK.md (why Option A)
- [ ] Read: ROOT_CAUSE_ANALYSIS.md (technical foundation)
- [ ] Understand: Phase 0a socratic-agents is CRITICAL path
- [ ] Block calendar: 85-100 hours over next 3-4 weeks

---

## Phase 0a: Fix socratic-agents (15-20 hours)

**This is the FOUNDATION - everything depends on it being correct**

### Step 0a.1: Extract Code from Monolithic (4 hours)

#### Task 1: Get the complete SocraticCounselor

```bash
# Get complete monolithic SocraticCounselor
git show Monolithic-Socrates:socratic_system/agents/socratic_counselor.py > /tmp/monolithic_counselor.py

# Verify all methods are there
grep "def " /tmp/monolithic_counselor.py | wc -l
# Should be ~30+ methods
```

#### Task 2: Create extraction checklist

```markdown
## Extraction Checklist

Methods to extract (in order):
- [ ] Class definition and __init__
- [ ] process() - main router
- [ ] _generate_question() - CRITICAL
- [ ] _process_response() - CRITICAL
- [ ] _generate_dynamic_question()
- [ ] _generate_static_question()
- [ ] _extract_insights_only()
- [ ] _handle_conflict_detection()
- [ ] _update_project_and_maturity()
- [ ] _track_question_effectiveness()
- [ ] _check_phase_completion()
- [ ] _advance_phase()
- [ ] _rollback_phase()
- [ ] _generate_hint()
- [ ] _explain_document()
- [ ] Helper methods (10+ more)

Total: ~30 methods, ~1500 lines
```

### Step 0a.2: Implement in PyPI socratic-agents (8 hours)

**File**: `C:\Users\themi\PycharmProjects\socratic-agents-repo\src\socratic_agents\agents\socratic_counselor.py`

#### Task 1: Adapt imports

Replace monolithic imports with standalone versions:
```python
# Remove these:
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.models import ProjectContext, ConflictInfo

# Replace with parameters/inputs instead:
# def _generate_question(self, project: Dict, user_id: str) -> Dict:
#     (project is now a dict/object passed in, not from orchestrator)
```

#### Task 2: Extract orchestrator references

```python
# Find and replace patterns:
self.orchestrator.database.save_project(project)
→ return {"status": "success", "project": project}

self.orchestrator.claude_client.extract_insights(...)
→ Pass llm_client as parameter in __init__

self.logger.info(...)
→ Keep as-is or pass logger as parameter

self.orchestrator.context_analyzer.get_context_summary(...)
→ Pass context as parameter input
```

#### Task 3: Implementation order (do in this order)

1. **Copy class structure** (50 lines)
   - Class definition
   - __init__
   - process() router method

2. **Copy process() method** (30 lines)
   - Main routing logic
   - Action handlers

3. **Copy _generate_question()** (200 lines)
   - CRITICAL - full orchestration
   - All 8 steps
   - Test this first

4. **Copy _process_response()** (250 lines)
   - CRITICAL - full answer processing
   - All 9 steps
   - Test thoroughly

5. **Copy helper methods** (500 lines)
   - Question generation variants
   - Insight extraction
   - Maturity tracking
   - Phase completion

6. **Copy remaining methods** (400 lines)
   - Conflict detection
   - Phase advancement
   - Hint generation
   - Document explanation

### Step 0a.3: Test individually (4 hours)

#### Unit Tests

```python
# tests/agents/test_socratic_counselor.py

def test_generate_question_checks_existing():
    """Test that existing unanswered question is returned."""
    counselor = SocraticCounselor(llm_client=mock_llm)
    project = create_test_project_with_unanswered_question()

    result = counselor.process({
        "action": "generate_question",
        "project": project,
        "user_id": "test_user"
    })

    assert result["status"] == "success"
    assert result["existing"] == True
    assert result["question"] == expected_question

def test_generate_question_creates_new():
    """Test that new question is generated when none unanswered."""
    counselor = SocraticCounselor(llm_client=mock_llm)
    project = create_test_project_no_questions()

    result = counselor.process({
        "action": "generate_question",
        "project": project,
        "user_id": "test_user"
    })

    assert result["status"] == "success"
    assert "question" in result
    assert len(result["question"]) > 0

def test_process_response_extracts_insights():
    """Test that response processing extracts insights."""
    counselor = SocraticCounselor(llm_client=mock_llm)
    project = create_test_project_with_question()

    result = counselor.process({
        "action": "process_response",
        "project": project,
        "user_id": "test_user",
        "response": "My answer to the question"
    })

    assert result["status"] == "success"
    assert "insights" in result
    assert "next_question" in result  # CRITICAL
    assert result["next_question"]  # Must have value

def test_process_response_marks_answered():
    """Test that question is marked answered before conflict detection."""
    # This is CRITICAL - ordering matters
    counselor = SocraticCounselor(llm_client=mock_llm)
    project = create_test_project_with_conflict_question()

    result = counselor.process({
        "action": "process_response",
        "project": project,
        "user_id": "test_user",
        "response": "Answer that causes conflict"
    })

    # Even if conflicts found, question should be marked answered
    assert project.pending_questions[0]["status"] == "answered"
    assert "conflicts" in result or result["status"] == "success"
```

#### Integration Tests

```python
def test_full_dialogue_flow():
    """Test complete dialogue: Q1 → A1 → Q2 → A2 → Q3."""
    counselor = SocraticCounselor(llm_client=real_llm)
    project = create_test_project()

    # Round 1: Get question
    q1_result = counselor.process({
        "action": "generate_question",
        "project": project,
        "user_id": "user1"
    })
    assert q1_result["status"] == "success"
    q1_text = q1_result["question"]
    project.conversation_history.append({
        "type": "assistant",
        "content": q1_text
    })

    # Round 1: Answer question
    a1_result = counselor.process({
        "action": "process_response",
        "project": project,
        "user_id": "user1",
        "response": "User's answer to Q1"
    })
    assert a1_result["status"] == "success"
    assert "next_question" in a1_result
    q2_text = a1_result["next_question"]

    # Verify conversation history grew
    assert len(project.conversation_history) == 3  # Q1, A1, Q2

    # Round 2: Answer second question
    a2_result = counselor.process({
        "action": "process_response",
        "project": project,
        "user_id": "user1",
        "response": "User's answer to Q2"
    })
    assert a2_result["status"] == "success"
    assert "next_question" in a2_result

    # Verify questions keep coming
    assert len(a2_result["next_question"]) > 0
```

### Step 0a.4: Document & Publish (2-3 hours)

#### Update Documentation

```markdown
# socratic-agents v1.0.0

## Complete Orchestration Engine

This module provides complete Socratic dialogue orchestration.

### Methods

#### process(request: Dict) -> Dict

Routes to appropriate handler:
- action: "generate_question", "process_response", etc.

#### _generate_question(request: Dict) -> Dict

Full question generation with orchestration:
1. Check for existing unanswered question
2. Validate subscription limits
3. Auto-create user if needed
4. Generate question with KB context
5. Store in conversation_history AND pending_questions
6. Update user metrics
7. Save to database

#### _process_response(request: Dict) -> Dict

Full response processing with orchestration:
1. Add response to conversation_history
2. Extract insights
3. Mark question answered (BEFORE conflict detection!)
4. Detect conflicts (early return if found)
5. Update maturity metrics
6. Track effectiveness
7. Check phase completion
8. Generate NEXT question
9. Save to database

[Continue for all 30+ methods...]
```

#### Update CHANGELOG

```markdown
# Changelog - socratic-agents

## [1.0.0] - 2026-04-XX

### Added - Complete Orchestration Engine

- **Major rewrite**: From question-generation-only to complete orchestration
- **30+ methods**: All critical dialogue methods now implemented
- **Full dialogue flow**: Question generation → Answer processing → Next question
- **State management**: Conversation history + pending questions tracking
- **Insight extraction**: Claude-powered spec extraction from responses
- **Conflict detection**: Real-time conflict detection with resolution
- **Maturity tracking**: Phase-based maturity scoring
- **User management**: Auto-create users, track usage
- **Subscription checking**: Enforce question limits by tier
- **Hint generation**: Context-aware hints for stuck users
- **Phase advancement**: Automatic phase completion detection

### Changed
- BREAKING: Module now requires more configuration (llm_client, etc.)
- API version bumped to 1.0.0 (major rewrite)

### Removed
- Placeholder/stub methods (now fully implemented)
- Dependency on orchestrator for core logic

### Fixed
- N/A (complete rewrite from scratch)
```

#### Publish to PyPI

```bash
# In socratic-agents-repo
python -m build
python -m twine upload dist/*

# Verify
pip install --upgrade socratic-agents==1.0.0
```

---

## Phase 0b: Audit All Libraries (3-5 hours)

**Use the audit procedure from LIBRARY_AUDIT_AND_REMEDIATION_PLAN.md**

### Libraries to Audit (in order)

1. **socratic-conflict** - High priority
2. **socratic-learning** - High priority
3. **socratic-rag** - Medium priority
4. **socratic-maturity** - High priority
5. **socratic-core** - Medium priority
6. **socratic-knowledge** - Medium priority
7. **socratic-workflow** - Medium priority
8. **socratic-security** - Low priority
9. **socratic-analyzer** - Low priority
10. **socratic-performance** - Low priority
11. **socratic-docs** - Low priority
12. **socrates-nexus** - System integration

### For Each Library

**Create this file**: `AUDIT_socratic-XXX.md`

```markdown
# Audit: socratic-XXX

## Source Code Location
Monolithic: socratic_system/.../agent.py
PyPI: src/socratic_agents/agents/agent.py

## Methods in Monolithic
[List all methods found in monolithic]

## Methods in PyPI
[List all methods found in PyPI]

## Missing Methods (Must Implement)
- [ ] method1 (lines XXX-YYY)
- [ ] method2 (lines XXX-YYY)

## Effort Estimate
X-Y hours

## Implementation Order
1. method_with_no_deps
2. method_depends_on_1
3. method_depends_on_2
```

---

## Phase 0c: Fix Remaining Libraries (35-40 hours)

**For each library (in order of dependency)**:

1. Extract methods from monolithic
2. Implement in PyPI
3. Test independently
4. Publish new version
5. Verify installation

**Per-library effort breakdown**:

- socratic-conflict: 8-10 hours (high priority)
- socratic-learning: 10-12 hours (high priority)
- socratic-rag: 10-12 hours (medium priority)
- socratic-maturity: 6-8 hours (high priority)
- Others: 15-20 hours combined

---

## Phase 1: Integration (20-30 hours)

**Only after all Phase 0 libraries are fixed and published to PyPI**

See: IMPLEMENTATION_REQUIREMENTS.md for detailed Phase 1 plan

### Phase 1a: Orchestrator Implementation (8-10 hours)

File: `backend/src/socrates_api/orchestrator.py`

- [ ] Rewrite `_orchestrate_question_generation()`
- [ ] Rewrite `_orchestrate_answer_processing()`
- [ ] Add KB context gathering
- [ ] Add user management
- [ ] Add metrics tracking

### Phase 1b: API Updates (2-3 hours)

File: `backend/src/socrates_api/routers/projects_chat.py`

- [ ] Update `send_message` endpoint to include next_question

### Phase 1c: Testing (10-15 hours)

- [ ] Unit tests for orchestrator methods
- [ ] Integration tests for full dialogue
- [ ] Database persistence tests
- [ ] Performance tests
- [ ] End-to-end tests with real scenarios

---

## Phase 2: Production Ready (5-10 hours)

- [ ] Final validation of all components
- [ ] Upgrade instructions for users
- [ ] Deployment plan
- [ ] Rollback plan
- [ ] Post-deployment verification

---

## Daily Standup Template

**Use this each day to track progress**:

```
DATE: 2026-04-XX
PHASE: 0a (socratic-agents)
STATUS: IN PROGRESS

COMPLETED TODAY (X hours):
- [ ] Task 1
- [ ] Task 2

BLOCKERS:
- None / [Description if any]

PLANNED FOR TOMORROW:
- [ ] Task 3
- [ ] Task 4

CONFIDENCE: [% complete]
NEXT BLOCKER TO WATCH: [What might slow progress]
```

---

## Success Criteria Checklist

### Phase 0a Complete When:
- [ ] All 30+ SocraticCounselor methods extracted and adapted
- [ ] socratic-agents v1.0.0 published to PyPI
- [ ] Full dialogue test passing (Q → A → Q → A → Q)
- [ ] All unit tests passing
- [ ] Documentation complete

### Phase 0b Complete When:
- [ ] All 14+ libraries audited
- [ ] Missing methods documented
- [ ] Implementation specs created
- [ ] Effort estimates accurate

### Phase 0c Complete When:
- [ ] All libraries fixed and published
- [ ] Each library has passing tests
- [ ] Dependencies satisfied
- [ ] Integration-ready versions available

### Phase 1 Complete When:
- [ ] Orchestrator implementation complete
- [ ] API endpoints working
- [ ] Full dialogue flow working end-to-end
- [ ] Database persistence verified
- [ ] All tests passing (100%)

### Phase 2 Complete When:
- [ ] Production validation complete
- [ ] Deployment verified
- [ ] Users have working dialogue system
- [ ] No critical issues

---

## What to Do If Stuck

**Problem**: Method doesn't work after extraction

**Solution**:
1. Check monolithic example
2. Compare parameter passing
3. Test with monolithic data structures
4. Add debug logging
5. Create minimal test case
6. Review ROOT_CAUSE_ANALYSIS.md for similar issues

**Problem**: Test failing

**Solution**:
1. Read test error carefully
2. Check what monolithic does for same scenario
3. Verify mocks/test data correct
4. Add print statements for debugging
5. Run smaller/simpler test first

**Problem**: Time running out

**Solution**:
1. Focus on Phase 0a first (foundation)
2. Defer Phase 0c libraries to later if needed
3. Get Phase 1 running with what you have
4. Users can use partial system
5. Complete remaining libraries incrementally

---

## Support Resources

**If confused**:
- ROOT_CAUSE_ANALYSIS.md - Technical details
- LIBRARY_AUDIT_AND_REMEDIATION_PLAN.md - Implementation specs
- IMPLEMENTATION_REQUIREMENTS.md - Phase 1 details

**Reference**:
- Monolithic branch: github.com/Nireus79/Socrates/tree/Monolithic-Socrates
- This repo: github.com/Nireus79/Socratic-agents

---

## Ready to Start in 3 Days?

✅ All documentation prepared
✅ Extraction checklists created
✅ Code templates provided
✅ Test specifications defined
✅ Success criteria clear
✅ Support resources available

**When your limit resets, you can start immediately with:**
1. Clone monolithic-socrates branch
2. Follow Phase 0a extraction steps
3. Update socratic_counselor.py
4. Run tests
5. Proceed to next phase

**Good luck! This is the right approach.**
