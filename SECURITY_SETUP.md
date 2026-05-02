# Security Setup Guide

**Date**: 2026-04-29

## Environment Variables & Secrets Management

This document explains how to properly configure sensitive environment variables for the Socrates API.

---

## Critical: Encryption Key Setup

### Problem
The API requires a `SOCRATES_ENCRYPTION_KEY` environment variable to encrypt sensitive data like API keys and authentication tokens.

### Solution: Generate Your Own Key

**Never use the same key across environments!** Generate a unique key for each environment.

#### Step 1: Generate a Secure Encryption Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

This will output a secure 32-byte random string. Example:
```
IYAI7psQRsdTU0yz7LH8th9GHKLqf5JEft09JkYU1UU
```

#### Step 2: Set the Environment Variable

**For Development:**
```bash
# Create socrates-api/.env file
cp socrates-api/.env.example socrates-api/.env

# Edit socrates-api/.env and replace YOUR_ENCRYPTION_KEY_HERE with your generated key
SOCRATES_ENCRYPTION_KEY=<paste-your-generated-key-here>
```

**For Production:**
Set as environment variable on your server (never commit to repository):
```bash
export SOCRATES_ENCRYPTION_KEY="<your-production-key>"
```

Or use your deployment platform's secrets management:
- AWS: Secrets Manager
- GCP: Secret Manager
- Azure: Key Vault
- Docker: Secrets
- Kubernetes: Secrets
- Heroku: Config Vars

#### Step 3: Verify Setup

The API will automatically load the .env file and use the encryption key.

Test by making a request to the `/llm/api-key` endpoint:
```bash
curl -X POST http://localhost:8000/llm/api-key \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "provider": "anthropic",
    "api_key": "test_key"
  }'
```

If you see a 500 error mentioning `SOCRATES_ENCRYPTION_KEY`, the environment variable is not set.

---

## File Structure

```
.gitignore (already includes .env)
├── .env              ❌ NEVER COMMIT (secrets!)
├── .env.example      ✅ COMMIT (template only)
└── .env.local        ❌ NEVER COMMIT (optional local override)
```

### .env (Development)
- Contains actual encryption keys and secrets
- Generated from .env.example
- Listed in .gitignore (protected)
- **Never commit to repository**

### .env.example (Template)
- Safe template showing required variables
- No actual secrets (placeholder values only)
- **Safe to commit to repository**
- Copy to .env and fill in actual values

### .env.local (Optional)
- Local machine overrides
- Useful for different local configurations
- Listed in .gitignore
- Never committed

---

## How the API Loads Environment Variables

When the API starts, it:

1. Checks for `socrates-api/.env` file
2. If found, loads all variables from it
3. Falls back to system environment variables
4. Variables in .env override system environment

This is implemented in `socrates-api/src/socrates_api/main.py`:

```python
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()  # Load from system environment
```

---

## Required vs Optional Variables

### REQUIRED
- `SOCRATES_ENCRYPTION_KEY` - Must be set for API to work

### OPTIONAL (with defaults)
- `ENVIRONMENT` - development (default)
- `SOCRATES_DATA_DIR` - ${HOME}/.socrates (default)
- `API_HOST` - 127.0.0.1 (default)
- `API_PORT` - 8000 (default)
- `FRONTEND_URL` - http://localhost:5173 (default)
- `DEBUG` - false (default)
- `LOG_LEVEL` - INFO (default)

See `socrates-api/.env.example` for complete list.

---

## Security Best Practices

### ✅ DO

- [ ] Generate unique encryption keys for each environment
- [ ] Store keys in environment variables (not code)
- [ ] Use secrets management system in production
- [ ] Rotate encryption keys periodically
- [ ] Use strong, random key generation
- [ ] Document required environment variables
- [ ] Keep .env files in .gitignore
- [ ] Review .gitignore regularly

### ❌ DON'T

- [ ] Commit .env files to version control
- [ ] Use the same key across environments
- [ ] Share encryption keys in chat/email
- [ ] Hardcode secrets in source code
- [ ] Use weak or predictable keys
- [ ] Check secrets into git history
- [ ] Expose keys in logs or error messages
- [ ] Use default/example keys in production

---

## Troubleshooting

### Error: "SOCRATES_ENCRYPTION_KEY environment variable is required"

**Causes:**
1. .env file not created
2. .env file exists but is empty
3. Environment variable not set on server
4. Wrong key format or spacing

**Solution:**
```bash
# Check if .env file exists
ls -la socrates-api/.env

# Check if variable is set
echo $SOCRATES_ENCRYPTION_KEY

# If empty, generate new key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env file
echo "SOCRATES_ENCRYPTION_KEY=<generated-key>" >> socrates-api/.env
```

### Error: "Invalid encryption key format"

**Cause:** Key was corrupted or has special characters not properly escaped

**Solution:**
1. Generate a new key
2. Ensure no extra spaces or quotes
3. Use the base64 format from secrets.token_urlsafe()

---

## Deployment Checklist

Before deploying to production:

- [ ] Generated unique encryption key for production
- [ ] Stored key in production secrets manager
- [ ] Verified .env file is in .gitignore
- [ ] Tested API with encryption key set
- [ ] Configured automatic key rotation (if supported)
- [ ] Documented key management process
- [ ] Set up monitoring for missing environment variables
- [ ] Tested recovery if key is lost

---

## Additional Resources

- [Python secrets module](https://docs.python.org/3/library/secrets.html)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [dotenv documentation](https://github.com/theskumar/python-dotenv)
- [FastAPI environment variables](https://fastapi.tiangolo.com/advanced/settings/)

---

## Summary

1. Generate encryption key with Python secrets module
2. Copy .env.example to .env
3. Set SOCRATES_ENCRYPTION_KEY in .env or environment
4. Keep .env out of version control (protected by .gitignore)
5. Use .env.example as template (safe to commit)
6. Use production secrets manager for deployment

**Status**: ✅ Security setup complete and documented
