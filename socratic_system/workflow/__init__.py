"""Workflow orchestration and optimization - imported from socratic-workflow library."""

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
    WorkflowApprovalRequest = None
    WorkflowDefinition = None
    WorkflowEdge = None
    WorkflowExecutionState = None
    WorkflowNode = None
    WorkflowPath = None

# Local workflow utilities
try:
    from socratic_system.core.workflow_builder import (
        create_discovery_workflow_comprehensive,
        create_legacy_compatible_workflow,
    )
except ImportError:
    create_discovery_workflow_comprehensive = None
    create_legacy_compatible_workflow = None

try:
    from socratic_system.core.workflow_optimizer import WorkflowOptimizer
except ImportError:
    WorkflowOptimizer = None

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
