# Phase 3 Implementation Guide - 28 Missing Endpoints

**Objective**: Implement missing endpoints to achieve 100% test pass rate (336/336)
**Estimated Time**: 10 hours
**Target**: All 28 endpoints with full functionality
**Success Criteria**: All 58 failing tests pass

---

## Quick Reference

| Priority | Module | Count | Time | Tests | Status |
|----------|--------|-------|------|-------|--------|
| 1 | Auth | 1 | 0.5h | 1 test | ⏳ Pending |
| 2 | GitHub | 5 | 2h | 7 tests | ⏳ Pending |
| 3 | Knowledge | 4 | 1.5h | 4 tests | ⏳ Pending |
| 4 | LLM | 6 | 2h | 6 tests | ⏳ Pending |
| 5 | Analysis | 2 | 1h | 2 tests | ⏳ Pending |
| 6 | Collaboration | 6 | 2h | 6 tests | ⏳ Pending |
| 7 | Analytics | 4 | 1.5h | 4 tests | ⏳ Pending |
| | **TOTAL** | **28** | **10h** | **30+ tests** | |

---

## Priority 1: Authentication (1 Endpoint, 30 min)

### Endpoint 1: Change Password
**Route**: `PUT /auth/change-password`
**Status**: ❌ Missing (404 Not Found)
**Tests Failing**: 1

**Expected Request**:
```json
{
  "old_password": "current_password",
  "new_password": "new_secure_password"
}
```

**Expected Response** (200 OK):
```json
{
  "message": "Password changed successfully"
}
```

**Error Cases**:
- `401`: Old password incorrect
- `400`: New password doesn't meet requirements
- `422`: Invalid request format

**Implementation Steps**:
1. Create endpoint in `socrates-api/src/socrates_api/routers/auth.py`
2. Get current user from auth header
3. Verify old password matches user's passcode_hash
4. Validate new password strength (8+ chars, mixed case/numbers)
5. Hash new password
6. Update database
7. Log password change
8. Return success

**Test Reference**:
- `test_change_password_endpoint`

---

## Priority 2: GitHub Integration (5 Endpoints, 2 hours)

### Endpoint 1: Import from GitHub
**Route**: `POST /projects/{project_id}/github/import`
**Status**: ❌ Missing (404)
**Tests Failing**: 2-3

**Expected Request**:
```json
{
  "github_url": "https://github.com/user/repo",
  "branch": "main",
  "auth_token": "optional_github_token"
}
```

**Expected Response** (200 OK):
```json
{
  "status": "importing",
  "project_id": "proj_xxx",
  "repo_url": "https://github.com/user/repo",
  "imported_files": 42,
  "sync_status": "in_progress"
}
```

**Implementation**:
1. Validate GitHub URL format
2. Clone or fetch repository
3. Store GitHub credentials securely
4. Index files into knowledge base
5. Return import status

---

### Endpoint 2: Check GitHub Sync Status
**Route**: `GET /projects/{project_id}/github/status`
**Status**: ❌ Missing

**Expected Response** (200 OK):
```json
{
  "status": "synced",
  "last_sync": "2025-12-23T10:30:00Z",
  "github_url": "https://github.com/user/repo",
  "branch": "main",
  "pending_changes": 0,
  "total_files": 42
}
```

---

### Endpoint 3: Pull Latest Changes
**Route**: `POST /projects/{project_id}/github/pull`
**Status**: ❌ Missing

**Expected Response** (200 OK):
```json
{
  "status": "success",
  "changes_pulled": 5,
  "new_files": 2,
  "modified_files": 3,
  "deleted_files": 0,
  "sync_time": "2025-12-23T10:35:00Z"
}
```

---

### Endpoint 4: Push Changes
**Route**: `POST /projects/{project_id}/github/push`
**Status**: ❌ Missing

**Expected Request**:
```json
{
  "commit_message": "Update analysis results",
  "branch": "main"
}
```

**Expected Response** (200 OK):
```json
{
  "status": "success",
  "commit_hash": "abc123def456",
  "pushed_files": 3,
  "branch": "main"
}
```

---

### Endpoint 5: Disconnect GitHub
**Route**: `POST /projects/{project_id}/github/disconnect`
**Status**: ❌ Missing

**Expected Response** (200 OK):
```json
{
  "status": "disconnected",
  "project_id": "proj_xxx",
  "message": "GitHub integration removed"
}
```

**Implementation Notes**:
- Remove stored credentials
- Keep existing project data
- Clear sync status
- Allow re-connection later

---

## Priority 3: Knowledge Management (4 Endpoints, 1.5 hours)

### Endpoint 1: List Knowledge Documents
**Route**: `GET /projects/{project_id}/knowledge/documents`
**Status**: ❌ Missing (404)
**Query Params**: `?page=1&limit=20&sort=created_at`

**Expected Response** (200 OK):
```json
{
  "documents": [
    {
      "id": "doc_xxx",
      "title": "API Documentation",
      "source": "https://api.example.com/docs",
      "created_at": "2025-12-20T10:00:00Z",
      "file_size": 45678,
      "format": "html"
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 20
}
```

---

### Endpoint 2: Export Knowledge Base
**Route**: `POST /projects/{project_id}/knowledge/export`
**Status**: ❌ Missing
**Body**: `{"format": "csv|json|markdown", "include_metadata": true}`

**Expected Response** (200 OK):
```json
{
  "status": "exported",
  "format": "csv",
  "file_url": "/downloads/knowledge_export_20251223.csv",
  "total_documents": 15,
  "export_time": "2025-12-23T10:40:00Z"
}
```

---

### Endpoint 3: Search Knowledge
**Route**: `GET /projects/{project_id}/knowledge/search`
**Status**: ❌ Missing
**Query**: `?q=authentication&limit=10`

**Expected Response** (200 OK):
```json
{
  "results": [
    {
      "id": "doc_xxx",
      "title": "Authentication Guide",
      "snippet": "...relevant excerpt...",
      "relevance_score": 0.95
    }
  ],
  "total_results": 3
}
```

---

### Endpoint 4: Delete Knowledge Document
**Route**: `DELETE /projects/{project_id}/knowledge/{document_id}`
**Status**: ❌ Missing

**Expected Response** (200 OK):
```json
{
  "status": "deleted",
  "document_id": "doc_xxx",
  "title": "API Documentation"
}
```

---

## Priority 4: LLM Configuration (6 Endpoints, 2 hours)

### Endpoint 1: List LLM Providers
**Route**: `GET /llm/providers`
**Status**: ❌ Missing (404)

**Expected Response** (200 OK):
```json
{
  "providers": [
    {
      "name": "openai",
      "display_name": "OpenAI",
      "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
      "requires_api_key": true
    },
    {
      "name": "anthropic",
      "display_name": "Anthropic Claude",
      "models": ["claude-opus", "claude-sonnet"],
      "requires_api_key": true
    }
  ]
}
```

---

### Endpoint 2: Set Default Provider
**Route**: `PUT /llm/default-provider`
**Status**: ❌ Missing

**Expected Request**:
```json
{
  "provider": "openai"
}
```

**Expected Response** (200 OK):
```json
{
  "default_provider": "openai",
  "updated_at": "2025-12-23T10:45:00Z"
}
```

---

### Endpoint 3: Set Model
**Route**: `POST /llm/model`
**Status**: ❌ Missing

**Expected Request**:
```json
{
  "provider": "openai",
  "model": "gpt-4-turbo"
}
```

**Expected Response** (200 OK):
```json
{
  "provider": "openai",
  "model": "gpt-4-turbo",
  "set_at": "2025-12-23T10:46:00Z"
}
```

---

### Endpoint 4: Add API Key
**Route**: `POST /llm/api-keys`
**Status**: ❌ Missing

**Expected Request**:
```json
{
  "provider": "openai",
  "api_key": "sk-..."
}
```

**Expected Response** (200 OK):
```json
{
  "provider": "openai",
  "key_added": true,
  "added_at": "2025-12-23T10:47:00Z"
}
```

**Security Notes**:
- Don't echo API key in response
- Encrypt in database
- Hash for verification only

---

### Endpoint 5: Remove API Key
**Route**: `DELETE /llm/api-keys/{provider}`
**Status**: ❌ Missing

**Expected Response** (200 OK):
```json
{
  "provider": "openai",
  "removed": true,
  "removed_at": "2025-12-23T10:48:00Z"
}
```

---

### Endpoint 6: List Models
**Route**: `GET /llm/models`
**Status**: ❌ Missing

**Expected Response** (200 OK):
```json
{
  "models": [
    {
      "provider": "openai",
      "name": "gpt-4-turbo",
      "display_name": "GPT-4 Turbo",
      "available": true
    }
  ]
}
```

---

## Priority 5: Code Analysis (2 Endpoints, 1 hour)

### Endpoint 1: Code Maturity Assessment
**Route**: `POST /projects/{project_id}/analysis/maturity`
**Status**: ❌ Missing (404)

**Expected Request**:
```json
{
  "code": "def hello():\n    print('world')",
  "language": "python"
}
```

**Expected Response** (200 OK):
```json
{
  "maturity_score": 4.2,
  "category_scores": {
    "maintainability": 4.0,
    "reliability": 4.5,
    "security": 4.0,
    "performance": 4.0,
    "testability": 4.2
  },
  "recommendations": ["Add type hints", "Increase test coverage"]
}
```

---

### Endpoint 2: Code Validation (already exists but may need fixes)
**Status**: Verify passes all tests

---

## Priority 6: Collaboration (6 Endpoints, 2 hours)

### Endpoint 1: Invite Team Member
**Route**: `POST /projects/{project_id}/team/invite`
**Status**: ❌ Missing (404)

**Expected Request**:
```json
{
  "email": "colleague@company.com",
  "role": "editor"
}
```

**Expected Response** (201 Created):
```json
{
  "invitation_id": "inv_xxx",
  "email": "colleague@company.com",
  "role": "editor",
  "status": "pending",
  "expires_at": "2025-12-30T00:00:00Z"
}
```

---

### Endpoints 2-6: Team Management
- List team members
- Update member role
- Remove member
- Accept invitation
- Revoke invitation

**Similar implementation pattern to invite endpoint**

---

## Priority 7: Analytics (4 Endpoints, 1.5 hours)

### Endpoint 1: Analytics Summary
**Route**: `GET /analytics/summary`
**Status**: ❌ Missing (404)

**Expected Response** (200 OK):
```json
{
  "total_projects": 5,
  "total_files_analyzed": 250,
  "average_code_maturity": 4.1,
  "api_calls_this_month": 12500
}
```

---

### Endpoints 2-4: Detailed Analytics
- Project analytics (files, metrics)
- Code metrics (by language, quality)
- Usage analytics (API calls, features)

---

## Implementation Approach

### For Each Endpoint:

1. **Check if router exists**
   ```bash
   grep -r "def.*endpoint_name\|@router.*endpoint_path" socrates-api/src/
   ```

2. **If missing, create route**:
   ```python
   @router.post("/change-password")
   async def change_password(request: RequestModel, current_user = Depends(get_current_user)):
       # Implementation
       return ResponseModel()
   ```

3. **Add validation**:
   - Input validation (required fields, types)
   - Authorization checks (user permissions)
   - Business logic validation

4. **Implement logic**:
   - Database operations
   - External service calls (GitHub, LLM, etc.)
   - Data transformations

5. **Handle errors**:
   - Return appropriate HTTP status codes
   - Provide meaningful error messages
   - Log for debugging

6. **Test**:
   ```bash
   pytest socrates-api/tests/integration/ -k "endpoint_name" -v
   ```

---

## Database Considerations

### Tables Needed/Existing
- `users_v2` ✅ (exists)
- `projects_v2` ✅ (exists)
- `github_integrations` ⏳ (may need to create)
- `knowledge_documents` ⏳ (may need to create)
- `llm_configs` ✅ (exists)
- `team_members` ⏳ (may need to create)

### Queries Needed
Review `socratic_system/database/project_db_v2.py` for existing methods:
- User queries ✅
- Project queries ✅
- LLM config queries ✅
- Document queries ⏳
- Team queries ⏳

---

## Testing Strategy

After implementing each endpoint:

1. **Run the specific failing tests**:
   ```bash
   pytest socrates-api/tests/integration/test_all_endpoints.py::TestGitHubEndpoints::test_import_from_github -v
   ```

2. **Verify no regressions**:
   ```bash
   pytest socrates-api/tests/integration/ --tb=short -q
   ```

3. **Check coverage improvement**:
   ```bash
   pytest --cov=socrates_api socrates-api/tests/integration/ -q
   ```

---

## Priority Implementation Order

**Recommended sequence**:
1. **Auth change-password** (0.5h) - Most critical
2. **LLM endpoints** (2h) - Likely simpler, existing DB tables
3. **GitHub import** (1h) - Foundation for other GitHub endpoints
4. **Knowledge list & export** (1.5h) - Core functionality
5. **Collaboration invite** (1h) - Foundation for other team endpoints
6. **Analytics summary** (1h) - Aggregation, relatively simple
7. **Remaining endpoints** (2.5h)

**Total**: ~10 hours

---

## Success Metrics

After completing all implementations:

```
Target: 336/336 tests passing (100%)
Expected: 330+ tests passing (98%+)

Breakdown:
- 278 tests currently passing
- +50+ tests from endpoint implementations
- +8 tests from bug fixes if found
= 336+ tests ✅

Coverage targets:
- Auth module: 95%+
- API endpoints: 90%+
- Overall: 85%+
```

---

## Quick Links

- **Current Progress**: EXECUTION_PROGRESS_REPORT.md
- **Test Results**: TEST_EXECUTION_REPORT.md
- **Auth Router**: socrates-api/src/socrates_api/routers/auth.py
- **Database**: socratic_system/database/project_db_v2.py
- **Test File**: socrates-api/tests/integration/test_all_endpoints.py

---

**Status**: Ready to implement
**Next Action**: Start with Priority 1 (change-password endpoint)
**Timeline**: 10 hours for all 28 endpoints
**Target**: 100% test pass rate (336/336)
