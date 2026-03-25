"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.
Automatic documentation generation commands
"""

from typing import Any, Dict, List
from colorama import Fore, Style
from socratic_system.ui.commands.base import BaseCommand


class GenerateReadmeCommand(BaseCommand):
    """Generate comprehensive README documentation"""

    def __init__(self):
        super().__init__(
            name="docs generate readme",
            description="Generate a comprehensive README file for the project",
            usage="docs generate readme <project_name>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute README generation command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.docs:
            return self.error("Documentation generator not available")

        project_name = args[0] if args else input(f"{Fore.WHITE}Project name: ").strip()
        if not project_name:
            return self.error("Project name cannot be empty")

        description = input(f"{Fore.WHITE}Project description: ").strip()
        if not description:
            return self.error("Project description cannot be empty")

        features_input = input(f"{Fore.WHITE}Features (comma-separated, optional): ").strip()
        features = [f.strip() for f in features_input.split(",") if f.strip()] if features_input else None

        installation = input(f"{Fore.WHITE}Installation instructions (optional): ").strip() or None
        usage = input(f"{Fore.WHITE}Usage instructions (optional): ").strip() or None

        try:
            readme_content = library_manager.docs.generate_comprehensive_readme(
                project_name=project_name,
                description=description,
                features=features,
                installation=installation,
                usage=usage
            )

            if not readme_content:
                return self.error("Failed to generate README")

            self.print_header(f"README Generated for {project_name}")
            self.print_success("README generated successfully")

            # Print preview
            preview_lines = readme_content.split("\n")[:20]
            print(f"\n{Fore.CYAN}Preview:{Style.RESET_ALL}")
            for line in preview_lines:
                print(f"  {line}")
            if len(readme_content.split('\n')) > 20:
                print(f"  ... ({len(readme_content.split(chr(10))) - 20} more lines)")

            return self.success(data={
                "project_name": project_name,
                "description": description,
                "content_length": len(readme_content),
                "content": readme_content,
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class GenerateApiDocsCommand(BaseCommand):
    """Generate API documentation from code structure"""

    def __init__(self):
        super().__init__(
            name="docs generate api",
            description="Generate API documentation from code structure",
            usage="docs generate api <file_path>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API documentation generation command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.docs:
            return self.error("Documentation generator not available")

        file_path = args[0] if args else input(f"{Fore.WHITE}File path: ").strip()
        if not file_path:
            return self.error("File path cannot be empty")

        try:
            # Read the file to get code structure
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()

            # Simple code structure extraction (ideally would use AST)
            code_structure = {
                "file": file_path,
                "content": code_content,
                "size": len(code_content)
            }

            api_docs = library_manager.docs.generate_api_documentation(code_structure)

            if not api_docs:
                return self.error("Failed to generate API documentation")

            self.print_header(f"API Documentation for {file_path}")
            self.print_success("API documentation generated successfully")

            # Print preview
            preview_lines = api_docs.split("\n")[:20]
            print(f"\n{Fore.CYAN}Preview:{Style.RESET_ALL}")
            for line in preview_lines:
                print(f"  {line}")
            if len(api_docs.split('\n')) > 20:
                print(f"  ... ({len(api_docs.split(chr(10))) - 20} more lines)")

            return self.success(data={
                "file": file_path,
                "content_length": len(api_docs),
                "content": api_docs,
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class GenerateArchitectureDocsCommand(BaseCommand):
    """Generate architecture documentation"""

    def __init__(self):
        super().__init__(
            name="docs generate architecture",
            description="Generate architecture documentation for modules",
            usage="docs generate architecture <module1> [module2] ...",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute architecture documentation generation command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.docs:
            return self.error("Documentation generator not available")

        if args:
            modules = args
        else:
            modules_input = input(f"{Fore.WHITE}Modules (comma-separated): ").strip()
            if not modules_input:
                return self.error("At least one module is required")
            modules = [m.strip() for m in modules_input.split(",")]

        try:
            arch_docs = library_manager.docs.generate_architecture_docs(modules)

            if not arch_docs:
                return self.error("Failed to generate architecture documentation")

            self.print_header("Architecture Documentation")
            self.print_success("Architecture documentation generated successfully")

            print(f"\n{Fore.CYAN}Modules Documented:{Style.RESET_ALL}")
            for module in modules:
                print(f"  - {module}")

            # Print preview
            preview_lines = arch_docs.split("\n")[:20]
            print(f"\n{Fore.CYAN}Preview:{Style.RESET_ALL}")
            for line in preview_lines:
                print(f"  {line}")
            if len(arch_docs.split('\n')) > 20:
                print(f"  ... ({len(arch_docs.split(chr(10))) - 20} more lines)")

            return self.success(data={
                "modules": modules,
                "modules_count": len(modules),
                "content_length": len(arch_docs),
                "content": arch_docs,
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class GenerateAllDocsCommand(BaseCommand):
    """Generate all documentation types"""

    def __init__(self):
        super().__init__(
            name="docs generate all",
            description="Generate all documentation types for a project",
            usage="docs generate all <project_name> <project_path>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive documentation generation command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.docs:
            return self.error("Documentation generator not available")

        project_name = args[0] if args else input(f"{Fore.WHITE}Project name: ").strip()
        if not project_name:
            return self.error("Project name cannot be empty")

        project_path = args[1] if len(args) > 1 else input(f"{Fore.WHITE}Project path: ").strip()
        if not project_path:
            return self.error("Project path cannot be empty")

        description = input(f"{Fore.WHITE}Project description: ").strip() or "Auto-generated documentation"

        try:
            docs_generated = {}

            # Generate README
            readme = library_manager.docs.generate_comprehensive_readme(
                project_name=project_name,
                description=description
            )
            if readme:
                docs_generated["readme"] = len(readme)

            # Generate Architecture docs
            modules = ["core", "ui", "database", "orchestration"]
            arch_docs = library_manager.docs.generate_architecture_docs(modules)
            if arch_docs:
                docs_generated["architecture"] = len(arch_docs)

            self.print_header(f"Complete Documentation Generated for {project_name}")
            self.print_success("All documentation generated successfully")

            print(f"\n{Fore.CYAN}Generated Documents:{Style.RESET_ALL}")
            for doc_type, size in docs_generated.items():
                print(f"  {doc_type}: {size} bytes")

            print(f"\n{Fore.CYAN}Total: {sum(docs_generated.values())} bytes{Style.RESET_ALL}")

            return self.success(data={
                "project_name": project_name,
                "project_path": project_path,
                "documents_generated": list(docs_generated.keys()),
                "total_size": sum(docs_generated.values()),
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")
