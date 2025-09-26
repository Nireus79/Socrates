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
        SocraticSystem, get_system, get_config, get_logger, get_event_bus, get_db_manager,

        # Configuration and utilities
        SystemConfig, ConfigManager, LogManager, DateTimeHelper, FileHelper, ValidationHelper,

        # Exceptions
        SocraticException, ConfigurationError, ValidationError, APIError,
        DatabaseError, CodeGenerationError, TestingError, IDEIntegrationError,
        AuthenticationError, ConflictError,

        # Event system
        Event, EventBus, DatabaseManager
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
        ConversationMessage, TechnicalSpecification,

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
        DatabaseService, get_database,

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

    # This will be expanded as we add service modules:
    # from .services import claude_service, vector_service, git_service, ide_service
    SERVICES_AVAILABLE = True
except ImportError:
    # Services not yet implemented - this is expected during development
    pass

# ============================================================================
# AGENTS IMPORTS (Dynamic - will expand as agents are added)
# ============================================================================

AGENTS_AVAILABLE = False
try:
    from . import agents

    # This will be expanded as we add agent modules:
    # from .agents import get_orchestrator, SocraticCounselorAgent, CodeGeneratorAgent, etc.
    AGENTS_AVAILABLE = True
except ImportError:
    # Agents not yet implemented - this is expected during development
    pass

# ============================================================================
# PACKAGE INFORMATION
# ============================================================================

__version__ = "7.2.0"
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


def initialize_system(config_path: Optional[str] = None,
                      auto_initialize: bool = True) -> Optional['SocraticSystem']:
    """Initialize the complete Socratic system"""
    if not CORE_AVAILABLE:
        print("Error: Core system not available - cannot initialize")
        return None

    try:
        if auto_initialize:
            # Get the global system instance (initializes automatically)
            system = get_system()

            # Initialize database if available
            if DATABASE_AVAILABLE:
                get_database()

            logger = get_logger('package')
            logger.info(f"Socratic RAG Enhanced v{__version__} initialized successfully")
            logger.info(f"Components available: {list(k for k, v in AVAILABILITY_STATUS.items() if v)}")

            return system
        else:
            # Manual initialization
            system = SocraticSystem(config_path)
            system.initialize()
            return system

    except Exception as e:
        print(f"Error: System initialization failed: {e}")
        return None


def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status"""
    status = {
        'package_info': get_package_info(),
        'system_initialized': False,
        'database_healthy': False,
        'services_available': {},
        'agents_available': {}
    }

    if CORE_AVAILABLE:
        try:
            system = get_system()
            status['system_initialized'] = system.is_initialized
        except:
            pass

    if DATABASE_AVAILABLE:
        try:
            db = get_database()
            health = db.health_check()
            status['database_healthy'] = health.get('status') == 'healthy'
            status['database_info'] = health
        except:
            pass

    # Add service and agent status as they become available
    if SERVICES_AVAILABLE:
        # This will be expanded as services are implemented
        status['services_available'] = {}

    if AGENTS_AVAILABLE:
        # This will be expanded as agents are implemented
        status['agents_available'] = {}

    return status


# ============================================================================
# CONVENIENCE IMPORTS - MAIN INTERFACES
# ============================================================================

# Make the most commonly used items available at package level
if CORE_AVAILABLE:
    # Most common core imports
    from .core import get_system, get_config, get_logger, SocraticException

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
        'SocraticSystem', 'get_system', 'get_config', 'get_logger', 'get_event_bus', 'get_db_manager',
        'SystemConfig', 'ConfigManager', 'DateTimeHelper', 'FileHelper', 'ValidationHelper',
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
        'get_database', 'DatabaseService', 'UserRepository', 'ProjectRepository'
    ])

if UTILS_AVAILABLE:
    __all__.extend([
        'get_file_processor', 'get_text_processor', 'get_code_analyzer',
        'get_validator', 'get_knowledge_extractor',
        'DocumentInfo', 'TextChunk', 'CodeAnalysisResult'
    ])

# ============================================================================
# PACKAGE INITIALIZATION
# ============================================================================

# Create package-level logger if core is available
if CORE_AVAILABLE:
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
        print(f"\n⚙️  System Config Available: {get_config() is not None}")

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

"""
What src/__init__.py Provides:

📦 **Package Organization**:
- Makes `src/` a proper Python package
- Clean imports for all major components
- Graceful handling of missing/pending components

🔧 **System Management**:
- `initialize_system()` - Complete system setup
- `get_system_status()` - Comprehensive status checking
- `get_package_info()` - Version and component information

📊 **Component Availability Tracking**:
- Tracks which components are loaded successfully
- Handles missing dependencies gracefully
- Reports on optional dependency status

🚀 **Convenience Imports**:
- Most common items available at package level
- `from src import get_logger, Project, get_database`
- Easy access without deep imports

🔍 **Development Support**:
- Debug information printing
- Dependency status checking
- Component availability reporting

Usage Examples:
```python
# Package-level usage
from src import initialize_system, get_package_info
system = initialize_system()
info = get_package_info()

# Component usage
from src import get_logger, Project, get_database
logger = get_logger('my_module')
db = get_database()
project = Project(name="My Project", owner="user")

# Status checking
from src import get_system_status
status = get_system_status()
print(f"System healthy: {status['database_healthy']}")
```

🎯 **Benefits**:
- Clean package structure
- Easy imports for external code
- Graceful degradation during development
- Comprehensive status tracking
- Ready for services/ and agents/ subdirectories
"""