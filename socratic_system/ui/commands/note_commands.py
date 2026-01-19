"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.Project note management commands
"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand
from socratic_system.utils.orchestrator_helper import safe_orchestrator_call


class NoteAddCommand(BaseCommand):
    """Add a new note to the current project"""

    def __init__(self):
        super().__init__(
            name="note add",
            description="Add a new note to the current project",
            usage="note add <type> <title>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute note add command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")
        user = context.get("user")

        if not orchestrator or not project or not user:
            return self.error("Required context not available")

        # Parse arguments
        if len(args) >= 2:
            note_type = args[0]
            title = " ".join(args[1:])
        else:
            note_type = (
                input(f"{Fore.WHITE}Note type (design/bug/idea/task/general): ").strip().lower()
            )
            title = input(f"{Fore.WHITE}Note title: ").strip()

        if not note_type or not title:
            return self.error("Note type and title cannot be empty")

        # Validate note type
        valid_types = ["design", "bug", "idea", "task", "general"]
        if note_type not in valid_types:
            return self.error(f"Invalid note type. Must be one of: {', '.join(valid_types)}")

        # Get tags
        tags_input = input(f"{Fore.WHITE}Tags (comma-separated, optional): ").strip()
        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

        # Get content
        print(f"{Fore.YELLOW}Enter note content (press Enter twice to finish):{Style.RESET_ALL}")
        lines = []
        empty_lines = 0
        while empty_lines < 2:
            line = input()
            if line == "":
                empty_lines += 1
            else:
                empty_lines = 0
            lines.append(line)

        content = "\n".join(lines[:-2]) if len(lines) > 2 else ""  # Remove last two empty lines

        if not content.strip():
            return self.error("Note content cannot be empty")

        try:
            # Add note via orchestrator
            result = safe_orchestrator_call(
                orchestrator,
                "note_manager",
                {
                    "action": "add_note",
                    "project_id": project.project_id,
                    "note_type": note_type,
                    "title": title,
                    "content": content,
                    "created_by": user.username,
                    "tags": tags,
                },
                operation_name="add note",
            )

            note_data = result.get("note", {})
            self.print_success(f"Note '{title}' added")
            print(f"{Fore.CYAN}Note ID: {note_data.get('note_id', 'unknown')}")

            return self.success(data={"note": note_data})
        except ValueError as e:
            return self.error(str(e))


class NoteListCommand(BaseCommand):
    """List notes for the current project"""

    def __init__(self):
        super().__init__(
            name="note list",
            description="List notes for the current project",
            usage="note list [type]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute note list command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Get note type filter if provided
        note_type = args[0].lower() if args else None

        # Validate note type if provided
        if note_type:
            valid_types = ["design", "bug", "idea", "task", "general"]
            if note_type not in valid_types:
                return self.error(f"Invalid note type. Must be one of: {', '.join(valid_types)}")

        try:
            # List notes via orchestrator
            result = safe_orchestrator_call(
                orchestrator,
                "note_manager",
                {"action": "list_notes", "project_id": project.project_id, "note_type": note_type},
                operation_name="list notes",
            )

            notes = result.get("notes", [])
            count = result.get("count", 0)

            if count == 0:
                self.print_info("No notes found")
                return self.success(data={"notes": [], "count": 0})

            title = f"Notes for '{project.name}'"
            if note_type:
                title += f" (Type: {note_type})"

            self.print_header(title)

            for note in notes:
                type_label = {
                    "design": "[DESIGN]",
                    "bug": "[BUG]",
                    "idea": "[IDEA]",
                    "task": "[TASK]",
                    "general": "[NOTE]",
                }.get(note["type"], "[NOTE]")

                print(f"{Fore.CYAN}{type_label} {note['title']}{Style.RESET_ALL}")
                print(f"   Created by: {note['created_by']} on {note['created_at']}")
                if note.get("tags"):
                    print(f"   Tags: {', '.join(note['tags'])}")
                print(f"   {note['preview']}")
                print(f"   ID: {Fore.YELLOW}{note['note_id']}{Style.RESET_ALL}")
                print()

            print(f"Total: {count} note(s)")
            return self.success(data={"notes": notes, "count": count})
        except ValueError as e:
            return self.error(str(e))


class NoteSearchCommand(BaseCommand):
    """Search notes in the current project"""

    def __init__(self):
        super().__init__(
            name="note search",
            description="Search notes in the current project",
            usage="note search <query>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute note search command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        if not args:
            query = input(f"{Fore.WHITE}Search query: ").strip()
        else:
            query = " ".join(args)

        if not query:
            return self.error("Search query cannot be empty")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        try:
            # Search notes via orchestrator
            result = safe_orchestrator_call(
                orchestrator,
                "note_manager",
                {"action": "search_notes", "project_id": project.project_id, "query": query},
                operation_name="search notes",
            )

            results = result.get("results", [])
            count = result.get("count", 0)

            if count == 0:
                self.print_info(f"No notes found matching '{query}'")
                return self.success(data={"results": [], "count": 0})

            self.print_header(f"Search Results for '{query}'")

            for note in results:
                type_label = {
                    "design": "[DESIGN]",
                    "bug": "[BUG]",
                    "idea": "[IDEA]",
                    "task": "[TASK]",
                    "general": "[NOTE]",
                }.get(note["type"], "[NOTE]")

                print(f"{Fore.CYAN}{type_label} {note['title']}{Style.RESET_ALL}")
                print(f"   Type: {note['type']} | Created by: {note['created_by']}")
                if note.get("tags"):
                    print(f"   Tags: {', '.join(note['tags'])}")
                print(f"   {note['preview']}")
                print()

            print(f"Found: {count} note(s)")
            return self.success(data={"results": results, "count": count})
        except ValueError as e:
            return self.error(str(e))


class NoteDeleteCommand(BaseCommand):
    """Delete a note from the current project"""

    def __init__(self):
        super().__init__(
            name="note delete",
            description="Delete a note from the current project",
            usage="note delete <note-id>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute note delete command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        if not args:
            note_id = input(f"{Fore.WHITE}Note ID to delete: ").strip()
        else:
            note_id = args[0]

        if not note_id:
            return self.error("Note ID cannot be empty")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Confirm deletion
        confirm = input(f"{Fore.RED}Are you sure you want to delete this note? (yes/no): ").lower()
        if confirm != "yes":
            self.print_info("Deletion cancelled")
            return self.success()

        try:
            # Delete note via orchestrator
            result = safe_orchestrator_call(
                orchestrator,
                "note_manager",
                {"action": "delete_note", "note_id": note_id, "project_id": project.project_id},
                operation_name="delete note",
            )

            self.print_success("Note deleted successfully")
            return self.success(data={"deleted_note_id": note_id})
        except ValueError as e:
            return self.error(str(e))
