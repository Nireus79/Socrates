"""
Workflow optimizer orchestrating path enumeration, cost/risk calculation, and path selection

Main engine for evaluating all workflow paths and recommending the optimal one
based on the selected strategy.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from socratic_system.core.workflow_cost_calculator import WorkflowCostCalculator
from socratic_system.core.workflow_path_finder import WorkflowPathFinder
from socratic_system.core.workflow_risk_calculator import WorkflowRiskCalculator
from socratic_system.models.project import ProjectContext
from socratic_system.models.workflow import (
    PathDecisionStrategy,
    WorkflowApprovalRequest,
    WorkflowDefinition,
    WorkflowPath,
)

logger = logging.getLogger(__name__)


class WorkflowOptimizer:
    """Orchestrates workflow optimization including path enumeration and selection"""

    def __init__(self):
        """Initialize optimizer with calculation components"""
        self.path_finder_class = WorkflowPathFinder
        self.cost_calculator = WorkflowCostCalculator()
        self.risk_calculator = WorkflowRiskCalculator()

        logger.debug("WorkflowOptimizer initialized")

    def optimize_workflow(
        self,
        workflow: WorkflowDefinition,
        project: ProjectContext,
        strategy: PathDecisionStrategy,
        requested_by: str = "system",
    ) -> WorkflowApprovalRequest:
        """
        Main entry point for workflow optimization.

        Enumerates all paths, calculates metrics, selects optimal path,
        and returns approval request.

        Args:
            workflow: WorkflowDefinition to optimize
            project: ProjectContext for context information
            strategy: PathDecisionStrategy to use for selection
            requested_by: User/agent requesting optimization

        Returns:
            WorkflowApprovalRequest with all paths and recommendation

        Raises:
            ValueError: If workflow is invalid or no paths found
        """
        logger.info(
            f"Starting workflow optimization for {workflow.workflow_id} "
            f"using strategy {strategy.value}"
        )

        # Step 1: Find all paths
        logger.debug("Step 1: Enumerating workflow paths")
        all_paths = self._find_all_paths(workflow)

        if not all_paths:
            logger.error(f"No paths found for workflow {workflow.workflow_id}")
            raise ValueError(f"Workflow {workflow.workflow_id} has no valid paths")

        logger.info(f"Found {len(all_paths)} paths for workflow")

        # Step 2: Calculate metrics for each path
        logger.debug("Step 2: Calculating metrics for each path")
        all_paths = self._calculate_path_metrics(all_paths, workflow, project)

        # Step 3: Select optimal path
        logger.debug("Step 3: Selecting optimal path")
        recommended_path = self._select_optimal_path(all_paths, strategy)

        # Step 4: Create approval request
        logger.debug("Step 4: Creating approval request")
        approval_request = WorkflowApprovalRequest(
            request_id=f"wf_approval_{uuid.uuid4().hex[:8]}",
            project_id=project.project_id,
            phase=project.phase,
            workflow=workflow,
            all_paths=all_paths,
            recommended_path=recommended_path,
            strategy=strategy,
            created_at=datetime.now().isoformat(),
            requested_by=requested_by,
            status="pending",
        )

        logger.info(
            f"Workflow optimization complete. "
            f"Recommended path: {recommended_path.path_id} "
            f"(cost: {recommended_path.total_cost_tokens} tokens, "
            f"risk: {recommended_path.risk_score:.1f}%)"
        )

        return approval_request

    def _find_all_paths(self, workflow: WorkflowDefinition) -> List[WorkflowPath]:
        """
        Find all valid paths through workflow graph.

        Args:
            workflow: WorkflowDefinition

        Returns:
            List of WorkflowPath objects

        Raises:
            ValueError: If workflow is invalid
        """
        if not workflow.start_node:
            raise ValueError("Workflow must have a start_node")

        if not workflow.end_nodes:
            raise ValueError("Workflow must have end_nodes")

        finder = self.path_finder_class(workflow)
        return finder.find_all_paths()

    def _calculate_path_metrics(
        self,
        paths: List[WorkflowPath],
        workflow: WorkflowDefinition,
        project: ProjectContext,
    ) -> List[WorkflowPath]:
        """
        Calculate cost, risk, and quality metrics for all paths.

        Args:
            paths: List of paths to evaluate
            workflow: WorkflowDefinition
            project: ProjectContext

        Returns:
            Updated paths with calculated metrics
        """
        for path in paths:
            # Calculate cost
            cost_metrics = self.cost_calculator.calculate_path_cost(path, workflow)
            path.total_cost_tokens = cost_metrics["total_tokens"]
            path.total_cost_usd = cost_metrics["total_cost_usd"]

            # Calculate risk
            risk_metrics = self.risk_calculator.calculate_path_risk(
                path, workflow, project
            )
            path.risk_score = risk_metrics["risk_score"]
            path.incompleteness_risk = risk_metrics["incompleteness_risk"]
            path.complexity_risk = risk_metrics["complexity_risk"]
            path.rework_probability = risk_metrics["rework_probability"]
            path.missing_categories = risk_metrics["missing_categories"]

            # Calculate quality and ROI
            path.quality_score = self._calculate_quality_score(path, project)
            path.expected_maturity_gain = self._calculate_expected_maturity_gain(
                path, project
            )
            path.roi_score = self._calculate_roi(
                path, cost_metrics["total_tokens"], path.expected_maturity_gain
            )

            logger.debug(
                f"Path {path.path_id}: {path.total_cost_tokens} tokens, "
                f"risk={path.risk_score:.1f}, quality={path.quality_score:.1f}, "
                f"roi={path.roi_score:.2f}"
            )

        return paths

    def _select_optimal_path(
        self, paths: List[WorkflowPath], strategy: PathDecisionStrategy
    ) -> WorkflowPath:
        """
        Select best path based on strategy.

        Strategies:
        - MINIMIZE_COST: Lowest token count
        - MINIMIZE_RISK: Lowest risk score
        - BALANCED: 50% cost, 30% risk, 20% quality
        - MAXIMIZE_QUALITY: Highest quality score
        - USER_CHOICE: Return first (user will choose)

        Args:
            paths: List of evaluated paths
            strategy: Selection strategy

        Returns:
            Recommended WorkflowPath
        """
        if not paths:
            raise ValueError("Cannot select from empty path list")

        if strategy == PathDecisionStrategy.MINIMIZE_COST:
            return min(paths, key=lambda p: p.total_cost_tokens)

        elif strategy == PathDecisionStrategy.MINIMIZE_RISK:
            return min(paths, key=lambda p: p.risk_score)

        elif strategy == PathDecisionStrategy.MAXIMIZE_QUALITY:
            return max(paths, key=lambda p: p.quality_score)

        elif strategy == PathDecisionStrategy.BALANCED:
            # Normalize metrics and combine: 50% cost, 30% risk, 20% quality
            scores = []
            for path in paths:
                normalized_cost = self._normalize_value(
                    path.total_cost_tokens,
                    [p.total_cost_tokens for p in paths],
                    invert=True,  # Lower is better
                )
                normalized_risk = self._normalize_value(
                    path.risk_score, [p.risk_score for p in paths], invert=True
                )
                normalized_quality = self._normalize_value(
                    path.quality_score, [p.quality_score for p in paths]
                )

                combined_score = (
                    (normalized_cost * 0.5)
                    + (normalized_risk * 0.3)
                    + (normalized_quality * 0.2)
                )

                scores.append((path, combined_score))
                logger.debug(
                    f"Path {path.path_id} balanced score: {combined_score:.3f} "
                    f"(cost={normalized_cost:.3f}, risk={normalized_risk:.3f}, "
                    f"quality={normalized_quality:.3f})"
                )

            # Select path with highest combined score
            best_path = max(scores, key=lambda x: x[1])[0]
            return best_path

        else:  # USER_CHOICE
            return paths[0]

    def _calculate_quality_score(
        self, path: WorkflowPath, project: ProjectContext
    ) -> float:
        """
        Calculate quality score for a path.

        Quality = coverage + depth - risk
        Higher is better.

        Args:
            path: WorkflowPath to score
            project: ProjectContext

        Returns:
            Quality score (0-100)
        """
        # Base quality from coverage (inverse of incompleteness)
        coverage_quality = 100.0 - path.incompleteness_risk

        # Depth/complexity adds quality (deeper analysis = better)
        complexity_quality = path.complexity_risk * 0.5

        # Risk reduces quality
        risk_penalty = path.risk_score * 0.3

        quality = coverage_quality + complexity_quality - risk_penalty
        quality = max(0.0, min(100.0, quality))  # Clamp to 0-100

        return quality

    def _calculate_expected_maturity_gain(
        self, path: WorkflowPath, project: ProjectContext
    ) -> float:
        """
        Estimate maturity points this path will gain.

        Based on coverage and complexity.

        Args:
            path: WorkflowPath
            project: ProjectContext

        Returns:
            Expected maturity gain (0-100)
        """
        # Paths with better coverage gain more maturity
        coverage_gain = (100.0 - path.incompleteness_risk) * 0.7

        # Paths with good complexity (deep questions) gain more
        complexity_gain = min(30.0, path.complexity_risk * 0.3)

        expected_gain = coverage_gain + complexity_gain
        expected_gain = min(100.0, expected_gain)

        return expected_gain

    def _calculate_roi(
        self, path: WorkflowPath, tokens: int, maturity_gain: float
    ) -> float:
        """
        Calculate ROI (return on investment) for a path.

        ROI = maturity_gain / tokens (points per token)

        Args:
            path: WorkflowPath
            tokens: Token cost
            maturity_gain: Expected maturity gain

        Returns:
            ROI score (higher is better)
        """
        if tokens == 0:
            return 0.0

        roi = maturity_gain / (tokens / 1000.0)  # Points per 1000 tokens
        return round(roi, 2)

    @staticmethod
    def _normalize_value(
        value: float, all_values: List[float], invert: bool = False
    ) -> float:
        """
        Normalize a value to 0-1 range based on min/max of all values.

        Args:
            value: Value to normalize
            all_values: All values for computing min/max
            invert: If True, invert (1 - normalized) for "lower is better" metrics

        Returns:
            Normalized value (0-1)
        """
        if not all_values:
            return 0.5

        min_val = min(all_values)
        max_val = max(all_values)

        if max_val == min_val:
            normalized = 0.5
        else:
            normalized = (value - min_val) / (max_val - min_val)

        if invert:
            normalized = 1.0 - normalized

        return normalized
