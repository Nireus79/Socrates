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
    get_logger = lambda x: None
    get_config = lambda: {}
    get_event_bus = lambda: None
    get_database = lambda: None
    DateTimeHelper = None
    ANTHROPIC_AVAILABLE = False
    AgentError = Exception

# Anthropic client import with fallback
if ANTHROPIC_AVAILABLE:
    try:
        from anthropic import Anthropic
    except ImportError:
        ANTHROPIC_AVAILABLE = False


class BaseAgent(ABC):
    """Base class for all Socratic RAG agents with enterprise capabilities"""

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.config = get_config() if CORE_AVAILABLE else {}
        self.logger = get_logger(f"agent.{agent_id}") if CORE_AVAILABLE else None
        self.db = get_database() if CORE_AVAILABLE else None
        self.events = get_event_bus() if CORE_AVAILABLE else None

        # Initialize Claude client if API key available
        self.claude_client = None
        if ANTHROPIC_AVAILABLE and self.config:
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
        try:
            if self.logger:
                self.logger.info(f"Processing {action} request")

            # Validate input data
            if not self._validate_request(action, data):
                return self._error_response("Invalid request data")

            # Route to appropriate method
            method_name = f"_{action}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                result = method(data)

                # Emit event for successful processing
                self._emit_event('agent_action_completed', {
                    'agent_id': self.agent_id,
                    'action': action,
                    'success': True,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
                })

                return self._success_response(result)
            else:
                return self._error_response(f"Action '{action}' not supported")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error processing {action}: {str(e)}")
            self._emit_event('agent_error', {
                'agent_id': self.agent_id,
                'action': action,
                'error': str(e),
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            })
            return self._error_response(str(e))

    def _validate_request(self, action: str, data: Dict[str, Any]) -> bool:
        """Validate request data"""
        return isinstance(data, dict)

    def _success_response(self, data: Any) -> Dict[str, Any]:
        """Standard success response format"""
        return {
            'success': True,
            'data': data,
            'agent_id': self.agent_id,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
        }

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Standard error response format"""
        return {
            'success': False,
            'error': message,
            'agent_id': self.agent_id,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
        }

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event using the event system"""
        try:
            if self.events and hasattr(self.events, 'emit'):
                self.events.emit(event_type, self.agent_id, data)
            elif self.events and hasattr(self.events, 'publish_async'):
                self.events.publish_async(event_type, self.agent_id, data)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to emit event {event_type}: {e}")

    def call_claude(self, prompt: str, model: str = None, max_tokens: int = None) -> str:
        """Make Claude API call with error handling"""
        if not self.claude_client:
            return "Claude API not available"

        try:
            model = model or (self.config.get('services.claude.model') if self.config else 'claude-3-5-sonnet-20241022')
            max_tokens = max_tokens or (self.config.get('services.claude.max_tokens') if self.config else 4000)

            response = self.claude_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            # Log API usage
            self._emit_event('claude_api_usage', {
                'agent_id': self.agent_id,
                'model': model,
                'tokens_used': max_tokens,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            })

            return response.content[0].text

        except Exception as e:
            if self.logger:
                self.logger.error(f"Claude API error: {e}")
            return f"Error: {str(e)}"


class AgentUtils:
    """Utility functions for agent operations"""

    @staticmethod
    def validate_project_access(project_id: str, username: str) -> bool:
        """Validate if user has access to project"""
        try:
            db = get_database()
            if not db:
                return False

            # Get project
            project = db.projects.get_by_id(project_id)
            if not project:
                return False

            # Check if user is owner
            if project.owner_id == username:
                return True

            # Check if user is in team members
            if hasattr(project, 'team_members') and username in project.team_members:
                return True

            # Check collaborators table if it exists
            try:
                collaborators = db.project_collaborators.get_project_collaborators(project_id)
                for collab in collaborators:
                    if collab.get('username') == username and collab.get('is_active'):
                        return True
            except:
                pass

            return False

        except Exception as e:
            logger = get_logger('agent.utils') if CORE_AVAILABLE else None
            if logger:
                logger.error(f"Error validating project access: {e}")
            return False

    @staticmethod
    def get_user_role_in_project(project_id: str, username: str) -> str:
        """Get user's role in a specific project"""
        try:
            db = get_database()
            if not db:
                return 'none'

            # Get project
            project = db.projects.get_by_id(project_id)
            if not project:
                return 'none'

            # Check if owner
            if project.owner_id == username:
                return 'owner'

            # Check collaborator role
            try:
                collaborators = db.project_collaborators.get_project_collaborators(project_id)
                for collab in collaborators:
                    if collab.get('username') == username and collab.get('is_active'):
                        return collab.get('role', 'member')
            except:
                pass

            # Check if in team members (default role)
            if hasattr(project, 'team_members') and username in project.team_members:
                return 'member'

            return 'none'

        except Exception as e:
            logger = get_logger('agent.utils') if CORE_AVAILABLE else None
            if logger:
                logger.error(f"Error getting user role: {e}")
            return 'none'

    @staticmethod
    def create_agent_context(project_id: str, username: str) -> Dict[str, Any]:
        """Create context object for agent requests"""
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
                return context

            # Get project details
            try:
                project = db.projects.get_by_id(project_id)
                if project:
                    context.update({
                        'project_name': project.name,
                        'project_phase': project.phase.value if hasattr(project.phase, 'value') else str(project.phase),
                        'project_status': project.status.value if hasattr(project.status, 'value') else str(project.status)
                    })
            except Exception as e:
                context['project_error'] = str(e)

            # Get user details
            try:
                user = db.users.get_by_username(username)
                if user:
                    context.update({
                        'user_email': user.email,
                        'user_role_global': user.role.value if hasattr(user.role, 'value') else str(user.role)
                    })
            except Exception as e:
                context['user_error'] = str(e)

            return context

        except Exception as e:
            logger = get_logger('agent.utils') if CORE_AVAILABLE else None
            if logger:
                logger.error(f"Error creating agent context: {e}")
            return {
                'project_id': project_id,
                'username': username,
                'error': str(e),
                'has_access': False
            }


def require_project_access(func):
    """Decorator to require project access for agent methods"""
    @wraps(func)
    def wrapper(self, data: Dict[str, Any]) -> Dict[str, Any]:
        project_id = data.get('project_id')
        username = data.get('username')

        if not project_id:
            return self._error_response("Project ID is required")

        if not username:
            return self._error_response("Username is required")

        if not AgentUtils.validate_project_access(project_id, username):
            return self._error_response("Access denied: User does not have access to this project")

        return func(self, data)

    return wrapper


def require_authentication(func):
    """Decorator to require user authentication for agent methods"""
    @wraps(func)
    def wrapper(self, data: Dict[str, Any]) -> Dict[str, Any]:
        username = data.get('username')

        if not username:
            return self._error_response("Authentication required: Username is required")

        try:
            db = get_database()
            if not db:
                return self._error_response("Authentication error: Database not available")

            # Check if user exists and is active
            user = db.users.get_by_username(username)
            if not user:
                return self._error_response("Authentication failed: User not found")

            if not user.is_active:
                return self._error_response("Authentication failed: User account is inactive")

            return func(self, data)

        except Exception as e:
            return self._error_response(f"Authentication error: {str(e)}")

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
                self.logger.info(f"Agent action completed: {action_name} (success: {success}, time: {execution_time:.2f}s)")

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
        func._last_calls = []

        @wraps(func)
        def wrapper(self, data: Dict[str, Any]) -> Dict[str, Any]:
            current_time = time.time()

            # Clean old calls
            func._last_calls = [t for t in func._last_calls if current_time - t < 60]

            # Check rate limit
            if len(func._last_calls) >= calls_per_minute:
                return self._error_response(f"Rate limit exceeded: {calls_per_minute} calls per minute")

            # Record this call
            func._last_calls.append(current_time)

            return func(self, data)

        return wrapper
    return decorator
