# Socrates Setup & Onboarding Review

**Date**: April 28, 2026
**Purpose**: Comprehensive review of Socrates installation experience for new users

---

## Executive Summary

While Socrates has excellent documentation and architecture, there are **8 critical issues** that would prevent a user from successfully running it from GitHub without troubleshooting. These range from incorrect module paths to missing API key configuration.

**Severity Breakdown**:
- 🔴 **Critical (Will Block)**: 3 issues
- 🟠 **High (Will Confuse)**: 3 issues
- 🟡 **Medium (Not Ideal)**: 2 issues

---

---

## 🔐 SECURITY CONCERNS FOUND (Not blocking, but important)

### Security Issue A: Static Salt in PBKDF2 Encryption

**Location**: `socratic_system/agents/multi_llm_agent.py:763`

```python
salt = b"socrates-salt"  # ← STATIC SALT - should be random per-record
kdf = PBKDF2HMAC(...)
```

**Problem**:
- Same salt used for all encrypted keys
- Reduces effectiveness of PBKDF2
- Attackers can precompute rainbow tables for this salt

**Impact**: Medium - encryption still strong (100k iterations) but not optimal

**Fix**: Use random salt per encryption
```python
import os
salt = os.urandom(16)  # ← Random 16-byte salt
# Store salt with encrypted key or use different KDF
```

---

### Security Issue B: Hardcoded Default Encryption Key

**Location**: `socratic_system/agents/multi_llm_agent.py:758-760`

```python
secret = os.getenv(
    "SOCRATES_ENCRYPTION_KEY",
    "default-insecure-key-change-in-production"  # ← HARDCODED DEFAULT
).encode()
```

**Problem**:
- If env var not set, uses predictable default key
- Anyone reading the code knows the key
- Database is not actually encrypted

**Fix**:
1. Require the env var (fail fast if not set):
```python
secret = os.getenv("SOCRATES_ENCRYPTION_KEY")
if not secret:
    raise ValueError("SOCRATES_ENCRYPTION_KEY environment variable is required")
secret = secret.encode()
```

2. Update `.env` documentation to show generation

---

### Security Issue C: Frontend Sends API Key via URL Parameters

**Location**: `socrates-frontend/src/api/llm.ts:132-136`

```typescript
async addAPIKey(provider: string, apiKey: string) {
    const params = new URLSearchParams();
    params.append('api_key', apiKey);  // ← In URL, not body!
    return apiClient.post(`/llm/api-key?${params.toString()}`, {});
}
```

**Problem**:
- API key visible in URLs
- Could be logged by proxy servers, firewalls, WAF
- Browser history might contain the key
- Server logs will show URL with API key

**Fix**: Use POST body instead
```typescript
async addAPIKey(provider: string, apiKey: string) {
    return apiClient.post('/llm/api-key', {
        provider: provider,
        api_key: apiKey
    });
}
```

---

### Security Issue D: Base64 Fallback for Failed Encryption

**Location**: `socratic_system/agents/multi_llm_agent.py:778-783`

```python
except Exception as e:
    self.logger.warning(f"Encryption failed, using base64 fallback: {e}")
    # Fallback to base64 if crypto unavailable
    return base64.b64encode(api_key.encode()).decode()  # ← UNENCRYPTED!
```

**Problem**:
- If Fernet library fails, falls back to base64 (NOT encryption)
- Base64 is encoding, not encryption - easily decoded
- Silent failure - no error raised

**Fix**: Fail hard instead of silent fallback
```python
except Exception as e:
    self.logger.error(f"Encryption failed and cannot proceed: {e}")
    raise RuntimeError(f"Failed to encrypt API key: {e}") from e
```

---

## 🔴 CRITICAL ISSUES (Will Block Execution)

### Issue 1: Wrong Module Path in start-dev.bat

**Location**: `scripts/start-dev.bat`, Line 96

**Current Code**:
```batch
start cmd /k "title Socrates Backend && python -m uvicorn socratic_system.main:app --host 0.0.0.0 --port 8000 --reload"
```

**Problem**:
- The script tries to run `socratic_system.main:app` but the backend is in `socrates_api/src/socrates_api/main.py`
- This will fail with: `ModuleNotFoundError: No module named 'socratic_system'`
- Users on Windows cannot run the development server

**Fix**:
```batch
start cmd /k "title Socrates Backend && python -m uvicorn socrates_api.main:app --host 0.0.0.0 --port 8000 --reload"
```

---

### ✅ RESOLVED: API Key Configuration

**Status**: NOT AN ISSUE - API keys are entered via Frontend/CLI and stored safely in database

**How it works** (verified in codebase):
1. Users enter API key in Frontend Settings UI (`socrates-frontend/src/components/llm/LLMSettingsPage.tsx`)
2. OR users provide key via CLI with `click.prompt("Enter your Claude API key", hide_input=True)`
3. Key is encrypted using Fernet (PBKDF2-SHA256 + symmetric encryption) in `multi_llm_agent.py:738-783`
4. Encrypted key is stored in SQLite database (`api_keys` table)
5. System has fallback to `ANTHROPIC_API_KEY` env var if set

**Security implementation**:
- ✅ Encrypted at rest with Fernet (symmetric encryption)
- ✅ Hashed separately for verification (SHA256)
- ✅ CLI hides input with `hide_input=True`
- ✅ Per-user API key management in database

**Remaining concerns** (see section below):

---

### Issue 3: Insecure Database Encryption Key

**Location**: `.env` file, Line 15

**Current Code**:
```env
SECURITY_DATABASE_ENCRYPTION=true
DATABASE_ENCRYPTION_KEY=SocrateMasterKey32CharacterString123456
```

**Problem**:
- The encryption key is a placeholder string, not a secure random key
- Even though it's 32 characters, it's predictable and should never be in source
- This is a security vulnerability if the `.env` file is checked into git
- The comment above correctly explains it should be 32-character random, but the value doesn't follow this

**Impact**:
- False sense of security; the encryption provides minimal protection
- If `.env` is accidentally committed, the database is not actually secure
- Production deployments will be vulnerable

**Fix**:
1. Regenerate with secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. Update `.env`:
```env
DATABASE_ENCRYPTION_KEY=<generated-secure-key>
```

3. Add `.env` to `.gitignore` (should already be there, but verify)

---

## 🟠 HIGH PRIORITY ISSUES (Will Confuse Users)

### Issue 4: Port Mismatch Between .env and start-dev.bat

**Locations**:
- `.env`: Line 7 (`SOCRATES_API_PORT=8009`)
- `scripts/start-dev.bat`: Line 96 (`--port 8000`)

**Problem**:
- The `.env` file specifies port 8009
- The startup script uses port 8000
- The README shows port 8000
- This inconsistency causes confusion about which port the API is actually running on

**Current .env**:
```env
SOCRATES_API_PORT=8009
```

**Current start-dev.bat**:
```batch
python -m uvicorn socratic_system.main:app --host 0.0.0.0 --port 8000 --reload
```

**Impact**:
- Users might try to access http://localhost:8009 when the API is on 8000
- Environment variable is ignored, user might think it's not working
- Confusing for debugging and configuration

**Fix**: Standardize on port 8000:
```env
SOCRATES_API_PORT=8000
```

---

### Issue 5: Frontend Port Documentation Mismatch

**Locations**:
- `README.md`: Line 44 ("http://localhost:3000")
- `scripts/start-dev.bat`: Line 88 ("http://localhost:5173")
- `docs/INSTALLATION.md`: Line 320 (shows 5173)

**Problem**:
- README says Frontend runs on port 3000
- Actual Vite dev server runs on port 5173 (default)
- start-dev.bat correctly shows 5173 but README doesn't match
- Docker Compose might expose 3000, but local dev doesn't

**Impact**:
- New users follow README, go to http://localhost:3000, get nothing
- Confusing first-time experience
- Multiple places showing different ports

**Fix**:
1. Update README.md line 44:
```markdown
# Access at http://localhost:5173 (Frontend) and http://localhost:8000 (API)
```

2. Consider adding a note about Docker vs local dev:
```markdown
### Docker Compose (Local Development)
Frontend: http://localhost:3000 (via Nginx reverse proxy)
API: http://localhost:8000

### Local Development (python/npm)
Frontend: http://localhost:5173 (Vite dev server)
API: http://localhost:8000
```

---

### Issue 6: README References Non-Existent Example Files

**Location**: `README.md`, Line 39 and 201

**Current Code**:
```markdown
cp .env.production.example .env.local
```

**Problem**:
- The file is actually named `.env.example` or `.env.production.example` in `deployment/configurations/`
- Not in the root directory where the user expects it
- Running this command will fail: `cp: cannot stat '.env.production.example': No such file or directory`

**Files Actually Available**:
- `deployment/configurations/.env.example`
- `deployment/configurations/.env.production.example`
- `socrates-frontend/.env.example`

**Impact**:
- First step in the Quick Start fails
- New users get immediate failure before even trying to run anything
- Very bad first impression

**Fix**: Update README to be precise:
```bash
# For local development
cp deployment/configurations/.env.example .env

# For production
cp deployment/configurations/.env.production.example .env.production
```

Or create `.env.example` in the root directory.

---

## 🟡 MEDIUM PRIORITY ISSUES

### Issue 7: Missing Frontend .env Configuration

**Location**: `socrates-frontend/.env.example`

**Current File**:
```env
VITE_API_URL=http://localhost:8000

VITE_APP_NAME=Socrates
VITE_APP_VERSION=0.1.0

VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_WEBSOCKET=true
```

**Problem**:
- The `.env.example` exists, but the actual `.env` is never created by the startup script
- The start-dev.bat doesn't copy `.env.example` to `.env` for the frontend
- If the user modifies the port or API URL, they won't know to update this

**Impact**:
- If user runs on a different machine/port, frontend won't connect to API
- Users might not realize they need to configure this
- Silent failure if API URL doesn't match

**Recommendation**:
Update `start-dev.bat` to also handle frontend env setup:

```batch
REM Copy frontend .env if it doesn't exist
if not exist "socrates-frontend\.env" (
    echo.
    echo Configuring frontend environment...
    copy socrates-frontend\.env.example socrates-frontend\.env
    if errorlevel 1 (
        echo [WARNING] Failed to create frontend .env
        REM Continue anyway, might be okay
    )
)
```

---

### Issue 8: Unclear Database Setup Instructions

**Location**: `README.md` and `docs/INSTALLATION.md`

**Problem**:
- The README doesn't mention database initialization
- No clear instructions on whether user needs PostgreSQL or if SQLite is used
- Users might expect a database but don't know how to set it up
- Docker Compose sets up PostgreSQL, but local dev doesn't explain this

**What the Code Actually Does**:
- Local development uses SQLite (`.env` shows `DATABASE_URL=sqlite:///./socrates.db`)
- Docker Compose uses PostgreSQL (with automatic setup)
- No mention of running `alembic upgrade head` for migrations

**Impact**:
- Users might try to install PostgreSQL unnecessarily
- Or assume the system is broken if they don't have it
- Database migrations might not run automatically

**Recommendation**:
Add to README Quick Start section:

```markdown
## Quick Start

### Docker Compose (Local Development - Recommended)

**Database**: Automatic PostgreSQL setup
**Requirements**: Docker and Docker Compose only

```bash
docker-compose up -d
# Wait for services to be ready (30-60 seconds)
# Access: Frontend http://localhost:3000, API http://localhost:8000
```

### Local Development (Without Docker)

**Database**: SQLite (automatic)
**Requirements**: Python 3.9+, Node.js 14+

```bash
# Setup
cp deployment/configurations/.env.example .env
python -m venv venv
source venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run database migrations (first time only)
alembic upgrade head

# Start services
scripts/start-dev.sh  # or start-dev.bat on Windows
```
```

---

## 📋 Testing Checklist for First-Time Users

A new user should be able to:

- [ ] Clone repository
- [ ] Follow Quick Start instructions exactly as written
- [ ] Get the system running without errors
- [ ] Access Frontend UI at documented URL
- [ ] Access API docs at documented URL
- [ ] Create a test project
- [ ] Use AI features (requires API key)

**Current State**: Would FAIL on steps 3, 4, and 6 without fixes.

---

## 🔧 Recommended Fixes (Priority Order)

### MUST FIX (Before Release):
1. ✅ Fix module path in `start-dev.bat` (Issue 1)
2. ✅ Add Anthropic API Key to `.env` configuration (Issue 2)
3. ✅ Fix `.env.example` path in README (Issue 6)

### SHOULD FIX (Before Next Release):
4. ✅ Secure the database encryption key (Issue 3)
5. ✅ Standardize API port in `.env` (Issue 4)
6. ✅ Fix frontend port in README (Issue 5)

### NICE TO FIX (Improvement):
7. ✅ Add frontend `.env` auto-configuration to startup script (Issue 7)
8. ✅ Add clear database setup documentation (Issue 8)

---

## Summary Table

| Issue | Severity | Component | Impact | Status |
|-------|----------|-----------|--------|--------|
| **SETUP ISSUES** | | | | |
| Wrong module path | 🔴 Critical | start-dev.bat | Cannot start backend on Windows | TO FIX |
| Insecure encryption key | 🔴 Critical | .env | False security | TO FIX |
| Port mismatch | 🟠 High | .env + script | Confusion, connection issues | TO FIX |
| Frontend port wrong | 🟠 High | README | Users access wrong URL | TO FIX |
| Wrong .env path | 🟠 High | README | First step fails | TO FIX |
| No frontend .env setup | 🟡 Medium | start-dev.bat | Fragile setup | TO FIX |
| Unclear DB setup | 🟡 Medium | Documentation | User confusion | TO FIX |
| **SECURITY ISSUES** | | | | |
| Static PBKDF2 salt | 🟠 Medium | multi_llm_agent.py | Reduced encryption strength | TO FIX |
| Hardcoded default key | 🔴 Critical | multi_llm_agent.py | No encryption if env not set | TO FIX |
| API key in URL params | 🟠 Medium | llm.ts | Key visible in logs/history | TO FIX |
| Base64 fallback | 🔴 Critical | multi_llm_agent.py | Unencrypted fallback | TO FIX |

---

## Conclusion

Socrates is well-architected with excellent documentation overall, but these **8 configuration and instruction issues** would significantly impair a new user's onboarding experience. Fixing the 3 critical issues is essential before this can be considered production-ready for self-serve deployments.

The fixes are straightforward and low-risk. Once implemented, the setup experience would be smooth and welcoming for new users discovering Socrates on GitHub.

---

**Recommendations**:
1. Create a setup checklist in CI/CD to test fresh clones
2. Have a new user test the Quick Start against a clean clone
3. Add automated tests to verify `.env` examples match actual configuration
4. Document any platform-specific setup needs clearly
