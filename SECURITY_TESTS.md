# Comprehensive Security Tests - Socrates Backend

## Test Plan for Critical Vulnerabilities

All tests MUST pass before any deployment.

---

## TEST 1: Testing Mode Header Bypass (CRITICAL)

### 1.1: Free Tier User Cannot Add 2+ Team Members (Database Check)

**Objective**: Verify that free tier users cannot add multiple team members, and testing mode must use database flag.

**Setup**:
```
1. Create User A (free tier, testing_mode=false in database)
2. Create Project for User A
3. Prepare User B to invite as team member
```

**Test Steps**:
```
1. User A calls: POST /collaboration/add-member
   - Body: { username: "UserB", role: "editor" }
   - Should SUCCEED (first team member added)

2. User A calls: POST /collaboration/add-member
   - Body: { username: "UserC", role: "editor" }
   - Should FAIL with 403 (free tier limit = 1)
```

**Expected Results**:
- First member adds successfully
- Second member fails with "subscription tier" error
- Status code: 403 Forbidden
- Error message: mentions subscription or collaboration feature

**FAILURE SCENARIO** (If fixed incorrectly):
- If test passes with HTTP header x-testing-mode: enabled when database is false
  - This means the fix DIDN'T WORK
  - Header injection vulnerability still exists

**Test Code**:
```bash
# Verify database flag is used (not headers)
curl -X POST http://localhost:8000/collaboration/add-member \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "x-testing-mode: enabled" \
  -H "Content-Type: application/json" \
  -d '{"username": "UserC", "role": "editor"}'

# Expected: MUST FAIL with 403 (should not be bypassed by header)
```

---

### 1.2: Testing Mode Toggle Only Works from Database

**Objective**: Verify testing mode comes from database, not HTTP headers.

**Setup**:
```
1. Create User D (free tier, testing_mode=false in database)
2. Don't set x-testing-mode header
```

**Test Steps**:
```
1. User D calls: POST /collaboration/add-member
   - NO x-testing-mode header
   - Header would be: x-testing-mode: disabled (or missing)
   - Should FAIL (free tier limit)

2. User D calls: PUT /subscription/testing-mode?enabled=true
   - Should update database testing_mode=true

3. User D calls: POST /collaboration/add-member
   - NO x-testing-mode header (still missing)
   - Should SUCCEED (database flag now true)
```

**Expected Results**:
- Step 1 FAILS: Free tier limit enforced
- Step 2 SUCCEEDS: Mode toggled in database
- Step 3 SUCCEEDS: Mode uses database flag, not header

**Verification Query**:
```sql
SELECT username, testing_mode FROM users WHERE username='UserD';
-- Should show testing_mode=1 after step 2
```

---

## TEST 2: API Key Data Exposure (CRITICAL)

### 2.1: API Key Not Exposed in Error Messages

**Objective**: Verify API key is never echoed back in error responses.

**Setup**:
```
1. Create User E
2. Prepare invalid API keys
```

**Test Steps**:
```
1. User E calls: POST /llm-config/api-key
   - Body: { provider: "invalid_provider", api_key: "test-key-12345" }

2. Capture response error message
   - Search for "test-key-12345" in response
   - Should NOT appear anywhere
```

**Expected Results**:
- Error message: Generic message (no API key exposed)
- Example: "Failed to set API key. Please verify the provider and try again."
- API key "test-key-12345" NOT in response body
- Status code: 500 or 400

**FAILURE SCENARIO**:
```
If response contains:
- "test-key-12345" anywhere
- "Invalid key: test-key-12345"
- Raw error message echoing the key
  -> API key exposure vulnerability still exists
```

---

### 2.2: Empty API Key Validation

**Objective**: Verify empty API keys are rejected before processing.

**Test Steps**:
```
1. User E calls: POST /llm-config/api-key
   - Body: { provider: "anthropic", api_key: "" }
   - Should FAIL with 400 Bad Request

2. User E calls: POST /llm-config/api-key
   - Body: { provider: "anthropic", api_key: "   " (whitespace only) }
   - Should FAIL with 400 Bad Request
```

**Expected Results**:
- Both calls return 400
- Error message: "API key is required"
- No processing/storage attempted

---

### 2.3: Empty Provider Validation

**Objective**: Verify empty provider names are rejected.

**Test Steps**:
```
1. User E calls: POST /llm-config/api-key
   - Body: { provider: "", api_key: "sk-proj-..." }
   - Should FAIL with 400 Bad Request
```

**Expected Results**:
- Returns 400
- Error message: "Provider name is required"

---

## TEST 3: Subscription Tier Enforcement

### 3.1: Free Tier Limits Project Creation

**Objective**: Verify free tier users can only create 1 project.

**Setup**:
```
1. Create User F (free tier, testing_mode=false)
```

**Test Steps**:
```
1. User F creates Project 1
   - POST /projects
   - Should SUCCEED

2. User F creates Project 2
   - POST /projects
   - Should FAIL with 403 (tier limit)
```

**Expected Results**:
- Project 1: Created successfully
- Project 2: Fails with 403 Forbidden
- Error mentions "subscription tier" or "project limit"

---

### 3.2: Testing Mode Bypasses Project Limit

**Objective**: Verify testing mode properly bypasses project limits.

**Setup**:
```
1. User F has 1 project, testing_mode=false
```

**Test Steps**:
```
1. User F calls: PUT /subscription/testing-mode?enabled=true
   - Should update database

2. User F creates Project 2
   - Should SUCCEED (bypass activated)

3. User F creates Project 3
   - Should SUCCEED (bypass still active)
```

**Expected Results**:
- Both projects created successfully
- No tier limit errors
- Database shows testing_mode=1

---

## TEST 4: Production Environment Safety

### 4.1: Testing Mode Blocked in Production

**Objective**: Verify testing mode cannot be toggled when ENVIRONMENT=production.

**Setup**:
```
1. Set environment variable: ENVIRONMENT=production
2. Restart backend
3. Create User G (free tier)
```

**Test Steps**:
```
1. User G calls: PUT /subscription/testing-mode?enabled=true
   - Should FAIL with 403 Forbidden
   - Error: "Testing mode is not available in production environment"
```

**Expected Results**:
- Returns 403 Forbidden
- Error message clearly indicates production block
- No database changes (testing_mode remains false)

---

## TEST 5: Team Member Access Control

### 5.1: Free Tier User Cannot Add Team Member (Even With Testing Mode Header)

**Objective**: Verify header injection cannot bypass team member limits.

**Setup**:
```
1. User H (free tier, testing_mode=false)
2. NO PUT /subscription/testing-mode call made
3. Database definitely has testing_mode=false
```

**Test Steps**:
```
1. User H calls: POST /collaboration/add-member
   - Headers: x-testing-mode: enabled (INJECTED)
   - Body: { username: "UserI", role: "editor" }
   - Should FAIL with 403
```

**Expected Results**:
- Returns 403 Forbidden
- Fails because database testing_mode=false
- Header is ignored
- No team member added

**Verification**:
```sql
SELECT COUNT(*) FROM collaborators WHERE project_id='...' AND username='UserI';
-- Should return 0 (not added)
```

---

## TEST 6: Role-Based Access Control

### 6.1: Viewer Cannot Add Team Member

**Objective**: Verify non-owners cannot add team members.

**Setup**:
```
1. Create Project owned by User A
2. Add User J as 'viewer' on the project
```

**Test Steps**:
```
1. User J calls: POST /collaboration/add-member (for same project)
   - Should FAIL with 403 (not owner)
```

**Expected Results**:
- Returns 403 Forbidden
- Error mentions permissions/ownership
- No team member added

---

### 6.2: Editor Cannot Delete Project

**Objective**: Verify only owners can delete projects.

**Setup**:
```
1. Create Project owned by User A
2. Add User K as 'editor' on the project
```

**Test Steps**:
```
1. User K calls: DELETE /projects/{project_id}
   - Should FAIL with 403 (not owner)
```

**Expected Results**:
- Returns 403 Forbidden
- Error mentions ownership requirement
- Project not deleted

---

## TEST 7: Input Validation

### 7.1: XSS Prevention in Project Names

**Objective**: Verify script injection in project names is prevented.

**Setup**:
```
1. Create User L
```

**Test Steps**:
```
1. User L creates project with name: "<script>alert('xss')</script>"
   - POST /projects
   - Body: { name: "<script>alert('xss')</script>" }
```

**Expected Results**:
- Project created successfully OR
- Request fails with validation error (depends on implementation)
- If created, verify stored safely (retrieve and check content)
- HTML/JavaScript NOT executable when displayed

---

### 7.2: SQL Injection Prevention in Search

**Objective**: Verify search terms don't cause SQL injection.

**Setup**:
```
1. Create User M
2. Create project and add knowledge items
```

**Test Steps**:
```
1. User M calls: GET /knowledge/search?query='; DROP TABLE users; --
   - Should return empty results, NOT execute SQL
```

**Expected Results**:
- Returns 200 OK with empty search results
- All data intact (no tables dropped)
- No SQL errors in response

---

## TEST 8: Rate Limiting

### 8.1: Auth Endpoint Rate Limited to 5/Minute

**Objective**: Verify rate limiting on authentication endpoints.

**Setup**:
```
1. Use any client (no auth needed for registration)
```

**Test Steps**:
```
1. Call: POST /auth/register (username: test1, ...)
2. Call: POST /auth/register (username: test2, ...)
3. Call: POST /auth/register (username: test3, ...)
4. Call: POST /auth/register (username: test4, ...)
5. Call: POST /auth/register (username: test5, ...)
6. Call: POST /auth/register (username: test6, ...)
   - 6th call should FAIL with 429 Too Many Requests
```

**Expected Results**:
- Calls 1-5: Success or partial success
- Call 6: Returns 429 Too Many Requests
- Client can retry after rate limit window

---

## TEST 9: CSRF Protection

### 9.1: POST Without CSRF Token (When Enabled)

**Objective**: Verify CSRF protection works when enabled.

**Setup**:
```
1. Set CSRF protection enabled in configuration
2. Restart backend
3. Create User N
```

**Test Steps**:
```
1. User N calls: GET /auth/csrf-token
   - Retrieve CSRF token from response

2. User N calls: POST /projects (WITH token)
   - Add header: X-CSRF-Token: <token>
   - Should SUCCEED

3. User N calls: POST /projects (WITHOUT token)
   - Should FAIL with 403 (CSRF validation failed)
```

**Expected Results**:
- With token: Success
- Without token: 403 Forbidden
- Error message: CSRF-related

---

## TEST 10: Data Isolation

### 10.1: User A Cannot See User B's Projects

**Objective**: Verify users cannot access other users' projects.

**Setup**:
```
1. Create User O (creates private project)
2. Create User P (different user)
```

**Test Steps**:
```
1. User O creates Project
2. User P calls: GET /projects
   - Should NOT see User O's project

3. User P calls: GET /projects/{User_O_project_id}
   - Should FAIL with 404 or 403
```

**Expected Results**:
- GET /projects returns empty or only User P's projects
- GET /projects/{User_O_id}: Returns 404 Not Found or 403 Forbidden

---

### 10.2: User A Cannot Access User B's Knowledge Base

**Objective**: Verify knowledge base isolation.

**Setup**:
```
1. User O adds knowledge items to project
2. User P is not a team member
```

**Test Steps**:
```
1. User P calls: GET /knowledge/...?project_id={User_O_project_id}
   - Should FAIL with 403 (access denied)
```

**Expected Results**:
- Returns 403 Forbidden
- Error mentions access denied/project membership
- No knowledge items returned

---

## TEST 11: Error Handling Security

### 11.1: Stack Traces Not Exposed

**Objective**: Verify error responses don't expose implementation details.

**Setup**:
```
1. Create scenario that causes 500 error
   - E.g., invalid request that triggers unhandled exception
```

**Test Steps**:
```
1. Cause error that would normally show stack trace
2. Capture response
3. Check for:
   - File paths (/home/user/..., C:\Users\...)
   - Function names (Python tracebacks)
   - Library versions
   - Internal error messages
```

**Expected Results**:
- Generic error message: "An error occurred" or similar
- NO file paths
- NO function names
- NO implementation details
- Error logged server-side for debugging

---

### 11.2: User Enumeration Not Possible

**Objective**: Verify registration doesn't leak user existence.

**Setup**:
```
1. Known existing user: "existing_user"
2. Non-existent user: "definitely_not_exists_12345"
```

**Test Steps**:
```
1. POST /auth/register
   - username: "existing_user"
   - Capture response

2. POST /auth/register
   - username: "definitely_not_exists_12345"
   - Capture response

3. Compare error messages
```

**Expected Results**:
- Both return same generic error
- Example: "User already exists" for both OR "Invalid request" for both
- Error messages identical so user cannot enumerate

---

## EXECUTION CHECKLIST

### Pre-Testing
- [ ] Read all test cases above
- [ ] Understand each objective
- [ ] Prepare test users and projects
- [ ] Set up test environment

### Testing Phase 1: Critical Vulnerabilities
- [ ] TEST 1: Testing Mode Header Bypass
- [ ] TEST 2: API Key Exposure
- [ ] TEST 3: Subscription Enforcement
- [ ] TEST 4: Production Safety
- [ ] TEST 5: Team Member Control

### Testing Phase 2: Security
- [ ] TEST 6: RBAC
- [ ] TEST 7: Input Validation
- [ ] TEST 8: Rate Limiting
- [ ] TEST 9: CSRF
- [ ] TEST 11: Error Handling

### Testing Phase 3: Integration
- [ ] TEST 10: Data Isolation
- [ ] Cross-endpoint consistency
- [ ] State persistence

### Post-Testing
- [ ] All tests passed
- [ ] Document any failures
- [ ] Create issues for failures
- [ ] Get security review approval

---

## FAILURE RESPONSE PLAN

If ANY test fails:

1. **Document failure**:
   - Test number and name
   - Steps to reproduce
   - Actual vs expected result
   - Screenshot/log output

2. **Assess severity**:
   - CRITICAL: Do not deploy
   - HIGH: Fix before production
   - MEDIUM: Plan fix, can deploy with risk acceptance
   - LOW: Can patch later

3. **Remediate**:
   - Fix code
   - Re-run failing test
   - Re-run all related tests
   - Full test suite before deployment

4. **Approve**:
   - Security team review
   - Code review
   - Release approval

---

## PASSING CRITERIA

All tests MUST pass:
- ✅ No security vulnerabilities exploitable
- ✅ Subscription tiers properly enforced
- ✅ Data isolation working
- ✅ Authentication/authorization working
- ✅ Error messages safe
- ✅ Rate limiting working
- ✅ Input validation working

**DO NOT DEPLOY WITHOUT 100% PASSING**

---

**Test Plan Version**: 1.0
**Date**: 2026-03-27
**Status**: Ready for Execution
**Estimated Time**: 2-4 hours
