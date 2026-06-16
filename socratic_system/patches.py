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


def patch_multi_llm_agent_provider_config():
    """
    Patch MultiLLMAgent to handle provider configs returned as dicts (not objects).

    The database now returns flattened dicts from get_user_llm_config(), but the
    agent code expects LLMProviderConfig objects. This patch wraps returned configs
    back into LLMProviderConfig objects for compatibility.
    """
    try:
        from socratic_agents.multi_llm_agent import MultiLLMAgent
        from socratic_agents.models import LLMProviderConfig
        from datetime import datetime, timezone
        import uuid

        def dict_to_config(config_dict):
            """Convert dict from DB to LLMProviderConfig if needed"""
            if not config_dict:
                return None
            if isinstance(config_dict, dict) and not isinstance(config_dict, LLMProviderConfig):
                return LLMProviderConfig.from_dict(config_dict)
            return config_dict

        def patched_set_default_provider(self, data):
            """Patched version that converts dict configs to LLMProviderConfig objects"""
            user_id = data.get("user_id")
            provider = data.get("provider", "").lower()
            settings = data.get("settings", {})

            if not user_id or not provider:
                return {"status": "error", "message": "user_id and provider required"}

            self.logger.debug(f"Setting default provider for {user_id}: {provider}")

            try:
                from socratic_agents.models import get_provider_metadata

                metadata = get_provider_metadata(provider)
                if not metadata:
                    self.logger.warning(f"Unknown provider requested: {provider}")
                    return {"status": "error", "message": f"Unknown provider: {provider}"}

                self.logger.debug(f"Provider {provider} verified, models: {metadata.models}")

                # Get existing config (returns dict, convert to object)
                existing_dict = self.orchestrator.database.get_user_llm_config(user_id, provider)
                existing = dict_to_config(existing_dict)

                if existing:
                    existing.is_default = True
                    existing.enabled = True
                    existing.settings = settings or existing.settings
                    existing.updated_at = datetime.now(timezone.utc)
                    config = existing
                else:
                    config = LLMProviderConfig(
                        id=str(uuid.uuid4()),
                        provider=provider,
                        user_id=user_id,
                        is_default=True,
                        enabled=True,
                        settings=settings,
                    )

                # Save to database
                self.logger.debug(f"Saving config: {config.id}")
                self.orchestrator.database.save_user_llm_config(
                    user_id, provider, config.to_dict()
                )

                self.logger.info(f"Set default provider {provider} for user {user_id}")
                return {
                    "status": "success",
                    "provider": provider,
                    "config_id": config.id,
                }

            except Exception as e:
                self.logger.error(f"Error setting default provider: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}

        def patched_set_provider_model(self, data):
            """Patched version for setting provider model"""
            user_id = data.get("user_id")
            provider = data.get("provider", "").lower()
            model = data.get("model", "").strip()

            if not user_id or not provider or not model:
                return {"status": "error", "message": "user_id, provider, and model required"}

            self.logger.debug(f"Setting model for {user_id}/{provider}: {model}")

            try:
                from socratic_agents.models import get_provider_metadata

                metadata = get_provider_metadata(provider)
                if not metadata:
                    return {"status": "error", "message": f"Unknown provider: {provider}"}

                if model not in metadata.models:
                    return {"status": "error", "message": f"Unknown model {model} for {provider}"}

                # Get existing config (returns dict, convert to object)
                existing_dict = self.orchestrator.database.get_user_llm_config(user_id, provider)
                existing = dict_to_config(existing_dict)

                if existing:
                    existing.settings = existing.settings or {}
                    existing.settings["model"] = model
                    existing.updated_at = datetime.now(timezone.utc)
                    config = existing
                else:
                    config = LLMProviderConfig(
                        id=str(uuid.uuid4()),
                        provider=provider,
                        user_id=user_id,
                        is_default=False,
                        enabled=True,
                        settings={"model": model},
                    )

                # Save to database
                self.orchestrator.database.save_user_llm_config(
                    user_id, provider, config.to_dict()
                )

                self.logger.info(f"Set model {model} for {provider}")
                return {
                    "status": "success",
                    "provider": provider,
                    "model": model,
                    "config_id": config.id,
                }

            except Exception as e:
                self.logger.error(f"Error setting provider model: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}

        def patched_get_provider_config(self, data):
            """Patched version for getting provider config"""
            user_id = data.get("user_id")

            if not user_id:
                return {"status": "error", "message": "user_id required"}

            self.logger.debug(f"Getting provider config for {user_id}")

            try:
                # Get all configs (returns list of dicts, convert to objects)
                configs_list = self.orchestrator.database.get_user_llm_configs(user_id)
                configs = [dict_to_config(c) for c in configs_list]

                default_provider = None
                provider_list = []

                for config in configs:
                    if config:
                        provider_dict = {
                            "id": config.id,
                            "provider": config.provider,
                            "is_default": config.is_default,
                            "enabled": config.enabled,
                            "settings": config.settings or {},
                        }
                        provider_list.append(provider_dict)

                        if config.is_default:
                            default_provider = config.provider

                self.logger.info(f"Retrieved provider config for {user_id}")
                return {
                    "status": "success",
                    "default_provider": default_provider,
                    "providers": provider_list,
                    "count": len(provider_list),
                }

            except Exception as e:
                self.logger.error(f"Error getting provider config: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}

        MultiLLMAgent._set_default_provider = patched_set_default_provider
        MultiLLMAgent._set_provider_model = patched_set_provider_model
        MultiLLMAgent._get_provider_config = patched_get_provider_config
        logger.info("Patched MultiLLMAgent provider config methods to handle dict configs")

    except Exception as e:
        logger.error(f"Failed to patch MultiLLMAgent provider config handling: {e}")


def apply_all_patches():
    """Apply all runtime patches"""
    patch_list_available_providers()
    patch_multi_llm_agent()
    patch_multi_llm_agent_provider_config()
