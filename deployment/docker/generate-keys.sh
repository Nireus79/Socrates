#!/bin/bash
# Generate secure encryption and JWT keys for Socrates Docker deployment
# Usage: ./generate-keys.sh [output-file]

set -e

OUTPUT_FILE="${1:-.env}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Socrates Docker Key Generation Tool                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists and is not empty
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo -e "${YELLOW}⚠️  File '$OUTPUT_FILE' already exists${NC}"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

echo "Generating secure keys..."
echo ""

# Generate keys
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || python -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())" 2>/dev/null || python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())")
DB_ENCRYPTION=$(python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())" 2>/dev/null || python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())")

echo -e "${GREEN}✓ JWT_SECRET_KEY generated${NC}"
echo -e "${GREEN}✓ SOCRATES_ENCRYPTION_KEY generated${NC}"
echo -e "${GREEN}✓ DATABASE_ENCRYPTION_KEY generated${NC}"
echo ""

# Create .env file or update existing
cat > "$OUTPUT_FILE" << EOF
# Socrates Production Environment Configuration
# Generated on $(date)
# IMPORTANT: Keep this file secure and never commit to version control!

# ============================================================================
# ENCRYPTION & SECURITY (Generated - UNIQUE for each environment)
# ============================================================================

# Encryption key for storing provider API keys and sensitive data in database
SOCRATES_ENCRYPTION_KEY=$ENCRYPTION_KEY

# Encryption key for database-level encryption
DATABASE_ENCRYPTION_KEY=$DB_ENCRYPTION

# JWT Secret Key - CRITICAL for session persistence across container restarts
# MUST BE CONSISTENT across all deployments to prevent invalidating user sessions
JWT_SECRET_KEY=$JWT_SECRET

# ============================================================================
# API KEY (REQUIRED - Add your Anthropic API key here)
# ============================================================================

# Anthropic API Key (get from https://console.anthropic.com)
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# PostgreSQL credentials (for production use)
POSTGRES_USER=socrates
POSTGRES_PASSWORD=socrates_dev_password
POSTGRES_DB=socrates_db

# ============================================================================
# REDIS CACHE CONFIGURATION
# ============================================================================

REDIS_URL=redis://redis:6379/0

# ============================================================================
# API CONFIGURATION
# ============================================================================

# API host binding (0.0.0.0 for Docker)
SOCRATES_API_HOST=0.0.0.0

# API port
SOCRATES_API_PORT=8000

# Allowed hosts
ALLOWED_HOSTS=localhost,127.0.0.1,api,host.docker.internal

# CORS allowed origins
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://api:3000

# ============================================================================
# RUNTIME CONFIGURATION
# ============================================================================

# Environment (development, staging, production)
ENVIRONMENT=development

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Python configuration
PYTHONUNBUFFERED=1

# ============================================================================
# NEXT STEPS
# ============================================================================
# 1. Add your ANTHROPIC_API_KEY above (replace sk-ant-YOUR-KEY-HERE)
# 2. For production, change ENVIRONMENT=production
# 3. For production, generate new POSTGRES_PASSWORD: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# 4. Start containers: docker-compose up -d
# 5. Access at: http://localhost:3000
# 6. Add Anthropic API key via Settings → LLM Configuration (if not in .env)
EOF

echo -e "${GREEN}✓ Created $OUTPUT_FILE${NC}"
echo ""
echo -e "${YELLOW}📋 IMPORTANT: Next steps${NC}"
echo "1. Add your Anthropic API key:"
echo "   - Get from: https://console.anthropic.com"
echo "   - Edit $OUTPUT_FILE and replace: sk-ant-YOUR-KEY-HERE"
echo ""
echo "2. Start Docker:"
echo "   docker-compose up -d"
echo ""
echo "3. Access Socrates:"
echo "   Frontend: http://localhost:3000"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo -e "${BLUE}✨ Keys generated successfully!${NC}"
