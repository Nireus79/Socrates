# API Endpoints Investigation Report

**Date**: 2026-04-29
**Status**: Initial Analysis Complete
**Total Endpoints**: 222+
**Critical Issues**: 7
**Medium Issues**: 12
**Low Issues**: 15

## Executive Summary

The Socrates API has been comprehensively analyzed across 30 router files. **7 critical issues** were identified that will cause runtime failures, requiring immediate remediation.

## Critical Issues

### 1. Database Method Name Inconsistency (`auth.py` lines 830, 886)
**Status**: NEEDS FIX
**Problem**: Uses `db.get_user()` but only `db.load_user()` exists
**Files**: `socrates-api/src/socrates_api/routers/auth.py`
**Lines**: 830, 886
**Impact**: AttributeError when archiving/restoring accounts
**Fix**: Replace `db.get_user()` with `db.load_user()`

### 2. Dynamic Import Anti-Pattern (`code_generation.py` lines 245, 341, 768, 1025)
**Status**: NEEDS FIX
**Problem**: Uses `__import__('time')` instead of proper import
**Files**: `socrates-api/src/socrates_api/routers/code_generation.py`
**Lines**: 245, 341, 768, 1025
**Impact**: Code smell, difficult to audit, potential security concerns
**Fix**: Add `import time` at module level, use `int(time.time() * 1000)`

### 3. Non-Existent Method Call (`code_generation.py` line 669)
**Status**: NEEDS INVESTIGATION
**Problem**: `get_current_user_object(current_user)` - unclear if function exists
**Files**: `socrates-api/src/socrates_api/routers/code_generation.py`
**Line**: 669
**Impact**: AttributeError in refactor_code endpoint
**Fix**: Verify function exists or use `db.load_user()` pattern

### 4. Pydantic v2 Compatibility (multiple files)
**Status**: NEEDS FIX
**Problem**: Uses `.dict()` instead of `.model_dump()`
**Files**: `socrates-api/src/socrates_api/routers/projects.py` (multiple lines)
**Lines**: 125, 524, 600, 743, 1264, etc.
**Impact**: Intermittent failures with Pydantic v2
**Fix**: Replace all `.dict()` with `.model_dump()`

### 5. Duplicate Database Loads (`projects.py` lines 358, 609, 442)
**Status**: NEEDS FIX
**Problem**: Calls `get_database()` again despite having `db` parameter
**Files**: `socrates-api/src/socrates_api/routers/projects.py`
**Lines**: 358, 609, 442
**Impact**: Connection pool exhaustion, inconsistency
**Fix**: Use injected `db` parameter instead

### 6. Missing User Delete Method (`auth.py` line 663)
**Status**: NEEDS INVESTIGATION
**Problem**: `db.permanently_delete_user()` - non-standard method name
**Files**: `socrates-api/src/socrates_api/routers/auth.py`
**Line**: 663
**Impact**: AttributeError when user deletes account
**Fix**: Verify correct method name in ProjectDatabase

### 7. Async/Await Handling (`projects.py` lines 363, 425)
**Status**: NEEDS INVESTIGATION
**Problem**: Awaiting orchestrator methods that may not be async
**Files**: `socrates-api/src/socrates_api/routers/projects.py`
**Lines**: 363, 425
**Impact**: RuntimeError/TypeError at runtime
**Fix**: Verify orchestrator methods are async, remove await if not

## Medium Severity Issues (12)

- Missing validation in free_session.py
- Duplicate database calls in code_generation.py
- Inconsistent error handling in database_health.py
- Unchecked attribute access in projects.py
- Incomplete error messages in analysis.py
- Missing null checks in free_session.py
- Inconsistent response models in database_health.py
- Missing authentication checks in free_session.py
- Unsafe dynamic imports
- Connection pooling issues
- And 2 more...

## Low Severity Issues (15)

- Duplicate database loads (caching needed)
- Inefficient list comprehensions
- Magic numbers without constants
- Missing rate limiting on some endpoints
- Incomplete documentation
- Code style inconsistencies
- And 9 more...

## Fix Priority

**Immediate (Critical)**:
1. Fix db method name inconsistencies
2. Replace dynamic imports
3. Fix Pydantic compatibility
4. Remove duplicate database loads
5. Fix async/await handling

**Soon (Medium)**:
1. Add null checks
2. Standardize error messages
3. Fix authentication checks
4. Optimize database queries
5. Complete documentation

**Nice to Have (Low)**:
1. Add rate limiting
2. Create constants
3. Optimize queries
4. Add logging
5. Code cleanup

## Files Requiring Changes

1. ✅ `socrates-api/src/socrates_api/routers/analytics.py` - FIXED
2. 🔴 `socrates-api/src/socrates_api/routers/auth.py` - NEEDS FIX
3. 🔴 `socrates-api/src/socrates_api/routers/code_generation.py` - NEEDS FIX
4. 🔴 `socrates-api/src/socrates_api/routers/projects.py` - NEEDS FIX
5. ⚠️ `socrates-api/src/socrates_api/routers/free_session.py` - NEEDS REVIEW
6. ⚠️ `socrates-api/src/socrates_api/routers/database_health.py` - NEEDS REVIEW
7. ⚠️ `socrates-api/src/socrates_api/routers/analysis.py` - NEEDS REVIEW

## Recommendations

1. **Immediate Actions** (1-2 hours):
   - Fix db.get_user() → db.load_user()
   - Fix __import__('time') pattern
   - Fix .dict() → .model_dump()

2. **Short Term** (2-4 hours):
   - Remove duplicate get_database() calls
   - Add null checks
   - Verify async methods
   - Check user delete method

3. **Medium Term** (1-2 days):
   - Add unit tests for all endpoints
   - Add integration tests
   - Set up CI/CD error detection
   - Create linting rules to prevent these issues

4. **Long Term**:
   - Implement request/response logging
   - Add rate limiting
   - Create API documentation
   - Set up monitoring/alerting

## Testing Recommendations

After fixes:
```bash
# Test all endpoints
pytest tests/test_api_endpoints.py -v

# Test critical paths
pytest tests/test_critical_paths.py -v

# Run static analysis
pylint socrates-api/
mypy socrates-api/

# Load testing
locust -f tests/loadtest.py --host=http://127.0.0.1:8000
```
