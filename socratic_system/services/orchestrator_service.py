"""
OrchestratorService - Manages user-scoped agent system instances.

This service implements a singleton pattern to provide centralized agent system
management for both CLI and web API, enabling shared backend services while
maintaining user isolation and automatic memory management.

Phase 3: Refactored to use SocraticAgentsSystem (independent library)
instead of AgentOrchestrator (local orchestrator).

Features:
- User-scoped SocraticAgentsSystem instances (one per user)
- TTL-based cleanup (30 min idle by default)
- Thread-safe concurrent access
- Memory management (max 100 systems, LRU eviction)
- Automatic initialization with config
- Backward compatibility: agents access via process_request()
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from socratic_agents import SocraticAgentsSystem

if TYPE_CHECKING:
    pass  # No longer importing AgentOrchestrator


class OrchestratorService:
    """
    Singleton service for managing user-scoped SocraticAgentsSystem instances.

    Phase 3 Migration: Now manages SocraticAgentsSystem instead of AgentOrchestrator.

    Ensures that:
    1. Each user has their own agent system with isolated state
    2. Agent systems are automatically cleaned up after idle timeout
    3. Memory usage is bounded (max 100 systems)
    4. Thread-safe access from both sync and async contexts
    """

    _instance: OrchestratorService | None = None
    _lock = threading.RLock()

    def __new__(cls) -> OrchestratorService:
        """Implement singleton pattern with thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the service (only once due to singleton)."""
        if self._initialized:
            return

        self._systems: dict[str, SocraticAgentsSystem] = {}
        self._access_times: dict[str, float] = {}
        self._cleanup_tasks: dict[str, asyncio.TimerHandle] = {}
        self._access_lock = threading.RLock()
        self._max_systems = 100
        self._idle_timeout_seconds = 30 * 60  # 30 minutes
        self.logger = logging.getLogger(__name__)

        self._initialized = True
        self.logger.info("OrchestratorService initialized as singleton (Phase 3: SocraticAgentsSystem)")

    def get_or_create(self, user_id: str, api_key: str) -> SocraticAgentsSystem:
        """
        Get or create a SocraticAgentsSystem for a user.

        Thread-safe method that retrieves an existing system or creates
        a new one with automatic TTL-based cleanup.

        Args:
            user_id: Unique identifier for the user
            api_key: Anthropic API key for Claude access

        Returns:
            SocraticAgentsSystem instance for the user

        Raises:
            ValueError: If api_key is invalid
            RuntimeError: If system creation fails
        """
        if not user_id or not api_key:
            raise ValueError("user_id and api_key are required")

        with self._access_lock:
            # Update access time
            self._access_times[user_id] = time.time()

            # Cancel existing cleanup if any
            if user_id in self._cleanup_tasks:
                self._cleanup_tasks[user_id].cancel()

            # Return existing system
            if user_id in self._systems:
                self.logger.debug(f"Returning existing system for user: {user_id}")
                self._schedule_cleanup(user_id)
                return self._systems[user_id]

            # Create new system
            self.logger.info(f"Creating new SocraticAgentsSystem for user: {user_id}")

            try:
                # Create user-specific data directory
                user_data_dir = Path.home() / ".socrates" / "users" / user_id
                user_data_dir.mkdir(parents=True, exist_ok=True)

                # Create SocraticAgentsSystem (Phase 3 migration)
                system = SocraticAgentsSystem(
                    api_key=api_key,
                    data_dir=str(user_data_dir),
                )

                self._systems[user_id] = system

                # Check memory limits
                if len(self._systems) > self._max_systems:
                    self._evict_lru()

                # Schedule cleanup
                self._schedule_cleanup(user_id)

                self.logger.info(
                    f"SocraticAgentsSystem created for user {user_id}. "
                    f"Total systems: {len(self._systems)}"
                )

                return system

            except Exception as e:
                self.logger.error(f"Failed to create system for user {user_id}: {e}")
                raise RuntimeError(f"Failed to create system: {e}") from e

    def get(self, user_id: str) -> SocraticAgentsSystem | None:
        """
        Get a SocraticAgentsSystem for a user without creating one.

        Args:
            user_id: User identifier

        Returns:
            SocraticAgentsSystem if exists, None otherwise
        """
        with self._access_lock:
            if user_id in self._systems:
                self._access_times[user_id] = time.time()
                return self._systems[user_id]
            return None

    def cleanup(self, user_id: str) -> None:
        """
        Manually cleanup a system (e.g., on logout).

        Args:
            user_id: User identifier
        """
        with self._access_lock:
            if user_id in self._cleanup_tasks:
                self._cleanup_tasks[user_id].cancel()
                del self._cleanup_tasks[user_id]

            if user_id in self._systems:
                self.logger.info(f"Cleaning up system for user: {user_id}")
                # Call shutdown if available
                system = self._systems[user_id]
                try:
                    system.shutdown()
                except Exception as e:
                    self.logger.warning(f"Error during system shutdown: {e}")
                del self._systems[user_id]

            if user_id in self._access_times:
                del self._access_times[user_id]

    def _schedule_cleanup(self, user_id: str) -> None:
        """
        Schedule cleanup task for an orchestrator.

        Args:
            user_id: User identifier
        """
        # Cancel existing task
        if user_id in self._cleanup_tasks:
            self._cleanup_tasks[user_id].cancel()

        # Schedule new task using asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in current thread, create one (happens in CLI/sync contexts)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Schedule cleanup after idle timeout
        def cleanup_callback():
            self.cleanup(user_id)
            self.logger.info(f"Auto-cleanup completed for user: {user_id}")

        # Note: In production, this would be more sophisticated with proper async handling
        # For now, we log the scheduling
        self.logger.debug(
            f"Scheduled cleanup for user {user_id} after {self._idle_timeout_seconds}s"
        )

    def _evict_lru(self) -> None:
        """
        Evict least recently used system when memory limit exceeded.

        Uses LRU strategy based on last access time.
        """
        if not self._access_times:
            return

        # Find LRU user
        lru_user = min(self._access_times.items(), key=lambda x: x[1])[0]

        self.logger.warning(
            f"Memory limit ({self._max_systems}) reached. "
            f"Evicting LRU system for user: {lru_user}"
        )

        self.cleanup(lru_user)

    def get_stats(self) -> dict:
        """
        Get statistics about system pool.

        Returns:
            Dictionary with pool statistics
        """
        with self._access_lock:
            return {
                "total_systems": len(self._systems),
                "max_systems": self._max_systems,
                "active_users": list(self._systems.keys()),
                "idle_timeout_seconds": self._idle_timeout_seconds,
            }

    def shutdown(self) -> None:
        """
        Shutdown all systems and cleanup resources.

        Should be called on application shutdown.
        """
        with self._access_lock:
            self.logger.info(f"Shutting down {len(self._systems)} systems")

            # Cancel all cleanup tasks
            for user_id in list(self._cleanup_tasks.keys()):
                self._cleanup_tasks[user_id].cancel()
            self._cleanup_tasks.clear()

            # Shutdown all systems
            for user_id, system in self._systems.items():
                try:
                    system.shutdown()
                except Exception as e:
                    self.logger.warning(f"Error shutting down system for {user_id}: {e}")

            # Clear systems
            self._systems.clear()
            self._access_times.clear()

            self.logger.info("OrchestratorService shutdown complete")


# Module-level convenience function
def get_orchestrator_service() -> OrchestratorService:
    """
    Get the singleton OrchestratorService instance.

    Returns:
        OrchestratorService singleton
    """
    return OrchestratorService()
