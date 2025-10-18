# COMPLETE OPTIMIZATION WORKFLOW - Socratic RAG Enhanced
**Date Created:** October 17, 2025
**Status:** READY FOR IMPLEMENTATION
**Priority:** CRITICAL - Foundation rebuild required before feature development

---

## EXECUTIVE SUMMARY

The codebase has been analyzed and tested. Current status: **15 of 24 core workflows broken** due to fundamental architecture issues, not simple bugs. This document provides a complete optimization strategy to rebuild the system properly.

**Key Finding:** The database schema is incomplete, core features are stubbed, and there's no consistent data persistence pattern.

**Recommendation:** Complete rebuild of persistence layer + architecture cleanup (not just bug fixes).

---

## PART 1: CURRENT STATE ANALYSIS

### What Works (9/24 tests passing)
- ✅ User authentication (login/logout/register)
- ✅ Dashboard page loading
- ✅ Dashboard health metrics API
- ✅ Project list viewing
- ✅ User profile viewing
- ✅ Profile update API (returns success but doesn't persist)
- ✅ Password change API
- ✅ LLM settings API
- ✅ System settings API

### What's Broken (15/24 tests failing)
- ✗ **Database schema incomplete** - Missing sessions table and other core tables
- ✗ **User ID not retrievable** - Database query issues
- ✗ **Project creation** - Endpoint fails or doesn't save
- ✗ **Project persistence** - Data not saved to database
- ✗ **Project updates** - Endpoint fails
- ✗ **Session creation** - Fails completely
- ✗ **Session persistence** - Can't save sessions
- ✗ **Message sending** - No storage, fake responses only
- ✗ **Message persistence** - Never stored to database
- ✗ **Response generation** - Returns hardcoded fake responses
- ✗ **Response persistence** - Fake responses not stored
- ✗ **Session mode toggle** - Fails
- ✗ **Profile persistence** - API success but data doesn't save
- ✗ **Settings persistence** - API success but data doesn't load
- ✗ **Database consistency** - Tables missing, orphaned data

### Root Causes (Strategic Issues)
1. **No database schema initialization** - Core tables don't exist
2. **Mixed patterns** - Some endpoints use ORM, others use raw SQL
3. **No transaction management** - Partial failures not handled
4. **Stubbed features** - Message responses are hardcoded, not real
5. **Greedy assumptions** - "Will implement later" approach throughout
6. **No data validation layer** - Forms accept anything
7. **Silent failures** - APIs return success even when data isn't saved
8. **No audit trail** - Can't track what happened
9. **Flask architecture** - Good for prototypes, but not maintainable at scale
10. **Monolithic codebase** - All logic in one file (web/app.py is 3900+ lines)

---

## PART 2: ARCHITECTURE REDESIGN

### Current Architecture (Problems)
```
User → Flask App → Mixed ORM/Raw SQL → SQLite
         ↓
    Single monolithic file (app.py)
    No service layer
    No clear separation of concerns
    No dependency injection
    Tightly coupled components
```

### Proposed Architecture (Solution)
```
User → API Layer → Service Layer → Repository Layer → Database
         ↓            ↓              ↓
    Route handlers   Business logic  Data access
    Request validation  Transactions  Query building
    Response formatting  Error handling  SQL operations
    Authentication     Event emission  Persistence

With Clear Separation:
- Controllers: Handle HTTP (request → response)
- Services: Handle business logic (validation, orchestration)
- Repositories: Handle data (queries, persistence, transactions)
- Models: Define structure (SQLAlchemy ORM)
```

---

## PART 3: DATABASE SCHEMA REDESIGN

### Current Issue
- Tables are created ad-hoc
- No migrations
- No constraints
- No relationships
- No audit columns

### Required Tables (Complete)

```sql
-- Users and Authentication
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    bio TEXT,
    status TEXT DEFAULT 'ACTIVE',  -- ACTIVE, INACTIVE, SUSPENDED
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Projects
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'PLANNING',  -- PLANNING, DESIGN, DEVELOPMENT, TESTING, COMPLETE
    technology_stack TEXT,  -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Sessions
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    project_id TEXT,
    name TEXT,
    status TEXT DEFAULT 'ACTIVE',  -- ACTIVE, ARCHIVED, PAUSED
    mode TEXT DEFAULT 'chat',  -- chat, question, teaching
    role TEXT,  -- developer, manager, designer, etc
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- Messages (Core functionality - CRITICAL)
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text',  -- text, code, question, etc
    metadata TEXT,  -- JSON for additional data
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- User Preferences
CREATE TABLE user_preferences (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    theme TEXT DEFAULT 'dark',
    llm_model TEXT DEFAULT 'claude-3-sonnet',
    llm_temperature REAL DEFAULT 0.7,
    llm_max_tokens INTEGER DEFAULT 2000,
    ide_type TEXT,  -- 'vscode', 'pycharm', etc
    auto_sync BOOLEAN DEFAULT FALSE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Documents
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    project_id TEXT,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT,  -- pdf, docx, txt, md, py, etc
    content_summary TEXT,
    vector_id TEXT,  -- Reference to ChromaDB
    status TEXT DEFAULT 'PROCESSED',  -- UPLOADING, PROCESSING, PROCESSED, ERROR
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- Audit Log (Track all changes)
CREATE TABLE audit_log (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    entity_type TEXT,  -- 'user', 'project', 'session', 'message'
    entity_id TEXT,
    action TEXT,  -- 'CREATE', 'UPDATE', 'DELETE'
    old_value TEXT,  -- JSON of previous values
    new_value TEXT,  -- JSON of new values
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_sessions_owner ON sessions(owner_id);
CREATE INDEX idx_sessions_project ON sessions(project_id);
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_user ON messages(user_id);
CREATE INDEX idx_documents_owner ON documents(owner_id);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
```

---

## PART 4: SERVICE LAYER REDESIGN

### Current Problem
- Business logic scattered in route handlers
- No reusable services
- No error handling strategy
- No validation layer

### Solution: Service Classes

```python
# Directory structure:
src/services/
├── base_service.py          # Abstract service with common functionality
├── user_service.py          # User management + authentication
├── project_service.py       # Project CRUD + lifecycle
├── session_service.py       # Session management + message handling
├── message_service.py       # Message persistence + retrieval
├── preference_service.py    # User preferences + settings
├── document_service.py      # Document management + processing
├── agent_service.py         # Agent orchestration + response generation
└── audit_service.py         # Audit logging
```

### BaseService Pattern
```python
class BaseService:
    """Abstract service providing common functionality"""

    def __init__(self, repository, logger, audit_service):
        self.repository = repository
        self.logger = logger
        self.audit = audit_service

    def validate_input(self, data, schema):
        """Validate input against schema"""
        # Marshmallow schema validation
        pass

    def audit_change(self, entity_id, action, old_value, new_value):
        """Log all changes for audit trail"""
        pass

    def handle_error(self, error, context):
        """Consistent error handling"""
        pass

    def create_response(self, success, data, message, code):
        """Standardized response format"""
        pass
```

---

## PART 5: IMPLEMENTATION PHASES

### PHASE 1: Database Foundation (2-3 hours)
**Goal:** Proper database schema with migrations

**Steps:**
1. Create migration system (Alembic)
2. Define all tables above
3. Create indexes
4. Initialize fresh database
5. Add seed data (test users)
6. Create database backup

**Tests to Pass:**
- [ ] All tables created
- [ ] All relationships work
- [ ] Indexes created
- [ ] Sample data queryable
- [ ] No orphaned records

---

### PHASE 2: Repository Layer (2-3 hours)
**Goal:** Clean data access layer with transactions

**Files to Create:**
```
src/repositories/
├── __init__.py
├── base_repository.py       # CRUD base class
├── user_repository.py       # User queries
├── project_repository.py    # Project queries
├── session_repository.py    # Session queries
├── message_repository.py    # Message queries + persistence
├── preference_repository.py # Preferences
└── audit_repository.py      # Audit logging
```

**Key Features:**
- All queries use parameterized statements (SQL injection prevention)
- Transaction management (begin/commit/rollback)
- Connection pooling
- Error logging
- Query performance logging

**Tests to Pass:**
- [ ] CRUD operations work
- [ ] Transactions commit/rollback correctly
- [ ] No SQL injection vulnerabilities
- [ ] Query performance acceptable (<100ms)
- [ ] Connection pool working

---

### PHASE 3: Service Layer (3-4 hours)
**Goal:** Business logic with validation and error handling

**Implement Services:**
1. **UserService** - Registration, authentication, profile updates
2. **ProjectService** - CRUD, lifecycle management
3. **SessionService** - Session creation, mode toggling, archiving
4. **MessageService** - Message persistence, retrieval, response handling
5. **PreferenceService** - Settings load/save with persistence
6. **AuditService** - Logging all changes

**Key Features Per Service:**
- Input validation (Marshmallow schemas)
- Business rule enforcement
- Error handling with meaningful messages
- Audit logging
- Transaction management
- Caching where appropriate

**Tests to Pass:**
- [ ] All CRUD operations work
- [ ] Validation catches invalid input
- [ ] Errors are meaningful
- [ ] Audit log captures all changes
- [ ] Data persists correctly

---

### PHASE 4: API Layer Refactoring (3-4 hours)
**Goal:** Clean, consistent API endpoints

**Changes:**
1. Remove business logic from routes
2. Add request validation
3. Add response formatting
4. Add error handling middleware
5. Remove duplicate code

**New Pattern:**
```python
@api.route('/projects', methods=['POST'])
@require_authentication
@validate_json
def create_project(data, user):
    """Create new project"""
    try:
        service = ProjectService(...)
        project = service.create(data, user.id)
        return jsonify({'success': True, 'data': project})
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Project creation failed: {e}")
        return jsonify({'success': False, 'error': 'Internal error'}), 500
```

**Tests to Pass:**
- [ ] All endpoints return JSON consistently
- [ ] Validation works
- [ ] Error messages are helpful
- [ ] No duplicate endpoints
- [ ] Response format matches spec

---

### PHASE 5: Critical Features Fix (3-4 hours)

#### 5a: Message Persistence (CRITICAL)
**Current:** Returns hardcoded fake responses
**Fix:**
```python
# Message flow:
1. User sends message
2. MessageService.persist_message(session_id, user_id, content)
   - Saves to messages table
   - Returns message ID
3. MessageService.generate_response(session_id, user_id, message_id)
   - Calls agent for response
   - Saves response message
   - Returns response ID
4. Frontend receives both message and response
```

**Tests:**
- [ ] Message saves to database
- [ ] Response saves to database
- [ ] Both persist after refresh
- [ ] Can retrieve conversation history

#### 5b: Profile Update Persistence (CRITICAL)
**Current:** Success API but data doesn't save
**Fix:**
```python
# Profile update flow:
1. Validate new data
2. Check for conflicts (email uniqueness)
3. Save to database using ORM
4. Log change in audit
5. Return success with saved data
```

**Tests:**
- [ ] Profile field saves correctly
- [ ] Email uniqueness enforced
- [ ] Changes persist after refresh
- [ ] Audit log records change

#### 5c: Settings Persistence
**Current:** Saves but doesn't load
**Fix:**
```python
# Settings flow:
1. Save to user_preferences table (not scattered around)
2. Load from one source on app start
3. Cache in memory with TTL
4. Invalidate cache on update
```

**Tests:**
- [ ] Settings save
- [ ] Settings load correctly
- [ ] Cache works
- [ ] Persist across restarts

---

### PHASE 6: Code Quality & Architecture (2-3 hours)

**Remove Greedy Patterns:**
1. ❌ "Will implement X later" → ✅ Implement properly now
2. ❌ Copy-paste code → ✅ Extract to shared functions
3. ❌ Magic strings → ✅ Use enums/constants
4. ❌ Silent failures → ✅ Log and return errors
5. ❌ No validation → ✅ Validate all inputs
6. ❌ Monolithic files → ✅ Split into modules

**Refactor Structure:**
```
Current (BAD - 3900 line file):
web/app.py  ← Everything here

Proposed (GOOD):
web/
├── app.py           ← App factory + middleware
├── routes.py        ← Route registration
├── handlers/
│   ├── auth.py
│   ├── projects.py
│   ├── sessions.py
│   └── messages.py
└── middleware/
    ├── auth.py
    ├── error.py
    └── validation.py

src/
├── services/        ← Business logic
├── repositories/    ← Data access
├── models/          ← SQLAlchemy models
└── schemas/         ← Validation schemas
```

---

## PART 6: UI FRAMEWORK ANALYSIS

### Flask (Current)
**Pros:**
- Simple to learn
- Good for prototypes
- Lightweight

**Cons:**
- Not designed for complex UIs
- Requires separate frontend framework
- Server-side rendering is outdated
- State management difficult
- Not scalable for large apps

### Better Options for This Project

#### Option A: FastAPI + React/Vue (RECOMMENDED)
**Why:** Modern, professional, scalable
```
Frontend: React/Vue with TypeScript
- Component-based UI
- State management (Redux/Pinia)
- Real-time updates with WebSocket
- Professional dev tools

Backend: FastAPI
- Async-first design
- Automatic OpenAPI docs
- Type validation with Pydantic
- Better performance than Flask
- Middleware system

Database: PostgreSQL (not SQLite)
- ACID transactions
- Better concurrency
- Proper migrations
- Production-ready
```

#### Option B: FastAPI + React (MOST PROFESSIONAL)
```
Tech Stack:
- Frontend: React 18 + TypeScript + TailwindCSS
- Backend: FastAPI + SQLAlchemy
- Database: PostgreSQL
- Caching: Redis
- Deployment: Docker + Kubernetes
- Testing: Pytest + Jest
```

#### Option C: Keep Flask but Properly
```
Add:
- Blueprints for route organization
- SQLAlchemy ORM properly
- Marshmallow for validation
- Celery for async tasks
- Redis for caching
- Better error handling
```

### RECOMMENDATION
**FastAPI + React** is the best choice because:
1. **Scalability** - Built for growth
2. **Type Safety** - Catch errors early
3. **Developer Experience** - Modern tooling
4. **Performance** - Async by default
5. **Community** - Growing ecosystem
6. **Professional** - Used in production by major companies

**Estimated Rewrite Time:** 1-2 weeks (not urgent, can be done after optimization)

---

## PART 7: TESTING STRATEGY

### Automated Test Suite (Already Built)
**File:** `tests/test_complete_ui_workflow.py`
- 24 integration tests
- Tests complete user workflows
- Verifies database persistence
- Can be run after each phase

**Current Status:**
- 9/24 passing (UI/API responses work)
- 15/24 failing (persistence/database issues)

### Phase-by-Phase Testing

**After Phase 1 (Database):**
```python
✓ Test database tables exist
✓ Test relationships work
✓ Test constraints enforced
✓ Test sample data queryable
```

**After Phase 2 (Repositories):**
```python
✓ Test CRUD operations
✓ Test transactions
✓ Test query performance
✓ Test connection pooling
```

**After Phase 3 (Services):**
```python
✓ Test input validation
✓ Test business logic
✓ Test error handling
✓ Test audit logging
```

**After Phase 4 (API):**
```python
✓ Test endpoint responses
✓ Test error handling
✓ Test authentication
✓ Run automated UI tests
```

**After Phase 5 (Critical Features):**
```python
✓ Test message persistence
✓ Test profile updates
✓ Test settings persistence
✓ Test data survives refresh
✓ RUN FULL AUTOMATED TEST SUITE → All 24 tests should pass
```

---

## PART 8: IMPLEMENTATION CHECKLIST

### Phase 1: Database
- [ ] Create migration system (Alembic)
- [ ] Define all tables (copy SQL above)
- [ ] Create indexes
- [ ] Create audit table
- [ ] Run migrations
- [ ] Verify tables exist
- [ ] Add test data

### Phase 2: Repositories
- [ ] Create base_repository.py
- [ ] Implement user_repository.py
- [ ] Implement project_repository.py
- [ ] Implement session_repository.py
- [ ] Implement message_repository.py
- [ ] Implement preference_repository.py
- [ ] Implement audit_repository.py
- [ ] Add transaction support
- [ ] Add error handling
- [ ] Write repository tests

### Phase 3: Services
- [ ] Create base_service.py
- [ ] Implement user_service.py
- [ ] Implement project_service.py
- [ ] Implement session_service.py
- [ ] Implement message_service.py
- [ ] Implement preference_service.py
- [ ] Implement document_service.py
- [ ] Implement audit_service.py
- [ ] Add validation schemas (Marshmallow)
- [ ] Add error handling
- [ ] Write service tests

### Phase 4: API Refactoring
- [ ] Create API blueprint structure
- [ ] Refactor user endpoints
- [ ] Refactor project endpoints
- [ ] Refactor session endpoints
- [ ] Refactor message endpoints
- [ ] Refactor settings endpoints
- [ ] Add request validation
- [ ] Add response formatting
- [ ] Add error middleware
- [ ] Remove duplicate code

### Phase 5: Critical Features
- [ ] Implement real message persistence
- [ ] Implement agent response calling
- [ ] Implement profile persistence
- [ ] Implement settings persistence
- [ ] Add response/message storage
- [ ] Add message retrieval
- [ ] Test end-to-end workflows

### Phase 6: Code Quality
- [ ] Remove greedy patterns
- [ ] Extract duplicated code
- [ ] Use enums/constants
- [ ] Add logging everywhere
- [ ] Add error messages
- [ ] Reorganize file structure
- [ ] Update documentation

### Phase 7: Testing & Verification
- [ ] Run automated test suite
- [ ] Fix any failing tests
- [ ] Verify all 24 tests pass
- [ ] Performance testing
- [ ] Load testing
- [ ] Manual testing of critical flows

---

## PART 9: ESTIMATED TIMELINE

```
Phase 1 (Database):        2-3 hours
Phase 2 (Repositories):    2-3 hours
Phase 3 (Services):        3-4 hours
Phase 4 (API Refactor):    3-4 hours
Phase 5 (Critical Fix):    3-4 hours
Phase 6 (Code Quality):    2-3 hours
Phase 7 (Testing):         2-3 hours
                          ───────────
                TOTAL:    18-24 hours
```

**Broken into sessions:**
- Session 1: Phases 1-2 (4-6 hours)
- Session 2: Phases 3-4 (6-8 hours)
- Session 3: Phases 5-7 (8-10 hours)

---

## PART 10: MIGRATION FROM CURRENT STATE

### Step 1: Parallel Development
```
Keep Flask app running (old)
Build new structure in src/services/ (new)
```

### Step 2: Integration Points
```
1. Create repository layer first (doesn't break existing)
2. Create services layer (parallel with routes)
3. Update routes one at a time to use services
4. Gradually migrate to new patterns
```

### Step 3: Zero-Downtime Migration
```
1. Database: Add new tables alongside old
2. Services: Create new services without modifying routes
3. Routes: Switch to services gradually
4. Tests: Run automated tests to verify
5. Remove: Clean up old code
```

---

## PART 11: WHAT NOT TO DO (Anti-Patterns)

❌ **DON'T:**
1. Make "small quick fixes" - leads to more mess
2. Copy-paste code - leads to maintenance nightmare
3. Skip validation - leads to corrupted data
4. Have silent failures - leads to user confusion
5. Mix business logic in routes - leads to complexity
6. Use magic strings everywhere - leads to bugs
7. Skip error handling - leads to crashes
8. Assume "we'll fix later" - we won't

✅ **DO:**
1. Plan before implementing
2. Extract reusable code to services
3. Validate all inputs
4. Log all errors
5. Separate concerns (routes/services/repos)
6. Use constants and enums
7. Handle errors explicitly
8. Fix issues as they appear

---

## PART 12: SUCCESS CRITERIA

**When optimization is complete:**
- [ ] All 24 automated tests pass
- [ ] Database properly normalized
- [ ] All data persists correctly
- [ ] Message workflow functional
- [ ] Profile updates persistent
- [ ] Settings survive restart
- [ ] No greedy patterns remain
- [ ] Code organized into modules
- [ ] Error handling consistent
- [ ] Audit logging working
- [ ] No silent failures
- [ ] Performance acceptable (<500ms per request)
- [ ] Code is maintainable
- [ ] New developers can understand code
- [ ] Ready for production deployment

---

## PART 13: FUTURE IMPROVEMENTS (After Optimization)

### Phase 8: Real-Time Features
- WebSocket support for live messages
- Real-time user presence
- Live notifications
- Chat typing indicators

### Phase 9: Agent Integration
- Proper agent response generation
- Agent orchestration
- Response caching
- Cost tracking

### Phase 10: Analytics & Monitoring
- Usage metrics
- Performance monitoring
- Error tracking (Sentry)
- User analytics

### Phase 11: UI Framework Upgrade
- Migrate to FastAPI + React
- Modern component system
- Better state management
- Professional UX

### Phase 12: Scalability
- Database migration to PostgreSQL
- Redis caching
- Microservices architecture
- Docker/Kubernetes deployment

---

## CONCLUSION

This project needs **architectural optimization**, not just bug fixes. The foundation is broken, so patching individual issues won't solve the problem.

**Recommendation:** Follow the phases above sequentially. Each phase builds on the previous one and can be tested independently. By the end, you'll have a professional, maintainable, production-ready system.

**Time Investment:** 18-24 hours for complete optimization

**ROI:**
- Maintainable codebase for years
- Easy to add features
- Professional quality
- Ready for production
- Scalable architecture

**Start Date:** Next session
**Execution Method:** Follow phases sequentially, run automated tests after each phase

---

**End of Optimization Workflow Document**
