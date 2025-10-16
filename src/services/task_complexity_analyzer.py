"""
Task Complexity Analyzer
========================

Analyzes task complexity to determine optimal LLM provider selection.

The analyzer evaluates tasks based on multiple dimensions:
- Reasoning depth (simple answers vs complex reasoning)
- Code generation requirements (simple vs complex implementations)
- Context requirements (small vs large context windows)
- Latency sensitivity (interactive vs background)
- Cost sensitivity (compute-intensive vs lightweight)

Classification:
- SIMPLE: Fast responses for straightforward questions (Haiku)
- MODERATE: Balanced reasoning and code quality (Sonnet)
- COMPLEX: Deep reasoning and architecture analysis (Opus)

Usage:
    analyzer = TaskComplexityAnalyzer()
    complexity = analyzer.analyze({
        'task_type': 'code_generation',
        'requirements': 'Complex REST API with microservices',
        'context_size': 5000
    })
    print(f"Complexity: {complexity.level}")  # COMPLEX
    print(f"Provider: {complexity.recommended_provider}")  # claude
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ComplexityLevel(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"         # Use Haiku: fast, cost-effective for straightforward tasks
    MODERATE = "moderate"     # Use Sonnet: balanced reasoning and quality
    COMPLEX = "complex"       # Use Opus: deep reasoning and architecture analysis


class TaskType(Enum):
    """Types of tasks the system handles."""
    CHAT_REPLY = "chat_reply"                          # Simple chat responses
    SOCRATIC_QUESTIONS = "socratic_questions"          # Generate Socratic questions
    CODE_GENERATION = "code_generation"                # Generate code
    CODE_ANALYSIS = "code_analysis"                    # Analyze code
    ARCHITECTURE_ANALYSIS = "architecture_analysis"    # Design analysis
    DOCUMENT_PROCESSING = "document_processing"        # Process documents
    CONFLICT_DETECTION = "conflict_detection"          # Detect conflicts in specs
    FOLLOW_UP_QUESTION = "follow_up_question"          # Quick follow-ups to previous responses


@dataclass
class ComplexityAnalysis:
    """Result of task complexity analysis."""
    level: ComplexityLevel
    score: float  # 0.0 (simple) to 1.0 (complex)
    recommended_provider: str  # Provider recommendation: 'ollama', 'haiku', 'sonnet', 'opus', 'claude'
    factors: Dict[str, float]  # Breakdown of complexity factors
    reasoning: str  # Explanation of the recommendation
    estimated_tokens: int  # Estimated token usage
    latency_sensitive: bool  # Whether response time is critical


class TaskComplexityAnalyzer:
    """
    Analyzes task complexity and recommends optimal LLM provider.

    Scoring Factors (0.0-1.0):
    1. Reasoning Depth (0-0.3 simple to 0.7-1.0 complex)
       - Keywords: "analyze", "architecture", "optimize", "explain", "why"
       - Complexity: number of decision points
    2. Code Complexity (0-0.25 simple to 0.75-1.0 complex)
       - Keywords: "REST API", "microservice", "database design", "security"
       - Patterns: architecture, scalability, testing requirements
    3. Context Requirement (0-0.2 small to 0.8-1.0 large)
       - Input size (characters, lines of code, documents)
       - Required context (specifications, requirements)
    4. Latency Sensitivity (0-0.15 interactive to 0.85-1.0 background)
       - Task type: chat replies are interactive, analysis can be background
    5. Domain Specificity (0-0.1 general to 0.9-1.0 specialized)
       - Technical depth: architectural vs simple questions
    """

    # Keywords indicating different complexity levels
    SIMPLE_KEYWORDS = {
        'hello', 'help', 'what', 'which', 'how', 'define', 'list',
        'explain', 'brief', 'quick', 'simple', 'basic', 'overview',
        'tell me about', 'what is', 'describe', 'show example'
    }

    MODERATE_KEYWORDS = {
        'implement', 'create', 'design', 'build', 'develop', 'write',
        'improve', 'refactor', 'optimize', 'test', 'review',
        'component', 'function', 'feature', 'integration'
    }

    COMPLEX_KEYWORDS = {
        'architecture', 'microservice', 'scalability', 'performance',
        'security', 'reliability', 'fault tolerance', 'distributed',
        'analysis', 'evaluate', 'compare', 'strategy', 'trade-off',
        'conflict', 'resolution', 'validation', 'greedy'
    }

    # Task type complexity mappings
    TASK_TYPE_BASE_COMPLEXITY = {
        TaskType.CHAT_REPLY: 0.15,                    # Very simple
        TaskType.FOLLOW_UP_QUESTION: 0.20,            # Simple
        TaskType.DOCUMENT_PROCESSING: 0.35,           # Moderate-low
        TaskType.SOCRATIC_QUESTIONS: 0.45,            # Moderate
        TaskType.CODE_ANALYSIS: 0.55,                 # Moderate-high
        TaskType.CODE_GENERATION: 0.65,               # High
        TaskType.CONFLICT_DETECTION: 0.70,            # High
        TaskType.ARCHITECTURE_ANALYSIS: 0.85,         # Very high
    }

    def __init__(self):
        """Initialize the complexity analyzer."""
        self.logger = logger

    def analyze(self, task_data: Dict[str, Any]) -> ComplexityAnalysis:
        """
        Analyze task complexity and recommend provider.

        Args:
            task_data: Dict containing task information:
                - task_type: str or TaskType (required)
                - content: str (optional) - main task content
                - requirements: str (optional) - specific requirements
                - context_size: int (optional) - size of context in bytes
                - code_lines: int (optional) - number of lines of code
                - is_interactive: bool (optional) - true for real-time responses
                - use_rag: bool (optional) - true if using RAG context
                - domain_keywords: list[str] (optional) - domain-specific keywords
                - architecture_related: bool (optional) - involves architecture

        Returns:
            ComplexityAnalysis with recommendation
        """
        try:
            # Extract task information
            task_type = self._parse_task_type(task_data.get('task_type'))
            content = task_data.get('content', '') or ''
            requirements = task_data.get('requirements', '') or ''
            context_size = task_data.get('context_size', 0)
            code_lines = task_data.get('code_lines', 0)
            is_interactive = task_data.get('is_interactive', True)
            use_rag = task_data.get('use_rag', False)
            architecture_related = task_data.get('architecture_related', False)

            # Calculate complexity factors
            factors = {}

            # 1. Reasoning Depth (0.0 to 0.3)
            factors['reasoning_depth'] = self._calculate_reasoning_depth(
                content, requirements, architecture_related
            )

            # 2. Code Complexity (0.0 to 0.25)
            factors['code_complexity'] = self._calculate_code_complexity(
                content, requirements, code_lines
            )

            # 3. Context Requirement (0.0 to 0.2)
            factors['context_requirement'] = self._calculate_context_requirement(
                context_size, use_rag
            )

            # 4. Latency Sensitivity (0.0 to 0.15)
            factors['latency_sensitivity'] = self._calculate_latency_sensitivity(
                is_interactive, task_type
            )

            # 5. Domain Specificity (0.0 to 0.1)
            factors['domain_specificity'] = self._calculate_domain_specificity(
                task_data.get('domain_keywords', [])
            )

            # 6. Base task complexity (0.0 to 0.85)
            factors['base_task'] = self.TASK_TYPE_BASE_COMPLEXITY.get(
                task_type, 0.45
            )

            # Calculate total score (weighted average)
            score = (
                factors['reasoning_depth'] * 0.30 +      # 30% - most important
                factors['code_complexity'] * 0.25 +       # 25%
                factors['context_requirement'] * 0.15 +   # 15%
                factors['latency_sensitivity'] * 0.10 +   # 10%
                factors['domain_specificity'] * 0.05 +    # 5%
                factors['base_task'] * 0.15               # 15% - task type baseline
            )

            # Normalize to 0.0-1.0 range
            score = min(1.0, max(0.0, score))

            # Determine complexity level and recommendation
            level, provider, reasoning = self._determine_level_and_provider(
                score, task_type, is_interactive, factors
            )

            # Estimate tokens
            estimated_tokens = self._estimate_tokens(
                content, requirements, code_lines
            )

            return ComplexityAnalysis(
                level=level,
                score=score,
                recommended_provider=provider,
                factors=factors,
                reasoning=reasoning,
                estimated_tokens=estimated_tokens,
                latency_sensitive=is_interactive
            )

        except Exception as e:
            self.logger.error(f"Error analyzing task complexity: {e}")
            # Fallback to moderate complexity
            return ComplexityAnalysis(
                level=ComplexityLevel.MODERATE,
                score=0.5,
                recommended_provider='sonnet',
                factors={'error': 1.0},
                reasoning=f"Error during analysis, using default: {str(e)}",
                estimated_tokens=1000,
                latency_sensitive=True
            )

    def _parse_task_type(self, task_type: Any) -> TaskType:
        """Parse task type from string or enum."""
        if isinstance(task_type, TaskType):
            return task_type
        if isinstance(task_type, str):
            try:
                return TaskType[task_type.upper()]
            except KeyError:
                return TaskType.CHAT_REPLY  # Default
        return TaskType.CHAT_REPLY

    def _calculate_reasoning_depth(
        self, content: str, requirements: str, architecture_related: bool
    ) -> float:
        """Calculate reasoning depth factor (0.0-0.3)."""
        combined = (content + ' ' + requirements).lower()

        # Check for complex keywords
        complex_count = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in combined)
        moderate_count = sum(1 for kw in self.MODERATE_KEYWORDS if kw in combined)
        simple_count = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in combined)

        # Base score from keywords
        if architecture_related or complex_count > 2:
            score = 0.28
        elif moderate_count > 2 or complex_count > 0:
            score = 0.18
        elif simple_count > 3:
            score = 0.05
        else:
            score = 0.12

        # Adjust based on content length (more reasoning needed for longer content)
        content_length = len(combined)
        if content_length > 1000:
            score += 0.05
        elif content_length > 5000:
            score += 0.08

        return min(0.3, score)

    def _calculate_code_complexity(
        self, content: str, requirements: str, code_lines: int
    ) -> float:
        """Calculate code complexity factor (0.0-0.25)."""
        combined = (content + ' ' + requirements).lower()

        # Check for code-related keywords
        code_keywords = {
            'api': 2, 'database': 2, 'microservice': 3, 'rest': 1.5,
            'security': 2, 'authentication': 2, 'encryption': 2,
            'test': 1, 'integration': 2, 'deployment': 1.5,
            'scalability': 2, 'performance': 1.5, 'caching': 1,
            'framework': 1, 'library': 0.5, 'component': 1
        }

        keyword_score = sum(
            code_keywords.get(kw, 1) for kw in code_keywords
            if kw in combined
        ) / 10.0

        # Base on code lines
        if code_lines > 1000:
            score = 0.20
        elif code_lines > 500:
            score = 0.15
        elif code_lines > 100:
            score = 0.10
        else:
            score = keyword_score * 0.25

        return min(0.25, max(keyword_score, score))

    def _calculate_context_requirement(
        self, context_size: int, use_rag: bool
    ) -> float:
        """Calculate context requirement factor (0.0-0.2)."""
        # Small context: < 2KB
        # Medium context: 2KB-20KB
        # Large context: 20KB-100KB
        # Extra large: > 100KB

        if context_size < 2000:
            score = 0.02
        elif context_size < 20000:
            score = 0.08
        elif context_size < 100000:
            score = 0.15
        else:
            score = 0.20

        # Add bonus for RAG (requires better understanding)
        if use_rag and score < 0.15:
            score += 0.05

        return min(0.2, score)

    def _calculate_latency_sensitivity(
        self, is_interactive: bool, task_type: TaskType
    ) -> float:
        """Calculate latency sensitivity factor (0.0-0.15)."""
        # Interactive tasks need fast responses
        if not is_interactive:
            return 0.0

        # Different task types have different latency requirements
        latency_sensitive_tasks = {
            TaskType.CHAT_REPLY: 0.12,            # Very latency sensitive
            TaskType.FOLLOW_UP_QUESTION: 0.10,    # Latency sensitive
            TaskType.SOCRATIC_QUESTIONS: 0.06,    # Somewhat latency sensitive
        }

        return latency_sensitive_tasks.get(task_type, 0.03)

    def _calculate_domain_specificity(self, domain_keywords: List[str]) -> float:
        """Calculate domain specificity factor (0.0-0.1)."""
        if not domain_keywords:
            return 0.0

        # More domain keywords = more specialized
        score = min(0.1, len(domain_keywords) * 0.02)
        return score

    def _determine_level_and_provider(
        self, score: float, task_type: TaskType,
        is_interactive: bool, factors: Dict[str, float]
    ) -> tuple[ComplexityLevel, str, str]:
        """Determine complexity level, recommended provider, and reasoning."""

        # Decision thresholds
        if score < 0.35:
            level = ComplexityLevel.SIMPLE
            if is_interactive and task_type in (TaskType.CHAT_REPLY, TaskType.FOLLOW_UP_QUESTION):
                # Fast response needed
                provider = 'haiku'  # Fastest and cheapest
                reasoning = "Simple task requiring fast response - using Haiku for speed and cost"
            else:
                provider = 'ollama'  # Free, fast local model
                reasoning = "Simple task - using local Ollama for cost efficiency"

        elif score < 0.65:
            level = ComplexityLevel.MODERATE
            provider = 'sonnet'  # Balanced quality and speed
            reasoning = "Moderate complexity - using Sonnet for balanced reasoning and performance"

        else:
            level = ComplexityLevel.COMPLEX
            provider = 'opus'  # Best reasoning for complex tasks
            reasoning = "Complex task requiring sophisticated reasoning - using Opus for quality"

        # Special cases
        if factors.get('latency_sensitivity', 0) > 0.08 and score < 0.5:
            provider = 'haiku'
            reasoning += " (optimized for interactive latency)"

        return level, provider, reasoning

    def _estimate_tokens(
        self, content: str, requirements: str, code_lines: int
    ) -> int:
        """Estimate token count for the task."""
        # Rough estimation: ~4 characters per token
        combined_text = content + ' ' + requirements
        text_tokens = len(combined_text) // 4

        # Code adds tokens
        code_tokens = code_lines // 2  # ~2 tokens per line of code

        # Add overhead for system prompts and responses
        overhead = 500

        return text_tokens + code_tokens + overhead


# Convenience functions

def analyze_task_complexity(task_data: Dict[str, Any]) -> ComplexityAnalysis:
    """
    Analyze task complexity and get provider recommendation.

    Convenience function for quick access.

    Args:
        task_data: Task information dict

    Returns:
        ComplexityAnalysis with recommendation
    """
    analyzer = TaskComplexityAnalyzer()
    return analyzer.analyze(task_data)


def should_use_fast_provider(task_type: str, is_interactive: bool) -> bool:
    """
    Quick check if task should use fast/cheap provider.

    Args:
        task_type: Type of task
        is_interactive: Whether response time is critical

    Returns:
        True if should use fast provider
    """
    analysis = analyze_task_complexity({
        'task_type': task_type,
        'is_interactive': is_interactive
    })
    return analysis.level in (ComplexityLevel.SIMPLE, ComplexityLevel.MODERATE)


__all__ = [
    'TaskComplexityAnalyzer',
    'ComplexityAnalysis',
    'ComplexityLevel',
    'TaskType',
    'analyze_task_complexity',
    'should_use_fast_provider',
]
