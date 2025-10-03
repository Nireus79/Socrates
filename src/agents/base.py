#!/usr/bin/env python3
"""
BaseAgent - Foundation Class for All Agents
============================================

Provides common functionality like Claude API integration, logging, events.
Uses dependency injection pattern with ServiceContainer.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from functools import wraps

# Import core system components with proper fallbacks
try:
    from src.core import (
        ServiceContainer, DateTimeHelper, ANTHROPIC_AVAILABLE,
        AgentError, ValidationError, DatabaseError
    )
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

    # Fallback ServiceContainer class
    class ServiceContainer:
        """Fallback ServiceContainer when core is not available"""

        def __init__(self):
            self.config = None
            self.logger_system = None
            self.event_system = None
            self.db_manager = None

        def get_logger(self, name: str):
            import logging
            return logging.getLogger(name)

        def get_config(self):
            return {}

        def get_event_bus(self):
            return None

        def get_db_manager(self):
            return None


    # Fallback helper classes
    class DateTimeHelper:
        @staticmethod
        def now():
            from datetime import datetime, timezone
            return datetime.now(timezone.utc)

        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None


    # Fallback exceptions
    class AgentError(Exception):
        pass


    class ValidationError(Exception):
        pass


    class DatabaseError(Exception):
        pass


    # Fallback constants
    ANTHROPIC_AVAILABLE = False

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

    def __init__(self, agent_id: str, name: str, services: Optional[ServiceContainer] = None):
        """
        Initialize base agent with dependency injection

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            services: ServiceContainer with configured services
        """
        self.agent_id = agent_id
        self.name = name
        self.services = services

        # Initialize services with fallbacks
        if services:
            self.config = services.get_config()
            self.logger = services.get_logger(f"agent.{agent_id}")
            self.events = services.get_event_bus()
            self.db_manager = services.get_db_manager()
        else:
            # Fallback when no services provided
            self.config = {}
            self.logger = logging.getLogger(f"agent.{agent_id}")
            self.events = None
            self.db_manager = None

        # Claude API client setup
        self.claude_client = None
        self._initialize_claude_client()

        # Agent statistics
        self.stats: Dict[str, Union[int, float, datetime, None]] = {
            'requests_processed': 0,
            'errors_encountered': 0,
            'last_activity': None,  # Will be datetime or None
            'average_response_time': 0.0
        }

        # Performance tracking
        self._start_times = {}

        if self.logger:
            self.logger.info(f"Agent {self.name} ({self.agent_id}) initialized")

    def _initialize_claude_client(self):
        """Initialize Claude API client if available"""
        if not ANTHROPIC_AVAILABLE or not Anthropic:
            if self.logger:
                self.logger.debug("Claude API not available")
            return

        try:
            api_key = None
            if self.config:
                api_key = self.config.get('anthropic.api_key')

            if not api_key:
                # Fallback for direct environment check
                import os
                api_key = os.getenv('API_KEY_CLAUDE')

            if api_key:
                self.claude_client = Anthropic(api_key=api_key)
                if self.logger:
                    self.logger.info("Claude API client initialized successfully")
            else:
                if self.logger:
                    self.logger.warning("No Anthropic API key found")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize Claude client: {e}")

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        pass

    def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming request

        Args:
            action: Action to perform
            data: Request data

        Returns:
            Dict with response
        """
        # Track request start
        start_time = time.time()
        self.stats['requests_processed'] += 1
        self.stats['last_activity'] = DateTimeHelper.now()

        try:
            # Find and execute action method
            method_name = f"_{action}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                result = method(data)

                # Update performance stats
                duration = time.time() - start_time
                self._update_response_time(duration)

                return result
            else:
                return self._error_response(
                    f"Unknown action: {action}",
                    "UNKNOWN_ACTION"
                )

        except Exception as e:
            self.stats['errors_encountered'] += 1
            if self.logger:
                self.logger.error(f"Request processing error: {e}", exc_info=True)
            return self._error_response(str(e), "PROCESSING_ERROR")

    def _update_response_time(self, duration: float):
        """Update average response time"""
        current_avg = self.stats['average_response_time']
        count = self.stats['requests_processed']
        self.stats['average_response_time'] = (
            (current_avg * (count - 1) + duration) / count
        )

    def _success_response(self, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized success response"""
        return {
            'success': True,
            'message': message,
            'data': data or {},
            'agent_id': self.agent_id,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

    def _error_response(self, message: str, error_code: str = None) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'success': False,
            'error': message,
            'error_code': error_code,
            'agent_id': self.agent_id,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get agent performance statistics"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'stats': self.stats.copy(),
            'capabilities': self.get_capabilities(),
            'claude_available': self.claude_client is not None,
            'services_available': self.services is not None
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on agent"""
        health_status = {
            'agent_id': self.agent_id,
            'name': self.name,
            'status': 'healthy',
            'services': {},
            'claude_available': self.claude_client is not None,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

        # Check services availability
        if self.services:
            health_status['services'] = {
                'config': self.services.get_config() is not None,
                'logger': self.services.get_logger('test') is not None,
                'events': self.services.get_event_bus() is not None,
                'database': self.services.get_db_manager() is not None
            }
        else:
            health_status['services'] = {
                'config': False,
                'logger': True,  # Basic logging always available
                'events': False,
                'database': False
            }
            health_status['status'] = 'active'

        # Check database connectivity if available
        if self.db_manager:
            try:
                db_healthy = self.db_manager.health_check()
                health_status['services']['database'] = db_healthy
                if not db_healthy:
                    health_status['status'] = 'degraded'
            except Exception as e:
                health_status['services']['database'] = False
                health_status['status'] = 'unhealthy'
                health_status['error'] = f"Database check failed: {e}"

        return health_status

    def claude_request(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Make request to Claude API"""
        if not self.claude_client:
            if self.logger:
                self.logger.warning("Claude API not available for request")
            return None

        try:
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        except Exception as e:
            if self.logger:
                self.logger.error(f"Claude API request failed: {e}")
            return None


# ============================================================================
# DECORATORS
# ============================================================================

def require_authentication(func):
    """
    Decorator to require authentication for agent methods.

    Validates that:
    - user_id is provided in data
    - User exists in database
    - User status is 'active'

    Adds _authenticated_user to data dict for use in wrapped method.
    """

    @wraps(func)
    def wrapper(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Check for user_id
        user_id = data.get('user_id')
        if not user_id:
            return self._error_response(
                "Authentication required: user_id must be provided",
                "AUTH_REQUIRED"
            )

        # Get database manager
        db_manager = self.services.get_db_manager() if self.services else None
        if not db_manager:
            return self._error_response(
                "Database service unavailable",
                "DB_UNAVAILABLE"
            )

        # Verify user exists and is active
        try:
            # Import here to avoid circular imports
            from src.database import get_database
            db = get_database()
            user = db.users.get_by_id(user_id)

            if not user:
                return self._error_response(
                    f"Invalid user_id: {user_id}",
                    "INVALID_USER"
                )

            # Check user status
            user_status = user.status if hasattr(user, 'status') else 'active'
            if isinstance(user_status, str):
                status_value = user_status
            else:
                status_value = user_status.value if hasattr(user_status, 'value') else str(user_status)

            if status_value != 'active':
                return self._error_response(
                    f"User account is not active: {status_value}",
                    "USER_INACTIVE"
                )

            # Add authenticated user to data for use in wrapped method
            data['_authenticated_user'] = user

            # Call the wrapped function
            return func(self, data)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Authentication error: {e}")
            return self._error_response(
                f"Authentication failed: {str(e)}",
                "AUTH_FAILED"
            )

    return wrapper


def require_project_access(func):
    """
    Decorator to require project access for agent methods.

    Validates that:
    - User is authenticated (applies require_authentication automatically)
    - project_id is provided
    - Project exists
    - User is owner or active collaborator

    Adds _project_role and _project to data dict for use in wrapped method.
    """

    @wraps(func)
    @require_authentication
    def wrapper(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Check for project_id
        project_id = data.get('project_id')
        if not project_id:
            return self._error_response(
                "project_id is required",
                "PROJECT_ID_REQUIRED"
            )

        # Get authenticated user (added by require_authentication)
        user = data.get('_authenticated_user')
        if not user:
            return self._error_response(
                "Authentication required",
                "AUTH_REQUIRED"
            )

        try:
            # Import here to avoid circular imports
            from src.database import get_database
            db = get_database()

            # Check if project exists
            project = db.projects.get_by_id(project_id)
            if not project:
                return self._error_response(
                    f"Project not found: {project_id}",
                    "PROJECT_NOT_FOUND"
                )

            # Check if user is owner
            project_owner_id = project.owner_id if hasattr(project, 'owner_id') else None
            user_id = user.id if hasattr(user, 'id') else str(user)

            if project_owner_id == user_id:
                data['_project_role'] = 'owner'
                data['_project'] = project
                return func(self, data)

            # Check if user is a collaborator
            collaborators = db.project_collaborators.get_by_project_id(project_id)
            for collab in collaborators:
                collab_user_id = collab.user_id if hasattr(collab, 'user_id') else None
                collab_status = collab.status if hasattr(collab, 'status') else 'active'

                # Handle status enum
                if not isinstance(collab_status, str):
                    collab_status = collab_status.value if hasattr(collab_status, 'value') else str(collab_status)

                if collab_user_id == user_id and collab_status == 'active':
                    collab_role = collab.role if hasattr(collab, 'role') else 'collaborator'
                    if not isinstance(collab_role, str):
                        collab_role = collab_role.value if hasattr(collab_role, 'value') else str(collab_role)

                    data['_project_role'] = collab_role
                    data['_project'] = project
                    return func(self, data)

            # User has no access
            return self._error_response(
                f"Access denied: User {user_id} does not have access to project {project_id}",
                "ACCESS_DENIED"
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Project access check error: {e}")
            return self._error_response(
                f"Access check failed: {str(e)}",
                "ACCESS_CHECK_FAILED"
            )

    return wrapper


def log_agent_action(func):
    """
    Decorator to log agent actions with performance tracking
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        action_name = func.__name__
        start_time = time.time()

        if hasattr(self, 'logger') and self.logger:
            self.logger.info(f"Starting action: {action_name}")

        try:
            result = func(self, *args, **kwargs)
            duration = time.time() - start_time

            if hasattr(self, 'logger') and self.logger:
                self.logger.info(f"Completed action: {action_name} in {duration:.3f}s")

            # Emit event if event bus available
            if hasattr(self, 'events') and self.events:
                self.events.emit('agent_action', self.agent_id, {
                    'action': action_name,
                    'duration': duration,
                    'success': True
                })

            return result

        except Exception as e:
            duration = time.time() - start_time

            if hasattr(self, 'logger') and self.logger:
                self.logger.error(f"Failed action: {action_name} after {duration:.3f}s - {e}")

            # Emit error event
            if hasattr(self, 'events') and self.events:
                self.events.emit('agent_action', self.agent_id, {
                    'action': action_name,
                    'duration': duration,
                    'success': False,
                    'error': str(e)
                })

            raise

    return wrapper


def monitor_performance(operation: str = None):
    """
    Decorator factory for detailed performance monitoring

    Args:
        operation: Custom operation name (defaults to function name)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            op_name = operation or func.__name__
            start_time = time.time()

            try:
                result = func(self, *args, **kwargs)

                # Log performance
                duration = time.time() - start_time
                if hasattr(self, 'logger') and self.logger:
                    self.logger.debug(f"Operation {op_name} completed in {duration:.3f}s")

                # Emit performance event
                if hasattr(self, 'events') and self.events:
                    self.events.emit('agent_performance', self.agent_id, {
                        'operation': op_name,
                        'duration': duration,
                        'success': True
                    })

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Log error with performance
                if hasattr(self, 'logger') and self.logger:
                    self.logger.error(f"Operation {op_name} failed after {duration:.3f}s: {e}")

                # Emit error event
                if hasattr(self, 'events') and self.events:
                    self.events.emit('agent_performance', self.agent_id, {
                        'operation': op_name,
                        'duration': duration,
                        'success': False,
                        'error': str(e)
                    })

                raise

        return wrapper

    return decorator


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_agent_with_services(agent_class, agent_id: str, name: str,
                                services: ServiceContainer) -> BaseAgent:
    """Factory function to create agents with services"""
    try:
        return agent_class(agent_id, name, services)
    except Exception as e:
        # Fallback to basic agent creation
        logger = services.get_logger('agent_factory') if services else logging.getLogger('agent_factory')
        logger.error(f"Failed to create agent {agent_id} with services: {e}")

        # Try without services
        try:
            return agent_class(agent_id, name)
        except Exception as e2:
            logger.error(f"Failed to create agent {agent_id} without services: {e2}")
            raise AgentError(f"Could not create agent {agent_id}: {e2}")


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'BaseAgent',
    'require_authentication',
    'require_project_access',
    'log_agent_action',
    'monitor_performance',
    'create_agent_with_services',
    'AgentError',
    'ValidationError',
    'DatabaseError'
]

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # Test base agent functionality
    print("Testing BaseAgent with ServiceContainer...")

    class TestAgent(BaseAgent):
        def get_capabilities(self) -> List[str]:
            return ['test']

        def _test_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
            return {'result': 'success'}


    # Test agent creation
    agent = TestAgent('test_agent', 'Test Agent')
    print(f"✅ Created agent: {agent.name}")

    # Test request processing
    result = agent.process_request('test_action', {'test': 'data'})
    print(f"✅ Request result: {result['success']}")

    # Test health check
    health = agent.health_check()
    print(f"✅ Health status: {health['status']}")

    # Test stats
    stats = agent.get_stats()
    print(f"✅ Requests processed: {stats['stats']['requests_processed']}")

    print("\n🎉 BaseAgent tests passed!")
