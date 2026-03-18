"""Tests for socratic_core.events module."""

import asyncio

import pytest

from socratic_core.events import EventEmitter, EventType


class TestEventType:
    """Tests for EventType enum."""

    def test_event_type_exists(self):
        """Test that common event types exist."""
        assert hasattr(EventType, "PROJECT_CREATED")
        assert hasattr(EventType, "PROJECT_SAVED")
        assert hasattr(EventType, "CODE_GENERATED")
        assert hasattr(EventType, "AGENT_START")
        assert hasattr(EventType, "AGENT_COMPLETE")

    def test_event_type_values_are_strings(self):
        """Test that event type values are strings."""
        event_type = EventType.PROJECT_CREATED
        assert isinstance(event_type.value, str)

    def test_event_type_unique_values(self):
        """Test that event types have unique values."""
        all_events = [e.value for e in EventType]
        assert len(all_events) == len(set(all_events))


class TestEventEmitter:
    """Tests for EventEmitter class."""

    def test_emitter_creation(self):
        """Test creating an EventEmitter."""
        emitter = EventEmitter()
        assert emitter is not None

    def test_event_listener_registration(self):
        """Test registering an event listener."""
        emitter = EventEmitter()
        callback = lambda data: None

        emitter.on(EventType.PROJECT_CREATED, callback)
        # Should not raise

    def test_event_emission_basic(self):
        """Test basic event emission."""
        emitter = EventEmitter()
        received_data = {}

        def handler(data):
            received_data.update({"received": True, "data": data})

        emitter.on(EventType.PROJECT_CREATED, handler)
        emitter.emit(EventType.PROJECT_CREATED, {"project_id": "123"})

        assert received_data.get("received") is True
        assert received_data.get("data") == {"project_id": "123"}

    def test_multiple_listeners(self):
        """Test multiple listeners for same event."""
        emitter = EventEmitter()
        results = []

        def handler1(data):
            results.append("handler1")

        def handler2(data):
            results.append("handler2")

        emitter.on(EventType.PROJECT_CREATED, handler1)
        emitter.on(EventType.PROJECT_CREATED, handler2)

        emitter.emit(EventType.PROJECT_CREATED, {})

        assert "handler1" in results
        assert "handler2" in results
        assert len(results) == 2

    def test_different_event_types(self):
        """Test different event types don't interfere."""
        emitter = EventEmitter()
        results = []

        def handler1(data):
            results.append("created")

        def handler2(data):
            results.append("saved")

        emitter.on(EventType.PROJECT_CREATED, handler1)
        emitter.on(EventType.PROJECT_SAVED, handler2)

        emitter.emit(EventType.PROJECT_CREATED, {})
        assert results == ["created"]

        emitter.emit(EventType.PROJECT_SAVED, {})
        assert results == ["created", "saved"]

    def test_event_data_passed_correctly(self):
        """Test that event data is passed to handlers."""
        emitter = EventEmitter()
        received_data = {}

        def handler(data):
            received_data.update(data)

        test_data = {"key1": "value1", "key2": "value2"}
        emitter.on(EventType.CODE_GENERATED, handler)
        emitter.emit(EventType.CODE_GENERATED, test_data)

        assert received_data == test_data

    def test_remove_listener(self):
        """Test removing an event listener."""
        emitter = EventEmitter()
        results = []

        def handler(data):
            results.append("called")

        emitter.on(EventType.PROJECT_CREATED, handler)
        emitter.emit(EventType.PROJECT_CREATED, {})
        assert len(results) == 1

        emitter.off(EventType.PROJECT_CREATED, handler)
        emitter.emit(EventType.PROJECT_CREATED, {})
        assert len(results) == 1  # Should not increase

    def test_emit_without_listeners(self):
        """Test emitting event without listeners."""
        emitter = EventEmitter()
        # Should not raise
        emitter.emit(EventType.PROJECT_CREATED, {"test": "data"})

    def test_listener_exception_handling(self):
        """Test that exceptions in listeners don't break emitter."""
        emitter = EventEmitter()
        results = []

        def bad_handler(data):
            raise ValueError("Handler error")

        def good_handler(data):
            results.append("called")

        emitter.on(EventType.PROJECT_CREATED, bad_handler)
        emitter.on(EventType.PROJECT_CREATED, good_handler)

        # Should handle exception gracefully
        emitter.emit(EventType.PROJECT_CREATED, {})

        # Good handler should still be called
        assert "called" in results

    def test_decorator_syntax(self):
        """Test using decorator syntax for listeners."""
        emitter = EventEmitter()
        results = []

        @emitter.on(EventType.PROJECT_CREATED)
        def handler(data):
            results.append("decorator")

        emitter.emit(EventType.PROJECT_CREATED, {})
        assert "decorator" in results

    def test_once_listener(self):
        """Test listener that fires only once."""
        emitter = EventEmitter()
        results = []

        def handler(data):
            results.append("called")

        emitter.once(EventType.PROJECT_CREATED, handler)

        emitter.emit(EventType.PROJECT_CREATED, {})
        assert len(results) == 1

        emitter.emit(EventType.PROJECT_CREATED, {})
        assert len(results) == 1  # Should not increase

    def test_clear_all_listeners(self):
        """Test clearing all listeners."""
        emitter = EventEmitter()
        results = []

        def handler(data):
            results.append("called")

        emitter.on(EventType.PROJECT_CREATED, handler)
        emitter.on(EventType.PROJECT_SAVED, handler)

        emitter.emit(EventType.PROJECT_CREATED, {})
        emitter.emit(EventType.PROJECT_SAVED, {})
        assert len(results) == 2

        emitter.clear_all()

        emitter.emit(EventType.PROJECT_CREATED, {})
        emitter.emit(EventType.PROJECT_SAVED, {})
        assert len(results) == 2  # Should not increase

    def test_get_listeners(self):
        """Test getting listeners for an event."""
        emitter = EventEmitter()

        def handler1(data):
            pass

        def handler2(data):
            pass

        emitter.on(EventType.PROJECT_CREATED, handler1)
        emitter.on(EventType.PROJECT_CREATED, handler2)

        listeners = emitter.get_listeners(EventType.PROJECT_CREATED)
        assert len(listeners) >= 2


class TestAsyncEventEmitter:
    """Tests for async event handling."""

    @pytest.mark.asyncio
    async def test_async_listener(self):
        """Test async event listener."""
        emitter = EventEmitter()
        results = []

        async def async_handler(data):
            await asyncio.sleep(0.01)
            results.append("async")

        emitter.on_async(EventType.PROJECT_CREATED, async_handler)
        await emitter.emit_async(EventType.PROJECT_CREATED, {})

        assert "async" in results

    @pytest.mark.asyncio
    async def test_multiple_async_listeners(self):
        """Test multiple async listeners."""
        emitter = EventEmitter()
        results = []

        async def handler1(data):
            results.append("handler1")

        async def handler2(data):
            results.append("handler2")

        emitter.on_async(EventType.PROJECT_CREATED, handler1)
        emitter.on_async(EventType.PROJECT_CREATED, handler2)

        await emitter.emit_async(EventType.PROJECT_CREATED, {})

        assert "handler1" in results
        assert "handler2" in results

    @pytest.mark.asyncio
    async def test_mixed_sync_and_async(self):
        """Test mixing sync and async listeners."""
        emitter = EventEmitter()
        results = []

        def sync_handler(data):
            results.append("sync")

        async def async_handler(data):
            results.append("async")

        emitter.on(EventType.PROJECT_CREATED, sync_handler)
        emitter.on_async(EventType.PROJECT_CREATED, async_handler)

        # Sync emission shouldn't wait for async
        emitter.emit(EventType.PROJECT_CREATED, {})
        assert "sync" in results

        # Async emission should wait for async handlers
        await emitter.emit_async(EventType.PROJECT_CREATED, {})
        assert "async" in results


class TestEventEmitterEdgeCases:
    """Tests for edge cases and corner cases."""

    def test_null_data(self):
        """Test handling null/None data."""
        emitter = EventEmitter()
        received = {}

        def handler(data):
            received["data"] = data

        emitter.on(EventType.PROJECT_CREATED, handler)
        emitter.emit(EventType.PROJECT_CREATED, None)

        assert received.get("data") is None

    def test_empty_dict_data(self):
        """Test handling empty dict data."""
        emitter = EventEmitter()
        received = {}

        def handler(data):
            received["data"] = data

        emitter.on(EventType.PROJECT_CREATED, handler)
        emitter.emit(EventType.PROJECT_CREATED, {})

        assert received.get("data") == {}

    def test_complex_nested_data(self):
        """Test handling complex nested data structures."""
        emitter = EventEmitter()
        received = {}

        def handler(data):
            received["data"] = data

        complex_data = {
            "nested": {
                "level2": {
                    "level3": ["value1", "value2"]
                }
            },
            "list": [1, 2, 3],
            "tuple": (4, 5, 6),
        }

        emitter.on(EventType.PROJECT_CREATED, handler)
        emitter.emit(EventType.PROJECT_CREATED, complex_data)

        assert received.get("data") == complex_data

    def test_large_data_payload(self):
        """Test handling large data payloads."""
        emitter = EventEmitter()
        received = {}

        def handler(data):
            received["data"] = data

        large_data = {"content": "x" * 10000}

        emitter.on(EventType.PROJECT_CREATED, handler)
        emitter.emit(EventType.PROJECT_CREATED, large_data)

        assert received.get("data") == large_data
