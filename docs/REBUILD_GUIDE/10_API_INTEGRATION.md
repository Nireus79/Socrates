# API INTEGRATION
## Complete FastAPI Endpoint Specifications

---

## API OVERVIEW

**Base URL:** `http://localhost:8000/api`
**Authentication:** JWT Bearer token in Authorization header
**Response Format:** JSON
**Error Format:** Standard error responses with status codes

```
Authorization: Bearer <token>
Content-Type: application/json
```

---

## AUTHENTICATION ENDPOINTS

### POST /auth/register

**Description:** Register new user

**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "username": "johndoe",
      "email": "john@example.com",
      "status": "active",
      "createdAt": "2025-10-18T10:30:00Z"
    },
    "token": "eyJhbGc..."
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

**Errors:**
- 400: Username/email already exists
- 422: Validation error (password too weak, invalid email)

---

### POST /auth/login

**Description:** Authenticate user and get token

**Request:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "username": "johndoe",
      "email": "john@example.com"
    },
    "token": "eyJhbGc...",
    "expiresIn": 86400
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

**Errors:**
- 401: Invalid credentials
- 429: Too many login attempts

---

### GET /auth/me

**Description:** Get current user profile
**Auth:** Required ✓

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "username": "johndoe",
    "email": "john@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "status": "active",
    "createdAt": "2025-10-18T10:30:00Z"
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### POST /auth/logout

**Description:** Logout user (invalidate token)
**Auth:** Required ✓

**Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully",
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### POST /auth/refresh

**Description:** Refresh access token using refresh token
**Auth:** Required ✓

**Response (200):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGc...",
    "expiresIn": 86400
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

## PROJECTS ENDPOINTS

### GET /projects

**Description:** List user's projects with filtering
**Auth:** Required ✓

**Query Parameters:**
```
page=1              (optional, default 1)
limit=10            (optional, default 10, max 100)
status=active       (optional: active, archived, deleted)
phase=design        (optional: planning, design, development, testing, deployment, completed)
search=api          (optional: search in name/description)
sort=created_at     (optional: created_at, updated_at, name)
order=desc          (optional: asc, desc)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "proj_123",
        "ownerId": "user_123",
        "name": "My API Project",
        "description": "RESTful API for e-commerce",
        "phase": "development",
        "status": "active",
        "techStack": "React, Node, PostgreSQL",
        "createdAt": "2025-10-18T10:30:00Z",
        "updatedAt": "2025-10-18T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 23,
      "pages": 3
    }
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### POST /projects

**Description:** Create new project
**Auth:** Required ✓

**Request:**
```json
{
  "name": "My API Project",
  "description": "Building a RESTful API",
  "techStack": "React, Node, PostgreSQL"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "proj_123",
    "ownerId": "user_123",
    "name": "My API Project",
    "phase": "planning",
    "status": "active",
    "createdAt": "2025-10-18T10:30:00Z"
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

**Errors:**
- 400: Project name required
- 409: Project already exists

---

### GET /projects/{projectId}

**Description:** Get project details
**Auth:** Required ✓
**Authorization:** Project owner or collaborator

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "proj_123",
    "ownerId": "user_123",
    "name": "My API Project",
    "description": "...",
    "phase": "development",
    "status": "active",
    "techStack": "React, Node, PostgreSQL",
    "collaborators": [
      {
        "userId": "user_456",
        "username": "janedoe",
        "role": "editor",
        "joinedAt": "2025-10-18T10:30:00Z"
      }
    ],
    "createdAt": "2025-10-18T10:30:00Z",
    "updatedAt": "2025-10-18T10:30:00Z"
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### PUT /projects/{projectId}

**Description:** Update project
**Auth:** Required ✓
**Authorization:** Project owner only

**Request:**
```json
{
  "name": "Updated Project Name",
  "description": "New description",
  "phase": "testing",
  "status": "active"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "proj_123",
    "name": "Updated Project Name",
    "phase": "testing",
    "updatedAt": "2025-10-18T10:35:00Z"
  },
  "timestamp": "2025-10-18T10:35:00Z"
}
```

---

### DELETE /projects/{projectId}

**Description:** Delete project (soft delete to archive)
**Auth:** Required ✓
**Authorization:** Project owner only

**Response (200):**
```json
{
  "success": true,
  "message": "Project deleted",
  "timestamp": "2025-10-18T10:35:00Z"
}
```

---

## SESSIONS ENDPOINTS

### GET /projects/{projectId}/sessions

**Description:** List sessions for a project
**Auth:** Required ✓

**Query Parameters:**
```
page=1          (optional)
limit=10        (optional)
type=socratic   (optional: socratic, chat, code_review)
status=active   (optional: active, completed, archived)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "session_123",
        "projectId": "proj_123",
        "type": "socratic",
        "status": "active",
        "title": "API Design Discussion",
        "createdAt": "2025-10-18T10:30:00Z"
      }
    ],
    "pagination": { "page": 1, "limit": 10, "total": 5 }
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### POST /projects/{projectId}/sessions

**Description:** Create new session
**Auth:** Required ✓

**Request:**
```json
{
  "type": "socratic",
  "title": "API Design Discussion"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "session_123",
    "projectId": "proj_123",
    "type": "socratic",
    "status": "active",
    "title": "API Design Discussion",
    "createdAt": "2025-10-18T10:30:00Z"
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### GET /sessions/{sessionId}/messages

**Description:** Get all messages in a session
**Auth:** Required ✓

**Query Parameters:**
```
page=1          (optional)
limit=50        (optional)
sort=created_at (optional)
order=asc       (optional)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "msg_123",
        "sessionId": "session_123",
        "role": "user",
        "content": "What patterns should I use for the API?",
        "createdAt": "2025-10-18T10:30:00Z"
      },
      {
        "id": "msg_124",
        "sessionId": "session_123",
        "role": "agent",
        "agentId": "socratic",
        "content": "Great question! Consider REST patterns...",
        "createdAt": "2025-10-18T10:30:05Z"
      }
    ],
    "pagination": { "page": 1, "limit": 50, "total": 24 }
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### POST /sessions/{sessionId}/messages

**Description:** Send message to session
**Auth:** Required ✓

**Request:**
```json
{
  "content": "What patterns should I use for the API?"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "userMessage": {
      "id": "msg_123",
      "sessionId": "session_123",
      "role": "user",
      "content": "What patterns should I use for the API?",
      "createdAt": "2025-10-18T10:30:00Z"
    },
    "agentResponse": {
      "id": "msg_124",
      "sessionId": "session_123",
      "role": "agent",
      "agentId": "socratic",
      "content": "Great question! Consider REST patterns...",
      "createdAt": "2025-10-18T10:30:05Z"
    }
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

**Errors:**
- 400: Message content required
- 404: Session not found

---

### POST /sessions/{sessionId}/toggle-mode

**Description:** Toggle session mode (Socratic ↔ Chat)
**Auth:** Required ✓

**Response (200):**
```json
{
  "success": true,
  "data": {
    "sessionId": "session_123",
    "oldType": "socratic",
    "newType": "chat"
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

## AGENTS ENDPOINTS

### POST /agents/route

**Description:** Route request to specific agent
**Auth:** Required ✓

**Request:**
```json
{
  "agentId": "code",
  "action": "generate_code",
  "data": {
    "requirements": "Create a REST API endpoint for user registration",
    "projectId": "proj_123"
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "agentId": "code",
    "action": "generate_code",
    "result": {
      "code": "...",
      "explanation": "...",
      "suggestions": [...]
    }
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

**Errors:**
- 400: Invalid agent_id or action
- 503: Agent not available

---

### GET /agents/status

**Description:** Get status of all agents
**Auth:** Required ✓

**Response (200):**
```json
{
  "success": true,
  "data": {
    "agents": {
      "user": "ready",
      "project": "ready",
      "socratic": "ready",
      "code": "ready",
      "context": "ready",
      "document": "ready",
      "services": "ready",
      "monitor": "ready",
      "optimizer": "ready"
    },
    "timestamp": "2025-10-18T10:30:00Z"
  }
}
```

---

### GET /agents/{agentId}/capabilities

**Description:** Get capabilities of specific agent
**Auth:** Required ✓

**Response (200):**
```json
{
  "success": true,
  "data": {
    "agentId": "code",
    "capabilities": [
      "generate_code",
      "refactor_code",
      "debug_code",
      "fix_bugs",
      "analyze_code_quality",
      "optimize_performance"
    ],
    "status": "ready"
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

## CODE ENDPOINTS

### POST /code/generate

**Description:** Generate code using CodeGeneratorAgent
**Auth:** Required ✓

**Request:**
```json
{
  "requirements": "Create user registration endpoint",
  "language": "python",
  "projectId": "proj_123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "code": "...",
    "explanation": "...",
    "suggestions": [...]
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### POST /code/refactor

**Description:** Refactor code
**Auth:** Required ✓

**Request:**
```json
{
  "code": "def process_data(x, y):\n    z = x+y\n    return z",
  "refactoringType": "readability",
  "projectId": "proj_123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "originalCode": "...",
    "refactoredCode": "...",
    "diff": "...",
    "suggestions": ["Added type hints", "Improved naming"],
    "qualityScore": 8
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### POST /code/debug

**Description:** Debug code and find issues
**Auth:** Required ✓

**Request:**
```json
{
  "code": "...",
  "language": "python",
  "projectId": "proj_123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "issues": [
      {
        "severity": "error",
        "line": 5,
        "description": "Bare except clause",
        "suggestion": "Catch specific exceptions"
      }
    ],
    "summary": "Found 3 issues (1 error, 2 warnings)"
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### POST /code/fix-bugs

**Description:** Auto-fix identified bugs
**Auth:** Required ✓

**Request:**
```json
{
  "code": "...",
  "language": "python",
  "projectId": "proj_123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "originalCode": "...",
    "fixedCode": "...",
    "fixes": [
      {
        "type": "security",
        "description": "Fixed SQL injection vulnerability",
        "line": 12
      }
    ]
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

## INSTRUCTIONS ENDPOINTS

### GET /instructions

**Description:** Get user's instructions
**Auth:** Required ✓

**Query Parameters:**
```
projectId=proj_123  (optional: get project-specific + global)
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "instr_123",
      "userId": "user_123",
      "projectId": null,
      "rules": "- Always include tests\n- Use TypeScript\n- Document breaking changes",
      "categories": {
        "quality": ["Always include tests"],
        "custom": ["Use TypeScript", "Document breaking changes"]
      },
      "isActive": true,
      "createdAt": "2025-10-18T10:30:00Z"
    }
  ],
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### POST /instructions

**Description:** Create new instruction set
**Auth:** Required ✓

**Request:**
```json
{
  "rules": "- Always include tests\n- Use TypeScript\n- Document breaking changes",
  "projectId": "proj_123"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "instr_123",
    "userId": "user_123",
    "projectId": "proj_123",
    "rules": "...",
    "categories": {...},
    "isActive": true,
    "createdAt": "2025-10-18T10:30:00Z"
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

### PUT /instructions/{instructionId}

**Description:** Update instruction set
**Auth:** Required ✓

**Request:**
```json
{
  "rules": "- Updated rules here",
  "isActive": true
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "instr_123",
    "rules": "- Updated rules here",
    "updatedAt": "2025-10-18T10:35:00Z"
  },
  "timestamp": "2025-10-18T10:35:00Z"
}
```

---

### DELETE /instructions/{instructionId}

**Description:** Delete instruction set
**Auth:** Required ✓

**Response (200):**
```json
{
  "success": true,
  "message": "Instruction deleted",
  "timestamp": "2025-10-18T10:35:00Z"
}
```

---

## HEALTH & MONITORING

### GET /health

**Description:** Check API health
**Auth:** Not required

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-18T10:30:00Z",
  "uptime": 3600,
  "version": "2.0.0"
}
```

---

### GET /api/metrics/{metric}

**Description:** Get system metrics
**Auth:** Required ✓

**Metric Types:** `projects`, `sessions`, `messages`, `agents`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "metric": "projects",
    "value": 23,
    "timestamp": "2025-10-18T10:30:00Z"
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

---

## ERROR RESPONSE FORMAT

All error responses follow this format:

```json
{
  "success": false,
  "error": "error_code",
  "message": "Human readable error message",
  "details": {
    "field": "Additional error details"
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

### Common Error Codes

```
VALIDATION_ERROR      400  Invalid request data
UNAUTHORIZED          401  Missing/invalid authentication
FORBIDDEN             403  Permission denied
NOT_FOUND             404  Resource not found
CONFLICT              409  Resource already exists
UNPROCESSABLE         422  Cannot process request
RATE_LIMITED          429  Too many requests
INTERNAL_ERROR        500  Server error
SERVICE_UNAVAILABLE   503  Service temporarily unavailable
```

---

## RATE LIMITING

- **Authenticated requests:** 100 requests per minute
- **Unauthenticated requests:** 20 requests per minute
- **Rate limit headers:**
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 85
  X-RateLimit-Reset: 1634559000
  ```

---

## NEXT STEPS

1. Implement all endpoints in FastAPI
2. Add proper authentication middleware
3. Add rate limiting
4. Add comprehensive error handling
5. Write endpoint tests
6. Generate API documentation (Swagger)

**Proceed to 11_REAL_TIME_FEATURES.md** for WebSocket specifications
