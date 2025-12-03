#!/usr/bin/env python3

import os
import json
import hashlib
import getpass
import datetime
import pickle
import uuid
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import sqlite3
import threading
import time
import numpy as np
from colorama import init, Fore, Back, Style
import mimetypes
from pathlib import Path

# from docx import Document as DocxDocument

# Third-party imports
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ChromaDB not found. Install with: pip install chromadb")
    exit(1)

try:
    import anthropic
except ImportError:
    print("Anthropic package not found. Install with: pip install anthropic")
    exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Sentence Transformers not found. Install with: pip install sentence-transformers")
    exit(1)

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not found. Install with: pip install PyPDF2")
    PyPDF2 = None

# try:
#     from docx import Document as DocxDocument
# except ImportError:
#     print("python-docx not found. Install with: pip install python-docx")
#     DocxDocument = None

init(autoreset=True)

# Import from modularized structure
from socratic_system.config import CONFIG
from socratic_system.models import (
    User, ProjectContext, KnowledgeEntry, TokenUsage, ConflictInfo
)
from socratic_system.agents import (
    Agent, ProjectManagerAgent, UserManagerAgent, SocraticCounselorAgent,
    ContextAnalyzerAgent, CodeGeneratorAgent, SystemMonitorAgent,
    ConflictDetectorAgent, DocumentAgent
)
from socratic_system.clients import ClaudeClient
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.ui import SocraticRAGSystem


# Claude API Client has been extracted to socratic_system/clients/
# AgentOrchestrator has been extracted to socratic_system/orchestration/
# SocraticRAGSystem has been extracted to socratic_system/ui/main_app.py

class DocumentProcessor:
    """Handles processing of various document formats"""

    def __init__(self, orchestrator: 'AgentOrchestrator'):
        self.orchestrator = orchestrator
        self.supported_formats = {
            '.pdf': self._process_pdf,
            '.txt': self._process_text,
            '.md': self._process_text,
            # '.docx': self._process_docx,
            '.py': self._process_text,
            '.js': self._process_text,
            '.html': self._process_text,
            '.css': self._process_text,
            '.json': self._process_text,
            '.xml': self._process_text,
            '.csv': self._process_text,
            '.yml': self._process_text,
            '.yaml': self._process_text
        }

    def process_file(self, file_path: str, project_id: str = None) -> Dict[str, Any]:
        """Process a file and add to knowledge base"""
        try:
            path = Path(file_path)

            if not path.exists():
                return {'status': 'error', 'message': f'File not found: {file_path}'}

            if not path.is_file():
                return {'status': 'error', 'message': f'Path is not a file: {file_path}'}

            # Get file extension
            extension = path.suffix.lower()

            if extension not in self.supported_formats:
                return {'status': 'error', 'message': f'Unsupported file format: {extension}'}

            # Process the file
            processor = self.supported_formats[extension]
            content = processor(path)

            if not content:
                return {'status': 'error', 'message': 'No content extracted from file'}

            # Chunk the content
            chunks = self._chunk_content(content, path.name)

            # Add chunks to knowledge base
            added_entries = []
            for i, chunk in enumerate(chunks):
                entry_id = f"{path.stem}_{i}_{uuid.uuid4().hex[:8]}"

                metadata = {
                    'source_file': str(path),
                    'file_type': extension,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'project_id': project_id,
                    'imported_at': datetime.datetime.now().isoformat()
                }

                entry = KnowledgeEntry(
                    id=entry_id,
                    content=chunk,
                    category=f"document_{extension[1:]}",  # Remove the dot
                    metadata=metadata
                )

                self.orchestrator.vector_db.add_knowledge(entry)
                added_entries.append(entry_id)

            return {
                'status': 'success',
                'entries_added': len(added_entries),
                'entry_ids': added_entries,
                'file_name': path.name
            }

        except Exception as e:
            return {'status': 'error', 'message': f'Error processing file: {str(e)}'}

    def process_directory(self, directory_path: str, project_id: str = None, recursive: bool = True) -> Dict[str, Any]:
        """Process all supported files in a directory"""
        try:
            path = Path(directory_path)

            if not path.exists():
                return {'status': 'error', 'message': f'Directory not found: {directory_path}'}

            if not path.is_dir():
                return {'status': 'error', 'message': f'Path is not a directory: {directory_path}'}

            # Find all supported files
            pattern = "**/*" if recursive else "*"
            all_files = list(path.glob(pattern))

            supported_files = [f for f in all_files
                               if f.is_file() and f.suffix.lower() in self.supported_formats]

            if not supported_files:
                return {'status': 'error', 'message': 'No supported files found in directory'}

            # Process each file
            results = {
                'processed_files': [],
                'failed_files': [],
                'total_entries': 0
            }

            for file_path in supported_files:
                print(f"{Fore.YELLOW}Processing: {file_path.name}")
                result = self.process_file(str(file_path), project_id)

                if result['status'] == 'success':
                    results['processed_files'].append({
                        'file': str(file_path),
                        'entries': result['entries_added']
                    })
                    results['total_entries'] += result['entries_added']
                else:
                    results['failed_files'].append({
                        'file': str(file_path),
                        'error': result['message']
                    })

            return {
                'status': 'success',
                'summary': results,
                'message': f"Processed {len(results['processed_files'])} files, {results['total_entries']} entries added"
            }

        except Exception as e:
            return {'status': 'error', 'message': f'Error processing directory: {str(e)}'}

    def _process_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        if not PyPDF2:
            raise ImportError("PyPDF2 not available")

        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"

        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")

        return text.strip()

    # def _process_docx(self, file_path: Path) -> str:
    #     """Extract text from Word document"""
    #     if not DocxDocument:
    #         raise ImportError("python-docx not available")
    #
    #     try:
    #         doc = DocxDocument(file_path)
    #         paragraphs = []
    #
    #         for paragraph in doc.paragraphs:
    #             if paragraph.text.strip():
    #                 paragraphs.append(paragraph.text.strip())
    #
    #         return "\n".join(paragraphs)
    #
    #     except Exception as e:
    #         raise Exception(f"Error reading Word document: {str(e)}")

    def _process_text(self, file_path: Path) -> str:
        """Process plain text files"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue

            # If all encodings fail, read as binary and decode with errors='ignore'
            with open(file_path, 'rb') as file:
                return file.read().decode('utf-8', errors='ignore')

        except Exception as e:
            raise Exception(f"Error reading text file: {str(e)}")

    def _chunk_content(self, content: str, filename: str, max_chunk_size: int = 1500) -> List[str]:
        """Split content into manageable chunks"""
        if len(content) <= max_chunk_size:
            return [content]

        chunks = []

        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        current_chunk = ""

        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    # Paragraph itself is too long, split by sentences
                    sentences = paragraph.split('. ')
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) > max_chunk_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = sentence
                            else:
                                # Sentence is too long, hard split
                                while len(sentence) > max_chunk_size:
                                    chunks.append(sentence[:max_chunk_size])
                                    sentence = sentence[max_chunk_size:]
                                current_chunk = sentence
                        else:
                            current_chunk += sentence + ". "
            else:
                current_chunk += paragraph + "\n\n"

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks


class DocumentAgent(Agent):
    def __init__(self, orchestrator):
        super().__init__("DocumentAgent", orchestrator)
        self.processor = DocumentProcessor(orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        action = request.get('action')

        if action == 'import_file':
            return self._import_file(request)
        elif action == 'import_directory':
            return self._import_directory(request)
        elif action == 'list_documents':
            return self._list_documents(request)

        return {'status': 'error', 'message': 'Unknown action'}

    def _import_file(self, request: Dict) -> Dict:
        file_path = request.get('file_path')
        project_id = request.get('project_id')

        return self.processor.process_file(file_path, project_id)

    def _import_directory(self, request: Dict) -> Dict:
        directory_path = request.get('directory_path')
        project_id = request.get('project_id')
        recursive = request.get('recursive', True)

        return self.processor.process_directory(directory_path, project_id, recursive)

    def _list_documents(self, request: Dict) -> Dict:
        """List imported documents"""
        project_id = request.get('project_id')

        # This would require querying the vector database for document entries
        # Implementation depends on how you want to structure the query
        return {'status': 'success', 'documents': []}


# Main Application Class
# Entry Point
def main():
    try:
        system = SocraticRAGSystem()
        system.start()
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
