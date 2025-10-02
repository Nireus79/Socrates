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
    # Fixed: get_logger is in src/__init__.py, not src.core
    from src import get_logger

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

        # Check for required session tables
        required_tables = ['socratic_sessions', 'questions', 'conversation_messages']

        for table in required_tables:
            if table in existing_tables:
                print(f"✓ {table} table exists")
            else:
                print(f"✗ {table} table MISSING")

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
        print(f"\n⚠ Warning: Missing tables: {missing_tables}")
        print("\nThese tables need to be added to DatabaseManager._init_schema()")
        print("Location: src/database.py, method _init_schema()")
        print("\nThe schema should include CREATE TABLE statements for:")
        for table in missing_tables:
            print(f"  - {table}")
    else:
        print("\n✓ All required tables exist!")
        print("You can now run: python tests/test_session_persistence.py")

except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nMake sure you're running from the project root directory.")
    print("Try: cd /path/to/socratic-rag-enhanced")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
