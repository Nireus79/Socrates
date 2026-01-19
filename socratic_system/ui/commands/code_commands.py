"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.Code generation and documentation commands"""

from pathlib import Path
from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand
from socratic_system.utils.artifact_saver import ArtifactSaver
from socratic_system.utils.orchestrator_helper import safe_orchestrator_call


class CodeGenerateCommand(BaseCommand):
    """Generate code for the current project"""

    def __init__(self):
        super().__init__(
            name="code generate",
            description="Generate code based on current project context",
            usage="code generate",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code generate command"""
        # Validate context
        validation_error = self._validate_code_context(context)
        if validation_error:
            return validation_error

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        print(f"\n{Fore.CYAN}Generating Code...{Style.RESET_ALL}")

        # Generate code
        try:
            result = safe_orchestrator_call(
                orchestrator,
                "code_generator",
                {"action": "generate_script", "project": project},
                operation_name="generate code script"
            )

            script = result.get("script")
            save_path = result.get("save_path")
            is_multi_file = result.get("is_multi_file", False)

            self.print_success("Code Generated Successfully!")

            # Display generated code
            self._display_generated_code(script, save_path, is_multi_file)

            # Ask if user wants documentation
            if self._prompt_for_documentation():
                self._generate_and_display_documentation(orchestrator, project, script, save_path)

            return self.success(data={"script": script, "save_path": save_path})
        except ValueError as e:
            return self.error(str(e))

    def _validate_code_context(self, context: Dict[str, Any]) -> Dict:
        """Validate required context for code generation"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        return None

    def _display_generated_code(self, script: str, save_path: str, is_multi_file: bool) -> None:
        """Display generated code or project structure"""
        if is_multi_file:
            self._display_multi_file_structure(save_path)
        else:
            self._display_single_file_code(script, save_path)

    def _display_multi_file_structure(self, save_path: str) -> None:
        """Display multi-file project structure"""
        print(ArtifactSaver.get_save_location_message(save_path))
        print(f"\n{Fore.CYAN}Project Structure:{Style.RESET_ALL}")
        tree = ArtifactSaver.get_project_structure_tree(save_path)
        print(tree)

        files = ArtifactSaver.list_project_files(save_path)
        print(f"\n{Fore.GREEN}Total files:{Style.RESET_ALL} {len(files)} files created")

    def _display_single_file_code(self, script: str, save_path: str) -> None:
        """Display single-file code"""
        print(f"\n{Fore.YELLOW}{'=' * 60}")
        print(f"{Fore.WHITE}{script}")
        print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")

        if save_path:
            self._display_save_location(save_path, "Save path was returned but file not found")

    def _display_save_location(self, save_path: str, warning_msg: str) -> None:
        """Display save location or warning if not found"""
        if Path(save_path).exists():
            print(ArtifactSaver.get_save_location_message(save_path))
        else:
            self.print_warning(f"{warning_msg}: {save_path}")

    def _prompt_for_documentation(self) -> bool:
        """Ask user if they want documentation"""
        doc_choice = input(f"{Fore.CYAN}Generate documentation? (y/n): ").lower()
        return doc_choice == "y"

    def _generate_and_display_documentation(
        self, orchestrator, project, script: str, save_path: str
    ) -> None:
        """Generate and display documentation"""
        try:
            doc_result = safe_orchestrator_call(
                orchestrator,
                "code_generator",
                {"action": "generate_documentation", "project": project, "script": script},
                operation_name="generate code documentation"
            )

            doc_save_path = doc_result.get("save_path")

            self.print_success("Documentation Generated!")
            print(f"\n{Fore.YELLOW}{'=' * 60}")
            print(f"{Fore.WHITE}{doc_result['documentation']}")
            print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")

            if doc_save_path:
                self._display_save_location(
                    doc_save_path, "Documentation save path returned but file not found"
                )
        except ValueError as e:
            self.print_warning("Failed to generate documentation")


class CodeDocsCommand(BaseCommand):
    """Generate documentation for code"""

    def __init__(self):
        super().__init__(
            name="code docs",
            description="Generate comprehensive documentation for the project",
            usage="code docs",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code docs command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        print(f"\n{Fore.CYAN}Generating Documentation...{Style.RESET_ALL}")

        # First generate code if not done yet
        try:
            result = safe_orchestrator_call(
                orchestrator,
                "code_generator",
                {"action": "generate_script", "project": project},
                operation_name="generate code script"
            )

            script = result.get("script")

            # Generate documentation
            try:
                doc_result = safe_orchestrator_call(
                    orchestrator,
                    "code_generator",
                    {"action": "generate_documentation", "project": project, "script": script},
                    operation_name="generate code documentation"
                )

                doc_save_path = doc_result.get("save_path")

                self.print_success("Documentation Generated Successfully!")
                print(f"\n{Fore.YELLOW}{'=' * 60}")
                print(f"{Fore.WHITE}{doc_result['documentation']}")
                print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")

                # Show save location
                if doc_save_path:
                    print(ArtifactSaver.get_save_location_message(doc_save_path))

                return self.success(
                    data={"documentation": doc_result.get("documentation"), "save_path": doc_save_path}
                )
            except ValueError as e:
                return self.error(str(e))
        except ValueError as e:
            return self.error(str(e))
