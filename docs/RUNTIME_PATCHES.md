# Runtime Patches Documentation

This document describes all runtime patches applied to external dependencies for compatibility with Socrates. These patches are automatically applied in `socratic_system/patches.py` during orchestrator initialization.

## Overview

Runtime patches resolve incompatibilities between Socrates and its PyPI dependencies:
- **socratic-agents** - Multi-LLM agent orchestration library
- **socratic-nexus** - Client and communication library

These patches are **temporary** and should be removed once upstream packages are updated.

---

## Patches Applied

### 1. Encryption Patch: `patch_claude_client_decryption()`

**Problem:**
- `socratic-nexus.clients.claude_client.ClaudeClient` may use legacy encryption methods
- Socrates uses unified encryption (`socratic_system.encryption`) with PBKDF2-Fernet
- Inconsistent encryption/decryption causes API key retrieval failures

**Solution:**
- Patches `ClaudeClient._decrypt_api_key_from_db()` to use `decrypt_data()` from `socratic_system.encryption`
- Falls back to original method if unified decryption fails (backward compatibility)
- Logs errors at both stages for debugging

**Status:** ✅ Active
**Lines:** socratic_system/patches.py:18-63

**When to update:**
- If `socratic-nexus` is updated to use unified encryption natively
- Check: Does `ClaudeClient._decrypt_api_key_from_db()` import from `socratic_system.encryption`?
- If yes, remove this patch

---

### 2. LLM Provider Patch: `patch_list_available_providers()`

**Problem:**
- `socratic-agents` PyPI version returns string list: `["claude", "openai", ...]`
- `MultiLLMAgent` expects `ProviderMetadata` objects with attributes like `.models`, `.cost_per_1k_input_tokens`, etc.
- Causes AttributeError when agent processes provider information

**Solution:**
- Patches `socratic_agents.models.list_available_providers()` to return `ProviderMetadata` objects
- Uses Socrates' `get_provider_metadata()` to create proper objects with all required attributes
- References: `socratic_system/models/llm_provider.py` (PROVIDER_METADATA)

**Status:** ✅ Active
**Lines:** socratic_system/patches.py:66-91

**When to update:**
- If `socratic-agents` is updated to return `ProviderMetadata` objects natively
- Check: Does `list_available_providers()` return objects with `.models` attribute?
- If yes, remove this patch

---

### 3. LLM Agent Patch: `patch_multi_llm_agent()`

**Problem:**
- `MultiLLMAgent._list_providers()` accesses `ProviderMetadata` attributes incorrectly
- Uses `.name` instead of `.provider` (Socrates' ProviderMetadata uses `.provider`)
- Uses `.max_context_tokens` instead of `.context_window`
- Causes attribute errors when listing available providers

**Solution:**
- Patches `_list_providers()` method to use correct attribute names
- Maps: `.name` → `.provider`, `.max_context_tokens` → `.context_window`
- Adds fallback for missing optional attributes (description, auth_methods)

**Status:** ✅ Active
**Lines:** socratic_system/patches.py:94-151

**When to update:**
- If `socratic-agents` is updated to match Socrates' ProviderMetadata schema
- Check: Does `MultiLLMAgent._list_providers()` use `.provider` and `.context_window`?
- If yes, remove this patch

---

### 4. Provider Config Patch: `patch_multi_llm_agent_provider_config()`

**Problem:**
- Socrates' database returns flattened dicts from `get_user_llm_config()`:
  ```python
  {
    "id": str,
    "provider": str,
    "is_default": bool,
    "enabled": bool,
    "settings": dict
  }
  ```
- `MultiLLMAgent` methods (`_set_default_provider`, `_set_provider_model`, `_get_provider_config`) expect `LLMProviderConfig` objects with attributes
- Code tries: `existing.is_default = True` on dict, causing `'dict' object has no attribute 'is_default'`

**Solution:**
- Patches three `MultiLLMAgent` methods to convert dict responses to `LLMProviderConfig` objects
- Provides `dict_to_config()` helper for consistent conversion
- Saves converted objects back to database as dicts (maintains database contract)

**Methods Patched:**
1. `_set_default_provider(data)` - Sets default provider for user
2. `_set_provider_model(data)` - Sets model for specific provider
3. `_get_provider_config(data)` - Retrieves provider configuration

**Status:** ✅ Active
**Lines:** socratic_system/patches.py:154-269

**When to update:**
- If `socratic-agents` is updated to handle dict configs natively
- If database contract changes (dict → object conversion)
- Check: Does `MultiLLMAgent` methods accept dict configs directly?
- If yes, update conversion logic

---

## Data Contract: Database ↔ MultiLLMAgent

### Database Returns (dict)
```python
{
    "id": "config-123",
    "user_id": "user-456",
    "provider": "claude",
    "is_default": True,
    "enabled": True,
    "settings": {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 4096,
        "temperature": 0.7
    },
    "created_at": "2026-06-17T01:37:00+00:00",
    "updated_at": "2026-06-17T01:37:00+00:00"
}
```

### Agent Expects (LLMProviderConfig object)
```python
LLMProviderConfig(
    id="config-123",
    user_id="user-456",
    provider="claude",
    is_default=True,
    enabled=True,
    settings={...},
    created_at=datetime(...),
    updated_at=datetime(...)
)
```

**The patch converts between these two formats transparently.**

---

## Patch Application Order

Patches are applied in this order (from `apply_all_patches()`):

1. **Encryption patches** (security-critical)
   - `patch_claude_client_decryption()`

2. **LLM provider patches** (agent compatibility)
   - `patch_list_available_providers()`
   - `patch_multi_llm_agent()`
   - `patch_multi_llm_agent_provider_config()`

Order ensures encryption is unified before agents try to access API keys.

---

## Maintenance Checklist

### When Updating `socratic-agents`
- [ ] Check CHANGELOG for LLM provider handling fixes
- [ ] Verify `list_available_providers()` returns objects, not strings
- [ ] Test `MultiLLMAgent._list_providers()` with Socrates ProviderMetadata
- [ ] Test `_set_default_provider()` with dict configs from database
- [ ] Test `_set_provider_model()` with dict configs
- [ ] Test `_get_provider_config()` with dict configs
- [ ] Remove/update patches if compatible with Socrates' data structure

### When Updating `socratic-nexus`
- [ ] Check if `ClaudeClient` uses unified encryption
- [ ] Verify decryption works with Socrates' salt:encrypted format
- [ ] Test API key retrieval for Claude provider
- [ ] Remove `patch_claude_client_decryption()` if integrated

### Testing Patches
```bash
# Run in Python interpreter
from socratic_system.patches import apply_all_patches
apply_all_patches()  # Should see 5 "Patched..." log messages

# Verify imports work
from socratic_agents.multi_llm_agent import MultiLLMAgent
from socratic_nexus.clients.claude_client import ClaudeClient

# Test API startup
socrates-api --port 8000
# Should start without "dict object has no attribute" errors
```

---

## Related Files

- **Implementation:** `socratic_system/patches.py`
- **Encryption:** `socratic_system/encryption.py`
- **LLM Models:** `socratic_system/models/llm_provider.py`
- **Database:** `socratic_system/database/project_db.py` (get_user_llm_config methods)
- **Tests:** `tests/test_*patches*` or `tests/test_llm_*`

---

## Version History

| Date | Patch | Status |
|------|-------|--------|
| 2026-06-17 | Provider Config Dict Handling | Added |
| 2026-06-17 | Claude Client Encryption | Restored |
| 2026-05-17 | MultiLLMAgent Attribute Names | Active |
| 2026-05-17 | list_available_providers Return Type | Active |

---

## Future: Removing Patches

Once upstream packages are compatible, patches can be removed by:

1. **Verify upstream compatibility** (see checklists above)
2. **Comment out** `apply_all_patches()` in `socratic_system/orchestration/orchestrator.py:75`
3. **Test thoroughly** (API startup, agent operations, encryption)
4. **Delete patch function** and update `apply_all_patches()`
5. **Document in CHANGELOG** when patches are no longer needed
