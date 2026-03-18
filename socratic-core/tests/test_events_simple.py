"""Simplified tests for EventEmitter"""

from socratic_core.events import EventEmitter, EventType


def test_event_emitter_creation():
    """Test creating event emitter."""
    emitter = EventEmitter()
    assert emitter is not None


def test_event_listener_registration():
    """Test registering an event listener."""
    emitter = EventEmitter()
    called = []

    def callback(data):
        called.append(data)

    emitter.on(EventType.LOG_INFO, callback)
    emitter.emit(EventType.LOG_INFO, {"message": "test"})

    assert len(called) > 0


def test_event_once():
    """Test once() listener - should only fire once."""
    emitter = EventEmitter()
    call_count = [0]

    def callback(data):
        call_count[0] += 1

    emitter.once(EventType.LOG_INFO, callback)
    emitter.emit(EventType.LOG_INFO, {"message": "first"})
    emitter.emit(EventType.LOG_INFO, {"message": "second"})

    assert call_count[0] == 1


def test_async_event_emission():
    """Test async event emission."""
    import asyncio

    emitter = EventEmitter()
    called = []

    async def async_callback(data):
        called.append(data)

    emitter.on(EventType.LOG_INFO, async_callback)

    async def test():
        await emitter.emit_async(EventType.LOG_INFO, {"message": "async"})
        return len(called) > 0

    result = asyncio.run(test())
    assert result
