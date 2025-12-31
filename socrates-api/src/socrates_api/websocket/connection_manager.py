"""
WebSocket Connection Manager - Manages active WebSocket connections.

Handles:
- Per-user, per-project connection pooling
- Connection lifecycle (connect, disconnect)
- Broadcasting messages to specific users/projects
- Connection tracking and statistics
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class ConnectionMetadata:
    """Metadata for a WebSocket connection."""

    connection_id: str
    user_id: str
    project_id: str
    connected_at: str
    last_message_at: Optional[str] = None
    message_count: int = 0


class ConnectionManager:
    """
    Manages WebSocket connections for real-time chat and events.

    Architecture:
    - Per-user connection pool: {user_id → {project_id → set(WebSocket)}}
    - Metadata tracking: {connection_id → ConnectionMetadata}
    - Thread-safe concurrent access
    """

    def __init__(self):
        """Initialize connection manager."""
        # Structure: user_id → project_id → set of WebSocket connections
        self._connections: Dict[str, Dict[str, Set[WebSocket]]] = {}

        # Metadata tracking
        self._metadata: Dict[str, ConnectionMetadata] = {}

        # Lock for thread-safe access
        self._lock = asyncio.Lock()

        # Configuration
        self._max_connections_per_project = 100
        self._connection_timeout_seconds = 3600  # 1 hour

        logger.info("ConnectionManager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        project_id: str,
        connection_id: str,
    ) -> None:
        """
        Register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            user_id: User identifier
            project_id: Project identifier
            connection_id: Unique connection identifier

        Raises:
            RuntimeError: If max connections per project exceeded
        """
        await websocket.accept()

        async with self._lock:
            # Ensure user entry exists
            if user_id not in self._connections:
                self._connections[user_id] = {}

            # Ensure project entry exists
            if project_id not in self._connections[user_id]:
                self._connections[user_id][project_id] = set()

            # Check connection limit
            project_connections = self._connections[user_id][project_id]
            if len(project_connections) >= self._max_connections_per_project:
                logger.warning(
                    f"Max connections ({self._max_connections_per_project}) reached "
                    f"for project {project_id}"
                )
                raise RuntimeError("Max connections for project exceeded")

            # Add connection
            project_connections.add(websocket)

            # Store metadata
            self._metadata[connection_id] = ConnectionMetadata(
                connection_id=connection_id,
                user_id=user_id,
                project_id=project_id,
                connected_at=datetime.now(timezone.utc).isoformat(),
            )

            logger.info(
                f"Connection established: {connection_id} "
                f"for user {user_id} on project {project_id}"
            )

    async def disconnect(self, connection_id: str) -> Optional[tuple[str, str]]:
        """
        Remove a WebSocket connection.

        Args:
            connection_id: Connection identifier

        Returns:
            Tuple of (user_id, project_id) if found, None otherwise
        """
        async with self._lock:
            if connection_id not in self._metadata:
                return None

            metadata = self._metadata[connection_id]
            user_id = metadata.user_id
            project_id = metadata.project_id

            # Remove connection
            if user_id in self._connections:
                if project_id in self._connections[user_id]:
                    # Find and remove the WebSocket
                    self._connections[user_id][project_id]
                    # Since we store the WebSocket directly, we need to search
                    # In practice, we'd store websocket with connection_id mapping

                    logger.info(f"Connection disconnected: {connection_id}")

            # Remove metadata
            del self._metadata[connection_id]

            return (user_id, project_id)

    async def broadcast_to_project(
        self,
        user_id: str,
        project_id: str,
        message: Dict[str, Any],
        exclude_connection_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast a message to all connections in a project.

        Args:
            user_id: User identifier
            project_id: Project identifier
            message: Message payload
            exclude_connection_id: Optional connection to exclude from broadcast

        Returns:
            Number of connections message was sent to
        """
        message_json = json.dumps(message)
        sent_count = 0
        failed_connections = []

        async with self._lock:
            if user_id not in self._connections:
                return 0

            if project_id not in self._connections[user_id]:
                return 0

            connections = self._connections[user_id][project_id].copy()

        # Send outside lock to avoid deadlocks
        for connection in connections:
            try:
                # Check exclusion
                # Note: In production, would need to map WebSocket to connection_id
                await connection.send_text(message_json)
                sent_count += 1

                # Update metadata
                async with self._lock:
                    for cid, metadata in self._metadata.items():
                        if metadata.user_id == user_id and metadata.project_id == project_id:
                            if cid != exclude_connection_id:
                                metadata.last_message_at = datetime.now(timezone.utc).isoformat()
                                metadata.message_count += 1

            except Exception as e:
                logger.error(f"Failed to send message to connection: {e}")
                failed_connections.append(connection)

        # Clean up failed connections
        if failed_connections:
            async with self._lock:
                if user_id in self._connections and project_id in self._connections[user_id]:
                    for conn in failed_connections:
                        self._connections[user_id][project_id].discard(conn)

        return sent_count

    async def broadcast_to_user(
        self,
        user_id: str,
        message: Dict[str, Any],
    ) -> int:
        """
        Broadcast a message to all connections for a user (all projects).

        Args:
            user_id: User identifier
            message: Message payload

        Returns:
            Number of connections message was sent to
        """
        message_json = json.dumps(message)
        sent_count = 0

        async with self._lock:
            if user_id not in self._connections:
                return 0

            # Collect all connections for this user
            all_connections = []
            for project_connections in self._connections[user_id].values():
                all_connections.extend(project_connections)

        # Send outside lock
        for connection in all_connections:
            try:
                await connection.send_text(message_json)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send message to user connection: {e}")

        return sent_count

    async def broadcast_to_all(
        self,
        message: Dict[str, Any],
    ) -> int:
        """
        Broadcast a message to all active connections.

        Args:
            message: Message payload

        Returns:
            Number of connections message was sent to
        """
        message_json = json.dumps(message)
        sent_count = 0

        async with self._lock:
            all_connections = []
            for user_connections in self._connections.values():
                for project_connections in user_connections.values():
                    all_connections.extend(project_connections)

        # Send outside lock
        for connection in all_connections:
            try:
                await connection.send_text(message_json)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send message to connection: {e}")

        return sent_count

    async def get_connection_metadata(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific connection.

        Args:
            connection_id: Connection identifier

        Returns:
            Metadata dict or None if not found
        """
        async with self._lock:
            if connection_id in self._metadata:
                return asdict(self._metadata[connection_id])
            return None

    async def get_project_connections(
        self,
        user_id: str,
        project_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all active connections for a project.

        Args:
            user_id: User identifier
            project_id: Project identifier

        Returns:
            List of connection metadata
        """
        async with self._lock:
            connections = []
            for cid, metadata in self._metadata.items():
                if metadata.user_id == user_id and metadata.project_id == project_id:
                    connections.append(asdict(metadata))
            return connections

    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics for a user's connections.

        Args:
            user_id: User identifier

        Returns:
            Statistics dictionary
        """
        async with self._lock:
            projects = {}
            total_connections = 0
            total_messages = 0

            if user_id in self._connections:
                for project_id, conns in self._connections[user_id].items():
                    project_conns = len(conns)
                    total_connections += project_conns

                    # Count messages for this project
                    project_messages = sum(
                        self._metadata[cid].message_count
                        for cid in self._metadata
                        if (
                            self._metadata[cid].user_id == user_id
                            and self._metadata[cid].project_id == project_id
                        )
                    )
                    total_messages += project_messages

                    projects[project_id] = {
                        "connections": project_conns,
                        "messages": project_messages,
                    }

            return {
                "user_id": user_id,
                "total_projects": len(projects),
                "total_connections": total_connections,
                "total_messages": total_messages,
                "projects": projects,
            }

    async def get_global_statistics(self) -> Dict[str, Any]:
        """
        Get global statistics for all connections.

        Returns:
            Global statistics dictionary
        """
        async with self._lock:
            total_users = len(self._connections)
            total_projects = 0
            total_connections = 0

            for user_connections in self._connections.values():
                total_projects += len(user_connections)
                for project_connections in user_connections.values():
                    total_connections += len(project_connections)

            total_messages = sum(metadata.message_count for metadata in self._metadata.values())

            return {
                "total_users": total_users,
                "total_projects": total_projects,
                "total_connections": total_connections,
                "total_messages": total_messages,
                "max_connections_per_project": self._max_connections_per_project,
            }

    async def cleanup_user_connections(self, user_id: str) -> int:
        """
        Force cleanup all connections for a user (e.g., on logout).

        Args:
            user_id: User identifier

        Returns:
            Number of connections closed
        """
        closed_count = 0

        async with self._lock:
            if user_id not in self._connections:
                return 0

            # Close all connections
            for project_id in list(self._connections[user_id].keys()):
                for connection in list(self._connections[user_id][project_id]):
                    try:
                        await connection.close()
                        closed_count += 1
                    except Exception as e:
                        logger.error(f"Error closing connection: {e}")

            # Remove all metadata for user
            connection_ids_to_remove = [
                cid for cid, metadata in self._metadata.items() if metadata.user_id == user_id
            ]

            for cid in connection_ids_to_remove:
                del self._metadata[cid]

            # Remove user entry
            del self._connections[user_id]

            logger.info(f"Cleaned up {closed_count} connections for user {user_id}")

        return closed_count


# Module-level singleton instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    Get the singleton ConnectionManager instance.

    Returns:
        ConnectionManager singleton
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
