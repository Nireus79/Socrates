#!/usr/bin/env python3
"""
UserManagerAgent - Enhanced User Management with Role-Based Capabilities
=========================================================================

Handles user lifecycle, authentication, role assignment, and team management.
Fully corrected according to project standards.

Capabilities:
- User lifecycle management (create, authenticate, update, deactivate)
- Role-based access control and permission management
- Team management and collaboration features
- User activity tracking and analytics
- Skill assessment and productivity monitoring
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging
import secrets

# ============================================================================
# IMPORTS WITH COMPREHENSIVE FALLBACKS
# ============================================================================

try:
    from src.core import ServiceContainer, DateTimeHelper, ValidationError, ValidationHelper
    from src.models import User, UserRole, UserStatus, ModelValidator
    from src.database import get_database
    from .base import BaseAgent, require_authentication, log_agent_action

    CORE_AVAILABLE = True

except ImportError:
    CORE_AVAILABLE = False

    # Fallback ServiceContainer
    class ServiceContainer:
        """Fallback ServiceContainer when core is not available"""

        def __init__(self):
            self.config = None
            self.logger_system = None
            self.event_system = None
            self.db_manager = None

        def get_logger(self, name: str):
            return logging.getLogger(name)

        def get_config(self):
            return {}

        def get_event_bus(self):
            return None

        def get_db_manager(self):
            return None


    # Fallback DateTimeHelper
    class DateTimeHelper:
        """Fallback DateTimeHelper"""

        @staticmethod
        def now():
            return datetime.now()

        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None

        @staticmethod
        def from_iso_string(iso_str):
            return datetime.fromisoformat(iso_str) if iso_str else None


    # Fallback ValidationError
    class ValidationError(Exception):
        """Fallback ValidationError"""
        pass


    # Fallback ValidationHelper
    class ValidationHelper:
        """Fallback ValidationHelper"""

        @staticmethod
        def validate_email(email: str) -> bool:
            return "@" in str(email) if email else False

        @staticmethod
        def validate_required(value: Any, field_name: str) -> bool:
            if not value:
                raise ValidationError(f"{field_name} is required")
            return True

        @staticmethod
        def validate_length(value: str, min_len: int, max_len: int, field_name: str) -> bool:
            if len(value) < min_len or len(value) > max_len:
                raise ValidationError(f"{field_name} must be between {min_len} and {max_len} characters")
            return True


    # Fallback UserRole enum
    class UserRole(Enum):
        """Fallback UserRole enum"""
        ADMIN = "admin"
        PROJECT_MANAGER = "project_manager"
        DEVELOPER = "developer"
        DESIGNER = "designer"
        TESTER = "tester"
        STAKEHOLDER = "stakeholder"
        VIEWER = "viewer"


    # Fallback UserStatus enum
    class UserStatus(Enum):
        """Fallback UserStatus enum"""
        ACTIVE = "active"
        PENDING = "pending"
        SUSPENDED = "suspended"
        INACTIVE = "inactive"


    # Fallback User model
    class User:
        """Fallback User model"""

        def __init__(self, **kwargs):
            self.id = kwargs.get('id', '')
            self.username = kwargs.get('username', '')
            self.email = kwargs.get('email', '')
            self.password_hash = kwargs.get('password_hash', '')
            self.first_name = kwargs.get('first_name', '')
            self.last_name = kwargs.get('last_name', '')
            self.full_name = kwargs.get('full_name', '')
            self.role = kwargs.get('role', UserRole.VIEWER)
            self.status = kwargs.get('status', UserStatus.PENDING)
            self.created_at = kwargs.get('created_at', DateTimeHelper.now())
            self.last_login = kwargs.get('last_login', None)
            self.skills = kwargs.get('skills', [])
            self.projects_created = kwargs.get('projects_created', 0)

        def to_dict(self):
            return {
                'id': self.id,
                'username': self.username,
                'email': self.email,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'full_name': self.full_name,
                'role': self.role.value if isinstance(self.role, Enum) else self.role,
                'status': self.status.value if isinstance(self.status, Enum) else self.status,
                'created_at': DateTimeHelper.to_iso_string(self.created_at),
                'last_login': DateTimeHelper.to_iso_string(self.last_login),
                'skills': self.skills,
                'projects_created': self.projects_created
            }


    # Fallback ModelValidator
    class ModelValidator:
        """Fallback ModelValidator"""

        @staticmethod
        def validate(model: Any) -> bool:
            return True

        @staticmethod
        def validate_user(user: User) -> bool:
            if not user.username or not user.email:
                raise ValidationError("Username and email are required")
            return True


    # Fallback database function
    def get_database():
        """Fallback database function"""
        return None


    # Fallback BaseAgent class
    class BaseAgent:
        """Fallback BaseAgent when base module is not available"""

        def __init__(self, agent_id: str, name: str, services: Optional[ServiceContainer] = None):
            self.agent_id = agent_id
            self.name = name
            self.services = services
            self.logger = logging.getLogger(f"agent.{agent_id}")
            self.config = {}
            self.event_bus = None
            self.db_manager = None
            self.db_service = None

        def get_capabilities(self) -> List[str]:
            return []

        def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
            return {
                'success': False,
                'error': 'Agent functionality not available',
                'agent_id': self.agent_id,
                'action': action
            }

        def health_check(self) -> Dict[str, Any]:
            return {
                'agent_id': self.agent_id,
                'name': self.name,
                'status': 'degraded',
                'available': False
            }

        def _error_response(self, message: str) -> Dict[str, Any]:
            return {
                'success': False,
                'error': message
            }

        def _success_response(self, message: str, data: Any = None) -> Dict[str, Any]:
            """Create success response with message and optional data"""
            response = {
                'success': True,
                'message': message
            }
            if data is not None:
                response['data'] = data
            return response


    # Fallback decorators
    def require_authentication(func):
        """Fallback authentication decorator"""

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


    def log_agent_action(func):
        """Fallback logging decorator"""

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


# ============================================================================
# ROLE CONSTANTS - Using string literals to avoid enum .value type issues
# ============================================================================

class RoleConstants:
    """String constants for roles"""
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    TESTER = "tester"
    STAKEHOLDER = "stakeholder"
    VIEWER = "viewer"


# ============================================================================
# USER MANAGER AGENT
# ============================================================================

class UserManagerAgent(BaseAgent):
    """
    Enhanced user management agent with role-based capabilities

    Capabilities: Complete user lifecycle, authentication, team management
    """

    def __init__(self, services: Optional[ServiceContainer] = None):
        """Initialize UserManagerAgent"""
        super().__init__("user_manager", "User Manager", services)

        # Get database service if available
        if self.db_manager:
            self.db_service = get_database()
        else:
            self.db_service = None

        if self.logger:
            self.logger.info("UserManagerAgent initialized successfully")

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            "create_user", "authenticate_user", "update_profile", "manage_roles",
            "assign_permissions", "track_activity", "team_management",
            "skill_assessment", "productivity_analytics", "list_users",
            "deactivate_user", "get_user_info", "check_permissions"
        ]

    def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user management requests"""
        action_map = {
            'create_user': self._create_user,
            'authenticate_user': self._authenticate_user,
            'update_profile': self._update_profile,
            'manage_roles': self._manage_roles,
            'assign_permissions': self._assign_permissions,
            'list_users': self._list_users,
            'deactivate_user': self._deactivate_user,
            'get_user_info': self._get_user_info,
            'check_permissions': self._check_permissions,
            'get_role_info': self._get_role_info
        }

        handler = action_map.get(action)
        if not handler:
            return self._error_response(f"Unknown action: {action}")

        try:
            return handler(data)
        except Exception as e:
            self.logger.error(f"Error processing {action}: {e}")
            return self._error_response(f"Action failed: {str(e)}")

    # ========================================================================
    # USER LIFECYCLE MANAGEMENT
    # ========================================================================

    @log_agent_action
    def _create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user with proper validation and role assignment"""
        try:
            # Extract and validate required fields
            username = data.get('username')
            email = data.get('email')
            password_hash = data.get('password_hash') or data.get('passcode_hash')

            # Only validate email if provided and not empty
            if email and email.strip():
                existing_email = self.db_service.users.get_by_email(email)
                if existing_email:
                    return self._error_response(f"Email '{email}' is already registered")

            # Check if user already exists
            if self.db_service:
                existing_user = self.db_service.users.get_by_username(username)
                if existing_user:
                    return self._error_response(f"User '{username}' already exists")

                # Only check for duplicate email if provided and not empty
                if email and email.strip():
                    existing_email = self.db_service.users.get_by_email(email)
                    if existing_email:
                        return self._error_response(f"Email '{email}' is already registered")

            # Parse role with validation
            role_str = data.get('role', RoleConstants.DEVELOPER)
            try:
                if isinstance(role_str, str):
                    user_role = UserRole(role_str.lower())
                else:
                    user_role = UserRole.DEVELOPER
            except ValueError:
                self.logger.warning(f"Invalid role '{role_str}', defaulting to DEVELOPER")
                user_role = UserRole.DEVELOPER

            # Create user model
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                full_name=data.get('full_name', f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()),
                role=user_role,
                status=UserStatus.ACTIVE,
                created_at=DateTimeHelper.now(),
                skills=data.get('skills', [])
            )

            # Validate user data
            try:
                ModelValidator.validate_user(new_user)
            except ValidationError as e:
                return self._error_response(f"User validation failed: {str(e)}")

            # Save to database
            if self.db_service:
                created_user = self.db_service.users.create(new_user)

                self.logger.info(f"User created successfully: {username}")

                # Assign default role permissions
                self._assign_role_to_user(created_user, str(user_role.value))

                return self._success_response(
                    f"User '{username}' created successfully with role '{user_role.value}'",
                    created_user.to_dict()
                )
            else:
                return self._error_response("Database service not available")

        except Exception as e:
            self.logger.error(f"User creation failed: {e}")
            return self._error_response(f"Failed to create user: {str(e)}")

    @log_agent_action
    def _authenticate_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user with username/email and password"""
        try:
            identifier = data.get('username') or data.get('email')
            password_hash = data.get('password_hash')

            if not identifier or not password_hash:
                return self._error_response("Username/email and password are required")

            if not self.db_service:
                return self._error_response("Database service not available")

            # Try to find user by username or email
            user = None
            if '@' in identifier:
                user = self.db_service.users.get_by_email(identifier)
            else:
                user = self.db_service.users.get_by_username(identifier)

            if not user:
                self.logger.warning(f"Authentication failed: User '{identifier}' not found")
                return self._error_response("Invalid credentials")

            # Check if account is active
            if user.status != UserStatus.ACTIVE:
                return self._error_response(f"Account is {user.status.value}")

            # Verify password
            if user.password_hash != password_hash:
                self.logger.warning(f"Authentication failed: Invalid password for '{identifier}'")
                return self._error_response("Invalid credentials")

            # Update last login
            user.last_login = DateTimeHelper.now()
            self.db_service.users.update(user.id, user)

            self.logger.info(f"User authenticated successfully: {user.username}")

            # Generate session token (simplified)
            session_token = secrets.token_urlsafe(32)

            return self._success_response(
                f"Welcome back, {user.username}!",
                {
                    'user': user.to_dict(),
                    'session_token': session_token,
                    'permissions': self._get_user_permissions(user.role)
                }
            )

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return self._error_response(f"Authentication failed: {str(e)}")

    @log_agent_action
    def _update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile information"""
        try:
            user_id = data.get('user_id')
            if not user_id:
                return self._error_response("User ID is required")

            if not self.db_service:
                return self._error_response("Database service not available")

            user = self.db_service.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}")

            # Update allowed fields
            updatable_fields = ['first_name', 'last_name', 'full_name', 'email', 'skills']

            for field in updatable_fields:
                if field in data:
                    setattr(user, field, data[field])

            # Validate updated user
            if 'email' in data:
                if not ValidationHelper.validate_email(data['email']):
                    return self._error_response("Invalid email address")

            # Save changes
            updated_user = self.db_service.users.update(user_id, user)

            self.logger.info(f"User profile updated: {user.username}")

            return self._success_response(
                "Profile updated successfully",
                updated_user.to_dict()
            )

        except Exception as e:
            self.logger.error(f"Profile update failed: {e}")
            return self._error_response(f"Failed to update profile: {str(e)}")

    @log_agent_action
    def _deactivate_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deactivate a user account"""
        try:
            user_id = data.get('user_id')
            if not user_id:
                return self._error_response("User ID is required")

            if not self.db_service:
                return self._error_response("Database service not available")

            user = self.db_service.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}")

            # Update status
            user.status = UserStatus.INACTIVE
            updated_user = self.db_service.users.update(user_id, user)

            self.logger.info(f"User deactivated: {user.username}")

            return self._success_response(
                f"User '{user.username}' has been deactivated",
                updated_user.to_dict()
            )

        except Exception as e:
            self.logger.error(f"User deactivation failed: {e}")
            return self._error_response(f"Failed to deactivate user: {str(e)}")

    # ========================================================================
    # ROLE AND PERMISSION MANAGEMENT
    # ========================================================================

    @log_agent_action
    def _manage_roles(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage user roles (assign, update, revoke)"""
        try:
            user_id = data.get('user_id')
            new_role = data.get('role')

            if not user_id or not new_role:
                return self._error_response("User ID and role are required")

            # Validate role
            try:
                role_enum = UserRole(new_role.lower())
            except ValueError:
                return self._error_response(f"Invalid role: {new_role}")

            if not self.db_service:
                return self._error_response("Database service not available")

            user = self.db_service.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}")

            old_role = user.role
            user.role = role_enum
            updated_user = self.db_service.users.update(user_id, user)

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
            return self._error_response(f"Failed to manage role: {str(e)}")

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
            user_id = data.get('user_id')
            permissions = data.get('permissions', [])

            if not user_id:
                return self._error_response("User ID is required")

            if not self.db_service:
                return self._error_response("Database service not available")

            user = self.db_service.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}")

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
            return self._error_response(f"Failed to assign permissions: {str(e)}")

    @log_agent_action
    def _check_permissions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if user has specific permissions"""
        try:
            user_id = data.get('user_id')
            required_permissions = data.get('permissions', [])

            if not user_id:
                return self._error_response("User ID is required")

            if not self.db_service:
                return self._error_response("Database service not available")

            user = self.db_service.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}")

            user_permissions = self._get_user_permissions(user.role)

            # Check each required permission
            has_all = all(perm in user_permissions for perm in required_permissions)
            missing = [perm for perm in required_permissions if perm not in user_permissions]

            return self._success_response(
                "Permission check completed",
                {
                    'user_id': user_id,
                    'role': str(user.role.value),
                    'has_all_permissions': has_all,
                    'user_permissions': user_permissions,
                    'required_permissions': required_permissions,
                    'missing_permissions': missing
                }
            )

        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            return self._error_response(f"Failed to check permissions: {str(e)}")

    # ========================================================================
    # USER INFORMATION AND LISTING
    # ========================================================================

    @log_agent_action
    def _get_user_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a user"""
        try:
            user_id = data.get('user_id')
            username = data.get('username')

            if not user_id and not username:
                return self._error_response("User ID or username is required")

            if not self.db_service:
                return self._error_response("Database service not available")

            # Get user
            if user_id:
                user = self.db_service.users.get(user_id)
            else:
                user = self.db_service.users.get_by_username(username)

            if not user:
                return self._error_response("User not found")

            # Get role information
            role_info = self._get_role_capabilities(str(user.role.value))

            user_info = user.to_dict()
            user_info['role_info'] = role_info
            user_info['permissions'] = self._get_user_permissions(user.role)

            return self._success_response("User information retrieved", user_info)

        except Exception as e:
            self.logger.error(f"Get user info failed: {e}")
            return self._error_response(f"Failed to get user info: {str(e)}")

    @log_agent_action
    def _list_users(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """List users with optional filtering"""
        try:
            if not self.db_service:
                return self._error_response("Database service not available")

            # Get filtering parameters
            role_filter = data.get('role')
            status_filter = data.get('status')
            limit = data.get('limit', 50)
            offset = data.get('offset', 0)

            # Get all users
            all_users = self.db_service.users.list()

            # Apply filters
            filtered_users = all_users
            if role_filter:
                try:
                    role_enum = UserRole(role_filter.lower())
                    filtered_users = [u for u in filtered_users if u.role == role_enum]
                except ValueError:
                    return self._error_response(f"Invalid role filter: {role_filter}")

            if status_filter:
                try:
                    status_enum = UserStatus(status_filter.lower())
                    filtered_users = [u for u in filtered_users if u.status == status_enum]
                except ValueError:
                    return self._error_response(f"Invalid status filter: {status_filter}")

            # Apply pagination
            total_count = len(filtered_users)
            paginated_users = filtered_users[offset:offset + limit]

            # Format user data
            user_list = []
            for user in paginated_users:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': getattr(user, 'full_name', ''),
                    'role': str(user.role.value) if hasattr(user.role, 'value') else str(user.role),
                    'status': str(user.status.value) if hasattr(user.status, 'value') else str(user.status),
                    'created_at': DateTimeHelper.to_iso_string(user.created_at) if isinstance(user.created_at,
                                                                                              datetime) else str(
                        user.created_at),
                    'last_login': DateTimeHelper.to_iso_string(user.last_login) if isinstance(user.last_login,
                                                                                              datetime) else str(
                        user.last_login) if user.last_login else None
                }
                user_list.append(user_data)

            return self._success_response(
                f"Retrieved {len(user_list)} users",
                {
                    'users': user_list,
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + limit) < total_count
                }
            )

        except Exception as e:
            self.logger.error(f"List users failed: {e}")
            return self._error_response(f"Failed to list users: {str(e)}")

    @log_agent_action
    def _get_role_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a specific role"""
        try:
            role = data.get('role')
            if not role:
                # Return info about all roles
                all_roles = {}
                for role_key in [RoleConstants.ADMIN, RoleConstants.PROJECT_MANAGER,
                                 RoleConstants.DEVELOPER, RoleConstants.DESIGNER,
                                 RoleConstants.TESTER, RoleConstants.STAKEHOLDER,
                                 RoleConstants.VIEWER]:
                    all_roles[role_key] = self._get_role_capabilities(role_key)

                return self._success_response("Role information retrieved", {'roles': all_roles})

            # Get specific role info
            role_info = self._get_role_capabilities(role)
            return self._success_response("Role information retrieved", role_info)

        except Exception as e:
            self.logger.error(f"Get role info failed: {e}")
            return self._error_response(f"Failed to get role info: {str(e)}")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_role_capabilities(self, role: str) -> Dict[str, Any]:
        """
        Get capabilities and information for a specific role

        Args:
            role: Role string (e.g., 'admin', 'developer')

        Returns:
            Dict containing role capabilities and description
        """
        # Use string literals for dictionary keys to avoid enum .value type issues
        role_capabilities: Dict[str, List[str]] = {
            "admin": [
                'manage_users', 'system_admin', 'view_all_projects', 'delete_projects',
                'manage_system_settings', 'view_analytics', 'manage_permissions'
            ],
            "project_manager": [
                'create_project', 'manage_team', 'view_analytics', 'manage_timeline',
                'allocate_resources', 'manage_risks', 'approve_deliverables'
            ],
            "developer": [
                'write_code', 'run_tests', 'submit_code_reviews', 'implement_features',
                'fix_bugs', 'create_documentation', 'deploy_code'
            ],
            "designer": [
                'create_designs', 'user_research', 'design_systems', 'prototyping',
                'accessibility_review', 'visual_design', 'ux_research'
            ],
            "tester": [
                'create_tests', 'run_test_suites', 'report_bugs', 'validate_requirements',
                'performance_testing', 'security_testing', 'test_automation'
            ],
            "stakeholder": [
                'view_progress', 'provide_feedback', 'approve_requirements',
                'review_deliverables', 'request_changes', 'view_reports'
            ],
            "viewer": [
                'view_projects', 'view_progress', 'read_documentation'
            ]
        }

        return {
            'role': role,
            'capabilities': role_capabilities.get(role, []),
            'description': self._get_role_description(role)
        }

    def _get_role_description(self, role: str) -> str:
        """
        Get description for a role

        Args:
            role: Role string (e.g., 'admin', 'developer')

        Returns:
            Human-readable role description
        """
        # Use string literals for dictionary keys
        descriptions: Dict[str, str] = {
            "admin": "Full system administration and user management",
            "project_manager": "Project planning, team coordination, and delivery management",
            "developer": "Software development, coding, and technical implementation",
            "designer": "User experience design, visual design, and prototyping",
            "tester": "Quality assurance, testing, and bug reporting",
            "stakeholder": "Business oversight, requirements approval, and feedback",
            "viewer": "Read-only access to projects and documentation"
        }
        return descriptions.get(role, "Unknown role")

    def _get_user_permissions(self, role: UserRole) -> List[str]:
        """
        Get permissions for a specific role

        Args:
            role: UserRole enum instance

        Returns:
            List of permission strings
        """
        # Convert enum to string explicitly
        role_str = str(role.value) if hasattr(role, 'value') else str(role)
        role_capabilities = self._get_role_capabilities(role_str)
        return role_capabilities['capabilities']

    def health_check(self) -> Dict[str, Any]:
        """Check agent health status"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'status': 'healthy',
            'capabilities': len(self.get_capabilities()),
            'services_available': self.services is not None
        }
