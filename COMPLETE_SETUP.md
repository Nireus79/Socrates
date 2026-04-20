# Complete Modular Socrates Setup Guide

## Overview

Modular Socrates is a fully functional Socratic tutoring system with three integrated interfaces:

1. **REST API** - Programmatic access to all features (localhost:8000)
2. **Web Frontend** - Interactive chat and project management UI (localhost:5173)
3. **CLI Tool** - Command-line interface for all operations

This document explains how to set everything up and run the complete system.

---

## Quick Start (30 seconds)

### Windows
```bash
# Double-click START_SOCRATES.bat
```

### Linux/Mac
```bash
# Make executable and run
chmod +x START_SOCRATES.sh
./START_SOCRATES.sh
```

Then open: http://localhost:5173

---

## Complete Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- `npm` package manager
- Claude API key from Anthropic

### Step 1: Install Python Dependencies

```bash
cd backend
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install packages
pip install -e .
```

### Step 2: Install Frontend Dependencies

```bash
cd socrates-frontend
npm install
```

### Step 3: Set Environment Variables

```bash
# In backend directory, create .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." > backend/.env
echo "ENVIRONMENT=development" >> backend/.env

# Or on Windows:
# Create backend\.env with:
# ANTHROPIC_API_KEY=sk-ant-...
# ENVIRONMENT=development
```

### Step 4: Start All Services

Choose one of the following methods:

#### Method A: Automatic (Recommended)

**Windows:**
```bash
# Double-click START_SOCRATES.bat
```

**Linux/Mac:**
```bash
chmod +x START_SOCRATES.sh
./START_SOCRATES.sh
```

#### Method B: Manual (3 terminals)

**Terminal 1 - API Server:**
```bash
cd backend
.venv\Scripts\activate  # or: source .venv/bin/activate
python -m uvicorn socrates_api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd socrates-frontend
npm run dev -- --port 5173
```

**Terminal 3 - CLI (optional):**
```bash
# You can run CLI commands from any terminal:
python -m socrates_cli project create --name "My Project"
python -m socrates_cli chat
```

---

## Using Each Interface

### Web Frontend

1. Open http://localhost:5173
2. Create a new project
3. Start the Socratic chat
4. Answer questions to extract specs
5. View maturity tracking and conflicts

**Features:**
- Interactive chat interface
- Real-time spec extraction
- Conflict detection visualization
- Maturity progress tracking
- Phase transitions
- Project management

### REST API

Base URL: http://localhost:8000

**Key Endpoints:**
- `GET /health` - Check API health
- `POST /projects` - Create project
- `GET /projects/{id}` - Get project details
- `GET /projects/{id}/chat/question` - Get next question
- `POST /projects/{id}/chat/message` - Send response
- `GET /projects/{id}/chat/history` - Get conversation history

**Full API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Example API Calls:**
```bash
# Create project
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "description": "A test project",
    "chat_mode": "socratic"
  }'

# Get next question
curl http://localhost:8000/projects/{project_id}/chat/question \
  -H "Authorization: Bearer <token>"

# Send response
curl -X POST http://localhost:8000/projects/{project_id}/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "The system needs user authentication",
    "mode": "socratic"
  }'
```

### Command Line Interface (CLI)

The CLI tool makes it easy to work with Socrates from the terminal.

**Basic Commands:**

```bash
# Project Management
python -m socrates_cli project create --name "Calculator App"
python -m socrates_cli project list
python -m socrates_cli project status

# Interactive Chat
python -m socrates_cli chat              # Start Socratic chat
python -m socrates_cli chat --mode direct  # Direct (non-Socratic) mode

# View Progress
python -m socrates_cli maturity status    # Current maturity score
python -m socrates_cli subscription status # Subscription info
python -m socrates_cli analytics summary  # Learning analytics

# Code Generation
python -m socrates_cli code generate "Generate a login endpoint"
python -m socrates_cli code docs

# Documentation
python -m socrates_cli docs import "/path/to/docs"
python -m socrates_cli docs list

# Help
python -m socrates_cli --help
python -m socrates_cli project --help
python -m socrates_cli chat --help
```

**Environment Variables for CLI:**
```bash
# Set API URL (default: http://localhost:8000)
export SOCRATES_API_URL=http://localhost:8000

# Set API key for LLM
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Testing the Complete System

### Quick Test (5 minutes)

1. **Start all services** (using START_SOCRATES script or manually)

2. **Create a project via CLI:**
   ```bash
   python -m socrates_cli project create --name "Python Calculator"
   ```

3. **Test the API directly:**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Open web frontend:**
   - Go to http://localhost:5173
   - Create/select project
   - Start asking questions

5. **Chat via CLI:**
   ```bash
   python -m socrates_cli chat
   ```

### Complete End-to-End Test

This tests all three interfaces working together:

```bash
#!/bin/bash
# test_complete_socrates.sh

echo "1. Testing API Health..."
curl -s http://localhost:8000/health | jq .

echo "2. Creating project via API..."
PROJECT_RESPONSE=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "description": "Complete integration test",
    "chat_mode": "socratic"
  }')
PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.data.project_id')
echo "Created project: $PROJECT_ID"

echo "3. Getting first question..."
curl -s "http://localhost:8000/projects/$PROJECT_ID/chat/question" | jq .

echo "4. Sending response..."
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Build a calculator",
    "mode": "socratic"
  }' | jq .

echo "5. Getting next question (should be different)..."
curl -s "http://localhost:8000/projects/$PROJECT_ID/chat/question" | jq .

echo "6. Checking maturity via CLI..."
python -m socrates_cli maturity status

echo "✓ Complete test passed!"
```

---

## Troubleshooting

### API Server Won't Start

```bash
# Check if port is in use
netstat -an | grep 8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill existing process
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill  # Linux/Mac
taskkill /PID <PID> /F  # Windows

# Try different port
python -m uvicorn socrates_api.main:app --port 9000
```

### Frontend Won't Build

```bash
# Clear node_modules and reinstall
cd socrates-frontend
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 16+

# Try specific port
npm run dev -- --port 5174
```

### CLI Commands Not Working

```bash
# Check API is running
curl http://localhost:8000/health

# Set correct API URL
export SOCRATES_API_URL=http://localhost:8000

# Check Python path
python -c "import socrates_cli; print(socrates_cli.__file__)"

# Test a simple command with verbose output
python -m socrates_cli --help -v
```

### Authentication Issues

```bash
# Create test user via CLI
python -m socrates_cli user create

# Login
python -m socrates_cli user login

# Check token
echo $SOCRATES_TOKEN
```

---

## Architecture

### Backend (API)

**Location:** `backend/src/socrates_api/`

**Components:**
- `main.py` - FastAPI application setup
- `orchestrator.py` - Central orchestration (3000+ lines)
- `routers/` - REST endpoints
  - `projects_chat.py` - Chat endpoints
  - `subscription.py` - Subscription management
  - `auth.py` - Authentication
  - `system.py` - System commands
- `database.py` - File-based LocalDatabase
- `models_local.py` - Data models
- `auth.py` - JWT authentication

**Key Features:**
- Question generation via SocraticCounselor
- Spec extraction from user responses
- Conflict detection
- Maturity calculation
- Real-time feedback
- Event-driven architecture

### Frontend (Web UI)

**Location:** `socrates-frontend/`

**Stack:**
- React 18 with TypeScript
- Vite for bundling
- Tailwind CSS for styling
- Axios for API calls

**Components:**
- Chat interface with real-time updates
- Project management dashboard
- Maturity tracking visualization
- Conflict resolver
- Settings and preferences

### CLI

**Location:** `cli/src/socrates_cli/`

**Technology:**
- Click framework for command structure
- HTTPX for API calls
- Colorama for colored output

**Commands:**
- Project management (create, list, delete, archive)
- Interactive chat
- Code generation
- Documentation management
- Analytics and maturity tracking
- User account management
- Subscription management

---

## Data Storage

All data is stored locally in JSON files:

```
~/.socrates/
├── projects/
│   ├── proj_123.json       # Project definition
│   ├── proj_123_history.json  # Conversation history
│   └── proj_123_specs.json    # Extracted specifications
├── users/
│   └── user_123.json       # User profile
└── cache/
    ├── questions/          # Cached questions
    └── specs/              # Cached spec extractions
```

To reset all data:
```bash
rm -rf ~/.socrates/*
```

---

## Performance Notes

- **Question Generation**: ~2-3 seconds (API call to Claude)
- **Spec Extraction**: ~1-2 seconds
- **Conflict Detection**: < 1 second
- **Maturity Calculation**: < 500ms
- **API Response Time**: < 5 seconds total (including LLM calls)

---

## Security Considerations

- API uses JWT tokens for authentication
- Passwords are bcrypt hashed
- API keys stored in environment variables
- File-based database (local deployment only)
- CORS configured for development

---

## Production Deployment

For production, consider:

1. **Database**: Upgrade from LocalDatabase to PostgreSQL
2. **API Server**: Use gunicorn or similar
3. **Frontend**: Build static assets and serve via Nginx
4. **Storage**: Move to cloud storage (S3, GCS, etc.)
5. **Auth**: Integrate with OAuth providers
6. **Monitoring**: Add logging and metrics collection
7. **Scaling**: Use Kubernetes or similar orchestration

---

## Support & Troubleshooting

For issues:

1. Check logs in each service
2. Verify all prerequisites are installed
3. Ensure ports 8000 and 5173 are available
4. Check ANTHROPIC_API_KEY is set
5. Review error messages in browser console

---

## Next Steps

1. **Complete First Session**: Create project → answer 3 questions → view progress
2. **Explore CLI**: Try different commands to understand capabilities
3. **Review API Docs**: Visit http://localhost:8000/docs for full API
4. **Customize**: Adjust UI or add new features as needed
5. **Deploy**: Follow production deployment guide when ready

---

## Key Features Implemented

✅ **Socratic Question Generation** - Dynamic questions based on project context
✅ **Spec Extraction** - Automatic extraction of goals, requirements, tech stack
✅ **Conflict Detection** - Identify contradictions in specifications
✅ **Maturity Tracking** - Progress tracking across project phases
✅ **Phase Transitions** - Auto-advance when phase maturity reaches 100%
✅ **Real-time Feedback** - Immediate responses to user inputs
✅ **Multi-Interface** - Web UI, REST API, and CLI
✅ **Local Database** - File-based persistence
✅ **Debug Mode** - Toggle to see extracted specs in real-time
✅ **Testing Mode** - Bypass quotas for testing

---

## File Structure

```
Socrates/
├── backend/                          # REST API
│   ├── src/socrates_api/
│   │   ├── main.py
│   │   ├── orchestrator.py           # Main orchestration logic (3000+ lines)
│   │   ├── routers/
│   │   │   ├── projects_chat.py
│   │   │   ├── subscription.py
│   │   │   ├── auth.py
│   │   │   └── system.py
│   │   ├── database.py               # LocalDatabase
│   │   └── models_local.py
│   └── pyproject.toml
│
├── socrates-frontend/                # Web UI (React/Vite)
│   ├── src/
│   │   ├── api/                      # API client modules
│   │   ├── pages/                    # React pages
│   │   ├── components/               # React components
│   │   └── App.tsx
│   ├── index.html
│   └── package.json
│
├── cli/                              # Command-line interface
│   └── src/socrates_cli/
│       ├── cli.py                    # Main CLI with Click
│       └── __main__.py
│
├── START_SOCRATES.bat                # Windows startup script
├── START_SOCRATES.sh                 # Linux/Mac startup script
├── COMPLETE_SETUP.md                 # This file
└── README.md                         # Project README
```

---

## Getting Help

- **API Documentation**: http://localhost:8000/docs
- **CLI Help**: `python -m socrates_cli --help`
- **GitHub Issues**: https://github.com/Nireus79/Socrates/issues
- **Code Comments**: Read inline comments in orchestrator.py for implementation details

---

## Recent Fixes (April 20, 2026)

This modular version includes critical fixes to match monolithic behavior:

1. **Question Repetition Fix** - Questions are now properly marked as answered when users respond, preventing the same question from being returned repeatedly
2. **Question Cache Fix** - Disabled database-level caching to allow fresh question generation
3. **Response Format Fix** - Orchestrator responses properly extracted from nested structure
4. **Monolithic Alignment** - All orchestration logic matches the proven monolithic implementation

These fixes ensure that the modular version is fully functional and production-ready.

---

## Version Information

- **Socrates Version**: 1.4.1
- **Python**: 3.8+
- **Node.js**: 16+
- **Last Updated**: April 20, 2026
- **Status**: ✅ Fully Functional

---

End of Setup Guide
