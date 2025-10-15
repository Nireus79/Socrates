"""
Base LLM Provider - Abstract Interface for LLM Integration
==========================================================

Provides abstract base class for all LLM providers.
Makes it easy to add support for new LLMs (OpenAI, Gemini, Ollama, etc.).

Design Pattern: Strategy Pattern + Factory Pattern
- BaseLLMProvider defines the interface all LLMs must implement
- Concrete providers (ClaudeProvider, OpenAIProvider) implement specific LLM logic
- LLMProviderFactory creates appropriate provider based on user preference
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class LLMUsage:
    """Track LLM API usage and costs."""
    request_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_estimate: float = 0.0
    last_request: Optional[datetime] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None


@dataclass
class LLMResponse:
    """Structured response from LLM API (provider-agnostic)."""
    content: str
    role: str = "assistant"
    model: str = ""
    usage: Optional[Dict[str, int]] = None
    stop_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    provider: str = ""  # Which LLM provider generated this


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM providers must implement these methods to ensure consistent behavior
    across different LLMs (Claude, OpenAI, Gemini, Ollama, etc.).

    This abstraction allows the system to support multiple LLMs without changing
    agent code - agents work with the BaseLLMProvider interface, not specific LLMs.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM provider.

        Args:
            config: Optional configuration dict for this LLM
        """
        self.config = config or {}
        self.provider_name = self.get_provider_name()
        self.usage = LLMUsage()

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get human-readable provider name.

        Returns:
            Provider name (e.g., "Claude", "OpenAI", "Gemini")
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this LLM provider is available (API key set, etc.).

        Returns:
            True if provider is available, False otherwise
        """
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """
        Get list of available models for this provider.

        Returns:
            List of model identifiers
        """
        pass

    @abstractmethod
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> LLMResponse:
        """
        Send a chat message to the LLM.

        Args:
            message: User message content
            system_prompt: Optional system prompt for context
            conversation_history: Previous messages in conversation
            model: Override default model
            max_tokens: Override default max tokens
            temperature: Override default temperature

        Returns:
            LLMResponse with content and metadata
        """
        pass

    @abstractmethod
    def generate_code(
        self,
        requirements: str,
        programming_language: str = "python",
        framework: Optional[str] = None,
        include_tests: bool = True,
        include_documentation: bool = True
    ) -> LLMResponse:
        """
        Generate code based on requirements.

        Args:
            requirements: Detailed code requirements
            programming_language: Target programming language
            framework: Optional framework specification
            include_tests: Whether to include test code
            include_documentation: Whether to include documentation

        Returns:
            LLMResponse with generated code
        """
        pass

    @abstractmethod
    def analyze_code(
        self,
        code: str,
        programming_language: str = "python",
        analysis_type: str = "comprehensive"
    ) -> LLMResponse:
        """
        Analyze existing code for quality, security, and improvements.

        Args:
            code: Code to analyze
            programming_language: Programming language of the code
            analysis_type: Type of analysis (comprehensive, security, performance, style)

        Returns:
            LLMResponse with analysis results
        """
        pass

    @abstractmethod
    def process_document(
        self,
        document_content: str,
        task: str = "summarize",
        document_type: str = "text"
    ) -> LLMResponse:
        """
        Process and analyze documents.

        Args:
            document_content: Content of the document
            task: Processing task (summarize, extract_key_points, analyze, question)
            document_type: Type of document (text, code, technical, business)

        Returns:
            LLMResponse with processed document analysis
        """
        pass

    @abstractmethod
    def generate_socratic_questions(
        self,
        topic: str,
        role: str = "developer",
        context: Optional[str] = None,
        question_count: int = 5
    ) -> LLMResponse:
        """
        Generate role-based Socratic questions.

        Args:
            topic: Topic or project to generate questions about
            role: Role perspective (developer, manager, designer, tester, etc.)
            context: Additional context for question generation
            question_count: Number of questions to generate

        Returns:
            LLMResponse with generated questions
        """
        pass

    @abstractmethod
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.

        Returns:
            Dict with usage stats (requests, tokens, costs, etc.)
        """
        pass

    @abstractmethod
    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check provider health and connectivity.

        Returns:
            Dict with health status information
        """
        pass

    # Optional methods with default implementations

    def get_default_model(self) -> str:
        """
        Get default model for this provider.

        Returns:
            Default model identifier
        """
        models = self.get_models()
        return models[0] if models else ""

    def get_cost_per_1k_tokens(self, model: Optional[str] = None) -> Dict[str, float]:
        """
        Get cost per 1K tokens for a model.

        Args:
            model: Model to get pricing for (defaults to default model)

        Returns:
            Dict with 'input' and 'output' costs per 1K tokens
        """
        # Override in subclass with actual pricing
        return {"input": 0.0, "output": 0.0}

    def supports_streaming(self) -> bool:
        """
        Check if provider supports streaming responses.

        Returns:
            True if streaming is supported
        """
        return False

    def supports_function_calling(self) -> bool:
        """
        Check if provider supports function/tool calling.

        Returns:
            True if function calling is supported
        """
        return False


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass


__all__ = [
    'BaseLLMProvider',
    'LLMResponse',
    'LLMUsage',
    'LLMProviderError'
]
