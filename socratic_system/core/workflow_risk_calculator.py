"""
Workflow risk calculator for assessing path viability

Calculates multi-dimensional risk scores including incompleteness,
complexity, and rework probability for workflow paths.
"""

import logging
from typing import Any, Dict, List

from socratic_system.core.project_categories import get_phase_categories
from socratic_system.models.project import ProjectContext
from socratic_system.models.workflow import WorkflowDefinition, WorkflowPath

logger = logging.getLogger(__name__)


class WorkflowRiskCalculator:
    """Calculate comprehensive risk assessment for workflow paths"""

    # Risk component weights (must sum to 1.0)
    INCOMPLETENESS_WEIGHT = 0.4  # Categories not covered
    COMPLEXITY_WEIGHT = 0.3  # Technical difficulty
    REWORK_WEIGHT = 0.3  # Probability of needing to redo

    def __init__(self):
        """Initialize risk calculator"""
        logger.debug("WorkflowRiskCalculator initialized")

    def calculate_path_risk(
        self,
        path: WorkflowPath,
        workflow: WorkflowDefinition,
        project: ProjectContext,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for a workflow path.

        Combines multiple risk dimensions into a weighted overall score.

        Args:
            path: WorkflowPath to assess
            workflow: WorkflowDefinition containing node metadata
            project: ProjectContext for category and project information

        Returns:
            Dict with:
                - risk_score: Overall weighted risk (0-100)
                - incompleteness_risk: Coverage gap percentage
                - complexity_risk: Technical difficulty percentage
                - rework_probability: Likelihood of rework percentage
                - missing_categories: List of uncovered categories
        """
        logger.debug(f"Calculating risk for path {path.path_id} in project {project.project_id}")

        # 1. Calculate incompleteness risk (missing categories)
        incompleteness_risk = self._calculate_incompleteness_risk(path, workflow, project)

        # 2. Calculate complexity risk (question depth)
        complexity_risk = self._calculate_complexity_risk(path, workflow)

        # 3. Calculate rework risk (probability of redo)
        rework_risk = self._calculate_rework_probability(
            path, workflow, project, incompleteness_risk
        )

        # Weighted overall risk score
        risk_score = (
            (incompleteness_risk * self.INCOMPLETENESS_WEIGHT)
            + (complexity_risk * self.COMPLEXITY_WEIGHT)
            + (rework_risk * self.REWORK_WEIGHT)
        )

        # Get missing categories for detailed reporting
        missing_categories = self._get_missing_categories(path, workflow, project)

        logger.info(
            f"Path {path.path_id} risk assessment: "
            f"overall={risk_score:.1f}, incompleteness={incompleteness_risk:.1f}, "
            f"complexity={complexity_risk:.1f}, rework={rework_risk:.1f}"
        )

        return {
            "risk_score": risk_score,
            "incompleteness_risk": incompleteness_risk,
            "complexity_risk": complexity_risk,
            "rework_probability": rework_risk,
            "missing_categories": missing_categories,
        }

    def _calculate_incompleteness_risk(
        self,
        path: WorkflowPath,
        workflow: WorkflowDefinition,
        project: ProjectContext,
    ) -> float:
        """
        Calculate incompleteness risk (coverage gaps).

        Based on percentage of phase categories not addressed by this path.

        Args:
            path: WorkflowPath to assess
            workflow: WorkflowDefinition
            project: ProjectContext with project_type

        Returns:
            Risk percentage (0-100)
        """
        try:
            # Get all categories for this phase
            phase_categories = get_phase_categories(project.project_type)

            if workflow.phase not in phase_categories:
                logger.warning(f"Phase {workflow.phase} not found in categories")
                return 0.0

            all_categories = set(phase_categories[workflow.phase].keys())

            # Get categories covered by this path
            covered_categories = self._get_covered_categories(path, workflow)

            # Calculate missing percentage
            missing_count = len(all_categories - covered_categories)
            total_count = len(all_categories)

            if total_count == 0:
                logger.warning(f"No categories found for {workflow.phase}")
                return 0.0

            incompleteness_risk = (missing_count / total_count) * 100.0

            logger.debug(
                f"Incompleteness risk: {missing_count}/{total_count} = {incompleteness_risk:.1f}%"
            )

            return incompleteness_risk

        except Exception as e:
            logger.error(f"Error calculating incompleteness risk: {e}")
            return 50.0  # Default to moderate risk on error

    def _calculate_complexity_risk(self, path: WorkflowPath, workflow: WorkflowDefinition) -> float:
        """
        Calculate complexity risk (technical difficulty).

        Based on number of questions and analysis depth in the path.

        Args:
            path: WorkflowPath to assess
            workflow: WorkflowDefinition

        Returns:
            Risk percentage (0-100)
        """
        complexity_score = 0.0
        question_set_count = 0

        for node_id in path.nodes:
            if node_id not in workflow.nodes:
                continue

            node = workflow.nodes[node_id]

            # Identify node types that add complexity
            if node.node_type.value == "question_set":
                question_set_count += 1
                # More questions = higher depth = higher complexity
                complexity_score += 20.0  # Base complexity per question set

                # Questions with metadata add more complexity
                if node.metadata.get("target_categories"):
                    complexity_score += len(node.metadata["target_categories"]) * 2

            elif node.node_type.value == "analysis":
                complexity_score += 30.0  # Analysis adds significant complexity

            elif node.node_type.value == "validation":
                complexity_score += 15.0  # Validation adds some complexity

        # Cap at 100
        complexity_risk = min(100.0, complexity_score)

        logger.debug(f"Complexity risk: {complexity_risk:.1f}%")

        return complexity_risk

    def _calculate_rework_probability(
        self,
        path: WorkflowPath,
        workflow: WorkflowDefinition,
        project: ProjectContext,
        incompleteness_risk: float,
    ) -> float:
        """
        Calculate rework probability.

        High incompleteness or gaps lead to higher rework probability.

        Args:
            path: WorkflowPath
            workflow: WorkflowDefinition
            project: ProjectContext
            incompleteness_risk: Already calculated incompleteness

        Returns:
            Rework probability percentage (0-100)
        """
        # Base rework risk from incompleteness
        rework_base = incompleteness_risk * 0.8

        # Additional rework risk based on path length
        # Longer paths = more questions = more potential for gaps
        path_length = len(path.nodes)
        length_risk = min(20.0, path_length * 2)  # Cap at 20%

        # Missing categories specifically
        missing_categories = self._get_missing_categories(path, workflow, project)
        missing_risk = len(missing_categories) * 5.0  # 5% per missing category

        rework_probability = min(100.0, rework_base + length_risk + missing_risk)

        logger.debug(
            f"Rework probability: base={rework_base:.1f}%, "
            f"length={length_risk:.1f}%, missing={missing_risk:.1f}% = {rework_probability:.1f}%"
        )

        return rework_probability

    def _get_covered_categories(self, path: WorkflowPath, workflow: WorkflowDefinition) -> set:
        """
        Identify which categories are covered by this path.

        Args:
            path: WorkflowPath
            workflow: WorkflowDefinition

        Returns:
            Set of covered category names
        """
        covered = set()

        for node_id in path.nodes:
            if node_id not in workflow.nodes:
                continue

            node = workflow.nodes[node_id]

            # Check if node metadata specifies target categories
            if node.metadata.get("target_categories"):
                covered.update(node.metadata["target_categories"])

            # Question set nodes implicitly cover what they ask about
            if node.node_type.value == "question_set":
                # Questions typically cover goals, requirements, tech_stack, constraints
                covered.update(["goals", "requirements", "tech_stack", "constraints"])

        logger.debug(f"Covered categories: {covered}")

        return covered

    def _get_missing_categories(
        self,
        path: WorkflowPath,
        workflow: WorkflowDefinition,
        project: ProjectContext,
    ) -> List[str]:
        """
        Get list of categories not covered by this path.

        Args:
            path: WorkflowPath
            workflow: WorkflowDefinition
            project: ProjectContext

        Returns:
            List of uncovered category names
        """
        try:
            phase_categories = get_phase_categories(project.project_type)

            if workflow.phase not in phase_categories:
                return []

            all_categories = set(phase_categories[workflow.phase].keys())
            covered_categories = self._get_covered_categories(path, workflow)

            missing = sorted(list(all_categories - covered_categories))

            logger.debug(f"Missing categories: {missing}")

            return missing

        except Exception as e:
            logger.error(f"Error getting missing categories: {e}")
            return []
