"""
Runtime patches to unify encryption across the codebase.

Patches the installed socratic_nexus.clients.claude_client to use
the standard Socrates encryption system.
"""

import logging

logger = logging.getLogger(__name__)


def patch_claude_client_decryption():
    """
    Patch claude_client._decrypt_api_key_from_db to use unified encryption.

    This ensures the installed package uses the same encryption/decryption
    as the local Socrates system.
    """
    try:
        from socratic_nexus.clients.claude_client import ClaudeClient
        from socratic_system.encryption import decrypt_data

        # Save original method for reference
        original_decrypt = ClaudeClient._decrypt_api_key_from_db

        def patched_decrypt(self, encrypted_key: str):
            """Use unified encryption system for decryption"""
            try:
                return decrypt_data(encrypted_key)
            except Exception as e:
                logger.warning(
                    f"Failed to decrypt API key with unified encryption: {e}. "
                    f"Attempting legacy decryption methods..."
                )
                # Fall back to original implementation for backward compatibility
                # (though we've deleted all old databases, this is for safety)
                try:
                    return original_decrypt(self, encrypted_key)
                except Exception as legacy_e:
                    logger.error(
                        f"Both unified and legacy decryption failed for API key. "
                        f"Unified error: {e}, Legacy error: {legacy_e}"
                    )
                    return None

        # Replace the method
        ClaudeClient._decrypt_api_key_from_db = patched_decrypt
        logger.info("Patched ClaudeClient to use unified encryption system")

    except Exception as e:
        logger.error(f"Failed to patch claude_client: {e}")
        raise


def patch_list_available_providers():
    """
    Patch socratic_agents.models.list_available_providers to return ProviderMetadata objects.

    The MultiLLMAgent expects list_available_providers to return metadata objects,
    but the installed package returns strings. This patch fixes the incompatibility.
    """
    try:
        from socratic_agents import models
        from socratic_agents.models import get_provider_metadata

        original_func = models.list_available_providers

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

    The code tries to access .provider and .context_window but ProviderMetadata has
    .name and .max_context_tokens. This patch wraps the method to fix attribute access.
    """
    try:
        from socratic_agents.multi_llm_agent import MultiLLMAgent

        original_list_providers = MultiLLMAgent._list_providers

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
                    # Using correct attribute names from ProviderMetadata
                    provider_dict = {
                        "name": provider.name,  # Fixed: ProviderMetadata has .name
                        "label": provider.display_name,
                        "models": provider.models,
                        "requires_api_key": provider.requires_api_key,
                        "description": getattr(provider, "description", ""),
                        "cost_per_1k_input_tokens": provider.cost_per_1k_input_tokens,
                        "cost_per_1k_output_tokens": provider.cost_per_1k_output_tokens,
                        "context_window": provider.max_context_tokens,  # Fixed: .max_context_tokens
                        "supports_streaming": provider.supports_streaming,
                        "supports_vision": provider.supports_vision,
                        "available": True,
                        "auth_methods": getattr(provider, "auth_methods", ["api_key"]),
                    }

                    # Check if user has configured this provider (has API key)
                    if user_id:
                        try:
                            api_key = self.orchestrator.database.get_api_key(user_id, provider.name)
                            provider_dict["is_configured"] = api_key is not None
                        except Exception as e:
                            self.logger.debug(f"Error checking API key for {provider.name}: {e}")
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
    patch_claude_client_decryption()
    patch_list_available_providers()
    patch_multi_llm_agent()
