# Socrates Setup Guide

## First-Time Setup (Automatic)

When you first run Socrates, it will automatically set up required environment variables:

```bash
python socrates.py --full
```

**What happens automatically:**
- ✅ Generates `JWT_SECRET_KEY` (required for API security)
- ✅ Sets up default configuration
- ✅ Creates `.env` file with settings
- ✅ Validates everything is ready

## Manual Setup

If you need to set up manually or reconfigure:

```bash
python setup_env.py
```

This will:
1. Generate or use existing JWT_SECRET_KEY
2. Check for ANTHROPIC_API_KEY
3. Create `.env` file with all defaults
4. Show next steps

## Understanding the Setup

### Why JWT_SECRET_KEY?

The API uses JWT (JSON Web Tokens) for authentication. The `JWT_SECRET_KEY` is a secret key that signs these tokens to prevent tampering.

- **Generated automatically** for development
- **Must be different** in production (use a strong, random key)
- **Keep it secret** - don't commit to git

### What Gets Created?

Running setup creates a `.env` file with:

```bash
JWT_SECRET_KEY=<random-secure-key>              # API security
ANTHROPIC_API_KEY=<your-api-key>                # Optional, add later
SOCRATES_DATA_DIR=~/.socrates                   # Data storage location
SOCRATES_API_HOST=127.0.0.1                     # API server address
SOCRATES_API_PORT=8000                          # API server port
ENVIRONMENT=development                          # development or production
```

## Running Socrates

### After Setup

```bash
# Full stack (API + Frontend)
python socrates.py --full

# API only
python socrates.py --api

# CLI only
python socrates.py

# Frontend only
python socrates.py --frontend
```

### What Each Mode Does

| Command | What Starts | Port |
|---------|------------|------|
| `--full` | API + Frontend | 8000 + 5173 |
| `--api` | REST API only | 8000 |
| (default) | CLI only | - |
| `--frontend` | CLI + React UI | 5173 |

## Adding Your API Key

### Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Create account or sign in
3. Generate API key in settings
4. Copy the key

### Add to Socrates

**Option 1: Edit .env file**

```bash
# Open .env and add/update:
ANTHROPIC_API_KEY=sk-ant-xxx...
```

**Option 2: Set environment variable**

```bash
# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-xxx..."

# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-xxx..."

# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-xxx...
```

**Option 3: Use in app**

Users can add API key through the app UI:
- Open http://localhost:5173
- Settings → LLM → Anthropic
- Enter API key

## Troubleshooting

### API won't start - JWT_SECRET_KEY error

```
Failed to load auth_router router: CRITICAL: JWT_SECRET_KEY environment variable is not set
```

**Solution:**
```bash
python setup_env.py
# or
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

### Port already in use

The API automatically tries the next available port.

To use a specific port:
```bash
python socrates.py --api --port 9000
```

To fail if port is busy (instead of auto-detecting):
```bash
python socrates.py --api --no-auto-port --port 8000
```

### Frontend not loading

Check browser console for errors:
1. Open http://localhost:5173
2. Press F12 (Dev Tools)
3. Check Console tab for errors

Common causes:
- API not running (check http://localhost:8000/health)
- Port conflict (try `--port` flag)
- Missing ANTHROPIC_API_KEY

### Can't find setup_env.py

Make sure you're in the Socrates directory:

```bash
cd /path/to/Socrates
python setup_env.py
```

## Configuration Details

### Environment Variables

**Required:**
- `JWT_SECRET_KEY` - API security (auto-generated)

**Recommended:**
- `ANTHROPIC_API_KEY` - Your Claude API key

**Optional:**
- `SOCRATES_DATA_DIR` - Where to store data (default: `~/.socrates`)
- `SOCRATES_API_HOST` - API address (default: `127.0.0.1`)
- `SOCRATES_API_PORT` - API port (default: `8000`)
- `ENVIRONMENT` - `development` or `production`

### Data Locations

- **Projects**: `~/.socrates/projects.db`
- **Knowledge**: `~/.socrates/vector_db/`
- **API Data**: `~/.socrates/api_projects.db`

## Development vs Production

### Development (Default)

```bash
ENVIRONMENT=development
JWT_SECRET_KEY=auto-generated
CORS=enabled for localhost
```

Use for testing and learning.

### Production

```bash
ENVIRONMENT=production
JWT_SECRET_KEY=strong-secret-key
CORS=restricted to your domain
```

For production deployment:
1. Generate a strong key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
2. Use environment variables, not `.env` file
3. Set `ENVIRONMENT=production`
4. Restrict CORS origins
5. Use HTTPS
6. Secure your ANTHROPIC_API_KEY

## Getting Help

If you encounter issues:

1. Check logs in the terminal
2. Read error messages carefully (they usually explain the fix)
3. Run `python setup_env.py` to reset configuration
4. Check `~/.socrates/` for data files

## Next Steps

1. ✅ Run `python socrates.py --full` to start
2. ✅ Browser opens to http://localhost:5173
3. ✅ Add your API key in Settings
4. ✅ Start creating projects!

---

**Everything configured? You're ready to go! 🚀**
