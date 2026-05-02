"""
Event handlers for decoupled event processing.

Provides:
- Handler registration and execution
- Event listener patterns
- Async event processing
- Error handling for handlers
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from socratic_system.events.event_emitter import EventEmitter


class EventHandler:
    """Wrapper for event handler with metadata"""

    def __init__(
        self,
        event_type: str,
        handler: Callable,
        async_handler: bool = False,
    ):
        """
        Initialize event handler.

        Args:
            event_type: Type of event to handle
            handler: Handler function
            async_handler: Whether handler is async
        """
        self.event_type = event_type
        self.handler = handler
        self.async_handler = async_handler
        self.execution_count = 0
        self.error_count = 0

    async def execute(self, data: Dict[str, Any]) -> Any:
        """
        Execute handler.

        Args:
            data: Event data

        Returns:
            Handler result
        """
        try:
            self.execution_count += 1

            if self.async_handler:
                return await self.handler(data)
            else:
                return self.handler(data)

        except Exception as e:
            self.error_count += 1
            logging.error(
                f"Error executing handler for {self.event_type}: {e}"
            )
            raise


class EventHandlerRegistry:
    """Registry for event handlers"""

    def __init__(self):
        """Initialize handler registry"""
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.logger = logging.getLogger(__name__)

    def register(
        self,
        event_type: str,
        handler: Callable,
        async_handler: bool = False,
    ) -> None:
        """
        Register event handler.

        Args:
            event_type: Type of event
            handler: Handler function
            async_handler: Whether handler is async
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        handler_obj = EventHandler(event_type, handler, async_handler)
        self.handlers[event_type].append(handler_obj)

        self.logger.debug(f"Registered handler for {event_type}")

    def unregister(self, event_type: str, handler: Callable) -> None:
        """
        Unregister event handler.

        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        if event_type in self.handlers:
            self.handlers[event_type] = [
                h for h in self.handlers[event_type]
                if h.handler != handler
            ]

    async def execute_handlers(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> List[Any]:
        """
        Execute all handlers for event type.

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            List of handler results
        """
        if event_type not in self.handlers:
            return []

        results = []
        for handler in self.handlers[event_type]:
            try:
                result = await handler.execute(data)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Handler execution failed: {e}")

        return results

    def get_handlers(self, event_type: str) -> List[EventHandler]:
        """
        Get handlers for event type.

        Args:
            event_type: Type of event

        Returns:
            List of handlers
        """
        return self.handlers.get(event_type, [])

    def get_stats(self) -> Dict[str, Any]:
        """
        Get handler statistics.

        Returns:
            Statistics dictionary
        """
        stats = {}
        for event_type, handlers in self.handlers.items():
            stats[event_type] = {
                "handler_count": len(handlers),
                "total_executions": sum(h.execution_count for h in handlers),
                "total_errors": sum(h.error_count for h in handlers),
            }
        return stats


class AsyncEventProcessor:
    """Async event processor for background event handling"""

    def __init__(self, event_emitter: EventEmitter):
        """
        Initialize async processor.

        Args:
            event_emitter: EventEmitter instance
        """
        self.event_emitter = event_emitter
        self.handler_registry = EventHandlerRegistry()
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.queue: asyncio.Queue = asyncio.Queue()

    async def start(self) -> None:
        """Start background event processor"""
        self.running = True
        self.logger.info("Async event processor started")

    async def stop(self) -> None:
        """Stop background event processor"""
        self.running = False
        self.logger.info("Async event processor stopped")

    def register_handler(
        self,
        event_type: str,
        handler: Callable,
        async_handler: bool = False,
    ) -> None:
        """
        Register handler.

        Args:
            event_type: Type of event
            handler: Handler function
            async_handler: Whether handler is async
        """
        self.handler_registry.register(
            event_type, handler, async_handler
        )

    async def process_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> List[Any]:
        """
        Process event asynchronously.

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            Results from handlers
        """
        return await self.handler_registry.execute_handlers(
            event_type, data
        )

    async def emit_and_process(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> List[Any]:
        """
        Emit event and process asynchronously.

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            Handler results
        """
        self.event_emitter.emit(event_type, data)
        return await self.process_event(event_type, data)
