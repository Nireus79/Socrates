"""
Ollama LLM Provider Implementation
===================================

Implements BaseLLMProvider for Ollama (local LLM runtime).

Ollama allows running LLMs locally:
- Llama 2, Llama 3
- Mistral, Mixtral
- CodeLlama
- Phi
- Many others

Supports:
- Chat completions
- Code generation with analysis
- Document processing
- Socratic question generation
- Usage tracking (no costs - local execution)
- Health monitoring

Requirements:
- Ollama installed and running (ollama.ai)
- Models pulled locally (ollama pull <model>)

Environment Variables:
- OLLAMA_HOST: Ollama server URL (default: http://localhost:11434)
"""

import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .base_provider import (
    BaseLLMProvider,
    LLMResponse,
    LLMUsage,
    LLMProviderError
)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider implementation for local LLM execution.

    No API costs, unlimited usage, complete privacy.
    Requires Ollama to be installed and running locally.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Ollama provider.

        Args:
            config: Configuration dict with optional settings:
                - host: Ollama server URL (default: http://localhost:11434)
                - model: Default model (default: llama3)
                - max_tokens: Default max tokens (default: 8192)
                - temperature: Default temperature (default: 0.7)
                - timeout_seconds: Request timeout (default: 120)
        """
        # Initialize config first
        self.config = config or {}

        # Ollama server URL
        self.host = (
            self.config.get('host') or
            os.getenv('OLLAMA_HOST') or
            'http://localhost:11434'
        )

        # Ensure host doesn't end with /
        self.host = self.host.rstrip('/')

        # Model settings
        self.default_model = self.config.get('model', 'llama3')
        self.default_max_tokens = self.config.get('max_tokens', 8192)
        self.default_temperature = self.config.get('temperature', 0.7)
        self.timeout = self.config.get('timeout_seconds', 120)  # Longer for local models

        # Available models cache
        self._available_models: Optional[List[str]] = None
        self._models_cache_time: Optional[float] = None
        self._models_cache_ttl = 300  # 5 minutes

        # Call parent init
        super().__init__(config)

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Ollama"

    def is_available(self) -> bool:
        """Check if Ollama is available and running."""
        if not REQUESTS_AVAILABLE:
            return False

        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_models(self) -> List[str]:
        """Get list of locally available Ollama models."""
        # Check cache
        now = time.time()
        if (self._available_models is not None and
            self._models_cache_time is not None and
            now - self._models_cache_time < self._models_cache_ttl):
            return self._available_models

        # Fetch from Ollama
        if not REQUESTS_AVAILABLE:
            return []

        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                self._available_models = models
                self._models_cache_time = now
                return models
        except:
            pass

        return []

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    def _update_usage(self, prompt: str, response_text: str) -> None:
        """Update usage statistics (no costs for Ollama)."""
        input_tokens = self._estimate_tokens(prompt)
        output_tokens = self._estimate_tokens(response_text)

        self.usage.request_count += 1
        self.usage.input_tokens += input_tokens
        self.usage.output_tokens += output_tokens
        self.usage.cost_estimate = 0.0  # Ollama is free
        self.usage.last_request = datetime.now()

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
        Make a completion request to Ollama.

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
            raise LLMProviderError(
                "Ollama is not available. "
                "Ensure Ollama is installed and running (ollama serve). "
                "Visit https://ollama.ai for installation instructions."
            )

        if not REQUESTS_AVAILABLE:
            raise LLMProviderError("requests package not installed (pip install requests)")

        # Use defaults if not specified
        model_name = model or self.default_model
        max_tokens = max_tokens or self.default_max_tokens
        temperature = temperature if temperature is not None else self.default_temperature

        # Check if model is available
        available_models = self.get_models()
        if model_name not in available_models:
            raise LLMProviderError(
                f"Model '{model_name}' not found locally. "
                f"Pull it with: ollama pull {model_name}\n"
                f"Available models: {', '.join(available_models) if available_models else 'none'}"
            )

        try:
            # Build messages
            messages = []

            # Add system message if provided
            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt
                })

            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)

            # Add current prompt
            messages.append({
                'role': 'user',
                'content': prompt
            })

            # Make request to Ollama
            payload = {
                'model': model_name,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            }

            response = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code != 200:
                raise LLMProviderError(f"Ollama API error: HTTP {response.status_code} - {response.text}")

            data = response.json()

            # Extract response
            content = data.get('message', {}).get('content', '')

            # Ollama provides token counts in some cases
            eval_count = data.get('eval_count', 0)
            prompt_eval_count = data.get('prompt_eval_count', 0)

            # If not provided, estimate
            if eval_count == 0:
                eval_count = self._estimate_tokens(content)
            if prompt_eval_count == 0:
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"
                prompt_eval_count = self._estimate_tokens(full_prompt)

            # Update usage
            full_input = prompt
            if system_prompt:
                full_input = f"{system_prompt}\n\n{prompt}"
            if conversation_history:
                for msg in conversation_history:
                    full_input += msg.get('content', '')

            self._update_usage(full_input, content)

            usage_dict = {
                'prompt_tokens': prompt_eval_count,
                'completion_tokens': eval_count,
                'total_tokens': prompt_eval_count + eval_count
            }

            return LLMResponse(
                content=content,
                role='assistant',
                model=model_name,
                usage=usage_dict,
                stop_reason='stop',
                provider='ollama',
                metadata={
                    'eval_duration': data.get('eval_duration'),
                    'load_duration': data.get('load_duration'),
                    'total_duration': data.get('total_duration')
                }
            )

        except requests.exceptions.Timeout:
            raise LLMProviderError(f"Ollama request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise LLMProviderError(
                f"Could not connect to Ollama at {self.host}. "
                "Ensure Ollama is running (ollama serve)."
            )
        except Exception as e:
            raise LLMProviderError(f"Ollama API error: {str(e)}")

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
        Send a chat message to Ollama.

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
            'provider': 'ollama',
            'request_count': self.usage.request_count,
            'input_tokens': self.usage.input_tokens,
            'output_tokens': self.usage.output_tokens,
            'total_tokens': self.usage.input_tokens + self.usage.output_tokens,
            'estimated_cost_usd': 0.0,  # Ollama is free
            'last_request': self.usage.last_request.isoformat() if self.usage.last_request else None,
            'default_model': self.default_model,
            'host': self.host,
            'note': 'Ollama runs locally - no API costs'
        }

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.usage = LLMUsage()

    def health_check(self) -> Dict[str, Any]:
        """Check provider health and connectivity."""
        health = {
            'provider': 'ollama',
            'status': 'unknown',
            'requests_available': REQUESTS_AVAILABLE,
            'host': self.host,
            'default_model': self.default_model,
            'timestamp': datetime.now().isoformat()
        }

        if not REQUESTS_AVAILABLE:
            health['status'] = 'unhealthy'
            health['error'] = 'requests package not installed (pip install requests)'
            return health

        # Try to connect to Ollama
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]

                health['status'] = 'healthy'
                health['ollama_running'] = True
                health['available_models'] = models
                health['model_count'] = len(models)

                # Check if default model is available
                if self.default_model not in models:
                    health['warning'] = f"Default model '{self.default_model}' not found locally. Pull it with: ollama pull {self.default_model}"
            else:
                health['status'] = 'unhealthy'
                health['error'] = f'Ollama returned HTTP {response.status_code}'
                health['ollama_running'] = False

        except requests.exceptions.ConnectionError:
            health['status'] = 'unhealthy'
            health['error'] = f'Could not connect to Ollama at {self.host}. Ensure Ollama is running (ollama serve).'
            health['ollama_running'] = False
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = f'Health check failed: {str(e)}'
            health['ollama_running'] = False

        return health

    def get_cost_per_1k_tokens(self, model: Optional[str] = None) -> Dict[str, float]:
        """Get cost per 1K tokens for a model (always 0 for Ollama)."""
        return {'input': 0.0, 'output': 0.0}

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses."""
        return True  # Ollama supports streaming

    def supports_function_calling(self) -> bool:
        """Check if provider supports function/tool calling."""
        return False  # Most Ollama models don't support function calling


__all__ = ['OllamaProvider']
