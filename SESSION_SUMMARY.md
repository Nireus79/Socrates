# Socrates Debugging Session Summary

**Date**: 2026-03-28
**Status**: At 97% weekly token limit
**What's Done**: 50% (question generation fixed, infrastructure broken)
**What's Left**: 50% (API key support implementation)

---

## What You Need to Know in 30 Seconds

**The Good News**: Questions now generate with Claude dynamically ✅
**The Bad News**: Only the server can do this, not individual users ❌
**The Fix**: Implement user API key storage and per-user LLM clients (2 hours)

---

## Files Created This Session

These documents explain everything:

1. **📋 CRITICAL_ARCHITECTURE_ISSUES.md** (13 parts)
   - Complete technical documentation
   - Everything that was done, everything that's broken
   - Why monolithic vs current architecture matters
   - Read this first for full context

2. **⚡ QUICK_REFERENCE.md**
   - TL;DR version
   - Copy-paste code snippets ready to use
   - 4-step action plan with code examples

3. **📊 ARCHITECTURE_DIAGRAMS.md**
   - Visual explanations with ASCII diagrams
   - Data flows before/after fixes
   - What should happen vs. what actually happens
   - Great for understanding the architecture

4. **📝 SESSION_SUMMARY.md** (this file)
   - Quick navigation guide
   - What was completed
   - What still needs to be done

---

## What Was Completed This Session ✅

### 1. Custom SocraticCounselor Implementation
**Location**: `backend/src/socrates_api/orchestrator.py` lines 14-88

**What**: Created subclass of `socratic_agents.SocraticCounselor` that actually uses Claude

**Why**: The library's original class accepts `llm_client` parameter but never uses it

**How It Works**:
- Overrides `_generate_guiding_questions()` method
- If `llm_client` available: calls `_generate_dynamic_questions()`
- That method sends prompt to Claude via `self.llm_client.generate_response()`
- Parses JSON response or falls back to templates

**Code**:
```python
class SocraticCounselor(BaseSocraticCounselor):
    def _generate_guiding_questions(self, topic: str, level: str) -> list:
        if self.llm_client:
            return self._generate_dynamic_questions(topic, level)
        return super()._generate_guiding_questions(topic, level)
```

**Status**: Committed ✅

### 2. Question Extraction Fix
**Location**: `backend/src/socrates_api/routers/projects_chat.py` lines 599-607

**What**: Extract question from array format returned by library

**Why**: Library returns `{"questions": ["Q1", "Q2", "Q3"]}` but code expected `{"question": "Q1"}`

**How It Works**:
```python
question = question_data.get("question", "").strip()
if not question:
    questions = question_data.get("questions", [])
    if questions and len(questions) > 0:
        question = questions[0].strip()
```

**Status**: Committed ✅

### 3. Topic Parameter Fix
**Location**: `backend/src/socrates_api/routers/projects_chat.py` line 569

**What**: Pass topic at TOP LEVEL of request dict to orchestrator

**Why**: Library's `SocraticCounselor.process()` expects `{"topic": "..."}`, not nested in project

**Before**: `{"project": {...}, "description": "..."}`
**After**: `{"project": {...}, "topic": "Python Calculator"}`

**Status**: Committed ✅

### 4. Process Response Handler
**Location**: `backend/src/socrates_api/orchestrator.py` lines 934-951

**What**: Added handler for `process_response` action

**Why**: Users sending responses to questions got "Unknown action" 500 error

**Current Implementation**: Basic - just returns success message

**Status**: Committed ✅

### 5. Git Commits Made
```
3ce8a10 feat: Enhance SocraticCounselor to use Claude for dynamic question generation
70149cc fix: Add handler for process_response action in orchestrator
db0dcce fix: Extract question from 'questions' array returned by orchestrator
3988d9e fix: Pass topic at top level to SocraticCounselor agent
```

---

## What Still Needs to be Done ❌

### Critical (Blocks User API Keys)

#### 1. Implement Database Storage for User API Keys
**File**: `backend/src/socrates_api/database.py`
**Current**: Line 943 is a stub function returning None
**Needed**: Implement `save_api_key()`, `get_api_key()`, `delete_api_key()`
**Time**: 15 min
**Complexity**: Easy - simple SQL operations

Also need to add table:
```sql
CREATE TABLE IF NOT EXISTS user_api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    api_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, provider)
);
```

#### 2. Add Missing Orchestrator Handlers
**File**: `backend/src/socrates_api/orchestrator.py`
**Location**: In `_handle_multi_llm()` method (lines 783-872)
**Current**: Only 5 handlers implemented (list_providers, get_provider_config, etc.)
**Missing**:
- `add_api_key` - Save user's API key
- `remove_api_key` - Delete user's API key
- `set_auth_method` - Switch between subscription vs API key
- `set_provider_model` - Select model
- `get_provider_models` - List models

**Time**: 20 min
**Complexity**: Medium - need to call database methods

**Example Handler** (from QUICK_REFERENCE.md):
```python
elif action == "add_api_key":
    user_id = request_data.get("user_id", "")
    provider = request_data.get("provider", "anthropic")
    api_key = request_data.get("api_key", "")

    db = get_database()
    success = db.save_api_key(user_id, provider, api_key)

    return {
        "status": "success" if success else "error",
        "message": "API key saved" if success else "Failed to save"
    }
```

#### 3. Use Per-User API Key in Question Generation
**File**: `backend/src/socrates_api/orchestrator.py`
**Location**: In `_handle_socratic_counselor()` method (lines 878-897)
**Current**: Always uses global `self.llm_client` for all users
**Needed**: Look up user's API key and create per-user LLMClient

**Change** (line 891):
```python
# OLD (current):
if counselor and self.llm_client:
    result = counselor.process({"topic": topic})

# NEW (needed):
db = get_database()
user_api_key = db.get_api_key(user_id, "anthropic")

if user_api_key:
    user_llm_client = LLMClient(
        provider="anthropic",
        model="claude-3-sonnet",
        api_key=user_api_key
    )
    counselor.llm_client = user_llm_client
else:
    counselor.llm_client = self.llm_client

if counselor and (user_api_key or self.llm_client):
    result = counselor.process({"topic": topic})
```

**Time**: 15 min
**Complexity**: Medium - need to import, create client, assign

---

### Important (Improve Experience)

#### 4. Implement Full process_response Handler
**File**: `backend/src/socrates_api/orchestrator.py`
**Location**: Lines 934-951
**Current**: Just returns success message
**Needed**: Analyze user response, provide feedback, suggest next question

**Not blocking** - basic functionality works without this

#### 5. Investigate Direct Mode
**Status**: Unknown - not investigated this session
**Needed**: Determine if it has same API key problem, implement if needed

---

## How to Continue in Next Session

### Step 1: Read Documentation (10 min)
```
1. Read this file (SESSION_SUMMARY.md)
2. Read QUICK_REFERENCE.md
3. Skim ARCHITECTURE_DIAGRAMS.md
4. Reference CRITICAL_ARCHITECTURE_ISSUES.md as needed
```

### Step 2: Implement Database Layer (15 min)
```
database.py:
- Add save_api_key() method
- Implement get_api_key() method (replace stub)
- Add delete_api_key() method
- Create user_api_keys table in database
```

### Step 3: Add Orchestrator Handlers (20 min)
```
orchestrator.py._handle_multi_llm():
- Add elif for "add_api_key"
- Add elif for "remove_api_key"
- Add elif for "set_auth_method"
- (Optional) Add elif for "set_provider_model"
- (Optional) Add elif for "get_provider_models"
```

### Step 4: Use User API Keys (15 min)
```
orchestrator.py._handle_socratic_counselor():
- Get user_id from request_data
- Look up user's API key from database
- Create per-user LLMClient if key exists
- Use per-user client for question generation
```

### Step 5: Test (20 min)
```
Test 1: User sets API key
  POST /llm/api-key?provider=anthropic&api_key=sk-ant-xxx
  → Should save to database

Test 2: User gets question
  GET /projects/{id}/chat/question
  → Should use user's API key

Test 3: Fallback if no user key
  DELETE /llm/api-key/anthropic
  GET /projects/{id}/chat/question
  → Should fall back to server key
```

**Total Time**: ~1-1.5 hours

---

## File Quick Reference

### Files to Read for Understanding
- **CRITICAL_ARCHITECTURE_ISSUES.md** - Deep technical details
- **QUICK_REFERENCE.md** - Quick summary + code
- **ARCHITECTURE_DIAGRAMS.md** - Visual explanations

### Files to Modify
```
backend/src/socrates_api/database.py
  Line 943: get_api_key() - implement

backend/src/socrates_api/orchestrator.py
  Line 14-88: Custom SocraticCounselor - DONE ✅
  Line 116-132: _create_llm_client() - may need per-user version
  Line 783-872: _handle_multi_llm() - add handlers
  Line 874-932: _handle_socratic_counselor() - use user key
  Line 934-951: process_response handler - optional enhancement
```

### Test Files (for reference)
```
backend/src/tests/test_comprehensive_system.py
backend/src/tests/test_id_generator.py
```

---

## Current Git Status

**Branch**: master
**Latest Commit**: 3ce8a10 "feat: Enhance SocraticCounselor to use Claude for dynamic question generation"
**Status**: Clean (all changes committed)

Next commit will be something like:
```
git commit -m "feat: Implement per-user API key support

- Implement database storage for user API keys
- Add save_api_key(), get_api_key(), delete_api_key() methods
- Add user_api_keys table to schema
- Add orchestrator handlers: add_api_key, remove_api_key, set_auth_method
- Update question generation to use per-user API keys
- Fall back to global key if user key not available"
```

---

## Key Insights for Next Session

1. **The Library Bug**: `socratic_agents.SocraticCounselor` accepts `llm_client` but never uses it. Our custom subclass fixes this.

2. **The Architecture Gap**: User API keys are accepted via UI but never stored or used because:
   - Database method is a stub
   - Orchestrator handlers are missing
   - Question generation always uses global client

3. **The Easy Win**: The custom SocraticCounselor works! The problem is infrastructure around it.

4. **The Quick Fix**: Database + 3 orchestrator handlers = user API keys work. No library changes needed.

5. **The Scope**: After fixing API keys, investigate if Direct mode needs same treatment.

---

## What to Tell Users When It's Fixed

When this is fully implemented:

> "You can now provide your own Claude API key. Your questions will be generated using your own API quota. If you don't provide a key, the system will use the server's shared key. You can change your API key or remove it anytime from Settings."

---

## Token Budget Note

- Current session: Used significant context
- 3 comprehensive documents created for next session
- No re-investigation needed - everything is documented
- Next session: Start fresh with these docs for reference
- Estimated token usage for fixes: 15-20k (well within limits)

---

**Documents Created**: 4 files
**Git Commits This Session**: 4
**Lines of Code Added**: ~150
**Lines of Code Fixed**: ~100
**Remaining Work**: ~50-60 lines of code

🎯 **Ready to Resume**: Yes - Documentation Complete
