"""
LLM Provider Package
====================

Multi-LLM provider support with unified interface.

Supported Providers:
- Claude (Anthropic) - Wraps existing ClaudeService
- OpenAI (GPT-4, GPT-3.5-turbo)
- Google Gemini
- Ollama (local models)

Easy to extend with new providers:
- Create provider class inheriting from BaseLLMProvider
- Implement all abstract methods
- Register in LLMProviderFactory
- Add to config.yaml

Usage:
    from src.services.llm import get_llm_provider, detect_available_providers

    # Get provider for user's preferred LLM
    provider = get_llm_provider('openai')

    # Or detect and use best available LLM
    providers = detect_available_providers()
    provider = get_llm_provider(providers[0])

    # Auto-detect (simplest usage)
    provider = get_llm_provider()  # Returns best available LLM

    # Use provider
    response = provider.chat('Hello, how are you?')
    print(response.content)

    # Generate code
    response = provider.generate_code(
        requirements='Create a REST API for user management',
        programming_language='python',
        framework='Flask'
    )
"""

from .base_provider import (
    BaseLLMProvider,
    LLMResponse,
    LLMUsage,
    LLMProviderError
)

from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider

from .factory import (
    LLMProviderFactory,
    get_llm_provider,
    detect_available_providers,
    get_supported_providers,
    health_check_all_providers
)

__all__ = [
    # Base classes and data structures
    'BaseLLMProvider',
    'LLMResponse',
    'LLMUsage',
    'LLMProviderError',

    # Providers
    'ClaudeProvider',
    'OpenAIProvider',
    'GeminiProvider',
    'OllamaProvider',

    # Factory
    'LLMProviderFactory',

    # Convenience functions
    'get_llm_provider',
    'detect_available_providers',
    'get_supported_providers',
    'health_check_all_providers',
]
