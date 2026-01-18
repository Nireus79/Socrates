# Installation & Setup Guide

This guide covers installing Socrates AI and preparing it for use.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 2GB for data and logs
- **Internet**: Required for Claude API access

### Recommended Requirements

- **Python**: 3.11 or higher
- **RAM**: 8GB or more
- **Storage**: SSD for vector database performance
- **CPU**: 2+ cores for concurrent operations

### Supported Platforms

- ✅ Ubuntu 20.04+
- ✅ macOS 10.14+
- ✅ Windows 10/11
- ✅ Docker (containerized deployment)
- ✅ WSL2 (Windows Subsystem for Linux)

---

## Prerequisites

### 1. Python Installation

**Check Python version**:
```bash
python --version
# or
python3 --version
```

**If Python is not installed**:

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

**macOS**:
```bash
brew install python@3.11
```

**Windows**:
- Download from [python.org](https://www.python.org/downloads/)
- Run installer, **check "Add Python to PATH"**
- Verify: `python --version`

### 2. Get Anthropic API Key

Required for using Claude AI.

1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)
6. **Keep this secret!** Never commit to version control

### 3. Node.js & npm (Required for Web Frontend)

Required if you plan to use the web frontend with `python socrates.py --full`.

**Check if installed**:
```bash
node --version
npm --version
```

**Ubuntu/Debian**:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

**macOS**:
```bash
brew install node
```

**Windows**:
- Download from [nodejs.org](https://nodejs.org/) (LTS version)
- Run installer with defaults
- Verify: `node --version` and `npm --version`

### 4. Git Installation (Optional but Recommended)

**Ubuntu/Debian**:
```bash
sudo apt install git
```

**macOS**:
```bash
brew install git
```

**Windows**:
- Download from [git-scm.com](https://git-scm.com/download/win)
- Run installer with defaults

---

## Installation Steps

### Step 1: Clone or Download the Repository

**Option A: Clone with Git** (recommended)
```bash
git clone https://github.com/your-org/socrates.git
cd socrates
```

**Option B: Download ZIP**
1. Visit repository on GitHub
2. Click "Code" → "Download ZIP"
3. Extract to desired location
4. Open terminal in extracted folder

### Step 2: Create Virtual Environment

A virtual environment isolates project dependencies from system Python.

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# On Linux/macOS:
source .venv/bin/activate

# On Windows (Command Prompt):
.venv\Scripts\activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Verify activation (should show (.venv) prefix)
```

### Step 3: Install Dependencies

```bash
# Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel

# Install project dependencies
pip install -r requirements.txt
```

**What gets installed**:
- `anthropic` - Claude API client
- `chromadb` - Vector database
- `sentence-transformers` - Embedding model
- `PyPDF2` - PDF processing
- `colorama` - Terminal colors
- `python-dateutil` - Date utilities
- And dependencies of above

**Installation time**: 3-10 minutes (depends on internet speed)

### Step 4: Configure API Key

**Option A: Environment Variable** (recommended)

**Linux/macOS**:
```bash
export ANTHROPIC_API_KEY="sk-ant-your-actual-key-here"

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (Command Prompt)**:
```cmd
setx ANTHROPIC_API_KEY sk-ant-your-actual-key-here
# Restart terminal for changes to take effect
```

**Windows (PowerShell)**:
```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-your-actual-key-here", "User")
# Restart PowerShell
```

**Option B: .env File** (for development)

Create `.env` file in project root:
```bash
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
SOCRATES_LOG_LEVEL=INFO
SOCRATES_DATA_DIR=~/.socrates
```

Then load it before running:
```bash
export $(cat .env | xargs)
python socrates.py
```

**Option C: Interactive Prompt** (fallback)

If not configured, Socrates will ask for API key on startup.

### Step 5: (Optional) Configure Data Directory

By default, Socrates stores data in `~/.socrates`. To use a custom location:

**Linux/macOS**:
```bash
export SOCRATES_DATA_DIR="/custom/path/to/socrates"
```

**Windows**:
```cmd
setx SOCRATES_DATA_DIR "C:\custom\path\to\socrates"
```

Or set in `.env`:
```
SOCRATES_DATA_DIR=/custom/path
```

---

## Entry Points & Startup Options

After installation, you can start Socrates in different ways depending on your use case.

### Running Socrates

All commands are run from the project root directory where `socrates.py` is located:

```bash
cd path/to/Socrates  # Navigate to project root
```

### Available Entry Points

#### 1. Interactive CLI (Default)

**Command:**
```bash
python socrates.py
```

**What it starts:**
- Terminal-based interactive interface
- Command prompt for Socratic dialogue
- Full CLI functionality

**Best for:**
- Learning and testing
- Interactive development
- Rapid prototyping
- Users without web UI requirements

**Output:**
```
╔══════════════════════════════════════════════════════╗
║         🤔 Socrates AI                               ║
║      Version 1.3.0 - "Know Thyself"                  ║
╚══════════════════════════════════════════════════════╝

Socrates> /help
```

---

#### 2. Full Stack (API + Web Frontend)

**Command:**
```bash
python socrates.py --full
```

**What it starts:**
- REST API server on `http://localhost:8000`
- React web frontend on `http://localhost:5173`
- Automatic browser opening
- Auto-port detection (uses next available port if primary is busy)

**Best for:**
- Full experience with visual interface
- Web-based project management
- Team collaboration
- Programmatic API access + UI interaction
- Production-like environment (local)

**Services:**
- **API Server**: `http://localhost:8000`
  - REST endpoints for all operations
  - WebSocket for real-time updates
  - Health check: `GET /health`
  - API docs: `GET /docs` (OpenAPI/Swagger)
- **Frontend**: `http://localhost:5173`
  - Visual dashboard
  - Project management UI
  - Real-time collaboration features

**Shutdown:**
- Press `Ctrl+C` to stop all services
- Graceful shutdown of both API and frontend

---

#### 3. API Server Only

**Command:**
```bash
python socrates.py --api
```

**What it starts:**
- REST API server only (no frontend)
- Listens on `0.0.0.0:8000` by default
- Auto-port detection if port 8000 is busy

**Best for:**
- Integration with other applications
- Headless/server-only deployments
- Building custom frontends
- Automation and scripting
- Production deployments

**API Access:**
```bash
# Health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs

# Example: Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project"}'
```

---

#### 4. CLI with Web Frontend

**Command:**
```bash
python socrates.py --frontend
```

**What it starts:**
- Interactive CLI interface
- React web frontend alongside CLI
- Both services run simultaneously

**Best for:**
- Hybrid workflow
- Visual dashboard + terminal interface
- Development and testing
- Power users who want both interfaces

**Services:**
- **CLI**: Terminal-based interface
- **Frontend**: `http://localhost:5173`

---

### Port Configuration

#### Default Ports

| Service | Default Port | Environment Variable |
|---------|--------------|----------------------|
| API Server | 8000 | (set with --port flag) |
| Frontend (Vite) | 5173 | PORT |
| Health Check | 8000 | (same as API) |

#### Custom Port for API

**Specific port:**
```bash
python socrates.py --api --port 9000

# API runs on http://localhost:9000
```

**Disable auto-detection (fail if port busy):**
```bash
python socrates.py --api --port 8000 --no-auto-port
```

**Custom host (instead of 0.0.0.0):**
```bash
python socrates.py --api --host 127.0.0.1

# API only accessible from localhost
```

#### Frontend Port

Set via environment variable:
```bash
PORT=3000 python socrates.py --full

# Frontend runs on http://localhost:3000
```

---

### Auto-Port Detection

By default, Socrates automatically detects available ports:

```bash
python socrates.py --api

# If port 8000 is busy:
# [INFO] Port 8000 is in use, using port 8001 instead
# [INFO] API server running on http://localhost:8001
```

To disable this behavior:
```bash
python socrates.py --api --no-auto-port

# Fails if port 8000 is not available
```

---

### Help & Version Information

**Show all available commands:**
```bash
python socrates.py --help
```

**Output:**
```
usage: socrates [-h] [--version] [--api | --full | --frontend] [--host HOST]
                [--port PORT] [--no-auto-port] [--reload]

Socrates AI - A Socratic method tutoring system powered by Claude AI

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --api                 Start API server only
  --full                Start full stack (API + Frontend)
  --frontend            Start CLI with React frontend
  --host HOST           API server host (default: 0.0.0.0)
  --port PORT           API server port (default: 8000)
  --no-auto-port        Disable automatic port detection
  --reload              Enable auto-reload for API (development only)

Examples:
  python socrates.py                    Start CLI (default)
  python socrates.py --api              Start API server only
  python socrates.py --full             Start full stack
  python socrates.py --api --port 9000  Start API on custom port
```

**Show version:**
```bash
python socrates.py --version

# Output: Socrates AI 1.1.0
```

---

### Environment Variables for Startup

Control startup behavior via environment variables:

```bash
# Enable debug logging
export SOCRATES_LOG_LEVEL=DEBUG
python socrates.py --api

# Set data directory
export SOCRATES_DATA_DIR=/data/socrates
python socrates.py

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...
python socrates.py --full

# Set frontend port
export PORT=3000
python socrates.py --full
```

---

### Troubleshooting Startup Issues

**Port already in use:**
```bash
# Auto-detection handles this, but you can:
python socrates.py --api --port 9000

# Or find what's using the port:
# Linux/macOS:
lsof -i :8000

# Windows:
netstat -ano | findstr :8000
```

**API connection error:**
```bash
# Verify API is running:
curl http://localhost:8000/health

# Check logs:
tail -f ~/.socrates/logs/socratic.log
```

**Frontend not starting:**
```bash
# Ensure npm is installed:
npm --version

# Install frontend dependencies manually:
cd socrates-frontend
npm install
npm run dev
```

---

## Configuration

### First-Time Setup

When you run Socrates for the first time:

1. **Create account**: Provide username and passcode
2. **Create data directories**: Automatically created at `~/.socrates`
3. **Initialize databases**:
   - SQLite: `projects.db` for projects and users
   - ChromaDB: `vector_db/` for knowledge base
4. **Load knowledge base**: Default knowledge loaded into vector database
5. **Initialize logging**: Log file created at `socratic_logs/socratic.log`

### Configuration Files

**Main configuration** (`~/.socrates/`):
```
~/.socrates/
├── projects.db              # SQLite database (projects, users)
├── vector_db/               # ChromaDB vector database
│   ├── chroma.sqlite3       # Vector store metadata
│   └── {collection_uuid}/   # Vector data
├── logs/
│   └── socratic.log         # Application log file
└── .env                     # (Optional) Local config
```

**Project configuration** (`./socratic_system/config/`):
```
socratic_system/config/
└── knowledge_base.json      # Default knowledge entries
```

### Logging Configuration

**Default log level**: `INFO` (warnings and errors only)

To enable debug logging:

```bash
export SOCRATES_LOG_LEVEL=DEBUG
python socrates.py
```

Or configure in code:
```python
from socratic_system.config import ConfigBuilder

config = ConfigBuilder("sk-ant-...") \
    .with_log_level("DEBUG") \
    .build()
```

**Log file location**: `~/.socrates/logs/socratic.log`

View recent logs:
```bash
tail -f ~/.socrates/logs/socratic.log
```

---

## Running Socrates

After installation, you can run Socrates in different modes:

### Mode 1: Full Stack (API + Web Frontend)

**Recommended for**: Visual users, collaboration, web-based development

```bash
python socrates.py --full
```

**What starts**:
- API Server: http://localhost:8000
- React Web UI: http://localhost:5173

**Next steps**:
1. Open browser to http://localhost:5173
2. Login or create account
3. Create new project
4. Collaborate with team members

**Requirements**:
- Node.js and npm installed
- Ports 8000 and 5173 available

### Mode 2: API Server Only

**Recommended for**: Developers, integrations, programmatic access

```bash
python socrates.py --api
```

**What starts**:
- API Server: http://localhost:8000
- Swagger API docs: http://localhost:8000/docs

**Next steps**:
1. Use API endpoints directly
2. Build custom frontends
3. Integrate with other tools

**Example API call**:
```bash
curl http://localhost:8000/api/health
```

### Mode 3: Interactive CLI (Default)

**Recommended for**: Quick testing, terminal users, headless systems

```bash
python socrates.py
```

**What starts**:
- Interactive CLI interface
- Terminal-based project management
- Commands like `/project create`, `/code generate`

**Features**:
- No browser required
- Works over SSH
- Lightweight

**Type `/help` for available commands**

---

## Verification

### Test Installation

```bash
# Ensure virtual environment is active
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Start Socratic
python socrates.py
```

**Expected output**:
```
╔══════════════════════════════════════════════════════╗
║         🤔 Socrates AI                               ║
║      Version 1.3.0 - "Know Thyself"                  ║
╚══════════════════════════════════════════════════════╝

[INFO] system: Initializing Socrates AI...
[INFO] system: Loading knowledge base...
[INFO] system: System initialized successfully
```

### First-Time User Flow

1. **Authenticate**:
   ```
   Username: alice
   New user? (y/n): y
   Create passcode: ****
   ```

2. **Main menu**:
   ```
   Welcome, alice!
   /project create    - Create new project
   /project list      - List your projects
   /help              - Show all commands
   ```

3. **Create test project**:
   ```
   /project create
   Project name: Test Project

   🤔 What specific problem or frustration in people's daily
   lives are you hoping this project will solve?
   > (type your answer)
   ```

### Verify Components

```bash
# Check Python packages installed
pip list | grep -E "anthropic|chromadb|sentence-transformers"

# Check database initialization
ls -la ~/.socrates/

# Check logs
tail ~/.socrates/logs/socratic.log

# Run system status command (in CLI)
/status
```

---

## Troubleshooting

### Common Issues

#### 1. Python Not Found

**Error**: `command not found: python`

**Solution**:
```bash
# Use python3 explicitly
python3 socrates.py

# Or create alias
alias python=python3
```

#### 2. API Key Not Configured

**Error**: `ValueError: API key required`

**Solution**:
```bash
# Set environment variable
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify it's set
echo $ANTHROPIC_API_KEY

# Then run
python socrates.py
```

#### 3. Virtual Environment Not Activated

**Error**: `ModuleNotFoundError: No module named 'anthropic'`

**Solution**:
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# You should see (.venv) prefix in terminal
```

#### 4. Permission Denied

**Error**: `Permission denied` when creating `.venv`

**Solution**:
```bash
# Check directory permissions
ls -ld $(pwd)

# Try with sudo (not recommended for venv)
# Better: Change directory or use different location
cd /tmp/socrates  # Try in /tmp
python -m venv .venv
```

#### 5. Module Installation Fails

**Error**: `Could not build wheels for chromadb` or similar

**Solution**:
```bash
# Update pip first
pip install --upgrade pip setuptools wheel

# Install build tools
# Linux (Ubuntu):
sudo apt install build-essential python3-dev

# macOS:
brew install python3 python3-dev

# Windows: Install Visual C++ Build Tools

# Then retry
pip install -r requirements.txt
```

#### 6. Database Initialization Error

**Error**: `sqlite3.OperationalError: database is locked`

**Solution**:
```bash
# Close all running Socrates instances
# Delete lock file if it exists
rm ~/.socrates/.db.lock

# Restart Socrates
python socrates.py
```

#### 7. Port Already in Use

**Error**: `Address already in use` (if running API server)

**Solution**:
```bash
# Find process using port
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill process (use PID from above)
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows
```

#### 8. Insufficient Disk Space

**Error**: `No space left on device`

**Solution**:
```bash
# Check disk usage
df -h  # Linux/macOS
dir C:\ /s  # Windows

# Clear cache (if needed)
rm -rf ~/.socrates/vector_db/__pycache__
rm -rf .venv
# Reinstall dependencies if needed
```

#### 9. Network Connection Error

**Error**: `Failed to connect to API` or timeout

**Solution**:
```bash
# Check internet connection
ping google.com

# Check if Anthropic API is accessible
curl https://api.anthropic.com

# Check proxy settings (if behind corporate proxy)
pip install --proxy [user:passwd@]proxy.server:port ...
```

#### 10. Character Encoding Issues

**Error**: `UnicodeEncodeError` or garbled text

**Solution**:
```bash
# Set UTF-8 encoding
export PYTHONIOENCODING=utf-8  # Linux/macOS
set PYTHONIOENCODING=utf-8     # Windows

# Or in ~/.bashrc or ~/.zshrc
echo 'export PYTHONIOENCODING=utf-8' >> ~/.bashrc
```

---

## Uninstallation

To completely remove Socrates:

```bash
# Remove virtual environment
rm -rf .venv

# Remove data directory (keeps everything)
rm -rf ~/.socrates

# Remove from system (if installed via pip)
pip uninstall socrates-ai-cli socrates-ai-api

# Remove repository
rm -rf socrates
```

---

## Docker Installation (Optional)

For containerized deployment:

```bash
# Build Docker image
docker build -t socratic-rag .

# Run container
docker run -it \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  -v ~/.socrates:/home/socratic/.socrates \
  socratic-rag

# Or using docker-compose
docker-compose up
```

See `Dockerfile` and `docker-compose.yml` in repository root.

---

## Next Steps

After successful installation:

1. **Read [USER_GUIDE.md](USER_GUIDE.md)** - Learn how to use the system
2. **Create your first project** - Run `/project create`
3. **Enable debug mode** - Run `/debug on` to see detailed logs
4. **Check [CONFIGURATION.md](CONFIGURATION.md)** - Customize settings

---

## Getting Help

If you encounter issues:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common problems
2. Review logs: `~/.socrates/logs/socratic.log`
3. Enable debug mode: `/debug on`
4. Check [API_REFERENCE.md](API_REFERENCE.md) for system capabilities
5. Submit issue on GitHub with:
   - Python version: `python --version`
   - OS: `uname -a` (Linux/macOS) or `systeminfo` (Windows)
   - Error message and logs
   - Steps to reproduce

---

## Advanced Setup

### Development Installation

For contributing to the project:

```bash
# Clone repository
git clone https://github.com/your-org/socrates.git
cd socrates

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black socratic_system tests
ruff check socratic_system tests

# Type checking
mypy socratic_system
```

### Custom Knowledge Base

```python
config = ConfigBuilder("sk-ant-...") \
    .with_custom_knowledge([
        "Your custom knowledge here...",
        "More knowledge entries..."
    ]) \
    .with_knowledge_base(Path("/path/to/custom/kb.json")) \
    .build()

orchestrator = AgentOrchestrator(config)
```

### Multi-User Deployment

For team deployment, use shared databases:

```python
config = ConfigBuilder("sk-ant-...") \
    .with_data_dir(Path("/shared/socrates/data")) \
    .build()

# Share data_dir across users/machines
```

---

## System Optimization

### For Large Projects

```bash
# Increase available RAM for vector searches
export PYTHONUNBUFFERED=1
export PYTHONOPTIMIZE=2

# Run with more memory
python -O socrates.py
```

### For High Concurrency

See [ARCHITECTURE.md - Scaling Considerations](ARCHITECTURE.md#scaling-considerations)

---

**Last Updated**: January 2026
**Version**: 1.3.0
