# Specs Extraction and Confirmation Workflow Guide

Complete guide to the Socratic dialogue specs extraction and confirmation workflow, including debug mode behavior, API reference, and integration patterns.

## Table of Contents

1. [Overview](#overview)
2. [Workflow Phases](#workflow-phases)
3. [Debug vs Production Mode](#debug-vs-production-mode)
4. [API Reference](#api-reference)
5. [Integration Examples](#integration-examples)
6. [Frontend Implementation](#frontend-implementation)
7. [Data Models](#data-models)
8. [Error Handling](#error-handling)

---

## Overview

### What are Specs?

Specifications (specs) are extracted insights from user responses to Socratic questions. They capture:

- **Goals**: What problems does the project solve?
- **Requirements**: What features are needed?
- **Tech Stack**: What technologies will be used?
- **Constraints**: What limitations exist?

### Workflow Philosophy

The Socratic dialogue system extracts specs through a **transparent confirmation model**:

1. **Production Mode** (Debug OFF): Auto-save specs silently, user sees only success
2. **Debug Mode** (Debug ON): Show extracted specs, ask for user confirmation before saving

This approach:
- ✅ Keeps production UX clean and fast
- ✅ Allows developers to review spec extraction in debug mode
- ✅ Prevents accidental auto-save of incorrect specs in development
- ✅ Provides transparency about what the system extracted

### Specs Lifecycle

```
User Response
    ↓
Claude Analyzes Response
    ↓
System Extracts: goals, requirements, tech_stack, constraints
    ↓
Conflict Detection (concurrent)
    ↓
Check Debug Mode
    ├─ Debug OFF → Auto-save → Return success
    └─ Debug ON → Return with confirmation flag → Wait for user approval
    ↓
Save Confirmed Specs
    ↓
Update ProjectContext
    ↓
Emit Spec Events
```

---

## Workflow Phases

### Phase 1: Response Processing and Extraction

**Trigger**: User submits response to Socratic question

**Process**:
```python
async def process_response_async(self, request):
    """Phase 1: Extract insights from user response"""

    project_id = request["project_id"]
    user_response = request["response"]
    phase = request.get("phase", "discovery")

    # Load current project context
    project = self.database.load_project(project_id)

    # ✅ Extract insights using Claude
    # Claude analyzes: goals, requirements, tech_stack, constraints
    insights = await self.claude_client.extract_insights(
        user_response,
        project,
        phase=phase
    )
    # Returns: {"goals": [...], "requirements": [...], ...}

    # ✅ Detect conflicts with existing specs
    conflicts = await self.orchestrator.agent_bus.send_request(
        "conflict_detector",
        {
            "action": "detect_conflicts",
            "new_insights": insights,
            "existing_specs": project.to_dict(),
            "project_id": project_id
        }
    )

    # ✅ Check debug mode setting
    if not is_debug_mode():
        # Production: Auto-save silently
        return await _handle_production_mode(project, insights, conflicts)
    else:
        # Debug: Return specs for confirmation
        return await _handle_debug_mode(insights, conflicts)
```

**Output**:
- Production Mode: Success message
- Debug Mode: Extracted specs with confirmation flag

### Phase 2: Confirmation (Debug Mode Only)

**Trigger**: User reviews and confirms specs in UI

**User Actions**:
1. Review extracted specs in confirmation dialog
2. Review detected conflicts
3. Optionally edit specs
4. Click "Confirm" or "Cancel"

**Frontend Flow**:
```javascript
// 1. Receive response with confirmation flag
const response = await sendChatMessage(projectId, userMessage);

// 2. Check if confirmation needed
if (response.requires_confirmation) {
    // 3. Show confirmation dialog
    const specs = response.extracted_specs;
    const conflicts = response.conflicts;

    showSpecsConfirmationDialog({
        goals: specs.goals,
        requirements: specs.requirements,
        tech_stack: specs.tech_stack,
        constraints: specs.constraints,
        conflicts: conflicts
    });

    // 4. Wait for user confirmation
    const confirmed = await waitForUserConfirmation();

    if (confirmed) {
        // 5. Send confirmation to API
        await saveExtractedSpecs(projectId, specs);
    }
}
```

### Phase 3: Persistence

**Trigger**: User confirms specs (debug) or auto-save completes (production)

**Process**:
```python
async def save_extracted_specs(self, project_id: str, specs: dict) -> dict:
    """Phase 3: Persist confirmed specs to database"""

    project = self.database.load_project(project_id)

    # ✅ Update project with confirmed specs
    project.goals.extend(specs.get("goals", []))
    project.requirements.extend(specs.get("requirements", []))
    project.tech_stack.extend(specs.get("tech_stack", []))
    project.constraints.extend(specs.get("constraints", []))

    # ✅ Update timestamps
    project.updated_at = datetime.now()
    project.specs_updated_at = datetime.now()

    # ✅ Save to database
    self.database.save_project(project)

    # ✅ Emit event
    await self.event_emitter.emit_async(
        EventType.SPECS_CONFIRMED,
        {
            "project_id": project_id,
            "specs_count": sum([
                len(specs.get("goals", [])),
                len(specs.get("requirements", [])),
                len(specs.get("tech_stack", [])),
                len(specs.get("constraints", []))
            ])
        }
    )

    return {
        "status": "success",
        "message": "Specs saved successfully",
        "project_id": project_id,
        "specs_saved": {
            "goals": len(specs.get("goals", [])),
            "requirements": len(specs.get("requirements", [])),
            "tech_stack": len(specs.get("tech_stack", [])),
            "constraints": len(specs.get("constraints", []))
        }
    }
```

---

## Debug vs Production Mode

### Configuration

**Check Debug Mode**:
```python
from socratic_system.utils.logger import is_debug_mode

if is_debug_mode():
    # Debug mode: Explicit confirmation required
    logger.info("Debug mode enabled - awaiting spec confirmation")
else:
    # Production mode: Auto-save
    logger.info("Production mode - auto-saving specs")
```

**Set Debug Mode**:
```bash
# Environment variable
export DEBUG_MODE=true

# Or in config file
# config.py or .env
DEBUG_MODE=true
```

### Production Mode Behavior

**When DEBUG_MODE=false** (Production):

```json
{
    "status": "success",
    "message": "Response processed successfully",
    "insights_count": 4,
    "insights": {
        "goals": ["Streamline operations", "Reduce costs"],
        "requirements": ["Real-time reporting", "Mobile app"],
        "tech_stack": ["Python", "React"],
        "constraints": ["Budget: $100k", "Timeline: 6 months"]
    }
}
```

**Behavior**:
- ✅ Specs auto-saved to database
- ✅ No confirmation dialog shown
- ✅ Response includes insights (for reference)
- ✅ Fast response time
- ⚠️ No user review step

### Debug Mode Behavior

**When DEBUG_MODE=true** (Debug):

```json
{
    "status": "success",
    "requires_confirmation": true,
    "confirmation_message": "Extracted 4 spec categories - please confirm to save",
    "extracted_specs": {
        "goals": ["Streamline operations", "Reduce costs"],
        "requirements": ["Real-time reporting", "Mobile app"],
        "tech_stack": ["Python", "React"],
        "constraints": ["Budget: $100k", "Timeline: 6 months"]
    },
    "conflicts": [
        {
            "type": "tech_stack",
            "severity": "warning",
            "message": "React requires Node.js, but not mentioned in existing stack"
        }
    ]
}
```

**Behavior**:
- ⏳ Specs held temporarily (not saved)
- ✅ Confirmation dialog shown to user
- ✅ Conflicts highlighted
- ✅ User can edit before confirming
- ✅ Transparent extraction process

**Comparison Table**:

| Aspect | Production (Debug OFF) | Debug (Debug ON) |
|--------|------------------------|-----------------|
| Auto-save | ✅ Yes | ❌ No |
| Show specs in response | ✅ Yes | ✅ Yes |
| Requires confirmation | ❌ No | ✅ Yes |
| Confirmation endpoint | N/A | POST /save-extracted-specs |
| User review step | ❌ No | ✅ Yes |
| Response time | Fast | Same |
| Use case | Production | Development |

---

## API Reference

### 1. POST /projects/{project_id}/chat/message

Send message and process response for specs extraction.

**Request**:
```json
{
    "content": "We're building a web app for small businesses using Python backend",
    "user_id": "user_123"
}
```

**Response (Production Mode)**:
```json
{
    "status": "success",
    "message": "Response processed successfully",
    "data": {
        "message": {
            "id": "msg_xyz",
            "role": "assistant",
            "content": "Great! A Python-based web app for small businesses...",
            "timestamp": "2026-05-02T12:00:00Z"
        },
        "mode": "socratic",
        "requires_confirmation": false,
        "extracted_specs": {
            "goals": ["Build web app for small businesses"],
            "requirements": [],
            "tech_stack": ["Python"],
            "constraints": []
        }
    }
}
```

**Response (Debug Mode)**:
```json
{
    "status": "success",
    "data": {
        "message": {
            "id": "msg_xyz",
            "role": "assistant",
            "content": "Great! A Python-based web app for small businesses...",
            "timestamp": "2026-05-02T12:00:00Z"
        },
        "mode": "socratic",
        "requires_confirmation": true,
        "confirmation_message": "Extracted 2 spec categories - please confirm to save",
        "extracted_specs": {
            "goals": ["Build web app for small businesses"],
            "requirements": [],
            "tech_stack": ["Python"],
            "constraints": []
        },
        "conflicts": []
    }
}
```

**Status Codes**:
- `200` - Success
- `400` - Invalid input
- `401` - Unauthorized
- `404` - Project not found
- `500` - Server error

---

### 2. POST /projects/{project_id}/save-extracted-specs

Save previously extracted specs (debug mode only).

**Request**:
```json
{
    "goals": ["Build web app for small businesses"],
    "requirements": ["User authentication", "Data export"],
    "tech_stack": ["Python", "PostgreSQL", "React"],
    "constraints": ["Budget: $50k"]
}
```

**Response**:
```json
{
    "status": "success",
    "message": "Specs saved successfully",
    "data": {
        "project_id": "proj_abc",
        "specs_saved": {
            "goals": 1,
            "requirements": 2,
            "tech_stack": 3,
            "constraints": 1
        }
    }
}
```

**Status Codes**:
- `200` - Specs saved
- `400` - Invalid specs format
- `401` - Unauthorized
- `404` - Project not found
- `422` - Empty specs (nothing to save)

---

### 3. GET /projects/{project_id}/specs

Get current specs for a project.

**Response**:
```json
{
    "status": "success",
    "data": {
        "project_id": "proj_abc",
        "goals": ["...", "..."],
        "requirements": ["...", "...", "..."],
        "tech_stack": ["Python", "PostgreSQL"],
        "constraints": ["..."],
        "last_updated": "2026-05-02T12:00:00Z",
        "extracted_count": 7
    }
}
```

---

## Integration Examples

### Example 1: Socratic Counselor Agent Integration

```python
class SocraticCounselorAgent(Agent):
    """Main agent handling Socratic dialogue and specs extraction"""

    async def process_response_async(self, request: dict) -> dict:
        """Process user response with specs extraction"""

        project_id = request["project_id"]
        user_response = request["response"]
        phase = request.get("phase")

        # Load project
        project = self.database.load_project(project_id)

        # Extract insights from response
        insights = await self.claude_client.extract_insights(
            user_response,
            project,
            phase=phase
        )

        # Detect conflicts
        conflict_result = await self.orchestrator.agent_bus.send_request(
            "conflict_detector",
            {
                "action": "detect",
                "insights": insights,
                "project_id": project_id
            }
        )

        conflicts = conflict_result.get("conflicts", [])

        # Check debug mode
        from socratic_system.utils.logger import is_debug_mode

        if not is_debug_mode():
            # Production: Auto-save
            self._update_project_context(project, insights)
            self.database.save_project(project)

            logger.info(f"Specs auto-saved for {project_id}")

            return {
                "status": "success",
                "message": "Response processed",
                "data": {
                    "message": {
                        "id": generate_id(),
                        "role": "assistant",
                        "content": f"Thank you for that response. {generate_next_question()}",
                        "timestamp": datetime.now().isoformat()
                    },
                    "extracted_specs": insights,
                    "requires_confirmation": False
                }
            }
        else:
            # Debug: Request confirmation
            logger.info(f"Debug mode - awaiting spec confirmation for {project_id}")

            return {
                "status": "success",
                "data": {
                    "message": {
                        "id": generate_id(),
                        "role": "assistant",
                        "content": f"Thank you for that response. {generate_next_question()}",
                        "timestamp": datetime.now().isoformat()
                    },
                    "extracted_specs": insights,
                    "requires_confirmation": True,
                    "confirmation_message": f"Extracted {len(insights)} spec categories - please confirm to save",
                    "conflicts": conflicts
                }
            }
```

### Example 2: API Router Integration

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/{project_id}/chat/message")
async def send_chat_message(
    project_id: str,
    message: ChatMessage,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """Send message and process specs extraction"""

    try:
        # Validate project exists
        project = orchestrator.database.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Send to socratic counselor agent
        response = await orchestrator.agent_bus.send_request(
            "socratic_counselor",
            {
                "action": "process_response",
                "project_id": project_id,
                "response": message.content,
                "user_id": message.user_id
            }
        )

        return response

    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{project_id}/save-extracted-specs")
async def save_extracted_specs(
    project_id: str,
    specs: ExtractedSpecs,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """Save confirmed specs (debug mode)"""

    try:
        # Validate project exists
        project = orchestrator.database.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate specs not empty
        if not any([specs.goals, specs.requirements, specs.tech_stack, specs.constraints]):
            raise HTTPException(status_code=422, detail="No specs provided")

        # Update project
        project.goals.extend(specs.goals or [])
        project.requirements.extend(specs.requirements or [])
        project.tech_stack.extend(specs.tech_stack or [])
        project.constraints.extend(specs.constraints or [])
        project.updated_at = datetime.now()

        # Save
        orchestrator.database.save_project(project)

        # Emit event
        await orchestrator.event_emitter.emit_async(
            EventType.SPECS_CONFIRMED,
            {"project_id": project_id}
        )

        return {
            "status": "success",
            "message": "Specs saved successfully",
            "project_id": project_id
        }

    except Exception as e:
        logger.exception(f"Error saving specs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Frontend Implementation

### React Component Example

```jsx
import React, { useState } from 'react';

export function SpecsConfirmationDialog({ specs, conflicts, onConfirm, onCancel }) {
    const [editedSpecs, setEditedSpecs] = useState(specs);

    const handleConfirm = () => {
        onConfirm(editedSpecs);
    };

    const handleEditGoal = (index, value) => {
        const newGoals = [...editedSpecs.goals];
        newGoals[index] = value;
        setEditedSpecs({ ...editedSpecs, goals: newGoals });
    };

    return (
        <div className="specs-confirmation-dialog">
            <h2>Confirm Extracted Specifications</h2>

            {/* Goals Section */}
            <section className="specs-section">
                <h3>Goals</h3>
                {editedSpecs.goals.map((goal, i) => (
                    <div key={i} className="spec-item">
                        <textarea
                            value={goal}
                            onChange={(e) => handleEditGoal(i, e.target.value)}
                        />
                    </div>
                ))}
            </section>

            {/* Requirements Section */}
            <section className="specs-section">
                <h3>Requirements</h3>
                {editedSpecs.requirements.map((req, i) => (
                    <div key={i} className="spec-item">
                        <textarea
                            value={req}
                            onChange={(e) => {
                                const newReqs = [...editedSpecs.requirements];
                                newReqs[i] = e.target.value;
                                setEditedSpecs({ ...editedSpecs, requirements: newReqs });
                            }}
                        />
                    </div>
                ))}
            </section>

            {/* Tech Stack Section */}
            <section className="specs-section">
                <h3>Tech Stack</h3>
                {editedSpecs.tech_stack.map((tech, i) => (
                    <div key={i} className="spec-item">
                        <textarea value={tech} readOnly />
                    </div>
                ))}
            </section>

            {/* Conflicts Warning */}
            {conflicts && conflicts.length > 0 && (
                <div className="conflicts-section warning">
                    <h3>⚠️ Detected Conflicts</h3>
                    {conflicts.map((conflict, i) => (
                        <div key={i} className="conflict-item">
                            <p><strong>{conflict.type}:</strong> {conflict.message}</p>
                        </div>
                    ))}
                </div>
            )}

            {/* Action Buttons */}
            <div className="dialog-actions">
                <button onClick={handleConfirm} className="btn-primary">
                    Confirm & Save
                </button>
                <button onClick={onCancel} className="btn-secondary">
                    Cancel
                </button>
            </div>
        </div>
    );
}

// Usage in Chat Component
export function ChatPage() {
    const [showConfirmation, setShowConfirmation] = useState(false);
    const [pendingSpecs, setPendingSpecs] = useState(null);

    const handleChatMessage = async (message) => {
        const response = await sendChatMessage(projectId, message);

        if (response.requires_confirmation) {
            // Show confirmation dialog
            setPendingSpecs({
                specs: response.extracted_specs,
                conflicts: response.conflicts
            });
            setShowConfirmation(true);
        }
    };

    const handleConfirmSpecs = async (confirmedSpecs) => {
        await saveExtractedSpecs(projectId, confirmedSpecs);
        setShowConfirmation(false);
        setPendingSpecs(null);
    };

    return (
        <div>
            {/* Chat interface */}
            <ChatInput onSubmit={handleChatMessage} />

            {/* Confirmation dialog */}
            {showConfirmation && pendingSpecs && (
                <SpecsConfirmationDialog
                    specs={pendingSpecs.specs}
                    conflicts={pendingSpecs.conflicts}
                    onConfirm={handleConfirmSpecs}
                    onCancel={() => setShowConfirmation(false)}
                />
            )}
        </div>
    );
}
```

---

## Data Models

### ExtractedSpecs Schema

```python
from pydantic import BaseModel, Field
from typing import List

class ExtractedSpecs(BaseModel):
    """Extracted specifications from user response"""

    goals: List[str] = Field(
        default_factory=list,
        description="Goals and objectives",
        example=["Streamline operations", "Reduce costs"]
    )

    requirements: List[str] = Field(
        default_factory=list,
        description="Functional requirements",
        example=["Real-time reporting", "Mobile support"]
    )

    tech_stack: List[str] = Field(
        default_factory=list,
        description="Technologies to use",
        example=["Python", "PostgreSQL", "React"]
    )

    constraints: List[str] = Field(
        default_factory=list,
        description="Constraints and limitations",
        example=["Budget: $100k", "Timeline: 6 months"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "goals": ["Streamline operations"],
                "requirements": ["Real-time reporting"],
                "tech_stack": ["Python"],
                "constraints": ["Budget: $100k"]
            }
        }
```

### ChatMessage Schema

```python
class ChatMessage(BaseModel):
    """Chat message from user"""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Message content"
    )

    user_id: str = Field(
        ...,
        description="User who sent message"
    )

    project_id: str = Field(
        ...,
        description="Project context"
    )
```

### Conflict Schema

```python
class Conflict(BaseModel):
    """Detected conflict in specs"""

    type: str = Field(
        ...,
        description="Conflict type: tech_stack, requirements, goals, constraints"
    )

    severity: str = Field(
        default="warning",
        description="Severity: info, warning, error"
    )

    message: str = Field(
        ...,
        description="Human-readable conflict description"
    )

    details: Optional[Dict] = Field(
        default=None,
        description="Additional details"
    )
```

---

## Error Handling

### Common Error Scenarios

**Scenario 1: Project Not Found**

```json
{
    "status": "error",
    "error": {
        "code": "NOT_FOUND",
        "message": "Project not found",
        "details": "Project 'proj_xyz' does not exist"
    }
}
```

**Scenario 2: Invalid Input**

```json
{
    "status": "error",
    "error": {
        "code": "INVALID_INPUT",
        "message": "Invalid message content",
        "details": "Content cannot be empty"
    }
}
```

**Scenario 3: Extraction Failed**

```json
{
    "status": "error",
    "error": {
        "code": "EXTRACTION_FAILED",
        "message": "Failed to extract specifications",
        "details": "Claude API returned unexpected response"
    }
}
```

### Error Handling in Frontend

```javascript
async function handleChatMessage(projectId, message) {
    try {
        const response = await fetch(`/api/projects/${projectId}/chat/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: message })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'Request failed');
        }

        const data = await response.json();

        if (data.requires_confirmation) {
            // Show confirmation dialog
            showSpecsConfirmationDialog(data.extracted_specs);
        } else {
            // Show success message
            showSuccessMessage('Response processed');
        }

    } catch (error) {
        console.error('Error:', error);
        showErrorMessage(`Failed to process message: ${error.message}`);
    }
}
```

---

**Last Updated**: May 2026
**Version**: 1.3.3
