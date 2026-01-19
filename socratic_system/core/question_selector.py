"""
Question selector for path-constrained question generation

Selects questions aligned with current position in approved workflow path,
ensuring questions target specific categories.
"""

import logging
from typing import List, Set

from socratic_system.models.project import ProjectContext
from socratic_system.models.workflow import (
    WorkflowDefinition,
    WorkflowExecutionState,
    WorkflowNodeType,
)

logger = logging.getLogger(__name__)


class QuestionSelector:
    """Select questions aligned with current workflow node"""

    def __init__(self):
        """Initialize question selector"""
        logger.debug("QuestionSelector initialized")

    def select_next_questions(
        self,
        project: ProjectContext,
        workflow: WorkflowDefinition,
        execution: WorkflowExecutionState,
        max_questions: int = 1,
    ) -> List[str]:
        """
        Select next questions based on current node in approved workflow path.

        Only generates questions for categories that:
        1. Are targeted by the current node
        2. Have not yet been covered

        Args:
            project: ProjectContext with specifications
            workflow: WorkflowDefinition with node metadata
            execution: WorkflowExecutionState tracking progress
            max_questions: Maximum questions to return

        Returns:
            List of question strings (limited to max_questions)
        """
        logger.debug(
            f"Selecting next questions for workflow execution {execution.execution_id} "
            f"at node {execution.current_node_id}"
        )

        # Get current node
        current_node = workflow.nodes.get(execution.current_node_id)

        if not current_node:
            logger.error(f"Current node {execution.current_node_id} not found in workflow")
            return []

        # Only question set nodes generate questions
        if current_node.node_type != WorkflowNodeType.QUESTION_SET:
            logger.debug(f"Node {execution.current_node_id} is not a question set, no questions")
            return []

        # Get categories this node should target
        target_categories = current_node.metadata.get("target_categories", [])

        if not target_categories:
            logger.debug(f"Node {execution.current_node_id} has no target categories")
            return []

        # Get categories already covered
        covered_categories = self._get_covered_categories(project)

        # Find uncovered categories
        uncovered = [c for c in target_categories if c not in covered_categories]

        if not uncovered:
            logger.info(
                f"All target categories already covered for node {execution.current_node_id}"
            )
            return []

        logger.debug(f"Uncovered categories: {uncovered}")

        # Generate questions for uncovered categories
        questions = self._generate_category_targeted_questions(
            project, uncovered, current_node, max_questions
        )

        logger.info(f"Generated {len(questions)} questions for node {execution.current_node_id}")

        return questions

    def _get_covered_categories(self, project: ProjectContext) -> Set[str]:
        """
        Identify which categories have been covered in the current phase.

        Args:
            project: ProjectContext with specifications

        Returns:
            Set of covered category names
        """
        covered = set()

        # Check categorized_specs for current phase
        phase_specs = project.categorized_specs.get(project.phase, {})

        for category_specs in phase_specs.values():
            if isinstance(category_specs, (list, dict)):
                if isinstance(category_specs, list) and category_specs:
                    # If it's a list with items, category is covered
                    covered.add(str(list(phase_specs.keys())[0]))
                elif isinstance(category_specs, dict):
                    for category in category_specs.keys():
                        covered.add(category)

        logger.debug(f"Covered categories: {covered}")

        return covered

    def _generate_category_targeted_questions(
        self, project: ProjectContext, categories: List[str], node, max_questions: int = 1
    ) -> List[str]:
        """
        Generate questions targeting specific uncovered categories.

        Args:
            project: ProjectContext
            categories: List of categories to generate questions for
            node: WorkflowNode with metadata
            max_questions: Max questions to generate

        Returns:
            List of question strings
        """
        questions = []

        # Get pre-defined questions from node if available
        if node.questions:
            logger.debug(f"Using pre-defined questions from node: {node.questions}")
            return node.questions[:max_questions]

        # Otherwise, generate dynamic questions for each category
        logger.debug(f"Generating dynamic questions for categories: {categories}")

        category_question_map = {
            "goals": "What are the main goals or objectives for {project_name}?",
            "requirements": "What are the key requirements or must-haves for {project_name}?",
            "tech_stack": "What technologies or tools will you use for {project_name}?",
            "constraints": "What constraints do you have (time, budget, resources)?",
            "timeline": "What's your timeline or schedule for {project_name}?",
            "team_structure": "How is your team structured?",
            "risks": "What risks or challenges do you foresee?",
            "dependencies": "What dependencies or integrations are needed?",
            "assumptions": "What assumptions are you making?",
            "success_criteria": "How will you measure success?",
            "scope": "What's the scope of {project_name}?",
            "stakeholders": "Who are the key stakeholders?",
            "deployment_target": "Where will {project_name} be deployed?",
            "architecture": "How will {project_name} be architected?",
            "testing_strategy": "What testing strategy will you use?",
        }

        project_name = project.name or "this project"

        for category in categories[:max_questions]:
            template = category_question_map.get(
                category, f"Tell me about the {category.replace('_', ' ')} for {project_name}."
            )

            question = template.format(project_name=project_name)
            questions.append(question)

            if len(questions) >= max_questions:
                break

        logger.debug(f"Generated {len(questions)} questions")

        return questions

    def get_next_node(self, workflow: WorkflowDefinition, execution: WorkflowExecutionState) -> str:
        """
        Get the next node ID to advance to after current node completes.

        Args:
            workflow: WorkflowDefinition
            execution: WorkflowExecutionState

        Returns:
            ID of next node, or None if no valid next node

        Raises:
            ValueError: If workflow is malformed
        """
        current_node = execution.current_node_id

        # Find edges from current node
        next_nodes = [edge.to_node for edge in workflow.edges if edge.from_node == current_node]

        if not next_nodes:
            logger.debug(f"No edges from node {current_node}")
            return None

        if len(next_nodes) == 1:
            return next_nodes[0]

        # Multiple edges - choose first (simplified; could be enhanced with conditions)
        logger.debug(f"Node {current_node} has {len(next_nodes)} outgoing edges, choosing first")
        return next_nodes[0]

    def is_execution_complete(
        self, execution: WorkflowExecutionState, workflow: WorkflowDefinition
    ) -> bool:
        """
        Check if workflow execution has reached an end node.

        Args:
            execution: WorkflowExecutionState
            workflow: WorkflowDefinition

        Returns:
            True if current node is an end node
        """
        is_complete = execution.current_node_id in workflow.end_nodes
        logger.debug(
            f"Execution complete check: {execution.current_node_id} in {workflow.end_nodes} = {is_complete}"
        )
        return is_complete
