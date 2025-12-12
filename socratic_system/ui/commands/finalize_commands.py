"""Finalize project - generate artifacts and documentation for any project type"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class FinalizeGenerateCommand(BaseCommand):
    """Generate project-type-appropriate artifact (code, business plan, research protocol, etc.)"""

    def __init__(self):
        super().__init__(
            name="finalize generate",
            description="Generate project artifact based on type (code, business plan, research protocol, etc.)",
            usage="finalize generate",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute finalize generate command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Map project types to artifact names
        artifact_names = {
            "software": "Code",
            "business": "Business Plan",
            "research": "Research Protocol",
            "creative": "Creative Brief",
            "marketing": "Marketing Plan",
            "educational": "Curriculum",
        }
        artifact_name = artifact_names.get(project.project_type, "Artifact")

        print(f"\n{Fore.CYAN}Generating {artifact_name}...{Style.RESET_ALL}")

        result = orchestrator.process_request(
            "code_generator", {"action": "generate_artifact", "project": project}
        )

        if result["status"] == "success":
            artifact = result["artifact"]
            artifact_type = result.get("artifact_type", "code")

            self.print_success(f"{artifact_name} Generated Successfully!")
            print(f"\n{Fore.YELLOW}{'=' * 60}")
            print(f"{Fore.WHITE}{artifact}")
            print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}\n")

            # Ask if user wants documentation
            doc_choice = input(f"{Fore.CYAN}Generate implementation documentation? (y/n): ").lower()
            if doc_choice == "y":
                doc_result = orchestrator.process_request(
                    "code_generator",
                    {
                        "action": "generate_documentation",
                        "project": project,
                        "artifact": artifact,
                    },
                )

                if doc_result["status"] == "success":
                    self.print_success("Documentation Generated!")
                    print(f"\n{Fore.YELLOW}{'=' * 60}")
                    print(f"{Fore.WHITE}{doc_result['documentation']}")
                    print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}\n")

            return self.success(data={"artifact": artifact, "artifact_type": artifact_type})
        else:
            return self.error(result.get("message", f"Failed to generate {artifact_name.lower()}"))


class FinalizeDocsCommand(BaseCommand):
    """Generate implementation documentation for project artifact"""

    def __init__(self):
        super().__init__(
            name="finalize docs",
            description="Generate implementation documentation for the project",
            usage="finalize docs",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute finalize docs command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Map project types to artifact names
        artifact_names = {
            "software": "Code",
            "business": "Business Plan",
            "research": "Research Protocol",
            "creative": "Creative Brief",
            "marketing": "Marketing Plan",
            "educational": "Curriculum",
        }
        artifact_name = artifact_names.get(project.project_type, "Artifact")

        print(f"\n{Fore.CYAN}Generating {artifact_name} and Documentation...{Style.RESET_ALL}")

        # First generate artifact if not done yet
        result = orchestrator.process_request(
            "code_generator", {"action": "generate_artifact", "project": project}
        )

        if result["status"] == "success":
            artifact = result["artifact"]

            # Generate documentation
            doc_result = orchestrator.process_request(
                "code_generator",
                {
                    "action": "generate_documentation",
                    "project": project,
                    "artifact": artifact,
                },
            )

            if doc_result["status"] == "success":
                self.print_success("Documentation Generated Successfully!")
                print(f"\n{Fore.YELLOW}{'=' * 60}")
                print(f"{Fore.WHITE}{doc_result['documentation']}")
                print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}\n")

                return self.success(data={"documentation": doc_result["documentation"]})
            else:
                return self.error(doc_result.get("message", "Failed to generate documentation"))
        else:
            return self.error(result.get("message", f"Failed to generate {artifact_name.lower()}"))
