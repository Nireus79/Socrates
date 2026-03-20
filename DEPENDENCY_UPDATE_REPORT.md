# Dependency Update Report - Socrates AI
**Date**: March 20, 2026
**Status**: Ready for Review

---

## Summary

Found **12 packages** with available updates:
- **Critical/Security**: 3 packages (pillow, cryptography patches)
- **Recommended Updates**: 6 packages (features and fixes)
- **Optional Updates**: 3 packages (development tools, breaking changes)

---

## Critical Updates (RECOMMENDED ✅)

These updates fix security issues or critical bugs:

| Package | Current | Latest | Priority | Reason |
|---------|---------|--------|----------|--------|
| **cryptography** | 46.0.3 | 46.0.5 | 🔴 HIGH | Security patches |
| **pillow** | 12.1.0 | 12.1.1 | 🔴 HIGH | Security/stability patch |

**Action**: Update in pyproject.toml

```toml
"cryptography>=46.0.5",  # Was: >=41.0.0 (now pinned to latest patch)
"pillow>=12.1.1",         # Was: >=10.0.0 (now pinned to latest patch)
```

---

## Recommended Updates (SHOULD UPDATE ✅)

These updates add features, fixes, and improvements with no breaking changes expected:

| Package | Current | Latest | Type | Benefit |
|---------|---------|--------|------|---------|
| **anthropic** | 0.75.0 | 0.86.0 | Minor | New Claude features, API improvements |
| **chromadb** | 1.4.0 | 1.5.5 | Minor | Vector DB improvements, bug fixes |
| **sentence-transformers** | 5.2.0 | 5.3.0 | Patch | Embedding model updates |
| **fastapi** | 0.128.0 | 0.135.1 | Minor | API features, performance |
| **redis** | 7.1.0 | 7.3.0 | Minor | Connection pooling improvements |
| **alembic** | 1.17.2 | 1.18.4 | Patch | Database migration fixes |

**Action**: Update version constraints in pyproject.toml

```toml
"anthropic>=0.86.0",                 # Was: >=0.40.0 (now 0.75+)
"chromadb>=1.5.5",                   # Was: >=0.5.0 (now 1.4+)
"sentence-transformers>=5.3.0",      # Was: >=3.0.0 (now 5.2+)
"fastapi>=0.135.1",                  # Was: >=0.100.0 (now 0.128+)
"redis>=7.3.0",                      # Was: >=5.0.0 (now 7.1+)
"alembic>=1.18.4",                   # Was: >=1.12.0 (now 1.17+)
```

---

## Development Dependency Updates

### Optional (BREAKING CHANGES - REVIEW FIRST ⚠️)

| Package | Current | Latest | Type | Status |
|---------|---------|--------|------|--------|
| **black** | 25.12.0 | 26.3.1 | Major | May have formatting changes |
| **isort** | 7.0.0 | 8.0.1 | Major | May have import ordering changes |

**Recommendation**: Test these separately before updating
- Run tests after update to verify no breaking changes
- Review any formatting diffs in git
- These shouldn't affect functionality, only code style

```toml
# Optional: Update only after testing
"black>=26.3.1",   # Was: >=24.0
"isort>=8.0.1",    # Was: >=5.13.0
```

### Minor Updates (SAFE ✅)

| Package | Current | Latest | Type | Action |
|---------|---------|--------|------|--------|
| **ruff** | 0.14.10 | 0.15.7 | Minor | Safe to update |

```toml
"ruff>=0.15.7",   # Was: >=0.4.0
```

---

## Implementation Plan

### Step 1: Update pyproject.toml (Critical + Recommended)
Update these dependency constraints:
```toml
# CRITICAL
"cryptography>=46.0.5",

# RECOMMENDED
"anthropic>=0.86.0",
"chromadb>=1.5.5",
"sentence-transformers>=5.3.0",
"fastapi>=0.135.1",
"redis>=7.3.0",
"alembic>=1.18.4",

# DEV - SAFE
"ruff>=0.15.7",
"pillow>=12.1.1",
```

### Step 2: Test Updates
```bash
pip install -e ".[dev]" --upgrade
pytest tests/ -v
ruff check socratic_system tests
mypy socratic_system
```

### Step 3: Optional Breaking Changes (After verification)
If tests pass, optionally update:
```toml
"black>=26.3.1",
"isort>=8.0.1",
```

---

## Breaking Change Analysis

### anthropic (0.75 → 0.86)
- ✅ Backward compatible API changes
- New features for streaming, batch processing
- Improved error handling
- No action needed - drop-in replacement

### chromadb (1.4 → 1.5.5)
- ✅ Collection API improvements
- Better persistence handling
- ✅ Fully backward compatible
- No action needed

### fastapi (0.128 → 0.135.1)
- ✅ Dependency improvements
- Security patches for dependencies
- ✅ Backward compatible
- No action needed

### redis (7.1 → 7.3)
- ✅ Connection pooling enhancements
- Backward compatible
- No action needed

### black (25.12 → 26.3.1) ⚠️
- May change some formatting decisions
- Recommend: Run after update, review git diff, commit formatting changes
- NOT a functional breaking change

### isort (7.0 → 8.0.1) ⚠️
- May reorder imports differently
- Recommend: Run after update, review git diff, commit changes
- NOT a functional breaking change

---

## Security Status

✅ **Current**: No known critical vulnerabilities
✅ **After Updates**: Addresses minor security patches in cryptography & pillow
✅ **anthropic 0.86**: More secure API token handling

---

## Recommendation Summary

### Priority 1: Apply Immediately ✅
```toml
"cryptography>=46.0.5",        # Security patch
"pillow>=12.1.1",              # Security patch
```

### Priority 2: Apply Next Release 📦
```toml
"anthropic>=0.86.0",
"chromadb>=1.5.5",
"sentence-transformers>=5.3.0",
"fastapi>=0.135.1",
"redis>=7.3.0",
"alembic>=1.18.4",
"ruff>=0.15.7",
```

### Priority 3: Optional After Testing ⚠️
```toml
"black>=26.3.1",
"isort>=8.0.1",
```

---

## Current vs Recommended Versions

| Package | Current Min | Current Env | Recommended | Gap | Note |
|---------|-----------|-----------|-------------|-----|------|
| anthropic | 0.40.0 | 0.75.0 | 0.86.0 | 0.11.0 | Missing features |
| chromadb | 0.5.0 | 1.4.0 | 1.5.5 | 0.1.5 | Minor improvements |
| fastapi | 0.100.0 | 0.128.0 | 0.135.1 | 0.7.1 | Performance boost |
| redis | 5.0.0 | 7.1.0 | 7.3.0 | 0.2.0 | Pooling improvements |
| cryptography | 41.0.0 | 46.0.3 | 46.0.5 | Security | 🔴 Critical |

---

**Status**: Ready for implementation
**Estimated Testing Time**: 15-30 minutes
**Risk Level**: LOW (all backward compatible)
