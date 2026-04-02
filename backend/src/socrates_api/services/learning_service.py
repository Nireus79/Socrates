"""
Learning Service - Phase 6

Analyzes question effectiveness and learns from answer patterns.
Uses insights to optimize future question generation and ordering.

Key Features:
- Question effectiveness scoring
- Answer pattern detection
- Learning curve analysis
- Question optimization recommendations
- Future question improvement
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class QuestionEffectiveness:
    """Score for question effectiveness."""
    question_id: str
    text: str
    effectiveness_score: float  # 0-1
    gaps_addressed: int
    answer_quality: float
    impact_score: float
    times_asked: int
    success_rate: float


@dataclass
class AnswerPattern:
    """Pattern detected in answers."""
    pattern_name: str
    frequency: int  # How often this pattern appears
    typical_gaps_addressed: List[str]
    average_quality: float
    examples: List[str]


@dataclass
class LearningCurve:
    """Learning curve analysis."""
    metric_name: str
    phase: str
    initial_value: float
    current_value: float
    improvement_rate: float  # per day
    projected_plateau: float
    questions_to_plateau: int


@dataclass
class OptimizationRecommendation:
    """Recommendation for question optimization."""
    recommendation_type: str  # ordering, rewording, removal, addition
    question_id: Optional[str]
    current_metric: str
    target_metric: str
    confidence: float  # 0-1
    reasoning: str
    priority: str  # high, medium, low


# ============================================================================
# Learning Service
# ============================================================================

class LearningService:
    """
    Learns from question answering patterns and optimizes future questions.

    Responsibilities:
    - Score question effectiveness
    - Detect answer patterns
    - Analyze learning curves
    - Generate optimization recommendations
    - Track improvement over time
    """

    def __init__(self):
        """Initialize the Learning Service."""
        self._question_effectiveness_cache: Dict[str, QuestionEffectiveness] = {}
        self._answer_patterns_cache: Dict[str, List[AnswerPattern]] = {}
        self._learning_curves_cache: Dict[str, LearningCurve] = {}
        self._optimization_cache: Dict[str, List[OptimizationRecommendation]] = {}

        # Question tracking
        self._question_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        logger.info("Learning Service initialized")

    # ========================================================================
    # Question Effectiveness Scoring
    # ========================================================================

    def score_question_effectiveness(
        self,
        question_id: str,
        question_text: str,
        answer_text: str,
        gaps_addressed: int,
        answer_quality: float,
        times_asked: int = 1
    ) -> QuestionEffectiveness:
        """
        Score how effective a question is at generating useful answers.

        Factors:
        - Answer quality (0-1)
        - Gaps addressed (count)
        - Answer length and specificity
        - Success rate (% of good answers)

        Args:
            question_id: Question identifier
            question_text: The question text
            answer_text: The answer provided
            gaps_addressed: Number of gaps this answer addresses
            answer_quality: Quality of answer (0-1)
            times_asked: How many times this question has been asked

        Returns:
            QuestionEffectiveness score
        """
        try:
            # Calculate impact score
            impact_score = (answer_quality * 0.6) + (gaps_addressed / max(gaps_addressed, 5) * 0.4)
            impact_score = min(1.0, impact_score)

            # Calculate success rate
            question_data = self._question_history.get(question_id, [])
            successful = sum(1 for q in question_data if q.get("quality", 0) > 0.6)
            success_rate = successful / max(times_asked, 1)

            # Overall effectiveness
            effectiveness_score = (
                impact_score * 0.5 +
                success_rate * 0.3 +
                answer_quality * 0.2
            )

            effectiveness = QuestionEffectiveness(
                question_id=question_id,
                text=question_text,
                effectiveness_score=min(1.0, effectiveness_score),
                gaps_addressed=gaps_addressed,
                answer_quality=answer_quality,
                impact_score=impact_score,
                times_asked=times_asked,
                success_rate=success_rate
            )

            # Cache and track
            self._question_effectiveness_cache[question_id] = effectiveness
            self._track_question(question_id, answer_text, answer_quality, gaps_addressed)

            logger.debug(
                f"Question effectiveness scored: {question_id} = "
                f"{effectiveness_score:.2f} (quality={answer_quality:.2f}, gaps={gaps_addressed})"
            )

            return effectiveness

        except Exception as e:
            logger.error(f"Error scoring question effectiveness: {e}")
            return QuestionEffectiveness(
                question_id=question_id,
                text=question_text,
                effectiveness_score=0.5,
                gaps_addressed=0,
                answer_quality=answer_quality,
                impact_score=0.0,
                times_asked=times_asked,
                success_rate=0.0
            )

    def _track_question(
        self,
        question_id: str,
        answer_text: str,
        quality: float,
        gaps: int
    ) -> None:
        """Track question usage and answers."""
        self._question_history[question_id].append({
            "timestamp": datetime.now().isoformat(),
            "answer": answer_text[:500],  # First 500 chars
            "quality": quality,
            "gaps": gaps
        })

        # Keep only last 100 attempts
        if len(self._question_history[question_id]) > 100:
            self._question_history[question_id] = self._question_history[question_id][-100:]

    def get_most_effective_questions(
        self,
        project_id: str,
        top_k: int = 10
    ) -> List[QuestionEffectiveness]:
        """
        Get the most effective questions for a project.

        Args:
            project_id: Project identifier
            top_k: Number of top questions to return

        Returns:
            List of QuestionEffectiveness sorted by score
        """
        try:
            questions = list(self._question_effectiveness_cache.values())

            if not questions:
                return []

            # Sort by effectiveness score
            sorted_questions = sorted(
                questions,
                key=lambda q: q.effectiveness_score,
                reverse=True
            )

            logger.debug(f"Retrieved top {len(sorted_questions[:top_k])} effective questions")

            return sorted_questions[:top_k]

        except Exception as e:
            logger.error(f"Error getting most effective questions: {e}")
            return []

    # ========================================================================
    # Answer Pattern Detection
    # ========================================================================

    def detect_answer_patterns(
        self,
        project_id: str,
        answers: List[Dict[str, Any]]
    ) -> List[AnswerPattern]:
        """
        Detect common patterns in answers.

        Patterns:
        - Technical vs business focus
        - Detailed vs high-level
        - Specific examples provided
        - Completeness
        - Reference to documentation

        Args:
            project_id: Project identifier
            answers: List of answer dictionaries

        Returns:
            List of detected patterns
        """
        try:
            patterns = []

            # Pattern 1: Answer length distribution
            length_pattern = self._detect_length_pattern(answers)
            if length_pattern:
                patterns.append(length_pattern)

            # Pattern 2: Technical vs business focus
            focus_pattern = self._detect_focus_pattern(answers)
            if focus_pattern:
                patterns.append(focus_pattern)

            # Pattern 3: Example usage
            example_pattern = self._detect_example_pattern(answers)
            if example_pattern:
                patterns.append(example_pattern)

            # Pattern 4: Reference pattern
            reference_pattern = self._detect_reference_pattern(answers)
            if reference_pattern:
                patterns.append(reference_pattern)

            # Pattern 5: Completeness pattern
            completeness_pattern = self._detect_completeness_pattern(answers)
            if completeness_pattern:
                patterns.append(completeness_pattern)

            # Cache
            self._answer_patterns_cache[project_id] = patterns

            logger.debug(f"Detected {len(patterns)} answer patterns for {project_id}")

            return patterns

        except Exception as e:
            logger.error(f"Error detecting answer patterns: {e}")
            return []

    def _detect_length_pattern(self, answers: List[Dict[str, Any]]) -> Optional[AnswerPattern]:
        """Detect answer length distribution pattern."""
        if not answers:
            return None

        lengths = [len(a.get("text", "")) for a in answers]
        avg_length = sum(lengths) / len(lengths) if lengths else 0

        if avg_length > 500:
            return AnswerPattern(
                pattern_name="long_detailed_answers",
                frequency=sum(1 for l in lengths if l > 500),
                typical_gaps_addressed=["complex_requirements", "architecture"],
                average_quality=0.8,
                examples=[]
            )
        elif avg_length < 200:
            return AnswerPattern(
                pattern_name="short_concise_answers",
                frequency=sum(1 for l in lengths if l < 200),
                typical_gaps_addressed=["simple_decisions"],
                average_quality=0.6,
                examples=[]
            )
        else:
            return AnswerPattern(
                pattern_name="medium_balanced_answers",
                frequency=len(answers),
                typical_gaps_addressed=["general_requirements"],
                average_quality=0.7,
                examples=[]
            )

    def _detect_focus_pattern(self, answers: List[Dict[str, Any]]) -> Optional[AnswerPattern]:
        """Detect technical vs business focus pattern."""
        if not answers:
            return None

        technical_keywords = ["api", "database", "code", "implementation", "technical"]
        business_keywords = ["goal", "user", "requirement", "business", "stakeholder"]

        technical_count = 0
        business_count = 0

        for answer in answers:
            text = answer.get("text", "").lower()
            technical_count += sum(1 for kw in technical_keywords if kw in text)
            business_count += sum(1 for kw in business_keywords if kw in text)

        if technical_count > business_count:
            return AnswerPattern(
                pattern_name="technical_focus",
                frequency=len(answers),
                typical_gaps_addressed=["architecture", "implementation"],
                average_quality=0.75,
                examples=[]
            )
        elif business_count > technical_count:
            return AnswerPattern(
                pattern_name="business_focus",
                frequency=len(answers),
                typical_gaps_addressed=["requirements", "goals"],
                average_quality=0.75,
                examples=[]
            )

        return None

    def _detect_example_pattern(self, answers: List[Dict[str, Any]]) -> Optional[AnswerPattern]:
        """Detect usage of examples pattern."""
        if not answers:
            return None

        with_examples = sum(
            1 for a in answers
            if "example" in a.get("text", "").lower() or "e.g." in a.get("text", "")
        )

        if with_examples / len(answers) > 0.5:
            return AnswerPattern(
                pattern_name="example_based",
                frequency=with_examples,
                typical_gaps_addressed=["implementation", "design"],
                average_quality=0.85,
                examples=[]
            )

        return None

    def _detect_reference_pattern(self, answers: List[Dict[str, Any]]) -> Optional[AnswerPattern]:
        """Detect documentation/reference pattern."""
        if not answers:
            return None

        with_references = sum(
            1 for a in answers
            if any(ref in a.get("text", "").lower() for ref in ["documentation", "guide", "reference", "spec"])
        )

        if with_references / len(answers) > 0.3:
            return AnswerPattern(
                pattern_name="reference_based",
                frequency=with_references,
                typical_gaps_addressed=["compliance", "standards"],
                average_quality=0.8,
                examples=[]
            )

        return None

    def _detect_completeness_pattern(self, answers: List[Dict[str, Any]]) -> Optional[AnswerPattern]:
        """Detect completeness/comprehensive pattern."""
        if not answers:
            return None

        comprehensive_indicators = ["all", "everything", "complete", "comprehensive", "covers"]
        comprehensive_count = sum(
            1 for a in answers
            if any(ind in a.get("text", "").lower() for ind in comprehensive_indicators)
        )

        if comprehensive_count / len(answers) > 0.4:
            return AnswerPattern(
                pattern_name="comprehensive",
                frequency=comprehensive_count,
                typical_gaps_addressed=["architecture", "requirements"],
                average_quality=0.82,
                examples=[]
            )

        return None

    # ========================================================================
    # Learning Curve Analysis
    # ========================================================================

    def analyze_learning_curve(
        self,
        project_id: str,
        phase: str,
        metric_values: List[float],
        timestamps: List[str]
    ) -> LearningCurve:
        """
        Analyze learning curve for a metric.

        Shows how a metric improves over time in a phase.

        Args:
            project_id: Project identifier
            phase: Project phase
            metric_values: Historical metric values
            timestamps: Corresponding timestamps

        Returns:
            LearningCurve analysis
        """
        try:
            if len(metric_values) < 2:
                return LearningCurve(
                    metric_name="unknown",
                    phase=phase,
                    initial_value=metric_values[0] if metric_values else 0,
                    current_value=metric_values[-1] if metric_values else 0,
                    improvement_rate=0.0,
                    projected_plateau=metric_values[-1] if metric_values else 0,
                    questions_to_plateau=0
                )

            initial = metric_values[0]
            current = metric_values[-1]
            improvement = current - initial

            # Calculate improvement rate (per day)
            try:
                first_time = datetime.fromisoformat(timestamps[0])
                last_time = datetime.fromisoformat(timestamps[-1])
                days = max((last_time - first_time).days, 1)
                improvement_rate = improvement / days
            except:
                improvement_rate = improvement

            # Project plateau (asymptotic limit)
            projected_plateau = min(1.0, current + (improvement * 0.3))

            # Estimate questions to plateau
            if improvement_rate > 0:
                questions_to_plateau = int((projected_plateau - current) / max(improvement_rate, 0.01))
            else:
                questions_to_plateau = 0

            curve = LearningCurve(
                metric_name=f"{phase}_metric",
                phase=phase,
                initial_value=initial,
                current_value=current,
                improvement_rate=improvement_rate,
                projected_plateau=projected_plateau,
                questions_to_plateau=max(0, questions_to_plateau)
            )

            # Cache
            cache_key = f"{project_id}_{phase}_curve"
            self._learning_curves_cache[cache_key] = curve

            logger.debug(
                f"Learning curve analyzed: initial={initial:.2f}, "
                f"current={current:.2f}, improvement_rate={improvement_rate:.3f}/day"
            )

            return curve

        except Exception as e:
            logger.error(f"Error analyzing learning curve: {e}")
            return LearningCurve(
                metric_name="unknown",
                phase=phase,
                initial_value=0.0,
                current_value=0.0,
                improvement_rate=0.0,
                projected_plateau=0.0,
                questions_to_plateau=0
            )

    # ========================================================================
    # Optimization Recommendations
    # ========================================================================

    def generate_optimization_recommendations(
        self,
        project_id: str,
        questions: List[QuestionEffectiveness],
        patterns: List[AnswerPattern]
    ) -> List[OptimizationRecommendation]:
        """
        Generate recommendations for optimizing question generation.

        Recommendations:
        - Reorder questions by effectiveness
        - Remove low-performing questions
        - Rephrase ambiguous questions
        - Add missing question types

        Args:
            project_id: Project identifier
            questions: List of questions with effectiveness scores
            patterns: Detected answer patterns

        Returns:
            List of optimization recommendations
        """
        try:
            recommendations = []

            # Recommendation 1: Low effectiveness questions
            low_performers = [q for q in questions if q.effectiveness_score < 0.5]
            for question in low_performers:
                recommendations.append(OptimizationRecommendation(
                    recommendation_type="review_or_remove",
                    question_id=question.question_id,
                    current_metric=f"effectiveness={question.effectiveness_score:.2f}",
                    target_metric="effectiveness>=0.7",
                    confidence=0.8,
                    reasoning=f"Question '{question.text[:50]}...' has low effectiveness. Consider rephrasing or removing.",
                    priority="high"
                ))

            # Recommendation 2: Pattern-based improvements
            for pattern in patterns:
                if pattern.average_quality < 0.7:
                    recommendations.append(OptimizationRecommendation(
                        recommendation_type="improve_pattern",
                        question_id=None,
                        current_metric=f"pattern_quality={pattern.average_quality:.2f}",
                        target_metric="pattern_quality>=0.8",
                        confidence=0.7,
                        reasoning=f"Pattern '{pattern.pattern_name}' produces below-average answers. Adjust question phrasing.",
                        priority="medium"
                    ))

            # Recommendation 3: Reordering
            if questions:
                high_performers = [q for q in questions if q.effectiveness_score > 0.8]
                if len(high_performers) > 0:
                    recommendations.append(OptimizationRecommendation(
                        recommendation_type="prioritize_questions",
                        question_id=None,
                        current_metric=f"top_effectiveness={high_performers[0].effectiveness_score:.2f}",
                        target_metric="ask_high_effectiveness_questions_first",
                        confidence=0.85,
                        reasoning=f"Reorder questions to ask high-performing questions first for better results.",
                        priority="medium"
                    ))

            # Cache
            self._optimization_cache[project_id] = recommendations

            logger.debug(f"Generated {len(recommendations)} optimization recommendations")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    # ========================================================================
    # Future Question Improvement
    # ========================================================================

    def suggest_improved_question(
        self,
        original_question: str,
        issue: str,
        patterns: List[AnswerPattern]
    ) -> str:
        """
        Suggest an improved version of a question.

        Based on patterns and common issues.

        Args:
            original_question: Original question text
            issue: What's wrong with the question
            patterns: Detected answer patterns

        Returns:
            Improved question suggestion
        """
        try:
            # Build improved version based on issue
            if "ambiguous" in issue.lower():
                # Make more specific
                improved = f"{original_question}? Please be specific about..."

            elif "too broad" in issue.lower():
                # Make narrower
                improved = f"Specifically, {original_question.lower()}?"

            elif "low quality answers" in issue.lower():
                # Add guidance
                improved = f"{original_question}? Include specific details, examples, and reasoning."

            elif "missing examples" in issue.lower() and any(p.pattern_name == "example_based" for p in patterns):
                # Add example request
                improved = f"{original_question}? Please provide a concrete example."

            else:
                # General improvement
                improved = f"{original_question}? Could you provide more detail?"

            logger.debug(f"Improved question suggestion generated")

            return improved

        except Exception as e:
            logger.error(f"Error suggesting improved question: {e}")
            return original_question

    # ========================================================================
    # Cache Management
    # ========================================================================

    def clear_cache(self, project_id: Optional[str] = None) -> None:
        """
        Clear learning service caches.

        Args:
            project_id: Optional project ID to clear specific caches
        """
        try:
            if project_id:
                # Clear specific project caches
                keys_to_delete = [
                    k for k in self._optimization_cache.keys()
                    if k.startswith(project_id)
                ]
                for key in keys_to_delete:
                    del self._optimization_cache[key]
            else:
                # Clear all caches
                self._question_effectiveness_cache.clear()
                self._answer_patterns_cache.clear()
                self._learning_curves_cache.clear()
                self._optimization_cache.clear()

            logger.info(f"Cleared learning service cache for {project_id or 'all projects'}")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    # ========================================================================
    # Analytics
    # ========================================================================

    def get_learning_summary(
        self,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive learning summary for a project.

        Args:
            project_id: Project identifier

        Returns:
            Learning summary dictionary
        """
        try:
            questions = list(self._question_effectiveness_cache.values())
            patterns = self._answer_patterns_cache.get(project_id, [])

            if not questions:
                return {
                    "total_questions_analyzed": 0,
                    "avg_effectiveness": 0.0,
                    "patterns_detected": 0
                }

            avg_effectiveness = sum(q.effectiveness_score for q in questions) / len(questions)
            best_question = max(questions, key=lambda q: q.effectiveness_score) if questions else None

            return {
                "total_questions_analyzed": len(questions),
                "avg_effectiveness": round(avg_effectiveness, 2),
                "patterns_detected": len(patterns),
                "best_performing_question": {
                    "id": best_question.question_id if best_question else None,
                    "effectiveness": round(best_question.effectiveness_score, 2) if best_question else 0,
                    "gaps_addressed": best_question.gaps_addressed if best_question else 0
                } if best_question else None,
                "primary_pattern": patterns[0].pattern_name if patterns else None
            }

        except Exception as e:
            logger.error(f"Error getting learning summary: {e}")
            return {}
