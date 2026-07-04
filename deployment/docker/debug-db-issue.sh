#!/bin/bash
# Comprehensive database debugging script
# Run from the host: bash deployment/docker/debug-db-issue.sh

echo "================================================================================"
echo "SOCRATES DATABASE DEBUGGING SCRIPT"
echo "================================================================================"

cd deployment/docker

echo ""
echo "1. CHECK DOCKER-COMPOSE STATUS"
echo "   ================================================================================"
docker-compose ps
if [ $? -ne 0 ]; then
    echo "   ERROR: docker-compose is not running or not found"
    exit 1
fi

echo ""
echo "2. CHECK ENVIRONMENT VARIABLES IN API CONTAINER"
echo "   ================================================================================"
echo "   SOCRATES_DATA_DIR:"
docker-compose exec -T api env | grep SOCRATES_DATA_DIR || echo "   NOT SET!"

echo "   PYTHONPATH:"
docker-compose exec -T api env | grep PYTHONPATH

echo ""
echo "3. CHECK DATA DIRECTORY CONTENTS"
echo "   ================================================================================"
echo "   /app/data/ directory:"
docker-compose exec -T api ls -lah /app/data/ || echo "   ERROR: Directory doesn't exist!"

echo ""
echo "4. CHECK IF projects.db EXISTS"
echo "   ================================================================================"
docker-compose exec -T api test -f /app/data/projects.db && \
    echo "   ✓ projects.db EXISTS" || \
    echo "   ✗ projects.db DOES NOT EXIST"

if docker-compose exec -T api test -f /app/data/projects.db; then
    echo "   File size:"
    docker-compose exec -T api ls -lh /app/data/projects.db
fi

echo ""
echo "5. CHECK SCHEMA FILE"
echo "   ================================================================================"
docker-compose exec -T api test -f /app/socratic_system/database/schema_v2.sql && \
    echo "   ✓ schema_v2.sql EXISTS" || \
    echo "   ✗ schema_v2.sql DOES NOT EXIST"

echo ""
echo "6. RUN API INITIALIZATION TEST"
echo "   ================================================================================"
docker-compose exec -T api python3 -c "
import os
import sys
from pathlib import Path

print('Testing database initialization...')
print(f'SOCRATES_DATA_DIR = {os.getenv(\"SOCRATES_DATA_DIR\", \"NOT SET\")}')

# Add paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/socrates-api/src')

try:
    from socrates_api.database import DatabaseSingleton
    print('✓ DatabaseSingleton imported')

    print('Calling DatabaseSingleton.initialize()...')
    DatabaseSingleton.initialize()
    print('✓ DatabaseSingleton.initialize() completed')

    print('Calling DatabaseSingleton.get_instance()...')
    db = DatabaseSingleton.get_instance()
    print(f'✓ Database instance created')
    print(f'✓ Database path: {db.db_path}')

    # Check if file was created
    if Path(db.db_path).exists():
        size = Path(db.db_path).stat().st_size
        print(f'✓ Database file EXISTS: {size} bytes')
    else:
        print(f'✗ Database file DOES NOT EXIST: {db.db_path}')
        sys.exit(1)

except Exception as e:
    print(f'✗ ERROR: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "7. CHECK API LOGS FOR ERRORS"
echo "   ================================================================================"
echo "   Last 30 lines of API logs:"
docker-compose logs --tail 30 api

echo ""
echo "8. TRY DIRECT SQLITE CHECK"
echo "   ================================================================================"
docker-compose exec -T api sqlite3 /app/data/projects.db ".tables" 2>&1 | \
    if [ $? -eq 0 ]; then
        echo "   ✓ Database is readable"
    else
        echo "   ✗ Database file is not accessible"
    fi

echo ""
echo "================================================================================"
echo "END OF DEBUG OUTPUT"
echo "================================================================================"
