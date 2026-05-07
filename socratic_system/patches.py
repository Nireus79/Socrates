"""
Runtime patches for library compatibility.

Patches for socratic-agents PyPI distribution which still contains old code.
These patches are temporary until the correct version is available on PyPI.

Patches applied:
- list_available_providers() returns ProviderMetadata objects (instead of strings)
- MultiLLMAgent._list_providers() uses correct attribute names
"""

import logging

logger = logging.getLogger(__name__)


def patch_list_available_providers():
    """
    Patch socratic_agents.models.list_available_providers to return ProviderMetadata objects.

    PyPI version still returns strings; this patch fixes the return type.
    """
    try:
        from socratic_agents import models
        from socratic_agents.models import get_provider_metadata

        def patched_list_available_providers():
            """Return ProviderMetadata objects instead of strings"""
            provider_names = ["claude", "openai", "gemini", "ollama"]
            return [get_provider_metadata(name) for name in provider_names]

        models.list_available_providers = patched_list_available_providers
        logger.info("Patched list_available_providers to return ProviderMetadata objects")

    except Exception as e:
        logger.error(f"Failed to patch list_available_providers: {e}")


def patch_multi_llm_agent():
    """
    Patch MultiLLMAgent._list_providers to use correct ProviderMetadata attributes.
    """
    try:
        from socratic_agents.multi_llm_agent import MultiLLMAgent

        def patched_list_providers(self, data):
            """Fixed version using correct ProviderMetadata attributes"""
            self.logger.debug("Listing available LLM providers")
            user_id = data.get("user_id")

            try:
                from socratic_agents.models import list_available_providers

                providers = list_available_providers()
                provider_dicts = []

                for provider in providers:
                    # Transform backend provider metadata to frontend format
                    provider_dict = {
                        "name": provider.provider,  # ProviderMetadata has .provider, not .name
                        "label": provider.display_name,
                        "models": provider.models,
                        "requires_api_key": provider.requires_api_key,
                        "description": getattr(provider, "description", ""),
                        "cost_per_1k_input_tokens": provider.cost_per_1k_input_tokens,
                        "cost_per_1k_output_tokens": provider.cost_per_1k_output_tokens,
                        "context_window": provider.context_window,  # ProviderMetadata has .context_window
                        "supports_streaming": provider.supports_streaming,
                        "supports_vision": provider.supports_vision,
                        "available": provider.available,  # Use from provider, not hardcoded
                        "auth_methods": provider.auth_methods,  # Use from provider
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

        MultiLLMAgent._list_providers = patched_list_providers
        logger.info("Patched MultiLLMAgent._list_providers to use correct attribute names")

    except Exception as e:
        logger.error(f"Failed to patch MultiLLMAgent: {e}")


def apply_all_patches():
    """Apply all runtime patches"""
    patch_list_available_providers()
    patch_multi_llm_agent()
