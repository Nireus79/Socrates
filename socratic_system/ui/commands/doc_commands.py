"""Document and knowledge base management commands"""

from typing import Dict, Any, List
from colorama import Fore, Style
from socratic_system.ui.commands.base import BaseCommand


class DocImportCommand(BaseCommand):
    """Import a single document into the knowledge base"""

    def __init__(self):
        super().__init__(
            name="docs import",
            description="Import a single file into the knowledge base",
            usage="docs import <path>"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute docs import command"""
        if not self.validate_args(args, min_count=1):
            file_path = input(f"{Fore.WHITE}Enter file path: ").strip()
        else:
            file_path = ' '.join(args)  # Allow spaces in file path

        if not file_path:
            return self.error("File path cannot be empty")

        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Ask if they want to link to current project
        project_id = None
        if project:
            link_choice = input(
                f"{Fore.CYAN}Link to current project '{project.name}'? (y/n): ").lower()
            if link_choice == 'y':
                project_id = project.project_id

        print(f"{Fore.YELLOW}Processing file...{Style.RESET_ALL}")

        result = orchestrator.process_request('document_agent', {
            'action': 'import_file',
            'file_path': file_path,
            'project_id': project_id
        })

        if result['status'] == 'success':
            self.print_success(f"Successfully imported '{result.get('file_name', 'file')}'")
            print(f"{Fore.WHITE}Added {result.get('entries_added', 0)} knowledge entries")

            return self.success(data={'file_name': result.get('file_name'), 'entries_added': result.get('entries_added')})
        else:
            return self.error(result.get('message', 'Failed to import file'))


class DocImportDirCommand(BaseCommand):
    """Import all files from a directory into the knowledge base"""

    def __init__(self):
        super().__init__(
            name="docs import-dir",
            description="Import all files from a directory into the knowledge base",
            usage="docs import-dir <path>"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute docs import-dir command"""
        if not self.validate_args(args, min_count=1):
            directory_path = input(f"{Fore.WHITE}Enter directory path: ").strip()
        else:
            directory_path = ' '.join(args)  # Allow spaces in directory path

        if not directory_path:
            return self.error("Directory path cannot be empty")

        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Ask if they want to include subdirectories
        recursive_choice = input(
            f"{Fore.CYAN}Include subdirectories? (y/n): ").lower()
        recursive = recursive_choice == 'y'

        # Ask if they want to link to current project
        project_id = None
        if project:
            link_choice = input(
                f"{Fore.CYAN}Link to current project '{project.name}'? (y/n): ").lower()
            if link_choice == 'y':
                project_id = project.project_id

        print(f"{Fore.YELLOW}Processing directory...{Style.RESET_ALL}")

        result = orchestrator.process_request('document_agent', {
            'action': 'import_directory',
            'directory_path': directory_path,
            'project_id': project_id,
            'recursive': recursive
        })

        if result['status'] == 'success':
            self.print_success(result.get('message', 'Directory processed'))

            summary = result.get('summary', {})
            print(f"{Fore.WHITE}Processed files:  {len(summary.get('processed_files', []))}")
            print(f"Failed files:     {len(summary.get('failed_files', []))}")
            print(f"Total entries:    {summary.get('total_entries', 0)}")

            if summary.get('failed_files'):
                print(f"\n{Fore.YELLOW}Failed files:{Style.RESET_ALL}")
                for failed in summary['failed_files']:
                    print(f"  - {failed.get('file', 'unknown')}: {failed.get('error', 'unknown error')}")

            return self.success(data={'summary': summary})
        else:
            return self.error(result.get('message', 'Failed to import directory'))


class DocListCommand(BaseCommand):
    """List imported documents"""

    def __init__(self):
        super().__init__(
            name="docs list",
            description="List all imported documents",
            usage="docs list [project-id]"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute docs list command"""
        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Get project ID from args or current project
        if args:
            project_id = args[0]
        elif project:
            project_id = project.project_id
        else:
            return self.error("No project specified and no project loaded")

        result = orchestrator.process_request('document_agent', {
            'action': 'list_documents',
            'project_id': project_id
        })

        if result['status'] == 'success':
            documents = result.get('documents', [])

            if not documents:
                self.print_info("No documents imported for this project")
                return self.success()

            print(f"\n{Fore.CYAN}Imported Documents:{Style.RESET_ALL}")
            for i, doc in enumerate(documents, 1):
                file_name = doc.get('file_name', 'unknown')
                entries = doc.get('entries_count', 0)
                imported_at = doc.get('imported_at', 'unknown')

                print(f"{i}. {Fore.WHITE}{file_name:40}{Style.RESET_ALL} ({entries} entries) - {imported_at}")

            print()
            return self.success(data={'documents': documents})
        else:
            return self.error(result.get('message', 'Failed to list documents'))
