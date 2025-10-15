"""
LLM Provider Factory
====================

Factory pattern for LLM provider selection and auto-detection.

Supports:
- Claude (Anthropic)
- OpenAI (GPT-4, GPT-3.5)
- Google Gemini
- Ollama (local models)

Features:
- Auto-detection of available providers
- Preference-based selection
- Graceful fallback
- Easy provider registration

Usage:
    # Get specific provider
    provider = get_llm_provider('openai')

    # Auto-detect best available
    provider = get_llm_provider()

    # Check what's available
    providers = detect_available_providers()
"""

from typing import Dict, List, Optional, Type, Any
import logging

from .base_provider import BaseLLMProvider, LLMProviderError
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """
    Factory for creating LLM provider instances.

    Manages provider registration, auto-detection, and selection.
    """

    # Registry of available providers
    _providers: Dict[str, Type[BaseLLMProvider]] = {
        'claude': ClaudeProvider,
        'openai': OpenAIProvider,
        'gemini': GeminiProvider,
        'ollama': OllamaProvider,
    }

    # Default preference order (can be overridden)
    _preference_order: List[str] = ['claude', 'openai', 'gemini', 'ollama']

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseLLMProvider]) -> None:
        """
        Register a new LLM provider.

        Args:
            name: Provider identifier (e.g., 'claude', 'openai')
            provider_class: Provider class implementing BaseLLMProvider
        """
        cls._providers[name] = provider_class
        logger.info(f"Registered LLM provider: {name}")

    @classmethod
    def get_provider(
        cls,
        provider_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        auto_detect: bool = True
    ) -> BaseLLMProvider:
        """
        Get an LLM provider instance.

        Args:
            provider_name: Specific provider to use (e.g., 'claude', 'openai')
            config: Configuration dict for the provider
            auto_detect: If True and provider_name not available, try alternatives

        Returns:
            BaseLLMProvider instance

        Raises:
            LLMProviderError: If no providers available
        """
        config = config or {}

        # If specific provider requested
        if provider_name:
            if provider_name not in cls._providers:
                raise LLMProviderError(
                    f"Unknown LLM provider: '{provider_name}'. "
                    f"Available: {', '.join(cls._providers.keys())}"
                )

            # Try to create the requested provider
            try:
                provider_class = cls._providers[provider_name]
                provider = provider_class(config.get(provider_name, {}))

                if provider.is_available():
                    logger.info(f"Using LLM provider: {provider_name}")
                    return provider
                else:
                    error_msg = f"Provider '{provider_name}' is not available."
                    if not auto_detect:
                        raise LLMProviderError(error_msg)
                    logger.warning(f"{error_msg} Will try alternatives.")

            except Exception as e:
                error_msg = f"Failed to initialize provider '{provider_name}': {e}"
                if not auto_detect:
                    raise LLMProviderError(error_msg)
                logger.warning(f"{error_msg} Will try alternatives.")

        # Auto-detect if no provider specified or requested provider unavailable
        if auto_detect:
            available = cls.detect_available_providers()

            if not available:
                raise LLMProviderError(
                    "No LLM providers available. "
                    "Install at least one: anthropic, openai, google-generativeai, or ollama"
                )

            # Try providers in preference order
            for provider_id in cls._preference_order:
                if provider_id in available:
                    try:
                        provider_class = cls._providers[provider_id]
                        provider = provider_class(config.get(provider_id, {}))
                        logger.info(f"Auto-detected LLM provider: {provider_id}")
                        return provider
                    except Exception as e:
                        logger.warning(f"Failed to initialize {provider_id}: {e}")
                        continue

            # If we got here, no providers worked
            raise LLMProviderError(
                f"Found {len(available)} provider(s) but none could be initialized: {', '.join(available)}"
            )

        # Should not reach here, but just in case
        raise LLMProviderError("Failed to get LLM provider")

    @classmethod
    def detect_available_providers(cls) -> List[str]:
        """
        Detect which LLM providers are available (installed and configured).

        Returns:
            List of available provider names
        """
        available = []

        for provider_id, provider_class in cls._providers.items():
            try:
                # Create temporary instance to check availability
                provider = provider_class({})
                if provider.is_available():
                    available.append(provider_id)
            except Exception as e:
                logger.debug(f"Provider {provider_id} not available: {e}")
                continue

        return available

    @classmethod
    def get_provider_info(cls, provider_name: str) -> Dict[str, Any]:
        """
        Get information about a provider without initializing it.

        Args:
            provider_name: Provider identifier

        Returns:
            Dict with provider information
        """
        if provider_name not in cls._providers:
            raise LLMProviderError(f"Unknown provider: {provider_name}")

        provider_class = cls._providers[provider_name]

        return {
            'name': provider_name,
            'class': provider_class.__name__,
            'available': provider_name in cls.detect_available_providers(),
        }

    @classmethod
    def get_all_providers_info(cls) -> List[Dict[str, Any]]:
        """
        Get information about all registered providers.

        Returns:
            List of provider info dicts
        """
        available = cls.detect_available_providers()

        return [
            {
                'name': provider_id,
                'class': provider_class.__name__,
                'available': provider_id in available,
                'provider_name': provider_class({}).get_provider_name() if provider_id in available else 'N/A'
            }
            for provider_id, provider_class in cls._providers.items()
        ]

    @classmethod
    def set_preference_order(cls, order: List[str]) -> None:
        """
        Set the preference order for auto-detection.

        Args:
            order: List of provider names in preference order
        """
        # Validate all providers exist
        unknown = [p for p in order if p not in cls._providers]
        if unknown:
            raise LLMProviderError(f"Unknown providers in preference order: {', '.join(unknown)}")

        cls._preference_order = order
        logger.info(f"LLM provider preference order set: {order}")

    @classmethod
    def get_preference_order(cls) -> List[str]:
        """Get current preference order."""
        return cls._preference_order.copy()


# Convenience functions
def get_llm_provider(
    provider_name: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    auto_detect: bool = True
) -> BaseLLMProvider:
    """
    Get an LLM provider instance.

    Convenience wrapper for LLMProviderFactory.get_provider().

    Args:
        provider_name: Specific provider to use (e.g., 'claude', 'openai')
        config: Configuration dict for the provider
        auto_detect: If True and provider_name not available, try alternatives

    Returns:
        BaseLLMProvider instance

    Examples:
        # Auto-detect best available provider
        provider = get_llm_provider()

        # Get specific provider
        provider = get_llm_provider('openai')

        # Get provider with custom config
        provider = get_llm_provider('claude', config={'claude': {'model': 'claude-3-opus'}})
    """
    return LLMProviderFactory.get_provider(provider_name, config, auto_detect)


def detect_available_providers() -> List[str]:
    """
    Detect which LLM providers are available.

    Returns:
        List of available provider names

    Examples:
        providers = detect_available_providers()
        print(f"Available: {', '.join(providers)}")
    """
    return LLMProviderFactory.detect_available_providers()


def get_supported_providers() -> List[str]:
    """
    Get list of all supported provider names (whether available or not).

    Returns:
        List of provider names

    Examples:
        supported = get_supported_providers()
        print(f"Supported: {', '.join(supported)}")
    """
    return list(LLMProviderFactory._providers.keys())


def health_check_all_providers() -> Dict[str, Dict[str, Any]]:
    """
    Run health checks on all available providers.

    Returns:
        Dict mapping provider names to health check results

    Examples:
        health = health_check_all_providers()
        for provider, status in health.items():
            print(f"{provider}: {status['status']}")
    """
    results = {}
    available = detect_available_providers()

    for provider_id in available:
        try:
            provider = get_llm_provider(provider_id, auto_detect=False)
            results[provider_id] = provider.health_check()
        except Exception as e:
            results[provider_id] = {
                'status': 'error',
                'error': str(e)
            }

    return results


__all__ = [
    'LLMProviderFactory',
    'get_llm_provider',
    'detect_available_providers',
    'get_supported_providers',
    'health_check_all_providers',
]
