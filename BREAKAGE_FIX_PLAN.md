# System Breakage Fix Plan

**Date:** 2026-04-01
**Status:** Planning Phase
**Scope:** Fix 6 critical + 8 moderate issues

---

## Priority 1: CRITICAL FIXES (Must Complete Before Deployment)

### FIX 1: WebSocket Authentication - CRITICAL SECURITY

**Current Broken Code (WebSocket connection handler):**
```python
# Current: token NOT validated
user_id = None  # Default - SECURITY ISSUE!
token = query_params.get("token")  # Extracted but never checked
```

**Issue:**
- Any client can connect claiming any user_id
- No actual authentication verification
- Unauthorized access possible

**Fix Required:**
```python
# Add after line where token extracted:
try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user_id = payload.get("user_id")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token")
        return
except jwt.InvalidTokenError:
    await websocket.close(code=1008, reason="Invalid token")
    return
```

**Files to Modify:**
- `backend/src/socrates_api/websocket/handlers.py` (or similar)
- `backend/src/socrates_api/websocket/connection_manager.py`

**Test Cases:**
- [ ] Invalid token → connection closes
- [ ] Valid token → connection opens
- [ ] No token → connection closes
- [ ] Expired token → connection closes

**Estimated Time:** 15 minutes

---

### FIX 2: Cache Invalidation - CRITICAL DATA FRESHNESS

**Current Broken Code:**
```python
# Line 842-851 in projects_chat.py
project.conversation_history.append({"role": "user", ...})
project.conversation_history.append({"role": "assistant", ...})
db.save_project(project)
# *** MISSING: No cache invalidation! ***
```

**Issue:**
- Metrics cache remains stale for up to 5 minutes
- User sees outdated progress
- Analytics lag by up to 5 minutes

**Fix Required:**
```python
# After db.save_project(project), add:
from socrates_api.services.query_cache import get_query_cache

project.conversation_history.append({"role": "user", ...})
project.conversation_history.append({"role": "assistant", ...})
db.save_project(project)

# CRITICAL: Invalidate affected caches
cache = get_query_cache()
cache.invalidate(f"metrics:{project_id}")
cache.invalidate(f"readiness:{project_id}")
cache.invalidate(f"conversation_history:{project_id}")
```

**Files to Modify:**
- `backend/src/socrates_api/routers/projects_chat.py` (lines 842-851)
- `backend/src/socrates_api/routers/projects.py` (after all saves)
- `backend/src/socrates_api/routers/code_generation.py` (after all saves)

**Additional Invalidation Points:**
```python
# After ANY conversation_history modification:
project.conversation_history.append(msg) → invalidate metrics
project.conversation_history.clear() → invalidate metrics
project.chat_sessions[sid]['messages'].append(msg) → invalidate conversation

# After ANY project field modification:
project.goals = ... → invalidate project_detail
project.requirements = ... → invalidate project_detail
project.tech_stack = ... → invalidate project_detail
```

**Test Cases:**
- [ ] Add message → metrics cache invalid
- [ ] Get metrics after message → fresh data
- [ ] No 5-minute delay in updates
- [ ] Cache miss triggers recalculation

**Estimated Time:** 20 minutes

---

### FIX 3: Consolidate Conversation Storage - CRITICAL DATA CONSISTENCY

**Current Broken Code:**
Two parallel systems:
```python
# System 1: conversation_history (list)
project.conversation_history.append({"role": "user", "content": "..."})

# System 2: chat_sessions (nested dict)
project.chat_sessions[session_id]["messages"].append({"id": "msg_123", ...})

# They diverge!
```

**Issue:**
- Data could exist in one system but not the other
- Different endpoints read different sources
- Analytics uses only conversation_history (ignoring chat_sessions)
- No sync mechanism

**Fix Required:**

**Step 1: Audit Current Usage**
```
conversation_history used by:
- GET /chat/history/{project_id}
- analytics/metrics calculation
- _get_conversation_summary() in orchestrator
- conflict detection
- spec extraction

chat_sessions used by:
- GET /chat/sessions/{session_id}/messages
- session_manager.py operations
- WebSocket handlers
```

**Step 2: Choose Single Source**
- **Recommendation**: Use conversation_history (simpler, used more widely)
- Deprecate chat_sessions

**Step 3: Data Migration**
```python
# Migration script for existing projects:
def migrate_chat_sessions_to_conversation_history(project):
    """Migrate messages from chat_sessions to conversation_history"""
    for session_id, session_data in project.chat_sessions.items():
        for message in session_data.get("messages", []):
            # Convert format from chat_sessions to conversation_history
            history_entry = {
                "role": message.get("role", "user"),
                "content": message.get("message", message.get("content", "")),
                "timestamp": message.get("timestamp", datetime.now().isoformat()),
                "message_id": message.get("id")  # Preserve ID for reference
            }
            project.conversation_history.append(history_entry)

    # Clear old sessions
    project.chat_sessions = {}
    return project
```

**Step 4: Update All Endpoints**
```
PUT /chat/sessions/{session_id}/messages/{message_id}
→ Update conversation_history entry
  (search by message_id or timestamp)

DELETE /chat/sessions/{session_id}/messages/{message_id}
→ Delete from conversation_history
  (search by message_id or timestamp)

POST /chat/sessions/{session_id}/end
→ Mark conversation_history as ended
```

**Step 5: Remove Double-Storage**
- Delete all code that updates chat_sessions
- Keep conversation_history as single source of truth

**Files to Modify:**
- `backend/src/socrates_api/routers/projects_chat.py` (multiple places)
- `backend/src/socrates_api/routers/chat_sessions.py` (redirect to conversation_history)
- `backend/src/socrates_api/models_local.py` (ProjectContext - deprecate chat_sessions)
- Migration script

**Test Cases:**
- [ ] Migrate existing projects without data loss
- [ ] All conversation history present after migration
- [ ] All endpoints use conversation_history only
- [ ] No divergence between systems
- [ ] Analytics reads all messages

**Estimated Time:** 45 minutes (complex, requires data migration)

---

### FIX 4: Event Persistence - CRITICAL AUDIT TRAIL

**Current Broken Code:**
```python
# Current: Events only in-memory queue
events_queue = []  # Lost on server restart!

def record_event(event_type, data, user_id):
    events_queue.append({...})  # Just adds to list
    # No database persistence!
```

**Issue:**
- All events lost on server restart
- Cannot audit user actions
- Analytics incomplete
- No event history

**Fix Required:**

**Step 1: Create Events Table**
```python
# In database.py, add to _initialize():
self.conn.execute("""
    CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        user_id TEXT NOT NULL,
        project_id TEXT,
        data TEXT,  -- JSON
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )
""")
self.conn.execute(
    "CREATE INDEX IF NOT EXISTS idx_events_user_time ON events(user_id, created_at)"
)
self.conn.execute(
    "CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)"
)
```

**Step 2: Update record_event() Function**
```python
def record_event(event_type: str, data: dict, user_id: str = None, project_id: str = None):
    """Record an event to database instead of in-memory queue"""
    try:
        from socrates_api.database import get_database
        from datetime import datetime, timezone

        db = get_database()
        event_id = f"evt_{uuid.uuid4().hex[:12]}"

        db.conn.execute(
            """INSERT INTO events (event_id, event_type, user_id, project_id, data, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                event_id,
                event_type,
                user_id,
                project_id,
                json.dumps(data),
                datetime.now(timezone.utc).isoformat()
            )
        )
        db.conn.commit()
        logger.info(f"Event recorded: {event_type}")

    except Exception as e:
        logger.error(f"Failed to record event: {e}")
        # Don't raise - event failure shouldn't crash request
```

**Step 3: Add Query Methods**
```python
# In database.py:
def get_events_for_user(self, user_id: str, limit: int = 100) -> List[Dict]:
    """Get events for a user"""
    cursor = self.conn.execute(
        "SELECT * FROM events WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    return [dict(row) for row in cursor.fetchall()]

def get_events_for_project(self, project_id: str) -> List[Dict]:
    """Get events for a project"""
    cursor = self.conn.execute(
        "SELECT * FROM events WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,)
    )
    return [dict(row) for row in cursor.fetchall()]
```

**Step 4: Add Event Query Endpoints**
```python
@router.get("/analytics/events")
def get_user_events(
    limit: int = 100,
    current_user: str = Depends(get_current_user)
):
    """Get interaction events for current user"""
    db = get_database()
    events = db.get_events_for_user(current_user, limit)
    return APIResponse(success=True, data={"events": events})

@router.get("/{project_id}/events")
def get_project_events(
    project_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get all events for a project"""
    db = get_database()
    events = db.get_events_for_project(project_id)
    return APIResponse(success=True, data={"events": events})
```

**Files to Modify:**
- `backend/src/socrates_api/database.py` (add table + methods)
- `backend/src/socrates_api/routers/events.py` (update record_event function)
- Create new endpoints for event queries

**Test Cases:**
- [ ] Events persisted to database
- [ ] Events survive server restart
- [ ] Query methods return correct events
- [ ] Event schema consistent
- [ ] User can view their event history

**Estimated Time:** 30 minutes

---

### FIX 5: Orphaned Knowledge Base Documents - CRITICAL DATA INTEGRITY

**Current Broken Code:**
```python
# In DELETE project:
DELETE FROM projects WHERE id = ?
# *** MISSING: NOT cleaning knowledge_documents! ***
```

**Issue:**
- Knowledge documents remain in database
- Foreign key references become invalid
- Orphaned records accumulate
- Data corruption

**Fix Required:**

**Option A: Add CASCADE DELETE (Recommended)**
```python
# In database.py _initialize(), modify knowledge_documents table:
self.conn.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_documents (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        source TEXT,
        document_type TEXT DEFAULT 'text',
        uploaded_at TEXT NOT NULL,
        chunk_count INTEGER DEFAULT 0,
        is_deleted INTEGER DEFAULT 0,
        metadata TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,  -- ADD CASCADE
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(project_id, id)
    )
""")
```

**Option B: Manual Cleanup (If cascade not supported)**
```python
# In projects.py delete_project():
def delete_project(self, project_id: str):
    """Delete project and all related data"""
    try:
        db = get_database()

        # Clean up related data BEFORE deleting project
        db.conn.execute("DELETE FROM knowledge_documents WHERE project_id = ?", (project_id,))
        db.conn.execute("DELETE FROM team_members WHERE project_id = ?", (project_id,))
        db.conn.execute("DELETE FROM events WHERE project_id = ?", (project_id,))

        # THEN delete project
        db.conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        db.conn.commit()

        logger.info(f"Project {project_id} and all related data deleted")

    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        raise
```

**Files to Modify:**
- `backend/src/socrates_api/database.py` (add CASCADE DELETE or cleanup methods)
- `backend/src/socrates_api/routers/projects.py` (implement cleanup before delete)

**Test Cases:**
- [ ] Delete project with knowledge documents
- [ ] Knowledge documents removed or properly handled
- [ ] No foreign key violations
- [ ] No orphaned records

**Estimated Time:** 15 minutes

---

## Priority 2: HIGH FIXES (Complete in Next Sprint)

### FIX 6: Transaction Guarantees (30-40 minutes)
- Wrap multi-step operations in database transactions
- Add rollback on failure
- Test failure scenarios

### FIX 7: Improve Error Handling (30-40 minutes)
- Remove silent failures (catch exceptions but propagate)
- Add explicit error states
- Users notified of failures

### FIX 8: WebSocket Message Sync (30-40 minutes)
- Sync WebSocket messages with conversation_history
- Ensure consistency between transports

---

## Priority 3: MEDIUM FIXES (Following Sprint)

### FIX 9: Conflict History Tracking (30 minutes)
### FIX 10: Atomic Conflict Resolution (30 minutes)
### FIX 11: WebSocket Broadcast (45 minutes)

---

## IMPLEMENTATION SCHEDULE

### Session 1: Priority 1 Fixes (2-3 hours)
1. FIX 1: WebSocket Auth - 15 min
2. FIX 2: Cache Invalidation - 20 min
3. FIX 3: Conversation Consolidation - 45 min
4. FIX 4: Event Persistence - 30 min
5. FIX 5: Orphaned Documents - 15 min
6. Testing - 20 min
**Total: 2h 35min**

### Session 2: Priority 2 Fixes (2-3 hours)
7. FIX 6: Transactions - 35 min
8. FIX 7: Error Handling - 35 min
9. FIX 8: WebSocket Sync - 35 min
10. Testing - 20 min
**Total: 2h 5min**

### Session 3: Priority 3 Fixes (2-3 hours)
11. FIX 9: Conflict History - 30 min
12. FIX 10: Conflict Resolution - 30 min
13. FIX 11: WebSocket Broadcast - 45 min
14. Testing - 20 min
**Total: 2h 5min**

---

## VERIFICATION CHECKLIST

After each fix:
- [ ] Code compiles without errors
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] No new warnings in logs
- [ ] Backward compatible with existing data

Final verification:
- [ ] All 6 critical fixes implemented
- [ ] All 8 moderate fixes implemented
- [ ] Full system test (E2E)
- [ ] Performance unaffected
- [ ] No regressions in existing functionality

---

## ROLLBACK PLAN

If any fix causes issues:
1. Revert the specific fix file
2. Restart API
3. Investigate root cause
4. Create alternative fix

No data loss expected (all changes backward compatible).

---

**Ready to implement. Awaiting approval.**
