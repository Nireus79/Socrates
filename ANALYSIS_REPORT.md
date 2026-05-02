# Database Dependency Injection Analysis Report

## Summary

**Status**: ISSUES FOUND - 22 async functions across 12 files are using `db.` syntax without proper database dependency injection.

**Total Files with Issues**: 12  
**Total Functions with Issues**: 22

---

## Issues by File

### 1. **analysis.py**
- **Function**: `validate_code()`
  - **Definition Line**: 33
  - **Issue**: Uses `db.` at line [64] but parameter list missing `db` injection
  - **Current Parameters**: `code, language, project_id, current_user`

### 2. **auth.py**
- **Function**: `archive_account()`
  - **Definition Line**: 808
  - **Issue**: Uses `db.` at lines [829, 836]
  - **Current Parameters**: `current_user` (missing `db`)

- **Function**: `restore_account()`
  - **Definition Line**: 865
  - **Issue**: Uses `db.` at lines [885, 895]
  - **Current Parameters**: `current_user` (missing `db`)

### 3. **code_generation.py**
- **Function**: `generate_documentation()`
  - **Definition Line**: 868
  - **Issue**: Uses `db.` at lines [901, 939, 1027]
  - **Current Parameters**: `project_id, format, include_examples` (missing `db`)

### 4. **knowledge.py**
- **Function**: `debug_get_vector_db_chunks()`
  - **Definition Line**: 1510
  - **Issue**: Uses `db.` at line [1527]
  - **Current Parameters**: `orchestrator` (missing `db`)

### 5. **nlu.py**
- **Function**: `interpret_input()`
  - **Definition Line**: 214
  - **Issue**: Uses `db.` at lines [252, 261, 277]
  - **Current Parameters**: `request, current_user` (missing `db`)

### 6. **query.py**
- **Function**: `search_knowledge()`
  - **Definition Line**: 123
  - **Issue**: Uses `db.` at line [152]
  - **Current Parameters**: `query, project_id, limit, current_user` (missing `db`)

### 7. **sponsorships.py**
**NOTE**: These functions have `db=Depends(get_database)` parameter but missing type annotation
- **Function**: `github_sponsors_webhook()`
  - **Definition Line**: 25
  - **Issue**: Uses `db.` at lines [74, 85, 94, 106, 114, 134]
  - **Current Parameters**: `request, db=Depends(get_database)` (MISSING TYPE: `db: ProjectDatabase`)

- **Function**: `verify_sponsorship()`
  - **Definition Line**: 203
  - **Issue**: Uses `db.` at lines [221, 229, 245]
  - **Current Parameters**: `current_user, db=Depends(get_database)` (MISSING TYPE)

- **Function**: `get_sponsorship_history()`
  - **Definition Line**: 286
  - **Issue**: Uses `db.` at line [301]
  - **Current Parameters**: `current_user, db=Depends(get_database)` (MISSING TYPE)

- **Function**: `get_payment_history()`
  - **Definition Line**: 328
  - **Issue**: Uses `db.` at line [345]
  - **Current Parameters**: `current_user, db=Depends(get_database), limit` (MISSING TYPE)

- **Function**: `get_refund_history()`
  - **Definition Line**: 381
  - **Issue**: Uses `db.` at line [398]
  - **Current Parameters**: `current_user, db=Depends(get_database), limit` (MISSING TYPE)

- **Function**: `get_tier_change_history()`
  - **Definition Line**: 433
  - **Issue**: Uses `db.` at line [450]
  - **Current Parameters**: `current_user, db=Depends(get_database), limit` (MISSING TYPE)

- **Function**: `get_sponsorship_analytics()`
  - **Definition Line**: 483
  - **Issue**: Uses `db.` at line [500]
  - **Current Parameters**: `current_user, db=Depends(get_database)` (MISSING TYPE)

- **Function**: `get_payment_methods()`
  - **Definition Line**: 523
  - **Issue**: Uses `db.` at lines [538, 551]
  - **Current Parameters**: `current_user, db=Depends(get_database)` (MISSING TYPE)

- **Function**: `get_admin_dashboard()`
  - **Definition Line**: 707
  - **Issue**: Uses `db.` at lines [733, 787]
  - **Current Parameters**: `current_user, db=Depends(get_database)` (MISSING TYPE)

### 8. **subscription.py**
- **Function**: `get_subscription_status()`
  - **Definition Line**: 110
  - **Issue**: Uses `db.` at lines [129, 138]
  - **Current Parameters**: `current_user` (missing `db`)

### 9. **system.py**
- **Function**: `get_info()`
  - **Definition Line**: 192
  - **Issue**: Uses `db.` at lines [218, 226]
  - **Current Parameters**: `current_user` (missing `db`)

- **Function**: `get_context()`
  - **Definition Line**: 497
  - **Issue**: Uses `db.` at lines [520, 530]
  - **Current Parameters**: `current_user` (missing `db`)

### 10. **websocket.py**
- **Function**: `_handle_chat_message()`
  - **Definition Line**: 212
  - **Issue**: Uses `db.` at lines [249, 328]
  - **Current Parameters**: `message, user_id, project_id, connection_id` (missing `db`)
  - **Note**: Internal function, may need orchestrator instead

- **Function**: `_route_command()`
  - **Definition Line**: 406
  - **Issue**: Uses `db.` at lines [428, 469, 478, 493]
  - **Current Parameters**: `command, args, user_id, project_id` (missing `db`)
  - **Note**: Internal function, may need orchestrator instead

- **Function**: `websocket_collaboration_endpoint()`
  - **Definition Line**: 1190
  - **Issue**: Uses `db.` at line [1303]
  - **Current Parameters**: `websocket, project_id, token` (missing `db`)

---

## Issue Categories

### Category A: Missing db Parameter Entirely (11 functions)
These need to add: `db: ProjectDatabase = Depends(get_database)`
- analysis.py: `validate_code()`
- auth.py: `archive_account()`, `restore_account()`
- code_generation.py: `generate_documentation()`
- knowledge.py: `debug_get_vector_db_chunks()`
- nlu.py: `interpret_input()`
- query.py: `search_knowledge()`
- subscription.py: `get_subscription_status()`
- system.py: `get_info()`, `get_context()`

### Category B: Missing Type Annotation (9 functions in sponsorships.py)
These have `db=Depends(get_database)` but need type annotation:
Change from: `db=Depends(get_database)`
Change to: `db: ProjectDatabase = Depends(get_database)`

### Category C: WebSocket Internal Functions (3 functions in websocket.py)
These are internal helper functions that may need orchestrator access or dependency injection:
- `_handle_chat_message()`
- `_route_command()`
- `websocket_collaboration_endpoint()`

---

## Fix Strategy

### For Category A Functions (add parameter):
```python
async def example_func(
    existing_param: str = ...,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),  # ADD THIS
) -> APIResponse:
```

### For Category B Functions (add type annotation):
Change:
```python
async def example_func(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),  # MISSING TYPE
) -> APIResponse:
```

To:
```python
async def example_func(
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),  # ADDED TYPE
) -> APIResponse:
```

### For Category C Functions (WebSocket):
Review if these should use orchestrator.get_agent_bus() or require db injection. These may be design issues.

---

## Required Import

Ensure each file has:
```python
from socratic_system.database import ProjectDatabase
from socrates_api.database import get_database
```

---

## Impact Assessment

- **Critical**: Category A functions will fail at runtime if db methods are called
- **High**: Category B functions will have type checking issues
- **Medium**: Category C functions need architectural review

## Total Lines Affected

- Category A: 9 functions across 6 files
- Category B: 9 functions in 1 file (sponsorships.py)
- Category C: 3 functions in 1 file (websocket.py)

