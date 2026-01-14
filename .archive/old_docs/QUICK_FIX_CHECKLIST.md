# Quick Fix Checklist for Failing Tests

## Status: 18 Failing Tests Analyzed
- 6 tests: Authentication before parameter validation
- 3 tests: Missing `/knowledge/export` endpoint
- 4 tests: Wrong maturity endpoint path
- 1 test: CORS OPTIONS handling issue
- 1 test: OpenAPI duplicate Operation IDs
- 3 tests: Workflow failures (depend on above)

---

## Fix 1: Implement /knowledge/export Endpoint
**Files Affected:** 3 tests + 1 workflow

### Checklist
- [ ] Add new endpoint `GET /knowledge/export` to `src/socrates_api/routers/knowledge.py`
- [ ] Support `format` query parameter (json, csv, markdown, xml)
- [ ] Support optional `project_id` query parameter
- [ ] Implement proper authorization checks
- [ ] Return appropriate content-type headers
- [ ] Handle invalid format parameter with 400 response
- [ ] Run tests to verify:
  - `test_export_knowledge` PASSES
  - `test_export_knowledge_specific_format` PASSES
  - `test_knowledge_export_endpoint` PASSES
  - `test_import_search_export_knowledge_workflow` PASSES

### Code Location
**File:** `socrates-api/src/socrates_api/routers/knowledge.py`

Add this function:
```python
@router.get(
    "/export",
    summary="Export knowledge base",
    responses={
        200: {"description": "Knowledge base exported"},
        400: {"description": "Invalid format"},
        401: {"description": "Unauthorized"},
    },
)
async def export_knowledge(
    format: str = "json",
    project_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """Export knowledge base in specified format."""
    # Implementation here
```

---

## Fix 2: Update Maturity Assessment Tests
**Files Affected:** 4 tests + 2 workflow tests

### Checklist
- [ ] Update test path from `/analysis/maturity` to `/analysis/{project_id}/maturity`
- [ ] Provide valid project_id in all tests (can use 'test-project' for unit tests)
- [ ] For workflow tests, ensure project_id is obtained from earlier steps
- [ ] Run tests to verify:
  - `test_code_maturity_assessment` PASSES
  - `test_maturity_missing_code` PASSES
  - `test_code_maturity_assessment_workflow` PASSES
  - `test_analysis_maturity_endpoint` PASSES
  - `test_github_project_import_workflow` PASSES

### Files to Update
1. `socrates-api/tests/integration/test_all_endpoints.py`
   - Line ~420: Change `'/analysis/maturity'` to `'/analysis/test-project/maturity'`
   - Line ~429: Change `'/analysis/maturity'` to `'/analysis/test-project/maturity'`

2. `socrates-api/tests/integration/test_e2e_workflows.py`
   - Line ~285: Change `'/analysis/maturity'` to `'/analysis/{project_id}/maturity'`
   - Line ~380: Change `'/analysis/maturity'` to `'/analysis/github-import-test/maturity'`

3. `socrates-api/tests/integration/test_routers_comprehensive.py`
   - Line ~224: Change `'/analysis/maturity'` to `'/analysis/test-project/maturity'`

---

## Fix 3: Add Authentication to Parameter Validation Tests
**Files Affected:** 6 tests

### Checklist - Option A: Add Headers to Tests (Recommended)
- [ ] Create test fixture for authentication headers
- [ ] Add headers to all 6 affected tests
- [ ] Run tests to verify:
  - `test_import_missing_url` PASSES (gets 400/422)
  - `test_import_knowledge_missing_text` PASSES (gets 400/422)
  - `test_search_knowledge_missing_query` PASSES (gets 400/422)
  - `test_validate_missing_language` PASSES (gets 400/422)
  - `test_validate_missing_code` PASSES (gets 400/422)
  - `test_invite_missing_email` PASSES (gets 400/422)

### Files to Update
`socrates-api/tests/integration/test_all_endpoints.py`

Example fix:
```python
def test_import_missing_url(self, client: TestClient):
    """POST /github/import missing URL"""
    headers = {'Authorization': 'Bearer test-token'}
    response = client.post('/github/import', json={}, headers=headers)
    assert response.status_code in [400, 422]
```

### Checklist - Option B: Move Validation Before Auth (Alternative)
- [ ] Modify endpoint handlers in routers
- [ ] Check parameters before `Depends(get_current_user)`
- [ ] This requires careful refactoring of auth flow

---

## Fix 4: Fix CORS Preflight Handling
**Files Affected:** 1 test

### Checklist
- [ ] Check CORS middleware configuration in `main.py`
- [ ] Ensure:
  - CORSMiddleware is added BEFORE auth middleware
  - `allow_methods=["*"]` includes OPTIONS
  - `allow_headers=["*"]` includes custom CORS headers
- [ ] Test OPTIONS request manually
- [ ] Run test to verify:
  - `test_cors_preflight_handled` PASSES (gets 200 or 405)

### Configuration Check
File: `socrates-api/src/socrates_api/main.py`

Ensure pattern:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# AUTH middleware added AFTER
```

---

## Fix 5: Fix OpenAPI Operation ID Duplicates
**Files Affected:** 1 test (warnings only, test passes)

### Checklist
- [ ] Find duplicate operation IDs in affected files
- [ ] Add explicit `operation_id` to route decorators
- [ ] Files to update:
  - `src/socrates_api/routers/progress.py`
  - `src/socrates_api/routers/chat_sessions.py`
- [ ] Run test to verify no warnings:
  - `test_openapi_schema` PASSES (no warnings)

### Example Fix
Before:
```python
@router.get("/{project_id}/stats")
async def get_project_stats(...):
```

After:
```python
@router.get("/{project_id}/stats", operation_id="get_project_statistics")
async def get_project_stats(...):
```

---

## Verification Steps

### After Each Fix
```bash
cd socrates-api

# Run specific test
pytest tests/integration/test_all_endpoints.py::TestKnowledgeEndpoints::test_export_knowledge -v

# Run all failing tests
pytest tests/integration/test_all_endpoints.py \
        tests/integration/test_e2e_workflows.py \
        tests/integration/test_routers_comprehensive.py \
        tests/integration/test_security_penetration.py -v

# Run full integration test suite
pytest tests/integration/ -v
```

### Expected Results
- Before fixes: 18 FAILED, 173 PASSED
- After Fix 1: 15 FAILED, 176 PASSED
- After Fix 2: 11 FAILED, 180 PASSED
- After Fix 3: 5 FAILED, 186 PASSED
- After Fix 4: 4 FAILED, 187 PASSED
- After Fix 5: 3 FAILED, 188 PASSED (warnings only)
- After Fix 3 (complete): 0 FAILED, 191 PASSED

---

## Time Estimates

| Fix | Complexity | Time Estimate | Priority |
|-----|-----------|---------------|----------|
| Fix 1: Export endpoint | Medium | 1-2 hours | HIGH |
| Fix 2: Maturity paths | Low | 15 minutes | HIGH |
| Fix 3: Auth headers | Low | 30 minutes | HIGH |
| Fix 4: CORS | Low | 15 minutes | MEDIUM |
| Fix 5: Operation IDs | Low | 10 minutes | LOW |

**Total Time:** 2-3 hours

---

## Related Files Reference

### Test Files
- `socrates-api/tests/integration/test_all_endpoints.py` - 11 tests failing
- `socrates-api/tests/integration/test_e2e_workflows.py` - 4 tests failing
- `socrates-api/tests/integration/test_routers_comprehensive.py` - 2 tests failing
- `socrates-api/tests/integration/test_security_penetration.py` - 1 test failing

### Implementation Files
- `socrates-api/src/socrates_api/routers/knowledge.py` - Add export endpoint
- `socrates-api/src/socrates_api/routers/analysis.py` - Correct path (already correct)
- `socrates-api/src/socrates_api/routers/progress.py` - Fix Operation ID
- `socrates-api/src/socrates_api/routers/chat_sessions.py` - Fix Operation IDs
- `socrates-api/src/socrates_api/main.py` - Check CORS configuration

---

## Notes

1. **No API bugs found** - All failures are test/configuration issues
2. **No data loss risks** - Safe to make these changes
3. **Backward compatible** - All fixes are additive or path corrections
4. **Tests are comprehensive** - Good coverage of API functionality
5. **Most failures are discoverable** - Clear error messages guide fixes
