# Fix #4: Question Deduplication - Architecture Decision Analysis

**Status**: Architecture decision ready for implementation
**Based on**: Investigation of Monolithic-Socrates branch (socratic_system/agents/socratic_counselor.py)
**Recommendation**: Adopt "Hybrid Approach" pattern

---

## Problem Summary

Currently on Master branch:
1. Questions are stored in `conversation_history` (monolithic pattern)
2. Question deduplication extracts from `conversation_history`
3. BUT: SocraticCounselor has internal logic to return "existing unanswered question"
4. When counselor returns unanswered question, it's not stored in `conversation_history`
5. Result: Question repeats indefinitely because counselor keeps returning the same unanswered question

---

## Monolithic-Socrates Solution: "Hybrid Approach"

The Monolithic-Socrates branch (which is newer/more advanced) uses a **Hybrid Approach** that maintains **BOTH** data structures:

### Architecture Overview

```
conversation_history (single source of truth for dialogue flow)
    ├─ Messages with type="user" (user responses)
    ├─ Messages with type="assistant" (questions asked)
    └─ Messages with type="assistant" marked with phase and timestamp

pending_questions (unified question tracking)
    ├─ Question ID
    ├─ Question text
    ├─ Status: "unanswered" | "answered" | "skipped"
    ├─ Phase
    └─ Timestamps for creation/answer/skip
```

### The Key Logic (from Monolithic-Socrates)

**When generating a question:**

```python
# HYBRID APPROACH: Check for existing unanswered question before generating new one
# This prevents double question generation (unless force_refresh is set)
if not force_refresh and project.pending_questions:
    unanswered = [q for q in project.pending_questions if q.get("status") == "unanswered"]
    if unanswered:
        # Return the first unanswered question instead of generating new
        return {
            "status": "success",
            "question": unanswered[0].get("question"),
            "existing": True,  # Signal to frontend: this is existing, not newly generated
        }
```

**When generating a new question:**

```python
# Extract previously asked questions for deduplication
previously_asked_questions = []
if project.conversation_history:
    for msg in project.conversation_history:
        if msg.get("type") == "assistant" and msg.get("phase") == project.phase:
            previously_asked_questions.append(msg.get("content", ""))

# Pass to counselor for deduplication
question = self._generate_dynamic_question(
    project,
    context,
    len(phase_questions),
    current_user,
    previously_asked_questions=previously_asked_questions
)

# Store NEW question in conversation_history
project.conversation_history.append({
    "timestamp": datetime.datetime.now().isoformat(),
    "type": "assistant",
    "content": question,
    "phase": project.phase,
    "question_number": len(phase_questions) + 1,
})

# HYBRID APPROACH: Also store in pending_questions for unified tracking
project.pending_questions.append({
    "id": f"q_{uuid.uuid4().hex[:8]}",
    "question": question,
    "phase": project.phase,
    "status": "unanswered",
    "created_at": datetime.datetime.now().isoformat(),
    "answer": None,
})

self.database.save_project(project)
```

---

## Why This Works

### Before (Current Master - BROKEN):

```
1. Ask Question 1 → Stored in conversation_history ONLY
2. User answers → Deduplication extracts Q1 from conversation_history
3. Generate Question 2 → Passed ["Q1"] to counselor
4. Counselor checks internal state:
   - "I have Q1 in my pending list and it's unanswered"
   - Returns: "Q1 instead of generating Q2"
5. Q1 returned but NOT stored in conversation_history
6. Next request: Deduplication still only sees ["Q1"]
7. LOOP: Counselor keeps returning Q1 forever
```

### After (Hybrid Approach - FIXED):

```
1. Ask Question 1:
   - Store in conversation_history
   - Store in pending_questions with status="unanswered"

2. User answers:
   - Deduplication extracts ["Q1"] from conversation_history
   - No need to generate: pending_questions has Q1 with status="unanswered"

3. Generate Question 2 (with force_refresh=true after answer):
   - Check pending_questions for unanswered
   - Passed ["Q1"] to counselor
   - Counselor respects deduplication
   - Returns NEW Q2
   - Stored in BOTH conversation_history AND pending_questions

4. Next request:
   - Check pending_questions for unanswered: finds Q2
   - Returns Q2 (existing, not generating)
   - OR generate Q3 if Q2 answered (force_refresh=true)
```

---

## Implementation Strategy for Master Branch

**Option 1: Adopt Full Hybrid Approach** (Recommended)

This is the fix recommended based on Monolithic-Socrates evidence:

### Step 1: Update `_orchestrate_question_generation()` in orchestrator.py

Before generating new question, check if unanswered exists in pending_questions:

```python
def _orchestrate_question_generation(self, project, user_id, force_refresh=False):
    """
    Generate next question with hybrid approach.
    Check for unanswered question before generating new one.
    """

    # HYBRID APPROACH: Check for existing unanswered question
    if not force_refresh and project.pending_questions:
        unanswered = [
            q for q in project.pending_questions
            if q.get("status") == "unanswered" and q.get("phase") == project.phase
        ]
        if unanswered:
            logger.info(f"Returning existing unanswered question: {unanswered[0]['question']}")
            return {
                "status": "success",
                "question": unanswered[0]["question"],
                "question_id": unanswered[0].get("id", ""),
                "existing": True,  # Signal: not newly generated
            }

    # Generate new question with deduplication
    # ... existing generation code ...

    # NEW: Store in BOTH structures
    project.conversation_history.append({
        "type": "assistant",
        "content": question,
        "phase": project.phase,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Store in pending_questions for unified tracking
    import uuid
    question_id = f"q_{uuid.uuid4().hex[:8]}"
    project.pending_questions.append({
        "id": question_id,
        "question": question,
        "phase": project.phase,
        "status": "unanswered",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "answer": None,
        "answered_at": None,
    })

    # Save project with both structures updated
    self.database.save_project(project)

    return {
        "status": "success",
        "question": question,
        "question_id": question_id,
        "existing": False,  # Signal: newly generated
    }
```

### Step 2: Update answer processing to mark question as answered

When user answers a question, update status in pending_questions:

```python
# In _process_answer_monolithic():
# After processing answer, mark question as answered

if project.pending_questions:
    for q in project.pending_questions:
        if q.get("phase") == project.phase and q.get("status") == "unanswered":
            # Mark as answered when we process answer in this phase
            q["status"] = "answered"
            q["answered_at"] = datetime.now(timezone.utc).isoformat()
            break

self.database.save_project(project)
```

### Step 3: Update question generation to force refresh after answer

The frontend should pass `force_refresh=true` when requesting next question after answer:

```python
# In projects_chat.py get_question() endpoint:
force_refresh = request.json.get("force_refresh", False)  # true after user answers

result = self.orchestrator.generate_question(
    project_id=project_id,
    user_id=user_id,
    force_refresh=force_refresh  # Force generation of new question
)
```

---

## Benefits of Hybrid Approach

1. **Eliminates Question Repetition**:
   - Checks pending_questions first before generating
   - If unanswered exists, returns it
   - Only generates new when all answered

2. **Respects Counselor Logic**:
   - Counselor can still return existing unanswered questions internally
   - But orchestrator handles this at the higher level
   - No lost/duplicate questions

3. **Backward Compatible**:
   - Code that reads pending_questions still works
   - Code that reads conversation_history still works
   - Both stay in sync

4. **Better Question Tracking**:
   - Question status clearly tracked (unanswered/answered/skipped)
   - Better audit trail
   - Can detect when questions are skipped

5. **Supports Counselor's Design**:
   - The SocraticCounselor has logic to return existing unanswered questions
   - This IS the intended behavior, just needs to be properly coordinated

---

## Comparison: Master vs Monolithic-Socrates

| Aspect | Master (Current) | Monolithic-Socrates | Recommended |
|--------|------------------|---------------------|------------|
| **Storage** | conversation_history only | Both structures | Hybrid |
| **Deduplication** | Extract from conv_history | Extract from conv_history | Extract from conv_history |
| **Unanswered Check** | Not implemented | Check pending_questions | Check pending_questions |
| **Question Generation** | Direct to counselor | With unanswered check | With unanswered check |
| **Question Repetition** | 🔴 BROKEN | 🟢 WORKS | 🟢 WORKS |
| **Code Complexity** | Lower | Higher | Medium |
| **Backward Compatible** | N/A | N/A | ✓ YES |

---

## Testing After Implementation

### Test Case 1: No Question Repetition

```
1. Generate Question 1
2. User answers
3. Generate Question 2
4. User answers
5. Generate Question 3

Expected: All 3 questions are DIFFERENT
Actual (before fix): Questions 1, 2, 3 might all be "What is the main purpose..."
```

### Test Case 2: Existing Unanswered Question Returned

```
1. Generate Question 1
2. DON'T answer
3. Request question again (without force_refresh)

Expected: Same Question 1 returned (existing=true)
Actual (before fix): New question generated or repetition
```

### Test Case 3: New Question After Answer

```
1. Generate Question 1
2. User answers
3. Request question with force_refresh=true

Expected: Question 2 is NEW and DIFFERENT from Q1
Actual (before fix): Q1 repeats
```

---

## Migration Path

1. **Phase 1**: Keep Master's current approach but add hybrid logic
2. **Phase 2**: Ensure all question generation goes through _orchestrate_question_generation()
3. **Phase 3**: Update frontend to pass force_refresh=true after user answers
4. **Phase 4**: Monitor logs for SUCCESS indicators

---

## Files to Modify for This Fix

1. **orchestrator.py**:
   - Update `_orchestrate_question_generation()` to check pending_questions first
   - Update answer processing to mark questions as answered in pending_questions
   - Ensure both structures are populated

2. **projects_chat.py**:
   - Update `get_question()` endpoint to pass force_refresh parameter
   - Update `send_message()` endpoint to set force_refresh=true after processing answer

3. **Frontend** (if needed):
   - Ensure question generation request includes force_refresh flag

---

## Conclusion

The **Hybrid Approach** is the proven solution used in Monolithic-Socrates. It:
- ✓ Solves question repetition
- ✓ Respects counselor's internal design
- ✓ Maintains backward compatibility
- ✓ Provides better question tracking
- ✓ Is more resilient to data loss

**Recommendation**: Implement this approach as described in Step 1-3 above.

