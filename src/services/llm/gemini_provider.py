"""
Google Gemini LLM Provider Implementation
==========================================

Implements BaseLLMProvider for Google's Gemini models (Gemini Pro, Gemini Ultra, etc.).

Supports:
- Chat completions
- Code generation with analysis
- Document processing
- Socratic question generation
- Usage tracking and cost calculation
- Rate limiting
- Health monitoring

Environment Variables:
- GOOGLE_API_KEY or GEMINI_API_KEY: Google API key (required)
"""

import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base_provider import (
    BaseLLMProvider,
    LLMResponse,
    LLMUsage,
    LLMProviderError
)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini provider implementation.

    Supports Gemini Pro, Gemini Ultra, and other Gemini models.
    """

    # Gemini pricing per 1K tokens (as of 2024)
    # Note: Gemini has free tier with rate limits
    PRICING = {
        'gemini-pro': {'input': 0.00025, 'output': 0.0005},
        'gemini-pro-vision': {'input': 0.00025, 'output': 0.0005},
        'gemini-1.5-pro': {'input': 0.0035, 'output': 0.0105},
        'gemini-1.5-flash': {'input': 0.00035, 'output': 0.00105},
        'gemini-ultra': {'input': 0.00125, 'output': 0.00375},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Gemini provider.

        Args:
            config: Configuration dict with optional settings:
                - api_key: Google API key (falls back to env var)
                - model: Default model (default: gemini-1.5-pro)
                - max_tokens: Default max tokens (default: 8192)
                - temperature: Default temperature (default: 0.7)
                - timeout_seconds: Request timeout (default: 60)
        """
        # Initialize config first
        self.config = config or {}

        # API key (try both GOOGLE_API_KEY and GEMINI_API_KEY)
        self.api_key = (
            self.config.get('api_key') or
            os.getenv('GOOGLE_API_KEY') or
            os.getenv('GEMINI_API_KEY')
        )

        # Model settings
        self.default_model = self.config.get('model', 'gemini-1.5-pro')
        self.default_max_tokens = self.config.get('max_tokens', 8192)
        self.default_temperature = self.config.get('temperature', 0.7)
        self.timeout = self.config.get('timeout_seconds', 60)

        # Initialize Gemini
        self.model_instances = {}
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to configure Gemini: {e}")

        # Rate limiting
        self.rate_limit_requests = 60  # Gemini has higher free tier limits
        self.rate_limit_window = 60  # seconds
        self._request_times: List[float] = []

        # Call parent init
        super().__init__(config)

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Google Gemini"

    def is_available(self) -> bool:
        """Check if Gemini is available."""
        return GEMINI_AVAILABLE and self.api_key is not None

    def get_models(self) -> List[str]:
        """Get list of available Gemini models."""
        return [
            'gemini-pro',
            'gemini-pro-vision',
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            'gemini-ultra',
        ]

    def _get_model(self, model_name: str):
        """Get or create model instance."""
        if model_name not in self.model_instances:
            try:
                self.model_instances[model_name] = genai.GenerativeModel(model_name)
            except Exception as e:
                raise LLMProviderError(f"Failed to create Gemini model '{model_name}': {str(e)}")

        return self.model_instances[model_name]

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
        pricing = self.PRICING.get(model, {'input': 0.00025, 'output': 0.0005})

        input_cost = (input_tokens / 1000.0) * pricing['input']
        output_cost = (output_tokens / 1000.0) * pricing['output']

        return input_cost + output_cost

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Gemini uses similar tokenization to other models
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    def _update_usage(self, prompt: str, response_text: str, model: str) -> None:
        """Update usage statistics."""
        # Gemini API doesn't always provide token counts in free tier
        # We'll estimate them
        input_tokens = self._estimate_tokens(prompt)
        output_tokens = self._estimate_tokens(response_text)

        self.usage.request_count += 1
        self.usage.input_tokens += input_tokens
        self.usage.output_tokens += output_tokens
        self.usage.cost_estimate += self._calculate_cost(model, input_tokens, output_tokens)
        self.usage.last_request = datetime.now()

    def _build_chat_history(
        self,
        system_prompt: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """Build chat history for Gemini."""
        history = []

        # Gemini uses 'user' and 'model' roles (not 'assistant')
        if conversation_history:
            for msg in conversation_history:
                role = msg.get('role', 'user')
                if role == 'assistant':
                    role = 'model'
                history.append({
                    'role': role,
                    'parts': [msg.get('content', '')]
                })

        return history

    def _make_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> LLMResponse:
        """
        Make a completion request to Gemini.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            conversation_history: Previous messages
            model: Model to use
            max_tokens: Max tokens to generate
            temperature: Temperature for sampling

        Returns:
            LLMResponse with completion
        """
        if not self.is_available():
            raise LLMProviderError("Gemini provider is not available. Check API key and installation.")

        # Check rate limit
        self._check_rate_limit()

        # Use defaults if not specified
        model_name = model or self.default_model
        max_tokens = max_tokens or self.default_max_tokens
        temperature = temperature if temperature is not None else self.default_temperature

        try:
            model = self._get_model(model_name)

            # Configure generation
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )

            # If we have conversation history, use chat mode
            if conversation_history:
                # Build history
                history = self._build_chat_history(system_prompt, conversation_history)

                # Start chat
                chat = model.start_chat(history=history)

                # Send message
                response = chat.send_message(
                    prompt,
                    generation_config=generation_config
                )
            else:
                # Single prompt mode
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"

                response = model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )

            # Extract response
            content = response.text
            stop_reason = 'stop'  # Gemini doesn't provide detailed stop reasons

            # Update usage (estimated)
            full_input = prompt
            if system_prompt:
                full_input = f"{system_prompt}\n\n{prompt}"
            if conversation_history:
                for msg in conversation_history:
                    full_input += msg.get('content', '')

            self._update_usage(full_input, content, model_name)

            # Estimate usage for response
            usage_dict = {
                'prompt_tokens': self._estimate_tokens(full_input),
                'completion_tokens': self._estimate_tokens(content),
                'total_tokens': self._estimate_tokens(full_input) + self._estimate_tokens(content)
            }

            return LLMResponse(
                content=content,
                role='assistant',
                model=model_name,
                usage=usage_dict,
                stop_reason=stop_reason,
                provider='gemini'
            )

        except Exception as e:
            raise LLMProviderError(f"Gemini API error: {str(e)}")

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
        Send a chat message to Gemini.

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
        return self._make_completion(
            prompt=message,
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )

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

        system_prompt = 'You are an expert software engineer who writes clean, efficient, well-documented code.'

        return self._make_completion(prompt, system_prompt=system_prompt, max_tokens=4096)

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

        system_prompt = 'You are an expert code reviewer with deep knowledge of software engineering best practices, security, and performance optimization.'

        return self._make_completion(prompt, system_prompt=system_prompt, max_tokens=4096)

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

        system_prompt = f'You are an expert at analyzing and processing {document_type} documents.'

        return self._make_completion(prompt, system_prompt=system_prompt, max_tokens=4096)

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

        system_prompt = f'You are a Socratic mentor helping a {role} think deeply about their work.'

        return self._make_completion(prompt, system_prompt=system_prompt, max_tokens=2048)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            'provider': 'gemini',
            'request_count': self.usage.request_count,
            'input_tokens': self.usage.input_tokens,
            'output_tokens': self.usage.output_tokens,
            'total_tokens': self.usage.input_tokens + self.usage.output_tokens,
            'estimated_cost_usd': round(self.usage.cost_estimate, 4),
            'last_request': self.usage.last_request.isoformat() if self.usage.last_request else None,
            'rate_limit_remaining': self.rate_limit_requests - len(self._request_times),
            'default_model': self.default_model,
            'note': 'Token counts are estimated (Gemini API does not always provide exact counts)'
        }

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.usage = LLMUsage()
        self._request_times = []

    def health_check(self) -> Dict[str, Any]:
        """Check provider health and connectivity."""
        health = {
            'provider': 'gemini',
            'status': 'unknown',
            'gemini_available': GEMINI_AVAILABLE,
            'api_key_configured': self.api_key is not None,
            'default_model': self.default_model,
            'timestamp': datetime.now().isoformat()
        }

        # Check if basic requirements are met
        if not GEMINI_AVAILABLE:
            health['status'] = 'unhealthy'
            health['error'] = 'Gemini package not installed (pip install google-generativeai)'
            return health

        if not self.api_key:
            health['status'] = 'unhealthy'
            health['error'] = 'Google API key not configured'
            return health

        # Try a test request
        try:
            model = self._get_model(self.default_model)
            response = model.generate_content(
                "Hello",
                generation_config=genai.types.GenerationConfig(max_output_tokens=5)
            )
            _ = response.text  # Access text to trigger any errors

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
        return self.PRICING.get(model, {'input': 0.00025, 'output': 0.0005})

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses."""
        return True  # Gemini supports streaming

    def supports_function_calling(self) -> bool:
        """Check if provider supports function/tool calling."""
        return True  # Gemini Pro supports function calling


__all__ = ['GeminiProvider']
