# Socrates API - Role-Based Access Control Matrix

**Version:** 8.0.0
**Date:** 2026-01-14
**Last Updated:** January 14, 2026

---

## Executive Summary

This document defines the comprehensive access control matrix for the Socrates API system. The system implements three primary roles with progressively restricted permissions:

- **Owner**: Full administrative control over projects and all resources
- **Editor**: Can contribute and develop, but cannot perform admin tasks
- **Viewer**: Read-only access to project data and progress

The authorization model is **owner-based with no global admin role**. Each project has a single owner (the creator), and only project owners can manage collaborators and modify project settings.

---

## Authorization Model Overview

### Role Hierarchy

```
OWNER
├── Full project control
├── User/team management
├── Settings modification
├── Resource deletion
└── Subscription-based limits

EDITOR
├── Contribute to project
├── Participate in chat/QA
├── View analytics
├── Create code/documents
└── Cannot delete/archive/manage team

VIEWER
├── Read all project data
├── View progress/analytics
├── View chat history
└── Cannot create or modify anything
```

### Key Authorization Rules

1. **Authentication**: All endpoints (except public ones) require valid JWT token
2. **Project Access**: User must be project member (owner, editor, or viewer)
3. **Role-Based Actions**: Specific actions restricted to specific roles
4. **Subscription Limits**: Enforced at creation time based on tier
5. **Testing Mode**: Can bypass subscription limits (admin override)

---

## Endpoints by Category

## 1. AUTHENTICATION & USER MANAGEMENT

### 1.1 Authentication Endpoints

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Register | POST | `/auth/register` | Allow | Allow | Allow | Public endpoint, anyone can register |
| Login | POST | `/auth/login` | Allow | Allow | Allow | Public endpoint, returns JWT token |
| Refresh Token | POST | `/auth/refresh` | Allow | Allow | Allow | Required valid JWT, returns new token |
| Logout | POST | `/auth/logout` | Allow | Allow | Allow | Invalidates session |
| Change Password | PUT | `/auth/change-password` | Allow | Allow | Allow | Own account only |

### 1.2 User Profile Endpoints

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Get Profile | GET | `/auth/me` | Allow | Allow | Allow | Returns current user info |
| Update Profile | PUT | `/auth/me` | Allow | Allow | Allow | Can update own profile only |
| Delete Account | DELETE | `/auth/me` | Allow | Allow | Allow | Permanent account deletion |
| Archive Account | POST | `/auth/me/archive` | Allow | Allow | Allow | Soft delete account |
| Restore Account | POST | `/auth/me/restore` | Allow | Allow | Allow | Restore archived account |
| Toggle Testing Mode | PUT | `/auth/me/testing-mode` | Allow | Deny | Deny | Admin feature, bypasses subscription limits |

---

## 2. PROJECT MANAGEMENT

### 2.1 Core Project Operations

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| List Projects | GET | `/projects` | Allow | Allow | Allow | Returns user's own projects |
| Create Project | POST | `/projects` | Allow | Deny | Deny | Only authenticated users, subject to subscription tier |
| Get Project | GET | `/projects/{project_id}` | Allow | Allow | Allow | Must be project member |
| Update Project | PUT | `/projects/{project_id}` | Allow | Deny | Deny | Only owner can update settings |
| Delete Project | DELETE | `/projects/{project_id}` | Allow | Deny | Deny | Permanent deletion, owner only |
| Restore Project | POST | `/projects/{project_id}/restore` | Allow | Deny | Deny | Restore archived project |

### 2.2 Project Status & Analytics

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Get Project Stats | GET | `/projects/{project_id}/stats` | Allow | Allow | Allow | High-level project statistics |
| Get Maturity | GET | `/projects/{project_id}/maturity` | Allow | Allow | Allow | Maturity score and metrics |
| Maturity Analysis | GET | `/projects/{project_id}/maturity/analysis` | Allow | Allow | Allow | Detailed maturity breakdown |
| Update Phase | PUT | `/projects/{project_id}/phase` | Allow | Deny | Deny | Only owner can change phase |
| Rollback Phase | POST | `/projects/{project_id}/phase/rollback` | Allow | Deny | Deny | Revert to previous phase |
| Get Analytics | GET | `/projects/{project_id}/analytics` | Allow | Allow | Allow | Project-level analytics |
| Get Files | GET | `/projects/{project_id}/files` | Allow | Allow | Allow | List project files |

---

## 3. PROJECT DEVELOPMENT

### 3.1 Chat & Socratic Questioning

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Create Chat Session | POST | `/projects/{project_id}/chat/sessions` | Allow | Allow | Deny | Create new session for discussion |
| List Chat Sessions | GET | `/projects/{project_id}/chat/sessions` | Allow | Allow | Allow | View all sessions in project |
| Get Chat Session | GET | `/projects/{project_id}/chat/sessions/{session_id}` | Allow | Allow | Allow | View specific session |
| Delete Chat Session | DELETE | `/projects/{project_id}/chat/sessions/{session_id}` | Allow | Deny | Deny | Only creator can delete |
| Post Chat Message | POST | `/projects/{project_id}/chat/{session_id}/message` | Allow | Allow | Deny | Contribute to discussion |
| Get Chat Messages | GET | `/projects/{project_id}/chat/{session_id}/messages` | Allow | Allow | Allow | View conversation history |
| Update Chat Message | PUT | `/projects/{project_id}/chat/sessions/{session_id}/messages/{message_id}` | Allow | Allow | Deny | Only own messages, within 15 min |
| Delete Chat Message | DELETE | `/projects/{project_id}/chat/sessions/{session_id}/messages/{message_id}` | Allow | Allow | Deny | Only own messages |
| Archive Chat Session | PUT | `/projects/{project_id}/chat/sessions/{session_id}/archive` | Allow | Allow | Deny | Archive session for reference |
| Restore Chat Session | PUT | `/projects/{project_id}/chat/sessions/{session_id}/restore` | Allow | Allow | Deny | Restore archived session |
| Get Question | GET | `/projects/{project_id}/chat/question` | Allow | Allow | Allow | Get Socratic question |
| Post Message | POST | `/projects/{project_id}/chat/message` | Allow | Allow | Deny | Contribute message |
| Get Chat History | GET | `/projects/{project_id}/chat/history` | Allow | Allow | Allow | View full chat history |
| Set Chat Mode | PUT | `/projects/{project_id}/chat/mode` | Allow | Allow | Deny | Change questioning mode |
| Get Hint | GET | `/projects/{project_id}/chat/hint` | Allow | Allow | Allow | Request hint for question |
| Clear Chat | DELETE | `/projects/{project_id}/chat/clear` | Allow | Allow | Deny | Clear chat history |
| Get Chat Summary | GET | `/projects/{project_id}/chat/summary` | Allow | Allow | Allow | Summarize discussion |
| Search Chat | POST | `/projects/{project_id}/chat/search` | Allow | Allow | Allow | Search chat content |

### 3.2 Code Generation & Development

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Generate Code | POST | `/projects/{project_id}/code/generate` | Allow | Allow | Deny | Generate code from spec |
| Validate Code | POST | `/projects/{project_id}/code/validate` | Allow | Allow | Deny | Check code syntax/quality |
| Get Code History | GET | `/projects/{project_id}/code/history` | Allow | Allow | Allow | View previous versions |
| List Languages | GET | `/projects/code/languages` | Allow | Allow | Allow | Supported programming languages |
| Refactor Code | POST | `/projects/{project_id}/code/refactor` | Allow | Allow | Deny | Improve existing code |
| Generate Docs | POST | `/projects/{project_id}/docs/generate` | Allow | Allow | Deny | Auto-generate documentation |

### 3.3 Notes & Documentation

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Create Note | POST | `/projects/{project_id}/notes` | Allow | Allow | Deny | Add project notes |
| List Notes | GET | `/projects/{project_id}/notes` | Allow | Allow | Allow | View all notes |
| Search Notes | POST | `/projects/{project_id}/notes/search` | Allow | Allow | Allow | Full-text search notes |
| Delete Note | DELETE | `/projects/{project_id}/notes/{note_id}` | Allow | Allow | Deny | Only creator can delete |

### 3.4 Skills & Workflow

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Create Skill | POST | `/projects/{project_id}/skills` | Allow | Allow | Deny | Define project skill |
| List Skills | GET | `/projects/{project_id}/skills` | Allow | Allow | Allow | View all skills |
| Get Pending Approvals | GET | `/api/v1/workflow/pending-approvals/{project_id}` | Allow | Allow | Allow | View items needing approval |
| Approve Request | POST | `/api/v1/workflow/approve` | Allow | Deny | Deny | Approve workflow item |
| Reject Request | POST | `/api/v1/workflow/reject` | Allow | Deny | Deny | Reject workflow item |
| Get Request Info | GET | `/api/v1/workflow/info/{request_id}` | Allow | Allow | Allow | View request details |

---

## 4. PROJECT ANALYTICS & MONITORING

### 4.1 Analytics Endpoints

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Get Summary | GET | `/analytics/summary` | Allow | Allow | Allow | High-level analytics summary |
| Get Project Analytics | GET | `/analytics/projects/{project_id}` | Allow | Allow | Allow | Detailed project analytics |
| Get Code Metrics | GET | `/analytics/code-metrics` | Allow | Allow | Allow | Code quality metrics |
| Get Usage Stats | GET | `/analytics/usage` | Allow | Allow | Allow | API usage statistics |
| Get Trends | GET | `/analytics/trends` | Allow | Allow | Allow | Usage trends over time |
| Get Recommendation | POST | `/analytics/recommend` | Allow | Allow | Allow | AI recommendations |
| Export Analytics | POST | `/analytics/export` | Allow | Allow | Allow | Export data as file |
| Download Report | GET | `/analytics/export/{report_filename}` | Allow | Allow | Allow | Download exported report |
| Comparative Analysis | POST | `/analytics/comparative` | Allow | Allow | Allow | Compare projects |
| Generate Report | POST | `/analytics/report` | Allow | Allow | Allow | Create custom report |
| Analyze Data | POST | `/analytics/analyze` | Allow | Allow | Allow | Analyze dataset |
| Get Dashboard | GET | `/analytics/dashboard/{project_id}` | Allow | Allow | Allow | Dashboard metrics |
| Get Breakdown | GET | `/analytics/breakdown/{project_id}` | Allow | Allow | Allow | Detailed metric breakdown |

### 4.2 Progress Tracking

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Get Progress | GET | `/projects/{project_id}/progress` | Allow | Allow | Allow | Project progress metrics |
| Get Progress Status | GET | `/projects/{project_id}/progress/status` | Allow | Allow | Allow | Current progress state |
| Get Stats | GET | `/projects/{project_id}/stats` | Allow | Allow | Allow | Project statistics |

### 4.3 Code Analysis

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Validate Code | POST | `/analysis/validate` | Allow | Allow | Allow | Validate code structure |
| Analyze Maturity | POST | `/analysis/{project_id}/maturity` | Allow | Allow | Allow | Calculate maturity score |
| Test Code | POST | `/analysis/test` | Allow | Allow | Allow | Run code tests |
| Analyze Structure | POST | `/analysis/structure` | Allow | Allow | Allow | Analyze code structure |
| Code Review | POST | `/analysis/review` | Allow | Allow | Allow | Get code review |
| Fix Issues | POST | `/analysis/fix` | Allow | Allow | Allow | Auto-fix issues |
| Get Report | GET | `/analysis/report/{project_id}` | Allow | Allow | Allow | Analysis report |

---

## 5. FILE MANAGEMENT

### 5.1 File Operations

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Get Files | GET | `/projects/{project_id}/files` | Allow | Allow | Allow | List project files |
| Upload File | POST | `/projects/{project_id}/files` | Allow | Allow | Deny | Add file to project |
| Get File | GET | `/projects/{project_id}/files/{file_id}` | Allow | Allow | Allow | Download file |
| Delete File | DELETE | `/projects/{project_id}/files/{file_id}` | Allow | Allow | Deny | Remove file |

---

## 6. COLLABORATION MANAGEMENT

### 6.1 Collaborator Management

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Add Collaborator | POST | `/projects/{project_id}/collaborators` | Allow | Deny | Deny | Invite team member, owner-only |
| List Collaborators | GET | `/projects/{project_id}/collaborators` | Allow | Allow | Allow | View team members |
| Update Role | PUT | `/projects/{project_id}/collaborators/{username}/role` | Allow | Deny | Deny | Change collaborator role |
| Remove Collaborator | DELETE | `/projects/{project_id}/collaborators/{username}` | Allow | Deny | Deny | Remove team member |

### 6.2 Presence & Activity

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Get Presence | GET | `/projects/{project_id}/presence` | Allow | Allow | Allow | See who's online |
| Create Activity | POST | `/projects/{project_id}/activities` | Allow | Allow | Allow | Log activity |
| Get Activities | GET | `/projects/{project_id}/activities` | Allow | Allow | Allow | View activity log |

### 6.3 Invitations

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Create Invitation | POST | `/projects/{project_id}/invitations` | Allow | Deny | Deny | Send invite link |
| List Invitations | GET | `/projects/{project_id}/invitations` | Allow | Allow | Allow | View pending invites |
| Accept Invitation | POST | `/collaboration/invitations/{token}/accept` | Allow | Allow | Allow | Join project via invite |
| Delete Invitation | DELETE | `/projects/{project_id}/invitations/{invitation_id}` | Allow | Deny | Deny | Cancel invitation |

---

## 7. KNOWLEDGE MANAGEMENT

### 7.1 Knowledge Base

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| List Documents | GET | `/knowledge/documents` | Allow | Allow | Allow | View KB documents |
| Get All Documents | GET | `/knowledge/all` | Allow | Allow | Allow | Full KB listing |
| Get Document | GET | `/knowledge/documents/{document_id}` | Allow | Allow | Allow | View document content |
| Download Document | GET | `/knowledge/documents/{document_id}/download` | Allow | Allow | Allow | Download as file |
| Import File | POST | `/knowledge/import/file` | Allow | Allow | Deny | Upload KB file |
| Import URL | POST | `/knowledge/import/url` | Allow | Allow | Deny | Add KB from URL |
| Import Text | POST | `/knowledge/import/text` | Allow | Allow | Deny | Add KB from text |
| Search Knowledge | GET | `/knowledge/search` | Allow | Allow | Allow | Full-text search KB |
| Delete Document | DELETE | `/knowledge/documents/{document_id}` | Allow | Allow | Deny | Remove KB entry |
| Bulk Delete | POST | `/knowledge/documents/bulk-delete` | Allow | Allow | Deny | Delete multiple entries |
| Bulk Import | POST | `/knowledge/documents/bulk-import` | Allow | Allow | Deny | Import multiple files |
| Get Analytics | GET | `/knowledge/documents/{document_id}/analytics` | Allow | Allow | Allow | Document usage stats |
| Add Entry | POST | `/knowledge/entries` | Allow | Allow | Deny | Create KB entry |

### 7.2 Project Knowledge

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Create Document | POST | `/projects/{project_id}/knowledge/documents` | Allow | Allow | Deny | Create project KB doc |
| Add Knowledge | POST | `/projects/{project_id}/knowledge/add` | Allow | Allow | Deny | Add to project KB |
| List Knowledge | GET | `/projects/{project_id}/knowledge/list` | Allow | Allow | Allow | View project KB |
| Search Knowledge | POST | `/projects/{project_id}/knowledge/search` | Allow | Allow | Allow | Search project KB |
| Remember Knowledge | POST | `/projects/{project_id}/knowledge/remember` | Allow | Allow | Deny | Save to memory |
| Delete Knowledge | DELETE | `/projects/{project_id}/knowledge/{knowledge_id}` | Allow | Allow | Deny | Remove from KB |
| Export Knowledge | POST | `/projects/{project_id}/knowledge/export` | Allow | Allow | Allow | Export KB |
| Import Knowledge | POST | `/projects/{project_id}/knowledge/import` | Allow | Allow | Deny | Import KB |

---

## 8. GITHUB INTEGRATION

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Import Repository | POST | `/github/import` | Allow | Allow | Deny | Import GitHub repo |
| Pull Changes | POST | `/github/projects/{project_id}/pull` | Allow | Allow | Deny | Pull GitHub changes |
| Push Changes | POST | `/github/projects/{project_id}/push` | Allow | Allow | Deny | Push to GitHub |
| Sync Repo | POST | `/github/projects/{project_id}/sync` | Allow | Allow | Deny | Sync with GitHub |
| Get Repo Status | GET | `/github/projects/{project_id}/status` | Allow | Allow | Allow | Check sync status |
| Pull Global | GET | `/github/pull` | Allow | Allow | Deny | Pull all repos |
| Push Global | POST | `/github/push` | Allow | Allow | Deny | Push all repos |
| Get Global Status | GET | `/github/status` | Allow | Allow | Allow | Global sync status |
| Disconnect GitHub | POST | `/github/disconnect` | Allow | Deny | Deny | Remove GitHub integration |

---

## 9. FINALIZATION & DELIVERY

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Generate Final Code | POST | `/projects/{project_id}/finalize/generate` | Allow | Allow | Deny | Generate final version |
| Generate Final Docs | POST | `/projects/{project_id}/finalize/docs` | Allow | Allow | Deny | Generate documentation |

---

## 10. SYSTEM & MONITORING

### 10.1 System Information

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Get Help | GET | `/system/help` | Allow | Allow | Allow | Get system help |
| Get Info | GET | `/system/info` | Allow | Allow | Allow | System information |
| Get Status | GET | `/system/status` | Allow | Allow | Allow | System status |
| Post Logs | POST | `/system/logs` | Allow | Allow | Allow | Send logs |
| Post Context | POST | `/system/context` | Allow | Allow | Allow | Send context |
| Toggle Debug | POST | `/system/debug/toggle` | Allow | Deny | Deny | Debug mode toggle |
| Get Debug Status | GET | `/system/debug/status` | Allow | Deny | Deny | Check debug mode |

### 10.2 Health & Metrics

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Health Check | GET | `/health` | Allow | Allow | Allow | Basic health check |
| Detailed Health | GET | `/health/detailed` | Allow | Allow | Allow | Comprehensive health |
| Metrics | GET | `/metrics` | Allow | Allow | Allow | Prometheus metrics |
| Metrics Summary | GET | `/metrics/summary` | Allow | Allow | Allow | Metric summary |
| Query Metrics | GET | `/metrics/queries` | Allow | Allow | Allow | Database query metrics |
| Slow Queries | GET | `/metrics/queries/slow` | Allow | Allow | Allow | Slow query list |
| Slowest Queries | GET | `/metrics/queries/slowest` | Allow | Allow | Allow | Slowest queries |
| Database Health | GET | `/database/health` | Allow | Allow | Allow | DB health status |
| Database Details | GET | `/database/health/detailed` | Allow | Allow | Allow | Detailed DB health |
| Database Stats | GET | `/database/stats` | Allow | Allow | Allow | DB statistics |
| Reset Stats | POST | `/database/stats/reset` | Allow | Deny | Deny | Reset statistics |
| Liveness Probe | GET | `/database/live` | Allow | Allow | Allow | Kubernetes liveness |
| Readiness Probe | GET | `/database/ready` | Allow | Allow | Allow | Kubernetes readiness |

### 10.3 Events & Streaming

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Get Event History | GET | `/api/events/history` | Allow | Allow | Allow | View past events |
| Stream Events | GET | `/api/events/stream` | Allow | Allow | Allow | WebSocket event stream |

---

## 11. LLM CONFIGURATION

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| List Providers | GET | `/llm/providers` | Allow | Allow | Allow | Available LLM providers |
| Get Config | GET | `/llm/config` | Allow | Allow | Allow | Current LLM config |
| Set Default Provider | PUT | `/llm/default-provider` | Allow | Allow | Allow | Change default LLM |
| Set Model | PUT | `/llm/model` | Allow | Allow | Allow | Change model |
| Set API Key | POST | `/llm/api-key` | Allow | Allow | Allow | Configure API key |
| Remove API Key | DELETE | `/llm/api-key/{provider}` | Allow | Allow | Allow | Remove API key |
| Set Auth Method | PUT | `/llm/auth-method` | Allow | Allow | Allow | Change auth method |
| Get Models | GET | `/llm/models/{provider}` | Allow | Allow | Allow | List provider models |
| Usage Stats | GET | `/llm/usage-stats` | Allow | Allow | Allow | LLM usage tracking |

---

## 12. QUERY & SEARCH

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Explain Query | POST | `/query/explain` | Allow | Allow | Allow | Get explanation |
| Search | POST | `/query/search` | Allow | Allow | Allow | Search content |
| Similar Concepts | GET | `/query/similar/{concept}` | Allow | Allow | Allow | Find similar items |

---

## 13. NATURAL LANGUAGE UNDERSTANDING

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Interpret Command | POST | `/nlu/interpret` | Allow | Allow | Allow | Parse user command |
| Get Commands | GET | `/nlu/commands` | Allow | Allow | Allow | List available commands |
| Get Suggestions | GET | `/nlu/suggestions` | Allow | Allow | Allow | Get command suggestions |

---

## 14. FREE SESSION (UNAUTHENTICATED)

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Ask Question | POST | `/free_session/ask` | Deny | Deny | Deny | Public demo session |
| List Sessions | GET | `/free_session/sessions` | Deny | Deny | Deny | Anonymous sessions |
| Get Session | GET | `/free_session/sessions/{session_id}` | Deny | Deny | Deny | View demo session |
| Delete Session | DELETE | `/free_session/sessions/{session_id}` | Deny | Deny | Deny | Clear session |
| Get Recommendations | GET | `/free_session/recommendations` | Deny | Deny | Deny | Demo recommendations |

---

## 15. SUBSCRIPTION MANAGEMENT

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Get Status | GET | `/subscription/status` | Allow | Allow | Allow | Current subscription |
| List Plans | GET | `/subscription/plans` | Allow | Allow | Allow | Available plans |
| Upgrade Plan | POST | `/subscription/upgrade` | Allow | Deny | Deny | Change to higher tier |
| Downgrade Plan | POST | `/subscription/downgrade` | Allow | Deny | Deny | Change to lower tier |
| Toggle Testing Mode | PUT | `/subscription/testing-mode` | Allow | Deny | Deny | Enable testing mode |

---

## 16. SECURITY ENDPOINTS

| Endpoint | Method | Path | Owner | Editor | Viewer | Notes |
|----------|--------|------|-------|--------|--------|-------|
| Change Password | POST | `/security/password/change` | Allow | Allow | Allow | Update password |
| Setup 2FA | POST | `/security/2fa/setup` | Allow | Allow | Allow | Enable two-factor |
| Verify 2FA | POST | `/security/2fa/verify` | Allow | Allow | Allow | Verify 2FA code |
| Disable 2FA | POST | `/security/2fa/disable` | Allow | Allow | Allow | Disable two-factor |
| Get Sessions | GET | `/security/sessions` | Allow | Allow | Allow | List active sessions |
| Delete Session | DELETE | `/security/sessions/{session_id}` | Allow | Allow | Allow | Logout from device |
| Revoke All Sessions | POST | `/security/sessions/revoke-all` | Allow | Allow | Allow | Logout all devices |

---

## Role Permission Summary Table

| Action Category | Owner | Editor | Viewer |
|-----------------|-------|--------|--------|
| **Authentication** | - | - | - |
| Register/Login/Profile | Allow | Allow | Allow |
| Testing Mode | Allow | Deny | Deny |
| **Project Management** | - | - | - |
| Create Projects | Allow | Deny | Deny |
| Update Projects | Allow | Deny | Deny |
| Delete/Archive Projects | Allow | Deny | Deny |
| View Projects | Allow | Allow | Allow |
| **Development Work** | - | - | - |
| Chat/Questions | Allow | Allow | Deny |
| Code Generation | Allow | Allow | Deny |
| Create Notes | Allow | Allow | Deny |
| **Analytics & Monitoring** | - | - | - |
| View Analytics | Allow | Allow | Allow |
| View Progress | Allow | Allow | Allow |
| **Collaboration** | - | - | - |
| Add/Remove Collaborators | Allow | Deny | Deny |
| Manage Roles | Allow | Deny | Deny |
| Send Invitations | Allow | Deny | Deny |
| View Team | Allow | Allow | Allow |
| **Knowledge Management** | - | - | - |
| Create KB Entries | Allow | Allow | Deny |
| Search KB | Allow | Allow | Allow |
| Delete KB Entries | Allow | Allow | Deny |
| **System Admin** | - | - | - |
| Manage Subscription | Allow | Deny | Deny |
| Debug/Logs | Allow | Deny | Deny |
| Reset Statistics | Allow | Deny | Deny |

---

## Authorization Enforcement Points

### JWT Token Validation
- All protected endpoints require valid Bearer token in Authorization header
- Token validation performed by `get_current_user()` dependency
- Invalid/expired tokens return 401 Unauthorized

### Project Membership Check
- User must be added as collaborator (owner/editor/viewer) to access project
- Checked via database collaborators table
- Missing membership returns 403 Forbidden

### Role-Based Authorization
- Specific endpoints enforce role requirements
- Role checked against collaborator record for project
- Insufficient role returns 403 Forbidden

### Subscription Tier Limits
- Project creation limited by subscription tier
- Free tier: 3 projects
- Pro tier: 25 projects
- Enterprise: unlimited
- Testing mode bypasses limits (admin feature)

### Resource Ownership
- Chat messages, notes, etc. can only be modified by creator
- Deletion restricted to owner
- Edited within time window (15 minutes for messages)

---

## Implementation Guide

### Key Components in Codebase

1. **Auth Module** (`/socrates_api/auth/`)
   - `dependencies.py`: JWT validation and user extraction
   - `jwt_handler.py`: Token creation and verification
   - `password.py`: Password hashing and validation

2. **Routers** (`/socrates_api/routers/`)
   - Each router defines endpoints for specific feature
   - Role enforcement via `require_project_role()` decorator
   - Subscription checking via `SubscriptionChecker` middleware

3. **Models** (`/socratic_system/models/`)
   - User model with subscription_tier field
   - ProjectContext with collaborators list
   - CollaboratorRole enum (OWNER, EDITOR, VIEWER)

### Decorator Functions

```python
# Authentication (required for all protected endpoints)
@Depends(get_current_user)

# Role-based access (for project-specific endpoints)
@Depends(require_project_role("owner"))
@Depends(require_project_role("editor"))

# Optional authentication (for endpoints supporting both auth and anon)
@Depends(get_current_user_optional)
```

### Error Responses

- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: User lacks permission for action
- **404 Not Found**: Resource not found or user not member
- **429 Too Many Requests**: Rate limit exceeded

---

## Compliance & Security

### Data Protection
- User data encrypted at rest and in transit
- Passwords hashed using bcrypt with salt
- Tokens signed with HS256 algorithm
- Session timeout after inactivity

### Audit Trail
- All modifications logged with user ID and timestamp
- Activities tracked for collaboration features
- Admin access logged separately

### Rate Limiting
- API requests rate-limited by user/IP
- Default: 100 requests per minute
- Higher limits for authenticated users

---

## Future Enhancements

1. **Custom Roles**: Allow projects to define custom roles with granular permissions
2. **Time-Based Access**: Grant temporary access for specific time periods
3. **IP Whitelisting**: Restrict access by IP range
4. **API Key Management**: Service-to-service authentication
5. **Audit Logging**: Comprehensive change tracking with export capability
6. **SAML/OAuth2**: Enterprise SSO integration
7. **API Token Scopes**: Fine-grained permission scopes for API tokens

---

## Document Information

**Version:** 1.0
**Status:** Active
**Last Updated:** 2026-01-14
**Last Reviewed By:** System Architecture Team
**Next Review Date:** 2026-04-14

For questions, issues, or change requests, please open an issue in the repository referencing this document.
