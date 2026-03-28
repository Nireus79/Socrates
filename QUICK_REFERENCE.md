# Socrates - Quick Reference Guide

## One-Sentence Summary
**The custom SocraticCounselor works with Claude, but the system can't use user-specific API keys because database storage and orchestrator handlers are not implemented.**

---

## The Three Critical Issues

### Issue 1: Questions Are Generic (FIXED ✅)
- **Was**: Library returned hardcoded questions like "What do you know about {topic}?"
- **Now**: Custom subclass uses Claude to generate context-aware questions
- **Location**: `orchestrator.py` lines 14-88

### Issue 2: User API Keys Don't Work (BROKEN ❌)
- **Was**: Not applicable - monolithic version had different architecture
- **Now**: Database stub doesn't store keys, orchestrator has no handlers for add_api_key
- **Impact**: Users can't use their own Claude API keys
- **Locations**: `database.py` line 943, `orchestrator.py` line 783-872

### Issue 3: Only One Global API Key (BROKEN ❌)
- **Was**: Not applicable - monolithic had different architecture
- **Now**: Orchestrator initialized once with server's API key (or placeholder)
- **Impact**: All users share same API key quota
- **Location**: `main.py` lines 118-124, `orchestrator.py` lines 116-132

---

## Visual Comparison: Before vs After

### Before (Monolithic)
```
User → Frontend → Backend (monolithic) → Claude API (direct call)
                   ↓
              Generate question specific to project
```

### Now - Intended Design
```
User → Frontend → Backend (orchestrator + socratic_agents library) → Claude API
                   ↓
              Custom SocraticCounselor subclass → Dynamic questions
```

### Now - Actual Reality (Broken)
```
User → Frontend → Backend
        ↓
     Sets API key via /llm/api-key
        ↓
     Orchestrator.add_api_key handler → "Unknown action" error
        ↓
     Key is LOST (not stored)
        ↓
When user gets question:
    Backend uses global server API key only
    Questions generated for ALL users are the same hardcoded defaults
```

---

## The Fix in 4 Steps

### Step 1: Add Database Schema (5 min)
**File**: `database.py`

```python
# Add this method - it's just a stub now
def save_api_key(self, user_id: str, provider: str, api_key: str) -> bool:
    """Store user's API key for a provider"""
    # Implementation: INSERT or UPDATE into user_api_keys table

def get_api_key(self, user_id: str, provider: str) -> Optional[str]:
    """Retrieve user's API key for a provider"""
    # Implementation: SELECT from user_api_keys table
```

Also need SQL table:
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

### Step 2: Add Orchestrator Handlers (15 min)
**File**: `orchestrator.py` in `_handle_multi_llm()` method

```python
elif action == "add_api_key":
    user_id = request_data.get("user_id", "")
    provider = request_data.get("provider", "anthropic")
    api_key = request_data.get("api_key", "")

    db = get_database()
    db.save_api_key(user_id, provider, api_key)

    return {
        "status": "success",
        "data": {"provider": provider},
        "message": "API key saved"
    }

elif action == "remove_api_key":
    user_id = request_data.get("user_id", "")
    provider = request_data.get("provider", "anthropic")

    # Add delete_api_key method to database.py
    db = get_database()
    db.delete_api_key(user_id, provider)

    return {
        "status": "success",
        "message": "API key removed"
    }
```

### Step 3: Use Per-User API Key in Question Generation (15 min)
**File**: `orchestrator.py` in `_handle_socratic_counselor()` method

**Change this** (line 891):
```python
if counselor and self.llm_client:
    result = counselor.process({"topic": topic})
```

**To this**:
```python
# Try to get user's API key
db = get_database()
user_api_key = db.get_api_key(user_id, "anthropic")

# Create LLM client with user's key if available
if user_api_key:
    from socrates_nexus import LLMClient
    user_llm_client = LLMClient(
        provider="anthropic",
        model="claude-3-sonnet",
        api_key=user_api_key
    )
    # Assign to counselor temporarily
    counselor.llm_client = user_llm_client
elif self.llm_client:
    # Fallback to global key
    counselor.llm_client = self.llm_client

if counselor and (user_api_key or self.llm_client):
    result = counselor.process({"topic": topic})
```

### Step 4: Test (10 min)
```bash
# Set environment variable for server key
export ANTHROPIC_API_KEY="sk-ant-..."

# Test 1: User without API key
curl -H "Authorization: Bearer token" \
  GET /projects/{id}/chat/question
# → Should use server key or error

# Test 2: User with API key
curl -H "Authorization: Bearer token" \
  POST /llm/api-key?provider=anthropic&api_key=sk-ant-user-key

curl -H "Authorization: Bearer token" \
  GET /projects/{id}/chat/question
# → Should use user key
```

---

## Code Snippets - Copy-Paste Ready

### Database Methods to Implement

```python
# Add to LocalDatabase class in database.py

def save_api_key(self, user_id: str, provider: str, api_key: str) -> bool:
    """Save or update user's API key for a provider"""
    try:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO user_api_keys (user_id, provider, api_key)
            VALUES (?, ?, ?)
            """,
            (user_id, provider, api_key)
        )
        self.conn.commit()
        logger.info(f"API key saved for user {user_id} provider {provider}")
        return True
    except Exception as e:
        logger.error(f"Failed to save API key: {e}")
        return False

def get_api_key(self, user_id: str, provider: str) -> Optional[str]:
    """Get user's API key for a provider"""
    try:
        cursor = self.conn.execute(
            "SELECT api_key FROM user_api_keys WHERE user_id = ? AND provider = ?",
            (user_id, provider)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Failed to get API key: {e}")
        return None

def delete_api_key(self, user_id: str, provider: str) -> bool:
    """Delete user's API key for a provider"""
    try:
        self.conn.execute(
            "DELETE FROM user_api_keys WHERE user_id = ? AND provider = ?",
            (user_id, provider)
        )
        self.conn.commit()
        logger.info(f"API key deleted for user {user_id} provider {provider}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        return False
```

### Orchestrator Handler

```python
# Add to _handle_multi_llm method in orchestrator.py

elif action == "add_api_key":
    user_id = request_data.get("user_id", "")
    provider = request_data.get("provider", "anthropic")
    api_key = request_data.get("api_key", "")

    if not user_id or not api_key:
        return {
            "status": "error",
            "message": "user_id and api_key are required"
        }

    try:
        from socrates_api.database import get_database
        db = get_database()
        success = db.save_api_key(user_id, provider, api_key)

        if success:
            return {
                "status": "success",
                "data": {"provider": provider},
                "message": f"API key saved for {provider}"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to save API key"
            }
    except Exception as e:
        logger.error(f"Failed to handle add_api_key: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

elif action == "remove_api_key":
    user_id = request_data.get("user_id", "")
    provider = request_data.get("provider", "anthropic")

    if not user_id:
        return {
            "status": "error",
            "message": "user_id is required"
        }

    try:
        from socrates_api.database import get_database
        db = get_database()
        success = db.delete_api_key(user_id, provider)

        if success:
            return {
                "status": "success",
                "message": f"API key removed for {provider}"
            }
        else:
            return {
                "status": "error",
                "message": "API key not found"
            }
    except Exception as e:
        logger.error(f"Failed to handle remove_api_key: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
```

### Updated Question Generation Handler

```python
# Replace the existing _handle_socratic_counselor generate_question section

if action == "generate_question":
    project = request_data.get("project", {})
    topic = request_data.get("topic", "")
    user_id = request_data.get("user_id", "")
    force_refresh = request_data.get("force_refresh", False)

    logger.info(f"_handle_socratic_counselor generate_question: topic={topic[:50] if topic else 'EMPTY'}")

    counselor = self.agents.get("socratic_counselor")

    try:
        # Try to get user's API key
        from socrates_api.database import get_database
        db = get_database()
        user_api_key = db.get_api_key(user_id, "anthropic")

        # Create LLM client with user's key if available
        llm_client_to_use = None
        if user_api_key:
            try:
                from socrates_nexus import LLMClient
                llm_client_to_use = LLMClient(
                    provider="anthropic",
                    model="claude-3-sonnet",
                    api_key=user_api_key
                )
                logger.info(f"Using user API key for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to create LLMClient with user key: {e}")
                llm_client_to_use = self.llm_client
        else:
            llm_client_to_use = self.llm_client
            if not llm_client_to_use:
                logger.warning("No user API key and no global API key")

        if counselor and llm_client_to_use:
            # Temporarily assign the correct LLM client
            original_llm_client = counselor.llm_client
            counselor.llm_client = llm_client_to_use

            try:
                logger.info(f"Calling counselor.process() with topic: {topic[:50] if topic else 'EMPTY'}")
                result = counselor.process({"topic": topic})
                logger.info(f"counselor.process() returned: {result}")
                return {"status": "success", "data": result, "message": "Question generated"}
            finally:
                # Restore original client
                counselor.llm_client = original_llm_client
    except Exception as e:
        logger.warning(f"Failed to use socratic_counselor agent: {e}", exc_info=True)

    # Fallback: Generic questions (existing code)
    # ... rest of the fallback logic stays the same
```

---

## How to Apply Fixes

1. **First**: Read `CRITICAL_ARCHITECTURE_ISSUES.md` completely
2. **Database**: Add schema and methods
3. **Orchestrator**: Add handlers
4. **Question Generation**: Update to use user API key
5. **Test**: Run through all test cases
6. **Commit**: Create a commit with all changes

---

## Files to Modify Summary

| File | Lines | Action |
|------|-------|--------|
| `database.py` | ~943 | Implement save_api_key(), get_api_key(), delete_api_key() |
| `orchestrator.py` | ~783-872 | Add handlers for add_api_key, remove_api_key, set_auth_method |
| `orchestrator.py` | ~878-897 | Update generate_question to use per-user API key |

**Total Changes**: ~100-150 lines of code
**Estimated Time**: 30-40 minutes
**Risk Level**: Low (isolated to LLM functionality)
**Testing Required**: Yes (each step)

---

## Current Git Status

```
HEAD: 3ce8a10 feat: Enhance SocraticCounselor to use Claude for dynamic question generation
Branch: master
Status: clean
```

After fixes, you'll commit something like:
```
git commit -m "feat: Implement per-user API key support

- Add user_api_keys table to database
- Implement database methods for saving/retrieving user API keys
- Add orchestrator handlers for add_api_key, remove_api_key, set_auth_method
- Update question generation to use user-specific API keys
- Fallback to global key if user key not available"
```

---

## Known Limitations After Fix

Even after implementing these fixes:

1. ⚠️ Only one provider supported (Anthropic/Claude)
2. ⚠️ Direct mode still needs investigation
3. ⚠️ process_response handler is basic
4. ⚠️ No usage tracking per user
5. ⚠️ No model selection UI implemented yet

These are Phase 2+ improvements.

---

**Ready to implement?** Start with the CRITICAL_ARCHITECTURE_ISSUES.md file.
