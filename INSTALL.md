# Installation Guide

Complete installation guide for all Socrates components.

## System Requirements

- **Python**: 3.8 or later
- **OS**: Linux, macOS, or Windows
- **RAM**: 2GB minimum (4GB recommended)
- **Disk Space**: 100MB for core installation

## Installation Options

### Option 1: Full Platform (Recommended)

Install everything: core, CLI, API, and all libraries.

```bash
pip install socrates-ai
```

This includes:
- `socratic-core` - Framework foundation
- `socratic-rag` - Knowledge management
- `socratic-agents` - Multi-agent orchestration
- `socratic-analyzer` - Code analysis
- `socratic-knowledge` - Enterprise knowledge
- `socratic-learning` - Learning system
- `socratic-workflow` - Workflow orchestration
- `socratic-conflict` - Conflict detection
- `socrates-nexus` - LLM foundation
- `socrates-cli` - Command-line interface
- `socrates-api` - REST API server

**Installation time**: 1-2 minutes
**Disk space**: 50-100MB

### Option 2: Core Framework Only

Minimal installation for developers building on Socrates.

```bash
pip install socratic-core
```

This includes:
- Configuration management
- Event system
- Exception hierarchy
- Logging infrastructure
- Utilities (ID generators, caching, etc.)

**Installation time**: 30 seconds
**Disk space**: 5-10MB
**Use case**: Building custom tools on top of Socrates

### Option 3: Core + CLI

Framework + command-line interface for local development.

```bash
pip install socratic-core socrates-cli
```

**Installation time**: 30 seconds
**Disk space**: 15-20MB
**Use case**: CLI-based workflows, CI/CD integration

### Option 4: Core + API

Framework + REST API server for application integration.

```bash
pip install socratic-core socrates-api
```

**Installation time**: 30 seconds
**Disk space**: 20-30MB
**Use case**: Server deployments, programmatic access

### Option 5: Core + Specific Libraries

Compose your own combination.

```bash
# Core + RAG (knowledge management)
pip install socratic-core socratic-rag

# Core + Agents (multi-agent orchestration)
pip install socratic-core socratic-agents

# Core + Analysis (code analysis)
pip install socratic-core socratic-analyzer

# Core + RAG + Agents
pip install socratic-core socratic-rag socratic-agents

# Core + everything except agents
pip install socratic-core socratic-rag socratic-analyzer socratic-knowledge
```

### Option 6: Installation with Optional Features

Install with optional dependencies.

```bash
# All optional features
pip install socrates-ai[full]

# Just Nexus (LLM support)
pip install socratic-core[nexus]

# Just agents
pip install socratic-core[agents]

# With development tools
pip install socrates-ai[dev]
```

## Installation from Source

### Clone the Repository
```bash
git clone https://github.com/themsou/Socrates.git
cd Socrates
```

### Install in Development Mode
```bash
pip install -e .
```

### Install with Development Dependencies
```bash
pip install -e ".[dev]"
```

## Verification

### Verify Installation
```bash
# Check core installation
python -c "from socratic_core import SocratesConfig; print('Core OK')"

# Check CLI installation
socrates --version

# Check API installation
socrates-api --help

# Check full installation
python -c "import socrates_ai; print(f'Version: {socrates_ai.__version__}')"
```

### Check Dependencies
```bash
# List installed packages
pip list | grep socratic

# Check dependency tree
pip install pipdeptree
pipdeptree -p socratic-core
```

## Configuration

### Set Environment Variables

```bash
# Required: API Key
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: Data directory
export SOCRATES_DATA_DIR="$HOME/.socrates"

# Optional: Database path
export SOCRATES_DB_PATH="$HOME/.socrates/socrates.db"

# Optional: Logging
export SOCRATES_LOG_LEVEL="INFO"
export SOCRATES_LOG_FILE="socrates.log"

# Optional: API Server
export SOCRATES_API_URL="http://localhost:8000"
export SOCRATES_API_PORT=8000
```

### Create Configuration File

Create `.env` in your project:
```
ANTHROPIC_API_KEY=sk-ant-...
SOCRATES_DATA_DIR=./socrates_data
SOCRATES_LOG_LEVEL=INFO
SOCRATES_API_URL=http://localhost:8000
```

Then in your code:
```python
from socratic_core import SocratesConfig

config = SocratesConfig.from_env()
```

## Platform-Specific Installation

### macOS

```bash
# Using Homebrew (if available)
brew install socrates-ai

# Or using pip
pip install socrates-ai
```

### Linux

```bash
# Ubuntu/Debian
sudo apt-get install python3-pip
pip install socrates-ai

# RedHat/CentOS
sudo yum install python3-pip
pip install socrates-ai
```

### Windows

```powershell
# Using pip
python -m pip install socrates-ai

# Or using Windows Package Manager (if installed)
winget install socrates-ai
```

### Docker

```bash
# Build image
docker build -t socrates-api .

# Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key \
  socrates-api
```

## Troubleshooting

### ImportError: No module named 'socratic_core'

**Solution**: Install socratic-core separately
```bash
pip install socratic-core
```

Or reinstall full platform:
```bash
pip install --upgrade socrates-ai
```

### Permission Denied on Linux/macOS

**Solution**: Use `--user` flag or virtual environment
```bash
# Option 1: Install for current user
pip install --user socrates-ai

# Option 2: Use virtual environment (recommended)
python -m venv socrates_env
source socrates_env/bin/activate  # On Windows: socrates_env\Scripts\activate
pip install socrates-ai
```

### SSL Certificate Error

**Solution**: Update certificates or use `--trusted-host`
```bash
# Option 1: Update pip and certificates
pip install --upgrade pip certifi

# Option 2: Use trusted host
pip install --trusted-host files.pythonhosted.org socrates-ai
```

### Conflicting Dependencies

**Solution**: Use a clean virtual environment
```bash
python -m venv clean_env
source clean_env/bin/activate  # On Windows: clean_env\Scripts\activate
pip install socrates-ai
```

### API Key Not Found

**Solution**: Set environment variable
```bash
export ANTHROPIC_API_KEY="your-api-key-here"

# Verify it's set
echo $ANTHROPIC_API_KEY

# Or create .env file
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
```

### Cannot Connect to API Server

**Solution**: Make sure API is running
```bash
# Terminal 1: Start API
socrates-api

# Terminal 2: Test connection
curl http://localhost:8000/health

# Or check logs
tail -f socrates.log
```

## Upgrading

### Upgrade All Packages
```bash
pip install --upgrade socrates-ai
```

### Upgrade Specific Package
```bash
pip install --upgrade socratic-core
pip install --upgrade socrates-cli
pip install --upgrade socrates-api
```

### Upgrade from Source
```bash
git pull origin master
pip install --upgrade -e .
```

## Uninstallation

### Remove Single Package
```bash
pip uninstall socratic-core
```

### Remove All Socrates Packages
```bash
pip uninstall socratic-core socrates-ai socratic-rag socratic-agents \
    socratic-analyzer socratic-knowledge socratic-learning \
    socratic-workflow socratic-conflict socrates-cli socrates-api
```

### Remove Data (Optional)
```bash
# Remove configuration and data
rm -rf ~/.socrates/

# On Windows
rmdir /s %APPDATA%\socrates
```

## Getting Help

### Check Installation
```bash
# Verify all components
socrates --version
socrates-api --help
python -c "from socratic_core import SocratesConfig; print('OK')"
```

### View Documentation
```bash
# Command help
socrates --help

# API documentation (when running)
# Open: http://localhost:8000/docs

# Full docs
cat QUICKSTART.md
cat ARCHITECTURE.md
```

### Report Issues
If you encounter problems:

1. Check the [troubleshooting section](#troubleshooting) above
2. Search [GitHub Issues](https://github.com/themsou/Socrates/issues)
3. Create a new issue with:
   - Python version: `python --version`
   - Installation: `pip list | grep socratic`
   - Error output
   - Steps to reproduce

## Next Steps

After installation:

1. **[Quick Start](QUICKSTART.md)** - Get started in 5 minutes
2. **[Architecture](ARCHITECTURE.md)** - Understand the system
3. **[Migration Guide](MIGRATION_GUIDE.md)** - Upgrade from old versions
4. **CLI Help**: `socrates --help`
5. **API Docs**: `http://localhost:8000/docs` (when API running)

## System Specifications

### Minimum Installation Sizes
- **socratic-core**: 5-10 MB
- **socrates-cli**: 10-15 MB
- **socrates-api**: 15-25 MB
- **socratic-rag**: 8-12 MB
- **socratic-agents**: 12-20 MB
- **Full platform**: 50-100 MB

### Typical Memory Usage
- **socratic-core alone**: 10-20 MB
- **CLI with API connection**: 30-50 MB
- **API server**: 100-200 MB
- **Full platform**: 200-500 MB

### Python Version Support
- Python 3.8: Supported
- Python 3.9: Supported
- Python 3.10: Supported
- Python 3.11: Supported
- Python 3.12: Supported

## Advanced Installation

### Install from Specific Branch
```bash
pip install git+https://github.com/themsou/Socrates.git@develop
```

### Install Specific Version
```bash
pip install socrates-ai==2.0.0
```

### Install Pre-release
```bash
pip install --pre socrates-ai
```

### Editable Installation with Tests
```bash
git clone https://github.com/themsou/Socrates.git
cd Socrates
pip install -e ".[dev,test]"
pytest tests/
```

## Need Help?

- **Documentation**: https://github.com/themsou/Socrates
- **Issues**: https://github.com/themsou/Socrates/issues
- **Discussions**: https://github.com/themsou/Socrates/discussions
