"""Job tracking for Phase 3 background processing.

Tracks status of async background jobs for analysis processing.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Lock

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Status of background job"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    """Result of async job execution"""

    job_id: str
    project_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = field(default=0.0)  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert job result to dictionary for serialization.

        Returns:
            Dict representation of job result
        """
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "progress": self.progress
        }

    def is_complete(self) -> bool:
        """Check if job has completed (success or failure)"""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)


class JobTracker:
    """Track status of background async jobs.

    Maintains in-memory job tracking for async analysis processing.
    Jobs are automatically cleaned up after completion.
    """

    def __init__(self):
        """Initialize job tracker"""
        self._jobs: Dict[str, JobResult] = {}
        self._lock = Lock()
        self._max_jobs = 10000  # Max tracked jobs
        logger.info("JobTracker initialized")

    def create_job(self, job_id: str, project_id: str) -> JobResult:
        """Create new job tracking entry.

        Args:
            job_id: Unique job identifier
            project_id: Associated project ID

        Returns:
            JobResult object initialized in PENDING state
        """
        with self._lock:
            job = JobResult(
                job_id=job_id,
                project_id=project_id,
                status=JobStatus.PENDING,
                created_at=datetime.now()
            )
            self._jobs[job_id] = job
            logger.debug(f"Job created: {job_id} for project {project_id}")
            return job

    def get_job(self, job_id: str) -> Optional[JobResult]:
        """Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            JobResult if exists, None otherwise
        """
        with self._lock:
            return self._jobs.get(job_id)

    def mark_processing(self, job_id: str):
        """Mark job as processing.

        Args:
            job_id: Job identifier
        """
        with self._lock:
            if job := self._jobs.get(job_id):
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now()
                logger.debug(f"Job started: {job_id}")

    def mark_completed(self, job_id: str, result: Dict[str, Any]):
        """Mark job as completed with result.

        Args:
            job_id: Job identifier
            result: Job result data
        """
        with self._lock:
            if job := self._jobs.get(job_id):
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                job.result = result
                job.progress = 1.0
                logger.debug(f"Job completed: {job_id}")

    def mark_failed(self, job_id: str, error: str):
        """Mark job as failed.

        Args:
            job_id: Job identifier
            error: Error message
        """
        with self._lock:
            if job := self._jobs.get(job_id):
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
                job.error = error
                logger.debug(f"Job failed: {job_id} - {error}")

    def mark_cancelled(self, job_id: str):
        """Mark job as cancelled.

        Args:
            job_id: Job identifier
        """
        with self._lock:
            if job := self._jobs.get(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                logger.debug(f"Job cancelled: {job_id}")

    def update_progress(self, job_id: str, progress: float):
        """Update job progress.

        Args:
            job_id: Job identifier
            progress: Progress value (0.0 to 1.0)
        """
        with self._lock:
            if job := self._jobs.get(job_id):
                job.progress = min(1.0, max(0.0, progress))
                logger.debug(f"Job progress: {job_id} = {job.progress * 100:.0f}%")

    def get_project_jobs(self, project_id: str) -> list:
        """Get all jobs for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of JobResult objects
        """
        with self._lock:
            return [
                job for job in self._jobs.values()
                if job.project_id == project_id
            ]

    def get_pending_jobs(self) -> list:
        """Get all pending jobs.

        Returns:
            List of JobResult objects in PENDING status
        """
        with self._lock:
            return [
                job for job in self._jobs.values()
                if job.status == JobStatus.PENDING
            ]

    def delete_job(self, job_id: str):
        """Delete job entry (for cleanup).

        Args:
            job_id: Job identifier
        """
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                logger.debug(f"Job deleted: {job_id}")

    def cleanup_completed(self, max_age_seconds: int = 86400):
        """Clean up completed jobs older than max_age.

        Args:
            max_age_seconds: Maximum age in seconds (default 24 hours)
        """
        with self._lock:
            current_time = datetime.now()
            to_delete = []

            for job_id, job in self._jobs.items():
                if job.is_complete():
                    age = (current_time - job.completed_at).total_seconds()
                    if age > max_age_seconds:
                        to_delete.append(job_id)

            for job_id in to_delete:
                del self._jobs[job_id]

            if to_delete:
                logger.info(f"Cleaned up {len(to_delete)} completed jobs")

    def get_stats(self) -> Dict[str, Any]:
        """Get job tracker statistics.

        Returns:
            Statistics about tracked jobs
        """
        with self._lock:
            total = len(self._jobs)
            pending = sum(1 for j in self._jobs.values() if j.status == JobStatus.PENDING)
            processing = sum(1 for j in self._jobs.values() if j.status == JobStatus.PROCESSING)
            completed = sum(1 for j in self._jobs.values() if j.status == JobStatus.COMPLETED)
            failed = sum(1 for j in self._jobs.values() if j.status == JobStatus.FAILED)

            return {
                "total_jobs": total,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "max_jobs": self._max_jobs
            }
