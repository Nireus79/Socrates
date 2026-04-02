"""
Progress Dashboard Service - Phase 6

Provides aggregated progress data for UI visualization and real-time tracking.
Handles data formatting for dashboards and maintains historical progress records.

Key Features:
- Data aggregation from advancement tracker and metrics service
- Visualization data formatting
- Historical tracking and trending
- Real-time status updates
- Progress forecasting
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ProgressUpdate:
    """Single progress update for dashboard."""
    timestamp: str
    phase: str
    completeness: float
    gap_closure_percentage: float
    maturity: float
    questions_answered: int
    total_gaps: int
    quality_score: float


@dataclass
class DashboardData:
    """Comprehensive dashboard data."""
    project_id: str
    current_phase: str
    overall_progress: float  # 0-100% overall project completion
    phase_progress: Dict[str, float] = field(default_factory=dict)  # % per phase
    completeness: float = 0.0
    gap_closure_percentage: float = 0.0
    maturity: float = 0.0
    quality_score: float = 0.0
    advancement_confidence: float = 0.0
    questions_answered: int = 0
    total_gaps: int = 0
    estimated_completion_date: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ChartData:
    """Formatted data for chart visualization."""
    title: str
    labels: List[str]
    datasets: List[Dict[str, Any]]
    type: str  # line, bar, pie, etc.
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressTimeline:
    """Historical progress timeline."""
    project_id: str
    snapshots: List[ProgressUpdate] = field(default_factory=list)
    oldest_timestamp: Optional[str] = None
    newest_timestamp: Optional[str] = None
    record_count: int = 0


@dataclass
class StatusIndicator:
    """Status indicator for dashboard display."""
    label: str
    value: float  # 0-1
    percentage: float  # 0-100
    status: str  # healthy, warning, critical
    trend: str  # improving, stable, declining
    target: Optional[float] = None


# ============================================================================
# Progress Dashboard Service
# ============================================================================

class ProgressDashboard:
    """
    Aggregates and formats progress data for UI visualization.

    Core responsibilities:
    - Aggregate data from AdvancementTracker and MetricsService
    - Format data for chart visualization
    - Maintain historical tracking
    - Provide real-time status updates
    - Calculate progress forecasts
    """

    def __init__(self):
        """Initialize the Progress Dashboard service."""
        self._dashboard_cache: Dict[str, DashboardData] = {}
        self._timeline_cache: Dict[str, ProgressTimeline] = {}
        self._chart_data_cache: Dict[str, Dict[str, ChartData]] = {}
        self._cache_timestamps: Dict[str, str] = {}
        logger.info("Progress Dashboard service initialized")

    # ========================================================================
    # Dashboard Data Aggregation
    # ========================================================================

    def get_dashboard_data(
        self,
        project_id: str,
        current_phase: str,
        completeness: float,
        gap_closure_percentage: float,
        maturity: float,
        quality_score: float,
        advancement_confidence: float,
        questions_answered: int,
        total_gaps: int,
        phase_history: Optional[Dict[str, int]] = None
    ) -> DashboardData:
        """
        Aggregate all dashboard data.

        Args:
            project_id: Project identifier
            current_phase: Current project phase
            completeness: Specification completeness (0-1)
            gap_closure_percentage: Gap closure percentage (0-1)
            maturity: Current phase maturity (0-1)
            quality_score: Quality score (0-1)
            advancement_confidence: Advancement confidence (0-1)
            questions_answered: Number of answered questions
            total_gaps: Total number of gaps
            phase_history: Dictionary of phase names to completion percentages

        Returns:
            DashboardData with aggregated metrics
        """
        try:
            # Calculate overall progress
            overall_progress = self._calculate_overall_progress(
                completeness, gap_closure_percentage, maturity, quality_score
            )

            # Calculate phase progress
            phase_progress = self._calculate_phase_progress(phase_history)

            # Estimate completion date
            completion_date = self._estimate_completion_date(
                completeness, questions_answered, total_gaps
            )

            dashboard_data = DashboardData(
                project_id=project_id,
                current_phase=current_phase,
                overall_progress=overall_progress,
                phase_progress=phase_progress,
                completeness=completeness,
                gap_closure_percentage=gap_closure_percentage,
                maturity=maturity,
                quality_score=quality_score,
                advancement_confidence=advancement_confidence,
                questions_answered=questions_answered,
                total_gaps=total_gaps,
                estimated_completion_date=completion_date
            )

            # Cache result
            self._dashboard_cache[project_id] = dashboard_data
            self._cache_timestamps[project_id] = datetime.now().isoformat()

            logger.info(f"Dashboard data aggregated for project {project_id}")
            return dashboard_data

        except Exception as e:
            logger.error(f"Error aggregating dashboard data: {e}")
            raise

    # ========================================================================
    # Chart Data Formatting
    # ========================================================================

    def format_completeness_chart(
        self,
        completeness_history: List[float],
        timestamps: List[str],
        category_metrics: Optional[Dict[str, List[float]]] = None
    ) -> ChartData:
        """
        Format completeness data for chart visualization.

        Args:
            completeness_history: List of completeness values over time
            timestamps: Corresponding timestamps
            category_metrics: Optional per-category completeness history

        Returns:
            ChartData formatted for chart library
        """
        try:
            datasets = []

            # Overall completeness dataset
            datasets.append({
                "label": "Overall Completeness",
                "data": [int(v * 100) for v in completeness_history],
                "borderColor": "rgb(75, 192, 192)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "tension": 0.4,
                "fill": True
            })

            # Category completeness datasets
            if category_metrics:
                colors = [
                    ("rgb(255, 99, 132)", "rgba(255, 99, 132, 0.2)"),
                    ("rgb(54, 162, 235)", "rgba(54, 162, 235, 0.2)"),
                    ("rgb(255, 206, 86)", "rgba(255, 206, 86, 0.2)"),
                    ("rgb(75, 192, 192)", "rgba(75, 192, 192, 0.2)"),
                ]
                for idx, (category, values) in enumerate(category_metrics.items()):
                    color = colors[idx % len(colors)]
                    datasets.append({
                        "label": f"{category.title()} Completeness",
                        "data": [int(v * 100) for v in values],
                        "borderColor": color[0],
                        "backgroundColor": color[1],
                        "tension": 0.4,
                        "hidden": True  # Hide by default
                    })

            chart_data = ChartData(
                title="Specification Completeness Progress",
                labels=timestamps,
                datasets=datasets,
                type="line",
                options={
                    "responsive": True,
                    "plugins": {
                        "legend": {"position": "top"},
                        "title": {"display": True, "text": "Completeness Over Time"}
                    },
                    "scales": {
                        "y": {"min": 0, "max": 100, "title": {"display": True, "text": "%"}}
                    }
                }
            )

            logger.info("Completeness chart formatted")
            return chart_data

        except Exception as e:
            logger.error(f"Error formatting completeness chart: {e}")
            raise

    def format_gap_closure_chart(
        self,
        closed_gaps_history: List[int],
        total_gaps: int,
        timestamps: List[str]
    ) -> ChartData:
        """
        Format gap closure data for chart visualization.

        Args:
            closed_gaps_history: Number of closed gaps at each timestamp
            total_gaps: Total number of gaps
            timestamps: Corresponding timestamps

        Returns:
            ChartData formatted for chart library
        """
        try:
            # Calculate gap closure percentage
            closure_percentages = [
                int((count / total_gaps * 100) if total_gaps > 0 else 0)
                for count in closed_gaps_history
            ]

            chart_data = ChartData(
                title="Gap Closure Progress",
                labels=timestamps,
                datasets=[
                    {
                        "label": "Gaps Closed",
                        "data": closed_gaps_history,
                        "borderColor": "rgb(75, 192, 192)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)",
                        "yAxisID": "y",
                        "tension": 0.4
                    },
                    {
                        "label": "Closure %",
                        "data": closure_percentages,
                        "borderColor": "rgb(255, 99, 132)",
                        "backgroundColor": "rgba(255, 99, 132, 0.2)",
                        "yAxisID": "y1",
                        "tension": 0.4
                    }
                ],
                type="line",
                options={
                    "responsive": True,
                    "interaction": {"mode": "index", "intersect": False},
                    "scales": {
                        "y": {"type": "linear", "position": "left", "title": {"display": True, "text": "Gaps Closed"}},
                        "y1": {"type": "linear", "position": "right", "title": {"display": True, "text": "%"}, "min": 0, "max": 100}
                    }
                }
            )

            logger.info("Gap closure chart formatted")
            return chart_data

        except Exception as e:
            logger.error(f"Error formatting gap closure chart: {e}")
            raise

    def format_phase_progress_chart(
        self,
        phase_history: Dict[str, float]
    ) -> ChartData:
        """
        Format phase progress data for chart visualization.

        Args:
            phase_history: Dictionary of phase names to completion percentages (0-1)

        Returns:
            ChartData formatted for chart library
        """
        try:
            phases = list(phase_history.keys())
            percentages = [int(v * 100) for v in phase_history.values()]

            # Color phases based on completion
            colors = [
                self._get_phase_color(pct) for pct in percentages
            ]

            chart_data = ChartData(
                title="Phase Completion Status",
                labels=phases,
                datasets=[
                    {
                        "label": "Completion %",
                        "data": percentages,
                        "backgroundColor": colors,
                        "borderColor": "rgba(0, 0, 0, 0.1)",
                        "borderWidth": 1
                    }
                ],
                type="bar",
                options={
                    "responsive": True,
                    "plugins": {
                        "legend": {"display": False},
                        "title": {"display": True, "text": "Phase Completion Status"}
                    },
                    "scales": {
                        "y": {"min": 0, "max": 100, "title": {"display": True, "text": "%"}}
                    }
                }
            )

            logger.info("Phase progress chart formatted")
            return chart_data

        except Exception as e:
            logger.error(f"Error formatting phase progress chart: {e}")
            raise

    # ========================================================================
    # Historical Tracking
    # ========================================================================

    def record_progress_snapshot(
        self,
        project_id: str,
        phase: str,
        completeness: float,
        gap_closure_percentage: float,
        maturity: float,
        questions_answered: int,
        total_gaps: int,
        quality_score: float
    ) -> ProgressUpdate:
        """
        Record a progress snapshot for historical tracking.

        Args:
            project_id: Project identifier
            phase: Current phase
            completeness: Specification completeness (0-1)
            gap_closure_percentage: Gap closure percentage (0-1)
            maturity: Phase maturity (0-1)
            questions_answered: Number of answered questions
            total_gaps: Total gaps
            quality_score: Quality score (0-1)

        Returns:
            ProgressUpdate record
        """
        try:
            update = ProgressUpdate(
                timestamp=datetime.now().isoformat(),
                phase=phase,
                completeness=completeness,
                gap_closure_percentage=gap_closure_percentage,
                maturity=maturity,
                questions_answered=questions_answered,
                total_gaps=total_gaps,
                quality_score=quality_score
            )

            # Initialize timeline if needed
            if project_id not in self._timeline_cache:
                self._timeline_cache[project_id] = ProgressTimeline(project_id=project_id)

            timeline = self._timeline_cache[project_id]
            timeline.snapshots.append(update)
            timeline.newest_timestamp = update.timestamp
            if not timeline.oldest_timestamp:
                timeline.oldest_timestamp = update.timestamp
            timeline.record_count = len(timeline.snapshots)

            logger.info(f"Progress snapshot recorded for project {project_id}")
            return update

        except Exception as e:
            logger.error(f"Error recording progress snapshot: {e}")
            raise

    def get_progress_timeline(
        self,
        project_id: str,
        days: int = 30
    ) -> ProgressTimeline:
        """
        Get historical progress timeline.

        Args:
            project_id: Project identifier
            days: Number of days to include (default 30)

        Returns:
            ProgressTimeline with historical snapshots
        """
        try:
            if project_id not in self._timeline_cache:
                return ProgressTimeline(project_id=project_id)

            timeline = self._timeline_cache[project_id]
            cutoff_date = datetime.now() - timedelta(days=days)

            # Filter snapshots by date
            filtered_snapshots = [
                snap for snap in timeline.snapshots
                if datetime.fromisoformat(snap.timestamp) >= cutoff_date
            ]

            return ProgressTimeline(
                project_id=project_id,
                snapshots=filtered_snapshots,
                oldest_timestamp=filtered_snapshots[0].timestamp if filtered_snapshots else None,
                newest_timestamp=filtered_snapshots[-1].timestamp if filtered_snapshots else None,
                record_count=len(filtered_snapshots)
            )

        except Exception as e:
            logger.error(f"Error retrieving progress timeline: {e}")
            raise

    # ========================================================================
    # Real-Time Status
    # ========================================================================

    def get_status_indicators(
        self,
        current_metrics: DashboardData,
        target_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, StatusIndicator]:
        """
        Generate status indicators for dashboard display.

        Args:
            current_metrics: Current dashboard metrics
            target_metrics: Optional target metrics for comparison

        Returns:
            Dictionary of status indicators by metric name
        """
        try:
            targets = target_metrics or {
                "completeness": 1.0,
                "gap_closure": 1.0,
                "maturity": 1.0,
                "quality": 0.9
            }

            indicators = {}

            # Completeness indicator
            indicators["completeness"] = StatusIndicator(
                label="Specification Completeness",
                value=current_metrics.completeness,
                percentage=current_metrics.completeness * 100,
                status=self._get_status(current_metrics.completeness, targets.get("completeness", 1.0)),
                trend=self._calculate_trend("completeness", current_metrics.project_id),
                target=targets.get("completeness")
            )

            # Gap closure indicator
            indicators["gap_closure"] = StatusIndicator(
                label="Gap Closure",
                value=current_metrics.gap_closure_percentage,
                percentage=current_metrics.gap_closure_percentage * 100,
                status=self._get_status(current_metrics.gap_closure_percentage, targets.get("gap_closure", 1.0)),
                trend=self._calculate_trend("gap_closure", current_metrics.project_id),
                target=targets.get("gap_closure")
            )

            # Maturity indicator
            indicators["maturity"] = StatusIndicator(
                label="Phase Maturity",
                value=current_metrics.maturity,
                percentage=current_metrics.maturity * 100,
                status=self._get_status(current_metrics.maturity, targets.get("maturity", 1.0)),
                trend=self._calculate_trend("maturity", current_metrics.project_id),
                target=targets.get("maturity")
            )

            # Quality indicator
            indicators["quality"] = StatusIndicator(
                label="Advancement Quality",
                value=current_metrics.quality_score,
                percentage=current_metrics.quality_score * 100,
                status=self._get_status(current_metrics.quality_score, targets.get("quality", 0.9)),
                trend=self._calculate_trend("quality", current_metrics.project_id),
                target=targets.get("quality")
            )

            logger.info(f"Status indicators generated for project {current_metrics.project_id}")
            return indicators

        except Exception as e:
            logger.error(f"Error generating status indicators: {e}")
            raise

    # ========================================================================
    # Cache Management
    # ========================================================================

    def clear_cache(self, project_id: Optional[str] = None) -> None:
        """
        Clear dashboard cache.

        Args:
            project_id: Optional project ID to clear specific project cache.
                       If None, clears all caches.
        """
        try:
            if project_id:
                self._dashboard_cache.pop(project_id, None)
                self._timeline_cache.pop(project_id, None)
                self._chart_data_cache.pop(project_id, None)
                self._cache_timestamps.pop(project_id, None)
                logger.info(f"Cache cleared for project {project_id}")
            else:
                self._dashboard_cache.clear()
                self._timeline_cache.clear()
                self._chart_data_cache.clear()
                self._cache_timestamps.clear()
                logger.info("All dashboard caches cleared")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            raise

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _calculate_overall_progress(
        self,
        completeness: float,
        gap_closure: float,
        maturity: float,
        quality: float
    ) -> float:
        """
        Calculate overall project progress.

        Weighted average: completeness (40%), gap_closure (30%), maturity (20%), quality (10%)
        """
        return (
            completeness * 0.40 +
            gap_closure * 0.30 +
            maturity * 0.20 +
            quality * 0.10
        )

    def _calculate_phase_progress(
        self,
        phase_history: Optional[Dict[str, int]]
    ) -> Dict[str, float]:
        """Calculate progress for each phase."""
        if not phase_history:
            return {}

        # Convert raw phase history to percentages
        return {
            phase: min(count / 100, 1.0)  # Assume 100 items per phase
            for phase, count in phase_history.items()
        }

    def _estimate_completion_date(
        self,
        completeness: float,
        questions_answered: int,
        total_gaps: int
    ) -> Optional[str]:
        """Estimate project completion date."""
        if completeness >= 1.0:
            return datetime.now().isoformat()

        if total_gaps == 0 or questions_answered == 0:
            return None

        # Simple linear extrapolation
        gaps_per_question = total_gaps / max(questions_answered, 1)
        remaining_gaps = total_gaps * (1 - completeness)
        remaining_questions = remaining_gaps * gaps_per_question

        # Assume 1 question per day on average
        days_remaining = max(int(remaining_questions), 1)
        completion_date = datetime.now() + timedelta(days=days_remaining)

        return completion_date.isoformat()

    def _get_phase_color(self, percentage: float) -> str:
        """Get color for phase based on completion percentage."""
        if percentage >= 0.9:
            return "rgba(75, 192, 75, 0.6)"  # Green
        elif percentage >= 0.7:
            return "rgba(255, 193, 7, 0.6)"  # Yellow
        elif percentage >= 0.5:
            return "rgba(255, 152, 0, 0.6)"  # Orange
        else:
            return "rgba(244, 67, 54, 0.6)"  # Red

    def _get_status(self, value: float, target: float) -> str:
        """Determine status based on value vs. target."""
        if value >= target * 0.9:
            return "healthy"
        elif value >= target * 0.7:
            return "warning"
        else:
            return "critical"

    def _calculate_trend(self, metric_name: str, project_id: str) -> str:
        """Calculate trend for a metric."""
        if project_id not in self._timeline_cache:
            return "stable"

        timeline = self._timeline_cache[project_id]
        if len(timeline.snapshots) < 2:
            return "stable"

        recent_snapshots = timeline.snapshots[-5:]
        values = []

        for snapshot in recent_snapshots:
            if metric_name == "completeness":
                values.append(snapshot.completeness)
            elif metric_name == "gap_closure":
                values.append(snapshot.gap_closure_percentage)
            elif metric_name == "maturity":
                values.append(snapshot.maturity)
            elif metric_name == "quality":
                values.append(snapshot.quality_score)

        if len(values) < 2:
            return "stable"

        # Calculate trend
        change = values[-1] - values[0]
        threshold = 0.05  # 5% change threshold

        if change > threshold:
            return "improving"
        elif change < -threshold:
            return "declining"
        else:
            return "stable"
