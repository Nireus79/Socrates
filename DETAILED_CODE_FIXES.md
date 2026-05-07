# SOCRATES - DETAILED CODE FIXES WITH EXACT LOCATIONS

## FIX 1: Add cleanup_pending_questions() to ProjectContext

**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/models/project.py`
**Location**: After line 272 (after the `is_solo_project()` method ends)
**Action**: ADD NEW METHOD

Current end of file (around line 272-273):
```python
    def is_solo_project(self) -> bool:
        """Check if this is a solo project (only owner, no other team members)."""
        return len(self.team_members or []) <= 1
```

**ADD AFTER LINE 273**:
```python
    def cleanup_pending_questions(self, max_pending: int = 1) -> int:
        """
        Clean up pending questions by removing answered/skipped ones.
        Maintains FIFO order with max_pending limit.

        Removes all questions with status='answered' or status='skipped'
        and trims list to max_pending questions (keeping first ones in FIFO order).

        Args:
            max_pending: Maximum pending questions to keep (default 1 for single active)

        Returns:
            Number of questions removed
        """
        if not self.pending_questions:
            return 0

        removed_count = 0

        # Remove all answered and skipped questions (clean up completed ones)
        original_count = len(self.pending_questions)
        self.pending_questions = [
            q for q in self.pending_questions
            if q.get("status") not in ("answered", "skipped")
        ]
        removed_count = original_count - len(self.pending_questions)

        # Trim to max_pending questions (keep first ones in FIFO order)
        # This ensures only max_pending active questions exist
        if len(self.pending_questions) > max_pending:
            self.pending_questions = self.pending_questions[:max_pending]

        return removed_count
```

**Test this addition**:
```python
# In test file, verify:
project = ProjectContext(...)
project.pending_questions = [
    {"id": "q1", "status": "answered", "question": "Q1"},
    {"id": "q2", "status": "unanswered", "question": "Q2"},
    {"id": "q3", "status": "answered", "question": "Q3"},
]
removed = project.cleanup_pending_questions(max_pending=1)
assert removed == 2  # Should remove q1 and q3
assert len(project.pending_questions) == 1  # Only q2 left
assert project.pending_questions[0]["id"] == "q2"  # FIFO order maintained
```

---

## FIX 2: Update project_service.py to store knowledge_base_content

**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/project_service.py`
**Location**: Lines 41-69 in create_project() method
**Action**: ADD ONE LINE

Current code (lines 61-69):
```python
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

**CHANGE TO** (add line after `updated_at=now,`):
```python
        now = datetime.datetime.now()
        project = ProjectContext(
            project_id=str(uuid.uuid4()),
            name=spec["name"],
            description=spec.get("description", ""),
            owner=spec.get("user_id"),
            phase="discovery",
            created_at=now,
            updated_at=now,
            knowledge_base_content=spec.get("knowledge_base_content", ""),
        )
```

**Test this change**:
```python
# In test file, verify:
spec = {
    "name": "TestProject",
    "user_id": "user1",
    "knowledge_base_content": "# My KB\nSome content here"
}
project = project_service.create_project(spec)
assert project.knowledge_base_content == "# My KB\nSome content here"

# Test without KB content
spec2 = {"name": "TestProject2", "user_id": "user2"}
project2 = project_service.create_project(spec2)
assert project2.knowledge_base_content == ""
```

---

## FIX 3: Add validation to insight_service.py

**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/insight_service.py`
**Location**: Lines 38-66 (extract_insights method)
**Action**: MODIFY METHOD + ADD NEW METHOD

Current code (lines 38-66):
```python
    def extract_insights(
        self,
        context: str,
        project: "ProjectContext",
        user_id: Optional[str] = None,
        user_auth_method: str = "api_key",
    ) -> Dict[str, Any]:
        """Extract insights from user response using Claude.

        Args:
            context: User response text
            project: ProjectContext
            user_id: User identifier
            user_auth_method: User's auth method for API

        Returns:
            Extracted insights dict with goals, requirements, tech_stack, constraints
        """
        self.logger.info(f"Extracting insights from user response ({len(context)} chars)")

        insights = self.claude_client.extract_insights(
            context,
            project,
            user_auth_method=user_auth_method,
            user_id=user_id,
        )

        self.logger.debug(f"Extracted insights: {len(insights)} keys")
        return insights
```

**CHANGE TO**:
```python
    def extract_insights(
        self,
        context: str,
        project: "ProjectContext",
        user_id: Optional[str] = None,
        user_auth_method: str = "api_key",
    ) -> Dict[str, Any]:
        """Extract insights from user response using Claude.

        Args:
            context: User response text
            project: ProjectContext
            user_id: User identifier
            user_auth_method: User's auth method for API

        Returns:
            Extracted insights dict with goals, requirements, tech_stack, constraints
        """
        self.logger.info(f"Extracting insights from user response ({len(context)} chars)")

        insights = self.claude_client.extract_insights(
            context,
            project,
            user_auth_method=user_auth_method,
            user_id=user_id,
        )

        self.logger.debug(f"Extracted insights: {len(insights)} keys")

        # NEW: Validate insights before returning
        if not self._validate_insights(insights):
            self.logger.warning("Extracted insights failed validation - returning empty dict")
            return {}

        return insights
```

**ADD NEW METHOD after extract_insights()** (around line 67):
```python
    def _validate_insights(self, insights: Dict[str, Any]) -> bool:
        """Validate that insights are non-empty and well-formed.

        Args:
            insights: Insights dict from Claude

        Returns:
            True if valid, False otherwise
        """
        # Check if insights is None or not a dict
        if not insights or not isinstance(insights, dict):
            self.logger.warning("Insights validation failed: not a dict or empty")
            return False

        # Check that at least one insight key has non-empty content
        has_content = False
        for key, value in insights.items():
            if value:
                if isinstance(value, str):
                    if value.strip():  # Non-empty string
                        has_content = True
                        break
                elif isinstance(value, list):
                    if len(value) > 0:  # Non-empty list
                        has_content = True
                        break

        if not has_content:
            self.logger.warning("Insights validation failed: no non-empty content found")
            return False

        self.logger.debug(f"Insights validation passed: {list(insights.keys())}")
        return True
```

**Test this change**:
```python
# In test file, verify:

# Test with valid insights
service = InsightService(config, claude_client)
valid_insights = {
    "goals": "Build a system",
    "requirements": ["Req1", "Req2"]
}
assert service._validate_insights(valid_insights) == True

# Test with empty insights
empty_insights = {}
assert service._validate_insights(empty_insights) == False

# Test with null
assert service._validate_insights(None) == False

# Test with empty strings
invalid_insights = {
    "goals": "",
    "requirements": []
}
assert service._validate_insights(invalid_insights) == False
```

---

## FIX 4: Add KB loading validation to orchestrator.py

**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/orchestration/orchestrator.py`
**Location**: Lines 561-574 (_process_knowledge_entries method)
**Action**: MODIFY METHOD

Current code (lines 561-574):
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

**CHANGE TO**:
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

        # NEW: Validate that entries were actually added to database
        if loaded_count == 0 and len(knowledge_data) > 0:
            self.logger.warning(
                f"Knowledge base loading validation FAILED: {len(knowledge_data)} entries "
                f"attempted but only {loaded_count} successfully added ({error_count} errors)"
            )
        elif loaded_count > 0:
            # Verify entries exist in vector DB
            try:
                if hasattr(self.vector_db, 'count'):
                    total_entries = self.vector_db.count()
                    if total_entries > 0:
                        self.logger.info(
                            f"Knowledge base loading VERIFIED: {loaded_count} entries added, "
                            f"{total_entries} total in database"
                        )
                    else:
                        self.logger.warning(
                            "Knowledge base validation WARNING: entries added but database appears empty"
                        )
            except Exception as e:
                self.logger.debug(f"Could not verify KB entries in database: {e}")

        return loaded_count, error_count
```

**Test this change**:
```python
# In test file, verify:

# Mock knowledge data
knowledge_data = [
    {"id": "kb1", "category": "Python", "content": "Python info"},
    {"id": "kb2", "category": "Design", "content": "Design patterns"}
]

# Call with valid data
loaded, errors = orchestrator._process_knowledge_entries(knowledge_data)
assert loaded == 2
assert errors == 0

# Call with empty data
loaded, errors = orchestrator._process_knowledge_entries([])
assert loaded == 0

# Verify logging includes validation messages
# (Check orchestrator logs contain "VERIFIED:" or "FAILED:")
```

---

## FIX 5: Create question_service.py (NEW FILE)

**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/question_service.py` (CREATE NEW)
**Action**: CREATE NEW FILE

Full content:
```python
"""
Service for managing question lifecycle and cleanup.

Handles:
- Cleaning up answered/skipped questions from pending_questions list
- Maintaining FIFO order with max pending limit
- Ensuring single active question at a time
"""

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from socratic_system.models import ProjectContext


class QuestionService:
    """Manages question cleanup and FIFO lifecycle"""

    def __init__(self, config: Optional[object] = None):
        """Initialize question service.

        Args:
            config: Socrates configuration (optional)
        """
        self.logger = logging.getLogger(__name__)

    def cleanup_pending_questions(
        self,
        project: "ProjectContext",
        max_pending: int = 1
    ) -> int:
        """
        Clean up answered/skipped questions from project's pending_questions list.

        Removes all questions with status='answered' or status='skipped'.
        Trims list to max_pending questions (FIFO - keeps first ones).

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
            self.logger.debug(
                f"Cleaned up {removed} answered/skipped questions "
                f"({len(project.pending_questions)} pending remaining)"
            )

        return removed

    def get_active_question(self, project: "ProjectContext") -> Optional[dict]:
        """Get the current active (unanswered) question.

        Args:
            project: ProjectContext with pending_questions

        Returns:
            First unanswered question dict, or None if none pending
        """
        if not project or not project.pending_questions:
            return None

        for q in project.pending_questions:
            if q.get("status") == "unanswered":
                return q

        return None

    def get_pending_count(self, project: "ProjectContext") -> int:
        """Get count of unanswered pending questions.

        Args:
            project: ProjectContext with pending_questions

        Returns:
            Number of unanswered questions
        """
        if not project or not project.pending_questions:
            return 0

        return sum(1 for q in project.pending_questions if q.get("status") == "unanswered")
```

**Test this creation**:
```python
# In test file, verify:
from socratic_system.services.question_service import QuestionService

service = QuestionService()
project = ProjectContext(...)

# Test cleanup
project.pending_questions = [
    {"id": "q1", "status": "answered"},
    {"id": "q2", "status": "unanswered"},
    {"id": "q3", "status": "skipped"},
]
removed = service.cleanup_pending_questions(project, max_pending=1)
assert removed == 2

# Test get_active_question
active = service.get_active_question(project)
assert active["id"] == "q2"

# Test get_pending_count
count = service.get_pending_count(project)
assert count == 1
```

---

## FIX 6: Create socratic_counselor_wrapper.py (NEW FILE)

**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/services/socratic_counselor_wrapper.py` (CREATE NEW)
**Action**: CREATE NEW FILE

Full content:
```python
"""
Wrapper and patches for socratic_counselor agent to add question cleanup.

Since socratic_counselor is from socratic_agents library (in .venv),
we can't directly modify it. This wrapper monkey-patches the agent
to add cleanup support after answer/skip/process_response operations.
"""

from typing import Dict, Any
from socratic_system.utils.logger import get_logger

logger = get_logger("socratic_counselor_wrapper")


def patch_socratic_counselor_cleanup(agent):
    """
    Monkey-patch socratic_counselor agent to add question cleanup.

    Wraps the process() method to call cleanup_pending_questions()
    after answer/skip/process_response actions.

    Args:
        agent: SocraticCounselorAgent instance to patch

    Raises:
        AttributeError: If agent doesn't have required attributes
    """
    if not hasattr(agent, 'process'):
        raise AttributeError("Agent must have 'process' method")

    original_process = agent.process

    def patched_process(request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request with cleanup support for question lifecycle.

        Calls original process, then cleans up pending questions
        after certain actions.

        Args:
            request: Agent request dict with 'action' and 'project'

        Returns:
            Agent response dict
        """
        action = request.get("action")
        project = request.get("project")

        # Call original process method
        result = original_process(request)

        # After answer/skip/process_response, cleanup pending questions
        # These actions change question status and may result in answered/skipped questions
        if action in ("answer_question", "skip_question", "process_response"):
            if project and hasattr(project, 'pending_questions'):
                # Import here to avoid circular imports
                from socratic_system.services.question_service import QuestionService

                qs = QuestionService()
                removed = qs.cleanup_pending_questions(project, max_pending=1)

                if removed > 0:
                    logger.debug(
                        f"Cleaned up {removed} answered/skipped questions after '{action}' "
                        f"({qs.get_pending_count(project)} pending remaining)"
                    )

                    # Persist the cleanup to database
                    if hasattr(agent, 'database') and agent.database:
                        try:
                            agent.database.save_project(project)
                            logger.debug(f"Project saved with cleaned questions")
                        except Exception as e:
                            logger.warning(f"Failed to save project after cleanup: {e}")

        return result

    # Replace the process method with patched version
    agent.process = patched_process
    logger.info("Successfully patched socratic_counselor with question cleanup support")
    return agent
```

**Test this creation**:
```python
# In test file, verify:
from socratic_system.services.socratic_counselor_wrapper import patch_socratic_counselor_cleanup
from socratic_agents import SocraticCounselorAgent

# Create and patch agent
agent = SocraticCounselorAgent(orchestrator)
patched = patch_socratic_counselor_cleanup(agent)
assert patched is agent

# Verify process method works
result = agent.process({
    "action": "answer_question",
    "project": project,
    "question_id": "q1"
})
assert result["status"] == "success"

# Verify questions were cleaned up
# (Check that answered questions were removed from pending_questions)
```

---

## FIX 7: Apply patch in orchestrator.py

**File**: `/c/Users/themi/PycharmProjects/Socrates/socratic_system/orchestration/orchestrator.py`
**Location**: Lines 350-357 (socratic_counselor property)
**Action**: MODIFY PROPERTY

Current code (lines 350-357):
```python
    @property
    def socratic_counselor(self) -> SocraticCounselorAgent:
        """Lazy-load socratic counselor agent"""
        if "socratic_counselor" not in self._agents_cache:
            from socratic_agents import SocraticCounselorAgent

            self._agents_cache["socratic_counselor"] = SocraticCounselorAgent(self)
        return self._agents_cache["socratic_counselor"]
```

**CHANGE TO**:
```python
    @property
    def socratic_counselor(self) -> SocraticCounselorAgent:
        """Lazy-load socratic counselor agent with question cleanup patch"""
        if "socratic_counselor" not in self._agents_cache:
            from socratic_agents import SocraticCounselorAgent
            from socratic_system.services.socratic_counselor_wrapper import (
                patch_socratic_counselor_cleanup,
            )

            agent = SocraticCounselorAgent(self)
            # Apply question cleanup patch to agent
            patch_socratic_counselor_cleanup(agent)
            self._agents_cache["socratic_counselor"] = agent
        return self._agents_cache["socratic_counselor"]
```

**Test this change**:
```python
# In test file, verify:
from socratic_system.orchestration import AgentOrchestrator

orchestrator = AgentOrchestrator("test_api_key")

# Get counselor (should apply patch)
counselor = orchestrator.socratic_counselor
assert hasattr(counselor, 'process')

# Call process (should have cleanup)
result = counselor.process({
    "action": "answer_question",
    "project": project,
    "question_id": "q1"
})
assert result["status"] == "success"
```

---

## IMPLEMENTATION ORDER

1. **First**: Add cleanup_pending_questions() to ProjectContext (project.py)
   - This is the foundation all other fixes depend on

2. **Second**: Create question_service.py
   - Provides utilities for cleanup operations

3. **Third**: Create socratic_counselor_wrapper.py
   - Provides the patching mechanism

4. **Fourth**: Modify orchestrator.py to apply patch
   - Makes patch active in system

5. **Fifth**: Update project_service.py KB content
   - Independent fix for KB storage

6. **Sixth**: Add validation to insight_service.py
   - Independent fix for insight validation

7. **Seventh**: Add validation to orchestrator.py KB loading
   - Completes insight/KB validation

---

## VERIFICATION CHECKLIST

After implementing all fixes:

- [ ] Test cleanup_pending_questions() removes answered/skipped questions
- [ ] Test max_pending=1 limit is enforced (FIFO)
- [ ] Test get_active_question() returns first unanswered question
- [ ] Test create_project() accepts and stores knowledge_base_content
- [ ] Test extract_insights() validates and rejects empty insights
- [ ] Test orchestrator validates KB entries loaded successfully
- [ ] Test end-to-end: Answer Q1 -> Q1 removed -> Q2 becomes active
- [ ] Test project persists with cleaned questions after save/load
- [ ] Test KB content survives project reload

