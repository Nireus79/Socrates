"""WebSocket endpoints for real-time analysis result polling.

Complements HTTP GET polling with WebSocket for live updates as analyses complete.
"""

import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocketDisconnect, WebSocket
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections per project
active_subscriptions: Dict[str, Set[WebSocket]] = {}


@router.websocket("/ws/analysis/{project_id}")
async def websocket_analysis_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for subscribing to analysis result updates.

    Client connects and receives real-time updates as analysis results become available.
    
    Connection Flow:
    1. Client connects: ws://server/ws/analysis/{project_id}
    2. Server sends {"type": "subscribed", "project_id": "..."}
    3. Client receives updates as analyses complete:
       - {"type": "quality.completed", "data": {...}}
       - {"type": "conflicts.completed", "data": {...}}
       - {"type": "insights.completed", "data": {...}}
    4. Client can disconnect anytime
    
    Args:
        websocket: WebSocket connection
        project_id: Project identifier
    """
    await websocket.accept()
    logger.info(f"[WebSocket] Client subscribed to project {project_id}")

    # Register this connection
    if project_id not in active_subscriptions:
        active_subscriptions[project_id] = set()
    active_subscriptions[project_id].add(websocket)

    try:
        # Send subscription confirmation
        await websocket.send_json(
            {
                "type": "subscribed",
                "project_id": project_id,
                "message": f"Subscribed to analysis updates for {project_id}",
            }
        )

        # Keep connection open and wait for client messages
        while True:
            data = await websocket.receive_text()

            # Handle ping/pong
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                logger.debug(f"[WebSocket] Received from client: {data}")

    except WebSocketDisconnect:
        logger.info(f"[WebSocket] Client disconnected from project {project_id}")
        active_subscriptions[project_id].discard(websocket)

    except Exception as e:
        logger.error(f"[WebSocket] Error in websocket: {str(e)}")
        active_subscriptions[project_id].discard(websocket)
        await websocket.close()


async def broadcast_analysis_update(
    project_id: str, analysis_type: str, result: Dict
) -> None:
    """Broadcast analysis result update to all subscribers.

    Called by background handlers when analysis completes.

    Args:
        project_id: Project identifier
        analysis_type: Type of analysis (quality, conflicts, insights)
        result: Analysis result data
    """
    if project_id not in active_subscriptions:
        return

    disconnected = set()

    for websocket in active_subscriptions[project_id]:
        try:
            await websocket.send_json(
                {
                    "type": f"{analysis_type}.completed",
                    "project_id": project_id,
                    "data": result,
                }
            )
            logger.debug(
                f"[WebSocket] Sent {analysis_type} update to client for {project_id}"
            )

        except Exception as e:
            logger.error(f"[WebSocket] Error sending to client: {str(e)}")
            disconnected.add(websocket)

    # Remove disconnected clients
    for websocket in disconnected:
        active_subscriptions[project_id].discard(websocket)


async def broadcast_analysis_status(
    project_id: str, status: Dict[str, str]
) -> None:
    """Broadcast overall analysis status to all subscribers.

    Args:
        project_id: Project identifier
        status: Status dict with pending/processing/completed counts
    """
    if project_id not in active_subscriptions:
        return

    for websocket in active_subscriptions[project_id]:
        try:
            await websocket.send_json(
                {
                    "type": "status.update",
                    "project_id": project_id,
                    "status": status,
                }
            )
        except Exception as e:
            logger.error(f"[WebSocket] Error sending status: {str(e)}")


@router.get("/ws/active-subscriptions")
async def get_active_subscriptions() -> Dict[str, int]:
    """Get count of active WebSocket subscriptions per project.

    For monitoring/debugging purposes.

    Returns:
        Dict with project_id -> subscriber_count
    """
    return {
        project_id: len(sockets)
        for project_id, sockets in active_subscriptions.items()
        if sockets
    }
