# Environment Configuration Template

This file documents all environment variables needed for Socrates configuration.

**⚠️ SECURITY WARNING**: Never commit `.env`, `.env.production`, or any actual environment files to the repository. Always use a secure secrets manager for production credentials.

## Development Setup

Create `.env` in the project root:

```bash
# Socrates Environment Configuration
ENVIRONMENT=development
JWT_SECRET_KEY=your-random-secret-key-here
SOCRATES_API_HOST=127.0.0.1
SOCRATES_API_PORT=8000
SOCRATES_DATA_DIR=~/.socrates

# Database Encryption
SECURITY_DATABASE_ENCRYPTION=true
DATABASE_ENCRYPTION_KEY=your-32-char-encryption-key-here

# Optional: Anthropic API (for local testing)
ANTHROPIC_API_KEY=sk-ant-v4-your-actual-key-here
```

## Production Setup

Create `.env.production` in `deployment/configurations/`:

```bash
# ============================================================================
# API Configuration
# ============================================================================
SOCRATES_API_HOST=0.0.0.0
SOCRATES_API_PORT=8000
SOCRATES_API_RELOAD=false
ENVIRONMENT=production

# ============================================================================
# Security
# ============================================================================
JWT_SECRET_KEY=<generate-with-python-scripts/generate_jwt_secret.py>
ALLOWED_ORIGINS=https://socrates.app,https://app.socrates.app

# ============================================================================
# Database
# ============================================================================
DATABASE_URL=postgresql://user:password@postgres:5432/socrates

# ============================================================================
# Cache & Real-time
# ============================================================================
REDIS_URL=redis://redis:6379
CHROMADB_URL=http://chromadb:8000

# ============================================================================
# LLM Provider
# ============================================================================
ANTHROPIC_API_KEY=<use-aws-secrets-manager-or-vault>
CLAUDE_MODEL=claude-haiku-4-5-20251001

# ============================================================================
# Monitoring & Observability
# ============================================================================
SENTRY_DSN=<optional>
LOG_LEVEL=INFO

# ============================================================================
# Feature Flags
# ============================================================================
ENABLE_RATE_LIMITING=true
ENABLE_METRICS=true
ENABLE_WEBSOCKET=true
ENABLE_QUERY_PROFILING=true

# ============================================================================
# Data Persistence
# ============================================================================
LOGS_DIR=/var/log/socrates
DATA_DIR=/var/lib/socrates
BACKUP_DIR=/backups

# ============================================================================
# S3 Backup (optional)
# ============================================================================
AWS_ACCESS_KEY_ID=<use-aws-secrets-manager>
AWS_SECRET_ACCESS_KEY=<use-aws-secrets-manager>
AWS_REGION=us-east-1
S3_BUCKET=socrates-backups

# ============================================================================
# Email Notifications (optional)
# ============================================================================
SMTP_HOST=<your-smtp-host>
SMTP_PORT=587
SMTP_USER=<your-smtp-user>
SMTP_PASSWORD=<use-aws-secrets-manager>
SMTP_FROM=noreply@socrates.app

# ============================================================================
# Application Settings
# ============================================================================
MAX_UPLOAD_SIZE=10485760
REQUEST_TIMEOUT=30
SESSION_TIMEOUT=3600

# ============================================================================
# Database Pool Settings
# ============================================================================
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
SLOW_QUERY_THRESHOLD_MS=100
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE=redis
```

## Secrets Management Best Practices

### ✅ DO:
- Use AWS Secrets Manager, HashiCorp Vault, or similar
- Store secrets separately from code
- Rotate API keys regularly
- Use IAM roles for AWS credentials
- Document what each secret is for
- Audit access to secrets
- Generate strong JWT secrets with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### ❌ DON'T:
- Commit any `.env*` files to git
- Hardcode credentials in code
- Use the same secret across environments
- Share credentials via email or chat
- Store plaintext passwords
- Commit example files with placeholder keys

## Local Development Quick Start

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Create local .env file (not committed)
cat > .env << 'EOF'
ENVIRONMENT=development
JWT_SECRET_KEY=<paste-generated-secret>
SOCRATES_API_HOST=127.0.0.1
SOCRATES_API_PORT=8000
SOCRATES_DATA_DIR=~/.socrates
SECURITY_DATABASE_ENCRYPTION=true
DATABASE_ENCRYPTION_KEY=local-dev-key-not-for-production
EOF

# Load environment
source .env
```

## Docker Compose

For Docker Compose, create `docker-compose.env`:

```bash
ENVIRONMENT=development
POSTGRES_USER=socrates_dev
POSTGRES_PASSWORD=dev_password_change_me
POSTGRES_DB=socrates
REDIS_URL=redis://redis:6379
CHROMADB_URL=http://chromadb:8000
```

Then reference it in docker-compose.yml:
```yaml
services:
  api:
    env_file:
      - docker-compose.env
```

## Troubleshooting

**Missing API key**: Ensure `ANTHROPIC_API_KEY` is set before running the application
**Database connection failed**: Check `DATABASE_URL` format and database service is running
**Port already in use**: Change `SOCRATES_API_PORT` to an available port
**JWT errors**: Regenerate `JWT_SECRET_KEY` with the command above
