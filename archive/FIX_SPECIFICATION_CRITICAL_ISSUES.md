# FIX SPECIFICATION: Critical Issues
## Detailed Implementation Guide for Authorization & Knowledge Analysis Fixes

**Date**: 2025-12-27
**Scope**: 2 critical issues requiring fixes
**Effort**: ~1.5 weeks total
**Priority**: HIGH - Security and feature parity

---

## ISSUE #1: AUTHORIZATION SECURITY VULNERABILITY

### Summary
Free-tier users can access Pro-tier features via API endpoints while CLI correctly restricts them.

### Root Cause Analysis

**CLI (Correctly Gated)**:
- Commands check subscription tier before execution
- Example: `/analytics` command requires Pro tier
- Enforcement: `command_handler.py:152` via `SubscriptionChecker.check_command_access()`

**API (Incorrectly Gated)**:
- `@require_subscription_feature` decorator imported but never used
- No subscription checks on endpoints
- Project creation has fallback path with NO checks
- Result: Free users bypass tier restrictions

### Affected Endpoints

#### HIGH PRIORITY (Tier Bypass Possible)

| Endpoint | Issue | Fix |
|----------|-------|-----|
| `POST /projects` | Fallback path skips subscription check | Add explicit check to lines 208-230 |
| `POST /collaboration/add` | No team member limit check | Add subscription + limit validation |
| `GET /analytics/*` | 4 analytics endpoints unprotected | Add `@require_subscription_feature("professional")` |
| `POST /code-generation/*` | Code generation unprotected | Add `@require_subscription_feature("professional")` |

#### MEDIUM PRIORITY (Features Unprotected)

| Endpoint | Issue | Fix |
|----------|-------|-----|
| `POST /skills/set` | Skills tier not enforced | Add decorator |
| `POST /llm/*` | Multi-LLM features unprotected | Add decorator |
| `POST /maturity/*` | Maturity tracking unprotected | Add decorator |

### Implementation Specification

#### Fix #1.1: Project Creation Fallback Path (HIGH PRIORITY)

**File**: `socrates-api/src/socrates_api/routers/projects.py`

**Problem**: Lines 208-230 create project without subscription validation

**Current Code** (lines 207-230):
```python
# Fallback: Create project directly without orchestrator
logger.warning("Creating project without orchestrator validation")
project = Project(
    project_id=project_id,
    owner=current_user,
    name=request.name,
    knowledge_base_content=request.knowledge_base_content or "general",
    project_type=request.knowledge_base_content or "software",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    team_members=[],
)
db.save_project(project)
```

**Required Fix**:
```python
# Before creating project, validate subscription
user_object = get_current_user_object(current_user)
if not user_object.subscription.is_active:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Active subscription required to create projects"
    )

# Check project limit for subscription tier
from socratic_system.subscription import SubscriptionChecker
active_projects = db.get_user_projects(current_user)
can_create, error_msg = SubscriptionChecker.check_project_limit(
    user_object,
    len(active_projects)
)
if not can_create:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=error_msg
    )

# NOW create project
logger.warning("Creating project without orchestrator validation")
project = Project(...)
db.save_project(project)
```

**Testing**:
```python
def test_free_tier_cannot_create_project_fallback():
    """Verify free tier blocked even in fallback path"""
    free_user = create_free_tier_user()
    response = create_project(user=free_user)
    assert response.status_code == 403
    assert "subscription" in response.detail.lower()

def test_project_limit_enforced():
    """Verify tier limits enforced"""
    pro_user = create_pro_tier_user()
    # Create max projects for tier
    for i in range(5):  # Assume pro tier limit is 5
        create_project(user=pro_user)

    # Next should fail
    response = create_project(user=pro_user)
    assert response.status_code == 403
    assert "limit" in response.detail.lower()
```

---

#### Fix #1.2: Collaboration Endpoints (HIGH PRIORITY)

**File**: `socrates-api/src/socrates_api/routers/collaboration.py`

**Problem**: `/collaboration/add` has no subscription check for team limits

**Affected Endpoint** (lines 64-131):
```python
@router.post("/{project_id}/add", ...)
async def add_team_member(...):
    # Current: No subscription check
    # Just validates project exists and user not already added
```

**Required Fix**:
```python
@router.post("/{project_id}/add", ...)
async def add_team_member(
    project_id: str,
    request: AddTeamMemberRequest,
    current_user: str = Depends(get_current_user),
):
    # 1. Check subscription tier
    user_object = get_current_user_object(current_user)
    from socratic_system.subscription.tiers import SUBSCRIPTION_TIERS

    if user_object.subscription.tier != "professional":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team collaboration requires Professional subscription"
        )

    # 2. Check team member limit for tier
    project = db.load_project(project_id)
    if not project or project.owner != current_user:
        raise HTTPException(status_code=404, detail="Project not found")

    max_team_members = SUBSCRIPTION_TIERS[user_object.subscription.tier]["max_team_members"]
    if len(project.team_members) >= max_team_members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Team member limit ({max_team_members}) reached for {user_object.subscription.tier} tier"
        )

    # 3. NOW add team member
    # ... existing code ...
```

**Testing**:
```python
def test_free_tier_cannot_add_team_members():
    """Verify free tier cannot use collaboration"""
    free_user = create_free_tier_user()
    response = add_team_member(user=free_user, ...)
    assert response.status_code == 403
    assert "professional" in response.detail.lower()

def test_team_member_limit_enforced():
    """Verify team size limited by tier"""
    pro_user = create_pro_tier_user()
    # Pro tier: assume 5 member limit
    for i in range(4):
        add_team_member(user=pro_user, ...)

    # 5th should succeed
    response = add_team_member(user=pro_user, ...)
    assert response.status_code == 200

    # 6th should fail
    response = add_team_member(user=pro_user, ...)
    assert response.status_code == 403
    assert "limit" in response.detail.lower()
```

---

#### Fix #1.3: Analytics Endpoints (MEDIUM PRIORITY)

**File**: `socrates-api/src/socrates_api/routers/analytics.py`

**Problem**: All analytics endpoints missing subscription checks

**Affected Endpoints**:
- `GET /analytics/analyze` (line ~78)
- `GET /analytics/recommend` (line ~150)
- `GET /analytics/trends` (line ~220)
- `GET /analytics/summary` (line ~290)

**Required Fix** (Apply to all 4 endpoints):
```python
from socrates_api.auth import require_subscription_feature

@router.get("/analyze", ...)
@require_subscription_feature("professional")  # ADD THIS DECORATOR
async def analyze_project(project_id: str, current_user: str = Depends(get_current_user)):
    # ... existing code ...
```

**Testing**:
```python
def test_free_tier_cannot_access_analytics():
    """Verify all analytics endpoints restricted"""
    free_user = create_free_tier_user()

    endpoints = [
        "/analytics/analyze",
        "/analytics/recommend",
        "/analytics/trends",
        "/analytics/summary"
    ]

    for endpoint in endpoints:
        response = get(f"/projects/123{endpoint}", user=free_user)
        assert response.status_code == 403, f"Failed for {endpoint}"
        assert "professional" in response.detail.lower()
```

---

#### Fix #1.4: Code Generation Endpoints (MEDIUM PRIORITY)

**File**: `socrates-api/src/socrates_api/routers/code_generation.py`

**Problem**: Code generation endpoints missing subscription checks

**Affected Endpoints**:
- `POST /code-generation/generate` (line ~78)
- `POST /code-generation/docs` (line ~150)

**Required Fix**:
```python
@router.post("/generate", ...)
@require_subscription_feature("professional")  # ADD DECORATOR
async def generate_code(...):
    # ... existing code ...

@router.post("/docs", ...)
@require_subscription_feature("professional")  # ADD DECORATOR
async def generate_code_docs(...):
    # ... existing code ...
```

---

#### Fix #1.5: Other Tier-Gated Features (MEDIUM PRIORITY)

**Affected Features** (reference from CLI tier definitions):
- Skills: `socratic_system/subscription/tiers.py` - requires "professional"
- Multi-LLM: requires "professional"
- Maturity tracking: requires "professional"

**Files to Update**:
- `socrates-api/src/socrates_api/routers/skills.py` - Add `@require_subscription_feature("professional")`
- `socrates-api/src/socrates_api/routers/llm.py` - Add decorator (if exists)
- `socrates-api/src/socrates_api/routers/maturity.py` - Add decorator (if exists)

---

### Authorization Fix Testing Checklist

- [ ] Free tier cannot create projects (main path)
- [ ] Free tier cannot create projects (fallback path)
- [ ] Free tier cannot exceed project limit
- [ ] Free tier cannot add team members
- [ ] Free tier cannot access analytics endpoints
- [ ] Free tier cannot access code generation
- [ ] Free tier cannot access skills features
- [ ] Pro tier can do all above
- [ ] Enterprise tier can do all above
- [ ] Project limit enforced by tier
- [ ] Team member limit enforced by tier
- [ ] Error messages are clear

---

## ISSUE #2: KNOWLEDGE ANALYSIS PIPELINE BROKEN FOR CLI

### Summary
CLI import commands don't emit `DOCUMENT_IMPORTED` events, breaking the knowledge analysis pipeline that depends on these events.

### Root Cause Analysis

**Pipeline Overview**:
```
Document Imported → DOCUMENT_IMPORTED Event → KnowledgeAnalysisAgent Triggered
                                              → Analyzes knowledge
                                              → Regenerates questions
                                              → Emits QUESTIONS_REGENERATED
```

**Current Status**:
- API: Event emitted ✓ → Pipeline works ✓
- CLI: Event NOT emitted ✗ → Pipeline broken ✗

**Why Broken**:
- `KnowledgeAnalysisAgent` registered listener: `orchestrator.event_emitter.on(EventType.DOCUMENT_IMPORTED, ...)`
- CLI imports call `orchestrator.process_request("document_agent", {...})`
- Agent processes and stores documents in vector DB
- But CLI command never emits the event
- So listener never triggered
- So analysis never happens

### Implementation Specification

#### Fix #2.1: DocImportCommand

**File**: `socratic_system/ui/commands/doc_commands.py`

**Location**: Lines 110-130 (after import succeeds)

**Current Code**:
```python
result = orchestrator.process_request(
    "document_agent",
    {"action": "import_file", "file_path": file_path, "project_id": project_id},
)

if result["status"] == "success":
    self.print_success(f"Document imported: {file_path}")
    return self.success(data={"file_path": file_path})
else:
    self.print_error(result.get("message", "Import failed"))
    return self.error(result.get("message", "Import failed"))
```

**Required Fix**:
```python
result = orchestrator.process_request(
    "document_agent",
    {"action": "import_file", "file_path": file_path, "project_id": project_id},
)

if result["status"] == "success":
    # Emit DOCUMENT_IMPORTED event to trigger knowledge analysis
    try:
        from socratic_system.events import EventType
        orchestrator.event_emitter.emit(
            EventType.DOCUMENT_IMPORTED,
            {
                "project_id": project_id,
                "file_name": os.path.basename(file_path),
                "source_type": "file",
                "words_extracted": result.get("words_extracted", 0),
                "chunks_created": result.get("chunks_added", 0),
                "user_id": context.get("user").username if context.get("user") else "unknown",
            }
        )
        logger.debug(f"Emitted DOCUMENT_IMPORTED event for {file_path}")
    except Exception as e:
        logger.warning(f"Failed to emit DOCUMENT_IMPORTED event: {e}")

    self.print_success(f"Document imported: {file_path}")
    return self.success(data={"file_path": file_path})
else:
    self.print_error(result.get("message", "Import failed"))
    return self.error(result.get("message", "Import failed"))
```

**Code Location to Insert**: After successful import, before `self.print_success()`

---

#### Fix #2.2: DocImportDirCommand

**File**: `socratic_system/ui/commands/doc_commands.py`

**Location**: After directory import succeeds (around line 220)

**Required Fix** (apply same pattern for each file in directory):
```python
# After successfully processing each file in directory
try:
    from socratic_system.events import EventType
    orchestrator.event_emitter.emit(
        EventType.DOCUMENT_IMPORTED,
        {
            "project_id": project_id,
            "file_name": filename,
            "source_type": "file",
            "words_extracted": result.get("words_extracted", 0),
            "chunks_created": result.get("chunks_added", 0),
            "user_id": context.get("user").username if context.get("user") else "unknown",
        }
    )
except Exception as e:
    logger.warning(f"Failed to emit DOCUMENT_IMPORTED event for {filename}: {e}")
```

---

#### Fix #2.3: DocPasteCommand

**File**: `socratic_system/ui/commands/doc_commands.py`

**Location**: After paste import succeeds (around line 309)

**Required Fix**:
```python
result = orchestrator.process_request(
    "document_agent",
    {"action": "import_text", "content": content, "project_id": project_id, "title": title},
)

if result["status"] == "success":
    # Emit event
    try:
        from socratic_system.events import EventType
        orchestrator.event_emitter.emit(
            EventType.DOCUMENT_IMPORTED,
            {
                "project_id": project_id,
                "file_name": title or "Pasted Content",
                "source_type": "text",
                "words_extracted": result.get("words_extracted", 0),
                "chunks_created": result.get("chunks_added", 0),
                "user_id": context.get("user").username if context.get("user") else "unknown",
            }
        )
    except Exception as e:
        logger.warning(f"Failed to emit DOCUMENT_IMPORTED event: {e}")

    self.print_success(f"Content imported: {title}")
    # ...
```

---

#### Fix #2.4: DocImportUrlCommand

**File**: `socratic_system/ui/commands/doc_commands.py`

**Location**: After URL import succeeds (around line 383)

**Required Fix**:
```python
result = orchestrator.process_request(
    "document_agent",
    {"action": "import_url", "url": url, "project_id": project_id},
)

if result["status"] == "success":
    # Emit event
    try:
        from socratic_system.events import EventType
        orchestrator.event_emitter.emit(
            EventType.DOCUMENT_IMPORTED,
            {
                "project_id": project_id,
                "file_name": url,
                "source_type": "url",
                "words_extracted": result.get("words_extracted", 0),
                "chunks_created": result.get("chunks_added", 0),
                "user_id": context.get("user").username if context.get("user") else "unknown",
            }
        )
    except Exception as e:
        logger.warning(f"Failed to emit DOCUMENT_IMPORTED event: {e}")

    self.print_success(f"Content imported from: {url}")
    # ...
```

---

### Knowledge Analysis Pipeline Testing Checklist

- [ ] CLI import file → Event emitted
- [ ] CLI import directory → Events emitted for each file
- [ ] CLI paste content → Event emitted
- [ ] CLI import URL → Event emitted
- [ ] KnowledgeAnalysisAgent receives event
- [ ] Knowledge analysis triggered
- [ ] Questions regenerated after import
- [ ] QUESTIONS_REGENERATED event emitted
- [ ] API import still works (test backward compatibility)
- [ ] API events still emitted (no duplication issues)
- [ ] Event data consistent (same fields, same format)

---

### Integration Testing

**Test Scenario: End-to-end knowledge analysis pipeline in CLI**

```python
def test_knowledge_analysis_pipeline_cli():
    """Test complete flow: import → analyze → regenerate questions"""

    # Setup
    cli = start_cli_session()
    user = login(cli, "testuser")
    project = create_project(cli, "TestProject")

    # Get initial questions (baseline)
    questions_before = get_project_questions(project)

    # Import knowledge document
    result = run_command(cli, "/docs import test_document.pdf")
    assert result["status"] == "success"

    # Wait for knowledge analysis to complete
    # (It's event-driven, so should be nearly instant)
    time.sleep(2)

    # Verify knowledge analysis happened
    # (Check that new questions were generated)
    questions_after = get_project_questions(project)

    # Questions should be different (regenerated based on new knowledge)
    assert len(questions_after) > 0
    assert questions_after != questions_before  # Changed based on knowledge

    # Verify event was emitted
    events = get_emitted_events(project, EventType.DOCUMENT_IMPORTED)
    assert len(events) == 1
    assert events[0]["file_name"] == "test_document.pdf"

def test_knowledge_analysis_consistency_cli_vs_api():
    """Test that CLI and API emit same events and trigger same analysis"""

    # Setup
    project_cli = create_project_cli("TestCLI")
    project_api = create_project_api("TestAPI")

    # Import same document via CLI
    run_command(cli, f"/docs import test_doc.pdf --project {project_cli.id}")
    time.sleep(2)

    # Import same document via API
    response = api_import_file(project_api.id, "test_doc.pdf")
    time.sleep(2)

    # Verify events emitted from both paths
    cli_events = get_events(project_cli, EventType.DOCUMENT_IMPORTED)
    api_events = get_events(project_api, EventType.DOCUMENT_IMPORTED)

    assert len(cli_events) == 1
    assert len(api_events) == 1

    # Verify event data format matches
    assert cli_events[0]["source_type"] == api_events[0]["source_type"]
    assert cli_events[0]["words_extracted"] == api_events[0]["words_extracted"]
```

---

## IMPLEMENTATION PRIORITY

### Week 1: Authorization Fix
**Days 1-2**: Implement fixes 1.1-1.5
**Days 3-4**: Write comprehensive tests
**Days 4-5**: Security review and validation
**End Result**: Authorization gaps closed ✓

### Week 1.5: Knowledge Analysis Fix
**Days 1-2**: Implement fixes 2.1-2.4
**Days 2-3**: Write integration tests
**Days 3-4**: Verify end-to-end pipeline
**End Result**: CLI knowledge analysis works ✓

---

## ROLLBACK PLAN

If issues arise during implementation:

**Authorization Fixes**:
- Each endpoint change is independent
- Rollback: Remove decorator or subscription check
- Impact: Returns to current (vulnerable) state
- Recovery: Reapply fix with corrections

**Knowledge Analysis Fixes**:
- Event emissions are additive (don't break anything)
- If event causes issues: Wrap in try/except (already done)
- Impact: Minimal - worst case events silently fail and logged
- Recovery: Fix event payload or handler logic

---

## VALIDATION CHECKLIST

Before deploying fixes:

- [ ] All authorization tests pass
- [ ] All knowledge analysis tests pass
- [ ] No regressions in existing functionality
- [ ] Security audit performed
- [ ] Team review completed
- [ ] Event logging verified
- [ ] Backward compatibility confirmed
- [ ] Documentation updated

