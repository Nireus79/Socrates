"""
OpenAI LLM Provider Implementation
===================================

Implements BaseLLMProvider for OpenAI GPT models (GPT-4, GPT-3.5-turbo, etc.).

Supports:
- Chat completions
- Code generation with analysis
- Document processing
- Socratic question generation
- Usage tracking and cost calculation
- Rate limiting
- Health monitoring

Environment Variables:
- OPENAI_API_KEY: OpenAI API key (required)
"""

import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base_provider import (
    BaseLLMProvider,
    LLMResponse,
    LLMUsage,
    LLMProviderError
)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI GPT provider implementation.

    Supports GPT-4, GPT-4 Turbo, GPT-3.5-turbo, and other OpenAI models.
    """

    # OpenAI pricing per 1K tokens (as of 2024)
    PRICING = {
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
        'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
        'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
        'gpt-3.5-turbo-16k': {'input': 0.003, 'output': 0.004},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize OpenAI provider.

        Args:
            config: Configuration dict with optional settings:
                - api_key: OpenAI API key (falls back to env var)
                - model: Default model (default: gpt-4-turbo)
                - max_tokens: Default max tokens (default: 8192)
                - temperature: Default temperature (default: 0.7)
                - timeout_seconds: Request timeout (default: 60)
        """
        # Initialize config first
        self.config = config or {}

        # API key
        self.api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')

        # Model settings
        self.default_model = self.config.get('model', 'gpt-4-turbo')
        self.default_max_tokens = self.config.get('max_tokens', 8192)
        self.default_temperature = self.config.get('temperature', 0.7)
        self.timeout = self.config.get('timeout_seconds', 60)

        # Initialize OpenAI client
        self.client = None
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key, timeout=self.timeout)
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")

        # Rate limiting
        self.rate_limit_requests = 50
        self.rate_limit_window = 60  # seconds
        self._request_times: List[float] = []

        # Call parent init
        super().__init__(config)

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "OpenAI"

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return OPENAI_AVAILABLE and self.api_key is not None and self.client is not None

    def get_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        return [
            'gpt-4',
            'gpt-4-turbo',
            'gpt-4-turbo-preview',
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-16k',
        ]

    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        now = time.time()

        # Remove requests outside the window
        self._request_times = [t for t in self._request_times if now - t < self.rate_limit_window]

        # Check if we're at the limit
        if len(self._request_times) >= self.rate_limit_requests:
            oldest = self._request_times[0]
            wait_time = self.rate_limit_window - (now - oldest)
            if wait_time > 0:
                time.sleep(wait_time + 0.1)  # Add small buffer

        # Record this request
        self._request_times.append(time.time())

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for this request."""
        pricing = self.PRICING.get(model, {'input': 0.01, 'output': 0.03})

        input_cost = (input_tokens / 1000.0) * pricing['input']
        output_cost = (output_tokens / 1000.0) * pricing['output']

        return input_cost + output_cost

    def _update_usage(self, response_usage: Dict[str, int], model: str) -> None:
        """Update usage statistics."""
        input_tokens = response_usage.get('prompt_tokens', 0)
        output_tokens = response_usage.get('completion_tokens', 0)

        self.usage.request_count += 1
        self.usage.input_tokens += input_tokens
        self.usage.output_tokens += output_tokens
        self.usage.cost_estimate += self._calculate_cost(model, input_tokens, output_tokens)
        self.usage.last_request = datetime.now()

    def _make_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> LLMResponse:
        """
        Make a completion request to OpenAI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            max_tokens: Max tokens to generate
            temperature: Temperature for sampling

        Returns:
            LLMResponse with completion
        """
        if not self.is_available():
            raise LLMProviderError("OpenAI provider is not available. Check API key and installation.")

        # Check rate limit
        self._check_rate_limit()

        # Use defaults if not specified
        model = model or self.default_model
        max_tokens = max_tokens or self.default_max_tokens
        temperature = temperature if temperature is not None else self.default_temperature

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            # Extract response
            content = response.choices[0].message.content
            stop_reason = response.choices[0].finish_reason

            # Update usage
            usage_dict = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            self._update_usage(usage_dict, model)

            return LLMResponse(
                content=content,
                role='assistant',
                model=model,
                usage=usage_dict,
                stop_reason=stop_reason,
                provider='openai'
            )

        except Exception as e:
            raise LLMProviderError(f"OpenAI API error: {str(e)}")

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
        Send a chat message to OpenAI.

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
        # Build messages list
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current message
        messages.append({'role': 'user', 'content': message})

        return self._make_completion(messages, model, max_tokens, temperature)

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
        # Build prompt
        prompt = f"""Generate {programming_language} code based on these requirements:

{requirements}

"""

        if framework:
            prompt += f"Framework: {framework}\n\n"

        prompt += "Please provide:\n"
        prompt += "1. Complete, working code with proper structure\n"

        if include_tests:
            prompt += "2. Unit tests for the code\n"

        if include_documentation:
            prompt += "3. Documentation and usage examples\n"

        prompt += "\nEnsure the code follows best practices and is production-ready."

        messages = [
            {'role': 'system', 'content': 'You are an expert software engineer who writes clean, efficient, well-documented code.'},
            {'role': 'user', 'content': prompt}
        ]

        return self._make_completion(messages, max_tokens=4096)

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
        analysis_instructions = {
            'comprehensive': 'Provide a comprehensive analysis covering code quality, security, performance, maintainability, and best practices.',
            'security': 'Focus on security vulnerabilities, potential exploits, and security best practices.',
            'performance': 'Focus on performance optimization opportunities, bottlenecks, and efficiency.',
            'style': 'Focus on code style, formatting, naming conventions, and readability.'
        }

        instruction = analysis_instructions.get(analysis_type, analysis_instructions['comprehensive'])

        prompt = f"""Analyze this {programming_language} code:

```{programming_language}
{code}
```

{instruction}

Provide:
1. Summary of findings
2. Specific issues identified (with line numbers if applicable)
3. Recommended improvements
4. Severity levels for each issue (critical, high, medium, low)
"""

        messages = [
            {'role': 'system', 'content': 'You are an expert code reviewer with deep knowledge of software engineering best practices, security, and performance optimization.'},
            {'role': 'user', 'content': prompt}
        ]

        return self._make_completion(messages, max_tokens=4096)

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
        task_instructions = {
            'summarize': 'Provide a concise summary of the key points and main ideas.',
            'extract_key_points': 'Extract and list the most important key points, facts, and insights.',
            'analyze': 'Provide a detailed analysis including themes, arguments, and implications.',
            'question': 'Generate insightful questions that could be asked about this document.'
        }

        instruction = task_instructions.get(task, task_instructions['summarize'])

        prompt = f"""Process this {document_type} document:

{document_content}

Task: {instruction}
"""

        messages = [
            {'role': 'system', 'content': f'You are an expert at analyzing and processing {document_type} documents.'},
            {'role': 'user', 'content': prompt}
        ]

        return self._make_completion(messages, max_tokens=4096)

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
        prompt = f"""Generate {question_count} Socratic questions about: {topic}

Role perspective: {role}

"""

        if context:
            prompt += f"Context:\n{context}\n\n"

        prompt += f"""Generate thought-provoking Socratic questions that:
1. Challenge assumptions
2. Explore deeper implications
3. Encourage critical thinking
4. Are relevant to the {role} role
5. Help uncover potential issues or improvements

Format each question clearly and number them."""

        messages = [
            {'role': 'system', 'content': f'You are a Socratic mentor helping a {role} think deeply about their work.'},
            {'role': 'user', 'content': prompt}
        ]

        return self._make_completion(messages, max_tokens=2048)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            'provider': 'openai',
            'request_count': self.usage.request_count,
            'input_tokens': self.usage.input_tokens,
            'output_tokens': self.usage.output_tokens,
            'total_tokens': self.usage.input_tokens + self.usage.output_tokens,
            'estimated_cost_usd': round(self.usage.cost_estimate, 4),
            'last_request': self.usage.last_request.isoformat() if self.usage.last_request else None,
            'rate_limit_remaining': self.rate_limit_requests - len(self._request_times),
            'default_model': self.default_model
        }

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.usage = LLMUsage()
        self._request_times = []

    def health_check(self) -> Dict[str, Any]:
        """Check provider health and connectivity."""
        health = {
            'provider': 'openai',
            'status': 'unknown',
            'openai_available': OPENAI_AVAILABLE,
            'api_key_configured': self.api_key is not None,
            'client_initialized': self.client is not None,
            'default_model': self.default_model,
            'timestamp': datetime.now().isoformat()
        }

        # Check if basic requirements are met
        if not OPENAI_AVAILABLE:
            health['status'] = 'unhealthy'
            health['error'] = 'OpenAI package not installed (pip install openai)'
            return health

        if not self.api_key:
            health['status'] = 'unhealthy'
            health['error'] = 'OpenAI API key not configured'
            return health

        # Try a test request
        try:
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[{'role': 'user', 'content': 'Hello'}],
                max_tokens=5
            )
            health['status'] = 'healthy'
            health['test_successful'] = True
            health['available_models'] = self.get_models()
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = f'API test failed: {str(e)}'
            health['test_successful'] = False

        return health

    def get_cost_per_1k_tokens(self, model: Optional[str] = None) -> Dict[str, float]:
        """Get cost per 1K tokens for a model."""
        model = model or self.default_model
        return self.PRICING.get(model, {'input': 0.01, 'output': 0.03})

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses."""
        return True  # OpenAI supports streaming

    def supports_function_calling(self) -> bool:
        """Check if provider supports function/tool calling."""
        return True  # OpenAI supports function calling


__all__ = ['OpenAIProvider']
