"""
Workflow optimization models for Quality Controller

Provides data structures for workflow definition, path enumeration,
cost/risk calculation, and approval workflow management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkflowNodeType(Enum):
    """Types of nodes in a workflow graph"""

    PHASE_START = "phase_start"
    QUESTION_SET = "question_set"
    ANALYSIS = "analysis"
    DECISION = "decision"
    PHASE_END = "phase_end"
    VALIDATION = "validation"


class PathDecisionStrategy(Enum):
    """Strategies for selecting optimal workflow path"""

    MINIMIZE_COST = "minimize_cost"
    MINIMIZE_RISK = "minimize_risk"
    BALANCED = "balanced"
    MAXIMIZE_QUALITY = "maximize_quality"
    USER_CHOICE = "user_choice"


@dataclass
class WorkflowNode:
    """Represents a step/node in a workflow graph"""

    node_id: str
    node_type: WorkflowNodeType
    label: str
    estimated_tokens: int = 0
    questions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowEdge:
    """Represents a transition/edge between workflow nodes"""

    from_node: str
    to_node: str
    probability: float = 1.0
    condition: Optional[str] = None
    cost: int = 0


@dataclass
class WorkflowPath:
    """Complete path through workflow with calculated metrics"""

    path_id: str
    nodes: List[str]  # Ordered list of node IDs in this path
    edges: List[str]  # Ordered list of edge IDs in this path
    total_cost_tokens: int = 0
    total_cost_usd: float = 0.0
    risk_score: float = 0.0
    rework_probability: float = 0.0
    incompleteness_risk: float = 0.0
    complexity_risk: float = 0.0
    category_coverage: Dict[str, float] = field(default_factory=dict)
    missing_categories: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    expected_maturity_gain: float = 0.0
    roi_score: float = 0.0


@dataclass
class WorkflowDefinition:
    """Complete workflow graph definition with nodes, edges, and metadata"""

    workflow_id: str
    name: str
    phase: str  # "discovery", "analysis", "design", "implementation"
    nodes: Dict[str, WorkflowNode]  # node_id -> WorkflowNode
    edges: List[WorkflowEdge]
    start_node: str  # ID of start node
    end_nodes: List[str]  # IDs of possible end nodes
    strategy: str = "balanced"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowApprovalRequest:
    """Request for user/system approval of a workflow path"""

    request_id: str
    project_id: str
    phase: str
    workflow: WorkflowDefinition
    all_paths: List[WorkflowPath]
    recommended_path: WorkflowPath
    strategy: PathDecisionStrategy
    created_at: str
    requested_by: str
    status: str = "pending"  # "pending", "approved", "rejected"
    approved_path_id: Optional[str] = None
    approval_timestamp: Optional[str] = None


@dataclass
class WorkflowExecutionState:
    """Tracks current execution state within an approved workflow path"""

    execution_id: str
    workflow_id: str
    approved_path_id: str
    current_node_id: str
    completed_nodes: List[str] = field(default_factory=list)
    remaining_nodes: List[str] = field(default_factory=list)
    actual_tokens_used: int = 0
    estimated_tokens_remaining: int = 0
    started_at: str = ""
    status: str = "active"  # "active", "completed", "paused"
