"""Document and knowledge base management commands"""

import os
from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class DocsCommand(BaseCommand):
    """View documentation on a topic"""

    def __init__(self):
        super().__init__(
            name="docs",
            description="View documentation on a topic (e.g., docs projects, docs authentication)",
            usage="docs [topic]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute docs command to retrieve documentation on a topic"""
        # Get topic from args
        if not args:
            topic = input(f"{Fore.WHITE}Enter topic to learn about: ").strip()
        else:
            topic = " ".join(args)

        if not topic:
            return self.error("Please specify a topic (e.g., 'docs projects')")

        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        # Check if Claude client is available
        if not hasattr(orchestrator, "claude_client") or not orchestrator.claude_client:
            return self.error("Claude client not available")

        try:
            # Build documentation request prompt
            prompt = f"""Provide a clear, concise guide on: {topic}

Focus on:
- Key features and concepts
- How to use it
- Pro tips and best practices
- When to use it

Keep the response well-formatted and easy to read."""

            # Get documentation from Claude
            print(f"{Fore.YELLOW}Fetching documentation on '{topic}'...{Style.RESET_ALL}")
            documentation = orchestrator.claude_client.generate_response(prompt)

            if documentation:
                self.print_success(f"Documentation: {topic}")
                print(documentation)
                return self.success(
                    data={
                        "topic": topic,
                        "documentation": documentation,
                    }
                )
            else:
                return self.error(f"Could not retrieve documentation for '{topic}'")

        except Exception as e:
            return self.error(f"Error retrieving documentation: {str(e)}")


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

            # CRITICAL: Emit DOCUMENT_IMPORTED event to trigger knowledge analysis
            try:
                from socratic_system.events import EventType
                orchestrator.event_emitter.emit(
                    EventType.DOCUMENT_IMPORTED,
                    {
                        "project_id": project_id,
                        "file_name": file_name,
                        "source_type": "file",
                        "words_extracted": words,
                        "chunks_created": chunks,
                        "user_id": context.get("user").username if context.get("user") else "unknown",
                    }
                )
                print(f"{Fore.GREEN}Knowledge analysis triggered{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Warning: Could not trigger knowledge analysis: {str(e)}{Style.RESET_ALL}")

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

            # CRITICAL: Emit DOCUMENT_IMPORTED event to trigger knowledge analysis
            try:
                from socratic_system.events import EventType
                orchestrator.event_emitter.emit(
                    EventType.DOCUMENT_IMPORTED,
                    {
                        "project_id": project_id,
                        "file_name": f"directory_import_{successful}_files",
                        "source_type": "directory",
                        "words_extracted": total_words,
                        "chunks_created": total_chunks,
                        "user_id": context.get("user").username if context.get("user") else "unknown",
                    }
                )
                print(f"{Fore.GREEN}Knowledge analysis triggered{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Warning: Could not trigger knowledge analysis: {str(e)}{Style.RESET_ALL}")

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
        # Get title from arguments or user input
        title = self._get_title_from_input(args)

        # Get text content from user
        text_content = self._get_text_content_from_input()

        if not text_content.strip():
            return self.error("No content provided")

        # Validate context
        validation_error = self._validate_doc_paste_context(context)
        if validation_error:
            return validation_error

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        # Determine project association
        project_id = self._get_project_association(project)

        # Process text content
        result = self._process_text_import(orchestrator, text_content, title, project_id)

        # Handle result
        if result["status"] == "success":
            return self._handle_import_success(result, title, project_id, context, orchestrator)
        else:
            return self.error(result.get("message", "Failed to import text"))

    def _get_title_from_input(self, args: List[str]) -> str:
        """Get document title from args or user input"""
        if args:
            return " ".join(args)

        title = "pasted_text"
        title_input = input(f"{Fore.CYAN}Enter a title for this content (default: pasted_text): ").strip()
        if title_input:
            title = title_input
        return title

    def _get_text_content_from_input(self) -> str:
        """Get multi-line text content from user input"""
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
            pass

        return "\n".join(lines)

    def _validate_doc_paste_context(self, context: Dict[str, Any]) -> Dict:
        """Validate required context for docs paste command"""
        if not context.get("orchestrator"):
            return self.error("Orchestrator not available")
        return None

    def _get_project_association(self, project) -> str:
        """Get project ID if user wants to link to current project"""
        project_id = None
        if project:
            link_choice = input(
                f"{Fore.CYAN}Link to current project '{project.name}'? (y/n): "
            ).lower()
            if link_choice == "y":
                project_id = project.project_id
        return project_id

    def _process_text_import(self, orchestrator, text_content: str, title: str, project_id: str) -> Dict:
        """Process text import request"""
        print(f"{Fore.YELLOW}Processing text...{Style.RESET_ALL}")

        return orchestrator.process_request(
            "document_agent",
            {
                "action": "import_text",
                "text_content": text_content,
                "title": title,
                "project_id": project_id,
            },
        )

    def _handle_import_success(
        self, result: Dict, title: str, project_id: str, context: Dict, orchestrator
    ) -> Dict:
        """Handle successful text import"""
        words = result.get("words_extracted", 0)
        chunks = result.get("chunks_created", 0)
        entries = result.get("entries_added", 0)

        self.print_success(f"Successfully imported '{title}'")
        self._display_import_stats(words, chunks, entries)

        # Emit DOCUMENT_IMPORTED event
        self._emit_document_imported_event(orchestrator, project_id, title, words, chunks, context)

        return self.success(
            data={
                "title": title,
                "words_extracted": words,
                "chunks_created": chunks,
                "entries_added": entries,
            }
        )

    def _display_import_stats(self, words: int, chunks: int, entries: int) -> None:
        """Display import statistics"""
        print(f"{Fore.WHITE}Content extracted: {words} words")
        print(f"Chunks created: {chunks}")
        print(f"Stored in knowledge base: {entries} entries")

    def _emit_document_imported_event(
        self, orchestrator, project_id: str, title: str, words: int, chunks: int, context: Dict
    ) -> None:
        """Emit DOCUMENT_IMPORTED event to trigger knowledge analysis"""
        try:
            from socratic_system.events import EventType
            orchestrator.event_emitter.emit(
                EventType.DOCUMENT_IMPORTED,
                {
                    "project_id": project_id,
                    "file_name": title,
                    "source_type": "pasted_text",
                    "words_extracted": words,
                    "chunks_created": chunks,
                    "user_id": context.get("user").username if context.get("user") else "unknown",
                }
            )
            print(f"{Fore.GREEN}Knowledge analysis triggered{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Could not trigger knowledge analysis: {str(e)}{Style.RESET_ALL}")


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

            # CRITICAL: Emit DOCUMENT_IMPORTED event to trigger knowledge analysis
            try:
                from socratic_system.events import EventType
                orchestrator.event_emitter.emit(
                    EventType.DOCUMENT_IMPORTED,
                    {
                        "project_id": project_id,
                        "file_name": file_name,
                        "source_type": "url",
                        "url": url,
                        "words_extracted": words,
                        "chunks_created": chunks,
                        "user_id": context.get("user").username if context.get("user") else "unknown",
                    }
                )
                print(f"{Fore.GREEN}Knowledge analysis triggered{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Warning: Could not trigger knowledge analysis: {str(e)}{Style.RESET_ALL}")

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
