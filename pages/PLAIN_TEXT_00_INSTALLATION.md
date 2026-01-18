INSTALLATION - Socrates AI

Get Socrates Running in Minutes

Choose your platform and follow the steps below. All options are free to try!

QUICK START

For Windows users: Download and run installer
For macOS/Linux users:
git clone https://github.com/Nireus79/Socrates.git
cd Socrates
pip install -e .
socrates /project create

For Docker users:
docker run -it ghcr.io/nireus79/socrates:latest

WINDOWS INSTALLATION

Option A: Download Pre-built Executable (Easiest)

Prerequisites: Windows 10/11, 500 MB free disk space

Steps:

1. Download the latest Windows executable from https://github.com/Nireus79/Socrates/releases/latest
   Look for file: socrates-v1.3.0-windows.exe (280 MB)

2. Run the installer
   Double-click socrates.exe
   Follow the installation wizard
   Choose installation directory (default: C:\Program Files\Socrates)

3. Launch the application
   Click "Launch Socrates" at end of installer
   Or find "Socrates AI" in Start Menu
   Browser will open automatically

4. Set your API key
   Get your Claude API key from https://console.anthropic.com/
   Paste into the "Settings" → "API Configuration" section
   Click Save

That's it! You're ready to create your first project.

Advantages:
- No programming knowledge needed
- One-click installation
- Automatic updates available
- Desktop shortcut created
- Uninstall through Control Panel

File Size: 280 MB

System Requirements:
- OS: Windows 10 (build 19041) or later, Windows 11
- RAM: 4 GB minimum (8 GB recommended)
- Disk: 500 MB free
- Internet: Required (for Claude API)
- Port: 8000 (default, can be changed)

Option B: Clone from GitHub (For Developers)

Prerequisites:
- Windows 10/11
- Git installed (Download from https://git-scm.com/download/win)
- Python 3.9+ installed (Download from https://www.python.org/downloads/)

Steps:

1. Clone the repository:
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

2. Create virtual environment (recommended):
python -m venv venv
venv\Scripts\activate

3. Install dependencies:
pip install -r requirements.txt

4. Set your API key:
set CLAUDE_API_KEY=your-api-key-here

5. Run Socrates:
socrates /project create

Or use Windows-specific launcher:
python socrates_windows_entry.py

6. Open browser:
http://localhost:8000

Advantages:
- Full source code access
- Can modify and customize
- Easy to contribute back
- Latest development version
- Can develop extensions

Troubleshooting:
- Port 8000 already in use: Edit config.py and change PORT=8001
- Python not found: Add Python to PATH or use full path: C:\Python39\python.exe
- API key errors: Verify key at https://console.anthropic.com/
- Git not found: Install Git or use GitHub Desktop

MACOS INSTALLATION

Option A: Homebrew (Easiest)

Prerequisites: Homebrew installed (Install from https://brew.sh/)

Steps:

Install Socrates:
brew tap nireus79/socrates
brew install socrates

Launch:
socrates /project create

Browser opens automatically at http://localhost:8000

Advantages:
- One-line installation
- Automatic updates via brew upgrade
- Easy uninstall: brew uninstall socrates

Option B: Clone from GitHub

Prerequisites:
- macOS 10.15+
- Git installed (comes with Xcode Command Line Tools)
- Python 3.9+ installed (Download from https://www.python.org/downloads/ or use Homebrew)

Steps:

Clone repository:
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

Create virtual environment:
python3 -m venv venv
source venv/bin/activate

Install dependencies:
pip install -r requirements.txt

Set API key:
export CLAUDE_API_KEY=your-api-key-here

Run Socrates:
socrates /project create

Advantages:
- Full source code access
- Latest development version
- Can customize for your needs

System Requirements:
- OS: macOS 10.15+ (Catalina or later)
- RAM: 4 GB minimum (8 GB recommended)
- Disk: 500 MB free
- Internet: Required
- Port: 8000 (configurable)

Troubleshooting:
- "Command not found: socrates": Make sure virtual environment is activated: source venv/bin/activate
- Permission denied: Run with python3 socrates_windows_entry.py
- Xcode tools not installed: Run xcode-select --install

LINUX INSTALLATION

Option A: Package Manager (Ubuntu/Debian)

Prerequisites: Ubuntu 20.04+ or Debian 11+

Steps:

Add repository:
sudo add-apt-repository ppa:nireus79/socrates

Update package list:
sudo apt update

Install Socrates:
sudo apt install socrates

Launch:
socrates /project create

Option B: Clone from GitHub

Prerequisites:
- Linux (Ubuntu, Debian, Fedora, CentOS, Arch, etc.)
- Git: sudo apt install git (Ubuntu/Debian) or sudo yum install git (Fedora/CentOS)
- Python 3.9+: sudo apt install python3 python3-pip (Ubuntu/Debian)

Steps:

Clone repository:
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

Create virtual environment:
python3 -m venv venv
source venv/bin/activate

Install dependencies:
pip install -r requirements.txt

Set API key:
export CLAUDE_API_KEY=your-api-key-here

Run Socrates:
socrates /project create

Advantages:
- Full control over installation
- Can install globally or per-user
- Latest code
- Easy to contribute

System Requirements:
- OS: Ubuntu 20.04+, Debian 11+, or any modern Linux distribution
- RAM: 4 GB minimum (8 GB recommended)
- Disk: 500 MB free
- Internet: Required
- Port: 8000 (configurable)

Troubleshooting:
- "command not found: socrates": Activate virtual environment: source venv/bin/activate
- Permission denied: Try with python3: python3 -m socrates.cli
- Module not found: Make sure you're in the Socrates directory and venv is activated

DOCKER INSTALLATION

Docker Container (Recommended for Production)

Prerequisites:
- Docker installed (Download from https://www.docker.com/products/docker-desktop)
- Docker daemon running

Steps:

Pull latest image:
docker pull ghcr.io/nireus79/socrates:latest

Run container:
docker run -it \
  -p 8000:8000 \
  -e CLAUDE_API_KEY=your-api-key-here \
  ghcr.io/nireus79/socrates:latest

Browser opens at: http://localhost:8000

With Persistent Data:

docker run -it \
  -p 8000:8000 \
  -v socrates-data:/app/data \
  -e CLAUDE_API_KEY=your-api-key-here \
  ghcr.io/nireus79/socrates:latest

Docker Compose (Best for Multi-Container):

Create docker-compose.yml:

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

Then run:
docker-compose up -d

Advantages:
- Works on any platform (Windows, macOS, Linux)
- Isolated environment (no conflicts)
- Easy to scale
- Production-ready
- Easy deployment

System Requirements:
- Docker 20.10+
- 4 GB RAM available
- 500 MB disk
- Internet connection

Stopping Container:

Get container ID:
docker ps

Stop specific container:
docker stop <container-id>

CLOUD / ONLINE (Coming Soon)

A hosted version of Socrates AI will be available at app.socrates-ai.com with:
- No installation needed
- Cloud-based storage
- Always updated
- Team collaboration built-in
- Enterprise features

Expected: Q2 2026

Notify me when available at: https://forms.gle/socrates-cloud-signup

SYSTEM REQUIREMENTS BY PLATFORM

Minimum (Entry Level):

Component | Windows | macOS | Linux
OS | Windows 10 | macOS 10.15+ | Ubuntu 20.04+
RAM | 4 GB | 4 GB | 4 GB
Disk | 500 MB | 500 MB | 500 MB
Internet | Required | Required | Required
Port | 8000 | 8000 | 8000

Recommended (Better Experience):

Component | Windows | macOS | Linux
OS | Windows 11 | macOS 12+ | Ubuntu 22.04+
RAM | 8 GB | 8 GB | 8 GB
Disk | 2 GB | 2 GB | 2 GB
CPU | 4 cores | 4 cores | 4 cores
Internet | Broadband | Broadband | Broadband

Enterprise (Best Performance):

Component | Specification
RAM | 16+ GB
CPU | 8+ cores
Disk | 10+ GB SSD
Internet | Dedicated connection
Deployment | Docker/Kubernetes

VERIFYING YOUR INSTALLATION

Test Your Installation:

Check version:
socrates --version
Should output: Socrates AI v1.3.0

Run diagnostic:
socrates --health-check
Should output: [CHECK] All systems operational

Test API connection:
socrates --test-api
Should output: [CHECK] Claude API connection successful

First Project Verification:

1. Open browser: http://localhost:8000
2. Sign up or log in
3. Click "Create New Project"
4. Enter a simple project name
5. Click "Begin Dialogue"
6. Answer the first question
7. If you see the next question → Installation successful!

PORT CONFIGURATION

Using a Different Port:

Windows (Command Prompt):
set SOCRATES_PORT=8001
socrates /project create

macOS/Linux (Terminal):
export SOCRATES_PORT=8001
socrates /project create

Docker:
docker run -p 9000:8000 ghcr.io/nireus79/socrates:latest
Access at http://localhost:9000

Edit Configuration (config.py):
PORT = 8001  # Change from 8000

API KEY SETUP

Getting Your API Key:

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys" section
4. Click "Create new secret key"
5. Copy the key (starts with sk-ant-)
6. Save securely (treat like a password)

Setting API Key in Socrates:

Option 1: Settings UI
- Launch Socrates
- Click "Settings"
- Paste API key in "Claude API Configuration"
- Click "Save"

Option 2: Environment Variable
Windows:
set CLAUDE_API_KEY=sk-ant-...

macOS/Linux:
export CLAUDE_API_KEY=sk-ant-...

Option 3: Config File (config.py)
CLAUDE_API_KEY = "sk-ant-..."

TROUBLESHOOTING COMMON ISSUES

Issue: "Connection refused" or "Cannot connect to localhost:8000"

Solutions:
1. Check if port 8000 is available
   Windows: netstat -ano | findstr :8000
   macOS/Linux: lsof -i :8000
2. Use different port: export SOCRATES_PORT=8001
3. Restart Socrates application
4. Check firewall settings (allow port 8000)

Issue: "API Key Invalid" or "Invalid API Key"

Solutions:
1. Verify key starts with sk-ant-
2. Check for leading/trailing spaces
3. Regenerate key at https://console.anthropic.com/
4. Verify key has "Read" and "Write" permissions
5. Check key hasn't expired

Issue: "Python not found" or "Command not recognized"

Solutions (Windows):
1. Reinstall Python from https://python.org
2. Check "Add Python to PATH" during installation
3. Use full path: C:\Python39\python.exe
4. Restart Command Prompt after installing Python

Solutions (macOS/Linux):
1. Check Python is installed: python3 --version
2. Install if missing: brew install python3 (macOS) or sudo apt install python3 (Linux)
3. Activate virtual environment: source venv/bin/activate

Issue: "ModuleNotFoundError" or Missing Dependencies

Solutions:
1. Ensure virtual environment is activated
2. Reinstall dependencies: pip install -r requirements.txt
3. Upgrade pip: pip install --upgrade pip
4. Clear pip cache: pip cache purge
5. Clean reinstall:
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

Issue: "Port Already in Use"

Solutions:
1. Find process using port 8000:
   Windows: netstat -ano | findstr :8000
   macOS/Linux: lsof -i :8000
2. Kill process:
   Windows: taskkill /PID <PID> /F
   macOS/Linux: kill -9 <PID>
3. Or use different port: export SOCRATES_PORT=8001

Issue: "Docker image not found"

Solutions:
1. Pull image first: docker pull ghcr.io/nireus79/socrates:latest
2. Check internet connection
3. Verify Docker is running: docker ps
4. Clear Docker cache: docker system prune

Issue: Browser Won't Open Automatically

Solutions:
1. Manually open: http://localhost:8000
2. Try different browser
3. Check firewall settings
4. Restart Socrates application

GETTING HELP

Documentation:
- Full Documentation at https://github.com/Nireus79/Socrates/blob/master/docs/
- Developer Guide at https://github.com/Nireus79/Socrates/blob/master/docs/DEVELOPER_GUIDE.md
- Getting Started Guide at https://github.com/Nireus79/Socrates/blob/master/pages/04_GETTING_STARTED.md

Community Support:
- Discord Community at https://discord.gg/socrates
- GitHub Issues at https://github.com/Nireus79/Socrates/issues
- GitHub Discussions at https://github.com/Nireus79/Socrates/discussions

Direct Support:
- Email Support at support@socrates-ai.com
- Contact Us at hermessoft.wordpress.com/socrates-ai/

UNINSTALLING SOCRATES

Windows (Pre-built Executable):

1. Open Control Panel
2. Go to "Programs" → "Programs and Features"
3. Find "Socrates AI"
4. Click "Uninstall"
5. Follow wizard
6. Done!

macOS (Homebrew):

brew uninstall socrates

macOS/Linux (From Source):

Remove virtual environment:
rm -rf venv

Remove cloned directory:
rm -rf Socrates

Docker:

Remove container:
docker rm <container-id>

Remove image:
docker rmi ghcr.io/nireus79/socrates:latest

Remove data volume (if persistent):
docker volume rm socrates-data

UPDATING SOCRATES

Windows (Pre-built):
- Updates available through installer
- Check "Settings" → "Check for Updates"

macOS (Homebrew):
brew upgrade socrates

Any Platform (From Source):
cd Socrates
git pull origin master
pip install -r requirements.txt

Docker:
docker pull ghcr.io/nireus79/socrates:latest
docker-compose up -d  # Recreates with new image

NEXT STEPS AFTER INSTALLATION

1. Get Started → Create your first project
2. Join Discord → Connect with community at https://discord.gg/socrates
3. Read Features → Learn what's possible at hermessoft.wordpress.com/socrates-ai/features
4. Try Examples → See sample projects at https://github.com/Nireus79/Socrates/tree/master/examples

GITHUB LINKS

Main Repository: https://github.com/Nireus79/Socrates
Releases & Downloads: https://github.com/Nireus79/Socrates/releases
Issues & Bugs: https://github.com/Nireus79/Socrates/issues
Discussions: https://github.com/Nireus79/Socrates/discussions
Contributing: https://github.com/Nireus79/Socrates/blob/master/CONTRIBUTING.md
Docker Image: https://ghcr.io/nireus79/socrates

Last Updated: January 2026
Version: 1.3.0

Ready to install? Download Now at https://github.com/Nireus79/Socrates/releases/latest
