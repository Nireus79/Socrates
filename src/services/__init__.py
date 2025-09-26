"""
Services Package - External Service Integrations
================================================

This module provides external service integrations for the Socratic RAG Enhanced system.
Handles Claude API, ChromaDB vector storage, Git operations, and IDE integration.

Services:
- ClaudeService: Anthropic Claude API integration
- VectorService: ChromaDB vector database operations
- GitService: Git repository operations and version control
- IDEService: VS Code integration and file synchronization
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Service availability tracking
_available_services = {}
_service_instances = {}


def check_service_availability() -> Dict[str, bool]:
    """Check availability of all external services."""
    availability = {}

    # Check Claude API service
    try:
        from .claude_service import ClaudeService
        availability['claude'] = True
    except ImportError as e:
        logger.warning(f"Claude service unavailable: {e}")
        availability['claude'] = False

    # Check Vector service (ChromaDB)
    try:
        from .vector_service import VectorService
        availability['vector'] = True
    except ImportError as e:
        logger.warning(f"Vector service unavailable: {e}")
        availability['vector'] = False

    # Check Git service
    try:
        from .git_service import GitService
        availability['git'] = True
    except ImportError as e:
        logger.warning(f"Git service unavailable: {e}")
        availability['git'] = False

    # Check IDE service
    try:
        from .ide_service import IDEService
        availability['ide'] = True
    except ImportError as e:
        logger.warning(f"IDE service unavailable: {e}")
        availability['ide'] = False

    global _available_services
    _available_services = availability
    return availability


def get_service(service_name: str) -> Optional[Any]:
    """Get a service instance by name."""
    if service_name not in _available_services:
        check_service_availability()

    if not _available_services.get(service_name, False):
        logger.error(f"Service '{service_name}' is not available")
        return None

    # Return cached instance if exists
    if service_name in _service_instances:
        return _service_instances[service_name]

    # Create new service instance
    try:
        if service_name == 'claude':
            from .claude_service import ClaudeService
            instance = ClaudeService()
        elif service_name == 'vector':
            from .vector_service import VectorService
            instance = VectorService()
        elif service_name == 'git':
            from .git_service import GitService
            instance = GitService()
        elif service_name == 'ide':
            from .ide_service import IDEService
            instance = IDEService()
        else:
            logger.error(f"Unknown service: {service_name}")
            return None

        _service_instances[service_name] = instance
        return instance

    except Exception as e:
        logger.error(f"Failed to create {service_name} service: {e}")
        return None


def get_available_services() -> List[str]:
    """Get list of currently available services."""
    if not _available_services:
        check_service_availability()
    return [name for name, available in _available_services.items() if available]


def initialize_services() -> bool:
    """Initialize all available services."""
    try:
        availability = check_service_availability()
        available_count = sum(availability.values())
        total_count = len(availability)

        logger.info(f"Services initialized: {available_count}/{total_count} available")
        logger.info(f"Available services: {get_available_services()}")

        return available_count > 0

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return False


def get_services_status() -> Dict[str, Any]:
    """Get detailed status of all services."""
    if not _available_services:
        check_service_availability()

    status = {
        'available_services': _available_services.copy(),
        'initialized_services': list(_service_instances.keys()),
        'total_available': sum(_available_services.values()),
        'total_services': len(_available_services)
    }

    return status


def initialize_all_services() -> Dict[str, Any]:
    """Initialize all available services (alias for initialize_services)"""
    try:
        success = initialize_services()
        status = get_services_status()

        return {
            'initialized': status['total_available'],
            'total': status['total_services'],
            'services': get_available_services(),
            'status': 'success' if success else 'partial',
            'details': status
        }

    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        return {
            'initialized': 0,
            'total': 0,
            'services': [],
            'status': 'failed',
            'error': str(e)
        }


# Convenience exports (will be available when services are implemented)
__all__ = [
    'check_service_availability',
    'get_service',
    'get_available_services',
    'initialize_services',
    'initialize_all_services',  # ← ADD THIS
    'get_services_status'
]

# Initialize services on module import
try:
    initialize_services()
except Exception as e:
    logger.warning(f"Service initialization failed: {e}")
    