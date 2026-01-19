"""
Workflow builder using fluent API for constructing workflow definitions

Provides convenient methods to define workflow graphs and factory methods
for common workflow patterns.
"""

import logging
import uuid
from typing import Dict, List, Optional

from socratic_system.models.project import ProjectContext
from socratic_system.models.workflow import (
    PathDecisionStrategy,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
    WorkflowNodeType,
)

logger = logging.getLogger(__name__)


class WorkflowBuilder:
    """Builder for constructing workflow definitions with fluent API"""

    def __init__(
        self,
        workflow_id: Optional[str] = None,
        name: str = "Unnamed Workflow",
        phase: str = "discovery",
    ):
        """
        Initialize workflow builder.

        Args:
            workflow_id: Unique ID for workflow (auto-generated if None)
            name: Human-readable name for workflow
            phase: Phase this workflow applies to
        """
        self.workflow_id = workflow_id or f"wf_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.phase = phase
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: List[WorkflowEdge] = []
        self.start_node: Optional[str] = None
        self.end_nodes: List[str] = []
        self.strategy = "balanced"
        self.metadata: Dict = {}

        logger.debug(f"WorkflowBuilder initialized: {self.workflow_id} ({name}, {phase})")

    def add_node(
        self,
        node_id: str,
        node_type: WorkflowNodeType,
        label: str,
        estimated_tokens: int = 0,
        questions: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> "WorkflowBuilder":
        """
        Add a node to the workflow.

        Args:
            node_id: Unique ID for this node
            node_type: Type of node (from WorkflowNodeType enum)
            label: Human-readable label
            estimated_tokens: Estimated tokens for this node
            questions: List of potential questions for this node
            metadata: Additional metadata (e.g., target_categories)

        Returns:
            Self for method chaining
        """
        node = WorkflowNode(
            node_id=node_id,
            node_type=node_type,
            label=label,
            estimated_tokens=estimated_tokens,
            questions=questions or [],
            metadata=metadata or {},
        )

        self.nodes[node_id] = node

        logger.debug(
            f"Added node {node_id}: {label} ({node_type.value}, {estimated_tokens} tokens)"
        )

        return self

    def add_edge(
        self,
        from_node: str,
        to_node: str,
        probability: float = 1.0,
        condition: Optional[str] = None,
        cost: int = 0,
    ) -> "WorkflowBuilder":
        """
        Add an edge (transition) between nodes.

        Args:
            from_node: Source node ID
            to_node: Destination node ID
            probability: Probability of taking this edge (0-1)
            condition: Optional condition for taking this edge
            cost: Token cost for this transition

        Returns:
            Self for method chaining
        """
        edge = WorkflowEdge(
            from_node=from_node,
            to_node=to_node,
            probability=probability,
            condition=condition,
            cost=cost,
        )

        self.edges.append(edge)

        logger.debug(f"Added edge: {from_node} -> {to_node} (cost: {cost})")

        return self

    def set_entry(self, node_id: str) -> "WorkflowBuilder":
        """
        Set the entry/start node for the workflow.

        Args:
            node_id: ID of start node

        Returns:
            Self for method chaining
        """
        self.start_node = node_id
        logger.debug(f"Set entry node: {node_id}")
        return self

    def add_exit(self, node_id: str) -> "WorkflowBuilder":
        """
        Add an exit/end node for the workflow.

        Args:
            node_id: ID of end node

        Returns:
            Self for method chaining
        """
        self.end_nodes.append(node_id)
        logger.debug(f"Added exit node: {node_id}")
        return self

    def set_strategy(self, strategy: PathDecisionStrategy) -> "WorkflowBuilder":
        """
        Set the strategy for path selection.

        Args:
            strategy: PathDecisionStrategy to use

        Returns:
            Self for method chaining
        """
        self.strategy = strategy.value
        logger.debug(f"Set strategy: {strategy.value}")
        return self

    def set_metadata(self, key: str, value) -> "WorkflowBuilder":
        """
        Set metadata key-value pair.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Self for method chaining
        """
        self.metadata[key] = value
        logger.debug(f"Set metadata: {key} = {value}")
        return self

    def build(self) -> WorkflowDefinition:
        """
        Build and return the workflow definition.

        Validates that all required fields are set.

        Returns:
            Complete WorkflowDefinition

        Raises:
            ValueError: If workflow is invalid
        """
        if not self.start_node:
            raise ValueError(f"Workflow {self.workflow_id}: start_node not set")

        if not self.end_nodes:
            raise ValueError(f"Workflow {self.workflow_id}: end_nodes not set")

        if not self.nodes:
            raise ValueError(f"Workflow {self.workflow_id}: no nodes defined")

        workflow = WorkflowDefinition(
            workflow_id=self.workflow_id,
            name=self.name,
            phase=self.phase,
            nodes=self.nodes,
            edges=self.edges,
            start_node=self.start_node,
            end_nodes=self.end_nodes,
            strategy=self.strategy,
            metadata=self.metadata,
        )

        logger.info(
            f"Built workflow {self.workflow_id}: {len(self.nodes)} nodes, "
            f"{len(self.edges)} edges, strategy={self.strategy}"
        )

        return workflow


# ============================================================================
# Factory Methods for Common Workflows
# ============================================================================


def create_discovery_workflow_simple(project: ProjectContext) -> WorkflowDefinition:
    """
    Create a simple discovery workflow (basic coverage).

    3 questions covering core categories:
    - goals
    - requirements
    - tech_stack

    Estimated cost: ~7,000 tokens
    Expected coverage: 40-50%
    Risk: High (many missing categories)

    Args:
        project: ProjectContext for project information

    Returns:
        WorkflowDefinition for simple discovery
    """
    logger.info("Creating simple discovery workflow")

    builder = WorkflowBuilder(
        name="Discovery - Simple",
        phase="discovery",
    )

    # Start node
    builder.add_node("start", WorkflowNodeType.PHASE_START, "Discovery Start", 0)

    # Basic questions node (3 questions)
    builder.add_node(
        "basic_questions",
        WorkflowNodeType.QUESTION_SET,
        "Basic Questions",
        estimated_tokens=7000,
        metadata={
            "target_categories": ["goals", "requirements", "tech_stack"],
            "question_count": 3,
        },
    )

    # Analysis node
    builder.add_node(
        "analysis",
        WorkflowNodeType.ANALYSIS,
        "Analyze Responses",
        estimated_tokens=5000,
    )

    # End node
    builder.add_node("end", WorkflowNodeType.PHASE_END, "Discovery Complete", 0)

    # Connect nodes
    builder.add_edge("start", "basic_questions")
    builder.add_edge("basic_questions", "analysis", cost=500)
    builder.add_edge("analysis", "end")

    # Set entry and exit
    builder.set_entry("start")
    builder.add_exit("end")

    # Set strategy
    builder.set_strategy(PathDecisionStrategy.BALANCED)

    return builder.build()


def create_discovery_workflow_comprehensive(project: ProjectContext) -> WorkflowDefinition:
    """
    Create a comprehensive discovery workflow (deep coverage).

    5-7 questions covering major categories:
    - goals
    - requirements
    - tech_stack
    - constraints
    - risks
    - timeline
    - team_structure

    Estimated cost: ~11,000 tokens
    Expected coverage: 60-70%
    Risk: Moderate (balanced approach)

    Args:
        project: ProjectContext for project information

    Returns:
        WorkflowDefinition for comprehensive discovery
    """
    logger.info("Creating comprehensive discovery workflow")

    builder = WorkflowBuilder(
        name="Discovery - Comprehensive",
        phase="discovery",
    )

    # Start node
    builder.add_node("start", WorkflowNodeType.PHASE_START, "Discovery Start", 0)

    # Comprehensive questions node (5-7 questions)
    builder.add_node(
        "comprehensive_questions",
        WorkflowNodeType.QUESTION_SET,
        "Comprehensive Questions",
        estimated_tokens=11000,
        metadata={
            "target_categories": [
                "goals",
                "requirements",
                "tech_stack",
                "constraints",
                "risks",
                "timeline",
                "team_structure",
            ],
            "question_count": 6,
        },
    )

    # Analysis node
    builder.add_node(
        "analysis",
        WorkflowNodeType.ANALYSIS,
        "Analyze Responses",
        estimated_tokens=5000,
    )

    # Validation node
    builder.add_node(
        "validation",
        WorkflowNodeType.VALIDATION,
        "Validate Coverage",
        estimated_tokens=3000,
    )

    # End node
    builder.add_node("end", WorkflowNodeType.PHASE_END, "Discovery Complete", 0)

    # Connect nodes
    builder.add_edge("start", "comprehensive_questions")
    builder.add_edge("comprehensive_questions", "analysis", cost=500)
    builder.add_edge("analysis", "validation", cost=300)
    builder.add_edge("validation", "end")

    # Set entry and exit
    builder.set_entry("start")
    builder.add_exit("end")

    # Set strategy
    builder.set_strategy(PathDecisionStrategy.BALANCED)

    return builder.build()


def create_discovery_workflow_with_alternatives(
    project: ProjectContext,
) -> WorkflowDefinition:
    """
    Create discovery workflow with branching paths (simple vs comprehensive).

    User can choose between:
    - Path 1: Quick (3 questions, ~7K tokens)
    - Path 2: Standard (6 questions, ~11K tokens)

    Both paths lead to same Analysis/Validation/End nodes.

    Args:
        project: ProjectContext for project information

    Returns:
        WorkflowDefinition with alternative paths
    """
    logger.info("Creating discovery workflow with alternatives")

    builder = WorkflowBuilder(
        name="Discovery - Alternatives",
        phase="discovery",
    )

    # Start node
    builder.add_node("start", WorkflowNodeType.PHASE_START, "Discovery Start", 0)

    # Path A: Quick
    builder.add_node(
        "quick_questions",
        WorkflowNodeType.QUESTION_SET,
        "Quick Questions",
        estimated_tokens=7000,
        metadata={
            "target_categories": ["goals", "requirements", "tech_stack"],
            "question_count": 3,
        },
    )

    # Path B: Standard
    builder.add_node(
        "standard_questions",
        WorkflowNodeType.QUESTION_SET,
        "Standard Questions",
        estimated_tokens=11000,
        metadata={
            "target_categories": [
                "goals",
                "requirements",
                "tech_stack",
                "constraints",
                "risks",
                "timeline",
            ],
            "question_count": 6,
        },
    )

    # Common nodes after questions
    builder.add_node(
        "analysis",
        WorkflowNodeType.ANALYSIS,
        "Analyze Responses",
        estimated_tokens=5000,
    )

    builder.add_node(
        "validation",
        WorkflowNodeType.VALIDATION,
        "Validate Coverage",
        estimated_tokens=3000,
    )

    builder.add_node("end", WorkflowNodeType.PHASE_END, "Discovery Complete", 0)

    # Edges: two paths from start
    builder.add_edge("start", "quick_questions", probability=0.5)
    builder.add_edge("start", "standard_questions", probability=0.5)

    # Both paths converge at analysis
    builder.add_edge("quick_questions", "analysis", cost=500)
    builder.add_edge("standard_questions", "analysis", cost=500)

    # Complete path
    builder.add_edge("analysis", "validation", cost=300)
    builder.add_edge("validation", "end")

    # Set entry and exits
    builder.set_entry("start")
    builder.add_exit("end")

    # Set strategy to BALANCED (recommend standard path)
    builder.set_strategy(PathDecisionStrategy.BALANCED)

    return builder.build()


def create_legacy_compatible_workflow(phase: str) -> WorkflowDefinition:
    """
    Create minimal workflow that maintains backward compatibility.

    Single linear path: Start → Questions → End
    No branching, no analysis, no validation.
    Mimics current behavior where questions are asked one-at-a-time.

    Args:
        phase: Phase for this workflow

    Returns:
        Simple WorkflowDefinition with minimal path
    """
    logger.info(f"Creating legacy-compatible workflow for {phase}")

    builder = WorkflowBuilder(
        name=f"{phase.capitalize()} - Legacy",
        phase=phase,
    )

    # Minimal workflow
    builder.add_node("start", WorkflowNodeType.PHASE_START, "Phase Start", 0)

    builder.add_node(
        "questions",
        WorkflowNodeType.QUESTION_SET,
        "Questions",
        estimated_tokens=15000,
        metadata={"legacy_mode": True},
    )

    builder.add_node("end", WorkflowNodeType.PHASE_END, "Phase Complete", 0)

    # Linear path
    builder.add_edge("start", "questions")
    builder.add_edge("questions", "end")

    builder.set_entry("start")
    builder.add_exit("end")

    return builder.build()
