"""
Socratic RAG Enhanced - Base Agent Architecture
==============================================

Base agent class and common utilities for all Socratic RAG agents.
Provides common functionality like Claude API integration, logging, events.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List

# Import our actual core system
from src.core import (
    get_logger, get_config, get_event_bus,
    DateTimeHelper, ANTHROPIC_AVAILABLE
)
from src.database import get_database

# Anthropic client import with fallback
if ANTHROPIC_AVAILABLE:
    from anthropic import Anthropic


class BaseAgent(ABC):
    """Base class for all Socratic RAG agents with enterprise capabilities"""

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.config = get_config()
        self.logger = get_logger(f"agent.{agent_id}")
        self.db = get_database()
        self.events = get_event_bus()

        # Initialize Claude client if API key available
        self.claude_client = None
        if ANTHROPIC_AVAILABLE and self.config.claude_api_key:
            try:
                self.claude_client = Anthropic(api_key=self.config.claude_api_key)
                self.logger.info(f"Claude client initialized for {self.name}")
            except Exception as e:
                self.logger.warning(f"Claude client initialization failed: {e}")

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        pass

    def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent request with error handling"""
        try:
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
                self.events.publish_async('agent_action_completed', self.agent_id, {
                    'agent_id': self.agent_id,
                    'action': action,
                    'success': True,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                })

                return self._success_response(result)
            else:
                return self._error_response(f"Action '{action}' not supported")

        except Exception as e:
            self.logger.error(f"Error processing {action}: {str(e)}")
            self.events.publish_async('agent_error', self.agent_id, {
                'agent_id': self.agent_id,
                'action': action,
                'error': str(e),
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
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
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Standard error response format"""
        return {
            'success': False,
            'error': message,
            'agent_id': self.agent_id,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

    def call_claude(self, prompt: str, model: str = None, max_tokens: int = None) -> str:
        """Make Claude API call with error handling"""
        if not self.claude_client:
            return "Claude API not available"

        try:
            model = model or self.config.claude_model
            max_tokens = max_tokens or 4000

            response = self.claude_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            # Log API usage
            self.events.publish_async('claude_api_usage', self.agent_id, {
                'agent_id': self.agent_id,
                'model': model,
                'tokens_used': max_tokens,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            })

            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Claude API error: {e}")
            return f"Error: {str(e)}"


class AgentUtils:
    """Utility functions for agent operations"""

    @staticmethod
    def validate_project_access(project_id: str, username: str) -> bool:
        """Validate if user has access to project"""
        try:
            db = get_database()
            project = db.projects.get_by_id(project_id)

            if not project:
                return False

            # Check if user is owner or collaborator
            if project.owner == username:
                return True

            return any(c.username == username and c.is_active for c in project.collaborators)

        except Exception as e:
            logger = get_logger('agent.utils')
            logger.error(f"Error validating project access: {e}")
            return False

    @staticmethod
    def get_user_role_in_project(project_id: str, username: str) -> str:
        """Get user's role in a specific project"""
        try:
            db = get_database()
            project = db.projects.get_by_id(project_id)

            if not project:
                return "None"

            # Check if owner
            if project.owner == username:
                return 'owner'

            # Check collaborators
            for collaborator in project.collaborators:
                if collaborator.username == username and collaborator.is_active:
                    return collaborator.role.value

            return 'None'

        except Exception as e:
            logger = get_logger('agent.utils')
            logger.error(f"Error getting user role: {e}")
            return 'None'

    @staticmethod
    def create_agent_context(project_id: str, username: str) -> Dict[str, Any]:
        """Create context object for agent requests"""
        try:
            db = get_database()
            project = db.projects.get_by_id(project_id)
            user = db.users.get_by_username(username)

            context = {
                'project_id': project_id,
                'username': username,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'has_access': AgentUtils.validate_project_access(project_id, username),
                'user_role': AgentUtils.get_user_role_in_project(project_id, username)
            }

            if project:
                context.update({
                    'project_name': project.name,
                    'project_phase': project.phase.value,
                    'project_status': project.status.value
                })

            if user:
                context.update({
                    'user_roles': [role.value for role in user.roles],
                    'user_email': user.email
                })

            return context

        except Exception as e:
            logger = get_logger('agent.utils')
            logger.error(f"Error creating agent context: {e}")
            return {
                'project_id': project_id,
                'username': username,
                'error': str(e),
                'has_access': False
            }


def require_project_access(func):
    """Decorator to require project access for agent methods"""

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

    def wrapper(self, data: Dict[str, Any]) -> Dict[str, Any]:
        username = data.get('username')

        if not username:
            return self._error_response("Authentication required: Username is required")

        try:
            db = get_database()
            user = db.users.get_by_username(username)

            if not user or not user.is_active:
                return self._error_response("Authentication failed: Invalid or inactive user")

            return func(self, data)

        except Exception as e:
            return self._error_response(f"Authentication error: {str(e)}")

    return wrapper


def log_agent_action(func):
    """Decorator to log agent actions"""

    def wrapper(self, data: Dict[str, Any]) -> Dict[str, Any]:
        action_name = func.__name__
        project_id = data.get('project_id', 'unknown')
        username = data.get('username', 'unknown')

        self.logger.info(f"Agent action started: {action_name} for project {project_id} by user {username}")

        start_time = time.time()
        try:
            result = func(self, data)
            execution_time = time.time() - start_time

            success = result.get('success', False) if isinstance(result, dict) else True
            self.logger.info(f"Agent action completed: {action_name} (success: {success}, time: {execution_time:.2f}s)")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Agent action failed: {action_name} (time: {execution_time:.2f}s, error: {str(e)})")
            raise

    return wrapper
