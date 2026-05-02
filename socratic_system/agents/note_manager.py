"""Note manager agent for handling project notes

Phase 2B Migration: Async-first implementation with agent bus support
"""

import asyncio
from typing import TYPE_CHECKING, Any, Dict

from socratic_system.agents.base import Agent
from socratic_system.models import ProjectNote

if TYPE_CHECKING:
    from socratic_system.orchestration.orchestrator import AgentOrchestrator


class NoteManagerAgent(Agent):
    """Agent for managing project notes

    Phase 2B Migration: Async-first CRUD implementation
    - Supports both sync (process) and async (process_async) interfaces
    - Registers with agent bus for discovery
    - All blocking operations run in thread pool (non-blocking)
    """

    def __init__(self, orchestrator: "AgentOrchestrator"):
        """Initialize note manager agent"""
        super().__init__("note_manager", orchestrator, auto_register=True)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process note-related requests (sync wrapper for backward compatibility).

        Phase 2B: Delegates to sync helper methods

        Supported actions:
        - add_note: Add a new note to a project
        - list_notes: List notes for a project
        - search_notes: Search notes by content
        - delete_note: Delete a note by ID
        """
        action = request.get("action")

        if action == "add_note":
            return self._add_note_sync(request)
        elif action == "list_notes":
            return self._list_notes_sync(request)
        elif action == "search_notes":
            return self._search_notes_sync(request)
        elif action == "delete_note":
            return self._delete_note_sync(request)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    async def process_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process note-related requests asynchronously (Phase 2B).

        Primary implementation - true async processing with thread pool
        """
        action = request.get("action")

        if action == "add_note":
            return await self._add_note_async(request)
        elif action == "list_notes":
            return await self._list_notes_async(request)
        elif action == "search_notes":
            return await self._search_notes_async(request)
        elif action == "delete_note":
            return await self._delete_note_async(request)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def get_capabilities(self) -> list:
        """Declare agent capabilities for bus discovery (Phase 2B)"""
        return ["note_management", "note_search", "note_persistence"]

    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata for registration (Phase 2B)"""
        return {
            "version": "2.0",
            "description": "Project note management and organization",
            "capabilities_count": 3,
        }

    def _add_note_sync(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new note to a project"""
        try:
            project_id = request.get("project_id")
            note_type = request.get("note_type")  # design, bug, idea, task, general
            title = request.get("title")
            content = request.get("content")
            created_by = request.get("created_by")
            tags = request.get("tags", [])

            if not all([project_id, note_type, title, content, created_by]):
                return {"status": "error", "message": "Missing required fields"}

            # Validate note type
            valid_types = ["design", "bug", "idea", "task", "general"]
            if note_type not in valid_types:
                return {
                    "status": "error",
                    "message": f'Invalid note type. Must be one of: {", ".join(valid_types)}',
                }

            # Create note
            note = ProjectNote.create(
                project_id=project_id,
                note_type=note_type,
                title=title,
                content=content,
                created_by=created_by,
                tags=tags,
            )

            # Save to database
            if self.orchestrator.database.save_note(note):
                self.log(f'Note "{title}" added to project {project_id}')

                # Vectorize note content for knowledge base
                vectorization_result = {
                    "status": "pending",
                    "chunks_created": 0,
                    "message": "Note vectorization pending",
                }

                try:
                    if self.orchestrator and self.orchestrator.vector_db:
                        # Prepare note content for vectorization
                        note_content = f"[{note_type.upper()} NOTE] {title}\n\n{content}"

                        # Chunk the note content (500-word chunks with 50-word overlap)
                        chunks = self._chunk_note_content(note_content, chunk_size=500, overlap=50)

                        # Store each chunk in vector database
                        chunks_added = 0
                        for i, chunk in enumerate(chunks):
                            try:
                                # Metadata for each chunk
                                metadata = {
                                    "source": f"note_{note.note_id}",
                                    "chunk": i + 1,
                                    "total_chunks": len(chunks),
                                    "project_id": project_id,
                                    "source_type": "project_note",
                                    "note_type": note_type,
                                    "title": title,
                                    "created_by": created_by,
                                }

                                # Add chunk to vector database
                                self.orchestrator.vector_db.add_text(chunk, metadata=metadata)
                                chunks_added += 1
                            except Exception as e:
                                self.log(
                                    f"Warning: Could not add chunk {i+1} of note: {e}",
                                    level="WARNING",
                                )

                        vectorization_result["status"] = "success"
                        vectorization_result["chunks_created"] = chunks_added
                        vectorization_result["message"] = (
                            f"Note chunked and vectorized ({chunks_added} chunks)"
                        )
                        self.log(
                            f"Vectorized note {note.note_id} to knowledge base ({chunks_added} chunks)"
                        )

                        # Emit DOCUMENT_IMPORTED event for knowledge base
                        try:
                            from socratic_system.events import EventType

                            if self.orchestrator.event_emitter:
                                self.orchestrator.event_emitter.emit(
                                    EventType.DOCUMENT_IMPORTED,
                                    {
                                        "project_id": project_id,
                                        "file_name": f"{note_type}_{note.note_id}",
                                        "source_type": "project_note",
                                        "words_extracted": len(content.split()),
                                        "chunks_created": chunks_added,
                                        "user_id": created_by,
                                    },
                                )
                                self.log(f"Emitted DOCUMENT_IMPORTED event for note {note.note_id}")
                        except Exception as e:
                            self.log(
                                f"Warning: Could not emit DOCUMENT_IMPORTED event: {e}",
                                level="WARNING",
                            )

                except Exception as e:
                    self.log(f"Warning: Could not vectorize note: {e}", level="WARNING")
                    vectorization_result["status"] = "error"
                    vectorization_result["message"] = str(e)

                return {
                    "status": "success",
                    "message": f'Note "{title}" added successfully',
                    "note": {
                        "note_id": note.note_id,
                        "title": note.title,
                        "type": note.note_type,
                        "created_at": note.created_at.isoformat(),
                    },
                    "vectorization_result": vectorization_result,
                }
            else:
                return {"status": "error", "message": "Failed to save note to database"}

        except Exception as e:
            self.log(f"Error adding note: {str(e)}", level="ERROR")
            return {"status": "error", "message": f"Error adding note: {str(e)}"}

    def _list_notes_sync(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """List notes for a project"""
        try:
            project_id = request.get("project_id")
            note_type = request.get("note_type")  # Optional filter

            if not project_id:
                return {"status": "error", "message": "project_id required"}

            # Get notes from database
            notes = self.orchestrator.database.get_project_notes(project_id, note_type)

            # Format for output
            notes_data = []
            for note in notes:
                notes_data.append(
                    {
                        "note_id": note.note_id,
                        "title": note.title,
                        "type": note.note_type,
                        "created_by": note.created_by,
                        "created_at": note.created_at.isoformat(),
                        "tags": note.tags,
                        "preview": note.content[:100] + ("..." if len(note.content) > 100 else ""),
                    }
                )

            self.log(f"Retrieved {len(notes_data)} notes for project {project_id}")
            return {"status": "success", "notes": notes_data, "count": len(notes_data)}

        except Exception as e:
            self.log(f"Error listing notes: {str(e)}", level="ERROR")
            return {"status": "error", "message": f"Error listing notes: {str(e)}"}

    def _search_notes_sync(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Search notes by content"""
        try:
            project_id = request.get("project_id")
            query = request.get("query")

            if not project_id or not query:
                return {"status": "error", "message": "project_id and query required"}

            # Search notes in database
            notes = self.orchestrator.database.search_notes(project_id, query)

            # Format for output
            notes_data = []
            for note in notes:
                notes_data.append(
                    {
                        "note_id": note.note_id,
                        "title": note.title,
                        "type": note.note_type,
                        "created_by": note.created_by,
                        "created_at": note.created_at.isoformat(),
                        "tags": note.tags,
                        "preview": note.content[:100] + ("..." if len(note.content) > 100 else ""),
                    }
                )

            self.log(f'Found {len(notes_data)} notes matching "{query}" in project {project_id}')
            return {
                "status": "success",
                "results": notes_data,
                "count": len(notes_data),
                "query": query,
            }

        except Exception as e:
            self.log(f"Error searching notes: {str(e)}", level="ERROR")
            return {"status": "error", "message": f"Error searching notes: {str(e)}"}

    def _delete_note_sync(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a note by ID"""
        try:
            note_id = request.get("note_id")

            if not note_id:
                return {"status": "error", "message": "note_id required"}

            # Delete from database
            if self.orchestrator.database.delete_note(note_id):
                self.log(f"Note {note_id} deleted")
                return {"status": "success", "message": "Note deleted successfully"}
            else:
                return {"status": "error", "message": "Failed to delete note"}

        except Exception as e:
            self.log(f"Error deleting note: {str(e)}", level="ERROR")
            return {"status": "error", "message": f"Error deleting note: {str(e)}"}

    def _chunk_note_content(self, content: str, chunk_size: int = 500, overlap: int = 50) -> list:
        """
        Split note content into overlapping chunks for better embedding coverage.

        Args:
            content: Full note text
            chunk_size: Target words per chunk
            overlap: Words to overlap between chunks

        Returns:
            List of text chunks
        """
        import re

        # Split into sentences to avoid breaking in middle of thought
        sentences = re.split(r"(?<=[.!?])\s+", content)

        chunks = []
        current_chunk = []
        current_words = 0

        for sentence in sentences:
            sentence_words = len(sentence.split())

            # If adding this sentence exceeds chunk size and we have content
            if current_words + sentence_words > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)

                # Create overlap: keep last few sentences
                overlap_words = 0
                overlap_sentences = []
                for s in reversed(current_chunk):
                    s_words = len(s.split())
                    if overlap_words + s_words <= overlap:
                        overlap_sentences.insert(0, s)
                        overlap_words += s_words
                    else:
                        break

                current_chunk = overlap_sentences
                current_words = overlap_words

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_words += sentence_words

        # Add last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks if chunks else [content]  # Return at least the full content

    # ========================================================================
    # Phase 2B Async Wrapper Methods
    # ========================================================================

    async def _add_note_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Add note asynchronously (Phase 2B)."""
        return await asyncio.to_thread(self._add_note_sync, request)

    async def _list_notes_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """List notes asynchronously (Phase 2B)."""
        return await asyncio.to_thread(self._list_notes_sync, request)

    async def _search_notes_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Search notes asynchronously (Phase 2B)."""
        return await asyncio.to_thread(self._search_notes_sync, request)

    async def _delete_note_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Delete note asynchronously (Phase 2B)."""
        return await asyncio.to_thread(self._delete_note_sync, request)
