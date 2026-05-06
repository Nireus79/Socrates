"""
Tests for Phase 3.5 - Mutual TLS Configuration

Tests certificate management, TLS configuration, and secure session establishment.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta

from socratic_system.security.mutual_tls import (
    MutualTLSManager,
    CertificateType,
    TLSVersion,
    MutualTLSPolicy,
)


class TestCertificateManagement:
    """Test certificate creation and management."""

    def setup_method(self):
        """Set up TLS manager."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.manager = MutualTLSManager(cert_directory=self.tmpdir.name)

    def teardown_method(self):
        """Clean up."""
        self.tmpdir.cleanup()

    def test_manager_initializes(self):
        """Manager initializes successfully."""
        assert self.manager is not None
        assert self.manager.logger is not None
        assert len(self.manager.certificates) == 0

    def test_create_certificate(self):
        """Can create a certificate."""
        cert = self.manager.create_certificate(
            name="test_cert",
            cert_type=CertificateType.AGENT,
            subject="CN=agent1",
            issuer="CN=root-ca",
            valid_days=365,
        )

        assert cert is not None
        assert cert.name == "test_cert"
        assert cert.cert_type == CertificateType.AGENT
        assert not cert.is_expired()

    def test_certificate_has_metadata(self):
        """Created certificate contains all metadata."""
        cert = self.manager.create_certificate(
            name="metadata_cert",
            cert_type=CertificateType.SERVER,
            subject="CN=server.example.com",
            issuer="CN=intermediate-ca",
            valid_days=90,
            key_bits=2048,
        )

        assert cert.subject == "CN=server.example.com"
        assert cert.issuer == "CN=intermediate-ca"
        assert cert.public_key_bits == 2048
        assert cert.is_valid

    def test_certificate_expiration_check(self):
        """Certificate expiration is tracked correctly."""
        # Create short-lived cert
        cert = self.manager.create_certificate(
            name="short_lived",
            cert_type=CertificateType.CLIENT,
            subject="CN=client1",
            issuer="CN=root",
            valid_days=1,
        )

        assert not cert.is_expired()
        assert cert.days_until_expiration() == 1


class TestTLSConfiguration:
    """Test TLS configuration for agents."""

    def setup_method(self):
        """Set up with certificates and configurations."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.manager = MutualTLSManager(cert_directory=self.tmpdir.name)

        # Create certificates
        self.manager.create_certificate(
            name="root_ca",
            cert_type=CertificateType.ROOT_CA,
            subject="CN=root-ca",
            issuer="CN=root-ca",
        )

        self.manager.create_certificate(
            name="agent1_cert",
            cert_type=CertificateType.AGENT,
            subject="CN=agent1",
            issuer="CN=root-ca",
        )

    def teardown_method(self):
        """Clean up."""
        self.tmpdir.cleanup()

    def test_create_agent_configuration(self):
        """Can create TLS configuration for an agent."""
        config = self.manager.create_agent_configuration(
            agent_id="agent1",
            certificate_name="agent1_cert",
            ca_certificate_name="root_ca",
        )

        assert config is not None
        assert config.agent_id == "agent1"
        assert config.is_valid()

    def test_configuration_has_correct_paths(self):
        """Configuration includes certificate paths."""
        config = self.manager.create_agent_configuration(
            agent_id="agent2",
            certificate_name="agent1_cert",
            ca_certificate_name="root_ca",
        )

        assert config.cert_path
        assert config.key_path
        assert config.ca_cert_path

    def test_configuration_has_cipher_suites(self):
        """Configuration includes cipher suites."""
        config = self.manager.create_agent_configuration(
            agent_id="agent3",
            certificate_name="agent1_cert",
            ca_certificate_name="root_ca",
        )

        assert len(config.cipher_suites) > 0


class TestCertificateValidation:
    """Test certificate validation against policy."""

    def setup_method(self):
        """Set up manager with policy."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.manager = MutualTLSManager(cert_directory=self.tmpdir.name)

        self.valid_cert = self.manager.create_certificate(
            name="valid",
            cert_type=CertificateType.AGENT,
            subject="CN=agent",
            issuer="CN=root",
            valid_days=100,
        )

    def teardown_method(self):
        """Clean up."""
        self.tmpdir.cleanup()

    def test_valid_certificate_passes_validation(self):
        """Valid certificate passes validation."""
        is_valid, reason = self.manager.validate_certificate(self.valid_cert)

        assert is_valid
        assert "valid" in reason.lower() or "recommended" in reason.lower()

    def test_expired_certificate_fails_validation(self):
        """Expired certificate fails validation."""
        expired_cert = self.manager.create_certificate(
            name="expired",
            cert_type=CertificateType.AGENT,
            subject="CN=agent",
            issuer="CN=root",
            valid_days=-1,  # Expired
        )

        is_valid, reason = self.manager.validate_certificate(expired_cert)

        assert not is_valid
        assert "expired" in reason.lower()


class TestSessionManagement:
    """Test TLS session establishment and management."""

    def setup_method(self):
        """Set up with configured agents."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.manager = MutualTLSManager(cert_directory=self.tmpdir.name)

        # Create certificates
        for name in ["root_ca", "agent1_cert", "agent2_cert"]:
            self.manager.create_certificate(
                name=name,
                cert_type=CertificateType.AGENT,
                subject=f"CN={name}",
                issuer="CN=root",
            )

        # Create configurations
        for agent_id, cert_name in [("agent1", "agent1_cert"), ("agent2", "agent2_cert")]:
            self.manager.create_agent_configuration(
                agent_id=agent_id,
                certificate_name=cert_name,
                ca_certificate_name="root_ca",
            )

    def teardown_method(self):
        """Clean up."""
        self.tmpdir.cleanup()

    def test_establish_session(self):
        """Can establish a TLS session."""
        session = self.manager.establish_session(
            agent_id="agent1",
            peer_agent_id="agent2",
        )

        assert session is not None
        assert session.agent_id == "agent1"
        assert session.peer_agent_id == "agent2"
        assert session.is_active

    def test_session_has_tls_info(self):
        """Session includes TLS information."""
        session = self.manager.establish_session(
            agent_id="agent1",
            peer_agent_id="agent2",
        )

        assert session.tls_version == TLSVersion.TLS_1_3
        assert session.cipher_suite is not None
        assert session.established_at is not None

    def test_close_session(self):
        """Can close a TLS session."""
        session = self.manager.establish_session(
            agent_id="agent1",
            peer_agent_id="agent2",
        )

        closed = self.manager.close_session(session.session_id)

        assert closed
        assert session.session_id not in self.manager.active_sessions


class TestPolicyEnforcement:
    """Test TLS policy enforcement."""

    def setup_method(self):
        """Set up with custom policy."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.manager = MutualTLSManager(cert_directory=self.tmpdir.name)

        # Create certificates
        self.manager.create_certificate(
            name="root_ca",
            cert_type=CertificateType.ROOT_CA,
            subject="CN=root",
            issuer="CN=root",
        )

    def teardown_method(self):
        """Clean up."""
        self.tmpdir.cleanup()

    def test_set_custom_policy(self):
        """Can set custom TLS policy."""
        policy = MutualTLSPolicy(
            min_tls_version=TLSVersion.TLS_1_2,
            require_mutual_auth=True,
        )

        self.manager.set_policy(policy)

        assert self.manager.policy.min_tls_version == TLSVersion.TLS_1_2


class TestCertificateStatus:
    """Test certificate status reporting."""

    def setup_method(self):
        """Set up with various certificates."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.manager = MutualTLSManager(cert_directory=self.tmpdir.name)

        # Create certificates with different expiration dates
        self.manager.create_certificate(
            name="valid",
            cert_type=CertificateType.AGENT,
            subject="CN=agent",
            issuer="CN=root",
            valid_days=120,
        )

        self.manager.create_certificate(
            name="expiring_soon",
            cert_type=CertificateType.AGENT,
            subject="CN=agent",
            issuer="CN=root",
            valid_days=20,
        )

    def teardown_method(self):
        """Clean up."""
        self.tmpdir.cleanup()

    def test_get_certificate_status(self):
        """Can get certificate status."""
        status = self.manager.get_certificate_status()

        assert status["total_certificates"] == 2
        assert "expired" in status
        assert "expiring_soon" in status
        assert "valid_certificates" in status


class TestSessionStatus:
    """Test session status reporting."""

    def setup_method(self):
        """Set up with active sessions."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.manager = MutualTLSManager(cert_directory=self.tmpdir.name)

        # Create certificates and configurations
        for name in ["root", "agent1", "agent2"]:
            self.manager.create_certificate(
                name=name,
                cert_type=CertificateType.AGENT,
                subject=f"CN={name}",
                issuer="CN=root",
            )

        for agent_id in ["agent1", "agent2"]:
            self.manager.create_agent_configuration(
                agent_id=agent_id,
                certificate_name=agent_id,
                ca_certificate_name="root",
            )

        # Establish sessions
        self.manager.establish_session("agent1", "agent2")

    def teardown_method(self):
        """Clean up."""
        self.tmpdir.cleanup()

    def test_get_session_status(self):
        """Can get session status."""
        status = self.manager.get_session_status()

        assert status["total_sessions"] > 0
        assert status["active_sessions"] > 0
        assert "sessions" in status


class TestConfigurationImportExport:
    """Test importing and exporting configurations."""

    def setup_method(self):
        """Set up with configuration."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.manager = MutualTLSManager(cert_directory=self.tmpdir.name)

        self.manager.create_certificate(
            name="root",
            cert_type=CertificateType.ROOT_CA,
            subject="CN=root",
            issuer="CN=root",
        )

        self.manager.create_certificate(
            name="agent1",
            cert_type=CertificateType.AGENT,
            subject="CN=agent1",
            issuer="CN=root",
        )

        self.manager.create_agent_configuration(
            agent_id="agent1",
            certificate_name="agent1",
            ca_certificate_name="root",
        )

    def teardown_method(self):
        """Clean up."""
        self.tmpdir.cleanup()

    def test_export_configuration(self):
        """Can export agent configuration."""
        export_path = os.path.join(self.tmpdir.name, "agent1_config.json")

        success = self.manager.export_configuration("agent1", export_path)

        assert success
        assert os.path.exists(export_path)

    def test_import_configuration(self):
        """Can import agent configuration."""
        export_path = os.path.join(self.tmpdir.name, "agent1_config.json")

        # Export first
        self.manager.export_configuration("agent1", export_path)

        # Create new manager and import
        new_manager = MutualTLSManager(cert_directory=self.tmpdir.name)
        imported_config = new_manager.import_configuration(export_path)

        assert imported_config is not None
        assert imported_config.agent_id == "agent1"

    def test_round_trip_preserves_config(self):
        """Export-import round trip preserves configuration."""
        export_path = os.path.join(self.tmpdir.name, "config_export.json")

        # Get original
        original = self.manager.configurations["agent1"]

        # Round trip
        self.manager.export_configuration("agent1", export_path)
        new_manager = MutualTLSManager(cert_directory=self.tmpdir.name)
        imported = new_manager.import_configuration(export_path)

        # Verify
        assert imported.agent_id == original.agent_id
        assert imported.tls_version == original.tls_version
