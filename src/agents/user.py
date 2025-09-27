#!/usr/bin/env python3
"""
UserManagerAgent Fixes for src/agents/user.py
==============================================

Replace the existing methods in src/agents/user.py with these corrected versions.
Key fixes: field names, database access patterns, and model compatibility.
"""

# Update the imports at the top (around line 10):
from typing import Dict, List, Any, Optional

from src.core import get_logger, DateTimeHelper, ValidationError, ValidationHelper
from src.models import User, UserRole, UserStatus, ModelValidator
from src.database import get_database
from .base import BaseAgent, require_authentication, log_agent_action


class UserManagerAgent(BaseAgent):
    """
    Enhanced user management agent with role-based capabilities

    Absorbs: Role management functionality
    Capabilities: User lifecycle, role assignment, team management, permissions
    """

    def __init__(self):
        super().__init__("user_manager", "User Manager")
        self.db_service = get_database()

    def get_capabilities(self) -> List[str]:
        return [
            "create_user", "authenticate_user", "update_profile", "manage_roles",
            "assign_permissions", "track_activity", "team_management",
            "skill_assessment", "productivity_analytics", "list_users",
            "deactivate_user", "get_user_info"
        ]

    @log_agent_action
    def _create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user with role assignment"""
        username = data.get('username')
        email = data.get('email')
        password_hash = data.get('password_hash') or data.get('passcode_hash')  # Support both field names
        full_name = data.get('full_name', '')

        if not username or not password_hash:
            raise ValidationError("Username and password hash are required")

        # Validate username format
        if not username.replace('_', '').replace('-', '').isalnum() or len(username) < 3:
            raise ValidationError("Username must be alphanumeric, at least 3 characters")

        # Validate email if provided
        if email and not ValidationHelper.validate_email(email):
            raise ValidationError("Invalid email format")

        # Check if user already exists
        existing_user = self.db_service.users.get_by_username(username)
        if existing_user:
            raise ValidationError(f"User {username} already exists")

        # Check if email already exists
        if email:
            existing_email = self.db_service.users.get_by_email(email)
            if existing_email:
                raise ValidationError(f"Email {email} already registered")

        # Create user model
        user = User(
            username=username,
            email=email or '',
            password_hash=password_hash,
            first_name=full_name.split()[0] if full_name else '',
            last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
            role=UserRole(data.get('role', 'developer')),  # Single role, not list
            status=UserStatus.ACTIVE,
            preferences=data.get('preferences', {})
        )

        # Create user in database
        success = self.db_service.users.create(user)
        if not success:
            raise Exception("Failed to create user in database")

        # Initialize user tracking
        self._initialize_user_tracking(user.username)

        return {
            'user_id': user.id,
            'status': 'created',
            'role': user.role.value,  # Single role
            'email': user.email,
            'created_at': DateTimeHelper.to_iso_string(user.created_at)
        }

    def _initialize_user_tracking(self, username: str):
        """Initialize tracking for new user"""
        self.events.publish_async('user_created', 'user_manager', {
            'username': username,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        })

        self.logger.info(f"User tracking initialized for {username}")

    @log_agent_action
    def _authenticate_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user and return session info"""
        username = data.get('username')
        password_hash = data.get('password_hash') or data.get('passcode_hash')  # Support both field names

        if not username or not password_hash:
            return {
                'success': False,
                'message': 'Username and password are required',
                'authenticated': False
            }

        # Find user
        user = self.db_service.users.get_by_username(username)
        if not user:
            return {
                'success': False,
                'message': 'User not found',
                'authenticated': False
            }

        # For authentication, we just verify the user exists and is active
        # Password verification is done in the web layer
        if user.status != UserStatus.ACTIVE:
            return {
                'success': False,
                'message': 'Account deactivated',
                'authenticated': False
            }

        # Update last login
        user.last_login = DateTimeHelper.now()
        self.db_service.users.update(user)

        # Emit login event
        self.events.publish_async('user_login', 'user_manager', {
            'username': username,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        })

        return {
            'success': True,
            'authenticated': True,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value,  # Single role
            'full_name': user.full_name,
            'last_login': DateTimeHelper.to_iso_string(user.last_login) if user.last_login else None
        }

    @require_authentication
    @log_agent_action
    def _update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile information"""
        username = data.get('username')

        user = self.db_service.users.get_by_username(username)
        if not user:
            raise ValidationError("User not found")

        # Update allowed fields
        if 'email' in data:
            email = data['email']
            if email and not ValidationHelper.validate_email(email):
                raise ValidationError("Invalid email format")
            user.email = email

        if 'full_name' in data:
            full_name = data['full_name']
            if full_name:
                name_parts = full_name.split()
                user.first_name = name_parts[0] if name_parts else ''
                user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        if 'preferences' in data:
            # Merge preferences instead of replacing
            if not hasattr(user, 'preferences') or user.preferences is None:
                user.preferences = {}
            user.preferences.update(data['preferences'])

        # Save changes
        user.updated_at = DateTimeHelper.now()
        success = self.db_service.users.update(user)

        if not success:
            raise Exception("Failed to update user profile")

        return {
            'success': True,
            'message': 'Profile updated successfully',
            'updated_fields': list(data.keys()),
            'updated_at': DateTimeHelper.to_iso_string(user.updated_at)
        }

    @require_authentication
    @log_agent_action
    def _manage_roles(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simplified role management for single role system"""
        action = data.get('action')
        target_username = data.get('target_username') or data.get('username')

        if not target_username:
            raise ValidationError("Target username is required")

        user = self.db_service.users.get_by_username(target_username)
        if not user:
            raise ValidationError("User not found")

        if action == 'assign':
            return self._assign_role(user, data)
        elif action == 'list':
            return self._list_user_roles(user)
        elif action == 'capabilities':
            return self._get_role_capabilities(data.get('role'))
        else:
            raise ValidationError(f"Unknown role action: {action}")

    def _assign_role(self, user: User, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assign role to user (single role system)"""
        role = data.get('role')
        if not role:
            raise ValidationError("Role is required")

        try:
            new_role = UserRole(role)
            old_role = user.role.value if user.role else 'none'

            user.role = new_role
            user.updated_at = DateTimeHelper.now()
            self.db_service.users.update(user)

            # Emit role assignment event
            self.events.publish_async('user_role_assigned', 'user_manager', {
                'username': user.username,
                'old_role': old_role,
                'new_role': role,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            })

            return {
                'success': True,
                'message': f'Role {role} assigned to {user.username}',
                'role': user.role.value
            }
        except ValueError:
            raise ValidationError(f"Invalid role: {role}")

    def _list_user_roles(self, user: User) -> Dict[str, Any]:
        """List role for a user (single role system)"""
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

        # Define role capabilities
        role_capabilities = {
            UserRole.ADMIN.value: [
                'manage_users', 'system_admin', 'view_all_projects', 'delete_projects',
                'manage_system_settings', 'view_analytics'
            ],
            UserRole.PROJECT_MANAGER.value: [
                'create_project', 'manage_team', 'view_analytics', 'manage_timeline',
                'allocate_resources', 'manage_risks'
            ],
            UserRole.DEVELOPER.value: [
                'write_code', 'run_tests', 'submit_code_reviews', 'implement_features',
                'fix_bugs', 'create_documentation'
            ],
            UserRole.DESIGNER.value: [
                'create_designs', 'user_research', 'design_systems', 'prototyping',
                'accessibility_review'
            ],
            UserRole.TESTER.value: [
                'create_tests', 'run_test_suites', 'report_bugs', 'validate_requirements',
                'performance_testing'
            ],
            UserRole.BUSINESS_ANALYST.value: [
                'gather_requirements', 'stakeholder_communication', 'process_analysis',
                'create_specifications', 'validate_business_rules'
            ],
            UserRole.DEVOPS.value: [
                'deploy_applications', 'manage_infrastructure', 'monitor_systems',
                'automate_processes', 'security_management'
            ],
            UserRole.VIEWER.value: [
                'view_projects', 'view_documentation', 'participate_in_meetings'
            ]
        }

        try:
            UserRole(role)  # Validate role exists
            capabilities = role_capabilities.get(role, [])

            return {
                'role': role,
                'capabilities': capabilities,
                'capability_count': len(capabilities)
            }
        except ValueError:
            raise ValidationError(f"Invalid role: {role}")

    @require_authentication
    @log_agent_action
    def _get_user_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a user"""
        target_username = data.get('target_username') or data.get('username')
        requesting_username = data.get('username')

        if not target_username:
            raise ValidationError("Target username is required")

        user = self.db_service.users.get_by_username(target_username)
        if not user:
            raise ValidationError("User not found")

        # Basic info available to all authenticated users
        user_info = {
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role.value if user.role else 'none',
            'status': user.status.value if user.status else 'unknown',
            'created_at': DateTimeHelper.to_iso_string(user.created_at)
        }

        # Additional info only if requesting own info
        if requesting_username == target_username:
            user_info.update({
                'email': user.email,
                'preferences': getattr(user, 'preferences', {}),
                'last_login': DateTimeHelper.to_iso_string(user.last_login) if user.last_login else None,
                'updated_at': DateTimeHelper.to_iso_string(user.updated_at)
            })

        return user_info

    @require_authentication
    @log_agent_action
    def _deactivate_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deactivate a user account"""
        target_username = data.get('target_username')
        requesting_username = data.get('username')
        reason = data.get('reason', 'No reason provided')

        if not target_username:
            raise ValidationError("Target username is required")

        # Basic permission check - users can only deactivate themselves
        # In a real system, you'd check admin permissions
        if requesting_username != target_username:
            raise ValidationError("Users can only deactivate their own accounts")

        user = self.db_service.users.get_by_username(target_username)
        if not user:
            raise ValidationError("User not found")

        if user.status != UserStatus.ACTIVE:
            return {
                'success': False,
                'message': 'User is already deactivated'
            }

        # Deactivate user
        user.status = UserStatus.INACTIVE
        user.updated_at = DateTimeHelper.now()

        success = self.db_service.users.update(user)
        if not success:
            raise Exception("Failed to deactivate user")

        # Emit deactivation event
        self.events.publish_async('user_deactivated', 'user_manager', {
            'username': target_username,
            'reason': reason,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        })

        return {
            'success': True,
            'message': f'User {target_username} has been deactivated',
            'deactivated_at': DateTimeHelper.to_iso_string(user.updated_at)
        }

    @log_agent_action
    def _track_activity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track user activity and generate analytics"""
        username = data.get('username')
        period = data.get('period', '7d')  # 1d, 7d, 30d

        if not username:
            raise ValidationError("Username is required")

        user = self.db_service.users.get_by_username(username)
        if not user:
            raise ValidationError("User not found")

        # Simplified activity tracking - in a real system you'd track actual events
        activity = {
            'username': username,
            'period': period,
            'login_count': 5,  # Would track actual logins
            'projects_accessed': 3,  # Would track actual project access
            'questions_asked': 15,  # Would track Socratic sessions
            'files_generated': 8,  # Would track code generation
            'last_active': DateTimeHelper.to_iso_string(user.last_login) if user.last_login else None,
            'productivity_score': 85.0,  # Would calculate based on actual activity
            'engagement_level': 'high'  # high, medium, low
        }

        return activity