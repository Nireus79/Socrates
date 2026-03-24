'''
NOTE: Responses now use APIResponse format with data wrapped in "data" field.
Workflow orchestration and execution commands
'''

from typing import Any, Dict, List
from colorama import Fore
from socratic_system.ui.commands.base import BaseCommand


class WorkflowCreateCommand(BaseCommand):
    '''Create a new workflow'''

    def __init__(self):
        super().__init__(
            name="workflow create",
            description="Create a new workflow with tasks",
            usage="workflow create <name>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.workflow:
            return self.error("Workflow engine not available")

        workflow_name = args[0] if args else input(f"{Fore.WHITE}Workflow name: ").strip()
        if not workflow_name:
            return self.error("Workflow name cannot be empty")

        steps_input = input(f"{Fore.WHITE}Workflow steps (comma-separated): ").strip()
        steps = [s.strip() for s in steps_input.split(",") if s.strip()]

        if not steps:
            return self.error("At least one step is required")

        description = input(f"{Fore.WHITE}Description (optional): ").strip()

        try:
            task_configs = [
                {
                    "name": f"Step {i+1}: {step}",
                    "description": f"Execute {step} agent",
                    "agent_type": step.lower(),
                }
                for i, step in enumerate(steps)
            ]

            workflow = library_manager.workflow.define_workflow(
                name=workflow_name,
                tasks=task_configs,
                dependencies={}
            )

            if not workflow:
                return self.error("Failed to create workflow")

            workflow_data = library_manager.workflow.serialize_workflow(workflow)

            if hasattr(orchestrator.database, "save_workflow"):
                orchestrator.database.save_workflow(
                    workflow_name=workflow_name,
                    description=description,
                    steps=steps,
                    workflow_data=workflow_data
                )

            self.print_header(f"Workflow Created: {workflow_name}")
            self.print_success("Workflow created successfully")

            return self.success(data={
                "workflow_name": workflow_name,
                "steps": steps,
                "description": description,
            })

        except Exception as e:
            return self.error(f"Failed to create workflow: {str(e)}")


class WorkflowListCommand(BaseCommand):
    '''List all workflows'''

    def __init__(self):
        super().__init__(
            name="workflow list",
            description="List all available workflows",
            usage="workflow list",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        try:
            workflows = []
            if hasattr(orchestrator.database, "get_workflows"):
                workflows = orchestrator.database.get_workflows()

            if not workflows:
                self.print_info("No workflows found")
                return self.success(data={"workflows": [], "count": 0})

            self.print_header("Available Workflows")
            workflows_data = [{
                "id": w.get("workflow_id"),
                "name": w.get("name"),
                "steps": w.get("steps", []),
            } for w in workflows]

            return self.success(data={
                "workflows": workflows_data,
                "count": len(workflows_data),
            })

        except Exception as e:
            return self.error(f"Failed to list workflows: {str(e)}")


class WorkflowExecuteCommand(BaseCommand):
    '''Execute a workflow'''

    def __init__(self):
        super().__init__(
            name="workflow execute",
            description="Execute a workflow",
            usage="workflow execute <workflow_id>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        workflow_id = args[0] if args else input(f"{Fore.WHITE}Workflow ID: ").strip()
        if not workflow_id:
            return self.error("Workflow ID cannot be empty")

        try:
            if not hasattr(orchestrator.database, "get_workflow"):
                return self.error("Workflow retrieval not available")

            workflow_data = orchestrator.database.get_workflow(workflow_id)
            if not workflow_data:
                return self.error(f"Workflow {workflow_id} not found")

            library_manager = orchestrator.library_manager
            if not library_manager or not library_manager.workflow:
                return self.error("Workflow engine not available")

            workflow = library_manager.workflow.deserialize_workflow(
                workflow_data.get("workflow_data", {})
            )

            if not workflow:
                return self.error("Failed to reconstruct workflow")

            result = library_manager.workflow.execute_with_retry(workflow=workflow, max_retries=3)

            if hasattr(orchestrator.database, "save_workflow_execution"):
                orchestrator.database.save_workflow_execution(
                    workflow_id=workflow_id,
                    status="success" if result.get("success") else "failed",
                    duration_ms=result.get("duration_ms", 0),
                    result_data=result
                )

            self.print_header("Workflow Execution Result")
            self.print_success("Workflow executed successfully" if result.get("success") else "Workflow failed")

            return self.success(data={
                "workflow_id": workflow_id,
                "status": "success" if result.get("success") else "failed",
                "duration_ms": result.get("duration_ms", 0),
            })

        except Exception as e:
            return self.error(f"Failed to execute workflow: {str(e)}")
