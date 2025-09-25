#!/usr/bin/env python3
"""
Socratic RAG Enhanced - User Management Agent
==============================================

User management agent with role-based capabilities.

Absorbs: Role management functionality
Capabilities: User lifecycle, role assignment, team management, permissions
"""

from typing import Dict, List, Any, Optional

from src.core import get_logger, DateTimeHelper, ValidationError, ValidationHelper
from src.models import User, UserRole, ModelValidator
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
        passcode_hash = data.get('passcode_hash')

        if not username or not passcode_hash:
            raise ValidationError("Username and passcode hash are required")

        # Validate username format
        if not username.replace('_', '').replace('-', '').isalnum() or len(username) < 3:
            raise ValidationError("Username must be alphanumeric, at least 3 characters")

        # Validate email if provided
        if email and not ValidationHelper.validate_email(email):
            raise ValidationError("Invalid email format")

        # Check if user already exists
        if self.db.users.exists(username):
            raise ValidationError(f"User {username} already exists")

        # Create user model
        user = User(
            username=username,
            email=email,
            full_name=data.get('full_name', ''),
            passcode_hash=passcode_hash,
            roles=[UserRole(data.get('role', 'developer'))],
            preferences=data.get('preferences', {})
        )

        # Create user in database
        success = self.db.users.create(user)
        if not success:
            raise Exception("Failed to create user in database")

        # Initialize user tracking
        self._initialize_user_tracking(user.username)

        return {
            'user_id': user.username,
            'status': 'created',
            'roles': [role.value for role in user.roles],
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
        passcode_hash = data.get('passcode_hash')

        if not username or not passcode_hash:
            return {
                'success': False,
                'message': 'Username and passcode are required',
                'authenticated': False
            }

        # Find user
        user = self.db.users.get_by_username(username)
        if not user:
            return {
                'success': False,
                'message': 'User not found',
                'authenticated': False
            }

        # Verify passcode
        if user.passcode_hash != passcode_hash:
            return {
                'success': False,
                'message': 'Invalid passcode',
                'authenticated': False
            }

        # Check if active
        if not user.is_active:
            return {
                'success': False,
                'message': 'Account deactivated',
                'authenticated': False
            }

        # Update last login
        user.last_login = DateTimeHelper.now()
        self.db.users.update(user)

        # Emit login event
        self.events.publish_async('user_login', 'user_manager', {
            'username': username,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        })

        return {
            'success': True,
            'authenticated': True,
            'user_id': user.username,
            'username': user.username,
            'email': user.email,
            'roles': [role.value for role in user.roles],
            'full_name': user.full_name,
            'last_login': DateTimeHelper.to_iso_string(user.last_login) if user.last_login else None
        }

    @require_authentication
    @log_agent_action
    def _update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile information"""
        username = data.get('username')

        user = self.db.users.get_by_username(username)
        if not user:
            raise ValidationError("User not found")

        # Update allowed fields
        if 'email' in data:
            email = data['email']
            if email and not ValidationHelper.validate_email(email):
                raise ValidationError("Invalid email format")
            user.email = email

        if 'full_name' in data:
            user.full_name = data['full_name']

        if 'preferences' in data:
            # Merge preferences instead of replacing
            user.preferences.update(data['preferences'])

        # Save changes
        user.updated_at = DateTimeHelper.now()
        success = self.db.users.update(user)

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
        """Comprehensive role management"""
        action = data.get('action')
        target_username = data.get('target_username') or data.get('username')

        if not target_username:
            raise ValidationError("Target username is required")

        user = self.db.users.get_by_username(target_username)
        if not user:
            raise ValidationError("User not found")

        if action == 'assign':
            return self._assign_role(user, data)
        elif action == 'remove':
            return self._remove_role(user, data)
        elif action == 'list':
            return self._list_user_roles(user)
        elif action == 'capabilities':
            return self._get_role_capabilities(data.get('role'))
        else:
            raise ValidationError(f"Unknown role action: {action}")

    def _assign_role(self, user: User, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assign role to user"""
        role = data.get('role')
        if not role:
            raise ValidationError("Role is required")

        try:
            new_role = UserRole(role)
            if new_role not in user.roles:
                user.roles.append(new_role)
                user.updated_at = DateTimeHelper.now()
                self.db.users.update(user)

                # Emit role assignment event
                self.events.publish_async('user_role_assigned', 'user_manager', {
                    'username': user.username,
                    'role': role,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                })

                return {
                    'success': True,
                    'message': f'Role {role} assigned to {user.username}',
                    'roles': [r.value for r in user.roles]
                }
            else:
                return {
                    'success': False,
                    'message': f'User already has role {role}',
                    'roles': [r.value for r in user.roles]
                }
        except ValueError:
            raise ValidationError(f"Invalid role: {role}")

    def _remove_role(self, user: User, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove role from user"""
        role = data.get('role')
        if not role:
            raise ValidationError("Role is required")

        try:
            role_to_remove = UserRole(role)
            if role_to_remove in user.roles:
                # Don't allow removing all roles
                if len(user.roles) <= 1:
                    return {
                        'success': False,
                        'message': 'Cannot remove last role from user',
                        'roles': [r.value for r in user.roles]
                    }

                user.roles.remove(role_to_remove)
                user.updated_at = DateTimeHelper.now()
                self.db.users.update(user)

                return {
                    'success': True,
                    'message': f'Role {role} removed from {user.username}',
                    'roles': [r.value for r in user.roles]
                }
            else:
                return {
                    'success': False,
                    'message': f'User does not have role {role}',
                    'roles': [r.value for r in user.roles]
                }
        except ValueError:
            raise ValidationError(f"Invalid role: {role}")

    def _list_user_roles(self, user: User) -> Dict[str, Any]:
        """List all roles for a user"""
        return {
            'username': user.username,
            'roles': [role.value for role in user.roles],
            'is_active': user.is_active,
            'is_archived': user.is_archived,
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
            UserRole.PROJECT_MANAGER.value: [
                'create_project', 'manage_team', 'view_analytics', 'manage_timeline',
                'allocate_resources', 'manage_risks'
            ],
            UserRole.TECHNICAL_LEAD.value: [
                'review_code', 'approve_architecture', 'make_technical_decisions',
                'mentor_developers', 'design_systems'
            ],
            UserRole.DEVELOPER.value: [
                'write_code', 'run_tests', 'submit_code_reviews', 'implement_features',
                'fix_bugs', 'create_documentation'
            ],
            UserRole.DESIGNER.value: [
                'create_designs', 'user_research', 'design_systems', 'prototyping',
                'accessibility_review'
            ],
            UserRole.QA_TESTER.value: [
                'create_tests', 'run_test_suites', 'report_bugs', 'validate_requirements',
                'performance_testing'
            ],
            UserRole.BUSINESS_ANALYST.value: [
                'gather_requirements', 'stakeholder_communication', 'process_analysis',
                'create_specifications', 'validate_business_rules'
            ],
            UserRole.DEVOPS_ENGINEER.value: [
                'deploy_applications', 'manage_infrastructure', 'monitor_systems',
                'automate_processes', 'security_management'
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

    @log_agent_action
    def _list_users(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """List all users with filtering options"""
        include_archived = data.get('include_archived', False)
        role_filter = data.get('role_filter')

        # Note: This is a simplified implementation since the actual database
        # doesn't have a list_all method. In a real implementation, you'd add this.
        try:
            # For now, return empty list - would need to implement in database layer
            return {
                'users': [],
                'total_count': 0,
                'filters_applied': {
                    'include_archived': include_archived,
                    'role_filter': role_filter
                },
                'message': 'User listing not implemented in database layer'
            }
        except Exception as e:
            self.logger.error(f"Failed to list users: {e}")
            return {
                'users': [],
                'total_count': 0,
                'error': str(e)
            }

    @require_authentication
    @log_agent_action
    def _get_user_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a user"""
        target_username = data.get('target_username') or data.get('username')
        requesting_username = data.get('username')

        if not target_username:
            raise ValidationError("Target username is required")

        user = self.db.users.get_by_username(target_username)
        if not user:
            raise ValidationError("User not found")

        # Basic info available to all authenticated users
        user_info = {
            'username': user.username,
            'full_name': user.full_name,
            'roles': [role.value for role in user.roles],
            'is_active': user.is_active,
            'created_at': DateTimeHelper.to_iso_string(user.created_at)
        }

        # Additional info only if requesting own info
        if requesting_username == target_username:
            user_info.update({
                'email': user.email,
                'preferences': user.preferences,
                'projects': user.projects,
                'last_login': DateTimeHelper.to_iso_string(user.last_login) if user.last_login else None,
                'updated_at': DateTimeHelper.to_iso_string(user.updated_at),
                'is_archived': user.is_archived
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

        user = self.db.users.get_by_username(target_username)
        if not user:
            raise ValidationError("User not found")

        if not user.is_active:
            return {
                'success': False,
                'message': 'User is already deactivated'
            }

        # Deactivate user
        user.is_active = False
        user.updated_at = DateTimeHelper.now()

        success = self.db.users.update(user)
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

        user = self.db.users.get_by_username(username)
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
