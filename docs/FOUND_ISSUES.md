# Project Issues Found During Audit and Testing

## Summary
During comprehensive end-to-end testing and project reorganization, the following issues were identified and need to be addressed.

---

## CRITICAL ISSUES (Must Fix)

### 1. Backend Database Test Failures
**Location:** `tests/backend/test_comprehensive_system.py`
**Status:** 8 failing tests out of 47
**Severity:** CRITICAL

#### Failed Tests:
1. `test_delete_project` - Assertion expects True, got None
2. `test_permanently_delete_user` - Assertion expects True, got None
3. `test_create_and_retrieve_project` - Project owner field mismatch (expects 'owner_user', got 'Test Project')
4. `test_save_project` - Assertion expects True, got ProjectContext object
5. `test_create_and_retrieve_user` - UserNotFoundError: User not found after creation
6. `test_get_user_projects` - Returns 0 projects, expects minimum 2
7. `test_load_nonexistent_user` - Not handling expected exception properly
8. `test_load_nonexistent_project` - Not handling expected exception properly

#### Root Causes:
- Tests may not be properly initializing test databases
- Database methods returning unexpected types (None vs True/object)
- User/project creation not persisting to database
- Exception handling tests not properly mocking exceptions

#### Impact:
- Backend database operations cannot be reliably tested
- Cannot verify CRUD operations work correctly
- Risk of undetected database bugs in production

---

### 2. Deprecated datetime.utcnow() Usage
**Location:** `backend/src/socrates_api/database.py` (lines 315, 403, 680)
**Status:** 11 warnings during test run
**Severity:** HIGH

#### Issue:
```python
now = datetime.utcnow().isoformat()  # DEPRECATED
```

#### Solution:
```python
from datetime import datetime, timezone
now = datetime.now(timezone.utc).isoformat()
```

#### Impact:
- Code will break in future Python versions (3.13+)
- DeprecationWarnings fill up logs
- Not using timezone-aware datetime objects

#### Files to Fix:
- `backend/src/socrates_api/database.py` - Multiple occurrences
- Any other files using `datetime.utcnow()`

---

## HIGH PRIORITY ISSUES

### 3. test_api_quick_check.py Not Running Properly
**Location:** `tests/e2e/test_api_quick_check.py`
**Status:** Tests don't appear in test output
**Severity:** HIGH

#### Issue:
- Renamed from `quick_test.py` to `test_api_quick_check.py`
- May have import issues or setup problems
- Not being discovered/run by pytest

#### Action:
- Review the file for import and setup issues
- Ensure it follows pytest conventions
- Add proper conftest fixtures if needed

---

### 4. Test Skips in test_orchestrator_basic.py
**Location:** `tests/unit/orchestration/test_orchestrator_basic.py`
**Status:** 26 tests skipped
**Severity:** HIGH

#### Issue:
- Large number of tests are being skipped (marked with `s` in test output)
- Reasons for skipping not visible in quick output
- May indicate missing dependencies or fixtures

#### Investigation Needed:
- Why are these tests skipped?
- Are dependencies missing?
- Should they be enabled?

---

## MEDIUM PRIORITY ISSUES

### 5. Database Operations Return Type Issues
**Location:** `tests/backend/test_comprehensive_system.py` and related database code
**Status:** Test assertions failing
**Severity:** MEDIUM

#### Issue:
- `delete_project()` returning None instead of True/False
- `save_project()` returning object instead of boolean
- Tests expect boolean returns, code returns different types

#### Solution:
- Standardize return types for all database operations
- Update tests to expect correct return types
- Document expected return types in code comments

---

### 6. User Creation/Retrieval Issues
**Location:** Database tests
**Status:** Users created but not retrievable
**Severity:** MEDIUM

#### Issue:
- `test_create_and_retrieve_user` fails with UserNotFoundError
- Suggests user creation not persisting
- May be database initialization or transaction issue

#### Likely Causes:
- Database not being committed after insert
- Test isolation issues (one test's cleanup affecting another)
- Database fixture not properly set up

---

## LOW PRIORITY ISSUES

### 7. Frontend Test Organization Incomplete
**Location:** `socrates-frontend/src/__tests__/`
**Status:** Tests moved but e2e directory not created
**Severity:** LOW

#### Issue:
- Not all frontend tests have been moved to __tests__/
- E2E directory structure might not be complete
- Some tests might still be in old locations

#### Solution:
- Complete the e2e test directory structure
- Verify all tests are in appropriate subdirectories
- Remove any duplicate test locations

---

### 8. Test Data Inconsistency
**Location:** Phase 3 tests vs unit tests
**Status:** Similar test files with different implementations
**Severity:** LOW

#### Issue:
- `test_phase3_2_agents.py` and `test_phase3_2_agents_backup.py` seem to test same functionality
- Unclear which is the "correct" version
- Maintenance burden if both need updates

#### Solution:
- Determine which version is authoritative
- Merge if both are needed
- Delete the other version

---

## RECOMMENDATION ROADMAP

### Phase 1: Fix Critical Issues (Do First)
1. Fix deprecated datetime.utcnow() → datetime.now(timezone.utc)
2. Debug and fix database CRUD test failures
3. Investigate and fix test_orchestrator skips
4. Review test_api_quick_check.py for issues

**Estimated Time:** 2-3 hours
**Priority:** Must complete before any production work

### Phase 2: Fix High Priority Issues
1. Fix user creation/retrieval database issue
2. Standardize database return types
3. Complete frontend test organization

**Estimated Time:** 1-2 hours
**Priority:** Complete before next major feature work

### Phase 3: Clean Up Low Priority Issues
1. Remove duplicate test files
2. Verify all tests are in correct locations
3. Document test dependencies and requirements

**Estimated Time:** 30 minutes
**Priority:** Nice to have, do when convenient

---

## TEST STATISTICS

- **Total Unit Tests:** 618 collected
- **Backend Tests:** 47 (8 failing, 11 warnings)
- **Frontend Tests:** 11 consolidated
- **Tests Skipped:** 26+ (mainly orchestrator tests)
- **Critical Failures:** 8
- **Deprecation Warnings:** 11+

---

## NEXT STEPS

1. **Immediately:** Fix deprecated datetime calls
2. **Today:** Debug database test failures and fix root causes
3. **This Week:** Get all tests passing green
4. **Then:** Document test best practices for contributors

---

## Questions to Investigate

1. Why does user creation not persist to database in tests?
2. Why are 26 orchestrator tests skipped?
3. What is the purpose of test_phase3_2_agents_backup.py vs test_phase3_2_agents.py?
4. Why do database operations return mixed types (None, bool, object)?
5. Are frontend tests actually running in the test suite?
6. What test framework/tools are expected for frontend tests?

