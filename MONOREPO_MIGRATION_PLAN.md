# Monorepo Migration Plan

**Status**: Ready for implementation
**Estimated Effort**: 2-3 hours
**Risk Level**: Low (can be rolled back easily)
**Benefits**: Fixes debugging issues, simplifies imports, atomic commits

---

## Overview

Move from separate repositories (Socrates, Socrates-api, Socrates-cli) to a single monorepo in the Socrates directory.

---

## Current Structure

```
C:\Users\themi\PycharmProjects\
├── Socrates/                 (Frontend + main)
│   ├── socrates-frontend/
│   └── ...
├── Socrates-api/             (API - installed as package)
│   ├── src/socrates_api/
│   └── setup.py
└── Socrates-cli/             (CLI - installed as package)
    ├── src/socrates_cli/
    └── setup.py
```

## Target Structure

```
C:\Users\themi\PycharmProjects\Socrates/  (Single monorepo)
├── frontend/                 (React code)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
├── backend/                  (API code from Socrates-api)
│   ├── src/socrates_api/
│   ├── tests/
│   └── README.md
├── cli/                      (CLI code from Socrates-cli)
│   ├── src/socrates_cli/
│   └── README.md
├── requirements.txt          (All Python dependencies)
├── package.json              (All Node dependencies)
├── .env                      (Single config)
└── scripts/                  (Build/run scripts)
```

---

## Step-by-Step Migration

### Phase 1: Preparation (15 minutes)

#### 1.1: Backup Current State
```bash
# Backup current repos (keep on disk as reference)
cp -r Socrates Socrates.backup
cp -r Socrates-api Socrates-api.backup
cp -r Socrates-cli Socrates-cli.backup
```

#### 1.2: Create Directory Structure
```bash
cd C:\Users\themi\PycharmProjects\Socrates

# Create new directories
mkdir -p backend/{src,tests}
mkdir -p cli/{src,tests}
mkdir -p frontend/src

# Keep existing frontend in place, will organize later
```

---

### Phase 2: Move Backend Code (20 minutes)

#### 2.1: Copy API Code
```bash
# Copy from Socrates-api to Socrates
cp -r ../Socrates-api/src/socrates_api backend/src/

# Copy tests if they exist
cp -r ../Socrates-api/tests/* backend/tests/ 2>/dev/null || echo "No tests found"

# Copy documentation
cp ../Socrates-api/README.md backend/ || echo "No README"
```

#### 2.2: Copy CLI Code
```bash
# Copy from Socrates-cli
cp -r ../Socrates-cli/src/socrates_cli cli/src/

# Copy tests
cp -r ../Socrates-cli/tests/* cli/tests/ 2>/dev/null || echo "No tests found"

# Copy documentation
cp ../Socrates-cli/README.md cli/ || echo "No README"
```

---

### Phase 3: Update Python Path Configuration (15 minutes)

#### 3.1: Create PYTHONPATH Setup
Create `C:\Users\themi\PycharmProjects\Socrates\setup_env.sh`:
```bash
#!/bin/bash
# Setup environment for monorepo development

export PYTHONPATH="${PWD}/backend/src:${PWD}/cli/src:${PYTHONPATH}"

echo "PYTHONPATH configured for monorepo"
echo "Backend: ${PWD}/backend/src"
echo "CLI: ${PWD}/cli/src"
```

On Windows (PowerShell):
Create `setup_env.ps1`:
```powershell
$env:PYTHONPATH = "$PWD\backend\src;$PWD\cli\src;$env:PYTHONPATH"
Write-Host "PYTHONPATH configured"
```

#### 3.2: Update Imports in Backend Code

Search and replace in `backend/src/socrates_api/`:
```
# From:
from socrates_api.

# To:
from socrates_api.  (stays the same - local import)
```

Actually, imports should work as-is because we're using `src/` layout. Python will find `socrates_api` at `backend/src/socrates_api/`.

#### 3.3: Verify Import Paths

Test imports work:
```bash
export PYTHONPATH=backend/src
python -c "from socrates_api.main import app; print('Import OK')"
```

---

### Phase 4: Merge Dependencies (10 minutes)

#### 4.1: Combine Python Requirements
```bash
# Merge Socrates-api and Socrates-cli requirements
cat > requirements.txt <<EOF
# Backend API
fastapi==0.135.2
uvicorn==0.42.0
starlette==1.0.0

# CLI
click>=8.0.0

# Database & ORM
sqlalchemy>=2.0

# Auth & Security
pyjwt>=2.8.0
bcrypt>=4.1.0

# Utils
python-dotenv>=1.0
requests>=2.31.0

# Dev dependencies
pytest>=7.0
pytest-asyncio>=0.21.0
black>=23.0
flake8>=6.0
mypy>=1.0

# (Add any others from original requirements)
EOF
```

#### 4.2: Install Combined Dependencies
```bash
pip install -r requirements.txt
```

---

### Phase 5: Create Run Scripts (10 minutes)

#### 5.1: Create Backend Start Script
Create `scripts/run_backend.sh`:
```bash
#!/bin/bash
export PYTHONPATH=backend/src:$PYTHONPATH
python -m socrates_api
```

Or `scripts/run_backend.ps1` for PowerShell:
```powershell
$env:PYTHONPATH = "backend\src;$env:PYTHONPATH"
python -m socrates_api
```

#### 5.2: Create Frontend Start Script
Create `scripts/run_frontend.sh`:
```bash
#!/bin/bash
cd frontend
npm run dev
```

#### 5.3: Create Full-Stack Start Script
Create `scripts/run_full_stack.sh`:
```bash
#!/bin/bash
# Start both backend and frontend in parallel

echo "Starting Socrates Full Stack..."

# Start backend
./scripts/run_backend.sh &
BACKEND_PID=$!

# Give backend time to initialize
sleep 3

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!

echo "Full stack running (PIDs: $BACKEND_PID, $FRONTEND_PID)"
echo "Frontend: http://localhost:5173"
echo "Backend: http://localhost:8000"

# Wait for both
wait
```

---

### Phase 6: Update Git Configuration (10 minutes)

#### 6.1: Remove Old Package References
```bash
cd Socrates

# Remove separate package installs
pip uninstall socrates-api -y 2>/dev/null || true
pip uninstall socrates-cli -y 2>/dev/null || true
```

#### 6.2: Add Directory to Git
```bash
# Add new directories
git add backend/ cli/ scripts/

# Commit the monorepo structure
git commit -m "chore: Move to monorepo structure

Consolidated Socrates-api and Socrates-cli into single Socrates repo.

Changes:
- backend/ <- Socrates-api code
- cli/ <- Socrates-cli code
- scripts/ <- Run scripts for monorepo
- requirements.txt <- Merged dependencies

Benefits:
- Atomic commits across frontend/backend/cli
- Simpler debugging and development
- Single deployment unit
- No package installation issues"
```

#### 6.3: Stop Tracking Old Repos
```bash
# Remove the old repos from tracking (in separate terminal)
cd Socrates-api
git remote remove origin  # Disconnect from GitHub
cd ../Socrates-cli
git remote remove origin
```

---

### Phase 7: Update Documentation (5 minutes)

#### 7.1: Create Root README
Create `Socrates/README.md`:
```markdown
# Socrates - AI-Powered Education Platform

Monorepo containing Frontend, API, and CLI for the Socrates system.

## Directory Structure

- **frontend/** - React TypeScript application
- **backend/** - FastAPI Python API server
- **cli/** - Python CLI tools
- **scripts/** - Build and run scripts

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- pip

### Setup

```bash
# 1. Set Python path
source setup_env.sh  # macOS/Linux
or
.\setup_env.ps1     # Windows PowerShell

# 2. Install dependencies
pip install -r requirements.txt
cd frontend && npm install

# 3. Create .env file
cp .env.example .env
# Edit .env with your configuration
```

### Running the Full Stack

#### Option 1: Separate terminals
```bash
# Terminal 1: Backend
source setup_env.sh
python -m socrates_api

# Terminal 2: Frontend
cd frontend
npm run dev
```

#### Option 2: One command
```bash
./scripts/run_full_stack.sh
```

### Accessing the Application

- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Development

#### Backend
```bash
cd backend
source ../setup_env.sh
pytest  # Run tests
python -m socrates_api  # Start server
```

#### Frontend
```bash
cd frontend
npm run dev
```

#### CLI
```bash
python -m socrates_cli --help
```

## Project Structure

```
Socrates/
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/
│   ├── src/socrates_api/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── models.py
│   │   └── ...
│   ├── tests/
│   └── README.md
├── cli/
│   ├── src/socrates_cli/
│   └── README.md
├── scripts/
├── requirements.txt
└── .env
```

## Dependencies

See `requirements.txt` for Python dependencies.
See `frontend/package.json` for Node dependencies.

## Contributing

All changes should be made to the appropriate directory (frontend/, backend/, cli/).

Commits should follow conventional commit format:
```
feat(backend): Add new API endpoint
fix(frontend): Fix routing bug
docs: Update README
```

## Deployment

The entire stack can be deployed as a single unit from this repository.
```

#### 7.2: Create Setup Guide
Create `SETUP_GUIDE.md`:
```markdown
# Detailed Setup Guide

See README.md for quick start, this guide covers detailed configuration.

## Environment Variables

Copy to `.env`:
```
# Backend
SOCRATES_API_HOST=127.0.0.1
SOCRATES_API_PORT=8000
JWT_SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./test.db

# Frontend
VITE_API_URL=http://localhost:8000
```

...etc
```

---

## Rollback Plan (If Needed)

If issues arise:

```bash
# Option 1: Use backup
rm -rf Socrates
cp -r Socrates.backup Socrates
cd Socrates
git reset --hard HEAD~1

# Option 2: Keep working with monorepo and fix issues
# (Monorepo is less risky than original multi-repo setup)
```

---

## Timeline for Implementation

| Phase | Task | Time | Who |
|---|---|---|---|
| 1 | Preparation & backup | 15 min | Developer |
| 2 | Move backend/CLI code | 20 min | Developer |
| 3 | Update Python paths | 15 min | Developer |
| 4 | Merge dependencies | 10 min | Developer |
| 5 | Create run scripts | 10 min | Developer |
| 6 | Git configuration | 10 min | Developer |
| 7 | Documentation | 5 min | Developer |
| **Total** | **Full migration** | **85 min** | |

---

## Testing After Migration

### 1. Backend
```bash
export PYTHONPATH=backend/src
python -c "from socrates_api.main import app; print('✓ Backend imports OK')"
python -m socrates_api &
sleep 3
curl http://localhost:8000/health  # Should return 200
kill %1
```

### 2. Frontend
```bash
cd frontend
npm install
npm run build  # Should succeed
npm run dev &
sleep 3
# Check http://localhost:5173
kill %1
```

### 3. Full Stack
```bash
./scripts/run_full_stack.sh &
# Test both frontend and backend work together
kill %1
```

---

## Post-Migration Cleanup

### 1. Remove Old Repos (Optional)
```bash
cd ../
rm -rf Socrates-api
rm -rf Socrates-cli
```

### 2. Update Any CI/CD
Update GitHub Actions or other CI to point to monorepo.

### 3. Update Team Documentation
Let team know new repo structure and development workflow.

---

## Benefits After Migration

✅ **Single source of truth** - Everything in one place
✅ **Atomic commits** - Frontend + backend changes in one commit
✅ **Simpler debugging** - All code visible, easier to trace issues
✅ **Unified dependencies** - Single requirements.txt, no conflicts
✅ **Easier deployment** - Deploy entire stack from one repo
✅ **Better IDE support** - Integrated project in one directory
✅ **Clearer git history** - Related changes together

---

## Notes

- The `.src/` layout is preserved for imports to work correctly
- PYTHONPATH must be set before running (handled by setup_env script)
- Old repos can be kept as backup until monorepo is fully tested
- No changes to actual code logic needed, just organization

---

**Status**: Ready to execute
**Complexity**: Low (mostly moving files and updating paths)
**Risk**: Very Low (can be rolled back easily)

