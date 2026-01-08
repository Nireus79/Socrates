# Socrates API Documentation

## Overview

The Socrates API provides endpoints for managing software development projects with AI-powered Socratic method guidance. This document covers all available endpoints, authentication, subscription tiers, and response formats.

**Base URL:** `http://localhost:8008` (development) or `https://api.socrates.dev` (production)

---

## Authentication

### JWT Bearer Token

All protected endpoints require a JWT bearer token in the `Authorization` header.

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  http://localhost:8008/projects
```

### Getting Tokens

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `201 Created`
```json
{
  "user": {
    "username": "john_doe",
    "email": "john@example.com",
    "subscription_tier": "free",
    "subscription_status": "active",
    "created_at": "2026-01-08T19:00:00Z"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "user": {...},
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

## API Response Format

All endpoints return a standardized response format:

```json
{
  "success": true|false,
  "status": "success|created|deleted|error|pending",
  "data": {...},
  "message": "Optional message",
  "error_code": "Optional error code",
  "timestamp": "2026-01-08T19:00:00Z"
}
```

### Response Status Values

- `success` - Successful GET/LIST operation
- `created` - Resource successfully created (POST)
- `deleted` - Resource successfully deleted (DELETE)
- `error` - Operation failed
- `pending` - Operation is pending completion

---

## Projects

### Create Project

```http
POST /projects
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "name": "My Web App",
  "description": "A full-stack web application",
  "project_type": "general"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "created",
  "data": {
    "project_id": "proj_abc123...",
    "name": "My Web App",
    "description": "A full-stack web application",
    "phase": "discovery",
    "owner": "john_doe",
    "created_at": "2026-01-08T19:00:00Z",
    "updated_at": "2026-01-08T19:00:00Z"
  },
  "message": "Project created successfully"
}
```

**Subscription Requirements:**
- Free: 1 project max
- Pro: 10 projects max
- Enterprise: Unlimited

### List Projects

```http
GET /projects
Authorization: Bearer <TOKEN>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "success",
  "data": [
    {
      "project_id": "proj_abc123...",
      "name": "My Web App",
      "phase": "discovery",
      "created_at": "2026-01-08T19:00:00Z"
    },
    ...
  ]
}
```

### Get Project

```http
GET /projects/{project_id}
Authorization: Bearer <TOKEN>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "success",
  "data": {
    "project_id": "proj_abc123...",
    "name": "My Web App",
    "description": "A full-stack web application",
    "phase": "discovery",
    "owner": "john_doe",
    "overall_maturity": 0.45,
    "created_at": "2026-01-08T19:00:00Z"
  }
}
```

### Update Project

```http
PUT /projects/{project_id}
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "name": "Updated Project Name",
  "description": "Updated description"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "success",
  "data": {...},
  "message": "Project updated successfully"
}
```

### Delete Project

```http
DELETE /projects/{project_id}
Authorization: Bearer <TOKEN>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "deleted",
  "message": "Project deleted successfully"
}
```

---

## Chat & Questions

### Get Next Socratic Question

```http
GET /projects/{project_id}/chat/question
Authorization: Bearer <TOKEN>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "success",
  "data": {
    "question": "What are the main requirements for your application?",
    "phase": "discovery"
  }
}
```

### Send Chat Message

```http
POST /projects/{project_id}/chat/message
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "message": "The app needs user authentication and a dashboard"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "success",
  "data": {
    "message": {
      "id": "msg_xyz789...",
      "role": "assistant",
      "content": "Great! User authentication is crucial...",
      "timestamp": "2026-01-08T19:00:00Z"
    }
  }
}
```

### Get Chat History

```http
GET /projects/{project_id}/chat/history?limit=50
Authorization: Bearer <TOKEN>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "success",
  "data": {
    "project_id": "proj_abc123...",
    "messages": [...],
    "mode": "socratic",
    "total": 12
  }
}
```

### Switch Chat Mode

```http
PUT /projects/{project_id}/chat/mode
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "mode": "direct"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "success",
  "data": {
    "mode": "direct"
  }
}
```

---

## Notes

### Create Note

```http
POST /projects/{project_id}/notes
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "title": "Architecture Notes",
  "content": "Consider using microservices for scalability"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "status": "created",
  "data": {
    "note_id": "note_def456...",
    "title": "Architecture Notes",
    "content": "Consider using microservices for scalability",
    "created_at": "2026-01-08T19:00:00Z"
  }
}
```

### List Notes

```http
GET /projects/{project_id}/notes
Authorization: Bearer <TOKEN>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "success",
  "data": [
    {
      "note_id": "note_def456...",
      "title": "Architecture Notes",
      "created_at": "2026-01-08T19:00:00Z"
    }
  ]
}
```

---

## Collaboration

### Add Collaborator

```http
POST /projects/{project_id}/collaboration/add
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "user_id": "jane_doe",
  "role": "editor"
}
```

**Subscription Requirements:**
- Free: Collaboration disabled
- Pro: Up to 5 team members
- Enterprise: Unlimited team members

**Response:** `201 Created`
```json
{
  "success": true,
  "status": "created",
  "data": {
    "collaborator_id": "jane_doe",
    "role": "editor",
    "added_at": "2026-01-08T19:00:00Z"
  }
}
```

### List Collaborators

```http
GET /projects/{project_id}/collaboration
Authorization: Bearer <TOKEN>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "success",
  "data": [
    {
      "user_id": "jane_doe",
      "role": "editor",
      "added_at": "2026-01-08T19:00:00Z"
    }
  ]
}
```

---

## Code Generation

### Generate Code

```http
POST /projects/{project_id}/code/generate
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "requirements": "Create a login page with form validation",
  "language": "python"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "created",
  "data": {
    "generation_id": "gen_ghi012...",
    "code": "def validate_login(username, password):\n    # Validation logic\n    pass",
    "language": "python",
    "generated_at": "2026-01-08T19:00:00Z"
  }
}
```

### Get Code History

```http
GET /projects/{project_id}/code/history?limit=20&offset=0
Authorization: Bearer <TOKEN>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "status": "success",
  "data": {
    "project_id": "proj_abc123...",
    "generations": [...],
    "total": 5
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "status": "error",
  "message": "Invalid request parameters",
  "error_code": "INVALID_REQUEST"
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "status": "error",
  "message": "Missing or invalid authentication credentials",
  "error_code": "AUTHENTICATION_REQUIRED"
}
```

### 403 Forbidden
```json
{
  "success": false,
  "status": "error",
  "message": "Collaboration feature requires 'pro' or 'enterprise' subscription",
  "error_code": "SUBSCRIPTION_REQUIRED"
}
```

### 404 Not Found
```json
{
  "success": false,
  "status": "error",
  "message": "Project not found",
  "error_code": "NOT_FOUND"
}
```

### 422 Unprocessable Entity
```json
{
  "success": false,
  "status": "error",
  "message": "Validation error: Field 'name' is required",
  "error_code": "VALIDATION_ERROR"
}
```

### 429 Too Many Requests
```json
{
  "success": false,
  "status": "error",
  "message": "Rate limit exceeded. Max 5 requests per minute",
  "error_code": "RATE_LIMITED"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "status": "error",
  "message": "Internal server error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Subscription Tiers

### Free Tier
- 1 project
- 1 team member (solo)
- Basic chat features
- Code generation
- All features available (feature-gated by quotas)
- **Restrictions:** No collaboration, limited to solo work

### Pro Tier
- 10 projects
- 5 team members
- Team collaboration
- Code generation
- Advanced analytics
- Multi-LLM support
- Priority support

### Enterprise Tier
- Unlimited projects
- Unlimited team members
- Full collaboration features
- Code generation
- Advanced analytics
- Multi-LLM support
- Dedicated support
- Custom integrations

---

## Rate Limiting

Rate limits are applied per user:
- Auth endpoints: 5 requests/minute
- Standard endpoints: 100 requests/minute
- Chat endpoints: 50 requests/minute

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

---

## Pagination

List endpoints support pagination with query parameters:

```
GET /projects?limit=20&offset=0
```

Parameters:
- `limit`: Number of items to return (default: 20, max: 100)
- `offset`: Number of items to skip (default: 0)

**Response includes pagination info:**
```json
{
  "success": true,
  "status": "success",
  "data": [...],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 150,
    "has_more": true
  }
}
```

---

## Webhooks

Socrates API can send webhooks for important events. Configure webhooks in your account settings.

### Webhook Events

- `project.created` - Project created
- `project.updated` - Project updated
- `project.deleted` - Project deleted
- `code.generated` - Code generation completed
- `collaboration.added` - Collaborator added
- `collaboration.removed` - Collaborator removed

### Webhook Payload

```json
{
  "event": "project.created",
  "timestamp": "2026-01-08T19:00:00Z",
  "data": {
    "project_id": "proj_abc123...",
    "name": "My Web App"
  }
}
```

---

## SDKs and Libraries

### Python
```bash
pip install socrates-sdk
```

```python
from socrates_sdk import SocratesClient

client = SocratesClient(api_key="your-api-key")
projects = client.projects.list()
```

### JavaScript/TypeScript
```bash
npm install @socrates/sdk
```

```javascript
import { SocratesClient } from '@socrates/sdk';

const client = new SocratesClient({ apiKey: 'your-api-key' });
const projects = await client.projects.list();
```

---

## Support & Contact

- **Email:** api-support@socrates.dev
- **Documentation:** https://docs.socrates.dev
- **GitHub Issues:** https://github.com/socrates/api/issues
- **Status Page:** https://status.socrates.dev
