#!/usr/bin/env python3
"""
Initialize Test Database
========================

Creates the required database tables for session persistence tests.
Run this before running the session persistence tests.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.database import get_database
    from src.core import get_logger

    print("Initializing test database...")

    # Get database service
    db = get_database()
    db_manager = db.db_manager

    print(f"Database path: {db_manager.db_path}")

    # Check if tables exist
    try:
        result = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row['name'] for row in result]
        print(f"\nExisting tables: {existing_tables}")

        if 'socratic_sessions' in existing_tables:
            print("✓ socratic_sessions table already exists")
        else:
            print("✗ socratic_sessions table missing - will be created by DatabaseManager")

        if 'questions' in existing_tables:
            print("✓ questions table already exists")
        else:
            print("✗ questions table missing - will be created by DatabaseManager")

        if 'conversation_messages' in existing_tables:
            print("✓ conversation_messages table already exists")
        else:
            print("✗ conversation_messages table missing - will be created by DatabaseManager")

    except Exception as e:
        print(f"Error checking tables: {e}")

    # The DatabaseManager should auto-create tables via _init_schema()
    # Force a health check to ensure schema is initialized
    health = db_manager.health_check()
    print(f"\nDatabase health: {health.get('status')}")

    # Verify tables were created
    result = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
    final_tables = [row['name'] for row in result]

    print(f"\nFinal tables in database: {final_tables}")

    # Check for required tables
    required_tables = ['socratic_sessions', 'questions', 'conversation_messages']
    missing_tables = [t for t in required_tables if t not in final_tables]

    if missing_tables:
        print(f"\n⚠ Warning: Still missing tables: {missing_tables}")
        print("\nThe database schema may need to be manually initialized.")
        print("Check that DatabaseManager._init_schema() includes these tables.")
    else:
        print("\n✓ All required tables exist!")
        print("You can now run: python tests/test_session_persistence.py")

except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nMake sure you're running from the project root directory.")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)