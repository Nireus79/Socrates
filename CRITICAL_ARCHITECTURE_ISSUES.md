# Socrates Critical Architecture Issues - Complete Documentation

**Status**: 97% weekly token limit reached. This document captures all investigation and work done.
**Last Updated**: 2026-03-28
**Session**: Continued from previous context on debugging Socratic question generation

---

## Executive Summary

Socrates system has three critical architectural problems:

1. **Custom SocraticCounselor implementation completed** ✅ - Uses Claude for dynamic question generation
2. **Question extraction logic fixed** ✅ - Extracts from array format returned by library
3. **LLM connection broken for users** ❌ - System only uses server's API key, not user-specific keys
4. **User API key infrastructure incomplete** ❌ - Database and orchestrator handlers missing

---

## Part 1: Work Completed This Session

### 1.1 Problem Identified: Hardcoded Questions

**Original Issue**: The system was returning generic hardcoded template questions instead of Claude-generated context-aware questions.

**Root Cause**: The `socratic_agents` library's `SocraticCounselor` class accepts an `llm_client` parameter but its `_generate_guiding_questions()` method was never using it - just returning hardcoded templates.

**Solution Implemented**: Created a custom `SocraticCounselor` subclass in `orchestrator.py` (lines 14-88) that:
- Extends `BaseSocraticCounselor` (imported from `socratic_agents.SocraticCounselor`)
- Overrides `_generate_guiding_questions()` to check if `llm_client` exists
- If yes: calls `_generate_dynamic_questions()` which uses Claude via `self.llm_client.generate_response()`
- If no: falls back to parent class hardcoded templates

**Code Location**: `backend/src/socrates_api/orchestrator.py` lines 14-88

**Implementation Details**:
```python
class SocraticCounselor(BaseSocraticCounselor):
    def _generate_guiding_questions(self, topic: str, level: str) -> list:
        if self.llm_client:
            return self._generate_dynamic_questions(topic, level)
        return super()._generate_guiding_questions(topic, level)

    def _generate_dynamic_questions(self, topic: str, level: str) -> list:
        # Builds prompt, calls self.llm_client.generate_response(prompt)
        # Tries to parse JSON array response
        # Falls back to parsing lines
        # Ultimate fallback: returns template questions if all fails
```

### 1.2 Problem Identified: Question Format Mismatch

**Issue**: The orchestrator returned questions in a `"questions"` array field, but the endpoint expected a `"question"` string field, causing extraction failures.

**Solution**: Updated `projects_chat.py` `get_question()` endpoint (lines 599-607) to:
```python
# Extract question from either 'question' (single) or 'questions' (array) field
question = question_data.get("question", "").strip() if question_data.get("question") else ""

# If no single question, try to get first question from questions array
if not question:
    questions = question_data.get("questions", [])
    if questions and len(questions) > 0:
        question = questions[0].strip()
        logger.info(f"Extracted first question from questions array: {question[:50]}...")
```

### 1.3 Problem Identified: Topic Expected at Top Level

**Issue**: The `socratic_agents.SocraticCounselor.process()` method expects `"topic"` at the TOP LEVEL of the request dict, not nested in a project object. This caused "Topic required" 400 errors.

**Solution**: Updated `projects_chat.py` `get_question()` endpoint (line 569) to pass topic at top level:
```python
result = orchestrator.process_request(
    "socratic_counselor",
    {
        "action": "generate_question",
        "project": project,
        "topic": project.description,  # ← TOP LEVEL (CRITICAL)
        "current_user": current_user,
        "user_id": current_user,
        "force_refresh": False,
    },
)
```

### 1.4 Problem Identified: Missing process_response Handler

**Issue**: When users sent responses to questions, the system returned "Unknown action: process_response" 500 error.

**Solution**: Added handler in `orchestrator.py` `_handle_socratic_counselor()` method (lines 934-951):
```python
elif action == "process_response":
    response = request_data.get("response", "")
    project = request_data.get("project", {})
    current_user = request_data.get("current_user", "")

    return {
        "status": "success",
        "data": {
            "feedback": "Thank you for your response. Let me guide you further...",
            "next_action": "generate_question",
        },
        "message": "Response processed",
    }
```

**Note**: This is a basic implementation. In full mode, it should analyze user response and provide feedback.

### 1.5 Git Commits Made

```
3ce8a10 feat: Enhance SocraticCounselor to use Claude for dynamic question generation
70149cc fix: Add handler for process_response action in orchestrator
db0dcce fix: Extract question from 'questions' array returned by orchestrator
3988d9e fix: Pass topic at top level to SocraticCounselor agent
```

---

## Part 2: How Socrates Used to Work (Monolithic Version)

### 2.1 Architecture When Monolithic

When Socrates was a single monolithic application (before socratic_agents library was integrated), the question generation worked like this:

1. **Direct Call to Claude**: The system directly called Claude API with the project description
2. **Contextual Questions**: Questions were generated fresh for each project based on its specific topic
3. **Socratic Mode**: Questions were designed to guide the user through Socratic reasoning (asking guiding questions instead of giving answers)
4. **Direct Mode**: Users could ask direct questions and get direct answers from Claude

**Key Difference**: It didn't use an external `socratic_agents` library - it had its own implementation of Socratic questioning.

### 2.2 Question Generation Flow (Monolithic)

```
User creates project with description
    ↓
Frontend calls GET /projects/{id}/chat/question
    ↓
Backend (monolithic code):
    1. Load project description
    2. Call Claude with prompt: "Generate Socratic questions about: {topic}"
    3. Claude returns dynamic, context-aware questions
    4. Return first question to frontend
    ↓
User sees Claude-generated Socratic question specific to their project
```

### 2.3 Socratic vs Direct Modes (Monolithic)

**Socratic Mode**:
- Claude acted as Socrates tutor
- Asked guiding questions instead of giving answers
- Encouraged user to think critically
- Used Socratic method prompts

**Direct Mode**:
- Claude answered questions directly
- Provided explanations and code
- No Socratic method, just assistance
- Fast answers

Both modes existed and users could switch between them.

---

## Part 3: Current Architecture After socratic_agents Integration

### 3.1 Intended Architecture

When `socratic_agents` library was introduced:

1. **External Library Used**: Socratic questioning logic moved to `socratic_agents.SocraticCounselor` class
2. **Library Accepts LLM Client**: The library is designed to accept an `llm_client` parameter for dynamic generation
3. **Agents Pattern**: Multiple agents (code generator, validator, etc.) work together
4. **Orchestrator Pattern**: Central orchestrator manages all agents

### 3.2 What Happened: Library Design Flaw

**The Problem**: The `socratic_agents.SocraticCounselor` class has a critical bug:

```python
# In socratic_agents library:
class SocraticCounselor:
    def __init__(self, llm_client=None, ...):
        self.llm_client = llm_client  # ← Stores it but never uses it!

    def _generate_guiding_questions(self, topic: str, level: str) -> list:
        # Just returns hardcoded templates, ignores self.llm_client
        return [
            "What do you already know about {topic}?",
            "Why is {topic} important to you?",
            # ... more hardcoded questions
        ]
```

**Result**: Even though the system passes an `llm_client`, the library ignores it and returns generic hardcoded questions.

### 3.3 Current Question Generation Flow (Broken)

```
User creates project: "I want to create a simple python calculator"
    ↓
Frontend calls GET /projects/{id}/chat/question
    ↓
Backend:
    1. Load project description: "I want to create a simple python calculator"
    2. Pass to orchestrator with topic="I want to create a simple python calculator"
    ↓
Orchestrator._handle_socratic_counselor():
    1. Gets counselor agent from self.agents
    2. Check: if counselor and self.llm_client:
    3. Call: counselor.process({"topic": "..."})
    ↓
Library's SocraticCounselor.process():
    1. Ignores topic and llm_client
    2. Returns hardcoded question: "What do you already know about the topic?"
    ↓
User sees generic hardcoded question (not specific to calculator project)
```

---

## Part 4: LLM Connection Problems (Critical)

### 4.1 Problem 1: Single Global API Key

**Current State**:
```python
# main.py line 118-122
api_key = os.getenv("ANTHROPIC_API_KEY")
orchestrator = create_orchestrator(
    api_key=api_key or "placeholder-key-will-use-user-specific-keys"
)
```

**Issue**:
- System initialized with single API key from environment
- This key is used for ALL users
- Users cannot provide their own API keys
- Global placeholder key suggests this was always meant to be temporary

### 4.2 Problem 2: Database Stub Not Implemented

**Location**: `database.py` line 943-947

```python
def get_api_key(self, username: str, provider: str) -> Optional[str]:
    """Get API key for a user and provider (stub - not persisted)"""
    # In production, this would be stored in database
    # For now, return None (API key not found)
    return None
```

**Issue**:
- Function exists but is a stub
- Always returns `None`
- User API keys are never actually stored or retrieved
- Comment explicitly says "In production, this would be stored in database"

### 4.3 Problem 3: Orchestrator Handlers Missing

**Location**: `orchestrator.py` lines 783-872 `_handle_multi_llm()`

**What's Implemented**:
- `list_providers`
- `get_provider_config`
- `set_default_provider`
- `update_api_key` (only updates global key)
- `get_usage_stats`

**What's Missing** (called but not handled):
- `add_api_key` - User sets their API key
- `remove_api_key` - User removes their API key
- `set_auth_method` - User switches between subscription vs API key auth
- `set_provider_model` - User selects model
- `get_provider_models` - List available models

**Impact**: When frontend calls `/llm/api-key` endpoint (routers/llm.py line 103-130) with action `"add_api_key"`, the orchestrator returns **"Unknown action: add_api_key"** and the key is lost.

### 4.4 Problem 4: No Per-User LLM Client

**Current Architecture**:
```python
orchestrator = APIOrchestrator(api_key="global-key")
# ↓
self.llm_client = self._create_llm_client()  # Single client with global key

# When processing requests:
def _handle_socratic_counselor(self, request_data):
    user_id = request_data.get("user_id", "")  # ← User ID available
    # ...but it's never used to look up user's API key!

    if counselor and self.llm_client:  # ← Always uses global client
        result = counselor.process({"topic": topic})
```

**Issue**:
- User ID is passed to orchestrator but ignored
- No mechanism to look up user's stored API key
- No per-user LLMClient creation
- All users share the same global API key (or placeholder)

### 4.5 Frontend UI Expectations

**Location**: Frontend has UI components in `CreateProjectModal.tsx` and settings pages that:

1. Allow users to add API keys via `/llm/api-key` endpoint
2. Allow users to select provider and model
3. Allow users to switch auth methods
4. Show usage statistics

**Reality**: These endpoints exist but:
- API keys are never stored (database stub)
- Handlers are missing (orchestrator)
- Keys are never used (no per-user LLM client)
- **Frontend is connected to broken backend infrastructure**

---

## Part 5: How Socratic vs Direct Modes Work Now

### 5.1 Current State

**Socratic Mode** (enabled when generating questions):
- Uses `SocraticCounselor` agent
- My custom subclass tries to use Claude
- But still limited by global API key issue
- Questions formatted as array (needs extraction)

**Direct Mode** (not investigated yet):
- Likely uses different endpoint
- Probably has same global API key limitation
- Not tested in this session

### 5.2 Mode Switching

**Location**: `projects_chat.py` has endpoints suggesting mode switching:
- Line 1488: `get_questions()` - Get multiple questions (Socratic mode)
- Line 1547: `reopen_question()` - Reopen a question
- Line 1609: `skip_question()` - Skip to next question

But unclear if there's a "mode switching" endpoint or if it's implicit.

---

## Part 6: What Needs to be Fixed

### Priority 1: Essential for Basic Functionality (Do First)

1. **Implement `database.get_api_key()` and `save_api_key()`**
   - File: `database.py`
   - Currently: Stub returning None
   - Needed: Actually store/retrieve user API keys from database
   - Impact: Enables user API key persistence

2. **Add missing orchestrator handlers in `_handle_multi_llm()`**
   - File: `orchestrator.py`
   - Add handlers for: `add_api_key`, `remove_api_key`, `set_auth_method`, `set_provider_model`, `get_provider_models`
   - Each handler should call database methods to store/retrieve user keys
   - Impact: Frontend API key endpoints will work

3. **Modify `_handle_socratic_counselor()` to use per-user API key**
   - File: `orchestrator.py`
   - Add logic to look up user's API key before generating questions
   - If user key exists: create temporary LLMClient with that key
   - If no user key: use global API key (fallback)
   - Pass correct LLMClient to the counselor
   - Impact: Questions will use user's API key quota

### Priority 2: Improve User Experience

1. **Implement full `process_response` handler**
   - File: `orchestrator.py` line 934-951
   - Current: Just returns success
   - Needed: Analyze user response, provide feedback, suggest next question
   - Optional: Not blocking basic functionality

2. **Add Direct Mode Implementation**
   - If missing, need to implement similar per-user API key logic
   - Unknown current state - needs investigation

### Priority 3: Testing & Validation

1. **Test custom SocraticCounselor with real Claude API calls**
   - Verify dynamic question generation works
   - Verify fallback to templates works
   - Verify error handling works

2. **Test end-to-end user flow**
   - User sets API key via `/llm/api-key`
   - Key is stored in database
   - Create project and get question
   - Verify question uses user's Claude credit, not server's

3. **Test mode switching** (if applicable)
   - Switch between Socratic and Direct modes
   - Verify each uses correct API key

---

## Part 7: Database Schema Changes Needed

**Current**: No tables for API keys (get_api_key stub suggests they were planned but not implemented)

**Needed**:
```sql
CREATE TABLE IF NOT EXISTS user_api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,  -- 'anthropic', 'openai', etc.
    api_key TEXT NOT NULL,
    auth_method TEXT DEFAULT 'api_key',  -- 'api_key' or 'subscription'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, provider)
);
```

**Migrations Needed**:
- Add table `user_api_keys`
- Add table `user_llm_models` (for storing user's selected models per provider)
- Update `users` table to add `default_llm_provider` field if not exists

---

## Part 8: Testing Results

### What Works ✅
- Custom `SocraticCounselor` subclass created and committed
- Question extraction from array format implemented
- Topic passed at correct level to library
- process_response handler exists (basic)
- All changes committed to git

### What's Broken ❌
- User API keys: Not stored, not used
- LLM connection: Only uses server's global API key or placeholder
- All frontend LLM settings: Endpoints exist but don't actually work
- Direct mode: State unknown
- Per-user question generation: Impossible without user API key support

### Not Tested 🤔
- Whether custom SocraticCounselor actually generates Claude responses
- Whether library properly calls _generate_dynamic_questions override
- Whether fallback to hardcoded templates works
- Whether process_response handler is called correctly
- Whether query to database for user API keys would work (can't test with stub)

---

## Part 9: Code Locations Quick Reference

### Files Modified This Session
```
backend/src/socrates_api/orchestrator.py
  - Lines 14-88: Custom SocraticCounselor class
  - Lines 158: Instantiation with llm_client
  - Lines 934-951: process_response handler
  - Lines 844-854: update_api_key handler (only updates global key)

backend/src/socrates_api/routers/projects_chat.py
  - Lines 564-574: Pass topic at top level
  - Lines 599-607: Extract question from array
  - Line 569: topic=project.description (CRITICAL FIX)
```

### Files Needing Work
```
backend/src/socrates_api/database.py
  - Line 943-947: get_api_key() stub - IMPLEMENT THIS

backend/src/socrates_api/orchestrator.py
  - Line 783-872: _handle_multi_llm() - ADD MISSING HANDLERS
  - Line 874-932: _handle_socratic_counselor() - USE USER API KEY

backend/src/socrates_api/main.py
  - Line 118-124: get_orchestrator_from_state() - SUPPORTS per-user keys but not used
```

### Frontend Files
```
socrates-frontend/src/components/project/CreateProjectModal.tsx
  - Shows project creation form
  - Calls API to create project with description

socrates-frontend/src/routers/llm.py (if exists)
  - Endpoints for /llm/* - all work with broken orchestrator handlers
```

---

## Part 10: Key Code Snippets for Reference

### LLMClient Creation (Current - Single Global)
```python
# orchestrator.py line 116-132
def _create_llm_client(self) -> Optional[Any]:
    try:
        if not self.api_key:
            logger.debug("No API key provided - LLM client will be None")
            return None

        from socrates_nexus import LLMClient

        llm_client = LLMClient(
            provider="anthropic", model="claude-3-sonnet", api_key=self.api_key
        )
        logger.info("LLM client created successfully")
        return llm_client
    except Exception as e:
        logger.warning(f"Failed to create LLM client: {e}")
        return None
```

### Custom SocraticCounselor (New - Dynamic Questions)
```python
# orchestrator.py line 14-88
class SocraticCounselor(BaseSocraticCounselor):
    def _generate_guiding_questions(self, topic: str, level: str) -> list:
        if self.llm_client:
            return self._generate_dynamic_questions(topic, level)
        return super()._generate_guiding_questions(topic, level)

    def _generate_dynamic_questions(self, topic: str, level: str) -> list:
        try:
            level_guidance = {...}
            prompt = f"""Generate 3 thoughtful Socratic questions..."""
            response = self.llm_client.generate_response(prompt)
            # Parse JSON, fallback to line parsing, ultimate fallback to templates
```

### Where User ID Available But Unused
```python
# orchestrator.py line 874-897
def _handle_socratic_counselor(self, request_data: Dict[str, Any]):
    action = request_data.get("action", "")
    if action == "generate_question":
        project = request_data.get("project", {})
        topic = request_data.get("topic", "")
        user_id = request_data.get("user_id", "")  # ← AVAILABLE BUT NOT USED

        counselor = self.agents.get("socratic_counselor")

        if counselor and self.llm_client:  # ← Always uses global llm_client
            result = counselor.process({"topic": topic})
            # ← Should instead:
            # user_api_key = db.get_api_key(user_id, "anthropic")
            # if user_api_key:
            #     user_llm_client = LLMClient(..., api_key=user_api_key)
            #     assign to counselor temporarily
```

---

## Part 11: Environment & Dependencies

### Key Dependencies
- `socratic_agents` - Library with buggy SocraticCounselor
- `socrates_nexus` - Provides LLMClient for Claude API calls
- `anthropic` SDK - Actual Claude API client

### Environment Variables
- `ANTHROPIC_API_KEY` - Server's global API key (required to work at all)
- Not per-user - should be implemented

### Database
- SQLite (local file based)
- No user API key tables yet
- `get_api_key()` method is stub

---

## Part 12: How to Test When Fixed

### Test Case 1: Basic Question Generation
```bash
# 1. Ensure ANTHROPIC_API_KEY env var is set
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Create user account
POST /auth/register
{"username": "testuser", "password": "test123"}

# 3. Set user API key
POST /llm/api-key?provider=anthropic&api_key=sk-ant-user-key

# 4. Create project
POST /projects
{
  "name": "Python Calculator",
  "type": "software",
  "description": "A simple calculator in Python with basic arithmetic operations"
}

# 5. Get question
GET /projects/{project_id}/chat/question

# Expected: Claude generates question specific to calculator project
```

### Test Case 2: Verify User Key is Used
```bash
# Use test API key with low quota
# Call get_question multiple times
# Verify Claude tokens are consumed from test key, not server key
```

### Test Case 3: Fallback When No User Key
```bash
# Don't set user API key
# Call get_question
# Verify it uses server's global key (or returns error if none)
```

---

## Part 13: Summary of Current State

| Component | Status | Details |
|-----------|--------|---------|
| Custom SocraticCounselor | ✅ Complete | Committed, uses Claude when llm_client available |
| Question extraction | ✅ Complete | Handles array format from library |
| Topic parameter fix | ✅ Complete | Passed at top level to library |
| process_response handler | ✅ Complete | Basic implementation exists |
| Database API key storage | ❌ Missing | Stub function returns None |
| Orchestrator API key handlers | ❌ Missing | add_api_key, remove_api_key, set_auth_method not implemented |
| Per-user LLM client | ❌ Missing | No mechanism to look up user key and create client |
| Direct mode | 🤔 Unknown | Not investigated |
| Mode switching | 🤔 Unknown | Endpoints exist, implementation unclear |
| Testing | ❌ Not done | Need to verify custom counselor actually works |

---

## Next Session: Action Plan

When resuming work to fix the LLM connection issues:

1. **Read this document first** ← You are here
2. **Create database schema for user API keys** (5 min)
3. **Implement database.get_api_key() and .save_api_key()** (10 min)
4. **Add orchestrator handlers for add_api_key, remove_api_key, etc.** (15 min)
5. **Modify _handle_socratic_counselor() to use per-user keys** (10 min)
6. **Test end-to-end with user API key** (10 min)
7. **Fix Direct mode if needed** (time varies)
8. **Test both modes thoroughly** (time varies)

**Total estimated work**: 1-2 hours for basic functionality, more for complete testing

---

## Questions for Next Session

These questions should help guide the work:

1. Was Direct mode a separate code path in the monolithic version?
2. Should users be able to use their own API keys or only the server's key?
3. What should happen if user has no API key set? (Error? Use server key? Restrict access?)
4. Should there be a way to see usage statistics per user?
5. Should multiple providers be supported (Claude, GPT-4, Gemini) or just Claude?

---

**Document Complete**
This documentation should enable you to understand the full situation and make targeted fixes in the next session without re-investigating.
