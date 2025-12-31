"""Finalize project - generate artifacts and documentation for any project type"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand
from socratic_system.utils.artifact_saver import ArtifactSaver


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
        # Validate context
        validation_error = self._validate_finalize_context(context)
        if validation_error:
            return validation_error

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        # Get artifact name for display
        artifact_name = self._get_artifact_name(project.project_type)

        print(f"\n{Fore.CYAN}Generating {artifact_name}...{Style.RESET_ALL}")

        # Generate artifact
        result = orchestrator.process_request(
            "code_generator", {"action": "generate_artifact", "project": project}
        )

        if result["status"] != "success":
            return self.error(result.get("message", f"Failed to generate {artifact_name.lower()}"))

        artifact = result["artifact"]
        artifact_type = result.get("artifact_type", "code")
        save_path = result.get("save_path")
        is_multi_file = result.get("is_multi_file", False)

        self.print_success(f"{artifact_name} Generated Successfully!")

        # Display artifact
        self._display_artifact(artifact, save_path, is_multi_file)

        # Ask for documentation
        if self._prompt_for_documentation():
            self._generate_and_display_documentation(orchestrator, project, artifact, save_path)

        return self.success(
            data={"artifact": artifact, "artifact_type": artifact_type, "save_path": save_path}
        )

    def _validate_finalize_context(self, context: Dict[str, Any]) -> Dict:
        """Validate required context for finalize command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        return None

    def _get_artifact_name(self, project_type: str) -> str:
        """Get artifact name based on project type"""
        artifact_names = {
            "software": "Code",
            "business": "Business Plan",
            "research": "Research Protocol",
            "creative": "Creative Brief",
            "marketing": "Marketing Plan",
            "educational": "Curriculum",
        }
        return artifact_names.get(project_type, "Artifact")

    def _display_artifact(self, artifact: str, save_path: str, is_multi_file: bool) -> None:
        """Display artifact content or project structure"""
        if is_multi_file:
            self._display_multi_file_structure(save_path)
        else:
            self._display_single_file_artifact(artifact, save_path)

    def _display_multi_file_structure(self, save_path: str) -> None:
        """Display multi-file project structure"""
        print(ArtifactSaver.get_save_location_message(save_path))
        print(f"\n{Fore.CYAN}Project Structure:{Style.RESET_ALL}")
        tree = ArtifactSaver.get_project_structure_tree(save_path)
        print(tree)

        files = ArtifactSaver.list_project_files(save_path)
        print(f"\n{Fore.GREEN}Total files:{Style.RESET_ALL} {len(files)} files created")

    def _display_single_file_artifact(self, artifact: str, save_path: str) -> None:
        """Display single-file artifact"""
        print(f"\n{Fore.YELLOW}{'=' * 60}")
        print(f"{Fore.WHITE}{artifact}")
        print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")

        if save_path:
            self._display_save_location(save_path, "Save path was returned but file not found")

    def _display_save_location(self, save_path: str, warning_msg: str) -> None:
        """Display save location or warning if not found"""
        from pathlib import Path

        if Path(save_path).exists():
            print(ArtifactSaver.get_save_location_message(save_path))
        else:
            self.print_warning(f"{warning_msg}: {save_path}")

    def _prompt_for_documentation(self) -> bool:
        """Ask user if they want documentation"""
        doc_choice = input(f"{Fore.CYAN}Generate implementation documentation? (y/n): ").lower()
        return doc_choice == "y"

    def _generate_and_display_documentation(
        self, orchestrator, project, artifact: str, save_path: str
    ) -> None:
        """Generate and display implementation documentation"""
        doc_result = orchestrator.process_request(
            "code_generator",
            {
                "action": "generate_documentation",
                "project": project,
                "artifact": artifact,
            },
        )

        if doc_result["status"] != "success":
            self.print_warning("Failed to generate documentation")
            return

        doc_save_path = doc_result.get("save_path")

        self.print_success("Documentation Generated!")
        print(f"\n{Fore.YELLOW}{'=' * 60}")
        print(f"{Fore.WHITE}{doc_result['documentation']}")
        print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")

        if doc_save_path:
            self._display_save_location(
                doc_save_path, "Documentation save path returned but file not found"
            )


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
                doc_save_path = doc_result.get("save_path")

                self.print_success("Documentation Generated Successfully!")
                print(f"\n{Fore.YELLOW}{'=' * 60}")
                print(f"{Fore.WHITE}{doc_result['documentation']}")
                print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")

                # Show save location if file actually exists
                if doc_save_path:
                    from pathlib import Path

                    if Path(doc_save_path).exists():
                        print(ArtifactSaver.get_save_location_message(doc_save_path))
                    else:
                        self.print_warning(
                            f"Documentation save path returned but file not found: {doc_save_path}"
                        )

                return self.success(
                    data={"documentation": doc_result["documentation"], "save_path": doc_save_path}
                )
            else:
                return self.error(doc_result.get("message", "Failed to generate documentation"))
        else:
            return self.error(result.get("message", f"Failed to generate {artifact_name.lower()}"))
