# Frontend Integration Guide

## Overview

This document describes how the frontend should interact with the Socrates API backend. The frontend needs to follow a specific sequence of API calls to properly initialize the system and create projects.

## Prerequisites

1. **ANTHROPIC_API_KEY environment variable** must be set before starting the API server
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..." # Your Claude API key
   ```

2. **API Server running** on `http://localhost:8000` (or configured host/port)

## Frontend Integration Flow

### Step 1: Initialize the API

**Endpoint:** `POST /initialize`

**Request:**
```json
{}
```

**Response (200 OK):**
```json
{
  "version": "8.0.0",
  "library_version": "...",
  "status": "operational",
  "uptime": 0.0
}
```

**What happens:**
- The API reads the `ANTHROPIC_API_KEY` environment variable (no API key needs to be sent)
- Initializes the orchestrator and connects to Claude
- Sets up the system for subsequent requests

**Why it works:**
- The endpoint now falls back to the environment variable when no API key is provided in the request body
- This allows deployment without exposing the API key in client code

### Step 2: Register or Login

#### Option A: Register a new user

**Endpoint:** `POST /auth/register`

**Request:**
```json
{
  "username": "john_doe",
  "password": "secure_password_123",
  "email": "john@example.com"  // Optional - defaults to username@localhost
}
```

**Response (200 OK):**
```json
{
  "user": {
    "username": "john_doe",
    "email": "john@example.com",
    "subscription_tier": "free",
    "subscription_status": "active"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

#### Option B: Login existing user

**Endpoint:** `POST /auth/login`

**Request:**
```json
{
  "username": "john_doe",
  "password": "secure_password_123"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "username": "john_doe",
    "email": "john@example.com",
    "subscription_tier": "free",
    "subscription_status": "active"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

**What happens:**
- User account is created (register) or verified (login)
- Returns authentication tokens for subsequent API calls
- Stores the tokens in the response for frontend to use

**What to do with the tokens:**
- Save `access_token` for authenticated API calls
- Store `refresh_token` for obtaining new tokens when current one expires

### Step 3: Create a Project

**Endpoint:** `POST /projects`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "name": "My First Project",
  "description": "A description of my project"
}
```

**Response (200 OK):**
```json
{
  "project_id": "proj_john_doe_1702000000000",
  "name": "My First Project",
  "owner": "john_doe",
  "description": "A description of my project",
  "phase": "discovery",
  "created_at": "2024-12-23T12:00:00Z",
  "updated_at": "2024-12-23T12:00:00Z",
  "is_archived": false
}
```

**What happens:**
- New project is created with the authenticated user as the owner
- Cannot create projects for other users (owner is always the authenticated user)
- Returns project details including the generated project_id

**Error handling:**
- **401 Unauthorized:** Access token is missing or invalid
  - Solution: Call `/auth/login` or `/auth/register` to get a new token
- **403 Forbidden:** Attempting to create project for another user
  - Solution: Use the current user as the owner (this is now automatic)

## Important Changes from Previous Version

### 1. API Key Handling (Fixed)

**Before:**
- `/initialize` required API key in request body
- Frontend had to obtain and send the API key

**After:**
- `/initialize` can read API key from environment variable
- Frontend doesn't need to send API key
- More secure for browser-based clients

### 2. Project Ownership (Fixed)

**Before:**
- `/projects` accepted `owner` parameter in request
- Would reject if owner didn't match authenticated user

**After:**
- `/projects` ignores owner parameter
- Always uses authenticated user as the owner
- Simpler and more secure

## Authentication Flow Diagram

```
┌─────────┐
│ Frontend│
└────┬────┘
     │
     │ 1. POST /initialize (no auth needed)
     ├─────────────────────────────────────→ API
     │                                       │
     │                           ┌─ Initialize from ANTHROPIC_API_KEY env var
     │                           │
     │ 200 OK                     │
     │◄─────────────────────────────────────┤
     │
     │ 2. POST /auth/register or /auth/login
     ├─────────────────────────────────────→ API
     │                                       │
     │                           ┌─ Verify credentials
     │                           │ Generate tokens
     │                           │
     │ 200 OK + tokens           │
     │◄─────────────────────────────────────┤
     │ Save access_token
     │
     │ 3. POST /projects (with auth header)
     ├─────────────────────────────────────→ API
     │ Authorization: Bearer {access_token}  │
     │                                       │
     │                           ┌─ Verify token
     │                           │ Create project
     │                           │
     │ 200 OK + project          │
     │◄─────────────────────────────────────┤
```

## Code Example (TypeScript/JavaScript)

```typescript
// Step 1: Initialize API
async function initializeAPI() {
  const response = await fetch('http://localhost:8000/initialize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });

  if (!response.ok) {
    throw new Error('Failed to initialize API');
  }

  const data = await response.json();
  console.log('API initialized:', data);
}

// Step 2: Register user
async function registerUser(username: string, password: string) {
  const response = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username,
      password,
      email: `${username}@localhost`
    })
  });

  if (!response.ok) {
    throw new Error('Failed to register');
  }

  const data = await response.json();

  // Store access token for subsequent requests
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  localStorage.setItem('user', JSON.stringify(data.user));

  return data;
}

// Step 3: Create project
async function createProject(name: string, description: string) {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/projects', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      name,
      description
    })
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Token expired, need to login again
      throw new Error('Session expired, please login again');
    }
    throw new Error('Failed to create project');
  }

  const data = await response.json();
  return data;
}

// Usage
async function main() {
  try {
    // 1. Initialize
    await initializeAPI();

    // 2. Register or login
    const authData = await registerUser('testuser', 'password123');
    console.log('User created:', authData.user);

    // 3. Create project
    const project = await createProject(
      'My Project',
      'Project description'
    );
    console.log('Project created:', project);
  } catch (error) {
    console.error('Error:', error);
  }
}

main();
```

## Troubleshooting

### 500 Error on /initialize

**Cause:** ANTHROPIC_API_KEY environment variable is not set

**Solution:**
```bash
# Set the environment variable before running the API
export ANTHROPIC_API_KEY="sk-ant-..."
# Then start the API server
python -m socrates_api.main
```

### 401 Error on /projects

**Cause:** Access token is missing or invalid

**Solution:**
1. Check that the Authorization header is set correctly
2. Verify the access token was obtained from `/auth/register` or `/auth/login`
3. If token has expired, call `/auth/login` again to get a new one

### 403 Error on /projects (deprecated)

**Note:** This error should no longer occur with the latest code. The owner is now automatically set to the authenticated user.

## API Endpoints Summary

| Method | Endpoint | Auth Required | Purpose |
|--------|----------|---------------|---------|
| POST | `/initialize` | No | Initialize API (reads env var for API key) |
| POST | `/auth/register` | No | Create new user account |
| POST | `/auth/login` | No | Login existing user |
| POST | `/projects` | Yes | Create new project |
| GET | `/projects` | Yes | List user's projects |
| GET | `/projects/{project_id}` | Yes | Get specific project |
| PUT | `/projects/{project_id}` | Yes | Update project |
| DELETE | `/projects/{project_id}` | Yes | Delete project |

## See Also

- [API Documentation](http://localhost:8000/docs) - Swagger UI
- [API ReDoc](http://localhost:8000/redoc) - ReDoc UI
- [Backend Architecture](./ARCHITECTURE.md)
