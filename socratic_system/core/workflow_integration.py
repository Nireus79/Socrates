"""
Workflow system integration using socratic-workflow library.

Provides workflow orchestration, task management, and execution tracking
using socratic-workflow's Workflow and Task classes.
"""

import logging
from typing import Any, Dict, List, Optional

try:
    from socratic_workflow import Task, Workflow, WorkflowEngine
except ImportError:
    # socratic_workflow is optional - provide graceful fallback
    Task = None  # type: ignore
    Workflow = None  # type: ignore
    WorkflowEngine = None  # type: ignore

from socratic_system.models.workflow import WorkflowExecutionState

logger = logging.getLogger("socrates.workflow")


class WorkflowIntegration:
    """
    Integrated workflow system combining:
    - socratic-workflow's Workflow for workflow definition and execution
    - Task management and status tracking
    - Workflow execution with progress monitoring
    """

    engine: WorkflowEngine
    active_workflows: Dict[str, Workflow]
    workflow_tasks: Dict[str, List[Task]]

    def __init__(self, executor_type: str = "sequential") -> None:
        """
        Initialize workflow integration.

        Args:
            executor_type: Type of executor (sequential, parallel, hybrid)
        """
        self.executor_type = executor_type
        self.logger = logging.getLogger("socrates.workflow")
        self.engine: Any = None
        self.active_workflows: Dict[str, Any] = {}
        self.workflow_tasks: Dict[str, List[Any]] = {}

        if WorkflowEngine is None:
            self.logger.warning("socratic_workflow not available - workflow features disabled")
            return

        try:
            # Initialize workflow engine
            self.engine = WorkflowEngine()
            self.logger.info(f"WorkflowEngine initialized ({executor_type})")

        except Exception as e:
            self.logger.error(f"Failed to initialize workflow integration: {e}")
            # Don't raise - allow graceful degradation

    def create_workflow(
        self,
        workflow_id: str,
        name: str,
        description: str,
        phase: str = "discovery"
    ) -> Any:
        """
        Create a new workflow.

        Args:
            workflow_id: Unique workflow identifier
            name: Human-readable workflow name
            description: Workflow description
            phase: Project phase (discovery, design, implementation, etc.)

        Returns:
            Workflow object
        """
        if Workflow is None:
            self.logger.debug("Workflow creation unavailable - workflow features disabled")
            return None

        try:
            workflow = Workflow(
                workflow_id=workflow_id,
                name=name,
                description=description,
                metadata={"phase": phase}
            )
            self.active_workflows[workflow_id] = workflow
            self.workflow_tasks[workflow_id] = []
            self.logger.debug(f"Created workflow: {name} ({workflow_id})")
            return workflow

        except Exception as e:
            self.logger.error(f"Failed to create workflow: {e}")
            return None

    def add_task(
        self,
        workflow_id: str,
        task_id: str,
        name: str,
        description: str,
        task_type: str = "question",
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Any:
        """
        Add a task to a workflow.

        Args:
            workflow_id: Workflow identifier
            task_id: Unique task identifier
            name: Task name
            description: Task description
            task_type: Type of task (question, analysis, decision, etc.)
            dependencies: List of task IDs this task depends on
            metadata: Additional metadata

        Returns:
            Task object
        """
        if Task is None:
            self.logger.debug("Task creation unavailable - workflow features disabled")
            return None

        try:
            if workflow_id not in self.active_workflows:
                raise ValueError(f"Workflow {workflow_id} not found")

            task = Task(
                task_id=task_id,
                name=name,
                description=description,
                task_type=task_type,
                dependencies=dependencies or [],
                metadata=metadata or {}
            )

            workflow = self.active_workflows[workflow_id]
            workflow.add_task(task)
            self.workflow_tasks[workflow_id].append(task)

            self.logger.debug(f"Added task {task_id} to workflow {workflow_id}")
            return task

        except Exception as e:
            self.logger.error(f"Failed to add task: {e}")
            return None

    def execute_workflow(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow_id: Workflow to execute
            context: Execution context/variables
            timeout: Execution timeout in seconds

        Returns:
            Execution result with status and output
        """
        try:
            if workflow_id not in self.active_workflows:
                raise ValueError(f"Workflow {workflow_id} not found")

            if self.engine is None:
                raise RuntimeError("Workflow engine not initialized")

            workflow = self.active_workflows[workflow_id]
            result = self.engine.execute(
                workflow=workflow,
                context=context or {},
                timeout=timeout
            )

            self.logger.info(f"Executed workflow {workflow_id}: {result.status}")

            return {
                "workflow_id": workflow_id,
                "status": getattr(result, "status", "unknown"),
                "output": getattr(result, "output", {}),
                "execution_time": getattr(result, "execution_time", 0.0),
                "tasks_completed": getattr(result, "tasks_completed", 0),
                "tasks_failed": getattr(result, "tasks_failed", 0)
            }

        except Exception as e:
            self.logger.error(f"Failed to execute workflow: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e),
                "output": {}
            }

    def get_task_status(self, workflow_id: str, task_id: str) -> Dict[str, Any]:
        """
        Get status of a task in a workflow.

        Args:
            workflow_id: Workflow identifier
            task_id: Task identifier

        Returns:
            Task status and metadata
        """
        try:
            if workflow_id not in self.active_workflows:
                return {"status": "not_found", "error": f"Workflow {workflow_id} not found"}

            workflow = self.active_workflows[workflow_id]
            task = workflow.get_task(task_id)

            if not task:
                return {"status": "not_found", "error": f"Task {task_id} not found"}

            return {
                "task_id": task_id,
                "name": getattr(task, "name", ""),
                "status": getattr(task, "status", "pending"),
                "started_at": getattr(task, "started_at", None),
                "completed_at": getattr(task, "completed_at", None),
                "output": getattr(task, "output", {}),
                "error": getattr(task, "error", None)
            }

        except Exception as e:
            self.logger.error(f"Failed to get task status: {e}")
            return {"status": "error", "error": str(e)}

    def get_workflow_progress(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get progress of a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Progress information with completion percentage and status breakdown
        """
        try:
            if workflow_id not in self.active_workflows:
                return {"error": f"Workflow {workflow_id} not found"}

            tasks = self.workflow_tasks.get(workflow_id, [])

            if not tasks:
                return {
                    "workflow_id": workflow_id,
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "pending_tasks": 0,
                    "progress_percentage": 0.0
                }

            completed = sum(1 for t in tasks if getattr(t, "status", None) == "completed")
            failed = sum(1 for t in tasks if getattr(t, "status", None) == "failed")
            pending = len(tasks) - completed - failed

            return {
                "workflow_id": workflow_id,
                "total_tasks": len(tasks),
                "completed_tasks": completed,
                "failed_tasks": failed,
                "pending_tasks": pending,
                "progress_percentage": (completed / len(tasks) * 100) if tasks else 0.0
            }

        except Exception as e:
            self.logger.error(f"Failed to get workflow progress: {e}")
            return {"error": str(e)}

    def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a workflow execution.

        Args:
            workflow_id: Workflow to cancel

        Returns:
            True if cancelled successfully
        """
        try:
            if workflow_id not in self.active_workflows:
                return False

            if self.engine is None:
                return False

            self.engine.cancel(workflow_id)
            self.logger.info(f"Cancelled workflow {workflow_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to cancel workflow: {e}")
            return False

    def get_execution_state(self, workflow_id: str) -> Optional[WorkflowExecutionState]:
        """
        Get execution state of a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            WorkflowExecutionState or None
        """
        try:
            if workflow_id not in self.active_workflows:
                return None

            workflow = self.active_workflows[workflow_id]

            # Get execution state from workflow
            execution_id = getattr(workflow, "execution_id", f"exec_{workflow_id}")
            approved_path_id = getattr(workflow, "approved_path_id", workflow_id)
            current_node_id = getattr(workflow, "current_task_id", "")

            return WorkflowExecutionState(
                execution_id=execution_id,
                workflow_id=workflow_id,
                approved_path_id=approved_path_id,
                current_node_id=current_node_id,
                completed_nodes=[],
                remaining_nodes=[],
                actual_tokens_used=0,
                estimated_tokens_remaining=0,
                started_at=getattr(workflow, "started_at", ""),
                status=getattr(workflow, "status", "active")
            )

        except Exception as e:
            self.logger.error(f"Failed to get execution state: {e}")
            return None

    def export_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Export workflow definition for persistence.

        Args:
            workflow_id: Workflow to export

        Returns:
            Serializable workflow definition
        """
        try:
            if workflow_id not in self.active_workflows:
                return {}

            workflow = self.active_workflows[workflow_id]
            tasks = self.workflow_tasks.get(workflow_id, [])

            return {
                "workflow_id": workflow_id,
                "name": getattr(workflow, "name", ""),
                "description": getattr(workflow, "description", ""),
                "metadata": getattr(workflow, "metadata", {}),
                "tasks": [
                    {
                        "task_id": getattr(t, "task_id", ""),
                        "name": getattr(t, "name", ""),
                        "type": getattr(t, "task_type", ""),
                        "dependencies": getattr(t, "dependencies", [])
                    }
                    for t in tasks
                ]
            }

        except Exception as e:
            self.logger.error(f"Failed to export workflow: {e}")
            return {}

    def close(self):
        """Close workflow integration"""
        try:
            if self.engine is not None:
                self.engine.shutdown()
            self.active_workflows.clear()
            self.workflow_tasks.clear()
            self.logger.info("Workflow integration closed")
        except Exception as e:
            self.logger.error(f"Error closing workflow integration: {e}")

    def __del__(self):
        """Cleanup on object deletion"""
        try:
            self.close()
        except Exception:
            pass
