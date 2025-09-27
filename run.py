#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Main Application Entry Point
Version: 7.3.0

This is the single entry point for the Socratic RAG Enhanced system.
Initializes all components, agents, services, and the web interface.
"""

import os
import sys
import signal
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    # Core system imports
    from src.core import (
        SystemConfig,
        SystemLogger,
        EventSystem,
        DatabaseManager,
        initialize_system,
        cleanup_system
    )
    from src.database import init_database
    from src.agents import get_orchestrator, initialize_all_agents
    from src.services import initialize_all_services
    from web.app import create_app

except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


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

    def initialize(self) -> bool:
        """Initialize all system components"""
        try:
            print("🚀 Starting Socratic RAG Enhanced v7.3.0...")

            # 1. Initialize core system
            print("📋 Initializing core system...")
            success = initialize_system(self.config_path)
            if not success:
                print("❌ Failed to initialize core system")
                return False

            self.config = SystemConfig()
            self.logger = logging.getLogger(__name__)

            self.logger.info("Core system initialized successfully")

            # 2. Initialize database
            print("🗄️ Initializing database...")
            try:
                init_database()
                self.logger.info("Database initialized successfully")
            except Exception as e:
                self.logger.error(f"Database initialization failed: {e}")
                return False

            # 3. Initialize services
            print("🌐 Initializing external services...")
            try:
                service_status = initialize_all_services()
                if service_status.get('initialized', 0) == 0:
                    self.logger.warning("No external services initialized - running in limited mode")
                else:
                    self.logger.info(f"Services initialized: {service_status}")
            except Exception as e:
                self.logger.error(f"Service initialization failed: {e}")
                # Continue in limited mode

            # 4. Initialize agents
            print("🤖 Initializing agent system...")
            try:
                agent_status = initialize_all_agents()
                self.orchestrator = get_orchestrator()

                if agent_status.get('initialized', 0) == 0:
                    self.logger.error("No agents initialized - system cannot function")
                    return False

                self.logger.info(f"Agents initialized: {agent_status}")
            except Exception as e:
                self.logger.error(f"Agent initialization failed: {e}")
                return False

            # 5. Create Flask application
            print("🌐 Initializing web interface...")
            try:
                self.app = create_app(
                    config_override={
                        'DEBUG': self.debug,
                        'TESTING': False,
                    }
                )

                if not self.app:
                    self.logger.error("Failed to create Flask application")
                    return False

                self.logger.info("Web interface initialized successfully")
            except Exception as e:
                self.logger.error(f"Web interface initialization failed: {e}")
                return False

            # 6. Setup shutdown handlers
            self._setup_shutdown_handlers()

            print("✅ Socratic RAG Enhanced initialized successfully!")
            self._print_system_status()

            return True

        except Exception as e:
            print(f"❌ Fatal error during initialization: {e}")
            if self.logger:
                self.logger.exception("Fatal initialization error")
            return False

    def run(self, host: str = "127.0.0.1", port: int = 5000, **kwargs) -> None:
        """Run the application"""
        if not self.app:
            print("❌ Application not initialized. Call initialize() first.")
            return

        try:
            # Development vs Production configuration
            if self.debug:
                print(f"🔧 Running in DEBUG mode on http://{host}:{port}")
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
            self.logger.exception(f"Application runtime error: {e}")
            print(f"❌ Application error: {e}")
            self.shutdown()

    def shutdown(self) -> None:
        """Gracefully shutdown the application"""
        print("🛑 Shutting down Socratic RAG Enhanced...")

        try:
            # Call all registered shutdown handlers
            for handler in self.shutdown_handlers:
                try:
                    handler()
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Shutdown handler error: {e}")

            # Cleanup core system
            cleanup_system()

            print("✅ Shutdown complete")

        except Exception as e:
            print(f"❌ Error during shutdown: {e}")
        finally:
            sys.exit(0)

    def _setup_shutdown_handlers(self) -> None:
        """Setup graceful shutdown handlers"""

        def signal_handler(signum, frame):
            self.shutdown()

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Add custom shutdown tasks
        def agent_cleanup():
            if self.orchestrator:
                try:
                    self.orchestrator.shutdown_all()
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Agent cleanup error: {e}")

        self.shutdown_handlers.append(agent_cleanup)

    def _print_system_status(self) -> None:
        """Print current system status"""
        print("\n" + "=" * 60)
        print("📊 SYSTEM STATUS")
        print("=" * 60)

        # Configuration status
        if self.config:
            print(f"⚙️  Configuration: {self.config.config_file}")
            print(f"📁 Data Directory: {self.config.get('data.base_path', 'data/')}")
            print(f"🔍 Debug Mode: {self.debug}")

        # Agent status
        if self.orchestrator:
            agent_count = len(self.orchestrator.list_available_agents())
            print(f"🤖 Active Agents: {agent_count}")

        # Database status
        try:
            db_manager = DatabaseManager()
            if db_manager.health_check():
                print("🗄️  Database: Connected")
            else:
                print("🗄️  Database: Error")
        except:
            print("🗄️  Database: Unknown")

        # Service status (basic check)
        services_available = []
        try:
            from src.services import claude_service, vector_service
            if hasattr(claude_service, 'client') and claude_service.client:
                services_available.append("Claude API")
            if hasattr(vector_service, 'client') and vector_service.client:
                services_available.append("Vector DB")
        except:
            pass

        if services_available:
            print(f"🌐 Services: {', '.join(services_available)}")
        else:
            print("🌐 Services: Limited mode")

        print("=" * 60)
        print("🎯 Ready for intelligent project development!")
        print("=" * 60 + "\n")


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
        '--version',
        action='version',
        version='Socratic RAG Enhanced v7.3.0'
    )

    return parser


def check_prerequisites() -> bool:
    """Check if all prerequisites are met"""
    errors = []

    # Check Python version
    if sys.version_info < (3, 8):
        errors.append("Python 3.8 or higher is required")

    # Check required directories
    required_dirs = ['src', 'web', 'data']
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            if dir_name == 'data':
                # Create data directory if it doesn't exist
                Path(dir_name).mkdir(exist_ok=True)
                print(f"📁 Created {dir_name} directory")
            else:
                errors.append(f"Required directory '{dir_name}' not found")

    # Check configuration file
    config_file = Path('config.yaml')
    if not config_file.exists():
        errors.append("Configuration file 'config.yaml' not found")

    # Check requirements.txt
    requirements_file = Path('requirements.txt')
    if not requirements_file.exists():
        errors.append("Requirements file 'requirements.txt' not found")

    if errors:
        print("❌ Prerequisites check failed:")
        for error in errors:
            print(f"   • {error}")
        return False

    return True


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

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Please resolve the issues above and try again.")
        sys.exit(1)

    # Create and initialize application
    app = SocraticRAGApplication(
        config_path=args.config,
        debug=args.debug
    )

    # Initialize all components
    if not app.initialize():
        print("\n❌ Application initialization failed. Check logs for details.")
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


if __name__ == "__main__":
    main()
