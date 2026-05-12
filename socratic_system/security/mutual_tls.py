"""
Mutual TLS Configuration for Secure Agent Communication

Manages certificate generation, storage, validation, and TLS configuration
for secure inter-agent communication with mutual authentication.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any


class CertificateType(Enum):
    """Types of certificates in the TLS system."""

    ROOT_CA = "root_ca"
    INTERMEDIATE_CA = "intermediate_ca"
    SERVER = "server"
    CLIENT = "client"
    AGENT = "agent"


class TLSVersion(Enum):
    """Supported TLS versions."""

    TLS_1_2 = "1.2"
    TLS_1_3 = "1.3"


@dataclass
class CertificateInfo:
    """Information about a TLS certificate."""

    name: str
    cert_type: CertificateType
    subject: str  # Certificate subject/CN
    issuer: str  # Certificate issuer
    not_before: datetime  # Certificate validity start
    not_after: datetime  # Certificate validity end
    fingerprint: str  # Certificate fingerprint (SHA-256)
    public_key_bits: int  # RSA key size (2048, 4096, etc.)
    is_valid: bool = True
    file_path: str | None = None
    key_path: str | None = None
    created_date: datetime = field(default_factory=lambda: datetime.now(UTC))

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


@dataclass
class TLSConfiguration:
    """TLS configuration for an agent or service."""

    agent_id: str
    cert_path: str
    key_path: str
    ca_cert_path: str
    tls_version: TLSVersion = TLSVersion.TLS_1_3
    cipher_suites: list[str] = field(
        default_factory=lambda: [
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLS_AES_128_GCM_SHA256",
        ]
    )
    verify_peer: bool = True
    require_client_cert: bool = True
    allow_self_signed: bool = False
    certificate: CertificateInfo | None = None
    created_date: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_valid(self) -> bool:
        """Check if TLS configuration is valid."""
        if not self.certificate:
            return False
        return not self.certificate.is_expired() and self.certificate.is_valid

    def get_certificate_info(self) -> CertificateInfo | None:
        """Get detailed certificate information."""
        return self.certificate


@dataclass
class MutualTLSPolicy:
    """Policy for mutual TLS enforcement."""

    min_tls_version: TLSVersion = TLSVersion.TLS_1_3
    require_mutual_auth: bool = True
    certificate_validation_required: bool = True
    allowed_cipher_suites: list[str] = field(
        default_factory=lambda: [
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLS_AES_128_GCM_SHA256",
        ]
    )
    max_certificate_age_days: int = 365
    require_certificate_renewal: int = 30  # Days before expiry
    enforce_hostname_verification: bool = True
    allow_certificate_pinning: bool = True
    created_date: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TLSSessionInfo:
    """Information about an active TLS session."""

    session_id: str
    agent_id: str
    peer_agent_id: str
    tls_version: TLSVersion
    cipher_suite: str
    peer_certificate: CertificateInfo | None = None
    established_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True

    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Check if session is expired due to inactivity."""
        age = datetime.now(UTC) - self.last_activity
        return age > timedelta(minutes=timeout_minutes)


class MutualTLSManager:
    """
    Manages mutual TLS configuration and certificate lifecycle.

    Handles:
    - Certificate generation and storage
    - TLS configuration management
    - Certificate validation and renewal
    - Secure session establishment
    - Policy enforcement
    """

    def __init__(
        self,
        cert_directory: str = "./certs",
        logger: logging.Logger | None = None,
    ):
        """Initialize Mutual TLS Manager.

        Args:
            cert_directory: Directory for storing certificates
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.cert_directory = Path(cert_directory)
        self.cert_directory.mkdir(parents=True, exist_ok=True)

        self.certificates: dict[str, CertificateInfo] = {}
        self.configurations: dict[str, TLSConfiguration] = {}
        self.active_sessions: dict[str, TLSSessionInfo] = {}
        self.policy: MutualTLSPolicy = MutualTLSPolicy()

    def set_policy(self, policy: MutualTLSPolicy) -> None:
        """Set the mutual TLS policy.

        Args:
            policy: MutualTLSPolicy to enforce
        """
        self.policy = policy
        self.logger.info("[TLS Manager] Policy updated")

    def create_certificate(
        self,
        name: str,
        cert_type: CertificateType,
        subject: str,
        issuer: str,
        valid_days: int = 365,
        key_bits: int = 4096,
    ) -> CertificateInfo:
        """Create a new certificate.

        Args:
            name: Certificate name
            cert_type: Type of certificate
            subject: Certificate subject/CN
            issuer: Certificate issuer
            valid_days: Days until expiration
            key_bits: RSA key size

        Returns:
            CertificateInfo for the created certificate
        """
        now = datetime.now(UTC)
        not_after = now + timedelta(days=valid_days)

        # Generate fingerprint (simplified - in production use actual cert)
        fingerprint = self._generate_fingerprint(name, subject)

        cert_info = CertificateInfo(
            name=name,
            cert_type=cert_type,
            subject=subject,
            issuer=issuer,
            not_before=now,
            not_after=not_after,
            fingerprint=fingerprint,
            public_key_bits=key_bits,
            is_valid=True,
            file_path=str(self.cert_directory / f"{name}.crt"),
            key_path=str(self.cert_directory / f"{name}.key"),
        )

        self.certificates[name] = cert_info

        self.logger.info(
            f"[TLS Manager] Certificate created: {name} "
            f"(valid until {not_after.strftime('%Y-%m-%d')})"
        )

        return cert_info

    def create_agent_configuration(
        self,
        agent_id: str,
        certificate_name: str,
        ca_certificate_name: str,
    ) -> TLSConfiguration:
        """Create TLS configuration for an agent.

        Args:
            agent_id: Agent identifier
            certificate_name: Name of agent's certificate
            ca_certificate_name: Name of CA certificate

        Returns:
            TLSConfiguration for the agent
        """
        if certificate_name not in self.certificates:
            raise ValueError(f"Certificate not found: {certificate_name}")

        if ca_certificate_name not in self.certificates:
            raise ValueError(f"CA certificate not found: {ca_certificate_name}")

        cert_info = self.certificates[certificate_name]
        config = TLSConfiguration(
            agent_id=agent_id,
            cert_path=cert_info.file_path or "",
            key_path=cert_info.key_path or "",
            ca_cert_path=str(self.cert_directory / f"{ca_certificate_name}.crt"),
            certificate=cert_info,
        )

        self.configurations[agent_id] = config

        self.logger.info(f"[TLS Manager] Configuration created for agent: {agent_id}")

        return config

    def validate_certificate(self, cert_info: CertificateInfo) -> tuple[bool, str]:
        """Validate a certificate against policy.

        Args:
            cert_info: Certificate to validate

        Returns:
            Tuple of (is_valid, explanation)
        """
        # Check expiration
        if cert_info.is_expired():
            return False, "Certificate is expired"

        # Check validity flag
        if not cert_info.is_valid:
            return False, "Certificate marked as invalid"

        # Check age
        age_days = (datetime.now(UTC) - cert_info.created_date).days
        if age_days > self.policy.max_certificate_age_days:
            return False, f"Certificate age ({age_days} days) exceeds policy maximum"

        # Check renewal requirement
        if cert_info.requires_renewal(self.policy.require_certificate_renewal):
            return (
                True,
                f"Certificate renewal recommended ({cert_info.days_until_expiration()} days until expiry)",
            )

        return True, "Certificate is valid"

    def establish_session(
        self,
        agent_id: str,
        peer_agent_id: str,
        peer_certificate: CertificateInfo | None = None,
    ) -> TLSSessionInfo | None:
        """Establish a TLS session between agents.

        Args:
            agent_id: Initiating agent
            peer_agent_id: Peer agent
            peer_certificate: Peer's certificate information

        Returns:
            TLSSessionInfo if successful, None otherwise
        """
        # Validate agent configuration
        if agent_id not in self.configurations:
            self.logger.error(f"[TLS Manager] No configuration for agent: {agent_id}")
            return None

        agent_config = self.configurations[agent_id]

        # Validate peer certificate if provided
        if peer_certificate and self.policy.certificate_validation_required:
            is_valid, reason = self.validate_certificate(peer_certificate)
            if not is_valid:
                self.logger.error(f"[TLS Manager] Peer certificate validation failed: {reason}")
                return None

        # Create session
        session_id = f"tls_{agent_id}_{peer_agent_id}_{int(datetime.now(UTC).timestamp())}"

        session = TLSSessionInfo(
            session_id=session_id,
            agent_id=agent_id,
            peer_agent_id=peer_agent_id,
            tls_version=agent_config.tls_version,
            cipher_suite=agent_config.cipher_suites[0],
            peer_certificate=peer_certificate,
        )

        self.active_sessions[session_id] = session

        self.logger.info(
            f"[TLS Manager] Session established: {session_id} "
            f"({agent_config.tls_version.value})"
        )

        return session

    def close_session(self, session_id: str) -> bool:
        """Close a TLS session.

        Args:
            session_id: Session to close

        Returns:
            True if successful
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.is_active = False
            del self.active_sessions[session_id]

            self.logger.info(f"[TLS Manager] Session closed: {session_id}")
            return True

        return False

    def get_certificate_status(self) -> dict[str, Any]:
        """Get status of all certificates.

        Returns:
            Dictionary with certificate status information
        """
        expired_list: list[dict[str, Any]] = []
        requires_renewal_list: list[dict[str, Any]] = []
        expiring_soon_list: list[dict[str, Any]] = []
        valid_count = 0

        for cert_info in self.certificates.values():
            if cert_info.is_expired():
                expired_list.append(
                    {
                        "name": cert_info.name,
                        "expired_date": cert_info.not_after.isoformat(),
                    }
                )
            elif cert_info.requires_renewal():
                requires_renewal_list.append(
                    {
                        "name": cert_info.name,
                        "days_until_expiry": cert_info.days_until_expiration(),
                    }
                )
            elif cert_info.days_until_expiration() < 90:
                expiring_soon_list.append(
                    {
                        "name": cert_info.name,
                        "days_until_expiry": cert_info.days_until_expiration(),
                    }
                )
            else:
                valid_count += 1

        status: dict[str, Any] = {
            "total_certificates": len(self.certificates),
            "valid_certificates": valid_count,
            "expiring_soon": expiring_soon_list,
            "expired": expired_list,
            "requires_renewal": requires_renewal_list,
        }
        return status

    def get_session_status(self) -> dict[str, Any]:
        """Get status of all active TLS sessions.

        Returns:
            Dictionary with session status information
        """
        active_count = sum(1 for s in self.active_sessions.values() if s.is_active)
        expired_count = sum(
            1 for s in self.active_sessions.values() if s.is_active and s.is_expired()
        )

        return {
            "total_sessions": len(self.active_sessions),
            "active_sessions": active_count,
            "expired_sessions": expired_count,
            "sessions": [
                {
                    "session_id": s.session_id,
                    "agent_id": s.agent_id,
                    "peer_agent_id": s.peer_agent_id,
                    "tls_version": s.tls_version.value,
                    "is_active": s.is_active,
                    "established_at": s.established_at.isoformat(),
                }
                for s in self.active_sessions.values()
            ],
        }

    def export_configuration(self, agent_id: str, filepath: str) -> bool:
        """Export agent TLS configuration to file.

        Args:
            agent_id: Agent to export
            filepath: File path for export

        Returns:
            True if successful
        """
        if agent_id not in self.configurations:
            self.logger.error(f"[TLS Manager] No configuration for agent: {agent_id}")
            return False

        config = self.configurations[agent_id]

        data = {
            "agent_id": config.agent_id,
            "cert_path": config.cert_path,
            "key_path": config.key_path,
            "ca_cert_path": config.ca_cert_path,
            "tls_version": config.tls_version.value,
            "cipher_suites": config.cipher_suites,
            "verify_peer": config.verify_peer,
            "require_client_cert": config.require_client_cert,
            "created_date": config.created_date.isoformat(),
        }

        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"[TLS Manager] Configuration exported: {agent_id} -> {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"[TLS Manager] Export failed: {e}")
            return False

    def import_configuration(self, filepath: str) -> TLSConfiguration | None:
        """Import agent TLS configuration from file.

        Args:
            filepath: File path to import from

        Returns:
            TLSConfiguration if successful, None otherwise
        """
        try:
            with open(filepath) as f:
                data = json.load(f)

            agent_id = data["agent_id"]
            config = TLSConfiguration(
                agent_id=agent_id,
                cert_path=data["cert_path"],
                key_path=data["key_path"],
                ca_cert_path=data["ca_cert_path"],
                tls_version=TLSVersion(data.get("tls_version", "1.3")),
                cipher_suites=data.get("cipher_suites", []),
                verify_peer=data.get("verify_peer", True),
                require_client_cert=data.get("require_client_cert", True),
            )

            self.configurations[agent_id] = config

            self.logger.info(f"[TLS Manager] Configuration imported: {agent_id} <- {filepath}")
            return config

        except Exception as e:
            self.logger.error(f"[TLS Manager] Import failed: {e}")
            return None

    def _generate_fingerprint(self, name: str, subject: str) -> str:
        """Generate a certificate fingerprint (simplified).

        Args:
            name: Certificate name
            subject: Certificate subject

        Returns:
            Fingerprint string
        """
        import hashlib

        combined = f"{name}_{subject}_{datetime.now(UTC).isoformat()}"
        return hashlib.sha256(combined.encode()).hexdigest()
