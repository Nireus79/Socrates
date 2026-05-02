"""
Result poller for clients to retrieve async operation results.

Provides:
- Polling interface for results
- Status checking
- Batch result retrieval
"""

import logging
from typing import Any, Dict, List, Optional

from socratic_system.events.job_queue import JobQueue, JobStatus
from socratic_system.events.result_cache import ResultCache


class ResultPoller:
    """Poller for retrieving async operation results"""

    def __init__(
        self,
        job_queue: JobQueue,
        result_cache: ResultCache,
    ):
        """
        Initialize poller.

        Args:
            job_queue: JobQueue instance
            result_cache: ResultCache instance
        """
        self.job_queue = job_queue
        self.result_cache = result_cache
        self.logger = logging.getLogger(__name__)

    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result for job.

        Args:
            job_id: Job ID

        Returns:
            Result dictionary or None if not ready
        """
        # Try cache first
        cached = self.result_cache.get(job_id)
        if cached is not None:
            self.logger.debug(f"Cache hit for job: {job_id}")
            return cached

        # Get from job queue
        result = self.job_queue.get_job_status(job_id)
        if result is None:
            self.logger.warning(f"Job not found: {job_id}")
            return None

        # If completed, cache it
        if result.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            self.result_cache.set(
                job_id,
                result.to_dict(),
                ttl=3600.0,
            )

        return result.to_dict()

    def get_status(self, job_id: str) -> Optional[str]:
        """
        Get job status.

        Args:
            job_id: Job ID

        Returns:
            Status string or None
        """
        result = self.job_queue.get_job_status(job_id)
        if result:
            return result.status.value
        return None

    def is_ready(self, job_id: str) -> bool:
        """
        Check if result is ready.

        Args:
            job_id: Job ID

        Returns:
            True if result is available
        """
        result = self.job_queue.get_job_status(job_id)
        if result is None:
            return False

        return result.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.TIMEOUT,
            JobStatus.CANCELLED,
        )

    def get_batch_results(
        self,
        job_ids: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple results at once.

        Args:
            job_ids: List of job IDs

        Returns:
            Dictionary mapping job IDs to results
        """
        results = {}
        for job_id in job_ids:
            result = self.get_result(job_id)
            if result:
                results[job_id] = result

        return results

    def wait_for_result(
        self,
        job_id: str,
        max_polls: int = 30,
        poll_interval: float = 1.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for result with polling.

        Args:
            job_id: Job ID
            max_polls: Maximum number of polls
            poll_interval: Interval between polls in seconds

        Returns:
            Result if available, None if timed out
        """
        import time

        for attempt in range(max_polls):
            result = self.get_result(job_id)

            if result is not None:
                self.logger.debug(
                    f"Result ready after {attempt + 1} polls"
                )
                return result

            if attempt < max_polls - 1:
                time.sleep(poll_interval)

        self.logger.warning(
            f"Result polling timed out for job: {job_id}"
        )
        return None

    def get_poll_status(
        self,
        job_id: str,
    ) -> Dict[str, Any]:
        """
        Get poll status for result.

        Args:
            job_id: Job ID

        Returns:
            Status dictionary for polling
        """
        result = self.job_queue.get_job_status(job_id)

        if result is None:
            return {
                "job_id": job_id,
                "status": "not_found",
                "ready": False,
            }

        return {
            "job_id": job_id,
            "status": result.status.value,
            "ready": self.is_ready(job_id),
            "result": result.result if self.is_ready(job_id) else None,
            "error": result.error if result.status == JobStatus.FAILED else None,
            "duration_ms": result.duration_ms,
        }

    def get_active_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active jobs.

        Returns:
            Dictionary of job statuses
        """
        active = {}

        for job_id, result in self.job_queue.results.items():
            if result.status in (JobStatus.PENDING, JobStatus.RUNNING):
                active[job_id] = {
                    "status": result.status.value,
                    "started_at": result.started_at,
                }

        return active

    def get_completed_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all completed jobs.

        Returns:
            Dictionary of completed jobs
        """
        completed = {}

        for job_id, result in self.job_queue.results.items():
            if result.status == JobStatus.COMPLETED:
                completed[job_id] = result.to_dict()

        return completed

    def get_failed_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all failed jobs.

        Returns:
            Dictionary of failed jobs
        """
        failed = {}

        for job_id, result in self.job_queue.results.items():
            if result.status == JobStatus.FAILED:
                failed[job_id] = result.to_dict()

        return failed
