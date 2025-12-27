# Socrates Authorization Architecture

## Overview

The Socrates system uses **OWNER-BASED AUTHORIZATION**, not global admin roles. This is a decentralized model designed for collaborative project development.

## Key Design Decision

**There is NO global admin role in the system.**

- ❌ No `is_admin` field in the User model
- ❌ No global admin users
- ✅ Owner-based project control
- ✅ Collaborative team roles within projects
- ✅ Per-project authorization

## Authorization Model

### Global Level: No Admins

At the system level:
- All users are created equal
- No user can have elevated privileges across the entire system
- No global admin checks exist

### Project Level: Owner-Based Control

Each project has an **OWNER** (the user who created it):

| Operation | Owner | Editor | Viewer |
|-----------|-------|--------|--------|
| View project | ✅ | ✅ | ✅ |
| Edit project content | ✅ | ✅ | ❌ |
| Update settings | ✅ | ❌ | ❌ |
| Manage collaborators | ✅ | ❌ | ❌ |
| Delete project | ✅ | ❌ | ❌ |
| Archive/restore | ✅ | ❌ | ❌ |

### Team Level: Role-Based Contributions

Within projects, team members have roles describing their contribution:

| Role | Purpose |
|------|---------|
| **lead** | Overall vision, strategic goals, resource allocation |
| **creator** | Implementing deliverables, core outputs |
| **specialist** | Domain expertise, technical depth |
| **analyst** | Research, analysis, data interpretation |
| **coordinator** | Timelines, schedules, process management |

These are descriptive roles, not permission-based.

## Testing Mode

**Testing mode is NOT an admin-only feature.**

### Design Rationale

Testing mode allows users to bypass monetization restrictions during development/testing:

```python
# Available to ANY authenticated user
PUT /auth/me/testing-mode?enabled=true
```

Why? Because:
1. Users should be able to fully test the system without admin status
2. Developers and testers register as regular users, not admins
3. Testing mode is a per-user feature, not system-wide
4. Aligns with owner-based authorization model (decentralized)

### When Testing Mode Is Enabled

All subscription checks are bypassed:
- ❌ Project limits ignored
- ❌ Team member limits ignored
- ❌ Feature flags ignored
- ❌ Usage quotas not enforced
- ❌ Cost tracking disabled

## Files Implementing This Architecture

### Backend (Python)

- **`socratic_system/models/user.py`** - User model (no is_admin field)
- **`socratic_system/models/role.py`** - Team member roles definition
- **`socrates-api/src/socrates_api/routers/projects.py`** - Owner-based access control (11 checkpoints)
- **`socrates-api/src/socrates_api/routers/collaboration.py`** - Collaboration role management
- **`socrates-api/src/socrates_api/routers/auth.py`** - Testing mode endpoint (any user)
- **`socrates-api/src/socrates_api/routers/subscription.py`** - Testing mode info endpoint

### Frontend (TypeScript)

- **`socrates-frontend/src/types/models.ts`** - User and Collaborator types
- **`socrates-frontend/src/stores/collaborationStore.ts`** - Collaboration state
- **`socrates-frontend/src/api/collaboration.ts`** - Collaboration API client

## Implementation Details

### Owner Checks (projects.py)

Every project management endpoint checks:

```python
if project.owner != current_user:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only project owner can..."
    )
```

This pattern appears in:
1. Delete project (line 263)
2. Update project (line 324)
3. Get project details (line 390)
4. Update project (line 453)
5. List collaborators (line 515)
6. Add collaborators (line 580)
7. Archive project (line 643)
8. Restore project (line 714)
9. Update team roles (line 816)

### Testing Mode (auth.py)

```python
# No is_admin check needed
# Any authenticated user can toggle for their own account
user.testing_mode = enabled
db.save_user(user)
```

## Benefits of This Design

1. **Decentralized**: No central admin bottleneck
2. **Scalable**: Each user manages their own projects
3. **Fair**: All users have equal standing at registration
4. **Collaborative**: Teams work together within projects
5. **Simple**: No complex permission hierarchies

## Extending the Authorization Model

### To Add New Global Permissions

❌ Don't add an `is_admin` field

✅ Instead:
1. Create a new system-level resource (e.g., Organization)
2. Use owner-based control on that resource
3. Add owner checks where needed

### To Add New Project Roles

✅ Add to the `TeamMemberRole` enum in `socratic_system/models/role.py`

Example:
```python
# Add to role.py
class TeamMemberRole:
    LEAD = "lead"
    CREATOR = "creator"
    REVIEWER = "reviewer"  # NEW
```

Then use in collaboration management.

## Testing This Architecture

### Test that testing mode works for any user:

```bash
# Register as regular user
POST /auth/register

# Enable testing mode (no admin needed)
PUT /auth/me/testing-mode?enabled=true

# Should work!
```

### Test that only owners can manage projects:

```bash
# User A creates project
POST /projects (as user_a)

# User B tries to delete it
DELETE /projects/{id} (as user_b)

# Should return 403 Forbidden
```

### Test that collaborators have limited access:

```bash
# User A adds User B as "editor"
POST /projects/{id}/collaborators (as user_a)

# User B tries to add collaborator
POST /projects/{id}/collaborators (as user_b)

# Should return 403 Forbidden
```

## Migration Path (If Admin Needed Later)

If in the future you need a global admin role:

1. Add `is_admin: bool = False` to User model
2. Create admin-only endpoints as needed
3. Add admin checks ONLY where necessary
4. Keep owner-based project control unchanged
5. Document which endpoints require admin vs owner

But for now, this decentralized model is cleaner and more aligned with collaborative development.

## Summary

| Aspect | Status | Details |
|--------|--------|---------|
| Global admins | ❌ Not implemented | System is decentralized |
| `is_admin` field | ❌ Doesn't exist | No user-level admin field |
| Project owners | ✅ Implemented | User who created project controls it |
| Testing mode | ✅ Any user | Not admin-only, bypasses monetization |
| Collaboration roles | ✅ Per-project | Owner, Editor, Viewer within projects |
| Team roles | ✅ Per-project | Lead, Creator, Specialist, Analyst, Coordinator |

