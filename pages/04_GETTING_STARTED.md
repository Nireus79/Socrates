# Getting Started with Socrates AI

## Getting Started Header

**From idea to production code in 3 simple steps.**

Choose your platform and get started in minutes.

---

## Choose Your Platform

### Option 1: Windows (Recommended for First-Time Users)

#### Step 1: Download
- Click the **Download Windows** button
- File size: 280 MB
- Includes: Python, all dependencies, UI

#### Step 2: Install
- Double-click `socrates-installer.exe`
- Follow the on-screen prompts
- Creates desktop shortcut automatically

#### Step 3: Start
- Double-click the desktop shortcut
- Browser opens automatically
- Start your first project!

**Time to first project**: 2 minutes
**No configuration needed**

[Download Windows EXE →](download-link)

---

### Option 2: Mac/Linux

#### Prerequisites
- Python 3.8+ installed
- 5 minutes of terminal time
- ~500 MB free disk space

#### Step 1: Get the Code
```bash
git clone https://github.com/Nireus79/Socrates.git
cd Socrates
```

#### Step 2: Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
python -m pip install -r requirements.txt
```

#### Step 3: Set API Key
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

#### Step 4: Run
```bash
python socrates.py --full
```

Browser opens automatically. Start creating!

**Time to first project**: 5 minutes

[View Mac/Linux Install Guide →](install-guide-link)

---

### Option 3: Docker

#### Prerequisites
- Docker installed
- Command line comfort
- ~1 GB disk space

#### One Command to Run
```bash
docker run -it \
  -e ANTHROPIC_API_KEY="sk-ant-your-key" \
  -p 8000:8000 \
  -p 5173:5173 \
  -v socrates_data:/data \
  nireus79/socrates:latest
```

Browser opens at http://localhost:5173

**Time to first project**: 3 minutes (after Docker pulls image)

[View Docker Setup →](docker-link)

---

### Option 4: Try Online (No Installation)

**Coming Soon!**
Try Socrates in your browser without installing anything.

[Notify Me When Available →](notify-link)

---

## Get Your API Key (1 minute)

**Socrates needs Claude API access to generate code.**

### Step 1: Visit Anthropic
Go to https://console.anthropic.com

### Step 2: Sign Up (if needed)
- Create account or sign in
- Free API tier available ($5 free credit/month)

### Step 3: Get API Key
- Click "API Keys"
- Click "Create new key"
- Copy the key (starts with `sk-ant-`)

### Step 4: Set in Socrates
**Windows**: Already configured during installation
**Mac/Linux**: `export ANTHROPIC_API_KEY="sk-ant-your-key"`
**Docker**: Pass as environment variable

**⚠️ Important**: Keep your API key secret! Treat it like a password.

[Get Your API Key →](https://console.anthropic.com)

---

## Your First Project (5 minutes)

### Create a Project

1. **Login/Register**
   - Create an account with Socrates
   - Or login with existing account

2. **New Project**
   - Click "Create Project"
   - Enter project name
   - Click "Create"

3. **Start Dialogue**
   - Socrates shows first question
   - Answer based on your project
   - Click "Next" to continue

### Example: Building a Task Manager

**Question**: "What problem are you solving?"
**Your Answer**: "I need a simple task manager for personal use. Users should be able to create, edit, and complete tasks."

**Question**: "Who are your users?"
**Your Answer**: "Just me initially, but might scale to a small team of 5-10 people."

**Question**: "What does success look like?"
**Your Answer**: "A web app where tasks are persistent and quick to manage. Should work on mobile too."

### The 4 Phases

#### Phase 1: Discovery (5-10 questions)
- What problem are we solving?
- Who are the users?
- What's the goal?
- Success criteria?

#### Phase 2: Analysis (8-12 questions)
- What specific features?
- What constraints?
- What tech stack?
- What dependencies?

#### Phase 3: Design (5-10 questions)
- How will it work?
- What's the architecture?
- Database design?
- Security approach?

#### Phase 4: Implementation
- Generate production code
- Download specifications
- Export to your tools
- Start building!

---

## Generate Your First Code (2 minutes)

### After Completing Phase 4

1. **Review Specifications**
   - Socrates shows what it learned
   - Check for clarity
   - Make corrections if needed

2. **Generate Code**
   - Click "Generate Code"
   - Select language (Python, JavaScript, Go, etc.)
   - Wait 10-30 seconds

3. **Download**
   - View generated code
   - Copy to clipboard
   - Or download as file
   - Export full specification

### What You Get

✅ **Complete Project Structure**
- Organized file layout
- All dependencies listed
- Configuration files included

✅ **Documented Code**
- Comments explaining logic
- Docstrings for functions
- README with setup instructions

✅ **Specifications**
- Detailed requirements
- Architecture decisions
- Database schema (if applicable)

✅ **Ready to Deploy**
- Production-ready code
- Error handling included
- Security best practices
- Performance optimized

---

## Next Steps

### 1. Run the Code
```bash
# Example: If generated Python code
python app.py
```

### 2. Extend It
- Add more features
- Integrate with APIs
- Deploy to production

### 3. Create More Projects
- Start a new project with Socrates
- Generate another service
- Combine them together

### 4. Collaborate
- Invite team members (Pro tier)
- Share specifications
- Work together on requirements

---

## Common First Questions

### Q: What if I don't know how to answer a question?
**A**: Say "Not sure" or "Not decided yet". Socrates will ask differently or suggest options.

### Q: Can I change my answers?
**A**: Yes! Go back with `/back` command or click "Previous" in UI.

### Q: How long does it take to complete all phases?
**A**: Usually 30 minutes to 2 hours depending on project complexity.

### Q: Is the generated code production-ready?
**A**: Nearly! It's high-quality, but always:
- Review before deploying
- Add tests
- Test with real data
- Deploy to staging first

### Q: Can I generate code again for the same project?
**A**: Yes! Generate as many times as you want. Each generation is fresh.

### Q: What if I want to change the project requirements?
**A**: Update specifications, then regenerate code. Socrates will adjust.

### Q: Can my team use the same project?
**A**: Yes (Pro tier)! Invite team members and share projects.

---

## Keyboard Shortcuts

### In CLI Mode

| Shortcut | Action |
|----------|--------|
| `/continue` | Next question |
| `/back` | Previous question |
| `/hint` | Get hint for current question |
| `/advance` | Move to next phase |
| `/code generate` | Generate code |
| `/project list` | List all projects |
| `/project export` | Export current project |
| `/status` | Show system status |
| `/debug on` | Enable debug mode |
| `/help` | Show all commands |

---

## Troubleshooting First-Time Setup

### Browser Won't Connect

**Problem**: "Cannot reach localhost:5173"

**Solution**:
1. Wait 15 seconds (app needs time to start)
2. Manually go to http://localhost:5173
3. Check that console window is still running
4. Restart the application

### "API Key Required" Error

**Problem**: Socrates says it needs your API key

**Solution**:
```bash
# Windows: Already set during installation

# Mac/Linux: Run this command
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Then restart Socrates
python socrates.py
```

### "Port Already in Use"

**Problem**: Error about port 5173 or 8000 in use

**Solution**:
```bash
# Kill other running instances
pkill -f socrates  # macOS/Linux
taskkill /IM python.exe /F  # Windows

# Then restart
python socrates.py
```

### Performance Issues

**Problem**: Socrates is slow or unresponsive

**Solution**:
1. Check internet connection
2. Close other applications
3. Give it more time (first response might take 5-10 seconds)
4. Check CPU/RAM usage

[Full Troubleshooting Guide →](troubleshooting-link)

---

## Learning Resources

### Documentation
- [User Guide](user-guide-link) - Complete feature walkthrough
- [FAQ](faq-link) - Answers to common questions
- [Video Tutorials](videos-link) - Step-by-step demonstrations

### Community
- [Discord Community](discord-link) - Chat with other users
- [GitHub Discussions](github-discussions) - Ask questions
- [GitHub Issues](github-issues) - Report problems

### Examples
- [Task Manager Example](example-1)
- [API Service Example](example-2)
- [Full Stack App Example](example-3)

---

## Advanced Setup (Optional)

### Custom Port
```bash
python socrates.py --api --port 9000
```

### Offline/Headless Mode
```bash
python socrates.py --api
```

### Debug Mode
```bash
export SOCRATES_LOG_LEVEL=DEBUG
python socrates.py
```

### Custom Data Directory
```bash
export SOCRATES_DATA_DIR="/custom/path"
python socrates.py
```

[Advanced Configuration →](configuration-link)

---

## What's Your Next Step?

### Learn More
→ [View Features Guide](features-link)

### Read Documentation
→ [Full User Guide](user-guide-link)

### Get Help
→ [Browse FAQ](faq-link)

### Join Community
→ [Discord Community](discord-link)

### View Examples
→ [Project Examples](examples-link)

---

## Ready to Get Started?

### Download Now
[Download Windows] [Install Mac/Linux] [Docker] [Try Online (Coming)]

### Already Installed?
[Open Socrates] [Create Project] [View Help]

---

**Questions?** [Contact Support](support-link)
**Found a bug?** [Report on GitHub](github-issues)
**Have feedback?** [Join Discord](discord-link)

---

**Last Updated**: January 2026
**Version**: 1.3.0

**Welcome to Socrates! 🎓**
