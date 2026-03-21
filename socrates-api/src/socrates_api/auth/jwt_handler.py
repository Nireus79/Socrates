"""
JWT Token Handler for Socrates API.

Manages creation, validation, and refresh of JWT tokens for API authentication.
Uses short-lived access tokens (15 minutes) and long-lived refresh tokens (7 days).
Includes token fingerprinting for theft detection based on IP and User-Agent.
"""

import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    import warnings
    warnings.warn(
        "JWT_SECRET_KEY not set! Using insecure default. Set JWT_SECRET_KEY environment variable.",
        UserWarning,
        stacklevel=2
    )
    SECRET_KEY = "your-secret-key-change-in-production"  # Fallback with warning

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


class JWTHandler:
    """Manages JWT token creation, validation, and refresh."""

    @staticmethod
    def create_token_fingerprint(ip_address: str, user_agent: str) -> str:
        """
        Create a fingerprint from IP address and User-Agent.

        This fingerprint is used to detect token theft. If a token is stolen,
        the attacker likely won't have the same IP or User-Agent.

        Args:
            ip_address: Client IP address
            user_agent: Client User-Agent header

        Returns:
            SHA256 hash of IP + User-Agent
        """
        fingerprint_data = f"{ip_address}:{user_agent}"
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        return fingerprint

    @staticmethod
    def create_access_token(
        subject: str,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """
        Create a short-lived access token with optional fingerprinting.

        Args:
            subject: User ID or username to encode in token
            expires_delta: Optional custom expiration time
            additional_claims: Optional additional claims to include
            ip_address: Client IP address (for fingerprinting)
            user_agent: Client User-Agent (for fingerprinting)

        Returns:
            JWT access token
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        expire = datetime.now(timezone.utc) + expires_delta

        claims: Dict[str, Any] = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }

        # Add token fingerprint if IP and User-Agent provided
        if ip_address and user_agent:
            fingerprint = JWTHandler.create_token_fingerprint(ip_address, user_agent)
            claims["fingerprint"] = fingerprint

        if additional_claims:
            claims.update(additional_claims)

        encoded_jwt = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(subject: str) -> str:
        """
        Create a long-lived refresh token.

        Args:
            subject: User ID or username to encode in token

        Returns:
            JWT refresh token
        """
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        claims = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
        }

        encoded_jwt = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_token_pair(subject: str) -> Dict[str, str]:
        """
        Create both access and refresh tokens.

        Args:
            subject: User ID or username

        Returns:
            Dictionary with access_token and refresh_token
        """
        return {
            "access_token": JWTHandler.create_access_token(subject),
            "refresh_token": JWTHandler.create_refresh_token(subject),
        }

    @staticmethod
    def verify_token(
        token: str,
        token_type: str = "access",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token with optional fingerprint validation.

        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")
            ip_address: Current client IP (for fingerprint validation)
            user_agent: Current client User-Agent (for fingerprint validation)

        Returns:
            Decoded token claims if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Verify token type
            if payload.get("type") != token_type:
                return None

            # Verify token fingerprint if present and client info provided
            if "fingerprint" in payload and ip_address and user_agent:
                current_fingerprint = JWTHandler.create_token_fingerprint(ip_address, user_agent)
                token_fingerprint = payload.get("fingerprint")

                if current_fingerprint != token_fingerprint:
                    # Token fingerprint doesn't match - possible token theft
                    return None

            return payload

        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.InvalidTokenError:
            # Token is invalid
            return None

    @staticmethod
    def get_subject_from_token(token: str) -> Optional[str]:
        """
        Extract subject (user ID) from token without full validation.

        Useful for getting user ID from expired tokens for refresh flow.

        Args:
            token: JWT token

        Returns:
            Subject (user ID) if token is valid structure, None otherwise
        """
        try:
            # Don't verify signature/expiry, just decode
            payload = jwt.decode(
                token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False}
            )
            return payload.get("sub")
        except jwt.InvalidTokenError:
            return None


# Convenience functions
def create_access_token(
    subject: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> str:
    """Create an access token with optional fingerprinting."""
    return JWTHandler.create_access_token(
        subject,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def create_refresh_token(subject: str) -> str:
    """Create a refresh token."""
    return JWTHandler.create_refresh_token(subject)


def verify_access_token(
    token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Verify an access token with optional fingerprint validation."""
    return JWTHandler.verify_token(
        token,
        token_type="access",
        ip_address=ip_address,
        user_agent=user_agent,
    )


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a refresh token."""
    return JWTHandler.verify_token(token, token_type="refresh")
