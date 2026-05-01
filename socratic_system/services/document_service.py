"""
DocumentService - Business logic for document processing and import.

Extracted from DocumentProcessorAgent.
Uses DocumentRepository for all data access (not direct database calls).
Focuses on document import, content extraction, and chunking.
"""

import logging
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from socratic_system.parsers import CodeParser
from socratic_system.repositories.document_repository import DocumentRepository

from .base_service import BaseService

if TYPE_CHECKING:
    from socratic_system.config import SocratesConfig


class DocumentService(BaseService):
    """
    Service for document processing and import.

    Receives only required dependencies via DI (no orchestrator coupling).
    Uses repository pattern for all data access.
    """

    def __init__(self, config: "SocratesConfig", database):
        """
        Initialize document service.

        Args:
            config: SocratesConfig instance
            database: ProjectDatabase instance for repository initialization
        """
        super().__init__(config)
        self.repository = DocumentRepository(database)

        # Chunk configuration
        self.chunk_size = 500
        self.chunk_overlap = 50

        # Supported file extensions
        self.supported_extensions = {
            ".txt",
            ".md",
            ".py",
            ".js",
            ".java",
            ".cpp",
            ".pdf",
            ".code",
        }

        self.logger.info(
            f"DocumentService initialized with chunk_size={self.chunk_size}, overlap={self.chunk_overlap}"
        )

    def import_file(
        self,
        project_id: str,
        file_path: str,
        original_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Import a single file and extract its content.

        Args:
            project_id: Project ID
            file_path: Path to file to import
            original_filename: Original file name (optional override)

        Returns:
            Dict with import results
        """
        self._log_operation(
            "import_file",
            {"project_id": project_id, "file_path": file_path},
        )

        try:
            if not os.path.exists(file_path):
                return {
                    "status": "error",
                    "message": f"File not found: {file_path}",
                }

            file_name = original_filename or os.path.basename(file_path)
            self.logger.info(f"Processing file: {file_name}")

            # Read file content
            content = self._read_file(file_path)
            if not content:
                return {
                    "status": "error",
                    "message": f"Could not extract content from {file_name}",
                }

            # Count words and lines
            word_count = len(content.split())
            line_count = len(content.split("\n"))
            self.logger.debug(
                f"Extracted {word_count} words, {line_count} lines"
            )

            # Check if file is code and parse structure
            file_ext = os.path.splitext(file_path)[1].lower()
            is_code = file_ext in CodeParser.SUPPORTED_LANGUAGES
            code_structure = None

            if is_code:
                self.logger.debug(
                    f"Detected code file: {file_name}, parsing structure..."
                )
                try:
                    code_parser = CodeParser()
                    code_structure = code_parser.parse_file(file_path, content)

                    if code_structure and not code_structure.get("error"):
                        structure_prefix = (
                            f"[Code Structure: {code_structure['structure_summary']}]\n\n"
                        )
                        content = structure_prefix + content
                        self.logger.info(
                            f"Code structure parsed: {code_structure['structure_summary']}"
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to parse code structure: {e}")

            # Chunk content into logical pieces
            chunks = self._chunk_content(
                content, chunk_size=self.chunk_size, overlap=self.chunk_overlap
            )
            self.logger.info(f"Created {len(chunks)} chunks from {file_name}")

            # Store document metadata in repository
            self.repository.add_document(
                project_id,
                file_name,
                file_path,
                "file",
                word_count,
                len(chunks),
                len(chunks),  # entries_stored = chunks (assumed to be stored in vector DB)
                metadata={
                    "is_code": is_code,
                    "language": (
                        code_structure.get("language", "unknown")
                        if code_structure
                        else None
                    ),
                    "file_ext": file_ext,
                },
            )

            self.logger.info(
                f"Imported {file_name}: {word_count} words, {len(chunks)} chunks"
            )

            return {
                "status": "success",
                "file_name": file_name,
                "file_path": file_path,
                "project_id": project_id,
                "words_extracted": word_count,
                "chunks_created": len(chunks),
                "is_code": is_code,
                "code_structure": code_structure,
                "imported": True,
            }

        except Exception as e:
            self.logger.error(f"Error importing file {file_path}: {e}")
            return {"status": "error", "message": f"Failed to import file: {str(e)}"}

    def import_directory(
        self,
        project_id: str,
        directory_path: str,
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """
        Import all files from a directory.

        Args:
            project_id: Project ID
            directory_path: Path to directory
            recursive: Whether to recurse into subdirectories

        Returns:
            Dict with import results
        """
        self._log_operation(
            "import_directory",
            {
                "project_id": project_id,
                "directory_path": directory_path,
                "recursive": recursive,
            },
        )

        try:
            if not os.path.isdir(directory_path):
                return {
                    "status": "error",
                    "message": f"Directory not found: {directory_path}",
                }

            self.logger.info(
                f"Processing directory: {directory_path} (recursive={recursive})"
            )

            # Find all supported files
            files_to_process = []

            if recursive:
                for root, _, files in os.walk(directory_path):
                    for file in files:
                        if any(
                            file.endswith(ext)
                            for ext in self.supported_extensions
                        ):
                            files_to_process.append(os.path.join(root, file))
            else:
                for file in os.listdir(directory_path):
                    file_path = os.path.join(directory_path, file)
                    if os.path.isfile(file_path) and any(
                        file.endswith(ext)
                        for ext in self.supported_extensions
                    ):
                        files_to_process.append(file_path)

            self.logger.info(f"Found {len(files_to_process)} files to process")

            # Process each file
            total_words = 0
            total_chunks = 0
            successful = 0
            failed = 0

            for file_path in files_to_process:
                result = self.import_file(project_id, file_path)

                if result["status"] == "success":
                    total_words += result.get("words_extracted", 0)
                    total_chunks += result.get("chunks_created", 0)
                    successful += 1
                else:
                    failed += 1
                    self.logger.warning(
                        f"Failed to import {file_path}: {result.get('message')}"
                    )

            self.logger.info(
                f"Directory import complete: {successful} successful, {failed} failed"
            )

            return {
                "status": "success",
                "directory": directory_path,
                "project_id": project_id,
                "recursive": recursive,
                "files_processed": successful,
                "files_failed": failed,
                "total_words_extracted": total_words,
                "total_chunks_created": total_chunks,
                "imported": True,
            }

        except Exception as e:
            self.logger.error(f"Error importing directory {directory_path}: {e}")
            return {
                "status": "error",
                "message": f"Failed to import directory: {str(e)}",
            }

    def import_text(
        self,
        project_id: str,
        text_content: str,
        title: str = "pasted_text",
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Import pasted or inline text.

        Args:
            project_id: Project ID
            text_content: Text content to import
            title: Title for the text (used as filename)
            document_id: Optional document ID (overrides title)

        Returns:
            Dict with import results
        """
        self._log_operation(
            "import_text",
            {"project_id": project_id, "text_length": len(text_content)},
        )

        try:
            if not text_content:
                return {
                    "status": "error",
                    "message": "Text content required",
                }

            # Use document_id as source if provided, otherwise create from title
            file_name = document_id or f"{title}.txt"
            self.logger.info(f"Processing pasted text: {file_name}")

            # Count words
            word_count = len(text_content.split())
            self.logger.debug(f"Extracted {word_count} words from pasted text")

            # Chunk content
            chunks = self._chunk_content(
                text_content,
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap,
            )
            self.logger.info(f"Created {len(chunks)} chunks from pasted text")

            # Store document metadata in repository
            self.repository.add_document(
                project_id,
                file_name,
                file_name,
                "text",
                word_count,
                len(chunks),
                len(chunks),
                metadata={"title": title},
            )

            self.logger.info(
                f"Imported text {file_name}: {word_count} words, {len(chunks)} chunks"
            )

            return {
                "status": "success",
                "file_name": file_name,
                "project_id": project_id,
                "words_extracted": word_count,
                "chunks_created": len(chunks),
                "content_type": "text",
                "imported": True,
            }

        except Exception as e:
            self.logger.error(f"Error importing text: {e}")
            return {"status": "error", "message": f"Failed to import text: {str(e)}"}

    def get_project_documents(self, project_id: str) -> Dict[str, Any]:
        """
        Get all documents for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict with document list and statistics
        """
        self._log_operation(
            "get_project_documents", {"project_id": project_id}
        )

        try:
            documents = self.repository.get_project_documents(project_id)
            stats = self.repository.get_document_statistics(project_id)

            self.logger.debug(
                f"Retrieved {len(documents)} documents for {project_id}"
            )

            return {
                "status": "success",
                "documents": documents,
                "total": len(documents),
                "statistics": stats,
            }

        except Exception as e:
            self.logger.error(f"Error getting documents: {e}")
            return {"status": "error", "message": str(e)}

    def delete_document(
        self, project_id: str, file_name: str
    ) -> Dict[str, Any]:
        """
        Delete a document record.

        Args:
            project_id: Project ID
            file_name: File name to delete

        Returns:
            Dict with deletion status
        """
        self._log_operation(
            "delete_document",
            {"project_id": project_id, "file_name": file_name},
        )

        try:
            result = self.repository.delete_document(project_id, file_name)

            if result:
                self.logger.info(f"Deleted document {file_name}")
                return {
                    "status": "success",
                    "message": f"Document {file_name} deleted",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Document {file_name} not found",
                }

        except Exception as e:
            self.logger.error(f"Error deleting document: {e}")
            return {"status": "error", "message": str(e)}

    def _read_file(self, file_path: str) -> Optional[str]:
        """
        Read file content based on file type.

        Args:
            file_path: Path to file

        Returns:
            File content as string, or None if unable to read
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to read file {file_path}: {e}")
            return None

    def _chunk_content(
        self, content: str, chunk_size: int = 500, overlap: int = 50
    ) -> List[str]:
        """
        Split content into overlapping chunks.

        Args:
            content: Text content to chunk
            chunk_size: Target chunk size in words
            overlap: Number of words to overlap between chunks

        Returns:
            List of content chunks
        """
        words = content.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks
