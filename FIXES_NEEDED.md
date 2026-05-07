# SOCRATES LOCAL FIXES - IMPLEMENTATION GUIDE

## CRITICAL ISSUE 1: Question Lifecycle Management
**Status**: BROKEN - Questions never removed from pending_questions list
**Impact**: Memory leak, unclear current question, accumulation

### Location 1A: Add cleanup helper to ProjectContext
**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/models/project.py`
**Lines**: After line 272 (after is_solo_project method)

**Add this method**:
```python
def cleanup_pending_questions(self, max_pending: int = 1) -> int:
    """
    Clean up pending questions by removing answered/skipped ones.
    Maintains FIFO order with max_pending limit.

    Args:
        max_pending: Maximum pending questions to keep (default 1 for single active)

    Returns:
        Number of questions removed
    """
    if not self.pending_questions:
        return 0

    removed_count = 0

    # Remove all answered and skipped questions
    original_count = len(self.pending_questions)
    self.pending_questions = [
        q for q in self.pending_questions
        if q.get("status") not in ("answered", "skipped")
    ]
    removed_count = original_count - len(self.pending_questions)

    # Trim to max_pending questions (keep first ones in FIFO order)
    if len(self.pending_questions) > max_pending:
        self.pending_questions = self.pending_questions[:max_pending]

    return removed_count
```

---

### Location 1B: Call cleanup in socratic_agents library
**IMPORTANT**: These are in the .venv (installed package), so fixes must go to local socratic_system files OR the library must be patched via setup.

**File**: `/c/Users/themi/PycharmProjects/Socrates/.venv/Lib/site-packages/socratic_agents/socratic_counselor.py`
**Problem**: This is in .venv - need to patch in local code instead

**Solution**: Create wrapper methods in a new local file:
**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/question_service.py` (NEW FILE)

```python
"""Service for managing question lifecycle"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from socratic_system.models import ProjectContext

class QuestionService:
    """Manages question cleanup and lifecycle"""

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)

    def cleanup_pending_questions(
        self,
        project: "ProjectContext",
        max_pending: int = 1
    ) -> int:
        """
        Clean up answered/skipped questions from pending_questions list.

        Args:
            project: ProjectContext with pending_questions
            max_pending: Maximum questions to keep pending (1 for single active)

        Returns:
            Number of questions removed
        """
        if not project or not project.pending_questions:
            return 0

        removed = project.cleanup_pending_questions(max_pending)
        if removed > 0:
            self.logger.debug(f"Cleaned up {removed} answered/skipped questions")

        return removed
```

---

### Location 1C: Hook cleanup calls after answer/skip/process
**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/socratic_counselor_wrapper.py` (NEW FILE)

Create a wrapper to patch the socratic_counselor behavior:

```python
"""Patches to socratic_counselor agent for question cleanup"""

from typing import Dict, Any
from socratic_system.utils.logger import get_logger

logger = get_logger("socratic_counselor_wrapper")

def patch_socratic_counselor_cleanup(agent):
    """
    Monkey-patch socratic_counselor agent to add question cleanup.

    Call this in orchestrator after initializing socratic_counselor.
    """

    original_process = agent.process

    def patched_process(request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request with cleanup support"""
        action = request.get("action")
        project = request.get("project")

        # Call original process
        result = original_process(request)

        # After answer/skip/process_response, cleanup pending questions
        if action in ("answer_question", "skip_question", "process_response"):
            if project and project.pending_questions:
                from socratic_system.services.question_service import QuestionService
                qs = QuestionService(None)
                removed = qs.cleanup_pending_questions(project, max_pending=1)
                if removed > 0:
                    logger.debug(f"Cleaned up {removed} answered/skipped questions after {action}")

                # Save project to persist cleanup
                if hasattr(agent, 'database') and agent.database:
                    agent.database.save_project(project)

        return result

    # Replace the process method
    agent.process = patched_process
    logger.info("Patched socratic_counselor with question cleanup support")
```

---

### Location 1D: Apply patch in orchestrator
**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/orchestration/orchestrator.py`
**Lines**: Around line 356 (in socratic_counselor property after initialization)

**Modify**:
```python
@property
def socratic_counselor(self) -> SocraticCounselorAgent:
    """Lazy-load socratic counselor agent"""
    if "socratic_counselor" not in self._agents_cache:
        from socratic_agents import SocraticCounselorAgent
        from socratic_system.services.socratic_counselor_wrapper import patch_socratic_counselor_cleanup

        agent = SocraticCounselorAgent(self)
        # Apply question cleanup patch
        patch_socratic_counselor_cleanup(agent)
        self._agents_cache["socratic_counselor"] = agent
    return self._agents_cache["socratic_counselor"]
```

---

## ISSUE 2: Knowledge Base Content Storage
**Status**: BROKEN - Field exists but never populated
**Impact**: KB content lost, not persisted, can't reuse

### Location 2A: Update project_service.py
**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/project_service.py`
**Lines**: 41-69 (create_project method)

**Current code** (lines 41-69):
```python
def create_project(self, spec: Dict[str, Any]) -> "ProjectContext":
    """Create new project with initial specifications.
    ...
    """
    if not spec.get("name"):
        raise ValueError("Project name is required")

    self.logger.info(f"Creating project: {spec.get('name')}")

    # Create project context
    import datetime
    import uuid
    from socratic_system.models import ProjectContext

    now = datetime.datetime.now()
    project = ProjectContext(
        project_id=str(uuid.uuid4()),
        name=spec["name"],
        description=spec.get("description", ""),
        owner=spec.get("user_id"),
        phase="discovery",
        created_at=now,
        updated_at=now,
    )
```

**Fix** (add knowledge_base_content):
```python
def create_project(self, spec: Dict[str, Any]) -> "ProjectContext":
    """Create new project with initial specifications.
    ...
    """
    if not spec.get("name"):
        raise ValueError("Project name is required")

    self.logger.info(f"Creating project: {spec.get('name')}")

    # Create project context
    import datetime
    import uuid
    from socratic_system.models import ProjectContext

    now = datetime.datetime.now()
    project = ProjectContext(
        project_id=str(uuid.uuid4()),
        name=spec["name"],
        description=spec.get("description", ""),
        owner=spec.get("user_id"),
        phase="discovery",
        created_at=now,
        updated_at=now,
        knowledge_base_content=spec.get("knowledge_base_content", ""),  # NEW LINE
    )
```

---

## ISSUE 3: Initial Context Extraction Validation
**Status**: BROKEN - No validation of insights before applying
**Impact**: Empty/null insights processed silently, debugging difficult

### Location 3A: Add validation to insight_service.py
**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/insight_service.py`
**Lines**: 38-66 (extract_insights method)

**Add after line 65**:
```python
def extract_insights(
    self,
    context: str,
    project: "ProjectContext",
    user_id: Optional[str] = None,
    user_auth_method: str = "api_key",
) -> Dict[str, Any]:
    """Extract insights from user response using Claude.
    ...
    """
    self.logger.info(f"Extracting insights from user response ({len(context)} chars)")

    insights = self.claude_client.extract_insights(
        context,
        project,
        user_auth_method=user_auth_method,
        user_id=user_id,
    )

    self.logger.debug(f"Extracted insights: {len(insights)} keys")

    # NEW: Validate insights
    if not self._validate_insights(insights):
        self.logger.warning("Extracted insights failed validation - will not be applied")
        return {}

    return insights

def _validate_insights(self, insights: Dict[str, Any]) -> bool:
    """Validate that insights are non-empty and well-formed.

    Args:
        insights: Insights dict from Claude

    Returns:
        True if valid, False otherwise
    """
    if not insights or not isinstance(insights, dict):
        self.logger.warning("Insights validation failed: not a dict or empty")
        return False

    # Check that at least one insight key has non-empty content
    has_content = False
    for key, value in insights.items():
        if value and (isinstance(value, str) or isinstance(value, list)):
            if isinstance(value, str) and value.strip():
                has_content = True
                break
            elif isinstance(value, list) and len(value) > 0:
                has_content = True
                break

    if not has_content:
        self.logger.warning("Insights validation failed: no non-empty content found")
        return False

    self.logger.debug(f"Insights validation passed: {list(insights.keys())}")
    return True
```

---

### Location 3B: Add validation to orchestrator KB loading
**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/orchestration/orchestrator.py`
**Lines**: 510-517 (_process_knowledge_entries method)

**Current code**:
```python
def _process_knowledge_entries(self, knowledge_data: list) -> tuple:
    """Process and add knowledge entries to database"""
    self.logger.info(f"Found {len(knowledge_data)} knowledge entries to load")

    loaded_count = 0
    error_count = 0

    for entry_data in knowledge_data:
        if self._add_knowledge_entry(entry_data):
            loaded_count += 1
        else:
            error_count += 1

    return loaded_count, error_count
```

**Fix** (add validation):
```python
def _process_knowledge_entries(self, knowledge_data: list) -> tuple:
    """Process and add knowledge entries to database"""
    self.logger.info(f"Found {len(knowledge_data)} knowledge entries to load")

    loaded_count = 0
    error_count = 0

    for entry_data in knowledge_data:
        if self._add_knowledge_entry(entry_data):
            loaded_count += 1
        else:
            error_count += 1

    # NEW: Validate that entries were actually added
    if loaded_count == 0 and len(knowledge_data) > 0:
        self.logger.warning(f"Knowledge base loading failed: {len(knowledge_data)} entries processed but {error_count} errors")
        return loaded_count, error_count

    if loaded_count > 0:
        # Verify entries exist in vector DB
        if hasattr(self.vector_db, 'count'):
            entry_count = self.vector_db.count()
            if entry_count > 0:
                self.logger.info(f"Verified: {entry_count} total entries in knowledge database")
            else:
                self.logger.warning("Knowledge database is empty after loading")

    return loaded_count, error_count
```

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Question Cleanup (CRITICAL)
- [ ] Add cleanup_pending_questions() method to ProjectContext in project.py
- [ ] Create question_service.py with QuestionService
- [ ] Create socratic_counselor_wrapper.py with patch function
- [ ] Modify orchestrator.py to apply patch to socratic_counselor
- [ ] Test: Verify pending_questions list shrinks after each answer/skip
- [ ] Test: Verify max 1 active question at a time

### Phase 2: KB Content Storage (HIGH)
- [ ] Modify project_service.py to accept knowledge_base_content parameter
- [ ] Verify KB content is stored in project creation
- [ ] Test: Create project with KB content and verify persistence

### Phase 3: Validation (MEDIUM)
- [ ] Add _validate_insights() to insight_service.py
- [ ] Add validation call to extract_insights()
- [ ] Add KB loading validation to orchestrator.py
- [ ] Test: Verify empty insights are rejected
- [ ] Test: Verify KB loading is verified

---

## FILE SUMMARY

### Files to CREATE:
1. `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/question_service.py`
2. `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/socratic_counselor_wrapper.py`

### Files to MODIFY:
1. `/c/Users/themi/PycharmProjects/Socrates/socratic_system/models/project.py` - Add cleanup method
2. `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/project_service.py` - Add KB content param
3. `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/insight_service.py` - Add validation
4. `/c/Users/themi/PycharmProjects/Socrates/socratic_system/orchestration/orchestrator.py` - Apply patch + verify KB

### NO Changes needed to:
- socratic_agents library (in .venv) - patched via wrapper instead
- database layer
- CLI commands

---

## NOTES

1. **Library Patching**: socratic-agents is in .venv, so we can't directly edit it
   - Solution: Create wrapper that monkey-patches at runtime
   - Called from orchestrator initialization

2. **Backward Compatibility**:
   - All changes are additive (no breaking changes)
   - Existing projects with answered questions will be cleaned on next load
   - KB content field already exists, just needs population

3. **Testing Strategy**:
   - Unit test: cleanup_pending_questions()
   - Integration test: Full Q&A flow with cleanup
   - Persistence test: Save/load project with cleaned questions

