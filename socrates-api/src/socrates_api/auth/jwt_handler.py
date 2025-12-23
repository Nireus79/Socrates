"""
JWT Token Handler for Socrates API.

Manages creation, validation, and refresh of JWT tokens for API authentication.
Uses short-lived access tokens (15 minutes) and long-lived refresh tokens (7 days).
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


class JWTHandler:
    """Manages JWT token creation, validation, and refresh."""

    @staticmethod
    def create_access_token(
        subject: str,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a short-lived access token.

        Args:
            subject: User ID or username to encode in token
            expires_delta: Optional custom expiration time
            additional_claims: Optional additional claims to include

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
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")

        Returns:
            Decoded token claims if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Verify token type
            if payload.get("type") != token_type:
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
def create_access_token(subject: str) -> str:
    """Create an access token."""
    return JWTHandler.create_access_token(subject)


def create_refresh_token(subject: str) -> str:
    """Create a refresh token."""
    return JWTHandler.create_refresh_token(subject)


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify an access token."""
    return JWTHandler.verify_token(token, token_type="access")


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a refresh token."""
    return JWTHandler.verify_token(token, token_type="refresh")
