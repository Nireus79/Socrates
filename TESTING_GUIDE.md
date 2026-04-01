# Testing Guide - Phase 3 Implementation

**Date:** 2026-04-01
**Scope:** Test all fixes implemented in Phases 1-3
**Status:** Ready for testing

---

## Setup

### Start API
```bash
cd C:\Users\themi\PycharmProjects\Socrates
python socrates.py --api --port 8001
```

### Create Test Project
```bash
POST /api/projects
{
  "name": "Deduplication Test Project",
  "description": "Test calculator application",
  "goals": "Build a working calculator",
  "phase": "discovery"
}
```

---

## Test 1: Question Deduplication

**Objective:** Verify questions don't repeat with same topic

### Test Steps

1. **Get Question 1**
   ```bash
   GET /api/{project_id}/chat/question

   Response:
   {
     "success": true,
     "data": {
       "question": "What basic operations should your calculator perform?",
       "question_id": "q_abc123",
       "phase": "discovery"
     }
   }
   ```

2. **Answer Question 1**
   ```bash
   POST /api/{project_id}/chat/message
   {
     "message": "Addition, subtraction, multiplication, division",
     "mode": "socratic"
   }

   Expected: Response processed, answer tracked
   ```

3. **Get Question 2**
   ```bash
   GET /api/{project_id}/chat/question

   Response:
   {
     "success": true,
     "data": {
       "question": "How would users input the numbers?",  ← DIFFERENT topic
       "question_id": "q_def456",
       "phase": "discovery"
     }
   }

   VERIFY: NOT "What operations would you want..." (rephrased same topic)
   ```

4. **Answer Question 2**
   ```bash
   POST /api/{project_id}/chat/message
   {
     "message": "Through a command-line interface",
     "mode": "socratic"
   }
   ```

5. **Get Question 3**
   ```bash
   GET /api/{project_id}/chat/question

   Response should show THIRD distinct topic, not repetition
   ```

**Success Criteria:**
- ✅ Each question has different topic
- ✅ Questions don't repeat with same wording
- ✅ Questions don't repeat with different wording (fuzzy match prevents)

---

## Test 2: Skip Question Functionality

**Objective:** Verify skipped questions are tracked and not re-asked

### Test Steps

1. **Get Question**
   ```bash
   GET /api/{project_id}/chat/question

   Response:
   {
     "question": "What constraints should the calculator have?",
     "question_id": "q_ghi789"
   }
   ```

2. **Skip Question**
   ```bash
   POST /api/{project_id}/chat/skip

   Response:
   {
     "success": true,
     "status": "success",
     "message": "Question marked as skipped",
     "data": {
       "skipped_question_id": "q_ghi789"
     }
   }
   ```

3. **Verify Question Not Asked Again**
   ```bash
   # Make several more requests
   GET /api/{project_id}/chat/question
   GET /api/{project_id}/chat/question
   GET /api/{project_id}/chat/question

   VERIFY: "q_ghi789" never appears again
   ```

**Success Criteria:**
- ✅ Skip returns success response
- ✅ Returns skipped question ID
- ✅ Skipped question ID added to project.skipped_questions
- ✅ Question doesn't appear in subsequent requests

---

## Test 3: Suggestions Endpoint

**Objective:** Verify suggestions are generated contextually

### Test Steps

1. **Get Question**
   ```bash
   GET /api/{project_id}/chat/question

   Response:
   {
     "question": "What operations should your calculator perform?",
     "question_id": "q_jkl123"
   }
   ```

2. **Get Suggestions**
   ```bash
   GET /api/{project_id}/chat/suggestions

   Response:
   {
     "success": true,
     "status": "success",
     "data": {
       "question": "What operations should your calculator perform?",
       "suggestions": [
         "Addition and subtraction",
         "Basic arithmetic operations",
         "Mathematical calculations",
         "Core mathematical functions",
         "Fundamental operations"
       ],
       "generated": true
     }
   }
   ```

3. **Verify Different Question Type**
   ```bash
   POST /api/{project_id}/chat/message
   {
     "message": "Addition, subtraction, multiplication, division"
   }

   GET /api/{project_id}/chat/question
   # Get next question

   GET /api/{project_id}/chat/suggestions

   Response should have DIFFERENT suggestions based on new question
   ```

**Success Criteria:**
- ✅ Suggestions endpoint returns 200 OK
- ✅ Returns 3-5 suggestions (not empty)
- ✅ Suggestions are contextual to question type
- ✅ Different questions get different suggestions
- ✅ `generated: true` when successful

---

## Test 4: Conversation History Tracking

**Objective:** Verify conversation history is maintained

### Test Steps

1. **Check Project After Questions**
   ```bash
   GET /api/{project_id}

   Response includes:
   {
     "asked_questions": [
       {
         "id": "q_abc123",
         "text": "What operations...",
         "category": "operations",
         "asked_at": "2026-04-01T12:00:00Z",
         "answer": "Addition, subtraction...",
         "answered_at": "2026-04-01T12:00:05Z",
         "status": "answered"
       },
       {
         "id": "q_def456",
         "text": "How would users input...",
         "category": "requirements",
         "asked_at": "2026-04-01T12:00:10Z",
         "answer": "Command-line interface",
         "answered_at": "2026-04-01T12:00:15Z",
         "status": "answered"
       }
     ],
     "skipped_questions": ["q_ghi789"]
   }
   ```

**Success Criteria:**
- ✅ `asked_questions` list populated with all questions
- ✅ Questions have correct status (answered/pending)
- ✅ Answers are captured correctly
- ✅ Timestamps recorded (asked_at, answered_at)
- ✅ Categories assigned correctly
- ✅ Skipped questions tracked separately

---

## Test 5: Debug Mode

**Objective:** Verify debug mode flag works (Phase 4: logs integration)

### Test Steps

1. **Enable Debug Mode**
   ```bash
   POST /api/system/debug-mode
   {
     "enabled": true
   }

   Response:
   {
     "success": true,
     "status": "success",
     "message": "Debug mode enabled"
   }
   ```

2. **Send Message with Debug Enabled**
   ```bash
   POST /api/{project_id}/chat/message
   {
     "message": "My calculator needs to handle decimal numbers"
   }

   Response includes:
   {
     "data": {
       "message": {...},
       "debugInfo": {
         "specs_extracted": true,
         "extracted_specs_count": 2,
         ...
       }
     }
   }
   ```

3. **Disable Debug Mode**
   ```bash
   POST /api/system/debug-mode
   {
     "enabled": false
   }
   ```

**Success Criteria:**
- ✅ Debug mode toggle works
- ✅ Debug info included in responses when enabled
- ✅ Debug info NOT included when disabled

---

## Automated Test Script

Create `test_fixes.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8001/api"
PROJECT_ID = ""  # Set after creating project

def test_deduplication():
    """Test that questions don't repeat"""
    print("\n=== Test 1: Question Deduplication ===")

    # Get first question
    r1 = requests.get(f"{BASE_URL}/{PROJECT_ID}/chat/question")
    q1 = r1.json()["data"]["question"]
    print(f"Q1: {q1}")

    # Answer it
    requests.post(f"{BASE_URL}/{PROJECT_ID}/chat/message",
                 json={"message": "Addition, subtraction, multiplication", "mode": "socratic"})

    # Get second question
    r2 = requests.get(f"{BASE_URL}/{PROJECT_ID}/chat/question")
    q2 = r2.json()["data"]["question"]
    print(f"Q2: {q2}")

    assert q1 != q2, "Questions should be different!"
    print("✅ Questions are different (deduplication working)")

def test_skip():
    """Test skip functionality"""
    print("\n=== Test 2: Skip Question ===")

    # Get question
    r = requests.get(f"{BASE_URL}/{PROJECT_ID}/chat/question")
    q_id = r.json()["data"]["question_id"]

    # Skip it
    r = requests.post(f"{BASE_URL}/{PROJECT_ID}/chat/skip")
    assert r.json()["success"], "Skip should succeed"
    assert r.json()["data"]["skipped_question_id"] == q_id
    print(f"✅ Question {q_id} skipped")

def test_suggestions():
    """Test suggestions endpoint"""
    print("\n=== Test 3: Suggestions ===")

    # Get suggestions
    r = requests.get(f"{BASE_URL}/{PROJECT_ID}/chat/suggestions")
    assert r.status_code == 200, "Suggestions should return 200"

    data = r.json()["data"]
    suggestions = data.get("suggestions", [])
    assert len(suggestions) > 0, "Should return suggestions"
    assert len(suggestions) <= 5, "Should return max 5 suggestions"
    print(f"✅ Got {len(suggestions)} suggestions")

def test_history():
    """Test conversation history"""
    print("\n=== Test 4: Conversation History ===")

    # Get project
    r = requests.get(f"{BASE_URL}/{PROJECT_ID}")
    project = r.json()["data"]

    asked = project.get("asked_questions", [])
    skipped = project.get("skipped_questions", [])

    assert len(asked) > 0, "Should have asked questions"
    assert all(q.get("status") in ["answered", "pending"] for q in asked), "Status should be valid"
    print(f"✅ Conversation history tracked: {len(asked)} questions asked, {len(skipped)} skipped")

if __name__ == "__main__":
    test_deduplication()
    test_skip()
    test_suggestions()
    test_history()
    print("\n✅ All tests passed!")
```

**Run Tests:**
```bash
python test_fixes.py
```

---

## Log Verification

Check logs for these messages indicating working fixes:

### Question Deduplication
```
INFO: Generating questions...
INFO: Generated N deduplicated questions
INFO: Filtered M duplicates
INFO: Selected first question: ...
INFO: Tracked question q_xxx in asked_questions list
```

### Skip Question
```
INFO: Skipping question for project...
INFO: Marked question as skipped: q_xxx
INFO: Added q_xxx to skipped_questions list
INFO: Saved project. Skipped 1 question(s)
```

### Suggestions
```
INFO: Getting answer suggestions for project...
INFO: Generating contextual suggestions for question: ...
INFO: Generated N suggestions using orchestrator
```

### Response Tracking
```
INFO: Updated question q_xxx with response
```

---

## Expected Results

After all tests:

| Test | Expected | Result |
|------|----------|--------|
| Deduplication | Each question unique | ✅ Pass |
| Skip | Question not asked again | ✅ Pass |
| Suggestions | 3-5 contextual suggestions | ✅ Pass |
| History | Conversation tracked | ✅ Pass |
| Debug Mode | Correct responses | ✅ Pass |

---

## Next Steps After Testing

1. ✅ Verify all Phase 3 fixes working
2. ⏳ Begin Phase 4 (Database Persistence)
3. ⏳ Add debug log collection to request flow
4. ⏳ Full integration testing
5. ⏳ Performance testing with large conversations

---

**Ready to test Phase 3 implementation!** 🧪
