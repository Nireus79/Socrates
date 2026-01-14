# Role-Based Access Control (RBAC) Documentation

## Overview

The Socrates API implements comprehensive role-based access control (RBAC) for all project endpoints. This document describes the role hierarchy, access permissions, and how to manage team members.

## Role Hierarchy

### Three-Tier Role System

The RBAC system defines three role levels with a strict hierarchy:

| Role | Level | Description |
|------|-------|-------------|
| **Owner** | 3 | Full control of the project and all team management |
| **Editor** | 2 | Development access and collaborative features |
| **Viewer** | 1 | Read-only access to project data |

**Key Principle**: Higher-level roles inherit all permissions from lower-level roles.

---

## Role Permissions Matrix

### Owner Role (Level 3)
**Full project control - can do everything**

#### Project Management
- ✅ View project details and statistics
- ✅ Update project settings
- ✅ Delete project
- ✅ Advance to next phase
- ✅ Rollback to previous phase
- ✅ Manage project lifecycle

#### Team Management
- ✅ Add collaborators to project
- ✅ Update collaborator roles
- ✅ Remove collaborators
- ✅ View team member list
- ✅ Manage project access levels

#### Content & Analysis
- ✅ View all project data (notes, knowledge, files)
- ✅ Create/edit notes
- ✅ Create/edit knowledge base
- ✅ Create/manage project files
- ✅ Run code analysis
- ✅ Run tests
- ✅ Generate reports
- ✅ Access analytics

#### GitHub Integration
- ✅ Import projects from GitHub
- ✅ Sync changes with repository
- ✅ Pull/push code changes

#### Code Generation
- ✅ Generate and improve code
- ✅ Auto-fix issues

---

### Editor Role (Level 2)
**Development access - modify project content**

#### Project Management
- ✅ View project details and statistics
- ✅ View project phases and status
- ❌ Update project settings (owner only)
- ❌ Delete project (owner only)
- ❌ Advance/rollback phases (owner only)

#### Team Management
- ❌ Add/remove collaborators (owner only)
- ❌ Update collaborator roles (owner only)
- ✅ View team member list

#### Content & Analysis
- ✅ View all project data
- ✅ Create/edit notes
- ✅ Create/edit knowledge base
- ✅ Create/manage project files
- ✅ Run code analysis
- ✅ Run tests
- ✅ Generate reports
- ✅ Access analytics

#### GitHub Integration
- ✅ Import projects from GitHub
- ✅ Sync changes with repository
- ✅ Pull/push code changes

#### Code Generation
- ✅ Generate and improve code
- ✅ Auto-fix issues

#### Chat & Collaboration
- ✅ Resolve spec conflicts
- ✅ Answer project questions
- ✅ Access chat features

---

### Viewer Role (Level 1)
**Read-only access - view project data only**

#### Project Management
- ✅ View project details and statistics
- ✅ View project phases and status
- ❌ Update project settings (owner only)
- ❌ Delete project (owner only)
- ❌ Advance/rollback phases (owner only)

#### Team Management
- ❌ Add/remove collaborators (owner only)
- ❌ Update collaborator roles (owner only)
- ✅ View team member list

#### Content & Analysis
- ✅ View project notes (read-only)
- ✅ View knowledge base (read-only)
- ✅ View project files (read-only)
- ✅ Run code analysis (view results)
- ✅ Run tests (view results)
- ✅ Generate reports (view only)
- ✅ Access analytics (view only)
- ❌ Create/edit notes
- ❌ Create/edit knowledge base
- ❌ Create/manage files

#### GitHub Integration
- ❌ Import projects
- ❌ Sync changes
- ❌ Pull/push changes

#### Code Generation
- ❌ Generate code
- ❌ Auto-fix issues

#### Chat & Collaboration
- ❌ Resolve conflicts
- ❌ Answer questions
- ❌ Access chat features

---

## Adding and Managing Collaborators

### Add a Collaborator

**Endpoint**: `POST /projects/{project_id}/collaborators`

```bash
curl -X POST "http://localhost:8000/projects/proj_123/collaborators" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "collaborator@example.com",
    "role": "editor"
  }'
```

**Request Body**:
```json
{
  "email": "collaborator@example.com",
  "role": "viewer|editor|owner"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "status": "success",
  "message": "Collaborator added successfully",
  "data": {
    "username": "collaborator",
    "email": "collaborator@example.com",
    "role": "editor",
    "invited_at": "2026-01-14T12:00:00+00:00"
  }
}
```

### Update Collaborator Role

**Endpoint**: `PUT /projects/{project_id}/collaborators/{username}`

```bash
curl -X PUT "http://localhost:8000/projects/proj_123/collaborators/collaborator" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "viewer"
  }'
```

**Response** (200 OK):
```json
{
  "success": true,
  "status": "success",
  "message": "Collaborator role updated",
  "data": {
    "username": "collaborator",
    "role": "viewer"
  }
}
```

### List Collaborators

**Endpoint**: `GET /projects/{project_id}/collaborators`

```bash
curl -X GET "http://localhost:8000/projects/proj_123/collaborators" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "status": "success",
  "message": "Collaborators retrieved",
  "data": {
    "collaborators": [
      {
        "username": "collaborator1",
        "email": "collaborator1@example.com",
        "role": "editor",
        "invited_at": "2026-01-10T08:00:00+00:00",
        "accepted_at": "2026-01-10T08:15:00+00:00"
      },
      {
        "username": "collaborator2",
        "email": "collaborator2@example.com",
        "role": "viewer",
        "invited_at": "2026-01-14T10:00:00+00:00",
        "accepted_at": "2026-01-14T10:30:00+00:00"
      }
    ],
    "total": 2
  }
}
```

### Remove Collaborator

**Endpoint**: `DELETE /projects/{project_id}/collaborators/{username}`

```bash
curl -X DELETE "http://localhost:8000/projects/proj_123/collaborators/collaborator" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "status": "success",
  "message": "Collaborator removed successfully"
}
```

---

## Authorization Error Responses

### 403 Forbidden - Insufficient Permissions

Returned when a user lacks the required role for an endpoint.

```json
{
  "success": false,
  "status": "error",
  "message": "Access denied",
  "detail": "Insufficient permissions. Requires editor role.",
  "error_code": "INSUFFICIENT_PERMISSIONS"
}
```

**Common Causes**:
- Viewer trying to create notes (requires Editor+)
- Editor trying to delete project (requires Owner)
- Non-member trying to access project

### 404 Not Found - Project Not Found

Returned when the referenced project doesn't exist.

```json
{
  "success": false,
  "status": "error",
  "message": "Not Found",
  "detail": "Project not found",
  "error_code": "PROJECT_NOT_FOUND"
}
```

### 401 Unauthorized - Missing/Invalid Authentication

Returned when authentication token is missing or invalid.

```json
{
  "success": false,
  "status": "error",
  "message": "Unauthorized",
  "detail": "Not authenticated",
  "error_code": "NOT_AUTHENTICATED"
}
```

---

## Protected Endpoints Summary

### Analysis Endpoints (All Require Viewer+)
| Endpoint | Method | Min Role | Purpose |
|----------|--------|----------|---------|
| `/analysis/{project_id}/maturity` | POST | Viewer | Assess code maturity |
| `/analysis/test` | POST | Viewer | Run tests |
| `/analysis/structure` | POST | Viewer | Analyze project structure |
| `/analysis/review` | POST | Viewer | Get code review/statistics |
| `/analysis/fix` | POST | Viewer | Generate fixes |
| `/analysis/report/{project_id}` | GET | Viewer | Get analysis report |

### Notes Endpoints
| Endpoint | Method | Min Role | Purpose |
|----------|--------|----------|---------|
| `/projects/{project_id}/notes` | POST | Editor | Create note |
| `/projects/{project_id}/notes` | GET | Viewer | List notes |
| `/projects/{project_id}/notes/search` | POST | Viewer | Search notes |
| `/projects/{project_id}/notes/{note_id}` | DELETE | Editor | Delete note |

### Knowledge Management Endpoints
| Endpoint | Method | Min Role | Purpose |
|----------|--------|----------|---------|
| `/projects/{project_id}/knowledge` | POST | Editor | Add knowledge |
| `/projects/{project_id}/knowledge` | GET | Viewer | List knowledge |
| `/projects/{project_id}/knowledge/search` | POST | Viewer | Search knowledge |
| `/projects/{project_id}/knowledge/export` | POST | Viewer | Export knowledge |
| `/projects/{project_id}/knowledge/{doc_id}` | DELETE | Editor | Delete knowledge |

### Project Management Endpoints
| Endpoint | Method | Min Role | Purpose |
|----------|--------|----------|---------|
| `/projects/{project_id}/stats` | GET | Viewer | Get project statistics |
| `/projects/{project_id}/advance` | POST | Owner | Advance to next phase |
| `/projects/{project_id}/rollback` | POST | Owner | Rollback phase |
| `/projects/{project_id}/collaborators` | POST | Owner | Add collaborator |
| `/projects/{project_id}/collaborators` | GET | Viewer | List collaborators |
| `/projects/{project_id}/collaborators/{username}` | PUT | Owner | Update role |
| `/projects/{project_id}/collaborators/{username}` | DELETE | Owner | Remove collaborator |

### GitHub Integration Endpoints (All Require Editor+)
| Endpoint | Method | Min Role | Purpose |
|----------|--------|----------|---------|
| `/projects/{project_id}/github/import` | POST | Editor | Import from GitHub |
| `/projects/{project_id}/github/pull` | GET | Editor | Pull changes |
| `/projects/{project_id}/github/push` | POST | Editor | Push changes |
| `/projects/{project_id}/github/sync` | POST | Editor | Sync repository |

### Chat Endpoints
| Endpoint | Method | Min Role | Purpose |
|----------|--------|----------|---------|
| `/projects/{project_id}/chat/resolve-conflicts` | POST | Editor | Resolve conflicts |
| `/projects/{project_id}/chat/questions` | GET | Editor | Get next question |
| `/projects/{project_id}/chat/history` | GET | Viewer | Get chat history |

---

## Implementation Details

### Authorization Middleware

The RBAC system is implemented in `socrates_api/auth/project_access.py`:

```python
async def check_project_access(
    project_id: str,
    current_user: str,
    db: ProjectDatabase,
    min_role: str = "viewer"
) -> str:
    """
    Check if user has access to a project with minimum required role.

    Raises HTTPException(403) if access denied.
    Raises HTTPException(404) if project not found.

    Returns the user's role in the project.
    """
```

### Role Hierarchy

```python
ROLE_HIERARCHY = {
    "owner": 3,
    "editor": 2,
    "viewer": 1,
}
```

### Usage in Endpoints

All protected endpoints follow this pattern:

```python
@router.post("/{project_id}/notes")
async def add_note(
    project_id: str,
    request: NoteRequest,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    # Check project access - requires editor or better
    await check_project_access(
        project_id,
        current_user,
        db,
        min_role="editor"
    )

    # ... rest of endpoint logic
```

---

## Security Considerations

### Access Control Enforcement
1. **Authentication First**: All protected endpoints require valid JWT token
2. **Role Validation**: Role hierarchy is strictly enforced
3. **Project Membership**: User must be invited to project before accessing
4. **Audit Trail**: All access attempts are logged

### Best Practices
1. **Principle of Least Privilege**: Assign lowest necessary role
2. **Regular Audits**: Review team member access periodically
3. **Role Transitions**: Remove old roles before assigning new ones
4. **Owner Backup**: Ensure multiple owners for critical projects

---

## Migration Guide

### Existing Projects
If you have existing projects with collaborators:

1. **Existing Collaborators** are automatically assigned as **Editor** role
2. **Project Owner** remains as **Owner** role
3. **Non-Collaborators** have no access until explicitly invited

### Data Model
The system stores role information in `project.team_members`:

```python
team_members: Optional[List[TeamMemberRole]] = [
    {
        "username": "collaborator",
        "role": "editor",
        "skills": ["python", "testing"],
        "joined_at": "2026-01-14T12:00:00+00:00"
    }
]
```

---

## Troubleshooting

### "Insufficient permissions. Requires editor role"
**Solution**: Ask project owner to upgrade your role

### "Access denied to this project"
**Solution**: You haven't been added to the project yet. Contact the owner for an invitation.

### "Project not found"
**Solution**: The project ID is invalid or the project has been deleted

### Can't add a collaborator
**Solution**: You must be the project owner to add collaborators

---

## API Reference

### Authentication Header
All protected endpoints require:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

### Response Format
All API responses follow this format:
```json
{
  "success": true/false,
  "status": "success/error",
  "message": "Human readable message",
  "data": {},
  "error_code": "ERROR_CODE"
}
```

---

## Version History

- **v1.0** (2026-01-14): Initial RBAC implementation
  - Three-tier role system (Owner, Editor, Viewer)
  - Role-based access control for 42 endpoints
  - Comprehensive documentation

---

## Support

For questions or issues with RBAC:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [Permissions Matrix](#role-permissions-matrix)
3. Contact the project owner
4. Submit an issue on GitHub
