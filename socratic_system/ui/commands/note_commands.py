"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.Project note management commands
"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_core.utils import serialize_datetime
from socratic_system.models.note import ProjectNote
from socratic_system.ui.commands.base import BaseCommand


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
            # Create a ProjectNote and save it to the database
            note = ProjectNote.create(
                project_id=project.project_id,
                note_type=note_type,
                title=title,
                content=content,
                created_by=user.username,
                tags=tags,
            )

            # Save note to database
            try:
                orchestrator.database.save_note(note)
            except Exception as e:
                return self.error(f"Failed to save note: {str(e)}")

            self.print_success(f"Note '{title}' added")
            print(f"{Fore.CYAN}Note ID: {note.note_id}")

            # Return note as dict
            return self.success(
                data={
                    "note": {
                        "note_id": note.note_id,
                        "project_id": note.project_id,
                        "title": note.title,
                        "content": note.content,
                        "note_type": note.note_type,
                        "created_by": note.created_by,
                        "created_at": (
                            serialize_datetime(note.created_at)
                            if hasattr(note.created_at, "isoformat")
                            else str(note.created_at)
                        ),
                        "tags": note.tags,
                    }
                }
            )
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
            # Get notes from database
            notes_list = orchestrator.database.get_project_notes(project.project_id, note_type)

            if not notes_list:
                self.print_info("No notes found")
                return self.success(data={"notes": [], "count": 0})

            title = f"Notes for '{project.name}'"
            if note_type:
                title += f" (Type: {note_type})"

            self.print_header(title)

            # Convert ProjectNote objects to dicts
            notes_data = []
            for note in notes_list:
                preview = note.content[:100] + "..." if len(note.content) > 100 else note.content
                note_dict = {
                    "note_id": note.note_id,
                    "project_id": note.project_id,
                    "title": note.title,
                    "content": note.content,
                    "type": note.note_type,
                    "note_type": note.note_type,
                    "created_by": note.created_by,
                    "created_at": (
                        serialize_datetime(note.created_at)
                        if hasattr(note.created_at, "isoformat")
                        else str(note.created_at)
                    ),
                    "tags": note.tags,
                    "preview": preview,
                }
                notes_data.append(note_dict)

                type_label = {
                    "design": "[DESIGN]",
                    "bug": "[BUG]",
                    "idea": "[IDEA]",
                    "task": "[TASK]",
                    "general": "[NOTE]",
                }.get(note.note_type, "[NOTE]")

                print(f"{Fore.CYAN}{type_label} {note.title}{Style.RESET_ALL}")
                print(f"   Created by: {note.created_by} on {note_dict['created_at']}")
                if note.tags:
                    print(f"   Tags: {', '.join(note.tags)}")
                print(f"   {preview}")
                print(f"   ID: {Fore.YELLOW}{note.note_id}{Style.RESET_ALL}")
                print()

            count = len(notes_list)
            print(f"Total: {count} note(s)")
            return self.success(data={"notes": notes_data, "count": count})
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
            # Get all notes and search in memory
            all_notes = orchestrator.database.get_project_notes(project.project_id)

            # Filter notes matching the query
            results = [note for note in all_notes if note.matches_query(query)]

            if not results:
                self.print_info(f"No notes found matching '{query}'")
                return self.success(data={"results": [], "count": 0})

            self.print_header(f"Search Results for '{query}'")

            # Convert to dicts and display
            results_data = []
            for note in results:
                preview = note.content[:100] + "..." if len(note.content) > 100 else note.content
                note_dict = {
                    "note_id": note.note_id,
                    "project_id": note.project_id,
                    "title": note.title,
                    "content": note.content,
                    "type": note.note_type,
                    "note_type": note.note_type,
                    "created_by": note.created_by,
                    "created_at": (
                        serialize_datetime(note.created_at)
                        if hasattr(note.created_at, "isoformat")
                        else str(note.created_at)
                    ),
                    "tags": note.tags,
                    "preview": preview,
                }
                results_data.append(note_dict)

                type_label = {
                    "design": "[DESIGN]",
                    "bug": "[BUG]",
                    "idea": "[IDEA]",
                    "task": "[TASK]",
                    "general": "[NOTE]",
                }.get(note.note_type, "[NOTE]")

                print(f"{Fore.CYAN}{type_label} {note.title}{Style.RESET_ALL}")
                print(f"   Type: {note.note_type} | Created by: {note.created_by}")
                if note.tags:
                    print(f"   Tags: {', '.join(note.tags)}")
                print(f"   {preview}")
                print()

            count = len(results)
            print(f"Found: {count} note(s)")
            return self.success(data={"results": results_data, "count": count})
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
            # Delete note from database
            success = orchestrator.database.delete_note(note_id)
            if not success:
                return self.error(f"Failed to delete note {note_id}")

            self.print_success("Note deleted successfully")
            return self.success(data={"deleted_note_id": note_id})
        except Exception as e:
            return self.error(f"Failed to delete note: {str(e)}")
