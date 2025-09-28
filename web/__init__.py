"""
Web Package - Flask Application and User Interface
================================================

This module provides the web interface for the Socratic RAG Enhanced system.
Handles Flask application setup, routing, templates, and agent integration.

Components:
- Flask application with Blueprint organization
- Real-time dashboard and analytics
- Agent management interface
- Project and code generation UI
- User authentication and session management
- RESTful API endpoints for agent communication
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Web interface availability tracking
_flask_available = False
_app_instance = None
_config_loaded = False


def check_web_dependencies() -> Dict[str, bool]:
    """Check availability of web interface dependencies."""
    dependencies = {}

    # Check Flask
    try:
        import flask
        dependencies['flask'] = True
        global _flask_available
        _flask_available = True
    except ImportError:
        dependencies['flask'] = False
        logger.warning("Flask not available. Install with: pip install flask")

    # Check Flask extensions
    try:
        import flask_wtf
        dependencies['flask_wtf'] = True
    except ImportError:
        dependencies['flask_wtf'] = False
        logger.warning("Flask-WTF not available. Install with: pip install flask-wtf")

    try:
        import flask_login
        dependencies['flask_login'] = True
    except ImportError:
        dependencies['flask_login'] = False
        logger.warning("Flask-Login not available. Install with: pip install flask-login")

    # Check template engine dependencies
    try:
        import jinja2
        dependencies['jinja2'] = True
    except ImportError:
        dependencies['jinja2'] = False
        logger.warning("Jinja2 not available")

    return dependencies


def create_app(config_override: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    """
    Create and configure Flask application.

    Args:
        config_override: Optional configuration overrides

    Returns:
        Flask app instance or None if Flask not available
    """
    if not _flask_available:
        logger.error("Cannot create Flask app - Flask not available")
        return None

    try:
        from .app import create_flask_app

        app = create_flask_app(config_override)

        global _app_instance
        _app_instance = app

        logger.info("Flask application created successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to create Flask application: {e}")
        return None


def get_app() -> Optional[Any]:
    """Get the current Flask application instance."""
    global _app_instance

    if _app_instance is None and _flask_available:
        _app_instance = create_app()

    return _app_instance


def initialize_web_interface(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Initialize the web interface with agent integration.

    Args:
        config: Optional configuration dictionary

    Returns:
        True if initialization successful, False otherwise
    """
    try:
        # Check dependencies first
        deps = check_web_dependencies()
        missing_deps = [dep for dep, available in deps.items() if not available]

        if missing_deps:
            logger.warning(f"Web interface partially available - missing: {missing_deps}")

        if not deps.get('flask', False):
            logger.error("Flask not available - web interface disabled")
            return False

        # Create Flask application
        app = create_app(config)
        if app is None:
            return False

        # Import agent integrations
        try:
            from ..agents import get_orchestrator, initialize_agents
            from ..services import initialize_services

            # Initialize agents and services
            agents_ready = initialize_agents()
            services_ready = initialize_services()

            if not agents_ready:
                logger.warning("Some agents not available - limited functionality")

            if not services_ready:
                logger.warning("Some services not available - limited functionality")

            logger.info(f"Web interface initialized - Agents: {agents_ready}, Services: {services_ready}")

        except Exception as e:
            logger.error(f"Failed to initialize agent/service integration: {e}")
            # Continue anyway - web interface can still function with limited features

        global _config_loaded
        _config_loaded = True

        return True

    except Exception as e:
        logger.error(f"Web interface initialization failed: {e}")
        return False


def get_web_status() -> Dict[str, Any]:
    """Get current web interface status and availability."""
    deps = check_web_dependencies()

    status = {
        'web_available': deps.get('flask', False),
        'dependencies': deps,
        'app_created': _app_instance is not None,
        'config_loaded': _config_loaded,
        'missing_dependencies': [dep for dep, available in deps.items() if not available]
    }

    # Add agent/service status if available
    try:
        from ..agents import get_services_status as get_agent_status
        status['agents_status'] = get_agent_status()
    except:
        status['agents_status'] = {'available': False}

    try:
        from ..services import get_services_status
        status['services_status'] = get_services_status()
    except:
        status['services_status'] = {'available': False}

    return status


def run_development_server(
        host: str = '127.0.0.1',
        port: int = 5000,
        debug: bool = True,
        auto_reload: bool = True
) -> None:
    """
    Run Flask development server.

    Args:
        host: Host address to bind to
        port: Port number to bind to
        debug: Enable debug mode
        auto_reload: Enable auto-reload on code changes
    """
    app = get_app()

    if app is None:
        logger.error("Cannot start development server - Flask app not available")
        return

    try:
        logger.info(f"Starting development server on http://{host}:{port}")
        logger.info("Press CTRL+C to stop the server")

        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=auto_reload,
            threaded=True
        )

    except KeyboardInterrupt:
        logger.info("Development server stopped")
    except Exception as e:
        logger.error(f"Development server error: {e}")


def get_template_path() -> Path:
    """Get the path to template directory."""
    return Path(__file__).parent / 'templates'


def get_static_path() -> Path:
    """Get the path to static files directory."""
    return Path(__file__).parent / 'static'


def health_check() -> Dict[str, Any]:
    """Check web interface health and dependencies."""
    try:
        deps = check_web_dependencies()
        status = get_web_status()

        # Check template and static directories
        template_path = get_template_path()
        static_path = get_static_path()

        health_status = {
            'status': 'healthy' if deps.get('flask', False) else 'unhealthy',
            'flask_available': deps.get('flask', False),
            'dependencies': deps,
            'app_instance': _app_instance is not None,
            'template_directory': {
                'exists': template_path.exists(),
                'path': str(template_path)
            },
            'static_directory': {
                'exists': static_path.exists(),
                'path': str(static_path)
            },
            'web_status': status,
            'last_check': None  # Will be set by caller if needed
        }

        return health_status

    except Exception as e:
        logger.error(f"Web interface health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'flask_available': False
        }


# Convenience exports for common web operations
__all__ = [
    'create_app',
    'get_app',
    'initialize_web_interface',
    'run_development_server',
    'get_web_status',
    'health_check',
    'check_web_dependencies',
    'get_template_path',
    'get_static_path'
]

# Initialize web interface on import (if dependencies available)
try:
    if check_web_dependencies().get('flask', False):
        initialize_web_interface()
        logger.info("Web interface package initialized successfully")
    else:
        logger.warning("Web interface package loaded with limited functionality")
except Exception as e:
    logger.error(f"Web interface package initialization failed: {e}")
