"""
Agent Identity and Capability Token System

Implements zero-trust architecture with cryptographic verification of agent identity
and capability-based authorization.
"""

import hashlib
import hmac
import json
import logging
import secrets
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class TokenStatus(Enum):
    """Status of a capability token."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"


@dataclass
class AgentIdentity:
    """Cryptographic identity for an agent."""

    agent_name: str
    agent_id: str
    public_key: str
    issued_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    capabilities: List[str] = field(default_factory=list)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    signature: Optional[str] = None

    def __post_init__(self):
        """Initialize after dataclass creation."""

    def is_valid(self) -> bool:
        """Check if identity is valid."""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(UTC) > self.expires_at:
            return False
        return True

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data["issued_at"] = data["issued_at"].isoformat()
        if data["expires_at"]:
            data["expires_at"] = data["expires_at"].isoformat()
        return data


@dataclass
class CapabilityToken:
    """Token granting capabilities to an agent."""

    token_id: str
    agent_id: str
    agent_name: str
    capabilities: List[str]  # Actions agent can perform
    resource_access: Dict[str, str]  # Resources and access types
    resource_limits: Dict[str, Any]  # Limits (timeout, memory, etc.)
    issued_at: datetime
    expires_at: datetime
    is_active: bool = True
    is_revoked: bool = False
    signature: Optional[str] = None
    last_used: Optional[datetime] = None
    use_count: int = 0

    def is_valid(self) -> bool:
        """Check if token is valid and not expired."""
        if not self.is_active or self.is_revoked:
            return False
        if datetime.now(UTC) > self.expires_at:
            return False
        return True

    def has_capability(self, capability: str) -> bool:
        """Check if token grants a specific capability."""
        return capability in self.capabilities

    def get_resource_limit(self, resource_type: str) -> Optional[Any]:
        """Get resource limit for a resource type."""
        return self.resource_limits.get(resource_type)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data["issued_at"] = data["issued_at"].isoformat()
        data["expires_at"] = data["expires_at"].isoformat()
        if data["last_used"]:
            data["last_used"] = data["last_used"].isoformat()
        return data


class AgentIdentityManager:
    """
    Manages agent identities and cryptographic verification.

    Provides:
    - Agent identity registration
    - Capability token issuance
    - Token validation and verification
    - Token revocation
    - Audit logging of identity operations
    """

    def __init__(
        self,
        secret_key: str,
        logger: Optional[logging.Logger] = None,
        token_lifetime_hours: int = 24,
    ):
        """Initialize identity manager.

        Args:
            secret_key: Secret key for signing tokens
            logger: Python logger
            token_lifetime_hours: How long tokens are valid
        """
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
        self.logger = logger or logging.getLogger(__name__)
        self.token_lifetime_hours = token_lifetime_hours
        self._identities: Dict[str, AgentIdentity] = {}
        self._tokens: Dict[str, CapabilityToken] = {}

    def register_agent(
        self, agent_name: str, capabilities: List[str], resource_limits: Dict
    ) -> AgentIdentity:
        """Register a new agent identity.

        Args:
            agent_name: Name of the agent
            capabilities: List of capabilities granted
            resource_limits: Resource limits for agent

        Returns:
            AgentIdentity for the agent
        """
        # Generate unique agent ID
        agent_id = self._generate_agent_id(agent_name)

        # Generate public key (in real system, would be asymmetric)
        public_key = self._generate_key_pair(agent_name)

        # Create identity
        identity = AgentIdentity(
            agent_name=agent_name,
            agent_id=agent_id,
            public_key=public_key,
            issued_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=365),
            is_active=True,
            capabilities=capabilities,
            resource_limits=resource_limits,
        )

        # Sign identity
        identity.signature = self._sign_data(identity.to_dict())

        # Store identity
        self._identities[agent_id] = identity

        self.logger.info(
            f"[Identity] Registered agent '{agent_name}' with {len(capabilities)} capabilities"
        )

        return identity

    def issue_capability_token(
        self,
        agent_id: str,
        capabilities: List[str],
        resource_access: Dict[str, str],
        resource_limits: Dict,
    ) -> Tuple[bool, Optional[CapabilityToken], Optional[str]]:
        """Issue a capability token to an agent.

        Args:
            agent_id: Agent ID to issue token to
            capabilities: Capabilities to grant
            resource_access: Resource access permissions
            resource_limits: Resource limits

        Returns:
            Tuple of (success, token, error_message)
        """
        # Verify agent exists and is active
        identity = self._identities.get(agent_id)
        if not identity or not identity.is_valid():
            return False, None, f"Agent '{agent_id}' not found or not active"

        # Verify agent is not trying to escalate capabilities
        invalid_caps = set(capabilities) - set(identity.capabilities)
        if invalid_caps:
            self.logger.warning(
                f"[Token] Agent {agent_id} requested unauthorized capabilities: {invalid_caps}"
            )
            return False, None, "Requested capabilities not authorized for this agent"

        # Generate token
        token_id = self._generate_token_id(agent_id)
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=self.token_lifetime_hours)

        token = CapabilityToken(
            token_id=token_id,
            agent_id=agent_id,
            agent_name=identity.agent_name,
            capabilities=capabilities,
            resource_access=resource_access,
            resource_limits=resource_limits,
            issued_at=now,
            expires_at=expires_at,
            is_active=True,
            is_revoked=False,
        )

        # Sign token
        token.signature = self._sign_data(token.to_dict())

        # Store token
        self._tokens[token_id] = token

        self.logger.info(
            f"[Token] Issued token '{token_id}' to agent '{identity.agent_name}' "
            f"with {len(capabilities)} capabilities"
        )

        return True, token, None

    def verify_token(self, token: CapabilityToken) -> Tuple[bool, Optional[str]]:
        """Verify capability token integrity and validity.

        Args:
            token: CapabilityToken to verify

        Returns:
            Tuple of (valid, error_message)
        """
        # Check if token exists
        stored_token = self._tokens.get(token.token_id)
        if not stored_token:
            return False, f"Token '{token.token_id}' not found"

        # Check signature
        token_copy = asdict(token)
        stored_signature = token_copy.get("signature")
        token_copy["signature"] = None

        computed_signature = self._sign_data(token_copy)
        if not hmac.compare_digest(stored_signature or "", computed_signature):
            self.logger.warning(f"[Token] Invalid signature for token '{token.token_id}'")
            return False, "Token signature invalid"

        # Check validity
        if not token.is_valid():
            reason = "Token revoked" if token.is_revoked else "Token expired"
            return False, reason

        # Check expiration
        if datetime.now(UTC) > token.expires_at:
            return False, "Token expired"

        return True, None

    def revoke_token(self, token_id: str, reason: Optional[str] = None) -> bool:
        """Revoke a capability token.

        Args:
            token_id: Token ID to revoke
            reason: Reason for revocation

        Returns:
            True if revoked, False if not found
        """
        token = self._tokens.get(token_id)
        if not token:
            self.logger.warning(f"[Token] Attempted to revoke non-existent token '{token_id}'")
            return False

        token.is_revoked = True
        self.logger.warning(
            f"[Token] Revoked token '{token_id}' for agent '{token.agent_name}': {reason}"
        )

        return True

    def revoke_agent(self, agent_id: str) -> bool:
        """Revoke all capabilities for an agent.

        Args:
            agent_id: Agent ID to revoke

        Returns:
            True if revoked, False if not found
        """
        identity = self._identities.get(agent_id)
        if not identity:
            return False

        identity.is_active = False

        # Revoke all tokens for this agent
        for token in self._tokens.values():
            if token.agent_id == agent_id:
                token.is_revoked = True

        self.logger.warning(f"[Identity] Revoked agent '{identity.agent_name}' and all tokens")

        return True

    def get_agent_capabilities(
        self, agent_id: str
    ) -> Tuple[bool, Optional[List[str]], Optional[str]]:
        """Get capabilities for an agent.

        Args:
            agent_id: Agent ID to check

        Returns:
            Tuple of (success, capabilities_list, error_message)
        """
        identity = self._identities.get(agent_id)
        if not identity:
            return False, None, f"Agent '{agent_id}' not found"

        if not identity.is_valid():
            return False, None, f"Agent '{agent_id}' is not active"

        return True, identity.capabilities, None

    def can_perform_action(
        self, agent_id: str, action: str, token: Optional[CapabilityToken] = None
    ) -> Tuple[bool, Optional[str]]:
        """Check if agent can perform a specific action.

        Args:
            agent_id: Agent ID to check
            action: Action to perform
            token: Optional capability token for this agent

        Returns:
            Tuple of (allowed, error_message)
        """
        # Verify agent exists
        identity = self._identities.get(agent_id)
        if not identity or not identity.is_valid():
            return False, f"Agent '{agent_id}' not found or not active"

        # Check identity-level capabilities
        if action not in identity.capabilities:
            return False, f"Agent '{agent_id}' not authorized for action '{action}'"

        # If token provided, verify it too
        if token:
            valid, error = self.verify_token(token)
            if not valid:
                return False, error

            if action not in token.capabilities:
                return False, f"Token does not grant capability for '{action}'"

        return True, None

    def _generate_agent_id(self, agent_name: str) -> str:
        """Generate unique agent ID."""
        base = f"agent_{agent_name}_{secrets.token_hex(8)}"
        return base.lower().replace(" ", "_")

    def _generate_token_id(self, agent_id: str) -> str:
        """Generate unique token ID."""
        base = f"token_{agent_id}_{secrets.token_hex(16)}"
        return base.lower()

    def _generate_key_pair(self, agent_name: str) -> str:
        """Generate key pair for agent (simplified - real system would use asymmetric crypto)."""
        base = f"key_{agent_name}_{secrets.token_hex(32)}"
        return base

    def _sign_data(self, data: Dict) -> str:
        """Sign data with secret key.

        Args:
            data: Dictionary to sign

        Returns:
            Hex-encoded signature
        """
        # Convert data to JSON for consistent signing
        data_str = json.dumps(data, sort_keys=True, default=str)
        signature = hmac.new(self.secret_key, data_str.encode(), hashlib.sha256).hexdigest()
        return signature

    def get_stats(self) -> Dict:
        """Get identity manager statistics.

        Returns:
            Statistics dictionary
        """
        total_tokens = len(self._tokens)
        active_tokens = sum(1 for t in self._tokens.values() if t.is_valid())
        revoked_agents = sum(1 for i in self._identities.values() if not i.is_active)

        return {
            "registered_agents": len(self._identities),
            "active_agents": len([i for i in self._identities.values() if i.is_active]),
            "revoked_agents": revoked_agents,
            "total_tokens": total_tokens,
            "active_tokens": active_tokens,
            "expired_tokens": total_tokens - active_tokens,
        }
