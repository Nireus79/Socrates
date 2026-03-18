"""Knowledge management commands for project-specific and global knowledge"""

import json
from pathlib import Path
from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.models.knowledge import KnowledgeEntry
from socratic_system.ui.commands.base import BaseCommand


class KnowledgeAddCommand(BaseCommand):
    """Add knowledge to current project"""

    def __init__(self):
        super().__init__(
            name="knowledge add",
            description="Add a new knowledge entry to current project",
            usage="knowledge add --content=<text> --category=<cat> [--topic=<t>] [--difficulty=beginner|intermediate|advanced]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge add command"""
        if not self.require_project(context):
            return self.error("No project loaded. Load a project first with 'project select'")

        # Parse named arguments
        params = self._parse_args(args)

        if not params.get("content"):
            return self.error("Required: --content=<knowledge content>")
        if not params.get("category"):
            return self.error("Required: --category=<category name>")

        try:
            orchestrator = context.get("orchestrator")
            project = context.get("project")

            # Generate entry ID from content (non-security use)
            import hashlib

            # Use MD5 for non-security purposes (content hashing for ID generation)
            try:
                entry_id = hashlib.md5(
                    params["content"].encode(), usedforsecurity=False
                ).hexdigest()[:12]
            except TypeError:
                # Python 3.8 doesn't support usedforsecurity parameter
                entry_id = hashlib.md5(params["content"].encode()).hexdigest()[:12]  # nosec

            # Create knowledge entry
            entry = KnowledgeEntry(
                id=entry_id,
                content=params["content"],
                category=params["category"],
                metadata={
                    "topic": params.get("topic", "custom"),
                    "difficulty": params.get("difficulty", "intermediate"),
                    "domain": "project_custom",
                },
            )

            # Add to project knowledge
            success = orchestrator.vector_db.add_project_knowledge(entry, project.project_id)

            if success:
                self.print_success(f"Knowledge added to project: {entry_id}")
                return self.success(
                    f"Added knowledge entry to {project.name}", data={"entry_id": entry_id}
                )
            else:
                return self.error("Failed to add knowledge entry")

        except Exception as e:
            return self.error(f"Failed to add knowledge: {str(e)}")

    def _parse_args(self, args: List[str]) -> Dict[str, str]:
        """Parse named arguments from args list"""
        params = {}
        for arg in args:
            if "=" in arg and arg.startswith("--"):
                key, value = arg[2:].split("=", 1)
                params[key] = value
        return params


class KnowledgeListCommand(BaseCommand):
    """List knowledge entries for current project"""

    def __init__(self):
        super().__init__(
            name="knowledge list",
            description="List knowledge entries (project or global)",
            usage="knowledge list [--project] [--limit=10]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge list command"""
        try:
            orchestrator = context.get("orchestrator")
            project = context.get("project")

            # Parse options
            show_project = "--project" in args
            limit = self._get_limit(args)

            if show_project and not project:
                return self.error(
                    "No project loaded. Use '--project' with active project or omit for global knowledge"
                )

            self.print_header(f"Knowledge Entries {'(Project)' if show_project else '(Global)'}")

            if show_project:
                # List project knowledge
                entries = orchestrator.vector_db.get_project_knowledge(project.project_id)
                print(f"Project: {Fore.CYAN}{project.name}{Style.RESET_ALL}")
            else:
                # Search for global knowledge - return all with no project_id
                entries = []
                # For now, we'll search with an empty query to get all (approximate)
                entries = orchestrator.vector_db.search_similar("", top_k=limit, project_id=None)

            if not entries:
                print(f"{Fore.YELLOW}No entries found{Style.RESET_ALL}")
                return self.success()

            # Display entries
            count = 0
            for entry in entries[:limit]:
                count += 1
                entry_id = entry.get("id", "unknown")
                content = entry.get("content", "")[:80]
                meta = entry.get("metadata", {})
                category = meta.get("category", "unknown")
                difficulty = meta.get("difficulty", "unknown")

                print(f"\n{count}. {Fore.CYAN}{entry_id}{Style.RESET_ALL}")
                print(f"   Category: {category} | Difficulty: {difficulty}")
                print(f"   Content: {content}...")

            print(f"\n{Fore.GREEN}Total: {count} entries{Style.RESET_ALL}")
            return self.success()

        except Exception as e:
            return self.error(f"Failed to list knowledge: {str(e)}")

    def _get_limit(self, args: List[str]) -> int:
        """Extract limit from args"""
        for arg in args:
            if arg.startswith("--limit="):
                try:
                    return int(arg.split("=")[1])
                except (ValueError, IndexError):
                    pass
        return 10


class KnowledgeSearchCommand(BaseCommand):
    """Search knowledge entries"""

    def __init__(self):
        super().__init__(
            name="knowledge search",
            description="Search knowledge across global and project knowledge",
            usage="knowledge search <query> [--project] [--top=5]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge search command"""
        if not args or not args[0]:
            return self.error("Provide a search query")

        try:
            orchestrator = context.get("orchestrator")
            project = context.get("project")

            query = args[0]
            search_project = "--project" in args
            top_k = self._get_top_k(args)

            project_id = project.project_id if (search_project and project) else None

            results = orchestrator.vector_db.search_similar(
                query, top_k=top_k, project_id=project_id
            )

            self.print_header(f"Knowledge Search Results: '{query}'")
            if project_id:
                print(f"Project: {Fore.CYAN}{project.name}{Style.RESET_ALL}")

            if not results:
                print(f"{Fore.YELLOW}No matching knowledge found{Style.RESET_ALL}")
                return self.success()

            # Display results
            for idx, result in enumerate(results, 1):
                content = result.get("content", "")[:100]
                meta = result.get("metadata", {})
                category = meta.get("category", "unknown")
                score = result.get("score", 0)

                print(f"\n{idx}. {Fore.CYAN}{category}{Style.RESET_ALL} (relevance: {score:.2f})")
                print(f"   {content}...")

            print(f"\n{Fore.GREEN}Found {len(results)} relevant entries{Style.RESET_ALL}")
            return self.success()

        except Exception as e:
            return self.error(f"Search failed: {str(e)}")

    def _get_top_k(self, args: List[str]) -> int:
        """Extract top_k from args"""
        for arg in args:
            if arg.startswith("--top="):
                try:
                    return int(arg.split("=")[1])
                except (ValueError, IndexError):
                    pass
        return 5


class KnowledgeExportCommand(BaseCommand):
    """Export project knowledge to JSON file"""

    def __init__(self):
        super().__init__(
            name="knowledge export",
            description="Export project knowledge to a JSON file",
            usage="knowledge export <filename.json>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge export command"""
        if not self.require_project(context):
            return self.error("No project loaded. Load a project first")

        if not args or not args[0]:
            return self.error("Provide a filename to export to")

        try:
            orchestrator = context.get("orchestrator")
            project = context.get("project")
            filename = args[0]

            # Export knowledge
            exported = orchestrator.vector_db.export_project_knowledge(project.project_id)

            # Write to file
            filepath = Path(filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(exported, f, indent=2, ensure_ascii=False)

            self.print_success(f"Exported {len(exported)} entries to {filename}")
            return self.success(
                f"Knowledge exported to {filename}",
                data={"entry_count": len(exported), "filename": str(filepath.absolute())},
            )

        except Exception as e:
            return self.error(f"Export failed: {str(e)}")


class KnowledgeImportCommand(BaseCommand):
    """Import knowledge from JSON file to project"""

    def __init__(self):
        super().__init__(
            name="knowledge import",
            description="Import knowledge entries from a JSON file to current project",
            usage="knowledge import <filename.json>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge import command"""
        if not self.require_project(context):
            return self.error("No project loaded. Load a project first")

        if not args or not args[0]:
            return self.error("Provide a filename to import from")

        try:
            orchestrator = context.get("orchestrator")
            project = context.get("project")
            filename = args[0]

            # Read file
            filepath = Path(filename)
            if not filepath.exists():
                return self.error(f"File not found: {filename}")

            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            # Import entries
            if isinstance(data, list):
                entries = data
            else:
                entries = data.get("entries", []) or data.get("default_knowledge", [])

            if not entries:
                return self.error("No entries found in file")

            count = orchestrator.vector_db.import_project_knowledge(project.project_id, entries)

            self.print_success(f"Imported {count}/{len(entries)} entries to {project.name}")
            return self.success(
                f"Imported {count} knowledge entries",
                data={"imported": count, "total": len(entries)},
            )

        except json.JSONDecodeError:
            return self.error("Invalid JSON file")
        except Exception as e:
            return self.error(f"Import failed: {str(e)}")


class KnowledgeRemoveCommand(BaseCommand):
    """Remove a knowledge entry from project"""

    def __init__(self):
        super().__init__(
            name="knowledge remove",
            description="Remove a knowledge entry from current project",
            usage="knowledge remove <entry_id>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge remove command"""
        if not self.require_project(context):
            return self.error("No project loaded. Load a project first")

        if not args or not args[0]:
            return self.error("Provide an entry ID to remove")

        try:
            orchestrator = context.get("orchestrator")
            entry_id = args[0]

            # Delete entry
            orchestrator.vector_db.delete_entry(entry_id)

            self.print_success(f"Removed knowledge entry: {entry_id}")
            return self.success(f"Knowledge entry '{entry_id}' removed")

        except Exception as e:
            return self.error(f"Failed to remove entry: {str(e)}")


class RememberCommand(BaseCommand):
    """Quick shortcut to add knowledge to project"""

    def __init__(self):
        super().__init__(
            name="remember",
            description="Quick way to remember something for this project",
            usage="remember <text to remember>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute remember command"""
        if not self.require_project(context):
            return self.error("No project loaded. Load a project first")

        if not args or not " ".join(args).strip():
            return self.error("Tell me what to remember")

        try:
            orchestrator = context.get("orchestrator")
            project = context.get("project")
            content = " ".join(args)

            # Generate ID (non-security use)
            import hashlib

            # Use MD5 for non-security purposes (content hashing for ID generation)
            try:
                entry_id = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:12]
            except TypeError:
                # Python 3.8 doesn't support usedforsecurity parameter
                entry_id = hashlib.md5(content.encode()).hexdigest()[:12]  # nosec

            # Create entry
            entry = KnowledgeEntry(
                id=f"remembered_{entry_id}",
                content=content,
                category="remembered",
                metadata={
                    "topic": "project_note",
                    "difficulty": "intermediate",
                    "domain": "remembered",
                },
            )

            # Add to project
            success = orchestrator.vector_db.add_project_knowledge(entry, project.project_id)

            if success:
                self.print_success(f"Remembered: {content[:50]}...")
                return self.success(f"Remembered for {project.name}")
            else:
                return self.error("Failed to remember")

        except Exception as e:
            return self.error(f"Remember failed: {str(e)}")
