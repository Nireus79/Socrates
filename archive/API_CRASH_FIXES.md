# API Crash & 422 Error Fixes

## Issue Summary
The backend was crashing with no logs when users clicked on projects or tried to perform actions like archiving/deleting projects. The frontend received 422 (Unprocessable Entity) errors from various API endpoints.

## Root Causes Identified

### 1. **Null Request Bodies** (Frontend)
Multiple frontend API calls were passing `null` as the request body instead of an empty object `{}`:
- `projects.ts`: `advancePhase()` - passing null to PUT `/projects/{id}/phase`
- `chat.ts`: `switchMode()` - passing null to PUT `/projects/{id}/chat/mode`
- `collaboration.ts`: `addCollaborator()` and `updateCollaboratorRole()` - passing null to POST/PUT requests

**Why this matters**: When axios sends `null` as the request body, it can cause validation failures in Pydantic, resulting in 422 errors.

### 2. **Missing Request Body Model** (Backend)
The `/projects/{project_id}` PUT endpoint didn't have a proper request body model:
- Parameters were defined as function arguments with default `= None`
- FastAPI was interpreting these as optional query parameters instead of body fields
- Frontend was sending data in the request body, causing a mismatch

**Impact**: FastAPI validation would fail because it expected query parameters but received body data.

### 3. **Implicit Query Parameter Binding** (Backend)
The `advance_phase` endpoint had an implicit query parameter without explicit `Query()` decorator:
```python
async def advance_phase(
    project_id: str,
    new_phase: str,  # ← Missing Query() binding!
    ...
)
```

**Impact**: FastAPI couldn't properly bind the `new_phase` query parameter, causing validation errors.

## Fixes Applied

### Frontend Fixes (TypeScript)

1. **projects.ts** - Fixed `advancePhase()`:
```typescript
// Before:
return apiClient.put<Project>(`/projects/${projectId}/phase`, null, {
  params: { new_phase: newPhase },
});

// After:
return apiClient.put<Project>(`/projects/${projectId}/phase`, {}, {
  params: { new_phase: newPhase },
});
```

2. **chat.ts** - Fixed `switchMode()`:
```typescript
// Before:
return apiClient.put<{ mode: string }>(`/projects/${projectId}/chat/mode`, null, {
  params: { mode },
});

// After:
return apiClient.put<{ mode: string }>(`/projects/${projectId}/chat/mode`, {}, {
  params: { mode },
});
```

3. **collaboration.ts** - Fixed `addCollaborator()` and `updateCollaboratorRole()`:
```typescript
// Before:
return apiClient.post<{ collaborator: Collaborator }>(
  `/projects/${projectId}/collaborators`,
  null,  // ← Problem
  { params: { username, role } }
);

// After:
return apiClient.post<{ collaborator: Collaborator }>(
  `/projects/${projectId}/collaborators`,
  {},  // ← Fixed
  { params: { username, role } }
);
```

4. **projects.ts** - Added owner field to `createProject()`:
```typescript
async createProject(request: CreateProjectRequest): Promise<Project> {
  const data = {
    ...request,
    owner: request.owner || localStorage.getItem('username') || 'anonymous',
  };
  return apiClient.post<Project>('/projects', data);
}
```

### Backend Fixes (Python)

1. **models.py** - Created `UpdateProjectRequest` model:
```python
class UpdateProjectRequest(BaseModel):
    """Request body for updating a project"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    phase: Optional[str] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Project Name",
                "phase": "implementation",
            }
        }
```

2. **projects.py** - Updated `update_project()` endpoint:
```python
# Before:
async def update_project(
    project_id: str,
    name: Optional[str] = None,
    phase: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):

# After:
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    # Use request.name and request.phase instead
```

3. **projects.py** - Fixed `advance_phase()` parameter binding:
```python
# Before:
async def advance_phase(
    project_id: str,
    new_phase: str,  # ← Implicit parameter
    ...
):

# After:
from fastapi import Query

async def advance_phase(
    project_id: str,
    new_phase: str = Query(..., description="New phase"),
    ...
):
```

## Testing Recommendations

1. **Test project operations**:
   - Create a new project
   - Click on a project to view details
   - Archive a project
   - Restore an archived project
   - Update project name/phase

2. **Test chat operations**:
   - Switch between Socratic and Direct chat modes
   - Send chat messages

3. **Test collaboration**:
   - Add collaborators to a project
   - Update collaborator roles
   - Remove collaborators

4. **Monitor logs**:
   - Check backend logs for any new errors
   - Frontend console should show no 422 errors
   - Check that authentication tokens are properly injected

## Expected Outcomes

✅ No more 422 Unprocessable Entity errors
✅ Backend no longer crashes when accessing projects
✅ All CRUD operations work properly
✅ Authentication is properly handled
✅ Request/response validation passes

## Files Modified
- `socrates-api/src/socrates_api/models.py` - Added UpdateProjectRequest
- `socrates-api/src/socrates_api/routers/projects.py` - Fixed endpoints
- `socrates-frontend/src/api/projects.ts` - Fixed requests
- `socrates-frontend/src/api/chat.ts` - Fixed requests
- `socrates-frontend/src/api/collaboration.ts` - Fixed requests
