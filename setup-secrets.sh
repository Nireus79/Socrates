#!/bin/bash
# Setup Socrates encryption keys for Docker
# Generates secure random keys and saves to .env.local (not in git)
# Usage: ./setup-secrets.sh

set -e

ENV_LOCAL_FILE=".env.local"

# Check if .env.local already exists
if [ -f "$ENV_LOCAL_FILE" ]; then
    echo "⚠️  $ENV_LOCAL_FILE already exists"
    read -p "Do you want to regenerate keys? This will require re-entering API keys in Socrates. (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "✓ Keeping existing keys in $ENV_LOCAL_FILE"
        exit 0
    fi
    echo "⚠️  Backing up current keys to .env.local.backup"
    cp "$ENV_LOCAL_FILE" ".env.local.backup"
fi

echo "🔐 Generating encryption keys..."

# Generate cryptographically secure random keys
SOCRATES_ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
DATABASE_ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Create .env.local file
cat > "$ENV_LOCAL_FILE" << EOF
# Socrates Encryption Keys - Generated $(date)
# IMPORTANT: Do NOT commit this file to git
# These keys are required to run Socrates with Docker

# Encryption key for API credentials and sensitive data
SOCRATES_ENCRYPTION_KEY=$SOCRATES_ENCRYPTION_KEY

# Encryption key for database
DATABASE_ENCRYPTION_KEY=$DATABASE_ENCRYPTION_KEY

# JWT secret for session tokens
JWT_SECRET_KEY=$JWT_SECRET_KEY
EOF

# Restrict file permissions to owner only (Unix-like systems)
chmod 600 "$ENV_LOCAL_FILE" 2>/dev/null || true

echo ""
echo "✓ Encryption keys generated!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Start Socrates with:"
echo "   docker-compose --env-file .env.local up --build"
echo ""
echo "2. Open http://localhost:3000"
echo ""
echo "3. Set your LLM API keys (Claude, Ollama, etc.) in Settings"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - .env.local is in .gitignore (not in git)"
echo "   - Never commit .env.local to version control"
echo "   - Different deployments need different keys"
echo "   - If you lose .env.local, you'll need to re-enter your API keys"
echo ""
echo "🔄 To rotate keys:"
echo "   1. Run this script again"
echo "   2. Restart Docker: docker-compose down && docker-compose --env-file .env.local up --build"
echo "   3. Re-enter your API keys in Socrates Settings"
echo ""
