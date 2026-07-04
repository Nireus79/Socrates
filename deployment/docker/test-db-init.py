#!/usr/bin/env python3
"""
Diagnostic script to test database initialization.
Run inside the API container: docker-compose exec api python /app/test-db-init.py
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add app directories to path
sys.path.insert(0, '/app/socratic_system')
sys.path.insert(0, '/app/socrates-api/src')

logger.info("=" * 80)
logger.info("DATABASE INITIALIZATION DIAGNOSTIC")
logger.info("=" * 80)

# Check environment
logger.info("\n1. ENVIRONMENT CHECK")
data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
logger.info(f"   SOCRATES_DATA_DIR = {data_dir}")
logger.info(f"   Data dir exists: {Path(data_dir).exists()}")
logger.info(f"   Data dir is writable: {os.access(data_dir, os.W_OK)}")

# Check files in data directory
if Path(data_dir).exists():
    logger.info(f"   Contents of {data_dir}:")
    for item in Path(data_dir).iterdir():
        logger.info(f"      - {item.name} ({item.stat().st_size} bytes)")

db_path = os.path.join(data_dir, "projects.db")
logger.info(f"   Expected DB path: {db_path}")
logger.info(f"   DB file exists: {Path(db_path).exists()}")

# Check schema file
logger.info("\n2. SCHEMA FILE CHECK")
schema_path = Path("/app/socratic_system/database/schema_v2.sql")
logger.info(f"   Schema file path: {schema_path}")
logger.info(f"   Schema file exists: {schema_path.exists()}")
if schema_path.exists():
    logger.info(f"   Schema file size: {schema_path.stat().st_size} bytes")

# Try importing modules
logger.info("\n3. MODULE IMPORT CHECK")
try:
    from socratic_system.database import ProjectDatabase
    logger.info("   ✓ ProjectDatabase imported successfully")
except Exception as e:
    logger.error(f"   ✗ Failed to import ProjectDatabase: {e}")
    sys.exit(1)

try:
    from socrates_api.database import DatabaseSingleton
    logger.info("   ✓ DatabaseSingleton imported successfully")
except Exception as e:
    logger.error(f"   ✗ Failed to import DatabaseSingleton: {e}")
    sys.exit(1)

# Try initializing database
logger.info("\n4. DATABASE INITIALIZATION TEST")
try:
    logger.info(f"   Calling DatabaseSingleton.initialize()...")
    DatabaseSingleton.initialize()
    logger.info("   ✓ DatabaseSingleton.initialize() succeeded")
except Exception as e:
    logger.error(f"   ✗ DatabaseSingleton.initialize() failed: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

# Try getting database instance
logger.info("\n5. DATABASE INSTANCE TEST")
try:
    logger.info(f"   Calling DatabaseSingleton.get_instance()...")
    db = DatabaseSingleton.get_instance()
    logger.info(f"   ✓ Got database instance: {db}")
    logger.info(f"   ✓ Database path: {db.db_path}")
except Exception as e:
    logger.error(f"   ✗ DatabaseSingleton.get_instance() failed: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

# Check if DB file was created
logger.info("\n6. DB FILE CREATION CHECK")
logger.info(f"   Checking if {db_path} exists...")
if Path(db_path).exists():
    logger.info(f"   ✓ Database file created!")
    logger.info(f"   ✓ File size: {Path(db_path).stat().st_size} bytes")
else:
    logger.error(f"   ✗ Database file NOT created!")
    sys.exit(1)

# Try querying database
logger.info("\n7. DATABASE QUERY TEST")
try:
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    logger.info(f"   ✓ Successfully connected to database")
    logger.info(f"   ✓ Number of tables: {len(tables)}")
    for (table_name,) in tables:
        logger.info(f"      - {table_name}")
    conn.close()
except Exception as e:
    logger.error(f"   ✗ Failed to query database: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

logger.info("\n" + "=" * 80)
logger.info("✓ ALL CHECKS PASSED - DATABASE INITIALIZATION IS WORKING")
logger.info("=" * 80)
