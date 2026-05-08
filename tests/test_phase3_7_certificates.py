"""
Tests for Phase 3.7 - Certificate Management

Tests certificate generation, validation, revocation, and lifecycle management.
"""

import json
import tempfile
from datetime import UTC, datetime, timedelta

from socratic_system.security.agent_certificates import (
    AgentCertificate,
    CertificateAuthority,
)


class TestAgentCertificate:
    """Test AgentCertificate dataclass."""

    def test_certificate_initialization(self):
        """Certificate initializes with all fields."""
        now = datetime.now(UTC)
        later = now + timedelta(days=365)

        cert = AgentCertificate(
            agent_id="agent1",
            certificate_pem="-----BEGIN CERTIFICATE-----\ndata\n-----END CERTIFICATE-----",
            private_key_pem="-----BEGIN PRIVATE KEY-----\ndata\n-----END PRIVATE KEY-----",
            issuer_cn="Test CA",
            subject_cn="CN=agent1",
            serial_number="0x00000001",
            not_before=now,
            not_after=later,
            fingerprint="abc123def456",
            key_size=2048,
        )

        assert cert.agent_id == "agent1"
        assert cert.issuer_cn == "Test CA"
        assert cert.is_valid()
        assert not cert.is_expired()

    def test_certificate_validity_checking(self):
        """Certificate validity checking works correctly."""
        now = datetime.now(UTC)
        past = now - timedelta(days=1)
        future = now + timedelta(days=365)

        # Expired certificate
        expired_cert = AgentCertificate(
            agent_id="expired",
            certificate_pem="cert",
            private_key_pem="key",
            issuer_cn="CA",
            subject_cn="CN=expired",
            serial_number="0x00000001",
            not_before=past - timedelta(days=400),
            not_after=past,
            fingerprint="abc",
            key_size=2048,
        )

        assert expired_cert.is_expired()
        assert not expired_cert.is_valid()

        # Valid certificate
        valid_cert = AgentCertificate(
            agent_id="valid",
            certificate_pem="cert",
            private_key_pem="key",
            issuer_cn="CA",
            subject_cn="CN=valid",
            serial_number="0x00000002",
            not_before=now - timedelta(days=1),
            not_after=future,
            fingerprint="def",
            key_size=2048,
        )

        assert not valid_cert.is_expired()
        assert valid_cert.is_valid()

    def test_certificate_expiration_days(self):
        """Days until expiration calculated correctly."""
        now = datetime.now(UTC)
        future = now + timedelta(days=30)

        cert = AgentCertificate(
            agent_id="test",
            certificate_pem="cert",
            private_key_pem="key",
            issuer_cn="CA",
            subject_cn="CN=test",
            serial_number="0x00000001",
            not_before=now,
            not_after=future,
            fingerprint="abc",
            key_size=2048,
        )

        days_left = cert.days_until_expiration()
        # Allow for timing variations - should be 29 or 30 days
        assert days_left in (29, 30)

    def test_certificate_renewal_requirement(self):
        """Renewal requirement detected when near expiration."""
        now = datetime.now(UTC)
        soon = now + timedelta(days=15)  # Less than 30-day threshold

        cert = AgentCertificate(
            agent_id="test",
            certificate_pem="cert",
            private_key_pem="key",
            issuer_cn="CA",
            subject_cn="CN=test",
            serial_number="0x00000001",
            not_before=now,
            not_after=soon,
            fingerprint="abc",
            key_size=2048,
        )

        assert cert.requires_renewal()

    def test_certificate_revocation(self):
        """Certificate can be revoked."""
        cert = AgentCertificate(
            agent_id="test",
            certificate_pem="cert",
            private_key_pem="key",
            issuer_cn="CA",
            subject_cn="CN=test",
            serial_number="0x00000001",
            not_before=datetime.now(UTC),
            not_after=datetime.now(UTC) + timedelta(days=365),
            fingerprint="abc",
            key_size=2048,
        )

        assert cert.is_valid()
        cert.revoke("Test revocation")
        assert not cert.is_valid()
        assert cert.is_revoked
        assert cert.revocation_reason == "Test revocation"

    def test_certificate_to_dict(self):
        """Certificate serializes to dictionary."""
        cert = AgentCertificate(
            agent_id="test",
            certificate_pem="cert_data",
            private_key_pem="key_data",
            issuer_cn="CA",
            subject_cn="CN=test",
            serial_number="0x00000001",
            not_before=datetime.now(UTC),
            not_after=datetime.now(UTC) + timedelta(days=365),
            fingerprint="abc123",
            key_size=2048,
        )

        cert_dict = cert.to_dict()
        assert cert_dict["agent_id"] == "test"
        assert cert_dict["certificate_pem"] == "cert_data"
        assert cert_dict["private_key_pem"] == "key_data"
        assert "not_before" in cert_dict
        assert "not_after" in cert_dict


class TestCertificateAuthority:
    """Test CertificateAuthority."""

    def setup_method(self):
        """Set up CA."""
        self.ca = CertificateAuthority(
            ca_certificate_pem="-----BEGIN CERTIFICATE-----\nCA_CERT\n-----END CERTIFICATE-----",
            ca_private_key_pem="-----BEGIN PRIVATE KEY-----\nCA_KEY\n-----END PRIVATE KEY-----",
            ca_common_name="Test CA",
        )

    def test_ca_initializes(self):
        """CA initializes correctly."""
        assert self.ca is not None
        assert self.ca.ca_common_name == "Test CA"
        assert len(self.ca.issued_certificates) == 0

    def test_issue_certificate(self):
        """CA can issue certificates."""
        cert = self.ca.issue_certificate(
            agent_id="agent1",
            valid_days=365,
            key_size=2048,
        )

        assert cert is not None
        assert cert.agent_id == "agent1"
        assert cert.issuer_cn == "Test CA"
        assert cert.key_size == 2048
        assert cert.is_valid()
        assert "agent1" in self.ca.issued_certificates

    def test_issue_multiple_certificates(self):
        """CA can issue multiple certificates with unique serials."""
        cert1 = self.ca.issue_certificate("agent1")
        cert2 = self.ca.issue_certificate("agent2")

        assert cert1.serial_number != cert2.serial_number
        assert len(self.ca.issued_certificates) == 2

    def test_validate_certificate(self):
        """CA can validate certificates."""
        cert = self.ca.issue_certificate("agent1")
        is_valid, reason = self.ca.validate_certificate(cert)

        assert is_valid
        assert "valid" in reason.lower()

    def test_revoke_certificate(self):
        """CA can revoke certificates."""
        cert = self.ca.issue_certificate("agent1")
        assert cert.is_valid()

        revoked = self.ca.revoke_certificate("agent1", "Test revocation")
        assert revoked
        assert not cert.is_valid()

    def test_get_certificate(self):
        """CA can retrieve issued certificates."""
        self.ca.issue_certificate("agent1")
        retrieved = self.ca.get_certificate("agent1")

        assert retrieved is not None
        assert retrieved.agent_id == "agent1"

    def test_get_certificate_status(self):
        """CA provides certificate status summary."""
        self.ca.issue_certificate("agent1", valid_days=365)
        self.ca.issue_certificate("agent2", valid_days=20)  # Will expire soon
        self.ca.issue_certificate("agent3")
        self.ca.revoke_certificate("agent3")

        status = self.ca.get_certificate_status()

        assert status["total_issued"] == 3
        assert status["revoked"] == 1
        assert len(status["expiring_soon"]) > 0  # agent2 should expire soon

    def test_export_certificates(self):
        """CA can export certificates to JSON."""
        self.ca.issue_certificate("agent1")
        self.ca.issue_certificate("agent2")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        success = self.ca.export_certificates(filepath)
        assert success

        # Verify exported data
        with open(filepath) as f:
            data = json.load(f)
            assert "agent1" in data
            assert "agent2" in data
            assert data["agent1"]["agent_id"] == "agent1"

    def test_import_certificates(self):
        """CA can import certificates from JSON."""
        # First export
        ca1 = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )
        ca1.issue_certificate("agent1")
        ca1.issue_certificate("agent2")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        ca1.export_certificates(filepath)

        # Then import in new CA
        ca2 = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )
        success = ca2.import_certificates(filepath)
        assert success
        assert len(ca2.issued_certificates) == 2
        assert ca2.get_certificate("agent1") is not None

    def test_certificate_storage_persistence(self):
        """Certificates persist through export/import cycle."""
        cert = self.ca.issue_certificate("agent1")
        original_fingerprint = cert.fingerprint

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        self.ca.export_certificates(filepath)

        ca2 = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
        )
        ca2.import_certificates(filepath)

        retrieved = ca2.get_certificate("agent1")
        assert retrieved.fingerprint == original_fingerprint
        assert retrieved.is_valid()


class TestCertificateLifecycle:
    """Test complete certificate lifecycle."""

    def test_certificate_full_lifecycle(self):
        """Test certificate from issuance through revocation."""
        ca = CertificateAuthority(
            ca_certificate_pem="cert",
            ca_private_key_pem="key",
            ca_common_name="Test CA",
        )

        # Issue
        cert = ca.issue_certificate("agent1", valid_days=365)
        assert cert.is_valid()

        # Validate
        is_valid, reason = ca.validate_certificate(cert)
        assert is_valid

        # Check status
        status = ca.get_certificate_status()
        assert status["total_issued"] == 1
        assert status["valid"] == 1

        # Revoke
        ca.revoke_certificate("agent1", "Decommissioned")
        assert not cert.is_valid()

        # Check status again
        status = ca.get_certificate_status()
        assert status["revoked"] == 1
        assert status["valid"] == 0
