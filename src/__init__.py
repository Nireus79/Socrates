#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Main Package with ServiceContainer Architecture
=======================================================================

Main package initialization for the Socratic RAG Enhanced system.
Uses ServiceContainer pattern for clean dependency injection.

This module exposes the core functionality through organized imports,
making it easy for other modules to access configured service instances.
"""

import warnings
from typing import Optional, Dict, Any

# Package metadata
__version__ = "7.2.0"
__title__ = "Socratic RAG Enhanced"
__description__ = "AI-powered project development through Socratic questioning"
__author__ = "Socratic RAG Development Team"

# Suppress specific warnings that might occur during imports
warnings.filterwarnings('ignore', category=UserWarning, module='sentence_transformers')
warnings.filterwarnings('ignore', category=FutureWarning, module='transformers')

# Module availability tracking
CORE_AVAILABLE = False
MODELS_AVAILABLE = False
DATABASE_AVAILABLE = False
UTILS_AVAILABLE = False
SERVICES_AVAILABLE = False
AGENTS_AVAILABLE = False

# Import error tracking
_import_errors = {}

# Global service container instance
_services: Optional['ServiceContainer'] = None


# ============================================================================
# FALLBACK FUNCTIONS - For when services aren't available
# ============================================================================

def _fallback_get_services():
    """Fallback when services not available"""
    return None


def _fallback_initialize_system():
    """Fallback system initialization"""
    print("Warning: Core system initialization not available")
    return None


def _fallback_get_services_status():
    """Fallback services status function"""
    return {
        'available_services': {},
        'total_available': 0,
        'status': 'unavailable',
        'error': 'Services module not available'
    }


def _fallback_initialize_all_services():
    """Fallback services initialization function"""
    return {
        'initialized': 0,
        'status': 'failed',
        'error': 'Services module not available'
    }


def _fallback_get_orchestrator():
    """Fallback orchestrator function"""
    return None


def _fallback_initialize_all_agents():
    """Fallback agents initialization function"""
    return {
        'initialized': 0,
        'total': 0,
        'agents': [],
        'status': 'failed',
        'error': 'Agents module not available'
    }


def _fallback_get_agent_status():
    """Fallback agent status function"""
    return {
        'total_available': 0,
        'agents': {},
        'orchestrator_available': False,
        'error': 'Agents module not available'
    }


def _fallback_get_database():
    """Fallback database function"""
    return None


# ============================================================================
# CORE SYSTEM IMPORTS
# ============================================================================

try:
    # Core infrastructure with ServiceContainer
    from .core import (
        # Service Container and Factory
        ServiceContainer, ServiceFactory, initialize_system, cleanup_system,

        # Core Classes
        SystemConfig, SystemLogger, EventSystem, DatabaseManager,

        # Configuration and utilities
        DateTimeHelper, FileHelper, ValidationHelper,

        # Exceptions
        SocraticException, ConfigurationError, ValidationError, APIError,
        DatabaseError, CodeGenerationError, TestingError, IDEIntegrationError,
        AuthenticationError, ConflictError, ServiceError, AgentError,

        # Event system
        Event, EventBus
    )

    CORE_AVAILABLE = True

except ImportError as e:
    CORE_AVAILABLE = False
    _import_errors['core'] = str(e)

    class ServiceContainer:
        """Fallback ServiceContainer when core is not available"""

        def __init__(self):
            self.config: Optional[Any] = None
            self.logger_system: Optional[Any] = None
            self.event_system: Optional[Any] = None
            self.db_manager: Optional[Any] = None

        def get_logger(self, name: str):
            import logging
            return logging.getLogger(name)

        def get_config(self):
            return {}

        def get_event_bus(self):
            return None

        def get_db_manager(self):
            return None


    # Assign fallback functions
    initialize_system = _fallback_initialize_system
    cleanup_system = lambda services: None

# ============================================================================
# DATA MODELS IMPORTS
# ============================================================================

try:
    # Core data models
    from .models import (
        # Main entities
        Project, Module, GeneratedFile, TestResult, User, Collaborator,
        ConversationMessage, TechnicalSpec,

        # Enums
        ProjectPhase, ProjectStatus, ModuleStatus, ModuleType, Priority, RiskLevel,
        FileType, FileStatus, TestType, TestStatus, UserRole,

        # Utilities
        ModelValidator, ModelFactory
    )

    MODELS_AVAILABLE = True

except ImportError as e:
    MODELS_AVAILABLE = False
    _import_errors['models'] = str(e)

# ============================================================================
# DATABASE IMPORTS
# ============================================================================

try:
    # Database layer
    from .database import (
        # Main service
        DatabaseService, get_database, get_repository_manager,

        # Repositories
        UserRepository, ProjectRepository, ModuleRepository,
        GeneratedFileRepository,
        ProjectCollaboratorRepository,

        # Schema management
        # DatabaseSchema, TestResultRepository,

        # Base classes
        BaseRepository
    )

    DATABASE_AVAILABLE = True

except ImportError as e:
    DATABASE_AVAILABLE = False
    _import_errors['database'] = str(e)

    # Assign fallback function
    get_database = _fallback_get_database

# ============================================================================
# UTILITIES IMPORTS
# ============================================================================

try:
    # Processing utilities
    from .utils import (
        # Main processors
        FileProcessor, TextProcessor, CodeAnalyzer, ExtendedValidator, KnowledgeExtractor,

        # Data structures
        DocumentInfo, TextChunk, CodeAnalysisResult,

        # Factory and convenience functions
        UtilityFactory,
        get_file_processor, get_text_processor, get_code_analyzer,
        get_validator, get_knowledge_extractor
    )

    UTILS_AVAILABLE = True

except ImportError as e:
    UTILS_AVAILABLE = False
    _import_errors['utils'] = str(e)

# ============================================================================
# SERVICES IMPORTS (Optional - graceful degradation)
# ============================================================================

try:
    from .services import (
        initialize_all_services, get_services_status
    )

    SERVICES_AVAILABLE = True

except ImportError as e:
    SERVICES_AVAILABLE = False
    _import_errors['services'] = str(e)

    # Assign fallback functions
    initialize_all_services = _fallback_initialize_all_services
    get_services_status = _fallback_get_services_status

# ============================================================================
# AGENTS IMPORTS (Optional - graceful degradation)
# ============================================================================

try:
    from .agents import (
        get_orchestrator, initialize_all_agents, get_agent_status
    )

    AGENTS_AVAILABLE = True

except ImportError as e:
    AGENTS_AVAILABLE = False
    _import_errors['agents'] = str(e)

    # Assign fallback functions
    get_orchestrator = _fallback_get_orchestrator
    initialize_all_agents = _fallback_initialize_all_agents
    get_agent_status = _fallback_get_agent_status


# ============================================================================
# PACKAGE-LEVEL FUNCTIONS
# ============================================================================

def get_package_info() -> Dict[str, Any]:
    """Get package information and status"""
    return {
        'name': __title__,
        'version': __version__,
        'description': __description__,
        'author': __author__,
        'module_availability': {
            'core': CORE_AVAILABLE,
            'models': MODELS_AVAILABLE,
            'database': DATABASE_AVAILABLE,
            'utils': UTILS_AVAILABLE,
            'services': SERVICES_AVAILABLE,
            'agents': AGENTS_AVAILABLE
        },
        'import_errors': _import_errors.copy()
    }


def get_system_status() -> Dict[str, Any]:
    """Get detailed system status"""
    status = get_package_info()

    # ✅ FIX: Properly check _services and its attributes with type assertion
    if _services is not None:
        status['services_initialized'] = True
        # Type assertion to help IDE understand _services has these attributes
        assert isinstance(_services, ServiceContainer)
        status['service_container'] = {
            'config_loaded': _services.config is not None,
            'logger_system': _services.logger_system is not None,
            'event_system': _services.event_system is not None,
            'db_manager': _services.db_manager is not None
        }
    else:
        status['services_initialized'] = False
        status['service_container'] = None

    return status


def get_services() -> Optional[ServiceContainer]:
    """Get the global service container instance"""
    return _services


def initialize_package(config_path: Optional[str] = None) -> Optional[ServiceContainer]:
    """Initialize the package with services"""
    global _services

    if not CORE_AVAILABLE:
        print("Warning: Core system not available, cannot initialize services")
        return None

    try:
        _services = initialize_system(config_path)

        # Log successful initialization
        if _services:
            logg = _services.get_logger('package')
            logg.info(f"Socratic RAG Enhanced v{__version__} package initialized")
            logg.info(f"Available modules: {[k for k, v in get_system_status()['module_availability'].items() if v]}")

            if _import_errors:
                logg.warning(f"Some modules failed to import: {list(_import_errors.keys())}")

        return _services

    except Exception as e:
        print(f"Package initialization failed: {e}")
        return None


def cleanup_package():
    """Cleanup package resources"""
    global _services

    if _services is not None and CORE_AVAILABLE:
        try:
            cleanup_system(_services)
            _services = None
        except Exception as e:
            print(f"Package cleanup failed: {e}")


# ============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS
# ============================================================================

def get_logger(name: str):
    """Backward compatibility function for getting logger"""
    # ✅ FIX: Proper None check and type handling
    if _services is not None:
        return _services.get_logger(name)
    else:
        # Fallback to basic logging
        import logging
        return logging.getLogger(name)


def get_config():
    """Backward compatibility function for getting config"""
    # ✅ FIX: Proper None check and type handling
    if _services is not None:
        return _services.get_config()
    else:
        # Return empty dict as fallback
        return {}


def get_event_bus():
    """Backward compatibility function for getting event bus"""
    # ✅ FIX: Proper None check
    if _services is not None:
        return _services.get_event_bus()
    else:
        return None


def get_db_manager():
    """Backward compatibility function for getting database manager"""
    # ✅ FIX: Proper None check
    if _services is not None:
        return _services.get_db_manager()
    else:
        return None


# ============================================================================
# MODULE EXPORTS
# ============================================================================

# Base exports (always available)
__all__ = [
    # Package information
    '__version__', '__title__', '__description__', '__author__',

    # Package-level functions
    'get_package_info', 'get_system_status', 'get_services',
    'initialize_package', 'cleanup_package',

    # Service Container functions
    'initialize_system', 'cleanup_system',

    # Backward compatibility functions
    'get_logger', 'get_config', 'get_event_bus', 'get_db_manager',

    # Availability flags
    'CORE_AVAILABLE', 'MODELS_AVAILABLE', 'DATABASE_AVAILABLE',
    'UTILS_AVAILABLE', 'SERVICES_AVAILABLE', 'AGENTS_AVAILABLE',

    # Backward compatibility functions
    'get_logger', 'get_config', 'get_event_bus', 'get_db_manager',
]

# Add conditional exports based on what's available
if CORE_AVAILABLE:
    __all__.extend([
        'ServiceContainer', 'ServiceFactory', 'SystemConfig', 'SystemLogger',
        'EventSystem', 'DatabaseManager', 'Event', 'EventBus',
        'SocraticException', 'ConfigurationError', 'ValidationError',
        'DateTimeHelper', 'FileHelper', 'ValidationHelper'
    ])

if MODELS_AVAILABLE:
    __all__.extend([
        'Project', 'Module', 'GeneratedFile', 'TestResult', 'User',
        'ProjectPhase', 'ProjectStatus', 'ModuleStatus', 'ModuleType',
        'Priority', 'RiskLevel', 'FileType', 'FileStatus', 'TestType',
        'TestStatus', 'UserRole', 'ModelFactory'
    ])

if DATABASE_AVAILABLE:
    __all__.extend([
        'get_database', 'DatabaseService', 'DatabaseSchema'
    ])

if UTILS_AVAILABLE:
    __all__.extend([
        'get_file_processor', 'get_text_processor', 'get_code_analyzer',
        'get_validator', 'get_knowledge_extractor', 'DocumentInfo',
        'TextChunk', 'CodeAnalysisResult'
    ])

if SERVICES_AVAILABLE:
    __all__.extend([
        'get_services_status', 'initialize_all_services'
    ])

if AGENTS_AVAILABLE:
    __all__.extend([
        'get_orchestrator', 'initialize_all_agents', 'get_agent_status'
    ])

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Log initialization status
if CORE_AVAILABLE:
    # Don't auto-initialize services here, let the user do it explicitly
    print(f"Socratic RAG Enhanced v{__version__} package loaded")
    print(f"Available modules: {[k for k, v in get_package_info()['module_availability'].items() if v]}")

    if _import_errors:
        print(f"Import warnings: {list(_import_errors.keys())}")
else:
    print(f"Socratic RAG Enhanced v{__version__} package loaded (limited mode)")
    print(f"Import errors: {list(_import_errors.keys())}")

# Auto-initialize services only if running as main module
if __name__ == "__main__":
    print("Initializing services for testing...")
    services = initialize_package()
    if services:
        print("✅ Package initialization successful")

        # Basic functionality test
        logger = services.get_logger('test')
        logger.info("Package test successful")

        cleanup_package()
    else:
        print("❌ Package initialization failed")
