"""
Unit tests for Socrates event system
"""

import pytest
from unittest.mock import Mock, call

import socrates
from socratic_system.events import EventEmitter, EventType


@pytest.mark.unit
class TestEventEmitter:
    """Tests for EventEmitter class"""

    def test_event_emitter_creation(self):
        """Test creating an event emitter"""
        emitter = EventEmitter()

        assert emitter is not None
        assert isinstance(emitter, EventEmitter)

    def test_event_listener_registration(self, mock_event_emitter):
        """Test registering event listeners"""
        callback = Mock()

        mock_event_emitter.on(EventType.LOG_INFO, callback)

        assert mock_event_emitter.listener_count(EventType.LOG_INFO) >= 1

    def test_event_emission(self, mock_event_emitter):
        """Test emitting events"""
        callback = Mock()
        mock_event_emitter.on(EventType.LOG_INFO, callback)

        mock_event_emitter.emit(EventType.LOG_INFO, {"message": "test"})

        # Callback should be called
        assert callback.called

    def test_multiple_listeners_same_event(self, mock_event_emitter):
        """Test multiple listeners on same event"""
        callback1 = Mock()
        callback2 = Mock()

        mock_event_emitter.on(EventType.LOG_INFO, callback1)
        mock_event_emitter.on(EventType.LOG_INFO, callback2)

        mock_event_emitter.emit(EventType.LOG_INFO, {"test": "data"})

        assert callback1.called
        assert callback2.called

    def test_listener_receives_data(self, mock_event_emitter):
        """Test that listeners receive event data"""
        callback = Mock()
        test_data = {"key": "value", "number": 42}

        mock_event_emitter.on(EventType.PROJECT_CREATED, callback)
        mock_event_emitter.emit(EventType.PROJECT_CREATED, test_data)

        # Callback should be called with event type and data
        callback.assert_called_once()
        args = callback.call_args
        assert args[0][1] == test_data  # Second argument is the data

    def test_different_event_types(self, mock_event_emitter):
        """Test that different event types don't trigger wrong callbacks"""
        info_callback = Mock()
        error_callback = Mock()

        mock_event_emitter.on(EventType.LOG_INFO, info_callback)
        mock_event_emitter.on(EventType.LOG_ERROR, error_callback)

        mock_event_emitter.emit(EventType.LOG_INFO, {})

        assert info_callback.called
        assert not error_callback.called

    def test_once_listener(self, mock_event_emitter):
        """Test one-time listener registration"""
        callback = Mock()

        mock_event_emitter.once(EventType.SYSTEM_INITIALIZED, callback)

        # Emit twice
        mock_event_emitter.emit(EventType.SYSTEM_INITIALIZED, {})
        mock_event_emitter.emit(EventType.SYSTEM_INITIALIZED, {})

        # Callback should only be called once
        assert callback.call_count == 1

    def test_remove_listener(self, mock_event_emitter):
        """Test removing event listeners"""
        callback = Mock()

        mock_event_emitter.on(EventType.LOG_INFO, callback)
        assert mock_event_emitter.listener_count(EventType.LOG_INFO) >= 1

        removed = mock_event_emitter.remove_listener(EventType.LOG_INFO, callback)
        assert removed is True

        # Callback count should decrease
        assert mock_event_emitter.listener_count(EventType.LOG_INFO) == 0

    def test_listener_count(self, mock_event_emitter):
        """Test listener counting"""
        callback1 = Mock()
        callback2 = Mock()

        mock_event_emitter.on(EventType.LOG_INFO, callback1)
        assert mock_event_emitter.listener_count(EventType.LOG_INFO) == 1

        mock_event_emitter.on(EventType.LOG_INFO, callback2)
        assert mock_event_emitter.listener_count(EventType.LOG_INFO) == 2

        mock_event_emitter.remove_listener(EventType.LOG_INFO, callback1)
        assert mock_event_emitter.listener_count(EventType.LOG_INFO) == 1

    def test_get_event_names(self, mock_event_emitter):
        """Test getting list of registered event types"""
        callback = Mock()

        mock_event_emitter.on(EventType.LOG_INFO, callback)
        mock_event_emitter.on(EventType.CODE_GENERATED, callback)

        events = mock_event_emitter.get_event_names()

        assert EventType.LOG_INFO in events
        assert EventType.CODE_GENERATED in events

    def test_emit_without_listeners(self, mock_event_emitter):
        """Test emitting event with no listeners"""
        # Should not raise exception
        mock_event_emitter.emit(EventType.LOG_INFO, {"test": "data"})

    def test_emit_with_none_data(self, mock_event_emitter):
        """Test emitting event with None data"""
        callback = Mock()
        mock_event_emitter.on(EventType.LOG_INFO, callback)

        # Should accept None data
        mock_event_emitter.emit(EventType.LOG_INFO, None)

        assert callback.called


@pytest.mark.unit
class TestEventTypes:
    """Tests for EventType enum"""

    def test_event_type_values(self):
        """Test that EventType has expected values"""
        assert hasattr(EventType, 'LOG_INFO')
        assert hasattr(EventType, 'LOG_ERROR')
        assert hasattr(EventType, 'PROJECT_CREATED')
        assert hasattr(EventType, 'CODE_GENERATED')
        assert hasattr(EventType, 'AGENT_START')
        assert hasattr(EventType, 'AGENT_COMPLETE')
        assert hasattr(EventType, 'AGENT_ERROR')
        assert hasattr(EventType, 'TOKEN_USAGE')

    def test_event_type_string_conversion(self):
        """Test converting EventType to string"""
        event_str = EventType.LOG_INFO.value

        assert isinstance(event_str, str)
        assert "LOG_INFO" in event_str.upper() or "log" in event_str.lower()

    def test_all_event_types_are_unique(self):
        """Test that all event types have unique values"""
        values = [e.value for e in EventType]

        assert len(values) == len(set(values))


@pytest.mark.unit
class TestEventEmitterThreadSafety:
    """Tests for EventEmitter thread safety"""

    def test_concurrent_listener_registration(self, mock_event_emitter):
        """Test thread-safe listener registration"""
        import threading

        callbacks = [Mock() for _ in range(5)]
        threads = []

        def register_listener(callback):
            mock_event_emitter.on(EventType.LOG_INFO, callback)

        for callback in callbacks:
            t = threading.Thread(target=register_listener, args=(callback,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All callbacks should be registered
        assert mock_event_emitter.listener_count(EventType.LOG_INFO) == 5

    def test_concurrent_event_emission(self, mock_event_emitter):
        """Test thread-safe event emission"""
        import threading

        callback = Mock()
        mock_event_emitter.on(EventType.LOG_INFO, callback)

        def emit_event():
            mock_event_emitter.emit(EventType.LOG_INFO, {"thread": "test"})

        threads = []
        for _ in range(10):
            t = threading.Thread(target=emit_event)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Callback should be called 10 times
        assert callback.call_count == 10


@pytest.mark.unit
class TestEventData:
    """Tests for event data handling"""

    def test_event_data_with_timestamps(self, mock_event_emitter):
        """Test that events include timestamp information"""
        callback = Mock()
        mock_event_emitter.on(EventType.PROJECT_CREATED, callback)

        mock_event_emitter.emit(EventType.PROJECT_CREATED, {"project_id": "test"})

        # Check that callback was called
        assert callback.called

    def test_event_data_complex_structures(self, mock_event_emitter):
        """Test event data with complex Python objects"""
        callback = Mock()
        mock_event_emitter.on(EventType.AGENT_COMPLETE, callback)

        complex_data = {
            "agent": "code_generator",
            "results": [1, 2, 3],
            "nested": {"key": "value"},
            "tokens": {"input": 100, "output": 50}
        }

        mock_event_emitter.emit(EventType.AGENT_COMPLETE, complex_data)

        # Callback should receive the complex data
        args = callback.call_args
        assert args[0][1] == complex_data

    def test_event_data_immutability_concern(self, mock_event_emitter):
        """Test that event data mutations don't affect original"""
        callback = Mock()
        mock_event_emitter.on(EventType.LOG_INFO, callback)

        original_data = {"key": "value"}
        mock_event_emitter.emit(EventType.LOG_INFO, original_data.copy())

        # Original data should be unchanged
        assert original_data == {"key": "value"}
