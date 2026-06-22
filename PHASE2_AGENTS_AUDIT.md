# Phase 2: socratic-agents Library Audit - FINDINGS

**Date:** 2026-06-22  
**Status:** ISSUES FOUND - REQUIRES FIXES  

## Executive Summary

The socratic-agents library has issues with ProviderMetadata attribute access. The code tries to access attributes that don't exist in the ProviderMetadata dataclass.

## Issues Found

### Issue 1: ProviderMetadata Attribute Mismatch

**Problem:**  
The `ProviderMetadata` dataclass defines an attribute `name`, but `multi_llm_agent.py` tries to access `provider.provider`.

**File:** `src/socratic_agents/models.py`  
**Current Definition (line 52):**
```python
@dataclass
class ProviderMetadata:
    name: str                               # ← Has 'name', not 'provider'
    display_name: str
    models: List[str]
    default_model: str
    ...
```

**Current Usage (line 113 in multi_llm_agent.py):**
```python
"name": provider.provider,                 # ← Trying to access .provider (wrong!)
```

**Fix:** Change to:
```python
"name": provider.name,                     # ← Correct attribute
```

### Issue 2: Missing Attributes

**Problem:**  
The code tries to access attributes that don't exist in ProviderMetadata:

| Attribute | Line(s) | Current Access | Status |
|-----------|---------|-----------------|--------|
| `description` | 117 | `provider.description` | ❌ Missing |
| `context_window` | 120, 182 | `provider.context_window` | ❌ Missing (should be `max_context_tokens`) |
| `available` | 123 | `provider.available` | ❌ Missing |
| `auth_methods` | 124 | `provider.auth_methods` | ❌ Missing |

**Current ProviderMetadata fields:**
```python
name: str
display_name: str
models: List[str]
default_model: str
requires_api_key: bool
cost_per_1k_input_tokens: float
cost_per_1k_output_tokens: float
supports_streaming: bool
supports_vision: bool
max_context_tokens: int  # ← Not 'context_window'
metadata: Dict[str, Any]
```

**Fix Options:**

**Option A: Add missing attributes to ProviderMetadata** (adds to schema)
```python
@dataclass
class ProviderMetadata:
    # ... existing fields ...
    description: str = "Provider description"
    available: bool = True
    auth_methods: List[str] = field(default_factory=lambda: ["api_key"])
    # context_window remains as max_context_tokens
```

**Option B: Remove references to missing attributes** (cleaner)
```python
# Don't access .description, .available, .auth_methods
# Change .context_window to .max_context_tokens
```

**Recommendation:** Option B (cleaner approach - only access fields that exist)

## Files That Need Changes

### File: `src/socratic_agents/multi_llm_agent.py`

**Method: `_list_providers()` (lines 78-147)**

Changes needed:
```python
# Line 113: Change
"name": provider.provider,  # WRONG
# To:
"name": provider.name,      # CORRECT

# Line 117: Remove or handle
"description": provider.description,  # DOESN'T EXIST - REMOVE

# Line 120: Change
"context_window": provider.context_window,  # WRONG
# To:
"context_window": provider.max_context_tokens,  # CORRECT

# Line 123: Remove
"available": provider.available,  # DOESN'T EXIST - REMOVE

# Line 124: Remove
"auth_methods": provider.auth_methods,  # DOESN'T EXIST - REMOVE
```

**Method: `_get_provider_models()` (lines 149-189)**

Changes needed:
```python
# Line 182: Change
"context_window": metadata.context_window,  # WRONG
# To:
"context_window": metadata.max_context_tokens,  # CORRECT
```

## Recommended Fixes

### Fix 1: ProviderMetadata Attribute Name
**File:** `src/socratic_agents/models.py`  
**Action:** No change needed - field is correctly named `name`

### Fix 2: multi_llm_agent.py - _list_providers()
**File:** `src/socratic_agents/multi_llm_agent.py`  
**Lines:** 113, 117, 120, 123, 124

```python
def _list_providers(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """List all available LLM providers with configuration status."""
    self.logger.debug("Listing available LLM providers")
    user_id = data.get("user_id")

    try:
        providers = list_available_providers()
        provider_dicts = []

        for provider in providers:
            # Transform backend provider metadata to frontend format
            provider_dict = {
                "name": provider.name,  # FIX: was provider.provider
                "label": provider.display_name,
                "models": provider.models,
                "requires_api_key": provider.requires_api_key,
                # REMOVED: "description": provider.description,  (doesn't exist)
                "cost_per_1k_input_tokens": provider.cost_per_1k_input_tokens,
                "cost_per_1k_output_tokens": provider.cost_per_1k_output_tokens,
                "context_window": provider.max_context_tokens,  # FIX: was provider.context_window
                "supports_streaming": provider.supports_streaming,
                "supports_vision": provider.supports_vision,
                # REMOVED: "available": provider.available,  (doesn't exist)
                # REMOVED: "auth_methods": provider.auth_methods,  (doesn't exist)
            }

            # Check if user has configured this provider (has API key)
            if user_id:
                try:
                    api_key = self.orchestrator.database.get_api_key(user_id, provider.name)  # FIX: was provider.provider
                    provider_dict["is_configured"] = api_key is not None
                except Exception as e:
                    self.logger.debug(f"Error checking API key for {provider.name}: {e}")  # FIX: was provider.provider
                    provider_dict["is_configured"] = False
            else:
                provider_dict["is_configured"] = False

            provider_dicts.append(provider_dict)

        self.logger.info(f"Listed {len(providers)} LLM providers for user {user_id}")
        return {"status": "success", "providers": provider_dicts, "count": len(providers)}

    except Exception as e:
        self.logger.error(f"Error listing providers: {e}")
        return {"status": "error", "message": str(e)}
```

### Fix 3: multi_llm_agent.py - _get_provider_models()
**File:** `src/socratic_agents/multi_llm_agent.py`  
**Lines:** 182

```python
def _get_provider_models(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Get available models for a specific provider."""
    provider = data.get("provider", "").lower()

    if not provider:
        return {"status": "error", "message": "Provider name required"}

    self.logger.debug(f"Getting models for provider: {provider}")

    try:
        metadata = get_provider_metadata(provider)

        if not metadata:
            return {"status": "error", "message": f"Unknown provider: {provider}"}

        return {
            "status": "success",
            "provider": provider,
            "models": metadata.models,
            "default_model": metadata.models[0] if metadata.models else None,
            "context_window": metadata.max_context_tokens,  # FIX: was metadata.context_window
            "supports_streaming": metadata.supports_streaming,
            "supports_vision": metadata.supports_vision,
        }

    except Exception as e:
        self.logger.error(f"Error getting provider models: {e}")
        return {"status": "error", "message": str(e)}
```

## Additional Notes

**List of all `provider.provider` references to fix:**
- Line 113: `"name": provider.provider,` → `"name": provider.name,`
- Line 130: `self.orchestrator.database.get_api_key(user_id, provider.provider)` → `provider.name`
- Line 133: Logging statement uses `provider.provider` → should be `provider.name`

## Next Steps

1. Apply fixes to multi_llm_agent.py
2. Run tests to verify
3. Commit changes
4. Push to GitHub
5. Wait for GitHub Actions to pass
6. Publish to PyPI

## Status

- [x] Issues identified
- [ ] Fixes applied
- [ ] Tests passing
- [ ] Changes committed
- [ ] Changes pushed
- [ ] GitHub Actions passing
- [ ] PyPI updated

---

**Priority:** HIGH - These are breaking issues that prevent the agent from working with ProviderMetadata
