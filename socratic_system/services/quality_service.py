"""
QualityService - Business logic for quality metrics and maturity calculations.

Extracted from QualityControllerAgent.
Uses QualityRepository for all data access (not direct database calls).
Focuses on maturity calculations, analytics updates, and history tracking.
"""

import logging
from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from socratic_system.core.analytics_calculator import AnalyticsCalculator
from socratic_system.repositories.quality_repository import QualityRepository

try:
    from socratic_maturity import MaturityCalculator
except ImportError:
    MaturityCalculator = None

from .base_service import BaseService

if TYPE_CHECKING:
    from socratic_system.config import SocratesConfig
    from socratic_system.models import ProjectContext


class QualityService(BaseService):
    """
    Service for quality metrics and maturity calculations.

    Receives only required dependencies via DI (no orchestrator coupling).
    Uses repository pattern for all data access.
    """

    def __init__(self, config: "SocratesConfig", database):
        """
        Initialize quality service.

        Args:
            config: SocratesConfig instance
            database: ProjectDatabase instance for repository initialization
        """
        super().__init__(config)
        self.repository = QualityRepository(database)

        # Initialize maturity calculator
        if MaturityCalculator is None:
            raise ImportError(
                "socratic-maturity library not installed, required for QualityService"
            )

        # Get Claude client from config if available for maturity calculations
        claude_client = getattr(config, "claude_client", None)
        self.calculator = MaturityCalculator("software", claude_client=claude_client)

        # Expose calculator thresholds
        self.READY_THRESHOLD = self.calculator.READY_THRESHOLD
        self.COMPLETE_THRESHOLD = self.calculator.COMPLETE_THRESHOLD
        self.WARNING_THRESHOLD = self.calculator.WARNING_THRESHOLD

        self.logger.info(
            f"QualityService initialized with thresholds: "
            f"READY={self.READY_THRESHOLD}%, "
            f"COMPLETE={self.COMPLETE_THRESHOLD}%, "
            f"WARNING={self.WARNING_THRESHOLD}%"
        )

    def update_maturity_after_response(
        self,
        project_id: str,
        project: "ProjectContext",
        insights: Dict[str, Any],
        current_user: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update maturity scores after Q&A response.

        Uses incremental scoring: each answer contributes score = sum(spec_value * confidence).
        This prevents low-confidence specs from affecting previous answers.

        Args:
            project_id: Project ID
            project: ProjectContext object with current state
            insights: Dict of insights from user response
            current_user: User ID for API key lookup

        Returns:
            Dict with update status and score changes
        """
        self._log_operation(
            "update_maturity_after_response",
            {"project_id": project_id, "phase": project.phase},
        )

        try:
            # Capture score before changes
            score_before = project.phase_maturity_scores.get(project.phase, 0.0)

            # Categorize insights into specs
            self.logger.debug("Categorizing insights")
            categorized = self.calculator.categorize_insights(
                insights, project.phase, user_id=current_user
            )

            if not categorized:
                self.logger.debug("No specs categorized from insights")
                return {"status": "success", "message": "No new specs added"}

            # Calculate answer score (sum of spec values × confidence)
            answer_score = 0.0
            for spec in categorized:
                confidence = spec.get("confidence", 0.9)
                value = spec.get("value", 1.0)
                spec_score = value * confidence
                answer_score += spec_score
                self.logger.debug(f"Spec score: {value} × {confidence:.2f} = {spec_score:.2f}")

            self.logger.info(
                f"Answer score: {answer_score:.2f} from {len(categorized)} specs"
            )

            # Add specs to project
            self.repository.add_categorized_specs(
                project_id, project.phase, categorized
            )

            # Update phase maturity (clamped to 100)
            score_after = min(100.0, score_before + answer_score)
            self.repository.update_phase_maturity_score(project_id, project.phase, score_after)

            # Recalculate overall maturity
            project.overall_maturity = project._calculate_overall_maturity()
            project.progress = int(project.overall_maturity)

            # Record event in history
            delta = score_after - score_before
            self._record_maturity_event(
                project_id,
                event_type="response_processed",
                phase=project.phase,
                score_before=score_before,
                score_after=score_after,
                delta=delta,
                details={"specs_added": len(categorized), "answer_score": answer_score},
            )

            # Update analytics
            self.update_analytics_metrics(project_id, project)

            self.logger.info(
                f"Maturity updated: {len(categorized)} specs, "
                f"phase_score: {score_before:.1f}% → {score_after:.1f}% "
                f"(delta: +{delta:.2f}%)"
            )

            return {
                "status": "success",
                "message": "Maturity updated",
                "answer_score": answer_score,
                "score_before": score_before,
                "score_after": score_after,
            }

        except ValueError as e:
            self.logger.error(f"ValueError updating maturity: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            self.logger.error(f"Error updating maturity: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}

    def calculate_phase_maturity(
        self, project_id: str, project: "ProjectContext", phase: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate maturity for a specific phase.

        Uses saved maturity scores (from incremental scoring), not recalculation.

        Args:
            project_id: Project ID
            project: ProjectContext object
            phase: Phase name (defaults to project's current phase)

        Returns:
            Dict with maturity calculation results
        """
        self._log_operation("calculate_phase_maturity", {"project_id": project_id})

        if phase is None:
            phase = project.phase

        try:
            # Set calculator to project's type
            if project.project_type != self.calculator.project_type:
                self.logger.debug(
                    f"Switching calculator from {self.calculator.project_type} "
                    f"to {project.project_type}"
                )
                self.calculator.set_project_type(project.project_type)

            # Get saved maturity score
            saved_score = project.phase_maturity_scores.get(phase, 0.0)
            self.logger.debug(f"Using saved score for {phase}: {saved_score:.1f}%")

            # Get specs for category breakdown
            phase_specs = project.categorized_specs.get(phase, [])
            self.logger.debug(f"Found {len(phase_specs)} specs for phase {phase}")

            # Calculate category breakdown
            spec_maturity = self.calculator.calculate_phase_maturity(phase_specs, phase)

            # Update category scores in repository
            category_dict = {
                cat: dict(score) if hasattr(score, "__dict__") else score
                for cat, score in spec_maturity.category_scores.items()
            }
            self.repository.update_category_scores(project_id, phase, category_dict)

            self.logger.info(
                f"Phase {phase} maturity: {saved_score:.1f}% "
                f"(overall: {project.overall_maturity:.1f}%)"
            )

            return {"status": "success", "maturity": asdict(spec_maturity)}

        except ValueError as e:
            self.logger.error(f"ValueError calculating maturity: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            self.logger.error(f"Error calculating maturity: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}

    def get_maturity_summary(self, project_id: str, project: "ProjectContext") -> Dict[str, Any]:
        """
        Get maturity summary across all phases.

        Args:
            project_id: Project ID
            project: ProjectContext object

        Returns:
            Dict with maturity summary for all phases
        """
        self._log_operation("get_maturity_summary", {"project_id": project_id})

        try:
            summary = {}
            for phase in ["discovery", "analysis", "design", "implementation"]:
                score = project.phase_maturity_scores.get(phase, 0.0)
                summary[phase] = {
                    "score": score,
                    "ready": score >= self.READY_THRESHOLD,
                    "complete": score >= self.COMPLETE_THRESHOLD,
                }
                self.logger.debug(
                    f"Phase {phase}: {score:.1f}%, "
                    f"ready={score >= self.READY_THRESHOLD}, "
                    f"complete={score >= self.COMPLETE_THRESHOLD}"
                )

            return {"status": "success", "summary": summary}

        except Exception as e:
            self.logger.error(f"Error getting maturity summary: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}

    def get_maturity_history(self, project_id: str) -> Dict[str, Any]:
        """
        Get maturity progression history.

        Args:
            project_id: Project ID

        Returns:
            Dict with maturity history events
        """
        self._log_operation("get_maturity_history", {"project_id": project_id})

        try:
            history = self.repository.get_maturity_history(project_id)
            self.logger.info(f"Retrieved maturity history: {len(history)} events")
            return {
                "status": "success",
                "history": history,
                "total_events": len(history),
            }
        except Exception as e:
            self.logger.error(f"Error getting maturity history: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}

    def update_analytics_metrics(
        self, project_id: str, project: "ProjectContext"
    ) -> bool:
        """
        Update analytics metrics (velocity, confidence, categories).

        Args:
            project_id: Project ID
            project: ProjectContext object

        Returns:
            True if successful, False otherwise
        """
        self._log_operation("update_analytics_metrics", {"project_id": project_id})

        try:
            metrics = {}

            # Calculate velocity
            qa_events = [
                e for e in project.maturity_history
                if e.get("event_type") == "response_processed"
            ]
            if qa_events:
                total_gain = sum(e.get("delta", 0.0) for e in qa_events)
                velocity = total_gain / len(qa_events)
                metrics["velocity"] = velocity
                self.logger.debug(f"Calculated velocity: {velocity:.2f} points/session")

            metrics["total_qa_sessions"] = len(qa_events)

            # Calculate average confidence
            all_specs = []
            for phase_specs in project.categorized_specs.values():
                if isinstance(phase_specs, list):
                    all_specs.extend(phase_specs)

            if all_specs:
                avg_conf = sum(s.get("confidence", 0.9) for s in all_specs) / len(
                    all_specs
                )
                metrics["avg_confidence"] = avg_conf
                self.logger.debug(f"Average confidence: {avg_conf:.3f}")

            # Identify weak/strong categories
            calculator = AnalyticsCalculator(project.project_type)
            weak = calculator.identify_weak_categories(project)
            strong = calculator.identify_strong_categories(project)
            metrics["weak_categories"] = weak
            metrics["strong_categories"] = strong
            self.logger.debug(f"Identified {len(weak)} weak and {len(strong)} strong categories")

            metrics["last_updated"] = datetime.now().isoformat()

            # Update in repository
            return self.repository.update_analytics_metrics(project_id, metrics)

        except Exception as e:
            self.logger.error(
                f"Error updating analytics metrics: {type(e).__name__}: {e}"
            )
            return False

    def _record_maturity_event(
        self,
        project_id: str,
        event_type: str,
        phase: str,
        score_before: float,
        score_after: float,
        delta: float,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Record a maturity event in history.

        Args:
            project_id: Project ID
            event_type: Type of event (response_processed, phase_advanced, etc.)
            phase: Phase name
            score_before: Score before event
            score_after: Score after event
            delta: Score change
            details: Additional event details

        Returns:
            True if successful, False otherwise
        """
        if details is None:
            details = {}

        event = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "score_before": score_before,
            "score_after": score_after,
            "delta": delta,
            "event_type": event_type,
            "details": details,
        }

        return self.repository.add_maturity_event(project_id, event)
