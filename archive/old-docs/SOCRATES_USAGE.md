# Socrates.py - Usage Guide

## ✅ Modified to Support Frontend Startup with Auto-Browser Opening

The `socratic_system/ui/main_app.py` has been modified to:
1. Automatically start the React frontend along with the CLI
2. **Automatically open the browser** when frontend is ready
3. Run both CLI and Web UI simultaneously

---

## Usage

### 1️⃣ CLI Only (Default)
```bash
python socratic_system/ui/main_app.py
```

Access:
- CLI: Terminal (interactive commands)
- Database: `socratic_data/projects.db`

### 2️⃣ CLI + Frontend with Auto Browser Opening ✅ (Recommended)
```bash
python socratic_system/ui/main_app.py --frontend
```

or (short form):
```bash
python socratic_system/ui/main_app.py -f
```

**What happens:**
1. ✅ Checks dependencies
2. ✅ Installs npm modules if needed
3. ✅ Starts React dev server on port 5173
4. ✅ **Automatically opens browser to http://localhost:5173**
5. ✅ Starts FastAPI backend on port 8000
6. ✅ Starts CLI interface in terminal
7. ✅ Monitors all services

Access:
- Frontend: http://localhost:5173 (React UI) - **Auto-opened in your default browser**
- Backend API: http://localhost:8000
- CLI: Terminal (interactive commands)
- API Docs: http://localhost:8000/docs

### 3️⃣ Help
```bash
python socratic_system/ui/main_app.py --help
```

---

## What Happens With `--frontend`

```
┌─ Start Sequence ─────────────────────────────────┐
│ 1. Display banner                                │
│ 2. Check for socrates-frontend directory        │
│ 3. Install npm dependencies if needed           │
│ 4. Start React dev server (npm run dev)         │
│ 5. Wait for server to be ready (3 sec delay)   │
│ 6. ✅ OPEN BROWSER to http://localhost:5173    │
│ 7. Start backend API (FastAPI)                  │
│ 8. Start CLI command loop                       │
│    └─ Can use both Web UI and CLI simultaneously!
│ 9. Monitor processes & report status            │
│ 10. Graceful shutdown on Ctrl+C                 │
│    ├─ Stop React dev server                     │
│    ├─ Stop FastAPI backend                      │
│    └─ Exit CLI                                  │
└──────────────────────────────────────────────────┘
```

---

## Features

### ✅ Automatic Browser Opening
```
Detects your OS and opens default browser
├─ Windows: Uses default browser
├─ macOS: Uses default browser
└─ Linux: Uses default browser
```

### ✅ Automatic Dependency Installation
```
First run with --frontend?
└─ Checks for node_modules
└─ Automatically runs npm install if needed
└─ Then starts dev server
```

### ✅ Unified Startup
```
Single command starts:
├─ React dev server (port 5173)
├─ FastAPI backend (port 8000)
├─ Opens browser automatically
└─ CLI interface
```

### ✅ Graceful Shutdown
```
Press Ctrl+C:
├─ Stops React dev server
├─ Stops FastAPI backend
├─ Closes CLI
└─ Exits cleanly
```

### ✅ Process Monitoring
```
Monitors:
├─ Frontend crashes → Shows error
├─ Backend crashes → Shows error
└─ Service health
```

---

## Examples

### Example 1: Quickest Start (Complete System)
```bash
# One command starts everything
python socratic_system/ui/main_app.py --frontend

# Result:
# 1. Frontend opens in browser automatically
# 2. Backend API running on port 8000
# 3. CLI available in terminal
# 4. Everything ready to use!
```

### Example 2: Development with Web UI
```bash
# Start everything
python socratic_system/ui/main_app.py -f

# Browser automatically opens to http://localhost:5173
# In browser:
# 1. Register/Login
# 2. Create a project
# 3. Ask questions through Web UI
# 4. Chat in real-time

# In terminal (same window):
# Can also use CLI commands simultaneously!
```

### Example 3: Hybrid Usage (CLI + Web)
```bash
# Start with frontend
python socratic_system/ui/main_app.py --frontend

# Browser opens automatically
# Use Web UI for:
# - Project management
# - Real-time chat
# - Collaboration
# - Analytics

# Use CLI (in terminal) for:
# - Quick commands
# - Batch operations
# - Scripting
# - Both work simultaneously!
```

### Example 4: CLI Only (Lightweight)
```bash
# No frontend overhead
python socratic_system/ui/main_app.py

# Only terminal-based interface
# Faster startup
# Lower resource usage
```

---

## Browser Handling

### Automatic Opening
```
✅ Works on:
- Windows (default browser)
- macOS (default browser)
- Linux (default browser)

⚠️ If browser doesn't open:
- Check terminal for error message
- Manually open: http://localhost:5173
```

### Manual Fallback
```
If automatic opening fails:
1. Look for message in terminal:
   "[Frontend] Opening browser..."

2. Manually open in any browser:
   http://localhost:5173

3. Development continues normally
```

---

## Environment Variables

```bash
# API Key for Claude
export API_KEY_CLAUDE="sk-..."

# Or use subscription mode (interactive prompt)

# Frontend API URL (automatic)
# VITE_API_URL=http://localhost:8000 (set automatically)

# Browser auto-opening is handled internally
```

---

## Troubleshooting

### Problem: "Frontend directory not found"
```bash
# Make sure you're running from Socrates root:
cd /path/to/Socrates
python socratic_system/ui/main_app.py --frontend
```

### Problem: "Browser didn't open automatically"
```bash
1. Check terminal output for:
   "[Frontend] Opening browser..."

2. If error shown, still check:
   http://localhost:5173

3. Manually copy-paste URL into browser
```

### Problem: "npm not found"
```bash
# Install Node.js 14+
# https://nodejs.org/
# Then retry:
python socratic_system/ui/main_app.py --frontend
```

### Problem: "Port 5173 already in use"
```bash
# Frontend already running?
# Kill existing process:
lsof -i :5173          # Find PID
kill -9 <PID>          # Kill it
# Then restart
python socratic_system/ui/main_app.py --frontend
```

### Problem: "Port 8000 already in use"
```bash
# Backend already running?
lsof -i :8000          # Find PID
kill -9 <PID>          # Kill it
# Then restart
```

### Problem: Frontend loads but shows blank page
```bash
1. Check browser console (F12)
2. Check API connection:
   http://localhost:8000/health
3. Check that backend started:
   Look for messages in terminal
4. Try refresh (Ctrl+R or Cmd+R)
```

---

## Comparison: All Startup Methods

| Method | Command | Frontend | Browser | CLI | Auto Open |
|--------|---------|----------|---------|-----|-----------|
| **CLI Only** | `python main_app.py` | ❌ | ❌ | ✅ | N/A |
| **CLI + Frontend** | `python main_app.py -f` | ✅ | ✅ | ✅ | ✅ Auto |
| **start-dev.py** | `python scripts/start-dev.py` | ✅ | Manual | ❌ | ❌ |
| **Docker** | `docker-compose up` | ✅ | Manual | ❌ | ❌ |
| **3 Terminals** | Manual | ✅ | Manual | ✅ | ❌ |

---

## When to Use Each

### Use `python socratic_system/ui/main_app.py` (CLI Only)
- CLI-only operations
- Lightweight / low resource
- Headless servers
- Script automation

### Use `python socratic_system/ui/main_app.py --frontend` ✅ **RECOMMENDED**
- **Complete development experience**
- **Browser opens automatically**
- Can use Web UI OR CLI
- Interactive development
- Real-time collaboration testing
- Single command startup
- **Best of both worlds**

### Use `python scripts/start-dev.py`
- Web UI only (no CLI)
- Cleaner terminal output
- Better for frontend-only development

### Use `docker-compose up`
- Production-like environment
- Team development
- All services included (DB, Redis, etc.)

---

## Hybrid Workflow (Recommended)

### Best of Both Worlds
```bash
# 1. Start with single command
python socratic_system/ui/main_app.py --frontend

# 2. Browser opens automatically! 🎉
# You're now at http://localhost:5173

# 3. Use Web UI in browser
# - Create projects
# - Chat in real-time
# - View analytics
# - Manage team
# - Collaborate

# 4. Use CLI in terminal (same window)
# - Run quick commands
# - Check status
# - Execute operations
# - Debug issues
# - Run scripts

# Both work simultaneously!
# Everything shares same database
# No conflicts, synchronized state
```

---

## Summary

### Quick Start (Everything Automatic)
```bash
python socratic_system/ui/main_app.py --frontend
```

### What You Get
✅ React frontend (auto-opens in browser)
✅ FastAPI backend (http://localhost:8000)
✅ CLI interface (in terminal)
✅ Automatic npm dependency installation
✅ Graceful Ctrl+C shutdown
✅ Both Web UI and CLI working together

### Next Steps After Launch
1. Browser opens automatically to http://localhost:5173
2. Register or login with your account
3. Create your first project
4. Start asking questions!
5. Use CLI in terminal if needed

---

**You now have a complete, integrated system! 🎉**

Browser opens automatically. Everything works together. Enjoy!
