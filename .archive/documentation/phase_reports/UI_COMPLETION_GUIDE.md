# Phase 2 & 3 Completion Guide

## Status Summary

**Phase 2:** ✅ COMPLETE (January 6, 2026)
- Phase 2.1: ✅ Wrapped 70 orchestrator calls with `safe_orchestrator_call()`
- Phase 2.2: ✅ Fixed 10 chat session edge cases
- Phase 2.3: ✅ Completed doc import validation
- Phase 2.4: ✅ Comprehensive error handling integrated

**Phase 3:** 🔄 PENDING (Starting January 8, 2026)
- Phase 3.1: Frontend API consistency improvements
- Phase 3.2: GitHub sync edge case handling
- Phase 3.3: Test coverage expansion to 70%+

---

## Phase 2.1: Wrapping 65 Orchestrator Calls

### Pattern (standardized across all files)

**BEFORE:**
```python
result = orchestrator.process_request("agent_name", {"action": "do_something"})
```

**AFTER:**
```python
result = safe_orchestrator_call(
    orchestrator,
    "agent_name",
    {"action": "do_something"},
    operation_name="descriptive operation name"
)
```

### Files & Call Counts

| File | Count | Priority | Example Line |
|------|-------|----------|--------------|
| `llm_commands.py` | 8 | HIGH (AI responses) | Line 90 |
| `project_commands.py` | 10 | HIGH (core features) | Line 45 |
| `session_commands.py` | 9 | HIGH (session stability) | Line 192 |
| `collab_commands.py` | 8 | MEDIUM | Line 44 |
| `finalize_commands.py` | 4 | MEDIUM | Line 37 |
| `user_commands.py` | 4 | MEDIUM | Line 182 |
| `code_commands.py` | 4 | MEDIUM | Line 35 |
| `maturity_commands.py` | 3 | MEDIUM | Line 60 |
| `note_commands.py` | 4 | MEDIUM | Line 72 |
| `stats_commands.py` | 3 | LOW | Line 32 |
| `conv_commands.py` | 2 | LOW | Line 40 |
| `system_commands.py` | 2 | LOW | Line 116 |
| `github_commands.py` | 1 | LOW | Line 40 |
| **Agents** | 5 | HIGH | See next section |
| **TOTAL** | **65** | | |

### Agent Files (5 calls)

- `socratic_system/agents/project_manager.py` Line 275
- `socratic_system/agents/socratic_counselor.py` Lines 658, 698, 739, 1010

### Automated Wrapping Script

```python
#!/usr/bin/env python3
# apply_orchestrator_validation.py
# Usage: python apply_orchestrator_validation.py <file.py>

import re
import sys
from pathlib import Path

def add_import(content):
    """Add safe_orchestrator_call import if not present"""
    if 'safe_orchestrator_call' in content:
        return content

    # Add after other imports from socratic_system
    import_line = 'from socratic_system.utils.orchestrator_helper import safe_orchestrator_call\n'

    lines = content.split('\n')
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('from socratic_system'):
            insert_idx = i + 1

    lines.insert(insert_idx, import_line)
    return '\n'.join(lines)

def wrap_orchestrator_calls(content):
    """Replace orchestrator.process_request with safe_orchestrator_call"""
    # Pattern: result = orchestrator.process_request("agent", {...})
    pattern = r'(.*?)\s*=\s*orchestrator\.process_request\(\s*"([^"]+)",\s*(\{[^}]+\})\s*\)'

    def replacer(match):
        indent = match.group(1)
        agent = match.group(2)
        request_data = match.group(3)

        # Generate operation name from agent
        op_name = agent.replace('_', ' ')

        return f"""{indent} = safe_orchestrator_call(
{indent}    orchestrator,
{indent}    "{agent}",
{indent}    {request_data},
{indent}    operation_name="{op_name} operation"
{indent})"""

    return re.sub(pattern, replacer, content)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python apply_orchestrator_validation.py <file.py>")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    content = filepath.read_text()

    content = add_import(content)
    content = wrap_orchestrator_calls(content)

    filepath.write_text(content)
    print(f"✓ Updated {filepath}")
```

---

## Phase 2.2: Chat Session Edge Cases

### Edge Cases to Handle

1. **Session Timeout** (Lines 148-200 in session_commands.py)
   - Add idle timeout (default 30 min)
   - Save session state before timeout
   - Prompt user to resume or restart

2. **Mode Switching Validation** (Line 192)
   - Validate no processing in progress before switch
   - Save current mode state
   - Preserve conversation history

3. **Phase Advancement Prerequisites** (Line 192-193)
   - Check current phase completion status
   - Validate at least one question answered in phase
   - Log phase transitions

4. **Concurrent Session Access**
   - Add file locking for session save
   - Detect multi-instance access
   - Prevent race conditions

5. **Session Recovery** (New feature)
   - Store session_id in database
   - Allow resume interrupted sessions
   - Show last 5 questions on resume

### Implementation Pattern

```python
# Add session validation helper
def _validate_session_state(self, session_id, project):
    """Validate session can proceed safely"""
    # Check session exists
    # Check no timeout
    # Check project exists and is active
    # Return validation result or raise exception
```

---

## Phase 2.3: Documentation Import Validation

### Wrap 3 Unwrapped Calls

- `doc_commands.py` Line 113: `_import_file()`
- `doc_commands.py` Line 208: `_import_directory()`
- `doc_commands.py` Line 472: `_import_from_url()`

### Add Validation

```python
def _validate_import_file(self, filepath):
    """Validate file before import"""
    # Check file exists
    # Check not duplicate import
    # Check file not empty
    # Check not binary format
    # Check file size reasonable

def _validate_import_url(self, url):
    """Validate URL before import"""
    # Check URL format valid
    # Check URL reachable (with timeout)
    # Check response is text
    # Check content length reasonable
```

---

## Phase 2.4: Error Handling Improvements

### Priority Fixes

1. **Wrap all 65 orchestrator calls** (Phase 2.1) - This gives automatic error handling

2. **Session save error handling** (Lines 289-293)
   ```python
   try:
       result = safe_orchestrator_call(...)
       # Process response
       db.save_project(project)  # Could fail
   except ValueError as e:
       logger.error(f"Orchestrator error: {e}")
       raise
   except Exception as e:
       logger.error(f"Save error: {e}")
       # Rollback response processing
       raise
   ```

3. **Agent orchestrator calls** (5 calls in agents/)
   - Apply same safe_orchestrator_call wrapper
   - Add null checks for expected fields
   - Log missing fields as warnings

---

## Phase 3.1: Frontend API Consistency

### Problem Statement

The REST API endpoints in `socrates-api/src/socrates_api/routers/` return responses in **2 different formats**, causing client inconsistency:

**Format 1 (With "data" wrapper):** `/progress`, `/subscription/*`, `/projects/{id}`
```json
{
  "status": "success",
  "data": {
    "project_id": "...",
    "phase": "analysis"
  }
}
```

**Format 2 (Direct response):** `/code/generate`, `/phase`, `/chat`
```json
{
  "status": "success",
  "project_id": "...",
  "phase": "analysis"
}
```

### Detailed Tasks

#### 3.1.1: Audit All API Endpoints (~1 hour)
**File:** `socrates-api/src/socrates_api/routers/*.py`

Create a mapping of all endpoints:
```
GET  /projects                     -> Format ?
GET  /projects/{id}                -> Format ?
POST /projects                     -> Format ?
GET  /projects/{id}/progress       -> Format ?
POST /projects/{id}/code/generate  -> Format ?
...etc
```

**Location:** Create file `API_ENDPOINT_AUDIT.md` documenting current state

#### 3.1.2: Standardize Response Format (~1.5 hours)
**File:** `socrates-api/src/socrates_api/models.py`

Update response model:
```python
class APIResponse(BaseModel):
    """Standardized API response wrapper"""
    status: Literal["success", "error"]
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    timestamp: Optional[datetime] = None
```

Update all routers to use this model consistently.

**Files to update:**
- `socrates-api/src/socrates_api/routers/projects.py` (10 endpoints)
- `socrates-api/src/socrates_api/routers/code.py` (5 endpoints)
- `socrates-api/src/socrates_api/routers/chat.py` (4 endpoints)
- `socrates-api/src/socrates_api/routers/knowledge.py` (8 endpoints)
- `socrates-api/src/socrates_api/routers/collaboration.py` (3 endpoints)
- `socrates-api/src/socrates_api/routers/subscription.py` (4 endpoints)
- `socrates-api/src/socrates_api/routers/analytics.py` (6 endpoints)
- Plus any other routers

#### 3.1.3: Update Client-Side Code (~1 hour)
**Files:** All frontend/CLI code consuming the API

Update to handle consistent response format:
```python
response = safe_orchestrator_call(...)
if response["status"] == "success":
    data = response.get("data", {})  # Always present now
    project_id = data.get("project_id")
```

Remove all format-checking logic that tries to handle both formats.

### Testing Requirements
- Unit test: Verify each endpoint returns standardized format
- Integration test: Client correctly parses all endpoint responses
- Regression test: Ensure backward compatibility if needed

---

## Phase 3.2: GitHub Sync Edge Case Handling

### Problem Statement

GitHub sync operations in `socratic_system/agents/github_sync.py` and `socrates-api/src/socrates_api/routers/github_commands.py` don't handle edge cases that occur in production:

### 5 Critical Edge Cases to Implement

#### 3.2.1: Conflict Resolution (~1 hour)
**Scenario:** Multiple collaborators push simultaneously, creating merge conflicts

**Implementation:**
```python
def _handle_merge_conflict(self, repo_path, conflict_info):
    """Handle and resolve merge conflicts"""
    # 1. Detect conflict markers in files
    # 2. Log conflict details to database
    # 3. Notify all collaborators
    # 4. Provide options:
    #    - Accept ours (local)
    #    - Accept theirs (remote)
    #    - Manual merge (user decides)
    # 5. Complete merge with selected strategy
    # 6. Notify of resolution
```

**Location:** `socratic_system/agents/github_sync.py:250`

**Test case:** Create 2 simultaneous pushes to same file, verify conflict resolution

#### 3.2.2: Large File Handling (~45 minutes)
**Scenario:** Generated code or artifacts exceed GitHub's 100MB limit

**Implementation:**
```python
def _validate_file_size_before_push(self, files_to_push):
    """Check file sizes before pushing"""
    max_file_size = 100 * 1024 * 1024  # 100MB
    max_repo_size = 1 * 1024 * 1024 * 1024  # 1GB

    for file_path in files_to_push:
        size = os.path.getsize(file_path)
        if size > max_file_size:
            logger.warning(f"File {file_path} exceeds limit")
            # Option 1: Exclude from sync
            # Option 2: Use Git LFS
            # Option 3: Split into chunks
```

**Location:** `socratic_system/agents/github_sync.py:180`

**Test case:** Try to push 150MB file, verify graceful handling

#### 3.2.3: Authentication Token Expiry (~1 hour)
**Scenario:** GitHub authentication token expires during a long-running sync operation

**Implementation:**
```python
def _check_auth_token_validity(self, token):
    """Verify token hasn't expired"""
    from datetime import datetime, timedelta

    # Check token expiration (if using OAuth with expiry)
    if hasattr(self, 'token_expiry'):
        if datetime.now() > self.token_expiry:
            raise TokenExpiredError("GitHub token expired")

    # Verify token still works
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"},
            timeout=5
        )
        if response.status_code == 401:
            raise TokenExpiredError("Token no longer valid")
    except requests.RequestException as e:
        raise AuthenticationError(f"Token verification failed: {e}")

def _sync_with_token_refresh(self, repo_url):
    """Sync with automatic token refresh on expiry"""
    try:
        return self._perform_sync(repo_url)
    except TokenExpiredError:
        logger.warning("Token expired, attempting refresh")
        # Trigger refresh process
        new_token = self._refresh_github_token()
        # Retry sync with new token
        return self._perform_sync(repo_url)
```

**Location:** `socratic_system/agents/github_sync.py:150`

**Test case:** Simulate expired token during sync, verify refresh and retry

#### 3.2.4: Network Interruption Recovery (~1 hour)
**Scenario:** Network connection drops mid-push (e.g., user's internet fails)

**Implementation:**
```python
def _sync_with_retry_and_resume(self, repo_url, max_retries=3, timeout_per_attempt=30):
    """Sync with exponential backoff and progress tracking"""
    for attempt in range(max_retries):
        try:
            # Track progress in database
            sync_record = {
                'repo_url': repo_url,
                'attempt': attempt + 1,
                'started_at': datetime.now(),
                'status': 'in_progress'
            }
            db.save_sync_progress(sync_record)

            # Attempt sync with timeout
            result = timeout_call(
                self._perform_sync,
                args=(repo_url,),
                timeout_seconds=timeout_per_attempt
            )

            sync_record['status'] = 'success'
            db.save_sync_progress(sync_record)
            return result

        except (NetworkError, TimeoutError) as e:
            sync_record['status'] = 'failed'
            sync_record['error'] = str(e)
            db.save_sync_progress(sync_record)

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.info(f"Network error, retrying in {wait_time}s (attempt {attempt+2}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise NetworkSyncFailed(f"Sync failed after {max_retries} attempts: {e}")
```

**Location:** `socratic_system/agents/github_sync.py:100`

**Test case:** Simulate network timeout, verify retry and recovery

#### 3.2.5: Permission Errors & Access Revocation (~45 minutes)
**Scenario:** User's repo access is revoked (removed from collaborators, repo deleted, etc.)

**Implementation:**
```python
def _check_repo_access(self, repo_url, token):
    """Verify user still has access to repository"""
    try:
        response = requests.get(
            f"{repo_url}/collaborators",
            headers={"Authorization": f"token {token}"},
            timeout=5
        )
        if response.status_code == 403:
            raise PermissionDenied("No access to repository")
        elif response.status_code == 404:
            raise RepositoryNotFound("Repository no longer exists")
        return True
    except requests.RequestException as e:
        raise AuthenticationError(f"Failed to verify access: {e}")

def _sync_with_permission_check(self, repo_url, token):
    """Sync with pre-sync permission verification"""
    try:
        # Check access before attempting sync
        self._check_repo_access(repo_url, token)

        # Proceed with sync
        return self._perform_sync(repo_url)

    except PermissionDenied as e:
        logger.error(f"Permission denied for {repo_url}: {e}")
        # Notify user, suggest re-authentication
        db.log_sync_error(repo_url, "permission_denied", str(e))
        raise
    except RepositoryNotFound as e:
        logger.error(f"Repository not found: {e}")
        # Mark project as needing re-link
        db.mark_github_sync_broken(repo_url)
        raise
```

**Location:** `socratic_system/agents/github_sync.py:130`

**Test case:** Revoke token access, verify graceful error and user notification

### Summary Table

| Edge Case | Priority | Complexity | Estimated Time | Impact |
|-----------|----------|------------|-----------------|--------|
| Conflict resolution | HIGH | Medium | 1 hour | Prevents data loss |
| Large file handling | MEDIUM | Low | 45 min | Prevents sync failure |
| Token expiry | HIGH | Medium | 1 hour | Maintains session |
| Network interruption | HIGH | High | 1 hour | Ensures reliability |
| Permission errors | HIGH | Low | 45 min | Improves UX |

---

## Phase 3.3: Test Coverage Expansion to 70%+

### Current Coverage Status

**Current:** ~45-50% overall coverage
**Target:** 70%+ with focus on critical paths
**Gap:** ~20-25% additional coverage needed

### Coverage Breakdown by Module

#### 3.3.1: Orchestrator & Agent Testing (~8 hours)

**File:** `socratic_system/agents/*.py`

What to test:
```python
# Test each agent's main methods
- project_manager.py: validate_project, save_project, load_project
- socratic_counselor.py: generate_question, track_effectiveness, update_phase
- code_generator.py: generate_code, generate_documentation, validate_syntax
- document_processor.py: process_file, process_directory, extract_text
- conflict_detector.py: detect_conflicts, suggest_resolutions
```

**Pattern to implement:**
```python
def test_project_manager_validates_before_save():
    """Test that project manager validates before saving"""
    mock_db = MockDatabase()
    manager = ProjectManager(mock_db)

    # Test invalid project
    invalid_project = create_test_project(name="")
    with pytest.raises(ValidationError):
        manager.save_project(invalid_project)

    # Test valid project
    valid_project = create_test_project(name="Test Project")
    result = manager.save_project(valid_project)
    assert result["status"] == "success"
    assert mock_db.saved_projects[-1].name == "Test Project"
```

**Test files to create/expand:**
- `tests/unit/agents/test_project_manager.py` (+20 tests)
- `tests/unit/agents/test_socratic_counselor.py` (+15 tests)
- `tests/unit/agents/test_code_generator.py` (+15 tests)
- `tests/unit/agents/test_document_processor.py` (+10 tests)

#### 3.3.2: API Endpoint Testing (~6 hours)

**File:** `socrates-api/src/socrates_api/routers/*.py`

What to test:
```python
# Test each endpoint with:
- Valid input -> Correct response
- Invalid input -> Proper error
- Missing fields -> Validation error
- Unauthorized -> 401/403
- Database error -> 500 with details
```

**Files to create/expand:**
- `socrates-api/tests/test_projects_router.py` (+10 tests)
- `socrates-api/tests/test_code_router.py` (+8 tests)
- `socrates-api/tests/test_chat_router.py` (+8 tests)
- `socrates-api/tests/test_auth_router.py` (+10 tests)

#### 3.3.3: Error Path Testing (~4 hours)

**File:** All command files and API routers

What to test - orchestrator failures:
```python
def test_code_generate_handles_orchestrator_failure():
    """Test graceful handling when orchestrator fails"""
    context = create_test_context()
    context['orchestrator'] = MockOrchestrator(should_fail=True)

    cmd = CodeGenerateCommand()
    result = cmd.execute([], context)

    assert result["status"] == "error"
    assert "Failed to generate code" in result["message"]
    # Verify user-friendly error message
    assert "debug info" not in result["message"]
```

Test database failures:
```python
def test_session_handles_save_failure():
    """Test session gracefully handles database save failure"""
    session = SessionCommands()
    db = MockDatabase(should_fail_on_save=True)

    # Operation completes but save fails
    with pytest.raises(DatabaseError):
        session._save_session_state(test_data, db)
```

Test network timeouts:
```python
def test_doc_import_handles_url_timeout():
    """Test doc import gracefully handles URL timeout"""
    cmd = DocImportCommand()

    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.Timeout("Connection timeout")
        result = cmd.execute(["https://example.com/large.pdf"], context)

        assert result["status"] == "error"
        assert "timeout" in result["message"].lower()
```

#### 3.3.4: Integration & E2E Testing (~4 hours)

**File:** Expand `tests/e2e_tests.py`

What to test:
```python
# Complete workflows
- Create project → Add docs → Generate code → Export
- Create project → Multiple phase progressions → Generate artifact
- Create project → Add collaborators → Sync to GitHub
- Import docs → Ask questions → Generate based on Q&A
- Multiple users, same project → Verify no conflicts
```

**Test template:**
```python
def test_end_to_end_project_creation_to_code_generation():
    """Test full workflow: create project, add docs, generate code"""
    # Setup
    orchestrator = create_test_orchestrator()
    project = orchestrator.create_project("E2E Test Project")

    # Add documentation
    doc_result = orchestrator.process_request(
        "document_agent",
        {"action": "import_file", "project": project, "filepath": "test.md"}
    )
    assert doc_result["status"] == "success"

    # Progress through phases
    # ... (discovery, analysis, design)

    # Generate code
    code_result = orchestrator.process_request(
        "code_generator",
        {"action": "generate_script", "project": project}
    )
    assert code_result["status"] == "success"
    assert len(code_result["script"]) > 100  # Non-empty code
```

### Quick Wins (Can be done quickly)

1. **Test existing happy paths** (2 hours)
   - Write tests that document current working behavior
   - Run with coverage, identify gaps
   - Add assertions to cover branches

2. **Mock external dependencies** (1 hour)
   - Create MockDatabase, MockOrchestrator, MockGitHub
   - Reuse across tests
   - Reduces test complexity

3. **Use pytest fixtures** (1 hour)
   - Create `conftest.py` with:
     - `test_project()` fixture
     - `test_context()` fixture
     - `mock_orchestrator()` fixture
   - Reduces duplication

### Test Coverage Command

```bash
# Run with coverage report
pytest tests/ --cov=socratic_system --cov=socrates_api \
  --cov-report=html --cov-report=term-missing \
  -m "not integration"

# View report
open htmlcov/index.html

# Target: 70%+ overall, 80%+ for critical modules
```

### Files to Prioritize (High Impact)

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| `agents/project_manager.py` | 40% | 85% | CRITICAL |
| `agents/socratic_counselor.py` | 35% | 80% | CRITICAL |
| `utils/orchestrator_helper.py` | 60% | 90% | HIGH |
| `ui/commands/code_commands.py` | 30% | 75% | HIGH |
| `ui/commands/session_commands.py` | 25% | 70% | HIGH |
| API routers | 45% | 75% | MEDIUM |
| Database layer | 50% | 80% | MEDIUM |

---

## Time Estimates for Phase 3

### Phase 3.1: Frontend API Consistency
| Subtask | Time | Effort |
|---------|------|--------|
| 3.1.1: Audit all endpoints | 1 hour | Low |
| 3.1.2: Standardize response format | 1.5 hours | Medium |
| 3.1.3: Update client code | 1 hour | Medium |
| **Subtotal** | **3.5 hours** | |

**Critical Files to Update:**
- `socrates-api/src/socrates_api/models.py` (create APIResponse)
- `socrates-api/src/socrates_api/routers/projects.py` (10 endpoints)
- `socrates-api/src/socrates_api/routers/code.py` (5 endpoints)
- `socrates-api/src/socrates_api/routers/chat.py` (4 endpoints)
- All other routers (~7 more files)

### Phase 3.2: GitHub Sync Edge Cases
| Edge Case | Time | Complexity | Impact |
|-----------|------|-----------|--------|
| Conflict resolution | 1 hour | Medium | Prevents data loss |
| Large file handling | 45 min | Low | Prevents sync failure |
| Token expiry handling | 1 hour | Medium | Maintains reliability |
| Network interruption recovery | 1 hour | High | Ensures resilience |
| Permission error handling | 45 min | Low | Improves UX |
| **Subtotal** | **4.75 hours** | |

**Key Files to Modify:**
- `socratic_system/agents/github_sync.py` (main logic)
- `socrates-api/src/socrates_api/routers/github.py` (API endpoints)
- Database schema (track sync progress)

### Phase 3.3: Test Coverage Expansion to 70%+
| Category | Time | Tests | Target Coverage |
|----------|------|-------|-----------------|
| Agent testing | 8 hours | ~60 tests | 80-90% |
| API endpoint testing | 6 hours | ~36 tests | 75-85% |
| Error path testing | 4 hours | ~20 tests | 80-90% |
| Integration/E2E | 4 hours | ~10 tests | 70-85% |
| **Subtotal** | **22 hours** | ~126 tests | 70%+ |

**Files to Create/Expand:**
- `tests/unit/agents/test_project_manager.py` (+20 tests)
- `tests/unit/agents/test_socratic_counselor.py` (+15 tests)
- `tests/unit/agents/test_code_generator.py` (+15 tests)
- `tests/unit/agents/test_document_processor.py` (+10 tests)
- `socrates-api/tests/test_*.py` (4 files, ~36 tests total)
- `tests/e2e_tests.py` (expand with 10+ tests)

**Priority Modules to Target:**
- `agents/project_manager.py` (40% → 85%)
- `agents/socratic_counselor.py` (35% → 80%)
- `utils/orchestrator_helper.py` (60% → 90%)
- Command files (25-30% → 70%+)
- API routers (45% → 75%)

---

## Overall Timeline

| Phase | Status | Completion | Hours | Start Date |
|-------|--------|-----------|-------|-----------|
| **Phase 2** | ✅ COMPLETE | Jan 6, 2026 | 14.5 | Dec 28, 2025 |
| **Phase 3.1** | 🔄 PENDING | Jan 8, 2026 | 3.5 | Jan 8, 2026 |
| **Phase 3.2** | 🔄 PENDING | Jan 8-9, 2026 | 4.75 | Jan 8, 2026 |
| **Phase 3.3** | 🔄 PENDING | Jan 10-12, 2026 | 22 | Jan 9, 2026 |
| **TOTAL** | | Jan 12, 2026 | **44.75** | Dec 28, 2025 |

**Note:** Phase 3.1 can run in parallel with Phase 3.2. Phase 3.3 can begin after Phase 3.1 is complete to allow for testing the API changes.

---

## Recommended Execution Strategy for Phase 3

### Option A: Serial (Safer, Lower Risk)
1. Complete Phase 3.1 fully
2. Deploy and test API changes
3. Then start Phase 3.2
4. Overlap Phase 3.3 with 3.2

### Option B: Parallel (Faster, Moderate Risk)
1. Work on Phase 3.1 and 3.2 simultaneously (different teams/contexts)
2. Phase 3.1 (API consistency): 1 dev, 3.5 hours
3. Phase 3.2 (GitHub edge cases): 1 dev, 4.75 hours
4. Phase 3.3 (Testing): Start while 3.1 deploys, continue through 3.2

### Option C: Prioritized (Recommended)
1. **Day 1 (Jan 8):** Phase 3.1 - API consistency (highest user impact)
2. **Day 2 (Jan 9):** Phase 3.2 - GitHub edge cases (improves reliability)
3. **Days 3-4 (Jan 10-11):** Phase 3.3 - Test coverage (ensures quality)

---

## Success Criteria

### Phase 3.1: Frontend API Success
- [ ] All endpoints return `APIResponse` model
- [ ] Client code simplified (fewer format checks)
- [ ] API documentation auto-generated with consistent schema
- [ ] 100% endpoint compliance verified
- [ ] Backward compatibility maintained (if needed)

### Phase 3.2: GitHub Sync Success
- [ ] All 5 edge cases implemented and tested
- [ ] Merge conflicts resolved without user intervention (when possible)
- [ ] Token expiry handled gracefully with automatic refresh
- [ ] Network failures retry with exponential backoff
- [ ] Permission errors provide clear user messaging
- [ ] No data loss in any edge case scenario

### Phase 3.3: Test Coverage Success
- [ ] Overall coverage: 70%+ (current: 45-50%)
- [ ] Critical modules: 80%+ coverage
  - `agents/project_manager.py` (target: 85%)
  - `agents/socratic_counselor.py` (target: 80%)
  - Core API routers (target: 75%+)
- [ ] All error paths tested
- [ ] Integration tests cover major workflows
- [ ] No critical bugs in untested code

---

## Phase 3 Dependency Chain

```
Phase 3.1 (API Consistency)
    ↓
    ├─→ API models updated
    ├─→ All routers updated (~7 files)
    └─→ Client code updated
        ↓
        Tests: Verify format consistency

Phase 3.2 (GitHub Edge Cases)
    ├─→ Conflict resolution
    ├─→ Large file handling
    ├─→ Token expiry
    ├─→ Network retry
    └─→ Permission handling
        ↓
        Tests: E2E GitHub scenarios

Phase 3.3 (Test Coverage)
    ├─→ Agent tests (+60 tests)
    ├─→ API tests (+36 tests)
    ├─→ Error path tests (+20 tests)
    └─→ Integration tests (+10 tests)
        ↓
        Result: 70%+ coverage achieved
```

---

## Known Challenges & Mitigations

| Challenge | Severity | Mitigation |
|-----------|----------|-----------|
| Backward compatibility in API change | HIGH | Create adapter layer for old format |
| Testing GitHub sync without real repo | HIGH | Use mock GitHub client |
| Complex integration test setup | MEDIUM | Create comprehensive fixtures |
| Token refresh without user interaction | MEDIUM | Implement OAuth refresh flow |
| Determining test coverage gaps | LOW | Use coverage.py HTML report |

---

## Next Steps (Post-Phase-3)

Once Phase 3 is complete:
1. **Performance optimization** - Profile and optimize slow operations
2. **Documentation** - Auto-generate API docs from models
3. **Monitoring** - Add metrics/alerting for production issues
4. **Security audit** - Review authentication, data protection
5. **User feedback loop** - Gather UX feedback from real users

All changes maintain backward compatibility where possible and follow established patterns.
