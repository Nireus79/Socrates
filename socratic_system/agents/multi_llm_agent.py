"""
Multi-LLM Provider Agent - Unified LLM management and routing.

Manages connections to multiple LLM providers (Claude, OpenAI, Gemini, Ollama)
with a unified interface for:
- Provider configuration
- API key management
- Usage tracking
- Cost analysis
- Provider routing
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from socratic_system.agents.base import Agent
from socratic_system.models import (
    APIKeyRecord,
    LLMProviderConfig,
    LLMUsageRecord,
    get_provider_metadata,
    list_available_providers,
)


class MultiLLMAgent(Agent):
    """
    Manages multiple LLM providers with unified interface.

    Capabilities:
    - list_providers: List available LLM providers and their metadata
    - get_provider_config: Get user's provider configuration
    - set_default_provider: Set default provider for user
    - set_provider_model: Set the model to use for a specific provider
    - add_api_key: Store API key securely for a provider
    - remove_api_key: Remove API key for a provider
    - get_usage_stats: Get usage and cost statistics
    - track_usage: Record LLM usage for billing/monitoring
    - get_provider_models: Get available models for a provider
    """

    def __init__(self, orchestrator):
        """Initialize multi-LLM agent"""
        super().__init__("Multi-LLM Manager", orchestrator)
        self.logger.info("MultiLLMAgent initialized")

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process multi-LLM requests"""
        action = request.get("action")

        action_handlers = {
            "list_providers": self._list_providers,
            "get_provider_config": self._get_provider_config,
            "set_default_provider": self._set_default_provider,
            "set_provider_model": self._set_provider_model,
            "add_api_key": self._add_api_key,
            "remove_api_key": self._remove_api_key,
            "get_usage_stats": self._get_usage_stats,
            "track_usage": self._track_usage,
            "get_provider_models": self._get_provider_models,
        }

        handler = action_handlers.get(action)
        if handler:
            try:
                return handler(request)
            except Exception as e:
                self.logger.error(f"Error in {action}: {str(e)}", exc_info=True)
                return {"status": "error", "message": f"Failed to {action}: {str(e)}"}

        return {"status": "error", "message": f"Unknown action: {action}"}

    # ============================================================================
    # Provider Information
    # ============================================================================

    def _list_providers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List all available LLM providers.

        Returns:
            {
                'status': 'success',
                'providers': [
                    {
                        'provider': 'claude',
                        'display_name': 'Anthropic Claude',
                        'models': [...],
                        'requires_api_key': False,
                        'cost_per_1k_input_tokens': 0.003,
                        'available': True,
                        ...
                    },
                    ...
                ]
            }
        """
        self.logger.debug("Listing available LLM providers")

        try:
            providers = list_available_providers()
            provider_dicts = [p.to_dict() for p in providers]

            self.logger.info(f"Listed {len(providers)} LLM providers")

            return {"status": "success", "providers": provider_dicts, "count": len(providers)}

        except Exception as e:
            self.logger.error(f"Error listing providers: {e}")
            return {"status": "error", "message": str(e)}

    def _get_provider_models(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get available models for a specific provider.

        Args:
            data: {'provider': str}

        Returns:
            {
                'status': 'success',
                'provider': str,
                'models': [str, ...],
                'default_model': str
            }
        """
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
                "context_window": metadata.context_window,
                "supports_streaming": metadata.supports_streaming,
                "supports_vision": metadata.supports_vision,
            }

        except Exception as e:
            self.logger.error(f"Error getting provider models: {e}")
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # Provider Configuration
    # ============================================================================

    def _get_provider_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get user's provider configuration.

        Args:
            data: {'user_id': str}

        Returns:
            {
                'status': 'success',
                'default_provider': str,
                'providers': [
                    {
                        'id': str,
                        'provider': str,
                        'is_default': bool,
                        'enabled': bool,
                        'settings': {...},
                        ...
                    }
                ]
            }
        """
        user_id = data.get("user_id")

        if not user_id:
            return {"status": "error", "message": "user_id required"}

        self.logger.debug(f"Getting provider config for user: {user_id}")

        try:
            configs = self.orchestrator.database.get_user_llm_configs(user_id)

            if not configs:
                # Return defaults (Claude and Haiku)
                default_config = {
                    "provider": "claude",
                    "model": "claude-3-haiku-20240307",  # Default to Haiku
                    "enabled": True,
                    "is_default": True,
                }
                return {
                    "status": "success",
                    "default_provider": "claude",
                    "providers": [default_config],
                    "note": "Using default Claude configuration",
                }

            provider_dicts = [c.to_dict() for c in configs]
            default_provider = next(
                (c.provider for c in configs if c.is_default),
                configs[0].provider if configs else "claude",
            )

            return {
                "status": "success",
                "default_provider": default_provider,
                "providers": provider_dicts,
            }

        except Exception as e:
            self.logger.error(f"Error getting provider config: {e}")
            return {"status": "error", "message": str(e)}

    def _set_default_provider(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set default provider for a user.

        Args:
            data: {
                'user_id': str,
                'provider': str,
                'settings': dict (optional)
            }

        Returns:
            {'status': 'success', 'provider': str, 'config_id': str}
        """
        user_id = data.get("user_id")
        provider = data.get("provider", "").lower()
        settings = data.get("settings", {})

        if not user_id or not provider:
            return {"status": "error", "message": "user_id and provider required"}

        self.logger.debug(f"Setting default provider for {user_id}: {provider}")

        try:
            # Verify provider exists
            self.logger.debug(f"Verifying provider {provider} exists")
            metadata = get_provider_metadata(provider)
            if not metadata:
                self.logger.warning(f"Unknown provider requested: {provider}")
                return {"status": "error", "message": f"Unknown provider: {provider}"}

            self.logger.debug(f"Provider {provider} verified, models: {metadata.models}")

            # Get or create config
            self.logger.debug(f"Checking for existing config: user={user_id}, provider={provider}")
            existing = self.orchestrator.database.get_user_llm_config(user_id, provider)

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
                    settings=settings
                    or {
                        "model": metadata.models[0] if metadata.models else provider,
                        "max_tokens": 4096,
                        "temperature": 0.7,
                    },
                )

            # Unset other defaults
            self.orchestrator.database.unset_other_default_providers(user_id, provider)

            # Save config
            self.orchestrator.database.save_llm_config(config)

            self.logger.info(f"Set default provider to {provider} for user {user_id}")

            return {"status": "success", "provider": provider, "config_id": config.id}

        except Exception as e:
            self.logger.error(f"Error setting default provider: {e}")
            return {"status": "error", "message": str(e)}

    def _set_provider_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set the model for a specific provider.

        Args:
            data: {
                'user_id': str,
                'provider': str,
                'model': str
            }

        Returns:
            {'status': 'success', 'provider': str, 'model': str, 'config_id': str}
        """
        user_id = data.get("user_id")
        provider = data.get("provider", "").lower()
        model = data.get("model", "").strip()

        if not user_id or not provider or not model:
            return {"status": "error", "message": "user_id, provider, and model required"}

        self.logger.debug(f"Setting model for {user_id} on provider {provider}: {model}")

        try:
            # Verify provider exists
            self.logger.debug(f"Verifying provider {provider} exists")
            metadata = get_provider_metadata(provider)
            if not metadata:
                self.logger.warning(f"Unknown provider requested: {provider}")
                return {"status": "error", "message": f"Unknown provider: {provider}"}

            # Verify model is available for this provider
            self.logger.debug(f"Verifying model {model} is available for {provider}")
            if model not in metadata.models:
                available = ", ".join(metadata.models)
                self.logger.warning(
                    f"Model {model} not available for {provider}. Available: {available}"
                )
                return {
                    "status": "error",
                    "message": f"Model '{model}' not available for {provider}. Available models: {available}",
                }

            # Get or create config
            self.logger.debug(f"Checking for existing config: user={user_id}, provider={provider}")
            existing = self.orchestrator.database.get_user_llm_config(user_id, provider)

            if existing:
                existing.settings["model"] = model
                existing.updated_at = datetime.now(timezone.utc)
                config = existing
                self.logger.debug(f"Updated existing config for {provider}")
            else:
                config = LLMProviderConfig(
                    id=str(uuid.uuid4()),
                    provider=provider,
                    user_id=user_id,
                    is_default=False,
                    enabled=True,
                    settings={
                        "model": model,
                        "max_tokens": 4096,
                        "temperature": 0.7,
                    },
                )
                self.logger.debug(f"Created new config for {provider}")

            # Save config
            self.orchestrator.database.save_llm_config(config)

            self.logger.info(f"Set model {model} for provider {provider} for user {user_id}")

            return {
                "status": "success",
                "provider": provider,
                "model": model,
                "config_id": config.id,
            }

        except Exception as e:
            self.logger.error(f"Error setting provider model: {e}")
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # API Key Management
    # ============================================================================

    def _add_api_key(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add/update API key for a provider.

        Args:
            data: {
                'user_id': str,
                'provider': str,
                'api_key': str
            }

        Returns:
            {'status': 'success', 'key_id': str}
        """
        user_id = data.get("user_id")
        provider = data.get("provider", "").lower()
        api_key = data.get("api_key")

        if not all([user_id, provider, api_key]):
            return {"status": "error", "message": "user_id, provider, and api_key required"}

        self.logger.debug(f"Adding API key for {user_id}/{provider}")

        try:
            # Verify provider exists
            metadata = get_provider_metadata(provider)
            if not metadata:
                return {"status": "error", "message": f"Unknown provider: {provider}"}

            if not metadata.requires_api_key:
                return {
                    "status": "error",
                    "message": f"Provider {provider} does not require API key",
                }

            # Encrypt and store
            encrypted_key = self._encrypt_api_key(api_key)
            key_hash = self._hash_api_key(api_key)

            existing = self.orchestrator.database.get_api_key(user_id, provider)

            if existing:
                existing.encrypted_key = encrypted_key
                existing.key_hash = key_hash
                existing.updated_at = datetime.now(timezone.utc)
                record = existing
            else:
                record = APIKeyRecord(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    provider=provider,
                    encrypted_key=encrypted_key,
                    key_hash=key_hash,
                )

            self.orchestrator.database.save_api_key(record)

            self.logger.info(f"Stored API key for {user_id}/{provider}")

            return {"status": "success", "key_id": record.id, "provider": provider}

        except Exception as e:
            self.logger.error(f"Error adding API key: {e}")
            return {"status": "error", "message": str(e)}

    def _remove_api_key(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove API key for a provider.

        Args:
            data: {'user_id': str, 'provider': str}

        Returns:
            {'status': 'success'}
        """
        user_id = data.get("user_id")
        provider = data.get("provider", "").lower()

        if not user_id or not provider:
            return {"status": "error", "message": "user_id and provider required"}

        self.logger.debug(f"Removing API key for {user_id}/{provider}")

        try:
            success = self.orchestrator.database.delete_api_key(user_id, provider)

            if success:
                self.logger.info(f"Removed API key for {user_id}/{provider}")
                return {"status": "success"}
            else:
                return {"status": "error", "message": "API key not found"}

        except Exception as e:
            self.logger.error(f"Error removing API key: {e}")
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # Usage Tracking
    # ============================================================================

    def _track_usage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track LLM usage for monitoring and billing.

        Args:
            data: {
                'user_id': str,
                'provider': str,
                'model': str,
                'input_tokens': int,
                'output_tokens': int,
                'latency_ms': float,
                'success': bool (optional),
                'error_message': str (optional),
                'request_id': str (optional)
            }

        Returns:
            {'status': 'success', 'usage_id': str, 'cost': float}
        """
        user_id = data.get("user_id")
        provider = data.get("provider", "").lower()
        model = data.get("model")
        input_tokens = int(data.get("input_tokens", 0))
        output_tokens = int(data.get("output_tokens", 0))
        latency_ms = float(data.get("latency_ms", 0.0))

        if not all([user_id, provider, model]):
            return {"status": "error", "message": "user_id, provider, and model required"}

        self.logger.debug(
            f"Tracking usage: {user_id}/{provider}/{model}, "
            f"tokens={input_tokens + output_tokens}"
        )

        try:
            metadata = get_provider_metadata(provider)
            if not metadata:
                return {"status": "error", "message": f"Unknown provider: {provider}"}

            # Calculate cost
            input_cost = (input_tokens / 1000.0) * metadata.cost_per_1k_input_tokens
            output_cost = (output_tokens / 1000.0) * metadata.cost_per_1k_output_tokens
            total_cost = input_cost + output_cost

            self.logger.debug(
                f"Cost calculation: input=${input_cost:.6f}, output=${output_cost:.6f}, "
                f"total=${total_cost:.6f}, input_tokens={input_tokens}, output_tokens={output_tokens}"
            )

            # Create usage record
            usage = LLMUsageRecord(
                id=str(uuid.uuid4()),
                user_id=user_id,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                latency_ms=latency_ms,
                cost=total_cost,
                success=data.get("success", True),
                error_message=data.get("error_message"),
                request_id=data.get("request_id"),
            )

            self.logger.debug(
                f"Usage record created: id={usage.id}, tokens={usage.total_tokens}, "
                f"latency={latency_ms}ms, success={usage.success}"
            )

            # Save usage
            success = self.orchestrator.database.save_usage_record(usage)
            if success:
                self.logger.info(
                    f"Successfully tracked LLM usage: user={user_id}, provider={provider}, "
                    f"model={model}, tokens={usage.total_tokens}, cost=${total_cost:.4f}, "
                    f"latency={latency_ms:.0f}ms"
                )
            else:
                self.logger.error(
                    f"Failed to save usage record: user={user_id}, provider={provider}"
                )

            return {
                "status": "success",
                "usage_id": usage.id,
                "cost": total_cost,
                "tokens": usage.total_tokens,
            }

        except Exception as e:
            self.logger.error(f"Error tracking usage: {e}")
            return {"status": "error", "message": str(e)}

    def _get_usage_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get usage statistics for a user.

        Args:
            data: {
                'user_id': str,
                'provider': str (optional),
                'days': int (optional, default 30)
            }

        Returns:
            {
                'status': 'success',
                'total_tokens': int,
                'total_cost': float,
                'by_provider': {...},
                'daily_average': float
            }
        """
        user_id = data.get("user_id")
        provider = data.get("provider", "").lower() if data.get("provider") else None
        days = int(data.get("days", 30))

        if not user_id:
            return {"status": "error", "message": "user_id required"}

        self.logger.debug(f"Getting usage stats for {user_id}, last {days} days")

        try:
            usage_records = self.orchestrator.database.get_usage_records(user_id, days, provider)

            if not usage_records:
                return {
                    "status": "success",
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "by_provider": {},
                    "daily_average": 0.0,
                }

            # Aggregate stats
            total_tokens = sum(u.total_tokens for u in usage_records)
            total_cost = sum(u.cost for u in usage_records)
            success_count = sum(1 for u in usage_records if u.success)
            error_count = sum(1 for u in usage_records if not u.success)
            avg_latency = sum(u.latency_ms for u in usage_records) / len(usage_records)

            # By provider
            by_provider = {}
            for record in usage_records:
                if record.provider not in by_provider:
                    by_provider[record.provider] = {"tokens": 0, "cost": 0.0, "requests": 0}
                by_provider[record.provider]["tokens"] += record.total_tokens
                by_provider[record.provider]["cost"] += record.cost
                by_provider[record.provider]["requests"] += 1

            self.logger.info(f"Usage stats for {user_id}: {total_tokens} tokens, ${total_cost:.2f}")

            return {
                "status": "success",
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 4),
                "by_provider": by_provider,
                "daily_average": round(total_tokens / days, 2),
                "success_count": success_count,
                "error_count": error_count,
                "avg_latency_ms": round(avg_latency, 2),
                "period_days": days,
            }

        except Exception as e:
            self.logger.error(f"Error getting usage stats: {e}")
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # Encryption/Hashing Utilities
    # ============================================================================

    def _encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt API key.

        Args:
            api_key: Raw API key string

        Returns:
            Encrypted API key
        """
        try:
            import base64
            import os

            from cryptography.fernet import Fernet
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

            # Use a secret key from config or environment
            secret = os.getenv(
                "SOCRATES_ENCRYPTION_KEY", "default-insecure-key-change-in-production"
            ).encode()

            # Derive key using PBKDF2
            salt = b"socrates-salt"  # In production, use random per-record
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend(),
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(secret))

            # Encrypt
            cipher = Fernet(derived_key)
            encrypted = cipher.encrypt(api_key.encode())
            return encrypted.decode()

        except Exception as e:
            self.logger.warning(f"Encryption failed, using base64 fallback: {e}")
            # Fallback to base64 if crypto unavailable
            import base64

            return base64.b64encode(api_key.encode()).decode()

    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for verification without storing plaintext."""
        import hashlib

        return hashlib.sha256(api_key.encode()).hexdigest()
