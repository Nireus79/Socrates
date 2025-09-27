#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Utility Classes
======================================

Comprehensive utility classes for file processing, document parsing, and system operations.
Provides support for multiple file formats and advanced text processing capabilities.
"""

import os
import re
import json
import logging
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

# Import for document processing
try:
    import PyPDF2

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import docx

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Core imports
from .core import get_logger, SocraticException, ValidationError

logger = get_logger('utils')


# ============================================================================
# FILE PROCESSOR CLASS
# ============================================================================

class FileProcessor:
    """File processing utilities for various operations"""

    def __init__(self):
        self.logger = get_logger('file_processor')
        self.temp_dir = Path("data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def process_upload(self, file_path: Union[str, Path], project_id: str = None) -> Dict[str, Any]:
        """Process uploaded file and return metadata"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file info
        file_info = {
            'original_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'file_type': file_path.suffix.lower(),
            'mime_type': self._get_mime_type(file_path),
            'upload_time': datetime.datetime.now().isoformat(),
            'project_id': project_id
        }

        # Validate file
        validation = self.validate_file(file_path)
        file_info.update(validation)

        return file_info

    def validate_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Validate uploaded file"""
        file_path = Path(file_path)

        # Size limits (in bytes)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            validation['is_valid'] = False
            validation['errors'].append(f"File too large: {file_size / (1024 * 1024):.1f}MB (max: 50MB)")

        # Check file type
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.json', '.csv', '.xlsx', '.xls'}
        if file_path.suffix.lower() not in allowed_extensions:
            validation['warnings'].append(f"File type {file_path.suffix} may not be fully supported")

        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1024)  # Try to read first 1KB
        except Exception as e:
            validation['is_valid'] = False
            validation['errors'].append(f"File is not readable: {e}")

        return validation

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type based on file extension"""
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.json': 'application/json',
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel'
        }
        return mime_types.get(file_path.suffix.lower(), 'application/octet-stream')

    def save_processed_file(self, content: str, filename: str, project_id: str = None) -> Path:
        """Save processed content to file"""
        if project_id:
            save_dir = self.temp_dir / project_id
        else:
            save_dir = self.temp_dir

        save_dir.mkdir(parents=True, exist_ok=True)

        # Create safe filename
        safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        file_path = save_dir / safe_filename

        # Write content
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Saved processed file: {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"Failed to save file: {e}")
            raise SocraticException(f"Failed to save processed file: {e}")

    def cleanup_temp_files(self, project_id: str = None, older_than_hours: int = 24):
        """Clean up old temporary files"""
        if project_id:
            cleanup_dir = self.temp_dir / project_id
        else:
            cleanup_dir = self.temp_dir

        if not cleanup_dir.exists():
            return

        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=older_than_hours)
        deleted_count = 0

        try:
            for file_path in cleanup_dir.rglob('*'):
                if file_path.is_file():
                    file_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1

            self.logger.info(f"Cleaned up {deleted_count} temporary files")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def extract_text_preview(self, file_path: Union[str, Path], max_length: int = 500) -> str:
        """Extract a text preview from file"""
        try:
            parser = DocumentParser()
            result = parser.parse_document(file_path)

            content = result.get('content', '')
            if len(content) <= max_length:
                return content

            # Truncate at word boundary
            truncated = content[:max_length]
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.8:  # If we can find a space in the last 20%
                truncated = truncated[:last_space]

            return truncated + "..."

        except Exception as e:
            self.logger.error(f"Failed to extract preview: {e}")
            return f"[Preview unavailable: {e}]"


# ============================================================================
# DOCUMENT PARSER CLASS
# ============================================================================

class DocumentParser:
    """Advanced document parser for multiple file formats"""

    def __init__(self):
        self.logger = get_logger('document_parser')
        self.supported_formats = self._get_supported_formats()

    def _get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        formats = ['.txt', '.md', '.json', '.csv']

        if PDF_AVAILABLE:
            formats.append('.pdf')
        if DOCX_AVAILABLE:
            formats.extend(['.docx', '.doc'])
        if PANDAS_AVAILABLE:
            formats.extend(['.xlsx', '.xls'])

        return formats

    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if file format is supported"""
        file_path = Path(file_path)
        return file_path.suffix.lower() in self.supported_formats

    def parse_document(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Parse document and extract content and metadata"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.can_parse(file_path):
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        try:
            # Get file info
            file_info = self._get_file_info(file_path)

            # Parse content based on file type
            content_data = self._parse_by_type(file_path)

            # Combine results
            result = {
                **file_info,
                **content_data,
                'parsing_success': True,
                'parsed_at': datetime.datetime.now().isoformat()
            }

            self.logger.info(f"Successfully parsed: {file_path}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to parse {file_path}: {e}")
            return {
                'file_path': str(file_path),
                'parsing_success': False,
                'error': str(e),
                'content': '',
                'metadata': {}
            }

    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get basic file information"""
        stat = file_path.stat()

        return {
            'file_path': str(file_path),
            'filename': file_path.name,
            'file_type': file_path.suffix.lower(),
            'file_size': stat.st_size,
            'created_at': datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'file_hash': self._calculate_file_hash(file_path)
        }

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _parse_by_type(self, file_path: Path) -> Dict[str, Any]:
        """Parse content based on file type"""
        extension = file_path.suffix.lower()

        if extension == '.pdf':
            return self._parse_pdf(file_path)
        elif extension in ['.docx', '.doc']:
            return self._parse_docx(file_path)
        elif extension in ['.txt', '.md']:
            return self._parse_text(file_path)
        elif extension == '.json':
            return self._parse_json(file_path)
        elif extension == '.csv':
            return self._parse_csv(file_path)
        elif extension in ['.xlsx', '.xls']:
            return self._parse_excel(file_path)
        else:
            return self._parse_text(file_path)  # Fallback to text

    def _parse_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Parse PDF document"""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 not available. Install with: pip install PyPDF2")

        content = ""
        metadata = {}

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract metadata
                if pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'creation_date': str(pdf_reader.metadata.get('/CreationDate', '')),
                        'modification_date': str(pdf_reader.metadata.get('/ModDate', ''))
                    }

                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        self.logger.warning(f"Could not extract text from page {page_num + 1}: {e}")

                metadata['page_count'] = len(pdf_reader.pages)

        except Exception as e:
            raise SocraticException(f"Failed to parse PDF: {e}")

        return {
            'content': content.strip(),
            'metadata': metadata,
            'word_count': len(content.split()) if content else 0,
            'char_count': len(content) if content else 0
        }

    def _parse_docx(self, file_path: Path) -> Dict[str, Any]:
        """Parse DOCX document"""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not available. Install with: pip install python-docx")

        try:
            doc = docx.Document(file_path)

            # Extract text
            content = "\n".join([paragraph.text for paragraph in doc.paragraphs])

            # Extract metadata
            metadata = {
                'title': doc.core_properties.title or '',
                'author': doc.core_properties.author or '',
                'subject': doc.core_properties.subject or '',
                'comments': doc.core_properties.comments or '',
                'created': str(doc.core_properties.created) if doc.core_properties.created else '',
                'modified': str(doc.core_properties.modified) if doc.core_properties.modified else '',
                'paragraph_count': len(doc.paragraphs)
            }

            return {
                'content': content,
                'metadata': metadata,
                'word_count': len(content.split()) if content else 0,
                'char_count': len(content) if content else 0
            }

        except Exception as e:
            raise SocraticException(f"Failed to parse DOCX: {e}")

    def _parse_text(self, file_path: Path) -> Dict[str, Any]:
        """Parse plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Basic text analysis
            lines = content.split('\n')
            words = content.split()

            metadata = {
                'line_count': len(lines),
                'paragraph_count': len([line for line in lines if line.strip()]),
                'encoding': 'utf-8'
            }

            return {
                'content': content,
                'metadata': metadata,
                'word_count': len(words),
                'char_count': len(content)
            }

        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()

                    metadata = {'encoding': encoding, 'line_count': len(content.split('\n'))}
                    return {
                        'content': content,
                        'metadata': metadata,
                        'word_count': len(content.split()),
                        'char_count': len(content)
                    }
                except UnicodeDecodeError:
                    continue

            raise SocraticException(f"Could not decode text file: {file_path}")

    def _parse_json(self, file_path: Path) -> Dict[str, Any]:
        """Parse JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Convert to string for content
            content = json.dumps(data, indent=2, ensure_ascii=False)

            metadata = {
                'json_type': type(data).__name__,
                'top_level_keys': list(data.keys()) if isinstance(data, dict) else [],
                'item_count': len(data) if isinstance(data, (list, dict)) else 1
            }

            return {
                'content': content,
                'metadata': metadata,
                'structured_data': data,
                'word_count': len(content.split()),
                'char_count': len(content)
            }

        except Exception as e:
            raise SocraticException(f"Failed to parse JSON: {e}")

    def _parse_csv(self, file_path: Path) -> Dict[str, Any]:
        """Parse CSV file"""
        if not PANDAS_AVAILABLE:
            # Fallback to basic CSV parsing
            import csv
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    rows = list(reader)

                content = '\n'.join([','.join(row) for row in rows])
                metadata = {
                    'row_count': len(rows),
                    'column_count': len(rows[0]) if rows else 0,
                    'headers': rows[0] if rows else []
                }

                return {
                    'content': content,
                    'metadata': metadata,
                    'structured_data': rows,
                    'word_count': len(content.split()),
                    'char_count': len(content)
                }
            except Exception as e:
                raise SocraticException(f"Failed to parse CSV: {e}")

        try:
            df = pd.read_csv(file_path)

            # Convert to string representation
            content = df.to_string()

            metadata = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'null_counts': df.isnull().sum().to_dict()
            }

            return {
                'content': content,
                'metadata': metadata,
                'structured_data': df.to_dict('records'),
                'word_count': len(content.split()),
                'char_count': len(content)
            }

        except Exception as e:
            raise SocraticException(f"Failed to parse CSV: {e}")

    def _parse_excel(self, file_path: Path) -> Dict[str, Any]:
        """Parse Excel file"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas not available. Install with: pip install pandas openpyxl")

        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            all_content = ""
            all_data = {}
            total_rows = 0

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheet_content = f"\n--- Sheet: {sheet_name} ---\n{df.to_string()}\n"
                all_content += sheet_content
                all_data[sheet_name] = df.to_dict('records')
                total_rows += len(df)

            metadata = {
                'sheet_names': excel_file.sheet_names,
                'sheet_count': len(excel_file.sheet_names),
                'total_rows': total_rows
            }

            return {
                'content': all_content,
                'metadata': metadata,
                'structured_data': all_data,
                'word_count': len(all_content.split()),
                'char_count': len(all_content)
            }

        except Exception as e:
            raise SocraticException(f"Failed to parse Excel: {e}")

    def extract_keywords(self, content: str, max_keywords: int = 20) -> List[str]:
        """Extract keywords from content"""
        if not content:
            return []

        # Simple keyword extraction (can be enhanced with NLP libraries)
        words = re.findall(r'\b\w{3,}\b', content.lower())

        # Filter out common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our',
            'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two',
            'who', 'boy', 'did', 'she', 'use', 'way', 'what', 'said', 'each', 'which', 'their', 'time', 'will',
            'about', 'after', 'back', 'other', 'many', 'than', 'then', 'them', 'these', 'some', 'would', 'like'
        }

        # Count word frequency
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]

    def chunk_content(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Split content into overlapping chunks"""
        if not content or len(content) <= chunk_size:
            return [{
                'chunk_index': 0,
                'content': content,
                'start_pos': 0,
                'end_pos': len(content),
                'word_count': len(content.split()) if content else 0
            }]

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(content):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(content):
                for i in range(end, max(start + chunk_size - 200, start + 1), -1):
                    if content[i - 1] in '.!?':
                        end = i
                        break
                else:
                    # Break at word boundary
                    for i in range(end, max(start + chunk_size - 100, start + 1), -1):
                        if content[i].isspace():
                            end = i
                            break

            chunk_content = content[start:end].strip()
            if chunk_content:
                chunks.append({
                    'chunk_index': chunk_index,
                    'content': chunk_content,
                    'start_pos': start,
                    'end_pos': end,
                    'word_count': len(chunk_content.split())
                })
                chunk_index += 1

            start = end - overlap
            if start <= 0:
                start = end

        return chunks


# ============================================================================
# TEXT PROCESSOR CLASS
# ============================================================================

class TextProcessor:
    """Advanced text processing utilities"""

    def __init__(self):
        self.logger = get_logger('text_processor')

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)

        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")

        return text.strip()

    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        if not text:
            return []

        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def get_text_stats(self, text: str) -> Dict[str, Any]:
        """Get comprehensive text statistics"""
        if not text:
            return {
                'char_count': 0,
                'word_count': 0,
                'sentence_count': 0,
                'paragraph_count': 0,
                'avg_words_per_sentence': 0,
                'reading_time_minutes': 0
            }

        words = text.split()
        sentences = self.extract_sentences(text)
        paragraphs = [p for p in text.split('\n\n') if p.strip()]

        return {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),
            'avg_words_per_sentence': len(words) / len(sentences) if sentences else 0,
            'reading_time_minutes': len(words) / 200  # Assume 200 WPM reading speed
        }


# ============================================================================
# CODE ANALYZER CLASS
# ============================================================================

class CodeAnalyzer:
    """Code analysis and quality assessment utilities"""

    def __init__(self):
        self.logger = get_logger('code_analyzer')

    def analyze_code_quality(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Analyze code quality metrics"""
        if not code:
            return {'quality_score': 0, 'issues': ['No code provided']}

        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        analysis = {
            'total_lines': len(lines),
            'code_lines': len(non_empty_lines),
            'complexity_score': self._calculate_complexity(code, language),
            'maintainability_score': 0,
            'issues': [],
            'suggestions': []
        }

        # Check for common issues
        analysis['issues'].extend(self._check_code_issues(code, language))

        # Calculate maintainability
        analysis['maintainability_score'] = max(0, 100 - (analysis['complexity_score'] * 10))

        return analysis

    def _calculate_complexity(self, code: str, language: str) -> float:
        """Calculate cyclomatic complexity"""
        complexity_keywords = {
            'python': ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with'],
            'javascript': ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch'],
            'java': ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch']
        }

        keywords = complexity_keywords.get(language.lower(), complexity_keywords['python'])
        complexity = 0

        for line in code.split('\n'):
            line = line.strip().lower()
            for keyword in keywords:
                if keyword in line:
                    complexity += 1

        return min(complexity / max(len(code.split('\n')), 1) * 10, 10.0)

    def _check_code_issues(self, code: str, language: str) -> List[str]:
        """Check for common code issues"""
        issues = []

        if language.lower() == 'python':
            # Check for Python-specific issues
            if 'eval(' in code:
                issues.append('Use of eval() function (security risk)')
            if 'exec(' in code:
                issues.append('Use of exec() function (security risk)')
            if len([line for line in code.split('\n') if len(line) > 100]) > 0:
                issues.append('Lines longer than 100 characters detected')

        return issues


# ============================================================================
# EXTENDED VALIDATOR CLASS
# ============================================================================

class ExtendedValidator:
    """Extended validation utilities beyond core validation"""

    def __init__(self):
        self.logger = get_logger('extended_validator')

    def validate_project_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate project specification"""
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        required_fields = ['name', 'description', 'requirements']
        for field in required_fields:
            if not spec.get(field):
                validation['is_valid'] = False
                validation['errors'].append(f"Missing required field: {field}")

        # Validate requirements format
        requirements = spec.get('requirements', [])
        if not isinstance(requirements, list):
            validation['warnings'].append("Requirements should be a list")

        return validation

    def validate_file_content(self, content: str, file_type: str) -> Dict[str, Any]:
        """Validate file content based on type"""
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        if file_type == 'json':
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                validation['is_valid'] = False
                validation['errors'].append(f"Invalid JSON: {e}")

        elif file_type == 'python':
            try:
                compile(content, '<string>', 'exec')
            except SyntaxError as e:
                validation['is_valid'] = False
                validation['errors'].append(f"Python syntax error: {e}")

        return validation


# ============================================================================
# KNOWLEDGE EXTRACTOR CLASS
# ============================================================================

class KnowledgeExtractor:
    """Extract knowledge and insights from conversations and documents"""

    def __init__(self):
        self.logger = get_logger('knowledge_extractor')

    def extract_insights(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract insights from Socratic conversation"""
        insights = {
            'key_requirements': [],
            'technical_decisions': [],
            'user_preferences': [],
            'potential_conflicts': [],
            'recommended_actions': []
        }

        for message in conversation:
            content = message.get('content', '').lower()

            # Simple pattern matching for insights
            if any(word in content for word in ['must', 'required', 'need']):
                insights['key_requirements'].append(message.get('content', ''))

            if any(word in content for word in ['prefer', 'like', 'want']):
                insights['user_preferences'].append(message.get('content', ''))

            if any(word in content for word in ['conflict', 'issue', 'problem']):
                insights['potential_conflicts'].append(message.get('content', ''))

        return insights

    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text"""
        # Simple entity extraction using regex patterns
        entities = []

        # Extract potential technology names
        tech_pattern = r'\b(React|Angular|Vue|Django|Flask|Node|Python|Java|JavaScript)\b'
        entities.extend(re.findall(tech_pattern, text, re.IGNORECASE))

        # Extract potential database names
        db_pattern = r'\b(MySQL|PostgreSQL|MongoDB|SQLite|Redis|Oracle)\b'
        entities.extend(re.findall(db_pattern, text, re.IGNORECASE))

        return list(set(entities))


def validate_project_data(project_data: Dict[str, Any]) -> List[str]:
    """Validate project data dictionary"""
    issues = []

    if not isinstance(project_data, dict):
        return ["Project data must be a dictionary"]

    # Required fields
    required_fields = ['name', 'owner_id']
    for field in required_fields:
        if field not in project_data or not project_data[field]:
            issues.append(f"Required field '{field}' is missing or empty")

    # Basic validation
    if 'name' in project_data:
        name = project_data['name']
        if not name or len(name.strip()) < 2:
            issues.append("Project name must be at least 2 characters long")

    return issues


def validate_file_upload(file_info: Dict[str, Any]) -> List[str]:
    """Validate uploaded file information"""
    issues = []

    try:
        # Required fields
        required_fields = ['filename', 'content_type', 'size']
        for field in required_fields:
            if field not in file_info:
                issues.append(f"Missing required field: {field}")

        # File size validation (10MB limit)
        if 'size' in file_info:
            size = file_info['size']
            if not isinstance(size, (int, float)):
                issues.append("File size must be a number")
            elif size > 10 * 1024 * 1024:  # 10MB
                issues.append(f"File too large: {size} bytes (max 10MB)")
            elif size <= 0:
                issues.append("File is empty")

        # Filename validation
        if 'filename' in file_info:
            filename = file_info['filename']
            if not filename or len(filename.strip()) == 0:
                issues.append("Filename cannot be empty")
            elif len(filename) > 255:
                issues.append("Filename too long (max 255 characters)")

            # Check for dangerous file extensions
            dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.vbs']
            ext = Path(filename).suffix.lower()
            if ext in dangerous_extensions:
                issues.append(f"Potentially dangerous file type: {ext}")

        # Content type validation
        if 'content_type' in file_info:
            content_type = file_info['content_type']
            allowed_types = [
                'text/plain', 'text/markdown', 'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/json', 'text/html', 'text/css', 'application/javascript',
                'text/x-python', 'application/x-python-code'
            ]

            if content_type not in allowed_types and not content_type.startswith('text/'):
                issues.append(f"Unsupported file type: {content_type}")

        return issues

    except Exception as e:
        logger.error(f"File upload validation failed: {e}")
        return [f"Validation error: {str(e)}"]
# ============================================================================
# MODULE EXPORTS
# ============================================================================

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
    'get_validator', 'get_knowledge_extractor',

    # Validation functions
    'validate_project_data'
]

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # Test utilities
    print("Testing utility classes...")

    try:
        # Test DocumentParser
        parser = DocumentParser()
        print(f"✅ DocumentParser initialized - Supported formats: {parser.supported_formats}")

        # Test FileProcessor
        processor = FileProcessor()
        print("✅ FileProcessor initialized")

        # Test TextProcessor
        text_proc = TextProcessor()
        sample_text = "This is a test. It has multiple sentences! How exciting?"
        stats = text_proc.get_text_stats(sample_text)
        print(f"✅ TextProcessor working - Sample stats: {stats}")

        print("🎉 All utility classes working!")

    except Exception as e:
        print(f"❌ Utility test failed: {e}")
        raise
