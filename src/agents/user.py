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

try:
    from src.core import ServiceContainer, DateTimeHelper, ValidationError, ValidationHelper
    from src.models import User, UserRole, UserStatus, ModelValidator
    from src.database import get_database
    from .base import BaseAgent, require_authentication, log_agent_action

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

    # Fallback implementations
    def get_logger(name):
        import logging
        return logging.getLogger(name)

    class ServiceContainer:
        def get_logger(self, name):
            import logging
            return logging.getLogger(name)
        def get_config(self):
            return {}

    def get_database():
        return None


class UserManagerAgent(BaseAgent):
    """
    Enhanced user management agent with role-based capabilities

    Absorbs: Role management functionality from legacy system
    Capabilities: Complete user lifecycle, authentication, team management
    """

    def __init__(self, services: Optional[ServiceContainer] = None):
        """Initialize UserManagerAgent with corrected patterns"""
        super().__init__("user_manager", "User Manager", services)

        # Initialize logging
        if self.logger:
            self.logger.info(f"UserManagerAgent initialized successfully")

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            "create_user", "authenticate_user", "update_profile", "manage_roles",
            "assign_permissions", "track_activity", "team_management",
            "skill_assessment", "productivity_analytics", "list_users",
            "deactivate_user", "get_user_info", "check_permissions"
        ]

    @log_agent_action
    def _create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user with proper validation and role assignment"""
        username = data.get('username')  # Initialize early

        try:
            # Extract and validate required fields
            email = data.get('email')
            password_hash = data.get('password_hash') or data.get('passcode_hash')  # Support both field names
            full_name = data.get('full_name', '')

            if not username or not password_hash:
                self.logger.warning("User creation failed: Username and password are required")
                return self._error_response("Username and password are required")

            if not ValidationHelper.validate_email(email):
                return self._error_response("Valid email address is required")

            # Check if user already exists
            if self.db_service:
                existing_user = self.db_service.users.get_by_username(username)
                if existing_user:
                    return self._error_response(f"User '{username}' already exists")

                existing_email = self.db_service.users.get_by_email(email)
                if existing_email:
                    return self._error_response(f"Email '{email}' is already registered")

            # Parse role with validation
            role_str = data.get('role', UserRole.DEVELOPER.value)
            try:
                if isinstance(role_str, str):
                    user_role = UserRole(role_str.lower())
                else:
                    user_role = UserRole.DEVELOPER  # Default fallback
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
                role=user_role,
                status=UserStatus.ACTIVE,
                bio=data.get('bio', ''),
                skills=data.get('skills', []),
                preferences=data.get('preferences', {}),
                created_at=DateTimeHelper.now(),
                updated_at=DateTimeHelper.now()
            )

            # Validate user data
            validation_errors = ModelValidator.validate_user_data(new_user.to_dict())
            if validation_errors:
                return self._error_response(f"Validation failed: {', '.join(validation_errors)}")

            # Save to database
            if self.db_service:
                saved_user = self.db_service.users.create(new_user)
                user_id = saved_user.id if saved_user else new_user.id
            else:
                user_id = new_user.id

            # Emit user creation event
            if self.events:
                self.events.emit('user_created', self.agent_id, {
                    'user_id': user_id,
                    'username': username,
                    'role': user_role.value,
                    'created_by': 'user_manager_agent'
                })

            self.logger.info(f"Successfully created user: {username} (ID: {user_id})")

            return self._success_response(f"User '{username}' created successfully", {
                'user_id': user_id,
                'username': username,
                'email': email,
                'role': user_role.value,
                'status': UserStatus.ACTIVE.value,
                'full_name': full_name,
                'created_at': DateTimeHelper.to_iso_string(new_user.created_at)
            })

        except ValidationError as ve:
            error_msg = f"User creation validation failed: {ve}"
            self.logger.error(error_msg)
            return self._error_response(str(ve))

        except Exception as e:
            error_msg = f"User creation failed for '{username}': {e}"
            self.logger.error(error_msg)
            return self._error_response(f"Failed to create user: {str(e)}")

    @require_authentication
    @log_agent_action
    def _authenticate_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user with password verification"""
        try:
            username = data.get('username')
            password_hash = data.get('password_hash')

            if not username or not password_hash:
                return self._error_response("Username and password are required")

            if not self.db_service:
                return self._error_response("Database service not available")

            # Get user from database
            user = self.db_service.users.get_by_username(username)
            if not user:
                self.logger.warning(f"Authentication failed: User '{username}' not found")
                return self._error_response("Invalid username or password")

            # Check user status
            if user.status != UserStatus.ACTIVE:
                self.logger.warning(f"Authentication failed: User '{username}' is not active")
                return self._error_response("Account is not active")

            # Check if account is locked
            if user.is_locked:
                self.logger.warning(f"Authentication failed: User '{username}' account is locked")
                return self._error_response("Account is temporarily locked")

            # Verify password (simplified check - in real implementation, use proper hashing)
            if user.password_hash != password_hash:
                # Increment failed login attempts
                user.login_attempts += 1
                if user.login_attempts >= 5:
                    # Lock account for 30 minutes
                    import datetime
                    user.locked_until = DateTimeHelper.now() + datetime.timedelta(minutes=30)
                    self.logger.warning(f"Account locked for user '{username}' due to multiple failed attempts")

                if self.db_service:
                    self.db_service.users.update(user.id, user)

                return self._error_response("Invalid username or password")

            # Authentication successful
            user.last_login = DateTimeHelper.now()
            user.login_attempts = 0  # Reset on successful login
            user.locked_until = None

            if self.db_service:
                self.db_service.users.update(user.id, user)

            # Emit authentication event
            if self.events:
                self.events.emit('user_authenticated', self.agent_id, {
                    'user_id': user.id,
                    'username': username,
                    'login_time': DateTimeHelper.to_iso_string(user.last_login)
                })

            self.logger.info(f"User '{username}' authenticated successfully")

            return self._success_response("Authentication successful", {
                'user_id': user.id,
                'username': user.username,
                'role': user.role.value,
                'last_login': DateTimeHelper.to_iso_string(user.last_login),
                'permissions': self._get_user_permissions(user.role)
            })

        except Exception as e:
            error_msg = f"Authentication error: {e}"
            self.logger.error(error_msg)
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

            # Get existing user
            user = self.db_service.users.get(user_id)
            if not user:
                return self._error_response(f"User not found: {user_id}")

            # Update allowed fields
            updatable_fields = ['first_name', 'last_name', 'bio', 'skills', 'preferences', 'avatar_url']
            updated_fields = []

            for field in updatable_fields:
                if field in data:
                    setattr(user, field, data[field])
                    updated_fields.append(field)

            # Special handling for email updates (requires validation)
            if 'email' in data:
                new_email = data['email']
                if ValidationHelper.validate_email(new_email):
                    # Check if email is already in use
                    existing_user = self.db_service.users.get_by_email(new_email)
                    if existing_user and existing_user.id != user_id:
                        return self._error_response("Email address is already in use")

                    user.email = new_email
                    updated_fields.append('email')
                else:
                    return self._error_response("Invalid email address")

            # Update timestamp
            user.updated_at = DateTimeHelper.now()

            # Save changes
            updated_user = self.db_service.users.update(user_id, user)

            # Emit profile update event
            if self.events:
                self.events.emit('profile_updated', self.agent_id, {
                    'user_id': user_id,
                    'updated_fields': updated_fields,
                    'updated_by': 'user_manager_agent'
                })

            self.logger.info(f"Profile updated for user {user_id}: {updated_fields}")

            return self._success_response("Profile updated successfully", {
                'user_id': user_id,
                'updated_fields': updated_fields,
                'updated_at': DateTimeHelper.to_iso_string(user.updated_at)
            })

        except Exception as e:
            error_msg = f"Profile update failed: {e}"
            self.logger.error(error_msg)
            return self._error_response(f"Failed to update profile: {str(e)}")

    @require_authentication
    @log_agent_action
    def _manage_roles(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage user role assignments"""
        try:
            action = data.get('action')  # 'assign', 'revoke', 'list'
            target_user_id = data.get('target_user_id')

            if action not in ['assign', 'revoke', 'list']:
                return self._error_response("Invalid action. Use: assign, revoke, or list")

            if not self.db_service:
                return self._error_response("Database service not available")

            if action == 'list':
                # List user roles
                if target_user_id:
                    user = self.db_service.users.get(target_user_id)
                    if not user:
                        return self._error_response(f"User not found: {target_user_id}")
                    return self._success_response("User role retrieved", self._list_user_roles(user))
                else:
                    # List all users and their roles
                    all_users = self.db_service.users.list()
                    user_roles = [self._list_user_roles(user) for user in all_users]
                    return self._success_response("All user roles retrieved", {'users': user_roles})

            # For assign/revoke operations
            if not target_user_id:
                return self._error_response("Target user ID is required")

            user = self.db_service.users.get(target_user_id)
            if not user:
                return self._error_response(f"User not found: {target_user_id}")

            if action == 'assign':
                role = data.get('role')
                if not role:
                    return self._error_response("Role is required for assignment")

                return self._assign_role_to_user(user, role)

            elif action == 'revoke':
                # For simplified role system, revoke means setting to default role
                return self._assign_role_to_user(user, UserRole.VIEWER.value)

        except Exception as e:
            error_msg = f"Role management failed: {e}"
            self.logger.error(error_msg)
            return self._error_response(f"Failed to manage roles: {str(e)}")

    def _assign_role_to_user(self, user: User, role: str) -> Dict[str, Any]:
        """Assign a role to a user"""
        try:
            # Validate role
            try:
                new_role = UserRole(role.lower())
            except ValueError:
                return self._error_response(f"Invalid role: {role}")

            old_role = user.role.value if user.role else 'none'

            # Update user role
            user.role = new_role
            user.updated_at = DateTimeHelper.now()

            # Save to database
            if self.db_service:
                self.db_service.users.update(user.id, user)

            # Emit role change event
            if self.events:
                self.events.emit('role_assigned', self.agent_id, {
                    'user_id': user.id,
                    'username': user.username,
                    'old_role': old_role,
                    'new_role': new_role.value,
                    'assigned_by': 'user_manager_agent'
                })

            self.logger.info(f"Role '{new_role.value}' assigned to user '{user.username}'")

            return self._success_response(f"Role '{new_role.value}' assigned successfully", {
                'user_id': user.id,
                'username': user.username,
                'old_role': old_role,
                'new_role': new_role.value,
                'permissions': self._get_user_permissions(new_role),
                'assigned_at': DateTimeHelper.to_iso_string(user.updated_at)
            })

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Role assignment error: {e}")
            raise Exception(f"Failed to assign role: {str(e)}")

    def _list_user_roles(self, user: User) -> Dict[str, Any]:
        """List role information for a user (single role system)"""
        return {
            'username': user.username,
            'role': user.role.value if user.role else 'none',
            'status': user.status.value if user.status else 'unknown',
            'last_login': DateTimeHelper.to_iso_string(user.last_login) if user.last_login else None,
            'created_at': DateTimeHelper.to_iso_string(user.created_at),
            'updated_at': DateTimeHelper.to_iso_string(user.updated_at)
        }

    def _get_role_capabilities(self, role: str) -> Dict[str, Any]:
        """Get capabilities for a specific role"""
        if not role:
            raise ValidationError("Role is required")

        # Define role capabilities mapping
        role_capabilities = {
            UserRole.ADMIN.value: [
                'manage_users', 'system_admin', 'view_all_projects', 'delete_projects',
                'manage_system_settings', 'view_analytics', 'manage_permissions'
            ],
            UserRole.PROJECT_MANAGER.value: [
                'create_project', 'manage_team', 'view_analytics', 'manage_timeline',
                'allocate_resources', 'manage_risks', 'approve_deliverables'
            ],
            UserRole.DEVELOPER.value: [
                'write_code', 'run_tests', 'submit_code_reviews', 'implement_features',
                'fix_bugs', 'create_documentation', 'deploy_code'
            ],
            UserRole.DESIGNER.value: [
                'create_designs', 'user_research', 'design_systems', 'prototyping',
                'accessibility_review', 'visual_design', 'ux_research'
            ],
            UserRole.TESTER.value: [
                'create_tests', 'run_test_suites', 'report_bugs', 'validate_requirements',
                'performance_testing', 'security_testing', 'test_automation'
            ],
            UserRole.STAKEHOLDER.value: [
                'view_progress', 'provide_feedback', 'approve_requirements',
                'review_deliverables', 'request_changes', 'view_reports'
            ],
            UserRole.VIEWER.value: [
                'view_projects', 'view_progress', 'read_documentation'
            ]
        }

        return {
            'role': role,
            'capabilities': role_capabilities.get(role, []),
            'description': self._get_role_description(role)
        }

    def _get_role_description(self, role: str) -> str:
        """Get description for a role"""
        descriptions = {
            UserRole.ADMIN.value: "Full system administration and user management",
            UserRole.PROJECT_MANAGER.value: "Project planning, team coordination, and delivery management",
            UserRole.DEVELOPER.value: "Software development, coding, and technical implementation",
            UserRole.DESIGNER.value: "User experience design, visual design, and prototyping",
            UserRole.TESTER.value: "Quality assurance, testing, and bug reporting",
            UserRole.STAKEHOLDER.value: "Business oversight, requirements approval, and feedback",
            UserRole.VIEWER.value: "Read-only access to projects and documentation"
        }
        return descriptions.get(role, "Unknown role")

    def _get_user_permissions(self, role: UserRole) -> List[str]:
        """Get permissions for a specific role"""
        role_capabilities = self._get_role_capabilities(role.value)
        return role_capabilities['capabilities']

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
                    'full_name': user.full_name,
                    'role': user.role.value if user.role else 'none',
                    'status': user.status.value if user.status else 'unknown',
                    'last_login': DateTimeHelper.to_iso_string(user.last_login) if user.last_login else None,
                    'created_at': DateTimeHelper.to_iso_string(user.created_at),
                    'projects_created': user.projects_created,
                    'sessions_completed': user.sessions_completed
                }
                user_list.append(user_data)

            return self._success_response("Users retrieved successfully", {
                'users': user_list,
                'total_count': total_count,
                'offset': offset,
                'limit': limit,
                'filters_applied': {
                    'role': role_filter,
                    'status': status_filter
                }
            })

        except Exception as e:
            error_msg = f"Failed to list users: {e}"
            self.logger.error(error_msg)
            return self._error_response(error_msg)

    @log_agent_action
    def _get_user_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a specific user"""
        try:
            user_id = data.get('user_id')
            username = data.get('username')

            if not user_id and not username:
                return self._error_response("Either user_id or username is required")

            if not self.db_service:
                return self._error_response("Database service not available")

            # Get user
            if user_id:
                user = self.db_service.users.get(user_id)
            else:
                user = self.db_service.users.get_by_username(username)

            if not user:
                identifier = user_id or username
                return self._error_response(f"User not found: {identifier}")

            # Compile comprehensive user information
            user_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role.value if user.role else 'none',
                'status': user.status.value if user.status else 'unknown',
                'bio': user.bio,
                'skills': user.skills,
                'avatar_url': user.avatar_url,
                'created_at': DateTimeHelper.to_iso_string(user.created_at),
                'updated_at': DateTimeHelper.to_iso_string(user.updated_at),
                'last_login': DateTimeHelper.to_iso_string(user.last_login) if user.last_login else None,
                'is_locked': user.is_locked,
                'login_attempts': user.login_attempts,
                'statistics': {
                    'projects_created': user.projects_created,
                    'sessions_completed': user.sessions_completed,
                    'code_generated_lines': user.code_generated_lines
                },
                'permissions': self._get_user_permissions(user.role) if user.role else [],
                'role_info': self._get_role_capabilities(user.role.value) if user.role else {}
            }

            return self._success_response("User information retrieved", user_info)

        except Exception as e:
            error_msg = f"Failed to get user info: {e}"
            self.logger.error(error_msg)
            return self._error_response(error_msg)

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

            if user.status == UserStatus.INACTIVE:
                return self._success_response("User is already inactive", {
                    'user_id': user_id,
                    'username': user.username,
                    'status': 'already_inactive'
                })

            # Update user status
            user.status = UserStatus.INACTIVE
            user.updated_at = DateTimeHelper.now()

            # Save changes
            self.db_service.users.update(user_id, user)

            # Emit deactivation event
            if self.events:
                self.events.emit('user_deactivated', self.agent_id, {
                    'user_id': user_id,
                    'username': user.username,
                    'deactivated_by': 'user_manager_agent'
                })

            self.logger.info(f"User '{user.username}' deactivated successfully")

            return self._success_response("User deactivated successfully", {
                'user_id': user_id,
                'username': user.username,
                'previous_status': UserStatus.ACTIVE.value,
                'new_status': UserStatus.INACTIVE.value,
                'deactivated_at': DateTimeHelper.to_iso_string(user.updated_at)
            })

        except Exception as e:
            error_msg = f"User deactivation failed: {e}"
            self.logger.error(error_msg)
            return self._error_response(error_msg)

    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check for UserManagerAgent"""
        health = super().health_check()

        try:
            # Check database connectivity
            if self.db_service:
                # Try to count users
                users_count = len(self.db_service.users.list()) if hasattr(self.db_service, 'users') else 0
                health['database_check'] = {
                    'status': 'healthy',
                    'users_in_database': users_count
                }
            else:
                health['database_check'] = {
                    'status': 'unavailable',
                    'users_in_database': 0
                }

            # Check available roles
            health['role_system'] = {
                'available_roles': [role.value for role in UserRole],
                'role_count': len(UserRole)
            }

        except Exception as e:
            health['status'] = 'degraded'
            health['error'] = f"Health check failed: {e}"

        return health
