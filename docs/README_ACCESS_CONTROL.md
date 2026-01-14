# Socrates API - Role-Based Access Control Documentation

This directory contains comprehensive documentation for the Socrates API's role-based access control system.

## Quick Start

**Start here:** [`ACL_SUMMARY.txt`](./ACL_SUMMARY.txt) - Quick reference guide with key information

**Complete reference:** [`ACCESS_CONTROL_MATRIX.md`](./ACCESS_CONTROL_MATRIX.md) - Detailed matrix with all 186 endpoints

## What's Included

### 1. ACCESS_CONTROL_MATRIX.md (30KB, 577 lines)
The authoritative reference for all API endpoints and their access control rules.

**Contents:**
- Executive summary of the three-tier role system
- 186 endpoints organized by 16 feature categories
- Detailed access control matrix for each endpoint
- Role permission summary tables
- Authorization enforcement rules
- Implementation guidance
- Compliance and audit information

**Who should read this:** Developers implementing API security, security reviewers, API documentation maintainers

### 2. ACL_SUMMARY.txt (16KB, 490 lines)
Executive summary and quick reference guide.

**Contents:**
- High-level overview of the role system
- Summary statistics on endpoints
- Key access control rules
- Common implementation patterns
- Quick decision tree for authorization
- Scenario examples
- Testing and maintenance strategies

**Who should read this:** Project managers, security leads, new developers

## The Three Roles

### Owner
- Full administrative control over projects
- Can create, update, and delete projects
- Manages team members and their roles
- Modifies project settings and phases
- Creates, updates, and deletes all content
- Full access to analytics and admin functions

### Editor
- Participates in project development
- Can contribute code, notes, and knowledge entries
- Can view all analytics and progress
- Cannot create new projects
- Cannot delete anything or manage team
- Cannot modify project settings

### Viewer
- Read-only access to all project data
- Can view analytics, progress, and chat history
- Can view team members and knowledge base
- Cannot create, modify, or delete anything

## Key Statistics

| Metric | Count |
|--------|-------|
| Total Endpoints | 186 |
| Owner-Only Endpoints | 33 |
| Editor+ Endpoints | 52 |
| All Authenticated Users | 101 |
| Public Endpoints | 8 |

## By Feature Area

- Authentication (6)
- Project Management (13)
- Chat & Socratic QA (18)
- Code Generation (6)
- Notes & Documentation (4)
- Skills & Workflow (6)
- Analytics (13)
- File Management (4)
- Collaboration (11)
- Knowledge Management (21)
- GitHub Integration (9)
- Finalization (2)
- System & Monitoring (21)
- LLM Configuration (9)
- Query & Search (3)
- Natural Language (3)
- Plus 4 more categories

## Implementation Guide

### For New Endpoints

1. Add `@Depends(get_current_user)` to require authentication
2. If project-specific:
   - Add `@Depends(require_project_role("owner"|"editor"|"viewer"))`
   - Verify project membership
3. If resource-specific:
   - Check ownership or admin role
4. For creation: Check subscription tier
5. For updates: Check time window (if applicable)
6. Document role requirements
7. Add tests for 401/403/404 responses

### Authorization Decorators

```python
# Authentication required
@Depends(get_current_user)

# Role-based access
@Depends(require_project_role("owner"))
@Depends(require_project_role("editor"))

# Optional authentication
@Depends(get_current_user_optional)
```

## Error Responses

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Missing/invalid authentication | Get valid JWT token |
| 403 | Insufficient permissions | Verify user role/membership |
| 404 | Resource not found | Check project_id and membership |
| 429 | Rate limit exceeded | Implement backoff |

## Subscription Tiers

- **Free:** 3 projects, standard rate limit
- **Pro:** 25 projects, higher rate limit
- **Enterprise:** Unlimited, custom features

Testing mode (admin only) bypasses all limits.

## Quick Reference: Who Can Do What?

### Create Operations
- Owner: Yes
- Editor: No (except content like notes, code, KB)
- Viewer: No

### Read Operations
- Owner: Yes
- Editor: Yes
- Viewer: Yes

### Update Operations
- Owner: Yes (all)
- Editor: Yes (own content, within time window)
- Viewer: No

### Delete Operations
- Owner: Yes (all)
- Editor: No
- Viewer: No

## Authorization Flow

```
1. Extract & validate JWT token
   ├─> Invalid → 401 Unauthorized
   └─> Valid → Continue

2. Check project membership
   ├─> Not member → 403 Forbidden
   └─> Is member → Continue

3. Check role requirement
   ├─> Insufficient role → 403 Forbidden
   └─> Has role → Continue

4. Check resource ownership (if applicable)
   ├─> Not owner → 403 Forbidden
   └─> Is owner → Continue

5. Check subscription limits (if creation)
   ├─> Limit exceeded → 403 Forbidden
   └─> Within limit → Continue

6. Check time window (if modification)
   ├─> Window expired → 403 Forbidden
   └─> Within window → Allow
```

## Where to Find Code

### Authentication Module
- Location: `/socrates_api/auth/`
- Files:
  - `dependencies.py`: JWT validation
  - `jwt_handler.py`: Token management
  - `password.py`: Password hashing

### API Routers
- Location: `/socrates_api/routers/`
- Key files:
  - `projects.py`: Project management (13 endpoints)
  - `collaboration.py`: Team management (11 endpoints)
  - `projects_chat.py`: Chat and messaging (18 endpoints)
  - `code_generation.py`: Code operations (6 endpoints)
  - `knowledge_management.py`: Knowledge base (21 endpoints)
  - `analytics.py`: Analytics (13 endpoints)

### Database Models
- Location: `/socratic_system/models/`
- User model with subscription tier
- ProjectContext with collaborators
- CollaboratorRole enums

## Testing

Every endpoint should have tests for:
- 401 (missing/invalid auth)
- 403 (insufficient permissions)
- 404 (resource not found)
- 200/201/204 (success cases)

Example for each role:
- Owner: Full access test
- Editor: Partial access test
- Viewer: Read-only test

## Compliance

This implementation supports:
- RBAC (Role-Based Access Control)
- Principle of Least Privilege
- Audit and accountability
- Data protection regulations

All modifications are logged with:
- User ID
- Timestamp
- Operation type
- Resource affected

## Maintenance

- **Review frequency:** Quarterly
- **Update trigger:** New endpoints or role changes
- **Approval:** Security team review
- **Documentation:** Keep synchronized with code

## Glossary

- **JWT:** JSON Web Token for authentication
- **RBAC:** Role-Based Access Control
- **Collaborator:** User with access to a project
- **Project Member:** Same as collaborator
- **Owner:** Project creator with full control
- **Subscription Tier:** Free/Pro/Enterprise subscription level
- **Testing Mode:** Admin feature to bypass limits

## Related Documentation

- API Endpoint Documentation: `socrates-api/API_DOCUMENTATION.md`
- Database Schema: `socratic_system/models/`
- Authentication Details: `socrates-api/src/socrates_api/auth/`

## Contact

For questions about access control:
1. Review the detailed matrix: `ACCESS_CONTROL_MATRIX.md`
2. Check implementation in `/socrates_api/routers/`
3. Review auth module in `/socrates_api/auth/`
4. Open GitHub issue for specific questions

---

**Version:** 1.0  
**Last Updated:** January 14, 2026  
**Next Review:** April 14, 2026
