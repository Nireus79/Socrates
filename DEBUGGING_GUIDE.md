# API Runtime Issues - Debugging Guide

## Summary of Issues

The tests pass, but the running application has three critical issues:

1. **401 Unauthorized** on `/projects` endpoint
2. **500 Internal Server Error** on `/projects/{id}/collaborators`
3. **500 Internal Server Error** on `/projects/{id}/chat/question`

## What I've Done to Help Debug

I've added detailed logging to help identify the root causes:

### 1. Authentication Failures (401)
- Added logging in `auth/dependencies.py` to show IP/User-Agent when token fails
- This will help identify if it's a fingerprint mismatch or token expiry

### 2. Collaborators Endpoint (500)
- Improved error messages in `routers/collaboration.py`
- Now includes actual exception text in HTTP response
- Error logging changed from debug to error level for visibility

### 3. Chat Question Endpoint (500)
- Added orchestrator initialization error handling
- Added logging of orchestrator response to see what it returns
- Detailed error messages showing what data was received

## How to Debug

### Step 1: Start Backend with Logging

```bash
cd backend/src
export LOG_LEVEL=DEBUG
export SOCRATES_API_HOST=127.0.0.1
export SOCRATES_API_PORT=8000
python -m socrates_api.main
```

### Step 2: Reproduce Errors

1. Open frontend at http://localhost:5173
2. Try to login/create account
3. Try to access projects list
4. Try to open a project (if it loads)
5. Try to get a question (if collaborators loads)

### Step 3: Check Backend Console

Watch the backend console for detailed error messages. Look for:

#### For 401 Errors:
- "Token verification failed" messages
- IP and User-Agent values
- If the IP changes between token creation and use

#### For 500 Collaborators:
- Error message starting with "Error listing collaborators:"
- The actual exception that occurred
- What part of the code failed

#### For 500 Chat Question:
- "Failed to initialize orchestrator" messages
- "Orchestrator returned empty question" with actual result
- What the orchestrator.process_request() returned

## Likely Root Causes

### 401 Unauthorized
**Probably:** Token fingerprint mismatch due to IP change or User-Agent mismatch
- The token was created with one IP/User-Agent
- Frontend is making requests from a different context
- Fingerprint validation in `verify_access_token()` is rejecting it

**Solution options:**
1. Disable fingerprint validation for localhost (quick fix)
2. Fix frontend to maintain same IP/User-Agent context
3. Implement token refresh that updates fingerprint

### 500 Collaborators Endpoint
**Probably:** Exception in database operations or team_members field format
- `db.load_project()` might be failing
- `project.team_members` might be in unexpected format
- CollaboratorListData creation might have type mismatch

**Solution options:**
1. Check backend console error message
2. Verify project data structure in database
3. Fix type handling in collaborators endpoint

### 500 Chat Question
**Probably:** Orchestrator not returning expected data structure
- Real agent might be failing
- Fallback questions might not be working
- Result extraction failing

**Solution options:**
1. Check backend console for orchestrator error
2. Verify `get_orchestrator()` initializes correctly
3. Verify socratic_counselor agent exists and works
4. Check if orchestrator.process_request() returns correct structure

## Next Steps

1. **Run backend** with the logging improvements
2. **Reproduce errors** while watching console
3. **Share the backend console output** showing the actual error messages
4. I can then pinpoint and fix the specific issues

The logging improvements mean you should now see:
- Exact exception messages (not just generic "500 errors")
- What data structures are causing problems
- Whether orchestrator/database initialization is failing
- Why authentication is being rejected
