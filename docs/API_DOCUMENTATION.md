# Socratic RAG Enhanced - API Documentation

**Version:** 7.4.0
**Last Updated:** October 2024
**Audience:** Developers & Integrators

## Table of Contents

1. [Authentication](#authentication)
2. [Base URL & Headers](#base-url--headers)
3. [Projects API](#projects-api)
4. [Sessions API](#sessions-api)
5. [Code Generation API](#code-generation-api)
6. [Repositories API](#repositories-api)
7. [Documents API](#documents-api)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Code Examples](#code-examples)

---

## Authentication

### Session-Based Authentication
The API uses Flask session-based authentication with secure cookies.

### Login
```
POST /login
Content-Type: application/x-www-form-urlencoded

username=user@example.com
password=securepassword
```

**Response:**
```json
{
  "success": true,
  "user_id": "user_123",
  "username": "user@example.com",
  "message": "Successfully logged in"
}
```

### Logout
```
POST /logout
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

### CSRF Protection
All state-changing requests (POST, PUT, DELETE) require CSRF token:

```html
<!-- Get token from cookie or form -->
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

```javascript
// In AJAX requests
headers: {
  'X-CSRFToken': csrfToken
}
```

---

## Base URL & Headers

### Base URL
```
https://your-domain.com/api/
```

### Required Headers
```http
Content-Type: application/json
X-CSRFToken: <your-csrf-token>  # For state-changing operations
```

### Optional Headers
```http
X-Request-ID: <unique-request-id>  # For tracking
Accept-Language: en-US              # For localization
```

---

## Projects API

### List Projects
```
GET /projects
```

**Query Parameters:**
- `page` (int, optional) - Page number for pagination (default: 1)
- `per_page` (int, optional) - Results per page (default: 20)
- `sort` (string, optional) - Sort by: created, updated, name (default: updated)
- `order` (string, optional) - asc or desc (default: desc)

**Response:**
```json
{
  "success": true,
  "projects": [
    {
      "id": "proj_123",
      "name": "E-commerce Platform",
      "description": "Full-stack web application",
      "project_type": "web_application",
      "framework": "flask",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-10-16T14:22:00Z",
      "session_count": 5,
      "generation_count": 2
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

### Create Project
```
POST /projects
Content-Type: application/json
X-CSRFToken: <token>

{
  "name": "New Project",
  "description": "Project description",
  "project_type": "web_application",
  "framework": "flask",
  "complexity_level": "intermediate"
}
```

**Response:**
```json
{
  "success": true,
  "project_id": "proj_124",
  "message": "Project created successfully"
}
```

### Get Project Details
```
GET /projects/{project_id}
```

**Response:**
```json
{
  "success": true,
  "project": {
    "id": "proj_123",
    "name": "E-commerce Platform",
    "description": "Full-stack web application",
    "project_type": "web_application",
    "framework": "flask",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-10-16T14:22:00Z",
    "owner_id": "user_456",
    "collaborators": [
      {
        "id": "user_789",
        "email": "collaborator@example.com",
        "role": "editor"
      }
    ],
    "sessions": [],
    "generations": []
  }
}
```

### Update Project
```
PUT /projects/{project_id}
Content-Type: application/json
X-CSRFToken: <token>

{
  "name": "Updated Project Name",
  "description": "Updated description",
  "status": "archived"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Project updated successfully"
}
```

### Delete Project
```
DELETE /projects/{project_id}
X-CSRFToken: <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Project deleted successfully"
}
```

---

## Sessions API

### Create Session
```
POST /projects/{project_id}/sessions
Content-Type: application/json
X-CSRFToken: <token>

{
  "session_name": "Architecture Discussion",
  "role": "developer",
  "topic": "Microservices Architecture",
  "complexity_level": "advanced"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "sess_456",
  "message": "Session created successfully"
}
```

### Get Session
```
GET /sessions/{session_id}
```

**Response:**
```json
{
  "success": true,
  "session": {
    "id": "sess_456",
    "session_name": "Architecture Discussion",
    "project_id": "proj_123",
    "mode": "socratic",
    "role": "developer",
    "status": "active",
    "progress_percentage": 45,
    "questions_asked": 5,
    "questions_answered": 5,
    "created_at": "2024-10-16T10:00:00Z",
    "updated_at": "2024-10-16T14:30:00Z"
  }
}
```

### Send Message
```
POST /sessions/{session_id}/message
Content-Type: application/json

{
  "message": "We need to handle 10,000 concurrent users"
}
```

**Response:**
```json
{
  "success": true,
  "ai_response": "That's a significant scale. Let me ask you about your current infrastructure...",
  "progress": 50,
  "timestamp": "2024-10-16T14:31:00Z"
}
```

### Toggle Session Mode
```
POST /sessions/{session_id}/toggle-mode
Content-Type: application/json
X-CSRFToken: <token>

{
  "mode": "chat"
}
```

**Modes:** `socratic` or `chat`

**Response:**
```json
{
  "success": true,
  "mode": "chat",
  "message": "Switched to Chat Mode"
}
```

### Export Session
```
GET /sessions/{session_id}/export
```

**Response:** JSON file download
```json
{
  "export_timestamp": "2024-10-16T14:32:00Z",
  "session": { /* session data */ },
  "conversation": { /* messages */ },
  "questions": { /* Q&A */ },
  "summary": { /* statistics */ }
}
```

### Complete Session
```
POST /sessions/{session_id}/complete
Content-Type: application/json
X-CSRFToken: <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Session completed",
  "final_status": "completed"
}
```

---

## Code Generation API

### Create Generation
```
POST /projects/{project_id}/generations
Content-Type: application/json
X-CSRFToken: <token>

{
  "generation_name": "E-commerce Backend",
  "architecture_pattern": "microservices",
  "generation_type": "full_project",
  "primary_language": "python",
  "backend_framework": "fastapi",
  "frontend_framework": "react",
  "database_type": "postgresql",
  "include_authentication": true,
  "include_api_docs": true,
  "include_tests": true,
  "include_docker": true,
  "additional_features": "Payment integration, Admin panel"
}
```

**Response:**
```json
{
  "success": true,
  "generation_id": "gen_789",
  "status": "generating",
  "message": "Code generation started"
}
```

### Get Generation Progress
```
GET /api/generations/{generation_id}/progress
```

**Response:**
```json
{
  "success": true,
  "generation_id": "gen_789",
  "status": "generating",
  "progress": 65,
  "completed_files": 13,
  "total_files": 20,
  "file_count": 13,
  "generation_name": "E-commerce Backend",
  "created_at": "2024-10-16T14:00:00Z",
  "updated_at": "2024-10-16T14:15:00Z",
  "message": "Generating file 13 of 20"
}
```

### Get Generation Details
```
GET /generations/{generation_id}
```

**Response:**
```json
{
  "success": true,
  "generation": {
    "id": "gen_789",
    "project_id": "proj_123",
    "generation_name": "E-commerce Backend",
    "status": "completed",
    "progress": 100,
    "architecture_pattern": "microservices",
    "total_files": 20,
    "completed_files": 20,
    "created_at": "2024-10-16T14:00:00Z",
    "completed_at": "2024-10-16T14:20:00Z"
  }
}
```

### Get Generation File
```
GET /generations/{generation_id}/file/{file_id}
```

**Response:**
```json
{
  "success": true,
  "file": {
    "id": "file_101",
    "generation_id": "gen_789",
    "file_path": "src/app.py",
    "file_name": "app.py",
    "file_type": "python",
    "content": "from fastapi import FastAPI\n...",
    "file_size": 2048,
    "created_at": "2024-10-16T14:10:00Z"
  }
}
```

### Download Generation (ZIP)
```
GET /generations/{generation_id}/download
```

**Response:** Binary ZIP file download

---

## Repositories API

### List Repositories
```
GET /repositories
```

**Query Parameters:**
- `page` (int, optional) - Page number (default: 1)
- `per_page` (int, optional) - Results per page (default: 20)
- `status` (string, optional) - completed, in_progress, failed

**Response:**
```json
{
  "success": true,
  "repositories": [
    {
      "id": "repo_111",
      "name": "awesome-project",
      "owner": "github-user",
      "url": "https://github.com/user/awesome-project",
      "platform": "github",
      "branch": "main",
      "import_status": "completed",
      "total_files": 256,
      "total_lines": 15000,
      "languages": ["Python", "JavaScript"],
      "frameworks": ["Flask", "React"],
      "chunks_created": 450,
      "imported_at": "2024-10-16T12:00:00Z"
    }
  ],
  "total": 12,
  "page": 1
}
```

### Import Repository
```
POST /api/repositories/import
Content-Type: application/json
X-CSRFToken: <token>

{
  "repo_url": "https://github.com/user/awesome-project",
  "branch": "main",
  "project_id": "proj_123",
  "vectorize": true
}
```

**Response:**
```json
{
  "success": true,
  "repository_id": "repo_111",
  "status": "importing",
  "message": "Repository import started"
}
```

### Get Repository Details
```
GET /repositories/{repo_id}
```

**Response:**
```json
{
  "success": true,
  "repository": {
    "id": "repo_111",
    "name": "awesome-project",
    "owner": "github-user",
    "url": "https://github.com/user/awesome-project",
    "platform": "github",
    "branch": "main",
    "import_status": "completed",
    "total_files": 256,
    "total_lines": 15000,
    "languages": ["Python", "JavaScript", "HTML", "CSS"],
    "frameworks": ["Flask", "React"],
    "dependencies": ["flask", "sqlalchemy", "requests"],
    "chunks_created": 450,
    "imported_at": "2024-10-16T12:00:00Z"
  }
}
```

### Delete Repository
```
DELETE /repositories/{repo_id}
X-CSRFToken: <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Repository deleted successfully"
}
```

---

## Documents API

### Upload Document
```
POST /upload-document
Content-Type: multipart/form-data
X-CSRFToken: <token>

file: <binary-file-data>
project_id: proj_123
```

**Supported Formats:** PDF, DOCX, TXT, Markdown, Python, JavaScript, HTML, CSS

**Response:**
```json
{
  "success": true,
  "document_id": "doc_222",
  "filename": "specifications.pdf",
  "word_count": 1250,
  "chunk_count": 45,
  "processing_status": "completed",
  "vectorized": true,
  "message": "Document processed successfully"
}
```

### List Documents
```
GET /documents
```

**Query Parameters:**
- `project_id` (string, optional) - Filter by project
- `page` (int, optional) - Page number (default: 1)

**Response:**
```json
{
  "success": true,
  "documents": [
    {
      "id": "doc_222",
      "filename": "specifications.pdf",
      "project_id": "proj_123",
      "uploaded_by": "user_456",
      "word_count": 1250,
      "chunk_count": 45,
      "processing_status": "completed",
      "uploaded_at": "2024-10-16T13:00:00Z"
    }
  ],
  "total": 5
}
```

---

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "error": "Error message",
  "error_code": "INVALID_INPUT",
  "details": {
    "field": "message",
    "issue": "Required field missing"
  }
}
```

### HTTP Status Codes
| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Request processed successfully |
| 201 | Created | New resource created |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |

### Common Error Codes
- `INVALID_INPUT` - Request validation failed
- `NOT_FOUND` - Resource not found
- `UNAUTHORIZED` - Not authenticated
- `FORBIDDEN` - Access denied
- `RATE_LIMITED` - Too many requests
- `INTERNAL_ERROR` - Server error

---

## Rate Limiting

### Limits
- **Default:** 50 requests per 60 seconds
- **Per User:** Separate rate limit buckets
- **Per Endpoint:** Some endpoints have specific limits

### Rate Limit Headers
```http
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1697472000
```

### Handling Rate Limits
When you receive a 429 response:
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "error_code": "RATE_LIMITED",
  "retry_after": 60
}
```

**Best Practices:**
- Implement exponential backoff
- Cache responses when possible
- Use batch endpoints when available
- Request increased limits if needed

---

## Code Examples

### JavaScript/Node.js

```javascript
// Import a repository
const response = await fetch('https://your-domain.com/api/repositories/import', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken
  },
  body: JSON.stringify({
    repo_url: 'https://github.com/user/awesome-project',
    branch: 'main',
    vectorize: true
  })
});

const data = await response.json();
console.log('Repository ID:', data.repository_id);
```

### Python

```python
import requests
import json

# Create a session
headers = {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrf_token
}

data = {
    'session_name': 'Architecture Discussion',
    'role': 'developer'
}

response = requests.post(
    'https://your-domain.com/projects/proj_123/sessions',
    json=data,
    headers=headers,
    cookies={'session': session_cookie}
)

session_id = response.json()['session_id']
print(f"Session created: {session_id}")
```

### cURL

```bash
# Get generation progress
curl -X GET 'https://your-domain.com/api/generations/gen_789/progress' \
  -H 'Accept: application/json' \
  -b 'session=YOUR_SESSION_COOKIE'

# Response
{
  "success": true,
  "status": "generating",
  "progress": 65,
  "completed_files": 13,
  "total_files": 20
}
```

---

## Webhooks (Beta)

Webhooks notify your application of events:

```json
POST your-webhook-url

{
  "event": "generation.completed",
  "timestamp": "2024-10-16T14:20:00Z",
  "data": {
    "generation_id": "gen_789",
    "project_id": "proj_123",
    "status": "completed",
    "file_count": 20
  }
}
```

### Supported Events
- `generation.started`
- `generation.completed`
- `generation.failed`
- `repository.imported`
- `repository.import_failed`
- `session.completed`
- `document.processed`

---

## SDK & Libraries

### Official SDKs
- **Python SDK** - `pip install socratic-rag-sdk`
- **JavaScript SDK** - `npm install @socratic-rag/sdk`
- **Go SDK** - `go get github.com/socratic-rag/sdk-go`

### Community Libraries
- Ruby, PHP, Java, C#, and more available on GitHub

---

## Support

- 📧 API Support: api-support@socratic-rag.com
- 📚 OpenAPI Spec: `/api/openapi.json`
- 🐛 Report Issues: GitHub Issues
- 💡 Feedback: GitHub Discussions

For more information, see:
- User Guide: `docs/USER_GUIDE.md`
- Architecture: `docs/ARCHITECTURE.md`
- Deployment: `docs/DEPLOYMENT.md`
