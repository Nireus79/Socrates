# Complete Architecture Fix Guide - Patches Migration

**Status:** In Planning  
**Owner:** Nireus79  
**Start Date:** 2026-06-22  
**Target Completion:** TBD  

This document provides step-by-step instructions to properly migrate all runtime patches from Socrates into their respective library repositories, test them, publish to PyPI, then update Socrates.

---

## Overview

### Current State
- 5 runtime patches live in `socratic_system/patches.py` 
- Patches monkey-patch libraries at Socrates startup
- Libraries are out of sync with Socrates' requirements

### Target State
- All patches moved to their source libraries
- Libraries pass GitHub Actions tests
- Libraries published to PyPI
- Socrates updated to use library versions WITHOUT patches
- `patches.py` deleted from Socrates

### Timeline
1. **Phase 1:** Update socratic-nexus (Days 1-2)
2. **Phase 2:** Update socratic-agents (Days 3-5)
3. **Phase 3:** Update Socrates (Day 6)
4. **Phase 4:** Clean up and verify (Day 7)

---

## PHASE 1: Update socratic-nexus Library

### Task 1.1: Encryption Unification (socratic-nexus)

**What needs to be fixed:**
- `socratic-nexus/clients/claude_client.py` uses legacy encryption
- Needs to use unified `decrypt_data()` from Socrates

**Steps:**

1. **Clone socratic-nexus repository** (if not already done)
   ```bash
   cd ~/socratic-libraries  # Or appropriate directory
   git clone https://github.com/Nireus79/socratic-nexus.git
   cd socratic-nexus
   git checkout main
   git pull origin main
   ```

2. **Review current ClaudeClient implementation**
   ```bash
   cat socratic_nexus/clients/claude_client.py | grep -A 20 "_decrypt_api_key"
   ```

3. **Update ClaudeClient._decrypt_api_key_from_db()**
   
   File: `socratic_nexus/clients/claude_client.py`
   
   Replace:
   ```python
   def _decrypt_api_key_from_db(self, encrypted_key: str):
       # [old legacy decryption code]
   ```
   
   With:
   ```python
   def _decrypt_api_key_from_db(self, encrypted_key: str):
       """Decrypt API key using unified encryption system.
       
       Uses PBKDF2-Fernet encryption from socratic_system.encryption
       for consistency across all components.
       """
       try:
           from socratic_system.encryption import decrypt_data
           return decrypt_data(encrypted_key)
       except ImportError:
           self.logger.warning(
               "socratic_system not available, falling back to legacy decryption"
           )
           # Fallback to original implementation if needed
           return self._legacy_decrypt_api_key(encrypted_key)
       except Exception as e:
           self.logger.error(f"Failed to decrypt API key: {e}")
           return None
   ```

4. **Verify imports are available**
   ```bash
   grep -r "from socratic_system" socratic_nexus/
   ```
   
   If not present, add to `pyproject.toml`:
   ```toml
   dependencies = [
       "socratic-system>=1.0.0",  # Add this
       # ... other deps
   ]
   ```

5. **Run local tests**
   ```bash
   cd socratic-nexus
   pytest tests/test_claude_client.py -v
   # OR
   pytest tests/ -k "encryption" -v
   ```

6. **Commit changes**
   ```bash
   git add socratic_nexus/clients/claude_client.py
   git add pyproject.toml  # If dependencies changed
   git commit -m "fix: use unified encryption in ClaudeClient

   - Update _decrypt_api_key_from_db() to use socratic_system.encryption.decrypt_data()
   - Adds fallback to legacy decryption for backward compatibility
   - Ensures consistent encryption/decryption across all components
   
   This removes the need for the patch_claude_client_decryption() patch in Socrates."
   ```

7. **Push to remote**
   ```bash
   git push origin main
   ```

8. **Monitor GitHub Actions**
   - Go to: `https://github.com/Nireus79/socratic-nexus/actions`
   - Wait for workflow to complete (usually 5-10 minutes)
   - ✅ All checks must pass (tests, linting, coverage)
   - ❌ If failed, fix issues and push again

### Task 1.2: Verify LLM Clients are Complete (socratic-nexus)

**What needs to be verified:**
- `OllamaClient` exists and is fully implemented
- `OpenAIClient` exists and is fully implemented  
- `GeminiClient` exists and is fully implemented
- All have consistent interfaces with `ClaudeClient`

**Steps:**

1. **Check for missing client implementations**
   ```bash
   ls -la socratic_nexus/clients/
   # Should see: claude_client.py, ollama_client.py, openai_client.py, gemini_client.py
   ```

2. **For each missing client, create it:**
   
   **If OllamaClient missing:**
   
   Create `socratic_nexus/clients/ollama_client.py`:
   ```python
   """Ollama LLM client for local model inference."""
   import logging
   from typing import Optional, List, Dict, Any
   import httpx
   
   logger = logging.getLogger(__name__)
   
   class OllamaClient:
       """Client for Ollama local LLM inference."""
       
       def __init__(
           self,
           model: str = "mistral:latest",
           base_url: str = "http://localhost:11434",
           temperature: float = 0.3,
       ):
           """Initialize Ollama client.
           
           Args:
               model: Model name (e.g., 'mistral:latest', 'codellama:13b')
               base_url: Ollama API endpoint
               temperature: Sampling temperature (0.0-1.0)
           """
           self.model = model
           self.base_url = base_url.rstrip('/')
           self.temperature = temperature
           self.client = httpx.AsyncClient(timeout=60.0)
           
       async def generate(
           self,
           prompt: str,
           system: Optional[str] = None,
           stream: bool = False,
       ) -> str:
           """Generate response using Ollama.
           
           Args:
               prompt: Input prompt
               system: System prompt/instructions
               stream: Whether to stream response
               
           Returns:
               Generated text response
           """
           try:
               payload = {
                   "model": self.model,
                   "prompt": prompt,
                   "temperature": self.temperature,
                   "stream": stream,
               }
               if system:
                   payload["system"] = system
               
               response = await self.client.post(
                   f"{self.base_url}/api/generate",
                   json=payload,
               )
               response.raise_for_status()
               
               result = response.json()
               return result.get("response", "")
               
           except Exception as e:
               logger.error(f"Ollama API error: {e}")
               raise
       
       async def list_models(self) -> List[str]:
           """List available models on Ollama server."""
           try:
               response = await self.client.get(f"{self.base_url}/api/tags")
               response.raise_for_status()
               data = response.json()
               return [m["name"] for m in data.get("models", [])]
           except Exception as e:
               logger.error(f"Failed to list Ollama models: {e}")
               return []
       
       async def __aenter__(self):
           return self
       
       async def __aexit__(self, exc_type, exc_val, exc_tb):
           await self.client.aclose()
   ```

3. **Verify client interfaces match**
   ```bash
   # All clients should have these methods:
   grep -r "def generate\|def chat\|def __init__" socratic_nexus/clients/*.py
   ```

4. **Update `socratic_nexus/clients/__init__.py`** to export all clients:
   ```python
   from .claude_client import ClaudeClient
   from .ollama_client import OllamaClient
   from .openai_client import OpenAIClient
   from .gemini_client import GeminiClient
   
   __all__ = [
       "ClaudeClient",
       "OllamaClient", 
       "OpenAIClient",
       "GeminiClient",
   ]
   ```

5. **Test all clients can be imported**
   ```bash
   python3 -c "from socratic_nexus.clients import ClaudeClient, OllamaClient, OpenAIClient, GeminiClient; print('✓ All clients importable')"
   ```

6. **Commit and push**
   ```bash
   git add socratic_nexus/clients/
   git commit -m "feat: add complete LLM client implementations

   - Implement OllamaClient for local model inference
   - Ensure OpenAIClient and GeminiClient are complete
   - Add consistent interfaces across all clients
   - Update __init__.py for proper exports"
   git push origin main
   ```

7. **Wait for GitHub Actions** ✅

### Task 1.3: Publish socratic-nexus to PyPI

**Prerequisites:**
- All GitHub Actions tests passed ✅
- Code review completed
- Ready for release

**Steps:**

1. **Determine version bump** (follow semver)
   ```bash
   cd socratic-nexus
   git log --oneline -5
   # Decide: major, minor, or patch bump
   ```

2. **Trigger release workflow**
   ```bash
   # Option 1: Via GitHub CLI
   gh workflow run release.yml -f version-type=minor
   
   # Option 2: Manually
   # Go to: https://github.com/Nireus79/socratic-nexus/actions/workflows/release.yml
   # Click "Run workflow" → select version-type
   ```

3. **Monitor release process**
   - Workflow bumps version in `pyproject.toml`
   - Creates git tag (e.g., `v1.2.0`)
   - Builds distribution (`setup.py sdist bdist_wheel`)
   - Publishes to PyPI
   - Takes ~10 minutes total

4. **Verify on PyPI**
   ```bash
   pip index versions socratic-nexus
   # Should show new version at top
   
   # Install and verify
   pip install --upgrade socratic-nexus
   python3 -c "import socratic_nexus; print(socratic_nexus.__version__)"
   ```

5. **Document the version**
   ```bash
   echo "socratic-nexus updated to: X.Y.Z" >> ~/PATCH_MIGRATION_LOG.md
   ```

---

## PHASE 2: Update socratic-agents Library

### Task 2.1: Fix Provider Metadata Return Type

**File:** `socratic_agents/models.py`

**Current Issue:**
```python
def list_available_providers():
    return ["claude", "openai", "gemini", "ollama"]  # ❌ Returns strings
```

**Required Fix:**
```python
def list_available_providers():
    """List all available LLM providers.
    
    Returns:
        List[ProviderMetadata]: Metadata objects for each provider
    """
    provider_names = ["claude", "openai", "gemini", "ollama"]
    return [get_provider_metadata(name) for name in provider_names]
```

**Steps:**

1. **Clone socratic-agents repository**
   ```bash
   cd ~/socratic-libraries
   git clone https://github.com/Nireus79/socratic-agents.git
   cd socratic-agents
   git pull origin main
   ```

2. **Locate and review `models.py`**
   ```bash
   cat socratic_agents/models.py | grep -A 10 "def list_available_providers"
   ```

3. **Update the function**
   ```bash
   # Edit socratic_agents/models.py
   nano socratic_agents/models.py
   # OR use your editor
   ```

4. **Verify ProviderMetadata class exists**
   ```bash
   grep -r "class ProviderMetadata" socratic_agents/
   grep -r "def get_provider_metadata" socratic_agents/
   ```

5. **Test locally**
   ```bash
   python3 << 'EOF'
   from socratic_agents.models import list_available_providers
   providers = list_available_providers()
   for p in providers:
       assert hasattr(p, 'provider'), f"Missing .provider on {p}"
       assert hasattr(p, 'display_name'), f"Missing .display_name on {p}"
       print(f"✓ {p.provider}: {p.display_name}")
   print("All providers have required attributes")
   EOF
   ```

6. **Commit and push**
   ```bash
   git add socratic_agents/models.py
   git commit -m "fix: list_available_providers returns ProviderMetadata objects

   - Changed return type from List[str] to List[ProviderMetadata]
   - Enables downstream code to access provider properties directly
   - Removes need for patch_list_available_providers() in Socrates"
   git push origin main
   ```

### Task 2.2: Fix MultiLLMAgent Attribute Names

**File:** `socratic_agents/multi_llm_agent.py`

**Current Issue:**
- Uses `.name` instead of `.provider` on ProviderMetadata
- Uses non-existent `.context_window` attribute
- Doesn't properly convert database configs (dicts) to objects

**Steps:**

1. **Review current implementation**
   ```bash
   cat socratic_agents/multi_llm_agent.py | grep -A 50 "def _list_providers"
   ```

2. **Create new helper method** (add to MultiLLMAgent class):
   ```python
   def _ensure_config_object(self, config_dict):
       """Convert dict to LLMProviderConfig if needed.
       
       Database returns configs as dicts, but agent methods expect objects.
       This helper ensures consistent handling.
       """
       if not config_dict:
           return None
       if isinstance(config_dict, dict) and not isinstance(config_dict, LLMProviderConfig):
           return LLMProviderConfig.from_dict(config_dict)
       return config_dict
   ```

3. **Fix `_list_providers()` method**
   
   Replace entire method with:
   ```python
   def _list_providers(self, data):
       """List available LLM providers with user configuration status.
       
       Returns provider metadata along with whether user has configured each.
       """
       self.logger.debug("Listing available LLM providers")
       user_id = data.get("user_id")

       try:
           from socratic_agents.models import list_available_providers
           
           providers = list_available_providers()
           provider_dicts = []

           for provider in providers:
               # Transform backend provider metadata to frontend format
               provider_dict = {
                   "name": provider.provider,  # ✅ Use .provider, not .name
                   "label": provider.display_name,
                   "models": provider.models,
                   "requires_api_key": provider.requires_api_key,
                   "description": getattr(provider, "description", ""),
                   "cost_per_1k_input_tokens": provider.cost_per_1k_input_tokens,
                   "cost_per_1k_output_tokens": provider.cost_per_1k_output_tokens,
                   "context_window": provider.context_window,
                   "supports_streaming": provider.supports_streaming,
                   "supports_vision": provider.supports_vision,
                   "available": provider.available,
                   "auth_methods": provider.auth_methods,
               }

               # Check if user has configured this provider
               if user_id:
                   try:
                       api_key = self.orchestrator.database.get_api_key(
                           user_id, provider.provider
                       )
                       provider_dict["is_configured"] = api_key is not None
                   except Exception as e:
                       self.logger.debug(
                           f"Error checking API key for {provider.provider}: {e}"
                       )
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

4. **Fix `_set_default_provider()` method**
   
   Add `_ensure_config_object()` calls:
   ```python
   # Get existing config (convert dict to object)
   existing_dict = self.orchestrator.database.get_user_llm_config(user_id, provider)
   existing = self._ensure_config_object(existing_dict)  # ✅ Use helper

   if existing:
       existing.is_default = True
       existing.enabled = True
       existing.settings = settings or existing.settings
       config = existing
   else:
       config = LLMProviderConfig(...)
   ```

5. **Fix `_set_provider_model()` method**
   
   Same pattern - use `_ensure_config_object()` helper

6. **Fix `_get_provider_config()` method**
   
   ```python
   # Get all configs (convert dicts to objects)
   configs_list = self.orchestrator.database.get_user_llm_configs(user_id)
   configs = [self._ensure_config_object(c) for c in configs_list]  # ✅ Use helper
   ```

7. **Test locally**
   ```bash
   python3 << 'EOF'
   from socratic_agents.multi_llm_agent import MultiLLMAgent
   # Instantiate and test methods
   # Should not throw AttributeError about .name or .context_window
   print("✓ MultiLLMAgent methods work correctly")
   EOF
   ```

8. **Commit and push**
   ```bash
   git add socratic_agents/multi_llm_agent.py
   git commit -m "fix: correct ProviderMetadata attribute access in MultiLLMAgent

   - Use .provider instead of .name
   - Add _ensure_config_object() helper for dict/object conversion
   - Fix all three provider config methods to handle database dicts
   - Removes need for patch_multi_llm_agent() and patch_multi_llm_agent_provider_config() in Socrates"
   git push origin main
   ```

### Task 2.3: Add Provider Awareness to Agents

**File:** `socratic_agents/base_agent.py`

**Current Issue:**
- Agents only use `orchestrator.claude_client` (hardcoded)
- User's default provider setting is ignored

**Steps:**

1. **Review Agent.process() method**
   ```bash
   grep -A 30 "def process" socratic_agents/base_agent.py | head -40
   ```

2. **Add helper method to Agent class:**
   ```python
   def _get_llm_client_for_provider(self, provider_config):
       """Get LLM client factory for specified provider.
       
       Args:
           provider_config: Dict with 'provider' and 'settings' keys
           
       Returns:
           LLM client instance for the provider
       """
       provider = provider_config.get("provider", "claude")
       settings = provider_config.get("settings", {})

       self.logger.debug(f"Getting LLM client for provider: {provider}")

       try:
           if provider == "claude":
               # Use existing Claude client
               return (
                   self.orchestrator.claude_client
                   if hasattr(self, "orchestrator")
                   else None
               )

           elif provider == "ollama":
               try:
                   from socratic_nexus.clients.ollama_client import OllamaClient
                   
                   model = settings.get("model", "mistral:latest")
                   base_url = settings.get("api_endpoint", "http://localhost:11434")
                   
                   return OllamaClient(
                       model=model,
                       base_url=base_url,
                       temperature=settings.get("temperature", 0.3),
                   )
               except ImportError:
                   self.logger.warning("OllamaClient not available, using Claude")
                   return self.orchestrator.claude_client if hasattr(self, "orchestrator") else None

           elif provider == "openai":
               try:
                   from socratic_nexus.clients.openai_client import OpenAIClient
                   
                   return OpenAIClient(
                       model=settings.get("model", "gpt-4"),
                       temperature=settings.get("temperature", 0.7),
                   )
               except ImportError:
                   self.logger.warning("OpenAIClient not available, using Claude")
                   return self.orchestrator.claude_client if hasattr(self, "orchestrator") else None

           elif provider == "gemini":
               try:
                   from socratic_nexus.clients.gemini_client import GeminiClient
                   
                   return GeminiClient(
                       model=settings.get("model", "gemini-pro"),
                       temperature=settings.get("temperature", 0.7),
                   )
               except ImportError:
                   self.logger.warning("GeminiClient not available, using Claude")
                   return self.orchestrator.claude_client if hasattr(self, "orchestrator") else None

           else:
               self.logger.warning(f"Unknown provider: {provider}, using Claude")
               return self.orchestrator.claude_client if hasattr(self, "orchestrator") else None

       except Exception as e:
           self.logger.error(f"Error creating LLM client for {provider}: {e}")
           return self.orchestrator.claude_client if hasattr(self, "orchestrator") else None
   ```

3. **Update Agent.process() method**
   
   Modify to check for provider_config:
   ```python
   def process(self, request_data=None):
       """Process request with optional provider-specific LLM client.
       
       If request_data contains 'provider_config', uses that provider's client.
       Otherwise, falls back to orchestrator.claude_client.
       """
       if request_data is None:
           request_data = {}

       provider_config = request_data.get("provider_config")

       if provider_config:
           self.logger.debug(
               f"Agent using provider from request: "
               f"{provider_config.get('provider', 'unknown')}"
           )

           # Store original client
           original_client = (
               self.orchestrator.claude_client if hasattr(self, "orchestrator") else None
           )

           try:
               # Get the LLM client for this provider
               client = self._get_llm_client_for_provider(provider_config)

               if client and hasattr(self, "orchestrator"):
                   # Temporarily override orchestrator's client
                   self.orchestrator.claude_client = client
                   self.logger.debug(
                       f"Switched LLM client to {provider_config.get('provider')}"
                   )

               # Process with the appropriate client
               result = self._original_process(request_data)

               return result

           finally:
               # Restore original client
               if original_client and hasattr(self, "orchestrator"):
                   self.orchestrator.claude_client = original_client
       else:
           # No provider config, use default
           return self._original_process(request_data)

       def _original_process(self, request_data):
           """Original process implementation (rename existing method)"""
           # [existing implementation]
   ```

4. **Test locally**
   ```bash
   pytest tests/test_agent_provider_awareness.py -v
   ```

5. **Commit and push**
   ```bash
   git add socratic_agents/base_agent.py
   git commit -m "feat: add provider-aware LLM client selection to agents

   - Add _get_llm_client_for_provider() factory method
   - Update process() to check request for provider_config
   - Agents now respect user's default LLM provider setting
   - Enables per-request provider override
   - Removes need for patch_agents_for_provider_awareness() in Socrates"
   git push origin main
   ```

### Task 2.4: Publish socratic-agents to PyPI

1. **Wait for all GitHub Actions tests to pass** ✅

2. **Trigger release**
   ```bash
   gh workflow run release.yml -f version-type=minor
   ```

3. **Wait for PyPI publish** (10 minutes)

4. **Verify**
   ```bash
   pip install --upgrade socratic-agents
   python3 -c "import socratic_agents; print(socratic_agents.__version__)"
   ```

---

## PHASE 3: Update Socrates

### Task 3.1: Update Dependencies in pyproject.toml

**File:** `pyproject.toml`

1. **Check current versions**
   ```bash
   grep "socratic-agents\|socratic-nexus" pyproject.toml
   ```

2. **Update to new versions**
   ```toml
   [project]
   dependencies = [
       # ... other deps ...
       "socratic-agents>=2.0.0",  # Update to new version
       "socratic-nexus>=2.0.0",   # Update to new version
       # ... other deps ...
   ]
   ```

3. **Install updated versions**
   ```bash
   pip install --upgrade socratic-agents socratic-nexus
   ```

4. **Verify no conflicts**
   ```bash
   pip check
   # Should show: 0 broken requirements
   ```

### Task 3.2: Remove Patch Application from Orchestrator

**File:** `socratic_system/orchestration/orchestrator.py`

1. **Find patch application code**
   ```bash
   grep -n "apply_all_patches\|from.*patches import" socratic_system/orchestration/orchestrator.py
   ```

2. **Remove the lines**
   ```python
   # DELETE these lines:
   # from socratic_system.patches import apply_all_patches
   # apply_all_patches()
   ```

3. **Verify no other references**
   ```bash
   grep -r "apply_all_patches\|from.*patches import" socratic_system/ tests/
   # Should return 0 results (or only in patches.py which we're deleting)
   ```

### Task 3.3: Delete patches.py (No Longer Needed)

1. **Verify no imports reference it**
   ```bash
   grep -r "from socratic_system.patches import\|import socratic_system.patches" .
   ```

2. **Delete the file**
   ```bash
   rm socratic_system/patches.py
   ```

3. **Verify deletion**
   ```bash
   ls -la socratic_system/patches.py
   # Should show: No such file or directory
   ```

### Task 3.4: Update Socrates Documentation

1. **Update PATCHES_MAINTENANCE_PLAN.md**
   ```markdown
   # Status: COMPLETED ✅
   
   All patches have been successfully moved to their respective libraries and published to PyPI.
   This document is now archived for historical reference.
   ```

2. **Update README.md** (if it mentions patches)
   ```bash
   # Remove any references to runtime patches
   # Ensure it documents the provider-aware architecture
   ```

### Task 3.5: Run Full Test Suite

1. **Run all tests**
   ```bash
   pytest tests/ -v
   # Should pass 100%
   ```

2. **Test critical flows manually**
   ```bash
   # Start Socrates
   docker-compose -f deployment/docker/docker-compose.yml up -d
   
   # Test 1: Add API key via UI
   # Should encrypt and store without errors
   
   # Test 2: List providers
   # Should show all available providers
   
   # Test 3: Set Ollama as default
   # Should work without patches
   
   # Test 4: Make agent request
   # Should use Ollama if configured
   ```

3. **Check logs for errors**
   ```bash
   docker logs socrates_api_1 | grep -i error
   # Should show: No patch-related errors
   ```

### Task 3.6: Commit and Push Socrates Changes

1. **Stage changes**
   ```bash
   git add pyproject.toml
   git add socratic_system/orchestration/orchestrator.py
   git rm socratic_system/patches.py
   git add PATCHES_MAINTENANCE_PLAN.md
   ```

2. **Create commit**
   ```bash
   git commit -m "refactor: remove runtime patches after library updates

   - Updated socratic-agents to >=2.0.0 (provider-aware, fixed attributes)
   - Updated socratic-nexus to >=2.0.0 (unified encryption, complete clients)
   - Removed apply_all_patches() call from orchestrator
   - Deleted socratic_system/patches.py (no longer needed)
   
   Libraries now handle:
   - Provider-aware agent execution
   - Unified encryption in Claude client
   - Correct ProviderMetadata attribute access
   - Dict/object conversion for configs
   - Multi-provider LLM client support
   
   Socrates is now cleaner and more maintainable with logic in proper places."
   ```

3. **Push to origin**
   ```bash
   git push origin main
   ```

4. **Monitor CI/CD** ✅

---

## PHASE 4: Verification & Cleanup

### Task 4.1: Final Testing Checklist

- [ ] All pytest tests pass: `pytest tests/ -v`
- [ ] Docker build succeeds: `docker-compose build`
- [ ] Docker services start: `docker-compose up -d`
- [ ] API health check passes: `curl http://localhost:8000/health`
- [ ] Frontend loads: `http://localhost:3000`
- [ ] Add Anthropic API key via UI → ✅ Works
- [ ] Add Ollama API endpoint via UI → ✅ Works
- [ ] List available providers → ✅ All show with metadata
- [ ] Set Ollama as default → ✅ Works
- [ ] Make request to agent → ✅ Uses Ollama (no errors)
- [ ] Check logs for no patch-related errors → ✅ Clean

### Task 4.2: Update Documentation

1. **Add to README.md**
   ```markdown
   ### Provider-Aware Agent Execution
   
   Socrates now supports multiple LLM providers out of the box:
   - Anthropic Claude (default)
   - OpenAI GPT models
   - Google Gemini
   - Ollama (local models)
   
   Users can set their default provider in Settings → LLM Providers.
   Agents automatically use the configured provider.
   ```

2. **Add to CLAUDE.md** (if relevant)
   ```markdown
   ## Architecture Notes
   
   As of [date], all runtime patches have been removed and integrated into
   socratic-agents and socratic-nexus libraries. Socrates now uses clean
   imports without monkey-patching.
   ```

### Task 4.3: Archive & Close

1. **Tag release (if applicable)**
   ```bash
   git tag -a v1.2.0-clean-architecture -m "Remove runtime patches after library updates"
   git push origin v1.2.0-clean-architecture
   ```

2. **Document completion**
   ```bash
   cat > ARCHITECTURE_MIGRATION_COMPLETE.md << 'EOF'
   # Architecture Migration Complete ✅
   
   **Date:** 2026-06-28
   **Status:** Completed
   
   ## Summary
   All runtime patches have been successfully migrated to their respective libraries:
   
   1. socratic-nexus: Encryption unification ✅
   2. socratic-agents: Provider metadata, MultiLLMAgent fixes ✅
   3. socratic-agents: Provider-aware agent execution ✅
   
   Socrates now uses published library versions without patches.
   
   ## Versions Used
   - socratic-nexus: 2.0.0+
   - socratic-agents: 2.0.0+
   
   ## Impact
   - Cleaner architecture (logic in appropriate places)
   - Easier to maintain (changes in libraries, not Socrates)
   - Better for contributors (clear module responsibilities)
   - Improved testability (each library tested independently)
   EOF
   ```

3. **Final push**
   ```bash
   git add ARCHITECTURE_MIGRATION_COMPLETE.md
   git commit -m "docs: document architecture migration completion"
   git push origin main
   ```

---

## Timeline & Checkpoints

| Phase | Task | Est. Time | Checkpoint |
|-------|------|-----------|-----------|
| 1 | socratic-nexus encryption | 2-3 hrs | ✅ Tests pass, PyPI updated |
| 1 | socratic-nexus clients | 2-3 hrs | ✅ All clients implemented |
| 2 | socratic-agents providers | 3-4 hrs | ✅ Tests pass, PyPI updated |
| 2 | socratic-agents agent awareness | 3-4 hrs | ✅ Tests pass, PyPI updated |
| 3 | Socrates cleanup | 1-2 hrs | ✅ All tests pass, no patches |
| 4 | Verification & docs | 1-2 hrs | ✅ Full test suite passes |
| **Total** | | **12-18 hrs** | **Ready for production** |

---

## Rollback Plan (If Needed)

If issues occur at any phase:

1. **Phase 1-2 Issues (Library Updates):**
   ```bash
   # Revert library version bumps in pyproject.toml
   git checkout pyproject.toml
   pip install -r requirements.txt  # Restore old versions
   ```

2. **Phase 3 Issues (Socrates Cleanup):**
   ```bash
   # Restore patches.py and orchestrator changes
   git checkout socratic_system/patches.py
   git checkout socratic_system/orchestration/orchestrator.py
   ```

3. **Contact owners of libraries if:**
   - Tests fail in library CI/CD
   - Library changes break backward compatibility
   - PyPI publish fails

---

## Success Criteria

✅ All GitHub Actions workflows pass in all three repos  
✅ All pytest tests pass locally and in CI/CD  
✅ No patch-related errors in logs  
✅ Provider switching works via UI  
✅ Agents use user's default LLM provider  
✅ No functionality regressions  
✅ Documentation updated  
✅ Code review completed  

---

## Notes

- Each phase depends on previous phases succeeding
- GitHub Actions tests are non-negotiable (must pass before PyPI)
- Always wait for PyPI propagation (5-10 minutes) before moving forward
- Run full test suite before committing Phase 3 changes
- Consider running release in off-hours to avoid conflicts

