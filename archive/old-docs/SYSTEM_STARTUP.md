# Socrates AI - System Startup (Recommended Approach)

## 🎯 Quick Start

```bash
python scripts/start-dev.py
```

**That's it!** This single command starts:
- ✅ Backend API (FastAPI) - http://localhost:8000
- ✅ Frontend Dev Server (Vite) - http://localhost:5173
- ✅ All dependencies auto-installed
- ✅ Auto-reloading on code changes
- ✅ Unified logging in one terminal
- ✅ Graceful shutdown with Ctrl+C

---

## Why Python is the Best Choice

### 1. **Cross-Platform**
```
✓ Windows (start-dev.py directly)
✓ macOS (python start-dev.py)
✓ Linux (python start-dev.py)
```

vs.

```
✗ Batch files (.bat) - Windows only
✗ Shell scripts (.sh) - macOS/Linux only
```

### 2. **No Shell Dependencies**
```python
# Python handles everything:
- Platform detection
- Path resolution
- Signal handling
- Process management
```

vs.

```bash
# Shell scripts need:
- Bash installed
- Different syntax for Windows
- Manual signal handling
- Environment setup
```

### 3. **Better Error Handling**
```python
# Python can:
- Validate prerequisites with try/except
- Show readable error messages
- Handle timeouts gracefully
- Manage process lifecycle
```

vs.

```bash
# Shell scripts:
- Limited error handling
- Less readable output
- Can hang on errors
```

### 4. **Pre-startup Checks**
```python
# start-dev.py automatically:
1. Checks Python version
2. Checks Node.js version
3. Installs Python dependencies if needed
4. Installs Node dependencies if needed
5. Validates all tools available
```

---

## File Structure

```
Socrates/
├── scripts/
│   ├── start-dev.py         ← USE THIS (Primary)
│   ├── start-dev.bat        (Windows alternative)
│   └── start-dev.sh         (Linux/macOS alternative)
├── STARTUP_GUIDE.md         (Detailed guide)
├── SYSTEM_STARTUP.md        (This file)
├── docker-compose.yml       (For production)
└── ...
```

---

## Usage Scenarios

### Development (Most Common)
```bash
cd /path/to/Socrates
python scripts/start-dev.py
```

### With Virtual Environment
```bash
cd /path/to/Socrates
source venv/bin/activate  # or: venv\Scripts\activate on Windows
python scripts/start-dev.py
```

### In IDE (VS Code, PyCharm)
```python
# In IDE terminal, run:
python scripts/start-dev.py

# Or create Run Configuration:
# Script path: scripts/start-dev.py
# Working directory: project root
```

### Automated (CI/CD)
```bash
# In GitHub Actions or similar:
python scripts/start-dev.py
# Runs until Ctrl+C or process terminated
```

---

## What Happens Step by Step

```
1. Check Prerequisites
   ├─ Python 3.9+ ✓
   ├─ Node.js 14+ ✓
   └─ npm ✓

2. Install Dependencies
   ├─ pip install -r requirements.txt (if needed)
   └─ npm install in socrates-frontend (if needed)

3. Start Backend
   ├─ python -m uvicorn main:app --reload
   ├─ Listening on http://localhost:8000
   └─ Auto-reload on code changes

4. Start Frontend
   ├─ npm run dev
   ├─ Listening on http://localhost:5173
   └─ Hot module replacement active

5. Monitor & Report
   ├─ Display access URLs
   ├─ Monitor process health
   └─ Handle graceful shutdown
```

---

## Access Points After Startup

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend UI | http://localhost:5173 | React application |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| API Redoc | http://localhost:8000/redoc | ReDoc UI |
| Database | socratic_data/projects.db | SQLite file |

---

## Features of start-dev.py

### ✅ Automatic Prerequisite Installation
```
Not installed?           Automatically installs
─────────────────────────────────────────
Python deps             → pip install
Node deps               → npm install
```

### ✅ Cross-Platform Compatibility
```
Windows:     python scripts/start-dev.py  ✓
macOS:       python scripts/start-dev.py  ✓
Linux:       python scripts/start-dev.py  ✓
```

### ✅ Unified Logging
All services log to single terminal:
```
Backend: [startup] Uvicorn running
Frontend: [startup] VITE v4.x.x
Backend: [request] GET /health
```

### ✅ Graceful Shutdown
```
Press Ctrl+C:
├─ Signals all processes
├─ Waits for clean termination
├─ Closes file handles
└─ Exits cleanly
```

### ✅ Process Monitoring
```
Watches for crashes:
├─ Backend dies? → Shows error
├─ Frontend dies? → Shows error
└─ Auto-logs to temporary files
```

---

## Comparison with Alternatives

### vs. Docker Compose
```
start-dev.py                    docker-compose up
──────────────────────────────  ─────────────────────────
✓ Fast startup (10s)            ✓ Production-like (15s)
✓ Lightweight                   ✓ All services included
✓ Easy debugging                ✓ Consistent environment
✗ No database included          ✗ Heavier overhead
✗ No Redis/ChromaDB             ✗ Longer startup
```

**When to use Docker Compose:**
- Staging/production
- Need all services (PostgreSQL, Redis, etc.)
- Team development

### vs. Manual (3 terminals)
```
start-dev.py                    3x Terminal Windows
──────────────────────────────  ─────────────────────
✓ Single command                ✓ Most control
✓ Unified logging               ✓ Can restart individually
✓ Single Ctrl+C to stop all     ✗ More terminal management
✗ Less flexibility              ✗ More complex
```

**When to use 3 terminals:**
- Advanced debugging
- Need to restart single service
- Experienced developers

### vs. Socrates.py CLI
```
start-dev.py                    python socratic_system/ui/main_app.py
──────────────────────────────  ────────────────────────────────
✓ Web UI + CLI                  ✓ CLI only
✓ Real-time chat               ✗ No web interface
✓ Full feature access          ✓ Lightweight
✗ Need browser                  ✓ Quick access
```

**When to use CLI only:**
- Headless systems
- Server-only deployment
- Quick command execution

---

## Troubleshooting

### Problem: "Python not found"
```bash
# Install Python 3.9+
# Then in the directory:
python scripts/start-dev.py
# or
python3 scripts/start-dev.py
```

### Problem: "Port 8000 already in use"
```python
# Edit scripts/start-dev.py, find:
"--port", "8000",

# Change to:
"--port", "8001",
```

### Problem: "npm not found"
```bash
# Install Node.js 14+
# Includes npm automatically
# Then retry:
python scripts/start-dev.py
```

### Problem: "Module not found" on startup
```bash
# Manually install dependencies:
pip install -r requirements.txt
cd socrates-frontend && npm install
# Then run:
python scripts/start-dev.py
```

### Problem: Frontend not reloading
```
1. Check if Vite is running (port 5173)
2. Check browser console for errors
3. Restart frontend in scripts/start-dev.py
```

### Problem: Backend crashing
```
1. Check logs in /tmp/socrates-*.log
2. Check syntax errors in Python files
3. Check database file exists
4. Restart script
```

---

## Integration with Your Workflow

### With VS Code
```
1. Open VS Code in Socrates folder
2. Integrated Terminal → python scripts/start-dev.py
3. Watch logs in integrated terminal
4. Edit code, save (auto-reload happens)
5. Open http://localhost:5173 in browser
```

### With PyCharm
```
1. Open PyCharm in Socrates folder
2. Python Console → python scripts/start-dev.py
3. Watch logs in console
4. Edit code, save (auto-reload happens)
5. Open http://localhost:5173 in browser
```

### With Git Workflow
```
1. git checkout feature-branch
2. python scripts/start-dev.py
3. Develop and test
4. Code auto-reloads on save
5. Ctrl+C to stop
6. git add/commit/push
```

---

## Performance

| Metric | Time |
|--------|------|
| Initial startup | 10-15 seconds |
| Backend reload on change | 2-3 seconds |
| Frontend reload on change | < 1 second |
| Graceful shutdown | < 5 seconds |
| Memory usage | ~200-300 MB |

---

## Next Steps

1. **First Time?**
   ```bash
   python scripts/start-dev.py
   ```

2. **Open in Browser**
   ```
   http://localhost:5173
   ```

3. **Create a Project**
   - Click "New Project"
   - Enter project details
   - Start asking questions

4. **View API Docs**
   ```
   http://localhost:8000/docs
   ```

5. **For Production**
   ```bash
   docker-compose up -d
   ```

---

## Summary

### Recommended Startup Method
```bash
python scripts/start-dev.py
```

### Why This Approach
✅ Single command
✅ Cross-platform
✅ Auto-installs dependencies
✅ Unified logging
✅ Easy to use
✅ Perfect for development

### Alternative for Production
```bash
docker-compose up -d
```

### Alternative for Advanced Users
```bash
# Terminal 1:
python -m uvicorn socratic_system.main:app --reload

# Terminal 2:
cd socrates-frontend && npm run dev

# Terminal 3:
python socratic_system/ui/main_app.py
```

---

**Ready to start?**
```bash
python scripts/start-dev.py
```
