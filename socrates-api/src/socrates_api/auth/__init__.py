"""
Authentication module for Socrates API.

Provides JWT token handling, password hashing, and FastAPI dependencies
for API authentication.
"""

from socrates_api.auth.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_current_user_object,
    get_current_user_object_optional,
    require_project_role,
    security,
)
from socrates_api.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
)
from socrates_api.auth.password import (
    hash_password,
    verify_password,
)

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "get_current_user_object",
    "get_current_user_object_optional",
    "require_project_role",
    "security",
    "create_access_token",
    "create_refresh_token",
    "verify_access_token",
    "verify_refresh_token",
    "hash_password",
    "verify_password",
]
