"""
Agent Certificate Management

Handles certificate generation, storage, validation, and lifecycle management
for agent authentication and TLS communication.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class AgentCertificate:
    """Represents an agent's certificate for TLS communication."""

    agent_id: str
    certificate_pem: str  # PEM-encoded certificate
    private_key_pem: str  # PEM-encoded private key
    issuer_cn: str  # Common name of issuing authority
    subject_cn: str  # Common name of certificate subject
    serial_number: str  # Certificate serial number
    not_before: datetime  # Certificate validity start
    not_after: datetime  # Certificate validity end
    fingerprint: str  # SHA-256 fingerprint
    key_size: int  # RSA key size (2048, 4096, etc.)
    is_revoked: bool = False
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_valid(self) -> bool:
        """Check if certificate is currently valid."""
        if self.is_revoked:
            return False
        now = datetime.now(UTC)
        return self.not_before <= now <= self.not_after

    def is_expired(self) -> bool:
        """Check if certificate is expired."""
        return datetime.now(UTC) > self.not_after

    def days_until_expiration(self) -> int:
        """Days until certificate expires."""
        if self.is_expired():
            return 0
        delta = self.not_after - datetime.now(UTC)
        return delta.days

    def requires_renewal(self, days_threshold: int = 30) -> bool:
        """Check if certificate needs renewal."""
        return self.days_until_expiration() < days_threshold

    def revoke(self, reason: str = "No reason specified") -> None:
        """Revoke this certificate."""
        self.is_revoked = True
        self.revoked_at = datetime.now(UTC)
        self.revocation_reason = reason

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "agent_id": self.agent_id,
            "certificate_pem": self.certificate_pem,
            "private_key_pem": self.private_key_pem,
            "issuer_cn": self.issuer_cn,
            "subject_cn": self.subject_cn,
            "serial_number": self.serial_number,
            "not_before": self.not_before.isoformat(),
            "not_after": self.not_after.isoformat(),
            "fingerprint": self.fingerprint,
            "key_size": self.key_size,
            "is_revoked": self.is_revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revocation_reason": self.revocation_reason,
            "created_at": self.created_at.isoformat(),
        }


class CertificateAuthority:
    """
    Certificate Authority for issuing and managing agent certificates.

    Handles certificate generation, signing, storage, and revocation.
    """

    def __init__(
        self,
        ca_certificate_pem: str,
        ca_private_key_pem: str,
        ca_common_name: str = "Socrates CA",
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize Certificate Authority.

        Args:
            ca_certificate_pem: PEM-encoded CA certificate
            ca_private_key_pem: PEM-encoded CA private key
            ca_common_name: Common name for CA
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.ca_certificate_pem = ca_certificate_pem
        self.ca_private_key_pem = ca_private_key_pem
        self.ca_common_name = ca_common_name

        # Certificate inventory
        self.issued_certificates: Dict[str, AgentCertificate] = {}
        self.serial_counter = 0

    def issue_certificate(
        self,
        agent_id: str,
        valid_days: int = 365,
        key_size: int = 2048,
        subject_cn: Optional[str] = None,
    ) -> AgentCertificate:
        """
        Issue a certificate for an agent.

        Args:
            agent_id: Agent identifier
            valid_days: Days until certificate expires
            key_size: RSA key size (2048, 4096, etc.)
            subject_cn: Certificate subject common name (defaults to agent_id)

        Returns:
            Issued AgentCertificate
        """
        subject_cn = subject_cn or agent_id
        self.serial_counter += 1
        serial_number = f"0x{self.serial_counter:08x}"

        now = datetime.now(UTC)
        not_after = now + timedelta(days=valid_days)

        # Generate certificate PEM (simplified - in production use cryptography lib)
        certificate_pem = self._generate_certificate_pem(
            agent_id, subject_cn, serial_number, now, not_after, key_size
        )

        # Generate private key PEM (simplified)
        private_key_pem = self._generate_private_key_pem(agent_id, key_size)

        # Generate fingerprint
        fingerprint = self._generate_fingerprint(certificate_pem)

        cert = AgentCertificate(
            agent_id=agent_id,
            certificate_pem=certificate_pem,
            private_key_pem=private_key_pem,
            issuer_cn=self.ca_common_name,
            subject_cn=subject_cn,
            serial_number=serial_number,
            not_before=now,
            not_after=not_after,
            fingerprint=fingerprint,
            key_size=key_size,
        )

        self.issued_certificates[agent_id] = cert

        self.logger.info(
            f"[CA] Issued certificate for {agent_id} "
            f"(valid until {not_after.strftime('%Y-%m-%d')})"
        )

        return cert

    def validate_certificate(self, cert: AgentCertificate) -> tuple[bool, str]:
        """
        Validate a certificate.

        Args:
            cert: Certificate to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        if not cert.is_valid():
            if cert.is_revoked:
                return False, f"Certificate revoked: {cert.revocation_reason}"
            elif cert.is_expired():
                return False, "Certificate expired"
            else:
                return False, "Certificate not yet valid"

        if cert.requires_renewal():
            days_left = cert.days_until_expiration()
            return (
                True,
                f"Certificate valid but renewal recommended ({days_left} days left)",
            )

        return True, "Certificate is valid"

    def revoke_certificate(self, agent_id: str, reason: str = "No reason specified") -> bool:
        """
        Revoke a certificate.

        Args:
            agent_id: Agent whose certificate to revoke
            reason: Reason for revocation

        Returns:
            True if revocation successful
        """
        if agent_id not in self.issued_certificates:
            self.logger.warning(f"[CA] No certificate found for {agent_id}")
            return False

        cert = self.issued_certificates[agent_id]
        cert.revoke(reason)

        self.logger.info(f"[CA] Revoked certificate for {agent_id}: {reason}")
        return True

    def get_certificate(self, agent_id: str) -> Optional[AgentCertificate]:
        """Get a certificate by agent ID."""
        return self.issued_certificates.get(agent_id)

    def get_certificate_status(self) -> Dict[str, Any]:
        """Get status of all certificates."""
        valid_count = 0
        expired_count = 0
        revoked_count = 0
        expiring_soon_list: List[Dict[str, Any]] = []

        for cert in self.issued_certificates.values():
            if cert.is_revoked:
                revoked_count += 1
            elif cert.is_expired():
                expired_count += 1
            elif cert.requires_renewal():
                expiring_soon_list.append(
                    {
                        "agent_id": cert.agent_id,
                        "days_until_expiry": cert.days_until_expiration(),
                    }
                )
            else:
                valid_count += 1

        status: Dict[str, Any] = {
            "total_issued": len(self.issued_certificates),
            "valid": valid_count,
            "expired": expired_count,
            "revoked": revoked_count,
            "expiring_soon": expiring_soon_list,
        }
        return status

    def export_certificates(self, filepath: str) -> bool:
        """Export all certificates to JSON file."""
        try:
            data = {agent_id: cert.to_dict() for agent_id, cert in self.issued_certificates.items()}

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"[CA] Exported {len(data)} certificates to {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"[CA] Export failed: {e}")
            return False

    def import_certificates(self, filepath: str) -> bool:
        """Import certificates from JSON file."""
        try:
            with open(filepath) as f:
                data = json.load(f)

            for agent_id, cert_data in data.items():
                cert = AgentCertificate(
                    agent_id=agent_id,
                    certificate_pem=cert_data["certificate_pem"],
                    private_key_pem=cert_data["private_key_pem"],
                    issuer_cn=cert_data["issuer_cn"],
                    subject_cn=cert_data["subject_cn"],
                    serial_number=cert_data["serial_number"],
                    not_before=datetime.fromisoformat(cert_data["not_before"]),
                    not_after=datetime.fromisoformat(cert_data["not_after"]),
                    fingerprint=cert_data["fingerprint"],
                    key_size=cert_data["key_size"],
                    is_revoked=cert_data["is_revoked"],
                    revoked_at=(
                        datetime.fromisoformat(cert_data["revoked_at"])
                        if cert_data.get("revoked_at")
                        else None
                    ),
                    revocation_reason=cert_data.get("revocation_reason"),
                )
                self.issued_certificates[agent_id] = cert

            self.logger.info(f"[CA] Imported {len(data)} certificates from {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"[CA] Import failed: {e}")
            return False

    def _generate_certificate_pem(
        self,
        agent_id: str,
        subject_cn: str,
        serial_number: str,
        not_before: datetime,
        not_after: datetime,
        key_size: int,
    ) -> str:
        """Generate a certificate PEM (simplified - mock for testing)."""
        cert_data = {
            "type": "CERTIFICATE",
            "agent_id": agent_id,
            "subject_cn": subject_cn,
            "serial": serial_number,
            "not_before": not_before.isoformat(),
            "not_after": not_after.isoformat(),
            "key_size": key_size,
        }
        cert_str = json.dumps(cert_data)
        return f"-----BEGIN CERTIFICATE-----\n{cert_str}\n-----END CERTIFICATE-----"

    def _generate_private_key_pem(self, agent_id: str, key_size: int) -> str:
        """Generate a private key PEM (simplified - mock for testing)."""
        key_data = {
            "type": "PRIVATE KEY",
            "agent_id": agent_id,
            "key_size": key_size,
        }
        key_str = json.dumps(key_data)
        return f"-----BEGIN PRIVATE KEY-----\n{key_str}\n-----END PRIVATE KEY-----"

    def _generate_fingerprint(self, certificate_pem: str) -> str:
        """Generate certificate fingerprint (SHA-256)."""
        return hashlib.sha256(certificate_pem.encode()).hexdigest()
