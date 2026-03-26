# Socrates Maturity System Documentation

## Overview

The Socrates Maturity System measures how well a user (or project) understands a subject through progressive learning phases. It's a pure, decoupled calculation system that gates agent behavior based on learning readiness.

**Key Characteristics:**
- ✅ **Pure**: No side effects, pure mathematical calculations
- ✅ **Decoupled**: Not embedded in agent code
- ✅ **Observable**: Trackable history of maturity changes
- ✅ **Gating**: Controls which agents can run via PureOrchestrator
- ✅ **Extensible**: Customizable via callbacks

---

## What is Maturity?

Maturity represents a user's understanding level in a learning domain, expressed as a percentage (0-100) or float (0.0-1.0).

### Types of Maturity

1. **Overall Maturity**: Average across all phases
   - Calculated as: `Average(discovery, analysis, design, implementation)`
   - Range: 0-100%

2. **Phase Maturity**: Understanding within a specific phase
   - Discovery: Initial understanding
   - Analysis: Deeper analysis skills
   - Design: Design and architecture skills
   - Implementation: Practical implementation skills

3. **Category Maturity**: Understanding of specific topics within phases
   - Each phase can have multiple categories (e.g., "error handling", "performance")
   - Aggregated to calculate phase maturity

### Maturity Thresholds

| Threshold | Level | Status | Agent Behavior |
|-----------|-------|--------|-----------------|
| 0-5% | Novice | Low (🔴) | Can only access basic agents |
| 5-10% | Beginner | Moderate (🟡) | Limited agent access |
| 10-20% | Intermediate | Good (🟢) | Quality controller can guide improvements |
| 20%+ | Advanced | Excellent (✅) | All agents available, ready to advance |

---

## How is Maturity Calculated?

### 1. Phase Maturity Calculation

Phase maturity is calculated from category scores within that phase:

```python
phase_maturity = Average(category_scores[phase])
```

**Example:**
```
Discovery Phase Categories:
- Problem Understanding: 80%
- Requirements Definition: 70%
- Scope Definition: 90%

Phase Maturity = (80 + 70 + 90) / 3 = 80%
```

### 2. Overall Maturity Calculation

Overall maturity is the average of all phase maturities:

```python
overall_maturity = Average(phase_maturity_scores.values())
```

**Example:**
```
Phase Maturities:
- Discovery: 80%
- Analysis: 60%
- Design: 40%
- Implementation: 20%

Overall Maturity = (80 + 60 + 40 + 20) / 4 = 50%
```

### 3. Current Phase Estimation

The current phase is estimated based on overall maturity:

```python
if overall_maturity < 25%:
    current_phase = "discovery"
elif overall_maturity < 50%:
    current_phase = "analysis"
elif overall_maturity < 75%:
    current_phase = "design"
else:
    current_phase = "implementation"
```

### 4. Weak Area Identification

Categories with scores below a threshold are identified as weak:

```python
weak_categories = [
    category for category, score in categories.items()
    if score < threshold  # e.g., threshold = 25%
]
```

---

## Phases Explained

### Discovery (0-25% Overall Maturity)

**Goals:**
- Understand the problem
- Define requirements
- Identify constraints and scope

**Skills Developed:**
- Problem analysis
- Requirement gathering
- Stakeholder communication

**Quality Gates:**
- Minimum 5% maturity to progress
- Must complete specification document
- Peer review required

**Agent Roles:**
- SocraticCounselor: Asks guiding questions
- ContextAnalyzer: Helps identify context
- KnowledgeManager: Provides reference materials

### Analysis (25-50% Overall Maturity)

**Goals:**
- Decompose the problem
- Identify solution approaches
- Assess feasibility

**Skills Developed:**
- System decomposition
- Technical analysis
- Solution design

**Quality Gates:**
- Minimum 20% maturity to progress (triggers QualityController)
- Must document analysis
- Design review required

**Agent Roles:**
- ProjectManager: Organizes analysis work
- ContextAnalyzer: Decomposes problem
- QualityController: Reviews analysis quality

### Design (50-75% Overall Maturity)

**Goals:**
- Create detailed design
- Plan implementation
- Address edge cases

**Skills Developed:**
- Architecture design
- Implementation planning
- Error handling design

**Quality Gates:**
- All previous gates passed
- Design document complete
- Architecture approved

**Agent Roles:**
- CodeGenerator: Suggests design patterns
- QualityController: Reviews design
- SkillGeneratorAgent: Identifies skill gaps

### Implementation (75%+ Overall Maturity)

**Goals:**
- Implement the solution
- Handle edge cases
- Optimize and polish

**Skills Developed:**
- Coding skills
- Testing skills
- Performance optimization

**Quality Gates:**
- All previous gates passed
- Code review required
- Tests required

**Agent Roles:**
- CodeGenerator: Generates code
- CodeValidator: Validates code
- QualityController: Ensures quality standards

---

## Quality Thresholds

### By Maturity Level

| Maturity | Action | Agent Response |
|----------|--------|-----------------|
| 0-5% | Learning basics | Basic SocraticCounselor guidance |
| 5-10% | Building foundation | Gentle guidance, lots of questions |
| 10-20% | Steady progress | QualityController begins detailed feedback |
| 20-50% | Clear understanding | More advanced feedback, pattern suggestions |
| 50-75% | Advanced thinking | Architecture-level feedback |
| 75%+ | Expert level | Optimization and refinement focus |

### Per-Category Quality Standards

Each category has quality expectations that increase with maturity:

```python
# Discovery Phase - Problem Understanding
QUALITY_STANDARDS = {
    "discovery": {
        "problem_understanding": {
            "0-10%": "Identify basic problem statement",
            "10-20%": "Document detailed problem analysis",
            "20-50%": "Identify constraints and scope",
            "50%+": "Comprehensive problem decomposition"
        }
    }
}
```

---

## How Maturity Gates Agents

### PureOrchestrator Gating Mechanism

The `PureOrchestrator` controls agent execution based on maturity using quality gates:

```python
# In PureOrchestrator (from socratic-agents)
def execute_agent(self, agent_name: str, request: AgentRequest):
    # Get user maturity
    maturity = self.get_maturity(user_id, phase)

    # Check if maturity meets minimum threshold
    if not self._check_quality_gate(agent_name, maturity):
        return {
            "status": "blocked",
            "reason": f"Minimum {threshold}% maturity required",
            "current": maturity
        }

    # Execute agent
    return agent.process(request)
```

### Quality Gate Definitions

```python
QUALITY_GATES = {
    "code_generator": {
        "min_maturity": 20,  # Needs 20% maturity
        "phase": "implementation"
    },
    "quality_controller": {
        "min_maturity": 10,  # Needs 10% maturity
        "phase": "analysis"
    },
    "socratic_counselor": {
        "min_maturity": 0,   # Always available
        "phase": "all"
    }
}
```

### Example: Gating in Action

```python
# User has 8% overall maturity (Beginner phase)

# ✓ Allowed: SocraticCounselor (min 0%)
result = orchestrator.execute("socratic_counselor", request)
# Returns: Guided questions and gentle feedback

# ✗ Blocked: QualityController (min 10%)
result = orchestrator.execute("quality_controller", request)
# Returns: {"status": "blocked", "current": 8, "required": 10}

# User progresses to 20% maturity (Intermediate phase)

# ✓ Allowed: QualityController (min 10%)
result = orchestrator.execute("quality_controller", request)
# Returns: Detailed quality feedback and improvement suggestions
```

---

## Customizing the Maturity System

### 1. Setting a Custom Maturity Callback

The maturity system uses callbacks to integrate with Socrates data:

```python
from socratic_system.orchestration import get_library_manager

# Get the library manager
manager = get_library_manager(api_key="your-api-key")

# Define a custom maturity calculation
def calculate_user_maturity(user_id: str, phase: str) -> float:
    """
    Calculate maturity for a user in a phase.

    Args:
        user_id: User identifier
        phase: Phase name ("discovery", "analysis", "design", "implementation")

    Returns:
        Maturity score 0.0-1.0
    """
    # Load user's project
    project = db.load_user_project(user_id)

    # Get phase-specific maturity
    phase_scores = project.phase_maturity_scores or {}
    maturity_percent = phase_scores.get(phase, 0)

    # Convert to 0.0-1.0 range
    return maturity_percent / 100.0

# Register the callback
manager.set_maturity_callback(calculate_user_maturity)
```

### 2. Customizing Thresholds

Edit quality thresholds in `socratic_system/config/constants.py`:

```python
# Default thresholds
MATURITY_THRESHOLD_HIGH = 20.0      # Ready to advance
MATURITY_THRESHOLD_MEDIUM = 10.0    # Medium maturity
MATURITY_THRESHOLD_LOW = 5.0        # Low maturity

# Customize for your domain:
MATURITY_THRESHOLD_HIGH = 30.0      # Higher bar for advancement
MATURITY_THRESHOLD_MEDIUM = 15.0
MATURITY_THRESHOLD_LOW = 5.0
```

### 3. Customizing Phase Definitions

Edit phases in `socratic_system/models/project.py`:

```python
# Add custom phases
PROJECT_PHASES = [
    "discovery",
    "analysis",
    "design",
    "prototyping",      # Custom: add prototyping phase
    "implementation",
    "testing",          # Custom: add testing phase
    "deployment"        # Custom: add deployment phase
]
```

### 4. Handling Maturity Events

Register an event callback to react to maturity milestones:

```python
def handle_maturity_event(event, data: Dict[str, Any]):
    """
    Handle maturity-related events.

    Args:
        event: CoordinationEvent from PureOrchestrator
        data: Event data (agent, result, timestamp, etc.)
    """
    if event.value == "phase_gate_passed":
        # User advanced to new phase
        print(f"User {data['user_id']} advanced to {data['new_phase']}")

        # Could trigger:
        # - Send congratulations email
        # - Award badges
        # - Unlock new content
        # - Update learning plan

    elif event.value == "quality_threshold_met":
        # User reached quality milestone
        print(f"User {data['user_id']} reached {data['threshold']}% in {data['phase']}")

# Register the callback
manager.set_event_callback(handle_maturity_event)
```

### 5. Creating Agent Quality Gates

Define custom quality requirements for agents:

```python
# In your router or business logic
def my_endpoint(agent_name: str, project_id: str, request_data: Dict):
    # Get current maturity
    project = db.load_project(project_id)
    maturity = project.phase_maturity_scores.get("design", 0) / 100.0

    # Check gate
    if agent_name == "code_generator" and maturity < 0.30:
        return {
            "status": "error",
            "message": "Requires 30% design maturity",
            "current": maturity
        }

    # Execute agent
    return orchestrator.execute_agent(agent_name, request_data)
```

---

## API Endpoints for Maturity

### Get Project Maturity Status

```bash
GET /projects/{project_id}/maturity/status

Response:
{
    "overall_maturity": 45.5,
    "current_phase": "analysis",
    "phase_scores": {
        "discovery": 80.0,
        "analysis": 65.0,
        "design": 25.0,
        "implementation": 15.0
    },
    "category_breakdown": {
        "discovery": {
            "problem_understanding": 85.0,
            "requirements": 75.0
        },
        "analysis": {
            "decomposition": 70.0,
            "feasibility": 60.0
        }
    },
    "weak_areas": [
        "design.architecture",
        "implementation.coding"
    ],
    "ready_to_advance": false,
    "advancement_progress": "20% towards next phase"
}
```

### Get Maturity History

```bash
GET /projects/{project_id}/maturity/history?limit=10

Response:
{
    "events": [
        {
            "timestamp": "2025-03-26T10:30:00Z",
            "phase": "discovery",
            "before": 75.0,
            "after": 80.0,
            "category": "problem_understanding",
            "agent": "quality_controller",
            "feedback": "Excellent problem definition"
        },
        ...
    ]
}
```

### Recalculate Maturity (Future)

```bash
POST /projects/{project_id}/maturity/recalculate

Response:
{
    "status": "success",
    "overall_maturity": 48.0,
    "changes": [
        {
            "phase": "discovery",
            "before": 80.0,
            "after": 82.5
        }
    ]
}
```

---

## Implementation Status

### ✅ Complete

- [x] MaturityCalculator is pure (no side effects)
- [x] Phase definitions are clear (discovery, analysis, design, implementation)
- [x] Quality thresholds are defined (5%, 10%, 20%)
- [x] Maturity data is stored in ProjectContext
- [x] Maturity history tracking exists
- [x] UI display of maturity exists (terminal commands)
- [x] PureOrchestrator architecture ready for gating
- [x] Library manager callback system ready

### ⚠️ Partial / TODO

- [ ] PureOrchestrator maturity callback returns stub (0.5) - needs real data integration
- [ ] Automatic maturity recalculation after interactions
- [ ] Maturity update endpoints (POST to recalculate)
- [ ] Dynamic threshold configuration (currently hardcoded)
- [ ] More granular agent quality gates
- [ ] Maturity prediction (e.g., "You'll reach 50% in 3 more sessions")

---

## Best Practices

### 1. Always Check Maturity Before Gating

```python
# Good: Check maturity before expensive operation
if project.phase_maturity_scores.get("design", 0) >= 30:
    result = orchestrator.generate_architecture(project)
else:
    result = {"message": "Need more design maturity first"}
```

### 2. Use Callbacks, Not Direct Updates

```python
# Good: Use callback pattern
manager.set_maturity_callback(calculate_maturity)

# Bad: Direct update in agent
project.overall_maturity = 45.0  # ❌ Not tracked
```

### 3. Track Maturity Changes with Events

```python
# Good: Emit events for maturity changes
def handle_event(event, data):
    if event.value == "phase_gate_passed":
        log_to_analytics(f"Milestone: {data['phase']}")

# Bad: Silent updates
project.phase_maturity_scores["analysis"] = 70.0  # No event
```

### 4. Provide Feedback on Gating

```python
# Good: Explain why gated
if maturity < threshold:
    return {
        "status": "not_ready",
        "current": maturity,
        "required": threshold,
        "suggestions": ["Practice problem decomposition", "Review case studies"]
    }

# Bad: Silent failure
if maturity < threshold:
    return {"status": "error"}
```

---

## Architecture Summary

```
User Request
    ↓
APIRouter (e.g., /projects/{id}/code/generate)
    ↓
Get Current Maturity (via callback)
    ↓
Check Quality Gate (MaturityCalculator)
    ├─ If below threshold: Return "not ready" + suggestions
    └─ If above threshold: ↓
PureOrchestrator.execute_agent()
    ↓
Agent (e.g., CodeGenerator) processes request
    ↓
Event Emitted (agent_executed, skills_generated, etc.)
    ↓
Event Callback (update maturity, emit webhooks, etc.)
    ↓
Return Result to User
```

---

## Troubleshooting

### Issue: Agents always return "not ready"

**Solution:** Ensure maturity callback is registered:
```python
manager.set_maturity_callback(your_maturity_function)
```

### Issue: Maturity never advances

**Solution:** Check that maturity is being updated after interactions:
```python
# In your event handler:
def handle_event(event, data):
    if event.value == "agent_completed":
        recalculate_maturity(user_id, project_id)
```

### Issue: Phases don't align with curriculum

**Solution:** Customize phase definitions:
```python
# In constants.py
PROJECT_PHASES = [
    "fundamentals",      # Your phase 1
    "intermediate",      # Your phase 2
    "advanced",          # Your phase 3
    "expert"             # Your phase 4
]
```

---

## See Also

- **[PureOrchestrator Documentation](../ORCHESTRATION_FRAMEWORK.md)** - How orchestrator gates agents
- **[Agent Development Guide](../AGENT_DEVELOPMENT.md)** - Building custom agents (don't embed maturity)
- **[Configuration Guide](../CONFIGURATION.md)** - Setting quality thresholds
- **[API Reference](./API_ENDPOINTS.md)** - Full maturity endpoints
