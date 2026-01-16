# Dependencies Audit Report

Comprehensive analysis of all project dependencies across Socrates codebase.

**Date:** January 16, 2025
**Status:** ⚠️ Multiple issues found - requires fixes

---

## Summary

| Category | Status | Issues | Priority |
|----------|--------|--------|----------|
| Python Core | ⚠️ Mixed | Version mismatches between files | HIGH |
| Python Testing | ⚠️ Mixed | Inconsistent test version requirements | MEDIUM |
| Python API | ⚠️ Critical | Depends on non-published package | CRITICAL |
| Node.js Frontend | ⚠️ Caution | Pre-release packages in use | MEDIUM |
| Consistency | ❌ Failed | requirements.txt ≠ pyproject.toml | HIGH |

---

## 1. Python Core Dependencies Issues

### Issue 1.1: requirements.txt Missing Critical Packages ❌

**Problem:** `requirements.txt` is missing 4 important packages that are in `pyproject.toml`:

```
Missing from requirements.txt:
- gunicorn>=21.0.0
- psycopg2-binary>=2.9.0
- gitpython>=3.1.0
- cryptography>=41.0.0
```

**Impact:**
- Production Docker build uses `requirements.txt`
- Without these packages, API server cannot start properly
- Database connections will fail (missing psycopg2)
- Git operations will fail (missing gitpython)
- Security operations will fail (missing cryptography)

**Location:**
- Missing from: `requirements.txt` (lines 1-40)
- Present in: `pyproject.toml` (lines 87-89)

**Fix Required:** Add missing packages to requirements.txt:
```
gunicorn>=21.0.0
psycopg2-binary>=2.9.0
gitpython>=3.1.0
cryptography>=41.0.0
```

**Severity:** 🔴 CRITICAL - Production deployment will fail

---

### Issue 1.2: requirements.txt vs pyproject.toml Version Conflicts

**Problem:** Different minimum versions for overlapping packages:

| Package | requirements.txt | pyproject.toml | Conflict |
|---------|-----------------|-----------------|----------|
| aiosqlite | >= 0.19.0 | ❌ Missing | requirements.txt has package pyproject.toml lacks |
| python-jose | ❌ Missing | >= 3.3.0 (in req-test.txt) | pyproject.toml has, requirements.txt doesn't |

**Details:**
- `requirements.txt`: Has `aiosqlite>=0.19.0` (line 12)
- `pyproject.toml`: NO aiosqlite dependency listed
- `requirements.txt`: Has `python-jose>=3.3.0` in requirements-test.txt
- `pyproject.toml`: NO python-jose listed

**Impact:**
- Inconsistent installations depending on which requirements file is used
- Async support may not work properly

**Fix Required:** Align requirements.txt with pyproject.toml core dependencies

**Severity:** 🟠 HIGH - Can cause runtime failures

---

## 2. Python Testing Dependencies Issues

### Issue 2.1: Inconsistent Test Framework Versions ⚠️

**Problem:** Different pytest versions specified in different files:

| File | pytest | pytest-cov | pytest-asyncio |
|------|--------|-----------|-----------------|
| requirements-test.txt | >= 7.0.0 | >= 4.0.0 | >= 0.21.0 |
| pyproject.toml [dev] | >= 9.0.0 | >= 5.0.0 | >= 0.24.0 |

**Details:**
- `requirements-test.txt` line 5: `pytest>=7.0.0`
- `pyproject.toml` line 94: `pytest>=9.0.0` (major version difference)
- Similar conflicts in pytest-cov (4.0 vs 5.0)
- Similar conflicts in pytest-asyncio (0.21 vs 0.24)

**Impact:**
- Running `pip install -r requirements-test.txt` gets older versions
- Running `pip install .[dev]` gets newer versions
- Tests may behave differently depending on installation method

**Fix Required:** Choose one set of versions and update both files to match

**Recommendation:** Use pyproject.toml versions (newer) and update requirements-test.txt

**Severity:** 🟡 MEDIUM - Test inconsistency but doesn't break functionality

---

## 3. Python API Package Dependencies Issues

### Issue 3.1: socrates-api Depends on Non-Published Package ❌

**Problem:** `socrates-api/pyproject.toml` requires `socrates-ai>=1.2.0` as a dependency, but this package is NOT published to PyPI.

```toml
# socrates-api/pyproject.toml line 43
dependencies = [
    "socrates-ai>=1.2.0",  # ❌ This is not available on PyPI
    ...
]
```

**Current Situation:**
- `socrates-ai` (core package) is not published to PyPI
- The package is only available locally in the monorepo
- This breaks when trying to install `socrates-ai-api` from PyPI

**Impact:**
- ❌ Cannot install `socrates-ai-api` from PyPI (dependency resolution fails)
- ✓ Works locally because monorepo structure allows local imports
- ✓ Works in Docker because builds from source

**Related Issue:**
- `socrates-cli/pyproject.toml` has the same issue (line 43)

**Fix Options:**

**Option A: Publish socrates-ai to PyPI** (Recommended)
- Make `socrates-ai` a public package on PyPI
- Update version numbers across all packages
- Allows independent package installation

**Option B: Use relative path dependencies** (Current workaround)
- `socrates-api/pyproject.toml`: `"socrates-ai @ file://../"`
- Only works in monorepo structure

**Option C: Private package index**
- Publish to private PyPI or GitHub Packages
- Requires authentication for installation

**Severity:** 🔴 CRITICAL - Breaks external deployments

**Status:** This is intentional design (monorepo, not published) but should be documented

---

### Issue 3.2: socrates-cli Depends on Non-Published Package ❌

Same as Issue 3.1 - `socrates-cli/pyproject.toml` line 43 has the same dependency problem.

---

## 4. Node.js Frontend Dependencies Issues

### Issue 4.1: Pre-Release/Experimental Packages ⚠️

**Problem:** Frontend uses packages that are not stable releases:

```json
Dependencies with concerns:
- "@tailwindcss/postcss": "^4.1.18"  // Alpha/Beta version
```

**Details:**
- Tailwind CSS 4 is very new (2024-2025)
- May have breaking changes and stability issues
- Not recommended for production without thorough testing

**Impact:**
- Potential build issues
- Possible runtime styling issues
- Breaking changes in minor updates (SemVer ^4.1.18)

**Recommendation:**
- Test thoroughly before production deployment
- Consider pinning to exact version instead of `^` for stability
- Monitor Tailwind CSS releases for critical updates

**Severity:** 🟡 MEDIUM - Use with caution

---

### Issue 4.2: React 19 Very Recent Version ⚠️

**Problem:** Using React 19.2.0 (February 2025) in production is very recent:

```json
"react": "^19.2.0",
"react-dom": "^19.2.0"
```

**Details:**
- React 19 was released recently
- Third-party library compatibility may be incomplete
- Some ecosystem libraries may not support React 19 yet

**Impact:**
- May encounter library compatibility issues
- Less battle-tested in production environments
- Potential security issues undiscovered yet

**Recommendation:**
- Verify all major dependencies support React 19
- Extensive testing in staging environment
- Monitor for security updates closely
- Consider downgrading to React 18 LTS if stability is concern

**Severity:** 🟡 MEDIUM - Monitor closely in production

---

### Issue 4.3: Caret Dependencies Without Version Pinning ⚠️

**Problem:** Using caret (`^`) for versions allows breaking changes:

```json
// These allow breaking changes within the specified major version
"@monaco-editor/react": "^4.7.0",     // Allows 4.99.99
"@tanstack/react-query": "^5.90.12",  // Allows 5.99.99
"lucide-react": "^0.562.0",            // Allows 0.999.0
```

**Impact:**
- `npm install` on different dates gets different versions
- Different developers may have different behavior
- Unexpected breaking changes during `npm update`

**Recommendation for Production:**
- Use `package-lock.json` (already committed) ✓
- Consider switching to exact versions for critical dependencies
- Regular security updates via `npm audit fix`

**Severity:** 🟢 LOW - Mitigated by package-lock.json

---

## 5. Consistency Issues

### Issue 5.1: requirements.txt vs pyproject.toml Mismatch

**Problem:** Two conflicting sources of truth for Python dependencies:

**requirements.txt** (Production focus):
- 40 dependencies
- No testing packages
- Missing: gunicorn, psycopg2, gitpython, cryptography

**pyproject.toml** (Comprehensive):
- Core: 25 dependencies
- Dev: 7 dependencies
- Docs: 3 dependencies
- Total with optionals: ~35 dependencies

**Current Situation:**
```
Docker build uses: requirements.txt ❌ (missing critical packages)
Local dev uses: pyproject.toml ✓ (complete)
Testing uses: requirements-test.txt ⚠️ (older versions)
```

**Impact:**
- Development environment ≠ Production environment
- Can cause "works on my machine" issues
- Difficult to maintain consistency

**Recommendation:**
- Make `pyproject.toml` the single source of truth
- Remove `requirements.txt` and use `pip install .` in Docker
- Use `requirements.txt` only as generated from `pip freeze` for reproducibility

**Severity:** 🔴 CRITICAL - DevOps issue

---

## 6. Version Compatibility Matrix

### Python Version Support
```
requirements.txt:           No explicit requirement
pyproject.toml (core):      requires-python = ">=3.8"
pyproject.toml (api):       requires-python = ">=3.8"
pyproject.toml (cli):       requires-python = ">=3.8"
Docker (Dockerfile):        python:3.11-slim ✓ Compatible
```

**Status:** ✓ Aligned (Python 3.8+, using 3.11 in Docker)

### Node.js Version Support
```
package.json:   "node": ">=18.0.0"
Docker:         node:20-alpine ✓ Compatible
```

**Status:** ✓ Aligned (Node 18+, using 20 in Docker)

---

## 7. Summary Table: All Dependencies

### Working ✓
- Python 3.8+ requirement
- Node.js 18+ requirement
- Core package versions mostly reasonable
- FastAPI, pydantic, sqlalchemy versions reasonable
- Docker base images versions reasonable

### Needs Attention ⚠️
- Test framework version inconsistencies
- Pre-release packages (Tailwind, React 19)
- Caret version specifications without pinning

### Needs Fixing 🔴
- Missing packages in requirements.txt
- Non-published package dependencies
- Inconsistent version sources
- requirements.txt vs pyproject.toml conflict

---

## Recommended Action Plan

### Priority 1: CRITICAL (Fix Immediately)
1. **Add missing packages to requirements.txt**
   - Add: gunicorn, psycopg2-binary, gitpython, cryptography
   - Verify it matches pyproject.toml core dependencies

2. **Document local package dependencies**
   - Document that socrates-ai, socrates-api, socrates-cli are interdependent
   - Explain monorepo structure for users

### Priority 2: HIGH (Fix Soon)
3. **Standardize on single dependency source**
   - Make pyproject.toml the authoritative source
   - Update Docker to use `pip install .` instead of requirements.txt
   - Update CI/CD to use pyproject.toml

4. **Harmonize test dependencies**
   - Choose between requirements-test.txt or pyproject.toml [dev]
   - Update both files to use same versions

### Priority 3: MEDIUM (Fix When Convenient)
5. **Review pre-release packages**
   - Test React 19 thoroughly
   - Evaluate Tailwind CSS 4 stability
   - Consider version pinning for stability

6. **Improve version pinning strategy**
   - Document policy for caret vs exact versions
   - Consider pinning critical dependencies
   - Use package-lock.json (already in place) ✓

---

## Verification Checklist

- [ ] requirements.txt includes all packages from pyproject.toml
- [ ] Test versions consistent across requirements-test.txt and pyproject.toml
- [ ] All dependencies installable from PyPI (or documented as local-only)
- [ ] Docker build succeeds with updated requirements.txt
- [ ] Local dev environment works with `pip install .[dev]`
- [ ] Tests pass with all dependency combinations
- [ ] No version conflicts reported by `pip check`

---

## Files to Update

1. **C:\Users\themi\PycharmProjects\Socrates\requirements.txt**
   - Add missing packages

2. **C:\Users\themi\PycharmProjects\Socrates\requirements-test.txt**
   - Update to match pyproject.toml versions OR
   - Delete and use `pip install .[dev]`

3. **Documentation**
   - Add note about monorepo structure
   - Document local package dependencies
   - Add dependency management guide

---

## Testing the Fixes

```bash
# After applying fixes, run:

# Verify no conflicts
pip check

# Rebuild Docker
docker-compose build api

# Install locally
pip install -e .[dev]

# Run tests
pytest

# Verify versions
pip list
```

---

**Status:** Ready for fixes
**Owner:** Development team
**Review Date:** Before next release
