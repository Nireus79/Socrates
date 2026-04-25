# Critical Architectural Fixes - Comprehensive Plan

**Date:** 2026-04-01
**Status:** ⏳ PLANNING PHASE
**Scope:** Fix ALL remaining broken functionality

---

## Root Cause Analysis

### What's Actually Broken

1. **Question Repetition**
   - Library SocraticCounselor.process() only takes topic + level
   - NO support for conversation_history or asked_questions
   - Generates same questions every time (different wording)
   - Need: Conversation history tracking + question deduplication

2. **Debug Mode Not Working**
   - Toggle endpoint exists but debug info never returned
   - No debug logs collected during request processing
   - Frontend doesn't receive debug output
   - Need: Collect and return debug info in responses

3. **Suggestions Endpoint Empty**
   - Endpoint exists but returns nothing
   - Should analyze last question + provide suggestions
   - Never actually implemented
   - Need: Parse question, generate suggestions, return them

4. **Skipped Questions Not Persisted**
   - Skip endpoint called but no tracking
   - "No pending questions found" error
   - Skipped list not saved to database
   - Need: Track skipped questions on ProjectContext

5. **Library Agents Missing Features**
   - SocraticCounselor doesn't take conversation history
   - No built-in question deduplication
   - No debug mode support
   - No suggestions mechanism
   - Need: Orchestrator wrappers around library agents

---

## Solution Architecture

### Layer 1: Extended ProjectContext (socratic_system/models/project.py)

Add fields for conversation tracking:
- `conversation_history` - Already exists, use it
- `asked_questions` - Questions already posed (with answers)
- `skipped_questions` - Questions user skipped
- `question_cache` - Cache of generated questions
- `last_question_id` - Track current question
- `debug_info` - Collect debug logs during request

### Layer 2: Orchestrator Wrappers (backend/src/socrates_api/orchestrator.py)

Extend library agents:
- Wrap `SocraticCounselor.process()` with history/deduplication logic
- Add question caching mechanism
- Add debug collection during request processing
- Add suggestions generation logic
- Add skipped question tracking

### Layer 3: Router Implementations (backend/src/socrates_api/routers/)

Implement missing endpoints:
- `GET /chat/suggestions` - Generate suggestions from last question
- `POST /chat/skip` - Properly track skipped questions
- Add debug info to all chat responses when debug mode enabled

---

## Implementation Order

### PHASE 1: Extend ProjectContext
**Files:** `socratic_system/models/project.py`
**Work:** Add conversation tracking fields

### PHASE 2: Orchestrator Wrappers
**Files:** `backend/src/socrates_api/orchestrator.py`
**Work:**
- Wrap question generation with deduplication
- Implement question caching
- Implement debug log collection
- Implement suggestions generation

### PHASE 3: Router Implementations
**Files:**
- `backend/src/socrates_api/routers/projects_chat.py`
**Work:**
- Fix skip endpoint to track questions
- Implement suggestions endpoint properly
- Return debug info when enabled

### PHASE 4: Database Persistence
**Files:** `backend/src/socrates_api/database.py`
**Work:**
- Persist skipped questions
- Persist question cache
- Query methods for conversation history

---

## Detailed Specifications

### 1. Extended ProjectContext Fields

```python
# New fields to add:
asked_questions: List[Dict[str, Any]] = Field(default_factory=list)
# Example: [
#   {"id": "q1", "text": "What operations...", "answer": "Add, subtract", "status": "answered"},
#   {"id": "q2", "text": "How to get input...", "answer": None, "status": "pending"},
# ]

skipped_questions: List[str] = Field(default_factory=list)
# Example: ["q3", "q5"] - IDs of questions user skipped

question_cache: Dict[str, Any] = Field(default_factory=dict)
# Example: {"timestamp": "...", "questions": [...], "version": 1}

last_question_id: Optional[str] = None
# Currently displayed question ID

debug_logs: List[Dict[str, Any]] = Field(default_factory=list)
# Collected during request: [{"level": "info", "message": "...", "timestamp": "..."}]
```

### 2. Orchestrator Wrapper Methods

```python
def _generate_questions_deduplicated(
    self,
    topic: str,
    level: str,
    project: ProjectContext,
    current_user: str
) -> List[str]:
    """
    Generate questions avoiding those already asked/skipped.

    1. Call library counselor: counselor.process({"topic": topic, "level": level})
    2. Get returned questions
    3. Filter out: already_asked + skipped + variations (fuzzy match)
    4. If < 3 questions, generate more with different prompting
    5. Cache result on project
    6. Return non-duplicate questions
    """

def _collect_debug_logs(self, request_id: str) -> List[Dict]:
    """Collect all debug logs from request processing"""

def _generate_suggestions(
    self,
    question_text: str,
    project: ProjectContext
) -> List[str]:
    """
    Generate 3-5 suggestions for answering the question.

    1. Analyze question text
    2. Consider project context (goals, requirements, tech_stack)
    3. Generate contextual suggestions
    4. Return them
    """

def _get_conversation_summary(self, project: ProjectContext) -> str:
    """Get summary of conversation for context to agents"""
```

### 3. Router Implementations

```python
# GET /chat/suggestions
- Get project
- Get last_question_id from project
- Find question in asked_questions
- Get question text
- Call orchestrator._generate_suggestions()
- Return suggestions

# POST /chat/skip
- Get project
- Get current pending question (from cache or generate)
- Add question ID to skipped_questions
- Move to next question
- Save project
- Return new question

# GET /chat/question (MODIFIED)
- Generate questions (NEW: use _generate_questions_deduplicated)
- Add to question_cache
- Save pending question info
- If debug_mode: collect debug logs
- Return question + debug info
```

---

## Expected Results After Implementation

### Before
```
User: "What operations?"
System: "What operations..." (Q1)
User answers
System generates new question: "What operations would you want..." (Q2 - SAME TOPIC, rephrased)
User frustrated: "This is the same question!"
```

### After
```
User: "What operations?"
System: "What basic operations..." (Q1)
User answers
System tracks: asked_questions = [Q1]
System generates: "How could you get input..." (Q2 - DIFFERENT TOPIC)
User satisfied: "That's a new question!"
```

### Before
```
User: clicks Skip
System: WARNING - No pending questions found
User confused: "Why doesn't skip work?"
```

### After
```
User: clicks Skip
System: Tracks Q2 in skipped_questions
System generates: "Once you have numbers..." (Q3)
System returns: New question (Q3)
User satisfied: "It worked!"
```

### Before
```
User: enables Debug Mode
API: Returns success=true
Frontend: No debug info displayed
User: "Why is debug mode not working?"
```

### After
```
User: enables Debug Mode
API: Collects debug logs during processing
Response includes: debug_info = [
  {"level": "info", "message": "Generating questions..."},
  {"level": "debug", "message": "Filtered 2 duplicates"},
  ...
]
Frontend: Displays debug console with all logs
User satisfied: "Now I can see what's happening!"
```

---

## Files to Modify

1. **socratic_system/models/project.py**
   - Add asked_questions field
   - Add skipped_questions field
   - Add question_cache field
   - Add last_question_id field
   - Add debug_logs field

2. **backend/src/socrates_api/orchestrator.py**
   - Add _generate_questions_deduplicated()
   - Add _collect_debug_logs()
   - Add _generate_suggestions()
   - Add _get_conversation_summary()
   - Modify _handle_socratic_counselor() to use deduplicated questions
   - Add debug log collection during request processing

3. **backend/src/socrates_api/routers/projects_chat.py**
   - Modify get_question() to use deduplicated generation
   - Implement get_suggestions() endpoint properly
   - Implement skip_question() to track skipped
   - Add debug info to all responses when enabled

4. **backend/src/socrates_api/database.py**
   - Add save methods for asked_questions, skipped_questions
   - Add query methods for conversation history

---

## Success Criteria

✅ Questions never repeat (different topics each time)
✅ Skipped questions saved and tracked
✅ Skip endpoint works properly
✅ Suggestions endpoint returns 3-5 contextual suggestions
✅ Debug mode returns debug logs in response
✅ Conversation history tracked and queryable
✅ All data persisted to database
✅ No breaking changes to existing APIs

---

## Estimated Effort

- Phase 1 (ProjectContext): 30 minutes
- Phase 2 (Orchestrator): 2 hours
- Phase 3 (Routers): 1.5 hours
- Phase 4 (Database): 1 hour
- Testing & Verification: 1 hour

**Total: ~5.5 hours**

---

## Next: Begin Implementation
