"""
Advancement Tracker Service - Phase 6

Tracks specification advancement and gap closure through question answering.
Measures progress, calculates completeness, and predicts phase readiness.

Key Features:
- Gap closure tracking
- Specification completeness calculation
- Progress history management
- Phase readiness prediction
- Answer impact analysis
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

class GapStatus(str, Enum):
    """Status of a specification gap."""
    OPEN = "open"
    PARTIAL = "partial"
    CLOSED = "closed"
    RESOLVED = "resolved"


@dataclass
class GapClosureRecord:
    """Record of a gap being closed by an answer."""
    gap_id: str
    question_id: str
    answer_text: str
    closure_confidence: float  # 0-1, how confident gap is closed
    closed_at: str
    status: GapStatus = GapStatus.PARTIAL
    evidence: str = ""  # Text from answer supporting closure


@dataclass
class CompletenessMetrics:
    """Specification completeness metrics."""
    overall: float  # 0-1
    by_category: Dict[str, float] = field(default_factory=dict)
    trend: str = "stable"  # improving, stable, declining
    projected_completion: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AdvancementMetrics:
    """Phase advancement metrics."""
    phase: str
    maturity: float  # 0-1
    readiness: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0  # 0-1
    gap_closure_rate: float = 0.0  # 0-1
    confidence: float = 0.0  # 0-1


@dataclass
class ProgressSnapshot:
    """Point-in-time snapshot of project progress."""
    timestamp: str
    phase: str
    completeness: float
    gap_closure_count: int
    total_gaps: int
    maturity: float
    questions_answered: int


# ============================================================================
# Advancement Tracker Service
# ============================================================================

class AdvancementTracker:
    """
    Tracks specification advancement and gap closure.

    Core responsibilities:
    - Track which gaps are closed by which answers
    - Calculate specification completeness
    - Maintain progress history
    - Predict phase readiness
    - Analyze answer impact
    """

    def __init__(self):
        """Initialize the Advancement Tracker."""
        self._gap_closure_history: Dict[str, List[GapClosureRecord]] = {}
        self._completeness_history: Dict[str, List[CompletenessMetrics]] = {}
        self._progress_snapshots: Dict[str, List[ProgressSnapshot]] = {}
        self._advancement_cache: Dict[str, AdvancementMetrics] = {}

        logger.info("Advancement Tracker initialized")

    # ========================================================================
    # Gap Closure Tracking
    # ========================================================================

    def record_gap_closure(
        self,
        project_id: str,
        gap_id: str,
        question_id: str,
        answer_text: str,
        closure_confidence: float = 0.8
    ) -> GapClosureRecord:
        """
        Record that a gap has been addressed by an answer.

        Args:
            project_id: Project identifier
            gap_id: Gap being closed
            question_id: Question that led to answer
            answer_text: The answer provided
            closure_confidence: How confident gap is closed (0-1)

        Returns:
            GapClosureRecord
        """
        try:
            record = GapClosureRecord(
                gap_id=gap_id,
                question_id=question_id,
                answer_text=answer_text,
                closure_confidence=closure_confidence,
                closed_at=datetime.now().isoformat(),
                status=self._determine_gap_status(closure_confidence),
                evidence=answer_text[:200]  # First 200 chars as evidence
            )

            # Store in history
            if project_id not in self._gap_closure_history:
                self._gap_closure_history[project_id] = []

            self._gap_closure_history[project_id].append(record)

            # Invalidate completeness cache
            if project_id in self._advancement_cache:
                del self._advancement_cache[project_id]

            logger.debug(
                f"Recorded gap closure: {gap_id} by question {question_id} "
                f"(confidence: {closure_confidence:.2f})"
            )

            return record

        except Exception as e:
            logger.error(f"Error recording gap closure: {e}")
            raise

    def _determine_gap_status(self, confidence: float) -> GapStatus:
        """Determine gap status from confidence level."""
        if confidence >= 0.95:
            return GapStatus.RESOLVED
        elif confidence >= 0.8:
            return GapStatus.CLOSED
        elif confidence >= 0.5:
            return GapStatus.PARTIAL
        else:
            return GapStatus.OPEN

    def get_gap_closure_status(
        self,
        project_id: str,
        gap_id: str
    ) -> Dict[str, Any]:
        """
        Get closure status for a specific gap.

        Args:
            project_id: Project identifier
            gap_id: Gap to check

        Returns:
            Dictionary with closure status and history
        """
        try:
            history = self._gap_closure_history.get(project_id, [])
            gap_records = [r for r in history if r.gap_id == gap_id]

            if not gap_records:
                return {
                    "status": GapStatus.OPEN.value,
                    "closed": False,
                    "records": []
                }

            # Get most recent record
            latest = gap_records[-1]
            closed_count = sum(1 for r in gap_records if r.status in [GapStatus.CLOSED, GapStatus.RESOLVED])

            return {
                "status": latest.status.value,
                "closed": latest.status != GapStatus.OPEN,
                "closure_confidence": latest.closure_confidence,
                "closed_by_question": latest.question_id,
                "closed_at": latest.closed_at,
                "closure_attempts": len(gap_records),
                "successful_closures": closed_count,
                "evidence": latest.evidence
            }

        except Exception as e:
            logger.error(f"Error getting gap closure status: {e}")
            return {"status": GapStatus.OPEN.value, "closed": False, "records": []}

    # ========================================================================
    # Specification Completeness
    # ========================================================================

    def calculate_completeness(
        self,
        project_id: str,
        total_gaps: int,
        identified_gaps: int,
        closed_gaps: int,
        project_specs: Dict[str, Any]
    ) -> CompletenessMetrics:
        """
        Calculate specification completeness metrics.

        Measures:
        - Overall completeness (0-1)
        - Completeness by category (goals, requirements, constraints, etc.)
        - Trend (improving, stable, declining)

        Args:
            project_id: Project identifier
            total_gaps: Total possible gaps
            identified_gaps: Gaps identified so far
            closed_gaps: Gaps successfully closed
            project_specs: Project specifications

        Returns:
            CompletenessMetrics
        """
        try:
            # Calculate overall completeness
            # Formula: (Identified Gaps + Closed Gaps) / Total Gaps
            if total_gaps > 0:
                overall = (identified_gaps + (closed_gaps * 2)) / (total_gaps * 2)
            else:
                overall = 0.5  # Default to moderate if no gaps identified

            overall = min(1.0, max(0.0, overall))

            # Calculate by-category completeness
            by_category = self._calculate_category_completeness(
                project_id,
                project_specs,
                total_gaps,
                closed_gaps
            )

            # Determine trend
            trend = self._determine_completeness_trend(project_id, overall)

            # Project completion date
            projected_completion = self._project_completion_date(
                project_id,
                overall,
                closed_gaps,
                total_gaps
            )

            metrics = CompletenessMetrics(
                overall=overall,
                by_category=by_category,
                trend=trend,
                projected_completion=projected_completion
            )

            # Store in history
            if project_id not in self._completeness_history:
                self._completeness_history[project_id] = []

            self._completeness_history[project_id].append(metrics)

            # Keep only last 100 entries
            if len(self._completeness_history[project_id]) > 100:
                self._completeness_history[project_id] = self._completeness_history[project_id][-100:]

            logger.debug(
                f"Completeness calculated for {project_id}: "
                f"overall={overall:.2f}, trend={trend}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating completeness: {e}")
            return CompletenessMetrics(overall=0.5)

    def _calculate_category_completeness(
        self,
        project_id: str,
        project_specs: Dict[str, Any],
        total_gaps: int,
        closed_gaps: int
    ) -> Dict[str, float]:
        """Calculate completeness by specification category."""
        by_category = {}
        categories = ["goals", "requirements", "constraints", "tech_stack"]

        for category in categories:
            specs = project_specs.get(category, [])
            if specs:
                # Simple heuristic: category completeness based on gap closure
                category_completeness = 0.5 + (closed_gaps / max(total_gaps, 1)) * 0.5
                by_category[category] = min(1.0, category_completeness)
            else:
                by_category[category] = 0.0

        return by_category

    def _determine_completeness_trend(
        self,
        project_id: str,
        current_completeness: float
    ) -> str:
        """Determine if completeness is improving, stable, or declining."""
        history = self._completeness_history.get(project_id, [])

        if len(history) < 2:
            return "stable"

        # Compare last two measurements
        previous = history[-2].overall
        current = current_completeness

        if current > previous + 0.05:
            return "improving"
        elif current < previous - 0.05:
            return "declining"
        else:
            return "stable"

    def _project_completion_date(
        self,
        project_id: str,
        current_completeness: float,
        closed_gaps: int,
        total_gaps: int
    ) -> Optional[str]:
        """Project when specifications will be complete."""
        if current_completeness >= 0.95:
            return datetime.now().isoformat()

        history = self._completeness_history.get(project_id, [])

        if len(history) < 2:
            return None

        # Calculate completion rate
        if closed_gaps == 0:
            return None

        remaining_completeness = 1.0 - current_completeness

        # Estimate days to close one gap (average)
        time_span = self._calculate_time_span(history)
        gaps_closed_in_span = closed_gaps

        if gaps_closed_in_span == 0:
            return None

        days_per_gap = time_span / gaps_closed_in_span
        remaining_gaps = total_gaps - closed_gaps

        estimated_days = remaining_gaps * days_per_gap
        estimated_completion = datetime.now() + timedelta(days=estimated_days)

        return estimated_completion.isoformat()

    def _calculate_time_span(self, history: List[CompletenessMetrics]) -> float:
        """Calculate time span of completeness history in days."""
        if len(history) < 2:
            return 1.0

        first = datetime.fromisoformat(history[0].last_updated)
        last = datetime.fromisoformat(history[-1].last_updated)

        return (last - first).days or 1

    # ========================================================================
    # Phase Readiness Prediction
    # ========================================================================

    def calculate_advancement_metrics(
        self,
        project_id: str,
        phase: str,
        maturity: float,
        total_gaps: int,
        closed_gaps: int,
        question_count: int
    ) -> AdvancementMetrics:
        """
        Calculate comprehensive advancement metrics.

        Predicts phase readiness based on:
        - Maturity score
        - Gap closure rate
        - Specification completeness
        - Quality indicators

        Args:
            project_id: Project identifier
            phase: Current phase
            maturity: Phase maturity (0-1)
            total_gaps: Total identified gaps
            closed_gaps: Gaps successfully closed
            question_count: Questions answered so far

        Returns:
            AdvancementMetrics
        """
        try:
            # Calculate gap closure rate
            gap_closure_rate = closed_gaps / max(total_gaps, 1)

            # Calculate quality score
            quality_score = self._calculate_quality_score(
                maturity,
                gap_closure_rate,
                question_count,
                total_gaps
            )

            # Calculate advancement confidence
            confidence = self._calculate_advancement_confidence(
                maturity,
                gap_closure_rate,
                quality_score
            )

            # Build readiness information
            next_phase = self._get_next_phase(phase)
            readiness = {
                "current_phase": phase,
                "next_phase": next_phase,
                "can_advance": maturity >= 0.99,  # 99% maturity threshold
                "ready_percentage": int(maturity * 100),
                "required_percentage": 100,
                "gap_closure_percentage": int(gap_closure_rate * 100),
                "quality_score": int(quality_score * 100),
                "estimated_days_to_ready": max(0, int(5 * (1 - maturity)))
            }

            metrics = AdvancementMetrics(
                phase=phase,
                maturity=maturity,
                readiness=readiness,
                quality_score=quality_score,
                gap_closure_rate=gap_closure_rate,
                confidence=confidence
            )

            # Cache result
            self._advancement_cache[project_id] = metrics

            logger.debug(
                f"Advancement metrics for {project_id}: "
                f"phase={phase}, maturity={maturity:.2f}, "
                f"gap_closure={gap_closure_rate:.2f}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating advancement metrics: {e}")
            return AdvancementMetrics(
                phase=phase,
                maturity=maturity,
                quality_score=0.5,
                gap_closure_rate=0.0
            )

    def _calculate_quality_score(
        self,
        maturity: float,
        gap_closure_rate: float,
        question_count: int,
        total_gaps: int
    ) -> float:
        """
        Calculate advancement quality score.

        Factors:
        - Maturity (how well specifications meet requirements)
        - Gap closure (what percentage of gaps are addressed)
        - Efficiency (gaps closed per question)
        """
        # Component 1: Maturity (40% weight)
        maturity_score = maturity * 0.4

        # Component 2: Gap closure (40% weight)
        closure_score = gap_closure_rate * 0.4

        # Component 3: Efficiency (20% weight)
        if question_count > 0:
            efficiency = min(1.0, (total_gaps * 2) / question_count)
        else:
            efficiency = 0.0
        efficiency_score = efficiency * 0.2

        return min(1.0, maturity_score + closure_score + efficiency_score)

    def _calculate_advancement_confidence(
        self,
        maturity: float,
        gap_closure_rate: float,
        quality_score: float
    ) -> float:
        """Calculate confidence in advancement readiness."""
        # High confidence if metrics agree
        agreement = min(maturity, gap_closure_rate, quality_score)

        # Boost for high quality
        if quality_score > 0.8:
            agreement = min(1.0, agreement + 0.1)

        return min(1.0, agreement)

    def _get_next_phase(self, current_phase: str) -> str:
        """Get next phase in sequence."""
        phases = ["discovery", "analysis", "design", "implementation"]
        try:
            idx = phases.index(current_phase)
            return phases[idx + 1] if idx < len(phases) - 1 else phases[-1]
        except (ValueError, IndexError):
            return "implementation"

    # ========================================================================
    # Progress History
    # ========================================================================

    def record_progress_snapshot(
        self,
        project_id: str,
        phase: str,
        completeness: float,
        gap_closure_count: int,
        total_gaps: int,
        maturity: float,
        questions_answered: int
    ) -> ProgressSnapshot:
        """
        Record a point-in-time snapshot of project progress.

        Args:
            project_id: Project identifier
            phase: Current phase
            completeness: Specification completeness (0-1)
            gap_closure_count: Gaps closed
            total_gaps: Total gaps
            maturity: Phase maturity (0-1)
            questions_answered: Questions answered so far

        Returns:
            ProgressSnapshot
        """
        try:
            snapshot = ProgressSnapshot(
                timestamp=datetime.now().isoformat(),
                phase=phase,
                completeness=completeness,
                gap_closure_count=gap_closure_count,
                total_gaps=total_gaps,
                maturity=maturity,
                questions_answered=questions_answered
            )

            if project_id not in self._progress_snapshots:
                self._progress_snapshots[project_id] = []

            self._progress_snapshots[project_id].append(snapshot)

            # Keep only last 1000 snapshots
            if len(self._progress_snapshots[project_id]) > 1000:
                self._progress_snapshots[project_id] = self._progress_snapshots[project_id][-1000:]

            logger.debug(f"Progress snapshot recorded for {project_id}")

            return snapshot

        except Exception as e:
            logger.error(f"Error recording progress snapshot: {e}")
            raise

    def get_progress_timeline(
        self,
        project_id: str,
        days: int = 30
    ) -> List[ProgressSnapshot]:
        """
        Get project progress over time.

        Args:
            project_id: Project identifier
            days: Number of days to look back

        Returns:
            List of ProgressSnapshot ordered by time
        """
        try:
            snapshots = self._progress_snapshots.get(project_id, [])

            if not snapshots:
                return []

            # Filter by date
            cutoff = datetime.now() - timedelta(days=days)

            filtered = [
                s for s in snapshots
                if datetime.fromisoformat(s.timestamp) >= cutoff
            ]

            return sorted(filtered, key=lambda s: s.timestamp)

        except Exception as e:
            logger.error(f"Error getting progress timeline: {e}")
            return []

    def get_progress_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Get comprehensive progress summary.

        Args:
            project_id: Project identifier

        Returns:
            Dictionary with progress summary
        """
        try:
            snapshots = self._progress_snapshots.get(project_id, [])

            if not snapshots:
                return {
                    "total_snapshots": 0,
                    "current_phase": "unknown",
                    "current_completeness": 0.0
                }

            latest = snapshots[-1]
            earliest = snapshots[0]

            return {
                "total_snapshots": len(snapshots),
                "current_phase": latest.phase,
                "current_completeness": latest.completeness,
                "completeness_improvement": latest.completeness - earliest.completeness,
                "questions_answered": latest.questions_answered,
                "gap_closure_count": latest.gap_closure_count,
                "total_gaps": latest.total_gaps,
                "timeline_days": (
                    datetime.fromisoformat(latest.timestamp) -
                    datetime.fromisoformat(earliest.timestamp)
                ).days
            }

        except Exception as e:
            logger.error(f"Error getting progress summary: {e}")
            return {}

    # ========================================================================
    # Analytics
    # ========================================================================

    def analyze_answer_impact(
        self,
        project_id: str,
        question_id: str,
        answer_text: str,
        gaps_addressed: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze impact of an answer on project advancement.

        Args:
            project_id: Project identifier
            question_id: Question ID
            answer_text: Answer provided
            gaps_addressed: List of gaps this answer addresses

        Returns:
            Impact analysis dictionary
        """
        try:
            # Calculate answer quality
            answer_quality = self._assess_answer_quality(answer_text)

            # Calculate impact
            gap_impact = len(gaps_addressed)
            total_impact = answer_quality * (1 + gap_impact * 0.1)

            # Get category impact
            category_impact = self._calculate_category_impact(gaps_addressed)

            analysis = {
                "question_id": question_id,
                "answer_quality": answer_quality,
                "gaps_addressed": gap_impact,
                "total_impact_score": total_impact,
                "category_impact": category_impact,
                "effectiveness": "high" if total_impact > 0.7 else "medium" if total_impact > 0.4 else "low"
            }

            logger.debug(f"Answer impact analysis: {analysis}")

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing answer impact: {e}")
            return {}

    def _assess_answer_quality(self, answer_text: str) -> float:
        """
        Assess quality of an answer.

        Factors: length, specificity, completeness
        """
        if not answer_text:
            return 0.0

        # Length factor (longer usually better, but with diminishing returns)
        length = min(len(answer_text) / 1000, 1.0)

        # Specificity factor (check for specific details)
        specific_words = ["specifically", "detailed", "implementation", "example", "because"]
        specificity = sum(1 for word in specific_words if word in answer_text.lower()) / len(specific_words)

        # Completeness factor (check for comprehensive coverage)
        completeness_words = ["all", "everything", "complete", "comprehensive", "covers"]
        completeness = sum(1 for word in completeness_words if word in answer_text.lower()) / len(completeness_words)

        return min(1.0, (length * 0.5 + specificity * 0.3 + completeness * 0.2))

    def _calculate_category_impact(self, gaps: List[str]) -> Dict[str, int]:
        """Calculate impact on each specification category."""
        categories = {
            "goals": 0,
            "requirements": 0,
            "constraints": 0,
            "tech_stack": 0
        }

        for gap in gaps:
            gap_lower = gap.lower()
            for category in categories.keys():
                if category in gap_lower:
                    categories[category] += 1

        return categories

    # ========================================================================
    # Cache Management
    # ========================================================================

    def clear_cache(self, project_id: Optional[str] = None) -> None:
        """
        Clear advancement tracker caches.

        Args:
            project_id: Optional project ID to clear specific caches
        """
        try:
            if project_id:
                if project_id in self._advancement_cache:
                    del self._advancement_cache[project_id]
            else:
                self._advancement_cache.clear()

            logger.info(f"Cleared advancement cache for {project_id or 'all projects'}")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
