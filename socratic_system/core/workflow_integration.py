"""
Workflow system integration using socratic-workflow library.

Provides workflow orchestration, task management, and execution tracking
using socratic-workflow's Workflow and Task classes.
"""

import logging
from typing import Any, Dict, List, Optional

from socratic_workflow import Workflow, Task, TaskStatus, WorkflowExecutor

from socratic_system.models.workflow import WorkflowDefinition, WorkflowExecutionState


class WorkflowIntegration:
    """
    Integrated workflow system combining:
    - socratic-workflow's Workflow for workflow definition and execution
    - Task management and status tracking
    - Workflow execution with progress monitoring
    """

    def __init__(self, executor_type: str = "sequential"):
        """
        Initialize workflow integration.

        Args:
            executor_type: Type of executor (sequential, parallel, hybrid)
        """
        self.executor_type = executor_type
        self.logger = logging.getLogger("socrates.workflow")
        self.executor = None

        try:
            # Initialize workflow executor
            self.executor = WorkflowExecutor(
                executor_type=executor_type,
                enable_logging=True,
                enable_recovery=True
            )
            self.logger.info(f"WorkflowExecutor initialized ({executor_type})")

            self.active_workflows: Dict[str, Workflow] = {}
            self.workflow_tasks: Dict[str, List[Task]] = {}

        except Exception as e:
            self.logger.error(f"Failed to initialize workflow integration: {e}")
            raise

    def create_workflow(
        self,
        workflow_id: str,
        name: str,
        description: str,
        phase: str = "discovery"
    ) -> Workflow:
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
            raise

    def add_task(
        self,
        workflow_id: str,
        task_id: str,
        name: str,
        description: str,
        task_type: str = "question",
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Task:
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
            raise

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

            workflow = self.active_workflows[workflow_id]
            result = self.executor.execute(
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
                "status": getattr(task, "status", TaskStatus.PENDING),
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

            workflow = self.active_workflows[workflow_id]
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

            completed = sum(1 for t in tasks if getattr(t, "status", None) == TaskStatus.COMPLETED)
            failed = sum(1 for t in tasks if getattr(t, "status", None) == TaskStatus.FAILED)
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

            self.executor.cancel(workflow_id)
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
            progress = self.get_workflow_progress(workflow_id)

            return WorkflowExecutionState(
                workflow_id=workflow_id,
                current_task_id=getattr(workflow, "current_task_id", None),
                completed_tasks=progress.get("completed_tasks", 0),
                total_tasks=progress.get("total_tasks", 0),
                progress_percentage=progress.get("progress_percentage", 0.0),
                status=getattr(workflow, "status", "running"),
                started_at=getattr(workflow, "started_at", None),
                metadata=getattr(workflow, "metadata", {})
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
            self.executor.shutdown()
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
