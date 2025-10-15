import sys
import argparse
import logging
import webbrowser
from pathlib import Path
from threading import Timer
from web.app import create_app
# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('run_working')


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    return True


def check_flask_availability():
    """Check if Flask and required packages are available"""
    missing = []

    packages = [
        ('flask', 'Flask'),
        ('flask_wtf', 'Flask-WTF'),
        ('flask_login', 'Flask-Login'),
        ('wtforms', 'WTForms'),
        ('werkzeug', 'Werkzeug')
    ]

    for module, name in packages:
        try:
            __import__(module)
        except ImportError:
            missing.append(name)

    if missing:
        print(f"ERROR: Missing required packages: {', '.join(missing)}")
        print("   Install with: pip install Flask Flask-WTF Flask-Login WTForms")
        return False

    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Socratic RAG Enhanced - Working Version')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-browser', action='store_true', help='Don\'t open browser automatically')

    args = parser.parse_args()

    # Check requirements
    if not check_python_version():
        sys.exit(1)

    if not check_flask_availability():
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("Starting Socratic RAG Enhanced (Working Version)")
    logger.info("=" * 70)
    logger.info("All Flask dependencies available")
    logger.info("Bypassing broken src module imports")
    logger.info("Phase C: UI Rebuild - Settings UI Ready")
    logger.info("")

    try:
        app = create_app()
        print(f"Flask app created: {app}")

        logger.info("Flask application created successfully")
        logger.info("=" * 70)
        logger.info(f"Socratic RAG Enhanced is running!")
        logger.info(f"Access the application at: http://localhost:{args.port}")
        logger.info("Available features:")
        logger.info("   - User registration with validation")
        logger.info("   - User login/logout with sessions")
        logger.info("   - Profile management")
        logger.info("   - Password reset flow")
        logger.info("   - Project creation and management")
        logger.info("   - Settings page (LLM & IDE configuration)")
        logger.info("   - Responsive design")
        logger.info("=" * 70)
        logger.info("")

        # Open browser automatically unless disabled
        if not args.no_browser:
            Timer(1.5, lambda: webbrowser.open(f'http://127.0.0.1:{args.port}')).start()
        if app:
            # Start the server
            print("Starting Flask server...")
            app.run(host='127.0.0.1', port=args.port, debug=args.debug, use_reloader=False)
        else:
            print("ERROR: Failed to create Flask app")
    except Exception as e:
        logger.error(f"ERROR: Failed to start application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
