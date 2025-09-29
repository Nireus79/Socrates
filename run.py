#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Main Application Entry Point
Version: 7.3.0

This is the single entry point for the Socratic RAG Enhanced system.
Initializes all components, agents, services, and the web interface with graceful degradation.
"""

import sys
import signal
import logging
import argparse
import webbrowser
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Track what's available
COMPONENTS_AVAILABLE = {
    'core': False,
    'database': False,
    'agents': False,
    'services': False,
    'web': False
}

# Store import errors for debugging
IMPORT_ERRORS = {}


# ============================================================================
# FALLBACK FUNCTIONS - Define before imports
# ============================================================================

def _fallback_initialize_system(config_path: str = None) -> bool:
    """Fallback system initialization"""
    print("⚠️  Core system not available - running in minimal mode")
    return True


def _fallback_init_database() -> bool:
    """Fallback database initialization"""
    print("⚠️  Database not available - some features will be limited")
    return True


def _fallback_initialize_all_agents() -> Dict[str, Any]:
    """Fallback agents initialization"""
    return {'initialized': 0, 'status': 'unavailable', 'error': 'Agents not available'}


def _fallback_get_orchestrator():
    """Fallback orchestrator function"""
    return None


def _fallback_initialize_all_services() -> Dict[str, Any]:
    """Fallback services initialization"""
    return {'initialized': 0, 'status': 'unavailable', 'error': 'Services not available'}


def _fallback_create_app(**kwargs):
    """Fallback web app creation"""
    print("⚠️  Web interface not available - running headless mode")
    return None


# ============================================================================
# GRACEFUL IMPORTS WITH FALLBACKS
# ============================================================================

# Core system imports
try:
    from src.core import (
        SystemConfig, get_logger, initialize_system, cleanup_system
    )

    COMPONENTS_AVAILABLE['core'] = True
except ImportError as e:
    IMPORT_ERRORS['core'] = str(e)
    initialize_system = _fallback_initialize_system
    cleanup_system = lambda: None
    get_logger = lambda name: logging.getLogger(name)

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
            f"⚠️  Python {sys.version_info.major}.{sys.version_info.minor} detected. Some packages may have compatibility issues.")

    return True


def check_file_system() -> bool:
    """Check file system requirements"""
    errors = []

    # Check required directories
    required_dirs = ['src', 'data']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            if dir_name == 'data':
                # Create data directory if it doesn't exist
                dir_path.mkdir(exist_ok=True)
                print(f"📁 Created {dir_name} directory")
            else:
                errors.append(f"Required directory '{dir_name}' not found")

    # Check configuration file
    config_file = Path('config.yaml')
    if not config_file.exists():
        print("⚠️  Configuration file 'config.yaml' not found - using defaults")

    # Check requirements.txt
    requirements_file = Path('requirements.txt')
    if not requirements_file.exists():
        print("⚠️  Requirements file 'requirements.txt' not found")

    if errors:
        print("❌ File system check failed:")
        for error in errors:
            print(f"   • {error}")
        return False

    return True


# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class SocraticRAGApplication:
    """Main application class for Socratic RAG Enhanced"""

    def __init__(self, config_path: Optional[str] = None, debug: bool = False):
        self.config_path = config_path or "config.yaml"
        self.debug = debug
        self.app = None
        self.config = None
        self.logger = None
        self.orchestrator = None
        self.shutdown_handlers = []
        self.running_components = []

    def initialize(self) -> bool:
        """Initialize all system components with graceful degradation"""
        try:
            print("🚀 Starting Socratic RAG Enhanced v7.3.0...")

            # Track successful initializations
            success_count = 0
            total_attempts = 0

            # 1. Initialize core system
            print("📋 Initializing core system...")
            total_attempts += 1
            try:
                if COMPONENTS_AVAILABLE['core']:
                    success = initialize_system(self.config_path)
                    if success:
                        self.config = SystemConfig() if COMPONENTS_AVAILABLE['core'] else None
                        self.logger = get_logger(__name__)
                        self.logger.info("Core system initialized successfully")
                        self.running_components.append('core')
                        success_count += 1
                    else:
                        print("⚠️  Core system initialization failed - continuing with limited functionality")
                else:
                    print("⚠️  Core system not available - running in minimal mode")
            except Exception as e:
                print(f"⚠️  Core system error: {e}")

            # 2. Initialize database
            print("🗄️ Initializing database...")
            total_attempts += 1
            try:
                if COMPONENTS_AVAILABLE['database']:
                    init_database()
                    if self.logger:
                        self.logger.info("Database initialized successfully")
                    else:
                        print("✅ Database initialized successfully")
                    self.running_components.append('database')
                    success_count += 1
                else:
                    print("⚠️  Database not available - some features will be limited")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Database initialization failed: {e}")
                else:
                    print(f"⚠️  Database initialization failed: {e}")

            # 3. Initialize services
            print("🌐 Initializing external services...")
            total_attempts += 1
            try:
                if COMPONENTS_AVAILABLE['services']:
                    service_status = initialize_all_services()
                    if service_status.get('initialized', 0) > 0:
                        if self.logger:
                            self.logger.info(f"Services initialized: {service_status}")
                        else:
                            print(f"✅ Services initialized: {service_status}")
                        self.running_components.append('services')
                        success_count += 1
                    else:
                        print("⚠️  No external services initialized - running in limited mode")
                else:
                    print("⚠️  Services not available - running in limited mode")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Service initialization failed: {e}")
                else:
                    print(f"⚠️  Service initialization failed: {e}")

            # 4. Initialize agents
            print("🤖 Initializing agent system...")
            total_attempts += 1
            try:
                if COMPONENTS_AVAILABLE['agents']:
                    agent_status = initialize_all_agents()
                    self.orchestrator = get_orchestrator()

                    if agent_status.get('initialized', 0) > 0:
                        if self.logger:
                            self.logger.info(f"Agents initialized: {agent_status}")
                        else:
                            print(f"✅ Agents initialized: {agent_status}")
                        self.running_components.append('agents')
                        success_count += 1
                    else:
                        print("⚠️  No agents initialized - core functionality will be limited")
                else:
                    print("⚠️  Agents not available - core functionality will be limited")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Agent initialization failed: {e}")
                else:
                    print(f"⚠️  Agent initialization failed: {e}")

            # 5. Create Flask application
            print("🌐 Initializing web interface...")
            total_attempts += 1
            try:
                if COMPONENTS_AVAILABLE['web']:
                    self.app = create_app(
                        config_override={
                            'DEBUG': self.debug,
                            'TESTING': False,
                        }
                    )

                    if self.app:
                        if self.logger:
                            self.logger.info("Web interface initialized successfully")
                        else:
                            print("✅ Web interface initialized successfully")
                        self.running_components.append('web')
                        success_count += 1
                    else:
                        print("⚠️  Web interface creation failed - running headless")
                else:
                    print("⚠️  Web interface not available - running headless")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Web interface initialization failed: {e}")
                else:
                    print(f"⚠️  Web interface initialization failed: {e}")

            # 6. Setup shutdown handlers
            self._setup_shutdown_handlers()

            # Summary
            print(f"✅ Socratic RAG Enhanced initialized!")
            print(f"📊 Components running: {success_count}/{total_attempts}")
            if self.running_components:
                print(f"🔧 Active: {', '.join(self.running_components)}")

            if IMPORT_ERRORS:
                print(f"⚠️  Some components unavailable due to import errors")

            self._print_system_status()

            # Allow system to run even with partial failures
            return success_count > 0

        except Exception as e:
            print(f"❌ Fatal error during initialization: {e}")
            if self.logger:
                self.logger.exception("Fatal initialization error")
            return False

    def run(self, host: str = "127.0.0.1", port: int = 5000, **kwargs) -> None:
        """Run the application"""
        if not self.app:
            print("⚠️  Web interface not available - starting in headless mode")
            print("🔧 System is running but web interface is disabled")
            print("📝 Check logs for component status")

            # Keep the application running even without web interface
            try:
                print(f"🚀 System running in headless mode (Ctrl+C to stop)")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Received interrupt signal")
                self.shutdown()
            return

        try:
            # Development vs Production configuration
            if self.debug:
                print(f"🔧 Running in DEBUG mode on http://{host}:{port}")
                if self.logger:
                    self.logger.info(f"Starting development server on {host}:{port}")

                # Development server options
                run_options = {
                    'host': host,
                    'port': port,
                    'debug': True,
                    'use_reloader': False,  # Disable reloader to prevent agent duplication
                    'threaded': True,
                    **kwargs
                }
            else:
                print(f"🚀 Running in PRODUCTION mode on http://{host}:{port}")
                if self.logger:
                    self.logger.info(f"Starting production server on {host}:{port}")

                # Production server options
                run_options = {
                    'host': host,
                    'port': port,
                    'debug': False,
                    'use_reloader': False,
                    'threaded': True,
                    **kwargs
                }

            # Start the Flask application
            self.app.run(**run_options)

        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
            self.shutdown()
        except Exception as e:
            if self.logger:
                self.logger.exception(f"Application runtime error: {e}")
            else:
                print(f"❌ Application error: {e}")
            self.shutdown()

    def shutdown(self) -> None:
        """Gracefully shutdown all components"""
        print("\n🔄 Shutting down Socratic RAG Enhanced...")

        try:
            # Call registered shutdown handlers
            for handler in self.shutdown_handlers:
                try:
                    handler()
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Shutdown handler error: {e}")
                    else:
                        print(f"⚠️  Shutdown handler error: {e}")

            # Cleanup system
            if COMPONENTS_AVAILABLE['core']:
                cleanup_system()

            print("✅ Shutdown complete")

        except Exception as e:
            print(f"⚠️  Error during shutdown: {e}")

    def _setup_shutdown_handlers(self) -> None:
        """Setup graceful shutdown handlers"""

        def signal_handler(signum, frame):
            print(f"\n🔔 Received signal {signum}")
            self.shutdown()
            sys.exit(0)

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _print_system_status(self) -> None:
        """Print current system status"""
        print("\n📊 System Status:")
        print("=" * 50)

        for component, available in COMPONENTS_AVAILABLE.items():
            status = "✅ Available" if available else "❌ Unavailable"
            running = "🔧 Running" if component in self.running_components else "⏹️  Stopped"
            print(f"   {component.capitalize():12} | {status:12} | {running}")

            if not available and component in IMPORT_ERRORS:
                print(f"     └─ Error: {IMPORT_ERRORS[component][:60]}...")

        print("=" * 50)


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Socratic RAG Enhanced - AI-powered project development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                           # Run with default settings
  python run.py --debug                   # Run in debug mode
  python run.py --host 0.0.0.0 --port 8080  # Custom host and port
  python run.py --config custom.yaml      # Use custom config file
  python run.py --check-deps              # Check dependencies only
        """
    )

    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )

    parser.add_argument(
        '--config',
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check dependencies and exit'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Socratic RAG Enhanced v7.3.0'
    )

    return parser


def check_prerequisites() -> bool:
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")

    all_good = True

    # Check Python version
    if not validate_python_version():
        all_good = False
    else:
        print(f"✅ Python version: {sys.version.split()[0]}")

    # Check file system
    if not check_file_system():
        all_good = False
    else:
        print("✅ File system structure OK")

    # Check required packages
    missing_required = check_required_packages()
    if missing_required:
        all_good = False
    else:
        print("✅ Required packages installed")

    # Component availability summary
    available_count = sum(COMPONENTS_AVAILABLE.values())
    total_count = len(COMPONENTS_AVAILABLE)
    print(f"📦 Components available: {available_count}/{total_count}")

    return all_good


def main():
    """Main entry point"""
    # Print welcome banner
    print("\n" + "=" * 60)
    print("🧠 SOCRATIC RAG ENHANCED")
    print("   AI-Powered Project Development Through Intelligent Questioning")
    print("   Version: 7.3.0")
    print("=" * 60)

    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # Check dependencies only if requested
    if args.check_deps:
        success = check_prerequisites()
        if success:
            print("\n✅ All prerequisites met!")
            sys.exit(0)
        else:
            print("\n❌ Some prerequisites not met. See details above.")
            sys.exit(1)

    # Check prerequisites
    if not check_prerequisites():
        print("\n⚠️  Some prerequisites not met, but attempting to continue...")
        print("💡 Use --check-deps flag for detailed dependency information")

    # Create and initialize application
    app = SocraticRAGApplication(
        config_path=args.config,
        debug=args.debug
    )

    # Initialize all components
    if not app.initialize():
        print("\n❌ Critical initialization failure. Cannot continue.")
        print("💡 Try installing missing dependencies: pip install -r requirements.txt")
        sys.exit(1)

    try:
        # Run the application
        app.run(
            host=args.host,
            port=args.port
        )
    except Exception as e:
        print(f"\n❌ Failed to start application: {e}")
        sys.exit(1)


def open_browser():
    """Open browser after a short delay to ensure server is running"""
    time.sleep(2)  # Wait for server to start
    if COMPONENTS_AVAILABLE['web']:
        webbrowser.open('http://127.0.0.1:5000')


if __name__ == "__main__":
    if '--check-deps' not in sys.argv:
        threading.Thread(target=open_browser, daemon=True).start()
    main()
