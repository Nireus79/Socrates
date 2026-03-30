# Multi-Provider Quick Fix

**Good News**: User model already supports dynamic attributes!
**Implementation**: Store provider preferences in User attributes

---

## How to Fix

### 1. Database Methods (No schema change needed!)

Add to `database.py`:

```python
def set_user_default_provider(self, user_id: str, provider: str) -> bool:
    """Set user's default LLM provider"""
    try:
        user = self.load_user(user_id)
        if user:
            user.default_provider = provider
            self.save_user(user)
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to set default provider: {e}")
        return False

def get_user_default_provider(self, user_id: str) -> str:
    """Get user's default LLM provider, default to anthropic"""
    try:
        user = self.load_user(user_id)
        if user and hasattr(user, 'default_provider'):
            return user.default_provider
        return "anthropic"  # Default fallback
    except Exception as e:
        logger.error(f"Failed to get default provider: {e}")
        return "anthropic"

def set_provider_model(self, user_id: str, provider: str, model: str) -> bool:
    """Set user's preferred model for a provider"""
    try:
        user = self.load_user(user_id)
        if user:
            if not hasattr(user, 'provider_models'):
                user.provider_models = {}
            user.provider_models[provider] = model
            self.save_user(user)
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to set provider model: {e}")
        return False

def get_provider_model(self, user_id: str, provider: str) -> str:
    """Get user's preferred model for provider"""
    try:
        user = self.load_user(user_id)
        if user and hasattr(user, 'provider_models'):
            model = user.provider_models.get(provider)
            if model:
                return model

        # Fallback to defaults
        defaults = {
            "anthropic": "claude-3-sonnet",
            "openai": "gpt-4",
            "google": "gemini-pro"
        }
        return defaults.get(provider, "claude-3-sonnet")
    except Exception as e:
        logger.error(f"Failed to get provider model: {e}")
        return "claude-3-sonnet"
```

### 2. Update Orchestrator Handlers

Implement the stubbed handlers in `_handle_multi_llm()`:

```python
elif action == "set_default_provider":
    user_id = request_data.get("user_id", "")
    provider = request_data.get("provider", "anthropic")

    try:
        db = get_database()
        success = db.set_user_default_provider(user_id, provider)

        if success:
            return {
                "status": "success",
                "data": {"default_provider": provider},
                "message": f"Default provider set to {provider}"
            }
    except Exception as e:
        logger.error(f"Failed to set default provider: {e}")

    return {
        "status": "error",
        "message": "Failed to set default provider"
    }

elif action == "set_provider_model":
    user_id = request_data.get("user_id", "")
    provider = request_data.get("provider", "anthropic")
    model = request_data.get("model", "")

    try:
        db = get_database()
        success = db.set_provider_model(user_id, provider, model)

        if success:
            return {
                "status": "success",
                "data": {"provider": provider, "model": model},
                "message": f"Model set to {model} for {provider}"
            }
    except Exception as e:
        logger.error(f"Failed to set provider model: {e}")

    return {
        "status": "error",
        "message": "Failed to set provider model"
    }
```

### 3. Fix Question Generation

In `_handle_socratic_counselor()`, replace:

```python
# OLD (hardcoded):
user_api_key = db.get_api_key(user_id, "anthropic")
llm_client_to_use = LLMClient(
    provider="anthropic",
    model="claude-3-sonnet",
    api_key=user_api_key
)
```

With:

```python
# NEW (provider-aware):
from socrates_api.database import get_database
db = get_database()

# Get user's preferred provider
provider = db.get_user_default_provider(user_id)  # "anthropic", "openai", etc.

# Get API key for that provider
user_api_key = db.get_api_key(user_id, provider)

# Get preferred model for that provider
model = db.get_provider_model(user_id, provider)

if user_api_key:
    try:
        from socrates_nexus import LLMClient
        llm_client_to_use = LLMClient(
            provider=provider,  # User's chosen provider!
            model=model,        # User's chosen model!
            api_key=user_api_key
        )
        logger.info(f"Using {provider}/{model} for user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to create LLMClient with user key: {e}")
        llm_client_to_use = self.llm_client  # Fallback
else:
    llm_client_to_use = self.llm_client  # Use server's default
```

### 4. Fix Direct Mode

Same pattern in `_handle_direct_chat()` - use user's provider instead of hardcoded "anthropic"

### 5. Fix projects_chat.py

Update Direct Mode to use user's provider:

```python
# OLD (hardcoded):
user_api_key = db.get_api_key(current_user, "anthropic")

# NEW (provider-aware):
provider = db.get_user_default_provider(current_user)
user_api_key = db.get_api_key(current_user, provider)
```

---

## Implementation Steps

1. Add database methods: `set_user_default_provider()`, `get_user_default_provider()`, `set_provider_model()`, `get_provider_model()`

2. Implement orchestrator handlers for `set_default_provider` and `set_provider_model`

3. Update `_handle_socratic_counselor()` to use user's provider preference

4. Update `_handle_direct_chat()` to use user's provider preference

5. Update `projects_chat.py` to use user's provider preference

6. Update orchestrator handler to return accurate `get_provider_config` with user's actual settings

7. Test with multiple providers

---

## Key Insight

The User model stores ANY attribute dynamically via kwargs:
- `user.default_provider` = "openai"
- `user.provider_models` = {"openai": "gpt-4", "anthropic": "claude-3-sonnet"}

These are saved to database and loaded when needed. No schema changes required!

---

## Implementation Complexity

- ⭐ **Very Simple** - Just swap hardcoded strings with database lookups
- No schema changes
- Use existing User attribute system
- Backward compatible (defaults to "anthropic")

---

## Expected Time

- Database methods: 15 min
- Orchestrator handlers: 15 min
- Question generation fix: 15 min
- Direct Mode fix: 10 min
- projects_chat.py fix: 10 min
- Testing: 15 min
- **Total: ~1.5 hours**

---

## Success Criteria

✅ Users can set default provider (OpenAI, Google, Anthropic, etc.)
✅ Users can set preferred model per provider
✅ Questions use user's chosen provider
✅ Direct Mode uses user's chosen provider
✅ All providers work equally
✅ Backward compatible (defaults to Claude)
✅ No hardcoded providers

---

**This is much simpler than I initially thought!**
The infrastructure was already designed to support this.
Just need to implement the lookups instead of hardcoding.
