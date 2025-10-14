#!/usr/bin/env python3
"""
UserManagerAgent - User Lifecycle Management
============================================
Handles all user-related operations including CRUD, authentication, and permissions.
"""

from typing import Any, Dict, List
from datetime import datetime

# Import base agent and decorators
from .base import BaseAgent, log_agent_action

# Import ServiceContainer from correct location
from src.core import ServiceContainer

# Import models with proper fallbacks
try:
    from src.models import User, UserRole, UserStatus
    from src.core import DateTimeHelper

    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    from dataclasses import dataclass
    from enum import Enum


    class UserRole(Enum):
        ADMIN = 'admin'
        DEVELOPER = 'developer'
        VIEWER = 'viewer'


    class UserStatus(Enum):
        ACTIVE = 'active'
        INACTIVE = 'inactive'


    @dataclass
    class User:
        pass


    class DateTimeHelper:
        @staticmethod
        def now():
            from datetime import datetime, timezone
            return datetime.now(timezone.utc)


class UserManagerAgent(BaseAgent):
    """Agent responsible for user management and authentication"""

    def __init__(self, services: ServiceContainer):
        """Initialize UserManagerAgent"""
        super().__init__("user_manager", "User Manager", services)

    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            'create_user',
            'authenticate_user',
            'get_user',
            'update_user',
            'delete_user',
            'list_users',
            'deactivate_user',
            'manage_roles',
            'assign_permissions',
            'verify_permissions',
            'get_user_profile',
            'update_password'
        ]

    # ========================================================================
    # USER CRUD OPERATIONS
    # ========================================================================

    @log_agent_action
    def _create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with role and permissions"""
        try:
            # Validate required fields
            username = data.get('username')
            password_hash = data.get('password_hash') or data.get('passcode_hash')

            if not username or not password_hash:
                return self._error_response("Username and password are required", "MISSING_FIELDS")

            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            # Check if user already exists
            existing_user = self.db.users.get_by_username(username)
            if existing_user:
                return self._error_response(f"Username '{username}' already exists", "USER_EXISTS")

            # Get optional fields with defaults
            email = data.get('email', '')
            role_str = data.get('role', 'developer').lower()
            status_str = data.get('status', 'active').lower()

            # Convert to enums with validation
            try:
                role = UserRole(role_str.lower())
            except ValueError:
                return self._error_response(f"Invalid role: {role_str}", "INVALID_ROLE")

            try:
                status = UserStatus(status_str.lower())
            except ValueError:
                return self._error_response(f"Invalid status: {status_str}", "INVALID_STATUS")

            # Create user model
            user = User(
                username=username,
                email=email or "",
                password_hash=password_hash,
                role=role,
                status=status,
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                skills=data.get('skills', []),
                created_at=datetime.now(),
                last_login=None
            )

            # Save to database
            create_success = self.db.users.create(user)
            if not create_success:
                return self._error_response("Failed to create user in database", "DB_CREATE_FAILED")

            # Fetch the created user
            created_user = self.db.users.get_by_id(user.id)
            if not created_user:
                return self._error_response("User created but could not be retrieved", "DB_RETRIEVE_FAILED")

            # Assign role capabilities
            role_assignment = self._assign_role_to_user(created_user, role_str)

            self.logger.info(f"User created successfully: {username} with role {role_str}")

            return self._success_response(
                f"User '{username}' created successfully with role '{role_str}'",
                {
                    'user': created_user.to_dict(),
                    'role_assignment': role_assignment
                }
            )

        except Exception as e:
            self.logger.error(f"User creation failed: {e}")
            return self._error_response(f"Failed to create user: {str(e)}", "CREATE_FAILED")

    @log_agent_action
    def _authenticate_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user and return session token"""
        try:
            username = data.get('username')
            password_hash = data.get('password_hash') or data.get('passcode_hash')

            if not username or not password_hash:
                return self._error_response("Username and password are required", "MISSING_CREDENTIALS")

            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            # Get user
            user = self.db.users.get_by_username(username)
            if not user:
                return self._error_response("Invalid username or password", "AUTH_FAILED")

            # Verify password
            if user.password_hash != password_hash:
                return self._error_response("Invalid username or password", "AUTH_FAILED")

            # Check if user is active
            if user.status != UserStatus.ACTIVE:
                return self._error_response(f"User account is {user.status.value}", "USER_INACTIVE")

            # Update last login
            user.last_login = DateTimeHelper.now()
            self.db.users.update(user.id, user)

            self.logger.info(f"User authenticated successfully: {username}")

            return self._success_response(
                "Authentication successful",
                {
                    'user_id': user.id,
                    'username': user.username,
                    'role': str(user.role.value),
                    'permissions': self._get_user_permissions(user.role)
                }
            )

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return self._error_response(f"Authentication failed: {str(e)}", "AUTH_ERROR")

    @log_agent_action
    def _get_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve user by ID or username"""
        try:
            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            username = data.get('username')

            if not user_id and not username:
                return self._error_response("User ID or username is required", "MISSING_IDENTIFIER")

            # Get user by ID or username
            if user_id:
                user = self.db.users.get(user_id)
            else:
                user = self.db.users.get_by_username(username)

            if not user:
                return self._error_response("User not found", "USER_NOT_FOUND")

            return self._success_response(
                "User retrieved successfully",
                {'user': user.to_dict()}
            )

        except Exception as e:
            self.logger.error(f"User retrieval failed: {e}")
            return self._error_response(f"Failed to retrieve user: {str(e)}", "GET_FAILED")

    @log_agent_action
    def _update_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information"""
        try:
            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            if not user_id:
                return self._error_response("User ID is required", "MISSING_USER_ID")

            user = self.db.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}", "USER_NOT_FOUND")

            # Update fields if provided
            if 'email' in data:
                user.email = data['email']
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'skills' in data:
                user.skills = data['skills']

            updated_user = self.db.users.update(user_id, user)

            self.logger.info(f"User updated successfully: {user.username}")

            return self._success_response(
                f"User '{user.username}' updated successfully",
                {'user': updated_user.to_dict()}
            )

        except Exception as e:
            self.logger.error(f"User update failed: {e}")
            return self._error_response(f"Failed to update user: {str(e)}", "UPDATE_FAILED")

    @log_agent_action
    def _delete_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a user (soft delete by setting status to inactive)"""
        try:
            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            if not user_id:
                return self._error_response("User ID is required", "MISSING_USER_ID")

            user = self.db.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}", "USER_NOT_FOUND")

            # Soft delete - set status to inactive
            user.status = UserStatus.INACTIVE
            self.db.users.update(user_id, user)

            self.logger.info(f"User deleted (soft): {user.username}")

            return self._success_response(
                f"User '{user.username}' has been deactivated",
                {'user_id': user_id}
            )

        except Exception as e:
            self.logger.error(f"User deletion failed: {e}")
            return self._error_response(f"Failed to delete user: {str(e)}", "DELETE_FAILED")

    @log_agent_action
    def _list_users(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """List all users with optional filters"""
        try:
            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            # Get filter parameters
            status = data.get('status')
            role = data.get('role')
            limit = data.get('limit')
            offset = data.get('offset')

            # Get users
            users = self.db.users.list_all(limit=limit, offset=offset)

            # Apply filters
            if status:
                try:
                    status_enum = UserStatus(status.lower())
                    users = [u for u in users if u.status == status_enum]
                except ValueError:
                    return self._error_response(f"Invalid status filter: {status}", "INVALID_FILTER")

            if role:
                try:
                    role_enum = UserRole(role.lower())
                    users = [u for u in users if u.role == role_enum]
                except ValueError:
                    return self._error_response(f"Invalid role filter: {role}", "INVALID_FILTER")

            return self._success_response(
                f"Retrieved {len(users)} users",
                {
                    'users': [u.to_dict() for u in users],
                    'count': len(users)
                }
            )

        except Exception as e:
            self.logger.error(f"User listing failed: {e}")
            return self._error_response(f"Failed to list users: {str(e)}", "LIST_FAILED")

    @log_agent_action
    def _deactivate_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deactivate a user account"""
        try:
            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            if not user_id:
                return self._error_response("User ID is required", "MISSING_USER_ID")

            user = self.db.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}", "USER_NOT_FOUND")

            # Update status
            user.status = UserStatus.INACTIVE
            updated_user = self.db.users.update(user_id, user)

            self.logger.info(f"User deactivated: {user.username}")

            return self._success_response(
                f"User '{user.username}' has been deactivated",
                updated_user.to_dict()
            )

        except Exception as e:
            self.logger.error(f"User deactivation failed: {e}")
            return self._error_response(f"Failed to deactivate user: {str(e)}", "DEACTIVATE_FAILED")

    # ========================================================================
    # ROLE AND PERMISSION MANAGEMENT
    # ========================================================================

    @log_agent_action
    def _manage_roles(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage user roles (assign, update, revoke)"""
        try:
            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            new_role = data.get('role')

            if not user_id or not new_role:
                return self._error_response("User ID and role are required", "MISSING_FIELDS")

            # Validate role
            try:
                role_enum = UserRole(new_role.lower())
            except ValueError:
                return self._error_response(f"Invalid role: {new_role}", "INVALID_ROLE")

            user = self.db.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}", "USER_NOT_FOUND")

            old_role = user.role
            user.role = role_enum
            updated_user = self.db.users.update(user_id, user)

            self.logger.info(f"User role updated: {user.username} from {old_role.value} to {role_enum.value}")

            return self._success_response(
                f"Role updated from '{old_role.value}' to '{role_enum.value}'",
                {
                    'user': updated_user.to_dict(),
                    'old_role': str(old_role.value),
                    'new_role': str(role_enum.value),
                    'permissions': self._get_user_permissions(role_enum)
                }
            )

        except Exception as e:
            self.logger.error(f"Role management failed: {e}")
            return self._error_response(f"Failed to manage role: {str(e)}", "ROLE_UPDATE_FAILED")

    def _assign_role_to_user(self, user: User, role: str) -> Dict[str, Any]:
        """Internal method to assign role and permissions to user"""
        try:
            role_info = self._get_role_capabilities(role)

            self.logger.info(
                f"Assigned role '{role}' to user '{user.username}' "
                f"with {len(role_info['capabilities'])} capabilities"
            )

            return {
                'success': True,
                'role': role,
                'capabilities': role_info['capabilities']
            }

        except Exception as e:
            self.logger.error(f"Role assignment failed: {e}")
            return {'success': False, 'error': str(e)}

    @log_agent_action
    def _assign_permissions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assign specific permissions to a user"""
        try:
            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            permissions = data.get('permissions', [])

            if not user_id:
                return self._error_response("User ID is required", "MISSING_USER_ID")

            user = self.db.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}", "USER_NOT_FOUND")

            # Get current role permissions
            role_permissions = self._get_user_permissions(user.role)

            # Combine with additional permissions
            all_permissions = list(set(role_permissions + permissions))

            self.logger.info(f"Assigned {len(permissions)} additional permissions to {user.username}")

            return self._success_response(
                f"Assigned {len(permissions)} additional permissions to {user.username}",
                {
                    'user_id': user_id,
                    'role': str(user.role.value),
                    'base_permissions': role_permissions,
                    'additional_permissions': permissions,
                    'total_permissions': all_permissions
                }
            )

        except Exception as e:
            self.logger.error(f"Permission assignment failed: {e}")
            return self._error_response(f"Failed to assign permissions: {str(e)}", "PERMISSION_ASSIGN_FAILED")

    @log_agent_action
    def _verify_permissions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify if user has specific permissions"""
        try:
            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            required_permissions = data.get('permissions', [])

            if not user_id:
                return self._error_response("User ID is required", "MISSING_USER_ID")

            user = self.db.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}", "USER_NOT_FOUND")

            # Get user permissions
            user_permissions = self._get_user_permissions(user.role)

            # Check if user has all required permissions
            has_permissions = all(perm in user_permissions for perm in required_permissions)

            return self._success_response(
                "Permission verification complete",
                {
                    'user_id': user_id,
                    'has_permissions': has_permissions,
                    'required_permissions': required_permissions,
                    'user_permissions': user_permissions
                }
            )

        except Exception as e:
            self.logger.error(f"Permission verification failed: {e}")
            return self._error_response(f"Failed to verify permissions: {str(e)}", "PERMISSION_VERIFY_FAILED")

    # ========================================================================
    # PROFILE MANAGEMENT
    # ========================================================================

    @log_agent_action
    def _get_user_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed user profile"""
        try:
            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            if not user_id:
                return self._error_response("User ID is required", "MISSING_USER_ID")

            user = self.db.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}", "USER_NOT_FOUND")

            profile = {
                'user': user.to_dict(),
                'permissions': self._get_user_permissions(user.role),
                'role_info': self._get_role_capabilities(user.role.value)
            }

            return self._success_response(
                "User profile retrieved",
                {'profile': profile}
            )

        except Exception as e:
            self.logger.error(f"Profile retrieval failed: {e}")
            return self._error_response(f"Failed to get profile: {str(e)}", "PROFILE_GET_FAILED")

    @log_agent_action
    def _update_password(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user password"""
        try:
            # Check database availability
            if not self.db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            new_password_hash = data.get('new_password_hash')

            if not user_id or not new_password_hash:
                return self._error_response("User ID and new password are required", "MISSING_FIELDS")

            user = self.db.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}", "USER_NOT_FOUND")

            # Update password
            user.password_hash = new_password_hash
            self.db.users.update(user_id, user)

            self.logger.info(f"Password updated for user: {user.username}")

            return self._success_response(
                "Password updated successfully",
                {'user_id': user_id}
            )

        except Exception as e:
            self.logger.error(f"Password update failed: {e}")
            return self._error_response(f"Failed to update password: {str(e)}", "PASSWORD_UPDATE_FAILED")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_user_permissions(self, role: UserRole) -> List[str]:
        """Get permissions for a specific role"""
        permissions_map = {
            UserRole.ADMIN: [
                'user:create', 'user:read', 'user:update', 'user:delete',
                'project:create', 'project:read', 'project:update', 'project:delete',
                'system:configure', 'system:monitor'
            ],
            UserRole.DEVELOPER: [
                'user:read',
                'project:create', 'project:read', 'project:update',
                'code:generate', 'code:review'
            ],
            UserRole.VIEWER: [
                'user:read',
                'project:read'
            ]
        }
        return permissions_map.get(role, [])

    def _get_role_capabilities(self, role: str) -> Dict[str, Any]:
        """Get detailed capabilities for a role"""
        capabilities_map = {
            'admin': {
                'name': 'Administrator',
                'description': 'Full system access with all permissions',
                'capabilities': [
                    'Manage all users',
                    'Manage all projects',
                    'Configure system settings',
                    'Monitor system health',
                    'Generate and review code'
                ]
            },
            'developer': {
                'name': 'Developer',
                'description': 'Can create and manage own projects',
                'capabilities': [
                    'View users',
                    'Create and manage projects',
                    'Generate code',
                    'Review code'
                ]
            },
            'viewer': {
                'name': 'Viewer',
                'description': 'Read-only access to projects',
                'capabilities': [
                    'View users',
                    'View projects'
                ]
            }
        }
        return capabilities_map.get(role.lower(), {})


# Module exports
__all__ = ['UserManagerAgent']
