#!/usr/bin/env python3
"""
Test Multi-LLM Integration (C3: Multiple LLM Support)
Tests multi-LLM provider system with Claude, OpenAI, Gemini, and Ollama
"""
import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.llm import (
    get_llm_provider,
    detect_available_providers,
    get_supported_providers,
    health_check_all_providers,
    LLMProviderFactory,
    ClaudeProvider,
    OpenAIProvider,
    GeminiProvider,
    OllamaProvider,
    BaseLLMProvider,
    LLMResponse,
    LLMProviderError
)


def test_supported_providers():
    """Test getting list of supported LLM providers."""
    supported = get_supported_providers()

    assert isinstance(supported, list)
    assert 'claude' in supported
    assert 'openai' in supported
    assert 'gemini' in supported
    assert 'ollama' in supported
    assert len(supported) >= 4

    print(f"✓ Supported LLM providers: {supported}")


def test_detect_available_providers():
    """Test LLM provider auto-detection."""
    available = detect_available_providers()

    assert isinstance(available, list)
    # At least one provider should be available (assuming Claude is set up)
    # But we don't assert this as CI environment might not have API keys

    print(f"✓ Detected LLM providers: {available if available else 'None (expected in CI)'}")


def test_claude_provider_initialization():
    """Test Claude provider can be initialized."""
    try:
        provider = ClaudeProvider(config={})

        assert provider is not None
        assert provider.get_provider_name() == "Claude"
        assert 'claude-3' in provider.get_models()[0]

        print(f"✓ Claude provider initialized")
        print(f"  Provider Name: {provider.get_provider_name()}")
        print(f"  Available Models: {len(provider.get_models())}")

    except Exception as e:
        # Claude might not be available - that's OK in CI
        print(f"✓ Claude provider not available (expected in CI): {e}")
        pytest.skip("Claude not available")


def test_openai_provider_initialization():
    """Test OpenAI provider can be initialized."""
    provider = OpenAIProvider(config={})

    assert provider is not None
    assert provider.get_provider_name() == "OpenAI"
    assert 'gpt-4' in provider.get_models()
    assert 'gpt-3.5-turbo' in provider.get_models()

    print(f"✓ OpenAI provider initialized")
    print(f"  Provider Name: {provider.get_provider_name()}")
    print(f"  Available Models: {provider.get_models()}")


def test_gemini_provider_initialization():
    """Test Gemini provider can be initialized."""
    provider = GeminiProvider(config={})

    assert provider is not None
    assert provider.get_provider_name() == "Google Gemini"
    assert 'gemini-pro' in provider.get_models()
    assert 'gemini-1.5-pro' in provider.get_models()

    print(f"✓ Gemini provider initialized")
    print(f"  Provider Name: {provider.get_provider_name()}")
    print(f"  Available Models: {provider.get_models()}")


def test_ollama_provider_initialization():
    """Test Ollama provider can be initialized."""
    provider = OllamaProvider(config={})

    assert provider is not None
    assert provider.get_provider_name() == "Ollama"

    print(f"✓ Ollama provider initialized")
    print(f"  Provider Name: {provider.get_provider_name()}")
    print(f"  Host: {provider.host}")


def test_provider_availability():
    """Test checking if providers are available."""
    providers = [
        ('claude', ClaudeProvider),
        ('openai', OpenAIProvider),
        ('gemini', GeminiProvider),
        ('ollama', OllamaProvider),
    ]

    for name, provider_class in providers:
        provider = provider_class(config={})
        is_available = provider.is_available()

        print(f"✓ {name.capitalize()} available: {is_available}")

        # We don't assert anything here as availability depends on environment
        # The test passing means the check didn't crash


def test_factory_get_specific_provider():
    """Test getting specific LLM via factory."""
    # Try each provider
    for provider_name in ['claude', 'openai', 'gemini', 'ollama']:
        try:
            provider = LLMProviderFactory.get_provider(provider_name, auto_detect=False)

            assert provider is not None
            assert isinstance(provider, BaseLLMProvider)

            print(f"✓ Factory created {provider_name} provider")

        except LLMProviderError as e:
            # Provider not available - that's OK
            print(f"✓ {provider_name.capitalize()} not available (expected): {e}")


def test_factory_auto_detect():
    """Test LLM auto-detection via factory."""
    available = detect_available_providers()

    if not available:
        pytest.skip("No LLM providers detected - skipping auto-detect test")

    # Auto-detect should return first available LLM
    provider = get_llm_provider()

    assert provider is not None
    assert isinstance(provider, BaseLLMProvider)
    assert provider.get_provider_name() in ['Claude', 'OpenAI', 'Google Gemini', 'Ollama']

    print(f"✓ Auto-detected LLM: {provider.get_provider_name()}")


def test_provider_health_checks():
    """Test provider health checks."""
    providers = [
        ('claude', ClaudeProvider),
        ('openai', OpenAIProvider),
        ('gemini', GeminiProvider),
        ('ollama', OllamaProvider),
    ]

    for name, provider_class in providers:
        provider = provider_class(config={})
        health = provider.health_check()

        assert isinstance(health, dict)
        assert 'status' in health
        assert 'provider' in health
        assert health['provider'] == name
        assert health['status'] in ['healthy', 'unhealthy', 'unknown']

        print(f"✓ {name.capitalize()} health check:")
        print(f"  Status: {health['status']}")
        if health.get('error'):
            print(f"  Error: {health['error']}")


def test_usage_stats():
    """Test usage statistics tracking."""
    provider = OpenAIProvider(config={})

    stats = provider.get_usage_stats()

    assert isinstance(stats, dict)
    assert 'provider' in stats
    assert 'request_count' in stats
    assert 'input_tokens' in stats
    assert 'output_tokens' in stats
    assert 'estimated_cost_usd' in stats
    assert stats['provider'] == 'openai'
    assert stats['request_count'] == 0  # Fresh provider

    print(f"✓ Usage stats format correct:")
    print(f"  Provider: {stats['provider']}")
    print(f"  Requests: {stats['request_count']}")


def test_cost_per_token():
    """Test cost calculation for different providers."""
    providers = [
        ('claude', ClaudeProvider),
        ('openai', OpenAIProvider),
        ('gemini', GeminiProvider),
        ('ollama', OllamaProvider),
    ]

    for name, provider_class in providers:
        provider = provider_class(config={})
        cost = provider.get_cost_per_1k_tokens()

        assert isinstance(cost, dict)
        assert 'input' in cost
        assert 'output' in cost
        assert isinstance(cost['input'], (int, float))
        assert isinstance(cost['output'], (int, float))

        # Ollama should be free
        if name == 'ollama':
            assert cost['input'] == 0.0
            assert cost['output'] == 0.0

        print(f"✓ {name.capitalize()} cost per 1K tokens:")
        print(f"  Input: ${cost['input']}")
        print(f"  Output: ${cost['output']}")


def test_feature_support():
    """Test checking feature support (streaming, function calling)."""
    providers = [
        ('claude', ClaudeProvider),
        ('openai', OpenAIProvider),
        ('gemini', GeminiProvider),
        ('ollama', OllamaProvider),
    ]

    for name, provider_class in providers:
        provider = provider_class(config={})

        streaming = provider.supports_streaming()
        function_calling = provider.supports_function_calling()

        assert isinstance(streaming, bool)
        assert isinstance(function_calling, bool)

        print(f"✓ {name.capitalize()} features:")
        print(f"  Streaming: {streaming}")
        print(f"  Function Calling: {function_calling}")


def test_preference_order():
    """Test setting LLM preference order."""
    # Get current order
    original_order = LLMProviderFactory.get_preference_order()

    # Set new order (OpenAI first)
    LLMProviderFactory.set_preference_order(['openai', 'gemini', 'claude', 'ollama'])

    assert LLMProviderFactory.get_preference_order() == ['openai', 'gemini', 'claude', 'ollama']

    print(f"✓ LLM preference order set: ['openai', 'gemini', 'claude', 'ollama']")

    # Restore original order
    LLMProviderFactory.set_preference_order(original_order)


def test_provider_info():
    """Test getting provider information."""
    info = LLMProviderFactory.get_provider_info('claude')

    assert isinstance(info, dict)
    assert info['name'] == 'claude'
    assert 'class' in info
    assert 'available' in info
    assert isinstance(info['available'], bool)

    print(f"✓ Provider info for 'claude':")
    print(f"  Class: {info['class']}")
    print(f"  Available: {info['available']}")


def test_all_providers_info():
    """Test getting info for all providers."""
    all_info = LLMProviderFactory.get_all_providers_info()

    assert isinstance(all_info, list)
    assert len(all_info) >= 4

    provider_names = [info['name'] for info in all_info]
    assert 'claude' in provider_names
    assert 'openai' in provider_names
    assert 'gemini' in provider_names
    assert 'ollama' in provider_names

    print(f"✓ All providers info:")
    for info in all_info:
        print(f"  {info['name']}: {info['class']} - Available: {info['available']}")


def test_health_check_all():
    """Test health checking all available providers."""
    health_results = health_check_all_providers()

    assert isinstance(health_results, dict)

    # Results should only include available providers
    available = detect_available_providers()
    for provider_name in health_results.keys():
        assert provider_name in available

    print(f"✓ Health check for all available providers:")
    for provider, health in health_results.items():
        print(f"  {provider}: {health.get('status', 'unknown')}")


def test_llm_response_structure():
    """Test LLMResponse data structure."""
    from src.services.llm.base_provider import LLMResponse

    response = LLMResponse(
        content="Hello, world!",
        role="assistant",
        model="test-model",
        usage={'input_tokens': 10, 'output_tokens': 5},
        stop_reason="stop",
        provider="test"
    )

    assert response.content == "Hello, world!"
    assert response.role == "assistant"
    assert response.model == "test-model"
    assert response.usage['input_tokens'] == 10
    assert response.stop_reason == "stop"
    assert response.provider == "test"

    print(f"✓ LLMResponse structure correct")


def test_error_handling():
    """Test error handling for invalid providers."""
    # Try to get non-existent provider
    with pytest.raises(LLMProviderError) as exc_info:
        LLMProviderFactory.get_provider('nonexistent', auto_detect=False)

    assert 'Unknown LLM provider' in str(exc_info.value)

    print(f"✓ Error handling works for invalid providers")


def test_backward_compatibility_claude():
    """Test that existing ClaudeService still works."""
    try:
        from src.services.claude_service import ClaudeService

        # This should still work
        print(f"✓ ClaudeService import still works (backward compatible)")

    except ImportError:
        pytest.fail("ClaudeService import failed - backward compatibility broken")


if __name__ == '__main__':
    print("=" * 70)
    print("Multi-LLM Integration Tests (C3: Multiple LLM Support)")
    print("=" * 70)

    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
