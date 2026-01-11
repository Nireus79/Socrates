"""File management commands"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class FileDeleteCommand(BaseCommand):
    """Delete a file from the current project"""

    def __init__(self):
        super().__init__(
            name="file delete",
            description="Delete a file from the current project",
            usage="file delete <file_name>"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file delete command"""
        # Check if user is logged in
        if not self.require_user(context):
            return self.error("Must be logged in to delete files")

        # Check if project is loaded
        if not self.require_project(context):
            return self.error("No project loaded. Use '/project load' first")

        # Validate arguments
        if not self.validate_args(args, min_count=1):
            file_name = input(f"{Fore.WHITE}File name to delete: ").strip()
        else:
            file_name = " ".join(args)  # Allow spaces in file names

        if not file_name:
            return self.error("File name cannot be empty")

        # Get project and orchestrator from context
        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not project or not orchestrator:
            return self.error("Required context not available")

        # Confirm deletion
        confirm = input(
            f"{Fore.YELLOW}Are you sure you want to delete '{file_name}'? This cannot be undone. (yes/no): {Style.RESET_ALL}"
        ).strip().lower()

        if confirm != "yes":
            return self.info("Deletion cancelled")

        # Delete the file using ProjectFileManager
        try:
            from socratic_system.database.project_file_manager import ProjectFileManager

            file_manager = ProjectFileManager(orchestrator.database.db_path)
            success, message = file_manager.delete_file(project.project_id, file_name)

            if success:
                self.print_success(f"File '{file_name}' deleted successfully!")
                return self.success(data={
                    "file_name": file_name,
                    "project_id": project.project_id
                })
            else:
                # Parse the error message to provide better feedback
                if "not found" in message.lower():
                    return self.error(f"File '{file_name}' not found in project")
                elif "directory" in message.lower():
                    return self.error(f"Cannot delete: {message}")
                else:
                    return self.error(f"Failed to delete file: {message}")

        except Exception as error:
            error_message = str(error)
            self.print_error(f"Error deleting file: {error_message}")
            return self.error(f"Failed to delete file: {error_message}")


__all__ = ["FileDeleteCommand"]
