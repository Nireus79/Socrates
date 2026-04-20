# Socrates Diagnostic Guide

## Overview
This guide explains how to use the enhanced logging to diagnose issues with:
1. Answer processing & spec extraction
2. Conflict detection
3. Question deduplication
4. Conversation history management

All logs are prefixed with `[SECTION_NAME]` for easy filtering.

---

## Issue #1: Answer Processing & Spec Extraction

### What Happens
When a user submits an answer in Socratic mode:
1. **Router** (`send_message`) calls orchestrator with `action="process_response"`
2. **Orchestrator** calls `_process_answer_monolithic()`
3. **Step 1**: Counselor extracts specs with confidence scores
4. **Step 2**: Filters for confidence >= 0.7
5. **Step 3**: Merges high-confidence specs into project
6. **Step 4**: Detects conflicts between new and existing specs
7. **Step 5**: Calculates maturity
8. **Step 6**: Saves to conversation history and database

### Log Format
```
[ANSWER_PROCESSING] START: Processing user response for project proj_XXX, phase=discovery
[ANSWER_PROCESSING] User response: basic calculations + - * / ...
[ANSWER_PROCESSING] Step 1: Extracting specs from user response...
[ANSWER_PROCESSING] Step 1 Result: Extracted 5 total specs
[ANSWER_PROCESSING] Step 2 Result: 3 high-confidence specs (filtered from 5)
[ANSWER_PROCESSING] Existing specs in project:
[ANSWER_PROCESSING]   Goals: 2 items - [...]
[ANSWER_PROCESSING]   Requirements: 0 items
[ANSWER_PROCESSING] Step 3 Result: Merged 3 new specs into project
[ANSWER_PROCESSING] Step 4 Result: Detected 1 conflict(s)
[ANSWER_PROCESSING] ✓ Project saved after answer processing
[ANSWER_PROCESSING] SUCCESS: Answer processing complete. Specs merged: 3, Conflicts: 1
```

### Troubleshooting

**Problem**: Specs not being extracted
- **Check**: `Step 1 Result: Extracted 0 total specs`
- **Cause**: Counselor not extracting objectives from user response
- **Action**: Verify counselor agent is available and functional

**Problem**: Specs extracted but not merged
- **Check**: `Step 2 Result: 0 high-confidence specs`
- **Cause**: All extracted specs have confidence < 0.7
- **Action**: Specs were low confidence - this might be expected behavior

**Problem**: Specs not saved to project
- **Check**: `Step 3 Result: Merged 0 new specs`
- **Cause**: No high-confidence specs to merge
- **Action**: Check Step 2 results

**Problem**: Conflicts not detected
- **Check**: `Step 4 Result: Detected 0 conflict(s)` when conflicts expected
- **Cause**:
  - Detector agent not available
  - No actual conflicts between new and existing specs
- **Action**: Check if conflict_detector agent is loaded

**Problem**: Database save failed
- **Check**: `[ANSWER_PROCESSING] WARNING: Failed to save project`
- **Cause**: Database locked or connection issue
- **Action**: Check database logs, ensure no concurrent writes

---

## Issue #2: Question Deduplication

### What Happens
When generating the next question:
1. **Orchestrator** extracts conversation history
2. **Filters** for messages with:
   - `type="assistant"` (questions only)
   - `phase=current_phase` (same phase)
3. **Passes** "recently_asked" list to counselor
4. **Counselor** generates new question avoiding duplicates

### Log Format
```
[QUESTION_DEDUP] Analyzing conversation history for deduplication...
[QUESTION_DEDUP] Total messages in history: 18
[QUESTION_DEDUP] Message 0: Skipped (type=user!=assistant)
[QUESTION_DEDUP] Message 1: Included (type=assistant, phase=discovery, content=What is the main pur...)
[QUESTION_DEDUP] Message 3: Skipped (phase=requirements!=discovery)
[QUESTION_DEDUP] ✓ Passing 5 previously asked questions in discovery phase for deduplication
[QUESTION_DEDUP]   Q1: What is the main purpose of Python calculator?
[QUESTION_DEDUP]   Q2: What would success look like?
[QUESTION_DEDUP]   Q3: What problems does it solve?
```

### Troubleshooting

**Problem**: No previously asked questions found
- **Check**: `No previously asked questions found for phase discovery`
- **Cause**:
  - First question of phase (expected)
  - Conversation history not populated
  - Phase not matching
- **Action**: Check if conversation_history has data and phase field is set

**Problem**: Messages included when they shouldn't be
- **Check**: `Message 2: Included` but message is user response
- **Cause**: Message type not "assistant"
- **Action**: Check message structure - must have `type="assistant"`

**Problem**: Message skipped due to phase mismatch
- **Check**: `phase=requirements!=discovery`
- **Cause**:
  - Phase changed between messages
  - Message from previous phase being incorrectly stored
- **Action**: Verify phase transitions are logged correctly

---

## Issue #3: Question Repetition

### What Happens
After deduplication passes previous questions to counselor:
1. **Counselor** receives list of "recently_asked" questions
2. **Generates** new question different from previously asked
3. **Returns** question to orchestrator
4. **Orchestrator** stores in conversation_history
5. **Router** returns to frontend

### Log Format
```
[QUESTION_GEN] Calling counselor.process() with 5 previously asked questions...
[QUESTION_GEN] Counselor returned: What are the specific operations your calculator supports?
[QUESTION_GEN] ✓ Generated question is new (not in previously asked list)
[QUESTION_GEN] Conversation state AFTER generation: 20 total, 6 questions (added 2 msgs, 1 questions)
```

### Troubleshooting

**Problem**: Question is identical to previously asked
- **Check**: `⚠️ WARNING: Generated question is IDENTICAL to previously asked`
- **Cause**:
  - Counselor not respecting "recently_asked" list
  - Duplicate in database despite deduplication
  - Agent logic issue
- **Action**: Check counselor agent implementation

**Problem**: Question not stored in conversation_history
- **Check**: `⚠️ WARNING: Question NOT stored in conversation_history!`
- **Cause**:
  - Conversation_history not being updated
  - Question stored elsewhere (pending_questions only)
  - Database save failing
- **Action**:
  - Check if question is in pending_questions instead
  - Verify db.save_project() succeeded
  - Check for database errors

**Problem**: Multiple questions generated at once
- **Check**: `added 2 msgs, 2 questions` when expecting only 1
- **Cause**: Counselor generating multiple questions in one call
- **Action**: Verify agent configuration

---

## Issue #4: Conversation History Management

### Storage Locations
Specs and questions are stored in TWO places:

**1. conversation_history** (List of messages)
```python
{
  "type": "assistant",      # Question
  "content": "What is...",
  "phase": "discovery",
  "timestamp": "2026-04-20T...",
  "response_turn": 1
}
```

**2. pending_questions** (Separate tracking)
```python
{
  "question": "What is...",
  "status": "unanswered",  # Or "answered", "skipped"
  "phase": "discovery",
  "timestamp": "..."
}
```

### Deduplication Uses conversation_history

The deduplication logic specifically looks in `conversation_history` with `type="assistant"`, NOT in `pending_questions`.

**If questions repeat:**
1. Check `conversation_history` has questions stored
2. Verify `type="assistant"` and `phase` fields are set
3. Ensure db.save_project() actually persists changes
4. Check if counselor agent is respecting "recently_asked" parameter

---

## Quick Log Filtering

### View Answer Processing Only
```bash
grep "\[ANSWER_PROCESSING\]" logs.txt
```

### View Question Deduplication Only
```bash
grep "\[QUESTION_DEDUP\]" logs.txt
```

### View Question Generation Only
```bash
grep "\[QUESTION_GEN\]" logs.txt
```

### View All Diagnostic Logs
```bash
grep "\[ANSWER_PROCESSING\]\|\[QUESTION_DEDUP\]\|\[QUESTION_GEN\]" logs.txt
```

### View Warnings and Errors
```bash
grep "WARNING\|ERROR\|FAIL" logs.txt | grep -E "\[ANSWER_PROCESSING\]|\[QUESTION_DEDUP\]|\[QUESTION_GEN\]"
```

---

## Testing Workflow

### Test Answer Processing
1. User submits answer: "basic calculations + - * /"
2. Look for: `[ANSWER_PROCESSING] SUCCESS`
3. Verify: Specs extracted and saved
4. Check: Conflicts detected (if any)

### Test Question Deduplication
1. Generate first question
2. User answers
3. Generate next question
4. Look for: `[QUESTION_DEDUP] ✓ Passing N previously asked questions`
5. Verify: Generated question != previously asked

### Test Conversation History
1. Send multiple answers
2. Check: `[ANSWER_PROCESSING] Conversation state AFTER generation`
3. Verify: Message count increases
4. Verify: `type="assistant"` and `phase` fields present

---

## Known Differences from Monolithic-Socrates Branch

### Answer Processing
- **Master**: Calls `extract_learning_objectives` action on counselor
- **Monolithic**: Calls `extract_insights` method directly
- **Status**: Both should work, master has more detailed feedback

### Question Deduplication
- **Master**: Uses fuzzy matching with Jaccard similarity (70% threshold)
- **Monolithic**: Delegates to counselor agent
- **Status**: Master is more aggressive; if duplicates still occur, might need fuzzy matching

### Specs Storage
- **Master**: Stores in both project fields AND metadata table
- **Monolithic**: Stores only in project fields
- **Status**: Master is more resilient to data loss

---

## Next Steps

After reviewing logs:

1. **If specs not extracting**: Verify counselor agent
2. **If questions repeating**: Check if "recently_asked" being passed to agent
3. **If conflicts not detected**: Verify conflict_detector agent availability
4. **If conversation_history not updating**: Verify database persistence

Run the application with these logs, submit some answers and questions, then review the logs to identify which step is failing.

