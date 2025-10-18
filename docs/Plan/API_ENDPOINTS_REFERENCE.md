# SOCRATES 8.0 - API ENDPOINTS REFERENCE
**Complete REST API Specification**

---

## RESPONSE FORMAT STANDARD

All endpoints return this structure:

**Success (200, 201):**
```json
{
  "success": true,
  "data": { /* actual data */ },
  "message": "Operation successful"
}
```

**Error (400, 404, 500):**
```json
{
  "success": false,
  "error": "error_code",
  "message": "Human-readable error message",
  "details": { /* optional */ }
}
```

---

## AUTHENTICATION ENDPOINTS

### POST /api/auth/register
**Register new user**

Request:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

Response (201):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2025-10-17T12:00:00Z"
  },
  "message": "User created successfully"
}
```

**Error Cases:**
- 400: Username/email already exists
- 400: Password doesn't meet requirements

---

### POST /api/auth/login
**Authenticate user**

Request:
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

Response (200):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "access_token": "jwt_token_here",
    "token_type": "bearer",
    "expires_in": 86400
  },
  "message": "Login successful"
}
```

**Error Cases:**
- 401: Invalid credentials
- 404: User not found

---

### POST /api/auth/logout
**Logout (invalidate token)**

Headers: `Authorization: Bearer {token}`

Response (200):
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### POST /api/auth/refresh
**Refresh access token**

Headers: `Authorization: Bearer {refresh_token}`

Response (200):
```json
{
  "success": true,
  "data": {
    "access_token": "new_jwt_token",
    "expires_in": 86400
  },
  "message": "Token refreshed"
}
```

---

## PROJECTS ENDPOINTS

### GET /api/projects
**List user projects**

Headers: `Authorization: Bearer {token}`

Query params: `?status=PLANNING&page=1&limit=10`

Response (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "AI Chat Bot",
      "description": "Build AI chatbot",
      "status": "DEVELOPMENT",
      "technology_stack": ["Python", "FastAPI", "React"],
      "owner_id": "uuid",
      "created_at": "2025-10-17T12:00:00Z",
      "updated_at": "2025-10-17T12:00:00Z"
    }
  ],
  "message": "Projects retrieved"
}
```

---

### POST /api/projects
**Create project**

Headers: `Authorization: Bearer {token}`

Request:
```json
{
  "name": "AI Chat Bot",
  "description": "Build AI chatbot",
  "technology_stack": ["Python", "FastAPI", "React"]
}
```

Response (201):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "AI Chat Bot",
    "description": "Build AI chatbot",
    "status": "PLANNING",
    "technology_stack": ["Python", "FastAPI", "React"],
    "owner_id": "uuid",
    "created_at": "2025-10-17T12:00:00Z"
  },
  "message": "Project created"
}
```

---

### GET /api/projects/{project_id}
**Get project details**

Response (200):
```json
{
  "success": true,
  "data": { /* project object */ },
  "message": "Project retrieved"
}
```

---

### PUT /api/projects/{project_id}
**Update project**

Request:
```json
{
  "name": "Updated name",
  "description": "Updated description",
  "status": "DEVELOPMENT"
}
```

Response (200):
```json
{
  "success": true,
  "data": { /* updated project */ },
  "message": "Project updated"
}
```

---

### DELETE /api/projects/{project_id}
**Delete project**

Response (200):
```json
{
  "success": true,
  "message": "Project deleted"
}
```

---

## SESSIONS ENDPOINTS

### GET /api/sessions
**List user sessions**

Headers: `Authorization: Bearer {token}`

Query params: `?status=ACTIVE&project_id=uuid&page=1&limit=10`

Response (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Chat Session 1",
      "status": "ACTIVE",
      "mode": "chat",
      "role": "developer",
      "project_id": "uuid",
      "created_at": "2025-10-17T12:00:00Z",
      "message_count": 15
    }
  ],
  "message": "Sessions retrieved"
}
```

---

### POST /api/sessions
**Create session**

Request:
```json
{
  "project_id": "uuid or null",
  "name": "Chat Session 1",
  "mode": "chat",
  "role": "developer"
}
```

Response (201):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Chat Session 1",
    "status": "ACTIVE",
    "mode": "chat",
    "created_at": "2025-10-17T12:00:00Z"
  },
  "message": "Session created"
}
```

---

### GET /api/sessions/{session_id}
**Get session details with messages**

Response (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Chat Session 1",
    "status": "ACTIVE",
    "mode": "chat",
    "messages": [
      {
        "id": "uuid",
        "role": "user",
        "content": "What is AI?",
        "message_type": "text",
        "created_at": "2025-10-17T12:00:00Z"
      },
      {
        "id": "uuid",
        "role": "assistant",
        "content": "AI is artificial intelligence...",
        "message_type": "text",
        "created_at": "2025-10-17T12:01:00Z"
      }
    ]
  },
  "message": "Session retrieved"
}
```

---

### PUT /api/sessions/{session_id}
**Update session (status, mode, name)**

Request:
```json
{
  "status": "ARCHIVED",
  "mode": "question",
  "name": "Updated name"
}
```

Response (200):
```json
{
  "success": true,
  "data": { /* updated session */ },
  "message": "Session updated"
}
```

---

### POST /api/sessions/{session_id}/toggle-mode
**Toggle session mode**

Request:
```json
{
  "mode": "question"
}
```

Response (200):
```json
{
  "success": true,
  "data": {
    "mode": "question",
    "message": "Mode changed to question"
  }
}
```

---

### DELETE /api/sessions/{session_id}
**Delete session**

Response (200):
```json
{
  "success": true,
  "message": "Session deleted"
}
```

---

## MESSAGES ENDPOINTS

### POST /api/sessions/{session_id}/messages
**Send message (user submits)**

Request:
```json
{
  "content": "What is the best architecture for a React app?",
  "message_type": "text"
}
```

Response (201):
```json
{
  "success": true,
  "data": {
    "user_message": {
      "id": "uuid",
      "role": "user",
      "content": "What is the best architecture...",
      "created_at": "2025-10-17T12:00:00Z"
    },
    "assistant_response": {
      "id": "uuid",
      "role": "assistant",
      "content": "The best architecture includes...",
      "created_at": "2025-10-17T12:00:01Z"
    }
  },
  "message": "Message sent and response generated"
}
```

---

### GET /api/sessions/{session_id}/messages
**Get session messages**

Query params: `?page=1&limit=20&order=desc`

Response (200):
```json
{
  "success": true,
  "data": [
    /* array of messages */
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  },
  "message": "Messages retrieved"
}
```

---

## PROFILE ENDPOINTS

### GET /api/profile
**Get current user profile**

Headers: `Authorization: Bearer {token}`

Response (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "bio": "Software developer",
    "avatar_url": "https://...",
    "created_at": "2025-10-17T12:00:00Z"
  },
  "message": "Profile retrieved"
}
```

---

### PUT /api/profile
**Update profile**

Request:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Updated bio",
  "avatar_url": "https://..."
}
```

Response (200):
```json
{
  "success": true,
  "data": { /* updated profile */ },
  "message": "Profile updated"
}
```

---

### POST /api/profile/password
**Change password**

Request:
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!",
  "confirm_password": "NewPass456!"
}
```

Response (200):
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

## SETTINGS ENDPOINTS

### GET /api/settings
**Get user preferences**

Response (200):
```json
{
  "success": true,
  "data": {
    "theme": "dark",
    "llm_model": "claude-3-sonnet",
    "llm_temperature": 0.7,
    "llm_max_tokens": 2000,
    "ide_type": "vscode",
    "auto_sync": true,
    "notifications_enabled": true
  },
  "message": "Settings retrieved"
}
```

---

### PUT /api/settings
**Update settings**

Request:
```json
{
  "theme": "light",
  "llm_temperature": 0.8,
  "auto_sync": false
}
```

Response (200):
```json
{
  "success": true,
  "data": { /* updated settings */ },
  "message": "Settings saved"
}
```

---

## HEALTH/STATUS ENDPOINTS

### GET /health
**System health check**

Response (200):
```json
{
  "status": "healthy",
  "version": "8.0.0",
  "timestamp": "2025-10-17T12:00:00Z"
}
```

---

### GET /api/status
**Detailed system status**

Response (200):
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "version": "8.0.0",
  "uptime_seconds": 3600
}
```

---

## ERROR CODES

| Code | HTTP | Meaning |
|------|------|---------|
| `AUTH_INVALID` | 401 | Invalid credentials |
| `AUTH_EXPIRED` | 401 | Token expired |
| `AUTH_REQUIRED` | 401 | No token provided |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `DUPLICATE` | 409 | Resource already exists |
| `SERVER_ERROR` | 500 | Internal server error |

---

## AUTHENTICATION FLOW

**Step 1: Register**
```bash
POST /api/auth/register
Body: { username, email, password, first_name, last_name }
Returns: user object
```

**Step 2: Login**
```bash
POST /api/auth/login
Body: { username, password }
Returns: access_token, user object
```

**Step 3: Use token**
```bash
GET /api/profile
Headers: Authorization: Bearer {access_token}
```

**Step 4: Refresh token (if expired)**
```bash
POST /api/auth/refresh
Headers: Authorization: Bearer {refresh_token}
Returns: new access_token
```

---

## REQUEST HEADERS

All authenticated endpoints require:
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

---

**API Version:** 8.0.0
**Last Updated:** October 17, 2025
