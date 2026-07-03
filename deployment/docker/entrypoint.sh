#!/bin/bash
set -e

# Socrates API Docker Entrypoint
# Runs database migrations and then starts the API server

echo "=== Socrates API Startup ==="

# Check if required environment variables are set
echo "Validating environment variables..."
REQUIRED_VARS=("SOCRATES_ENCRYPTION_KEY" "DATABASE_ENCRYPTION_KEY" "JWT_SECRET_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "ERROR: Missing required environment variables: ${MISSING_VARS[*]}"
    echo "Please set these variables before starting the container."
    exit 1
fi

echo "✓ Environment variables validated"

# Wait for database to be ready (if using PostgreSQL)
if [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "Waiting for PostgreSQL to be ready..."
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\).*/\1/p')
    DB_PORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p' | tail -1)

    for i in {1..30}; do
        if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
            echo "✓ PostgreSQL is ready"
            break
        fi
        echo "Waiting for PostgreSQL... ($i/30)"
        sleep 1
    done
fi

# Run database migrations (if applicable)
# Uncomment if using Alembic for migrations
# echo "Running database migrations..."
# cd /app
# alembic upgrade head
# echo "✓ Database migrations completed"

echo "Starting Socrates API server..."
exec python -m socrates_api.main
