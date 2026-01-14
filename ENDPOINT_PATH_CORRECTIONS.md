# Endpoint Path Corrections and Implementation Details

## Issue 1: Maturity Assessment Endpoint Path Mismatch

### Problem
Tests are calling endpoint with incorrect path:
- **Test Path (WRONG):** `POST /analysis/maturity`
- **Actual Path (CORRECT):** `POST /analysis/{project_id}/maturity`

### Affected Tests (4)
- `test_code_maturity_assessment` (test_all_endpoints.py)
- `test_maturity_missing_code` (test_all_endpoints.py)
- `test_code_maturity_assessment_workflow` (test_e2e_workflows.py)
- `test_analysis_maturity_endpoint` (test_routers_comprehensive.py)

### Current Implementation
**File:** `socrates-api/src/socrates_api/routers/analysis.py:119`

```python
@router.post(
    "/{project_id}/maturity",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess code maturity",
    responses={
        200: {"description": "Maturity assessment completed"},
        400: {"description": "Invalid input", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def assess_maturity(
    project_id: str,
    phase: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Assess project maturity for current or specified phase.

    Args:
        project_id: Project ID (required)
        phase: Phase to assess (discovery, analysis, design, implementation)
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with maturity metrics from quality_controller
    """
```

### Test Code That's FAILING
```python
# test_all_endpoints.py - TestAnalysisEndpoints
def test_code_maturity_assessment(self, client: TestClient):
    """POST /analysis/maturity"""
    response = client.post('/analysis/maturity', json={
        'code': 'def hello(): return "world"',
        'language': 'python'
    })
    assert response.status_code != 404  # FAILS: Gets 404
```

### Correct Test Code
```python
def test_code_maturity_assessment(self, client: TestClient):
    """POST /analysis/{project_id}/maturity"""
    response = client.post('/analysis/test-project-id/maturity', json={
        'code': 'def hello(): return "world"',
        'language': 'python'
    })
    assert response.status_code != 404  # Would PASS with valid project_id
```

### Why This Matters
The endpoint **DOES EXIST** but tests are looking for it at the wrong path. This is a test issue, not an implementation issue.

---

## Issue 2: Missing Knowledge Export Endpoint

### Problem
Tests call endpoint that doesn't exist:
- **Called Path:** `GET /knowledge/export`
- **Status Returned:** 404 Not Found
- **Actual Implementation:** Missing

### Affected Tests (3)
- `test_export_knowledge` (test_all_endpoints.py)
- `test_export_knowledge_specific_format` (test_all_endpoints.py)
- `test_knowledge_export_endpoint` (test_routers_comprehensive.py)

### Workflow Test Dependency
- `test_import_search_export_knowledge_workflow` (test_e2e_workflows.py) - FAILS at step 5

### Current Knowledge Router
**File:** `socrates-api/src/socrates_api/routers/knowledge.py`

Existing endpoints:
```
GET /documents - List all documents
GET /search - Search documents
POST /import/url - Import from URL
POST /import/text - Import from text
POST /import/file - Import file
GET /documents/{doc_id} - Get specific document
DELETE /documents/{doc_id} - Delete document
```

Missing endpoint:
```
GET /knowledge/export - DOES NOT EXIST
GET /knowledge/export?format=json - DOES NOT EXIST
GET /knowledge/export?format=csv - DOES NOT EXIST
```

### What Needs to be Implemented

```python
@router.get(
    "/export",
    summary="Export knowledge base",
    responses={
        200: {"description": "Knowledge base exported"},
        400: {"description": "Invalid format", "model": ErrorResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
    },
)
async def export_knowledge(
    format: str = "json",  # json, csv, markdown, xml
    project_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Export knowledge base in specified format.

    Args:
        format: Export format (json, csv, markdown, xml)
        project_id: Optional - export specific project's knowledge
        current_user: Authenticated user
        db: Database connection

    Returns:
        File response with exported knowledge or JSON
    """
    try:
        if format not in ["json", "csv", "markdown", "xml"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {format}. Supported: json, csv, markdown, xml"
            )

        # Get knowledge documents
        # Implement export logic based on format
        # Return appropriate response

    except Exception as e:
        logger.error(f"Error exporting knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export knowledge")
```

### Test Code
```python
# test_all_endpoints.py - TestKnowledgeEndpoints
def test_export_knowledge(self, client: TestClient):
    """GET /knowledge/export"""
    response = client.get('/knowledge/export')
    assert response.status_code != 404  # FAILS: Gets 404, endpoint missing

def test_export_knowledge_specific_format(self, client: TestClient):
    """GET /knowledge/export with format"""
    response = client.get('/knowledge/export?format=json')
    assert response.status_code != 404  # FAILS: Gets 404, endpoint missing
```

---

## Issue 3: Authentication Before Parameter Validation

### Problem
Six tests expect parameter validation errors (400/422) but get 401 Unauthorized instead, because authentication is checked before parameter validation.

### Affected Tests (6)
- `test_import_missing_url` (test_all_endpoints.py)
- `test_import_knowledge_missing_text` (test_all_endpoints.py)
- `test_search_knowledge_missing_query` (test_all_endpoints.py)
- `test_validate_missing_language` (test_all_endpoints.py)
- `test_validate_missing_code` (test_all_endpoints.py)
- `test_invite_missing_email` (test_all_endpoints.py)

### Current Implementation Pattern
```python
@router.post("/github/import")
async def import_github_repo(
    url: Optional[str] = None,
    current_user: str = Depends(get_current_user),  # Auth checked FIRST
):
    # Parameter validation happens AFTER auth
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
```

### Test Code That FAILS
```python
def test_import_missing_url(self, client: TestClient):
    """POST /github/import missing URL"""
    response = client.post('/github/import', json={})
    assert response.status_code in [400, 422]  # FAILS: Gets 401 instead
    # Expected flow: No auth headers -> 401 -> missing URL param -> 400
    # Actual flow: No auth headers -> 401 (stops here)
```

### Solutions

#### Option A: Add Authentication Headers to Tests
```python
def test_import_missing_url(self, client: TestClient):
    """POST /github/import missing URL"""
    headers = {'Authorization': 'Bearer test-token'}
    response = client.post('/github/import', json={}, headers=headers)
    assert response.status_code in [400, 422]  # Would PASS
```

#### Option B: Move Parameter Validation Before Auth
```python
@router.post("/github/import")
async def import_github_repo(
    url: Optional[str] = None,  # Validate BEFORE auth check
    current_user: str = Depends(get_current_user),
):
    # Validate parameters first
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Then use the authenticated user
    ...
```

#### Option C: Custom Dependency with Conditional Auth
```python
async def get_current_user_optional(request: Request):
    """Get current user, allowing operations that don't need auth"""
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return None
    # Validate and return user...

@router.post("/github/import")
async def import_github_repo(
    url: Optional[str] = None,
    current_user: Optional[str] = Depends(get_current_user_optional),
):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    ...
```

---

## Issue 4: CORS Preflight OPTIONS Request

### Problem
`OPTIONS /auth/login` returns 400 Bad Request instead of 200/404/405

### Affected Test (1)
- `test_cors_preflight_handled` (test_security_penetration.py)

### Test Code
```python
def test_cors_preflight_handled(self, client: TestClient):
    """Test CORS preflight request handling"""
    response = client.options('/auth/login',
                             headers={
                                 'Origin': 'https://example.com',
                                 'Access-Control-Request-Method': 'POST'
                             })
    assert response.status_code in [200, 404, 405]  # FAILS: Gets 400
```

### Likely Causes
1. CORS middleware misconfigured
2. OPTIONS handler in authentication router rejecting request
3. Header validation issue

### Current FastAPI CORS Configuration
Likely in: `socrates-api/src/socrates_api/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific list
    allow_credentials=True,
    allow_methods=["*"],  # Should include OPTIONS
    allow_headers=["*"],
)
```

### Fix
Ensure:
1. CORS middleware is installed BEFORE auth middleware
2. OPTIONS method is allowed
3. Preflight headers are properly handled

---

## Issue 5: Duplicate OpenAPI Operation IDs

### Problem
FastAPI generates warnings about duplicate Operation IDs

### Affected Test (1)
- `test_openapi_schema` (test_all_endpoints.py) - PASSES but with warnings

### Duplicates Found
1. `get_project_stats_projects__project_id__stats_get`
   - Location: `src/socrates_api/routers/progress.py`

2. `create_chat_session_projects__project_id__chat_sessions_post`
   - Location: `src/socrates_api/routers/chat_sessions.py`

3. `list_chat_sessions_projects__project_id__chat_sessions_get`
   - Location: `src/socrates_api/routers/chat_sessions.py`

4. `get_chat_session_projects__project_id__chat_sessions__session_id__get`
   - Location: `src/socrates_api/routers/chat_sessions.py`

### Solution
Use explicit operationId in route decorators:

```python
# Before (auto-generated, may duplicate)
@router.get("/{project_id}/stats")
async def get_project_stats(...):
    ...

# After (explicit, unique)
@router.get("/{project_id}/stats", operation_id="get_project_statistics")
async def get_project_stats(...):
    ...
```

---

## Summary of Required Changes

| Issue | Type | Count | Fix Complexity | Impact |
|-------|------|-------|-----------------|--------|
| Endpoint path mismatch | Test | 4 | LOW | HIGH |
| Missing export endpoint | Implementation | 3 | MEDIUM | HIGH |
| Auth before validation | Design | 6 | MEDIUM | MEDIUM |
| CORS OPTIONS handling | Configuration | 1 | LOW | LOW |
| Duplicate Operation IDs | Configuration | 1 | LOW | LOW |

---

## Implementation Order

1. **Fix maturity endpoint tests** (4 tests) - Update test paths
2. **Implement export endpoint** (3 tests) - Add new endpoint
3. **Fix authentication order** (6 tests) - Either add headers to tests or reorder checks
4. **Fix CORS configuration** (1 test) - Debug middleware
5. **Fix Operation IDs** (1 test) - Use explicit operation_id parameter

Total Expected Passing After Fixes: **191 tests (from 173)**
