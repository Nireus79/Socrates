"""
Tests for Phase 3.8 - TLS Integration

Tests secure client-server communication, certificate validation,
encryption, and request handling.
"""

import pytest
from datetime import datetime

from socratic_system.agents.secure_agent_client import (
    SecureAgentClient,
    SecureRequest,
    SecureResponse,
)
from socratic_system.agents.secure_agent_server import SecureAgentServer


class TestSecureRequest:
    """Test SecureRequest dataclass."""

    def test_secure_request_creation(self):
        """SecureRequest creates with all fields."""
        req = SecureRequest(
            request_id="req_001",
            source_agent="agent1",
            target_agent="agent2",
            action="test_action",
            parameters={"key": "value"},
            timestamp=datetime.utcnow(),
        )

        assert req.request_id == "req_001"
        assert req.source_agent == "agent1"
        assert req.target_agent == "agent2"
        assert req.action == "test_action"


class TestSecureResponse:
    """Test SecureResponse dataclass."""

    def test_secure_response_creation(self):
        """SecureResponse creates with all fields."""
        resp = SecureResponse(
            request_id="req_001",
            source_agent="agent2",
            status_code=200,
            data={"result": "success"},
        )

        assert resp.request_id == "req_001"
        assert resp.status_code == 200
        assert resp.data == {"result": "success"}
        assert resp.timestamp is not None


class TestSecureAgentClient:
    """Test SecureAgentClient."""

    def setup_method(self):
        """Set up client."""
        self.client = SecureAgentClient(
            source_agent_id="agent1",
            client_certificate_pem="-----BEGIN CERTIFICATE-----\nclient_cert\n-----END CERTIFICATE-----",
            client_private_key_pem="-----BEGIN PRIVATE KEY-----\nclient_key\n-----END PRIVATE KEY-----",
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )

    def test_client_initialization(self):
        """Client initializes correctly."""
        assert self.client.source_agent_id == "agent1"
        assert self.client.request_count == 0
        assert len(self.client.active_connections) == 0

    def test_client_connect(self):
        """Client can establish connection."""
        success = self.client.connect(
            target_agent_id="agent2",
            target_certificate_pem="-----BEGIN CERTIFICATE-----\ntarget_cert\n-----END CERTIFICATE-----",
        )

        assert success
        assert len(self.client.active_connections) == 1

    def test_client_connect_invalid_certificate(self):
        """Client rejects invalid certificates."""
        success = self.client.connect(
            target_agent_id="agent2",
            target_certificate_pem="invalid",  # Missing BEGIN/END markers
        )

        assert not success
        assert len(self.client.active_connections) == 0

    def test_client_send_request(self):
        """Client can send encrypted request."""
        # First connect
        self.client.connect(
            target_agent_id="agent2",
            target_certificate_pem="-----BEGIN CERTIFICATE-----\ntarget_cert\n-----END CERTIFICATE-----",
        )

        # Then send request
        response = self.client.send_request(
            target_agent_id="agent2",
            action="test_action",
            parameters={"key": "value"},
        )

        assert response is not None
        assert isinstance(response, SecureResponse)
        assert response.status_code == 200

    def test_client_multiple_requests(self):
        """Client increments request counter."""
        self.client.connect(
            target_agent_id="agent2",
            target_certificate_pem="-----BEGIN CERTIFICATE-----\ntarget_cert\n-----END CERTIFICATE-----",
        )

        self.client.send_request(
            target_agent_id="agent2",
            action="action1",
            parameters={},
        )

        assert self.client.request_count == 1

        self.client.send_request(
            target_agent_id="agent2",
            action="action2",
            parameters={},
        )

        assert self.client.request_count == 2

    def test_client_close_connection(self):
        """Client can close connections."""
        self.client.connect(
            target_agent_id="agent2",
            target_certificate_pem="-----BEGIN CERTIFICATE-----\ntarget_cert\n-----END CERTIFICATE-----",
        )

        assert len(self.client.active_connections) == 1

        success = self.client.close_connection("agent2")
        assert success
        assert len(self.client.active_connections) == 0

    def test_client_connection_status(self):
        """Client reports connection status."""
        self.client.connect(
            target_agent_id="agent2",
            target_certificate_pem="-----BEGIN CERTIFICATE-----\ntarget_cert\n-----END CERTIFICATE-----",
        )

        status = self.client.get_connection_status()
        assert len(status) == 1
        assert any("agent2" in key for key in status.keys())


class TestSecureAgentServer:
    """Test SecureAgentServer."""

    def setup_method(self):
        """Set up server."""
        self.server = SecureAgentServer(
            agent_id="agent2",
            server_certificate_pem="-----BEGIN CERTIFICATE-----\nserver_cert\n-----END CERTIFICATE-----",
            server_private_key_pem="-----BEGIN PRIVATE KEY-----\nserver_key\n-----END PRIVATE KEY-----",
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )

    def test_server_initialization(self):
        """Server initializes correctly."""
        assert self.server.agent_id == "agent2"
        assert not self.server.is_running
        assert len(self.server.request_handlers) == 0

    def test_server_start(self):
        """Server can start."""
        success = self.server.start()
        assert success
        assert self.server.is_running

    def test_server_stop(self):
        """Server can stop."""
        self.server.start()
        assert self.server.is_running

        success = self.server.stop()
        assert success
        assert not self.server.is_running

    def test_server_register_handler(self):
        """Server can register action handlers."""
        def test_handler(params):
            return {"status": "ok", "params": params}

        self.server.register_handler("test_action", test_handler)
        assert "test_action" in self.server.request_handlers

    def test_server_handle_request(self):
        """Server can handle requests."""
        def test_handler(params):
            return {"result": params.get("key")}

        self.server.register_handler("test_action", test_handler)

        response = self.server.handle_request(
            request_id="req_001",
            source_agent="agent1",
            action="test_action",
            parameters={"key": "value"},
        )

        assert response["status_code"] == 200
        assert response["data"]["result"] == "value"

    def test_server_handle_unknown_action(self):
        """Server rejects unknown actions."""
        response = self.server.handle_request(
            request_id="req_001",
            source_agent="agent1",
            action="unknown_action",
            parameters={},
        )

        assert response["status_code"] == 404
        assert "Unknown action" in response["error"]

    def test_server_handler_exception(self):
        """Server handles exceptions in handlers."""
        def failing_handler(params):
            raise Exception("Test error")

        self.server.register_handler("failing_action", failing_handler)

        response = self.server.handle_request(
            request_id="req_001",
            source_agent="agent1",
            action="failing_action",
            parameters={},
        )

        assert response["status_code"] == 500
        assert "Test error" in response["error"]

    def test_server_request_logging(self):
        """Server logs received requests."""
        def test_handler(params):
            return {"ok": True}

        self.server.register_handler("test_action", test_handler)

        self.server.handle_request(
            request_id="req_001",
            source_agent="agent1",
            action="test_action",
            parameters={"data": "test"},
        )

        log = self.server.get_request_log()
        assert "req_001" in log
        assert log["req_001"]["source_agent"] == "agent1"

    def test_server_get_certificate(self):
        """Server provides certificate for TLS handshake."""
        cert = self.server.get_certificate()
        assert "BEGIN CERTIFICATE" in cert

    def test_server_status(self):
        """Server provides status information."""
        def handler1(params):
            return {}

        def handler2(params):
            return {}

        self.server.register_handler("action1", handler1)
        self.server.register_handler("action2", handler2)

        status = self.server.get_server_status()

        assert status["agent_id"] == "agent2"
        assert status["is_running"] is False
        assert len(status["handlers_registered"]) == 2
        assert "action1" in status["handlers_registered"]


class TestSecureClientServerIntegration:
    """Test client-server integration."""

    def test_client_server_communication(self):
        """Client and server can communicate securely."""
        # Set up server
        server = SecureAgentServer(
            agent_id="agent2",
            server_certificate_pem="-----BEGIN CERTIFICATE-----\nserver_cert\n-----END CERTIFICATE-----",
            server_private_key_pem="-----BEGIN PRIVATE KEY-----\nserver_key\n-----END PRIVATE KEY-----",
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )

        def echo_handler(params):
            return {"echo": params.get("message")}

        server.register_handler("echo", echo_handler)
        server.start()

        # Set up client
        client = SecureAgentClient(
            source_agent_id="agent1",
            client_certificate_pem="-----BEGIN CERTIFICATE-----\nclient_cert\n-----END CERTIFICATE-----",
            client_private_key_pem="-----BEGIN PRIVATE KEY-----\nclient_key\n-----END PRIVATE KEY-----",
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )

        # Client connects to server
        assert client.connect(
            target_agent_id="agent2",
            target_certificate_pem=server.get_certificate(),
        )

        # Client sends request
        response = client.send_request(
            target_agent_id="agent2",
            action="echo",
            parameters={"message": "hello"},
        )

        assert response is not None
        assert response.status_code == 200

    def test_multiple_handlers(self):
        """Server can handle multiple action types."""
        server = SecureAgentServer(
            agent_id="agent2",
            server_certificate_pem="-----BEGIN CERTIFICATE-----\nserver_cert\n-----END CERTIFICATE-----",
            server_private_key_pem="-----BEGIN PRIVATE KEY-----\nserver_key\n-----END PRIVATE KEY-----",
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )

        server.register_handler("add", lambda p: {"result": p.get("a", 0) + p.get("b", 0)})
        server.register_handler("multiply", lambda p: {"result": p.get("a", 0) * p.get("b", 0)})

        r1 = server.handle_request("req1", "agent1", "add", {"a": 5, "b": 3})
        r2 = server.handle_request("req2", "agent1", "multiply", {"a": 5, "b": 3})

        assert r1["data"]["result"] == 8
        assert r2["data"]["result"] == 15
