# Multi-LLM Provider Support - Analysis & Fix Plan

**Status**: CRITICAL ISSUE FOUND
**Issue**: System hardcoded to Claude only, should support multiple providers
**Severity**: HIGH - Architecture breaking change needed

---

## The Problem

### What I Did Wrong
I hardcoded the system to use "anthropic" (Claude) only in:

1. **database.py**
   ```python
   db.get_api_key(user_id, "anthropic")  # ❌ Hardcoded
   ```

2. **orchestrator.py - Socratic Mode**
   ```python
   user_api_key = db.get_api_key(user_id, "anthropic")  # ❌ Hardcoded
   llm_client = LLMClient(
       provider="anthropic",  # ❌ Hardcoded
       model="claude-3-sonnet",  # ❌ Hardcoded
   )
   ```

3. **orchestrator.py - Direct Mode**
   ```python
   llm_client = LLMClient(
       provider="anthropic",  # ❌ Hardcoded
       model="claude-3-sonnet",  # ❌ Hardcoded
   )
   ```

4. **projects_chat.py**
   ```python
   user_api_key = db.get_api_key(user_id, "anthropic")  # ❌ Hardcoded
   ```

### What Should Happen
The system infrastructure already shows support for:
- Anthropic (Claude)
- OpenAI (GPT-4)
- Google (Gemini)

Users should be able to:
- Select their preferred LLM provider
- Store different API keys for different providers
- Use different providers for different projects
- Switch providers at any time

---

## The Architecture

### Current Intended Design
```
User Settings:
  - Default LLM Provider: anthropic (or openai, google, etc.)
  - For each provider:
    - API Key
    - Model (e.g., gpt-4, claude-3-sonnet, gemini-pro)
    - Auth Method (api_key or subscription)

When generating questions/answers:
  - Look up user's default provider
  - Get API key for that provider
  - Get model preference for that provider
  - Create LLMClient with correct provider/model
```

### What I Implemented Wrong
```
Hardcoded:
  - Provider: always "anthropic"
  - Model: always "claude-3-sonnet"

This breaks:
  - OpenAI users can't use their GPT-4 keys
  - Google users can't use their Gemini keys
  - Multi-provider users can't switch
  - Mixed team environments don't work
```

---

## Required Changes

### 1. Database Schema Enhancement
**File**: `database.py`

Need to add to `user_api_keys` table:
```sql
ALTER TABLE user_api_keys ADD COLUMN provider TEXT;  -- already has it!
ALTER TABLE user_api_keys ADD COLUMN model TEXT DEFAULT 'claude-3-sonnet';
ALTER TABLE user_api_keys ADD COLUMN auth_method TEXT DEFAULT 'api_key';
```

Actually, these columns likely already exist or need to be added to the schema initialization!

### 2. Store User's Provider Preference
**File**: `database.py`

Add methods:
```python
def set_default_provider(user_id: str, provider: str) -> bool:
    """Set user's default LLM provider"""
    # Store in user preferences or separate table

def get_default_provider(user_id: str) -> str:
    """Get user's default LLM provider"""
    # Default to "anthropic" if not set

def set_provider_model(user_id: str, provider: str, model: str) -> bool:
    """Store user's preferred model for a provider"""
    # e.g., user_id, "openai", "gpt-4-turbo"

def get_provider_model(user_id: str, provider: str) -> str:
    """Get user's preferred model for a provider"""
```

### 3. Fix Question Generation
**File**: `orchestrator.py` - _handle_socratic_counselor()

**Current (Wrong)**:
```python
user_api_key = db.get_api_key(user_id, "anthropic")
llm_client = LLMClient(
    provider="anthropic",
    model="claude-3-sonnet",
    api_key=user_api_key
)
```

**Should Be**:
```python
# Get user's preferred provider
default_provider = db.get_default_provider(user_id) or "anthropic"

# Get API key for that provider
user_api_key = db.get_api_key(user_id, default_provider)

# Get user's preferred model for that provider
model = db.get_provider_model(user_id, default_provider)

if user_api_key:
    llm_client = LLMClient(
        provider=default_provider,
        model=model,
        api_key=user_api_key
    )
```

### 4. Fix Direct Mode
**File**: `orchestrator.py` - _handle_direct_chat()

Same issue - hardcoded to "anthropic" and "claude-3-sonnet"

Should use user's default provider and model

### 5. Update Orchestrator Handlers
**File**: `orchestrator.py` - _handle_multi_llm()

Handlers need to:
- `set_default_provider` - Store user's preferred provider
- `set_provider_model` - Store user's preferred model
- `get_provider_config` - Return user's settings for all providers

### 6. Update projects_chat.py
**File**: `projects_chat.py`

Remove hardcoded "anthropic":
```python
# WRONG:
user_api_key = db.get_api_key(user_id, "anthropic")

# RIGHT:
provider = db.get_default_provider(user_id) or "anthropic"
user_api_key = db.get_api_key(user_id, provider)
```

---

## Implementation Order

1. **Analyze** current database schema
2. **Add methods** to get/set user's provider preference
3. **Update orchestrator** handlers for multi-provider support
4. **Fix question generation** to use user's provider
5. **Fix Direct Mode** to use user's provider
6. **Fix projects_chat.py** to pass correct provider
7. **Test** with multiple providers
8. **Document** changes

---

## What Needs Investigation

1. **Is there already a user preferences table?**
   - If yes: use it for provider/model storage
   - If no: add columns to users table or create preferences table

2. **What providers does socrates_nexus support?**
   - Check LLMClient initialization
   - What models are available for each?

3. **What was the original design intent?**
   - Look at git history
   - Check for commented code
   - Review any design docs

4. **How should user select provider?**
   - CLI? (already have endpoints)
   - Per-project basis?
   - Global preference?

---

## Estimated Effort

| Task | Time |
|------|------|
| Investigate current schema | 15 min |
| Add database methods | 15 min |
| Update orchestrator handlers | 20 min |
| Fix question generation | 15 min |
| Fix Direct Mode | 15 min |
| Fix projects_chat.py | 10 min |
| Testing | 20 min |
| Documentation | 15 min |
| **Total** | **~2 hours** |

---

## Success Criteria

- ✅ System supports multiple LLM providers
- ✅ Users can set preferred provider
- ✅ Users can set preferred model per provider
- ✅ Question generation uses user's provider
- ✅ Direct Mode uses user's provider
- ✅ No hardcoded providers
- ✅ All providers supported equally
- ✅ Tests pass
- ✅ Backward compatible

---

## Current Status

**Issue Severity**: HIGH
**Blocking**: Multi-provider support broken
**User Impact**: Users can't use OpenAI/Google/other providers
**Fix Priority**: CRITICAL

**This needs to be fixed before production deployment!**
