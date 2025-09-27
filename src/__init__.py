#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Main Package
====================================

Main package initialization for the Socratic RAG Enhanced system.
Provides clean imports and package-level initialization.

This module exposes the core functionality of the system through organized imports,
making it easy for other modules and external code to access the required components.
"""

import sys
import warnings
from typing import Optional, Dict, Any

# Suppress specific warnings that might occur during imports
warnings.filterwarnings('ignore', category=UserWarning, module='sentence_transformers')
warnings.filterwarnings('ignore', category=FutureWarning, module='transformers')

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
except ImportError as e:
    print(f"Warning: Core system import failed: {e}")
    CORE_AVAILABLE = False

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
    print(f"Warning: Models import failed: {e}")
    MODELS_AVAILABLE = False

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
except ImportError as e:
    print(f"Warning: Database import failed: {e}")
    DATABASE_AVAILABLE = False

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
    print(f"Warning: Utils import failed: {e}")
    UTILS_AVAILABLE = False

# ============================================================================
# SERVICES IMPORTS (Dynamic - will expand as services are added)
# ============================================================================

SERVICES_AVAILABLE = False
try:
    from . import services
    # Import specific service functions for web app access
    from .services import get_services_status, initialize_all_services

    SERVICES_AVAILABLE = True
except ImportError:
    # Services not yet implemented - this is expected during development
    SERVICES_AVAILABLE = False


    # Define fallback functions
    def get_services_status():
        return {'available_services': {}, 'total_available': 0, 'status': 'unavailable'}


    def initialize_all_services():
        return {'initialized': 0, 'status': 'failed', 'error': 'Services not available'}

# ============================================================================
# AGENTS IMPORTS (Dynamic - will expand as agents are added)
# ============================================================================

AGENTS_AVAILABLE = False
try:
    from . import agents
    # Import specific agent functions for web app access
    from .agents import get_orchestrator, initialize_all_agents

    AGENTS_AVAILABLE = True
except ImportError:
    # Agents not yet implemented - this is expected during development
    AGENTS_AVAILABLE = False


    # Define fallback functions
    def get_orchestrator():
        return None


    def initialize_all_agents():
        return {'initialized': 0, 'status': 'failed', 'error': 'Agents not available'}

# ============================================================================
# PACKAGE INFORMATION
# ============================================================================

__version__ = "7.3.0"
__title__ = "Socratic RAG Enhanced"
__description__ = "Complete Socratic questioning system with modular agent architecture"
__author__ = "Socratic RAG Development Team"

# Availability status
AVAILABILITY_STATUS = {
    'core': CORE_AVAILABLE,
    'models': MODELS_AVAILABLE,
    'database': DATABASE_AVAILABLE,
    'utils': UTILS_AVAILABLE,
    'services': SERVICES_AVAILABLE,
    'agents': AGENTS_AVAILABLE
}


# ============================================================================
# PACKAGE-LEVEL FUNCTIONS
# ============================================================================

def get_package_info() -> Dict[str, Any]:
    """Get package information and availability status"""
    return {
        'version': __version__,
        'title': __title__,
        'description': __description__,
        'components': AVAILABILITY_STATUS,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
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


def initialize_system(config_path: Optional[str] = None) -> Optional[SystemConfig]:
    """Initialize the complete Socratic system"""
    if not CORE_AVAILABLE:
        print("Error: Core system not available - cannot initialize")
        return None

    try:
        # Initialize core system
        if init_core_system:
            success = init_core_system(config_path or "config.yaml")
            if not success:
                print("Error: Core system initialization failed")
                return None

        # Get the global system instance
        system = get_config()

        # Initialize database if available
        if DATABASE_AVAILABLE:
            try:
                get_database()
            except Exception as e:
                print(f"Warning: Database initialization failed: {e}")

        # Initialize services if available
        if SERVICES_AVAILABLE:
            try:
                initialize_all_services()
            except Exception as e:
                print(f"Warning: Services initialization failed: {e}")

        # Initialize agents if available
        if AGENTS_AVAILABLE:
            try:
                initialize_all_agents()
            except Exception as e:
                print(f"Warning: Agents initialization failed: {e}")

        if CORE_AVAILABLE:
            logger = get_logger('package')
            logger.info(f"Socratic RAG Enhanced v{__version__} initialized successfully")
            logger.info(f"Components available: {list(k for k, v in AVAILABILITY_STATUS.items() if v)}")

        return system

    except Exception as e:
        print(f"Error: System initialization failed: {e}")
        return None


def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status"""
    status = {
        'package_info': get_package_info(),
        'system_initialized': CORE_AVAILABLE,
        'database_healthy': False,
        'services_available': {},
        'agents_available': {}
    }

    if DATABASE_AVAILABLE:
        try:
            db = get_database()
            health = db.health_check()
            status['database_healthy'] = health.get('status') == 'healthy'
            status['database_info'] = health
        except Exception as e:
            status['database_error'] = str(e)

    # Add service status
    if SERVICES_AVAILABLE:
        try:
            status['services_available'] = get_services_status()
        except Exception as e:
            status['services_error'] = str(e)

    # Add agent status
    if AGENTS_AVAILABLE:
        try:
            orchestrator = get_orchestrator()
            if orchestrator:
                status['agents_available'] = orchestrator.get_agent_status()
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
    # Most common core imports
    from .core import get_config, get_logger, SocraticException

if MODELS_AVAILABLE:
    # Most common model imports
    from .models import Project, Module, GeneratedFile, TestResult, ModelFactory

if DATABASE_AVAILABLE:
    # Most common database import
    from .database import get_database

if UTILS_AVAILABLE:
    # Most common utility imports
    from .utils import (
        get_file_processor, get_text_processor, get_code_analyzer,
        get_validator, get_knowledge_extractor
    )

# ============================================================================
# PACKAGE EXPORTS
# ============================================================================

__all__ = [
    # Package information
    '__version__', '__title__', '__description__', '__author__',

    # Package-level functions
    'get_package_info', 'initialize_system', 'get_system_status',

    # Availability flags
    'AVAILABILITY_STATUS',
]

# Conditionally add exports based on what's available
if CORE_AVAILABLE:
    __all__.extend([
        'SystemConfig', 'get_config', 'get_logger', 'get_event_bus',
        'DateTimeHelper', 'FileHelper', 'ValidationHelper',
        'SocraticException', 'ValidationError', 'DatabaseError', 'APIError'
    ])

if MODELS_AVAILABLE:
    __all__.extend([
        'Project', 'Module', 'GeneratedFile', 'TestResult', 'User',
        'ProjectPhase', 'ProjectStatus', 'FileType', 'TestType', 'UserRole',
        'ModelFactory', 'ModelValidator'
    ])

if DATABASE_AVAILABLE:
    __all__.extend([
        'get_database', 'get_repository_manager', 'DatabaseService',
        'UserRepository', 'ProjectRepository'
    ])

if UTILS_AVAILABLE:
    __all__.extend([
        'get_file_processor', 'get_text_processor', 'get_code_analyzer',
        'get_validator', 'get_knowledge_extractor',
        'DocumentInfo', 'TextChunk', 'CodeAnalysisResult'
    ])

if SERVICES_AVAILABLE:
    __all__.extend([
        'get_services_status', 'initialize_all_services'
    ])

if AGENTS_AVAILABLE:
    __all__.extend([
        'get_orchestrator', 'initialize_all_agents'
    ])

# ============================================================================
# PACKAGE INITIALIZATION
# ============================================================================

# Create package-level logger if core is available
if CORE_AVAILABLE:
    try:
        _package_logger = get_logger('package')
        _package_logger.info(f"Socratic RAG Enhanced v{__version__} package loaded")

        # Log component availability
        available_components = [name for name, status in AVAILABILITY_STATUS.items() if status]
        unavailable_components = [name for name, status in AVAILABILITY_STATUS.items() if not status]

        if available_components:
            _package_logger.info(f"Available components: {', '.join(available_components)}")

        if unavailable_components:
            _package_logger.info(f"Pending components: {', '.join(unavailable_components)}")

        # Check for missing critical dependencies
        deps = _check_optional_dependencies()
        missing_critical = []

        if not deps.get('anthropic', False):
            missing_critical.append('anthropic (Claude API)')

        if missing_critical:
            _package_logger.warning(f"Missing critical dependencies: {', '.join(missing_critical)}")
    except Exception as e:
        print(f"Warning: Package logging failed: {e}")

else:
    print(f"Socratic RAG Enhanced v{__version__} package loaded (core system unavailable)")


# ============================================================================
# DEVELOPMENT AND DEBUG INFORMATION
# ============================================================================

def _print_debug_info():
    """Print debug information (for development use)"""
    print(f"\n🔧 Socratic RAG Enhanced v{__version__} - Debug Info")
    print("=" * 50)

    print("\n📦 Component Status:")
    for component, available in AVAILABILITY_STATUS.items():
        status = "✅" if available else "🔄"
        print(f"  {status} {component}")

    if CORE_AVAILABLE:
        try:
            print(f"\n⚙️  System Config Available: {get_config() is not None}")
        except:
            print(f"\n⚙️  System Config Available: Error accessing config")

    print(f"\n🐍 Python Version: {sys.version}")

    deps = _check_optional_dependencies()
    available_deps = [name for name, status in deps.items() if status]
    missing_deps = [name for name, status in deps.items() if not status]

    if available_deps:
        print(f"\n✅ Available Dependencies: {', '.join(available_deps)}")

    if missing_deps:
        print(f"\n⚠️  Missing Dependencies: {', '.join(missing_deps)}")

    print("\n" + "=" * 50)


# Show debug info if run directly or in debug mode
if __name__ == "__main__" or getattr(sys, '_called_from_test', False):
    _print_debug_info()
