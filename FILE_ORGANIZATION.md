# File Organization Guide

**Date:** January 15, 2026

**Purpose:** Organize project files for production deployment and maintenance

---

## Directory Structure

```
socrates/
│
├── 📦 Source Code (Version Controlled)
│   ├── socratic_system/          # Core system modules
│   ├── socrates-api/             # FastAPI backend
│   ├── socrates-cli/             # CLI tool
│   ├── socrates-frontend/        # React frontend
│   ├── tests/                    # Test suite (180+ tests)
│   ├── alembic/                  # Database migrations
│   ├── alembic.ini               # Alembic configuration
│   ├── requirements.txt           # Python dependencies
│   └── requirements-test.txt      # Test dependencies
│
├── 📋 Root Configuration Files (Essential)
│   ├── .gitignore                # Git ignore rules
│   ├── .dockerignore             # Docker ignore rules
│   ├── .pre-commit-config.yaml   # Pre-commit hooks
│   ├── LICENSE                   # MIT License
│   ├── README.md                 # Project overview
│   ├── CHANGELOG.md              # Version history
│   └── .github/                  # GitHub workflows & templates
│
├── 📚 Documentation
│   └── docs/
│       ├── deployment/           # Deployment guides
│       │   ├── DEPLOYMENT_CHECKLIST.md      # 3-phase deployment
│       │   ├── STAGING_SETUP.md             # Staging environment
│       │   ├── GITHUB_TESTING_GUIDE.md      # GitHub integration testing
│       │   ├── PRODUCTION_READINESS.md      # Readiness verification
│       │   └── DEPLOYMENT_READY.md          # Quick reference
│       ├── api/                  # API documentation
│       ├── guides/               # General guides
│       ├── IMPLEMENTATION_COMPLETE.md       # Project completion
│       └── PROJECT_STRUCTURE.md             # Architecture overview
│
├── 🚀 Deployment Configuration
│   └── deployment/
│       ├── docker/               # Container configuration
│       │   ├── Dockerfile                  # Production container
│       │   ├── Dockerfile.prod             # Security-hardened
│       │   ├── docker-compose.yml          # Local/staging setup
│       │   └── nginx.conf                  # Reverse proxy
│       ├── configurations/       # Configuration files
│       │   ├── .env.example                # Environment template
│       │   ├── .env.local                  # Local development
│       │   ├── .env.local.example          # Local template
│       │   ├── .env.production.example     # Production template
│       │   └── socrates-api.service        # Systemd service
│       ├── kubernetes/           # K8s manifests (optional)
│       └── helm/                 # Helm charts (optional)
│
├── 📁 Examples & Reference
│   └── examples/                 # Example projects and code
│
├── 📦 Dependencies & Environment
│   ├── .venv/                    # Python virtual environment
│   └── node_modules/             # Node.js packages
│
├── 🗂️ Archive (Not Needed for Production)
│   ├── old-dockerfiles/          # Old Docker configurations
│   ├── old-configs/              # Old configuration files
│   ├── build-artifacts/          # Old build outputs
│   ├── migration_scripts/        # Old migration scripts
│   └── ...                       # Other archived files
│
└── .idea/                        # IDE configuration (not committed)
```

---

## Critical Files for Deployment

### 🔴 Must Have (DO NOT DELETE)
- `socratic_system/` - Core application code
- `socrates-api/` - Backend API
- `socrates-frontend/` - Frontend UI
- `tests/` - Test suite
- `alembic/` - Database migrations
- `docs/deployment/` - Deployment documentation
- `deployment/docker/` - Container configuration
- `deployment/configurations/` - Environment files
- `.github/` - CI/CD workflows
- `requirements.txt` - Dependencies

### 🟡 Important (Keep in Version Control)
- `README.md` - Project overview
- `CHANGELOG.md` - Version history
- `.gitignore` - Git rules
- `.pre-commit-config.yaml` - Code quality hooks
- `LICENSE` - License

### 🟢 Optional (Can Archive)
- `examples/` - Example code
- `docs/api/` - API documentation
- `docs/guides/` - General guides
- `archive/` - Old files and artifacts
- `.idea/` - IDE configuration

---

## File Organization Details

### 1. Deployment Documentation
**Location:** `docs/deployment/`

Essential deployment guides:
- ✅ `DEPLOYMENT_CHECKLIST.md` - 3-phase deployment procedure
- ✅ `STAGING_SETUP.md` - Staging environment guide (10 steps)
- ✅ `GITHUB_TESTING_GUIDE.md` - GitHub integration testing (13 tests)
- ✅ `PRODUCTION_READINESS.md` - Readiness verification checklist
- ✅ `DEPLOYMENT_READY.md` - Quick reference guide

**Use:** Follow guides in order during deployment

---

### 2. Docker & Container Configuration
**Location:** `deployment/docker/`

Production configuration files:
- ✅ `Dockerfile` - Production-optimized container
- ✅ `Dockerfile.prod` - Security-hardened with gunicorn
- ✅ `docker-compose.yml` - Local/staging environment
- ✅ `nginx.conf` - Reverse proxy with HTTPS/SSL

**Use:** Use in Docker build and Compose commands

---

### 3. Environment Configuration
**Location:** `deployment/configurations/`

Environment templates and service files:
- ✅ `.env.example` - General environment template
- ✅ `.env.local` - Local development environment
- ✅ `.env.local.example` - Local template
- ✅ `.env.production.example` - Production template
- ✅ `socrates-api.service` - Systemd service file

**Use:** Copy and customize for each environment

---

### 4. Kubernetes & Helm (Optional)
**Location:** `deployment/kubernetes/` and `deployment/helm/`

Optional Kubernetes configuration:
- K8s manifests for container orchestration
- Helm charts for package management

**Use:** Only if deploying to Kubernetes

---

### 5. Archived Files
**Location:** `archive/`

Old files not needed for current deployment:
- `old-dockerfiles/` - Previous Docker configurations
- `old-configs/` - Previous configuration files
- `build-artifacts/` - Old build outputs
- `migration_scripts/` - Old database scripts
- Other archived items

**Note:** Keep for reference but do not use

---

## How to Use This Organization

### For Development
```bash
cd socrates
source .venv/bin/activate
# Edit files in socratic_system/, socrates-api/, socrates-frontend/, tests/
# Configuration in .env.local
```

### For Staging Deployment
```bash
# 1. Read documentation
cat docs/deployment/STAGING_SETUP.md

# 2. Copy environment
cp deployment/configurations/.env.local .env

# 3. Build container
docker build -f deployment/docker/Dockerfile -t socrates:staging .

# 4. Run with compose
docker-compose -f deployment/docker/docker-compose.yml up
```

### For Production Deployment
```bash
# 1. Read documentation
cat docs/deployment/DEPLOYMENT_CHECKLIST.md

# 2. Copy production config
cp deployment/configurations/.env.production.example .env.production

# 3. Review and customize
nano .env.production

# 4. Follow deployment checklist step-by-step
```

### For Testing
```bash
# GitHub integration testing
cat docs/deployment/GITHUB_TESTING_GUIDE.md

# Production readiness verification
cat docs/deployment/PRODUCTION_READINESS.md
```

---

## Quick Reference

### Essential Paths
```
Code:           socratic_system/, socrates-api/, socrates-frontend/
Tests:          tests/
Deployment:     deployment/
Documentation:  docs/deployment/
Config:         deployment/configurations/
```

### Important Files
```
Deployment Guide:        docs/deployment/DEPLOYMENT_CHECKLIST.md
Staging Setup:           docs/deployment/STAGING_SETUP.md
GitHub Testing:          docs/deployment/GITHUB_TESTING_GUIDE.md
Production Readiness:    docs/deployment/PRODUCTION_READINESS.md
```

### Docker Files
```
Container Build:         deployment/docker/Dockerfile
Hardened Build:          deployment/docker/Dockerfile.prod
Compose Setup:           deployment/docker/docker-compose.yml
Web Server:              deployment/docker/nginx.conf
```

### Environment Files
```
Development:             deployment/configurations/.env.local
Example (General):       deployment/configurations/.env.example
Example (Production):    deployment/configurations/.env.production.example
Service File:            deployment/configurations/socrates-api.service
```

---

## Before Deployment Checklist

- [ ] Reviewed `docs/deployment/DEPLOYMENT_CHECKLIST.md`
- [ ] Reviewed `docs/deployment/STAGING_SETUP.md`
- [ ] Reviewed `docs/deployment/PRODUCTION_READINESS.md`
- [ ] Copied environment files from `deployment/configurations/`
- [ ] Verified Docker files in `deployment/docker/`
- [ ] All code committed to version control
- [ ] Tests passing (180+ tests)
- [ ] Team approved deployment schedule

---

## File Statistics

| Category | Count | Size |
|----------|-------|------|
| Source Code Directories | 4 | ~200MB |
| Python Code Files | 50+ | ~4MB |
| Test Files | 20+ | ~1MB |
| Documentation Files | 7+ | ~150KB |
| Configuration Files | 6+ | ~50KB |
| CI/CD Workflows | 6 | ~50KB |
| **Total** | **80+** | **~200MB** |

---

## Storage Optimization

### Excluded from Version Control (.gitignore)
- `.venv/` - Virtual environment (recreated per machine)
- `node_modules/` - Dependencies (recreated per machine)
- `.idea/` - IDE configuration
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python
- `.env` - Local environment (not committed)
- `.env.local` - Local overrides

### Archive Contents (Can Delete)
- `archive/old-dockerfiles/` - 20KB
- `archive/build-artifacts/` - 500KB
- `archive/migration_scripts/` - 50KB

**Potential savings:** ~600KB (not significant)

---

## Maintenance Guidelines

### What to Keep
✅ Source code (always)
✅ Tests (always)
✅ Documentation (always)
✅ Deployment configuration (always)
✅ Git history (always)

### What to Clean Up
- Old deployment files (archive after use)
- Build artifacts (delete after release)
- Local environment files (not committed)
- Cache and temporary files (ignored)

### What to Archive
- Previous versions of Docker configs
- Old migration scripts
- Retired configuration files
- Build outputs from old releases

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-15 | Initial organization structure |

---

**Last Updated:** January 15, 2026
**Status:** ✅ Active
**Location:** Root directory
