# SOCRATES 8.0 - QUICK START REFERENCE
**Modern Architecture | FastAPI + React + PostgreSQL**

---

## PROJECT SETUP (Copy this exactly)

```bash
# Create project directory
mkdir Socrates-8.0
cd Socrates-8.0

# Initialize git
git init
git config user.email "dev@socrates.local"
git config user.name "Socrates Dev"

# Create folder structure
mkdir -p backend frontend docs

# Backend structure
cd backend
mkdir -p src/{api,models,schemas,services,repositories,middleware,utils}
mkdir -p migrations/versions
mkdir -p tests/{unit,integration}

# Frontend structure
cd ../frontend
mkdir -p src/{components,pages,hooks,store,services,types,assets/styles}
mkdir -p public

cd ..
```

---

## TECHNOLOGY STACK

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend API** | FastAPI | 0.104+ |
| **Backend ORM** | SQLAlchemy | 2.0+ |
| **Database** | PostgreSQL | 14+ |
| **Migrations** | Alembic | 1.12+ |
| **Validation** | Pydantic | 2.0+ |
| **Auth** | Python-Jose + passlib | Latest |
| **Frontend** | React | 18+ |
| **Frontend Types** | TypeScript | 5+ |
| **State Management** | Redux Toolkit | Latest |
| **HTTP Client** | Axios | Latest |
| **UI Framework** | Tailwind CSS | 3+ |
| **Real-time** | python-socketio + socket.io-client | Latest |

---

## KEY FILES TO CREATE FIRST

### Backend Entry Point
**File:** `backend/src/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import routes
from src.middleware import error_handler

app = FastAPI(
    title="Socrates 8.0 API",
    description="AI-powered Socratic questioning system",
    version="8.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(routes.auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(routes.projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(routes.sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(routes.messages.router, prefix="/api/messages", tags=["messages"])

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "8.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Backend Config
**File:** `backend/src/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:pass@localhost/socrates_8"
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    ANTHROPIC_API_KEY: str
    CORS_ORIGINS: list = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()
```

### Frontend Entry Point
**File:** `frontend/src/App.tsx`
```typescript
import React from 'react';
import { Provider } from 'react-redux';
import { store } from './store';
import Router from './routes';

export default function App() {
  return (
    <Provider store={store}>
      <Router />
    </Provider>
  );
}
```

### Redux Store
**File:** `frontend/src/store/index.ts`
```typescript
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import projectsReducer from './slices/projectsSlice';
import sessionsReducer from './slices/sessionsSlice';
import messagesReducer from './slices/messagesSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    projects: projectsReducer,
    sessions: sessionsReducer,
    messages: messagesReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

---

## CORE CONCEPTS TO FOLLOW

### 1. No Greedy Patterns
- ✅ Implement complete features properly
- ✅ Use proper error handling
- ✅ Add validation everywhere
- ❌ No "will implement later"
- ❌ No hardcoded fake responses
- ❌ No silent failures

### 2. Database-First Approach
- Create all migrations before writing code
- Use Alembic for version control
- Test database constraints
- Verify relationships before coding

### 3. Type Safety
- Backend: Use Pydantic for all schemas
- Frontend: Use TypeScript for all components
- Define types upfront, not after

### 4. Clean Architecture
```
API Layer (FastAPI routes)
    ↓
Service Layer (business logic)
    ↓
Repository Layer (data access)
    ↓
Database (PostgreSQL)
```

### 5. Testing-First Mentality
- Write tests as you build
- Test each layer independently
- Integration tests after features
- 80% code coverage minimum

---

## CRITICAL FILES REFERENCE

See these separate reference files for detailed information:

1. **DATABASE_SCHEMA.md** - Complete PostgreSQL schema
2. **API_STRUCTURE.md** - All endpoints and responses
3. **SERVICE_LAYER.md** - Business logic patterns
4. **REPOSITORY_PATTERN.md** - Data access layer
5. **FRONTEND_COMPONENTS.md** - React component hierarchy
6. **ERROR_HANDLING.md** - Consistent error responses
7. **TESTING_STRATEGY.md** - How to test each layer

---

## FIRST SESSION CHECKLIST

- [ ] Create project structure (folder hierarchy)
- [ ] Set up backend (FastAPI, dependencies)
- [ ] Set up frontend (React, TypeScript)
- [ ] Create database schema (PostgreSQL)
- [ ] Create first migration
- [ ] Implement authentication endpoints
- [ ] Create Redux store structure
- [ ] Build login page (frontend)
- [ ] Test login flow end-to-end

---

## DEPENDENCIES FILE

**File:** `backend/requirements.txt`
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
python-socketio==5.10.0
python-dotenv==1.0.0
psycopg2-binary==2.9.9
anthropic==0.7.0
pytest==7.4.3
pytest-asyncio==0.21.1
```

**File:** `frontend/package.json` (key dependencies)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@reduxjs/toolkit": "^1.9.7",
    "react-redux": "^8.1.3",
    "axios": "^1.6.2",
    "socket.io-client": "^4.5.4",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.3.3"
  }
}
```

---

## NEXT STEPS

1. Read **DATABASE_SCHEMA.md** to understand data model
2. Read **API_STRUCTURE.md** to plan endpoints
3. Start with authentication (most critical)
4. Build incrementally with tests
5. Reference other .md files as needed

**Do not skip database schema or API design.**

---

**Reference Version:** 8.0.0 Architecture
**Created:** October 17, 2025
**Status:** Use as starting blueprint
