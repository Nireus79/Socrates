"""
User Manager Agent - Enhanced user management with role-based capabilities

This agent handles complete user lifecycle operations including:
- User creation and authentication
- Role-based access control
- Team management
- Permission management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import secrets

from src.agents.base import BaseAgent, log_agent_action
from src.models import User, UserRole, UserStatus
from src.core import ServiceContainer
from src.database import get_database
from src.core import ValidationHelper, DateTimeHelper


# ============================================================================
# CONSTANTS
# ============================================================================

class RoleConstants:
    """User role constants"""
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
            # Get database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            # Extract and validate required fields
            username = data.get('username')
            email = data.get('email')
            password_hash = data.get('password_hash') or data.get('passcode_hash')

            # Check if user already exists
            existing_user = db.users.get_by_username(username)
            if existing_user:
                return self._error_response(f"User '{username}' already exists")

            # Only validate email if provided and not empty
            if email and email.strip():
                existing_email = db.users.get_by_email(email)
                if existing_email:
                    return self._error_response(f"Email '{email}' is already registered")

            if not username or not password_hash:
                return self._error_response("Username and password are required")

            # Validate email format if provided
            if email and email.strip():
                if not ValidationHelper.validate_email(email):
                    return self._error_response("Invalid email address")

            # Get role from data or default to developer
            role_str = data.get('role', RoleConstants.DEVELOPER)
            try:
                role = UserRole(role_str.lower())
            except ValueError:
                return self._error_response(f"Invalid role: {role_str}")

            # Get status or default to active
            status_str = data.get('status', 'active')
            try:
                status = UserStatus(status_str.lower())
            except ValueError:
                return self._error_response(f"Invalid status: {status_str}")

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
            created_user = db.users.create(user)
            if not created_user:
                return self._error_response("Failed to create user in database")

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
            return self._error_response(f"Failed to create user: {str(e)}")

    @log_agent_action
    def _authenticate_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user and return session token"""
        try:
            # Get database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            username = data.get('username')
            password_hash = data.get('password_hash') or data.get('passcode_hash')

            if not username or not password_hash:
                return self._error_response("Username and password are required")

            # Get user
            user = db.users.get_by_username(username)
            if not user:
                return self._error_response("Invalid username or password")

            # Verify password
            if user.password_hash != password_hash:
                return self._error_response("Invalid username or password")

            # Check if user is active
            if user.status != UserStatus.ACTIVE:
                return self._error_response(f"User account is {user.status.value}")

            # Update last login
            user.last_login = datetime.now()
            db.users.update(user.id, user)

            # Generate session token
            session_token = secrets.token_urlsafe(32)

            self.logger.info(f"User authenticated successfully: {username}")

            return self._success_response(
                f"Authentication successful for user '{username}'",
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
            # Get database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            if not user_id:
                return self._error_response("User ID is required")

            user = db.users.get(user_id)
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
            updated_user = db.users.update(user_id, user)

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
            # Get database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            if not user_id:
                return self._error_response("User ID is required")

            user = db.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}")

            # Update status
            user.status = UserStatus.INACTIVE
            updated_user = db.users.update(user_id, user)

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
            # Get database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            new_role = data.get('role')

            if not user_id or not new_role:
                return self._error_response("User ID and role are required")

            # Validate role
            try:
                role_enum = UserRole(new_role.lower())
            except ValueError:
                return self._error_response(f"Invalid role: {new_role}")

            user = db.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}")

            old_role = user.role
            user.role = role_enum
            updated_user = db.users.update(user_id, user)

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
            # Get database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            permissions = data.get('permissions', [])

            if not user_id:
                return self._error_response("User ID is required")

            user = db.users.get(user_id)
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
            # Get database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            required_permissions = data.get('permissions', [])

            if not user_id:
                return self._error_response("User ID is required")

            user = db.users.get(user_id)
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
            # Get database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            user_id = data.get('user_id')
            username = data.get('username')

            if not user_id and not username:
                return self._error_response("User ID or username is required")

            # Get user
            if user_id:
                user = db.users.get(user_id)
            else:
                user = db.users.get_by_username(username)

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
            # Get database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")

            # Get filtering parameters
            role_filter = data.get('role')
            status_filter = data.get('status')
            limit = data.get('limit', 50)
            offset = data.get('offset', 0)

            # Get all users
            all_users = db.users.list()

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

                return self._success_response(
                    "Retrieved information for all roles",
                    {'roles': all_roles}
                )

            # Get specific role info
            role_info = self._get_role_capabilities(role)

            return self._success_response(
                f"Retrieved information for role '{role}'",
                {'role': role, 'info': role_info}
            )

        except Exception as e:
            self.logger.error(f"Get role info failed: {e}")
            return self._error_response(f"Failed to get role info: {str(e)}")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_user_permissions(self, role: UserRole) -> List[str]:
        """Get list of permissions for a given role"""
        role_permissions = {
            UserRole.ADMIN: [
                'create_user', 'delete_user', 'manage_roles', 'manage_permissions',
                'create_project', 'delete_project', 'manage_project_settings',
                'create_module', 'delete_module', 'create_task', 'delete_task',
                'generate_code', 'review_code', 'deploy_code',
                'view_analytics', 'export_data', 'system_configuration'
            ],
            UserRole.PROJECT_MANAGER: [
                'create_project', 'update_project', 'manage_project_settings',
                'create_module', 'update_module', 'delete_module',
                'create_task', 'update_task', 'delete_task', 'assign_tasks',
                'view_analytics', 'export_project_data', 'manage_collaborators'
            ],
            UserRole.DEVELOPER: [
                'create_module', 'update_module', 'create_task', 'update_task',
                'generate_code', 'review_code', 'commit_code',
                'run_tests', 'view_project', 'comment'
            ],
            UserRole.DESIGNER: [
                'create_module', 'update_module', 'create_task', 'update_task',
                'upload_designs', 'view_project', 'comment'
            ],
            UserRole.TESTER: [
                'create_task', 'update_task', 'run_tests', 'report_bugs',
                'view_project', 'comment'
            ],
            UserRole.STAKEHOLDER: [
                'view_project', 'view_analytics', 'comment', 'request_features'
            ],
            UserRole.VIEWER: [
                'view_project'
            ]
        }

        return role_permissions.get(role, [])

    def _get_role_capabilities(self, role: str) -> Dict[str, Any]:
        """Get detailed capabilities for a role"""
        role_capabilities = {
            RoleConstants.ADMIN: {
                'name': 'Administrator',
                'description': 'Full system access and control',
                'capabilities': [
                    'User management', 'System configuration', 'All project operations',
                    'Analytics and reporting', 'Security management'
                ],
                'level': 'system'
            },
            RoleConstants.PROJECT_MANAGER: {
                'name': 'Project Manager',
                'description': 'Manages projects and teams',
                'capabilities': [
                    'Project creation and management', 'Team coordination',
                    'Task assignment', 'Progress tracking', 'Resource allocation'
                ],
                'level': 'project'
            },
            RoleConstants.DEVELOPER: {
                'name': 'Developer',
                'description': 'Develops and implements features',
                'capabilities': [
                    'Code generation', 'Module development', 'Task implementation',
                    'Code review', 'Testing'
                ],
                'level': 'execution'
            },
            RoleConstants.DESIGNER: {
                'name': 'Designer',
                'description': 'Creates designs and user experiences',
                'capabilities': [
                    'UI/UX design', 'Design uploads', 'Design review',
                    'Prototyping', 'Design documentation'
                ],
                'level': 'execution'
            },
            RoleConstants.TESTER: {
                'name': 'Tester',
                'description': 'Tests and validates features',
                'capabilities': [
                    'Test execution', 'Bug reporting', 'Quality assurance',
                    'Test documentation', 'Regression testing'
                ],
                'level': 'validation'
            },
            RoleConstants.STAKEHOLDER: {
                'name': 'Stakeholder',
                'description': 'Reviews and provides feedback',
                'capabilities': [
                    'Project viewing', 'Progress monitoring', 'Feedback provision',
                    'Feature requests', 'Report access'
                ],
                'level': 'oversight'
            },
            RoleConstants.VIEWER: {
                'name': 'Viewer',
                'description': 'Read-only access',
                'capabilities': [
                    'View projects', 'View documentation'
                ],
                'level': 'read-only'
            }
        }

        return role_capabilities.get(role, {
            'name': 'Unknown',
            'description': 'Unknown role',
            'capabilities': [],
            'level': 'none'
        })
