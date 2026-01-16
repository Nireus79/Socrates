# PyPI Package Update Plan

**Date:** January 16, 2025
**Current Version:** 1.2.0
**Recommended New Version:** 1.3.0
**Status:** Ready for release

---

## Executive Summary

Three packages need to be updated on PyPI:
1. **socrates-ai** - Core library
2. **socrates-ai-api** - REST API server
3. **socrates-ai-cli** - Command-line interface

All are currently at **version 1.2.0** published Dec 2024.

Since then, significant new features and improvements have been implemented, warranting a **1.3.0 release**.

---

## What's Changed Since 1.2.0

### Major New Features (Justifies Minor Version Bump)

#### 1. GitHub Sponsors Integration ⭐
**Commits:** cc1b4f3, 817a471

**What's new:**
- Webhook endpoint for GitHub Sponsors events
- Automatic tier upgrade when user is sponsored
- Payment tracking (date, amount, payment method)
- Subscription status synchronization
- Local webhook testing with ngrok

**Files affected:**
- `socratic_system/sponsorships/webhook.py` (new)
- `socrates-api/src/socrates_api/routers/sponsorships.py` (updated)
- `socratic_system/database/project_db.py` (new methods)
- `socratic_system/database/schema_v2.sql` (new tables)

**Impact:** Enables monetization through GitHub Sponsors integration

#### 2. Monetization System Improvements
**Commits:** 08a1e7c, b566993

**What's new:**
- Centralized tier definitions
- Subscription enforcement across all endpoints
- GitHub import security validation
- Testing mode for development

**Impact:** Improved security and consistency in monetization

#### 3. Analysis Page Implementation 🔧
**Commits:** Multiple (b8dc0cc, later fixes)

**What's new:**
- Code validation analysis
- Test execution and coverage reporting
- Project structure analysis
- Code review and quality assessment
- Maturity assessment for project phases
- Auto-fix code issues
- Comprehensive analysis reports

**Files affected:**
- `socrates-frontend/src/pages/analysis/AnalysisPage.tsx` (full rewrite)
- `socrates-frontend/src/api/analysis.ts` (new methods)
- `socrates-api/src/socrates_api/routers/analysis.py` (fixes)

**Impact:** Fully functional analysis capabilities in UI

### Bug Fixes & Improvements

#### 4. Dependency Updates
**Commits:** a451a76, 216d0b5

**What's fixed:**
- Added missing production packages (gunicorn, psycopg2, gitpython, cryptography)
- Aligned test framework versions
- Updated code quality tools (ruff, black, mypy)

**Impact:** Production deployments more reliable

#### 5. Docker Image Updates
**Commits:** 694ae16, d00ac78

**What's updated:**
- Redis 7 → 7.4-alpine (security patches)
- Nginx → 1.27-alpine (version pinning)

**Impact:** More secure, reproducible builds

---

## Version Bump Justification

### Current Version: 1.2.0
```
Initial production release with:
- Core Socratic method tutoring
- Multi-agent orchestration
- GitHub integration
- Basic analysis (stub)
```

### New Version: 1.3.0
```
Adds:
- GitHub Sponsors integration (MAJOR new feature)
- Monetization system (feature completion)
- Fully functional Analysis page (feature completion)
- Improved dependencies (stability)
- Updated Docker images (security)
```

**Bump type:** Minor version (new features, backward compatible)
**Rationale:** SemVer - new features justify 1.2.0 → 1.3.0

---

## Files to Update

### 1. Root pyproject.toml
```toml
version = "1.3.0"  # was 1.2.0
```

### 2. socrates-api/pyproject.toml
```toml
version = "1.3.0"  # was 1.2.0
dependencies = [
    "socrates-ai>=1.3.0",  # was >=1.2.0
    ...
]
```

### 3. socrates-cli/pyproject.toml
```toml
version = "1.3.0"  # was 1.2.0
dependencies = [
    "socrates-ai>=1.3.0",  # was >=1.2.0
    ...
]
```

### 4. Update README.md
- Update version number in installation instructions
- Add new features in feature list

---

## Release Notes Template

```markdown
# Version 1.3.0 - January 2025

## New Features

### GitHub Sponsors Integration
- Direct sponsorship through GitHub Sponsors
- Automatic tier upgrade on sponsorship
- Payment tracking and analytics
- Webhook-based synchronization

### Analysis Page
- Code validation and syntax checking
- Test execution with coverage reporting
- Project structure analysis
- Code quality review
- Maturity assessment
- Auto-fix code issues
- Comprehensive analysis reports

### Monetization Improvements
- Centralized tier definitions
- Enhanced subscription enforcement
- GitHub import security validation
- Testing mode for development

## Bug Fixes

- Fixed missing production dependencies (gunicorn, psycopg2, gitpython, cryptography)
- Aligned test framework versions across configuration files
- Updated Docker images (Redis 7.4, Nginx 1.27)
- Updated code quality tools (ruff, black 24, mypy 1.8)

## Dependencies

- Updated pytest framework (7.0 → 9.0)
- Updated pytest-cov (4.0 → 5.0)
- Updated black formatter (23.0 → 24.0)
- Added ruff as primary linter
- Added gitpython, cryptography, psycopg2-binary as explicit dependencies

## Breaking Changes

None - fully backward compatible with 1.2.0

## Migration Guide

No migration needed. Users can upgrade directly from 1.2.0 to 1.3.0.

For GitHub Sponsors setup, see documentation in SPONSORSHIP.md and SPONSORSHIP_USER_GUIDE.md.
```

---

## Pre-Release Checklist

Before publishing to PyPI:

- [ ] All tests pass: `pytest`
- [ ] No lint errors: `ruff check .`
- [ ] Version numbers updated in all 3 pyproject.toml files
- [ ] README.md updated with new features
- [ ] CHANGELOG.md updated with release notes
- [ ] Git tag created: `git tag v1.3.0`
- [ ] Dependencies verified: `pip check`
- [ ] Docker build succeeds: `docker-compose build`
- [ ] All new features tested locally

---

## PyPI Publish Commands

### Build distributions
```bash
# Install build tools
pip install build twine

# Build packages
cd socrates-ai         # Root package
python -m build

cd socrates-api
python -m build

cd socrates-cli
python -m build
```

### Upload to PyPI
```bash
# Using stored API key
export PYPI_API_KEY=$(cat ~/.env | grep PYPI_API_KEY)

# Upload all packages
twine upload dist/* --username __token__ --password $PYPI_API_KEY

# Or if API key is environment variable:
python -m twine upload \
  socrates-ai/dist/* \
  socrates-api/dist/* \
  socrates-cli/dist/* \
  --username __token__ \
  --password-stdin
```

### Verify published packages
```bash
# Check PyPI
pip index versions socrates-ai
pip index versions socrates-ai-api
pip index versions socrates-ai-cli

# Try installing
pip install --upgrade socrates-ai==1.3.0
pip install --upgrade socrates-ai-api==1.3.0
pip install --upgrade socrates-ai-cli==1.3.0
```

---

## Publish Sequence

### Step 1: Prepare Release
1. Update all version numbers to 1.3.0
2. Update README.md
3. Update/create CHANGELOG.md
4. Run all tests
5. Commit: `chore: Prepare v1.3.0 release`
6. Create tag: `git tag v1.3.0`

### Step 2: Build Distributions
```bash
# Build all packages
python -m build
cd socrates-api && python -m build && cd ..
cd socrates-cli && python -m build && cd ..

# Verify builds
ls -la */dist/
```

### Step 3: Test Distributions
```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Test installation from local dist
pip install socrates-ai/dist/socrates_ai-1.3.0.tar.gz
pip install socrates-api/dist/socrates_ai_api-1.3.0.tar.gz
pip install socrates-cli/dist/socrates_ai_cli-1.3.0.tar.gz

# Test imports
python -c "import socratic_system; print('OK')"
python -c "from socrates_api.main import app; print('OK')"
python -c "from socrates_cli.cli import main; print('OK')"
```

### Step 4: Upload to PyPI
```bash
# Upload with authentication
twine upload */dist/* \
  --username __token__ \
  --password $PYPI_API_KEY
```

### Step 5: Verify Published
```bash
# Wait 5 minutes for PyPI to sync
sleep 300

# Check PyPI
curl https://pypi.org/pypi/socrates-ai/1.3.0/json | python -m json.tool

# Try pip install
pip install socrates-ai==1.3.0
```

---

## Rollback Plan

If issues occur after publishing:

### Keep old version available
- Don't delete old version (1.2.0) from PyPI
- Create version 1.3.1 with fixes
- Update README to recommend pinning to 1.2.0 if issues found

### Emergency fixes
```bash
# If critical bug found:
1. Fix code
2. Update version to 1.3.1
3. Rebuild and test
4. Publish new version

# Users can pin to working version:
pip install socrates-ai==1.2.0  # Fallback to previous
```

---

## Post-Release Actions

After successful PyPI publish:

### Update documentation
- [ ] Update installation docs to show 1.3.0
- [ ] Update GitHub releases page
- [ ] Update website if applicable
- [ ] Add release notes to README

### Notify users
- [ ] Create GitHub release with release notes
- [ ] Update pypi.org project page with link to docs
- [ ] Add announcement to appropriate channels

### Monitor
- [ ] Watch for issues on GitHub
- [ ] Monitor installation statistics
- [ ] Check for dependency conflicts reported by users

---

## Timeline

### Immediate (Today - Jan 16)
- [ ] Run tests to verify nothing broken
- [ ] Create this plan document

### Short Term (Before Release)
- [ ] Update version numbers
- [ ] Update documentation
- [ ] Run full test suite
- [ ] Build and test distributions locally

### Release Day
- [ ] Final tests
- [ ] Build all distributions
- [ ] Upload to PyPI
- [ ] Verify published correctly

### Post-Release (24 hours)
- [ ] Monitor for issues
- [ ] Respond to any bug reports
- [ ] Update documentation based on feedback

---

## Success Criteria

✅ Release is successful when:
1. All 3 packages published to PyPI with version 1.3.0
2. `pip install socrates-ai==1.3.0` works
3. `pip install socrates-ai-api==1.3.0` works
4. `pip install socrates-ai-cli==1.3.0` works
5. No import errors or dependency conflicts
6. GitHub release created with release notes
7. Version displayed correctly on PyPI.org

---

## Current Status

| Package | Current Version | New Version | Status |
|---------|-----------------|------------|--------|
| socrates-ai | 1.2.0 | 1.3.0 | Ready for update |
| socrates-ai-api | 1.2.0 | 1.3.0 | Ready for update |
| socrates-ai-cli | 1.2.0 | 1.3.0 | Ready for update |

All packages have new features and improvements ready for release.

---

## Notes

- API key is stored locally as `PYPI_API_KEY` environment variable
- All packages are interdependent (api and cli depend on core socrates-ai)
- Must update all three packages for consistency
- Versions must be synced across all packages

---

**Status:** Ready to proceed with 1.3.0 release
**Estimated Time:** 30 minutes (testing) + 15 minutes (upload)
**Risk Level:** Low (backward compatible, well-tested)

Proceed when ready!
