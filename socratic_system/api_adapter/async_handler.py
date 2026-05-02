"""
Async job handler for Phase 4.

Integrates with Phase 3 JobQueue to handle async service invocations
with result streaming and polling support.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from socratic_system.events.job_queue import JobQueue
from socratic_system.events.result_cache import ResultCache
from socratic_system.events.result_poller import ResultPoller

from .service_adapter import ServiceAdapter
from .base_adapter import AdapterError


class AsyncJobHandler:
    """
    Handler for async service invocations.

    Provides:
    - Async job submission
    - Result polling
    - Batch status checking
    - Result streaming
    """

    def __init__(
        self,
        job_queue: JobQueue,
        result_cache: Optional[ResultCache] = None,
        service_adapter: Optional[ServiceAdapter] = None,
        max_workers: int = 5,
    ):
        """
        Initialize async job handler.

        Args:
            job_queue: JobQueue instance
            result_cache: ResultCache instance (creates new if None)
            service_adapter: ServiceAdapter instance (creates new if None)
            max_workers: Max concurrent workers
        """
        self.job_queue = job_queue
        self.result_cache = result_cache or ResultCache()
        self.service_adapter = service_adapter or ServiceAdapter()
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)

    async def submit_async_job(
        self,
        service_name: str,
        method_name: str,
        params: Dict[str, Any],
        timeout: float = 300.0,
        job_name: Optional[str] = None,
    ) -> str:
        """
        Submit async job to queue.

        Args:
            service_name: Service name
            method_name: Method name
            params: Method parameters
            timeout: Job timeout in seconds
            job_name: Optional job name for tracking

        Returns:
            Job ID

        Raises:
            AdapterError: If job submission fails
        """
        self.logger.debug(
            f"Submitting async job: {service_name}.{method_name}"
        )

        # Create async task for service invocation
        async def async_service_call():
            request_data = {
                "service": service_name,
                "method": method_name,
                "params": params,
            }
            return await self.service_adapter.handle_request(request_data)

        try:
            # Submit job to queue
            job_id = await self.job_queue.submit(
                async_service_call,
                name=job_name or f"{service_name}.{method_name}",
                timeout=timeout,
            )

            self.logger.info(f"Async job submitted: {job_id}")
            return job_id

        except Exception as e:
            self.logger.error(f"Failed to submit async job: {str(e)}")
            raise AdapterError(
                f"Failed to submit job: {str(e)}",
                error_code="JOB_SUBMISSION_FAILED",
            )

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status.

        Args:
            job_id: Job ID

        Returns:
            Job status information

        Raises:
            AdapterError: If job not found
        """
        job_result = self.job_queue.get_job_status(job_id)

        if job_result is None:
            raise AdapterError(
                f"Job '{job_id}' not found",
                error_code="JOB_NOT_FOUND",
            )

        self.logger.debug(f"Retrieved status for job {job_id}: {job_result.status}")

        # Prepare response
        response = {
            "job_id": job_id,
            "status": job_result.status.value,
            "ready": job_result.status.value in (
                "completed",
                "failed",
                "timeout",
                "cancelled",
            ),
            "duration_ms": job_result.duration_ms,
        }

        # Add timestamps
        if job_result.started_at:
            response["started_at"] = job_result.started_at
        if job_result.completed_at:
            response["completed_at"] = job_result.completed_at

        # Add result or error
        if job_result.status.value == "completed":
            response["result"] = job_result.result
        elif job_result.status.value == "failed":
            response["error"] = job_result.error

        return response

    def get_batch_job_status(self, job_ids: list[str]) -> Dict[str, Any]:
        """
        Get status for multiple jobs.

        Args:
            job_ids: List of job IDs

        Returns:
            Batch status information

        Raises:
            AdapterError: If no jobs found
        """
        if not job_ids:
            raise AdapterError(
                "No job IDs provided",
                error_code="INVALID_REQUEST",
            )

        self.logger.debug(f"Retrieving batch status for {len(job_ids)} jobs")

        jobs = {}
        completed = 0
        pending = 0
        failed = 0

        for job_id in job_ids:
            try:
                status = self.get_job_status(job_id)
                jobs[job_id] = status

                # Count statuses
                if status["status"] == "completed":
                    completed += 1
                elif status["status"] in ("failed", "timeout"):
                    failed += 1
                elif status["status"] == "pending":
                    pending += 1

            except AdapterError:
                # Job not found - include in response
                jobs[job_id] = {
                    "status": "not_found",
                    "ready": False,
                }

        return {
            "total": len(job_ids),
            "completed": completed,
            "pending": pending,
            "failed": failed,
            "jobs": jobs,
        }

    async def wait_for_result(
        self,
        job_id: str,
        max_polls: int = 30,
        poll_interval: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Wait for job result with polling.

        Args:
            job_id: Job ID
            max_polls: Maximum number of polls
            poll_interval: Interval between polls in seconds

        Returns:
            Job result

        Raises:
            AdapterError: If job not found or times out
        """
        self.logger.debug(
            f"Waiting for result of job {job_id} (max {max_polls} polls)"
        )

        for attempt in range(max_polls):
            try:
                status = self.get_job_status(job_id)

                if status["ready"]:
                    self.logger.info(
                        f"Job {job_id} completed after {attempt + 1} polls"
                    )
                    return status

                if attempt < max_polls - 1:
                    await asyncio.sleep(poll_interval)

            except AdapterError:
                if attempt < max_polls - 1:
                    await asyncio.sleep(poll_interval)
                else:
                    raise

        raise AdapterError(
            f"Job {job_id} did not complete within {max_polls} polls",
            error_code="JOB_TIMEOUT",
        )

    def get_active_jobs(self) -> Dict[str, Any]:
        """
        Get all active jobs.

        Returns:
            Dictionary of active job statuses
        """
        active = {}

        for job_id in list(self.job_queue.results.keys()):
            try:
                status = self.get_job_status(job_id)
                if not status["ready"]:
                    active[job_id] = status
            except AdapterError:
                pass

        return {
            "total": len(active),
            "jobs": active,
        }

    def get_completed_jobs(self) -> Dict[str, Any]:
        """
        Get all completed jobs.

        Returns:
            Dictionary of completed job statuses
        """
        completed = {}

        for job_id in list(self.job_queue.results.keys()):
            try:
                status = self.get_job_status(job_id)
                if status["status"] == "completed":
                    completed[job_id] = status
            except AdapterError:
                pass

        return {
            "total": len(completed),
            "jobs": completed,
        }

    def get_failed_jobs(self) -> Dict[str, Any]:
        """
        Get all failed jobs.

        Returns:
            Dictionary of failed job statuses
        """
        failed = {}

        for job_id in list(self.job_queue.results.keys()):
            try:
                status = self.get_job_status(job_id)
                if status["status"] in ("failed", "timeout"):
                    failed[job_id] = status
            except AdapterError:
                pass

        return {
            "total": len(failed),
            "jobs": failed,
        }

    def clear_cache(self) -> int:
        """
        Clear result cache.

        Returns:
            Number of entries cleared
        """
        count = self.result_cache.clear()
        self.logger.info(f"Cleared {count} cache entries")
        return count

    async def initialize(self) -> None:
        """
        Initialize async job handler.

        Starts workers if not already started.
        """
        # Check if workers are already running
        workers_running = hasattr(self.job_queue, "workers") and self.job_queue.workers
        if not workers_running:
            self.logger.info(f"Starting {self.max_workers} job queue workers")
            await self.job_queue.start_workers()

    async def shutdown(self) -> None:
        """
        Shutdown async job handler.

        Stops workers and cleans up resources.
        """
        self.logger.info("Shutting down async job handler")
        workers_running = hasattr(self.job_queue, "workers") and self.job_queue.workers
        if workers_running:
            await self.job_queue.stop_workers()
