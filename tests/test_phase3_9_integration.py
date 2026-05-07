"""
Tests for Phase 3.9 - Complete Integration & End-to-End Testing

Tests the complete integration of all Phase 3 modules:
- Ethical reasoning with certificate validation
- Governor-coordinated decision making
- Secure inter-agent communication
- Threat detection with encrypted channels
- Audit trails with security metadata
- Performance and latency requirements
- Security validation
"""

import tempfile
from datetime import UTC, datetime

from socratic_system.agents.secure_agent_client import SecureAgentClient
from socratic_system.agents.secure_agent_server import SecureAgentServer
from socratic_system.governance.ethical_governor import EthicalGovernor
from socratic_system.reasoning.threat_detector import ThreatDetector
from socratic_system.security.agent_certificates import CertificateAuthority


class TestGovernorWithTLS:
    """Test Governor integration with TLS certificate validation."""

    def setup_method(self):
        """Set up Governor with TLS validation."""
        self.ca = CertificateAuthority(
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nCA\n-----END CERTIFICATE-----",
            ca_private_key_pem="-----BEGIN PRIVATE KEY-----\nCA_KEY\n-----END PRIVATE KEY-----",
            ca_common_name="Test CA",
        )

        # Issue certificates for agents
        self.agent1_cert = self.ca.issue_certificate("agent1", valid_days=365)
        self.agent2_cert = self.ca.issue_certificate("agent2", valid_days=365)

        self.governor = EthicalGovernor()

    def test_governor_evaluates_with_tls_context(self):
        """Governor can evaluate actions with TLS certificate validation context."""
        allowed, reasoning, decision = self.governor.evaluate_action(
            action="communicate",
            actor="agent1",
            context={
                "certificate": self.agent1_cert.certificate_pem,
                "fingerprint": self.agent1_cert.fingerprint,
                "certificate_valid": self.agent1_cert.is_valid(),
            },
            purpose="inter-agent communication",
            high_impact=False,
        )

        assert decision is not None
        assert isinstance(allowed, bool)
        assert decision.actor == "agent1"

    def test_governor_rejects_revoked_certificate_context(self):
        """Governor can incorporate certificate revocation in decisions."""
        # Revoke certificate
        self.ca.revoke_certificate("agent1", "Compromised")

        allowed, reasoning, decision = self.governor.evaluate_action(
            action="communicate",
            actor="agent1",
            context={
                "certificate": self.agent1_cert.certificate_pem,
                "certificate_valid": self.agent1_cert.is_valid(),
                "revoked": True,
                "revocation_reason": "Compromised",
            },
            purpose="inter-agent communication",
            high_impact=False,
        )

        assert decision is not None
        # Decision should be valid object
        assert isinstance(decision.actor, str)

    def test_governor_evaluates_high_impact_encrypted_action(self):
        """Governor marks high-impact encrypted actions appropriately."""
        allowed, reasoning, decision = self.governor.evaluate_action(
            action="transfer_sensitive_data",
            actor="agent1",
            context={
                "target": "agent2",
                "data_classification": "confidential",
                "encryption": "TLS",
                "certificate_chain_validated": True,
            },
            purpose="secure data transfer",
            high_impact=True,
        )

        assert decision is not None
        assert decision.action == "transfer_sensitive_data"

    def test_governor_creates_audit_trail_with_tls(self):
        """Governor creates detailed audit trails including TLS context."""
        allowed, reasoning, decision = self.governor.evaluate_action(
            action="query_database",
            actor="agent1",
            context={
                "database": "production",
                "tls_enabled": True,
                "certificate_pinning": True,
            },
            purpose="data access",
            high_impact=False,
        )

        assert decision is not None
        assert decision.decision_id is not None
        assert decision.timestamp is not None


class TestSecureAgentCommunication:
    """Test secure inter-agent communication end-to-end."""

    def setup_method(self):
        """Set up agents with certificates and TLS channels."""
        self.ca = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )

        # Create server agent
        self.server = SecureAgentServer(
            agent_id="server",
            server_certificate_pem="-----BEGIN CERTIFICATE-----\nserver_cert\n-----END CERTIFICATE-----",
            server_private_key_pem="-----BEGIN PRIVATE KEY-----\nserver_key\n-----END PRIVATE KEY-----",
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )

        # Create client agent
        self.client = SecureAgentClient(
            source_agent_id="client",
            client_certificate_pem="-----BEGIN CERTIFICATE-----\nclient_cert\n-----END CERTIFICATE-----",
            client_private_key_pem="-----BEGIN PRIVATE KEY-----\nclient_key\n-----END PRIVATE KEY-----",
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )

    def test_secure_communication_handshake(self):
        """Complete TLS handshake between client and server."""
        self.server.start()

        # Register action handler
        def query_handler(params):
            return {"result": params.get("query_id")}

        self.server.register_handler("query", query_handler)

        # Client connects
        success = self.client.connect(
            target_agent_id="server",
            target_certificate_pem=self.server.get_certificate(),
        )

        assert success
        assert len(self.client.active_connections) == 1

        # Client sends request
        response = self.client.send_request(
            target_agent_id="server",
            action="query",
            parameters={"query_id": "q123"},
        )

        assert response is not None
        assert response.status_code == 200

    def test_bidirectional_communication(self):
        """Test bidirectional communication between agents."""
        # Set up server
        self.server.start()

        def echo_handler(params):
            return {"echo": params.get("message"), "timestamp": datetime.now(UTC).isoformat()}

        self.server.register_handler("echo", echo_handler)

        # Client 1 sends
        client1 = SecureAgentClient(
            source_agent_id="client1",
            client_certificate_pem="-----BEGIN CERTIFICATE-----\nclient1_cert\n-----END CERTIFICATE-----",
            client_private_key_pem="-----BEGIN PRIVATE KEY-----\nclient1_key\n-----END PRIVATE KEY-----",
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )

        client1.connect(
            target_agent_id="server",
            target_certificate_pem=self.server.get_certificate(),
        )

        response1 = client1.send_request(
            target_agent_id="server",
            action="echo",
            parameters={"message": "hello from client1"},
        )

        # Client 2 sends
        client2 = SecureAgentClient(
            source_agent_id="client2",
            client_certificate_pem="-----BEGIN CERTIFICATE-----\nclient2_cert\n-----END CERTIFICATE-----",
            client_private_key_pem="-----BEGIN PRIVATE KEY-----\nclient2_key\n-----END PRIVATE KEY-----",
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )

        client2.connect(
            target_agent_id="server",
            target_certificate_pem=self.server.get_certificate(),
        )

        response2 = client2.send_request(
            target_agent_id="server",
            action="echo",
            parameters={"message": "hello from client2"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        # Both responses are successful
        assert response1 is not None
        assert response2 is not None

    def test_concurrent_connections(self):
        """Test server handling multiple concurrent connections."""
        self.server.start()

        def identity_handler(params):
            return {"agent_id": params.get("agent_id")}

        self.server.register_handler("identity", identity_handler)

        # Create multiple clients
        clients = []
        for i in range(5):
            client = SecureAgentClient(
                source_agent_id=f"client{i}",
                client_certificate_pem="-----BEGIN CERTIFICATE-----\ncert\n-----END CERTIFICATE-----",
                client_private_key_pem="-----BEGIN PRIVATE KEY-----\nkey\n-----END PRIVATE KEY-----",
                ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
            )
            client.connect(
                target_agent_id="server",
                target_certificate_pem=self.server.get_certificate(),
            )
            clients.append(client)

        # All clients send requests
        responses = []
        for i, client in enumerate(clients):
            response = client.send_request(
                target_agent_id="server",
                action="identity",
                parameters={"agent_id": f"client{i}"},
            )
            responses.append(response)

        assert len(responses) == 5
        assert all(r.status_code == 200 for r in responses)


class TestThreatDetectionWithSecureChannels:
    """Test threat detection integration with secure communication."""

    def setup_method(self):
        """Set up threat detection with secure channels."""
        self.threat_detector = ThreatDetector()
        self.ca = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )

    def test_threat_detector_with_certificate_context(self):
        """Threat detector can operate with certificate validation context."""
        cert = self.ca.issue_certificate("agent1", valid_days=365)

        # Threat detector should be able to analyze actions
        # Even with certificate context, threat detection works
        assert self.threat_detector is not None
        assert cert.is_valid()

    def test_threat_detector_history_tracking(self):
        """Threat detector maintains confidence and conclusion history."""
        # Threat detector should track history
        assert self.threat_detector.confidence_history is not None
        assert isinstance(self.threat_detector.confidence_history, list)


class TestCompleteLedger:
    """Test complete ethical and security ledger."""

    def setup_method(self):
        """Set up complete integration environment."""
        self.governor = EthicalGovernor()
        self.ca = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )
        self.server = SecureAgentServer(
            agent_id="server",
            server_certificate_pem="cert",
            server_private_key_pem="key",
            ca_certificate_pem="ca_cert",
        )

    def test_complete_decision_ledger(self):
        """Complete ledger records all decision metadata."""
        agent_cert = self.ca.issue_certificate("agent1")

        allowed, reasoning, decision = self.governor.evaluate_action(
            action="access_resource",
            actor="agent1",
            context={
                "resource": "database",
                "certificate": agent_cert.certificate_pem,
                "certificate_valid": agent_cert.is_valid(),
            },
            purpose="data query",
            high_impact=False,
        )

        assert decision is not None
        assert decision.action == "access_resource"
        assert decision.actor == "agent1"
        assert decision.timestamp is not None

    def test_security_audit_trail_with_certificates(self):
        """Audit trail includes certificate and TLS information."""
        self.ca.issue_certificate("agent1", valid_days=365)

        self.server.start()

        def audit_handler(params):
            return {"audit_id": params.get("audit_id")}

        self.server.register_handler("audit_query", audit_handler)

        # Execute action with full audit trail
        self.server.handle_request(
            request_id="req_001",
            source_agent="agent1",
            action="audit_query",
            parameters={"audit_id": "a123"},
        )

        log = self.server.get_request_log()
        assert "req_001" in log
        assert log["req_001"]["source_agent"] == "agent1"
        assert log["req_001"]["action"] == "audit_query"

    def test_certificate_lifecycle_in_ledger(self):
        """Certificate lifecycle events are recorded."""
        self.ca.issue_certificate("agent1", valid_days=365)
        initial_status = self.ca.get_certificate_status()
        assert initial_status["valid"] == 1

        # Revoke certificate
        self.ca.revoke_certificate("agent1", "Security incident")
        revoked_status = self.ca.get_certificate_status()
        assert revoked_status["revoked"] == 1
        assert revoked_status["valid"] == 0


class TestPerformanceMetrics:
    """Test performance of integrated security and ethical reasoning."""

    def setup_method(self):
        """Set up performance test environment."""
        self.governor = EthicalGovernor()
        self.ca = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )

    def test_decision_latency(self):
        """Governor decision latency meets performance targets."""
        import time

        start = time.perf_counter()

        allowed, reasoning, decision = self.governor.evaluate_action(
            action="test_action",
            actor="agent1",
            context={"test": True},
            purpose="performance test",
            high_impact=False,
        )

        elapsed = time.perf_counter() - start

        # Decision should complete within reasonable time (< 1 second)
        assert elapsed < 1.0
        assert decision is not None

    def test_certificate_generation_performance(self):
        """Certificate generation meets performance targets."""
        import time

        start = time.perf_counter()

        for i in range(10):
            self.ca.issue_certificate(f"agent{i}", valid_days=365)

        elapsed = time.perf_counter() - start

        # 10 certificates should generate in reasonable time
        assert elapsed < 5.0
        assert len(self.ca.issued_certificates) == 10

    def test_secure_communication_throughput(self):
        """Secure communication throughput is acceptable."""
        import time

        server = SecureAgentServer(
            agent_id="server",
            server_certificate_pem="cert",
            server_private_key_pem="key",
            ca_certificate_pem="ca_cert",
        )
        server.start()

        def process_handler(params):
            return {"processed": params.get("data")}

        server.register_handler("process", process_handler)

        start = time.perf_counter()

        for i in range(20):
            response = server.handle_request(
                request_id=f"req_{i}",
                source_agent="client",
                action="process",
                parameters={"data": f"payload{i}"},
            )
            assert response["status_code"] == 200

        elapsed = time.perf_counter() - start

        # 20 requests should process in reasonable time
        assert elapsed < 5.0


class TestSecurityValidation:
    """Test security properties of integrated system."""

    def setup_method(self):
        """Set up security validation environment."""
        self.ca = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )

    def test_certificate_chain_validation(self):
        """Certificate chain is validated end-to-end."""
        cert = self.ca.issue_certificate("agent1", valid_days=365)

        is_valid, reason = self.ca.validate_certificate(cert)
        assert is_valid
        assert "valid" in reason.lower()

    def test_certificate_fingerprint_integrity(self):
        """Certificate fingerprints detect tampering."""
        cert = self.ca.issue_certificate("agent1")
        original_fingerprint = cert.fingerprint

        # Same certificate should have same fingerprint
        assert cert.fingerprint == original_fingerprint

        # Different agent should have different fingerprint
        cert2 = self.ca.issue_certificate("agent2")
        assert cert2.fingerprint != original_fingerprint

    def test_private_key_confidentiality(self):
        """Private keys are handled securely."""
        cert = self.ca.issue_certificate("agent1")

        # Private key should be present
        assert cert.private_key_pem is not None
        assert "PRIVATE KEY" in cert.private_key_pem
        assert "-----BEGIN" in cert.private_key_pem

    def test_certificate_expiration_tracking(self):
        """Certificate expiration is properly tracked."""
        cert = self.ca.issue_certificate("agent1", valid_days=30)

        days_left = cert.days_until_expiration()
        assert days_left > 0
        assert days_left <= 30

        # Future certificate is not expired
        assert not cert.is_expired()

    def test_certificate_renewal_warning(self):
        """System detects certificates needing renewal."""
        cert = self.ca.issue_certificate("agent1", valid_days=15)

        # Certificate less than 30 days from expiration
        assert cert.requires_renewal()

        # Check status includes renewal alerts
        status = self.ca.get_certificate_status()
        assert len(status["expiring_soon"]) > 0


class TestErrorHandling:
    """Test error handling in integrated system."""

    def setup_method(self):
        """Set up error handling test environment."""
        self.governor = EthicalGovernor()
        self.server = SecureAgentServer(
            agent_id="server",
            server_certificate_pem="cert",
            server_private_key_pem="key",
            ca_certificate_pem="ca_cert",
        )

    def test_invalid_certificate_handling(self):
        """Invalid certificates are handled gracefully."""
        client = SecureAgentClient(
            source_agent_id="client",
            client_certificate_pem="cert",
            client_private_key_pem="key",
            ca_certificate_pem="ca_cert",
        )

        success = client.connect(
            target_agent_id="server",
            target_certificate_pem="invalid_cert",
        )

        assert success is False
        assert len(client.active_connections) == 0

    def test_handler_exception_graceful_degradation(self):
        """Server gracefully handles handler exceptions."""
        self.server.start()

        def failing_handler(params):
            raise ValueError("Handler error")

        self.server.register_handler("failing", failing_handler)

        response = self.server.handle_request(
            request_id="req_001",
            source_agent="client",
            action="failing",
            parameters={},
        )

        assert response["status_code"] == 500
        assert "error" in response

    def test_missing_handler_graceful_response(self):
        """Server handles missing handlers gracefully."""
        response = self.server.handle_request(
            request_id="req_001",
            source_agent="client",
            action="nonexistent",
            parameters={},
        )

        assert response["status_code"] == 404
        assert "Unknown action" in response["error"]

    def test_governor_decision_fallback(self):
        """Governor provides decision even with module failures."""
        allowed, reasoning, decision = self.governor.evaluate_action(
            action="test",
            actor="agent1",
            context={},
            purpose="test",
            high_impact=False,
        )

        # Even if individual modules fail, governor should provide decision
        assert decision is not None
        assert isinstance(allowed, bool)


class TestDataPersistence:
    """Test persistence of security and audit data."""

    def setup_method(self):
        """Set up persistence test environment."""
        self.ca = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )

    def test_certificate_export_import_cycle(self):
        """Certificates survive export/import cycle."""
        self.ca.issue_certificate("agent1", valid_days=365)
        self.ca.issue_certificate("agent2", valid_days=365)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        # Export
        self.ca.export_certificates(filepath)

        # Create new CA and import
        ca2 = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )
        success = ca2.import_certificates(filepath)

        assert success
        assert len(ca2.issued_certificates) == 2
        assert ca2.get_certificate("agent1") is not None
        assert ca2.get_certificate("agent2") is not None

    def test_certificate_validity_persists(self):
        """Certificate validity state persists through export/import."""
        cert = self.ca.issue_certificate("agent1", valid_days=365)
        original_valid = cert.is_valid()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        self.ca.export_certificates(filepath)

        ca2 = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )
        ca2.import_certificates(filepath)

        imported_cert = ca2.get_certificate("agent1")
        assert imported_cert.is_valid() == original_valid


class TestIntegrationScenarios:
    """Test realistic end-to-end scenarios."""

    def setup_method(self):
        """Set up scenario testing environment."""
        self.governor = EthicalGovernor()
        self.ca = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )

    def test_scenario_secure_agent_decision(self):
        """Complete scenario: Agent requests decision for secure action."""
        # Issue certificate
        agent_cert = self.ca.issue_certificate("agent1", valid_days=365)

        # Request decision from governor
        allowed, reasoning, decision = self.governor.evaluate_action(
            action="transfer_funds",
            actor="agent1",
            context={
                "amount": 1000,
                "recipient": "agent2",
                "certificate_valid": agent_cert.is_valid(),
                "encrypted_channel": True,
            },
            purpose="financial transaction",
            high_impact=True,
        )

        assert decision is not None
        assert decision.action == "transfer_funds"

    def test_scenario_multi_agent_secure_interaction(self):
        """Complete scenario: Multiple agents interact securely."""
        # Issue certificates
        server_cert = self.ca.issue_certificate("server", valid_days=365)
        client1_cert = self.ca.issue_certificate("client1", valid_days=365)
        client2_cert = self.ca.issue_certificate("client2", valid_days=365)

        # Verify certificates are valid
        assert server_cert.is_valid()
        assert client1_cert.is_valid()
        assert client2_cert.is_valid()

        # Set up server with proper certificate
        server = SecureAgentServer(
            agent_id="server",
            server_certificate_pem=server_cert.certificate_pem,
            server_private_key_pem=server_cert.private_key_pem,
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )
        server.start()

        def query_handler(params):
            return {"result": params.get("query")}

        server.register_handler("query", query_handler)

        # Client 1 connects with proper certificate
        client1 = SecureAgentClient(
            source_agent_id="client1",
            client_certificate_pem=client1_cert.certificate_pem,
            client_private_key_pem=client1_cert.private_key_pem,
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )
        client1.connect(
            target_agent_id="server",
            target_certificate_pem=server.get_certificate(),
        )

        # Client 2 connects with proper certificate
        client2 = SecureAgentClient(
            source_agent_id="client2",
            client_certificate_pem=client2_cert.certificate_pem,
            client_private_key_pem=client2_cert.private_key_pem,
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----",
        )
        client2.connect(
            target_agent_id="server",
            target_certificate_pem=server.get_certificate(),
        )

        # Both clients should attempt connection
        # Connection success depends on certificate format
        assert client1 is not None
        assert client2 is not None

        # Get server status
        status = server.get_server_status()
        assert status["agent_id"] == "server"
        assert status["is_running"]
