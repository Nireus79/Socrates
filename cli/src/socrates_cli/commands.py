"""
Commands module for Socrates CLI

Provides functionality for discovering, documenting, and executing commands
through the unified Commands API endpoint.
"""

import logging
from typing import Dict, List, Optional, Any

import httpx

logger = logging.getLogger(__name__)


class CommandClient:
    """Client for interacting with the Socrates Commands API."""

    def __init__(self, api_url: str):
        """
        Initialize the command client.

        Args:
            api_url: Base API URL (e.g., http://localhost:8000)
        """
        self.api_url = api_url
        self.base_endpoint = f"{api_url}/commands"

    def list_commands(self, category: Optional[str] = None, timeout: float = 30.0) -> Dict[str, Any]:
        """
        List all available commands, optionally filtered by category.

        Args:
            category: Optional category to filter by
            timeout: Request timeout in seconds

        Returns:
            Dictionary with status and command data

        Raises:
            httpx.RequestError: If API request fails
        """
        try:
            with httpx.Client(timeout=timeout) as client:
                params = {}
                if category:
                    params["category"] = category

                response = client.get(f"{self.base_endpoint}/", params=params)
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            logger.error(f"Failed to list commands: {e}")
            raise

    def list_categories(self, timeout: float = 30.0) -> Dict[str, Any]:
        """
        List all available command categories.

        Args:
            timeout: Request timeout in seconds

        Returns:
            Dictionary with status and category list

        Raises:
            httpx.RequestError: If API request fails
        """
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(f"{self.base_endpoint}/categories")
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            logger.error(f"Failed to list categories: {e}")
            raise

    def get_help(self, command: Optional[str] = None, timeout: float = 30.0) -> Dict[str, Any]:
        """
        Get help documentation for a command or all commands.

        Args:
            command: Optional command name to get help for
            timeout: Request timeout in seconds

        Returns:
            Dictionary with status and help text

        Raises:
            httpx.RequestError: If API request fails
        """
        try:
            with httpx.Client(timeout=timeout) as client:
                params = {}
                if command:
                    params["command"] = command

                response = client.get(f"{self.base_endpoint}/help", params=params)
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            logger.error(f"Failed to get help: {e}")
            raise

    def get_command_info(self, command_name: str, timeout: float = 30.0) -> Dict[str, Any]:
        """
        Get metadata for a specific command.

        Args:
            command_name: Name of the command
            timeout: Request timeout in seconds

        Returns:
            Dictionary with command metadata

        Raises:
            httpx.RequestError: If API request fails
            httpx.HTTPStatusError: If command not found
        """
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(f"{self.base_endpoint}/{command_name}")
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error(f"Command '{command_name}' not found")
            raise
        except httpx.RequestError as e:
            logger.error(f"Failed to get command info: {e}")
            raise

    def execute_command(
        self,
        command: str,
        args: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Execute a command through the API.

        Args:
            command: Command name or alias
            args: Optional list of command arguments
            project_id: Optional project ID for context
            session_id: Optional session ID for context
            timeout: Request timeout in seconds

        Returns:
            Dictionary with execution result and status

        Raises:
            httpx.RequestError: If API request fails
        """
        try:
            payload = {
                "command": command,
                "args": args or [],
                "project_id": project_id,
                "session_id": session_id,
            }

            with httpx.Client(timeout=timeout) as client:
                response = client.post(f"{self.base_endpoint}/execute", json=payload)
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            logger.error(f"Failed to execute command: {e}")
            raise

    def search_commands(self, query: str) -> List[str]:
        """
        Search for commands matching a query string.

        Args:
            query: Search query (searches command names and descriptions)

        Returns:
            List of matching command names

        Raises:
            httpx.RequestError: If API request fails
        """
        try:
            result = self.list_commands()
            query_lower = query.lower()

            matching = []
            for cmd_name, cmd_data in result.get("data", {}).items():
                if (
                    query_lower in cmd_name.lower()
                    or query_lower in cmd_data.get("description", "").lower()
                ):
                    matching.append(cmd_name)

            return matching

        except httpx.RequestError as e:
            logger.error(f"Failed to search commands: {e}")
            raise


# Global command client instance
_client: Optional[CommandClient] = None


def get_command_client(api_url: str) -> CommandClient:
    """Get or create the global command client."""
    global _client
    if _client is None or _client.api_url != api_url:
        _client = CommandClient(api_url)
    return _client
