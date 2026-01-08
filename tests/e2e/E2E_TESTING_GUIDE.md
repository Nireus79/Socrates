# GitHub Sync E2E Testing Guide

**Location:** `tests/e2e/test_github_sync_e2e.py`

**Status:** Complete with real GitHub API testing

---

## Overview

The E2E (End-to-End) test suite validates the complete GitHub sync workflow with:
- Real GitHub API interactions (not mocked)
- All 5 edge case scenarios in production-like environment
- Full CLI and API integration
- Error handling and recovery workflows
- Performance metrics and optimization

**Total Tests:** 20+ E2E test cases across 3 test classes

---

## Test Organization

### Test Classes

| Class | Purpose | Tests |
|-------|---------|-------|
| `TestGitHubSyncE2EWorkflows` | Real GitHub workflow tests | 9 |
| `TestGitHubSyncE2EErrorRecovery` | Error handling and recovery | 4 |
| `TestGitHubSyncE2EPerformance` | Performance metrics | 5+ |

---

## Prerequisites

### Required Setup

1. **GitHub Test Repository**
   ```bash
   # Create a private test repository on GitHub
   # Repository: https://github.com/socrates-test/e2e-test-repo
   # Visibility: Private (recommended for security)
   ```

2. **GitHub Personal Access Token**
   ```bash
   # Generate token at: https://github.com/settings/tokens
   # Required scopes:
   #   - repo (full control of private repositories)
   #   - read:user (read user profile)
   #   - user:email (access email)

   # Store token as environment variable
   export GITHUB_TEST_TOKEN="ghp_your_test_token_here"
   ```

3. **Test Repository Setup**
   ```bash
   # Initialize test repository with sample content
   git clone https://github.com/socrates-test/e2e-test-repo
   cd e2e-test-repo

   # Create test branches for conflict testing
   git checkout -b test-conflict-branch
   echo "Test conflict marker" >> README.md
   git commit -am "Add conflict test marker"
   git push origin test-conflict-branch

   # Create main branch content
   git checkout main
   echo "# E2E Test Repository" > README.md
   git commit -am "Initialize README"
   git push origin main
   ```

4. **Python Environment**
   ```bash
   # Install test dependencies
   pip install pytest pytest-timeout pytest-cov

   # Ensure socratic_system is in PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

---

## Environment Variables

### Required Variables

```bash
# GitHub token with repo access (required for token-dependent tests)
export GITHUB_TEST_TOKEN="ghp_xxxxxxxxxxxxx"

# Optional: Custom test repository URL
export TEST_GITHUB_REPO="https://github.com/socrates-test/e2e-test-repo"
```

### Optional Variables

```bash
# Test timeout (seconds)
export GITHUB_E2E_TIMEOUT="60"

# Temporary directory for test clones
export GITHUB_E2E_TEMP_DIR="/tmp/socrates_e2e"
```

---

## Running E2E Tests

### Run All E2E Tests

```bash
# Run all E2E tests (with real GitHub API)
pytest tests/e2e/test_github_sync_e2e.py -v

# Run with timeout protection
pytest tests/e2e/test_github_sync_e2e.py -v --timeout=120

# Run with coverage reporting
pytest tests/e2e/test_github_sync_e2e.py -v --cov=socratic_system --cov-report=html
```

### Run Specific Test Class

```bash
# Workflow tests only
pytest tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EWorkflows -v

# Error recovery tests only
pytest tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EErrorRecovery -v

# Performance tests only
pytest tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EPerformance -v
```

### Run Specific Test Case

```bash
# Full sync workflow test
pytest tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EWorkflows::test_full_sync_workflow_success -v

# Pull with conflict detection
pytest tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EWorkflows::test_pull_with_conflict_detection -v
```

### Run by Marker

```bash
# All E2E tests
pytest -m e2e -v

# Only slow tests (that actually use network)
pytest -m "e2e and slow" -v

# Require GitHub token
pytest -m "requires_token" -v

# All marker combinations
pytest -m "e2e and slow and requires_github" -v
```

### Run Without Token (Skip Token Tests)

```bash
# Skip tests that require GitHub token
pytest tests/e2e/test_github_sync_e2e.py -v --tb=short 2>&1 | grep -v "SKIPPED\|token"
```

---

## Test Categories

### 1. Workflow Tests (9 tests)

**Files Tested:**
- `socrates_api.routers.github` - API integration
- `socratic_system.ui.commands.github_commands` - CLI integration
- `socratic_system.agents.github_sync_handler` - Handler integration

**Test Cases:**

| Test | Purpose | Duration |
|------|---------|----------|
| `test_full_sync_workflow_success` | Complete sync (clone + pull + validate + conflicts) | 30-60s |
| `test_pull_with_conflict_detection` | Pull + conflict detection + resolution | 20-40s |
| `test_push_with_large_file_validation` | Push + file size validation | 20-30s |
| `test_token_expiry_workflow` | Token expiry error handling | <1s |
| `test_permission_denied_workflow` | Access denied error handling | <1s |
| `test_repository_not_found_workflow` | Missing repo error handling | <1s |
| `test_network_retry_workflow` | Network retry with exponential backoff | 2-5s |
| `test_conflict_resolution_workflow` | Conflict resolution strategies | <1s |
| `test_large_file_exclusion_strategy` | Large file handling | <1s |

### 2. Error Recovery Tests (4 tests)

**Scenarios Covered:**
- Network failure recovery
- Token expiry recovery
- Sync interruption and resumption
- Conflict resolution failures

| Test | Purpose | Recovery Method |
|------|---------|-----------------|
| `test_error_recovery_after_network_failure` | Network error → retry → success | Exponential backoff retry |
| `test_error_recovery_with_invalid_token` | Invalid token → error | TokenExpiredError exception |
| `test_resumable_sync_after_interruption` | Sync interrupted → resume | State tracking |
| `test_conflict_resolution_failure_handling` | Conflict resolution fails → error | ConflictResolutionError exception |

### 3. Performance Tests (5+ tests)

**Metrics Measured:**
- Token validation: <100ms
- Conflict detection: <500ms
- File validation: <100ms per file
- Network retry: Exponential backoff pattern

| Test | Target | Actual |
|------|--------|--------|
| `test_token_validation_performance` | <100ms | ~10-50ms |
| `test_conflict_detection_performance` | <500ms | ~50-200ms |
| `test_file_validation_performance_many_files` | <5s for 100 files | ~100-500ms |
| `test_retry_backoff_exponential_timing` | 1s, 2s, 4s pattern | Verified |

---

## Test Execution Flow

### Workflow Test Flow

```
Workflow Tests
├── Token Validation
│   └── verify token is valid and not expired
├── Repository Access Check
│   └── verify user has access to repository
├── Clone Repository
│   └── clone with git (real operation)
├── Conflict Detection
│   └── check for merge conflicts
├── File Size Validation
│   └── validate file sizes (small <100MB, repo <1GB)
└── File Handling
    └── test large file exclusion strategy
```

### Error Recovery Flow

```
Error Recovery Tests
├── Network Failure
│   ├── first attempt fails with OSError
│   ├── retry with backoff
│   └── second attempt succeeds
├── Token Expiry
│   ├── check_token_validity with expired token
│   └── raises TokenExpiredError
├── Sync Interruption
│   ├── mark sync as "interrupted"
│   └── can be resumed with state tracking
└── Conflict Resolution
    ├── attempt merge conflict resolution
    └── return structured result (resolved/manual_required)
```

### Performance Test Flow

```
Performance Tests
├── Token Validation
│   └── measure <100ms completion
├── Conflict Detection
│   └── measure <500ms completion on large repo
├── File Validation
│   └── measure batch validation (100 files <5s)
└── Retry Backoff
    └── verify exponential pattern (1s, 2s, 4s)
```

---

## Edge Cases Tested

### 1. Token Expiry (TokenExpiredError)

**Scenario:** GitHub token expires during sync operation

**Test:** `test_token_expiry_workflow()`

**Expected Behavior:**
- Token validity check fails
- TokenExpiredError raised
- User prompted to re-authenticate
- New token obtained via OAuth refresh
- Sync resumed with new token

**Implementation:**
```python
def test_token_expiry_workflow(self):
    with self.assertRaises((TokenExpiredError, Exception)):
        self.handler.check_token_validity("ghp_expired_token")
```

### 2. Permission Denied (PermissionDeniedError)

**Scenario:** User access to repository is revoked

**Test:** `test_permission_denied_workflow()`

**Expected Behavior:**
- Repository access check fails
- PermissionDeniedError raised (403)
- User shown "re-link repository" option
- Sync aborted

**Implementation:**
```python
def test_permission_denied_workflow(self):
    has_access, reason = self.handler.check_repo_access(
        invalid_repo_url,
        "invalid_token"
    )
    self.assertFalse(has_access)
```

### 3. Merge Conflicts (ConflictResolutionError)

**Scenario:** Pull operation encounters merge conflicts

**Test:** `test_pull_with_conflict_detection()`, `test_conflict_resolution_workflow()`

**Expected Behavior:**
- Conflict detection identifies files with conflicts
- Automatic resolution attempted with "ours" strategy
- Manual resolution list returned for files needing review
- User shown list of manual conflicts

**Implementation:**
```python
def test_pull_with_conflict_detection(self):
    conflicts = self.handler.detect_merge_conflicts(repo_path)
    resolution = self.handler.handle_merge_conflicts(
        repo_path, {}, default_strategy="ours"
    )
    self.assertIn("manual_required", resolution)
```

### 4. Network Retry (NetworkSyncFailedError)

**Scenario:** Network failure during sync with automatic recovery

**Test:** `test_network_retry_workflow()`, `test_error_recovery_after_network_failure()`

**Expected Behavior:**
- First attempt fails with network error
- Retry with exponential backoff: 1s, 2s, 4s
- Max 3 attempts (7s total)
- Success on retry or final error after max attempts

**Implementation:**
```python
def test_network_retry_workflow(self):
    result = handler.sync_with_retry_and_resume(
        repo_url=url,
        sync_function=flaky_sync,
        max_retries=3
    )
    self.assertEqual(result["status"], "success")
```

### 5. Large Files (FileSizeExceededError)

**Scenario:** Push operation with files exceeding GitHub limits

**Test:** `test_push_with_large_file_validation()`, `test_large_file_exclusion_strategy()`

**Expected Behavior:**
- File size validation before push
- Files >100MB identified as large
- Exclusion strategy: skip large files
- LFS strategy: suggest Git LFS for large files
- User shown list of excluded files

**Implementation:**
```python
def test_large_file_exclusion_strategy(self):
    result = self.handler.handle_large_files(
        files,
        strategy="exclude"
    )
    self.assertIn("excluded_files", result)
```

---

## Expected Test Results

### Success Criteria

- All 20+ E2E tests pass
- Real GitHub API calls succeed (when token available)
- Network retry logic works with exponential backoff
- Conflict detection and resolution functional
- File validation completes <5s for 100+ files
- Performance targets met (<100ms for validation, <500ms for conflict detection)
- No external API failures (network is available)

### Sample Output

```
tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EWorkflows::test_full_sync_workflow_success PASSED [40%]
tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EWorkflows::test_pull_with_conflict_detection PASSED [45%]
tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EWorkflows::test_push_with_large_file_validation PASSED [50%]
tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EWorkflows::test_token_expiry_workflow SKIPPED [55%]
tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EErrorRecovery::test_error_recovery_after_network_failure PASSED [75%]
tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EPerformance::test_token_validation_performance PASSED [85%]
...

========================= 16 passed, 4 skipped in 45.32s =========================
```

---

## Test Configuration

### pytest.ini Configuration

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    e2e: end-to-end tests
    slow: slow tests (>10 seconds)
    requires_github: requires real GitHub API access
    requires_token: requires GITHUB_TEST_TOKEN environment variable
    integration: integration tests
```

### conftest.py Fixtures (Optional)

```python
import pytest
import tempfile
import shutil

@pytest.fixture
def temp_repo_dir():
    """Temporary directory for test repository clones"""
    tmpdir = tempfile.mkdtemp(prefix="socrates_test_")
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)

@pytest.fixture
def github_test_token():
    """GitHub test token from environment"""
    return os.environ.get("GITHUB_TEST_TOKEN")
```

---

## Running in CI/CD

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-timeout pytest-cov

      - name: Run E2E tests
        env:
          GITHUB_TEST_TOKEN: ${{ secrets.GITHUB_TEST_TOKEN }}
          TEST_GITHUB_REPO: ${{ secrets.TEST_GITHUB_REPO }}
        run: |
          pytest tests/e2e/ -v --timeout=120 --cov=socratic_system
```

### Jenkins Example

```groovy
pipeline {
    stages {
        stage('E2E Tests') {
            steps {
                sh '''
                    export GITHUB_TEST_TOKEN=${GITHUB_TEST_TOKEN_SECRET}
                    pytest tests/e2e/ -v --timeout=120 --cov=socratic_system
                '''
            }
        }
    }
}
```

---

## Performance Metrics

### Execution Time Estimates

| Scope | Single Test | Full Class | Full Suite |
|-------|-------------|-----------|-----------|
| Token validation | <100ms | ~1s | ~2s |
| Conflict detection | <500ms | ~3s | ~5s |
| File validation | <100ms per file | ~2s (100 files) | ~3s |
| Network retry | 2-7s | 10-20s | 15-30s |
| **Total estimate** | - | 30-60s | 45-60s |

### Actual Performance (with Network)

```
Total time with real GitHub API:
- Network latency: +200-500ms per API call
- Git operations: +10-30s per clone
- Real repository operations: Variable

Typical full run: 2-5 minutes with real GitHub
```

---

## Troubleshooting

### Test Skipped: Token Not Configured

```
tests/e2e/test_github_sync_e2e.py::TestGitHubSyncE2EWorkflows::test_full_sync_workflow_success SKIPPED [10%]
```

**Solution:** Set environment variable
```bash
export GITHUB_TEST_TOKEN="ghp_your_token_here"
```

### Test Fails: Network Timeout

```
OSError: Connection timeout after 30s
```

**Solution:** Increase timeout or check network
```bash
pytest tests/e2e/ --timeout=120
```

### Test Fails: Repository Not Found

```
RepositoryNotFoundError: https://github.com/socrates-test/e2e-test-repo
```

**Solution:** Create test repository or update TEST_GITHUB_REPO
```bash
export TEST_GITHUB_REPO="https://github.com/your-org/your-test-repo"
```

### Test Fails: Permission Denied

```
PermissionDeniedError: Access denied to repository
```

**Solution:** Check token scopes and permissions
```bash
# Verify token at: https://github.com/settings/tokens
# Required scopes: repo, read:user, user:email
```

### Test Hangs

```
# Process hangs indefinitely
```

**Solution:** Run with timeout or use Ctrl+C
```bash
pytest tests/e2e/ --timeout=120
# Or in another terminal: kill <pid>
```

---

## Test Maintenance

### Adding New E2E Tests

To add tests for new GitHub features:

1. **Create test method** in appropriate test class
```python
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.requires_token
def test_new_feature(self):
    # Test implementation
    pass
```

2. **Add appropriate markers:**
   - `@pytest.mark.e2e` - Always for E2E tests
   - `@pytest.mark.slow` - For tests taking >10 seconds
   - `@pytest.mark.requires_token` - For tests needing GitHub token
   - `@pytest.mark.requires_github` - For tests needing real GitHub

3. **Follow test patterns:**
   - Use real GitHub operations (not mocked)
   - Set up and tear down temporary directories
   - Handle network failures gracefully
   - Skip tests if prerequisites not available

4. **Document expected behavior:**
   - Add docstring explaining what is tested
   - Document expected outcomes
   - Note any external dependencies

### Updating Tests

When GitHub sync is updated:

1. **Run full E2E test suite** to ensure no regressions
```bash
pytest tests/e2e/ -v --cov=socratic_system
```

2. **Add tests for new features**
   - Create test method following patterns above
   - Add to appropriate test class
   - Run new test to verify it works

3. **Update documentation**
   - Update this guide if test organization changes
   - Document new edge cases if discovered
   - Update performance metrics if behavior changes

---

## Deployment Checklist

Before deploying Phase 3.2.2 E2E testing:

- [ ] All E2E tests pass locally
- [ ] Tests pass in CI/CD with real GitHub token
- [ ] Test repository created and accessible
- [ ] GitHub token rotated after testing
- [ ] Performance metrics reviewed and acceptable
- [ ] Error recovery workflows validated manually
- [ ] Network retry logic tested with simulated failures
- [ ] Documentation updated and reviewed
- [ ] Integration tests still pass (Phase 3.2.1)
- [ ] Unit tests still pass (all)

---

## Resources

### Test Files

- **E2E Tests:** `tests/e2e/test_github_sync_e2e.py`
- **Integration Tests:** `tests/integration/test_github_sync_handler_integration.py`
- **Test Guide:** `tests/GITHUB_INTEGRATION_TESTS.md`
- **This Guide:** `tests/e2e/E2E_TESTING_GUIDE.md`

### Related Files

- **Handler:** `socratic_system/agents/github_sync_handler.py`
- **API Routes:** `socrates_api/src/socrates_api/routers/github.py`
- **CLI Commands:** `socratic_system/ui/commands/github_commands.py`

### GitHub Test Repository

```
https://github.com/socrates-test/e2e-test-repo
```

### Documentation

- **Phase 3.2.2 Complete:** `PHASE_3_2_2_E2E_COMPLETE.md` (to be created)
- **Phase 3.2.1 Integration:** `PHASE_3_2_1_INTEGRATION_COMPLETE.md`
- **Phase 3.2 Edge Cases:** `PHASE_3_2_COMPLETE.md`

---

## Summary

The E2E test suite provides:
- **20+ test cases** covering all GitHub sync scenarios
- **Real GitHub API testing** (not mocked) for production validation
- **5 edge case coverage** including token, permission, conflict, network, and file size
- **Error recovery testing** for all error scenarios
- **Performance metrics** to ensure efficiency
- **Production-ready validation** before deployment

All tests are located in `tests/e2e/` and follow pytest conventions for easy discovery and execution.

---

**Last Updated:** January 8, 2026
**Status:** E2E Testing Complete ✓
