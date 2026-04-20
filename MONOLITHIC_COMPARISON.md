# Monolithic-Socrates vs Master Branch Comparison

## Executive Summary

The **Master branch** (where you are) implements a more sophisticated "Monolithic Orchestrator" pattern with explicit confidence scoring, parallel processing, and detailed metadata tracking.

The **Monolithic-Socrates branch** uses a simpler "Agent Delegation" pattern where agents handle more logic internally.

---

## Key Architectural Differences

### Answer Processing Pipeline

#### Master Branch (Current)
```
User Answer
    ↓
Router: send_message()
    ↓
Orchestrator: _process_answer_monolithic()
    ├─ Step 1: counselor.extract_learning_objectives()  [Returns specs with confidence]
    ├─ Step 2: Filter confidence >= 0.7  [You control threshold]
    ├─ Step 3: Merge into project.goals/requirements/tech_stack/constraints
    ├─ Step 4: detector.detect({specs, existing_goals})  [Explicit conflict detection]
    ├─ Step 5: MaturityCalculator.calculate()  [Maturity tracking]
    └─ Step 6: Save to conversation_history + database
```

**Advantages:**
- ✓ Confidence-driven filtering (only high-confidence specs)
- ✓ Separate conflict detection step
- ✓ Maturity calculation integrated
- ✓ Clear separation of concerns
- ✓ Detailed logging for debugging

**Disadvantages:**
- ✗ More moving parts to coordinate
- ✗ Agents must return expected format
- ✗ Requires counselor + detector agents

#### Monolithic-Socrates Branch
```
User Answer
    ↓
Router: send_message()
    ├─ Direct Mode: Returns specs to user for approval
    └─ Socratic Mode: Silently saves specs without user visibility
```

**Advantages:**
- ✓ Simpler flow (fewer components)
- ✓ User approval step in direct mode
- ✓ Clean Socratic dialogue (no specs shown)

**Disadvantages:**
- ✗ No confidence filtering
- ✗ Less explicit control
- ✗ Harder to debug

---

## Question Deduplication Strategies

### Master Branch
```
Conversation History
    ↓
Extract messages where:
  type="assistant" AND
  phase=current_phase AND
  content exists
    ↓
Build "recently_asked" list
    ↓
Pass to counselor.process()
    ↓
Counselor returns non-duplicate
```

**Filter Logic**: Explicit message filtering by type + phase

**Logging**: `[QUESTION_DEDUP]` shows each message decision

**Agent Responsibility**: Counselor must respect "recently_asked" parameter

### Monolithic-Socrates Branch
```
Similar approach, but:
  - Less explicit message filtering
  - Relies more on agent abstraction
  - Counselor.process() handles deduplication internally
```

**Key Insight**: Both branches pass "recently_asked" list, but:
- **Master**: You have logs to verify it's being passed correctly
- **Monolithic**: Less visibility into agent decision-making

---

## Specs Extraction & Comparison

### Master Branch

**Extraction Action**: `extract_learning_objectives`
```python
counselor.process({
    "action": "extract_learning_objectives",
    "text": user_response,
    "context": project,
    "phase": phase
})
```

**Returns**:
```python
{
    "learning_objectives": [
        {"goal": "Build calculator", "confidence": 0.85},
        {"technology": "Python", "confidence": 0.92},
        {"constraint": "No external libs", "confidence": 0.65}
    ]
}
```

**Filtering**:
```python
high_confidence_specs = [
    spec for spec in extracted_specs
    if spec.get("confidence", 0) >= 0.7  # YOU control threshold
]
```

**Comparison Before Merge**:
```python
existing_goals = project.goals or []           # What's already there
existing_requirements = project.requirements   # For comparison
existing_tech_stack = project.tech_stack       # For comparison
existing_constraints = project.constraints     # For comparison

# Then merge high_confidence_specs and check conflicts
```

**Conflict Detection**:
```python
detector.detect({
    "specs": high_confidence_specs,
    "existing_goals": project.goals,
    "existing_requirements": project.requirements,
    "existing_tech_stack": project.tech_stack,
    "context": project
})
```

**Result**: Explicit conflicts array showing contradictions

### Monolithic-Socrates Branch

**Extraction Method**: `extract_insights` (simpler)
```python
insights = orchestrator.claude_client.extract_insights(
    f"User Input:\n{request.message}\nAssistant Answer:\n{answer}"
)
```

**Returns**:
```python
{
    "goals": ["Build calculator"],
    "requirements": ["Support +, -, *, /"],
    "tech_stack": ["Python"],
    "constraints": ["No external libs"]
}
```

**Key Difference**: NO confidence scores; all-or-nothing extraction

**Comparison**: Direct mode shows specs in modal for user approval

**Conflict Detection**: Delegated to agent, less explicit

---

## Conversation History Structure

### Both Branches Store Messages

```python
{
    "type": "assistant",      # Questions
    "content": "What is...?",
    "phase": "discovery",
    "timestamp": "2026-04-20T21:20:05.378Z",
    "response_turn": 1
}

{
    "type": "user",           # Answers
    "content": "basic calculations",
    "phase": "discovery",
    "timestamp": "2026-04-20T21:20:25.471Z"
}
```

### Key Fields for Deduplication
- `type="assistant"` → Identifies questions
- `phase=current_phase` → Filters to current phase only
- `content` → The actual question text
- `timestamp` → When it was asked

### Storage Method

**Master**:
```python
db.save_project(project)  # Saves everything including conversation_history
```

**Monolithic**:
```python
db.save_project(project)
db.save_conversation_history(project)  # Separate call for history
```

---

## Spec Storage Locations

### Master Branch
```
Specs stored in TWO places:

1. Project Fields (primary)
   project.goals = [...]
   project.requirements = [...]
   project.tech_stack = [...]
   project.constraints = [...]

2. Metadata Table (backup)
   db.save_extracted_specs(
       project_id=...,
       specs=...,
       extraction_method="direct_mode_extraction",
       confidence_score=0.8,
       source_text=...,
       response_turn=...,
       metadata={...}
   )

Benefits:
- Specs resilient to project corruption
- Audit trail of extractions
- Can recover from partial saves
```

### Monolithic-Socrates Branch
```
Specs stored ONCE:

1. Project Fields only
   project.goals = [...]
   project.requirements = [...]
   project.tech_stack = [...]
   project.constraints = [...]

Simpler but:
- Loss of extraction metadata
- No audit trail
- If project save fails, specs lost
```

---

## Conflict Detection Approach

### Master Branch (Explicit)
```
Step 1: Extract new specs with confidence
Step 2: Filter for high-confidence only
Step 3: Merge to project
Step 4: Call detector.detect() explicitly
Step 5: Return conflicts array
```

**Example Conflicts Returned**:
```python
{
    "conflicts": [
        {
            "type": "tech_contradiction",
            "old_value": ["Python 3.8"],
            "new_value": ["Python 3.11"],
            "severity": "warning",
            "description": "Python version conflict"
        }
    ]
}
```

**Control**: You control what gets flagged as conflict

### Monolithic-Socrates Branch (Delegated)
```
Step 1: Extract insights (no confidence)
Step 2: Merge directly
Step 3: Agent handles conflict detection
Step 4: Return agent result
```

**Less explicit**: Agent decides what's a conflict

---

## Summary Table

| Aspect | Master | Monolithic-Socrates |
|--------|--------|-------------------|
| **Spec Extraction** | `extract_learning_objectives` + confidence | `extract_insights` (no confidence) |
| **Filtering** | Confidence >= 0.7 (configurable) | No filtering (all specs saved) |
| **Conflict Detection** | Explicit detector.detect() call | Agent-based |
| **Specs Storage** | Project fields + metadata table | Project fields only |
| **Conversation History** | Type="assistant"/"user" filtering | Role-based filtering |
| **Deduplication** | Explicit "recently_asked" passing | Agent deduplication |
| **Maturity Tracking** | Integrated MaturityCalculator | Optional |
| **User Approval** | Silent (confidence-filtered) | Optional (direct mode) |
| **Logging** | Comprehensive [SECTION] tags | Minimal |
| **Resilience** | High (redundant storage) | Medium |

---

## Why Question Repetition Might Occur

### Possible Root Causes

1. **Deduplication not passing questions**
   ```
   Check: [QUESTION_DEDUP] Passing N previously asked questions
   If 0: Questions not being extracted from conversation_history
   ```

2. **Conversation_history not storing questions**
   ```
   Check: [QUESTION_GEN] added X questions
   If 0: Questions not persisted to conversation_history
   ```

3. **Counselor not respecting "recently_asked"**
   ```
   Check: [QUESTION_GEN] Generated question is IDENTICAL
   If true: Counselor not using deduplication parameter
   ```

4. **Phase not matching**
   ```
   Check: [QUESTION_DEDUP] phase=X!=Y
   If mismatch: Questions from previous phase not filtered
   ```

5. **Database persistence failing**
   ```
   Check: [ANSWER_PROCESSING] Project saved
   If warning: Database changes not persisted
   ```

---

## Recommended Diagnostics

### To Identify Answer Processing Issues
1. Look for `[ANSWER_PROCESSING]` logs
2. Verify "Step 1 Result: Extracted N total specs"
3. Verify "Step 2 Result: N high-confidence specs"
4. Verify "✓ Project saved" message

### To Identify Question Repetition
1. Look for `[QUESTION_DEDUP]` logs
2. Verify "Passing N previously asked questions"
3. Verify "Generated question is new"
4. Check `[QUESTION_GEN] added X questions`

### To Identify Conflict Detection Issues
1. Look for `[ANSWER_PROCESSING]` Step 4
2. Verify "Detected N conflict(s)"
3. Check if conflicts are being returned to frontend

---

## Next Steps

Based on your logs:

1. **If questions repeat**: Check `[QUESTION_DEDUP]` logs to see if questions are being passed to counselor
2. **If specs not extracted**: Check `[ANSWER_PROCESSING] Step 1` to see extraction result
3. **If conflicts not detected**: Check if detector agent is available
4. **If conversation not updating**: Check database persistence logs

Use the comprehensive logging added in commit `b1f13a8` to diagnose the exact point of failure.

