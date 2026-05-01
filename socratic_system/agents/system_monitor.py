"""
System monitoring agent for Socrates AI

Phase 2B Migration: Async-first implementation with agent bus support
"""

import asyncio
import datetime
from typing import Any, Dict

from socratic_system.models import TokenUsage

from .base import Agent


class SystemMonitorAgent(Agent):
    """Monitors system health, token usage, and API limits

    Phase 2B Migration: Async-first implementation
    - Supports both sync (process) and async (process_async) interfaces
    - Registers with agent bus for discovery
    - In-memory state management (token tracking)
    """

    def __init__(self, orchestrator):
        super().__init__("SystemMonitor", orchestrator, auto_register=True)
        self.token_usage = []
        self.connection_status = True
        self.last_health_check = datetime.datetime.now()

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process monitoring requests (sync wrapper for backward compatibility)

        Phase 2B: Delegates to async implementation
        """
        action = request.get("action")

        if action == "track_tokens":
            return self._track_tokens(request)
        elif action == "check_health":
            return self._check_health_sync(request)
        elif action == "get_stats":
            return self._get_stats(request)
        elif action == "check_limits":
            return self._check_limits(request)

        return {"status": "error", "message": "Unknown action"}

    async def process_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process monitoring requests asynchronously (Phase 2B)

        Primary implementation - true async processing
        """
        action = request.get("action")

        if action == "track_tokens":
            return self._track_tokens(request)
        elif action == "check_health":
            return await self._check_health_async(request)
        elif action == "get_stats":
            return self._get_stats(request)
        elif action == "check_limits":
            return self._check_limits(request)

        return {"status": "error", "message": "Unknown action"}

    def get_capabilities(self) -> list:
        """Declare agent capabilities for bus discovery (Phase 2B)"""
        return [
            "system_monitoring",
            "health_check",
            "token_tracking",
            "limit_checking",
        ]

    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata for registration (Phase 2B)"""
        return {
            "version": "2.0",
            "description": "System health and token usage monitoring",
            "capabilities_count": 4,
        }

    def _track_tokens(self, request: Dict) -> Dict:
        """Track API token usage"""
        usage = TokenUsage(
            input_tokens=request.get("input_tokens", 0),
            output_tokens=request.get("output_tokens", 0),
            total_tokens=request.get("total_tokens", 0),
            cost_estimate=request.get("cost_estimate", 0.0),
            timestamp=datetime.datetime.now(),
        )

        self.token_usage.append(usage)

        # Check if approaching limits
        total_tokens = sum(u.total_tokens for u in self.token_usage[-10:])
        warning = total_tokens > 50000  # Warning threshold

        return {
            "status": "success",
            "current_usage": usage,
            "warning": warning,
            "total_recent": total_tokens,
        }

    def _check_health_sync(self, request: Dict) -> Dict:
        """Check system health synchronously (backward compatibility)

        Phase 2B: Legacy sync implementation
        """
        try:
            self.orchestrator.claude_client.test_connection()
            self.connection_status = True
            self.last_health_check = datetime.datetime.now()

            return {"status": "success", "connection": True, "last_check": self.last_health_check}
        except Exception as e:
            self.connection_status = False
            self.log(f"Health check failed: {e}", "ERROR")

            return {"status": "error", "connection": False, "error": str(e)}

    async def _check_health_async(self, request: Dict) -> Dict:
        """Check system health asynchronously (Phase 2B)

        Primary implementation - runs Claude API check in thread pool
        to avoid blocking event loop
        """
        try:
            # Run blocking API call in thread pool
            await asyncio.to_thread(
                self.orchestrator.claude_client.test_connection
            )
            self.connection_status = True
            self.last_health_check = datetime.datetime.now()

            return {"status": "success", "connection": True, "last_check": self.last_health_check}
        except Exception as e:
            self.connection_status = False
            self.log(f"Health check failed: {e}", "ERROR")

            return {"status": "error", "connection": False, "error": str(e)}

    def _get_stats(self, request: Dict) -> Dict:
        """Get system statistics"""
        total_tokens = sum(u.total_tokens for u in self.token_usage)
        total_cost = sum(u.cost_estimate for u in self.token_usage)

        return {
            "status": "success",
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "api_calls": len(self.token_usage),
            "connection_status": self.connection_status,
        }

    def _check_limits(self, request: Dict) -> Dict:
        """Check if approaching usage limits"""
        recent_usage = sum(u.total_tokens for u in self.token_usage[-5:])
        warnings = []

        if recent_usage > 40000:
            warnings.append("High token usage detected")
        if not self.connection_status:
            warnings.append("API connection issues")

        return {"status": "success", "warnings": warnings, "recent_usage": recent_usage}
