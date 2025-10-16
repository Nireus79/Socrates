"""
Dynamic Provider Selector
=========================

Selects optimal LLM provider based on task complexity and user preferences.

This service bridges the gap between task complexity analysis and provider selection,
providing intelligent provider recommendations while respecting user configuration.

Features:
- Automatic provider selection based on task complexity
- User preference override capability
- Provider capability matching (e.g., don't use Haiku for complex reasoning)
- Cost-aware selection (prefers cheaper providers for simple tasks)
- Fallback to available providers if recommended not available
- Caching of provider instances for performance

Usage:
    selector = DynamicProviderSelector()

    # Get provider based on task
    provider = selector.select_provider({
        'task_type': 'code_generation',
        'requirements': 'Complex REST API',
        'user_preference': 'claude'  # User can override
    })

    # Get analysis without instantiating provider
    analysis = selector.analyze_task({
        'task_type': 'chat_reply',
        'content': 'Hello, what is Python?'
    })
"""

import logging
from typing import Dict, Any, Optional

from .llm.base_provider import BaseLLMProvider, LLMProviderError
from .llm.factory import get_llm_provider, detect_available_providers
from .task_complexity_analyzer import (
    TaskComplexityAnalyzer, ComplexityAnalysis, ComplexityLevel
)

logger = logging.getLogger(__name__)


class ProviderCapabilities:
    """Provider capability profiles for matching to task requirements."""

    # Defines what each provider excels at
    PROFILES = {
        'ollama': {
            'name': 'Local Ollama',
            'reasoning': 'moderate',      # Good for moderate reasoning
            'speed': 'very_fast',         # Instant (local)
            'cost': 'free',               # Completely free
            'code_quality': 'good',       # Decent code generation
            'best_for': [
                ComplexityLevel.SIMPLE,
                ComplexityLevel.MODERATE
            ],
            'min_context': 0,
            'max_context': 4096,
            'streaming': True,
            'function_calling': False,
        },
        'haiku': {
            'name': 'Claude 3 Haiku',
            'reasoning': 'good',          # Good for most tasks
            'speed': 'fast',              # Very fast responses
            'cost': 'very_cheap',         # Cheapest Claude model
            'code_quality': 'good',       # Good code, not excellent
            'best_for': [
                ComplexityLevel.SIMPLE,
                ComplexityLevel.MODERATE
            ],
            'min_context': 0,
            'max_context': 200000,
            'streaming': True,
            'function_calling': True,
        },
        'gpt35': {
            'name': 'OpenAI GPT-3.5 Turbo',
            'reasoning': 'good',
            'speed': 'fast',
            'cost': 'cheap',
            'code_quality': 'good',
            'best_for': [
                ComplexityLevel.SIMPLE,
                ComplexityLevel.MODERATE
            ],
            'min_context': 0,
            'max_context': 16000,
            'streaming': True,
            'function_calling': True,
        },
        'sonnet': {
            'name': 'Claude 3.5 Sonnet',
            'reasoning': 'excellent',     # Top-tier reasoning
            'speed': 'moderate',          # Good speed/quality balance
            'cost': 'moderate',           # Balanced pricing
            'code_quality': 'excellent',  # Best code for its cost
            'best_for': [
                ComplexityLevel.SIMPLE,
                ComplexityLevel.MODERATE,
                ComplexityLevel.COMPLEX
            ],
            'min_context': 0,
            'max_context': 200000,
            'streaming': True,
            'function_calling': True,
        },
        'gpt4': {
            'name': 'OpenAI GPT-4',
            'reasoning': 'excellent',
            'speed': 'slow',              # Slower but better quality
            'cost': 'expensive',          # Higher cost
            'code_quality': 'excellent',
            'best_for': [
                ComplexityLevel.COMPLEX
            ],
            'min_context': 0,
            'max_context': 128000,
            'streaming': True,
            'function_calling': True,
        },
        'opus': {
            'name': 'Claude 3 Opus',
            'reasoning': 'superior',      # Best reasoning available
            'speed': 'slower',
            'cost': 'expensive',
            'code_quality': 'superior',   # Best overall
            'best_for': [
                ComplexityLevel.COMPLEX
            ],
            'min_context': 0,
            'max_context': 200000,
            'streaming': True,
            'function_calling': True,
        },
        'gemini': {
            'name': 'Google Gemini',
            'reasoning': 'good',
            'speed': 'moderate',
            'cost': 'cheap',
            'code_quality': 'good',
            'best_for': [
                ComplexityLevel.SIMPLE,
                ComplexityLevel.MODERATE
            ],
            'min_context': 0,
            'max_context': 1000000,  # Million tokens
            'streaming': True,
            'function_calling': True,
        },
    }

    @classmethod
    def get_profile(cls, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get capability profile for a provider."""
        return cls.PROFILES.get(provider_id)

    @classmethod
    def is_suitable_for_complexity(
        cls, provider_id: str, complexity_level: ComplexityLevel
    ) -> bool:
        """Check if provider is suitable for complexity level."""
        profile = cls.get_profile(provider_id)
        if not profile:
            return False
        return complexity_level in profile['best_for']


class DynamicProviderSelector:
    """Intelligently selects LLM provider based on task complexity."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the provider selector.

        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        self.analyzer = TaskComplexityAnalyzer()
        self.available_providers = detect_available_providers()
        self.logger = logger

        # Provider preference mapping (complexity_level -> preferred_providers)
        self.provider_preferences = {
            ComplexityLevel.SIMPLE: ['ollama', 'haiku', 'gpt35', 'gemini'],
            ComplexityLevel.MODERATE: ['sonnet', 'haiku', 'gpt4', 'ollama'],
            ComplexityLevel.COMPLEX: ['opus', 'sonnet', 'gpt4'],
        }

    def select_provider(
        self, task_data: Dict[str, Any],
        user_preference: Optional[str] = None,
        auto_detect: bool = True
    ) -> BaseLLMProvider:
        """
        Select optimal provider for a task.

        Args:
            task_data: Task information (see TaskComplexityAnalyzer.analyze)
            user_preference: User-specified provider override
            auto_detect: If preferred not available, try alternatives

        Returns:
            Instantiated BaseLLMProvider

        Raises:
            LLMProviderError: If no suitable provider available
        """
        try:
            # If user has preference, try that first
            if user_preference and user_preference in self.available_providers:
                self.logger.info(
                    f"Using user-preferred provider: {user_preference}"
                )
                try:
                    return get_llm_provider(user_preference, auto_detect=False)
                except Exception as e:
                    self.logger.warning(
                        f"User preference '{user_preference}' failed: {e}. "
                        "Will use dynamic selection."
                    )

            # Analyze task complexity
            analysis = self.analyze_task(task_data)

            # Get preferred providers for this complexity level
            preferred = self.provider_preferences.get(
                analysis.level, ['sonnet']
            )

            # Filter to available providers
            available_preferred = [
                p for p in preferred if p in self.available_providers
            ]

            if not available_preferred:
                # Fall back to any available provider
                available_preferred = self.available_providers

            # Try preferred providers in order
            for provider_id in available_preferred:
                try:
                    # Map recommendation to actual provider ID
                    mapped_id = self._map_provider_id(provider_id)
                    provider = get_llm_provider(mapped_id, auto_detect=False)

                    self.logger.info(
                        f"Selected provider '{mapped_id}' for {analysis.level.value} "
                        f"complexity (score: {analysis.score:.2f})"
                    )
                    return provider

                except Exception as e:
                    self.logger.debug(f"Provider {provider_id} failed: {e}")
                    continue

            # No providers work, raise error
            raise LLMProviderError(
                f"No suitable provider available. "
                f"Needed: {analysis.level.value}, Available: {self.available_providers}"
            )

        except Exception as e:
            self.logger.error(f"Provider selection failed: {e}")
            raise

    def analyze_task(self, task_data: Dict[str, Any]) -> ComplexityAnalysis:
        """
        Analyze task complexity without instantiating provider.

        Args:
            task_data: Task information

        Returns:
            ComplexityAnalysis
        """
        return self.analyzer.analyze(task_data)

    def _map_provider_id(self, provider_id: str) -> str:
        """
        Map provider profile ID to actual provider factory ID.

        Examples:
            'haiku' -> 'claude'
            'gpt35' -> 'openai'
            'opus' -> 'claude'
        """
        mapping = {
            'ollama': 'ollama',
            'haiku': 'claude',
            'gpt35': 'openai',
            'gpt4': 'openai',
            'sonnet': 'claude',
            'opus': 'claude',
            'gemini': 'gemini',
        }
        return mapping.get(provider_id, provider_id)

    def get_recommendation_summary(
        self, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get detailed recommendation summary for debugging/logging.

        Args:
            task_data: Task information

        Returns:
            Dict with analysis and recommendation details
        """
        analysis = self.analyze_task(task_data)

        return {
            'complexity_level': analysis.level.value,
            'complexity_score': round(analysis.score, 2),
            'recommended_provider': analysis.recommended_provider,
            'reasoning': analysis.reasoning,
            'factors': {k: round(v, 3) for k, v in analysis.factors.items()},
            'estimated_tokens': analysis.estimated_tokens,
            'latency_sensitive': analysis.latency_sensitive,
            'available_providers': self.available_providers,
        }


# Convenience functions

def get_provider_for_task(
    task_data: Dict[str, Any],
    user_preference: Optional[str] = None
) -> BaseLLMProvider:
    """
    Get optimal provider for a task with one function call.

    Convenience function for quick access.

    Args:
        task_data: Task information
        user_preference: Optional user preference override

    Returns:
        Instantiated BaseLLMProvider
    """
    selector = DynamicProviderSelector()
    return selector.select_provider(task_data, user_preference)


def analyze_and_recommend(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze task and get recommendation without instantiating provider.

    Args:
        task_data: Task information

    Returns:
        Recommendation summary dict
    """
    selector = DynamicProviderSelector()
    return selector.get_recommendation_summary(task_data)


__all__ = [
    'DynamicProviderSelector',
    'ProviderCapabilities',
    'get_provider_for_task',
    'analyze_and_recommend',
]
