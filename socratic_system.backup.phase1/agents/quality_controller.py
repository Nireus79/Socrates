"""
Quality Controller Agent - Orchestrates maturity tracking and prevents greedy algorithm practices
"""

import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, Optional

from socratic_system.core.analytics_calculator import AnalyticsCalculator
from socratic_system.core.maturity_calculator import MaturityCalculator
from socratic_system.core.workflow_optimizer import WorkflowOptimizer
from socratic_system.events import EventType
from socratic_system.models import ProjectContext
from socratic_system.models.workflow import WorkflowApprovalRequest

from .base import Agent


class QualityControllerAgent(Agent):
    """
    Quality Control Agent - Orchestrates maturity tracking and prevents greedy algorithm practices.

    Uses MaturityCalculator for pure calculation logic and focuses on:
    - Orchestrating maturity updates during Q&A sessions
    - Emitting events for real-time maturity updates
    - Recording maturity history and events
    - Managing project context updates
    """

    def __init__(self, orchestrator):
        super().__init__("QualityController", orchestrator)
        logging.debug("Initializing QualityControllerAgent")

        # Initialize the pure calculation engine with Claude client for intelligent categorization
        claude_client = (
            orchestrator.claude_client if hasattr(orchestrator, "claude_client") else None
        )
        logging.debug(
            f"Creating MaturityCalculator with Claude client: {claude_client is not None}"
        )
        self.calculator = MaturityCalculator("software", claude_client=claude_client)

        # Expose calculator's phase categories and thresholds for reference
        self.phase_categories = self.calculator.phase_categories
        self.READY_THRESHOLD = self.calculator.READY_THRESHOLD
        self.COMPLETE_THRESHOLD = self.calculator.COMPLETE_THRESHOLD
        self.WARNING_THRESHOLD = self.calculator.WARNING_THRESHOLD

        # Initialize workflow optimizer for workflow optimization system
        logging.debug("Initializing WorkflowOptimizer")
        self.workflow_optimizer = WorkflowOptimizer()

        # Track pending workflow approval requests
        self.pending_approvals: Dict[str, WorkflowApprovalRequest] = {}
        logging.debug("Initialized pending_approvals dictionary")

        logging.info(
            f"QualityControllerAgent initialized with thresholds: READY={self.READY_THRESHOLD}%, COMPLETE={self.COMPLETE_THRESHOLD}%, WARNING={self.WARNING_THRESHOLD}%"
        )

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process quality control requests"""
        logging.debug(f"QualityController processing request: {list(request.keys())}")
        action = request.get("action")
        logging.debug(f"Action: {action}")

        if action == "calculate_maturity":
            logging.debug("Routing to _calculate_phase_maturity")
            return self._calculate_phase_maturity(request)
        elif action == "get_phase_maturity":
            logging.debug("Routing to _calculate_phase_maturity (get_phase_maturity)")
            return self._calculate_phase_maturity(request)
        elif action == "get_readiness":
            logging.debug("Routing to _get_phase_readiness")
            return self._get_phase_readiness(request)
        elif action == "update_after_response":
            logging.debug("Routing to _update_maturity_after_response")
            return self._update_maturity_after_response(request)
        elif action == "get_maturity_summary":
            logging.debug("Routing to _get_maturity_summary")
            return self._get_maturity_summary(request)
        elif action == "verify_advancement":
            logging.debug("Routing to _verify_advancement")
            return self._verify_advancement(request)
        elif action == "get_history":
            logging.debug("Routing to _get_maturity_history")
            return self._get_maturity_history(request)
        # Workflow optimization actions
        elif action == "request_workflow_approval":
            logging.debug("Routing to _request_workflow_approval")
            return self._request_workflow_approval(request)
        elif action == "approve_workflow":
            logging.debug("Routing to _approve_workflow")
            return self._approve_workflow(request)
        elif action == "reject_workflow":
            logging.debug("Routing to _reject_workflow")
            return self._reject_workflow(request)
        elif action == "get_pending_approvals":
            logging.debug("Routing to _get_pending_approvals")
            return self._get_pending_approvals(request)

        logging.error(f"Unknown action: {action}")
        return {"status": "error", "message": f"Unknown action: {action}"}

    def _calculate_phase_maturity(self, request: Dict) -> Dict:
        """
        Calculate maturity for current phase.

        Returns the SAVED maturity score (from incremental scoring), not recalculated from specs.
        This preserves the incremental scoring logic used during Q&A sessions.
        """
        logging.debug("_calculate_phase_maturity called")
        project = request.get("project")
        phase = request.get("phase", project.phase)

        logging.info(f"Calculating maturity for phase: {phase}, project: {project.name}")

        try:
            # Set calculator to project's type to get appropriate categories
            if project.project_type != self.calculator.project_type:
                logging.debug(
                    f"Switching calculator from {self.calculator.project_type} to {project.project_type}"
                )
                self.calculator.set_project_type(project.project_type)

            # Get the SAVED maturity score (from incremental scoring, NOT recalculation)
            saved_score = project.phase_maturity_scores.get(phase, 0.0)
            logging.debug(f"Using saved maturity score for phase {phase}: {saved_score:.1f}%")

            # Get specs for category breakdown (analysis only, not for score)
            phase_specs = project.categorized_specs.get(phase, [])
            logging.debug(f"Found {len(phase_specs)} specs for phase {phase}")

            # Use calculator to get category breakdown (for analysis/warnings only)
            logging.debug("Calculating category breakdown from specs")
            spec_maturity = self.calculator.calculate_phase_maturity(phase_specs, phase)

            # Create a maturity object with the SAVED score but spec analysis
            # This preserves incremental scoring while providing category details
            maturity = spec_maturity
            maturity.overall_score = saved_score  # Use saved score, not recalculated

            # Update category scores from analysis (for reference only)
            project.category_scores[phase] = {
                cat: asdict(score) for cat, score in maturity.category_scores.items()
            }

            # Overall maturity stays as-is (already calculated in _update_maturity_after_response)
            logging.info(
                f"Maturity for phase {phase}: {saved_score:.1f}% (saved), overall = {project.overall_maturity:.1f}%"
            )

            # Emit maturity updated event
            logging.debug("Emitting PHASE_MATURITY_UPDATED event")
            self.emit_event(
                EventType.PHASE_MATURITY_UPDATED,
                {
                    "phase": phase,
                    "score": saved_score,
                    "ready": saved_score >= self.READY_THRESHOLD,
                    "complete": saved_score >= self.COMPLETE_THRESHOLD,
                },
            )

            # If phase is at 100%, notify user
            if saved_score >= self.COMPLETE_THRESHOLD:
                logging.info(f"Phase {phase} reached 100% completion!")
                self.emit_event(
                    EventType.PHASE_READY_TO_ADVANCE,
                    {
                        "phase": phase,
                        "message": f"{phase.capitalize()} phase is 100% complete! You can advance or continue enriching.",
                    },
                )

            return {"status": "success", "maturity": asdict(maturity)}

        except ValueError as e:
            logging.error(f"ValueError in maturity calculation: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logging.error(f"Unexpected error in maturity calculation: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}

    def _update_maturity_after_response(self, request: Dict) -> Dict:
        """Called after each question/response to update maturity

        IMPORTANT: Uses incremental scoring instead of full recalculation.
        Each answer gets a score: answer_score = sum(spec_value * confidence)
        Then: overall_maturity += answer_score

        This prevents low-confidence specs from pulling down previous answers' scores.
        """
        logging.debug("_update_maturity_after_response called")
        project = request.get("project")
        insights = request.get("insights")
        current_user = request.get("current_user")

        logging.debug(
            f"Processing response with {len(insights)} insight fields for user {current_user}"
        )

        # Capture score BEFORE adding new specs
        score_before = project.phase_maturity_scores.get(project.phase, 0.0)

        # Use calculator to categorize the new insights (pass user_id for API key lookup)
        logging.debug("Categorizing insights")
        categorized = self.calculator.categorize_insights(
            insights, project.phase, user_id=current_user
        )
        logging.info(f"Insights categorized into {len(categorized)} specs")

        if not categorized:
            logging.debug("No specs categorized, returning")
            return {"status": "success", "message": "No new specs added"}

        # Calculate score contribution for THIS answer
        # score = sum(spec_value * confidence) for all specs in this response
        logging.debug("Calculating answer score from categorized specs")
        answer_score = 0.0
        for spec in categorized:
            confidence = spec.get("confidence", 0.9)
            value = spec.get("value", 1.0)
            spec_score = value * confidence
            answer_score += spec_score
            logging.debug(f"Spec score: {value} × {confidence:.2f} = {spec_score:.2f}")

        logging.info(f"Answer score: {answer_score:.2f} (from {len(categorized)} specs)")

        # Add to project's categorized specs for reference
        if project.phase not in project.categorized_specs:
            project.categorized_specs[project.phase] = []
        project.categorized_specs[project.phase].extend(categorized)

        logging.debug(f"Added {len(categorized)} specs to phase {project.phase}")

        # Instead of recalculating entire maturity, ADD this answer's score
        # This prevents previous answers' scores from being affected by new specs' confidence
        score_after = min(100.0, score_before + answer_score)
        project.phase_maturity_scores[project.phase] = score_after

        # Calculate and update overall maturity
        project.overall_maturity = project._calculate_overall_maturity()

        # Auto-update progress to match overall maturity
        project.progress = int(project.overall_maturity)

        # Notify user if phase just reached 100% completion
        if score_before < self.COMPLETE_THRESHOLD and score_after >= self.COMPLETE_THRESHOLD:
            logging.info(f"Phase {project.phase} reached 100% completion during response processing!")
            self.emit_event(
                EventType.PHASE_READY_TO_ADVANCE,
                {
                    "phase": project.phase,
                    "message": f"{project.phase.capitalize()} phase is 100% complete! You can advance or continue enriching.",
                },
            )

        # Record in history with before/after scores
        logging.debug("Recording maturity event in history")
        delta = score_after - score_before
        self._record_maturity_event(
            project,
            event_type="response_processed",
            score_before=score_before,
            score_after=score_after,
            delta=delta,
            details={"specs_added": len(categorized), "answer_score": answer_score},
        )

        # Update analytics metrics
        logging.debug("Updating analytics metrics")
        self._update_analytics_metrics(project)

        logging.info(
            f"Response processed: {len(categorized)} specs added, answer_score={answer_score:.2f}, "
            f"phase_maturity: {score_before:.1f}% → {score_after:.1f}% (delta: +{delta:.2f}%)"
        )

        return {
            "status": "success",
            "message": "Maturity updated",
            "answer_score": answer_score,
            "score_before": score_before,
            "score_after": score_after,
        }

    def _update_analytics_metrics(self, project: ProjectContext) -> None:
        """Update real-time analytics metrics after maturity change."""
        logging.debug("Updating analytics metrics")
        try:
            # Calculate velocity
            logging.debug("Calculating velocity from maturity history")
            qa_events = [
                e for e in project.maturity_history if e.get("event_type") == "response_processed"
            ]
            if qa_events:
                total_gain = sum(e.get("delta", 0.0) for e in qa_events)
                velocity = total_gain / len(qa_events)
                project.analytics_metrics["velocity"] = velocity
                logging.debug(
                    f"Calculated velocity: {velocity:.2f} points/session from {len(qa_events)} sessions"
                )

            project.analytics_metrics["total_qa_sessions"] = len(qa_events)

            # Calculate average confidence
            logging.debug("Calculating average confidence")
            all_specs = []
            for phase_specs in project.categorized_specs.values():
                if isinstance(phase_specs, list):
                    all_specs.extend(phase_specs)

            if all_specs:
                avg_conf = sum(s.get("confidence", 0.9) for s in all_specs) / len(all_specs)
                project.analytics_metrics["avg_confidence"] = avg_conf
                logging.debug(
                    f"Average confidence: {avg_conf:.3f} from {len(all_specs)} total specs"
                )

            # Update weak/strong categories
            logging.debug("Identifying weak/strong categories")
            calculator = AnalyticsCalculator(project.project_type)
            weak = calculator.identify_weak_categories(project)
            strong = calculator.identify_strong_categories(project)
            project.analytics_metrics["weak_categories"] = weak
            project.analytics_metrics["strong_categories"] = strong
            logging.debug(f"Identified {len(weak)} weak and {len(strong)} strong categories")

            project.analytics_metrics["last_updated"] = datetime.now().isoformat()
            logging.info("Analytics metrics updated successfully")

        except Exception as e:
            logging.error(f"Failed to update analytics metrics: {type(e).__name__}: {e}")

    def _record_maturity_event(
        self,
        project: ProjectContext,
        event_type: str,
        score_before: Optional[float] = None,
        score_after: Optional[float] = None,
        delta: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a maturity event in history with proper before/after scores"""
        logging.debug(f"Recording maturity event: {event_type}")

        if details is None:
            details = {}

        # Use provided scores or calculate from project state
        if score_before is None:
            score_before = project.phase_maturity_scores.get(project.phase, 0.0)
        if score_after is None:
            score_after = project.phase_maturity_scores.get(project.phase, 0.0)
        if delta is None:
            delta = score_after - score_before

        event = {
            "timestamp": datetime.now().isoformat(),
            "phase": project.phase,
            "score_before": score_before,
            "score_after": score_after,
            "delta": delta,
            "event_type": event_type,
            "details": details,
        }

        project.maturity_history.append(event)
        logging.debug(
            f"Event recorded: {event_type} at {event['timestamp']}, score: {score_before:.1f}% → {score_after:.1f}% (delta: {delta:+.1f}%)"
        )

    def _verify_advancement(self, request: Dict) -> Dict:
        """
        Verify phase readiness and generate warnings.

        Always returns success - never blocks advancement.
        Provides warnings and recommendations only.
        """
        logging.debug("_verify_advancement called")
        project = request.get("project")
        from_phase = request.get("from_phase")

        logging.info(f"Verifying phase advancement from: {from_phase}")

        # Calculate current phase maturity
        maturity_result = self._calculate_phase_maturity({"project": project, "phase": from_phase})

        if maturity_result["status"] != "success":
            logging.error(
                f"Failed to calculate maturity for advancement verification: {maturity_result}"
            )
            return maturity_result

        maturity = maturity_result["maturity"]
        score = maturity["overall_score"]

        # Generate warnings (from maturity object)
        warnings = maturity.get("warnings", [])

        logging.info(
            f"Phase {from_phase} advancement verification: score={score:.1f}%, warnings={len(warnings)}"
        )

        # Emit quality check event
        if warnings:
            logging.debug("Emitting QUALITY_CHECK_WARNING event")
            self.emit_event(
                EventType.QUALITY_CHECK_WARNING,
                {
                    "phase": from_phase,
                    "score": score,
                    "warnings": warnings,
                },
            )
        else:
            logging.debug("Emitting QUALITY_CHECK_PASSED event")
            self.emit_event(
                EventType.QUALITY_CHECK_PASSED,
                {
                    "phase": from_phase,
                    "score": score,
                },
            )

        return {
            "status": "success",
            "verification": {
                "maturity_score": score,
                "warnings": warnings,
                "missing_categories": maturity.get("missing_categories", []),
                "ready": score >= self.READY_THRESHOLD,
                "complete": score >= self.COMPLETE_THRESHOLD,
                "details": maturity,
            },
        }

    def _get_phase_readiness(self, request: Dict) -> Dict:
        """Get readiness assessment for a specific phase"""
        logging.debug("_get_phase_readiness called")
        project = request.get("project")
        phase = request.get("phase", project.phase)

        logging.info(f"Getting readiness assessment for phase: {phase}")

        return self._verify_advancement({"project": project, "from_phase": phase})

    def _get_maturity_summary(self, request: Dict) -> Dict:
        """Get summary of maturity across all phases"""
        logging.debug("_get_maturity_summary called")
        project = request.get("project")

        logging.info(f"Generating maturity summary for project: {project.name}")

        summary = {}
        for phase in ["discovery", "analysis", "design", "implementation"]:
            score = project.phase_maturity_scores.get(phase, 0.0)
            summary[phase] = {
                "score": score,
                "ready": score >= self.READY_THRESHOLD,
                "complete": score >= self.COMPLETE_THRESHOLD,
            }
            logging.debug(
                f"Phase {phase}: {score:.1f}%, ready={score >= self.READY_THRESHOLD}, complete={score >= self.COMPLETE_THRESHOLD}"
            )

        return {"status": "success", "summary": summary}

    def _get_maturity_history(self, request: Dict) -> Dict:
        """Get maturity progression history"""
        logging.debug("_get_maturity_history called")
        project = request.get("project")

        logging.info(
            f"Retrieving maturity history for project: {project.name}, total_events={len(project.maturity_history)}"
        )

        return {
            "status": "success",
            "history": project.maturity_history,
            "total_events": len(project.maturity_history),
        }

    # ========================================================================
    # Workflow Approval Methods (Phase 4)
    # ========================================================================

    def _request_workflow_approval(self, request: Dict) -> Dict:
        """
        Request workflow approval - BLOCKING POINT

        Runs optimizer to enumerate paths, calculate metrics, recommend optimal path,
        and returns pending status that halts execution until user approves.

        Args:
            request: Dict with keys:
                - project: ProjectContext
                - workflow: WorkflowDefinition

        Returns:
            Dict with status "pending_approval" (execution halts)
        """
        logging.debug("_request_workflow_approval called")

        try:
            project = request.get("project")
            workflow = request.get("workflow")

            if not project:
                logging.error("Project not provided in approval request")
                return {"status": "error", "message": "Project required"}

            if not workflow:
                logging.error("Workflow not provided in approval request")
                return {"status": "error", "message": "Workflow required"}

            logging.info(
                f"Requesting workflow approval for project: {project.name}, "
                f"workflow: {workflow.workflow_id}, phase: {workflow.phase}"
            )

            # Run optimizer to enumerate and evaluate all paths
            logging.debug("Running workflow optimizer")
            approval_request = self.workflow_optimizer.optimize_workflow(
                workflow=workflow,
                project=project,
                strategy=request.get("strategy", workflow.strategy),
                requested_by=request.get("requested_by", "quality_controller"),
            )

            # Store as pending approval
            self.pending_approvals[approval_request.request_id] = approval_request
            logging.info(
                f"Approval request created: {approval_request.request_id}, "
                f"paths: {len(approval_request.all_paths)}, "
                f"recommended: {approval_request.recommended_path.path_id}"
            )

            # Emit event for UI/notification
            logging.debug("Emitting WORKFLOW_APPROVAL_REQUESTED event")
            self.emit_event(
                EventType.WORKFLOW_APPROVAL_REQUESTED,
                {
                    "request_id": approval_request.request_id,
                    "project_id": project.project_id,
                    "phase": approval_request.phase,
                    "path_count": len(approval_request.all_paths),
                    "recommended_path_id": approval_request.recommended_path.path_id,
                },
            )

            # Return BLOCKING status - execution stops here until approval
            return {
                "status": "pending_approval",
                "request_id": approval_request.request_id,
                "approval_request": asdict(approval_request),
                "message": "Workflow approval required before proceeding",
            }

        except ValueError as e:
            logging.error(f"ValueError in workflow approval request: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logging.error(f"Unexpected error in workflow approval request: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}

    def _approve_workflow(self, request: Dict) -> Dict:
        """
        Approve a workflow path and unblock execution

        Marks the approval request as approved, sets the approved path,
        and removes from pending list to allow execution to resume.

        Args:
            request: Dict with keys:
                - request_id: ID of approval request
                - approved_path_id: ID of path to approve
                - project: Optional ProjectContext for logging

        Returns:
            Dict with status "success" (execution resumes)
        """
        logging.debug("_approve_workflow called")

        try:
            request_id = request.get("request_id")
            approved_path_id = request.get("approved_path_id")

            if not request_id:
                logging.error("request_id not provided in approval")
                return {"status": "error", "message": "request_id required"}

            if not approved_path_id:
                logging.error("approved_path_id not provided in approval")
                return {"status": "error", "message": "approved_path_id required"}

            # Get approval request from pending
            approval_request = self.pending_approvals.get(request_id)
            if not approval_request:
                logging.error(f"Approval request not found: {request_id}")
                return {"status": "error", "message": "Approval request not found"}

            logging.info(
                f"Approving workflow request: {request_id}, " f"approved path: {approved_path_id}"
            )

            # Mark as approved
            approval_request.status = "approved"
            approval_request.approved_path_id = approved_path_id
            approval_request.approval_timestamp = datetime.now().isoformat()

            # Remove from pending
            del self.pending_approvals[request_id]
            logging.debug("Removed request from pending_approvals")

            # Emit approval event
            logging.debug("Emitting WORKFLOW_APPROVED event")
            self.emit_event(
                EventType.WORKFLOW_APPROVED,
                {
                    "request_id": request_id,
                    "approved_path_id": approved_path_id,
                    "timestamp": approval_request.approval_timestamp,
                },
            )

            logging.info("Workflow approval completed successfully")

            return {
                "status": "success",
                "request_id": request_id,
                "approved_path_id": approved_path_id,
                "message": "Workflow approved and execution may proceed",
            }

        except Exception as e:
            logging.error(f"Unexpected error approving workflow: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}

    def _reject_workflow(self, request: Dict) -> Dict:
        """
        Reject a workflow and request alternatives

        Marks approval request as rejected and removes from pending.
        Caller should generate alternative workflows or prompt user.

        Args:
            request: Dict with keys:
                - request_id: ID of approval request
                - reason: Optional rejection reason
                - project: Optional ProjectContext

        Returns:
            Dict with status "success"
        """
        logging.debug("_reject_workflow called")

        try:
            request_id = request.get("request_id")
            reason = request.get("reason", "No reason provided")

            if not request_id:
                logging.error("request_id not provided in rejection")
                return {"status": "error", "message": "request_id required"}

            # Get approval request from pending
            approval_request = self.pending_approvals.get(request_id)
            if not approval_request:
                logging.error(f"Approval request not found: {request_id}")
                return {"status": "error", "message": "Approval request not found"}

            logging.info(f"Rejecting workflow request: {request_id}, reason: {reason}")

            # Mark as rejected
            approval_request.status = "rejected"
            approval_request.approval_timestamp = datetime.now().isoformat()

            # Remove from pending
            del self.pending_approvals[request_id]
            logging.debug("Removed request from pending_approvals")

            # Emit rejection event
            logging.debug("Emitting WORKFLOW_REJECTED event")
            self.emit_event(
                EventType.WORKFLOW_REJECTED,
                {
                    "request_id": request_id,
                    "reason": reason,
                    "timestamp": approval_request.approval_timestamp,
                },
            )

            logging.info("Workflow rejection completed successfully")

            return {
                "status": "success",
                "request_id": request_id,
                "reason": reason,
                "message": "Workflow rejected - alternatives may be requested",
            }

        except Exception as e:
            logging.error(f"Unexpected error rejecting workflow: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}

    def _get_pending_approvals(self, request: Dict) -> Dict:
        """
        Get list of pending workflow approval requests

        Returns all approval requests currently awaiting user decision.

        Args:
            request: Dict with optional keys:
                - project_id: Filter by project (optional)

        Returns:
            Dict with status "success" and list of pending approvals
        """
        logging.debug("_get_pending_approvals called")

        try:
            project_id = request.get("project_id")

            # Filter by project if specified
            pending = list(self.pending_approvals.values())
            if project_id:
                pending = [a for a in pending if a.project_id == project_id]

            logging.info(
                f"Retrieved {len(pending)} pending approval requests"
                + (f" for project: {project_id}" if project_id else "")
            )

            # Convert to dict for JSON serialization
            pending_dicts = [asdict(a) for a in pending]

            return {
                "status": "success",
                "pending_approvals": pending_dicts,
                "total_count": len(pending_dicts),
            }

        except Exception as e:
            logging.error(f"Unexpected error retrieving pending approvals: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}
