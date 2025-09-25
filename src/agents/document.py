"""
Socratic RAG Enhanced - Document Processing Agent
Handles multi-format file processing, GitHub analysis, and knowledge base integration
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import requests
from src.agents.base import BaseAgent
from src.models import KnowledgeEntry
from src.utils import FileProcessor, DocumentParser


class DocumentProcessorAgent(BaseAgent):
    """
    Enhanced document processing agent with knowledge base integration

    Capabilities: Multi-format processing, GitHub analysis, vector storage
    """

    def __init__(self):
        super().__init__("document_processor", "Document Processor")
        self.file_processor = FileProcessor()
        self.doc_parser = DocumentParser()

    def get_capabilities(self) -> List[str]:
        return [
            "process_files", "analyze_repository", "extract_knowledge",
            "chunk_documents", "store_vectors", "search_knowledge",
            "generate_summaries", "extract_code_structure"
        ]

    def _process_files(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process uploaded files and extract knowledge"""
        file_paths = data.get('file_paths', [])
        project_id = data.get('project_id')
        processing_options = data.get('options', {})

        results = {
            'processed_files': [],
            'knowledge_entries': [],
            'errors': []
        }

        for file_path in file_paths:
            try:
                # Process file based on type
                file_result = self.file_processor.process_file(file_path, processing_options)
                results['processed_files'].append(file_result)

                # Extract knowledge entries
                knowledge_entries = self._extract_knowledge_from_file(file_result, project_id)
                results['knowledge_entries'].extend(knowledge_entries)

            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
                results['errors'].append({
                    'file': file_path,
                    'error': str(e)
                })

        # Store knowledge entries in database
        for entry in results['knowledge_entries']:
            self.db.knowledge.create(entry)

        return results

    def _extract_knowledge_from_file(self, file_result: Dict[str, Any], project_id: str) -> List[KnowledgeEntry]:
        """Extract knowledge entries from processed file"""
        knowledge_entries = []

        # Create main knowledge entry for file
        entry = KnowledgeEntry(
            entry_id=f"knowledge_{int(time.time())}_{len(knowledge_entries)}",
            project_id=project_id,
            source_type=file_result.get('file_type', 'unknown'),
            source_path=file_result.get('file_path', ''),
            title=file_result.get('title', 'Untitled'),
            content=file_result.get('content', ''),
            metadata=file_result.get('metadata', {}),
            tags=file_result.get('tags', []),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        knowledge_entries.append(entry)

        # Create additional entries for code structures
        if file_result.get('code_structure'):
            for structure in file_result['code_structure']:
                code_entry = KnowledgeEntry(
                    entry_id=f"code_{int(time.time())}_{len(knowledge_entries)}",
                    project_id=project_id,
                    source_type='code_structure',
                    source_path=file_result.get('file_path', ''),
                    title=f"Code: {structure.get('name', 'Unknown')}",
                    content=structure.get('content', ''),
                    metadata={'structure_type': structure.get('type', 'unknown')},
                    tags=['code', structure.get('type', 'unknown')],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                knowledge_entries.append(code_entry)

        return knowledge_entries

    def _analyze_repository(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze GitHub repository or local directory"""
        repo_path = data.get('repo_path')
        repo_url = data.get('repo_url')
        project_id = data.get('project_id')
        analysis_depth = data.get('depth', 'full')  # full, summary, structure_only

        if repo_url:
            return self._analyze_remote_repository(repo_url, project_id, analysis_depth)
        elif repo_path:
            return self._analyze_local_repository(repo_path, project_id, analysis_depth)
        else:
            raise ValueError("Either repo_path or repo_url must be provided")

    def _analyze_remote_repository(self, repo_url: str, project_id: str, depth: str) -> Dict[str, Any]:
        """Analyze remote GitHub repository"""
        try:
            # Parse repository URL
            parsed_url = urlparse(repo_url)
            if 'github.com' not in parsed_url.netloc:
                raise ValueError("Only GitHub repositories are supported")

            # Extract owner and repo name
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) < 2:
                raise ValueError("Invalid GitHub repository URL")

            owner, repo = path_parts[0], path_parts[1]

            # Use GitHub API to fetch repository information
            repo_info = self._fetch_github_repo_info(owner, repo)

            # Clone or download repository for analysis
            local_path = self._download_repository(repo_url, repo)

            # Analyze the downloaded repository
            analysis = self._analyze_local_repository(local_path, project_id, depth)

            # Add repository metadata
            analysis['repository_info'] = repo_info
            analysis['source_type'] = 'github_repository'
            analysis['repo_url'] = repo_url

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing remote repository {repo_url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'repo_url': repo_url
            }

    def _fetch_github_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository information from GitHub API"""
        try:


            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(api_url, timeout=10)

            if response.status_code == 200:
                repo_data = response.json()
                return {
                    'name': repo_data.get('name'),
                    'description': repo_data.get('description'),
                    'language': repo_data.get('language'),
                    'stars': repo_data.get('stargazers_count'),
                    'forks': repo_data.get('forks_count'),
                    'topics': repo_data.get('topics', []),
                    'created_at': repo_data.get('created_at'),
                    'updated_at': repo_data.get('updated_at')
                }
            else:
                return {'error': f'GitHub API returned {response.status_code}'}

        except Exception as e:
            return {'error': str(e)}

    def _download_repository(self, repo_url: str, repo_name: str) -> str:
        """Download repository to temporary location"""
        import tempfile
        import subprocess

        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix=f"repo_{repo_name}_")

            # Clone repository
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, temp_dir],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")

            return temp_dir

        except Exception as e:
            self.logger.error(f"Error downloading repository: {e}")
            raise

    def _analyze_local_repository(self, repo_path: str, project_id: str, depth: str) -> Dict[str, Any]:
        """Analyze local repository or directory"""
        repo_path = Path(repo_path)

        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        analysis = {
            'repo_path': str(repo_path),
            'analysis_depth': depth,
            'timestamp': datetime.now().isoformat(),
            'file_structure': {},
            'code_files': [],
            'documentation_files': [],
            'config_files': [],
            'test_files': [],
            'total_files': 0,
            'languages_detected': {},
            'knowledge_entries_created': 0
        }

        # Get file structure
        analysis['file_structure'] = self._get_directory_structure(repo_path)

        # Analyze files based on depth
        if depth in ['full', 'summary']:
            self._analyze_repository_files(repo_path, analysis, project_id, depth)

        # Detect languages and technologies
        analysis['languages_detected'] = self._detect_languages(repo_path)

        # Generate summary
        if depth in ['full', 'summary']:
            analysis['summary'] = self._generate_repository_summary(analysis)

        return analysis

    def _get_directory_structure(self, path: Path, max_depth: int = 3, current_depth: int = 0) -> Dict[str, Any]:
        """Get directory structure as nested dictionary"""
        if current_depth > max_depth:
            return {"...": "truncated"}

        structure = {}

        try:
            for item in path.iterdir():
                if item.name.startswith('.') and item.name not in ['.env', '.gitignore', '.dockerignore']:
                    continue

                if item.is_dir():
                    structure[item.name + '/'] = self._get_directory_structure(
                        item, max_depth, current_depth + 1
                    )
                else:
                    structure[item.name] = {
                        'size': item.stat().st_size,
                        'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    }
        except PermissionError:
            structure['error'] = 'Permission denied'

        return structure

    def _analyze_repository_files(self, repo_path: Path, analysis: Dict[str, Any],
                                  project_id: str, depth: str):
        """Analyze files in repository"""
        file_extensions = {
            'code': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go'],
            'documentation': ['.md', '.rst', '.txt', '.pdf', '.doc', '.docx'],
            'config': ['.json', '.yml', '.yaml', '.toml', '.ini', '.cfg', '.xml'],
            'test': ['test_', '_test', '.test.', 'spec_', '_spec', '.spec.']
        }

        knowledge_entries = []

        for file_path in repo_path.rglob('*'):
            if not file_path.is_file():
                continue

            # Skip common ignore patterns
            if any(pattern in str(file_path) for pattern in ['.git/', '__pycache__/', 'node_modules/']):
                continue

            analysis['total_files'] += 1

            # Categorize file
            file_category = self._categorize_file(file_path, file_extensions)

            if file_category:
                analysis[f'{file_category}_files'].append({
                    'path': str(file_path.relative_to(repo_path)),
                    'size': file_path.stat().st_size,
                    'extension': file_path.suffix
                })

            # Process file content if full analysis
            if depth == 'full' and self._should_process_file(file_path):
                try:
                    file_result = self.file_processor.process_file(str(file_path))
                    entries = self._extract_knowledge_from_file(file_result, project_id)
                    knowledge_entries.extend(entries)
                except Exception as e:
                    self.logger.warning(f"Error processing {file_path}: {e}")

        # Store knowledge entries
        for entry in knowledge_entries:
            self.db.knowledge.create(entry)

        analysis['knowledge_entries_created'] = len(knowledge_entries)

    def _categorize_file(self, file_path: Path, file_extensions: Dict[str, List[str]]) -> Optional[str]:
        """Categorize file based on extension and name patterns"""
        file_name = file_path.name.lower()
        file_ext = file_path.suffix.lower()

        # Check test files first (by name pattern)
        for pattern in file_extensions['test']:
            if pattern in file_name:
                return 'test'

        # Check by extension
        for category, extensions in file_extensions.items():
            if category == 'test':
                continue
            if file_ext in extensions:
                return category

        return None

    def _should_process_file(self, file_path: Path) -> bool:
        """Determine if file should be processed for content extraction"""
        # Skip binary files and large files
        if file_path.stat().st_size > 1024 * 1024:  # 1MB limit
            return False

        # Process text-based files
        text_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go',
            '.md', '.rst', '.txt', '.json', '.yml', '.yaml', '.toml', '.ini', '.cfg'
        }

        return file_path.suffix.lower() in text_extensions

    def _detect_languages(self, repo_path: Path) -> Dict[str, int]:
        """Detect programming languages in repository"""
        language_extensions = {
            'Python': ['.py'],
            'JavaScript': ['.js', '.jsx'],
            'TypeScript': ['.ts', '.tsx'],
            'Java': ['.java'],
            'C++': ['.cpp', '.cxx', '.cc'],
            'C': ['.c'],
            'C#': ['.cs'],
            'PHP': ['.php'],
            'Ruby': ['.rb'],
            'Go': ['.go'],
            'Rust': ['.rs'],
            'HTML': ['.html', '.htm'],
            'CSS': ['.css'],
            'Shell': ['.sh', '.bash'],
            'SQL': ['.sql']
        }

        languages = {}

        for file_path in repo_path.rglob('*'):
            if not file_path.is_file():
                continue

            file_ext = file_path.suffix.lower()

            for language, extensions in language_extensions.items():
                if file_ext in extensions:
                    languages[language] = languages.get(language, 0) + 1

        return languages

    def _generate_repository_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate repository analysis summary"""
        summary = {
            'overview': {
                'total_files': analysis['total_files'],
                'code_files': len(analysis['code_files']),
                'documentation_files': len(analysis['documentation_files']),
                'test_files': len(analysis['test_files']),
                'config_files': len(analysis['config_files'])
            },
            'primary_language': max(analysis['languages_detected'].items(),
                                    key=lambda x: x[1])[0] if analysis['languages_detected'] else 'Unknown',
            'technology_stack': list(analysis['languages_detected'].keys()),
            'project_type': self._infer_project_type(analysis),
            'complexity_indicators': self._calculate_complexity_indicators(analysis)
        }

        return summary

    def _infer_project_type(self, analysis: Dict[str, Any]) -> str:
        """Infer project type from analysis"""
        languages = analysis['languages_detected']
        config_files = [f['path'] for f in analysis['config_files']]

        # Web application indicators
        if 'JavaScript' in languages and ('package.json' in str(config_files) or 'HTML' in languages):
            return 'web_application'

        # API/Backend indicators
        elif 'Python' in languages and any('requirements.txt' in f or 'setup.py' in f for f in config_files):
            return 'python_application'

        # Mobile app indicators
        elif 'Java' in languages and 'android' in str(config_files).lower():
            return 'android_application'

        # Data science indicators
        elif 'Python' in languages and any('jupyter' in str(f).lower() or '.ipynb' in str(f) for f in config_files):
            return 'data_science_project'

        else:
            return 'general_software_project'

    def _calculate_complexity_indicators(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate project complexity indicators"""
        return {
            'file_count_complexity': 'high' if analysis['total_files'] > 100 else 'medium' if analysis[
                                                                                                  'total_files'] > 20 else 'low',
            'language_diversity': 'high' if len(analysis['languages_detected']) > 5 else 'medium' if len(
                analysis['languages_detected']) > 2 else 'low',
            'test_coverage_indicator': 'good' if len(analysis['test_files']) > len(
                analysis['code_files']) * 0.3 else 'poor'
        }

    def _extract_knowledge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract knowledge from documents using advanced techniques"""
        content = data.get('content')
        content_type = data.get('content_type', 'text')
        project_id = data.get('project_id')
        extraction_method = data.get('method', 'standard')  # standard, ai_enhanced, structured

        if extraction_method == 'ai_enhanced':
            return self._ai_enhanced_extraction(content, content_type, project_id)
        elif extraction_method == 'structured':
            return self._structured_extraction(content, content_type, project_id)
        else:
            return self._standard_extraction(content, content_type, project_id)

    def _standard_extraction(self, content: str, content_type: str, project_id: str) -> Dict[str, Any]:
        """Standard knowledge extraction"""
        extracted = {
            'method': 'standard',
            'content_type': content_type,
            'extracted_entities': [],
            'key_phrases': [],
            'summary': '',
            'metadata': {}
        }

        # Basic text processing
        if content_type == 'text':
            # Extract key phrases (simplified)
            words = content.split()
            extracted['word_count'] = len(words)
            extracted['summary'] = ' '.join(words[:50]) + '...' if len(words) > 50 else content

            # Simple entity extraction (very basic)
            import re
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
            urls = re.findall(
                r'https?://(?:[a-zA-Z0-9$-_@.&+]|[!*(),]|%[0-9a-fA-F]{2})+',
                content
            )

            extracted['extracted_entities'] = {
                'emails': emails,
                'urls': urls
            }

        return extracted

    def _ai_enhanced_extraction(self, content: str, content_type: str, project_id: str) -> Dict[str, Any]:
        """AI-enhanced knowledge extraction using Claude"""
        prompt = f"""
        Analyze the following {content_type} content and extract key information:

        Content: {content[:2000]}...

        Please extract:
        1. Main topics and themes
        2. Key entities (people, organizations, technologies)
        3. Important concepts and definitions
        4. Action items or requirements if present
        5. A concise summary

        Return as structured JSON.
        """

        try:
            response = self.call_claude(prompt, max_tokens=1000)
            extracted = json.loads(response)
            extracted['method'] = 'ai_enhanced'
            return extracted
        except Exception as e:
            self.logger.error(f"AI extraction failed: {e}")
            # Fallback to standard extraction
            return self._standard_extraction(content, content_type, project_id)

    def _structured_extraction(self, content: str, content_type: str, project_id: str) -> Dict[str, Any]:
        """Structured extraction for specific content types"""
        extracted = {
            'method': 'structured',
            'content_type': content_type,
            'structure': {}
        }

        if content_type == 'code':
            extracted['structure'] = self._extract_code_structure(content)
        elif content_type == 'json':
            try:
                extracted['structure'] = json.loads(content)
            except:
                extracted['structure'] = {'error': 'Invalid JSON'}
        elif content_type == 'markdown':
            extracted['structure'] = self._extract_markdown_structure(content)

        return extracted

    def _extract_code_structure(self, code_content: str) -> Dict[str, Any]:
        """Extract structure from code content"""
        structure = {
            'functions': [],
            'classes': [],
            'imports': [],
            'comments': []
        }

        lines = code_content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            if line.startswith('def '):
                structure['functions'].append({
                    'name': line.split('(')[0].replace('def ', ''),
                    'line': line_num
                })
            elif line.startswith('class '):
                structure['classes'].append({
                    'name': line.split('(')[0].replace('class ', '').rstrip(':'),
                    'line': line_num
                })
            elif line.startswith(('import ', 'from ')):
                structure['imports'].append({
                    'statement': line,
                    'line': line_num
                })
            elif line.startswith('#'):
                structure['comments'].append({
                    'comment': line,
                    'line': line_num
                })

        return structure

    def _extract_markdown_structure(self, markdown_content: str) -> Dict[str, Any]:
        """Extract structure from markdown content"""
        structure = {
            'headings': [],
            'links': [],
            'code_blocks': [],
            'lists': []
        }

        lines = markdown_content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                heading = line.lstrip('#').strip()
                structure['headings'].append({
                    'level': level,
                    'text': heading,
                    'line': line_num
                })
            elif '[' in line and '](' in line:
                # Extract links
                import re
                links = re.findall(r'\[([^/]]+)/]\(([^)]+)\)', line)
                for text, url in links:
                    structure['links'].append({
                        'text': text,
                        'url': url,
                        'line': line_num
                    })

        return structure

    def _chunk_documents(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Chunk documents for vector storage"""
        content = data.get('content')
        chunk_size = data.get('chunk_size', 1000)
        overlap = data.get('overlap', 200)
        chunking_strategy = data.get('strategy', 'fixed_size')  # fixed_size, semantic, paragraph

        if chunking_strategy == 'semantic':
            chunks = self._semantic_chunking(content, chunk_size)
        elif chunking_strategy == 'paragraph':
            chunks = self._paragraph_chunking(content, chunk_size)
        else:
            chunks = self._fixed_size_chunking(content, chunk_size, overlap)

        return {
            'total_chunks': len(chunks),
            'chunks': chunks,
            'strategy': chunking_strategy,
            'chunk_size': chunk_size
        }

    def _fixed_size_chunking(self, content: str, chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """Split content into fixed-size chunks"""
        chunks = []
        start = 0

        while start < len(content):
            end = start + chunk_size
            chunk_text = content[start:end]

            chunks.append({
                'chunk_id': f"chunk_{len(chunks)}",
                'text': chunk_text,
                'start_pos': start,
                'end_pos': end,
                'size': len(chunk_text)
            })

            start = end - overlap

        return chunks

    def _semantic_chunking(self, content: str, target_size: int) -> List[Dict[str, Any]]:
        """Chunk content based on semantic boundaries"""
        # Split by sentences first
        sentences = content.split('. ')
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk + sentence) <= target_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append({
                        'chunk_id': f"chunk_{len(chunks)}",
                        'text': current_chunk.strip(),
                        'size': len(current_chunk)
                    })
                current_chunk = sentence + ". "

        # Add final chunk
        if current_chunk:
            chunks.append({
                'chunk_id': f"chunk_{len(chunks)}",
                'text': current_chunk.strip(),
                'size': len(current_chunk)
            })

        return chunks

    def _paragraph_chunking(self, content: str, max_size: int) -> List[Dict[str, Any]]:
        """Chunk content by paragraphs"""
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            if len(current_chunk + paragraph) <= max_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        'chunk_id': f"chunk_{len(chunks)}",
                        'text': current_chunk.strip(),
                        'size': len(current_chunk)
                    })
                current_chunk = paragraph + "\n\n"

        # Add final chunk
        if current_chunk:
            chunks.append({
                'chunk_id': f"chunk_{len(chunks)}",
                'text': current_chunk.strip(),
                'size': len(current_chunk)
            })

        return chunks

    def _search_knowledge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base using various methods"""
        query = data.get('query')
        project_id = data.get('project_id')
        search_type = data.get('search_type', 'similarity')  # similarity, keyword, hybrid
        max_results = data.get('max_results', 10)

        if search_type == 'similarity':
            results = self._similarity_search(query, project_id, max_results)
        elif search_type == 'keyword':
            results = self._keyword_search(query, project_id, max_results)
        else:
            results = self._hybrid_search(query, project_id, max_results)

        return {
            'query': query,
            'search_type': search_type,
            'results_count': len(results),
            'results': results
        }

    def _similarity_search(self, query: str, project_id: str, max_results: int) -> List[Dict[str, Any]]:
        """Vector similarity search"""
        # This would integrate with vector database (ChromaDB)
        # For now, return placeholder results
        return [
            {
                'entry_id': 'placeholder_1',
                'title': 'Similar content found',
                'content': 'This would be content from vector similarity search',
                'similarity_score': 0.85,
                'source_path': '/path/to/source'
            }
        ]

    def _keyword_search(self, query: str, project_id: str, max_results: int) -> List[Dict[str, Any]]:
        """Keyword-based search"""
        # Get knowledge entries from database
        knowledge_entries = self.db.knowledge.get_by_project_id(project_id)

        results = []
        query_terms = query.lower().split()

        for entry in knowledge_entries:
            # Simple keyword matching
            content_lower = entry.content.lower()
            matches = sum(1 for term in query_terms if term in content_lower)

            if matches > 0:
                results.append({
                    'entry_id': entry.entry_id,
                    'title': entry.title,
                    'content': entry.content[:200] + '...' if len(entry.content) > 200 else entry.content,
                    'match_score': matches / len(query_terms),
                    'source_path': entry.source_path
                })

        # Sort by match score
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:max_results]

    def _hybrid_search(self, query: str, project_id: str, max_results: int) -> List[Dict[str, Any]]:
        """Hybrid search combining similarity and keyword search"""
        similarity_results = self._similarity_search(query, project_id, max_results // 2)
        keyword_results = self._keyword_search(query, project_id, max_results // 2)

        # Combine and deduplicate results
        combined_results = similarity_results + keyword_results

        # Simple deduplication by entry_id
        seen_ids = set()
        unique_results = []

        for result in combined_results:
            if result['entry_id'] not in seen_ids:
                seen_ids.add(result['entry_id'])
                unique_results.append(result)

        return unique_results[:max_results]

    def _generate_summaries(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summaries from document content"""
        content = data.get('content')
        summary_type = data.get('type', 'extractive')  # extractive, abstractive, bullet_points
        length = data.get('length', 'medium')  # short, medium, long

        if summary_type == 'abstractive':
            return self._generate_abstractive_summary(content, length)
        elif summary_type == 'bullet_points':
            return self._generate_bullet_summary(content, length)
        else:
            return self._generate_extractive_summary(content, length)

    def _generate_extractive_summary(self, content: str, length: str) -> Dict[str, Any]:
        """Generate extractive summary by selecting key sentences"""
        sentences = content.split('. ')

        # Simple scoring based on word frequency
        word_freq = {}
        for sentence in sentences:
            words = sentence.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1

        # Score sentences
        sentence_scores = []
        for i, sentence in enumerate(sentences):
            words = sentence.lower().split()
            score = sum(word_freq.get(word, 0) for word in words if len(word) > 3)
            sentence_scores.append((score, i, sentence))

        # Select top sentences
        length_map = {'short': 3, 'medium': 5, 'long': 8}
        top_count = length_map.get(length, 5)

        top_sentences = sorted(sentence_scores, key=lambda x: x[0], reverse=True)[:top_count]
        top_sentences.sort(key=lambda x: x[1])  # Sort by original order

        summary = '. '.join([sentence for _, _, sentence in top_sentences])

        return {
            'summary_type': 'extractive',
            'length': length,
            'summary': summary,
            'sentence_count': len(top_sentences),
            'compression_ratio': len(summary) / len(content)
        }

    def _generate_abstractive_summary(self, content: str, length: str) -> Dict[str, Any]:
        """Generate abstractive summary using AI"""
        length_instructions = {
            'short': 'in 2-3 sentences',
            'medium': 'in 1 paragraph',
            'long': 'in 2-3 paragraphs'
        }

        prompt = f"""
        Please provide a concise summary of the following content {length_instructions.get(length, 'in 1 paragraph')}:

        {content[:3000]}...

        Focus on the main points and key information.
        """

        try:
            summary = self.call_claude(prompt, max_tokens=500)
            return {
                'summary_type': 'abstractive',
                'length': length,
                'summary': summary,
                'compression_ratio': len(summary) / len(content)
            }
        except Exception as e:
            # Fallback to extractive summary
            return self._generate_extractive_summary(content, length)

    def _generate_bullet_summary(self, content: str, length: str) -> Dict[str, Any]:
        """Generate bullet point summary"""
        prompt = f"""
        Create a bullet point summary of the following content. Include the most important points only:

        {content[:2000]}...

        Format as bullet points with key insights.
        """

        try:
            summary = self.call_claude(prompt, max_tokens=300)
            return {
                'summary_type': 'bullet_points',
                'length': length,
                'summary': summary,
                'compression_ratio': len(summary) / len(content)
            }
        except Exception as e:
            # Simple fallback bullet points
            sentences = content.split('. ')[:10]
            bullet_points = '\n'.join(f"• {sentence}" for sentence in sentences[:5])

            return {
                'summary_type': 'bullet_points',
                'length': length,
                'summary': bullet_points,
                'compression_ratio': len(bullet_points) / len(content)
            }
