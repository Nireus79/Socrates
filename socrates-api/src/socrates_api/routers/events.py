"""
Events API endpoints for Socrates.

Provides event history and streaming endpoints for tracking API activity.
"""

import asyncio
import json
import logging
from collections import deque
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from socrates_api.models import APIResponse
from socratic_system.database import ProjectDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/events", tags=["events"])

# In-memory event queue (FIFO) - stores last 1000 events
_event_queue = deque(maxlen=1000)
_event_subscribers = []  # List of async queues for streaming clients


def get_database() -> ProjectDatabase:
    """Get database instance."""
    import os
    from pathlib import Path

    data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
    db_path = os.path.join(data_dir, "projects.db")
    return ProjectDatabase(db_path)


def record_event(event_type: str, data: dict = None, user_id: str = None) -> None:
    """
    Record an event to the in-memory event queue.

    Args:
        event_type: Type of event (e.g., 'project_created', 'code_generated')
        data: Event data as dictionary
        user_id: User who triggered the event
    """
    event = {
        "id": f"evt_{len(_event_queue)}",
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "data": data or {},
    }
    _event_queue.append(event)
    logger.info(f"Event recorded: {event_type}")

    # Notify all streaming subscribers
    for subscriber_queue in _event_subscribers[:]:
        try:
            subscriber_queue.put_nowait(event)
        except asyncio.QueueFull:
            _event_subscribers.remove(subscriber_queue)


@router.get(
    "/history",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get event history",
    responses={
        200: {"description": "Event history retrieved"},
    },
)
async def get_event_history(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    event_type: Optional[str] = None,
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get historical events from the API.

    Args:
        limit: Maximum number of events to return (default: 100)
        offset: Number of events to skip (default: 0)
        event_type: Optional filter by event type
        db: Database connection

    Returns:
        Dictionary with list of events
    """
    try:
        logger.info(f"Getting event history: limit={limit}, offset={offset}, type={event_type}")

        # Get events from in-memory queue
        all_events = list(_event_queue)

        # Filter by type if specified
        if event_type:
            all_events = [e for e in all_events if e.get("type") == event_type]

        # Reverse to show newest first
        all_events.reverse()

        # Apply pagination
        paginated_events = all_events[offset : offset + limit] if limit else all_events[offset:]
        total = len(all_events)

        logger.info(f"Returning {len(paginated_events)} events (total: {total})")

        return APIResponse(
            success=True,
            status="success",
            message=f"Retrieved {len(paginated_events)} events",
            data={
                "events": paginated_events,
                "total": total,
                "limit": limit,
                "offset": offset,
                "event_type_filter": event_type,
            },
        )

    except Exception as e:
        logger.error(f"Error getting event history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get event history: {str(e)}",
        )


@router.get(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Stream events",
    responses={
        200: {"description": "Event stream established"},
    },
)
async def stream_events(
    db: ProjectDatabase = Depends(get_database),
):
    """
    Stream events as they occur (Server-Sent Events).

    Args:
        db: Database connection

    Returns:
        StreamingResponse with server-sent events
    """
    try:
        logger.info("Starting event stream")

        async def event_generator():
            # Create a queue for this subscriber
            subscriber_queue = asyncio.Queue(maxsize=100)
            _event_subscribers.append(subscriber_queue)

            try:
                # Send connection acknowledgment
                yield f"data: {json.dumps({'type': 'connected', 'message': 'Connected to event stream'})}\n\n"

                # Stream existing events first
                for event in list(_event_queue)[-20:]:  # Last 20 events
                    yield f"data: {json.dumps(event)}\n\n"
                    await asyncio.sleep(0.01)  # Small delay between events

                # Stream new events as they come
                while True:
                    try:
                        # Wait for new event (5 minute timeout)
                        event = await asyncio.wait_for(subscriber_queue.get(), timeout=300)
                        yield f"data: {json.dumps(event)}\n\n"
                    except asyncio.TimeoutError:
                        # Keep connection alive with heartbeat
                        yield ": heartbeat\n\n"
                    except asyncio.CancelledError:
                        break
            finally:
                # Clean up subscriber
                if subscriber_queue in _event_subscribers:
                    _event_subscribers.remove(subscriber_queue)
                logger.info("Event stream closed")

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable proxy buffering
            },
        )

    except Exception as e:
        logger.error(f"Error establishing event stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to establish event stream: {str(e)}",
        )
