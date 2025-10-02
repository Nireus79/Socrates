"""
Claude Service - Anthropic Claude API Integration
================================================

Provides integration with Anthropic's Claude API for the Socratic RAG Enhanced system.
Handles authentication, request management, rate limiting, and various AI operations.

Features:
- Authenticated Claude API client
- Rate limiting and error handling
- Role-based conversation management
- Code generation and analysis
- Document processing and summarization
- Cost tracking and usage monitoring
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import anthropic
    from anthropic import Anthropic, AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None
    Anthropic = None
    AsyncAnthropic = None

from ..core import SocraticException

logger = logging.getLogger(__name__)


@dataclass
class ClaudeUsage:
    """Track Claude API usage and costs."""
    request_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_estimate: float = 0.0
    last_request: Optional[datetime] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None


@dataclass
class ClaudeResponse:
    """Structured response from Claude API."""
    content: str
    role: str = "assistant"
    model: str = "claude-3-sonnet-20240229"
    usage: Optional[Dict[str, int]] = None
    stop_reason: Optional[str] = None
    metadata: Dict[str, Any] = None


class ClaudeServiceError(SocraticException):
    """Claude service specific exceptions."""
    pass


class ClaudeService:
    """
    Anthropic Claude API integration service.

    Provides methods for interacting with Claude API including:
    - Chat and conversation management
    - Code generation and analysis
    - Document processing and summarization
    - Role-based questioning
    - Usage tracking and rate limiting
    """

    def __init__(self):
        # Lazy load config to avoid circular imports
        try:
            from src import get_config
            self.config = get_config()
        except (ImportError, AttributeError):
            # Fallback if get_config not available yet
            self.config = None

        self.claude_config = self.config.get('services', {}).get('claude', {}) if self.config else {}

        if not ANTHROPIC_AVAILABLE:
            raise ClaudeServiceError("Anthropic package not available. Install with: pip install anthropic")

        # Initialize API client
        api_key = self.claude_config.get('') or self.config.get('')  # TODO API_KEY_CLAUDE
        if not api_key:
            raise ClaudeServiceError("Claude API key not found in configuration")

        self.client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)

        # Configuration
        self.default_model = self.claude_config.get('default_model', 'claude-3-sonnet-20240229')
        self.max_tokens = self.claude_config.get('max_tokens', 4096)
        self.temperature = self.claude_config.get('temperature', 0.7)

        # Rate limiting
        self.rate_limit_requests = self.claude_config.get('rate_limit_requests', 50)
        self.rate_limit_window = self.claude_config.get('rate_limit_window', 60)  # seconds
        self.request_timestamps = []

        # Usage tracking
        self.usage = ClaudeUsage()

        logger.info(f"Claude service initialized with model: {self.default_model}")

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = time.time()
        # Remove timestamps older than the window
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < self.rate_limit_window]

        if len(self.request_timestamps) >= self.rate_limit_requests:
            logger.warning(f"Rate limit exceeded: {len(self.request_timestamps)} requests in {self.rate_limit_window}s")
            return False
        return True

    def _update_usage(self, response: Any) -> None:
        """Update usage tracking from API response."""
        self.usage.request_count += 1
        self.usage.last_request = datetime.now()

        if hasattr(response, 'usage') and response.usage:
            self.usage.input_tokens += response.usage.input_tokens
            self.usage.output_tokens += response.usage.output_tokens

            # Rough cost estimate (Claude 3 Sonnet pricing as of 2024)
            input_cost = response.usage.input_tokens * 0.000003  # $3 per 1M input tokens
            output_cost = response.usage.output_tokens * 0.000015  # $15 per 1M output tokens
            self.usage.cost_estimate += input_cost + output_cost

    def chat(
            self,
            message: str,
            system_prompt: Optional[str] = None,
            conversation_history: Optional[List[Dict[str, str]]] = None,
            model: Optional[str] = None,
            max_tokens: Optional[int] = None,
            temperature: Optional[float] = None
    ) -> ClaudeResponse:
        """
        Send a chat message to Claude.

        Args:
            message: User message content
            system_prompt: Optional system prompt for context
            conversation_history: Previous messages in conversation
            model: Override default model
            max_tokens: Override default max tokens
            temperature: Override default temperature

        Returns:
            ClaudeResponse with content and metadata
        """
        if not self._check_rate_limit():
            raise ClaudeServiceError("Rate limit exceeded. Please wait before making more requests.")

        try:
            # Build messages
            messages = []
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({"role": "user", "content": message})

            # API parameters
            params = {
                "model": model or self.default_model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "messages": messages
            }

            if system_prompt:
                params["system"] = system_prompt

            # Make API call
            self.request_timestamps.append(time.time())
            response = self.client.messages.create(**params)

            # Update usage tracking
            self._update_usage(response)

            return ClaudeResponse(
                content=response.content[0].text,
                model=response.model,
                usage=response.usage.__dict__ if hasattr(response, 'usage') else None,
                stop_reason=response.stop_reason,
                metadata={"id": response.id, "type": response.type}
            )

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise ClaudeServiceError(f"Failed to get response from Claude: {e}")

    def generate_code(
            self,
            requirements: str,
            programming_language: str = "python",
            framework: Optional[str] = None,
            include_tests: bool = True,
            include_documentation: bool = True
    ) -> ClaudeResponse:
        """
        Generate code based on requirements.

        Args:
            requirements: Detailed code requirements
            programming_language: Target programming language
            framework: Optional framework specification
            include_tests: Whether to include test code
            include_documentation: Whether to include documentation

        Returns:
            ClaudeResponse with generated code
        """
        system_prompt = f"""You are an expert {programming_language} developer. Generate high-quality, production-ready code based on the requirements provided.

Code Generation Guidelines:
- Write clean, well-documented, maintainable code
- Follow best practices and conventions for {programming_language}
- Include proper error handling and validation
- Use appropriate design patterns
- Make code modular and testable
"""

        if framework:
            system_prompt += f"- Use {framework} framework as specified\n"

        if include_tests:
            system_prompt += "- Include comprehensive unit tests\n"

        if include_documentation:
            system_prompt += "- Include docstrings and inline documentation\n"

        user_message = f"""Generate {programming_language} code for the following requirements:

{requirements}

Please provide:
1. Main implementation code
2. {"Unit tests" if include_tests else ""}
3. {"Documentation and usage examples" if include_documentation else ""}
4. Brief explanation of the approach and architecture

Format the response with clear sections and code blocks."""

        return self.chat(
            message=user_message,
            system_prompt=system_prompt,
            temperature=0.3  # Lower temperature for more consistent code generation
        )

    def analyze_code(
            self,
            code: str,
            programming_language: str = "python",
            analysis_type: str = "comprehensive"
    ) -> ClaudeResponse:
        """
        Analyze existing code for quality, security, and improvements.

        Args:
            code: Code to analyze
            programming_language: Programming language of the code
            analysis_type: Type of analysis (comprehensive, security, performance, style)

        Returns:
            ClaudeResponse with analysis results
        """
        system_prompt = f"""You are an expert code reviewer and security analyst. Analyze the provided {programming_language} code and provide detailed feedback.

Analysis Focus:
- Code quality and maintainability
- Security vulnerabilities and concerns
- Performance optimization opportunities
- Best practices adherence
- Potential bugs and edge cases
- Suggestions for improvement
"""

        user_message = f"""Please analyze this {programming_language} code with focus on {analysis_type} analysis:

```{programming_language}
{code}
```

Provide:
1. Overall assessment
2. Specific issues found (with line numbers if applicable)
3. Security concerns
4. Performance considerations
5. Recommended improvements
6. Refactored code examples (if significant improvements possible)
"""

        return self.chat(
            message=user_message,
            system_prompt=system_prompt,
            temperature=0.2  # Lower temperature for consistent analysis
        )

    def process_document(
            self,
            document_content: str,
            task: str = "summarize",
            document_type: str = "text"
    ) -> ClaudeResponse:
        """
        Process and analyze documents.

        Args:
            document_content: Content of the document
            task: Processing task (summarize, extract_key_points, analyze, question)
            document_type: Type of document (text, code, technical, business)

        Returns:
            ClaudeResponse with processed document analysis
        """
        system_prompts = {
            "summarize": "You are an expert document analyst. Create concise, accurate summaries that capture the key information and main points.",
            "extract_key_points": "You are an expert information extractor. Identify and extract the most important points, facts, and insights from documents.",
            "analyze": "You are an expert document analyst. Provide thorough analysis including themes, insights, implications, and actionable takeaways.",
            "question": "You are an expert question generator. Create insightful questions that help explore and understand the document content deeply."
        }

        system_prompt = system_prompts.get(task, system_prompts["summarize"])

        task_instructions = {
            "summarize": "Create a concise summary that captures the main points and key information.",
            "extract_key_points": "Extract the most important points, facts, and insights as a bulleted list.",
            "analyze": "Provide comprehensive analysis including themes, insights, implications, and recommendations.",
            "question": "Generate thoughtful questions that would help someone understand and explore this content deeply."
        }

        instruction = task_instructions.get(task, task_instructions["summarize"])

        user_message = f"""Please {task} the following {document_type} document:

{document_content}

Task: {instruction}

Provide a structured response with clear sections and actionable insights."""

        return self.chat(
            message=user_message,
            system_prompt=system_prompt,
            temperature=0.4
        )

    def generate_socratic_questions(
            self,
            topic: str,
            role: str = "developer",
            context: Optional[str] = None,
            question_count: int = 5
    ) -> ClaudeResponse:
        """
        Generate role-based Socratic questions.

        Args:
            topic: Topic or project to generate questions about
            role: Role perspective (developer, manager, designer, tester, etc.)
            context: Additional context for question generation
            question_count: Number of questions to generate

        Returns:
            ClaudeResponse with generated questions
        """
        role_prompts = {
            "developer": "You are an expert software developer. Generate technical questions that explore implementation details, architecture, and code quality.",
            "manager": "You are an experienced project manager. Generate strategic questions about planning, resources, timelines, and stakeholder needs.",
            "designer": "You are a UX/UI design expert. Generate questions about user experience, interface design, and usability.",
            "tester": "You are a QA expert. Generate questions about testing, edge cases, quality assurance, and validation.",
            "business_analyst": "You are a business analyst. Generate questions about business requirements, processes, and stakeholder value.",
            "devops": "You are a DevOps engineer. Generate questions about deployment, infrastructure, monitoring, and scalability."
        }

        system_prompt = role_prompts.get(role, role_prompts["developer"])
        system_prompt += f"\n\nGenerate {question_count} insightful Socratic questions that help explore and refine the understanding of the topic."

        user_message = f"""Generate {question_count} Socratic questions from a {role} perspective for the following topic:

Topic: {topic}
"""

        if context:
            user_message += f"\nAdditional Context: {context}"

        user_message += f"""

The questions should:
1. Be open-ended and thought-provoking
2. Help clarify requirements and assumptions
3. Uncover potential issues or considerations
4. Guide toward better solutions
5. Be specific to the {role} role perspective

Format as a numbered list with brief explanations of why each question is important."""

        return self.chat(
            message=user_message,
            system_prompt=system_prompt,
            temperature=0.6  # Higher temperature for creative question generation
        )

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            "request_count": self.usage.request_count,
            "input_tokens": self.usage.input_tokens,
            "output_tokens": self.usage.output_tokens,
            "total_tokens": self.usage.input_tokens + self.usage.output_tokens,
            "estimated_cost": self.usage.cost_estimate,
            "last_request": self.usage.last_request.isoformat() if self.usage.last_request else None,
            "rate_limit_remaining": max(0, self.rate_limit_requests - len(self.request_timestamps)),
            "rate_limit_window": self.rate_limit_window
        }

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.usage = ClaudeUsage()
        logger.info("Claude usage statistics reset")

    def health_check(self) -> Dict[str, Any]:
        """Check service health and connectivity."""
        try:
            # Simple test request
            test_response = self.chat("Hello", max_tokens=10)

            return {
                "status": "healthy",
                "model": self.default_model,
                "api_accessible": True,
                "rate_limit_remaining": max(0, self.rate_limit_requests - len(self.request_timestamps)),
                "usage_stats": self.get_usage_stats(),
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Claude health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_accessible": False,
                "last_check": datetime.now().isoformat()
            }
