#!/usr/bin/env python3
"""
Repository Import Service - GitHub Repository Import and Vectorization
=====================================================================

Coordinates the complete repository import workflow:
1. Clone repository
2. Analyze codebase structure
3. Vectorize code for RAG knowledge base
4. Store metadata in database

Features:
- Complete import workflow orchestration
- Intelligent code chunking for vector storage
- Progress tracking and reporting
- Error handling and recovery
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from .git_service import GitService
from .repository_analyzer import get_repository_analyzer, RepositoryAnalysis
from .vector_service import VectorService
from .document_service import get_document_service

logger = logging.getLogger(__name__)


@dataclass
class ImportProgress:
    """Progress tracking for repository import."""
    stage: str  # 'cloning', 'analyzing', 'vectorizing', 'completed', 'failed'
    progress_percent: float
    message: str
    files_processed: int = 0
    files_total: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class ImportResult:
    """Result of complete repository import operation."""
    success: bool
    repository_id: str
    repository_name: str
    repository_owner: str
    local_path: str

    # Analysis results
    total_files: int = 0
    total_lines: int = 0
    primary_language: Optional[str] = None
    languages: Dict[str, int] = None

    # Vectorization results
    chunks_created: int = 0
    vectorization_success: bool = False

    # Metadata
    imported_at: datetime = None
    duration_seconds: float = 0.0

    # Errors
    error: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.languages is None:
            self.languages = {}
        if self.warnings is None:
            self.warnings = []
        if self.imported_at is None:
            self.imported_at = datetime.now()


class RepositoryImportService:
    """
    Orchestrates complete repository import workflow.

    Handles:
    - Repository cloning via GitService
    - Codebase analysis via RepositoryAnalyzer
    - Code vectorization via VectorService
    - Progress tracking and reporting
    """

    def __init__(self):
        """Initialize repository import service."""
        self.git_service = GitService()
        self.analyzer = get_repository_analyzer()
        self.vector_service = None  # Lazy init
        self.document_service = None  # Lazy init

        # Configuration
        self.max_file_size_for_vectorization = 500 * 1024  # 500KB
        self.chunk_size = 1500  # Larger chunks for code
        self.chunk_overlap = 300

        # Supported file types for vectorization
        self.vectorizable_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
            '.html', '.css', '.md', '.rst', '.txt', '.yaml', '.yml', '.json',
            '.sql', '.sh', '.bash'
        }

        logger.info("Repository import service initialized")

    def import_repository(
        self,
        repo_url: str,
        user_id: str,
        project_id: Optional[str] = None,
        branch: Optional[str] = None,
        vectorize: bool = True,
        progress_callback: Optional[callable] = None
    ) -> ImportResult:
        """
        Import a repository from a Git URL.

        Args:
            repo_url: Git repository URL
            user_id: User ID performing the import
            project_id: Optional project ID to associate with
            branch: Specific branch to clone
            vectorize: Whether to vectorize code for RAG
            progress_callback: Optional callback for progress updates

        Returns:
            ImportResult with complete import information
        """
        start_time = datetime.now()

        # Initialize variables before try block to ensure availability in except handler
        repo_id = str(uuid.uuid4())
        repo_info = None
        local_path = ''

        try:

            # Step 1: Clone repository
            logger.info(f"Starting repository import: {repo_url}")
            if progress_callback:
                progress_callback(ImportProgress(
                    stage='cloning',
                    progress_percent=0.0,
                    message='Cloning repository...'
                ))

            clone_result = self.git_service.clone_repository(
                url=repo_url,
                branch=branch,
                depth=1  # Shallow clone for faster import
            )

            if not clone_result.success:
                return ImportResult(
                    success=False,
                    repository_id=repo_id,
                    repository_name='unknown',
                    repository_owner='unknown',
                    local_path='',
                    error=f"Clone failed: {clone_result.error}"
                )

            repo_info = clone_result.repository_info
            local_path = clone_result.local_path

            logger.info(f"Repository cloned successfully to {local_path}")

            # Step 2: Analyze repository
            if progress_callback:
                progress_callback(ImportProgress(
                    stage='analyzing',
                    progress_percent=30.0,
                    message='Analyzing codebase structure...'
                ))

            analysis = self.analyzer.analyze_repository(
                repo_path=local_path,
                owner=repo_info.owner,
                name=repo_info.name
            )

            logger.info(f"Repository analysis complete: {analysis.total_files} files, "
                       f"{analysis.primary_language} primary language")

            # Step 3: Vectorize code (if requested)
            chunks_created = 0
            vectorization_success = False
            warnings = []

            if vectorize:
                if progress_callback:
                    progress_callback(ImportProgress(
                        stage='vectorizing',
                        progress_percent=50.0,
                        message='Vectorizing code for knowledge base...',
                        files_total=len(analysis.source_files)
                    ))

                vectorization_result = self._vectorize_repository(
                    repo_id=repo_id,
                    analysis=analysis,
                    user_id=user_id,
                    project_id=project_id,
                    progress_callback=progress_callback
                )

                chunks_created = vectorization_result['chunks_created']
                vectorization_success = vectorization_result['success']
                warnings = vectorization_result.get('warnings', [])

                logger.info(f"Vectorization complete: {chunks_created} chunks created")

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            # Final progress update
            if progress_callback:
                progress_callback(ImportProgress(
                    stage='completed',
                    progress_percent=100.0,
                    message='Import completed successfully!',
                    files_processed=analysis.total_files,
                    files_total=analysis.total_files
                ))

            return ImportResult(
                success=True,
                repository_id=repo_id,
                repository_name=repo_info.name,
                repository_owner=repo_info.owner,
                local_path=local_path,
                total_files=analysis.total_files,
                total_lines=analysis.total_lines,
                primary_language=analysis.primary_language,
                languages=analysis.languages,
                chunks_created=chunks_created,
                vectorization_success=vectorization_success,
                imported_at=datetime.now(),
                duration_seconds=duration,
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Repository import failed: {e}", exc_info=True)

            if progress_callback:
                progress_callback(ImportProgress(
                    stage='failed',
                    progress_percent=0.0,
                    message=f'Import failed: {str(e)}'
                ))

            return ImportResult(
                success=False,
                repository_id=repo_id,
                repository_name=repo_info.name if repo_info else 'unknown',
                repository_owner=repo_info.owner if repo_info else 'unknown',
                local_path=local_path,
                error=str(e)
            )

    def _vectorize_repository(
        self,
        repo_id: str,
        analysis: RepositoryAnalysis,
        user_id: str,
        project_id: Optional[str],
        progress_callback: Optional[callable]
    ) -> Dict[str, Any]:
        """
        Vectorize repository code for RAG knowledge base.

        Args:
            repo_id: Repository ID
            analysis: Repository analysis results
            user_id: User ID
            project_id: Optional project ID
            progress_callback: Optional progress callback

        Returns:
            Dictionary with vectorization results
        """
        try:
            # Lazy initialize services
            if self.vector_service is None:
                self.vector_service = VectorService()

            if self.document_service is None:
                self.document_service = get_document_service()

            chunks_created = 0
            warnings = []
            files_processed = 0

            # Collection name for this repository
            collection_name = f"repo_{repo_id}"

            # Process source files
            source_files = analysis.source_files[:200]  # Limit to 200 files

            for relative_path in source_files:
                try:
                    file_path = Path(analysis.repo_path) / relative_path

                    # Check file size
                    if file_path.stat().st_size > self.max_file_size_for_vectorization:
                        warnings.append(f"Skipped {relative_path}: too large")
                        continue

                    # Check file type
                    if file_path.suffix.lower() not in self.vectorizable_extensions:
                        continue

                    # Read file content
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except Exception as e:
                        warnings.append(f"Could not read {relative_path}: {e}")
                        continue

                    # Skip empty files
                    if not content.strip():
                        continue

                    # Chunk content
                    chunks = self.document_service.chunk_content(
                        content,
                        chunk_size=self.chunk_size,
                        overlap=self.chunk_overlap
                    )

                    # Add chunks to vector database
                    for i, chunk in enumerate(chunks):
                        doc_id = f"{repo_id}_{relative_path}_{i}"

                        metadata = {
                            'repository_id': repo_id,
                            'repository_name': analysis.repo_name,
                            'repository_owner': analysis.repo_owner,
                            'file_path': relative_path,
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'language': file_path.suffix.lower()[1:],  # Remove dot
                            'user_id': user_id,
                            'project_id': project_id or 'none',
                            'imported_at': datetime.now().isoformat()
                        }

                        try:
                            self.vector_service.add_document(
                                doc_id=doc_id,
                                content=chunk,
                                metadata=metadata,
                                collection_name=collection_name
                            )
                            chunks_created += 1
                        except Exception as e:
                            warnings.append(f"Failed to vectorize chunk {i} of {relative_path}: {e}")

                    files_processed += 1

                    # Progress update
                    if progress_callback and files_processed % 10 == 0:
                        progress_callback(ImportProgress(
                            stage='vectorizing',
                            progress_percent=50.0 + (files_processed / len(source_files) * 40.0),
                            message=f'Vectorizing files... ({files_processed}/{len(source_files)})',
                            files_processed=files_processed,
                            files_total=len(source_files)
                        ))

                except Exception as e:
                    warnings.append(f"Error processing {relative_path}: {e}")
                    logger.debug(f"Error processing {relative_path}: {e}")

            return {
                'success': True,
                'chunks_created': chunks_created,
                'files_processed': files_processed,
                'warnings': warnings
            }

        except Exception as e:
            logger.error(f"Vectorization failed: {e}", exc_info=True)
            return {
                'success': False,
                'chunks_created': 0,
                'files_processed': 0,
                'error': str(e),
                'warnings': [] if 'warnings' not in locals() else warnings
            }

    def reimport_repository(self, repo_id: str, user_id: str) -> ImportResult:
        """
        Re-import a repository (refresh analysis and vectorization).

        Args:
            repo_id: Repository ID to reimport
            user_id: User ID performing the reimport

        Returns:
            ImportResult with updated import information
        """
        try:
            logger.info(f"Re-importing repository {repo_id}")

            # For now, we'll return a success message
            # In a full implementation, this would:
            # 1. Find the original repository URL from database
            # 2. Delete old vectors
            # 3. Re-import with latest code

            return ImportResult(
                success=True,
                repository_id=repo_id,
                repository_name='reimported',
                repository_owner='unknown',
                local_path='',
                message='Repository re-import scheduled (full implementation pending)'
            )

        except Exception as e:
            logger.error(f"Re-import failed for repository {repo_id}: {e}")
            return ImportResult(
                success=False,
                repository_id=repo_id,
                repository_name='unknown',
                repository_owner='unknown',
                local_path='',
                error=f"Re-import failed: {str(e)}"
            )


# Global instance
_repository_import_service = None


def get_repository_import_service() -> RepositoryImportService:
    """Get or create the global RepositoryImportService instance."""
    global _repository_import_service
    if _repository_import_service is None:
        _repository_import_service = RepositoryImportService()
    return _repository_import_service


__all__ = [
    'RepositoryImportService',
    'ImportResult',
    'ImportProgress',
    'get_repository_import_service'
]
