"""
Background job queue for async operation processing.

Provides:
- Job creation and tracking
- Background job execution
- Job status and results management
- Result caching
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional


class JobStatus(Enum):
    """Status of a background job"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    """Result of a job execution"""

    job_id: str
    status: JobStatus = JobStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


class Job:
    """Background job"""

    def __init__(
        self,
        task: Callable,
        name: str = "",
        timeout: float = 300.0,
        **kwargs,
    ):
        """
        Initialize job.

        Args:
            task: Async function to execute
            name: Job name
            timeout: Job timeout in seconds
            **kwargs: Arguments for task
        """
        self.job_id = f"job_{str(uuid.uuid4())}"
        self.task = task
        self.name = name or task.__name__
        self.timeout = timeout
        self.kwargs = kwargs
        self.result = JobResult(job_id=self.job_id)

    async def execute(self) -> JobResult:
        """
        Execute job.

        Returns:
            JobResult with outcome
        """
        self.result.started_at = datetime.now(timezone.utc).isoformat()
        self.result.status = JobStatus.RUNNING

        try:
            # Execute with timeout
            task_result = await asyncio.wait_for(
                self.task(**self.kwargs),
                timeout=self.timeout,
            )

            self.result.status = JobStatus.COMPLETED
            self.result.result = task_result

        except asyncio.TimeoutError:
            self.result.status = JobStatus.TIMEOUT
            self.result.error = f"Job timed out after {self.timeout}s"

        except asyncio.CancelledError:
            self.result.status = JobStatus.CANCELLED
            self.result.error = "Job was cancelled"

        except Exception as e:
            self.result.status = JobStatus.FAILED
            self.result.error = str(e)

        finally:
            self.result.completed_at = (
                datetime.now(timezone.utc).isoformat()
            )

            # Calculate duration
            if self.result.started_at and self.result.completed_at:
                start = datetime.fromisoformat(self.result.started_at)
                end = datetime.fromisoformat(self.result.completed_at)
                self.result.duration_ms = (
                    (end - start).total_seconds() * 1000
                )

        return self.result


class JobQueue:
    """Queue for background jobs"""

    def __init__(self, max_workers: int = 5):
        """
        Initialize job queue.

        Args:
            max_workers: Maximum concurrent workers
        """
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)

        # Job tracking
        self.jobs: Dict[str, Job] = {}
        self.results: Dict[str, JobResult] = {}
        self.queue: asyncio.Queue = asyncio.Queue()

        # Metrics
        self.metrics = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "timeout_jobs": 0,
        }

    async def submit(
        self,
        task: Callable,
        name: str = "",
        timeout: float = 300.0,
        **kwargs,
    ) -> str:
        """
        Submit job to queue.

        Args:
            task: Async function to execute
            name: Job name
            timeout: Job timeout
            **kwargs: Task arguments

        Returns:
            Job ID
        """
        job = Job(task, name=name, timeout=timeout, **kwargs)
        self.jobs[job.job_id] = job
        self.metrics["total_jobs"] += 1

        await self.queue.put(job)
        self.logger.debug(f"Job submitted: {job.job_id}")

        return job.job_id

    async def execute_job(self, job: Job) -> JobResult:
        """
        Execute job and store result.

        Args:
            job: Job to execute

        Returns:
            JobResult
        """
        result = await job.execute()
        self.results[job.job_id] = result

        # Update metrics
        if result.status == JobStatus.COMPLETED:
            self.metrics["completed_jobs"] += 1
        elif result.status == JobStatus.FAILED:
            self.metrics["failed_jobs"] += 1
        elif result.status == JobStatus.TIMEOUT:
            self.metrics["timeout_jobs"] += 1

        return result

    async def worker(self) -> None:
        """Background worker processing jobs"""
        while True:
            try:
                job = await self.queue.get()

                self.logger.debug(f"Executing job: {job.job_id}")
                await self.execute_job(job)

                self.queue.task_done()

            except Exception as e:
                self.logger.error(f"Worker error: {e}")

    async def start_workers(self) -> None:
        """Start background workers"""
        self.workers = [
            asyncio.create_task(self.worker())
            for _ in range(self.max_workers)
        ]
        self.logger.info(f"Started {self.max_workers} workers")

    async def stop_workers(self) -> None:
        """Stop background workers"""
        for worker in self.workers:
            worker.cancel()
        self.logger.info("Stopped workers")

    def get_job_status(self, job_id: str) -> Optional[JobResult]:
        """
        Get job status.

        Args:
            job_id: Job ID

        Returns:
            JobResult if found
        """
        return self.results.get(job_id)

    def get_all_results(self) -> Dict[str, JobResult]:
        """
        Get all job results.

        Returns:
            Dictionary of results
        """
        return self.results.copy()

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get queue metrics.

        Returns:
            Metrics dictionary
        """
        return {
            **self.metrics,
            "pending_jobs": self.queue.qsize(),
            "cached_results": len(self.results),
        }

    def clear_results(self, older_than_seconds: Optional[int] = None) -> int:
        """
        Clear old results.

        Args:
            older_than_seconds: Clear results older than this

        Returns:
            Number of results cleared
        """
        if older_than_seconds is None:
            cleared = len(self.results)
            self.results.clear()
            return cleared

        # Clear old results
        now = datetime.now(timezone.utc)
        to_remove = []

        for job_id, result in self.results.items():
            if result.completed_at:
                completed = datetime.fromisoformat(result.completed_at)
                age_seconds = (now - completed).total_seconds()

                if age_seconds > older_than_seconds:
                    to_remove.append(job_id)

        for job_id in to_remove:
            del self.results[job_id]

        return len(to_remove)
