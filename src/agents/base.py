#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Base Agent Architecture
==============================================

Base agent class and common utilities for all Socratic RAG agents.
Provides common functionality like Claude API integration, logging, events.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from functools import wraps

# Import core system components
try:
    from src.core import (
        get_logger, get_config, get_event_bus, DatabaseManager,
        DateTimeHelper, ANTHROPIC_AVAILABLE, AgentError
    )
    from src.database import get_database

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False


    def get_logger(name: str):
        import logging
        return logging.getLogger(name)


    def get_config():
        return {}


    def get_event_bus():
        return None


    def get_database():
        return None


    DateTimeHelper = None
    ANTHROPIC_AVAILABLE = False
    AgentError = Exception

# Anthropic client import with fallback
if ANTHROPIC_AVAILABLE:
    try:
        from anthropic import Anthropic
    except ImportError:
        ANTHROPIC_AVAILABLE = False
        Anthropic = None
else:
    Anthropic = None


class BaseAgent(ABC):
    """Base class for all Socratic RAG agents with enterprise capabilities"""

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.config = get_config() if CORE_AVAILABLE else {}
        self.logger = get_logger(f"agent.{agent_id}") if CORE_AVAILABLE else None
        self.db_service = get_database() if CORE_AVAILABLE else None  # Fixed: Use db_service pattern
        self.events = get_event_bus() if CORE_AVAILABLE else None

        # Initialize Claude client if API key available
        self.claude_client = None
        if ANTHROPIC_AVAILABLE and Anthropic and self.config:
            api_key = self.config.get('services.claude.api_key') or self.config.get('claude.api_key')
            if api_key:
                try:
                    self.claude_client = Anthropic(api_key=api_key)
                    if self.logger:
                        self.logger.info(f"Claude client initialized for {self.name}")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Claude client initialization failed: {e}")
            else:
                if self.logger:
                    self.logger.warning("Claude API key not configured")

        if self.logger:
            self.logger.info(f"Agent {self.name} ({self.agent_id}) initialized")

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        pass

    def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent request with error handling"""
        if self.logger:
            self.logger.info(f"Processing {action} request")

        try:
            # Validate input data
            if not self._validate_request(action, data):
                if self.logger:
                    self.logger.warning(f"Invalid request data for action {action}")
                return self._error_response("Invalid request data")

            # Route to appropriate method
            method_name = f"_{action}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)

                if self.logger:
                    self.logger.debug(f"Calling method {method_name}")

                result = method(data)

                # Emit event for successful processing
                self._emit_event('agent_action_completed', {
                    'agent_id': self.agent_id,
                    'action': action,
                    'success': True,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
                })

                if self.logger:
                    self.logger.info(f"Successfully processed {action} request")

                return self._success_response(result)
            else:
                error_msg = f"Unknown action: {action}"
                if self.logger:
                    self.logger.error(error_msg)
                return self._error_response(error_msg)

        except Exception as e:
            error_msg = f"Error processing {action}: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)

            # Emit error event
            self._emit_event('agent_action_failed', {
                'agent_id': self.agent_id,
                'action': action,
                'error': str(e),
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            })

            return self._error_response(error_msg)

    def _validate_request(self, action: str, data: Dict[str, Any]) -> bool:
        """Validate incoming request data"""
        try:
            # Basic validation
            if not isinstance(data, dict):
                if self.logger:
                    self.logger.warning("Request data is not a dictionary")
                return False

            # Check for required fields based on action type
            if action in ['create_project', 'update_project', 'analyze_context']:
                if 'project_id' not in data:
                    if self.logger:
                        self.logger.warning(f"Action {action} requires project_id")
                    return False

            # Additional validation can be added here
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error validating request: {e}")
            return False

    def _success_response(self, data: Any) -> Dict[str, Any]:
        """Generate standardized success response"""
        response = {
            'success': True,
            'agent_id': self.agent_id,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
        }

        if data is not None:
            response['data'] = data

        return response

    def _error_response(self, error_message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
        """Generate standardized error response"""
        response = {
            'success': False,
            'error': error_message,
            'agent_id': self.agent_id,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
        }

        if error_code:
            response['error_code'] = error_code

        return response

    def _emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Emit event through event system if available"""
        if not self.events:
            return

        try:
            if hasattr(self.events, 'emit'):
                self.events.emit(event_type, self.agent_id, event_data)
            elif hasattr(self.events, 'publish'):
                self.events.publish(event_type, event_data)
            else:
                if self.logger:
                    self.logger.debug("Event system available but no known emit method")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to emit event {event_type}: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        try:
            status = {
                'agent_id': self.agent_id,
                'name': self.name,
                'status': 'active',
                'capabilities': self.get_capabilities(),
                'has_claude_client': self.claude_client is not None,
                'has_database': self.db_service is not None,
                'has_events': self.events is not None,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            }

            # Test basic functionality
            try:
                self.get_capabilities()
                status['responsive'] = True
            except Exception:
                status['responsive'] = False
                status['status'] = 'error'

            return status

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting agent status: {e}")

            return {
                'agent_id': self.agent_id,
                'name': self.name,
                'status': 'error',
                'error': str(e),
                'responsive': False
            }

    def shutdown(self) -> Dict[str, Any]:
        """Gracefully shutdown the agent"""
        if self.logger:
            self.logger.info(f"Shutting down agent {self.name}")

        try:
            # Close Claude client if available
            if self.claude_client:
                self.claude_client = None

            # Clear event handlers
            self.events = None

            # Clear database connections
            self.db_service = None

            if self.logger:
                self.logger.info(f"Agent {self.name} shutdown complete")

            return {
                'success': True,
                'agent_id': self.agent_id,
                'message': f"Agent {self.name} shutdown successfully"
            }

        except Exception as e:
            error_msg = f"Error during agent shutdown: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)

            return {
                'success': False,
                'agent_id': self.agent_id,
                'error': error_msg
            }


# ============================================================================
# UTILITY CLASSES
# ============================================================================

class AgentUtils:
    """Utility functions for agent operations"""

    @staticmethod
    def validate_project_access(project_id: str, username: str) -> bool:
        """Validate if user has access to project"""
        logger = get_logger('agent.utils') if CORE_AVAILABLE else None

        if logger:
            logger.debug(f"Validating project access for user {username} to project {project_id}")

        try:
            db = get_database()
            if not db:
                if logger:
                    logger.warning("Database not available for access validation")
                return False

            # Get project
            project = db.projects.get_by_id(project_id)
            if not project:
                if logger:
                    logger.warning(f"Project {project_id} not found")
                return False

            # Check if owner
            if project.owner_id == username:
                if logger:
                    logger.debug(f"User {username} is owner of project {project_id}")
                return True

            # Check collaborator access
            try:
                collaborators = db.project_collaborators.get_project_collaborators(project_id)
                for collab in collaborators:
                    if collab.get('username') == username and collab.get('is_active'):
                        if logger:
                            logger.debug(f"User {username} is active collaborator on project {project_id}")
                        return True
            except Exception as e:
                if logger:
                    logger.warning(f"Error checking collaborators: {e}")

            # Check if in team members
            if hasattr(project, 'team_members') and username in project.team_members:
                if logger:
                    logger.debug(f"User {username} is team member of project {project_id}")
                return True

            if logger:
                logger.warning(f"User {username} has no access to project {project_id}")
            return False

        except Exception as e:
            if logger:
                logger.error(f"Error validating project access: {e}")
            return False

    @staticmethod
    def get_user_role_in_project(project_id: str, username: str) -> str:
        """Get user's role in a specific project"""
        logger = get_logger('agent.utils') if CORE_AVAILABLE else None

        if logger:
            logger.debug(f"Getting user role for {username} in project {project_id}")

        try:
            db = get_database()
            if not db:
                if logger:
                    logger.warning("Database not available for role lookup")
                return 'none'

            # Get project
            project = db.projects.get_by_id(project_id)
            if not project:
                if logger:
                    logger.warning(f"Project {project_id} not found")
                return 'none'

            # Check if owner
            if project.owner_id == username:
                if logger:
                    logger.debug(f"User {username} is owner of project {project_id}")
                return 'owner'

            # Check collaborator role
            try:
                collaborators = db.project_collaborators.get_project_collaborators(project_id)
                for collab in collaborators:
                    if collab.get('username') == username and collab.get('is_active'):
                        role = collab.get('role', 'member')
                        if logger:
                            logger.debug(f"User {username} has role {role} in project {project_id}")
                        return role
            except Exception as e:
                if logger:
                    logger.warning(f"Error checking collaborator role: {e}")

            # Check if in team members (default role)
            if hasattr(project, 'team_members') and username in project.team_members:
                if logger:
                    logger.debug(f"User {username} is team member (default role) of project {project_id}")
                return 'member'

            if logger:
                logger.debug(f"User {username} has no role in project {project_id}")
            return 'none'

        except Exception as e:
            if logger:
                logger.error(f"Error getting user role: {e}")
            return 'none'

    @staticmethod
    def create_agent_context(project_id: str, username: str) -> Dict[str, Any]:
        """Create context object for agent requests"""
        logger = get_logger('agent.utils') if CORE_AVAILABLE else None

        if logger:
            logger.debug(f"Creating agent context for user {username}, project {project_id}")

        try:
            db = get_database()

            context = {
                'project_id': project_id,
                'username': username,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None,
                'has_access': AgentUtils.validate_project_access(project_id, username),
                'user_role': AgentUtils.get_user_role_in_project(project_id, username)
            }

            if not db:
                context['error'] = 'Database not available'
                if logger:
                    logger.warning("Database not available for context creation")
                return context

            # Get project details
            try:
                project = db.projects.get_by_id(project_id)
                if project:
                    context.update({
                        'project_name': project.name,
                        'project_phase': project.phase.value if hasattr(project.phase, 'value') else str(project.phase),
                        'project_status': project.status.value if hasattr(project.status, 'value') else str(
                            project.status)
                    })

                    if logger:
                        logger.debug(f"Added project details to context: {project.name}")

            except Exception as e:
                context['project_error'] = str(e)
                if logger:
                    logger.warning(f"Error getting project details: {e}")

            # Get user details
            try:
                user = db.users.get_by_username(username)
                if user:
                    context.update({
                        'user_email': user.email,
                        'user_role_global': user.role.value if hasattr(user.role, 'value') else str(user.role)
                    })

                    if logger:
                        logger.debug(f"Added user details to context: {user.email}")

            except Exception as e:
                context['user_error'] = str(e)
                if logger:
                    logger.warning(f"Error getting user details: {e}")

            if logger:
                logger.debug(f"Agent context created successfully for {username}")

            return context

        except Exception as e:
            error_msg = f"Error creating agent context: {e}"
            if logger:
                logger.error(error_msg)

            return {
                'project_id': project_id,
                'username': username,
                'error': str(e),
                'has_access': False
            }


# ============================================================================
# DECORATORS
# ============================================================================

def require_project_access(func):
    """Decorator to require project access for agent methods"""

    @wraps(func)
    def wrapper(self, data: Dict[str, Any]) -> Dict[str, Any]:
        project_id = data.get('project_id')
        username = data.get('username')

        if not project_id:
            if self.logger:
                self.logger.warning("Project ID is required but not provided")
            return self._error_response("Project ID is required")

        if not username:
            if self.logger:
                self.logger.warning("Username is required but not provided")
            return self._error_response("Username is required")

        if not AgentUtils.validate_project_access(project_id, username):
            if self.logger:
                self.logger.warning(f"Access denied for user {username} to project {project_id}")
            return self._error_response("Access denied: User does not have access to this project")

        return func(self, data)

    return wrapper


def require_authentication(func):
    """Decorator to require user authentication for agent methods"""

    @wraps(func)
    def wrapper(self, data: Dict[str, Any]) -> Dict[str, Any]:
        username = data.get('username')

        if not username:
            if self.logger:
                self.logger.warning("Authentication required but username not provided")
            return self._error_response("Authentication required: Username is required")

        try:
            db = get_database()
            if not db:
                if self.logger:
                    self.logger.error("Database not available for authentication")
                return self._error_response("Authentication error: Database not available")

            # Check if user exists and is active
            user = db.users.get_by_username(username)
            if not user:
                if self.logger:
                    self.logger.warning(f"Authentication failed: User {username} not found")
                return self._error_response("Authentication failed: User not found")

            if not getattr(user, 'is_active', True):
                if self.logger:
                    self.logger.warning(f"Authentication failed: User {username} account is inactive")
                return self._error_response("Authentication failed: User account is inactive")

            if self.logger:
                self.logger.debug(f"User {username} authenticated successfully")

            return func(self, data)

        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            return self._error_response(error_msg)

    return wrapper


def log_agent_action(func):
    """Decorator to log agent actions"""

    @wraps(func)
    def wrapper(self, data: Dict[str, Any]) -> Dict[str, Any]:
        action_name = func.__name__
        project_id = data.get('project_id', 'unknown')
        username = data.get('username', 'unknown')

        if self.logger:
            self.logger.info(f"Agent action started: {action_name} for project {project_id} by user {username}")

        start_time = time.time()
        try:
            result = func(self, data)
            execution_time = time.time() - start_time

            success = result.get('success', False) if isinstance(result, dict) else True
            if self.logger:
                self.logger.info(
                    f"Agent action completed: {action_name} (success: {success}, time: {execution_time:.2f}s)")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            if self.logger:
                self.logger.error(f"Agent action failed: {action_name} (time: {execution_time:.2f}s, error: {str(e)})")
            raise

    return wrapper


def rate_limit(calls_per_minute: int = 60):
    """Decorator to rate limit agent methods"""

    def decorator(func):
        # Store call history as function attribute (intentional use for rate limiting)
        if not hasattr(func, 'call_history'):
            func.call_history = []

        @wraps(func)
        def wrapper(self, data: Dict[str, Any]) -> Dict[str, Any]:
            current_time = time.time()

            # Clean old calls
            func.call_history = [t for t in func.call_history if current_time - t < 60]

            # Check rate limit
            if len(func.call_history) >= calls_per_minute:
                if self.logger:
                    self.logger.warning(f"Rate limit exceeded: {calls_per_minute} calls per minute")
                return self._error_response(f"Rate limit exceeded: {calls_per_minute} calls per minute")

            # Record this call
            func.call_history.append(current_time)

            return func(self, data)

        return wrapper

    return decorator
