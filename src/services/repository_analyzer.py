#!/usr/bin/env python3
"""
Repository Analyzer - Codebase Analysis and Intelligence
========================================================

Analyzes imported Git repositories to extract structure, dependencies,
and intelligence for RAG-enhanced interactions.

Features:
- File structure analysis
- Programming language detection
- Dependency extraction
- Documentation parsing
- Code statistics and metrics
- Automatic vectorization for knowledge base
"""

import logging
import os
import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from collections import Counter
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FileAnalysis:
    """Analysis result for a single file."""
    path: str
    relative_path: str
    language: str
    size_bytes: int
    line_count: int
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    comment_ratio: float = 0.0
    complexity_estimate: str = "low"  # low, medium, high
    is_test: bool = False
    is_config: bool = False
    is_documentation: bool = False


@dataclass
class RepositoryAnalysis:
    """Complete analysis of a repository."""
    repo_path: str
    repo_name: str
    repo_owner: str
    total_files: int = 0
    total_size_bytes: int = 0
    total_lines: int = 0

    # Language breakdown
    languages: Dict[str, int] = field(default_factory=dict)  # language -> file count
    primary_language: Optional[str] = None

    # File categorization
    source_files: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    documentation_files: List[str] = field(default_factory=list)

    # Dependencies and framework detection
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # type -> [dependencies]
    frameworks: List[str] = field(default_factory=list)
    build_tools: List[str] = field(default_factory=list)

    # Project structure
    has_readme: bool = False
    has_license: bool = False
    has_tests: bool = False
    has_ci_cd: bool = False
    has_docker: bool = False

    # Architecture insights
    project_type: Optional[str] = None  # web, cli, library, mobile, etc.
    architecture_pattern: Optional[str] = None  # mvc, mvvm, microservices, etc.

    # Detailed file analysis
    file_analyses: List[FileAnalysis] = field(default_factory=list)

    # Timestamps
    analyzed_at: datetime = field(default_factory=datetime.now)


class RepositoryAnalyzer:
    """
    Analyzes Git repositories to extract structure and intelligence.
    """

    # Language detection by file extension
    LANGUAGE_MAP = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JavaScript (React)',
        '.tsx': 'TypeScript (React)',
        '.java': 'Java',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.c': 'C',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.cs': 'C#',
        '.go': 'Go',
        '.rs': 'Rust',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.ps1': 'PowerShell',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.vue': 'Vue',
        '.dart': 'Dart',
        '.lua': 'Lua',
        '.pl': 'Perl',
        '.m': 'Objective-C',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.json': 'JSON',
        '.xml': 'XML',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.tex': 'LaTeX',
    }

    # Config file patterns
    CONFIG_FILES = {
        'package.json', 'package-lock.json', 'yarn.lock',
        'requirements.txt', 'Pipfile', 'Pipfile.lock', 'setup.py', 'setup.cfg', 'pyproject.toml',
        'Cargo.toml', 'Cargo.lock',
        'pom.xml', 'build.gradle', 'build.gradle.kts',
        'Gemfile', 'Gemfile.lock',
        'composer.json', 'composer.lock',
        'go.mod', 'go.sum',
        '.gitignore', '.dockerignore', '.eslintrc', '.prettierrc',
        'tsconfig.json', 'webpack.config.js', 'vite.config.js',
        'docker-compose.yml', 'Dockerfile',
        '.travis.yml', '.gitlab-ci.yml', 'Jenkinsfile', '.github',
    }

    # Documentation file patterns
    DOC_FILES = {
        'README.md', 'README.rst', 'README.txt', 'README',
        'CONTRIBUTING.md', 'LICENSE', 'LICENSE.txt', 'LICENSE.md',
        'CHANGELOG.md', 'CHANGELOG.txt', 'HISTORY.md',
        'docs', 'documentation', 'wiki',
    }

    # Test file patterns
    TEST_PATTERNS = ['test_', '_test.', 'tests/', 'test/', '__tests__/', 'spec/', '.spec.', '.test.']

    def __init__(self):
        """Initialize the repository analyzer."""
        self.ignored_dirs = {
            '.git', '.svn', '.hg', 'node_modules', 'venv', 'env', '.env',
            '__pycache__', '.pytest_cache', '.mypy_cache', '.tox',
            'build', 'dist', 'target', 'out', 'bin', 'obj',
            '.idea', '.vscode', '.vs',
            'vendor', 'deps', 'tmp', 'temp',
        }

        self.max_file_size = 10 * 1024 * 1024  # 10MB

    def analyze_repository(self, repo_path: str, owner: str = "unknown", name: str = "unknown") -> RepositoryAnalysis:
        """
        Analyze a repository and extract intelligence.

        Args:
            repo_path: Path to the cloned repository
            owner: Repository owner/organization
            name: Repository name

        Returns:
            RepositoryAnalysis with complete analysis
        """
        try:
            repo_path = Path(repo_path)
            if not repo_path.exists():
                raise ValueError(f"Repository path does not exist: {repo_path}")

            logger.info(f"Analyzing repository at {repo_path}")

            analysis = RepositoryAnalysis(
                repo_path=str(repo_path),
                repo_name=name,
                repo_owner=owner
            )

            # Analyze all files
            for file_path in self._iterate_files(repo_path):
                file_analysis = self._analyze_file(file_path, repo_path)
                if file_analysis:
                    analysis.file_analyses.append(file_analysis)
                    analysis.total_files += 1
                    analysis.total_size_bytes += file_analysis.size_bytes
                    analysis.total_lines += file_analysis.line_count

                    # Track language
                    lang = file_analysis.language
                    analysis.languages[lang] = analysis.languages.get(lang, 0) + 1

                    # Categorize files
                    if file_analysis.is_test:
                        analysis.test_files.append(file_analysis.relative_path)
                    elif file_analysis.is_config:
                        analysis.config_files.append(file_analysis.relative_path)
                    elif file_analysis.is_documentation:
                        analysis.documentation_files.append(file_analysis.relative_path)
                    else:
                        analysis.source_files.append(file_analysis.relative_path)

            # Determine primary language
            if analysis.languages:
                analysis.primary_language = max(analysis.languages, key=analysis.languages.get)

            # Detect project structure
            self._detect_project_structure(repo_path, analysis)

            # Extract dependencies
            self._extract_dependencies(repo_path, analysis)

            # Detect frameworks and architecture
            self._detect_frameworks_and_architecture(repo_path, analysis)

            logger.info(f"Repository analysis complete: {analysis.total_files} files, "
                       f"{analysis.total_lines} lines, primary language: {analysis.primary_language}")

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze repository {repo_path}: {e}")
            raise

    def _iterate_files(self, repo_path: Path) -> List[Path]:
        """Iterate through all non-ignored files in the repository."""
        files = []

        for root, dirs, filenames in os.walk(repo_path):
            # Remove ignored directories from traversal
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

            for filename in filenames:
                file_path = Path(root) / filename

                # Skip very large files
                try:
                    if file_path.stat().st_size > self.max_file_size:
                        logger.debug(f"Skipping large file: {file_path}")
                        continue
                except:
                    continue

                files.append(file_path)

        return files

    def _analyze_file(self, file_path: Path, repo_root: Path) -> Optional[FileAnalysis]:
        """Analyze a single file."""
        try:
            relative_path = file_path.relative_to(repo_root)
            extension = file_path.suffix.lower()

            # Detect language
            language = self.LANGUAGE_MAP.get(extension, 'Other')

            # Get file size
            size_bytes = file_path.stat().st_size

            # Categorize file type
            is_config = file_path.name in self.CONFIG_FILES or any(
                config in str(relative_path) for config in self.CONFIG_FILES
            )
            is_doc = file_path.name in self.DOC_FILES or any(
                doc in str(relative_path).lower() for doc in ['docs/', 'documentation/', 'wiki/']
            )
            is_test = any(pattern in str(relative_path).lower() for pattern in self.TEST_PATTERNS)

            # Read file content for analysis (text files only)
            line_count = 0
            function_count = 0
            class_count = 0
            import_count = 0
            comment_lines = 0

            if extension in self.LANGUAGE_MAP:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                        line_count = len(lines)

                        # Simple heuristics for code metrics
                        for line in lines:
                            line_stripped = line.strip()

                            # Count comments (simple detection)
                            if line_stripped.startswith(('#', '//', '/*', '*', '"""', "'''")):
                                comment_lines += 1

                            # Count functions/classes/imports (simple patterns)
                            if 'def ' in line or 'function ' in line or 'func ' in line:
                                function_count += 1
                            if 'class ' in line:
                                class_count += 1
                            if line_stripped.startswith(('import ', 'from ', 'require(', 'using ', 'include ')):
                                import_count += 1

                        comment_ratio = comment_lines / line_count if line_count > 0 else 0.0

                except Exception as e:
                    logger.debug(f"Could not read file {file_path}: {e}")

            # Estimate complexity
            complexity = "low"
            if line_count > 500:
                complexity = "high"
            elif line_count > 200:
                complexity = "medium"

            return FileAnalysis(
                path=str(file_path),
                relative_path=str(relative_path),
                language=language,
                size_bytes=size_bytes,
                line_count=line_count,
                function_count=function_count,
                class_count=class_count,
                import_count=import_count,
                comment_ratio=comment_ratio,
                complexity_estimate=complexity,
                is_test=is_test,
                is_config=is_config,
                is_documentation=is_doc
            )

        except Exception as e:
            logger.debug(f"Failed to analyze file {file_path}: {e}")
            return None

    def _detect_project_structure(self, repo_path: Path, analysis: RepositoryAnalysis):
        """Detect project structure flags."""
        # Check for common files
        for item in repo_path.iterdir():
            name_lower = item.name.lower()

            if name_lower.startswith('readme'):
                analysis.has_readme = True
            elif name_lower.startswith('license'):
                analysis.has_license = True
            elif name_lower == 'dockerfile' or name_lower == 'docker-compose.yml':
                analysis.has_docker = True
            elif name_lower in ['.travis.yml', '.gitlab-ci.yml', 'jenkinsfile'] or item.name == '.github':
                analysis.has_ci_cd = True

        # Check for tests
        analysis.has_tests = len(analysis.test_files) > 0

    def _extract_dependencies(self, repo_path: Path, analysis: RepositoryAnalysis):
        """Extract dependencies from config files."""
        # Python dependencies
        req_file = repo_path / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    deps = [line.split('==')[0].split('>=')[0].strip()
                           for line in f if line.strip() and not line.startswith('#')]
                    analysis.dependencies['python'] = deps[:50]  # Limit to first 50
            except:
                pass

        # Node.js dependencies
        package_json = repo_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    deps = list(data.get('dependencies', {}).keys())
                    dev_deps = list(data.get('devDependencies', {}).keys())
                    analysis.dependencies['node'] = (deps + dev_deps)[:50]
            except:
                pass

        # Go dependencies
        go_mod = repo_path / 'go.mod'
        if go_mod.exists():
            try:
                with open(go_mod, 'r') as f:
                    deps = [line.split()[0] for line in f if line.strip().startswith('require')]
                    analysis.dependencies['go'] = deps[:50]
            except:
                pass

    def _detect_frameworks_and_architecture(self, repo_path: Path, analysis: RepositoryAnalysis):
        """Detect frameworks, build tools, and architecture patterns."""
        # Framework detection based on dependencies and file structure
        all_deps = []
        for dep_list in analysis.dependencies.values():
            all_deps.extend([d.lower() for d in dep_list])

        # Python frameworks
        if 'flask' in all_deps:
            analysis.frameworks.append('Flask')
        if 'django' in all_deps:
            analysis.frameworks.append('Django')
        if 'fastapi' in all_deps:
            analysis.frameworks.append('FastAPI')

        # JavaScript frameworks
        if 'react' in all_deps:
            analysis.frameworks.append('React')
        if 'vue' in all_deps:
            analysis.frameworks.append('Vue.js')
        if 'angular' in all_deps or '@angular/core' in all_deps:
            analysis.frameworks.append('Angular')
        if 'express' in all_deps:
            analysis.frameworks.append('Express.js')
        if 'next' in all_deps or 'nextjs' in all_deps:
            analysis.frameworks.append('Next.js')

        # Detect project type
        if any(fw in analysis.frameworks for fw in ['Flask', 'Django', 'FastAPI', 'Express.js', 'Next.js']):
            analysis.project_type = 'web'
        elif (repo_path / 'setup.py').exists() or (repo_path / 'pyproject.toml').exists():
            analysis.project_type = 'library'
        elif (repo_path / 'cli.py').exists() or any('cli' in f.lower() for f in analysis.source_files):
            analysis.project_type = 'cli'

        # Build tools
        if (repo_path / 'Makefile').exists():
            analysis.build_tools.append('Make')
        if (repo_path / 'webpack.config.js').exists():
            analysis.build_tools.append('Webpack')
        if (repo_path / 'vite.config.js').exists() or (repo_path / 'vite.config.ts').exists():
            analysis.build_tools.append('Vite')


# Global instance
_repository_analyzer = None


def get_repository_analyzer() -> RepositoryAnalyzer:
    """Get or create the global RepositoryAnalyzer instance."""
    global _repository_analyzer
    if _repository_analyzer is None:
        _repository_analyzer = RepositoryAnalyzer()
    return _repository_analyzer


__all__ = [
    'RepositoryAnalyzer',
    'RepositoryAnalysis',
    'FileAnalysis',
    'get_repository_analyzer'
]
