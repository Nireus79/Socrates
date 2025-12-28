# Socrates AI - System Startup Guide

Choose the startup method that best fits your needs:

---

## 1. 🚀 Development Mode (Recommended for Development)

### Single Command Startup
```bash
python scripts/start-dev.py
```

### What This Does
- ✅ Starts Backend API (FastAPI) on port 8000
- ✅ Starts Frontend Dev Server (Vite) on port 5173
- ✅ Auto-reloads on code changes
- ✅ Shows real-time logs in terminal
- ✅ Graceful shutdown with Ctrl+C

### Access Points
```
Frontend:       http://localhost:5173
Backend API:    http://localhost:8000
API Docs:       http://localhost:8000/docs
```

### Features
- **Auto-reload**: Changes automatically reload
- **Hot Module Replacement**: Frontend updates without refresh
- **Unified Logging**: All service logs in one terminal
- **Graceful Shutdown**: Ctrl+C safely closes all services
- **Process Monitoring**: Detects and reports crashes

### Requirements
- Python 3.9+
- Node.js 14+
- pip & npm

---

## 2. 🐳 Docker Compose (Recommended for Staging/Production)

### Single Command Startup
```bash
docker-compose up
```

### What This Includes
- ✅ PostgreSQL Database (port 5432)
- ✅ Redis Cache (port 6379)
- ✅ ChromaDB Vector DB (port 8001)
- ✅ FastAPI Backend (port 8000)
- ✅ React Frontend (port 3000)
- ✅ Nginx Reverse Proxy (port 80)

### Access Points
```
Frontend:       http://localhost
Backend API:    http://localhost/api
API Docs:       http://localhost/api/docs
Nginx:          http://localhost
```

### Production vs Development
```bash
# Development (hot reload)
docker-compose up

# Detached (background)
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f frontend

# Stop
docker-compose down

# Rebuild
docker-compose up --build
```

### Benefits
- All services included
- Proper networking between services
- Volume persistence
- Health checks
- Isolated environments
- Easy scaling

---

## 3. 🔧 Manual Startup (For Advanced Users)

### Terminal 1: Backend API
```bash
python -m uvicorn socratic_system.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Frontend Dev Server
```bash
cd socrates-frontend
npm run dev
```

### Terminal 3: Database (optional, if not using Docker)
```bash
# For SQLite (default)
# Database file at: socratic_data/projects.db

# For PostgreSQL
psql -U postgres -d socrates_db
```

### Benefits
- Maximum control
- Easy debugging
- Selective restart
- Minimal overhead

### Access Points
```
Frontend:       http://localhost:5173
Backend API:    http://localhost:8000
```

---

## 4. 🎯 Production Build

### Build Frontend
```bash
cd socrates-frontend
npm run build
```

### Run Backend
```bash
python -m uvicorn socratic_system.main:app --host 0.0.0.0 --port 8000
```

### With Nginx Proxy
```bash
# Install nginx
sudo apt-get install nginx

# Copy config
sudo cp nginx.conf /etc/nginx/nginx.conf

# Start nginx
sudo systemctl start nginx
```

### Docker Production Build
```bash
# Build images
docker-compose build

# Run in production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 5. 📋 Using Socrates.py CLI

### Run Interactive CLI
```bash
python socratic_system/ui/main_app.py
```

### CLI Commands
```
> new
    Create new project

> projects
    List projects

> select <id>
    Select a project to work with

> ask
    Ask a question about the current project

> help
    Show all available commands

> exit
    Exit the CLI
```

### Run Specific Command
```bash
# Non-interactive mode (if implemented)
python -m socratic_system --command "create_project" --name "My Project"
```

---

## 6. 🌐 Web UI vs CLI

### Web UI (React Frontend)
```bash
python scripts/start-dev.py
# or
docker-compose up
# Then open: http://localhost:3000 or http://localhost:5173
```

**Advantages**:
- User-friendly interface
- Visual project management
- Real-time chat interface
- Collaboration features
- Analytics dashboard

### CLI (Socrates.py)
```bash
python socratic_system/ui/main_app.py
```

**Advantages**:
- Quick access
- Scriptable
- Lightweight
- No browser needed
- Familiar for developers

### Hybrid Approach
```bash
# Start both simultaneously
python scripts/start-dev.py
# Then in another terminal:
python socratic_system/ui/main_app.py
```

---

## 7. 🔄 Startup Decision Tree

```
Are you developing?
├─ Yes
│  ├─ Single machine?
│  │  └─ python scripts/start-dev.py  ✓ (easiest)
│  └─ Multiple machines?
│     └─ docker-compose up  ✓ (consistent)
│
├─ Staging/Testing?
│  └─ docker-compose up  ✓ (production-like)
│
└─ Production?
   ├─ Small scale?
   │  └─ docker-compose up -d  ✓ (simple)
   └─ Large scale?
      └─ Kubernetes  ✓ (scalable)
```

---

## 8. 🛠️ Troubleshooting

### Issue: Port 8000 Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in start-dev.py
# Change: "--port", "8000" to "--port", "8001"
```

### Issue: Node modules not installed
```bash
cd socrates-frontend
npm install --legacy-peer-deps
```

### Issue: Python dependencies missing
```bash
pip install -r requirements.txt
pip install -r socrates-api/requirements.txt  # If separate
```

### Issue: Database connection error
```bash
# Check database file exists
ls socratic_data/projects.db

# Or reinitialize
rm socratic_data/projects.db
python scripts/start-dev.py  # Will recreate
```

### Issue: Frontend not loading
```bash
# Check if Vite server running
ps aux | grep vite

# Check port 5173
netstat -tlnp | grep 5173

# Kill and restart
pkill -f vite
cd socrates-frontend && npm run dev
```

### Issue: WebSocket connection failed
```bash
# Check backend running
curl http://localhost:8000/health

# Check CORS settings in main.py
# Frontend might need CORS headers
```

---

## 9. 📊 Performance Comparison

| Method | Startup | Reload | Control | Overhead |
|--------|---------|--------|---------|----------|
| start-dev.py | 10s | 2s | Medium | Low |
| Docker Compose | 15s | 5s | Low | Medium |
| Manual 3-terminals | 5s | 1s | High | Low |
| Production Build | 2s | N/A | Low | Very Low |

---

## 10. 🔐 Environment Variables

### Development
```bash
# .env.dev
ANTHROPIC_API_KEY=sk-...
DATABASE_URL=sqlite:///socratic_data/projects.db
VITE_API_URL=http://localhost:8000
DEBUG=true
```

### Production
```bash
# .env.prod
ANTHROPIC_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@postgres:5432/socrates_db
VITE_API_URL=https://api.example.com
DEBUG=false
```

---

## 11. 🚀 Quick Reference

### Start Development
```bash
python scripts/start-dev.py
```

### Start Production (Docker)
```bash
docker-compose up -d
```

### View Logs
```bash
# Development
# Logs appear in terminal

# Docker
docker-compose logs -f api
docker-compose logs -f frontend
```

### Stop Services
```bash
# Development
Ctrl+C

# Docker
docker-compose down
```

### Clean Everything
```bash
# Remove containers, volumes, networks
docker-compose down -v

# Remove database
rm socratic_data/projects.db
```

---

## 12. 💡 Recommendations

### For First-Time Users
👉 **Start with**: `python scripts/start-dev.py`
- Single command
- All logs in one place
- Easy to see errors
- Auto-reload on changes

### For Team Development
👉 **Start with**: `docker-compose up`
- Consistent environment
- Everyone uses same stack
- Easier onboarding
- Production-like

### For Quick Testing
👉 **Start with**: Manual 3-terminals
- Fastest startup
- Most control
- Can restart individual services
- Best for debugging

### For Production
👉 **Start with**: Docker + orchestration (Kubernetes/Nomad)
- Scalable
- Resilient
- Auto-restart
- Load balancing

---

## 13. 🔄 Workflow Examples

### Typical Development Day
```bash
# Morning: Start everything
python scripts/start-dev.py

# Work on code
# Automatic reload happens when you save

# Need CLI access? In another terminal:
python socratic_system/ui/main_app.py

# Evening: Ctrl+C to shutdown all
```

### Quick Bug Fix Testing
```bash
# Terminal 1: Start services
python scripts/start-dev.py

# Terminal 2: Run tests
pytest tests/

# Terminal 3: CLI for manual testing
python socratic_system/ui/main_app.py

# Modify code, tests auto-run, frontend auto-reloads
```

### Staging Deployment
```bash
# On staging server
docker-compose -f docker-compose.yml up -d

# Monitor
docker-compose logs -f

# Update and redeploy
git pull
docker-compose build
docker-compose up -d
```

---

**Choose the method that fits your workflow best!**
