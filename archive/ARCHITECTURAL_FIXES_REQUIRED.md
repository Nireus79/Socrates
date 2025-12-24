# Architectural Fixes Required: API vs CLI Pattern Reconciliation

## Executive Summary

The CLI commands work correctly because they use the orchestrator-agent pattern with proper validation. The API endpoints bypass this pattern and go directly to the database, causing:

1. **Different code paths** - CLI validates via agents, API doesn't
2. **Missing user context** - API has only username, CLI has full User object
3. **Database singleton issues** - Potential for accessing different databases
4. **Project ID format inconsistency** - UUID vs timestamp-based IDs
5. **Password hashing fallback** - CLI could use different hashing than API

---

## Fix #1: API Endpoints MUST Use Orchestrator Pattern (Like CLI)

### Current (Broken) API Pattern

```python
# socrates-api/src/socrates_api/routers/projects.py (lines 94-162)
@router.post("")
async def create_project(
    request: CreateProjectRequest = None,
    current_user: Optional[str] = Depends(get_current_user_optional),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    # WRONG: Direct database access, skips agent validation
    project = ProjectContext(...)
    db.save_project(project)
    return _project_to_response(project)
```

### Required (Fixed) API Pattern

```python
# Must match CLI pattern: use orchestrator
@router.post("")
async def create_project(
    request: CreateProjectRequest,
    current_user: Optional[str] = Depends(get_current_user),
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """Create project using orchestrator (same as CLI)"""
    try:
        # Use orchestrator pattern like CLI does
        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "create_project",
                "project_name": request.name,
                "owner": current_user,
                "project_type": request.knowledge_base_content or "general",
            },
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Failed to create project")
            )

        return _project_to_response(result["project"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating project")
```

**Why This Matters:**
- CLI and API MUST use the same code path (orchestrator agent)
- Agent includes subscription checking, business logic validation
- Prevents code divergence and bugs

---

## Fix #2: API Must Use Full User Object (Not Just Username)

### Current (Broken) API Pattern

```python
# socrates-api/src/socrates_api/dependencies.py (lines 19-64)
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    # WRONG: Returns only username string
    user_id: Optional[str] = payload.get("sub")
    return user_id  # Just a string!
```

### Required (Fixed) API Pattern

```python
async def get_current_user_object(
    token: str = Depends(get_token),
    db: ProjectDatabaseV2 = Depends(get_database)
) -> User:
    """Get full User object from database (like CLI does)"""
    try:
        payload = verify_access_token(token)
        if payload is None:
            raise HTTPException(401, "Invalid token")

        username = payload.get("sub")
        user = db.load_user(username)  # Fetch full User object

        if user is None:
            raise HTTPException(401, "User not found")

        return user  # Return full User object

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, "Authentication failed")
```

### Updated Endpoints

```python
# Use the new dependency that returns User object
@router.post("/projects")
async def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_user_object),  # Full User object
    db: ProjectDatabaseV2 = Depends(get_database),
):
    # Now you can access all user properties
    can_create, message = SubscriptionChecker.check_project_limit(
        current_user,  # Full User object
        len(db.get_user_projects(current_user.username))
    )

    if not can_create:
        raise HTTPException(status_code=403, detail=message)

    # ... create project ...
```

**Why This Matters:**
- CLI has full User object with `subscription_tier`, `email`, status fields
- API needs same context to make proper authorization decisions
- Prevents incomplete permission checks

---

## Fix #3: Consolidate Database Singleton (API + CLI Must Share)

### Current (Broken) Pattern

```python
# CLI: Creates its own database instance per orchestrator
# socratic_system/orchestration/orchestrator.py (lines 76-81)
self.database = ProjectDatabaseV2(str(self.config.projects_db_path))

# API: Has global singleton
# socrates-api/src/socrates_api/database.py (lines 20-53)
_database = ProjectDatabaseV2(db_path)
```

**Problem:** If `db_path` differs between CLI and API configs, they access **different databases!**

### Required (Fixed) Pattern

```python
# socrates-api/src/socrates_api/database.py
# UNIFIED singleton database that both CLI and API use

import os
from pathlib import Path

class DatabaseSingleton:
    """Unified database singleton for both CLI and API"""
    _instance = None
    _db_path = None

    @classmethod
    def initialize(cls, db_path: str):
        """Initialize with specific path (call at startup)"""
        cls._db_path = db_path

    @classmethod
    def get_instance(cls) -> ProjectDatabaseV2:
        """Get or create singleton instance"""
        if cls._instance is None:
            db_path = cls._db_path or os.getenv(
                "SOCRATES_DB_PATH",
                str(Path.home() / ".socrates" / "projects.db")
            )
            cls._instance = ProjectDatabaseV2(db_path)
        return cls._instance

# API and CLI startup
def startup_both_systems():
    # Initialize database singleton FIRST
    db_path = os.getenv("SOCRATES_DB_PATH", default_path)
    DatabaseSingleton.initialize(db_path)

    # Now both CLI and API use the same instance
    api_db = DatabaseSingleton.get_instance()
    orchestrator_db = DatabaseSingleton.get_instance()

    assert api_db is orchestrator_db  # MUST be same instance!
```

**Why This Matters:**
- Prevents data access corruption from dual databases
- Ensures CLI and API see same data
- Single source of truth

---

## Fix #4: Standardize Project ID Generation

### Current (Broken) Inconsistency

```python
# CLI Agent (project_manager.py line 109)
project_id = str(uuid.uuid4())  # Pure UUID: "a1b2c3d4-e5f6-..."

# API Endpoint (projects.py line 139)
project_id = f"proj_{owner}_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
# Result: "proj_alice_1702123456000"
```

**Problem:** Projects created via API have different IDs than CLI-created ones!

### Required (Fixed) Pattern

```python
# Create a unified ProjectIDGenerator in both CLI and API
# socratic_system/utils/id_generator.py

import uuid
from datetime import datetime
from typing import Optional

class ProjectIDGenerator:
    """Unified project ID generation for CLI + API"""

    # Decide on ONE format (recommend: UUID for simplicity)
    # or use consistent timestamp format with owner prefix

    @staticmethod
    def generate(owner: str = None) -> str:
        """Generate project ID consistently"""
        # OPTION A: Pure UUID (recommended)
        return f"proj_{str(uuid.uuid4())}"

        # OPTION B: Timestamp-based (if you want sortability)
        # timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        # if owner:
        #     return f"proj_{owner}_{timestamp}"
        # return f"proj_{timestamp}"

# Use in BOTH CLI and API
from socratic_system.utils.id_generator import ProjectIDGenerator

# In CLI Agent (project_manager.py)
project_id = ProjectIDGenerator.generate(owner)

# In API Endpoint (projects.py)
project_id = ProjectIDGenerator.generate(current_user.username)
```

**Why This Matters:**
- API and CLI created projects are indistinguishable
- Consistent sorting/searching across both systems
- No data integrity issues

---

## Fix #5: Ensure Consistent Password Hashing

### Current (Broken) Pattern

```python
# socratic_system/ui/commands/user_commands.py (lines 11-23)
try:
    from socrates_api.auth.password import hash_password, verify_password
except ImportError:
    # FALLBACK: Uses argon2 instead of bcrypt!
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    hash_password = pwd_context.hash
    verify_password = pwd_context.verify
```

**Problem:** If import fails, CLI uses `argon2` but API uses `bcrypt` → password verification fails!

### Required (Fixed) Pattern

```python
# socrates-api/src/socrates_api/auth/password.py
# Make this importable and ensure it's the ONLY password hashing source

from passlib.context import CryptContext

# Use bcrypt exclusively (no fallback)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:
        return False

# In socratic_system/ui/commands/user_commands.py
# REMOVE the fallback, just import from API
from socrates_api.auth.password import hash_password, verify_password
# No try/except, let it fail if import doesn't work
```

**Why This Matters:**
- Single password hashing algorithm across entire system
- No "accidental" algorithm switching
- Password verification works consistently

---

## Fix #6: API Authentication Decorator Must Check Subscription

### Current (Broken) Pattern

```python
# socrates-api/src/socrates_api/routers/projects.py (line 105)
@router.post("")
@require_subscription_feature("project_creation")  # Decorator
async def create_project(...):
    # Project creation code
```

### Issue

The decorator checks subscription, but if the endpoint calls orchestrator (as per Fix #1), the agent ALSO checks subscription. This creates duplicate checks but actually works OK... except:

**The decorator doesn't have access to the full User object** so it might not work correctly.

### Required (Fixed) Pattern

```python
# Option A: Let orchestrator handle subscription (preferred)
@router.post("")
async def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_user_object),  # Full User object
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """Create project - subscription check done by orchestrator agent"""
    result = orchestrator.process_request(
        "project_manager",
        {
            "action": "create_project",
            "project_name": request.name,
            "owner": current_user.username,
            "project_type": request.knowledge_base_content or "general",
        },
    )

    if result["status"] != "success":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return _project_to_response(result["project"])

# Option B: Check subscription manually in endpoint
@router.post("")
async def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_user_object),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """Create project - manual subscription check"""
    from socratic_system.subscription.checker import SubscriptionChecker

    # Check subscription using full User object
    can_create, message = SubscriptionChecker.check_project_limit(
        current_user,
        len(db.get_user_projects(current_user.username))
    )

    if not can_create:
        raise HTTPException(status_code=403, detail=message)

    # ... create project ...
```

**Preferred:** Option A (use orchestrator) - keeps CLI and API synchronized.

---

## Fix #7: CreateProjectRequest Model - Remove Optional Owner

### Current (Broken) Status

```python
# socrates-api/src/socrates_api/models.py (line 14)
owner: Optional[str] = Field(None, min_length=1, max_length=100, ...)
```

Model is optional, but the problem is FastAPI/Pydantic validation.

### Root Cause

When you have:
```python
owner: Optional[str] = Field(None, min_length=1, ...)
```

The `min_length=1` on an Optional field can cause validation issues. Pydantic might still treat it as required.

### Required (Fixed) Pattern

```python
# socrates-api/src/socrates_api/models.py

class CreateProjectRequest(BaseModel):
    """Request body for creating a new project"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Project name"
    )
    # REMOVE owner field entirely - always uses authenticated user
    # owner: Optional[str] = Field(...)  # DELETE THIS LINE

    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Project description"
    )
    knowledge_base_content: Optional[str] = Field(
        None,
        description="Initial knowledge base content"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python API Development",
                "description": "Building a REST API with FastAPI",
                "knowledge_base_content": "FastAPI is a modern web framework...",
            }
        }
```

**Why This Matters:**
- Removes ambiguity about optional fields
- Owner is ALWAYS the authenticated user (security principle)
- No Pydantic validation confusion

---

## Implementation Checklist

### Phase 1: Foundation (Required)
- [ ] Fix #3: Implement unified DatabaseSingleton
- [ ] Fix #5: Ensure consistent password hashing
- [ ] Fix #4: Create ProjectIDGenerator for consistency
- [ ] Fix #7: Remove owner field from CreateProjectRequest

### Phase 2: API Updates (Required)
- [ ] Fix #2: Create `get_current_user_object` dependency returning User
- [ ] Update all API endpoints to use orchestrator pattern
- [ ] Update all API endpoints to use new User dependency

### Phase 3: CLI Updates (Optional but Recommended)
- [ ] Update CLI password hashing to import directly from API (no fallback)
- [ ] Update CLI project creation to use ProjectIDGenerator

### Phase 4: Testing
- [ ] Create comprehensive test suite comparing CLI vs API
- [ ] Verify both CLI and API use same database
- [ ] Verify password hashing works identically
- [ ] Verify project IDs are generated consistently

---

## Testing the Fixes

### Before Fixes (Current Broken State)
```bash
# This should fail or produce inconsistent behavior
pytest test_all_workflows.py -v

# Expected failures:
# - Create Project API: 422 validation error (owner field)
# - Project list: Empty (creation failed)
# - CLI and API project IDs: Different formats
```

### After Fixes (Expected Behavior)
```bash
# This should pass
pytest test_all_workflows.py -v

# Expected results:
# - Create Project API: 200 success
# - Project list: Shows created project
# - CLI and API project IDs: Same format
# - Password verify: Works for both CLI and API users
# - Database: Single shared instance
```

---

## Summary of Changes

| Issue | CLI Behavior | Current API | Required Fix |
|-------|-------------|------------|--------------|
| Code Path | Uses orchestrator agents | Direct DB | Use orchestrator ✓ |
| User Context | Full User object | Username only | Return User object ✓ |
| Database | Per orchestrator instance | Global singleton | Unified singleton ✓ |
| Project IDs | UUID | Timestamp-owner | Unified generator ✓ |
| Password Hashing | Imports from API | bcrypt | Remove fallback ✓ |
| Model Validation | N/A | Optional owner issue | Remove field ✓ |
| Subscription Check | In agent | In decorator | Harmonize via agent ✓ |

All fixes maintain backward compatibility while harmonizing API and CLI behavior.
