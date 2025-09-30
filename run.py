#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Application Entry Point
==============================================

Main entry point for starting the Socratic RAG Enhanced web application.
Handles system initialization, dependency validation, and Flask server startup.

Usage:
    python run.py [--port PORT] [--debug] [--check-deps] [--headless]
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import webbrowser
from threading import Timer

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup basic logging before imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ============================================================================
# COMPONENT AVAILABILITY TRACKING
# ============================================================================

COMPONENTS_AVAILABLE: Dict[str, bool] = {
    'core': False,
    'database': False,
    'agents': False,
    'services': False,
    'web': False
}

IMPORT_ERRORS: Dict[str, str] = {}


# ============================================================================
# FALLBACK FUNCTIONS - For graceful degradation
# ============================================================================

def _fallback_initialize_system(config_path: Optional[str] = None):
    """Fallback system initialization"""
    print("⚠️ Warning: Core system initialization not available")
    print("   Running in limited mode")
    return None


def _fallback_init_database():
    """Fallback database initialization"""
    print("⚠️ Warning: Database initialization not available")
    return False


def _fallback_get_orchestrator():
    """Fallback orchestrator function"""
    print("⚠️ Warning: Agent orchestrator not available")
    return None


def _fallback_initialize_all_agents():
    """Fallback agents initialization"""
    return {
        'initialized': 0,
        'total': 0,
        'status': 'unavailable',
        'error': 'Agents module not available'
    }


def _fallback_initialize_all_services():
    """Fallback services initialization"""
    return {
        'initialized': 0,
        'status': 'unavailable',
        'error': 'Services module not available'
    }


def _fallback_create_app():
    """Fallback web app creation"""
    print("❌ Error: Web application not available - cannot start server")
    print("   Please ensure Flask and web modules are installed")
    print("   Run: pip install Flask Flask-Login Flask-WTF")
    print("")
    print("   Alternative: Run in headless mode with --headless")
    print("   Example: python run.py --headless")
    print("")
    sys.exit(1)


def _fallback_create_headless_app():
    """Create minimal app when web interface is unavailable - running headless mode"""
    print("⚠️ Running in headless mode - no web interface")
    print("   System functionality available through API only")
    return None


# ============================================================================
# GRACEFUL IMPORTS WITH FALLBACKS
# ============================================================================

# Core system imports
try:
    from src import get_logger  # ✅ FIX: Import from src, not src.core
    from src.core import SystemConfig, initialize_system, cleanup_system

    COMPONENTS_AVAILABLE['core'] = True
except ImportError as e:
    IMPORT_ERRORS['core'] = str(e)


    # ✅ FIX: Define fallback SystemConfig class
    class SystemConfig:
        """Fallback SystemConfig when core is not available"""

        def __init__(self):
            self._config = {}

        def load_config(self, path=None):
            return False

        def get(self, key, default=None):
            return default


    # ✅ FIX: Use proper def instead of lambda (PEP 8: E731)
    def cleanup_system(services=None):
        """Fallback cleanup function"""
        pass


    def get_logger(name: str):
        """Fallback logger function"""
        return logging.getLogger(name)


    initialize_system = _fallback_initialize_system

# Database imports
try:
    from src.database import init_database

    COMPONENTS_AVAILABLE['database'] = True
except ImportError as e:
    IMPORT_ERRORS['database'] = str(e)
    init_database = _fallback_init_database

# Agents imports
try:
    from src.agents import get_orchestrator, initialize_all_agents

    COMPONENTS_AVAILABLE['agents'] = True
except ImportError as e:
    IMPORT_ERRORS['agents'] = str(e)
    get_orchestrator = _fallback_get_orchestrator
    initialize_all_agents = _fallback_initialize_all_agents

# Services imports
try:
    from src.services import initialize_all_services

    COMPONENTS_AVAILABLE['services'] = True
except ImportError as e:
    IMPORT_ERRORS['services'] = str(e)
    initialize_all_services = _fallback_initialize_all_services

# Web interface imports
try:
    from web import create_app

    COMPONENTS_AVAILABLE['web'] = True
except ImportError as e:
    IMPORT_ERRORS['web'] = str(e)
    # Try alternative import path
    try:
        from src.web import create_app

        COMPONENTS_AVAILABLE['web'] = True
    except ImportError as e2:
        IMPORT_ERRORS['web'] = f"Primary: {e}, Alternative: {e2}"
        create_app = _fallback_create_app


# ============================================================================
# DEPENDENCY VALIDATION
# ============================================================================

def check_required_packages() -> List[str]:
    """Check if required Python packages are installed"""
    required_packages = [
        'Flask',
        'PyYAML',
        'requests'
    ]

    optional_packages = [
        'anthropic',
        'chromadb',
        'sentence-transformers',
        'PyPDF2',
        'python-docx',
        'openpyxl',
        'black',
        'pytest'
    ]

    missing_required = []
    missing_optional = []

    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
        except ImportError:
            missing_required.append(package)

    for package in optional_packages:
        try:
            __import__(package.lower().replace('-', '_'))
        except ImportError:
            missing_optional.append(package)

    if missing_required:
        print(f"❌ Missing required packages: {', '.join(missing_required)}")
        print("   Install with: pip install -r requirements.txt")

    if missing_optional:
        print(f"⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("   Some features will be limited")

    return missing_required


def validate_python_version() -> bool:
    """Validate Python version requirements"""
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required. Current version: {sys.version}")
        return False

    if sys.version_info >= (3, 12):
        print(
            f"⚠️  Python {sys.version_info.major}.{sys.version_info.minor} detected. "
            f"Some packages may have compatibility issues."
        )

    return True


def validate_environment() -> bool:
    """Validate environment and configuration"""
    logger = get_logger('run')

    # Check data directory
    data_dir = project_root / 'data'
    if not data_dir.exists():
        logger.info(f"Creating data directory: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)

    # Check config file
    config_file = project_root / 'config.yaml'
    if not config_file.exists():
        logger.warning(f"Config file not found: {config_file}")
        logger.warning("System will use default configuration")

    # Check critical environment variables
    api_key = os.getenv('API_KEY_CLAUDE') or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.warning("⚠️ No Claude API key found in environment variables")
        logger.warning("   Set API_KEY_CLAUDE or ANTHROPIC_API_KEY to enable AI features")

    return True


# ============================================================================
# SYSTEM INITIALIZATION
# ============================================================================

def initialize_application(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Initialize the complete application system

    Args:
        config_path: Optional path to config file

    Returns:
        Dict with initialization status
    """
    logger = get_logger('run')
    logger.info("=" * 70)
    logger.info("Starting Socratic RAG Enhanced Application")
    logger.info("=" * 70)

    init_status = {
        'success': False,
        'services': None,
        'database': False,
        'agents': None,
        'external_services': None,
        'components': COMPONENTS_AVAILABLE.copy(),
        'errors': []
    }

    # 1. Initialize core system
    if COMPONENTS_AVAILABLE['core']:
        logger.info("Initializing core system...")
        try:
            services = initialize_system(config_path)
            if services:
                init_status['services'] = services
                logger.info("✅ Core system initialized")
            else:
                init_status['errors'].append("Core system initialization returned None")
                logger.warning("⚠️ Core system initialization returned None")
        except Exception as e:
            error_msg = f"Core system initialization failed: {e}"
            init_status['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
    else:
        logger.warning("⚠️ Core system not available")

    # 2. Initialize database
    if COMPONENTS_AVAILABLE['database']:
        logger.info("Initializing database...")
        try:
            db_success = init_database()
            init_status['database'] = db_success
            if db_success:
                logger.info("✅ Database initialized")
            else:
                logger.warning("⚠️ Database initialization failed")
        except Exception as e:
            error_msg = f"Database initialization failed: {e}"
            init_status['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
    else:
        logger.warning("⚠️ Database system not available")

    # 3. Initialize agents
    if COMPONENTS_AVAILABLE['agents']:
        logger.info("Initializing agent system...")
        try:
            agents_result = initialize_all_agents()
            init_status['agents'] = agents_result
            if agents_result.get('status') == 'success':
                logger.info(
                    f"✅ Agents initialized: {agents_result.get('initialized', 0)} active"
                )
            else:
                logger.warning(f"⚠️ Agent initialization incomplete: {agents_result}")
        except Exception as e:
            error_msg = f"Agent initialization failed: {e}"
            init_status['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
    else:
        logger.warning("⚠️ Agent system not available")

    # 4. Initialize external services
    if COMPONENTS_AVAILABLE['services']:
        logger.info("Initializing external services...")
        try:
            services_result = initialize_all_services()
            init_status['external_services'] = services_result
            if services_result.get('status') in ['success', 'partial']:
                logger.info(
                    f"✅ External services: {services_result.get('initialized', 0)} available"
                )
            else:
                logger.warning(f"⚠️ External services limited: {services_result}")
        except Exception as e:
            error_msg = f"External services initialization failed: {e}"
            init_status['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
    else:
        logger.warning("⚠️ External services not available")

    # Determine overall success
    init_status['success'] = (
            COMPONENTS_AVAILABLE['core'] and
            init_status['services'] is not None
    )

    # Print summary
    logger.info("=" * 70)
    logger.info("Initialization Summary:")
    logger.info(f"  Core System:        {'✅' if COMPONENTS_AVAILABLE['core'] else '❌'}")
    logger.info(f"  Database:           {'✅' if init_status['database'] else '❌'}")
    logger.info(f"  Agent System:       {'✅' if COMPONENTS_AVAILABLE['agents'] else '❌'}")
    logger.info(f"  External Services:  {'✅' if COMPONENTS_AVAILABLE['services'] else '❌'}")
    logger.info(f"  Web Interface:      {'✅' if COMPONENTS_AVAILABLE['web'] else '❌'}")

    if init_status['errors']:
        logger.warning(f"  Errors: {len(init_status['errors'])}")
        for error in init_status['errors']:
            logger.warning(f"    - {error}")

    logger.info("=" * 70)

    return init_status


# ============================================================================
# WEB SERVER
# ============================================================================
def open_browser():
    webbrowser.open('http://127.0.0.1:5000')


def start_web_server(
        port: int = 5000,
        debug: bool = False,
        host: str = '0.0.0.0'
) -> None:
    """Start the Flask web server

    Args:
        port: Port number to run on
        debug: Enable debug mode
        host: Host address to bind to
    """
    logger = get_logger('run')

    if not COMPONENTS_AVAILABLE['web']:
        logger.error("❌ Web interface not available - cannot start server")
        logger.error("   Install requirements: pip install Flask Flask-Login Flask-WTF")
        sys.exit(1)

    try:
        logger.info(f"Starting web server on {host}:{port}")
        logger.info(f"Debug mode: {'enabled' if debug else 'disabled'}")
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"🌐 Socratic RAG Enhanced is running!")
        logger.info(f"📍 Access the application at: http://localhost:{port}")
        logger.info(f"📖 Documentation: http://localhost:{port}/docs")
        logger.info(f"🛠️  API: http://localhost:{port}/api")
        logger.info("=" * 70)
        logger.info("")

        # Create and run Flask app
        app = create_app()
        Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
        app.run(host=host, port=port, debug=debug, use_reloader=False)

    except Exception as e:
        logger.error(f"❌ Failed to start web server: {e}")
        sys.exit(1)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main application entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Socratic RAG Enhanced - AI-Powered Project Development'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run the web server on (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check dependencies and exit'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (no web interface)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to config file (default: config.yaml)'
    )

    args = parser.parse_args()

    # Validate Python version
    if not validate_python_version():
        sys.exit(1)

    # Check dependencies if requested
    if args.check_deps:
        print("Checking dependencies...")
        print("")
        missing = check_required_packages()
        print("")

        if missing:
            print(f"❌ Missing {len(missing)} required packages")
            print("   Run: pip install -r requirements.txt")
            sys.exit(1)
        else:
            print("✅ All required dependencies are installed")

        print("")
        print("Component availability:")
        for component, available in COMPONENTS_AVAILABLE.items():
            status = "✅ Available" if available else "❌ Not available"
            print(f"  {component.capitalize():15} {status}")

        if IMPORT_ERRORS:
            print("")
            print("Import errors:")
            for component, error in IMPORT_ERRORS.items():
                print(f"  {component}: {error}")

        sys.exit(0)

    # Validate environment
    validate_environment()

    # Initialize application
    init_status = initialize_application(args.config)

    if not init_status['success']:
        print("")
        print("❌ Application initialization failed")
        print("   Some core components are unavailable")
        print("   Run with --check-deps to see details")
        print("")

        if not args.headless:
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)

    # Start server or run headless
    if args.headless:
        logger = get_logger('run')
        logger.info("Running in headless mode - press Ctrl+C to exit")
        try:
            # Keep the application running
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
    else:
        start_web_server(port=args.port, debug=args.debug)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
