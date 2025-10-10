# Targeted Flask App Creation Debug
# File: debug_full_flask.py
# This will identify exactly what's preventing the full Flask app from being created

import sys
import traceback


def debug_full_flask_creation():
    """Debug the full Flask app creation step by step"""

    print("=== FULL FLASK APP DEBUG ===")

    # Step 1: Test src module imports one by one
    print("\n1. Testing src module imports...")

    # Test core imports
    try:
        from src import get_logger
        print("✅ src.get_logger imported")
    except Exception as e:
        print(f"❌ src.get_logger failed: {e}")
        traceback.print_exc()
        return False

    # Test config imports
    try:
        from src.core import get_config
        config = get_config()
        print(f"✅ Config loaded: {type(config)}")
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        traceback.print_exc()

    # Test repository manager
    try:
        from src.database import get_repository_manager
        repo_manager = get_repository_manager()
        print(f"✅ Repository manager: {type(repo_manager)}")
    except Exception as e:
        print(f"❌ Repository manager failed: {e}")
        traceback.print_exc()

    # Test orchestrator
    try:
        from src.agents import get_orchestrator
        orchestrator = get_orchestrator()
        print(f"✅ Orchestrator: {type(orchestrator)}")
    except Exception as e:
        print(f"❌ Orchestrator failed: {e}")
        traceback.print_exc()

    # Step 2: Test web app imports
    print("\n2. Testing web app imports...")

    try:
        from web.app import create_flask_app
        print("✅ create_flask_app imported")
    except Exception as e:
        print(f"❌ create_flask_app import failed: {e}")
        traceback.print_exc()
        return False

    # Step 3: Test Flask app creation with detailed error catching
    print("\n3. Testing Flask app creation...")

    try:
        app = create_flask_app()
        if app:
            print("✅ Flask app created successfully!")
            return True
        else:
            print("❌ Flask app creation returned None (no exception thrown)")
            return False
    except Exception as e:
        print(f"❌ Flask app creation raised exception: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False


def test_simplified_flask_creation():
    """Test creating Flask app without problematic dependencies"""

    print("\n=== SIMPLIFIED FLASK CREATION TEST ===")

    try:
        # Try to create Flask app but skip problematic imports
        from flask import Flask
        from flask_wtf import CSRFProtect
        from flask_login import LoginManager

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'

        # Initialize basic extensions
        csrf = CSRFProtect()
        csrf.init_app(app)

        login_manager = LoginManager()
        login_manager.init_app(app)

        @app.route('/')
        def index():
            return "Simplified Flask app working!"

        print("✅ Simplified Flask app created successfully")
        return app

    except Exception as e:
        print(f"❌ Even simplified Flask creation failed: {e}")
        traceback.print_exc()
        return None


def identify_problematic_import():
    """Try to identify which specific import is causing issues"""

    print("\n=== IMPORT ISOLATION TEST ===")

    imports_to_test = [
        ("Flask basic", lambda: __import__('flask')),
        ("Flask-WTF", lambda: __import__('flask_wtf')),
        ("Flask-Login", lambda: __import__('flask_login')),
        ("WTForms", lambda: __import__('wtforms')),
        ("src.models", lambda: __import__('src.models')),
        ("src.core", lambda: __import__('src.core')),
        ("src.database", lambda: __import__('src.database')),
        ("src.agents", lambda: __import__('src.agents')),
        ("src.services", lambda: __import__('src.services')),
    ]

    for name, import_func in imports_to_test:
        try:
            import_func()
            print(f"✅ {name}")
        except Exception as e:
            print(f"❌ {name}: {e}")


if __name__ == "__main__":
    print("Starting targeted Flask app debug...\n")

    # Test import isolation first
    identify_problematic_import()

    # Test full Flask creation
    success = debug_full_flask_creation()

    if not success:
        print("\n=== FALLBACK: Testing simplified Flask creation ===")
        simple_app = test_simplified_flask_creation()

        if simple_app:
            print("\n✅ CONCLUSION: Flask works, issue is with src module integration")
            print("Recommendation: Create Flask app without problematic src imports")
        else:
            print("\n❌ CONCLUSION: Fundamental Flask setup issue")

    print("\n=== DEBUG COMPLETE ===")