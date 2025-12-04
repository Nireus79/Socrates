"""
Custom exceptions for Socrates system
"""

from .errors import (
    SocratesError,
    ConfigurationError,
    AgentError,
    DatabaseError,
    AuthenticationError,
    ProjectNotFoundError,
    UserNotFoundError,
    ValidationError,
    APIError,
)

__all__ = [
    'SocratesError',
    'ConfigurationError',
    'AgentError',
    'DatabaseError',
    'AuthenticationError',
    'ProjectNotFoundError',
    'UserNotFoundError',
    'ValidationError',
    'APIError',
]
