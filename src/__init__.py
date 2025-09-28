#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Main Package
====================================

Main package initialization for the Socratic RAG Enhanced system.
Provides clean imports and package-level initialization with robust error handling.

This module exposes the core functionality of the system through organized imports,
making it easy for other modules and external code to access the required components.
"""

import sys
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


# ============================================================================
# FALLBACK FUNCTIONS - Define before imports to ensure they always exist
# ============================================================================

def _fallback_get_config():
    """Fallback configuration function"""
    return None


def _fallback_get_logger(name: str = 'fallback'):
    """Fallback logger function"""
    import logging
    return logging.getLogger(name)


def _fallback_get_database():
    """Fallback database function"""
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


def _fallback_init_core_system(config_path: str = None):
    """Fallback core system initialization"""
    print("Warning: Core system initialization not available")
    return None


# ============================================================================
# CORE SYSTEM IMPORTS
# ============================================================================

try:
    # Core infrastructure
    from .core import (
        # System management
        SystemConfig, get_config, get_logger, get_event_bus, DatabaseManager,

        # Configuration and utilities
        DateTimeHelper, FileHelper, ValidationHelper,

        # Exceptions
        SocraticException, ConfigurationError, ValidationError, APIError,
        DatabaseError, CodeGenerationError, TestingError, IDEIntegrationError,
        AuthenticationError, ConflictError,

        # Event system
        Event, EventSystem, initialize_system as init_core_system
    )

    CORE_AVAILABLE = True

    # Use real logger once core is available
    logger = get_logger('package')
    logger.info("Core system imported successfully")

except ImportError as e:
    CORE_AVAILABLE = False
    _import_errors['core'] = str(e)

    # Fallback to basic logging before core is available
    import logging

    logger = logging.getLogger('package.fallback')
    logger.warning(f"Core system import failed: {e}")

    # Assign fallback functions
    get_config = _fallback_get_config
    get_logger = _fallback_get_logger
    init_core_system = _fallback_init_core_system

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
    if CORE_AVAILABLE:
        logger.info("Models imported successfully")

except ImportError as e:
    MODELS_AVAILABLE = False
    _import_errors['models'] = str(e)

    if CORE_AVAILABLE:
        logger.warning(f"Models import failed: {e}")
    else:
        print(f"Warning: Models import failed: {e}")

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
        GeneratedFileRepository, TestResultRepository, ProjectCollaboratorRepository,

        # Schema management
        DatabaseSchema,

        # Base classes
        BaseRepository
    )

    DATABASE_AVAILABLE = True
    if CORE_AVAILABLE:
        logger.info("Database layer imported successfully")

except ImportError as e:
    DATABASE_AVAILABLE = False
    _import_errors['database'] = str(e)

    if CORE_AVAILABLE:
        logger.warning(f"Database import failed: {e}")
    else:
        print(f"Warning: Database import failed: {e}")

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
    if CORE_AVAILABLE:
        logger.info("Utilities imported successfully")

except ImportError as e:
    UTILS_AVAILABLE = False
    _import_errors['utils'] = str(e)

    if CORE_AVAILABLE:
        logger.warning(f"Utils import failed: {e}")
    else:
        print(f"Warning: Utils import failed: {e}")

# ============================================================================
# SERVICES IMPORTS (Optional - graceful degradation)
# ============================================================================

try:
    from . import services
    # Import specific service functions for web app access
    from .services import get_services_status, initialize_all_services

    SERVICES_AVAILABLE = True
    if CORE_AVAILABLE:
        logger.info("Services imported successfully")

except ImportError as e:
    SERVICES_AVAILABLE = False
    _import_errors['services'] = str(e)

    if CORE_AVAILABLE:
        logger.info(f"Services not available (expected during development): {e}")
    else:
        print(f"Info: Services not available: {e}")

    # Assign fallback functions
    get_services_status = _fallback_get_services_status
    initialize_all_services = _fallback_initialize_all_services

# ============================================================================
# AGENTS IMPORTS (Optional - graceful degradation)
# ============================================================================

try:
    from .agents import (
        # Agent coordination
        get_orchestrator, initialize_all_agents, get_agent_status,

        # Agent implementations
        BaseAgent, AgentOrchestrator,
        ProjectManagerAgent, CodeGeneratorAgent, DocumentProcessorAgent,
        ServicesAgent, SocraticCounselorAgent, UserManagerAgent,
        ContextAnalyzerAgent, SystemMonitorAgent
    )

    AGENTS_AVAILABLE = True
    if CORE_AVAILABLE:
        logger.info("Agents imported successfully")

except ImportError as e:
    AGENTS_AVAILABLE = False
    _import_errors['agents'] = str(e)

    if CORE_AVAILABLE:
        logger.info(f"Agents not available (expected during development): {e}")
    else:
        print(f"Info: Agents not available: {e}")

    # Assign fallback functions
    get_orchestrator = _fallback_get_orchestrator
    initialize_all_agents = _fallback_initialize_all_agents
    get_agent_status = _fallback_get_agent_status

# ============================================================================
# WEB INTERFACE IMPORTS (Optional)
# ============================================================================

try:
    from .web import create_app, get_app, run_development_server, get_web_status

    WEB_AVAILABLE = True
    if CORE_AVAILABLE:
        logger.info("Web interface imported successfully")
except ImportError as e:
    WEB_AVAILABLE = False
    _import_errors['web'] = str(e)

    if CORE_AVAILABLE:
        logger.info(f"Web interface not available: {e}")
    else:
        print(f"Info: Web interface not available: {e}")


# ============================================================================
# PACKAGE-LEVEL FUNCTIONS
# ============================================================================

def get_package_info() -> Dict[str, Any]:
    """Get comprehensive package information"""
    return {
        'name': __title__,
        'version': __version__,
        'description': __description__,
        'author': __author__,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'module_availability': {
            'core': CORE_AVAILABLE,
            'models': MODELS_AVAILABLE,
            'database': DATABASE_AVAILABLE,
            'utils': UTILS_AVAILABLE,
            'services': SERVICES_AVAILABLE,
            'agents': AGENTS_AVAILABLE,
            'web': WEB_AVAILABLE
        },
        'import_errors': _import_errors,
        'dependencies_status': _check_optional_dependencies()
    }


def _check_optional_dependencies() -> Dict[str, bool]:
    """Check availability of optional dependencies"""
    dependencies = {}

    # AI/ML dependencies
    try:
        import anthropic
        dependencies['anthropic'] = True
    except ImportError:
        dependencies['anthropic'] = False

    try:
        import sentence_transformers
        dependencies['sentence_transformers'] = True
    except ImportError:
        dependencies['sentence_transformers'] = False

    try:
        import chromadb
        dependencies['chromadb'] = True
    except ImportError:
        dependencies['chromadb'] = False

    # Document processing
    try:
        import PyPDF2
        dependencies['PyPDF2'] = True
    except ImportError:
        dependencies['PyPDF2'] = False

    try:
        from docx import Document
        dependencies['python-docx'] = True
    except ImportError:
        dependencies['python-docx'] = False

    try:
        import openpyxl
        dependencies['openpyxl'] = True
    except ImportError:
        dependencies['openpyxl'] = False

    # Code analysis
    try:
        import black
        dependencies['black'] = True
    except ImportError:
        dependencies['black'] = False

    try:
        import pylint
        dependencies['pylint'] = True
    except ImportError:
        dependencies['pylint'] = False

    # Web and formatting
    try:
        import markdown
        dependencies['markdown'] = True
    except ImportError:
        dependencies['markdown'] = False

    try:
        from bs4 import BeautifulSoup
        dependencies['beautifulsoup4'] = True
    except ImportError:
        dependencies['beautifulsoup4'] = False

    return dependencies


def initialize_system(config_path: Optional[str] = None) -> Optional[Any]:
    """Initialize the complete Socratic system"""
    if not CORE_AVAILABLE:
        if CORE_AVAILABLE:
            logger.error("Cannot initialize system - core modules not available")
        else:
            print("Error: Cannot initialize system - core modules not available")
        return None

    try:
        # Initialize core system
        config = init_core_system(config_path)

        # Initialize services if available
        if SERVICES_AVAILABLE:
            services_result = initialize_all_services()
            logger.info(f"Services initialization: {services_result}")

        # Initialize agents if available
        if AGENTS_AVAILABLE:
            agents_result = initialize_all_agents()
            logger.info(f"Agents initialization: {agents_result}")

        logger.info("System initialization completed successfully")
        return config

    except Exception as e:
        if CORE_AVAILABLE:
            logger.error(f"System initialization failed: {e}")
        else:
            print(f"Error: System initialization failed: {e}")
        return None


def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status"""
    status = {
        'package_info': {
            'version': __version__,
            'title': __title__
        },
        'module_availability': {
            'core': CORE_AVAILABLE,
            'models': MODELS_AVAILABLE,
            'database': DATABASE_AVAILABLE,
            'utils': UTILS_AVAILABLE,
            'services': SERVICES_AVAILABLE,
            'agents': AGENTS_AVAILABLE,
            'web': WEB_AVAILABLE
        },
        'import_errors': _import_errors
    }

    # Add database status if available
    if DATABASE_AVAILABLE:
        try:
            db = get_database()
            if db:
                health = db.health_check() if hasattr(db, 'health_check') else {'status': 'unknown'}
                status['database_available'] = health.get('status') == 'healthy'
                status['database_info'] = health
        except Exception as e:
            status['database_error'] = str(e)

    # Add service status if available
    if SERVICES_AVAILABLE:
        try:
            status['services_available'] = get_services_status()
        except Exception as e:
            status['services_error'] = str(e)

    # Add agent status if available
    if AGENTS_AVAILABLE:
        try:
            orchestrator = get_orchestrator()
            if orchestrator:
                status['agents_available'] = get_agent_status()
            else:
                status['agents_available'] = {'status': 'no_orchestrator'}
        except Exception as e:
            status['agents_error'] = str(e)

    return status


# ============================================================================
# CONVENIENCE IMPORTS - MAIN INTERFACES
# ============================================================================

# Make the most commonly used items available at package level
if CORE_AVAILABLE:
    # Most common core imports - already imported above
    pass

if MODELS_AVAILABLE:
    # Most common model imports - already imported above
    pass

if DATABASE_AVAILABLE:
    # Most common database import - already imported above
    pass

if UTILS_AVAILABLE:
    # Most common utility imports - already imported above
    pass

# ============================================================================
# PACKAGE EXPORTS
# ============================================================================

# Base exports (always available)
__all__ = [
    # Package information
    '__version__', '__title__', '__description__', '__author__',

    # Package-level functions
    'get_package_info', 'initialize_system', 'get_system_status',

    # Availability flags
    'CORE_AVAILABLE', 'MODELS_AVAILABLE', 'DATABASE_AVAILABLE',
    'UTILS_AVAILABLE', 'SERVICES_AVAILABLE', 'AGENTS_AVAILABLE'
]

# Add conditional exports based on what's available
if CORE_AVAILABLE:
    __all__.extend([
        'get_config', 'get_logger', 'SocraticException', 'DateTimeHelper'
    ])

if MODELS_AVAILABLE:
    __all__.extend([
        'Project', 'Module', 'GeneratedFile', 'TestResult', 'ModelFactory'
    ])

if DATABASE_AVAILABLE:
    __all__.extend([
        'get_database', 'DatabaseService'
    ])

if UTILS_AVAILABLE:
    __all__.extend([
        'get_file_processor', 'get_text_processor', 'get_code_analyzer',
        'get_validator', 'get_knowledge_extractor'
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
    logger.info(f"Socratic RAG Enhanced v{__version__} package initialized")
    logger.info(f"Available modules: {[k for k, v in get_system_status()['module_availability'].items() if v]}")

    if _import_errors:
        logger.warning(f"Some modules failed to import: {list(_import_errors.keys())}")
else:
    print(f"Socratic RAG Enhanced v{__version__} package initialized (limited mode)")
    print(f"Import errors: {list(_import_errors.keys())}")
