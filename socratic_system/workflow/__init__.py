"""Workflow orchestration and optimization - imported from socratic-workflow library."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from socratic_workflow import (
        WorkflowApprovalRequest,
        WorkflowDefinition,
        WorkflowEdge,
        WorkflowExecutionState,
        WorkflowNode,
        WorkflowPath,
    )
    from socratic_system.core.workflow_builder import (
        create_discovery_workflow_comprehensive,
        create_legacy_compatible_workflow,
    )
    from socratic_system.core.workflow_optimizer import WorkflowOptimizer

try:
    from socratic_workflow import (
        WorkflowApprovalRequest,
        WorkflowDefinition,
        WorkflowEdge,
        WorkflowExecutionState,
        WorkflowNode,
        WorkflowPath,
    )
    WORKFLOW_AVAILABLE = True
except ImportError:
    WORKFLOW_AVAILABLE = False
    WorkflowApprovalRequest = None  # type: ignore
    WorkflowDefinition = None  # type: ignore
    WorkflowEdge = None  # type: ignore
    WorkflowExecutionState = None  # type: ignore
    WorkflowNode = None  # type: ignore
    WorkflowPath = None  # type: ignore

# Local workflow utilities
try:
    from socratic_system.core.workflow_builder import (
        create_discovery_workflow_comprehensive,
        create_legacy_compatible_workflow,
    )
except ImportError:
    create_discovery_workflow_comprehensive = None  # type: ignore
    create_legacy_compatible_workflow = None  # type: ignore

try:
    from socratic_system.core.workflow_optimizer import WorkflowOptimizer
except ImportError:
    WorkflowOptimizer = None  # type: ignore

__all__ = []

# Add local utilities
if WorkflowOptimizer is not None:
    __all__.append("WorkflowOptimizer")
if create_discovery_workflow_comprehensive is not None:
    __all__.append("create_discovery_workflow_comprehensive")
if create_legacy_compatible_workflow is not None:
    __all__.append("create_legacy_compatible_workflow")

# Add workflow items that were successfully imported
if WORKFLOW_AVAILABLE:
    __all__.extend([
        "WorkflowDefinition",
        "WorkflowNode",
        "WorkflowEdge",
        "WorkflowPath",
        "WorkflowApprovalRequest",
        "WorkflowExecutionState",
    ])
