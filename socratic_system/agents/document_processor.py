"""
Document processing for importing files into projects
Extracts content from PDFs, text files, and code files, then stores in vector database
"""

import os
import re
from typing import Any, Dict, List

from socratic_system.parsers import CodeParser
from socratic_system.utils.logger import get_logger

from .base import Agent


class DocumentProcessorAgent(Agent):
    """Handles document import and processing - extracts content and stores in vector database"""

    def __init__(self, orchestrator):
        super().__init__("DocumentProcessor", orchestrator)
        self.logger = get_logger("document_processor")

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process document import requests"""
        action = request.get("action")

        if action == "import_file":
            return self._import_file(request)
        elif action == "import_directory":
            return self._import_directory(request)
        elif action == "list_documents":
            return self._list_documents(request)

        return {"status": "error", "message": "Unknown action"}

    def _import_file(self, request: Dict) -> Dict:
        """Import a single file - extract content and store in vector database"""
        file_path = request.get("file_path")
        project_id = request.get("project_id")

        if not file_path:
            return {"status": "error", "message": "File path required"}

        try:
            # Get file name for logging
            file_name = os.path.basename(file_path)
            self.logger.info(f"Processing file: {file_name}")

            # Read file content
            content = self._read_file(file_path)
            if not content:
                return {"status": "error", "message": f"Could not extract content from {file_name}"}

            # Count words and lines
            word_count = len(content.split())
            line_count = len(content.split("\n"))
            self.logger.debug(f"Extracted {word_count} words, {line_count} lines")

            # Check if file is code and parse structure
            file_ext = os.path.splitext(file_path)[1].lower()
            is_code = file_ext in CodeParser.SUPPORTED_LANGUAGES
            code_structure = None

            if is_code:
                self.logger.debug(f"Detected code file: {file_name}, parsing structure...")
                code_parser = CodeParser()
                code_structure = code_parser.parse_file(file_path, content)

                if code_structure and not code_structure.get("error"):
                    # Store code structure as separate searchable entry
                    self._store_code_structure(file_name, code_structure, project_id)

                    # Prepend structure summary to content for better context
                    structure_prefix = f"[Code Structure: {code_structure['structure_summary']}]\n\n"
                    content = structure_prefix + content
                    self.logger.info(f"Code structure parsed and stored: {code_structure['structure_summary']}")

            # Chunk content into logical pieces
            chunks = self._chunk_content(content, chunk_size=500, overlap=50)
            self.logger.info(f"Created {len(chunks)} chunks from {file_name}")

            # Store chunks in vector database
            entries_added = 0
            if self.orchestrator and self.orchestrator.vector_db:
                for i, chunk in enumerate(chunks):
                    try:
                        # Add to vector database with metadata
                        metadata = {
                            "source": file_name,
                            "chunk": i + 1,
                            "total_chunks": len(chunks),
                            "project_id": project_id,
                        }

                        # Add type metadata for code files
                        if is_code:
                            metadata["type"] = "code"
                            metadata["language"] = code_structure.get("language", "unknown") if code_structure else "unknown"

                        self.orchestrator.vector_db.add_text(chunk, metadata=metadata)
                        entries_added += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to add chunk {i+1}: {e}")

            self.logger.info(f"Stored {entries_added} chunks to vector database from {file_name}")

            return {
                "status": "success",
                "file_name": file_name,
                "file_path": file_path,
                "project_id": project_id,
                "words_extracted": word_count,
                "chunks_created": len(chunks),
                "entries_added": entries_added,
                "is_code": is_code,
                "code_structure": code_structure,
                "imported": True,
            }

        except Exception as e:
            self.logger.error(f"Error importing file {file_path}: {e}", e)
            return {"status": "error", "message": f"Failed to import file: {str(e)}"}

    def _import_directory(self, request: Dict) -> Dict:
        """Import all files from a directory"""
        directory_path = request.get("directory_path")
        project_id = request.get("project_id")
        recursive = request.get("recursive", True)

        if not os.path.isdir(directory_path):
            return {"status": "error", "message": f"Directory not found: {directory_path}"}

        self.logger.info(f"Processing directory: {directory_path} (recursive={recursive})")

        # Find all text and code files
        supported_extensions = {".txt", ".md", ".py", ".js", ".java", ".cpp", ".pdf", ".code"}
        files_to_process = []

        if recursive:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    if any(file.endswith(ext) for ext in supported_extensions):
                        files_to_process.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory_path):
                file_path = os.path.join(directory_path, file)
                if os.path.isfile(file_path) and any(
                    file.endswith(ext) for ext in supported_extensions
                ):
                    files_to_process.append(file_path)

        self.logger.info(f"Found {len(files_to_process)} files to process")

        # Process each file
        total_words = 0
        total_chunks = 0
        total_entries = 0
        successful = 0
        failed = 0

        for file_path in files_to_process:
            result = self._import_file({"file_path": file_path, "project_id": project_id})

            if result["status"] == "success":
                total_words += result.get("words_extracted", 0)
                total_chunks += result.get("chunks_created", 0)
                total_entries += result.get("entries_added", 0)
                successful += 1
            else:
                failed += 1

        self.logger.info(f"Directory import complete: {successful} successful, {failed} failed")

        return {
            "status": "success",
            "directory": directory_path,
            "project_id": project_id,
            "recursive": recursive,
            "files_processed": successful,
            "files_failed": failed,
            "total_words_extracted": total_words,
            "total_chunks_created": total_chunks,
            "total_entries_stored": total_entries,
            "imported": True,
        }

    def _list_documents(self, request: Dict) -> Dict:
        """List imported documents (from metadata)"""
        project_id = request.get("project_id")

        return {
            "status": "success",
            "project_id": project_id,
            "documents": [],  # Would require metadata tracking
        }

    def _read_file(self, file_path: str) -> str:
        """Read content from various file types"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}")
                return None

            file_ext = os.path.splitext(file_path)[1].lower()
            content = ""

            # Handle text files
            if file_ext in [".txt", ".md", ".code", ".py", ".js", ".java", ".cpp"]:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()

            # Handle PDF files
            elif file_ext == ".pdf":
                try:
                    from pypdf import PdfReader

                    with open(file_path, "rb") as f:
                        pdf_reader = PdfReader(f)
                        for page in pdf_reader.pages:
                            content += page.extract_text() + "\n"
                except ImportError:
                    self.logger.warning("pypdf not installed, trying alternative PDF reading")
                    # Fallback: read as text (won't work for binary PDFs)
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

            return content.strip() if content else None

        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}", e)
            return None

    def _chunk_content(self, content: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split content into overlapping chunks for better embedding coverage

        Args:
            content: Full text content
            chunk_size: Target words per chunk
            overlap: Words to overlap between chunks

        Returns:
            List of text chunks
        """
        # Split into sentences first to avoid breaking in middle of thought
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

    def _store_code_structure(self, file_name: str, structure: Dict, project_id: str) -> bool:
        """
        Store code structure as a searchable entry in the knowledge base.

        Args:
            file_name: Name of the code file
            structure: Parsed code structure from CodeParser
            project_id: Project ID to associate with this entry

        Returns:
            True if successful, False otherwise
        """
        try:
            language = structure.get("language", "unknown")
            metrics = structure.get("metrics", {})

            # Build structure text for knowledge base
            structure_text = self._format_code_structure(file_name, structure)

            # Store in vector database with special metadata
            if self.orchestrator and self.orchestrator.vector_db:
                self.orchestrator.vector_db.add_text(
                    structure_text,
                    metadata={
                        "source": file_name,
                        "type": "code_structure",
                        "language": language,
                        "project_id": project_id,
                        "function_count": str(metrics.get("function_count", 0)),
                        "class_count": str(metrics.get("class_count", 0)),
                    }
                )
                self.logger.debug(f"Stored code structure for {file_name} in knowledge base")
                return True
            else:
                self.logger.warning("Vector database not available for storing code structure")
                return False

        except Exception as e:
            self.logger.warning(f"Failed to store code structure for {file_name}: {e}")
            return False

    def _format_code_structure(self, file_name: str, structure: Dict) -> str:
        """
        Format code structure information for knowledge base storage.

        Args:
            file_name: Name of the code file
            structure: Parsed code structure

        Returns:
            Formatted text describing the code structure
        """
        language = structure.get("language", "unknown")
        metrics = structure.get("metrics", {})
        functions = structure.get("functions", [])
        classes = structure.get("classes", [])
        imports = structure.get("imports", [])
        summary = structure.get("structure_summary", "")

        parts = [f"Code File: {file_name} ({language})"]
        parts.append(f"Structure Summary: {summary}")
        parts.append("")

        # Add metrics
        parts.append("Metrics:")
        parts.append(f"  - Lines of Code: {metrics.get('lines_of_code', 0)}")
        parts.append(f"  - Functions: {metrics.get('function_count', 0)}")
        parts.append(f"  - Classes: {metrics.get('class_count', 0)}")
        parts.append(f"  - Imports: {metrics.get('import_count', 0)}")
        parts.append("")

        # Add functions
        if functions:
            parts.append("Functions:")
            for func in functions[:10]:  # Limit to first 10
                params_str = ", ".join(func.get("params", []))
                parts.append(f"  - {func.get('name', 'unknown')}({params_str})")
            if len(functions) > 10:
                parts.append(f"  ... and {len(functions) - 10} more")
            parts.append("")

        # Add classes
        if classes:
            parts.append("Classes:")
            for cls in classes[:10]:  # Limit to first 10
                parent_info = f" extends {cls.get('parent')}" if cls.get("parent") else ""
                parts.append(f"  - {cls.get('name', 'unknown')}{parent_info}")
                methods = cls.get("methods", [])
                for method in methods[:5]:  # Limit methods per class
                    params_str = ", ".join(method.get("params", []))
                    parts.append(f"      - {method.get('name', 'unknown')}({params_str})")
                if len(methods) > 5:
                    parts.append(f"      ... and {len(methods) - 5} more methods")
            if len(classes) > 10:
                parts.append(f"  ... and {len(classes) - 10} more")
            parts.append("")

        # Add imports
        if imports:
            parts.append("Imports/Dependencies:")
            for imp in imports[:15]:  # Limit to first 15
                parts.append(f"  - {imp}")
            if len(imports) > 15:
                parts.append(f"  ... and {len(imports) - 15} more")

        return "\n".join(parts)
