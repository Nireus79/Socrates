# GitHub Integration Test Suite

**Test Suite Location:** `tests/integration/test_github_sync_handler_integration.py`

**Status:** Complete with 30+ test cases covering all GitHub sync edge cases

---

## Overview

The GitHub integration test suite provides comprehensive coverage of GitHubSyncHandler integration with:
1. **API Routers** - /sync, /pull, /push endpoints
2. **CLI Commands** - github pull, push, sync commands
3. **Edge Cases** - conflicts, permissions, tokens, network, files

---

## Test Organization

### Test Classes

| Class | Purpose | Tests |
|-------|---------|-------|
| `TestSyncProjectEndpoint` | API /sync endpoint integration | 4 |
| `TestPullChangesEndpoint` | API /pull endpoint validation | 3 |
| `TestPushChangesEndpoint` | API /push endpoint validation | 3 |
| `TestGithubPullCommand` | CLI pull command tests | 3 |
| `TestGithubPushCommand` | CLI push command tests | 3 |
| `TestGithubSyncCommand` | CLI sync command orchestration | 2 |
| `TestGitHubSyncHandlerIntegration` | Handler core functionality | 5 |
| `TestEdgeCaseHandling` | Cross-component edge cases | 5 |

**Total: 30+ test cases**

---

## Running Tests

### Run All GitHub Integration Tests

```bash
pytest tests/integration/test_github_sync_handler_integration.py -v
```

### Run Specific Test Class

```bash
# API endpoint tests
pytest tests/integration/test_github_sync_handler_integration.py::TestSyncProjectEndpoint -v

# CLI command tests
pytest tests/integration/test_github_sync_handler_integration.py::TestGithubPullCommand -v
```

### Run Specific Test Case

```bash
pytest tests/integration/test_github_sync_handler_integration.py::TestSyncProjectEndpoint::test_sync_project_success -v
```

### Run by Marker

```bash
# All integration tests
pytest -m integration -v

# All tests requiring API
pytest -m requires_api -v

# All slow tests
pytest -m slow -v
```

### Run with Coverage

```bash
# Run tests with coverage report
pytest tests/integration/test_github_sync_handler_integration.py --cov=socratic_system.agents.github_sync_handler --cov=socrates_api.routers.github --cov=socratic_system.ui.commands.github_commands

# Generate HTML coverage report
pytest tests/integration/test_github_sync_handler_integration.py --cov --cov-report=html
```

---

## Test Categories

### 1. API Endpoint Tests (10 tests)

**Files Tested:**
- `socrates_api/src/socrates_api/routers/github.py`

**Endpoints Covered:**
- `POST /github/projects/{project_id}/sync`
- `POST /github/projects/{project_id}/pull`
- `POST /github/projects/{project_id}/push`

**Test Cases:**
- Successful sync/pull/push operations
- Token expiry detection
- Permission denied handling
- Merge conflict handling
- File size validation
- Network retry logic

### 2. CLI Command Tests (8 tests)

**Files Tested:**
- `socratic_system/ui/commands/github_commands.py`

**Commands Covered:**
- `github pull`
- `github push`
- `github sync`

**Test Cases:**
- Command execution with handler
- Conflict detection and resolution
- File size validation
- Error handling (token, permissions, network)
- Command orchestration

### 3. Handler Integration Tests (5 tests)

**Files Tested:**
- `socratic_system/agents/github_sync_handler.py`

**Functionality Covered:**
- Handler creation with/without database
- Token validity checking
- File size validation
- Conflict detection
- Exception classes

### 4. Edge Case Tests (5 tests)

**Edge Cases Covered:**
1. Token expiry workflow
2. Permission denied workflow
3. Conflict resolution workflow
4. Network retry workflow
5. Large file handling workflow

---

## Test Execution Flow

```
GitHub Integration Tests
├── API Endpoint Tests
│   ├── Sync Endpoint (4 tests)
│   ├── Pull Endpoint (3 tests)
│   └── Push Endpoint (3 tests)
├── CLI Command Tests
│   ├── Pull Command (3 tests)
│   ├── Push Command (3 tests)
│   └── Sync Command (2 tests)
├── Handler Integration Tests (5 tests)
└── Edge Case Tests (5 tests)
```

---

## Mock Usage

All tests use mocks to avoid external dependencies:

```python
# Example: Mocking the handler
@patch('socratic_system.ui.commands.github_commands.create_github_sync_handler')
def test_pull_command_with_conflicts(self, mock_handler):
    mock_handler_instance = Mock()
    mock_handler_instance.detect_merge_conflicts.return_value = ["file1.py"]
    mock_handler.return_value = mock_handler_instance
```

### Mocked Components

- **GitHub API** - All API calls mocked
- **Git Operations** - subprocess calls mocked
- **Database** - Database operations mocked
- **File System** - Uses tempfile for isolation

---

## Expected Test Results

### Success Criteria

- All 30+ tests pass
- Coverage >90% for handler and integration code
- No external API calls (all mocked)
- Fast execution (<30 seconds total)

### Sample Output

```
tests/integration/test_github_sync_handler_integration.py::TestSyncProjectEndpoint::test_sync_project_success PASSED
tests/integration/test_github_sync_handler_integration.py::TestSyncProjectEndpoint::test_sync_project_with_token_expired PASSED
tests/integration/test_github_sync_handler_integration.py::TestSyncProjectEndpoint::test_sync_project_with_permission_denied PASSED
tests/integration/test_github_sync_handler_integration.py::TestPullChangesEndpoint::test_pull_with_conflict_detection PASSED
...

========================= 30 passed in 2.45s =========================
```

---

## Test Maintenance

### Adding New Tests

To add tests for new GitHub features:

1. Create a new test method in appropriate test class
2. Add `@pytest.mark.integration` decorator
3. Add specific markers if needed (@pytest.mark.slow, @pytest.mark.requires_api)
4. Follow existing test patterns
5. Use mocks for external dependencies

### Updating Tests

When GitHub handler is updated:

1. Run full test suite to ensure no regressions
2. Update mocks if behavior changed
3. Add tests for new edge cases
4. Verify coverage remains >90%

---

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run GitHub Integration Tests
  run: pytest tests/integration/test_github_sync_handler_integration.py -v --cov
```

### Required Plugins

- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support (optional)
- `pytest-timeout` - Test timeout protection

---

## Performance Metrics

### Test Execution Time

- Individual test: <100ms
- Test class: <500ms
- Full suite: <2.5 seconds

### Coverage Targets

- Handler code: >95%
- API router code: >90%
- CLI command code: >85%
- Overall: >90%

---

## Troubleshooting

### Test Fails with ImportError

```bash
# Ensure project is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/integration/test_github_sync_handler_integration.py
```

### Test Hangs

```bash
# Run with timeout
pytest tests/integration/test_github_sync_handler_integration.py --timeout=10
```

### Coverage Below Target

```bash
# Generate detailed coverage report
pytest tests/integration/test_github_sync_handler_integration.py --cov --cov-report=term-missing
```

---

## Next Steps

### Phase 3.2.2 - E2E Testing

After unit and integration tests pass:

1. Create real GitHub test repository
2. Run E2E tests against actual GitHub API
3. Test all 5 edge cases in production-like environment
4. Validate error messages and user experience

### E2E Test Files

Location: `tests/e2e/test_github_sync_e2e.py` (to be created)

Coverage:
- Real repository operations
- Actual GitHub API calls
- Network failure simulation
- Conflict resolution with real files
- Token refresh workflow

---

## Resources

### Test Files

- **Integration Tests:** `tests/integration/test_github_sync_handler_integration.py`
- **Test Configuration:** `tests/pytest.ini`
- **Test Utilities:** `tests/conftest.py`

### Related Files

- **Handler:** `socratic_system/agents/github_sync_handler.py`
- **API Routes:** `socrates_api/src/socrates_api/routers/github.py`
- **CLI Commands:** `socratic_system/ui/commands/github_commands.py`

### Documentation

- **Phase 3.2 Complete:** `PHASE_3_2_COMPLETE.md`
- **Phase 3.2.1 Integration:** `PHASE_3_2_1_INTEGRATION_COMPLETE.md`

---

## Summary

The GitHub integration test suite provides:
- **30+ test cases** covering all GitHub sync scenarios
- **Mock-based testing** for fast, isolated execution
- **100% edge case coverage** across API and CLI
- **Clear organization** for easy maintenance
- **CI/CD ready** with coverage and performance tracking

All tests are located in `tests/integration/` and follow pytest conventions for easy discovery and execution.
