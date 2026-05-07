# New User Onboarding Issues - Root Cause Analysis

## Problems Identified

### 1. **CRITICAL: Migration Files Not Found**
**Status**: Active blocker for new users

**Location**: `socratic_system/database/migration_runner.py` (lines 30-32, 48-54)

```python
archive_dir = Path(__file__).parent.parent.parent / "archive" / "migration_scripts"
root_dir = Path(__file__).parent.parent.parent / "migration_scripts"
self.migration_dir = archive_dir if archive_dir.exists() else root_dir
```

**Problem**:
- If neither `archive/migration_scripts/` nor `migration_scripts/` directory exists, migrations are silently skipped
- Optional migrations log at DEBUG level (hidden by default)
- Critical migrations fail silently at ERROR level when files are missing
- Schema is created but columns required by code may not exist

**Evidence**:
```python
# Lines 48-54: Silent failure for optional migrations
if not migration_path.exists():
    msg = f"Migration file not found: {migration_path}"
    if is_optional:
        self.logger.debug(msg)  # Only logged at DEBUG level!
    else:
        self.logger.error(msg)  # Error logged but execution continues
    return False, msg
```

**Impact on New Users**:
- Database schema created but migrations not applied
- Code expects columns that don't exist (e.g., `users.claude_auth_method`)
- Runtime errors when accessing these columns

**Critical Migration Dependencies**:
```
add_claude_auth_method_column.sql       - REQUIRED by user authentication
add_knowledge_documents_columns.sql     - REQUIRED by knowledge base operations
add_code_history_column.sql             - Optional but used if present
add_github_import_tables.sql            - Optional but used if present
```

---

### 2. **HIGH: API Key Not Validated Before Orchestrator Initialization**
**Status**: Partially fixed (with workaround)

**Location**: `socratic_system/ui/main_app.py` (lines 385-394)

```python
if api_key == "subscription_mode":
    self.orchestrator = AgentOrchestrator("subscription_placeholder_key")
else:
    self.orchestrator = AgentOrchestrator(api_key)  # Could be None or empty!
```

**Problem**:
- API key is optional in the CLI flow (`_get_api_key()`)
- User can skip providing a key
- Orchestrator is created with None or empty string
- ClaudeClient initialization doesn't validate the key
- Errors occur later when API is actually called

**Evidence** from `SocratesConfig.from_env()`:
```python
api_key: Optional[str] = None  # Can be None!
```

**Current Workaround**:
- Subscription mode uses placeholder key "subscription_placeholder_key"
- API key mode requires user input via `getpass.getpass()`

**Issue with Workaround**:
- If user just presses Enter at the prompt, empty string is accepted
- No validation that key starts with "sk-ant-" or "sk-" format
- No check if key is valid until API is called

---

### 3. **HIGH: No Default Onboarding Projects for New Users**
**Status**: Confirmed gap

**Location**: `socratic_system/models/user.py` (lines 8-10)

```python
@dataclass
class User:
    projects: Optional[List[str]] = None  # New users: empty list []
```

**Problem**:
- New users start with `projects = []` (empty list)
- No "Getting Started" or tutorial project created
- No onboarding project to guide new users
- Users see blank project list and don't know what to do next

**Flow**:
1. User registers → User model created with `projects=[]`
2. User sees "No projects" message
3. User must manually create a project via `/project create`
4. No guidance or template provided

---

### 4. **MEDIUM: Async Race Condition in DatabaseSingleton**
**Status**: Potential issue for API mode (multi-user)

**Location**: `socrates-api/database.py` (lines ~50-60)

```python
class DatabaseSingleton:
    _instance = None

    @classmethod
    def initialize(cls, db_path: str):
        if cls._instance is None:
            cls._instance = ProjectDatabase(db_path)  # Only runs once!
```

**Problem**:
- Singleton only initializes once globally
- In API mode with multiple concurrent users, initialization happens only for first request
- Subsequent users would use same database connection
- If different users have different data directories, subsequent users get wrong path

---

### 5. **MEDIUM: User Subscription Data Not Validated**
**Status**: Potential runtime issue

**Location**: `socratic_system/models/user.py` (lines 29-30)

```python
subscription_tier: str = "free"           # Assumed to exist
subscription_status: str = "active"       # Assumed to exist
```

**Problem**:
- New users created without validating subscription fields
- Code assumes these fields exist and are non-NULL
- Schema has defaults but in-memory User object might not
- Downstream code checks subscription without null-safety

---

## New User Onboarding Flow (Current)

```
1. Start Socrates
   ↓
2. User provides API key or chooses subscription mode
   ↓
3. Orchestrator initialized with API key
   - Database created
   - Migrations attempted (may fail silently)
   - Schema created but columns might not exist
   ↓
4. User registers/logs in
   - New User created with projects=[]
   - Subscription fields initialized
   ↓
5. User sees main menu
   ↓
6. User has empty projects list
   - No guidance
   - No tutorial
   - Must manually create project
```

---

## Fixes Required

### Fix 1: Validate Migration Files at Startup ✅ IMPLEMENT
**Priority**: CRITICAL

**Changes**:
1. Check if migration directory exists at startup
2. Verify critical migration files exist before database is created
3. Fail fast with clear error message if migrations missing
4. Provide remediation instructions

**Implementation**:
```python
def validate_migrations_available(self):
    """Validate that migration files are accessible"""
    critical_migrations = [
        "add_claude_auth_method_column.sql",
        "add_knowledge_documents_columns.sql"
    ]

    missing = []
    for migration_file in critical_migrations:
        if not (self.migration_dir / migration_file).exists():
            missing.append(migration_file)

    if missing:
        raise MigrationFilesNotFound(
            f"Critical migration files missing: {missing}\n"
            f"Expected in: {self.migration_dir}\n"
            f"Install from package archive if needed"
        )
```

---

### Fix 2: Validate API Key Before Orchestrator Init ✅ IMPLEMENT
**Priority**: CRITICAL

**Changes**:
1. Validate API key format before orchestrator creation
2. Provide clear error if key is empty/invalid
3. Don't initialize expensive components if API key missing
4. Allow subscription-only mode without API key

**Implementation**:
```python
def validate_api_key_or_subscription(api_key: str) -> bool:
    """Validate API key format or subscription mode"""
    if api_key == "subscription_mode":
        return True  # Will validate during user auth

    if not api_key or not isinstance(api_key, str):
        raise ValueError("API key required or select subscription mode")

    if not (api_key.startswith("sk-ant-") or api_key.startswith("sk-")):
        raise ValueError(f"Invalid API key format: {api_key[:10]}...")

    return True
```

---

### Fix 3: Create Default Onboarding Project ✅ IMPLEMENT
**Priority**: HIGH

**Changes**:
1. Create "Getting Started" project when new user registers
2. Pre-populate with example requirements and tech stack
3. Mark as template/example project
4. Guide user to customize it

**Implementation**:
```python
def create_onboarding_project(user: User) -> ProjectContext:
    """Create default onboarding project for new user"""
    return ProjectContext(
        project_id=str(uuid.uuid4()),
        name="Getting Started - My First Project",
        description="Customize this template to start your Socratic journey",
        owner=user.username,
        phase="discovery",
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        is_system_project=True,
        system_project_type="onboarding",
        requirements=[
            "Define what you want to build",
            "Identify key features needed",
            "List any constraints or dependencies"
        ],
        tech_stack=["Python"],  # Example
        goals="Get familiar with Socrates project management"
    )
```

---

### Fix 4: Add Database Initialization Checklist ✅ IMPLEMENT
**Priority**: MEDIUM

**Changes**:
1. After database initialization, verify schema is complete
2. Check all required tables and columns exist
3. Log initialization status at INFO level
4. Warn if any critical migrations are missing

**Implementation**:
```python
def _verify_database_integrity(self):
    """Verify database has all required tables and columns"""
    required_tables = ["users", "projects", "knowledge_documents"]
    required_columns = {
        "users": ["username", "email", "passcode_hash", "claude_auth_method"],
        "projects": ["project_id", "owner", "name", "code_history"],
        "knowledge_documents": ["id", "project_id", "content", "file_path", "file_size"]
    }

    # Check all tables exist
    for table in required_tables:
        if not self.table_exists(table):
            raise DatabaseIntegrityError(f"Missing table: {table}")

    # Check all columns exist
    for table, columns in required_columns.items():
        for column in columns:
            if not self._column_exists(table, column):
                raise DatabaseIntegrityError(
                    f"Missing column {table}.{column}\n"
                    f"This suggests migrations were not applied.\n"
                    f"Check migration files and run: socrates --reinit-db"
                )
```

---

### Fix 5: Thread-Safe DatabaseSingleton ✅ IMPLEMENT
**Priority**: MEDIUM (for API mode)

**Changes**:
1. Add locking for initialization
2. Queue concurrent initialization requests
3. Validate db_path matches on retry
4. Provide clear error if paths don't match

---

## Implementation Plan

### Phase 1: Critical Fixes (Blocking Issues)
1. ✅ Validate migration files exist before using them
2. ✅ Validate API key format before orchestrator init
3. ✅ Create default onboarding project for new users

### Phase 2: Robustness
4. ✅ Add database initialization checklist
5. ✅ Make DatabaseSingleton thread-safe

### Phase 3: UX Improvements
6. Add explicit onboarding wizard
7. Create project templates
8. Add subscription validation

---

## Testing New User Flow After Fixes

```bash
# 1. Clean up database
rm -f ~/.socrates/projects.db
rm -rf ~/.socrates/vector_db/

# 2. Start Socrates (should validate migrations)
python -m socratic_system.ui.main_app

# 3. Register new user (should create onboarding project)
/user create

# 4. Verify onboarding project was created
/project list

# 5. Verify database integrity
# (Should show: "All required tables and columns verified")
```

---

## Files to Modify

| File | Changes | Priority |
|------|---------|----------|
| `socratic_system/database/migration_runner.py` | Add migration validation | CRITICAL |
| `socratic_system/ui/main_app.py` | Add API key validation | CRITICAL |
| `socratic_system/services/project_service.py` | Add onboarding project creation | CRITICAL |
| `socratic_system/models/user.py` | Add project creation on user init | CRITICAL |
| `socratic_system/database/project_db.py` | Add database integrity checks | MEDIUM |
| `socrates-api/database.py` | Add thread-safe locking | MEDIUM |

