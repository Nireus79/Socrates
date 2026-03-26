# Socrates API Endpoints

Complete reference for all Socrates API endpoints. The API uses RESTful principles with JSON request/response format.

---

## Table of Contents

1. [Base Configuration](#base-configuration)
2. [Authentication](#authentication)
3. [Project Endpoints](#project-endpoints)
4. [Code Generation Endpoints](#code-generation-endpoints)
5. [Learning Endpoints](#learning-endpoints)
6. [Agent Endpoints](#agent-endpoints)
7. [User Endpoints](#user-endpoints)
8. [Analytics Endpoints](#analytics-endpoints)
9. [System Endpoints](#system-endpoints)
10. [Error Responses](#error-responses)
11. [Rate Limiting](#rate-limiting)

---

## Base Configuration

### API Server

- **URL**: `http://localhost:8000` (development)
- **Version**: v1
- **Port**: Configurable via `SOCRATES_API_PORT`
- **Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc`

### Environment Variables

```bash
SOCRATES_API_PORT=8000              # API server port
SOCRATES_API_HOST=0.0.0.0           # Bind to all interfaces
JWT_SECRET_KEY=your-secret-key      # JWT signing key
JWT_ALGORITHM=HS256                 # JWT algorithm
JWT_EXPIRATION=3600                 # Token expiration (seconds)
ANTHROPIC_API_KEY=sk-ant-...       # LLM API key
DATABASE_URL=sqlite:///...          # Database URL
REDIS_URL=redis://localhost:6379    # Redis URL (optional)
ENABLE_CORS=true                    # Enable CORS
ENABLE_RATE_LIMITING=true           # Enable rate limiting
```

---

## Authentication

### JWT Token Flow

```
1. User logs in with credentials
2. API returns access_token and refresh_token
3. Include token in Authorization header: Bearer {token}
4. When expired, use refresh_token to get new access_token
```

### Login

**Endpoint**: `POST /api/auth/login`

**Request**:
```json
{
    "username": "user@example.com",
    "password": "password123"
}
```

**Response**:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### Refresh Token

**Endpoint**: `POST /api/auth/refresh`

**Request**:
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response**:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### Register User

**Endpoint**: `POST /api/auth/register`

**Request**:
```json
{
    "username": "newuser",
    "email": "user@example.com",
    "password": "secure_password123"
}
```

**Response**:
```json
{
    "id": "user_123",
    "username": "newuser",
    "email": "user@example.com",
    "created_at": "2026-03-26T10:00:00Z"
}
```

### Logout

**Endpoint**: `POST /api/auth/logout`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response**:
```json
{
    "message": "Successfully logged out"
}
```

---

## Project Endpoints

### Create Project

**Endpoint**: `POST /api/projects`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request**:
```json
{
    "name": "My Python Project",
    "description": "A learning project",
    "language": "python",
    "project_type": "web_application"
}
```

**Response**:
```json
{
    "project_id": "proj_123abc",
    "name": "My Python Project",
    "owner": "user_123",
    "status": "active",
    "phase": "requirements",
    "created_at": "2026-03-26T10:00:00Z",
    "updated_at": "2026-03-26T10:00:00Z"
}
```

### Get Project

**Endpoint**: `GET /api/projects/{project_id}`

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "project_id": "proj_123abc",
    "name": "My Python Project",
    "owner": "user_123",
    "description": "A learning project",
    "language": "python",
    "status": "active",
    "phase": "development",
    "maturity_score": 0.65,
    "created_at": "2026-03-26T10:00:00Z",
    "updated_at": "2026-03-26T10:15:00Z",
    "metadata": {
        "tech_stack": ["Python", "FastAPI", "SQLite"],
        "requirements_count": 5,
        "code_files": 3
    }
}
```

### List Projects

**Endpoint**: `GET /api/projects`

**Query Parameters**:
- `skip` (int): Skip this many projects (default: 0)
- `limit` (int): Return this many projects (default: 10, max: 100)
- `status` (str): Filter by status (active, archived, completed)
- `language` (str): Filter by language

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "items": [
        {
            "project_id": "proj_123abc",
            "name": "My Python Project",
            "status": "active",
            "phase": "development"
        },
        {
            "project_id": "proj_456def",
            "name": "My JavaScript Project",
            "status": "active",
            "phase": "testing"
        }
    ],
    "total": 2,
    "skip": 0,
    "limit": 10
}
```

### Update Project

**Endpoint**: `PUT /api/projects/{project_id}`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request**:
```json
{
    "name": "Updated Project Name",
    "description": "Updated description",
    "status": "active"
}
```

**Response**:
```json
{
    "project_id": "proj_123abc",
    "name": "Updated Project Name",
    "description": "Updated description",
    "updated_at": "2026-03-26T10:30:00Z"
}
```

### Delete Project

**Endpoint**: `DELETE /api/projects/{project_id}`

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "message": "Project deleted successfully"
}
```

---

## Code Generation Endpoints

### Generate Code

**Endpoint**: `POST /api/code/generate`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request**:
```json
{
    "project_id": "proj_123abc",
    "prompt": "Create a function to validate email addresses",
    "language": "python",
    "style": "functional",
    "requirements": [
        "Support RFC 5322 format",
        "Handle edge cases"
    ]
}
```

**Response**:
```json
{
    "status": "success",
    "code": "def validate_email(email: str) -> bool:\n    ...",
    "language": "python",
    "explanation": "Function validates email using regex pattern...",
    "confidence": 0.95,
    "metadata": {
        "tokens_used": 250,
        "model": "claude-3-sonnet",
        "generation_time": 1.23
    }
}
```

### Validate Code

**Endpoint**: `POST /api/code/validate`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request**:
```json
{
    "code": "def hello():\n    print('Hello')",
    "language": "python",
    "strict": false
}
```

**Response**:
```json
{
    "status": "success",
    "valid": true,
    "errors": [],
    "warnings": [],
    "issues": [
        {
            "type": "style",
            "message": "Missing docstring",
            "line": 1
        }
    ]
}
```

### Analyze Code Quality

**Endpoint**: `POST /api/code/analyze`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request**:
```json
{
    "code": "def hello():\n    print('Hello')",
    "language": "python"
}
```

**Response**:
```json
{
    "status": "success",
    "quality_score": 85,
    "metrics": {
        "complexity": 1,
        "readability": 0.9,
        "maintainability": 0.85,
        "test_coverage": 0.0
    },
    "suggestions": [
        "Add type hints to function parameters",
        "Add docstring to function",
        "Add unit tests"
    ]
}
```

---

## Learning Endpoints

### Get Learning Profile

**Endpoint**: `GET /api/learning/profile`

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "user_id": "user_123",
    "maturity_score": 0.65,
    "total_interactions": 150,
    "skills": [
        {
            "skill_id": "skill_123",
            "name": "Python Basics",
            "proficiency": 0.85,
            "experience_count": 45
        }
    ],
    "weak_areas": [
        "async_programming",
        "testing"
    ],
    "recommended_skills": [
        "async_programming_1",
        "unit_testing_1"
    ]
}
```

### Record Learning Interaction

**Endpoint**: `POST /api/learning/interaction`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request**:
```json
{
    "project_id": "proj_123abc",
    "action": "code_generation",
    "success": true,
    "difficulty": 3,
    "time_spent": 5,
    "notes": "Successfully generated async code with proper error handling"
}
```

**Response**:
```json
{
    "interaction_id": "int_123",
    "recorded_at": "2026-03-26T10:45:00Z",
    "profile_updated": true,
    "maturity_change": 0.02
}
```

### Generate Skills

**Endpoint**: `POST /api/learning/generate-skills`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request**:
```json
{
    "weak_areas": ["async_programming", "testing"],
    "learning_style": "hands_on",
    "difficulty_preference": "medium"
}
```

**Response**:
```json
{
    "status": "success",
    "skills": [
        {
            "skill_id": "skill_456",
            "name": "Async Programming Basics",
            "difficulty": 3,
            "estimated_duration": 120,
            "description": "Learn async/await syntax and patterns"
        }
    ]
}
```

### Get Learning Path

**Endpoint**: `GET /api/learning/path`

**Query Parameters**:
- `time_available` (int): Minutes available per week
- `focus_area` (str): Primary learning focus

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "path_id": "path_123",
    "duration_weeks": 8,
    "weekly_hours": 10,
    "skills": [
        {
            "week": 1,
            "skill": "Async Programming Basics",
            "difficulty": 3
        }
    ]
}
```

---

## Agent Endpoints

### Execute Agent

**Endpoint**: `POST /api/agents/{agent_name}`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Path Parameters**:
- `agent_name` (str): Name of agent (code_generator, validator, etc.)

**Request**:
```json
{
    "action": "generate",
    "project_id": "proj_123abc",
    "prompt": "...",
    "parameters": {...}
}
```

**Response**:
```json
{
    "status": "success",
    "data": {...},
    "execution_time": 1.23
}
```

### List Available Agents

**Endpoint**: `GET /api/agents`

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "agents": [
        {
            "name": "code_generator",
            "description": "Generate code from specifications",
            "actions": ["generate", "refactor"],
            "requires_llm": true
        },
        {
            "name": "code_validator",
            "description": "Validate code syntax and semantics",
            "actions": ["validate", "lint"],
            "requires_llm": false
        }
    ],
    "total": 14
}
```

### Get Agent Status

**Endpoint**: `GET /api/agents/{agent_name}/status`

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "agent_name": "code_generator",
    "status": "operational",
    "initialized": true,
    "llm_available": true,
    "total_executions": 1523,
    "avg_execution_time": 1.45
}
```

---

## User Endpoints

### Get Current User

**Endpoint**: `GET /api/users/me`

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "id": "user_123",
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2026-01-01T00:00:00Z",
    "subscription_tier": "premium",
    "profile": {
        "bio": "Learning Python",
        "avatar_url": "https://..."
    }
}
```

### Update User Profile

**Endpoint**: `PUT /api/users/me`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request**:
```json
{
    "email": "newemail@example.com",
    "profile": {
        "bio": "Intermediate Python developer"
    }
}
```

**Response**:
```json
{
    "id": "user_123",
    "username": "john_doe",
    "email": "newemail@example.com",
    "updated_at": "2026-03-26T10:50:00Z"
}
```

### Change Password

**Endpoint**: `POST /api/users/change-password`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request**:
```json
{
    "old_password": "old_password123",
    "new_password": "new_secure_password"
}
```

**Response**:
```json
{
    "message": "Password changed successfully"
}
```

---

## Analytics Endpoints

### Get Dashboard Metrics

**Endpoint**: `GET /api/analytics/dashboard`

**Query Parameters**:
- `period` (str): time (day, week, month) - default: month

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "period": "month",
    "total_interactions": 150,
    "average_score": 0.78,
    "projects_created": 5,
    "code_generated": 45,
    "learning_progress": 0.15,
    "trend": "up"
}
```

### Get Project Analytics

**Endpoint**: `GET /api/analytics/projects/{project_id}`

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "project_id": "proj_123abc",
    "total_interactions": 25,
    "code_generations": 8,
    "validations": 6,
    "quality_average": 0.82,
    "learning_effectiveness": 0.88
}
```

### Export Data

**Endpoint**: `GET /api/analytics/export`

**Query Parameters**:
- `format` (str): csv, json, xlsx
- `start_date` (str): ISO date format
- `end_date` (str): ISO date format

**Headers**:
```
Authorization: Bearer {token}
```

**Response**: File download

---

## System Endpoints

### Health Check

**Endpoint**: `GET /api/health`

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2026-03-26T11:00:00Z",
    "components": {
        "api": "operational",
        "database": "operational",
        "cache": "operational",
        "llm": "operational"
    }
}
```

### System Info

**Endpoint**: `GET /api/system/info`

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "version": "1.0.0",
    "environment": "production",
    "api_port": 8000,
    "database": "postgresql",
    "cache": "redis",
    "features": {
        "llm_enabled": true,
        "learning_system": true,
        "maturity_gating": true
    }
}
```

### API Routes

**Endpoint**: `GET /api/routes`

**Headers**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
    "total_routes": 260,
    "routers": {
        "authentication": 4,
        "projects": 12,
        "code_generation": 8,
        "learning": 10,
        "agents": 6,
        "users": 8,
        "analytics": 6,
        "system": 5
    }
}
```

---

## Error Responses

### Standard Error Format

```json
{
    "detail": "Error message describing what went wrong",
    "status_code": 400,
    "error_code": "INVALID_REQUEST"
}
```

### Common HTTP Status Codes

| Code | Meaning | Cause |
|------|---------|-------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created |
| 204 | No Content | Request succeeded, no content |
| 400 | Bad Request | Invalid request format or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Examples

**Validation Error (400)**:
```json
{
    "detail": "Validation error",
    "status_code": 400,
    "error_code": "VALIDATION_ERROR",
    "errors": [
        {
            "field": "language",
            "message": "Unsupported language: rust"
        }
    ]
}
```

**Authentication Error (401)**:
```json
{
    "detail": "Invalid authentication credentials",
    "status_code": 401,
    "error_code": "INVALID_TOKEN"
}
```

**Rate Limit Error (429)**:
```json
{
    "detail": "Rate limit exceeded",
    "status_code": 429,
    "error_code": "RATE_LIMIT_EXCEEDED",
    "retry_after": 60
}
```

---

## Rate Limiting

### Rate Limits

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Authentication | 10 requests | 1 minute |
| Code Generation | 30 requests | 1 hour |
| General API | 100 requests | 1 minute |
| Analytics | 20 requests | 1 minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1648300200
```

### Handling Rate Limits

When rate limited (429 response):

```json
{
    "detail": "Rate limit exceeded",
    "retry_after": 60,
    "reset_at": "2026-03-26T11:05:00Z"
}
```

**Recommendation**: Implement exponential backoff:

```python
import time

retry_count = 0
max_retries = 3

while retry_count < max_retries:
    try:
        response = make_api_call()
        break
    except RateLimitError as e:
        wait_time = 2 ** retry_count  # Exponential backoff
        time.sleep(wait_time)
        retry_count += 1
```

---

## API Documentation

### Interactive Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### Generate API Client

Using OpenAPI schema to generate client libraries:

```bash
# Generate Python client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./client

# Generate JavaScript client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g javascript \
  -o ./client
```

---

## Examples

### Complete Workflow

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

# 1. Register user
user_response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "username": "newuser",
        "email": "user@example.com",
        "password": "secure123"
    }
)

# 2. Login
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "username": "newuser",
        "password": "secure123"
    }
)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 3. Create project
project_response = requests.post(
    f"{BASE_URL}/projects",
    headers=headers,
    json={
        "name": "My Project",
        "language": "python"
    }
)

project_id = project_response.json()["project_id"]

# 4. Generate code
code_response = requests.post(
    f"{BASE_URL}/code/generate",
    headers=headers,
    json={
        "project_id": project_id,
        "prompt": "Create a function to calculate fibonacci",
        "language": "python"
    }
)

print(code_response.json()["code"])
```

---

**Last Updated**: 2026-03-26
**API Version**: 1.0.0
**Status**: Production Ready
