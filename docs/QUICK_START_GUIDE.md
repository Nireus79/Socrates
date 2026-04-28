# Socrates Quick Start Guide (5-10 Minutes)

Get Socrates running locally in minutes!

---

## Prerequisites Check (1 minute)

Verify you have these installed:

```bash
# Check Python
python --version      # Should be 3.8+ (3.11+ recommended)

# Check Node.js
node --version        # Should be 14+
npm --version         # Should be 6+
```

If either is missing, install from:
- **Python**: https://www.python.org/downloads/
- **Node.js**: https://nodejs.org/

---

## Clone & Setup (2 minutes)

```bash
# Clone repository (note capital S!)
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Get your API key from https://console.anthropic.com/api/keys
# Copy and save it - you'll need it in the next step

# Copy environment template
cp deployment/configurations/.env.example .env

# Edit .env file and add your API key
# Find this line and replace with your actual key:
# ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
nano .env          # or use your preferred editor
```

---

## Install Dependencies (2-3 minutes)

```bash
# Create Python virtual environment
python -m venv .venv

# Activate it
# On Linux/macOS:
source .venv/bin/activate

# On Windows (Command Prompt):
.venv\Scripts\activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd socrates-frontend
npm install
cd ..
```

---

## Start the System (1 minute)

```bash
# Run startup script
# On Linux/macOS:
bash scripts/start-dev.sh

# On Windows:
scripts\start-dev.bat
```

Wait for both services to start:
- ✅ Backend API: http://localhost:8000
- ✅ Frontend: http://localhost:5173

---

## Access & Create Account (1-2 minutes)

1. **Open Browser**: http://localhost:5173
2. **Sign Up**: Click "Sign Up" button
3. **Create Account**: Enter username and password
4. **Add API Key**:
   - Go to Settings > LLM > Anthropic
   - Paste your API key
   - Click Save
5. **Create Project**: Click "New Project" and fill details

---

## What You Can Do Now

✅ **Chat with AI**: Ask Socrates questions about your project
✅ **Generate Code**: Use AI to generate code snippets
✅ **Ask Questions**: Use Socratic Method for problem-solving
✅ **Manage Projects**: Create and organize projects
✅ **View API Docs**: http://localhost:8000/docs

---

## Troubleshooting Quick Tips

**Port 8000/5173 already in use?**
```bash
# Linux/macOS: Find process
lsof -i :8000

# Windows: Find process
netstat -ano | findstr :8000

# Kill the process or use different port
```

**Virtual environment not activating?**
```bash
# Make sure you're in the Socrates directory
pwd   # Should end in /Socrates

# Try again with full path
source ./venv/bin/activate
```

**API key not working?**
```bash
# Double-check in .env file
cat .env | grep ANTHROPIC_API_KEY

# Verify the key starts with sk-ant-
# Get a new key if expired: https://console.anthropic.com/api/keys
```

**npm install fails?**
```bash
# Clear npm cache
npm cache clean --force

# Try again
cd socrates-frontend && npm install
```

---

## Next Steps

- 📖 Read [User Guide](USER_GUIDE.md) to learn features
- 🏗️ Check [Architecture](ARCHITECTURE.md) to understand the system
- 🔧 See [Configuration](CONFIGURATION.md) for advanced options
- 🚀 Deploy to Docker: See [Deployment Guide](DEPLOYMENT.md)

---

## Get Help

- 💬 Check [Troubleshooting](TROUBLESHOOTING.md) for common issues
- 🐛 Report bugs: https://github.com/Nireus79/Socrates/issues
- 📧 Email: support@socrates-ai.dev

---

**You're all set!** Start exploring Socrates! 🚀
