"""
Tests for Phase 4 API Adapter Layer.

Tests validate:
- Base adapter functionality
- Service registry and discovery
- Service adapter for HTTP request handling
- Async job handler with Phase 3 integration
- Request/response schemas
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from socratic_system.api_adapter import (
    BaseAdapter,
    AdapterError,
    AdapterValidationError,
    ResponseDTO,
    AsyncJobRequest,
    JobStatusResponse,
    ServiceAdapter,
    ServiceRegistry,
    ServiceInfo,
    AsyncJobHandler,
)
from socratic_system.events import JobQueue, ResultCache


class MockService:
    """Mock service for testing"""

    async def async_method(self, value: str) -> str:
        """Async method"""
        await asyncio.sleep(0.01)
        return f"async_{value}"

    def sync_method(self, value: str) -> str:
        """Sync method"""
        return f"sync_{value}"

    def failing_method(self):
        """Method that fails"""
        raise ValueError("Test error")


class TestBaseAdapter(unittest.TestCase):
    """Test base adapter"""

    def setUp(self):
        """Set up test fixtures"""

        class TestAdapter(BaseAdapter):
            async def handle_request(self, request_data, **kwargs):
                return {"result": "test"}

        self.adapter = TestAdapter("test_service")

    def test_create_adapter(self):
        """Create adapter"""
        self.assertEqual(self.adapter.service_name, "test_service")
        self.assertEqual(self.adapter.version, "v1")

    def test_validate_request_success(self):
        """Validate request successfully"""
        request = {"field1": "value1", "field2": "value2"}
        result = self.adapter.validate_request(request, ["field1"])
        self.assertEqual(result, request)

    def test_validate_request_missing_field(self):
        """Validate request with missing field"""
        request = {"field1": "value1"}
        with self.assertRaises(AdapterValidationError):
            self.adapter.validate_request(request, ["field1", "field2"])

    def test_check_authorization_success(self):
        """Check authorization success"""
        result = self.adapter.check_authorization("user1", "user1")
        self.assertTrue(result)

    def test_check_authorization_denied(self):
        """Check authorization denied"""
        with self.assertRaises(AdapterError):
            self.adapter.check_authorization("user1", "user2", allow_same_user=True)

    def test_transform_response(self):
        """Transform response"""
        response = self.adapter.transform_response(
            {"key": "value"}, message="Success"
        )
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["key"], "value")
        self.assertEqual(response["message"], "Success")

    def test_transform_error(self):
        """Transform error"""
        error = ValueError("Test error")
        response = self.adapter.transform_error(error)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"]["type"], "ValueError")

    def test_get_adapter_info(self):
        """Get adapter info"""
        info = self.adapter.get_adapter_info()
        self.assertEqual(info["service"], "test_service")
        self.assertEqual(info["version"], "v1")


class TestServiceRegistry(unittest.TestCase):
    """Test service registry"""

    def setUp(self):
        """Set up test fixtures"""
        self.registry = ServiceRegistry()
        self.service = MockService()

    def test_register_service(self):
        """Register service"""
        info = self.registry.register("mock", self.service)
        self.assertEqual(info.name, "mock")
        self.assertGreater(len(info.methods), 0)

    def test_service_exists(self):
        """Check service exists"""
        self.registry.register("mock", self.service)
        self.assertTrue(self.registry.service_exists("mock"))
        self.assertFalse(self.registry.service_exists("nonexistent"))

    def test_method_exists(self):
        """Check method exists"""
        self.registry.register("mock", self.service)
        self.assertTrue(self.registry.method_exists("mock", "async_method"))
        self.assertFalse(self.registry.method_exists("mock", "nonexistent"))

    def test_get_method(self):
        """Get method from service"""
        self.registry.register("mock", self.service)
        method = self.registry.get_method("mock", "sync_method")
        self.assertIsNotNone(method)
        self.assertEqual(method("test"), "sync_test")

    def test_list_services(self):
        """List all services"""
        self.registry.register("mock1", self.service)
        self.registry.register("mock2", self.service)
        services = self.registry.list_services()
        self.assertIn("mock1", services)
        self.assertIn("mock2", services)

    def test_unregister_service(self):
        """Unregister service"""
        self.registry.register("mock", self.service)
        result = self.registry.unregister("mock")
        self.assertTrue(result)
        self.assertFalse(self.registry.service_exists("mock"))

    def test_duplicate_register(self):
        """Register duplicate service"""
        self.registry.register("mock", self.service)
        with self.assertRaises(ValueError):
            self.registry.register("mock", self.service)


class TestServiceAdapter(unittest.IsolatedAsyncioTestCase):
    """Test service adapter"""

    async def asyncSetUp(self):
        """Set up test fixtures"""
        self.registry = ServiceRegistry()
        self.registry.register("mock", MockService())
        self.adapter = ServiceAdapter(self.registry)

    async def test_validate_service_exists(self):
        """Validate service exists"""
        result = self.adapter.validate_service_exists("mock")
        self.assertTrue(result)

    async def test_validate_service_not_exists(self):
        """Validate service not exists"""
        with self.assertRaises(AdapterValidationError):
            self.adapter.validate_service_exists("nonexistent")

    async def test_call_async_method(self):
        """Call async method"""
        result = await self.adapter.call_service_method(
            "mock", "async_method", {"value": "test"}
        )
        self.assertEqual(result, "async_test")

    async def test_call_sync_method(self):
        """Call sync method"""
        result = await self.adapter.call_service_method(
            "mock", "sync_method", {"value": "test"}
        )
        self.assertEqual(result, "sync_test")

    async def test_call_failing_method(self):
        """Call failing method"""
        with self.assertRaises(AdapterError):
            await self.adapter.call_service_method(
                "mock", "failing_method", {}
            )

    async def test_handle_request(self):
        """Handle service request"""
        request = {
            "service": "mock",
            "method": "sync_method",
            "params": {"value": "test"},
        }
        response = await self.adapter.handle_request(request)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], "sync_test")

    async def test_handle_request_invalid_service(self):
        """Handle request with invalid service"""
        request = {
            "service": "invalid",
            "method": "sync_method",
            "params": {},
        }
        with self.assertRaises(AdapterValidationError):
            await self.adapter.handle_request(request)

    async def test_get_service_info(self):
        """Get service information"""
        info = self.adapter.get_service_info("mock")
        self.assertEqual(info["name"], "mock")
        self.assertIn("methods", info)

    async def test_get_method_info(self):
        """Get method information"""
        info = self.adapter.get_method_info("mock", "sync_method")
        self.assertEqual(info["method"], "sync_method")
        self.assertIn("parameters", info)


class TestAsyncJobHandler(unittest.IsolatedAsyncioTestCase):
    """Test async job handler"""

    async def asyncSetUp(self):
        """Set up test fixtures"""
        self.queue = JobQueue(max_workers=2)
        self.cache = ResultCache()
        self.registry = ServiceRegistry()
        self.registry.register("mock", MockService())
        self.adapter = ServiceAdapter(self.registry)
        self.handler = AsyncJobHandler(self.queue, self.cache, self.adapter)
        await self.handler.initialize()

    async def asyncTearDown(self):
        """Clean up"""
        await self.handler.shutdown()

    async def test_submit_async_job(self):
        """Submit async job"""
        job_id = await self.handler.submit_async_job(
            "mock", "sync_method", {"value": "test"}, timeout=30.0
        )
        self.assertIsNotNone(job_id)
        self.assertIn("job_", job_id)

    async def test_get_job_status(self):
        """Get job status"""
        job_id = await self.handler.submit_async_job(
            "mock", "sync_method", {"value": "test"}
        )
        await asyncio.sleep(0.1)

        status = self.handler.get_job_status(job_id)
        self.assertEqual(status["job_id"], job_id)
        self.assertIn("status", status)

    async def test_get_batch_job_status(self):
        """Get batch job status"""
        job_ids = []
        for i in range(3):
            job_id = await self.handler.submit_async_job(
                "mock", "sync_method", {"value": f"test{i}"}
            )
            job_ids.append(job_id)

        await asyncio.sleep(0.1)

        batch_status = self.handler.get_batch_job_status(job_ids)
        self.assertEqual(batch_status["total"], 3)
        self.assertIn("jobs", batch_status)

    async def test_wait_for_result(self):
        """Wait for job result"""
        job_id = await self.handler.submit_async_job(
            "mock", "sync_method", {"value": "test"}, timeout=30.0
        )

        result = await self.handler.wait_for_result(job_id, max_polls=20)
        self.assertTrue(result["ready"])

    async def test_get_active_jobs(self):
        """Get active jobs"""
        job_id = await self.handler.submit_async_job(
            "mock", "sync_method", {"value": "test"}
        )

        active = self.handler.get_active_jobs()
        self.assertGreaterEqual(active["total"], 0)

    async def test_get_completed_jobs(self):
        """Get completed jobs"""
        job_id = await self.handler.submit_async_job(
            "mock", "sync_method", {"value": "test"}
        )
        await asyncio.sleep(0.2)

        completed = self.handler.get_completed_jobs()
        self.assertGreaterEqual(completed["total"], 0)

    async def test_clear_cache(self):
        """Clear cache"""
        self.cache.set("test_key", {"data": "test"})
        count = self.handler.clear_cache()
        self.assertEqual(count, 1)


class TestResponseSchemas(unittest.TestCase):
    """Test response schemas"""

    def test_response_dto_success(self):
        """Create success response DTO"""
        response = ResponseDTO.success(
            data={"key": "value"},
            service="test_service",
            message="Success",
        )
        self.assertEqual(response.status, "success")
        self.assertEqual(response.data["key"], "value")

    def test_response_dto_error(self):
        """Create error response DTO"""
        response = ResponseDTO.error(
            error_message="Test error",
            service="test_service",
            error_code="TEST_ERROR",
        )
        self.assertEqual(response.status, "error")
        self.assertEqual(response.data["error"], "Test error")

    def test_async_job_request(self):
        """Create async job request"""
        request = AsyncJobRequest(
            service="test_service",
            method="test_method",
            params={"key": "value"},
            timeout=60.0,
        )
        self.assertEqual(request.service, "test_service")
        self.assertEqual(request.method, "test_method")

    def test_job_status_response(self):
        """Create job status response"""
        response = JobStatusResponse(
            job_id="job_123",
            status="completed",
            ready=True,
            result={"key": "value"},
            error=None,
            duration_ms=1500,
        )
        self.assertEqual(response.job_id, "job_123")
        self.assertTrue(response.ready)


if __name__ == "__main__":
    unittest.main()
