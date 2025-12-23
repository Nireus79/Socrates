"""
Events API endpoints for Socrates.

Provides event history and streaming endpoints for tracking API activity.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse

from socratic_system.database import ProjectDatabaseV2
from socrates_api.models import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/events", tags=["events"])


def get_database() -> ProjectDatabaseV2:
    """Get database instance."""
    from pathlib import Path
    import os
    data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
    db_path = os.path.join(data_dir, "projects.db")
    return ProjectDatabaseV2(db_path)


@router.get(
    "/history",
    status_code=status.HTTP_200_OK,
    summary="Get event history",
    responses={
        200: {"description": "Event history retrieved"},
    },
)
async def get_event_history(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get historical events from the API.

    Args:
        limit: Maximum number of events to return (default: 100)
        offset: Number of events to skip (default: 0)
        db: Database connection

    Returns:
        Dictionary with list of events
    """
    try:
        logger.info(f"Getting event history: limit={limit}, offset={offset}")

        # TODO: Query events from database
        events = [
            {
                "id": "event_1",
                "type": "project_created",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {"project_id": "proj_1", "name": "Test Project"},
            },
            {
                "id": "event_2",
                "type": "code_generated",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {"project_id": "proj_1", "lines": 150},
            },
        ]

        return {
            "events": events[offset : offset + limit] if limit else events[offset:],
            "total": len(events),
            "limit": limit,
            "offset": offset,
        }

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
    db: ProjectDatabaseV2 = Depends(get_database),
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
            # TODO: Implement actual streaming from event queue
            yield "data: {\"type\": \"connected\", \"message\": \"Connected to event stream\"}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        logger.error(f"Error establishing event stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to establish event stream: {str(e)}",
        )
