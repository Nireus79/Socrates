"""
Metrics Service - Phase 6

Calculates and provides metrics for project advancement tracking.
Generates dashboard data, trends, statistics, and performance analysis.

Key Features:
- Dashboard metrics aggregation
- Trend calculation
- Performance analysis
- Quality scoring
- Comparative benchmarking
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class DashboardMetrics:
    """Main dashboard metrics."""
    project_id: str
    current_phase: str
    completeness: float
    maturity: float
    gap_closure_percentage: float
    questions_answered: int
    total_gaps: int
    quality_score: float
    advancement_confidence: float


@dataclass
class TrendData:
    """Trend analysis data."""
    metric_name: str
    values: List[float]
    timestamps: List[str]
    direction: str  # improving, stable, declining
    rate_of_change: float


@dataclass
class PerformanceMetrics:
    """Performance analysis metrics."""
    avg_time_per_gap: float  # minutes
    gaps_per_day: float
    questions_per_gap: float
    phase_progression_rate: float  # % per day
    estimated_project_duration: int  # days


# ============================================================================
# Metrics Service
# ============================================================================

class MetricsService:
    """
    Calculates and provides project advancement metrics.

    Responsibilities:
    - Aggregate dashboard metrics
    - Calculate trends
    - Analyze performance
    - Generate reports
    - Score quality
    """

    def __init__(self):
        """Initialize the Metrics Service."""
        self._metric_cache: Dict[str, Any] = {}
        self._trend_cache: Dict[str, TrendData] = {}
        logger.info("Metrics Service initialized")

    # ========================================================================
    # Dashboard Metrics
    # ========================================================================

    def get_dashboard_metrics(
        self,
        project_id: str,
        current_phase: str,
        completeness: float,
        maturity: float,
        gap_closure_count: int,
        total_gaps: int,
        questions_answered: int,
        quality_score: float,
        advancement_confidence: float
    ) -> DashboardMetrics:
        """
        Aggregate all metrics for dashboard display.

        Args:
            project_id: Project identifier
            current_phase: Current project phase
            completeness: Specification completeness (0-1)
            maturity: Phase maturity (0-1)
            gap_closure_count: Gaps successfully closed
            total_gaps: Total gaps identified
            questions_answered: Number of questions answered
            quality_score: Advancement quality (0-1)
            advancement_confidence: Confidence in advancement (0-1)

        Returns:
            DashboardMetrics
        """
        try:
            gap_closure_percentage = (
                gap_closure_count / max(total_gaps, 1) * 100
                if total_gaps > 0 else 0
            )

            metrics = DashboardMetrics(
                project_id=project_id,
                current_phase=current_phase,
                completeness=completeness,
                maturity=maturity,
                gap_closure_percentage=gap_closure_percentage,
                questions_answered=questions_answered,
                total_gaps=total_gaps,
                quality_score=quality_score,
                advancement_confidence=advancement_confidence
            )

            # Cache result
            cache_key = f"{project_id}_dashboard"
            self._metric_cache[cache_key] = metrics

            logger.debug(f"Dashboard metrics calculated for {project_id}")

            return metrics

        except Exception as e:
            logger.error(f"Error calculating dashboard metrics: {e}")
            return DashboardMetrics(
                project_id=project_id,
                current_phase=current_phase,
                completeness=0.0,
                maturity=0.0,
                gap_closure_percentage=0.0,
                questions_answered=0,
                total_gaps=0,
                quality_score=0.5,
                advancement_confidence=0.0
            )

    def dashboard_metrics_to_dict(self, metrics: DashboardMetrics) -> Dict[str, Any]:
        """Convert dashboard metrics to dictionary for API response."""
        return {
            "project_id": metrics.project_id,
            "current_phase": metrics.current_phase,
            "completeness": {
                "percentage": int(metrics.completeness * 100),
                "score": metrics.completeness
            },
            "maturity": {
                "percentage": int(metrics.maturity * 100),
                "score": metrics.maturity
            },
            "gap_closure": {
                "percentage": int(metrics.gap_closure_percentage),
                "count": int(metrics.gap_closure_percentage * metrics.total_gaps / 100),
                "total": metrics.total_gaps
            },
            "questions": {
                "answered": metrics.questions_answered,
                "per_gap": (
                    metrics.questions_answered / max(metrics.total_gaps, 1)
                    if metrics.total_gaps > 0 else 0
                )
            },
            "quality": {
                "score": int(metrics.quality_score * 100),
                "advancement_confidence": int(metrics.advancement_confidence * 100)
            }
        }

    # ========================================================================
    # Trend Analysis
    # ========================================================================

    def calculate_trend(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[str]
    ) -> TrendData:
        """
        Calculate trend for a metric.

        Args:
            metric_name: Name of metric
            values: Historical values
            timestamps: Corresponding timestamps

        Returns:
            TrendData with direction and rate of change
        """
        try:
            if len(values) < 2:
                return TrendData(
                    metric_name=metric_name,
                    values=values,
                    timestamps=timestamps,
                    direction="unknown",
                    rate_of_change=0.0
                )

            # Calculate rate of change
            recent_values = values[-10:] if len(values) > 10 else values
            old_value = recent_values[0]
            new_value = recent_values[-1]

            if old_value == 0:
                rate_of_change = 0.0
            else:
                rate_of_change = (new_value - old_value) / abs(old_value)

            # Determine direction
            if rate_of_change > 0.05:
                direction = "improving"
            elif rate_of_change < -0.05:
                direction = "declining"
            else:
                direction = "stable"

            trend = TrendData(
                metric_name=metric_name,
                values=values,
                timestamps=timestamps,
                direction=direction,
                rate_of_change=rate_of_change
            )

            # Cache
            cache_key = f"trend_{metric_name}"
            self._trend_cache[cache_key] = trend

            logger.debug(
                f"Trend calculated for {metric_name}: "
                f"direction={direction}, rate={rate_of_change:.2f}"
            )

            return trend

        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return TrendData(
                metric_name=metric_name,
                values=values,
                timestamps=timestamps,
                direction="unknown",
                rate_of_change=0.0
            )

    def get_trend_visualization_data(
        self,
        trend: TrendData
    ) -> Dict[str, Any]:
        """
        Format trend data for visualization.

        Args:
            trend: TrendData object

        Returns:
            Dictionary with visualization data
        """
        try:
            # Prepare time labels
            labels = []
            for ts in trend.timestamps:
                try:
                    dt = datetime.fromisoformat(ts)
                    labels.append(dt.strftime("%m/%d %H:%M"))
                except:
                    labels.append(ts[:10])

            return {
                "metric": trend.metric_name,
                "labels": labels,
                "values": [round(v, 2) for v in trend.values],
                "direction": trend.direction,
                "rate_of_change": round(trend.rate_of_change, 2),
                "current_value": round(trend.values[-1], 2) if trend.values else 0,
                "previous_value": round(trend.values[-2], 2) if len(trend.values) > 1 else 0
            }

        except Exception as e:
            logger.error(f"Error formatting trend visualization: {e}")
            return {}

    # ========================================================================
    # Performance Analysis
    # ========================================================================

    def analyze_performance(
        self,
        project_id: str,
        total_gaps: int,
        gaps_closed: int,
        questions_answered: int,
        started_at: str,
        current_phase: str,
        phases_completed: int
    ) -> PerformanceMetrics:
        """
        Analyze project performance metrics.

        Args:
            project_id: Project identifier
            total_gaps: Total gaps identified
            gaps_closed: Gaps successfully closed
            questions_answered: Questions answered
            started_at: Project start timestamp
            current_phase: Current phase
            phases_completed: Number of phases completed

        Returns:
            PerformanceMetrics
        """
        try:
            # Calculate time elapsed
            try:
                start_time = datetime.fromisoformat(started_at)
                elapsed = datetime.now() - start_time
                days_elapsed = max(elapsed.days, 1)
            except:
                days_elapsed = 1

            # Calculate metrics
            avg_time_per_gap = (
                (days_elapsed * 24 * 60) / max(gaps_closed, 1)
                if gaps_closed > 0 else 0
            )

            gaps_per_day = gaps_closed / max(days_elapsed, 1)

            questions_per_gap = (
                questions_answered / max(gaps_closed, 1)
                if gaps_closed > 0 else 0
            )

            phase_progression_rate = (
                (phases_completed * 100) / (days_elapsed * 1.75)  # 7 phases total
            )

            # Estimate total project duration
            remaining_gaps = max(total_gaps - gaps_closed, 0)
            if gaps_per_day > 0:
                days_to_complete = remaining_gaps / gaps_per_day
            else:
                days_to_complete = 30  # Default estimate

            estimated_project_duration = int(days_elapsed + days_to_complete)

            metrics = PerformanceMetrics(
                avg_time_per_gap=round(avg_time_per_gap, 1),
                gaps_per_day=round(gaps_per_day, 2),
                questions_per_gap=round(questions_per_gap, 2),
                phase_progression_rate=round(phase_progression_rate, 2),
                estimated_project_duration=estimated_project_duration
            )

            logger.debug(
                f"Performance analysis for {project_id}: "
                f"gaps_per_day={gaps_per_day:.2f}, "
                f"eta={estimated_project_duration} days"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return PerformanceMetrics(
                avg_time_per_gap=0.0,
                gaps_per_day=0.0,
                questions_per_gap=0.0,
                phase_progression_rate=0.0,
                estimated_project_duration=0
            )

    # ========================================================================
    # Statistical Analysis
    # ========================================================================

    def calculate_statistics(
        self,
        values: List[float]
    ) -> Dict[str, float]:
        """
        Calculate basic statistics for a list of values.

        Args:
            values: List of numeric values

        Returns:
            Dictionary with statistical measures
        """
        try:
            if not values:
                return {
                    "mean": 0.0,
                    "median": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "std_dev": 0.0,
                    "count": 0
                }

            # Sort for median
            sorted_values = sorted(values)
            n = len(sorted_values)

            # Mean
            mean = sum(values) / n

            # Median
            if n % 2 == 0:
                median = (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
            else:
                median = sorted_values[n // 2]

            # Min/Max
            min_val = min(values)
            max_val = max(values)

            # Standard deviation
            variance = sum((x - mean) ** 2 for x in values) / n
            std_dev = variance ** 0.5

            return {
                "mean": round(mean, 2),
                "median": round(median, 2),
                "min": round(min_val, 2),
                "max": round(max_val, 2),
                "std_dev": round(std_dev, 2),
                "count": n
            }

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}

    # ========================================================================
    # Comparative Benchmarking
    # ========================================================================

    def calculate_benchmark_comparison(
        self,
        project_metrics: Dict[str, Any],
        benchmark_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare project metrics to benchmarks.

        Args:
            project_metrics: Current project metrics
            benchmark_data: Benchmark metrics to compare against

        Returns:
            Comparison dictionary with deviations
        """
        try:
            comparison = {}

            for metric_name, project_value in project_metrics.items():
                benchmark_value = benchmark_data.get(metric_name)

                if benchmark_value is None or benchmark_value == 0:
                    deviation = 0.0
                    status = "no_benchmark"
                else:
                    deviation = (project_value - benchmark_value) / abs(benchmark_value)
                    if deviation > 0.2:
                        status = "above_benchmark"
                    elif deviation < -0.2:
                        status = "below_benchmark"
                    else:
                        status = "on_track"

                comparison[metric_name] = {
                    "project_value": round(project_value, 2) if isinstance(project_value, float) else project_value,
                    "benchmark_value": benchmark_value,
                    "deviation": round(deviation, 2),
                    "status": status
                }

            logger.debug(f"Benchmark comparison completed")

            return comparison

        except Exception as e:
            logger.error(f"Error calculating benchmark comparison: {e}")
            return {}

    # ========================================================================
    # Report Generation
    # ========================================================================

    def generate_progress_report(
        self,
        project_id: str,
        dashboard: DashboardMetrics,
        performance: PerformanceMetrics,
        trends: Dict[str, TrendData]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive progress report.

        Args:
            project_id: Project identifier
            dashboard: Dashboard metrics
            performance: Performance metrics
            trends: Trend data dictionary

        Returns:
            Complete progress report
        """
        try:
            report = {
                "project_id": project_id,
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "phase": dashboard.current_phase,
                    "completeness": f"{int(dashboard.completeness * 100)}%",
                    "maturity": f"{int(dashboard.maturity * 100)}%",
                    "quality": f"{int(dashboard.quality_score * 100)}/100"
                },
                "progress": {
                    "gaps_closed": int(dashboard.gap_closure_percentage * dashboard.total_gaps / 100),
                    "total_gaps": dashboard.total_gaps,
                    "questions_answered": dashboard.questions_answered,
                    "closure_percentage": f"{int(dashboard.gap_closure_percentage)}%"
                },
                "performance": {
                    "avg_time_per_gap_minutes": performance.avg_time_per_gap,
                    "gaps_per_day": performance.gaps_per_day,
                    "questions_per_gap": performance.questions_per_gap,
                    "estimated_project_duration_days": performance.estimated_project_duration
                },
                "trends": {}
            }

            # Add trend information
            for trend_name, trend_data in trends.items():
                report["trends"][trend_name] = {
                    "direction": trend_data.direction,
                    "rate_of_change": round(trend_data.rate_of_change, 3),
                    "current": round(trend_data.values[-1], 2) if trend_data.values else 0
                }

            logger.debug(f"Progress report generated for {project_id}")

            return report

        except Exception as e:
            logger.error(f"Error generating progress report: {e}")
            return {}

    # ========================================================================
    # Health Scoring
    # ========================================================================

    def calculate_project_health(
        self,
        maturity: float,
        completeness: float,
        gap_closure_percentage: float,
        quality_score: float
    ) -> Dict[str, Any]:
        """
        Calculate overall project health score.

        Factors:
        - Maturity (35%)
        - Completeness (35%)
        - Gap closure (15%)
        - Quality (15%)

        Args:
            maturity: Phase maturity (0-1)
            completeness: Specification completeness (0-1)
            gap_closure_percentage: Gap closure % (0-100)
            quality_score: Quality score (0-1)

        Returns:
            Health score and assessment
        """
        try:
            gap_closure = gap_closure_percentage / 100

            # Weighted calculation
            health_score = (
                maturity * 0.35 +
                completeness * 0.35 +
                gap_closure * 0.15 +
                quality_score * 0.15
            )

            # Determine health status
            if health_score >= 0.85:
                status = "excellent"
                color = "green"
            elif health_score >= 0.70:
                status = "good"
                color = "blue"
            elif health_score >= 0.50:
                status = "fair"
                color = "yellow"
            else:
                status = "needs_attention"
                color = "red"

            return {
                "health_score": round(health_score, 2),
                "percentage": int(health_score * 100),
                "status": status,
                "color": color,
                "components": {
                    "maturity": round(maturity, 2),
                    "completeness": round(completeness, 2),
                    "gap_closure": round(gap_closure, 2),
                    "quality": round(quality_score, 2)
                }
            }

        except Exception as e:
            logger.error(f"Error calculating project health: {e}")
            return {"health_score": 0.5, "percentage": 50, "status": "unknown"}

    # ========================================================================
    # Cache Management
    # ========================================================================

    def clear_cache(self) -> None:
        """Clear all metric caches."""
        try:
            self._metric_cache.clear()
            self._trend_cache.clear()
            logger.info("Cleared metrics service cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
