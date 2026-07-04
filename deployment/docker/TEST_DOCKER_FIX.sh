#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Docker Configuration Fix Test${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}\n"

# Navigate to docker directory
DOCKER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DOCKER_DIR"

echo -e "${YELLOW}[1/8]${NC} Checking environment configuration..."
if grep -q "SOCRATES_DATA_DIR=/app/data" docker-compose.yml; then
    echo -e "${GREEN}✓ SOCRATES_DATA_DIR is set to /app/data in docker-compose.yml${NC}"
else
    echo -e "${RED}✗ SOCRATES_DATA_DIR not found in docker-compose.yml${NC}"
    exit 1
fi

if grep -q "VITE_API_URL: http://localhost:8000" docker-compose.yml; then
    echo -e "${GREEN}✓ Frontend VITE_API_URL is set to http://localhost:8000${NC}"
else
    echo -e "${RED}✗ Frontend API URL not configured correctly${NC}"
    exit 1
fi

echo -e "\n${YELLOW}[2/8]${NC} Stopping existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true
echo -e "${GREEN}✓ Containers stopped${NC}"

echo -e "\n${YELLOW}[3/8]${NC} Removing old data volumes (clean test)..."
docker volume rm socrates_data 2>/dev/null || true
docker volume rm socrates_logs 2>/dev/null || true
echo -e "${GREEN}✓ Old volumes cleaned${NC}"

echo -e "\n${YELLOW}[4/8]${NC} Checking .env file..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}! .env file not found. Creating from .env.docker...${NC}"
    cp .env.docker .env
    echo -e "${YELLOW}! Please edit .env and add your ANTHROPIC_API_KEY${NC}"
    echo -e "${YELLOW}! Then run this script again${NC}"
    exit 0
else
    if grep -q "ANTHROPIC_API_KEY=sk-ant-" .env || grep -q "ANTHROPIC_API_KEY.*real.*key" .env; then
        echo -e "${GREEN}✓ .env file exists with API key${NC}"
    else
        echo -e "${YELLOW}⚠ .env exists but ANTHROPIC_API_KEY may not be set${NC}"
    fi
fi

echo -e "\n${YELLOW}[5/8]${NC} Building Docker images..."
docker-compose build --no-cache 2>&1 | tail -5
echo -e "${GREEN}✓ Build complete${NC}"

echo -e "\n${YELLOW}[6/8]${NC} Starting containers..."
docker-compose up -d
echo -e "${GREEN}✓ Containers started${NC}"

echo -e "\n${YELLOW}[7/8]${NC} Waiting for services to be healthy..."
echo "Please wait (this can take 30-60 seconds)..."

# Function to check container health
check_health() {
    local service=$1
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps | grep -q "$service.*Up"; then
            # Give it a moment to actually start responding
            sleep 2
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    return 1
}

# Check all critical services
for service in api frontend redis postgres; do
    if check_health "$service"; then
        echo -e "${GREEN}✓ $service is up${NC}"
    else
        echo -e "${RED}✗ $service failed to start${NC}"
        echo -e "${YELLOW}Showing logs:${NC}"
        docker-compose logs $service | tail -20
        exit 1
    fi
done

echo -e "\n${YELLOW}[8/8]${NC} Verifying configuration..."

# Check SOCRATES_DATA_DIR is set in running container
DATA_DIR=$(docker-compose exec api env | grep SOCRATES_DATA_DIR)
if echo "$DATA_DIR" | grep -q "/app/data"; then
    echo -e "${GREEN}✓ SOCRATES_DATA_DIR is set correctly in running container${NC}"
    echo "  $DATA_DIR"
else
    echo -e "${RED}✗ SOCRATES_DATA_DIR not set correctly in running container${NC}"
    exit 1
fi

# Check database file exists
if docker-compose exec api ls -la /app/data/ 2>/dev/null | grep -q "projects.db"; then
    echo -e "${GREEN}✓ Database file exists at /app/data/projects.db${NC}"
else
    echo -e "${YELLOW}ℹ Database will be created on first use${NC}"
fi

# Check volume exists
VOLUME_NAME=$(docker volume ls | grep socrates_data | awk '{print $2}')
if [ ! -z "$VOLUME_NAME" ]; then
    echo -e "${GREEN}✓ Docker volume '$VOLUME_NAME' is created${NC}"
else
    echo -e "${RED}✗ Docker volume not found${NC}"
    exit 1
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ ALL CHECKS PASSED!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Create a test user account"
echo "3. Create a test project"
echo "4. Run the persistence test (see instructions below)"
echo ""

echo -e "${YELLOW}Persistence Test:${NC}"
echo "To verify data persists across restarts:"
echo ""
echo "  # Stop containers"
echo "  docker-compose down"
echo ""
echo "  # Start again"
echo "  docker-compose up -d"
echo ""
echo "  # Verify your user and project still exist at http://localhost:3000"
echo ""

echo -e "${YELLOW}Useful Commands:${NC}"
echo "  docker-compose logs -f api        # Watch API logs"
echo "  docker-compose logs -f frontend   # Watch frontend logs"
echo "  docker-compose exec api bash      # Access API container"
echo "  docker volume ls                  # List volumes"
echo "  docker volume inspect deployment_docker_socrates_data  # Volume details"
echo ""

echo -e "${YELLOW}Service URLs:${NC}"
echo "  Frontend:     http://localhost:3000"
echo "  API:          http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo ""
