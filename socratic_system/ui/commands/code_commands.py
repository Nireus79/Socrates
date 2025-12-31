"""Code generation and documentation commands"""

from pathlib import Path
from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand
from socratic_system.utils.artifact_saver import ArtifactSaver


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
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        print(f"\n{Fore.CYAN}Generating Code...{Style.RESET_ALL}")

        result = orchestrator.process_request(
            "code_generator", {"action": "generate_script", "project": project}
        )

        if result["status"] == "success":
            script = result["script"]
            save_path = result.get("save_path")
            is_multi_file = result.get("is_multi_file", False)

            self.print_success("Code Generated Successfully!")

            if is_multi_file:
                # For multi-file projects, show structure instead of raw code
                print(ArtifactSaver.get_save_location_message(save_path))
                print(f"\n{Fore.CYAN}Project Structure:{Style.RESET_ALL}")
                tree = ArtifactSaver.get_project_structure_tree(save_path)
                print(tree)

                # Show file summary
                files = ArtifactSaver.list_project_files(save_path)
                print(
                    f"\n{Fore.GREEN}Total files:{Style.RESET_ALL} {len(files)} files created"
                )
            else:
                # For single-file, show the code
                print(f"\n{Fore.YELLOW}{'=' * 60}")
                print(f"{Fore.WHITE}{script}")
                print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")

                # Show save location if file actually exists
                if save_path:
                    if Path(save_path).exists():
                        print(ArtifactSaver.get_save_location_message(save_path))
                    else:
                        self.print_warning(f"Save path was returned but file not found: {save_path}")

            # Ask if user wants documentation
            doc_choice = input(f"{Fore.CYAN}Generate documentation? (y/n): ").lower()
            if doc_choice == "y":
                doc_result = orchestrator.process_request(
                    "code_generator",
                    {"action": "generate_documentation", "project": project, "script": script},
                )

                if doc_result["status"] == "success":
                    doc_save_path = doc_result.get("save_path")

                    self.print_success("Documentation Generated!")
                    print(f"\n{Fore.YELLOW}{'=' * 60}")
                    print(f"{Fore.WHITE}{doc_result['documentation']}")
                    print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")

                    # Show save location if file actually exists
                    if doc_save_path:
                        if Path(doc_save_path).exists():
                            print(ArtifactSaver.get_save_location_message(doc_save_path))
                        else:
                            self.print_warning(f"Documentation save path returned but file not found: {doc_save_path}")

            return self.success(data={"script": script, "save_path": save_path})
        else:
            return self.error(result.get("message", "Failed to generate code"))


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
        result = orchestrator.process_request(
            "code_generator", {"action": "generate_script", "project": project}
        )

        if result["status"] == "success":
            script = result["script"]

            # Generate documentation
            doc_result = orchestrator.process_request(
                "code_generator",
                {"action": "generate_documentation", "project": project, "script": script},
            )

            if doc_result["status"] == "success":
                doc_save_path = doc_result.get("save_path")

                self.print_success("Documentation Generated Successfully!")
                print(f"\n{Fore.YELLOW}{'=' * 60}")
                print(f"{Fore.WHITE}{doc_result['documentation']}")
                print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")

                # Show save location
                if doc_save_path:
                    print(ArtifactSaver.get_save_location_message(doc_save_path))

                return self.success(
                    data={"documentation": doc_result["documentation"], "save_path": doc_save_path}
                )
            else:
                return self.error(doc_result.get("message", "Failed to generate documentation"))
        else:
            return self.error(result.get("message", "Failed to generate code"))
