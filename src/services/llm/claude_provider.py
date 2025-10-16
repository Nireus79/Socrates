"""
Claude LLM Provider Implementation
===================================

Wraps the existing ClaudeService for backward compatibility with the new
BaseLLMProvider interface.

This allows the existing Claude integration to work seamlessly with the
new multi-LLM provider system without breaking existing code.

Environment Variables:
- ANTHROPIC_API_KEY: Anthropic API key (required)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_provider import (
    BaseLLMProvider,
    LLMResponse,
    LLMProviderError
)

# Import existing Claude service
try:
    from src.services.claude_service import ClaudeService, ClaudeServiceError
    CLAUDE_SERVICE_AVAILABLE = True
except ImportError:
    CLAUDE_SERVICE_AVAILABLE = False


class ClaudeProvider(BaseLLMProvider):
    """
    Claude provider implementation wrapping existing ClaudeService.

    Provides backward compatibility while implementing the new BaseLLMProvider interface.
    """

    # Claude pricing per 1K tokens (as of 2024)
    PRICING = {
        'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
        'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
        'claude-3-5-sonnet-20241022': {'input': 0.003, 'output': 0.015},
        'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Claude provider.

        Args:
            config: Configuration dict (unused - ClaudeService loads from system config)
        """
        # Initialize config first
        self.config = config or {}

        # Try to initialize the existing ClaudeService
        self.claude_service = None
        if CLAUDE_SERVICE_AVAILABLE:
            try:
                self.claude_service = ClaudeService()
            except Exception as e:
                print(f"Warning: Failed to initialize ClaudeService: {e}")

        # Call parent init
        super().__init__(config)

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Claude"

    def is_available(self) -> bool:
        """Check if Claude is available."""
        return CLAUDE_SERVICE_AVAILABLE and self.claude_service is not None

    def get_models(self) -> List[str]:
        """Get list of available Claude models."""
        return [
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-5-sonnet-20241022',
            'claude-3-haiku-20240307',
        ]

    def _convert_response(self, claude_response) -> LLMResponse:
        """
        Convert ClaudeResponse to LLMResponse.

        Args:
            claude_response: Response from ClaudeService

        Returns:
            LLMResponse
        """
        return LLMResponse(
            content=claude_response.content,
            role=claude_response.role,
            model=claude_response.model,
            usage=claude_response.usage,
            stop_reason=claude_response.stop_reason,
            metadata=claude_response.metadata,
            provider='claude'
        )

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
        Send a chat message to Claude.

        Args:
            message: User message content
            system_prompt: Optional system prompt
            conversation_history: Previous messages
            model: Override default model
            max_tokens: Override default max tokens
            temperature: Override default temperature

        Returns:
            LLMResponse with assistant's reply
        """
        if not self.is_available():
            raise LLMProviderError("Claude provider is not available. Check API key and installation.")

        try:
            response = self.claude_service.chat(
                message=message,
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return self._convert_response(response)
        except ClaudeServiceError as e:
            raise LLMProviderError(f"Claude error: {str(e)}")

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
        if not self.is_available():
            raise LLMProviderError("Claude provider is not available.")

        try:
            response = self.claude_service.generate_code(
                requirements=requirements,
                programming_language=programming_language,
                framework=framework,
                include_tests=include_tests,
                include_documentation=include_documentation
            )
            return self._convert_response(response)
        except ClaudeServiceError as e:
            raise LLMProviderError(f"Claude error: {str(e)}")

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
        if not self.is_available():
            raise LLMProviderError("Claude provider is not available.")

        try:
            response = self.claude_service.analyze_code(
                code=code,
                programming_language=programming_language,
                analysis_type=analysis_type
            )
            return self._convert_response(response)
        except ClaudeServiceError as e:
            raise LLMProviderError(f"Claude error: {str(e)}")

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
        if not self.is_available():
            raise LLMProviderError("Claude provider is not available.")

        try:
            response = self.claude_service.process_document(
                document_content=document_content,
                task=task,
                document_type=document_type
            )
            return self._convert_response(response)
        except ClaudeServiceError as e:
            raise LLMProviderError(f"Claude error: {str(e)}")

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
        if not self.is_available():
            raise LLMProviderError("Claude provider is not available.")

        try:
            response = self.claude_service.generate_socratic_questions(
                topic=topic,
                role=role,
                context=context,
                question_count=question_count
            )
            return self._convert_response(response)
        except ClaudeServiceError as e:
            raise LLMProviderError(f"Claude error: {str(e)}")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        if not self.is_available():
            return {
                'provider': 'claude',
                'error': 'Claude service not available'
            }

        stats = self.claude_service.get_usage_stats()

        # Add provider field and standardize format
        stats['provider'] = 'claude'
        stats['estimated_cost_usd'] = stats.pop('estimated_cost', 0.0)

        return stats

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        if self.is_available():
            self.claude_service.reset_usage_stats()

    def health_check(self) -> Dict[str, Any]:
        """Check provider health and connectivity."""
        health = {
            'provider': 'claude',
            'status': 'unknown',
            'claude_service_available': CLAUDE_SERVICE_AVAILABLE,
            'service_initialized': self.claude_service is not None,
            'timestamp': datetime.now().isoformat()
        }

        if not CLAUDE_SERVICE_AVAILABLE:
            health['status'] = 'unhealthy'
            health['error'] = 'ClaudeService not available (import failed)'
            return health

        if not self.claude_service:
            health['status'] = 'unhealthy'
            health['error'] = 'ClaudeService failed to initialize'
            return health

        # Get health from ClaudeService
        try:
            service_health = self.claude_service.health_check()
            health['status'] = service_health.get('status', 'unknown')
            health['model'] = service_health.get('model')
            health['api_accessible'] = service_health.get('api_accessible', False)
            health['rate_limit_remaining'] = service_health.get('rate_limit_remaining')
            health['available_models'] = self.get_models()
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = f'Health check failed: {str(e)}'

        return health

    def get_cost_per_1k_tokens(self, model: Optional[str] = None) -> Dict[str, float]:
        """Get cost per 1K tokens for a model."""
        if not model and self.claude_service:
            model = self.claude_service.default_model

        return self.PRICING.get(model or 'claude-3-sonnet-20240229', {'input': 0.003, 'output': 0.015})

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses."""
        return True  # Claude supports streaming

    def supports_function_calling(self) -> bool:
        """Check if provider supports function/tool calling."""
        return True  # Claude supports tool use


__all__ = ['ClaudeProvider']
