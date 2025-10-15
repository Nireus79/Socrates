#!/usr/bin/env python3
"""
Document Processing Service
============================

Provides document text extraction and processing for uploaded files.
Supports PDF, DOCX, TXT, MD, and code files.

Features:
- Text extraction from multiple formats
- Content chunking for large documents
- Metadata extraction
- Integration with vector database
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# PDF processing
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    logger.warning("pypdf not available. Install with: pip install pypdf")

# DOCX processing
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available. Install with: pip install python-docx")


@dataclass
class DocumentInfo:
    """Information about a processed document."""
    file_path: str
    file_name: str
    file_type: str
    size_bytes: int
    content: str
    word_count: int
    char_count: int
    line_count: int
    extraction_method: str
    mime_type: str
    errors: List[str]
    metadata: Dict[str, Any]


class DocumentProcessingError(Exception):
    """Exception raised for document processing errors."""
    pass


class DocumentService:
    """
    Service for processing uploaded documents.

    Handles text extraction from various file formats and prepares
    content for knowledge base storage.
    """

    def __init__(self, max_file_size: int = 10 * 1024 * 1024):
        """
        Initialize DocumentService.

        Args:
            max_file_size: Maximum file size in bytes (default 10MB)
        """
        self.max_file_size = max_file_size

        # Supported file types
        self.text_extensions = {'.txt', '.md', '.rst', '.log'}
        self.code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs',
                               '.php', '.rb', '.go', '.rs', '.html', '.css', '.json',
                               '.yaml', '.yml', '.xml'}
        self.document_extensions = {'.pdf', '.docx', '.doc'}

        logger.info("DocumentService initialized")

    def process_document(self, file_path: str) -> DocumentInfo:
        """
        Process a document and extract its content.

        Args:
            file_path: Path to the document file

        Returns:
            DocumentInfo object with extracted content and metadata

        Raises:
            DocumentProcessingError: If processing fails
        """
        try:
            path = Path(file_path)

            if not path.exists():
                raise DocumentProcessingError(f"File not found: {file_path}")

            # Check file size
            size_bytes = path.stat().st_size
            if size_bytes > self.max_file_size:
                raise DocumentProcessingError(
                    f"File too large: {size_bytes} bytes (max: {self.max_file_size})"
                )

            # Detect file type and extract content
            extension = path.suffix.lower()
            errors = []

            if extension in self.text_extensions or extension in self.code_extensions:
                content, method = self._extract_text_file(file_path)
                mime_type = 'text/plain'
            elif extension == '.pdf':
                content, method, errors = self._extract_pdf(file_path)
                mime_type = 'application/pdf'
            elif extension in {'.docx', '.doc'}:
                content, method, errors = self._extract_docx(file_path)
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                raise DocumentProcessingError(f"Unsupported file type: {extension}")

            # Calculate statistics
            word_count = len(content.split())
            char_count = len(content)
            line_count = len(content.splitlines())

            # Extract metadata
            metadata = self._extract_metadata(content, extension)

            return DocumentInfo(
                file_path=str(path),
                file_name=path.name,
                file_type=extension,
                size_bytes=size_bytes,
                content=content,
                word_count=word_count,
                char_count=char_count,
                line_count=line_count,
                extraction_method=method,
                mime_type=mime_type,
                errors=errors,
                metadata=metadata
            )

        except DocumentProcessingError:
            raise
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise DocumentProcessingError(f"Failed to process document: {e}")

    def _extract_text_file(self, file_path: str) -> tuple[str, str]:
        """Extract content from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 'direct_read'
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                return content, 'direct_read_latin1'
            except Exception as e:
                logger.error(f"Failed to read text file with fallback encoding: {e}")
                raise DocumentProcessingError(f"Failed to read text file: {e}")

    def _extract_pdf(self, file_path: str) -> tuple[str, str, List[str]]:
        """Extract content from PDF file."""
        errors = []

        if not PYPDF_AVAILABLE:
            errors.append("pypdf not available - PDF extraction not supported")
            return "", "pdf_unavailable", errors

        try:
            content_parts = []

            with open(file_path, 'rb') as f:
                pdf_reader = pypdf.PdfReader(f)

                for page_num in range(len(pdf_reader.pages)):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text:
                            content_parts.append(text)
                    except Exception as e:
                        errors.append(f"Failed to extract page {page_num + 1}: {e}")

            content = '\n\n'.join(content_parts)
            return content, 'pypdf', errors

        except Exception as e:
            logger.error(f"Failed to extract PDF content: {e}")
            errors.append(str(e))
            return "", "pdf_failed", errors

    def _extract_docx(self, file_path: str) -> tuple[str, str, List[str]]:
        """Extract content from DOCX file."""
        errors = []

        if not DOCX_AVAILABLE:
            errors.append("python-docx not available - DOCX extraction not supported")
            return "", "docx_unavailable", errors

        try:
            doc = docx.Document(file_path)
            paragraphs = []

            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)

            content = '\n\n'.join(paragraphs)
            return content, 'python-docx', errors

        except Exception as e:
            logger.error(f"Failed to extract DOCX content: {e}")
            errors.append(str(e))
            return "", "docx_failed", errors

    def _extract_metadata(self, content: str, file_type: str) -> Dict[str, Any]:
        """Extract metadata from content."""
        metadata = {
            'file_type': file_type,
            'has_urls': 'http://' in content or 'https://' in content,
            'has_code': False
        }

        # Check for code indicators
        if file_type in self.code_extensions:
            metadata['has_code'] = True
            metadata['language'] = self._detect_language(file_type)

        return metadata

    def _detect_language(self, extension: str) -> str:
        """Detect programming language from extension."""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.xml': 'XML'
        }
        return language_map.get(extension.lower(), 'Unknown')

    def chunk_content(self, content: str, chunk_size: int = 1000,
                     overlap: int = 200) -> List[str]:
        """
        Split content into overlapping chunks for vector storage.

        Args:
            content: Text content to chunk
            chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            List of content chunks
        """
        if len(content) <= chunk_size:
            return [content]

        chunks = []
        start = 0

        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk = content[start:end]

            # Try to break at sentence boundaries
            if end < len(content):
                # Look for period, question mark, or exclamation point
                last_period = max(chunk.rfind('. '), chunk.rfind('? '), chunk.rfind('! '))

                if last_period > chunk_size * 0.7:  # Don't break too early
                    chunk = chunk[:last_period + 1]
                    end = start + last_period + 1
                else:
                    # Fall back to word boundary
                    last_space = chunk.rfind(' ')
                    if last_space > chunk_size * 0.8:
                        chunk = chunk[:last_space]
                        end = start + last_space

            chunks.append(chunk.strip())

            # Move start position with overlap
            start = end - overlap if end < len(content) else end

        return chunks


# Global instance
_document_service = None


def get_document_service() -> DocumentService:
    """Get or create the global DocumentService instance."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service


__all__ = [
    'DocumentService',
    'DocumentInfo',
    'DocumentProcessingError',
    'get_document_service'
]
