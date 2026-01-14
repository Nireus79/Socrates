# Database Migration Guide - RBAC Role Assignments

## Overview

This guide explains how role data is stored in the database and how to verify that collaborators have been properly assigned roles.

---

## Data Structure

### ProjectContext Model

Roles are stored in the `team_members` field of each project:

```python
@dataclass
class ProjectContext:
    # ... other fields ...
    team_members: Optional[List[TeamMemberRole]] = None
```

### TeamMemberRole Model

```python
@dataclass
class TeamMemberRole:
    username: str              # Username of team member
    role: str                  # "owner", "editor", or "viewer"
    skills: List[str]          # Domain-specific skills
    joined_at: datetime        # When member joined
```

### Example Project Data

```python
{
    "project_id": "proj_123",
    "name": "My Project",
    "owner": "john_doe",
    "team_members": [
        {
            "username": "john_doe",
            "role": "owner",
            "skills": ["python", "testing"],
            "joined_at": "2026-01-10T08:00:00+00:00"
        },
        {
            "username": "jane_editor",
            "role": "editor",
            "skills": ["python", "documentation"],
            "joined_at": "2026-01-12T10:30:00+00:00"
        },
        {
            "username": "bob_viewer",
            "role": "viewer",
            "skills": [],
            "joined_at": "2026-01-14T14:00:00+00:00"
        }
    ]
}
```

---

## Database Schema

### projects Table

| Column | Type | Description |
|--------|------|-------------|
| project_id | TEXT PRIMARY KEY | Unique project identifier |
| project_data | JSON | Full project serialization including team_members |
| owner | TEXT | Project owner username |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

### team_members Storage

The `team_members` array is stored within the `project_data` JSON column:

```sql
-- Extract team members for a project
SELECT json_extract(project_data, '$.team_members') as team_members
FROM projects
WHERE project_id = 'proj_123';
```

---

## Migration Status

### Current State

✅ **Automatic Migration**

The system automatically migrates legacy data:

1. **Legacy `collaborators` field** → Converted to **`team_members`** on first access
2. **Default role assignment** → All existing collaborators become **"editor"**
3. **Project owner** → Automatically assigned **"owner"** role

### Migration Code

Located in `socratic_system/models/project.py`:

```python
def _initialize_team_members(self):
    """Migrate legacy collaborators to team_members with default roles"""
    if not self.team_members and self.collaborators:
        self.team_members = [
            TeamMemberRole(
                username=collaborator,
                role="editor",  # Default role for migrated users
                skills=[],
                joined_at=datetime.now(timezone.utc)
            )
            for collaborator in self.collaborators
        ]
```

### Backward Compatibility

- ✅ Old `project.collaborators` list still supported
- ✅ Auto-converts on first access
- ✅ No breaking changes to database
- ✅ Seamless transition for existing users

---

## Verification Steps

### 1. Check Project Team Members

**Via API**:
```bash
curl -X GET "http://localhost:8000/projects/proj_123/collaborators" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "collaborators": [
      {
        "username": "jane_editor",
        "role": "editor",
        "invited_at": "2026-01-12T10:30:00+00:00"
      }
    ]
  }
}
```

### 2. Verify Role Assignments

**Check in Database** (SQLite):
```sql
-- View all projects with their team members
SELECT
  project_id,
  owner,
  json_array_length(json_extract(project_data, '$.team_members')) as member_count,
  json_extract(project_data, '$.team_members') as team_info
FROM projects;

-- View specific project's team
SELECT
  json_extract(team, '$.username') as username,
  json_extract(team, '$.role') as role,
  json_extract(team, '$.joined_at') as joined_at
FROM projects,
  json_each(json_extract(project_data, '$.team_members')) as team
WHERE project_id = 'proj_123';
```

### 3. Test Role Permissions

**Test as Viewer** (should fail to create notes):
```bash
curl -X POST "http://localhost:8000/projects/proj_123/notes" \
  -H "Authorization: Bearer VIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test note", "title": "Test"}'

# Expected: 403 Forbidden
```

**Test as Editor** (should succeed):
```bash
curl -X POST "http://localhost:8000/projects/proj_123/notes" \
  -H "Authorization: Bearer EDITOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test note", "title": "Test"}'

# Expected: 201 Created or 200 OK
```

**Test as Non-member** (should fail):
```bash
curl -X GET "http://localhost:8000/projects/proj_123/stats" \
  -H "Authorization: Bearer NONMEMBER_TOKEN"

# Expected: 403 Forbidden
```

---

## Migration Checklist

### Pre-Migration
- [ ] Backup database
- [ ] Document current collaborator lists
- [ ] Identify projects with many collaborators
- [ ] Notify users about upcoming changes

### During Migration
- [ ] Deploy updated API code
- [ ] Monitor database for errors
- [ ] Check error logs for issues
- [ ] Test role permissions with sample users

### Post-Migration
- [ ] Verify team members appear in API responses
- [ ] Test all role levels (owner, editor, viewer)
- [ ] Check collaborator management works
- [ ] Review audit logs
- [ ] Get user feedback

### Rollback Plan
If issues occur:
1. Revert to previous API version
2. System will use legacy `collaborators` field
3. No data loss occurs
4. Investigate issue and retry migration

---

## Role Assignment Examples

### Add a New Editor

```bash
curl -X POST "http://localhost:8000/projects/proj_123/collaborators" \
  -H "Authorization: Bearer OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "neweditor@example.com",
    "role": "editor"
  }'
```

### Change Role from Viewer to Editor

```bash
curl -X PUT "http://localhost:8000/projects/proj_123/collaborators/bob_viewer" \
  -H "Authorization: Bearer OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "editor"
  }'
```

### Remove a Collaborator

```bash
curl -X DELETE "http://localhost:8000/projects/proj_123/collaborators/old_member" \
  -H "Authorization: Bearer OWNER_TOKEN"
```

---

## Troubleshooting

### Issue: "Collaborators not showing in API"

**Cause**: Project hasn't been migrated yet
**Solution**:
1. Load the project (which triggers migration)
2. Check if `team_members` now populated
3. Try API call again

### Issue: "User has no role but is in collaborators list"

**Cause**: Legacy data not yet migrated
**Solution**:
1. Explicitly add user with role via API
2. Or wait for automatic migration on next project load
3. Check that user appears in team_members

### Issue: "Can't access project despite being collaborator"

**Cause**: Role not properly assigned
**Solution**:
1. Verify via API that role is set
2. Check if token is valid
3. Ensure role level matches endpoint requirements
4. Check project actually contains this user in team_members

### Issue: "Owner not showing in team members list"

**Cause**: Owner is stored separately in `owner` field
**Solution**:
1. This is normal - owner is stored in `project.owner`
2. When checking permissions, owner is automatically treated as "owner" role
3. Owner doesn't need to be in `team_members` list

---

## Performance Considerations

### Database Query Performance
- ✅ Team members loaded with project (single query)
- ✅ No N+1 queries for role checking
- ✅ Role validation is O(n) where n = team size (typically <50)

### Caching Strategy
- Project data cached at request level
- No database calls repeated in single request
- Team members list cached with project

### Optimization Tips
1. Limit team size to <100 members per project
2. Archive old projects to reduce query load
3. Use read replicas for analytics queries
4. Index by `project_id` for fast lookups

---

## Data Consistency Checks

### SQL Queries to Verify Data Integrity

```sql
-- Check for projects missing owner
SELECT project_id FROM projects WHERE owner IS NULL;

-- Check for team members with invalid roles
SELECT
  project_id,
  json_extract(team, '$.username') as username,
  json_extract(team, '$.role') as role
FROM projects,
  json_each(json_extract(project_data, '$.team_members')) as team
WHERE json_extract(team, '$.role') NOT IN ('owner', 'editor', 'viewer');

-- Check for duplicate team members
SELECT
  project_id,
  json_extract(team, '$.username') as username,
  COUNT(*) as count
FROM projects,
  json_each(json_extract(project_data, '$.team_members')) as team
GROUP BY project_id, username
HAVING COUNT(*) > 1;

-- Check team member count by role
SELECT
  project_id,
  json_extract(team, '$.role') as role,
  COUNT(*) as count
FROM projects,
  json_each(json_extract(project_data, '$.team_members')) as team
GROUP BY project_id, role
ORDER BY project_id;
```

---

## Monitoring and Logging

### Key Metrics to Monitor

1. **403 Forbidden Errors**: Spike indicates authorization issues
2. **Team Member Updates**: API calls to add/modify collaborators
3. **Role Distribution**: How many users at each level
4. **Access Denied by Role**: Which roles are most restricted

### Logging Points

Every authorization check logs:
- Project ID
- User attempting access
- User's role
- Required minimum role
- Allow/deny decision

Example log:
```
2026-01-14 14:23:45 INFO Authorization check: proj_123, user=jane_editor, user_role=editor, min_role=viewer, ALLOWED
2026-01-14 14:24:10 WARN Authorization check: proj_123, user=bob_viewer, user_role=viewer, min_role=editor, DENIED
```

---

## Support

For database-related questions:
1. Check SQL queries in this guide
2. Verify data with verification steps
3. Consult RBAC_DOCUMENTATION.md
4. Check application logs for errors

---

**Last Updated**: 2026-01-14
**RBAC Version**: 1.0
**Database Version**: SQLite 3.40+
