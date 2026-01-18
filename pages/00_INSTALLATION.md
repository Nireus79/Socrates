# Installation - Socrates AI

## Get Socrates Running in Minutes

**Choose your platform and follow the steps below. All options are free to try!**

---

## Quick Start

### For Impatient People (5 minutes)

```bash
# Windows users: Download and run installer
# macOS/Linux users:
git clone https://github.com/Nireus79/Socrates.git
cd Socrates
pip install -e .
socrates /project create

# Docker users:
docker run -it ghcr.io/nireus79/socrates:latest
```

---

## Installation by Platform

### 1. Windows

#### Option A: Download Pre-built Executable (Easiest)

**Prerequisites**: Windows 10/11, 500 MB free disk space

**Steps**:
1. Download the latest Windows executable:
   - [Download socrates.exe (Latest Release →)](https://github.com/Nireus79/Socrates/releases/latest)
   - Look for file: `socrates-v1.3.0-windows.exe` (280 MB)

2. Run the installer:
   - Double-click `socrates.exe`
   - Follow the installation wizard
   - Choose installation directory (default: `C:\Program Files\Socrates`)

3. Launch the application:
   - Click "Launch Socrates" at end of installer
   - Or find "Socrates AI" in Start Menu
   - Browser will open automatically

4. Set your API key:
   - Get your Claude API key from [https://console.anthropic.com/](https://console.anthropic.com/)
   - Paste into the "Settings" → "API Configuration" section
   - Click Save

**That's it!** You're ready to create your first project.

**Advantages**:
- ✅ No programming knowledge needed
- ✅ One-click installation
- ✅ Automatic updates available
- ✅ Desktop shortcut created
- ✅ Uninstall through Control Panel

**File Size**: 280 MB

**System Requirements**:
- OS: Windows 10 (build 19041) or later, Windows 11
- RAM: 4 GB minimum (8 GB recommended)
- Disk: 500 MB free
- Internet: Required (for Claude API)
- Port: 8000 (default, can be changed)

#### Option B: Clone from GitHub (For Developers)

**Prerequisites**:
- Windows 10/11
- Git installed ([Download Git →](https://git-scm.com/download/win))
- Python 3.9+ installed ([Download Python →](https://www.python.org/downloads/))

**Steps**:

1. Clone the repository:
```bash
git clone https://github.com/Nireus79/Socrates.git
cd Socrates
```

2. Create virtual environment (recommended):
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set your API key:
```bash
set CLAUDE_API_KEY=your-api-key-here
```

5. Run Socrates:
```bash
socrates /project create
```

Or use Windows-specific launcher:
```bash
python socrates_windows_entry.py
```

6. Open browser:
```
http://localhost:8000
```

**Advantages**:
- ✅ Full source code access
- ✅ Can modify and customize
- ✅ Easy to contribute back
- ✅ Latest development version
- ✅ Can develop extensions

**Troubleshooting**:
- **Port 8000 already in use**: Edit `config.py` and change `PORT=8001`
- **Python not found**: Add Python to PATH or use full path: `C:\Python39\python.exe`
- **API key errors**: Verify key at [console.anthropic.com](https://console.anthropic.com/)
- **Git not found**: Install Git or use GitHub Desktop

---

### 2. macOS

#### Option A: Homebrew (Easiest)

**Prerequisites**: Homebrew installed ([Install Homebrew →](https://brew.sh/))

**Steps**:

```bash
# Install Socrates
brew tap nireus79/socrates
brew install socrates

# Launch
socrates /project create
```

**Browser opens automatically** at `http://localhost:8000`

**Advantages**:
- ✅ One-line installation
- ✅ Automatic updates via `brew upgrade`
- ✅ Easy uninstall: `brew uninstall socrates`

#### Option B: Clone from GitHub

**Prerequisites**:
- macOS 10.15+
- Git installed (comes with Xcode Command Line Tools)
- Python 3.9+ installed ([Download Python →](https://www.python.org/downloads/) or use Homebrew)

**Steps**:

```bash
# Clone repository
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export CLAUDE_API_KEY=your-api-key-here

# Run Socrates
socrates /project create
```

**Advantages**:
- ✅ Full source code access
- ✅ Latest development version
- ✅ Can customize for your needs

**System Requirements**:
- OS: macOS 10.15+ (Catalina or later)
- RAM: 4 GB minimum (8 GB recommended)
- Disk: 500 MB free
- Internet: Required
- Port: 8000 (configurable)

**Troubleshooting**:
- **"Command not found: socrates"**: Make sure virtual environment is activated: `source venv/bin/activate`
- **Permission denied**: Run with `python3 socrates_windows_entry.py`
- **Xcode tools not installed**: Run `xcode-select --install`

---

### 3. Linux

#### Option A: Package Manager (Ubuntu/Debian)

**Prerequisites**: Ubuntu 20.04+ or Debian 11+

**Steps**:

```bash
# Add repository
sudo add-apt-repository ppa:nireus79/socrates

# Update package list
sudo apt update

# Install Socrates
sudo apt install socrates

# Launch
socrates /project create
```

#### Option B: Clone from GitHub

**Prerequisites**:
- Linux (Ubuntu, Debian, Fedora, CentOS, Arch, etc.)
- Git: `sudo apt install git` (Ubuntu/Debian) or `sudo yum install git` (Fedora/CentOS)
- Python 3.9+: `sudo apt install python3 python3-pip` (Ubuntu/Debian)

**Steps**:

```bash
# Clone repository
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export CLAUDE_API_KEY=your-api-key-here

# Run Socrates
socrates /project create
```

**Advantages**:
- ✅ Full control over installation
- ✅ Can install globally or per-user
- ✅ Latest code
- ✅ Easy to contribute

**System Requirements**:
- OS: Ubuntu 20.04+, Debian 11+, or any modern Linux distribution
- RAM: 4 GB minimum (8 GB recommended)
- Disk: 500 MB free
- Internet: Required
- Port: 8000 (configurable)

**Troubleshooting**:
- **"command not found: socrates"**: Activate virtual environment: `source venv/bin/activate`
- **Permission denied**: Try with `python3`: `python3 -m socrates.cli`
- **Module not found**: Make sure you're in the Socrates directory and venv is activated

---

### 4. Docker (Any Platform)

#### Docker Container (Recommended for Production)

**Prerequisites**:
- Docker installed ([Download Docker →](https://www.docker.com/products/docker-desktop))
- Docker daemon running

**Steps**:

```bash
# Pull latest image
docker pull ghcr.io/nireus79/socrates:latest

# Run container
docker run -it \
  -p 8000:8000 \
  -e CLAUDE_API_KEY=your-api-key-here \
  ghcr.io/nireus79/socrates:latest
```

**Browser opens at**: `http://localhost:8000`

**With Persistent Data**:

```bash
docker run -it \
  -p 8000:8000 \
  -v socrates-data:/app/data \
  -e CLAUDE_API_KEY=your-api-key-here \
  ghcr.io/nireus79/socrates:latest
```

**Docker Compose** (Best for Multi-Container):

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  socrates:
    image: ghcr.io/nireus79/socrates:latest
    ports:
      - "8000:8000"
    environment:
      - CLAUDE_API_KEY=your-api-key-here
    volumes:
      - socrates-data:/app/data
    restart: unless-stopped

volumes:
  socrates-data:
```

Then run:
```bash
docker-compose up -d
```

**Advantages**:
- ✅ Works on any platform (Windows, macOS, Linux)
- ✅ Isolated environment (no conflicts)
- ✅ Easy to scale
- ✅ Production-ready
- ✅ Easy deployment

**System Requirements**:
- Docker 20.10+
- 4 GB RAM available
- 500 MB disk
- Internet connection

**Stopping Container**:
```bash
# Get container ID
docker ps

# Stop specific container
docker stop <container-id>
```

---

### 5. Cloud / Online (Coming Soon)

A hosted version of Socrates AI will be available at `app.socrates-ai.com` with:
- ✅ No installation needed
- ✅ Cloud-based storage
- ✅ Always updated
- ✅ Team collaboration built-in
- ✅ Enterprise features

**Expected**: Q2 2026

[Notify me when available →](https://forms.gle/socrates-cloud-signup)

---

## Developer Installation

### For Contributors & Extension Developers

**Setup Development Environment**:

```bash
# Clone repository
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Start development server
socrates /project create --debug
```

**For Extending Socrates**:

See [Developer Guide →](/docs/DEVELOPER_GUIDE.md) and [Contributing Guide →](https://github.com/Nireus79/Socrates/blob/master/CONTRIBUTING.md)

---

## System Requirements by Platform

### Minimum (Entry Level)

| Component | Windows | macOS | Linux |
|-----------|---------|-------|-------|
| OS | Windows 10 | macOS 10.15+ | Ubuntu 20.04+ |
| RAM | 4 GB | 4 GB | 4 GB |
| Disk | 500 MB | 500 MB | 500 MB |
| Internet | Required | Required | Required |
| Port | 8000 | 8000 | 8000 |

### Recommended (Better Experience)

| Component | Windows | macOS | Linux |
|-----------|---------|-------|-------|
| OS | Windows 11 | macOS 12+ | Ubuntu 22.04+ |
| RAM | 8 GB | 8 GB | 8 GB |
| Disk | 2 GB | 2 GB | 2 GB |
| CPU | 4 cores | 4 cores | 4 cores |
| Internet | Broadband | Broadband | Broadband |

### Enterprise (Best Performance)

| Component | Specification |
|-----------|---------------|
| RAM | 16+ GB |
| CPU | 8+ cores |
| Disk | 10+ GB SSD |
| Internet | Dedicated connection |
| Deployment | Docker/Kubernetes |

---

## Verifying Installation

### Test Your Installation

```bash
# Check version
socrates --version

# Should output: Socrates AI v1.3.0

# Run diagnostic
socrates --health-check

# Should output: ✓ All systems operational

# Test API connection
socrates --test-api

# Should output: ✓ Claude API connection successful
```

### First Project Verification

1. Open browser: `http://localhost:8000`
2. Sign up or log in
3. Click "Create New Project"
4. Enter a simple project name
5. Click "Begin Dialogue"
6. Answer the first question
7. If you see the next question → **Installation successful!**

---

## Port Configuration

### Using a Different Port

**Windows** (Command Prompt):
```bash
set SOCRATES_PORT=8001
socrates /project create
```

**macOS/Linux** (Terminal):
```bash
export SOCRATES_PORT=8001
socrates /project create
```

**Docker**:
```bash
docker run -p 9000:8000 ghcr.io/nireus79/socrates:latest
# Access at http://localhost:9000
```

**Edit Configuration** (`config.py`):
```python
PORT = 8001  # Change from 8000
```

---

## API Key Setup

### Getting Your API Key

1. Go to [Anthropic Console →](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to "API Keys" section
4. Click "Create new secret key"
5. Copy the key (starts with `sk-ant-`)
6. Save securely (treat like a password)

### Setting API Key in Socrates

**Option 1: Settings UI**
- Launch Socrates
- Click "Settings"
- Paste API key in "Claude API Configuration"
- Click "Save"

**Option 2: Environment Variable**
```bash
# Windows
set CLAUDE_API_KEY=sk-ant-...

# macOS/Linux
export CLAUDE_API_KEY=sk-ant-...
```

**Option 3: Config File** (`config.py`)
```python
CLAUDE_API_KEY = "sk-ant-..."
```

---

## Troubleshooting Installation

### Common Issues & Solutions

#### Issue: "Connection refused" or "Cannot connect to localhost:8000"

**Solutions**:
1. Check if port 8000 is available:
   - Windows: `netstat -ano | findstr :8000`
   - macOS/Linux: `lsof -i :8000`
2. Use different port: `export SOCRATES_PORT=8001`
3. Restart Socrates application
4. Check firewall settings (allow port 8000)

#### Issue: "API Key Invalid" or "Invalid API Key"

**Solutions**:
1. Verify key starts with `sk-ant-`
2. Check for leading/trailing spaces
3. Regenerate key at [console.anthropic.com](https://console.anthropic.com/)
4. Verify key has "Read" and "Write" permissions
5. Check key hasn't expired

#### Issue: "Python not found" or "Command not recognized"

**Solutions** (Windows):
1. Reinstall Python from [python.org](https://python.org)
2. Check "Add Python to PATH" during installation
3. Use full path: `C:\Python39\python.exe`
4. Restart Command Prompt after installing Python

**Solutions** (macOS/Linux):
1. Check Python is installed: `python3 --version`
2. Install if missing: `brew install python3` (macOS) or `sudo apt install python3` (Linux)
3. Activate virtual environment: `source venv/bin/activate`

#### Issue: "ModuleNotFoundError" or Missing Dependencies

**Solutions**:
1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Upgrade pip: `pip install --upgrade pip`
4. Clear pip cache: `pip cache purge`
5. Clean reinstall:
   ```bash
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

#### Issue: "Port Already in Use"

**Solutions**:
1. Find process using port 8000:
   - Windows: `netstat -ano | findstr :8000`
   - macOS/Linux: `lsof -i :8000`
2. Kill process:
   - Windows: `taskkill /PID <PID> /F`
   - macOS/Linux: `kill -9 <PID>`
3. Or use different port: `export SOCRATES_PORT=8001`

#### Issue: "Docker image not found"

**Solutions**:
1. Pull image first: `docker pull ghcr.io/nireus79/socrates:latest`
2. Check internet connection
3. Verify Docker is running: `docker ps`
4. Clear Docker cache: `docker system prune`

#### Issue: Browser Won't Open Automatically

**Solutions**:
1. Manually open: `http://localhost:8000`
2. Try different browser
3. Check firewall settings
4. Restart Socrates application

---

## Getting Help

### Documentation
- [Full Documentation →](/docs/)
- [Developer Guide →](/docs/DEVELOPER_GUIDE.md)
- [Getting Started Guide →](/pages/04_GETTING_STARTED.md)

### Community Support
- [Discord Community →](https://discord.gg/socrates)
- [GitHub Issues →](https://github.com/Nireus79/Socrates/issues)
- [GitHub Discussions →](https://github.com/Nireus79/Socrates/discussions)

### Direct Support
- [Email Support →](mailto:support@socrates-ai.com)
- [Contact Us →](/contact)

---

## Uninstalling Socrates

### Windows (Pre-built Executable)

1. Open Control Panel
2. Go to "Programs" → "Programs and Features"
3. Find "Socrates AI"
4. Click "Uninstall"
5. Follow wizard
6. Done!

### macOS (Homebrew)

```bash
brew uninstall socrates
```

### macOS/Linux (From Source)

```bash
# Remove virtual environment
rm -rf venv

# Remove cloned directory
rm -rf Socrates
```

### Docker

```bash
# Remove container
docker rm <container-id>

# Remove image
docker rmi ghcr.io/nireus79/socrates:latest

# Remove data volume (if persistent)
docker volume rm socrates-data
```

---

## Updating Socrates

### Windows (Pre-built)
- Updates available through installer
- Check "Settings" → "Check for Updates"

### macOS (Homebrew)
```bash
brew upgrade socrates
```

### Any Platform (From Source)
```bash
cd Socrates
git pull origin master
pip install -r requirements.txt
```

### Docker
```bash
docker pull ghcr.io/nireus79/socrates:latest
docker-compose up -d  # Recreates with new image
```

---

## Next Steps After Installation

1. **[Get Started →](/pages/04_GETTING_STARTED.md)** - Create your first project
2. **[Join Discord →](https://discord.gg/socrates)** - Connect with community
3. **[Read Features →](/pages/08_FEATURES.md)** - Learn what's possible
4. **[Try Examples →](https://github.com/Nireus79/Socrates/tree/master/examples)** - See sample projects

---

## GitHub Links

- **Main Repository**: [github.com/Nireus79/Socrates](https://github.com/Nireus79/Socrates)
- **Releases & Downloads**: [github.com/Nireus79/Socrates/releases](https://github.com/Nireus79/Socrates/releases)
- **Issues & Bugs**: [github.com/Nireus79/Socrates/issues](https://github.com/Nireus79/Socrates/issues)
- **Discussions**: [github.com/Nireus79/Socrates/discussions](https://github.com/Nireus79/Socrates/discussions)
- **Contributing**: [github.com/Nireus79/Socrates/blob/master/CONTRIBUTING.md](https://github.com/Nireus79/Socrates/blob/master/CONTRIBUTING.md)
- **Docker Image**: [ghcr.io/nireus79/socrates](https://ghcr.io/nireus79/socrates)

---

**Last Updated**: January 2026
**Version**: 1.3.0

**Ready to install? [Download Now →](https://github.com/Nireus79/Socrates/releases/latest)**
