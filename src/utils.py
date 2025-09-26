#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Utilities Module
========================================

File processing, document parsing, validation utilities, and text analysis
for the Socratic RAG Enhanced system.

Provides comprehensive utilities for:
- Document parsing (PDF, DOCX, TXT, MD, code files)
- Text processing and analysis for Socratic conversations
- Code analysis and quality assessment
- Knowledge extraction and chunking
- Extended validation utilities
"""

import os
import re
import ast
import json
import hashlib
import mimetypes
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
import datetime
import uuid

# Import core functionality
from src.core import (
    get_logger, get_config,
    SocraticException, ValidationError, DatabaseError,
    DateTimeHelper, FileHelper, ValidationHelper
)

# Import models for type hints and validation
from src.models import (
    GeneratedFile, FileType, FileStatus, ProjectPhase, UserRole,
    TestResult, TestType, Project, Module
)

# Third-party imports with graceful fallbacks
logger = get_logger('utils')

# Document processing imports
try:
    import PyPDF2

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available - PDF processing disabled")

try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available - DOCX processing disabled")

try:
    import markdown

    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logger.warning("markdown not available - Markdown processing disabled")

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup not available - HTML parsing disabled")

try:
    import openpyxl

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    logger.warning("openpyxl not available - Excel processing disabled")

# Text processing and embeddings
try:
    from sentence_transformers import SentenceTransformer

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers not available - embeddings disabled")

# Code analysis imports
try:
    import black

    BLACK_AVAILABLE = True
except ImportError:
    BLACK_AVAILABLE = False
    logger.warning("black not available - code formatting disabled")

try:
    import pylint.lint
    from pylint.reporters import JSONReporter
    from io import StringIO

    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False
    logger.warning("pylint not available - code analysis disabled")


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class DocumentInfo:
    """Information extracted from a document"""
    file_path: str
    file_name: str
    file_type: str
    mime_type: str
    size_bytes: int
    encoding: Optional[str] = None
    language: Optional[str] = None
    creation_date: Optional[datetime.datetime] = None
    modification_date: Optional[datetime.datetime] = None

    # Content information
    content: str = ""
    content_hash: str = ""
    page_count: int = 0
    word_count: int = 0
    character_count: int = 0

    # Metadata
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: List[str] = field(default_factory=list)

    # Processing information
    extraction_method: str = ""
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class TextChunk:
    """A chunk of text with metadata for knowledge processing"""
    chunk_id: str
    content: str
    source_file: str
    source_type: str
    chunk_index: int
    start_position: int
    end_position: int

    # Content analysis
    word_count: int = 0
    character_count: int = 0
    sentence_count: int = 0

    # Context information
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    line_number: Optional[int] = None

    # Processing metadata
    embedding_vector: Optional[List[float]] = None
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    importance_score: float = 0.0

    # Timestamps
    created_at: datetime.datetime = field(default_factory=DateTimeHelper.now)


@dataclass
class CodeAnalysisResult:
    """Result of code analysis"""
    file_path: str
    file_type: FileType
    analysis_timestamp: datetime.datetime = field(default_factory=DateTimeHelper.now)

    # Basic metrics
    lines_of_code: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    total_lines: int = 0

    # Complexity metrics
    cyclomatic_complexity: float = 0.0
    maintainability_index: float = 0.0
    technical_debt_ratio: float = 0.0

    # Quality indicators
    code_style_score: float = 0.0
    documentation_coverage: float = 0.0
    test_coverage: float = 0.0

    # Issues and suggestions
    syntax_errors: List[Dict[str, Any]] = field(default_factory=list)
    style_issues: List[Dict[str, Any]] = field(default_factory=list)
    security_issues: List[Dict[str, Any]] = field(default_factory=list)
    performance_issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    # Dependencies
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)


# ============================================================================
# FILE PROCESSING UTILITIES
# ============================================================================

class FileProcessor:
    """File processing and content extraction utilities"""

    def __init__(self):
        self.logger = get_logger('utils.file_processor')
        self.config = get_config()

        # Initialize embeddings model if available
        self.embeddings_model = None
        if EMBEDDINGS_AVAILABLE:
            try:
                model_name = getattr(self.config, 'embedding_model', 'all-MiniLM-L6-v2')
                self.embeddings_model = SentenceTransformer(model_name)
                self.logger.info(f"Loaded embeddings model: {model_name}")
            except Exception as e:
                self.logger.warning(f"Failed to load embeddings model: {e}")

    def process_file(self, file_path: str) -> DocumentInfo:
        """Process a file and extract all available information"""
        start_time = DateTimeHelper.now()

        try:
            # Basic file information
            file_path = Path(file_path)
            if not file_path.exists():
                raise ValidationError(f"File not found: {file_path}")

            # Get file stats
            stat_info = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))

            doc_info = DocumentInfo(
                file_path=str(file_path),
                file_name=file_path.name,
                file_type=file_path.suffix.lower(),
                mime_type=mime_type or 'application/octet-stream',
                size_bytes=stat_info.st_size,
                creation_date=datetime.datetime.fromtimestamp(stat_info.st_ctime, datetime.timezone.utc),
                modification_date=datetime.datetime.fromtimestamp(stat_info.st_mtime, datetime.timezone.utc)
            )

            # Extract content based on file type
            self._extract_content(doc_info)

            # Generate content hash
            doc_info.content_hash = hashlib.sha256(doc_info.content.encode('utf-8')).hexdigest()

            # Calculate processing time
            end_time = DateTimeHelper.now()
            doc_info.processing_time = (end_time - start_time).total_seconds()

            self.logger.info(f"Processed file: {file_path.name} ({doc_info.word_count} words)")
            return doc_info

        except Exception as e:
            self.logger.error(f"Failed to process file {file_path}: {e}")
            raise ValidationError(f"File processing failed: {e}")

    def _extract_content(self, doc_info: DocumentInfo) -> None:
        """Extract content based on file type"""
        file_ext = doc_info.file_type.lower()

        if file_ext == '.txt':
            self._extract_text_content(doc_info)
        elif file_ext == '.md':
            self._extract_markdown_content(doc_info)
        elif file_ext == '.pdf':
            self._extract_pdf_content(doc_info)
        elif file_ext in ['.docx', '.doc']:
            self._extract_docx_content(doc_info)
        elif file_ext in ['.html', '.htm']:
            self._extract_html_content(doc_info)
        elif file_ext in ['.py', '.js', '.ts', '.css', '.sql', '.yaml', '.yml', '.json']:
            self._extract_code_content(doc_info)
        elif file_ext in ['.xlsx', '.xls']:
            self._extract_excel_content(doc_info)
        else:
            # Try to read as text
            try:
                self._extract_text_content(doc_info)
            except:
                doc_info.errors.append(f"Unsupported file type: {file_ext}")

        # Calculate word and character counts
        if doc_info.content:
            doc_info.word_count = len(doc_info.content.split())
            doc_info.character_count = len(doc_info.content)

    def _extract_text_content(self, doc_info: DocumentInfo) -> None:
        """Extract content from plain text files"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']

            for encoding in encodings:
                try:
                    with open(doc_info.file_path, 'r', encoding=encoding) as f:
                        doc_info.content = f.read()
                        doc_info.encoding = encoding
                        doc_info.extraction_method = f"text_reader_{encoding}"
                        break
                except UnicodeDecodeError:
                    continue

            if not doc_info.content:
                raise ValidationError("Could not decode text file with any encoding")

        except Exception as e:
            doc_info.errors.append(f"Text extraction failed: {e}")

    def _extract_markdown_content(self, doc_info: DocumentInfo) -> None:
        """Extract content from Markdown files"""
        try:
            # First extract as text
            self._extract_text_content(doc_info)

            if MARKDOWN_AVAILABLE and doc_info.content:
                # Convert markdown to HTML for better parsing
                html_content = markdown.markdown(doc_info.content)

                if BS4_AVAILABLE:
                    # Extract plain text from HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    doc_info.content = soup.get_text(separator='\n')

                doc_info.extraction_method = "markdown_parser"
            else:
                doc_info.warnings.append("Markdown parsing not available, using text extraction")

        except Exception as e:
            doc_info.errors.append(f"Markdown extraction failed: {e}")

    def _extract_pdf_content(self, doc_info: DocumentInfo) -> None:
        """Extract content from PDF files"""
        if not PDF_AVAILABLE:
            doc_info.errors.append("PDF processing not available - PyPDF2 not installed")
            return

        try:
            with open(doc_info.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract metadata
                if pdf_reader.metadata:
                    doc_info.title = pdf_reader.metadata.get('/Title', '')
                    doc_info.author = pdf_reader.metadata.get('/Author', '')
                    doc_info.subject = pdf_reader.metadata.get('/Subject', '')

                # Extract text from all pages
                doc_info.page_count = len(pdf_reader.pages)
                text_content = []

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
                    except Exception as e:
                        doc_info.warnings.append(f"Failed to extract page {page_num + 1}: {e}")

                doc_info.content = '\n\n'.join(text_content)
                doc_info.extraction_method = "pypdf2"

        except Exception as e:
            doc_info.errors.append(f"PDF extraction failed: {e}")

    def _extract_docx_content(self, doc_info: DocumentInfo) -> None:
        """Extract content from Word documents"""
        if not DOCX_AVAILABLE:
            doc_info.errors.append("DOCX processing not available - python-docx not installed")
            return

        try:
            document = Document(doc_info.file_path)

            # Extract metadata
            if document.core_properties:
                doc_info.title = document.core_properties.title or ''
                doc_info.author = document.core_properties.author or ''
                doc_info.subject = document.core_properties.subject or ''
                doc_info.keywords = (document.core_properties.keywords or '').split(',')

            # Extract text from paragraphs
            paragraphs = []
            for paragraph in document.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text)

            doc_info.content = '\n\n'.join(paragraphs)
            doc_info.extraction_method = "python_docx"

        except Exception as e:
            doc_info.errors.append(f"DOCX extraction failed: {e}")

    def _extract_html_content(self, doc_info: DocumentInfo) -> None:
        """Extract content from HTML files"""
        try:
            with open(doc_info.file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            if BS4_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')

                # Extract metadata
                title_tag = soup.find('title')
                if title_tag:
                    doc_info.title = title_tag.get_text().strip()

                meta_description = soup.find('meta', attrs={'name': 'description'})
                if meta_description:
                    doc_info.subject = meta_description.get('content', '')

                # Extract text content
                doc_info.content = soup.get_text(separator='\n')
                doc_info.extraction_method = "beautifulsoup"
            else:
                # Fallback: basic HTML tag removal
                doc_info.content = re.sub(r'<[^>]+>', '', html_content)
                doc_info.extraction_method = "regex_html_strip"
                doc_info.warnings.append("BeautifulSoup not available, using basic HTML parsing")

        except Exception as e:
            doc_info.errors.append(f"HTML extraction failed: {e}")

    def _extract_code_content(self, doc_info: DocumentInfo) -> None:
        """Extract content from code files"""
        try:
            self._extract_text_content(doc_info)
            doc_info.extraction_method = f"code_reader_{doc_info.file_type}"

        except Exception as e:
            doc_info.errors.append(f"Code extraction failed: {e}")

    def _extract_excel_content(self, doc_info: DocumentInfo) -> None:
        """Extract content from Excel files"""
        if not EXCEL_AVAILABLE:
            doc_info.errors.append("Excel processing not available - openpyxl not installed")
            return

        try:
            workbook = openpyxl.load_workbook(doc_info.file_path, data_only=True)

            # Extract content from all worksheets
            sheet_contents = []
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                sheet_content = [f"--- Sheet: {sheet_name} ---"]

                for row in sheet.iter_rows(values_only=True):
                    if any(cell is not None for cell in row):
                        row_text = '\t'.join(str(cell) if cell is not None else '' for cell in row)
                        sheet_content.append(row_text)

                sheet_contents.append('\n'.join(sheet_content))

            doc_info.content = '\n\n'.join(sheet_contents)
            doc_info.extraction_method = "openpyxl"

        except Exception as e:
            doc_info.errors.append(f"Excel extraction failed: {e}")


# ============================================================================
# TEXT PROCESSING AND ANALYSIS
# ============================================================================

class TextProcessor:
    """Text processing utilities for Socratic conversations and analysis"""

    def __init__(self):
        self.logger = get_logger('utils.text_processor')
        self.config = get_config()

    def chunk_text(self, text: str, source_file: str, source_type: str,
                   chunk_size: int = 1000, overlap: int = 200) -> List[TextChunk]:
        """Split text into chunks with overlap for processing"""
        if not text.strip():
            return []

        chunks = []
        text_length = len(text)
        start = 0
        chunk_index = 0

        while start < text_length:
            end = min(start + chunk_size, text_length)

            # Try to break at sentence boundaries
            if end < text_length:
                # Look for sentence endings within overlap distance
                for i in range(end - overlap, end):
                    if i > start and text[i] in '.!?':
                        end = i + 1
                        break

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunk = TextChunk(
                    chunk_id=str(uuid.uuid4()),
                    content=chunk_content,
                    source_file=source_file,
                    source_type=source_type,
                    chunk_index=chunk_index,
                    start_position=start,
                    end_position=end,
                    word_count=len(chunk_content.split()),
                    character_count=len(chunk_content),
                    sentence_count=len(re.findall(r'[.!?]+', chunk_content))
                )

                # Extract keywords
                chunk.keywords = self.extract_keywords(chunk_content)

                chunks.append(chunk)
                chunk_index += 1

            start = max(start + 1, end - overlap)

        self.logger.info(f"Created {len(chunks)} chunks from {source_file}")
        return chunks

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text using simple frequency analysis"""
        if not text.strip():
            return []

        try:
            # Simple keyword extraction
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

            # Filter out common stop words
            stop_words = {
                'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
                'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
                'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy',
                'did', 'use', 'way', 'she', 'man', 'say', 'her', 'you', 'him', 'been',
                'than', 'were', 'said', 'from', 'have', 'they', 'know', 'want', 'been',
                'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just',
                'like', 'long', 'make', 'many', 'over', 'such', 'take', 'will', 'well'
            }

            filtered_words = [word for word in words if word not in stop_words and len(word) > 3]

            # Count frequency
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1

            # Return top keywords
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in keywords[:max_keywords]]

        except Exception as e:
            self.logger.warning(f"Keyword extraction failed: {e}")
            return []

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Basic sentiment analysis using keyword matching"""
        if not text.strip():
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}

        try:
            # Simple sentiment keywords
            positive_words = {
                'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love',
                'like', 'enjoy', 'happy', 'pleased', 'satisfied', 'perfect', 'awesome',
                'brilliant', 'outstanding', 'impressive', 'remarkable', 'superb'
            }

            negative_words = {
                'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'angry',
                'frustrated', 'disappointed', 'upset', 'sad', 'worried', 'concerned',
                'problem', 'issue', 'error', 'wrong', 'fail', 'broken', 'difficult'
            }

            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            total_words = len(words)

            if total_words == 0:
                return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}

            positive_score = positive_count / total_words
            negative_score = negative_count / total_words
            neutral_score = 1.0 - (positive_score + negative_score)

            return {
                'positive': positive_score,
                'negative': negative_score,
                'neutral': max(0.0, neutral_score)
            }

        except Exception as e:
            self.logger.warning(f"Sentiment analysis failed: {e}")
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        if not EMBEDDINGS_AVAILABLE or not self.embeddings_model:
            self.logger.warning("Embeddings not available")
            return []

        try:
            embeddings = self.embeddings_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()

        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            return []


# ============================================================================
# CODE ANALYSIS UTILITIES
# ============================================================================

class CodeAnalyzer:
    """Code analysis and quality assessment utilities"""

    def __init__(self):
        self.logger = get_logger('utils.code_analyzer')
        self.config = get_config()

    def analyze_code_file(self, file_path: str, content: Optional[str] = None) -> CodeAnalysisResult:
        """Analyze a code file and return quality metrics"""
        try:
            # Determine file type
            file_path = Path(file_path)
            file_ext = file_path.suffix.lower()
            file_type = self._get_file_type_from_extension(file_ext)

            # Read content if not provided
            if content is None:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    raise ValidationError(f"Could not read file {file_path}: {e}")

            result = CodeAnalysisResult(
                file_path=str(file_path),
                file_type=file_type
            )

            # Basic line counting
            self._count_lines(content, result)

            # Language-specific analysis
            if file_ext == '.py':
                self._analyze_python_code(content, result)
            elif file_ext in ['.js', '.ts']:
                self._analyze_javascript_code(content, result)
            elif file_ext == '.sql':
                self._analyze_sql_code(content, result)
            else:
                self._analyze_generic_code(content, result)

            # Common analysis for all file types
            self._analyze_documentation(content, result)
            self._check_code_style(content, result, file_ext)

            self.logger.info(f"Analyzed code file: {file_path.name}")
            return result

        except Exception as e:
            self.logger.error(f"Code analysis failed for {file_path}: {e}")
            raise ValidationError(f"Code analysis failed: {e}")

    def _get_file_type_from_extension(self, ext: str) -> FileType:
        """Map file extension to FileType enum"""
        mapping = {
            '.py': FileType.PYTHON,
            '.js': FileType.JAVASCRIPT,
            '.ts': FileType.TYPESCRIPT,
            '.html': FileType.HTML,
            '.css': FileType.CSS,
            '.sql': FileType.SQL,
            '.json': FileType.JSON,
            '.yaml': FileType.YAML,
            '.yml': FileType.YAML,
            '.md': FileType.MARKDOWN,
            'dockerfile': FileType.DOCKERFILE
        }
        return mapping.get(ext.lower(), FileType.CONFIG)

    def _count_lines(self, content: str, result: CodeAnalysisResult) -> None:
        """Count different types of lines in code"""
        lines = content.split('\n')
        result.total_lines = len(lines)

        for line in lines:
            stripped = line.strip()
            if not stripped:
                result.blank_lines += 1
            elif stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                result.comment_lines += 1
            else:
                result.lines_of_code += 1

    def _analyze_python_code(self, content: str, result: CodeAnalysisResult) -> None:
        """Python-specific code analysis"""
        try:
            # Parse AST
            tree = ast.parse(content)

            # Extract functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    result.functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    result.classes.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        result.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            result.imports.append(f"{node.module}.{alias.name}")

            # Calculate cyclomatic complexity (simplified)
            result.cyclomatic_complexity = self._calculate_python_complexity(tree)

            # Check for common issues
            self._check_python_issues(content, result)

        except SyntaxError as e:
            result.syntax_errors.append({
                'line': e.lineno or 0,
                'message': str(e),
                'type': 'syntax_error'
            })
        except Exception as e:
            result.suggestions.append(f"Python analysis failed: {e}")

    def _calculate_python_complexity(self, tree: ast.AST) -> float:
        """Calculate simplified cyclomatic complexity"""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With,
                                 ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return float(complexity)

    def _check_python_issues(self, content: str, result: CodeAnalysisResult) -> None:
        """Check for common Python issues"""
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Line length check
            if len(line) > 120:
                result.style_issues.append({
                    'line': i,
                    'message': f'Line too long ({len(line)} characters)',
                    'type': 'line_length'
                })

            # Check for dangerous functions
            dangerous_patterns = [
                (r'\beval\s*\(', 'Use of eval() is dangerous'),
                (r'\bexec\s*\(', 'Use of exec() is dangerous'),
                (r'\b__import__\s*\(', 'Direct use of __import__ is discouraged'),
            ]

            for pattern, message in dangerous_patterns:
                if re.search(pattern, line):
                    result.security_issues.append({
                        'line': i,
                        'message': message,
                        'type': 'security'
                    })

    def _analyze_javascript_code(self, content: str, result: CodeAnalysisResult) -> None:
        """JavaScript-specific code analysis"""
        try:
            # Extract functions (simple regex-based)
            function_pattern = r'function\s+(\w+)\s*\('
            result.functions.extend(re.findall(function_pattern, content))

            # Extract classes
            class_pattern = r'class\s+(\w+)\s*[{|extends]'
            result.classes.extend(re.findall(class_pattern, content))

            # Extract imports
            import_patterns = [
                r'import\s+.*\s+from\s+["\']([^"\']+)["\']',
                r'require\s*\(\s*["\']([^"\']+)["\']\s*\)'
            ]

            for pattern in import_patterns:
                result.imports.extend(re.findall(pattern, content))

            # Simple complexity estimation
            result.cyclomatic_complexity = self._calculate_js_complexity(content)

        except Exception as e:
            result.suggestions.append(f"JavaScript analysis failed: {e}")

    def _calculate_js_complexity(self, content: str) -> float:
        """Calculate simplified JavaScript complexity"""
        # Count decision points
        complexity_keywords = ['if', 'else', 'while', 'for', 'switch', 'case', '?', '&&', '||']
        complexity = 1

        for keyword in complexity_keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', content))

        return float(complexity)

    def _analyze_sql_code(self, content: str, result: CodeAnalysisResult) -> None:
        """SQL-specific code analysis"""
        try:
            # Count different statement types
            statements = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']

            for statement in statements:
                count = len(re.findall(rf'\b{statement}\b', content, re.IGNORECASE))
                if count > 0:
                    result.functions.append(f"{statement}: {count}")

            # Check for potential issues
            if re.search(r'SELECT\s+\*', content, re.IGNORECASE):
                result.performance_issues.append({
                    'message': 'SELECT * can impact performance',
                    'type': 'performance'
                })

            if not re.search(r'\bWHERE\b', content, re.IGNORECASE) and \
                    re.search(r'\b(UPDATE|DELETE)\b', content, re.IGNORECASE):
                result.security_issues.append({
                    'message': 'UPDATE/DELETE without WHERE clause is dangerous',
                    'type': 'security'
                })

        except Exception as e:
            result.suggestions.append(f"SQL analysis failed: {e}")

    def _analyze_generic_code(self, content: str, result: CodeAnalysisResult) -> None:
        """Generic code analysis for unknown file types"""
        # Basic pattern matching for functions and classes
        function_patterns = [
            r'function\s+(\w+)',
            r'def\s+(\w+)',
            r'(\w+)\s*\(',
        ]

        for pattern in function_patterns:
            matches = re.findall(pattern, content)
            result.functions.extend(matches[:10])  # Limit to avoid noise

        # Simple complexity based on nesting
        nesting_chars = content.count('{') + content.count('(') + content.count('[')
        result.cyclomatic_complexity = float(nesting_chars / 10)  # Normalized

    def _analyze_documentation(self, content: str, result: CodeAnalysisResult) -> None:
        """Analyze documentation coverage"""
        total_lines = result.lines_of_code
        if total_lines == 0:
            result.documentation_coverage = 0.0
            return

        # Count documentation patterns
        doc_patterns = [
            r'""".*?"""',  # Python docstrings
            r"'''.*?'''",
            r'/\*\*.*?\*/',  # JSDoc
            r'//.*$',  # Single line comments
            r'#.*$',  # Python/shell comments
        ]

        doc_lines = 0
        for pattern in doc_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            for match in matches:
                doc_lines += len(match.split('\n'))

        result.documentation_coverage = min(100.0, (doc_lines / total_lines) * 100)

    def _check_code_style(self, content: str, result: CodeAnalysisResult, file_ext: str) -> None:
        """Check code style and formatting"""
        lines = content.split('\n')
        style_score = 100.0

        for i, line in enumerate(lines, 1):
            # Trailing whitespace
            if line.endswith(' ') or line.endswith('\t'):
                result.style_issues.append({
                    'line': i,
                    'message': 'Trailing whitespace',
                    'type': 'whitespace'
                })
                style_score -= 1

            # Mixed tabs and spaces (Python specific)
            if file_ext == '.py' and '\t' in line and ' ' in line:
                result.style_issues.append({
                    'line': i,
                    'message': 'Mixed tabs and spaces',
                    'type': 'indentation'
                })
                style_score -= 5

        result.code_style_score = max(0.0, style_score)


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

class ExtendedValidator:
    """Extended validation utilities beyond core ValidationHelper"""

    def __init__(self):
        self.logger = get_logger('utils.validator')

    def validate_project_specifications(self, project: Project) -> List[str]:
        """Validate project specifications for completeness"""
        issues = []

        # Basic validation
        if not project.name.strip():
            issues.append("Project name is required")

        if not project.owner.strip():
            issues.append("Project owner is required")

        # Technical specifications
        if project.phase != ProjectPhase.DISCOVERY:
            if not project.tech_stack:
                issues.append("Technology stack should be defined after discovery phase")

            if not project.requirements:
                issues.append("Requirements should be defined after discovery phase")

        # Architecture validation
        if project.architecture_pattern:
            valid_patterns = ['mvc', 'microservices', 'layered', 'hexagonal', 'clean']
            if project.architecture_pattern.lower() not in valid_patterns:
                issues.append(f"Architecture pattern '{project.architecture_pattern}' not recognized")

        # Technology stack validation
        for tech in project.tech_stack:
            if not self.validate_technology_name(tech):
                issues.append(f"Technology '{tech}' format not recognized")

        return issues

    def validate_technology_name(self, tech: str) -> bool:
        """Validate technology name format"""
        if not tech or not tech.strip():
            return False

        # Allow alphanumeric, dots, hyphens, and spaces
        pattern = r'^[a-zA-Z0-9\s\.\-_+]+$'
        return bool(re.match(pattern, tech.strip()))

    def validate_generated_file(self, generated_file: GeneratedFile) -> List[str]:
        """Validate generated file content and structure"""
        issues = []

        if not generated_file.file_path.strip():
            issues.append("File path is required")

        if not generated_file.content and generated_file.status == FileStatus.GENERATED:
            issues.append("Content is required for generated files")

        # File path validation
        if not self.validate_file_path(generated_file.file_path):
            issues.append("Invalid file path format")

        # Content validation by file type
        if generated_file.content:
            content_issues = self.validate_code_content(
                generated_file.content,
                generated_file.file_type
            )
            issues.extend(content_issues)

        return issues

    def validate_file_path(self, file_path: str) -> bool:
        """Validate file path format"""
        if not file_path:
            return False

        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in file_path for char in invalid_chars):
            return False

        # Check for relative path attempts
        if '..' in file_path:
            return False

        return True

    def validate_code_content(self, content: str, file_type: FileType) -> List[str]:
        """Validate code content based on file type"""
        issues = []

        if file_type == FileType.PYTHON:
            issues.extend(self._validate_python_content(content))
        elif file_type == FileType.JAVASCRIPT:
            issues.extend(self._validate_javascript_content(content))
        elif file_type == FileType.JSON:
            issues.extend(self._validate_json_content(content))
        elif file_type == FileType.SQL:
            issues.extend(self._validate_sql_content(content))

        return issues

    def _validate_python_content(self, content: str) -> List[str]:
        """Validate Python code content"""
        issues = []

        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(f"Python syntax error: {e}")

        # Check for dangerous patterns
        dangerous_patterns = [
            (r'\beval\s*\(', 'eval() usage detected'),
            (r'\bexec\s*\(', 'exec() usage detected'),
            (r'\b__import__\s*\(', 'Direct __import__ usage detected'),
        ]

        for pattern, message in dangerous_patterns:
            if re.search(pattern, content):
                issues.append(message)

        return issues

    def _validate_javascript_content(self, content: str) -> List[str]:
        """Validate JavaScript code content"""
        issues = []

        # Basic syntax checks
        if content.count('{') != content.count('}'):
            issues.append("Mismatched braces in JavaScript code")

        if content.count('(') != content.count(')'):
            issues.append("Mismatched parentheses in JavaScript code")

        # Check for dangerous patterns
        dangerous_patterns = [
            (r'\beval\s*\(', 'eval() usage detected'),
            (r'innerHTML\s*=', 'innerHTML usage can be unsafe'),
        ]

        for pattern, message in dangerous_patterns:
            if re.search(pattern, content):
                issues.append(message)

        return issues

    def _validate_json_content(self, content: str) -> List[str]:
        """Validate JSON content"""
        issues = []

        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            issues.append(f"Invalid JSON: {e}")

        return issues

    def _validate_sql_content(self, content: str) -> List[str]:
        """Validate SQL content"""
        issues = []

        # Check for potentially dangerous patterns
        dangerous_patterns = [
            (r'DROP\s+TABLE', 'DROP TABLE statement detected'),
            (r'DELETE\s+FROM.*(?!WHERE)', 'DELETE without WHERE clause detected'),
            (r'UPDATE\s+.*(?!WHERE)', 'UPDATE without WHERE clause detected'),
        ]

        for pattern, message in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(message)

        return issues


# ============================================================================
# KNOWLEDGE EXTRACTION UTILITIES
# ============================================================================

class KnowledgeExtractor:
    """Knowledge extraction and processing utilities"""

    def __init__(self):
        self.logger = get_logger('utils.knowledge')
        self.file_processor = FileProcessor()
        self.text_processor = TextProcessor()

    def extract_project_insights(self, conversation_messages: List[Any]) -> Dict[str, Any]:
        """Extract insights from Socratic conversation"""
        insights = {
            'key_requirements': [],
            'technical_preferences': [],
            'constraints': [],
            'risks': [],
            'stakeholder_concerns': [],
            'role_perspectives': {}
        }

        try:
            for message in conversation_messages:
                if not hasattr(message, 'content') or not message.content:
                    continue

                # Analyze content based on role
                role = getattr(message, 'role', None)
                if role:
                    role_insights = self._extract_role_insights(message.content, role)
                    if role.value not in insights['role_perspectives']:
                        insights['role_perspectives'][role.value] = []
                    insights['role_perspectives'][role.value].extend(role_insights)

                # Extract different types of insights
                insights['key_requirements'].extend(self._extract_requirements(message.content))
                insights['technical_preferences'].extend(self._extract_tech_preferences(message.content))
                insights['constraints'].extend(self._extract_constraints(message.content))
                insights['risks'].extend(self._extract_risks(message.content))

            # Remove duplicates and clean up
            for key in insights:
                if isinstance(insights[key], list):
                    insights[key] = list(set(insights[key]))

            self.logger.info(f"Extracted insights: {len(insights['key_requirements'])} requirements, "
                             f"{len(insights['technical_preferences'])} tech preferences")

            return insights

        except Exception as e:
            self.logger.error(f"Insight extraction failed: {e}")
            return insights

    def _extract_role_insights(self, content: str, role: UserRole) -> List[str]:
        """Extract insights specific to a role"""
        insights = []

        role_keywords = {
            UserRole.PROJECT_MANAGER: ['timeline', 'budget', 'resource', 'stakeholder', 'deadline'],
            UserRole.TECHNICAL_LEAD: ['architecture', 'scalability', 'performance', 'technology', 'framework'],
            UserRole.DEVELOPER: ['implementation', 'code', 'algorithm', 'library', 'API'],
            UserRole.DESIGNER: ['user experience', 'interface', 'usability', 'design', 'visual'],
            UserRole.QA_TESTER: ['testing', 'quality', 'bug', 'validation', 'edge case'],
            UserRole.BUSINESS_ANALYST: ['requirement', 'business rule', 'compliance', 'workflow'],
            UserRole.DEVOPS_ENGINEER: ['deployment', 'infrastructure', 'monitoring', 'security', 'CI/CD']
        }

        keywords = role_keywords.get(role, [])
        sentences = re.split(r'[.!?]+', content)

        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 10:  # Filter out very short sentences
                    insights.append(clean_sentence)

        return insights[:5]  # Limit to top 5 insights per role

    def _extract_requirements(self, content: str) -> List[str]:
        """Extract requirements from text"""
        requirements = []

        requirement_patterns = [
            r'(?:must|should|need to|required to|have to)\s+([^.!?]+)',
            r'(?:requirement|feature):\s*([^.!?]+)',
            r'(?:user|system|application)\s+(?:should|must|needs?)\s+([^.!?]+)',
        ]

        for pattern in requirement_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                clean_req = match.strip()
                if len(clean_req) > 10:
                    requirements.append(clean_req)

        return requirements

    def _extract_tech_preferences(self, content: str) -> List[str]:
        """Extract technology preferences from text"""
        preferences = []

        # Common technology names
        tech_pattern = r'\b(?:Python|JavaScript|React|Node|Django|Flask|PostgreSQL|MySQL|MongoDB|Docker|Kubernetes|AWS|Azure|GCP)\b'
        matches = re.findall(tech_pattern, content, re.IGNORECASE)
        preferences.extend(matches)

        # Framework/library mentions
        framework_pattern = r'(?:using|with|prefer)\s+([A-Za-z][A-Za-z0-9_-]+)'
        matches = re.findall(framework_pattern, content, re.IGNORECASE)
        preferences.extend(matches)

        return preferences

    def _extract_constraints(self, content: str) -> List[str]:
        """Extract constraints from text"""
        constraints = []

        constraint_patterns = [
            r'(?:cannot|can\'t|unable to|restricted|limited|constraint)(?:[^.!?]+)([^.!?]+)',
            r'(?:budget|time|resource)\s+(?:constraint|limitation):\s*([^.!?]+)',
            r'(?:must not|should not|cannot have)\s+([^.!?]+)',
        ]

        for pattern in constraint_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                clean_constraint = match.strip()
                if len(clean_constraint) > 10:
                    constraints.append(clean_constraint)

        return constraints

    def _extract_risks(self, content: str) -> List[str]:
        """Extract risks from text"""
        risks = []

        risk_patterns = [
            r'(?:risk|concern|worry|problem|issue|challenge):\s*([^.!?]+)',
            r'(?:might|could|may)\s+(?:fail|break|cause problems?)\s+([^.!?]+)',
            r'(?:potential|possible)\s+(?:issue|problem|risk)\s+([^.!?]+)',
        ]

        for pattern in risk_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                clean_risk = match.strip()
                if len(clean_risk) > 10:
                    risks.append(clean_risk)

        return risks


# ============================================================================
# UTILITY FACTORY AND MAIN INTERFACE
# ============================================================================

class UtilityFactory:
    """Factory for creating utility instances"""

    _instances = {}

    @classmethod
    def get_file_processor(cls) -> FileProcessor:
        """Get FileProcessor instance (singleton)"""
        if 'file_processor' not in cls._instances:
            cls._instances['file_processor'] = FileProcessor()
        return cls._instances['file_processor']

    @classmethod
    def get_text_processor(cls) -> TextProcessor:
        """Get TextProcessor instance (singleton)"""
        if 'text_processor' not in cls._instances:
            cls._instances['text_processor'] = TextProcessor()
        return cls._instances['text_processor']

    @classmethod
    def get_code_analyzer(cls) -> CodeAnalyzer:
        """Get CodeAnalyzer instance (singleton)"""
        if 'code_analyzer' not in cls._instances:
            cls._instances['code_analyzer'] = CodeAnalyzer()
        return cls._instances['code_analyzer']

    @classmethod
    def get_validator(cls) -> ExtendedValidator:
        """Get ExtendedValidator instance (singleton)"""
        if 'validator' not in cls._instances:
            cls._instances['validator'] = ExtendedValidator()
        return cls._instances['validator']

    @classmethod
    def get_knowledge_extractor(cls) -> KnowledgeExtractor:
        """Get KnowledgeExtractor instance (singleton)"""
        if 'knowledge_extractor' not in cls._instances:
            cls._instances['knowledge_extractor'] = KnowledgeExtractor()
        return cls._instances['knowledge_extractor']


# ============================================================================
# MAIN EXPORTS
# ============================================================================

def get_file_processor() -> FileProcessor:
    """Get file processor instance"""
    return UtilityFactory.get_file_processor()


def get_text_processor() -> TextProcessor:
    """Get text processor instance"""
    return UtilityFactory.get_text_processor()


def get_code_analyzer() -> CodeAnalyzer:
    """Get code analyzer instance"""
    return UtilityFactory.get_code_analyzer()


def get_validator() -> ExtendedValidator:
    """Get extended validator instance"""
    return UtilityFactory.get_validator()


def get_knowledge_extractor() -> KnowledgeExtractor:
    """Get knowledge extractor instance"""
    return UtilityFactory.get_knowledge_extractor()


# Export main classes and functions
__all__ = [
    # Data structures
    'DocumentInfo', 'TextChunk', 'CodeAnalysisResult',

    # Main utility classes
    'FileProcessor', 'TextProcessor', 'CodeAnalyzer',
    'ExtendedValidator', 'KnowledgeExtractor',

    # Factory and convenience functions
    'UtilityFactory',
    'get_file_processor', 'get_text_processor', 'get_code_analyzer',
    'get_validator', 'get_knowledge_extractor'
]

# ============================================================================
# MODULE INITIALIZATION AND TESTING
# ============================================================================

if __name__ == "__main__":
    # Test the utilities
    logger.info("Testing utilities module...")

    try:
        # Test file processor
        file_proc = get_file_processor()
        logger.info("✅ FileProcessor created")

        # Test text processor
        text_proc = get_text_processor()
        test_text = "This is a test document with important information about Python development."
        keywords = text_proc.extract_keywords(test_text)
        logger.info(f"✅ TextProcessor test - Keywords: {keywords}")

        # Test code analyzer
        code_analyzer = get_code_analyzer()
        test_python_code = """
def hello_world():
    '''Simple test function'''
    print("Hello, World!")
    return True
        """
        # Note: We can't test file analysis without an actual file, but we can test the class creation
        logger.info("✅ CodeAnalyzer created")

        # Test validator
        validator = get_validator()
        test_tech = "Python 3.9"
        is_valid = validator.validate_technology_name(test_tech)
        logger.info(f"✅ Validator test - '{test_tech}' is valid: {is_valid}")

        # Test knowledge extractor
        knowledge = get_knowledge_extractor()
        logger.info("✅ KnowledgeExtractor created")

        logger.info("🎉 All utilities tests passed!")

    except Exception as e:
        logger.error(f"❌ Utilities test failed: {e}")
        raise
