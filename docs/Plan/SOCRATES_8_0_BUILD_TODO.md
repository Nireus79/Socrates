# SOCRATES 8.0 - BUILD TODO & CHECKLIST
**Complete Implementation Guide for New Project**

---

## REFERENCE DOCUMENTS

Before starting, read these in order:
1. ✓ SOCRATES_8_0_QUICK_START.md - Overview and setup
2. ✓ DATABASE_SCHEMA_REFERENCE.md - Complete database design
3. ✓ API_ENDPOINTS_REFERENCE.md - All API endpoints
4. ✓ SERVICE_LAYER_PATTERNS.md - Business logic patterns

---

## PHASE 1: PROJECT SETUP (2-3 hours)

### 1.1 Create project structure
- [ ] Create `Socrates-8.0/` directory
- [ ] Create `backend/` and `frontend/` folders
- [ ] Create all subdirectories per SOCRATES_8_0_QUICK_START.md
- [ ] Initialize git repository

### 1.2 Backend initialization
- [ ] Create `backend/requirements.txt` (copy from QUICK_START)
- [ ] Create `backend/.env` file with:
  - [ ] `DATABASE_URL=postgresql://user:pass@localhost/socrates_8`
  - [ ] `JWT_SECRET=your-secret-key`
  - [ ] `ANTHROPIC_API_KEY=your-api-key`
- [ ] Create Python virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Set up Alembic: `alembic init alembic`

### 1.3 Frontend initialization
- [ ] Create React app: `npx create-react-app frontend --template typescript`
- [ ] Install dependencies from QUICK_START
- [ ] Update `frontend/package.json` with required packages

### 1.4 Database setup
- [ ] Create PostgreSQL database: `createdb socrates_8`
- [ ] Configure Alembic connection string
- [ ] Verify database connection

---

## PHASE 2: DATABASE LAYER (2-3 hours)

### 2.1 Create SQLAlchemy models
- [ ] Create `backend/src/models/__init__.py`
- [ ] Create `backend/src/models/base.py` (Base class)
- [ ] Implement User model (from DATABASE_SCHEMA_REFERENCE.md)
- [ ] Implement Project model
- [ ] Implement Session model
- [ ] Implement Message model
- [ ] Implement UserPreference model
- [ ] Implement Document model
- [ ] Implement AuditLog model
- [ ] Test imports: `from src.models import *`

### 2.2 Create migrations
- [ ] Run: `alembic revision --autogenerate -m "Initial schema"`
- [ ] Review migration file
- [ ] Apply migration: `alembic upgrade head`
- [ ] Verify tables created in PostgreSQL

### 2.3 Seed test data
- [ ] Create `backend/scripts/seed_database.py`
- [ ] Create test user: `testuser@example.com / Test@1234`
- [ ] Create test project
- [ ] Run seed script

---

## PHASE 3: REPOSITORY LAYER (2-3 hours)

### 3.1 Create base repository
- [ ] Create `backend/src/repositories/base_repository.py`
- [ ] Implement CRUD base class
- [ ] Add filtering, pagination, sorting

### 3.2 Create specific repositories
- [ ] Create `user_repository.py` - get_by_username, get_by_email
- [ ] Create `project_repository.py` - get_by_owner, get_by_status
- [ ] Create `session_repository.py` - get_by_owner, get_by_project
- [ ] Create `message_repository.py` - get_by_session, with pagination
- [ ] Create `preference_repository.py` - get_by_user_id
- [ ] Create `document_repository.py` - get_by_owner, get_by_project
- [ ] Test all repository methods

### 3.3 Add repository tests
- [ ] Create `backend/tests/test_repositories.py`
- [ ] Test CRUD operations for each repository
- [ ] Test filtering and pagination
- [ ] Run tests: `pytest tests/test_repositories.py -v`

---

## PHASE 4: SERVICE LAYER (3-4 hours)

### 4.1 Create base service
- [ ] Create `backend/src/services/base_service.py`
- [ ] Implement BaseService class (from SERVICE_LAYER_PATTERNS.md)

### 4.2 Create user service
- [ ] Create `backend/src/services/user_service.py`
- [ ] Implement register_user with validation
- [ ] Implement authenticate_user
- [ ] Implement update_profile
- [ ] Implement change_password
- [ ] Implement password hashing

### 4.3 Create other services
- [ ] Create `project_service.py` - CRUD + authorization
- [ ] Create `session_service.py` - lifecycle management
- [ ] Create `message_service.py` - persistence + Claude API
- [ ] Create `preference_service.py` - settings management
- [ ] Create `document_service.py` - upload + processing

### 4.4 Add service tests
- [ ] Create `backend/tests/test_services.py`
- [ ] Test UserService (register, login, update)
- [ ] Test ProjectService (create, update, delete)
- [ ] Test SessionService (create, toggle)
- [ ] Test error handling and validation
- [ ] Run tests: `pytest tests/test_services.py -v`

---

## PHASE 5: AUTHENTICATION LAYER (2-3 hours)

### 5.1 JWT setup
- [ ] Create `backend/src/auth/jwt_handler.py`
- [ ] Implement create_access_token()
- [ ] Implement verify_token()
- [ ] Implement decode_token()

### 5.2 Dependencies
- [ ] Create `backend/src/dependencies.py`
- [ ] Implement get_db() - database session
- [ ] Implement get_current_user() - JWT verification
- [ ] Add CORS middleware configuration

### 5.3 Test auth
- [ ] Test JWT token creation and validation
- [ ] Test token expiration
- [ ] Test invalid tokens

---

## PHASE 6: API LAYER (3-4 hours)

### 6.1 Create schemas
- [ ] Create `backend/src/schemas/auth.py` - LoginRequest, RegisterRequest
- [ ] Create `backend/src/schemas/project.py` - ProjectCreate, ProjectUpdate
- [ ] Create `backend/src/schemas/session.py` - SessionCreate, SessionUpdate
- [ ] Create `backend/src/schemas/message.py` - MessageCreate, MessageResponse
- [ ] Create `backend/src/schemas/profile.py` - ProfileUpdate, PreferenceUpdate

### 6.2 Create route handlers
- [ ] Create `backend/src/api/routes/__init__.py`
- [ ] Create `backend/src/api/routes/auth.py` - /register, /login, /logout
- [ ] Create `backend/src/api/routes/projects.py` - CRUD endpoints
- [ ] Create `backend/src/api/routes/sessions.py` - Session management
- [ ] Create `backend/src/api/routes/messages.py` - Messaging
- [ ] Create `backend/src/api/routes/profile.py` - Profile + settings
- [ ] Create `backend/src/api/routes/health.py` - Health check

### 6.3 Test endpoints
- [ ] Test /api/auth/register
- [ ] Test /api/auth/login
- [ ] Test /api/projects (CRUD)
- [ ] Test /api/sessions (CRUD)
- [ ] Test /api/messages (send + get)
- [ ] Use Postman or curl for testing

---

## PHASE 7: FRONTEND (4-5 hours)

### 7.1 Project setup
- [ ] Set up Tailwind CSS
- [ ] Create folder structure
- [ ] Set up Redux store (auth, projects, sessions, messages)
- [ ] Create API client service

### 7.2 Create pages
- [ ] Create LoginPage component
- [ ] Create RegisterPage component
- [ ] Create DashboardPage component
- [ ] Create ProjectsPage component
- [ ] Create SessionPage component
- [ ] Create ProfilePage component
- [ ] Create SettingsPage component

### 7.3 Create components
- [ ] Create AuthLayout wrapper
- [ ] Create ProjectCard component
- [ ] Create SessionCard component
- [ ] Create MessageList component
- [ ] Create MessageInput component
- [ ] Create Header/Navigation

### 7.4 Connect frontend to backend
- [ ] Create API client (`src/services/api.ts`)
- [ ] Implement authentication flow
- [ ] Connect login form to /api/auth/login
- [ ] Connect project list to /api/projects
- [ ] Connect session creation to /api/sessions
- [ ] Test all API calls

---

## PHASE 8: REAL-TIME FEATURES (2-3 hours)

### 8.1 WebSocket setup
- [ ] Install websocket packages
- [ ] Create WebSocket handler in FastAPI
- [ ] Set up socket.io in React

### 8.2 Implement messaging
- [ ] Real-time message updates
- [ ] Live user presence
- [ ] Typing indicators

---

## PHASE 9: TESTING (2-3 hours)

### 9.1 Unit tests
- [ ] Create comprehensive unit tests
- [ ] Test all services (min 80% coverage)
- [ ] Test all repositories

### 9.2 Integration tests
- [ ] Test complete workflows
- [ ] Test authentication flow
- [ ] Test session + messaging flow
- [ ] Test profile updates

### 9.3 E2E tests
- [ ] Test complete user journey
- [ ] Register → Login → Create project → Create session → Send message

### 9.4 Run test suite
- [ ] Run: `pytest tests/ -v --cov=src`
- [ ] Verify coverage > 80%

---

## PHASE 10: DEPLOYMENT (1-2 hours)

### 10.1 Docker setup
- [ ] Create `backend/Dockerfile`
- [ ] Create `frontend/Dockerfile`
- [ ] Create `docker-compose.yml`

### 10.2 Environment configuration
- [ ] Create `.env.example` file
- [ ] Document all environment variables
- [ ] Create secrets management

### 10.3 Deploy to staging
- [ ] Deploy to Render or Railway
- [ ] Test all endpoints on staging
- [ ] Verify database backups

---

## QUALITY CHECKLIST

Before considering "done", verify:

- [ ] No greedy patterns (no "will implement later")
- [ ] All validation working
- [ ] All error handling implemented
- [ ] No hardcoded values
- [ ] No fake/stub responses
- [ ] All data persists to database
- [ ] All tests passing (100%)
- [ ] Code follows conventions
- [ ] All endpoints documented
- [ ] Security review completed
- [ ] Performance acceptable
- [ ] Logging enabled everywhere
- [ ] CORS configured correctly
- [ ] JWT tokens working
- [ ] Database migrations working
- [ ] Both frontend and backend running

---

## DAILY WORKFLOW

Each day follow this pattern:

1. **Start of day:**
   - [ ] Check todo list progress
   - [ ] Run full test suite
   - [ ] Review previous day's code

2. **Development:**
   - [ ] Pick next uncompleted item
   - [ ] Mark as "in progress"
   - [ ] Implement feature
   - [ ] Write tests
   - [ ] Verify with tests
   - [ ] Mark as "completed"

3. **End of day:**
   - [ ] Run full test suite
   - [ ] Commit code to git
   - [ ] Update this checklist
   - [ ] Document blockers

---

## ESTIMATED TIMELINE

| Phase | Hours | Days |
|-------|-------|------|
| Phase 1 (Setup) | 2-3 | 0.5 |
| Phase 2 (Database) | 2-3 | 0.5 |
| Phase 3 (Repository) | 2-3 | 0.5 |
| Phase 4 (Services) | 3-4 | 1 |
| Phase 5 (Auth) | 2-3 | 0.5 |
| Phase 6 (API) | 3-4 | 1 |
| Phase 7 (Frontend) | 4-5 | 1-2 |
| Phase 8 (Real-time) | 2-3 | 0.5-1 |
| Phase 9 (Testing) | 2-3 | 0.5-1 |
| Phase 10 (Deploy) | 1-2 | 0.5 |
| **TOTAL** | **24-35** | **6-7 days** |

**Full-time development: 6-7 days (1-2 weeks part-time)**

---

## GIT WORKFLOW

Commit after completing each major section:

```bash
# Phase 1: Setup
git commit -m "feat: Initial project setup with folder structure"

# Phase 2: Database
git commit -m "feat: Add SQLAlchemy models and migrations"

# Phase 3: Repositories
git commit -m "feat: Implement repository layer with CRUD"

# Phase 4: Services
git commit -m "feat: Implement service layer with business logic"

# Phase 5: Auth
git commit -m "feat: Add JWT authentication"

# Phase 6: API
git commit -m "feat: Implement FastAPI routes and endpoints"

# Phase 7: Frontend
git commit -m "feat: Create React UI with all pages"

# Phase 8: Real-time
git commit -m "feat: Add WebSocket support for real-time messaging"

# Phase 9: Testing
git commit -m "feat: Add comprehensive test suite"

# Phase 10: Deploy
git commit -m "feat: Add Docker and deployment configuration"
```

---

## BLOCKERS & HELP

If blocked on any phase:

1. **Database issues:**
   - Check migration files
   - Verify PostgreSQL connection
   - Check error logs

2. **API issues:**
   - Check FastAPI logs
   - Test with Postman
   - Verify CORS settings

3. **Frontend issues:**
   - Check browser console
   - Check Redux store
   - Verify API calls

4. **Testing issues:**
   - Check test database setup
   - Verify mocking
   - Check test fixtures

---

## SUCCESS CRITERIA

Project is complete when:

✓ All 10 phases implemented
✓ All tests passing (100%)
✓ All endpoints working
✓ No console errors
✓ Database properly normalized
✓ Authentication working
✓ Messaging working end-to-end
✓ Settings persist
✓ UI is responsive
✓ Code is well-documented
✓ Deployed to staging
✓ Ready for production

---

**Build Version:** 8.0.0
**Created:** October 17, 2025
**Status:** Ready to build
