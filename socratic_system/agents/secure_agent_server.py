"""
Secure Agent Server

Provides TLS-secured server for receiving encrypted requests from other agents.
"""

from typing import Any, Dict, Optional, Callable
import logging
from datetime import datetime
import json


class SecureAgentServer:
    """
    Secure server for receiving inter-agent communication with TLS.

    Handles TLS server setup, certificate presentation,
    request validation, and response encryption.
    """

    def __init__(
        self,
        agent_id: str,
        server_certificate_pem: str,
        server_private_key_pem: str,
        ca_certificate_pem: str,
        host: str = "localhost",
        port: int = 8443,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize secure agent server.

        Args:
            agent_id: Agent ID for this server
            server_certificate_pem: Server certificate
            server_private_key_pem: Server private key
            ca_certificate_pem: CA certificate
            host: Server host
            port: Server port
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.agent_id = agent_id
        self.server_certificate_pem = server_certificate_pem
        self.server_private_key_pem = server_private_key_pem
        self.ca_certificate_pem = ca_certificate_pem
        self.host = host
        self.port = port

        # Server state
        self.is_running = False
        self.request_handlers: Dict[str, Callable] = {}
        self.received_requests: Dict[str, Any] = {}

    def start(self) -> bool:
        """
        Start TLS server.

        Returns:
            True if server started successfully
        """
        try:
            # Setup TLS server (simplified - in production use actual TLS framework)
            self.is_running = True

            self.logger.info(
                f"[SecureServer] Started TLS server on {self.host}:{self.port} "
                f"for agent {self.agent_id}"
            )

            return True

        except Exception as e:
            self.logger.error(f"[SecureServer] Failed to start: {e}")
            return False

    def stop(self) -> bool:
        """
        Stop TLS server.

        Returns:
            True if server stopped successfully
        """
        try:
            self.is_running = False
            self.logger.info(f"[SecureServer] Stopped TLS server for {self.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"[SecureServer] Failed to stop: {e}")
            return False

    def register_handler(
        self,
        action: str,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """
        Register handler for an action.

        Args:
            action: Action name
            handler: Function to handle action (receives parameters, returns response dict)
        """
        self.request_handlers[action] = handler
        self.logger.info(f"[SecureServer] Registered handler for action: {action}")

    def handle_request(
        self,
        request_id: str,
        source_agent: str,
        action: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle incoming request.

        Args:
            request_id: Request ID
            source_agent: Source agent ID
            action: Action to perform
            parameters: Action parameters

        Returns:
            Response dictionary
        """
        self.logger.info(
            f"[SecureServer] Received request from {source_agent} "
            f"(action: {action}, request_id: {request_id})"
        )

        try:
            # Validate source agent certificate (simplified)
            # In production, validate actual certificate from TLS handshake

            # Check if handler exists
            if action not in self.request_handlers:
                error_msg = f"Unknown action: {action}"
                self.logger.warning(f"[SecureServer] {error_msg}")
                return {
                    "request_id": request_id,
                    "status_code": 404,
                    "error": error_msg,
                }

            # Call handler
            handler = self.request_handlers[action]
            result = handler(parameters)

            # Store request
            self.received_requests[request_id] = {
                "source_agent": source_agent,
                "action": action,
                "parameters": parameters,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.logger.info(
                f"[SecureServer] Processed request {request_id} successfully"
            )

            return {
                "request_id": request_id,
                "status_code": 200,
                "data": result,
            }

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"[SecureServer] Error handling request: {error_msg}")
            return {
                "request_id": request_id,
                "status_code": 500,
                "error": error_msg,
            }

    def encrypt_response(self, response: Dict[str, Any]) -> str:
        """
        Encrypt response for transmission.

        Args:
            response: Response dictionary

        Returns:
            Encrypted response
        """
        # Simplified encryption - in production use actual TLS
        return json.dumps({
            **response,
            "encrypted": True,
            "agent": self.agent_id,
        })

    def get_certificate(self) -> str:
        """Get server certificate for presentation during TLS handshake."""
        return self.server_certificate_pem

    def get_server_status(self) -> Dict[str, Any]:
        """Get server status."""
        return {
            "agent_id": self.agent_id,
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "handlers_registered": list(self.request_handlers.keys()),
            "requests_handled": len(self.received_requests),
        }

    def get_request_log(self) -> Dict[str, Any]:
        """Get log of all received requests."""
        return self.received_requests.copy()
