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
from functools import wraps

try:
    from src.core import get_logger, DateTimeHelper, ValidationError, ValidationHelper, get_event_bus
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


class UserManagerAgent(BaseAgent):
    """
    Enhanced user management agent with role-based capabilities

    Absorbs: Role management functionality from legacy system
    Capabilities: Complete user lifecycle, authentication, team management
    """

    def __init__(self):
        """Initialize UserManagerAgent with corrected patterns"""
        super().__init__("user_manager", "User Manager")

        # Database service initialization (corrected pattern)
        self.db_service = get_database() if CORE_AVAILABLE else None

        # Event bus for user-related events
        self.events = get_event_bus() if CORE_AVAILABLE else None

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
                self.logger.warning("User creation failed: Username and password hash are required")
                raise ValidationError("Username and password hash are required")

            # Validate username format
            if not username.replace('_', '').replace('-', '').isalnum() or len(username) < 3:
                self.logger.warning(f"User creation failed: Invalid username format: {username}")
                raise ValidationError(
                    "Username must be alphanumeric with optional underscores/hyphens, at least 3 characters")

            # Validate email if provided
            if email and not ValidationHelper.validate_email(email):
                self.logger.warning(f"User creation failed: Invalid email format: {email}")
                raise ValidationError("Invalid email format")

            # Check if user already exists
            existing_user = self.db_service.users.get_by_username(username)
            if existing_user:
                self.logger.warning(f"User creation failed: Username {username} already exists")
                raise ValidationError(f"User {username} already exists")

            # Check if email already exists
            if email:
                existing_email = self.db_service.users.get_by_email(email)
                if existing_email:
                    self.logger.warning(f"User creation failed: Email {email} already registered")
                    raise ValidationError(f"Email {email} already registered")

            # Create user model with corrected field names
            name_parts = full_name.split() if full_name else []
            user = User(
                username=username,
                email=email or '',
                password_hash=password_hash,
                first_name=name_parts[0] if name_parts else '',
                last_name=' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
                role=UserRole(data.get('role', 'developer')),  # Single role system
                status=UserStatus.ACTIVE,
                preferences=data.get('preferences', {}),
                created_at=DateTimeHelper.now(),  # Rule #7: Use DateTimeHelper
                updated_at=DateTimeHelper.now()
            )

            # Save user to database
            success = self.db_service.users.create(user)
            if not success:
                self.logger.error(f"Database operation failed for user creation: {username}")
                raise Exception("Failed to create user in database")

            # Initialize user tracking and emit events
            self._initialize_user_tracking(user.username)

            # Log successful creation
            self.logger.info(f"User created successfully: {username} with role {user.role.value}")

            return {
                'success': True,
                'user_id': user.id,
                'status': 'created',
                'username': user.username,
                'role': user.role.value,
                'email': user.email,
                'created_at': DateTimeHelper.to_iso_string(user.created_at)
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating user {username or 'unknown'}: {e}")
            return self._error_response(f"Failed to create user: {str(e)}")

    def _initialize_user_tracking(self, username: str):
        """Initialize tracking and analytics for new user"""
        try:
            if self.events:
                self.events.emit('user_created', 'user_manager', {
                    'username': username,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                })

            self.logger.info(f"User tracking initialized for {username}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize user tracking for {username}: {e}")

    @log_agent_action
    def _authenticate_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user and return session information"""
        username = data.get('username')  # Initialize username early

        try:
            password_hash = data.get('password_hash') or data.get('passcode_hash')  # Support both field names

            if not username or not password_hash:
                self.logger.warning("Authentication failed: Username and password are required")
                return {
                    'success': False,
                    'message': 'Username and password are required',
                    'authenticated': False
                }

            # Find user in database
            user = self.db_service.users.get_by_username(username)
            if not user:
                self.logger.warning(f"Authentication failed: User {username} not found")
                return {
                    'success': False,
                    'message': 'User not found',
                    'authenticated': False
                }

            # Check user status
            if user.status != UserStatus.ACTIVE:
                self.logger.warning(f"Authentication failed: User {username} account is not active")
                return {
                    'success': False,
                    'message': 'Account deactivated',
                    'authenticated': False
                }

            # Password verification is handled by the web layer
            # Update last login timestamp
            user.last_login = DateTimeHelper.now()  # Rule #7: Use DateTimeHelper
            user.updated_at = DateTimeHelper.now()
            self.db_service.users.update(user)

            # Emit login event
            if self.events:
                self.events.emit('user_login', 'user_manager', {
                    'username': username,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                })

            self.logger.info(f"User authenticated successfully: {username}")

            return {
                'success': True,
                'authenticated': True,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.value,
                'full_name': user.full_name,
                'last_login': DateTimeHelper.to_iso_string(user.last_login) if user.last_login else None,
                'preferences': getattr(user, 'preferences', {})
            }

        except Exception as e:
            self.logger.error(f"Authentication error for user {username or 'unknown'}: {e}")
            return {
                'success': False,
                'message': 'Authentication error occurred',
                'authenticated': False
            }

    @require_authentication
    @log_agent_action
    def _update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile information with validation"""
        username = data.get('username')  # Initialize early

        try:
            user = self.db_service.users.get_by_username(username)
            if not user:
                self.logger.warning(f"Profile update failed: User {username} not found")
                raise ValidationError("User not found")

            updated_fields = []

            # Update email if provided
            if 'email' in data:
                email = data['email']
                if email and not ValidationHelper.validate_email(email):
                    self.logger.warning(f"Profile update failed: Invalid email format: {email}")
                    raise ValidationError("Invalid email format")

                # Check if email is already taken by another user
                if email != user.email:
                    existing_email = self.db_service.users.get_by_email(email)
                    if existing_email and existing_email.username != username:
                        self.logger.warning(f"Profile update failed: Email {email} already taken")
                        raise ValidationError("Email already taken by another user")

                user.email = email
                updated_fields.append('email')

            # Update full name if provided
            if 'full_name' in data:
                full_name = data['full_name']
                if full_name:
                    name_parts = full_name.split()
                    user.first_name = name_parts[0] if name_parts else ''
                    user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                    updated_fields.extend(['first_name', 'last_name'])

            # Update preferences if provided
            if 'preferences' in data:
                # Merge preferences instead of replacing
                if not hasattr(user, 'preferences') or user.preferences is None:
                    user.preferences = {}
                user.preferences.update(data['preferences'])
                updated_fields.append('preferences')

            # Update other allowed fields
            allowed_fields = ['first_name', 'last_name']
            for field in allowed_fields:
                if field in data:
                    setattr(user, field, data[field])
                    updated_fields.append(field)

            # Update timestamp
            user.updated_at = DateTimeHelper.now()  # Rule #7: Use DateTimeHelper

            # Save changes to database
            success = self.db_service.users.update(user)
            if not success:
                self.logger.error(f"Database update failed for user profile: {username}")
                raise Exception("Failed to update user profile")

            self.logger.info(f"Profile updated successfully for user: {username}, fields: {updated_fields}")

            return {
                'success': True,
                'message': 'Profile updated successfully',
                'username': username,
                'updated_fields': updated_fields,
                'updated_at': DateTimeHelper.to_iso_string(user.updated_at)
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error updating profile for {username or 'unknown'}: {e}")
            return self._error_response(f"Failed to update profile: {str(e)}")

    @require_authentication
    @log_agent_action
    def _manage_roles(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage user roles with proper validation"""
        target_username = data.get('target_username') or data.get('username')  # Initialize early

        try:
            action = data.get('action')

            if not target_username:
                self.logger.warning("Role management failed: Target username is required")
                raise ValidationError("Target username is required")

            user = self.db_service.users.get_by_username(target_username)
            if not user:
                self.logger.warning(f"Role management failed: User {target_username} not found")
                raise ValidationError("User not found")

            if action == 'assign':
                return self._assign_role(user, data)
            elif action == 'list':
                return self._list_user_roles(user)
            elif action == 'capabilities':
                return self._get_role_capabilities(data.get('role'))
            else:
                self.logger.warning(f"Role management failed: Unknown action: {action}")
                raise ValidationError(f"Unknown role action: {action}")

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Role management error for {target_username or 'unknown'}: {e}")
            return self._error_response(f"Role management failed: {str(e)}")

    def _assign_role(self, user: User, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assign role to user (single role system)"""
        try:
            role = data.get('role')
            if not role:
                raise ValidationError("Role is required")

            try:
                new_role = UserRole(role)
                old_role = user.role.value if user.role else 'none'

                user.role = new_role
                user.updated_at = DateTimeHelper.now()  # Rule #7: Use DateTimeHelper

                success = self.db_service.users.update(user)
                if not success:
                    raise Exception("Failed to update user role in database")

                # Emit role assignment event
                if self.events:
                    self.events.emit('user_role_assigned', 'user_manager', {
                        'username': user.username,
                        'old_role': old_role,
                        'new_role': role,
                        'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                    })

                self.logger.info(f"Role {role} assigned to user {user.username} (was {old_role})")

                return {
                    'success': True,
                    'message': f'Role {role} assigned to {user.username}',
                    'username': user.username,
                    'old_role': old_role,
                    'new_role': user.role.value
                }
            except ValueError:
                self.logger.warning(f"Invalid role assignment attempted: {role}")
                raise ValidationError(f"Invalid role: {role}")

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
            UserRole.BUSINESS_ANALYST.value: [
                'gather_requirements', 'stakeholder_communication', 'process_analysis',
                'create_specifications', 'validate_business_rules', 'risk_analysis'
            ],
            UserRole.DEVOPS.value: [
                'deploy_applications', 'manage_infrastructure', 'monitor_systems',
                'automate_processes', 'security_management', 'performance_optimization'
            ],
            UserRole.VIEWER.value: [
                'view_projects', 'view_documentation', 'participate_in_meetings',
                'provide_feedback', 'view_reports'
            ]
        }

        try:
            UserRole(role)  # Validate role exists
            capabilities = role_capabilities.get(role, [])

            return {
                'success': True,
                'role': role,
                'capabilities': capabilities,
                'capability_count': len(capabilities)
            }
        except ValueError:
            self.logger.warning(f"Invalid role capabilities request: {role}")
            raise ValidationError(f"Invalid role: {role}")

    @require_authentication
    @log_agent_action
    def _get_user_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a user with privacy controls"""
        target_username = data.get('target_username') or data.get('username')  # Initialize early
        requesting_username = data.get('username')  # Initialize early

        try:
            if not target_username:
                raise ValidationError("Target username is required")

            user = self.db_service.users.get_by_username(target_username)
            if not user:
                self.logger.warning(f"User info request failed: User {target_username} not found")
                raise ValidationError("User not found")

            # Basic info available to all authenticated users
            user_info = {
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role.value if user.role else 'none',
                'status': user.status.value if user.status else 'unknown',
                'created_at': DateTimeHelper.to_iso_string(user.created_at)
            }

            # Additional sensitive info only if requesting own info
            if requesting_username == target_username:
                user_info.update({
                    'email': user.email,
                    'preferences': getattr(user, 'preferences', {}),
                    'last_login': DateTimeHelper.to_iso_string(user.last_login) if user.last_login else None,
                    'updated_at': DateTimeHelper.to_iso_string(user.updated_at)
                })
                self.logger.debug(f"Full user info provided for own account: {target_username}")
            else:
                self.logger.debug(
                    f"Basic user info provided for: {target_username} (requested by {requesting_username})")

            return {
                'success': True,
                **user_info
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting user info for {target_username or 'unknown'}: {e}")
            return self._error_response(f"Failed to get user info: {str(e)}")

    @require_authentication
    @log_agent_action
    def _deactivate_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deactivate a user account with proper authorization"""
        target_username = data.get('target_username')  # Initialize early
        requesting_username = data.get('username')  # Initialize early

        try:
            reason = data.get('reason', 'No reason provided')

            if not target_username:
                raise ValidationError("Target username is required")

            # Basic permission check - users can only deactivate themselves
            # In production, you'd implement proper admin role checking
            if requesting_username != target_username:
                self.logger.warning(
                    f"Unauthorized deactivation attempt: {requesting_username} tried to deactivate {target_username}")
                raise ValidationError("You can only deactivate your own account")

            user = self.db_service.users.get_by_username(target_username)
            if not user:
                self.logger.warning(f"Deactivation failed: User {target_username} not found")
                raise ValidationError("User not found")

            if user.status == UserStatus.INACTIVE:
                self.logger.info(f"User {target_username} already deactivated")
                return {
                    'success': True,
                    'message': f'User {target_username} is already deactivated',
                    'username': target_username,
                    'status': 'already_inactive'
                }

            # Deactivate user
            user.status = UserStatus.INACTIVE
            user.updated_at = DateTimeHelper.now()  # Rule #7: Use DateTimeHelper

            success = self.db_service.users.update(user)
            if not success:
                raise Exception("Failed to deactivate user in database")

            # Emit deactivation event
            if self.events:
                self.events.emit('user_deactivated', 'user_manager', {
                    'username': target_username,
                    'reason': reason,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                    'deactivated_by': requesting_username
                })

            self.logger.info(f"User deactivated: {target_username} by {requesting_username}, reason: {reason}")

            return {
                'success': True,
                'message': f'User {target_username} deactivated successfully',
                'username': target_username,
                'status': 'deactivated',
                'reason': reason,
                'deactivated_at': DateTimeHelper.to_iso_string(user.updated_at)
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error deactivating user {target_username or 'unknown'}: {e}")
            return self._error_response(f"Failed to deactivate user: {str(e)}")

    @require_authentication
    @log_agent_action
    def _list_users(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """List users with filtering and pagination"""
        try:
            # Get filtering parameters
            status_filter = data.get('status')
            role_filter = data.get('role')
            limit = data.get('limit', 50)
            offset = data.get('offset', 0)

            # Get users from database
            users = self.db_service.users.get_all()

            # Apply filters
            if status_filter:
                try:
                    status_enum = UserStatus(status_filter)
                    users = [u for u in users if u.status == status_enum]
                except ValueError:
                    self.logger.warning(f"Invalid status filter: {status_filter}")

            if role_filter:
                try:
                    role_enum = UserRole(role_filter)
                    users = [u for u in users if u.role == role_enum]
                except ValueError:
                    self.logger.warning(f"Invalid role filter: {role_filter}")

            # Apply pagination
            total_count = len(users)
            users = users[offset:offset + limit]

            # Format user list (basic info only)
            user_list = []
            for user in users:
                user_list.append({
                    'username': user.username,
                    'full_name': user.full_name,
                    'email': user.email,
                    'role': user.role.value if user.role else 'none',
                    'status': user.status.value if user.status else 'unknown',
                    'created_at': DateTimeHelper.to_iso_string(user.created_at),
                    'last_login': DateTimeHelper.to_iso_string(user.last_login) if user.last_login else None
                })

            self.logger.info(f"User list retrieved: {len(user_list)} users (total: {total_count})")

            return {
                'success': True,
                'users': user_list,
                'total_count': total_count,
                'returned_count': len(user_list),
                'offset': offset,
                'limit': limit
            }

        except Exception as e:
            self.logger.error(f"Error listing users: {e}")
            return self._error_response(f"Failed to list users: {str(e)}")

    @require_authentication
    @log_agent_action
    def _check_permissions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if user has specific permissions"""
        username = data.get('username')  # Initialize early

        try:
            permission = data.get('permission')
            context = data.get('context', {})

            if not permission:
                raise ValidationError("Permission is required")

            user = self.db_service.users.get_by_username(username)
            if not user:
                raise ValidationError("User not found")

            # Get role capabilities
            role_info = self._get_role_capabilities(user.role.value)
            capabilities = role_info.get('capabilities', [])

            # Check if user has the required permission
            has_permission = permission in capabilities

            # Additional context-based checks could be implemented here
            # For example, project-specific permissions

            self.logger.debug(f"Permission check for {username}: {permission} = {has_permission}")

            return {
                'success': True,
                'username': username,
                'permission': permission,
                'has_permission': has_permission,
                'user_role': user.role.value,
                'context': context
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error checking permissions for {username or 'unknown'}: {e}")
            return self._error_response(f"Failed to check permissions: {str(e)}")

    def _error_response(self, error_message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
        """Create standardized error response"""
        response = {
            'success': False,
            'error': error_message,
            'agent_id': self.agent_id,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

        if error_code:
            response['error_code'] = error_code

        return response
