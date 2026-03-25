# Socrates AI - Complete Setup Guide

This guide walks you through setting up Socrates from scratch, including Python installation, virtual environment configuration, and dependency management.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Python Installation](#python-installation)
3. [Clone the Repository](#clone-the-repository)
4. [Virtual Environment Setup](#virtual-environment-setup)
5. [Install Dependencies](#install-dependencies)
6. [Verify Installation](#verify-installation)
7. [Run Socrates](#run-socrates)
8. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Supported Python Versions

- **Recommended:** Python 3.11 (stable, used in production Docker images)
- **Also Supported:** Python 3.8, 3.9, 3.10, 3.12
- **Avoid:** Python 3.13+ (newer, may have edge cases)

### Why Python 3.11?

- ✅ Used in all official Docker images (`python:3.11-slim`)
- ✅ Default for release and deployment workflows
- ✅ Best compatibility with ML libraries (torch, transformers, scikit-learn)
- ✅ Fewer async/Windows edge cases
- ✅ Proven stable in production

### Other Requirements

- Git (for cloning the repository)
- 4GB+ RAM (for ML models and dependencies)
- 10GB+ disk space (for dependencies and models)

---

## Python Installation

### Windows

#### Option 1: Direct Installation (Recommended)

1. **Download Python 3.11**
   - Go to https://www.python.org/downloads/
   - Download "Python 3.11.x" for Windows (latest 3.11 version)

2. **Run the installer**
   - ✅ **IMPORTANT:** Check "Add Python to PATH"
   - Check "Install pip"
   - Click "Install Now"

3. **Verify installation**
   ```bash
   python --version  # Should show 3.11.x
   pip --version
   ```

#### Option 2: Using Windows Package Manager (winget)

```bash
winget install Python.Python.3.11
```

#### Option 3: Using Anaconda

```bash
conda create -n socrates python=3.11
conda activate socrates
```

### macOS

```bash
# Using Homebrew
brew install python@3.11

# Verify
python3.11 --version
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# Verify
python3.11 --version
```

---

## Clone the Repository

```bash
# Choose your directory
cd C:\Users\YourUsername\PycharmProjects  # Windows example

# Clone the repository
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Verify you're in the right place
pwd  # Should show: .../Socrates
ls  # Should show socrates.py, pyproject.toml, etc.
```

---

## Virtual Environment Setup

A virtual environment isolates project dependencies from your system Python.

### Step 1: Create Virtual Environment

#### Windows (Python 3.11)
```bash
python -m venv .venv
```

#### macOS/Linux (Python 3.11)
```bash
python3.11 -m venv .venv
```

### Step 2: Activate Virtual Environment

#### Windows (PowerShell)
```bash
.venv\Scripts\Activate.ps1

# If you get an execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then try Activate.ps1 again
```

#### Windows (Command Prompt)
```bash
.venv\Scripts\activate.bat
```

#### macOS/Linux
```bash
source .venv/bin/activate
```

**Success indicators:**
- Prompt should show `(.venv)` prefix
- `which python` should point to `.venv/bin/python` or `.venv\Scripts\python.exe`

---

## Install Dependencies

### Step 1: Upgrade pip

```bash
python -m pip install --upgrade pip
```

### Step 2: Install Project Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# This installs:
# - Core dependencies (anthropic, fastapi, sqlalchemy, etc.)
# - ML libraries (torch, transformers, sentence-transformers)
# - Database tools (chromadb, alembic)
# - API server (uvicorn)
# - And 50+ more packages
```

**Expected time:** 5-15 minutes (depending on internet and system)

### Step 3: Install Socrates in Development Mode

```bash
pip install -e .

# This installs:
# - socratic-core (config, events, exceptions)
# - socratic-agents (multi-agent orchestration)
# - socratic-rag (retrieval-augmented generation)
# - socratic-security (security utilities)
# - And 10+ more socratic packages
```

### Step 4: Verify Installation

```bash
# Test imports
python -c "from socratic_core import SocratesConfig; print('✓ socratic-core loaded')"
python -c "from socratic_system.orchestration import AgentOrchestrator; print('✓ orchestration loaded')"

# Check installed packages
pip list | grep -i socratic
```

---

## Verify Installation

### Run Help Command

```bash
python socrates.py --help
```

**Expected output:**
- Shows usage information
- Auto-generates `.env` file with API keys
- No errors

### Check Python Version

```bash
python --version
# Should show: Python 3.11.x
```

### Test Virtual Environment

```bash
# Deactivate
deactivate

# Python should revert to system version
python --version

# Reactivate
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Should be back to 3.11.x
python --version
```

---

## Run Socrates

### Option 1: Full Stack (API + Frontend)

```bash
python socrates.py --full
```

Opens browser to `http://localhost:5173`

### Option 2: API Only

```bash
python socrates.py --api
```

API runs on `http://localhost:8000`

### Option 3: CLI Only (Default)

```bash
python socrates.py
```

Starts interactive CLI

### First Run Notes

- **First run:** Generates security keys in `.env`
- **Add API Key:** Edit `.env` and add your `ANTHROPIC_API_KEY`
- **No API Key:** CLI still works, but some features disabled

---

## Troubleshooting

### "python: command not found"

**Cause:** Python not in PATH or not installed

**Solution (Windows):**
```bash
# Use full path
C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\python.exe --version

# Or reinstall with "Add Python to PATH" checked
```

### "No module named 'socratic_core'"

**Cause:** Dependencies not installed or venv not activated

**Solution:**
```bash
# Make sure venv is activated (should show (.venv) prefix)
which python  # or: where python (Windows)

# Reinstall in editable mode
pip install -e .

# Verify
python -c "import socratic_core; print('OK')"
```

### "Permission denied" on activate script (Windows PowerShell)

**Cause:** Execution policy restriction

**Solution:**
```bash
# Run in PowerShell as Administrator, then:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Restart PowerShell and try again
.venv\Scripts\Activate.ps1
```

### "ModuleNotFoundError: No module named 'torch'"

**Cause:** ML dependencies failed to install

**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# If still fails, try individually
pip install torch transformers sentence-transformers

# Check for disk space (torch is ~600MB)
```

### Virtual Environment Not Activating

**Cause:** Corrupted venv or wrong Python version

**Solution:**
```bash
# Delete and recreate
rm -r .venv  # or: rmdir /s .venv (Windows)

# Create fresh
python3.11 -m venv .venv

# Activate and reinstall
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

### "ANTHROPIC_API_KEY not set"

**Cause:** Missing API key in `.env`

**Solution:**
1. Get your API key from https://console.anthropic.com/
2. Edit `.env` in project root
3. Add: `ANTHROPIC_API_KEY=sk-...your-key...`
4. Save and restart Socrates

### Terminal Opens in Wrong Directory

**If using PyCharm:**
- Go to: `File → Settings → Tools → Terminal`
- Set "Initial directory" to: `C:\Users\YourUsername\PycharmProjects\Socrates`
- Close and reopen terminal

### Out of Memory Error

**Cause:** Large models or context length too high

**Solution:**
```bash
# Reduce context length in .env or config
# Or use smaller models

# Check available memory
# Windows: taskmgr → Memory tab
# Linux: free -h
```

---

## Complete Setup Script (Copy & Paste)

### Windows PowerShell

```powershell
# 1. Navigate to project
cd C:\Users\YourUsername\PycharmProjects\Socrates

# 2. Create virtual environment
python -m venv .venv

# 3. Activate it
.venv\Scripts\Activate.ps1

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Install Socrates
pip install -e .

# 7. Verify
python socrates.py --help

# 8. Run
python socrates.py --full
```

### macOS/Linux Bash

```bash
# 1. Navigate to project
cd ~/PycharmProjects/Socrates

# 2. Create virtual environment
python3.11 -m venv .venv

# 3. Activate it
source .venv/bin/activate

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Install Socrates
pip install -e .

# 7. Verify
python socrates.py --help

# 8. Run
python socrates.py --full
```

---

## Next Steps

1. **Add API Key:** Edit `.env` and add `ANTHROPIC_API_KEY`
2. **Start Socrates:** Run `python socrates.py --full`
3. **Open Browser:** Go to `http://localhost:5173`
4. **Read Documentation:** Check `README.md` and `docs/` folder

---

## Getting Help

- **Installation Issues:** See [Troubleshooting](#troubleshooting) above
- **Project Documentation:** Check `README.md`
- **GitHub Issues:** https://github.com/Nireus79/Socrates/issues
- **Documentation:** See `INSTALL.md` and `QUICKSTART.md`

---

## Development Notes

### Upgrading Python Version

If you need to switch Python versions:

```bash
# Deactivate current env
deactivate

# Delete old venv
rm -r .venv

# Create with new version
python3.12 -m venv .venv

# Activate and reinstall
.venv\Scripts\Activate.ps1  # or source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Installing Additional Packages

```bash
# Make sure venv is activated first
pip install package-name

# Update requirements.txt if needed
pip freeze > requirements.txt
```

### Running Tests

```bash
pip install -r requirements-test.txt
pytest
```

---

**Last Updated:** 2026-03-25
**Python Version:** 3.11 (recommended)
**Socrates Version:** 1.4.1
