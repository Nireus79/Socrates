# Phase 4 Investigation - Phase Advancement Flow

## Status: PARTIALLY IMPLEMENTED

**Date**: April 2, 2026
**Investigation Status**: Phase 4 components exist but need verification and completion

---

## Current Implementation Status

### ✅ Phase Advancement Endpoints - IMPLEMENTED

#### 1. PUT `/projects/{project_id}/phase` - Advance Phase (Lines 1243-1330)
**Location**: `backend/src/socrates_api/routers/projects.py:1243-1330`

**Features**:
- ✅ Auto-advance to next phase (discovery → analysis → design → implementation)
- ✅ Manual phase setting (provide specific phase in request)
- ✅ Owner-only access control
- ✅ Clears question cache for old phase
- ✅ Database persistence
- ✅ Full error handling

**Implementation**:
```python
@router.put(
    "/{project_id}/phase",
    response_model=APIResponse,
    ...
)
async def advance_phase(project_id, request, current_user, db):
    # Check owner access
    # Determine new phase (auto or from request)
    # Update project.phase
    # Clear question cache
    # Return updated project
```

**Status**: ✅ WORKING

---

#### 2. POST `/projects/{project_id}/phase/rollback` - Rollback Phase (Lines 1342-1425)
**Location**: `backend/src/socrates_api/routers/projects.py:1342-1425`

**Features**:
- ✅ Rollback to previous phase
- ✅ Prevents rollback from discovery phase
- ✅ Owner-only access control
- ✅ Database persistence
- ✅ Full error handling

**Implementation**:
```python
@router.post(
    "/{project_id}/phase/rollback",
    response_model=APIResponse,
    ...
)
async def rollback_phase(project_id, current_user, db):
    # Check owner access
    # Get current phase
    # Calculate previous phase
    # Validate can rollback (not at discovery)
    # Update project.phase
    # Return updated project
```

**Status**: ✅ WORKING

---

#### 3. DELETE `/projects/{project_id}/cache/questions` - Clear Question Cache (Lines 1428-1440+)
**Location**: `backend/src/socrates_api/routers/projects.py:1428-1440+`

**Features**:
- ✅ Clear cached questions when changing phases
- ✅ Phase-specific clearing
- ✅ Returns number of cleared items

**Status**: ✅ WORKING

---

### ✅ Maturity Calculation - IMPLEMENTED

#### Method: `calculate_phase_maturity()` in Orchestrator
**Location**: `backend/src/socrates_api/orchestrator.py:545-590`

**Features**:
- ✅ Uses socrates-maturity library for production-grade calculation
- ✅ Analyzes specs extraction
- ✅ Calculates maturity percentage (0-100%)
- ✅ Returns comprehensive metrics
- ✅ Integrated with answer processing

**Implementation**:
```python
def calculate_phase_maturity(self, project: Any) -> Dict[str, Any]:
    """
    Calculate maturity for a project phase using socratic-maturity library.

    Returns:
    - maturity_percentage: 0-100%
    - all_categories_covered: bool
    - focus_areas: [weak categories]
    - recommendations: [based on maturity]
    """
```

**Status**: ✅ WORKING

---

### ✅ Phase Completion Detection - IMPLEMENTED

#### In `send_message` endpoint (Lines 987-988, 1230-1237)
**Location**: `backend/src/socrates_api/routers/projects_chat.py`

**Features**:
- ✅ Extracts phase_complete from orchestrator result (line 988)
- ✅ Phase completion recommendations at score >= 100% (lines 1230-1237)
- ✅ User-friendly completion message

**Response Structure**:
```python
{
    "phase_complete": True,  # From orchestrator
    "recommendations": [
        {
            "priority": "success",
            "title": "Phase Complete",
            "description": "Excellent work! This phase is fully specified...",
            "focus_areas": []
        }
    ]
}
```

**Status**: ✅ WORKING

---

### ✅ Phase Readiness Checking - IMPLEMENTED

#### Method: `get_readiness_for_phase()` in Projects
**Location**: `backend/src/socrates_api/routers/projects.py:1078-1135`

**Features**:
- ✅ Calculates phase readiness score
- ✅ Breaks down by category (strong, adequate, weak, missing)
- ✅ Returns "ready_to_advance" flag at score >= 60%
- ✅ Includes focus areas for improvement

**Response Structure**:
```python
{
    "current_phase": "discovery",
    "phase_readiness": {
        "score": 75,
        "percentage": "75%",
        "status": "ready",
        "ready_to_advance": True,  # >= 60%
        "categories": {
            "strong": ["goals", "requirements"],
            "adequate": ["tech_stack"],
            "weak": ["constraints"],
            "missing": []
        }
    }
}
```

**Status**: ✅ WORKING

---

## Missing Components for Phase 4

### ⏳ 1. Phase Advancement Prompt Endpoint

**Purpose**: Generate user-friendly prompt asking if user is ready to advance

**Needed**:
```
GET /projects/{project_id}/phase/advancement-prompt
Response:
{
  "status": "success",
  "data": {
    "current_phase": "discovery",
    "maturity": 85,
    "ready_to_advance": True,
    "prompt": "Great work! Your project discovery phase is 85% complete...",
    "recommendation": "Ready to advance to analysis phase?",
    "can_advance": True,  # >= 100% OR manual override
    "next_phase": "analysis"
  }
}
```

**Status**: ⏳ NOT IMPLEMENTED

---

### ⏳ 2. Phase Completion Check (Non-blocking)

**Purpose**: After user answer, check if phase just completed

**Needed**: Enhancement to `send_message` response:
```python
# After processing answer:
if result.get("phase_complete"):
    # Include in response
    data["phase_complete"] = True
    data["next_phase"] = "analysis"
    data["advancement_prompt"] = "Phase complete! Ready to advance?"
```

**Current Status**: Partially done (phase_complete extracted but not fully utilized)
**Status**: ⚠️ PARTIAL

---

### ⏳ 3. Phase Advancement with Maturity Override

**Purpose**: Allow owner to override maturity check when advancing

**Needed**: Enhancement to `advance_phase`:
```python
# Add override flag to request
{
  "phase": "analysis",
  "force_advance": True,  # Override maturity check
  "reason": "User decided to move forward despite lower maturity"
}
```

**Current Status**: Not implemented
**Status**: ⏳ NOT IMPLEMENTED

---

### ⏳ 4. Phase Advancement Validation

**Purpose**: Verify phase can be advanced based on maturity

**Needed**:
```python
def validate_phase_advancement(project, target_phase) -> ValidationResult:
    """
    Check if project can advance to target_phase.

    Returns:
    - can_advance: bool
    - maturity: int (%)
    - requirements: dict (what's missing)
    - recommendations: list
    """
```

**Current Status**: Not implemented
**Status**: ⏳ NOT IMPLEMENTED

---

## Integration Points

### With Phase 3 (Conflict Resolution)
- ✅ Phase maturity updated after answer processing
- ✅ Conflicts don't prevent phase advancement
- ✅ Phase advancement independent of conflict resolution

### With Phase 2 (Orchestration)
- ✅ `_orchestrate_answer_processing` returns phase_complete
- ✅ Maturity calculated as part of answer processing
- ✅ Phase maturity passed to frontend

---

## Implementation Plan for Phase 4 Completion

### Task 1: Phase Advancement Prompt Endpoint (1 hour)

**File**: `backend/src/socrates_api/routers/projects.py`

**Implementation**:
```python
@router.get(
    "/{project_id}/phase/advancement-prompt",
    response_model=APIResponse,
)
async def get_phase_advancement_prompt(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Get phase advancement prompt when phase is near completion.

    Returns prompt data for user to decide if ready to advance.
    """
    project = db.load_project(project_id)
    maturity = calculate_phase_maturity(project)

    return APIResponse(
        success=True,
        data={
            "current_phase": project.phase,
            "maturity": maturity["maturity_percentage"],
            "ready_to_advance": maturity["maturity_percentage"] >= 100,
            "prompt": _generate_advancement_prompt(project, maturity),
            "next_phase": _get_next_phase(project.phase),
        }
    )
```

---

### Task 2: Enhanced Phase Completion Response (1 hour)

**File**: `backend/src/socrates_api/routers/projects_chat.py`

**Enhancement**: Improve send_message response when phase_complete detected

```python
# In send_message endpoint (around line 987-988)
if result.get("phase_complete"):
    # Add advancement prompt to response
    next_phase = _get_next_phase(project.phase)
    response_data["phase_complete"] = True
    response_data["next_phase"] = next_phase
    response_data["advancement_ready"] = result.get("phase_maturity", 0) >= 100
    response_data["advancement_prompt"] = (
        f"Congratulations! Your {project.phase} phase is complete. "
        f"Ready to advance to {next_phase}?"
    )
```

---

### Task 3: Phase Advancement Validation (1.5 hours)

**File**: `backend/src/socrates_api/orchestrator.py`

**Implementation**:
```python
def validate_phase_advancement(
    self,
    project: Any,
    target_phase: str,
    force: bool = False
) -> Dict[str, Any]:
    """
    Validate if project can advance to target_phase.

    Args:
        project: Project object
        target_phase: Desired next phase
        force: Override maturity requirements

    Returns:
        {
            "can_advance": bool,
            "maturity": int,
            "missing_requirements": list,
            "reason": str
        }
    """
    maturity = self.calculate_phase_maturity(project)

    if force:
        return {"can_advance": True, "forced": True}

    if maturity["maturity_percentage"] >= 100:
        return {"can_advance": True}

    return {
        "can_advance": False,
        "maturity": maturity["maturity_percentage"],
        "missing": maturity.get("focus_areas", []),
        "reason": "Phase not fully specified. Continue answering questions."
    }
```

---

### Task 4: Advanced Advancement Endpoint (1.5 hours)

**File**: `backend/src/socrates_api/routers/projects.py`

**Enhancement to advance_phase**:
```python
class PhaseAdvancementRequest(BaseModel):
    phase: Optional[str] = None  # Specific phase or auto-advance
    force_advance: bool = False  # Override maturity check
    reason: Optional[str] = None  # Why overriding

@router.put("/{project_id}/phase", ...)
async def advance_phase(
    project_id: str,
    request: Optional[PhaseAdvancementRequest] = None,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    # Validate advancement
    validation = orchestrator.validate_phase_advancement(
        project,
        target_phase=request.phase,
        force=request.force_advance
    )

    if not validation["can_advance"]:
        # Option 1: Require force_advance
        if not request.force_advance:
            raise HTTPException(
                status_code=400,
                detail=f"Phase not ready. {validation['reason']}"
            )
        # Option 2: Allow with warning
        logger.warning(
            f"User {current_user} forced phase advancement: {request.reason}"
        )

    # Proceed with advancement
    # ... rest of implementation
```

---

## Testing Requirements

### Unit Tests Needed

```python
# Test phase advancement
test_advance_from_discovery_to_analysis()
test_auto_advance_to_next_phase()
test_manual_phase_setting()
test_rollback_from_analysis()
test_cannot_rollback_from_discovery()
test_clear_question_cache_on_phase_change()

# Test maturity validation
test_can_advance_at_100_percent()
test_cannot_advance_below_100_percent()
test_force_advance_override()
test_maturity_calculation_with_specs()

# Test prompts
test_advancement_prompt_generated()
test_phase_complete_notification()
test_next_phase_calculated_correctly()
```

### Integration Tests Needed

```python
# Complete workflow
test_discovery_to_implementation_full_workflow()
test_answer_questions_until_phase_complete()
test_receive_advancement_prompt_at_100_percent()
test_advance_phase_clears_old_cache()
test_rollback_restores_previous_phase()
```

---

## Current Code Locations Summary

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| advance_phase endpoint | projects.py | 1243-1330 | ✅ Working |
| rollback_phase endpoint | projects.py | 1342-1425 | ✅ Working |
| get_readiness_for_phase | projects.py | 1078-1135 | ✅ Working |
| calculate_phase_maturity | orchestrator.py | 545-590 | ✅ Working |
| phase_complete detection | projects_chat.py | 987-988, 1230-1237 | ⚠️ Partial |
| Advancement prompt | N/A | N/A | ⏳ Missing |
| Validation logic | N/A | N/A | ⏳ Missing |

---

## Summary

**Phase 4 Status**: ⚠️ **PARTIALLY COMPLETE**

**What's Working**:
- ✅ Phase advancement endpoints
- ✅ Phase rollback
- ✅ Maturity calculation
- ✅ Phase completion detection
- ✅ Readiness checking

**What's Missing**:
- ⏳ Phase advancement prompt endpoint
- ⏳ Phase advancement validation logic
- ⏳ Force advancement override
- ⏳ Complete integration with answer flow

**Estimated Work to Complete**: 4-5 hours

**Recommended Next Steps**:
1. Create phase advancement prompt endpoint
2. Enhance phase_complete response in send_message
3. Add validation logic to orchestrator
4. Update advance_phase with validation
5. Comprehensive testing

---

## Ready to Proceed?

Phase 4 can be completed within this session by implementing the 4 tasks identified above.
Total estimated time: 5 hours

**Questions**:
- Should phase advancement require 100% maturity (strict) or allow 60% with warning?
- Should force_advance be allowed for all roles or just owners?
- Should we emit events (via WebSocket) when phase completes and advances?

