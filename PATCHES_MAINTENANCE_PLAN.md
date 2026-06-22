# Patches Maintenance Plan - Architecture Cleanup

This document outlines all runtime patches currently applied to Socrates and the plan to move them to their respective libraries.

## Summary

Currently, **5 major patches** are applied at runtime in `socratic_system/patches.py`. These patches fix incompatibilities between:
- **socratic-agents** PyPI package (outdated code)
- **socratic-nexus** (legacy encryption, missing clients)
- Socrates' unified encryption and provider awareness system

All patches are temporary until upstream packages are updated properly.

---

## Patch-by-Patch Breakdown

### 1. **Encryption Patch** ❌ → Should be in `socratic-nexus`

**Location:** `patch_claude_client_decryption()` in `socratic_system/patches.py`

**Issue:** 
- `socratic-nexus.clients.ClaudeClient` uses legacy or different encryption than Socrates
- Causes API key decryption failures when retrieving from database

**Current Patch:** 
- Overrides `ClaudeClient._decrypt_api_key_from_db()` 
- Uses unified `decrypt_data()` from `socratic_system.encryption`
- Falls back to original implementation for backward compatibility

**Fix Needed:**
Update `socratic-nexus` ClaudeClient to:
```python
# In socratic-nexus/clients/claude_client.py
from socratic_system.encryption import decrypt_data

def _decrypt_api_key_from_db(self, encrypted_key: str):
    return decrypt_data(encrypted_key)
```

**Owner:** `socratic-nexus` library
**Priority:** 🔴 HIGH (Security-critical)
**Effort:** Small (1-2 files)

---

### 2. **Provider Metadata Return Type** ❌ → Should be in `socratic-agents`

**Location:** `patch_list_available_providers()` in `socratic_system/patches.py`

**Issue:**
- PyPI version of `socratic_agents.models.list_available_providers()` returns strings
- Socrates and agents expect `ProviderMetadata` objects
- Causes AttributeError when accessing `.provider`, `.models`, etc.

**Current Patch:**
```python
def patched_list_available_providers():
    provider_names = ["claude", "openai", "gemini", "ollama"]
    return [get_provider_metadata(name) for name in provider_names]
```

**Fix Needed:**
Update `socratic-agents` to return `ProviderMetadata` objects:
```python
# In socratic-agents/models.py
def list_available_providers():
    provider_names = ["claude", "openai", "gemini", "ollama"]
    return [get_provider_metadata(name) for name in provider_names]
```

**Owner:** `socratic-agents` library
**Priority:** 🟠 MEDIUM
**Effort:** Trivial (1 function)

---

### 3. **MultiLLMAgent Attribute Naming** ❌ → Should be in `socratic-agents`

**Location:** `patch_multi_llm_agent()` in `socratic_system/patches.py`

**Issue:**
- `MultiLLMAgent._list_providers()` assumes `ProviderMetadata.name` exists
- Actual attribute is `ProviderMetadata.provider`
- Also accesses non-existent `.context_window` (should use `.context_length` or similar)

**Current Patch:** (93 lines)
- Rewrites entire `_list_providers()` method
- Uses correct attributes: `.provider`, `.display_name`, `.models`, etc.
- Handles `is_configured` check via database

**Fix Needed:**
Update `socratic-agents` MultiLLMAgent:
```python
# In socratic-agents/multi_llm_agent.py
def _list_providers(self, data):
    user_id = data.get("user_id")
    providers = list_available_providers()
    provider_dicts = []
    
    for provider in providers:
        provider_dict = {
            "name": provider.provider,  # NOT provider.name
            "label": provider.display_name,
            "models": provider.models,
            # ... use correct attributes from ProviderMetadata
        }
        provider_dicts.append(provider_dict)
    
    return {"status": "success", "providers": provider_dicts}
```

**Owner:** `socratic-agents` library
**Priority:** 🟠 MEDIUM
**Effort:** Medium (one method, ~80 lines)

---

### 4. **Provider Config Dict/Object Handling** ❌ → Should be in `socratic-agents`

**Location:** `patch_multi_llm_agent_provider_config()` in `socratic_system/patches.py`

**Issue:**
- Database returns provider config as flattened dicts
- `MultiLLMAgent` expects `LLMProviderConfig` objects
- Methods fail when accessing object attributes on dicts

**Current Patch:** (3 methods, ~150 lines)
- `patched_set_default_provider()` - handles object/dict conversion
- `patched_set_provider_model()` - same
- `patched_get_provider_config()` - same

**Fix Needed:**
Add helper method to `socratic-agents`:
```python
# In socratic-agents/multi_llm_agent.py
def _ensure_config_object(self, config_dict):
    """Convert dict to LLMProviderConfig if needed"""
    if not config_dict:
        return None
    if isinstance(config_dict, dict) and not isinstance(config_dict, LLMProviderConfig):
        return LLMProviderConfig.from_dict(config_dict)
    return config_dict

# Then update methods to use:
existing = self._ensure_config_object(existing_dict)
```

**Owner:** `socratic-agents` library
**Priority:** 🟠 MEDIUM
**Effort:** Medium (~150 lines to refactor)

---

### 5. **Provider-Aware Agent Execution** ⚠️ → Should be in `socratic-agents` + `socratic-nexus`

**Location:** `patch_agents_for_provider_awareness()` in `socratic_system/patches.py`

**Issue:**
- Agents only use `orchestrator.claude_client` (hardcoded)
- User's default provider (e.g., Ollama) is completely ignored
- Setting Ollama as default provider has no effect

**Current Patch:** (185 lines)
- Patches `Agent.process()` to check request for `provider_config`
- Adds `_get_llm_client_for_provider()` helper
- Creates provider-specific clients (Ollama, OpenAI, Gemini, etc.)
- Temporarily swaps `orchestrator.claude_client` during execution

**Fix Needed:**
This is more complex. Update both libraries:

**In `socratic-agents/base_agent.py`:**
```python
# Add provider awareness to Agent.process()
def process(self, request_data=None):
    if request_data is None:
        request_data = {}
    
    provider_config = request_data.get("provider_config")
    if provider_config:
        client = self._get_llm_client_for_provider(provider_config)
        # Use client instead of orchestrator.claude_client
        # ...
    return result

def _get_llm_client_for_provider(self, provider_config):
    """Factory method to get LLM client for provider"""
    provider = provider_config.get("provider", "claude")
    # Create appropriate client based on provider
```

**In `socratic-nexus/clients/`:**
- Add or verify `OllamaClient`, `OpenAIClient`, `GeminiClient` exist
- Ensure all clients have consistent interfaces

**Owner:** `socratic-agents` (primary) + `socratic-nexus` (clients)
**Priority:** 🔴 HIGH (Core feature)
**Effort:** High (~200 lines + client implementations)

---

## Migration Priority & Timeline

### Phase 1: Security & Core (Do First)
- ✅ Encryption patch → socratic-nexus
- ✅ Provider metadata return type → socratic-agents
- **Effort:** 3-4 hours
- **Impact:** Unblocks everything else

### Phase 2: Agent Compatibility (Do Second)
- ✅ MultiLLMAgent attribute naming → socratic-agents
- ✅ Provider config handling → socratic-agents
- **Effort:** 4-6 hours
- **Impact:** Stable agent execution

### Phase 3: Feature Completion (Do Third)
- ✅ Provider-aware execution → socratic-agents + socratic-nexus
- **Effort:** 6-8 hours
- **Impact:** Users can use their default LLM provider

### Phase 4: Cleanup
- Remove patches.py from Socrates
- Update orchestrator to NOT apply patches
- Mark libraries as updated in pyproject.toml

---

## Current Patch Application

**File:** `socratic_system/orchestration/orchestrator.py`

```python
# In __init__ or startup
from socratic_system.patches import apply_all_patches
apply_all_patches()  # Remove this once patches are in libraries
```

---

## Library Update Checklist

### socratic-agents
- [ ] Update `list_available_providers()` to return ProviderMetadata
- [ ] Fix `MultiLLMAgent._list_providers()` attribute names
- [ ] Add config dict/object conversion helpers
- [ ] Add provider awareness to `Agent.process()`
- [ ] Add `_get_llm_client_for_provider()` factory
- [ ] Test with Socrates without patches

### socratic-nexus
- [ ] Update `ClaudeClient._decrypt_api_key_from_db()` to use unified encryption
- [ ] Ensure `OllamaClient` is fully implemented
- [ ] Ensure `OpenAIClient` is implemented
- [ ] Ensure `GeminiClient` is implemented
- [ ] Test all clients with Socrates

---

## Testing After Migration

Once patches are moved to libraries:

1. **Install updated libraries:**
   ```bash
   pip install --upgrade socratic-agents socratic-nexus
   ```

2. **Remove patch application from Socrates:**
   ```python
   # In orchestrator.py - REMOVE this
   # from socratic_system.patches import apply_all_patches
   # apply_all_patches()
   ```

3. **Run full test suite:**
   ```bash
   pytest tests/ -v
   ```

4. **Test critical flows:**
   - User adds Anthropic API key → ✅ Decrypts correctly
   - User lists available providers → ✅ Returns metadata objects
   - User sets Ollama as default → ✅ Agents use Ollama
   - User requests with provider_config → ✅ Uses correct provider

---

## Files Affected

**Socrates (to remove):**
- `socratic_system/patches.py` → DELETE
- `socratic_system/orchestration/orchestrator.py` → Remove patch application

**Libraries (to update):**
- `socratic-agents/socratic_agents/models.py`
- `socratic-agents/socratic_agents/multi_llm_agent.py`
- `socratic-agents/socratic_agents/base_agent.py`
- `socratic-nexus/socratic_nexus/clients/claude_client.py`
- `socratic-nexus/socratic_nexus/clients/ollama_client.py` (verify exists)
- `socratic-nexus/socratic_nexus/clients/openai_client.py` (verify exists)
- `socratic-nexus/socratic_nexus/clients/gemini_client.py` (verify exists)

---

## Notes

- All patches have fallback mechanisms (don't break if library is old)
- Migration is backward-compatible (old versions still work with patches)
- Libraries can be updated independently
- Each library update should include tests

