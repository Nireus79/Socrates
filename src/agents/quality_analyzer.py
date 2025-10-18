#!/usr/bin/env python3
"""
  - Meta-level Quality Analysis for All Phases
============================================================

Analyzes and validates text across all project phases to detect greedy patterns
and ensure comprehensive requirement coverage. Prevents myopic decisions that bias
toward specific solutions without exploring alternatives.

Works across all phases:
- Socratic Phase: Validates questions for bias and coverage gaps
- Chat Phase: Validates conversational suggestions for quality and completeness
- Code Generation Phase: Validates code suggestions and architectural decisions
- Architecture Phase: Validates design choices and recommendations

Capabilities:
- Detect solution-biased suggestions/questions/statements
- Identify missing requirement coverage
- Calculate diversity and quality scores
- Suggest alternative approaches
- Track requirement coverage gaps
- Validate across all suggestion types

Part of C6 Architecture Optimizer Extension.
"""

from typing import Dict, List, Any, Optional, Set, Union
from enum import Enum
from dataclasses import dataclass, field


class QuestionBias(Enum):
    """Types of question bias that lead to greedy decisions"""
    SOLUTION_BIASED = "solution_biased"  # Question assumes a specific solution
    TECHNOLOGY_BIASED = "technology_biased"  # Question pushes specific tech
    NARROW_SCOPE = "narrow_scope"  # Question too narrow, missing alternatives
    LEADING_QUESTION = "leading_question"  # Question leads to specific answer
    PREMATURE_DETAIL = "premature_detail"  # Too detailed before high-level understanding
    MISSING_ALTERNATIVES = "missing_alternatives"  # Doesn't explore options


class CoverageGap(Enum):
    """Types of requirement coverage gaps"""
    NO_SCALABILITY = "no_scalability"
    NO_SECURITY = "no_security"
    NO_PERFORMANCE = "no_performance"
    NO_MAINTENANCE = "no_maintenance"
    NO_TESTING = "no_testing"
    NO_MONITORING = "no_monitoring"
    NO_ERROR_HANDLING = "no_error_handling"
    NO_DATA_RETENTION = "no_data_retention"
    NO_DISASTER_RECOVERY = "no_disaster_recovery"
    NO_USER_FEEDBACK = "no_user_feedback"


@dataclass
class QuestionAnalysis:
    """Analysis result for a single question"""
    question_id: str
    question_text: str
    bias_detected: Optional[QuestionBias]
    bias_score: float  # 0.0 = no bias, 1.0 = highly biased
    bias_explanation: str
    suggested_alternatives: List[str]
    coverage_areas: List[str]  # What requirement areas this question covers
    quality_score: float  # 0.0 to 1.0


@dataclass
class SessionAnalysis:
    """Analysis result for entire questioning session"""
    session_id: str
    total_questions: int
    biased_questions: int
    diversity_score: float  # 0.0 to 1.0
    coverage_gaps: List[CoverageGap]
    requirement_coverage: Dict[str, float]  # Area -> coverage percentage
    recommendations: List[str]
    suggested_questions: List[Dict[str, Any]]
    overall_quality: float  # 0.0 to 1.0


@dataclass
class SuggestionAnalysis:
    """Analysis result for a single suggestion (code, architecture, approach)"""
    suggestion_id: str
    suggestion_text: str
    suggestion_type: str  # 'code', 'architecture', 'approach', 'recommendation'
    bias_detected: Optional[QuestionBias]
    bias_score: float  # 0.0 = no bias, 1.0 = highly biased
    bias_explanation: str
    coverage_areas: List[str]
    quality_score: float  # 0.0 to 1.0
    confidence_level: str  # 'verified', 'assumed', 'speculative'
    missing_context: List[str]  # What information is missing
    suggested_improvements: List[str]


@dataclass
class AnalysisSession:
    """Analysis result for entire session of suggestions/statements"""
    session_id: str
    session_type: str  # 'socratic', 'chat', 'code_review', 'architecture'
    total_items: int
    biased_items: int
    diversity_score: float
    coverage_gaps: List[CoverageGap]
    requirement_coverage: Dict[str, float]
    recommendations: List[str]
    overall_quality: float
    analysis_items: List[Union[QuestionAnalysis, SuggestionAnalysis]] = field(default_factory=list)


class QualityAnalyzer:
    """
    Analyzes quality across all phases: questions, suggestions, statements, code changes.
    Detects greedy patterns, solution bias, coverage gaps, and ensures comprehensive analysis.

    This is a universal quality validator that works across:
    - Socratic questioning (original capability)
    - Chat conversations (new)
    - Code suggestions (new)
    - Architecture decisions (new)
    - Any text-based recommendation or statement
    """

    def __init__(self):
        """Initialize analyzer with bias detection patterns"""

        # Patterns that indicate solution bias
        self.solution_bias_patterns = [
            'using', 'with', 'implement', 'build with', 'use',
            'mongodb', 'postgresql', 'mysql', 'react', 'angular',
            'microservices', 'monolith', 'docker', 'kubernetes'
        ]

        # Patterns that indicate technology bias
        self.technology_bias_patterns = [
            'should we use', 'can we use', 'will you use',
            'technology stack', 'framework', 'library',
            'which database', 'which language'
        ]

        # Patterns that indicate leading questions
        self.leading_patterns = [
            'dont you think', 'wouldnt it be better', 'shouldnt we',
            'isnt it obvious', 'clearly', 'obviously'
        ]

        # Required coverage areas
        self.required_coverage_areas = {
            'scalability': [
                'scale', 'scalability', 'growth', 'users', 'load', 'concurrent',
                'traffic', 'volume', 'capacity'
            ],
            'security': [
                'security', 'authentication', 'authorization', 'encrypt',
                'privacy', 'compliance', 'audit', 'access control'
            ],
            'performance': [
                'performance', 'speed', 'latency', 'response time',
                'throughput', 'optimization', 'cache'
            ],
            'maintenance': [
                'maintenance', 'support', 'update', 'upgrade',
                'documentation', 'team', 'handoff', 'knowledge transfer'
            ],
            'testing': [
                'test', 'quality', 'validation', 'verification',
                'qa', 'automated testing', 'integration test'
            ],
            'monitoring': [
                'monitor', 'logging', 'metrics', 'observability',
                'alerting', 'tracking', 'telemetry'
            ],
            'error_handling': [
                'error', 'exception', 'failure', 'fallback',
                'retry', 'timeout', 'edge case'
            ],
            'data_retention': [
                'data retention', 'backup', 'archive', 'storage',
                'data lifecycle', 'cleanup', 'purge'
            ],
            'disaster_recovery': [
                'disaster recovery', 'failover', 'redundancy',
                'backup', 'restore', 'business continuity'
            ],
            'user_feedback': [
                'user feedback', 'analytics', 'metrics', 'behavior',
                'satisfaction', 'usability', 'user research'
            ]
        }

        # High-level questions that should be asked first
        self.foundational_questions = [
            "What problem are you solving?",
            "Who are the users?",
            "What does success look like?",
            "What are the constraints?",
            "What is the expected scale?"
        ]

    def analyze_question(self, question: Dict[str, Any]) -> QuestionAnalysis:
        """
        Analyze a single question for bias and quality

        Args:
            question: Dict with 'id', 'text', 'role', 'type', etc.

        Returns:
            QuestionAnalysis with bias detection and suggestions
        """
        question_id = question.get('id', '')
        question_text = question.get('text', '').lower()

        # Detect bias
        bias_detected = None
        bias_score = 0.0
        bias_explanation = ""

        # Check for solution bias
        solution_bias_count = sum(
            1 for pattern in self.solution_bias_patterns
            if pattern in question_text
        )
        if solution_bias_count > 0:
            bias_detected = QuestionBias.SOLUTION_BIASED
            bias_score = min(1.0, solution_bias_count * 0.3)
            bias_explanation = (
                f"Question assumes specific solution/technology. "
                f"Found {solution_bias_count} solution-specific terms."
            )

        # Check for technology bias
        tech_bias_count = sum(
            1 for pattern in self.technology_bias_patterns
            if pattern in question_text
        )
        if tech_bias_count > 0 and bias_score < 0.5:
            bias_detected = QuestionBias.TECHNOLOGY_BIASED
            bias_score = max(bias_score, min(1.0, tech_bias_count * 0.4))
            bias_explanation = (
                f"Question biases toward specific technology choice. "
                f"Found {tech_bias_count} technology-specific patterns."
            )

        # Check for leading questions
        leading_count = sum(
            1 for pattern in self.leading_patterns
            if pattern in question_text
        )
        if leading_count > 0 and bias_score < 0.6:
            bias_detected = QuestionBias.LEADING_QUESTION
            bias_score = max(bias_score, min(1.0, leading_count * 0.5))
            bias_explanation = (
                f"Question leads respondent toward specific answer. "
                f"Found {leading_count} leading patterns."
            )

        # Calculate quality score (inverse of bias)
        quality_score = max(0.0, 1.0 - bias_score)

        # Determine coverage areas
        coverage_areas = self._determine_coverage_areas(question_text)

        # Generate alternative questions if biased
        suggested_alternatives = []
        if bias_score > 0.4:
            suggested_alternatives = self._generate_alternative_questions(
                question_text, bias_detected, coverage_areas
            )

        return QuestionAnalysis(
            question_id=question_id,
            question_text=question.get('text', ''),
            bias_detected=bias_detected,
            bias_score=bias_score,
            bias_explanation=bias_explanation if bias_detected else "No significant bias detected",
            suggested_alternatives=suggested_alternatives,
            coverage_areas=coverage_areas,
            quality_score=quality_score
        )

    def analyze_session(
        self,
        session_id: str,
        questions: List[Dict[str, Any]],
        responses: Optional[List[Dict[str, Any]]] = None
    ) -> SessionAnalysis:
        """
        Analyze entire questioning session for greedy patterns

        Args:
            session_id: Session identifier
            questions: List of questions asked
            responses: Optional list of user responses

        Returns:
            SessionAnalysis with comprehensive session assessment
        """
        # Analyze each question
        question_analyses = [
            self.analyze_question(q) for q in questions
        ]

        # Count biased questions
        biased_questions = [
            qa for qa in question_analyses
            if qa.bias_score > 0.4
        ]

        # Calculate diversity score
        diversity_score = self._calculate_diversity_score(question_analyses)

        # Identify coverage gaps
        coverage_gaps = self._identify_coverage_gaps(question_analyses)

        # Calculate requirement coverage
        requirement_coverage = self._calculate_requirement_coverage(question_analyses)

        # Generate recommendations
        recommendations = self._generate_session_recommendations(
            question_analyses, coverage_gaps, diversity_score
        )

        # Suggest additional questions for gaps
        suggested_questions = self._suggest_gap_filling_questions(coverage_gaps)

        # Calculate overall quality
        avg_quality = sum(qa.quality_score for qa in question_analyses) / max(len(question_analyses), 1)
        coverage_quality = sum(requirement_coverage.values()) / max(len(requirement_coverage), 1)
        overall_quality = (avg_quality * 0.6) + (diversity_score * 0.2) + (coverage_quality * 0.2)

        return SessionAnalysis(
            session_id=session_id,
            total_questions=len(questions),
            biased_questions=len(biased_questions),
            diversity_score=diversity_score,
            coverage_gaps=coverage_gaps,
            requirement_coverage=requirement_coverage,
            recommendations=recommendations,
            suggested_questions=suggested_questions,
            overall_quality=overall_quality
        )

    def _determine_coverage_areas(self, question_text: str) -> List[str]:
        """Determine which requirement areas a question covers"""
        coverage = []

        for area, keywords in self.required_coverage_areas.items():
            if any(keyword in question_text for keyword in keywords):
                coverage.append(area)

        return coverage

    def _calculate_diversity_score(self, analyses: List[QuestionAnalysis]) -> float:
        """
        Calculate diversity score based on coverage breadth

        High score = questions cover many different areas
        Low score = questions focus on narrow area (greedy)
        """
        if not analyses:
            return 0.0

        # Count unique coverage areas
        all_coverage_areas: Set[str] = set()
        for analysis in analyses:
            all_coverage_areas.update(analysis.coverage_areas)

        # Ideal: cover all required areas
        total_required = len(self.required_coverage_areas)
        covered = len(all_coverage_areas)

        # Base diversity on breadth of coverage
        diversity = covered / total_required

        # Penalty if too many biased questions
        bias_penalty = sum(1 for a in analyses if a.bias_score > 0.4) / len(analyses)
        diversity = diversity * (1.0 - (bias_penalty * 0.5))

        return round(diversity, 2)

    def _identify_coverage_gaps(self, analyses: List[QuestionAnalysis]) -> List[CoverageGap]:
        """Identify which requirement areas are not covered"""
        covered_areas = set()
        for analysis in analyses:
            covered_areas.update(analysis.coverage_areas)

        gaps = []

        if 'scalability' not in covered_areas:
            gaps.append(CoverageGap.NO_SCALABILITY)
        if 'security' not in covered_areas:
            gaps.append(CoverageGap.NO_SECURITY)
        if 'performance' not in covered_areas:
            gaps.append(CoverageGap.NO_PERFORMANCE)
        if 'maintenance' not in covered_areas:
            gaps.append(CoverageGap.NO_MAINTENANCE)
        if 'testing' not in covered_areas:
            gaps.append(CoverageGap.NO_TESTING)
        if 'monitoring' not in covered_areas:
            gaps.append(CoverageGap.NO_MONITORING)
        if 'error_handling' not in covered_areas:
            gaps.append(CoverageGap.NO_ERROR_HANDLING)
        if 'data_retention' not in covered_areas:
            gaps.append(CoverageGap.NO_DATA_RETENTION)
        if 'disaster_recovery' not in covered_areas:
            gaps.append(CoverageGap.NO_DISASTER_RECOVERY)
        if 'user_feedback' not in covered_areas:
            gaps.append(CoverageGap.NO_USER_FEEDBACK)

        return gaps

    def _calculate_requirement_coverage(self, analyses: List[QuestionAnalysis]) -> Dict[str, float]:
        """Calculate coverage percentage for each requirement area"""
        coverage = {area: 0.0 for area in self.required_coverage_areas.keys()}

        for analysis in analyses:
            for area in analysis.coverage_areas:
                if area in coverage:
                    # Each question adds to coverage, max 1.0
                    coverage[area] = min(1.0, coverage[area] + 0.25)

        return coverage

    def _generate_session_recommendations(
        self,
        analyses: List[QuestionAnalysis],
        gaps: List[CoverageGap],
        diversity_score: float
    ) -> List[str]:
        """Generate recommendations for improving the session"""
        recommendations = []

        # Check for high bias
        high_bias_count = sum(1 for a in analyses if a.bias_score > 0.6)
        if high_bias_count > 0:
            recommendations.append(
                f"⚠️ {high_bias_count} questions show high solution bias. "
                f"Consider asking more open-ended questions before diving into solutions."
            )

        # Check diversity
        if diversity_score < 0.5:
            recommendations.append(
                f"⚠️ Low diversity score ({diversity_score:.2f}). "
                f"Questions focus too narrowly - expand to other requirement areas."
            )

        # Check critical gaps
        critical_gaps = [
            CoverageGap.NO_SECURITY,
            CoverageGap.NO_SCALABILITY,
            CoverageGap.NO_ERROR_HANDLING
        ]
        found_critical = [g for g in gaps if g in critical_gaps]

        if found_critical:
            gap_names = [g.value.replace('_', ' ') for g in found_critical]
            recommendations.append(
                f"🚨 CRITICAL: Missing coverage for {', '.join(gap_names)}. "
                f"These areas often cause costly rework if not addressed early."
            )

        # Check for premature detail
        if len(analyses) > 3:
            first_three = analyses[:3]
            detailed_early = sum(1 for a in first_three if len(a.question_text.split()) > 20)
            if detailed_early >= 2:
                recommendations.append(
                    "⚠️ Questions became detailed too quickly. "
                    "Start with high-level questions before diving into specifics."
                )

        # Positive feedback
        if diversity_score >= 0.7 and len(gaps) <= 3:
            recommendations.append(
                "✅ Good question diversity and coverage. Session is comprehensive."
            )

        return recommendations

    def _suggest_gap_filling_questions(self, gaps: List[CoverageGap]) -> List[Dict[str, Any]]:
        """Suggest questions to fill coverage gaps"""
        gap_questions = {
            CoverageGap.NO_SCALABILITY: {
                'text': "What is the expected user growth over the next 1-2 years, and how should the system scale?",
                'priority': 'critical',
                'estimated_hours_saved': 30
            },
            CoverageGap.NO_SECURITY: {
                'text': "What security and compliance requirements must the system meet?",
                'priority': 'critical',
                'estimated_hours_saved': 80
            },
            CoverageGap.NO_PERFORMANCE: {
                'text': "What are the acceptable response times and throughput requirements for key operations?",
                'priority': 'high',
                'estimated_hours_saved': 25
            },
            CoverageGap.NO_MAINTENANCE: {
                'text': "How will the system be maintained and updated after launch? What's the team structure?",
                'priority': 'high',
                'estimated_hours_saved': 15
            },
            CoverageGap.NO_TESTING: {
                'text': "What testing strategy and quality assurance processes should be in place?",
                'priority': 'high',
                'estimated_hours_saved': 50
            },
            CoverageGap.NO_MONITORING: {
                'text': "What monitoring, logging, and alerting capabilities are needed?",
                'priority': 'medium',
                'estimated_hours_saved': 20
            },
            CoverageGap.NO_ERROR_HANDLING: {
                'text': "How should the system handle errors, failures, and edge cases?",
                'priority': 'high',
                'estimated_hours_saved': 30
            },
            CoverageGap.NO_DATA_RETENTION: {
                'text': "What are the data retention, backup, and archival requirements?",
                'priority': 'medium',
                'estimated_hours_saved': 10
            },
            CoverageGap.NO_DISASTER_RECOVERY: {
                'text': "What disaster recovery and business continuity requirements exist?",
                'priority': 'medium',
                'estimated_hours_saved': 25
            },
            CoverageGap.NO_USER_FEEDBACK: {
                'text': "How will user feedback and analytics be collected to improve the system?",
                'priority': 'low',
                'estimated_hours_saved': 5
            }
        }

        suggested = []
        for gap in gaps:
            if gap in gap_questions:
                question_data = gap_questions[gap].copy()
                question_data['gap'] = gap.value
                question_data['reason'] = f"Missing {gap.value.replace('_', ' ')} coverage"
                suggested.append(question_data)

        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        suggested.sort(key=lambda q: priority_order.get(q['priority'], 99))

        return suggested

    def _generate_alternative_questions(
        self,
        biased_question: str,
        bias_type: Optional[QuestionBias],
        coverage_areas: List[str]
    ) -> List[str]:
        """Generate alternative, less biased questions"""
        alternatives = []

        if bias_type == QuestionBias.SOLUTION_BIASED:
            alternatives.append(
                "What approaches have you considered for solving this problem?"
            )
            alternatives.append(
                "What are the key requirements that any solution must meet?"
            )

        elif bias_type == QuestionBias.TECHNOLOGY_BIASED:
            alternatives.append(
                "What technical requirements and constraints should guide technology choices?"
            )
            alternatives.append(
                "What technologies is your team already experienced with?"
            )

        elif bias_type == QuestionBias.LEADING_QUESTION:
            alternatives.append(
                "What are your thoughts on this approach?"
            )
            alternatives.append(
                "What considerations are most important for this decision?"
            )

        return alternatives

    # ========================================================================
    # NEW METHODS FOR EXTENDED PHASES (Chat, Code, Architecture)
    # ========================================================================

    def analyze_suggestion(
        self,
        suggestion: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> SuggestionAnalysis:
        """
        Analyze a code/architecture/approach suggestion for bias and quality.

        Args:
            suggestion: Dict with 'id', 'text', 'type', 'context' (optional)
            context: Optional context about the project/decision

        Returns:
            SuggestionAnalysis with bias detection and quality assessment
        """
        suggestion_id = suggestion.get('id', '')
        suggestion_text = suggestion.get('text', '').lower()
        suggestion_type = suggestion.get('type', 'unknown')

        # Detect bias (reuse existing logic)
        bias_detected = None
        bias_score = 0.0
        bias_explanation = ""

        # Check for solution bias
        solution_bias_count = sum(
            1 for pattern in self.solution_bias_patterns
            if pattern in suggestion_text
        )
        if solution_bias_count > 0:
            bias_detected = QuestionBias.SOLUTION_BIASED
            bias_score = min(1.0, solution_bias_count * 0.3)
            bias_explanation = (
                f"Suggestion assumes specific solution/technology. "
                f"Found {solution_bias_count} solution-specific terms."
            )

        # Check for technology bias
        tech_bias_count = sum(
            1 for pattern in self.technology_bias_patterns
            if pattern in suggestion_text
        )
        if tech_bias_count > 0 and bias_score < 0.5:
            bias_detected = QuestionBias.TECHNOLOGY_BIASED
            bias_score = max(bias_score, min(1.0, tech_bias_count * 0.4))
            bias_explanation = (
                f"Suggestion biases toward specific technology choice. "
                f"Found {tech_bias_count} technology-specific patterns."
            )

        # Calculate quality score
        quality_score = max(0.0, 1.0 - bias_score)

        # Determine coverage areas
        coverage_areas = self._determine_coverage_areas(suggestion_text)

        # Detect confidence level (based on context/verification)
        confidence_level = self._assess_confidence_level(suggestion, context)

        # Identify missing context
        missing_context = self._identify_missing_context(suggestion_type, coverage_areas)

        # Generate improvements if biased
        suggested_improvements = []
        if bias_score > 0.4:
            suggested_improvements = self._generate_alternative_suggestions(
                suggestion_text, bias_detected, suggestion_type
            )

        return SuggestionAnalysis(
            suggestion_id=suggestion_id,
            suggestion_text=suggestion.get('text', ''),
            suggestion_type=suggestion_type,
            bias_detected=bias_detected,
            bias_score=bias_score,
            bias_explanation=bias_explanation if bias_detected else "No significant bias detected",
            coverage_areas=coverage_areas,
            quality_score=quality_score,
            confidence_level=confidence_level,
            missing_context=missing_context,
            suggested_improvements=suggested_improvements
        )

    def analyze_statement(
        self,
        statement: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> SuggestionAnalysis:
        """
        Analyze a chat statement or recommendation for quality and completeness.

        Args:
            statement: Dict with 'id', 'text', 'author', 'timestamp'
            context: Optional context about the conversation

        Returns:
            SuggestionAnalysis adapted for statement evaluation
        """
        # Reuse suggestion analysis with 'statement' type
        statement_as_suggestion = {
            'id': statement.get('id', ''),
            'text': statement.get('text', ''),
            'type': 'statement'
        }
        return self.analyze_suggestion(statement_as_suggestion, context)

    def analyze_code_change(
        self,
        code_change: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> SuggestionAnalysis:
        """
        Analyze a proposed code change for architecture quality and bias.

        Args:
            code_change: Dict with 'id', 'description', 'code', 'rationale'
            context: Optional context about the codebase

        Returns:
            SuggestionAnalysis focused on architectural concerns
        """
        # Combine description and rationale for analysis
        text = f"{code_change.get('description', '')} {code_change.get('rationale', '')}"

        code_as_suggestion = {
            'id': code_change.get('id', ''),
            'text': text,
            'type': 'code_change'
        }

        analysis = self.analyze_suggestion(code_as_suggestion, context)

        # Add code-specific checks
        code_text = code_change.get('code', '').lower()
        code_specific_issues = self._check_code_quality_patterns(code_text)

        if code_specific_issues:
            analysis.suggested_improvements.extend(code_specific_issues)

        return analysis

    def _assess_confidence_level(
        self,
        suggestion: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Assess confidence level based on whether suggestion is verified or assumed.

        Returns: 'verified', 'assumed', or 'speculative'
        """
        # If context is provided, it's likely verified
        if context and context.get('verified', False):
            return 'verified'

        # If suggestion includes evidence/reference, it's likely verified
        if suggestion.get('evidence') or suggestion.get('reference'):
            return 'verified'

        # If suggestion mentions assumptions, it's speculative
        text = suggestion.get('text', '').lower()
        if any(word in text for word in ['might', 'could', 'may', 'possibly', 'probably']):
            return 'speculative'

        # Default to assumed (most suggestions without verification)
        return 'assumed'

    def _identify_missing_context(
        self,
        suggestion_type: str,
        coverage_areas: List[str]
    ) -> List[str]:
        """Identify what context/information is missing from a suggestion."""
        missing = []

        # Check coverage gaps
        all_areas = set(self.required_coverage_areas.keys())
        covered = set(coverage_areas)
        gaps = all_areas - covered

        if gaps:
            missing.append(f"Missing coverage areas: {', '.join(sorted(gaps))}")

        # Type-specific checks
        if suggestion_type == 'code_change':
            if 'testing' not in coverage_areas:
                missing.append("No mention of testing strategy or test coverage")
            if 'error_handling' not in coverage_areas:
                missing.append("No mention of error handling or edge cases")

        elif suggestion_type == 'architecture':
            if 'scalability' not in coverage_areas:
                missing.append("No mention of scalability requirements")
            if 'security' not in coverage_areas:
                missing.append("No mention of security/compliance requirements")

        return missing

    def _generate_alternative_suggestions(
        self,
        biased_suggestion: str,
        bias_type: Optional[QuestionBias],
        suggestion_type: str
    ) -> List[str]:
        """Generate alternative, less biased suggestions."""
        alternatives = []

        if bias_type == QuestionBias.SOLUTION_BIASED:
            alternatives.append(
                f"Consider exploring multiple approaches to {suggestion_type}. "
                f"What are the key requirements that must be met?"
            )
            alternatives.append(
                "What trade-offs exist between different solutions?"
            )

        elif bias_type == QuestionBias.TECHNOLOGY_BIASED:
            alternatives.append(
                "What technical requirements and constraints should guide technology choices?"
            )
            alternatives.append(
                "Consider technologies the team is experienced with. "
                f"What are the compatibility requirements for {suggestion_type}?"
            )

        return alternatives

    def _check_code_quality_patterns(self, code_text: str) -> List[str]:
        """Check for code-specific quality issues."""
        issues = []

        # Check for bare except
        if 'except:' in code_text:
            issues.append("Code uses bare except clause - should catch specific exceptions")

        # Check for hardcoded values
        if any(f"'{i}'" in code_text or f'"{i}"' in code_text for i in range(10, 1000)):
            issues.append("Code may contain hardcoded values - consider parameterization")

        # Check for TODO/FIXME
        if 'todo' in code_text or 'fixme' in code_text:
            issues.append("Code contains TODO/FIXME comments - incomplete implementation")

        return issues


# ============================================================================
# BACKWARD COMPATIBILITY ALIAS
# ============================================================================

# Keep old name for backward compatibility
QuestionQualityAnalyzer = QualityAnalyzer


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # New names (preferred)
    'QualityAnalyzer',
    'SuggestionAnalysis',
    'AnalysisSession',
    'QuestionAnalysis',
    'SessionAnalysis',
    'QuestionBias',
    'CoverageGap',
    # Backward compatibility
    'QuestionQualityAnalyzer'
]
