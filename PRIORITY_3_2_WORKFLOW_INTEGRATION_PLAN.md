# Priority 3.2: Workflow Integration

**Status**: Ready for Implementation
**Estimated Effort**: 3 hours
**Expected Result**: Workflow automation for phase transitions, code review, and learning assessment

---

## Overview

Integrate socratic-workflow library to add workflow automation capabilities. This enables:
- Automated phase transitions based on maturity
- Code review workflows
- Learning assessment workflows
- Custom workflow automation

---

## Current State

### Available Libraries
- socratic-workflow: Provides WorkflowEngine, Workflow, Step classes
- Integration points: Orchestrator, projects management, learning

### Usage Opportunities
1. **Phase Transitions**: Automate advancement when phase maturity reaches threshold
2. **Code Review**: Define and execute code review workflows
3. **Learning**: Automate learning assessment workflows
4. **Custom**: Allow users to define custom workflows

---

## Implementation Plan

### Phase 3.2.1: Add WorkflowIntegration to models_local.py (45 min)

**New Class**: WorkflowIntegration (~120 lines)

```python
class WorkflowIntegration:
    """Wrapper around socratic-workflow library for workflow automation"""
    def __init__(self):
        self.available = False
        self.engine = None
        self.workflows = {}

        try:
            from socratic_workflow import WorkflowEngine, Workflow
            self.engine = WorkflowEngine()
            self.available = True
            logger.info("socratic-workflow library initialized successfully")
        except ImportError:
            logger.warning("socratic-workflow library not available - workflow features disabled")
            self.available = False
        except Exception as e:
            logger.warning(f"Failed to initialize socratic-workflow: {e}")
            self.available = False

    def create_workflow(
        self,
        workflow_id: str,
        name: str,
        steps: List[Dict[str, Any]],
        metadata: Dict = None
    ) -> bool:
        """Create a new workflow"""
        if not self.available or not self.engine:
            logger.debug(f"Workflow engine unavailable, cannot create workflow {workflow_id}")
            return False

        try:
            workflow = self.engine.create_workflow(
                workflow_id=workflow_id,
                name=name,
                steps=steps,
                metadata=metadata or {}
            )
            self.workflows[workflow_id] = workflow
            logger.debug(f"Created workflow: {workflow_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            return False

    def execute_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a workflow"""
        if not self.available or not self.engine:
            logger.debug(f"Workflow engine unavailable, cannot execute workflow {workflow_id}")
            return {"status": "failed", "error": "Workflow engine unavailable"}

        try:
            if workflow_id not in self.workflows:
                workflow = self.engine.get_workflow(workflow_id)
                if not workflow:
                    return {"status": "failed", "error": f"Workflow not found: {workflow_id}"}
                self.workflows[workflow_id] = workflow

            workflow = self.workflows[workflow_id]
            result = self.engine.execute(workflow, context or {})
            logger.debug(f"Executed workflow: {workflow_id}")
            return result if result else {"status": "completed"}
        except Exception as e:
            logger.error(f"Failed to execute workflow: {e}")
            return {"status": "failed", "error": str(e)}

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a workflow"""
        if not self.available or not self.engine:
            return {"status": "unavailable"}

        try:
            status = self.engine.get_status(workflow_id)
            return status if status else {"status": "not_found"}
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return {"status": "error", "error": str(e)}

    def get_workflow_history(
        self,
        workflow_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get execution history of a workflow"""
        if not self.available or not self.engine:
            logger.debug(f"Workflow engine unavailable for history of {workflow_id}")
            return []

        try:
            history = self.engine.get_history(workflow_id, limit=limit)
            return history if history else []
        except Exception as e:
            logger.error(f"Failed to get workflow history: {e}")
            return []

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        if not self.available or not self.engine:
            logger.debug(f"Workflow engine unavailable, cannot delete workflow {workflow_id}")
            return False

        try:
            self.engine.delete_workflow(workflow_id)
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]
            logger.debug(f"Deleted workflow: {workflow_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete workflow: {e}")
            return False

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows"""
        if not self.available or not self.engine:
            return []

        try:
            workflows = self.engine.list_workflows()
            return workflows if workflows else []
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []

    def get_status(self) -> Dict[str, bool]:
        """Get workflow integration status"""
        return {
            "available": self.available,
            "engine_available": self.engine is not None,
        }
```

---

### Phase 3.2.2: Create Workflow Router (1 hour)

**File**: `backend/src/socrates_api/routers/workflow.py` (NEW)

**Endpoints**:

1. **POST /workflow/create** - Create workflow
   - Parameters: workflow_id, name, steps, metadata
   - Response: Workflow created with ID

2. **POST /workflow/execute** - Execute workflow
   - Parameters: workflow_id, context
   - Response: Execution results

3. **GET /workflow/status/{workflow_id}** - Get workflow status
   - Parameters: workflow_id
   - Response: Current status and progress

4. **GET /workflow/history/{workflow_id}** - Get execution history
   - Parameters: workflow_id, limit
   - Response: List of past executions

5. **DELETE /workflow/{workflow_id}** - Delete workflow
   - Parameters: workflow_id
   - Response: Deletion confirmation

6. **GET /workflow/list** - List workflows
   - Response: All available workflows (optional)

---

### Phase 3.2.3: Pre-Built Workflow Templates (30 min)

**Workflow Templates** (predefined workflows):

1. **Phase Advancement Workflow**
   ```
   Step 1: Check phase maturity
   Step 2: Validate advancement criteria
   Step 3: Update project phase
   Step 4: Clear question cache for old phase
   Step 5: Notify user
   ```

2. **Code Review Workflow**
   ```
   Step 1: Analyze code quality
   Step 2: Check for security issues
   Step 3: Verify tests exist
   Step 4: Generate review summary
   Step 5: Return findings
   ```

3. **Learning Assessment Workflow**
   ```
   Step 1: Collect learning interactions
   Step 2: Calculate mastery levels
   Step 3: Detect misconceptions
   Step 4: Generate recommendations
   Step 5: Update progress
   ```

---

### Phase 3.2.4: Orchestrator Integration (45 min)

**File**: `backend/src/socrates_api/orchestrator.py`

**Add to LLMClientAdapter**:

```python
def execute_workflow(
    self,
    workflow_id: str,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Execute a workflow with project context"""
    from socrates_api.models_local import WorkflowIntegration

    workflow = WorkflowIntegration()
    if not workflow.available:
        logger.warning(f"Workflow integration unavailable for {workflow_id}")
        return {"status": "unavailable"}

    # Build workflow context
    wf_context = {
        "project": context.get("project"),
        "user": context.get("user"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **context
    }

    # Execute workflow
    result = workflow.execute_workflow(workflow_id, wf_context)
    logger.info(f"Workflow executed: {workflow_id}, status: {result.get('status')}")
    return result

def advance_phase_with_workflow(self, project, next_phase: str) -> Dict[str, Any]:
    """Advance project phase using workflow"""
    # Execute phase advancement workflow
    result = self.execute_workflow(
        "phase_advancement",
        {
            "project": project,
            "current_phase": project.phase,
            "next_phase": next_phase,
            "maturity_scores": project.phase_maturity_scores
        }
    )
    return result
```

---

## Workflow Definitions

### 1. Phase Advancement Workflow

```json
{
  "workflow_id": "phase_advancement",
  "name": "Advance Project Phase",
  "steps": [
    {
      "id": "check_maturity",
      "type": "check",
      "condition": "maturity >= threshold",
      "description": "Check if phase maturity meets advancement criteria"
    },
    {
      "id": "validate_criteria",
      "type": "validate",
      "criteria": ["goals_defined", "requirements_set", "design_complete"],
      "description": "Validate all advancement criteria are met"
    },
    {
      "id": "update_phase",
      "type": "update",
      "action": "set_phase",
      "target": "next_phase",
      "description": "Update project phase to next phase"
    },
    {
      "id": "clear_cache",
      "type": "action",
      "action": "clear_question_cache",
      "params": {"phase": "current_phase"},
      "description": "Clear question cache for old phase"
    },
    {
      "id": "notify",
      "type": "notify",
      "event": "phase_advanced",
      "description": "Notify user of phase advancement"
    }
  ],
  "completion_condition": "all_steps_completed"
}
```

### 2. Code Review Workflow

```json
{
  "workflow_id": "code_review",
  "name": "Automated Code Review",
  "steps": [
    {
      "id": "analyze_quality",
      "type": "analyze",
      "analyzer": "code_analyzer",
      "metrics": ["complexity", "maintainability", "coverage"]
    },
    {
      "id": "check_security",
      "type": "security_scan",
      "frameworks": ["owasp", "cwe"]
    },
    {
      "id": "verify_tests",
      "type": "check",
      "condition": "test_coverage > 80%"
    },
    {
      "id": "generate_report",
      "type": "generate",
      "template": "code_review_report"
    }
  ]
}
```

### 3. Learning Assessment Workflow

```json
{
  "workflow_id": "learning_assessment",
  "name": "Learning Progress Assessment",
  "steps": [
    {
      "id": "collect_interactions",
      "type": "collect",
      "source": "learning_interactions"
    },
    {
      "id": "calculate_mastery",
      "type": "calculate",
      "metric": "concept_mastery"
    },
    {
      "id": "detect_misconceptions",
      "type": "detect",
      "detector": "misconception_detector"
    },
    {
      "id": "generate_recommendations",
      "type": "generate",
      "engine": "recommendation_engine"
    }
  ]
}
```

---

## API Endpoints

### Workflow Endpoints (5-6 endpoints)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /workflow/create | Create workflow |
| POST | /workflow/execute | Execute workflow |
| GET | /workflow/status/{id} | Get workflow status |
| GET | /workflow/history/{id} | Get execution history |
| DELETE | /workflow/{id} | Delete workflow |
| GET | /workflow/list | List workflows (optional) |

---

## Usage Examples

### Create Phase Advancement Workflow
```bash
curl -X POST "http://localhost:8000/workflow/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "phase_advancement_v1",
    "name": "Advance to Analysis Phase",
    "steps": [
      {"id": "check", "type": "check", "condition": "maturity >= 0.95"},
      {"id": "update", "type": "update", "action": "set_phase", "target": "analysis"}
    ]
  }'
```

### Execute Workflow
```bash
curl -X POST "http://localhost:8000/workflow/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "phase_advancement_v1",
    "context": {
      "project_id": "proj_123",
      "current_phase": "discovery",
      "maturity": 0.96
    }
  }'
```

### Get Workflow Status
```bash
curl -X GET "http://localhost:8000/workflow/status/phase_advancement_v1" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Execution History
```bash
curl -X GET "http://localhost:8000/workflow/history/phase_advancement_v1?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Testing Strategy

### Unit Tests
```python
test_workflow_integration_available()
test_create_workflow()
test_execute_workflow()
test_workflow_status()
test_workflow_history()
test_delete_workflow()
test_workflow_graceful_fallback()
```

### Integration Tests
```python
test_phase_advancement_workflow()
test_code_review_workflow()
test_learning_assessment_workflow()
test_workflow_with_multiple_steps()
test_workflow_error_handling()
```

### E2E Tests
```
1. Create phase advancement workflow
2. Execute with project context
3. Verify phase changed
4. Get execution history
5. Verify workflow in history
```

---

## Success Criteria

- [ ] WorkflowIntegration class implemented in models_local
- [ ] Workflow router created with 5-6 endpoints
- [ ] Phase advancement workflow automated
- [ ] Code review workflow defined
- [ ] Learning assessment workflow defined
- [ ] Orchestrator integrated with workflow engine
- [ ] Graceful fallback if library unavailable
- [ ] All endpoints tested and working

---

## Files to Create/Modify

1. **backend/src/socrates_api/models_local.py** (add)
   - WorkflowIntegration class (~120 lines)

2. **backend/src/socrates_api/routers/workflow.py** (NEW)
   - 5-6 endpoints (~250 lines)

3. **backend/src/socrates_api/orchestrator.py** (modify)
   - Add execute_workflow() method
   - Add advance_phase_with_workflow() method

4. **backend/src/socrates_api/routers/__init__.py** (modify)
   - Add workflow_router import

5. **backend/src/socrates_api/main.py** (modify)
   - Add workflow_router to imports and registration

---

## Estimated Breakdown

| Task | Time |
|------|------|
| WorkflowIntegration class | 45 min |
| Workflow router creation | 60 min |
| Workflow templates | 30 min |
| Orchestrator integration | 45 min |
| **Total** | **3 hours** |

---

**Ready to implement Priority 3.2: Workflow Integration**

Next: Proceed to Priority 3.3 (Analyzer Deep Integration)
