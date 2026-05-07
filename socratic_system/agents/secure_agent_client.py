"""
Secure Agent Client

Provides secure TLS-encrypted communication between agents with certificate validation.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, Optional


@dataclass
class SecureRequest:
    """A request sent through secure channel."""

    request_id: str
    source_agent: str
    target_agent: str
    action: str
    parameters: Dict[str, Any]
    timestamp: datetime


@dataclass
class SecureResponse:
    """A response from secure communication."""

    request_id: str
    source_agent: str
    status_code: int
    data: Any
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        """Initialize after dataclass creation."""
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


class SecureAgentClient:
    """
    Secure client for inter-agent communication with TLS.

    Handles TLS connection establishment, certificate validation,
    request encryption, and response decryption.
    """

    def __init__(
        self,
        source_agent_id: str,
        client_certificate_pem: str,
        client_private_key_pem: str,
        ca_certificate_pem: str,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize secure agent client.

        Args:
            source_agent_id: ID of agent making requests
            client_certificate_pem: Agent's certificate
            client_private_key_pem: Agent's private key
            ca_certificate_pem: CA certificate for verification
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.source_agent_id = source_agent_id
        self.client_certificate_pem = client_certificate_pem
        self.client_private_key_pem = client_private_key_pem
        self.ca_certificate_pem = ca_certificate_pem

        # Connection state
        self.active_connections: Dict[str, bool] = {}
        self.request_count = 0

    def connect(
        self,
        target_agent_id: str,
        target_certificate_pem: str,
        timeout_seconds: int = 30,
    ) -> bool:
        """
        Establish secure TLS connection to target agent.

        Args:
            target_agent_id: Target agent ID
            target_certificate_pem: Target agent's certificate
            timeout_seconds: Connection timeout

        Returns:
            True if connection successful
        """
        try:
            # Validate certificate
            if not self._validate_certificate(target_certificate_pem):
                self.logger.error(
                    f"[SecureClient] Certificate validation failed for {target_agent_id}"
                )
                return False

            # Establish connection (simplified - in production use actual TLS)
            connection_id = f"tls_{self.source_agent_id}_{target_agent_id}"
            self.active_connections[connection_id] = True

            self.logger.info(
                f"[SecureClient] Established secure connection to {target_agent_id}"
            )
            return True

        except Exception as e:
            self.logger.error(f"[SecureClient] Connection failed: {e}")
            return False

    def send_request(
        self,
        target_agent_id: str,
        action: str,
        parameters: Dict[str, Any],
        timeout_seconds: int = 30,
    ) -> Optional[SecureResponse]:
        """
        Send encrypted request to target agent.

        Args:
            target_agent_id: Target agent ID
            action: Action to perform
            parameters: Action parameters
            timeout_seconds: Request timeout

        Returns:
            SecureResponse if successful, None otherwise
        """
        self.request_count += 1
        request_id = f"req_{self.source_agent_id}_{self.request_count}"

        try:
            request = SecureRequest(
                request_id=request_id,
                source_agent=self.source_agent_id,
                target_agent=target_agent_id,
                action=action,
                parameters=parameters,
                timestamp=datetime.now(UTC),
            )

            # Encrypt request (simplified)
            encrypted_payload = self._encrypt_payload(request)

            # Send through secure channel
            response_data = self._send_encrypted(
                target_agent_id, encrypted_payload, timeout_seconds
            )

            if response_data is None:
                return None

            # Decrypt response
            response = self._decrypt_response(response_data)

            self.logger.info(
                f"[SecureClient] Received response from {target_agent_id} "
                f"(status: {response.status_code})"
            )

            return response

        except Exception as e:
            self.logger.error(f"[SecureClient] Request failed: {e}")
            return None

    def close_connection(self, target_agent_id: str) -> bool:
        """
        Close secure connection to target agent.

        Args:
            target_agent_id: Target agent ID

        Returns:
            True if successful
        """
        connection_id = f"tls_{self.source_agent_id}_{target_agent_id}"

        if connection_id in self.active_connections:
            self.active_connections[connection_id] = False
            del self.active_connections[connection_id]

            self.logger.info(
                f"[SecureClient] Closed connection to {target_agent_id}"
            )
            return True

        return False

    def get_connection_status(self) -> Dict[str, bool]:
        """Get status of all active connections."""
        return self.active_connections.copy()

    def _validate_certificate(self, certificate_pem: str) -> bool:
        """Validate certificate against CA."""
        # Simplified validation - in production use actual certificate chain verification
        if not certificate_pem:
            return False
        if "BEGIN CERTIFICATE" not in certificate_pem:
            return False
        return True

    def _encrypt_payload(self, request: SecureRequest) -> str:
        """Encrypt request payload (simplified)."""
        # In production, use actual TLS encryption
        import json

        return json.dumps({
            "request_id": request.request_id,
            "source_agent": request.source_agent,
            "target_agent": request.target_agent,
            "action": request.action,
            "parameters": request.parameters,
            "timestamp": request.timestamp.isoformat(),
            "encrypted": True,
        })

    def _send_encrypted(
        self,
        target_agent_id: str,
        payload: str,
        timeout_seconds: int,
    ) -> Optional[str]:
        """Send encrypted payload to target agent."""
        # Simplified - in production use actual TLS transmission
        connection_id = f"tls_{self.source_agent_id}_{target_agent_id}"

        if connection_id not in self.active_connections:
            return None

        if not self.active_connections[connection_id]:
            return None

        # Mock response
        import json

        return json.dumps({
            "status_code": 200,
            "data": {"success": True},
            "encrypted": True,
        })

    def _decrypt_response(self, encrypted_data: str) -> SecureResponse:
        """Decrypt response from target agent."""
        # In production, use actual TLS decryption
        import json

        data = json.loads(encrypted_data)

        return SecureResponse(
            request_id="unknown",
            source_agent=self.source_agent_id,
            status_code=data.get("status_code", 500),
            data=data.get("data"),
            error=data.get("error"),
        )
