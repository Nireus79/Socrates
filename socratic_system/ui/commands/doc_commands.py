"""Document and knowledge base management commands"""

import os
from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class DocImportCommand(BaseCommand):
    """Import a single document into the knowledge base"""

    def __init__(self):
        super().__init__(
            name="docs import",
            description="Import a single file into the knowledge base",
            usage="docs import <path>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute docs import command"""
        if not self.validate_args(args, min_count=1):
            file_path = input(f"{Fore.WHITE}Enter file path: ").strip()
        else:
            file_path = " ".join(args)  # Allow spaces in file path

        if not file_path:
            return self.error("File path cannot be empty")

        # Normalize path to handle Windows paths correctly
        file_path = os.path.normpath(file_path)

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Ask if they want to link to current project
        project_id = None
        if project:
            link_choice = input(
                f"{Fore.CYAN}Link to current project '{project.name}'? (y/n): "
            ).lower()
            if link_choice == "y":
                project_id = project.project_id

        print(f"{Fore.YELLOW}Processing file...{Style.RESET_ALL}")

        result = orchestrator.process_request(
            "document_agent",
            {"action": "import_file", "file_path": file_path, "project_id": project_id},
        )

        if result["status"] == "success":
            file_name = result.get("file_name", "file")
            words = result.get("words_extracted", 0)
            chunks = result.get("chunks_created", 0)
            entries = result.get("entries_added", 0)

            self.print_success(f"Successfully imported '{file_name}'")
            print(f"{Fore.WHITE}Content extracted: {words} words")
            print(f"Chunks created: {chunks}")
            print(f"Stored in knowledge base: {entries} entries")

            return self.success(
                data={
                    "file_name": file_name,
                    "words_extracted": words,
                    "chunks_created": chunks,
                    "entries_added": entries,
                }
            )
        else:
            return self.error(result.get("message", "Failed to import file"))


class DocImportDirCommand(BaseCommand):
    """Import all files from a directory into the knowledge base"""

    def __init__(self):
        super().__init__(
            name="docs import-dir",
            description="Import all files from a directory into the knowledge base",
            usage="docs import-dir <path>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute docs import-dir command"""
        if not self.validate_args(args, min_count=1):
            directory_path = input(f"{Fore.WHITE}Enter directory path: ").strip()
        else:
            directory_path = " ".join(args)  # Allow spaces in directory path

        if not directory_path:
            return self.error("Directory path cannot be empty")

        # Normalize path to handle Windows paths correctly
        directory_path = os.path.normpath(directory_path)

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Ask if they want to include subdirectories
        recursive_choice = input(f"{Fore.CYAN}Include subdirectories? (y/n): ").lower()
        recursive = recursive_choice == "y"

        # Ask if they want to link to current project
        project_id = None
        if project:
            link_choice = input(
                f"{Fore.CYAN}Link to current project '{project.name}'? (y/n): "
            ).lower()
            if link_choice == "y":
                project_id = project.project_id

        print(f"{Fore.YELLOW}Processing directory...{Style.RESET_ALL}")

        result = orchestrator.process_request(
            "document_agent",
            {
                "action": "import_directory",
                "directory_path": directory_path,
                "project_id": project_id,
                "recursive": recursive,
            },
        )

        if result["status"] == "success":
            successful = result.get("files_processed", 0)
            failed = result.get("files_failed", 0)
            total_words = result.get("total_words_extracted", 0)
            total_chunks = result.get("total_chunks_created", 0)
            total_entries = result.get("total_entries_stored", 0)

            self.print_success("Directory import complete!")
            print(f"{Fore.WHITE}Files processed:     {successful}")
            if failed > 0:
                print(f"Files failed:        {failed}")
            print(f"Total content:       {total_words} words")
            print(f"Chunks created:      {total_chunks}")
            print(f"Stored in knowledge: {total_entries} entries")

            return self.success(
                data={
                    "files_processed": successful,
                    "files_failed": failed,
                    "total_words_extracted": total_words,
                    "total_chunks_created": total_chunks,
                    "total_entries_stored": total_entries,
                }
            )
        else:
            return self.error(result.get("message", "Failed to import directory"))


class DocPasteCommand(BaseCommand):
    """Import pasted or inline text into the knowledge base"""

    def __init__(self):
        super().__init__(
            name="docs paste",
            description="Import pasted or inline text into the knowledge base",
            usage="docs paste [title]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute docs paste command"""
        # Get optional title from args
        title = " ".join(args) if args else "pasted_text"

        # Get custom title if not provided
        if not args:
            title_input = input(f"{Fore.CYAN}Enter a title for this content (default: pasted_text): ").strip()
            if title_input:
                title = title_input

        print(f"{Fore.CYAN}Enter your text content (type EOF on a new line when done):{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}>>> {Style.RESET_ALL}", end="")

        lines = []
        try:
            while True:
                line = input()
                if line.strip().upper() == "EOF":
                    break
                lines.append(line)
        except EOFError:
            # Handle EOF from standard input
            pass

        text_content = "\n".join(lines)

        if not text_content.strip():
            return self.error("No content provided")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Ask if they want to link to current project
        project_id = None
        if project:
            link_choice = input(
                f"{Fore.CYAN}Link to current project '{project.name}'? (y/n): "
            ).lower()
            if link_choice == "y":
                project_id = project.project_id

        print(f"{Fore.YELLOW}Processing text...{Style.RESET_ALL}")

        result = orchestrator.process_request(
            "document_agent",
            {
                "action": "import_text",
                "text_content": text_content,
                "title": title,
                "project_id": project_id,
            },
        )

        if result["status"] == "success":
            words = result.get("words_extracted", 0)
            chunks = result.get("chunks_created", 0)
            entries = result.get("entries_added", 0)

            self.print_success(f"Successfully imported '{title}'")
            print(f"{Fore.WHITE}Content extracted: {words} words")
            print(f"Chunks created: {chunks}")
            print(f"Stored in knowledge base: {entries} entries")

            return self.success(
                data={
                    "title": title,
                    "words_extracted": words,
                    "chunks_created": chunks,
                    "entries_added": entries,
                }
            )
        else:
            return self.error(result.get("message", "Failed to import text"))


class DocImportUrlCommand(BaseCommand):
    """Import content from a web page URL into the knowledge base"""

    def __init__(self):
        super().__init__(
            name="docs import-url",
            description="Import content from a web page URL into the knowledge base",
            usage="docs import-url <url>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute docs import-url command"""
        if not self.validate_args(args, min_count=1):
            url = input(f"{Fore.WHITE}Enter URL: ").strip()
        else:
            url = " ".join(args)  # Allow spaces in URL

        if not url:
            return self.error("URL cannot be empty")

        # Validate URL format
        if not url.startswith(("http://", "https://")):
            return self.error("URL must start with http:// or https://")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Ask if they want to link to current project
        project_id = None
        if project:
            link_choice = input(
                f"{Fore.CYAN}Link to current project '{project.name}'? (y/n): "
            ).lower()
            if link_choice == "y":
                project_id = project.project_id

        print(f"{Fore.YELLOW}Fetching URL content...{Style.RESET_ALL}")

        result = orchestrator.process_request(
            "document_agent",
            {
                "action": "import_url",
                "url": url,
                "project_id": project_id,
            },
        )

        if result["status"] == "success":
            file_name = result.get("file_name", "webpage")
            words = result.get("words_extracted", 0)
            chunks = result.get("chunks_created", 0)
            entries = result.get("entries_added", 0)

            self.print_success(f"Successfully imported '{file_name}'")
            print(f"{Fore.WHITE}Content extracted: {words} words")
            print(f"Chunks created: {chunks}")
            print(f"Stored in knowledge base: {entries} entries")

            return self.success(
                data={
                    "file_name": file_name,
                    "url": url,
                    "words_extracted": words,
                    "chunks_created": chunks,
                    "entries_added": entries,
                }
            )
        else:
            return self.error(result.get("message", "Failed to import URL"))


class DocListCommand(BaseCommand):
    """List imported documents"""

    def __init__(self):
        super().__init__(
            name="docs list",
            description="List all imported documents",
            usage="docs list [project-id]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute docs list command"""
        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Get project ID from args or current project
        if args:
            project_id = args[0]
        elif project:
            project_id = project.project_id
        else:
            return self.error("No project specified and no project loaded")

        result = orchestrator.process_request(
            "document_agent", {"action": "list_documents", "project_id": project_id}
        )

        if result["status"] == "success":
            documents = result.get("documents", [])

            if not documents:
                self.print_info("No documents imported for this project")
                return self.success()

            print(f"\n{Fore.CYAN}Imported Documents:{Style.RESET_ALL}")
            for i, doc in enumerate(documents, 1):
                file_name = doc.get("file_name", "unknown")
                entries = doc.get("entries_count", 0)
                imported_at = doc.get("imported_at", "unknown")

                print(
                    f"{i}. {Fore.WHITE}{file_name:40}{Style.RESET_ALL} ({entries} entries) - {imported_at}"
                )

            print()
            return self.success(data={"documents": documents})
        else:
            return self.error(result.get("message", "Failed to list documents"))
