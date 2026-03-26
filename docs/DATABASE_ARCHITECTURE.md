# Socrates Database Architecture

## Overview

Socrates uses a **two-tier database architecture** that clearly separates concerns between the API layer and the core system:

- **LocalDatabase** (SQLite): API-specific data (projects, users, sessions)
- **ProjectDatabase** (SQLite): Complete domain model (everything else)

This architecture ensures:
- ✅ **Separation of concerns**: Each layer owns its data
- ✅ **Clear responsibilities**: No mixing of API and domain logic
- ✅ **Scalability**: Core system can migrate to PostgreSQL without affecting API
- ✅ **PyPI library purity**: No database access in reusable libraries
- ✅ **Event-driven persistence**: Async callbacks for data consistency

---

## Why Two Databases?

### Single Responsibility Principle

Different layers have different responsibilities:

1. **API Layer** (FastAPI)
   - Handles HTTP requests/responses
   - Manages user sessions
   - Tracks API projects and metadata
   - Concerns: Performance for API calls, quick access to session data

2. **Core System** (Socrates Domain)
   - Handles business logic (learning, analysis, quality gating)
   - Manages comprehensive project state
   - Stores all learning analytics
   - Concerns: Comprehensive data, complex queries, historical tracking

### Different Query Patterns

**API Layer Queries:**
- "What projects does user X own?"
- "Is this refresh token valid?"
- "Get project metadata"

**Core System Queries:**
- "What is the maturity progression for project X?"
- "What are weak areas in phase Y?"
- "Show conversation history"
- "Get all requirements for project X"
- "What skills were generated from this session?"

### Different Scale & Performance Requirements

**API Layer:**
- Small dataset (active sessions, user accounts)
- Frequent, simple queries
- Latency-sensitive (HTTP requests)
- SQLite is ideal

**Core System:**
- Large dataset (years of learning data, analytics)
- Complex queries with joins
- Batch processing acceptable
- PostgreSQL planned for future (better for 100GB+ datasets)

### Different Evolution Paths

**API Layer:**
- May stay SQLite forever (doesn't grow much)
- User data lifecycle matches project lifecycle
- Schema relatively stable

**Core System:**
- Will migrate to PostgreSQL as Socrates scales
- Vector DB integration for RAG
- Continuous schema evolution (migrations managed)
- Read replicas needed for analytics

---

## Database Tiers

### Tier 1: LocalDatabase (API Layer)

**Location:** `backend/src/socrates_api/database.py`

**Database File:** `~/.socrates/api_projects.db`

**Purpose:** RESTful API data (projects, users, authentication)

**Schema:**

```sql
-- Projects managed by API
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    owner TEXT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT,
    updated_at TEXT,
    phase TEXT DEFAULT 'discovery',
    is_archived INTEGER DEFAULT 0,
    metadata TEXT
);

-- User accounts
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    passcode_hash TEXT,
    subscription_tier TEXT DEFAULT 'free',
    subscription_status TEXT DEFAULT 'active',
    testing_mode INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT,
    metadata TEXT
);

-- Refresh token management
CREATE TABLE refresh_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revoked_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(username)
);

CREATE INDEX idx_user_tokens ON refresh_tokens(user_id);
CREATE INDEX idx_expires ON refresh_tokens(expires_at);
```

**Dependency Injection:**
```python
from socrates_api.database import get_database, LocalDatabase

async def my_endpoint(db: LocalDatabase = Depends(get_database)):
    project = db.get_project(project_id)
    user = db.load_user(username)
```

**Used By:** 26 router files (auth.py, projects.py, chat.py, etc.)

**Methods:**
- `create_project(project_id, name, description, owner, metadata)`
- `get_project(project_id)`
- `load_project(project_id)` - Alias for get_project
- `save_project(project)`
- `list_projects(limit)`
- `get_user_projects(username)` - Projects owned or collaborated on
- `create_user(user_id, username, email, passcode_hash, metadata)`
- `get_user(user_id)`
- `load_user(username)` - Get by username
- `load_user_by_email(email)`
- `save_user(user_data)`

**Features:**
- Schema migrations (auto-adds missing columns)
- Singleton pattern via `DatabaseSingleton`
- `check_same_thread=False` for async support
- Connection pooling via SQLite's built-in pooling

---

### Tier 2: ProjectDatabase (Core System)

**Location:** `socratic_system/database/project_db.py`

**Database File:** `~/.socrates/projects.db`

**Purpose:** Complete Socrates domain model (no pickled BLOBs)

**Schema (Normalized v2 - 50+ tables):**

```
CORE DOMAIN:
- projects (denormalized for speed: maturity_scores, tech_stack, etc.)
- project_phases (phase-specific data and metrics)
- users (user profiles with learning metadata)
- project_analytics (KPI metrics)

CONVERSATION:
- chat_sessions (session metadata)
- chat_messages (individual messages)
- conversation_history (thread structure)

KNOWLEDGE:
- knowledge_documents (RAG documents)
- project_knowledge (project-specific knowledge)
- embeddings (vector DB integration)

BUSINESS LOGIC:
- project_notes (notes with full-text search)
- project_requirements (originally in project BLOB)
- project_tech_stack (originally in project BLOB)
- project_constraints (originally in project BLOB)
- team_members (collaboration)
- project_invitations (team invites)
- activities (audit log)

WORKFLOWS:
- workflows (workflow definitions)
- workflow_executions (execution history)
- workflow_steps (individual steps)

LEARNING & METRICS:
- question_effectiveness (learning metrics)
- behavior_patterns (user behavior analysis)
- learning_sessions (learning analytics)
- analysis_results (analysis history)
- performance_metrics (system performance)

ADVANCED:
- conflicts (project conflict tracking)
- llm_config (LLM provider configurations)
- api_keys (encrypted API keys)
- usage_records (LLM API usage tracking)
- incidents (security incidents log)
- chat_sessions_archived (conversation versioning)

INDEX: 50+ optimized indices for common queries
FOREIGN KEYS: Cascade deletes enabled
MIGRATIONS: MigrationRunner handles schema evolution
ENCRYPTION: Optional field-level encryption
```

**Access Pattern:**
```python
from socratic_system.database import DatabaseSingleton

db = DatabaseSingleton.get_instance()
project = db.load_project(project_id)
maturity = project.phase_maturity_scores
requirements = db.get_project_requirements(project_id)  # Separate table query
```

**Used By:** 9 core system files (orchestrator.py, project_db.py, etc.)

**Key Difference:** Normalized schema - no pickled BLOBs
- `project_requirements` separate table (not in project blob)
- `project_tech_stack` separate table (not in project blob)
- `project_constraints` separate table (not in project blob)
- All fields queryable and indexable
- 10-20x faster queries than denormalized BLOB approach
- Can run analytics queries directly

---

## Layer Boundaries

### Import Boundaries (Strict)

**API Layer Can Import:**
```python
from socrates_api.database import LocalDatabase, get_database
from socrates_api.models_local import ProjectContext, User
```

**✗ API Layer CANNOT Import:**
```python
from socratic_system.database import ProjectDatabase  # FORBIDDEN
from socratic_system.database import DatabaseSingleton  # FORBIDDEN
```

**Core System Can Import:**
```python
from socratic_system.database import ProjectDatabase, DatabaseSingleton
from socratic_system.models.project import ProjectContext
```

**✗ Core System CANNOT Import:**
```python
from socrates_api.database import LocalDatabase  # FORBIDDEN (would create circular dependency)
```

**PyPI Libraries (socratic-agents) Can Import:**
```python
# Nothing database-related
# All persistence via dependency injection and callbacks
```

### Data Flow

```
FastAPI Request
    ↓
LocalDatabase (API metadata only)
    ├─ User exists? → load from LocalDatabase
    ├─ Project exists? → load from LocalDatabase
    ↓
Core System Orchestration
    ├─ Need full project state? → ProjectDatabase
    ├─ Need analytics? → ProjectDatabase
    ├─ Need conversation history? → ProjectDatabase
    ↓
Agents process request (no DB access)
    ↓
Events emitted (EventRecorder.record_event)
    ↓
Event callbacks (on_event hook)
    ├─ Update ProjectDatabase (maturity, analytics)
    ├─ Emit webhooks
    ├─ Log to audit trail
    ↓
Response to user
```

---

## How They're Synchronized

### Push Synchronization (Event-Driven)

When API endpoint creates a project:

```python
# POST /projects (in projects.py)
result = orchestrator.create_project(
    name=request.name,
    description=request.description,
    user_id=current_user
)

# 1. API layer saves to LocalDatabase
db_result = db.create_project(
    project_id=result["id"],
    owner=current_user,
    name=request.name,
    # ... etc
)

# 2. Orchestrator triggers event
record_event(
    "PROJECT_CREATED",
    data={
        "project_id": result["id"],
        "owner": current_user,
        "name": request.name
    }
)

# 3. Core system event handler (via on_event callback)
def _on_coordination_event(event, data):
    if event.value == "PROJECT_CREATED":
        # Save full project to ProjectDatabase
        core_db.save_project(ProjectContext(...))
        # Initialize analytics
        core_db.initialize_project_analytics(data["project_id"])
```

### Consistency Strategy

- **LocalDatabase is source of truth for API state** (auth, session data)
- **ProjectDatabase is source of truth for domain state** (learning, analytics)
- **Events ensure consistency** (changes in one trigger updates in other)
- **No direct cross-database reads** (always go through event callbacks)

### Conflict Resolution

If inconsistency detected:
1. **Reload from authoritative source** (determined by record type)
2. **Emit consistency event** (log for debugging)
3. **Return fresh data** (don't serve stale data)

---

## Migration Strategy to PostgreSQL

### Phase 1: Present (SQLite for Both)

```
~/.socrates/api_projects.db (LocalDatabase)
~/.socrates/projects.db (ProjectDatabase)
```

**Advantages:**
- Zero deployment complexity
- Single-machine development/small-scale
- No external dependencies
- Suitable for teams < 100 users

### Phase 2: Hybrid (LocalDatabase stays SQLite, ProjectDatabase → PostgreSQL)

```
~/.socrates/api_projects.db (LocalDatabase - SQLite)
    ↓
postgresql://socrates/projects (ProjectDatabase - PostgreSQL)
```

**Advantages:**
- API stays simple (SQLite)
- Core system gets PostgreSQL benefits (scalability, replication, backups)
- Transactions across databases via event consistency
- No breaking changes to API layer

**Migration Steps:**
1. Create PostgreSQL schema (schema_v2_postgres.sql)
2. Run migration tool: `python scripts/migrate_to_postgres.py`
3. Test with dual-write (write to both during transition)
4. Flip switch to PostgreSQL-only reads
5. Remove SQLite as fallback

### Phase 3: Full PostgreSQL (Both Databases)

```
postgresql://socrates/api (LocalDatabase - PostgreSQL)
postgresql://socrates/projects (ProjectDatabase - PostgreSQL)
```

**Advantages:**
- High availability (read replicas)
- Backups and point-in-time recovery
- Advanced analytics (streaming aggregations)
- Vector DB integration for RAG

### Phase 4: Sharding (Optional - Very Large Scale)

```
PostgreSQL Cluster (partitioned by user_id)
- Shard 1: Users A-M
- Shard 2: Users N-Z
- Leader: API access (single node)
- Followers: Analytics (distributed)
```

---

## Implementation Notes

### LocalDatabase Implementation

```python
class LocalDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = Path.home() / ".socrates"
            db_path = str(data_dir / "api_projects.db")
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
```

**Key Methods:**
- `_initialize()` - Creates tables and indices
- `_migrate_schema()` - Adds missing columns
- `load_user()` - Get user by username (for auth)
- `get_user_projects()` - Get projects user owns/collaborates on
- `save_project()` - Create or update project metadata

### ProjectDatabase Implementation

```python
class ProjectDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = Path(os.getenv("SOCRATES_DATA_DIR", Path.home() / ".socrates"))
            db_path = str(data_dir / "projects.db")
        self.db_path = db_path
        self.conn = sqlite3.connect(str(self.db_path))
```

**Key Features:**
- `MigrationRunner` - Handles schema evolution
- `ConnectionPool` - Manages concurrent connections
- `ReadWriteSplit` - Separates read replicas
- `Encryption` - Optional field-level encryption
- `VectorDB` - Integrated embedding storage

---

## Best Practices

### 1. Know Which Database to Use

**Use LocalDatabase for:**
- ✓ User authentication
- ✓ Active project list
- ✓ Session management
- ✓ User metadata (tier, status)

**Use ProjectDatabase for:**
- ✓ Complete project state
- ✓ Conversation history
- ✓ Learning analytics
- ✓ Maturity tracking
- ✓ Requirements/tech stack
- ✓ Audit logs

### 2. Never Access ProjectDatabase from API Layer

```python
# WRONG: Don't do this in routers
from socratic_system.database import ProjectDatabase
db = ProjectDatabase()
analytics = db.get_project_analytics(project_id)

# RIGHT: Use local database + orchestrator
from socrates_api.database import get_database
project = db.get_project(project_id)  # Get metadata
# If you need full state, call orchestrator:
full_state = orchestrator.get_project_state(project_id)
```

### 3. Use Events for Cross-Database Consistency

```python
# WRONG: Direct cross-database updates
local_db.save_project(project_data)
core_db.save_project(project_data)

# RIGHT: Event-driven consistency
local_db.save_project(project_data)
record_event("PROJECT_UPDATED", {"project_id": project_id})
# Core system updates via on_event callback
```

### 4. PyPI Libraries Should Never Import Database

```python
# agents in socratic-agents

# WRONG: Direct database access
from socratic_system.database import ProjectDatabase
class MyAgent:
    def process(self, request):
        db = ProjectDatabase()
        project = db.load_project(request["project_id"])

# RIGHT: Dependency injection
class MyAgent:
    def process(self, request, context=None):
        # Work with request data, return result
        # Let caller handle persistence
        return {"analysis": "..."}
```

### 5. Environment Configuration

```bash
# .env file (or environment variables)

# API Layer
SOCRATES_API_DATABASE_PATH=~/.socrates/api_projects.db

# Core System
SOCRATES_DATA_DIR=~/.socrates
# Projects DB will be at: ~/.socrates/projects.db

# Future PostgreSQL
SOCRATES_DATABASE_URL=postgresql://user:pass@localhost/socrates
SOCRATES_DATABASE_READONLY_URL=postgresql://user:pass@replica/socrates  # For analytics
```

---

## Troubleshooting

### Issue: "No such table: projects"

**Cause:** LocalDatabase tables not initialized

**Solution:**
```python
from socrates_api.database import DatabaseSingleton
db = DatabaseSingleton.get_instance()  # Auto-initializes
```

### Issue: Maturity scores not syncing between databases

**Cause:** Event callback not registered

**Solution:**
```python
manager = get_library_manager(api_key=api_key)
manager.set_event_callback(on_coordination_event)
```

### Issue: Slow analytics queries

**Cause:** Querying denormalized LocalDatabase instead of normalized ProjectDatabase

**Solution:**
```python
# SLOW: Querying API database
local_db.query("SELECT * FROM projects WHERE ...")

# FAST: Query core system normalized schema
core_db.get_project_analytics(project_id)
core_db.get_phase_progression(project_id)
```

### Issue: Projects exist in LocalDatabase but not in ProjectDatabase

**Cause:** Event callback failed to record event

**Solution:**
1. Check logs for event callback errors
2. Manually trigger: `record_event("PROJECT_CREATED", data)`
3. Verify on_event callback is registered
4. Check core_db connections are working

---

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│             FastAPI Web Server                             │
├────────────────────────────────────────────────────────────┤
│   HTTP Endpoints (26 routers)                              │
│   /auth, /projects, /chat, /knowledge, etc.                │
└────────┬─────────────────────────────────────┬─────────────┘
         │                                       │
         │ get_database()                        │ Orchestrator
         ↓                                       ↓
    ┌─────────────────┐           ┌──────────────────────┐
    │ LocalDatabase   │           │  Agent Orchestration │
    │ (API Layer)     │◄──────────│  (Business Logic)    │
    │                 │ Event     │                      │
    │ 3 tables        │ Callback  │  PureOrchestrator    │
    │ users           │───┐       │  Agents              │
    │ projects        │   │       │  Quality gating      │
    │ tokens          │   │       └──────────────────────┘
    └─────────────────┘   │
                          │
                          ↓
                    ┌──────────────────────┐
                    │ Event Recording      │
                    │ (In-Memory Queue)    │
                    └──────────┬───────────┘
                               │
                               ↓
                    ┌──────────────────────┐
                    │ Event Callbacks      │
                    │ on_event(event,data) │
                    └──────────┬───────────┘
                               │
                               ↓
                    ┌──────────────────────┐
                    │ ProjectDatabase      │
                    │ (Core System)        │
                    │                      │
                    │ 50+ normalized       │
                    │ tables               │
                    │                      │
                    │ Features:            │
                    │ - Migrations         │
                    │ - Encryption         │
                    │ - Vector DB          │
                    │ - Full-text search   │
                    └──────────────────────┘
```

---

## See Also

- **[Maturity System](./MATURITY_SYSTEM.md)** - How maturity scores are calculated and stored
- **[API Documentation](./API_ENDPOINTS.md)** - All API endpoints and their database usage
- **[Performance Guide](./PERFORMANCE_TUNING.md)** - Database query optimization
- **[Migration Guide](./MIGRATION_GUIDE.md)** - Steps to migrate to PostgreSQL
