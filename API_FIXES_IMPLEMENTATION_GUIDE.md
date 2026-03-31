# API Endpoint Fixes - Implementation Guide

**Status**: Ready for Development
**Priority**: Critical
**Estimated Effort**: 4 hours
**Created**: 2026-03-30

---

## Overview

Three critical endpoints have issues that must be fixed before the API can function properly:

1. **POST /projects/{id}/chat/message** (response processing stub)
2. **GET /conflicts/detect** (conflict detection stub)
3. **GET /nlu/interpret** + **POST /free_session/ask** (undefined claude_client)

This guide provides step-by-step implementation for each.

---

## Fix #1: Response Processing Endpoint

**File**: `backend/src/socrates_api/routers/projects_chat.py`
**Lines**: 1255-1272
**Current Status**: ❌ Stub - returns success without processing
**Impact**: Core dialogue feature broken
**Fix Time**: 2 hours

### Current Broken Code

```python
# Lines 1255-1272 in projects_chat.py
if action == "process_response":
    # Lines 1255-1272: Stub implementation
    logger.debug(f"Processing response for project {project_id}")

    # Return empty successful response
    return {
        "status": "success",
        "result": None,
        "feedback": "Response processing not yet implemented",
    }
```

### Expected Behavior

The endpoint should:
1. Receive user's answer to a socratic question
2. Validate the answer against current question
3. Extract project specifications from the answer
4. Generate feedback for the user
5. Update project context with new information
6. Check if phase is ready for advancement
7. Return structured response with feedback and metadata

### Implementation Step-by-Step

#### Step 1: Understand Current Question Context

First, retrieve the current question and context:

```python
if action == "process_response":
    try:
        # Step 1: Get current question context
        if not payload or "response" not in payload:
            return {
                "status": "error",
                "detail": "Response text is required"
            }

        user_response = payload.get("response", "").strip()

        # Get the last question asked (from session context)
        # This should be tracked in project.current_question or similar
        current_question = getattr(project, "current_question", None)
        if not current_question:
            logger.warning(f"No current question context for project {project_id}")
            # Graceful degradation - process anyway

        logger.info(f"Processing response for project {project_id}: '{user_response[:100]}...'")
```

#### Step 2: Extract Specifications from Response

Use the ContextAnalyzer agent to extract specs:

```python
        # Step 2: Extract specs from response
        extracted_specs = {}
        try:
            agent = orchestrator.agents.get("context_analyzer")
            if agent:
                result = agent.process({
                    "action": "analyze",
                    "content": user_response
                })
                if result and result.get("status") == "success":
                    extracted_specs = result.get("data", {})
                    logger.debug(f"Extracted specs: {extracted_specs}")
        except Exception as e:
            logger.warning(f"Spec extraction failed: {e}")
            # Continue with empty specs - don't fail the whole response
```

#### Step 3: Generate Feedback

Create feedback based on the response quality:

```python
        # Step 3: Generate feedback
        feedback = ""
        confidence_score = 0.5  # Default medium confidence

        try:
            # Evaluate response quality using orchestrator
            evaluation = orchestrator.evaluate_response(
                question=current_question,
                response=user_response,
                extracted_specs=extracted_specs
            )

            feedback = evaluation.get("feedback", "Thank you for your response.")
            confidence_score = evaluation.get("confidence", 0.5)

            logger.debug(f"Feedback: {feedback} (confidence: {confidence_score})")
        except Exception as e:
            logger.warning(f"Feedback generation failed: {e}")
            feedback = f"Thank you for sharing: '{user_response[:50]}...'"
```

#### Step 4: Update Project Context

Save the response and extracted specs to the database:

```python
        # Step 4: Update project context with new specs
        if extracted_specs:
            # Update project with extracted information
            if "goals" in extracted_specs and extracted_specs["goals"]:
                project.goals = list(set(
                    (project.goals or []) + extracted_specs["goals"]
                ))
            if "requirements" in extracted_specs and extracted_specs["requirements"]:
                project.requirements = list(set(
                    (project.requirements or []) + extracted_specs["requirements"]
                ))
            if "tech_stack" in extracted_specs and extracted_specs["tech_stack"]:
                project.tech_stack = list(set(
                    (project.tech_stack or []) + extracted_specs["tech_stack"]
                ))
            if "constraints" in extracted_specs and extracted_specs["constraints"]:
                project.constraints = list(set(
                    (project.constraints or []) + extracted_specs["constraints"]
                ))

        # Save response to conversation history
        response_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user,
            "text": user_response,
            "extracted_specs": extracted_specs,
            "confidence": confidence_score,
            "feedback": feedback
        }

        if not hasattr(project, "conversation_history"):
            project.conversation_history = []
        project.conversation_history.append(response_entry)

        # Log spec extraction to database (Task 3.4)
        try:
            db.log_spec_extraction(
                project_id=project_id,
                spec_id=None,  # Will be generated
                extraction_method="user_response",
                confidence=confidence_score
            )
        except Exception as e:
            logger.warning(f"Failed to log extraction: {e}")

        # Save updated project
        project.updated_at = datetime.now(timezone.utc)
        db.save_project(project)

        logger.info(f"Updated project {project_id} with extracted specs")
```

#### Step 5: Check Phase Readiness

Verify if the phase should advance:

```python
        # Step 5: Check if phase is ready to advance
        phase_readiness = None
        try:
            phase_readiness = orchestrator._check_phase_readiness(project)

            if phase_readiness and phase_readiness.get("is_complete"):
                logger.info(f"Phase {project.phase} is COMPLETE for {project_id}")
        except Exception as e:
            logger.warning(f"Phase readiness check failed: {e}")
```

#### Step 6: Build Response

Construct and return the response:

```python
        # Step 6: Build response
        response_data = {
            "status": "success",
            "message": feedback,
            "confidence": confidence_score,
            "extracted_specs": {
                "goals": extracted_specs.get("goals", []),
                "requirements": extracted_specs.get("requirements", []),
                "tech_stack": extracted_specs.get("tech_stack", []),
                "constraints": extracted_specs.get("constraints", [])
            }
        }

        # Include phase readiness if available
        if phase_readiness and (phase_readiness.get("is_complete") or phase_readiness.get("is_ready")):
            response_data["phase_readiness"] = {
                "phase": phase_readiness.get("phase"),
                "status": phase_readiness.get("status"),
                "maturity_percentage": phase_readiness.get("maturity_percentage"),
                "next_phase": phase_readiness.get("next_phase")
            }

        return response_data
```

#### Step 7: Error Handling

Wrap everything in comprehensive error handling:

```python
    except Exception as e:
        logger.error(f"Error processing response for project {project_id}: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to process response: {str(e)}",
            "detail": "Your response was received but could not be fully processed. Please try again."
        }
```

### Complete Implementation

```python
def _handle_socratic_counselor(
    action: str,
    project_id: str,
    payload: Optional[Dict] = None,
    current_user: str = None,
    db: LocalDatabase = None,
    debug_enabled: bool = False,
):
    """Generate questions or process responses via orchestrator agent"""

    # ... existing code for other actions ...

    elif action == "process_response":
        """Process user response to socratic question"""
        try:
            # Validate input
            if not payload or "response" not in payload:
                return {
                    "status": "error",
                    "detail": "Response text is required"
                }

            user_response = payload.get("response", "").strip()

            if len(user_response) == 0:
                return {
                    "status": "error",
                    "detail": "Response cannot be empty"
                }

            # Get current question context
            current_question = getattr(project, "current_question", None)

            # Extract specs from response
            extracted_specs = {}
            confidence_score = 0.5

            try:
                agent = orchestrator.agents.get("context_analyzer")
                if agent:
                    result = agent.process({
                        "action": "analyze",
                        "content": user_response
                    })
                    if result and result.get("status") == "success":
                        extracted_specs = result.get("data", {})
                        confidence_score = 0.7  # Higher confidence for agent-extracted specs
            except Exception as e:
                logger.warning(f"Spec extraction failed: {e}")

            # Generate feedback
            feedback = "Thank you for your detailed response."
            try:
                evaluation = orchestrator.evaluate_response(
                    question=current_question,
                    response=user_response,
                    extracted_specs=extracted_specs
                )
                feedback = evaluation.get("feedback", feedback)
                confidence_score = max(confidence_score, evaluation.get("confidence", 0.5))
            except Exception as e:
                logger.warning(f"Feedback generation failed: {e}")

            # Update project with extracted specs
            if extracted_specs:
                for spec_type in ["goals", "requirements", "tech_stack", "constraints"]:
                    if spec_type in extracted_specs and extracted_specs[spec_type]:
                        current = getattr(project, spec_type, []) or []
                        new_items = extracted_specs[spec_type]
                        updated = list(set(current + (new_items if isinstance(new_items, list) else [new_items])))
                        setattr(project, spec_type, updated)

            # Save response to history
            response_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": current_user,
                "text": user_response,
                "extracted_specs": extracted_specs,
                "confidence": confidence_score,
                "feedback": feedback
            }

            if not hasattr(project, "conversation_history"):
                project.conversation_history = []
            project.conversation_history.append(response_entry)

            # Log extraction
            try:
                db.log_spec_extraction(
                    project_id=project_id,
                    spec_id=None,
                    extraction_method="user_response",
                    confidence=confidence_score
                )
            except Exception as e:
                logger.warning(f"Failed to log extraction: {e}")

            # Update project
            project.updated_at = datetime.now(timezone.utc)
            db.save_project(project)

            # Check phase readiness
            phase_readiness = None
            try:
                phase_readiness = orchestrator._check_phase_readiness(project)
            except Exception as e:
                logger.warning(f"Phase readiness check failed: {e}")

            # Build response
            response_data = {
                "status": "success",
                "message": feedback,
                "confidence": confidence_score,
                "extracted_specs": {
                    "goals": extracted_specs.get("goals", []),
                    "requirements": extracted_specs.get("requirements", []),
                    "tech_stack": extracted_specs.get("tech_stack", []),
                    "constraints": extracted_specs.get("constraints", [])
                }
            }

            # Include phase readiness if ready/complete
            if phase_readiness and (phase_readiness.get("is_complete") or phase_readiness.get("is_ready")):
                response_data["phase_readiness"] = {
                    "phase": phase_readiness.get("phase"),
                    "status": phase_readiness.get("status"),
                    "maturity_percentage": phase_readiness.get("maturity_percentage"),
                    "next_phase": phase_readiness.get("next_phase")
                }

            logger.info(f"Successfully processed response for {project_id}")
            return response_data

        except Exception as e:
            logger.error(f"Error processing response: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to process response",
                "detail": "Please try again later"
            }
```

---

## Fix #2: Conflict Detection Endpoint

**File**: `backend/src/socrates_api/routers/conflicts.py`
**Lines**: 107-161
**Current Status**: ❌ Stub - returns empty conflicts list
**Impact**: Conflict resolution feature broken
**Fix Time**: 1.5 hours

### Current Broken Code

```python
@router.post("/detect", response_model=ConflictDetectionResponse)
def detect_conflicts(request: ConflictDetectionRequest) -> ConflictDetectionResponse:
    """Detect conflicts in project updates"""
    try:
        detector = get_conflict_detector()

        if detector.detector is None:
            return ConflictDetectionResponse(
                status="unavailable",
                conflicts=[],
                has_conflicts=False,
            )

        # Lines 139-144: Simulate conflict detection
        # In a real implementation, this would:
        # 1. Load project data from database
        # 2. Analyze new values against existing project context
        # 3. Use socratic-conflict library for detection
        conflicts: List[ConflictInfo] = []  # ALWAYS EMPTY!

        return ConflictDetectionResponse(
            status="success",
            conflicts=conflicts,
            has_conflicts=len(conflicts) > 0,
        )
```

### Implementation Step-by-Step

#### Step 1: Load Project Data

```python
@router.post("/detect", response_model=ConflictDetectionResponse)
def detect_conflicts(request: ConflictDetectionRequest) -> ConflictDetectionResponse:
    """Detect conflicts in project updates"""
    try:
        from socrates_api.database import get_database
        db = get_database()

        # Step 1: Load project
        project = db.load_project(request.project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project '{request.project_id}' not found"
            )

        logger.info(f"Detecting conflicts for project {request.project_id}")
```

#### Step 2: Get Conflict Detector

```python
        # Step 2: Get conflict detector
        detector = get_conflict_detector()

        if detector.detector is None:
            logger.warning("ConflictDetector unavailable - socratic-conflict not installed")
            return ConflictDetectionResponse(
                status="unavailable",
                conflicts=[],
                has_conflicts=False,
                total_conflicts=0,
                message="Conflict detection unavailable (library not installed)"
            )
```

#### Step 3: Analyze for Conflicts

```python
        # Step 3: Detect conflicts between new_values and existing project
        detected_conflicts: List[ConflictInfo] = []

        # Define fields to check
        fields_to_check = request.fields_to_check or [
            "goals", "requirements", "tech_stack", "constraints",
            "name", "description", "phase"
        ]

        existing_data = {
            "goals": project.goals or [],
            "requirements": project.requirements or [],
            "tech_stack": project.tech_stack or [],
            "constraints": project.constraints or [],
            "name": project.name,
            "description": project.description,
            "phase": project.phase,
        }

        # Check each field for conflicts
        for field_name in fields_to_check:
            if field_name not in request.new_values:
                continue

            existing_value = existing_data.get(field_name)
            new_value = request.new_values[field_name]

            # Skip if same
            if existing_value == new_value:
                continue

            # Detect conflict type
            conflict_type = _determine_conflict_type(field_name, existing_value, new_value)
            severity = _calculate_conflict_severity(field_name, conflict_type)

            conflict = ConflictInfo(
                conflict_type=conflict_type,
                field_name=field_name,
                existing_value=existing_value,
                new_value=new_value,
                severity=severity,
                description=_generate_conflict_description(field_name, existing_value, new_value),
                suggested_resolution=_suggest_resolution(conflict_type, existing_value, new_value) if request.include_resolution else None
            )

            detected_conflicts.append(conflict)
            logger.debug(f"Detected {severity} conflict in {field_name}: {existing_value} vs {new_value}")
```

#### Step 4: Save to Database

```python
        # Step 4: Save detected conflicts to database
        if detected_conflicts:
            for conflict in detected_conflicts:
                try:
                    db.save_conflict(
                        project_id=request.project_id,
                        conflict_type=conflict.conflict_type,
                        severity=conflict.severity,
                        context={
                            "field": conflict.field_name,
                            "existing": conflict.existing_value,
                            "new": conflict.new_value,
                            "description": conflict.description
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to save conflict: {e}")
```

#### Step 5: Return Response

```python
        # Step 5: Return response
        return ConflictDetectionResponse(
            status="success",
            conflicts=detected_conflicts,
            has_conflicts=len(detected_conflicts) > 0,
            total_conflicts=len(detected_conflicts),
            message=f"Found {len(detected_conflicts)} conflicts" if detected_conflicts else "No conflicts detected"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting conflicts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Conflict detection failed. Please try again."
        )


# Helper functions

def _determine_conflict_type(field_name: str, existing: Any, new: Any) -> str:
    """Determine conflict type based on field and values"""
    if field_name == "goals":
        return "goal_conflict"
    elif field_name == "tech_stack":
        return "tech_conflict"
    elif field_name == "requirements":
        return "requirement_conflict"
    elif field_name == "constraints":
        return "constraint_conflict"
    else:
        return "data_conflict"


def _calculate_conflict_severity(field_name: str, conflict_type: str) -> str:
    """Calculate severity of conflict"""
    critical_fields = ["goals", "phase", "tech_stack"]
    if field_name in critical_fields:
        return "high"
    return "medium"


def _generate_conflict_description(field_name: str, existing: Any, new: Any) -> str:
    """Generate human-readable description of conflict"""
    return f"Existing {field_name} ({existing}) conflicts with new value ({new})"


def _suggest_resolution(conflict_type: str, existing: Any, new: Any) -> str:
    """Suggest resolution strategy"""
    return f"Review both values and choose which better fits the project goals"
```

### Complete Implementation

```python
@router.post("/detect", response_model=ConflictDetectionResponse)
def detect_conflicts(request: ConflictDetectionRequest) -> ConflictDetectionResponse:
    """
    Detect conflicts in project updates.

    Analyzes proposed changes against existing project values to identify:
    - Data conflicts (contradictory values)
    - Goal conflicts (incompatible objectives)
    - Technology conflicts (incompatible tech choices)
    """
    try:
        from socrates_api.database import get_database
        db = get_database()

        # Load project
        project = db.load_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        logger.info(f"Detecting conflicts for project {request.project_id}")

        # Get detector
        detector = get_conflict_detector()
        if detector.detector is None:
            return ConflictDetectionResponse(
                status="unavailable",
                conflicts=[],
                has_conflicts=False,
                total_conflicts=0,
                message="Conflict detection not available"
            )

        # Detect conflicts
        detected_conflicts: List[ConflictInfo] = []

        fields_to_check = request.fields_to_check or [
            "goals", "requirements", "tech_stack", "constraints"
        ]

        existing_data = {
            "goals": project.goals or [],
            "requirements": project.requirements or [],
            "tech_stack": project.tech_stack or [],
            "constraints": project.constraints or [],
        }

        # Check for conflicts
        for field in fields_to_check:
            if field not in request.new_values:
                continue

            existing = existing_data.get(field)
            new = request.new_values[field]

            if existing != new:
                conflict_type = "data_conflict"
                if field == "goals":
                    conflict_type = "goal_conflict"
                elif field == "tech_stack":
                    conflict_type = "tech_conflict"

                severity = "high" if field in ["goals", "tech_stack"] else "medium"

                conflict = ConflictInfo(
                    conflict_type=conflict_type,
                    field_name=field,
                    existing_value=existing,
                    new_value=new,
                    severity=severity,
                    description=f"{field}: {existing} → {new}",
                    suggested_resolution=f"Review both values for project fit" if request.include_resolution else None
                )
                detected_conflicts.append(conflict)

                # Save to database
                try:
                    db.save_conflict(
                        project_id=request.project_id,
                        conflict_type=conflict_type,
                        severity=severity,
                        context={"field": field, "existing": existing, "new": new}
                    )
                except Exception as e:
                    logger.warning(f"Failed to save conflict: {e}")

        logger.info(f"Detected {len(detected_conflicts)} conflicts for {request.project_id}")

        return ConflictDetectionResponse(
            status="success",
            conflicts=detected_conflicts,
            has_conflicts=len(detected_conflicts) > 0,
            total_conflicts=len(detected_conflicts),
            message=f"Found {len(detected_conflicts)} conflict(s)" if detected_conflicts else "No conflicts detected"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting conflicts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Conflict detection failed")
```

---

## Fix #3: Undefined claude_client

**Files**:
- `nlu.py` (line ~206)
- `free_session.py` (line ~205)

**Current Status**: 🔶 Partial - References undefined `claude_client`
**Impact**: NLU interpretation and free session chat endpoints crash
**Fix Time**: 30 minutes

### Problem

Code calls `claude_client.complete(prompt)` but `claude_client` is never imported or initialized:

```python
# BROKEN CODE in both files:
response = claude_client.complete(prompt)  # ❌ NameError: claude_client not defined
```

### Solution: Use Orchestrator Agents

Replace all `claude_client` calls with proper orchestrator agent calls.

#### In `nlu.py`:

**Before** (broken):
```python
def interpret_input(text: str, context: Optional[dict] = None) -> NLUInterpretResponse:
    try:
        # Line ~206: Calls non-existent claude_client
        response = claude_client.complete(prompt)  # ❌ BROKEN
```

**After** (fixed):
```python
def interpret_input(text: str, context: Optional[dict] = None) -> NLUInterpretResponse:
    try:
        from socrates_api.main import get_orchestrator
        orchestrator = get_orchestrator()

        # Use NLU agent from orchestrator
        agent = orchestrator.agents.get("nlu_interpreter")
        if agent:
            result = agent.process({
                "action": "interpret",
                "input": text,
                "context": context or {}
            })

            if result and result.get("status") == "success":
                data = result.get("data", {})
                return NLUInterpretResponse(
                    status="success",
                    command=data.get("command"),
                    message=data.get("message", "Understood"),
                    entities=data.get("entities"),
                    intent=data.get("intent")
                )

        # Fallback if agent not available
        return NLUInterpretResponse(
            status="no_match",
            message="Could not interpret input",
            suggestions=[]
        )

    except Exception as e:
        logger.error(f"Error interpreting input: {e}")
        return NLUInterpretResponse(
            status="error",
            message=f"Interpretation failed: {str(e)}"
        )
```

#### In `free_session.py`:

**Before** (broken):
```python
async def ask_question(request: FreeSessionQuestion) -> FreeSessionAnswer:
    try:
        # Line ~205: Calls non-existent claude_client
        response = claude_client.complete(prompt)  # ❌ BROKEN
```

**After** (fixed):
```python
async def ask_question(request: FreeSessionQuestion) -> FreeSessionAnswer:
    try:
        from socrates_api.main import get_orchestrator
        orchestrator = get_orchestrator()

        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())

        # Use orchestrator to generate response
        response_text = orchestrator.generate_response(
            user_input=request.question,
            context=request.context or {},
            session_id=session_id
        )

        # Extract specs from question
        extracted_specs = None
        try:
            agent = orchestrator.agents.get("context_analyzer")
            if agent:
                result = agent.process({
                    "action": "analyze",
                    "content": request.question
                })
                if result and result.get("status") == "success":
                    extracted_specs = result.get("data", {})
        except Exception as e:
            logger.debug(f"Spec extraction failed: {e}")

        return FreeSessionAnswer(
            answer=response_text,
            has_context=request.context is not None,
            session_id=session_id,
            extracted_specs=extracted_specs
        )

    except Exception as e:
        logger.error(f"Error processing free session question: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process question"
        )
```

### Search and Replace Quick Command

Find all remaining `claude_client` references:

```bash
grep -rn "claude_client" backend/src/socrates_api/routers/
```

Expected output should show only documentation references after fixes.

---

## Testing the Fixes

### Test 1: Response Processing

```bash
# Create a test project first
PROJECT_ID="test-project-123"

# Generate a question
curl -X GET "http://localhost:8000/projects/$PROJECT_ID/chat/question" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Process a response (SHOULD WORK AFTER FIX)
curl -X POST "http://localhost:8000/projects/$PROJECT_ID/chat/message" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "mode": "socratic",
    "action": "process_response",
    "response": "I want to build a web application using Python and React"
  }'

# Expected response (AFTER FIX):
{
  "status": "success",
  "message": "Thank you for sharing...",
  "confidence": 0.7,
  "extracted_specs": {
    "goals": [],
    "requirements": [],
    "tech_stack": ["Python", "React"],
    "constraints": []
  }
}
```

### Test 2: Conflict Detection

```bash
# Detect conflicts in new values
curl -X POST "http://localhost:8000/conflicts/detect" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "project_id": "'$PROJECT_ID'",
    "new_values": {
      "goals": ["Build a mobile app"],
      "tech_stack": ["Swift"]
    },
    "include_resolution": true
  }'

# Expected response (AFTER FIX):
{
  "status": "success",
  "conflicts": [
    {
      "conflict_type": "goal_conflict",
      "field_name": "goals",
      "existing_value": [...],
      "new_value": ["Build a mobile app"],
      "severity": "high",
      "description": "...",
      "suggested_resolution": "..."
    }
  ],
  "has_conflicts": true,
  "total_conflicts": 1
}
```

### Test 3: NLU Interpretation

```bash
# Test NLU endpoint (SHOULD WORK AFTER FIX)
curl -X POST "http://localhost:8000/nlu/interpret" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "I want to create a mobile app",
    "context": {}
  }'

# Expected response (AFTER FIX):
{
  "status": "success",
  "command": "create_project",
  "message": "I understood you want to create a mobile app",
  "entities": {...},
  "intent": "project_creation"
}
```

### Test 4: Free Session

```bash
# Test free session endpoint (SHOULD WORK AFTER FIX)
curl -X POST "http://localhost:8000/free_session/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I build an e-commerce website?"
  }'

# Expected response (AFTER FIX):
{
  "answer": "To build an e-commerce website...",
  "has_context": false,
  "session_id": "uuid-here",
  "extracted_specs": {
    "goals": ["Build an e-commerce website"],
    "requirements": [],
    "tech_stack": [],
    "constraints": []
  }
}
```

---

## Verification Checklist

After implementing fixes, verify:

- [ ] Response processing extracts specs from answers
- [ ] Response processing generates feedback
- [ ] Response processing updates project context
- [ ] Response processing checks phase readiness
- [ ] Conflict detection finds actual conflicts
- [ ] Conflict detection saves to database
- [ ] Conflict detection suggests resolutions
- [ ] NLU endpoint interprets input correctly
- [ ] Free session endpoint generates responses
- [ ] Free session extracts specs from questions
- [ ] All error handling works properly
- [ ] Logging captures execution flow
- [ ] No NameError exceptions occur
- [ ] Database persistence works
- [ ] Agent integration functional

---

## Rollback Plan

If issues arise:

1. **Response Processing Issues**:
   - Disable by returning simple success response
   - Re-enable orchestrator integration step-by-step

2. **Conflict Detection Issues**:
   - Fall back to returning empty conflicts list
   - Debug agent integration separately

3. **claude_client Issues**:
   - Revert to calling orchestrator agents
   - If orchestrator unavailable, return error response

---

**Status**: Ready for Implementation
**Estimated Total Time**: 4 hours
**Next Step**: Begin with Fix #1 (Response Processing)
