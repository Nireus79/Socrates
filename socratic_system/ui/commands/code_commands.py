"""Code generation and documentation commands"""

from typing import Dict, Any, List
from colorama import Fore, Style
from socratic_system.ui.commands.base import BaseCommand


class CodeGenerateCommand(BaseCommand):
    """Generate code for the current project"""

    def __init__(self):
        super().__init__(
            name="code generate",
            description="Generate code based on current project context",
            usage="code generate"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code generate command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator or not project:
            return self.error("Required context not available")

        print(f"\n{Fore.CYAN}Generating Code...{Style.RESET_ALL}")

        result = orchestrator.process_request('code_generator', {
            'action': 'generate_script',
            'project': project
        })

        if result['status'] == 'success':
            script = result['script']
            self.print_success("Code Generated Successfully!")
            print(f"\n{Fore.YELLOW}{'=' * 60}")
            print(f"{Fore.WHITE}{script}")
            print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}\n")

            # Ask if user wants documentation
            doc_choice = input(f"{Fore.CYAN}Generate documentation? (y/n): ").lower()
            if doc_choice == 'y':
                doc_result = orchestrator.process_request('code_generator', {
                    'action': 'generate_documentation',
                    'project': project,
                    'script': script
                })

                if doc_result['status'] == 'success':
                    self.print_success("Documentation Generated!")
                    print(f"\n{Fore.YELLOW}{'=' * 60}")
                    print(f"{Fore.WHITE}{doc_result['documentation']}")
                    print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}\n")

            return self.success(data={'script': script})
        else:
            return self.error(result.get('message', 'Failed to generate code'))


class CodeDocsCommand(BaseCommand):
    """Generate documentation for code"""

    def __init__(self):
        super().__init__(
            name="code docs",
            description="Generate comprehensive documentation for the project",
            usage="code docs"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code docs command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator or not project:
            return self.error("Required context not available")

        print(f"\n{Fore.CYAN}Generating Documentation...{Style.RESET_ALL}")

        # First generate code if not done yet
        result = orchestrator.process_request('code_generator', {
            'action': 'generate_script',
            'project': project
        })

        if result['status'] == 'success':
            script = result['script']

            # Generate documentation
            doc_result = orchestrator.process_request('code_generator', {
                'action': 'generate_documentation',
                'project': project,
                'script': script
            })

            if doc_result['status'] == 'success':
                self.print_success("Documentation Generated Successfully!")
                print(f"\n{Fore.YELLOW}{'=' * 60}")
                print(f"{Fore.WHITE}{doc_result['documentation']}")
                print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}\n")

                return self.success(data={'documentation': doc_result['documentation']})
            else:
                return self.error(doc_result.get('message', 'Failed to generate documentation'))
        else:
            return self.error(result.get('message', 'Failed to generate code'))
