"""
Tests for Phase 3 Event-Driven Refactoring.

Tests validate:
- Event handlers and async processing
- Background job queue
- Result caching
- Result polling
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from socratic_system.events import (
    EventEmitter,
    EventHandler,
    EventHandlerRegistry,
    AsyncEventProcessor,
    JobQueue,
    JobStatus,
    ResultCache,
    ResultPoller,
)


class TestEventHandler(unittest.TestCase):
    """Test event handler"""

    def test_create_handler(self):
        """Create event handler"""
        handler = MagicMock()
        event_handler = EventHandler("test_event", handler)

        self.assertEqual(event_handler.event_type, "test_event")
        self.assertEqual(event_handler.execution_count, 0)
        self.assertEqual(event_handler.error_count, 0)

    async def test_execute_sync_handler(self):
        """Execute synchronous handler"""
        def sync_handler(data):
            return data.get("value")

        handler = EventHandler("test", sync_handler, async_handler=False)
        result = await handler.execute({"value": "test"})

        self.assertEqual(result, "test")
        self.assertEqual(handler.execution_count, 1)

    async def test_execute_async_handler(self):
        """Execute asynchronous handler"""
        async def async_handler(data):
            await asyncio.sleep(0.01)
            return data.get("value")

        handler = EventHandler("test", async_handler, async_handler=True)
        result = await handler.execute({"value": "test"})

        self.assertEqual(result, "test")
        self.assertEqual(handler.execution_count, 1)

    async def test_handler_error(self):
        """Handle errors in handler"""
        async def failing_handler(data):
            raise ValueError("Handler failed")

        handler = EventHandler("test", failing_handler, async_handler=True)

        with self.assertRaises(ValueError):
            await handler.execute({})

        self.assertEqual(handler.error_count, 1)


class TestEventHandlerRegistry(unittest.IsolatedAsyncioTestCase):
    """Test event handler registry"""

    async def asyncSetUp(self):
        """Set up test fixtures"""
        self.registry = EventHandlerRegistry()

    async def test_register_handler(self):
        """Register event handler"""
        async def handler(data):
            return data

        self.registry.register("test_event", handler, async_handler=True)

        handlers = self.registry.get_handlers("test_event")
        self.assertEqual(len(handlers), 1)

    async def test_execute_handlers(self):
        """Execute registered handlers"""
        async def handler1(data):
            return "result1"

        async def handler2(data):
            return "result2"

        self.registry.register("event", handler1, async_handler=True)
        self.registry.register("event", handler2, async_handler=True)

        results = await self.registry.execute_handlers("event", {})

        self.assertEqual(len(results), 2)
        self.assertIn("result1", results)
        self.assertIn("result2", results)

    async def test_unregister_handler(self):
        """Unregister handler"""
        def handler(data):
            return data

        self.registry.register("event", handler)
        self.registry.unregister("event", handler)

        handlers = self.registry.get_handlers("event")
        self.assertEqual(len(handlers), 0)


class TestAsyncEventProcessor(unittest.IsolatedAsyncioTestCase):
    """Test async event processor"""

    async def asyncSetUp(self):
        """Set up test fixtures"""
        self.emitter = EventEmitter()
        self.processor = AsyncEventProcessor(self.emitter)

    async def test_processor_start_stop(self):
        """Start and stop processor"""
        await self.processor.start()
        self.assertTrue(self.processor.running)

        await self.processor.stop()
        self.assertFalse(self.processor.running)

    async def test_register_and_execute(self):
        """Register handler and execute"""
        results = []

        async def handler(data):
            results.append(data)

        self.processor.register_handler("test", handler, async_handler=True)

        await self.processor.process_event("test", {"value": "test"})

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["value"], "test")


class TestJobQueue(unittest.IsolatedAsyncioTestCase):
    """Test background job queue"""

    async def asyncSetUp(self):
        """Set up test fixtures"""
        self.queue = JobQueue(max_workers=2)
        await self.queue.start_workers()

    async def asyncTearDown(self):
        """Clean up"""
        await self.queue.stop_workers()

    async def test_submit_job(self):
        """Submit job to queue"""
        async def task():
            return "result"

        job_id = await self.queue.submit(task)

        self.assertIsNotNone(job_id)
        self.assertIn("job_", job_id)

    async def test_job_execution(self):
        """Test job execution"""
        async def task():
            await asyncio.sleep(0.01)
            return "result"

        job_id = await self.queue.submit(task)

        # Wait for execution
        await asyncio.sleep(0.1)

        result = self.queue.get_job_status(job_id)

        self.assertIsNotNone(result)
        self.assertEqual(result.status, JobStatus.COMPLETED)
        self.assertEqual(result.result, "result")

    async def test_job_failure(self):
        """Test job failure handling"""
        async def failing_task():
            raise ValueError("Task failed")

        job_id = await self.queue.submit(failing_task)

        # Wait for execution
        await asyncio.sleep(0.1)

        result = self.queue.get_job_status(job_id)

        self.assertEqual(result.status, JobStatus.FAILED)
        self.assertIsNotNone(result.error)

    async def test_job_timeout(self):
        """Test job timeout"""
        async def slow_task():
            await asyncio.sleep(10)

        job_id = await self.queue.submit(slow_task, timeout=0.05)

        # Wait for timeout
        await asyncio.sleep(0.1)

        result = self.queue.get_job_status(job_id)

        self.assertEqual(result.status, JobStatus.TIMEOUT)

    async def test_queue_metrics(self):
        """Test queue metrics"""
        async def task():
            await asyncio.sleep(0.01)
            return "result"

        await self.queue.submit(task)
        await asyncio.sleep(0.1)

        metrics = self.queue.get_metrics()

        self.assertIn("total_jobs", metrics)
        self.assertEqual(metrics["total_jobs"], 1)


class TestResultCache(unittest.TestCase):
    """Test result cache"""

    def setUp(self):
        """Set up test fixtures"""
        self.cache = ResultCache(default_ttl=10.0)

    def test_set_and_get(self):
        """Set and get cache value"""
        self.cache.set("key1", {"result": "value1"})

        value = self.cache.get("key1")

        self.assertEqual(value, {"result": "value1"})

    def test_cache_miss(self):
        """Test cache miss"""
        value = self.cache.get("nonexistent")

        self.assertIsNone(value)

    def test_exists(self):
        """Test existence check"""
        self.cache.set("key1", "value1")

        self.assertTrue(self.cache.exists("key1"))
        self.assertFalse(self.cache.exists("key2"))

    def test_delete(self):
        """Test delete"""
        self.cache.set("key1", "value1")
        deleted = self.cache.delete("key1")

        self.assertTrue(deleted)
        self.assertFalse(self.cache.exists("key1"))

    def test_clear(self):
        """Test clear all"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        cleared = self.cache.clear()

        self.assertEqual(cleared, 2)
        self.assertEqual(len(self.cache.cache), 0)

    def test_stats(self):
        """Test cache statistics"""
        self.cache.set("key1", "value1")
        self.cache.get("key1")
        self.cache.get("key2")

        stats = self.cache.get_stats()

        self.assertEqual(stats["total_sets"], 1)
        self.assertEqual(stats["total_gets"], 2)
        self.assertEqual(stats["cache_hits"], 1)
        self.assertEqual(stats["cache_misses"], 1)


class TestResultPoller(unittest.IsolatedAsyncioTestCase):
    """Test result poller"""

    async def asyncSetUp(self):
        """Set up test fixtures"""
        self.queue = JobQueue()
        self.cache = ResultCache()
        self.poller = ResultPoller(self.queue, self.cache)

    async def test_get_result(self):
        """Get result for job"""
        async def task():
            return "result"

        job_id = await self.queue.submit(task)
        await asyncio.sleep(0.05)
        await self.queue.execute_job(
            self.queue.jobs[job_id]
        )

        result = self.poller.get_result(job_id)

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "completed")

    async def test_get_status(self):
        """Get job status"""
        async def task():
            return "result"

        job_id = await self.queue.submit(task)
        await asyncio.sleep(0.05)
        await self.queue.execute_job(
            self.queue.jobs[job_id]
        )

        status = self.poller.get_status(job_id)

        self.assertEqual(status, "completed")

    async def test_is_ready(self):
        """Check if result is ready"""
        async def task():
            return "result"

        job_id = await self.queue.submit(task)

        # Not ready yet
        self.assertFalse(self.poller.is_ready(job_id))

        await asyncio.sleep(0.05)
        await self.queue.execute_job(
            self.queue.jobs[job_id]
        )

        # Now ready
        self.assertTrue(self.poller.is_ready(job_id))

    async def test_get_batch_results(self):
        """Get multiple results"""
        async def task():
            return "result"

        job_ids = []
        for i in range(3):
            job_id = await self.queue.submit(task)
            job_ids.append(job_id)

        await asyncio.sleep(0.1)

        for job_id in job_ids:
            if job_id in self.queue.jobs:
                await self.queue.execute_job(self.queue.jobs[job_id])

        results = self.poller.get_batch_results(job_ids)

        self.assertGreaterEqual(len(results), 1)

    async def test_get_poll_status(self):
        """Get poll status"""
        async def task():
            return "result"

        job_id = await self.queue.submit(task)
        await asyncio.sleep(0.05)
        await self.queue.execute_job(
            self.queue.jobs[job_id]
        )

        status = self.poller.get_poll_status(job_id)

        self.assertEqual(status["job_id"], job_id)
        self.assertTrue(status["ready"])


if __name__ == "__main__":
    unittest.main()
