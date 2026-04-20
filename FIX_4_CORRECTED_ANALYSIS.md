# Fix #4: Question Deduplication - CORRECTED Analysis

**Status**: Corrected based on deeper investigation of Monolithic-Socrates
**Key Insight**: pending_questions is NOT just for legacy compatibility - it's the QUESTION LIFECYCLE TRACKER

---

## The Proper Monolithic-Socrates Approach

### What I Missed Initially

Monolithic-Socrates doesn't just check for existing questions - it implements **full question lifecycle management** using `pending_questions`:

**Question Statuses**:
- `"unanswered"` - Question asked, waiting for user response
- `"answered"` - User has responded to the question
- `"skipped"` - User chose not to answer at this time
- Can be recovered with special command (e.g., `/reopen` or `/unanswered`)

### The Complete Lifecycle

```
Generated Question
    ↓
pending_questions.append({
    "id": "q_abc123",
    "question": "What is...?",
    "status": "unanswered",  ← Can be skipped or answered
    "phase": "discovery"
})
    ↓
User Responds
    ↓
pending_questions[index].status = "answered"
    ↓
User Skips
    ↓
pending_questions[index].status = "skipped"
    ↓
User Wants to Recover (via /command)
    ↓
pending_questions[index].status = "unanswered"  ← Back to pending
```

### The Core Logic

**When generating next question**:

```python
# First, check if ANY unanswered questions exist
if project.pending_questions:
    unanswered = [q for q in project.pending_questions
                  if q.get("status") == "unanswered"]
    if unanswered:
        # Return one of the unanswered questions instead of generating new
        return unanswered[0]  # User should answer this before getting new one

# Only if NO unanswered questions exist, generate new question
new_question = counselor.generate_question(...)

# Store with full lifecycle tracking
pending_questions.append({
    "id": generate_id(),
    "question": new_question,
    "status": "unanswered",  # Start in unanswered state
    "phase": current_phase,
    "created_at": now(),
    "answered_at": None,
    "skipped_at": None,
})
```

**Key Insight**: `pending_questions` is the **source of truth for question state**, not just a fallback.

---

## Why This Prevents Question Repetition

### The Problem (Current Master)

```
1. Generate Q1 → stored in conversation_history
2. User answers → no status tracking
3. Next request → Counselor has internal logic
   → "I see an unanswered question, return it"
   → Returns Q1
4. Q1 returned but NOT marked as answered
5. Next request → Q1 returns again
6. LOOP: Q1 forever
```

**Root cause**: No formal status tracking, counselor's internal state doesn't sync with storage.

### The Solution (Monolithic-Socrates)

```
1. Generate Q1 → pending_questions: {"status": "unanswered"}
2. User answers → pending_questions: {"status": "answered"}
3. Next request → Check pending_questions first
   → No unanswered questions
   → Generate Q2
4. Q2 stored → pending_questions: {"status": "unanswered"}
5. Next request → Q2 is unanswered, return it
6. User answers Q2 → status = "answered"
7. Next request → No unanswered, generate Q3
```

**Key**: Explicit status tracking prevents confusion.

---

## What Should Master Branch Adopt

### NOT Just "Return Existing"

The pattern is NOT:
```python
# WRONG - Too simplistic
if has_unanswered:
    return unanswered[0]
```

### BUT Full Lifecycle Management

The pattern IS:
```python
# RIGHT - Complete state tracking

# 1. Before generating NEW question, check status
if project.pending_questions:
    unanswered = [q for q in project.pending_questions
                  if q.get("status") == "unanswered"]
    if unanswered:
        # Return unanswered question to user
        # User must answer or skip before getting new question
        return {
            "question": unanswered[0]["question"],
            "question_id": unanswered[0]["id"],
            "type": "existing_unanswered"  # Signal: this is existing
        }

# 2. Only generate new when all are answered/skipped
new_question = counselor.generate_question(...)

# 3. Store with EXPLICIT STATUS
question_id = generate_id()
project.pending_questions.append({
    "id": question_id,
    "question": new_question,
    "phase": current_phase,
    "status": "unanswered",      # ← EXPLICIT STATE
    "created_at": datetime.now(),
    "answered_at": None,
    "skipped_at": None,
})

# 4. Store in conversation_history for dialogue flow
project.conversation_history.append({
    "type": "assistant",
    "content": new_question,
    "phase": current_phase,
    "question_id": question_id  # Link to pending_questions
})

self.database.save_project(project)
```

---

## The Two Data Structures and Their Roles

### conversation_history
- **Purpose**: Dialogue flow record
- **Content**: Who said what, when
- **Used for**:
  - Showing dialogue to user
  - Context for next question
  - Deduplication (extracting previously asked)
- **Message types**: `type="user"` and `type="assistant"`

### pending_questions
- **Purpose**: Question lifecycle and recovery
- **Content**: Question text, ID, status, timestamps
- **Used for**:
  - Checking if unanswered questions exist
  - Tracking status (answered/unanswered/skipped)
  - Question recovery (user can reopen skipped)
  - Determining if new question needed
- **Statuses**: `"unanswered"`, `"answered"`, `"skipped"`

### Why Both?

1. **conversation_history** = Linear dialogue record (what happened)
2. **pending_questions** = Question state machine (current status)

They complement each other but serve different purposes.

---

## Implementation for Master Branch

### Required Changes

#### 1. When Answering a Question

```python
# In _process_answer_monolithic():

# After processing answer, mark question as answered
if project.pending_questions:
    for q in project.pending_questions:
        if (q.get("phase") == current_phase and
            q.get("status") == "unanswered"):
            q["status"] = "answered"
            q["answered_at"] = datetime.now(timezone.utc).isoformat()
            break

self.database.save_project(project)
```

#### 2. When Generating Next Question

```python
# In _orchestrate_question_generation():

# FIRST: Check for unanswered questions
if project.pending_questions:
    unanswered = [q for q in project.pending_questions
                  if (q.get("status") == "unanswered" and
                      q.get("phase") == current_phase)]
    if unanswered:
        logger.info(f"Returning unanswered question: {unanswered[0]['question']}")
        return {
            "status": "success",
            "question": unanswered[0]["question"],
            "question_id": unanswered[0]["id"],
            "is_existing": True  # Signal: not newly generated
        }

# ONLY if no unanswered, generate new
# ... (existing generation code) ...

# Store BOTH with status
import uuid
question_id = f"q_{uuid.uuid4().hex[:8]}"

# In conversation_history (dialogue record)
project.conversation_history.append({
    "type": "assistant",
    "content": question,
    "phase": current_phase,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "question_id": question_id  # Link to pending_questions
})

# In pending_questions (state tracking)
project.pending_questions.append({
    "id": question_id,
    "question": question,
    "phase": current_phase,
    "status": "unanswered",  # ← EXPLICIT STATUS
    "created_at": datetime.now(timezone.utc).isoformat(),
    "answered_at": None,
    "skipped_at": None,
})

self.database.save_project(project)

return {
    "status": "success",
    "question": question,
    "question_id": question_id,
    "is_existing": False  # Signal: newly generated
}
```

#### 3. Support Skip/Reopen Operations

```python
# Add skip_question method
def skip_question(self, project, question_id: str):
    """User skips a question for now"""
    for q in project.pending_questions or []:
        if q["id"] == question_id:
            q["status"] = "skipped"
            q["skipped_at"] = datetime.now(timezone.utc).isoformat()
            self.database.save_project(project)
            return {"status": "success"}
    return {"status": "error", "message": "Question not found"}

# Add reopen_question method
def reopen_question(self, project, question_id: str):
    """User wants to answer a previously skipped question"""
    for q in project.pending_questions or []:
        if q["id"] == question_id:
            q["status"] = "unanswered"
            q["skipped_at"] = None
            self.database.save_project(project)
            return {"status": "success"}
    return {"status": "error", "message": "Question not found"}
```

#### 4. Support /pending Command (Show Unanswered Questions)

```python
def list_pending_questions(self, project):
    """Return all unanswered and skipped questions for recovery"""
    pending = []

    # Include both unanswered (to answer) and skipped (to recover)
    for q in project.pending_questions or []:
        if q["status"] in ["unanswered", "skipped"]:
            pending.append({
                "id": q["id"],
                "question": q["question"],
                "phase": q["phase"],
                "status": q["status"],
                "created_at": q["created_at"],
                "skipped_at": q.get("skipped_at"),
            })

    return {
        "status": "success",
        "pending_questions": pending,
        "total": len(pending),
        "unanswered": len([q for q in pending if q["status"] == "unanswered"]),
        "skipped": len([q for q in pending if q["status"] == "skipped"]),
    }
```

---

## Testing After Implementation

### Test 1: No Question Repetition

```
1. Get Question 1
2. Answer Question 1
3. Get Question 2
4. Answer Question 2
5. Get Question 3

EXPECTED: All 3 different
VERIFY: pending_questions shows status="answered" for Q1 and Q2
```

### Test 2: Return Existing Unanswered

```
1. Get Question 1
2. DON'T answer (just request question again immediately)
3. Get Question ?

EXPECTED: Same Question 1 returned (is_existing=true)
ACTUAL: With proper status tracking, Q1 status="unanswered" still, so return Q1
```

### Test 3: Skip and Recover

```
1. Get Question 1
2. Skip Question 1
3. Run /pending command

EXPECTED: Shows Q1 with status="skipped"
4. Reopen Q1
5. Get Question ?

EXPECTED: Returns Q1 to answer (status changed back to "unanswered")
```

### Test 4: Answer Tracking

```
1. Get Question 1
2. Answer Question 1
3. Check pending_questions

EXPECTED: Q1 has status="answered" with answered_at timestamp
```

---

## Key Differences from My Initial Analysis

| Aspect | Initial Understanding | Corrected Understanding |
|--------|----------------------|------------------------|
| **pending_questions purpose** | Legacy fallback for compatibility | PRIMARY question state tracker |
| **Status tracking** | Not implemented | CRITICAL - answered/unanswered/skipped |
| **Check before generate** | Simple existence check | Check status="unanswered" |
| **Skip support** | Not mentioned | IMPORTANT - users can skip |
| **Recovery** | Not mentioned | IMPORTANT - users can reopen skipped |
| **Completeness** | Oversimplified | Full lifecycle management |

---

## Why This Prevents Repetition

**Simple**: Once a question is marked `status="answered"`, it will NEVER be returned again because:
1. Check for unanswered questions → Only finds status="unanswered"
2. Answered questions are filtered out
3. Only generates new when no unanswered remain

No confusion between counselor's internal state and database state.

---

## Summary

The correct approach is:
- ✓ **conversation_history**: Dialogue record (monolithic pattern)
- ✓ **pending_questions**: Question state machine with full lifecycle
- ✓ Before generating new: Check for status="unanswered"
- ✓ When answering: Mark status="answered"
- ✓ Support skip: status="skipped"
- ✓ Support recovery: status change from "skipped" → "unanswered"

This is the PROVEN pattern from Monolithic-Socrates that prevents question repetition while maintaining user flexibility to skip and recover questions.

