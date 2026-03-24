# Socrates Maturity Integration Guide

**Version:** 1.0
**Status:** Complete
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Core Concepts](#core-concepts)
4. [Integration Patterns](#integration-patterns)
5. [API Reference](#api-reference)
6. [Examples](#examples)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The **socrates-maturity** library provides a pure, phase-based maturity tracking system for AI projects. It integrates with Socrates to:

- **Calculate project maturity** across 4 phases and 5 quality categories
- **Drive agent coordination** through maturity-aware workflow gating
- **Track maturity progression** with historical events
- **Support phase advancement** without penalizing progress
- **Generate workflow recommendations** based on maturity state

### Key Capabilities

| Capability | Purpose | Use Case |
|------------|---------|----------|
| **Maturity Calculation** | Compute phase/category scores | Understand project state |
| **Phase Estimation** | Determine current project phase | Route to appropriate agent |
| **Workflow Orchestration** | Gate agent actions by maturity | Ensure appropriate progression |
| **Weak Area Detection** | Identify improvement opportunities | Prioritize agent focus |
| **Historical Tracking** | Record maturity changes | Track progress over time |

### The 4 Project Phases

```
Discovery (Phase 0)
  ↓ Project objectives and scope identified
Analysis (Phase 1)
  ↓ Requirements analyzed and documented
Design (Phase 2)
  ↓ Architecture and design completed
Implementation (Phase 3)
  ↓ Code written and tested
```

### The 5 Quality Categories

1. **code_quality** - Code structure, style, standards compliance
2. **testing** - Test coverage, test quality, test automation
3. **documentation** - Code docs, API docs, user guides
4. **architecture** - System design, modularity, scalability
5. **performance** - Speed, efficiency, resource usage

---

## Installation

### Prerequisites

- Python 3.8+
- socratic-core >= 0.1.0

### From PyPI

```bash
pip install socrates-maturity
```

### From Source

```bash
git clone https://github.com/anthropics/socrates-maturity.git
cd socrates-maturity
pip install -e .
```

### Verify Installation

```python
from socrates_maturity import MaturityCalculator, PhaseMaturity, CategoryScore

# Test basic calculation
phase_scores = {"discovery": 1.0, "analysis": 0.5, "design": 0.2}
overall = MaturityCalculator.calculate_overall_maturity(phase_scores)
print(f"Overall Maturity: {overall:.1%}")

# Test phase estimation
phase = MaturityCalculator.estimate_current_phase(overall)
print(f"Current Phase: {phase}")
```

---

## Core Concepts

### 1. CategoryScore

Represents maturity for a single quality category.

```python
from socrates_maturity.models import CategoryScore

score = CategoryScore(
    category="code_quality",
    score=0.75,
    last_updated="2026-03-24T10:30:45Z",
    history=[
        {"timestamp": "2026-03-20T09:00:00Z", "score": 0.60},
        {"timestamp": "2026-03-21T10:00:00Z", "score": 0.68},
        {"timestamp": "2026-03-24T10:30:45Z", "score": 0.75}
    ]
)

print(f"Code Quality: {score.score:.1%}")
print(f"Trend: Improving")
```

### 2. PhaseMaturity

Complete maturity information for a project phase.

```python
from socrates_maturity.models import PhaseMaturity

phase = PhaseMaturity(
    phase="analysis",
    overall_score=0.72,
    category_scores={
        "code_quality": 0.80,
        "testing": 0.65,
        "documentation": 0.70,
        "architecture": 0.75,
        "performance": 0.68
    },
    weak_areas=["testing", "performance"],
    strong_areas=["code_quality", "architecture"],
    recommendations=[
        "Increase test coverage",
        "Optimize critical paths"
    ]
)

print(f"Phase: {phase.phase}")
print(f"Overall: {phase.overall_score:.1%}")
print(f"Weak areas: {phase.weak_areas}")
```

### 3. MaturityEvent

Historical record of maturity changes.

```python
from socrates_maturity.models import MaturityEvent

event = MaturityEvent(
    timestamp="2026-03-24T10:30:45Z",
    event_type="category_improvement",
    category="code_quality",
    previous_score=0.60,
    new_score=0.75,
    change=0.15,
    agent_responsible="QualityController",
    description="Code quality improved through refactoring"
)

print(f"Improvement: {event.previous_score:.1%} → {event.new_score:.1%}")
```

### 4. Workflow Types

The maturity system supports workflow orchestration based on phase.

```python
from socrates_maturity.workflows import (
    WorkflowType,
    WorkflowState,
    PhaseProgressionWorkflow,
    SkillRecommendationWorkflow
)

# Phase progression workflow
progression = PhaseProgressionWorkflow()
can_advance = progression.can_advance_phase(
    current_phase="analysis",
    category_scores={
        "code_quality": 0.80,
        "testing": 0.70,
        "documentation": 0.75,
        "architecture": 0.78,
        "performance": 0.72
    }
)

# Skill recommendation workflow
skill_workflow = SkillRecommendationWorkflow()
recommendations = skill_workflow.get_skill_recommendations(
    current_phase="analysis",
    weak_categories=["testing", "documentation"]
)
```

---

## Integration Patterns

### Pattern 1: Maturity-Gated Agent Execution

Only allow certain agents based on maturity level.

```python
from socrates_maturity import MaturityCalculator
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.models import Project

class MaturityGatedOrchestrator:
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator

    def process_request(self, request: dict, project: Project) -> dict:
        # Get project maturity
        maturity = self._get_project_maturity(project)

        # Check if agent is appropriate for maturity level
        agent_phase_requirements = {
            "QualityController": ("analysis", "design", "implementation"),
            "SkillGenerator": ("analysis", "design", "implementation"),
            "CodeGenerator": ("design", "implementation"),
            "ArchitectureDesigner": ("discovery", "analysis"),
            "DocumentationAgent": ("analysis", "design", "implementation")
        }

        required_phases = agent_phase_requirements.get(
            request["agent"],
            ("discovery",)  # Default: allow in any phase
        )

        current_phase = MaturityCalculator.estimate_current_phase(
            maturity["overall_score"]
        )

        if current_phase not in required_phases:
            return {
                "status": "error",
                "error": (
                    f"Agent '{request['agent']}' not appropriate for "
                    f"phase '{current_phase}'. "
                    f"Required: {required_phases}"
                ),
                "current_phase": current_phase
            }

        # Process request with gating passed
        return self.orchestrator.process_request(request)

    def _get_project_maturity(self, project: Project) -> dict:
        """Retrieve project maturity"""
        return {
            "phase_scores": project.phase_scores,
            "category_scores": project.category_scores,
            "overall_score": project.overall_maturity
        }

# Usage
orchestrator = AgentOrchestrator(config)
gated = MaturityGatedOrchestrator(orchestrator)

project = Project.load("proj_123")
result = gated.process_request({
    "agent": "CodeGenerator",
    "action": "generate",
    "project_id": "proj_123"
}, project)

if result["status"] == "error":
    print(f"Cannot execute: {result['error']}")
    print(f"Current phase: {result['current_phase']}")
```

### Pattern 2: Progressive Workflow with Phase Transitions

Automatically progress through phases based on maturity thresholds.

```python
from socrates_maturity import MaturityCalculator
from socrates_maturity.workflows import PhaseProgressionWorkflow

class ProgressiveWorkflow:
    def __init__(self, project: Project):
        self.project = project
        self.calculator = MaturityCalculator()
        self.phase_workflow = PhaseProgressionWorkflow()

    def process_iteratively(self, request: dict) -> dict:
        """Process request and advance phase if appropriate"""

        # Execute agent
        orchestrator = AgentOrchestrator(config)
        result = orchestrator.process_request(request)

        if result["status"] != "success":
            return result

        # Update maturity
        self._update_project_maturity(request, result)

        # Check if phase advancement is possible
        phase_scores = {
            phase: score
            for phase, score in self.project.phase_scores.items()
        }

        can_advance = self.phase_workflow.can_advance_phase(
            current_phase=self.project.current_phase,
            category_scores=self.project.category_scores
        )

        if can_advance:
            self._advance_phase()
            result["phase_advanced"] = True
            result["new_phase"] = self.project.current_phase

        return result

    def _update_project_maturity(self, request: dict, result: dict):
        """Update project maturity based on result"""
        # Extract quality improvements from result
        quality_improvements = result["result"].get(
            "quality_metrics", {}
        )

        for category, score in quality_improvements.items():
            if category in self.project.category_scores:
                self.project.category_scores[category] = max(
                    self.project.category_scores[category],
                    score
                )

        # Recalculate overall maturity
        self.project.overall_maturity = (
            self.calculator.calculate_overall_maturity(
                self.project.phase_scores
            )
        )

    def _advance_phase(self):
        """Advance to next phase"""
        phases = ["discovery", "analysis", "design", "implementation"]
        current_idx = phases.index(self.project.current_phase)

        if current_idx < len(phases) - 1:
            self.project.current_phase = phases[current_idx + 1]
            self.project.save()

# Usage
project = Project.load("proj_123")
workflow = ProgressiveWorkflow(project)

result = workflow.process_iteratively({
    "agent": "QualityController",
    "action": "analyze",
    "project_id": "proj_123"
})

if result.get("phase_advanced"):
    print(f"Project advanced to: {result['new_phase']}")
```

### Pattern 3: Skill Generation Driven by Weak Areas

Generate targeted skills based on weak maturity areas.

```python
from socrates_maturity import MaturityCalculator
from socratic_system.orchestration import OrchestratorService

class SkillGenerationWorkflow:
    def __init__(self):
        self.calculator = MaturityCalculator()

    def generate_skills_for_project(self, project: Project) -> dict:
        """Generate skills targeting weak areas"""

        # Identify weak categories
        weak_categories = self.calculator.identify_weak_categories(
            project.category_scores
        )

        # Get orchestrator for project owner
        orchestrator = OrchestratorService.get_orchestrator(
            project.owner_id
        )

        # Generate skills for each weak area
        skills = {}
        for category in weak_categories:
            result = orchestrator.process_request({
                "agent": "SkillGenerator",
                "action": "generate",
                "project_id": project.project_id,
                "parameters": {
                    "focus_category": category,
                    "weak_score": project.category_scores[category],
                    "current_phase": project.current_phase
                }
            })

            if result["status"] == "success":
                skills[category] = result["result"]["skills"]

        return {
            "project_id": project.project_id,
            "weak_categories": weak_categories,
            "generated_skills": skills
        }

# Usage
workflow = SkillGenerationWorkflow()
project = Project.load("proj_123")

result = workflow.generate_skills_for_project(project)
print(f"Weak areas: {result['weak_categories']}")
for category, skills in result['generated_skills'].items():
    print(f"{category}: {len(skills)} skills generated")
```

### Pattern 4: Maturity Dashboard and Monitoring

Monitor project maturity over time.

```python
from socrates_maturity import MaturityCalculator
from socratic_learning.tracking import InteractionLogger
from socratic_learning.analytics import AnalyticsCalculator
import datetime

class MaturityDashboard:
    def __init__(self, project: Project):
        self.project = project
        self.calculator = MaturityCalculator()
        self.learning_logger = InteractionLogger()

    def get_dashboard_data(self) -> dict:
        """Get comprehensive maturity and learning data"""

        # Current maturity
        current_phase = self.calculator.estimate_current_phase(
            self.project.overall_maturity
        )

        weak_areas = self.calculator.identify_weak_categories(
            self.project.category_scores
        )

        # Historical trend
        history = self._get_maturity_history()

        # Learning progress
        learning_metrics = self._get_learning_metrics()

        return {
            "project": {
                "id": self.project.project_id,
                "name": self.project.name,
                "owner": self.project.owner_id
            },
            "maturity": {
                "overall": self.project.overall_maturity,
                "current_phase": current_phase,
                "category_scores": self.project.category_scores,
                "weak_areas": weak_areas,
                "strong_areas": [
                    cat for cat, score in self.project.category_scores.items()
                    if score > 0.8
                ]
            },
            "history": history,
            "learning": learning_metrics,
            "recommendations": self._generate_recommendations(
                current_phase,
                weak_areas
            )
        }

    def _get_maturity_history(self, days: int = 30) -> list:
        """Get maturity progression over time"""
        since = (
            datetime.datetime.now(datetime.timezone.utc) -
            datetime.timedelta(days=days)
        )

        events = self.project.get_maturity_events(since=since)

        return [
            {
                "timestamp": event.timestamp,
                "category": event.category,
                "change": event.change,
                "new_score": event.new_score
            }
            for event in events
        ]

    def _get_learning_metrics(self) -> dict:
        """Get associated learning metrics"""
        interactions = self.learning_logger.get_interactions(
            project_id=self.project.project_id
        )

        analytics = AnalyticsCalculator()
        metrics = analytics.calculate_learning_metrics(
            interactions=interactions
        )

        return metrics

    def _generate_recommendations(self, phase: str, weak_areas: list) -> list:
        """Generate recommendations for improvement"""
        recommendations = []

        if len(weak_areas) > 0:
            recommendations.append(
                f"Focus on improving: {', '.join(weak_areas)}"
            )

        if phase == "discovery":
            recommendations.append("Define clear project objectives")
        elif phase == "analysis":
            recommendations.append("Complete requirements documentation")
        elif phase == "design":
            recommendations.append("Finalize system architecture")
        elif phase == "implementation":
            recommendations.append("Ensure comprehensive testing")

        return recommendations

# Usage
project = Project.load("proj_123")
dashboard = MaturityDashboard(project)
data = dashboard.get_dashboard_data()

print(f"Project: {data['project']['name']}")
print(f"Overall Maturity: {data['maturity']['overall']:.1%}")
print(f"Current Phase: {data['maturity']['current_phase']}")
print(f"Weak Areas: {data['maturity']['weak_areas']}")
print(f"Recommendations:")
for rec in data['recommendations']:
    print(f"  - {rec}")
```

---

## API Reference

### MaturityCalculator

```python
from socrates_maturity import MaturityCalculator

# Static methods
overall = MaturityCalculator.calculate_overall_maturity(
    phase_scores: Dict[str, float]
) -> float
# Returns overall maturity (0.0-1.0) from phase scores

phase = MaturityCalculator.estimate_current_phase(
    overall_maturity: float
) -> str
# Returns: "discovery", "analysis", "design", or "implementation"

weak = MaturityCalculator.identify_weak_categories(
    category_scores: Dict[str, float],
    threshold: float = 0.7
) -> List[str]
# Returns categories with scores below threshold

strong = MaturityCalculator.identify_strong_categories(
    category_scores: Dict[str, float],
    threshold: float = 0.8
) -> List[str]
# Returns categories with scores above threshold
```

### PhaseMaturity

```python
from socrates_maturity import PhaseMaturity

phase = PhaseMaturity(
    phase: str,
    overall_score: float,
    category_scores: Dict[str, float],
    weak_areas: List[str],
    strong_areas: List[str],
    recommendations: List[str]
)

# Properties
phase.phase                 # Current phase name
phase.overall_score         # 0.0-1.0 maturity score
phase.category_scores       # Per-category scores
phase.weak_areas           # Areas needing improvement
phase.strong_areas         # Areas of strength
phase.recommendations      # Improvement suggestions
```

### MaturityEvent

```python
from socrates_maturity import MaturityEvent

event = MaturityEvent(
    timestamp: str,
    event_type: str,
    category: str,
    previous_score: float,
    new_score: float,
    change: float,
    agent_responsible: str,
    description: str
)

# Properties
event.timestamp            # ISO timestamp
event.event_type          # "category_improvement", "phase_change", etc.
event.category            # Category affected
event.previous_score      # Score before change
event.new_score          # Score after change
event.change             # Difference (new - previous)
event.agent_responsible  # Which agent made change
event.description        # Human-readable description
```

### Workflow Classes

```python
from socrates_maturity.workflows import (
    PhaseProgressionWorkflow,
    SkillRecommendationWorkflow,
    MaturityTransitionWorkflow,
    LearningVelocityWorkflow
)

# Phase Progression
progression = PhaseProgressionWorkflow()
can_advance = progression.can_advance_phase(
    current_phase: str,
    category_scores: Dict[str, float]
) -> bool

# Skill Recommendation
skill_rec = SkillRecommendationWorkflow()
recommendations = skill_rec.get_skill_recommendations(
    current_phase: str,
    weak_categories: List[str]
) -> List[str]

# Maturity Transition
transition = MaturityTransitionWorkflow()
suggestion = transition.suggest_next_action(
    current_maturity: float,
    category_scores: Dict[str, float]
) -> Dict[str, Any]

# Learning Velocity
velocity = LearningVelocityWorkflow()
speed = velocity.calculate_learning_velocity(
    previous_scores: Dict[str, float],
    current_scores: Dict[str, float],
    time_period_hours: float
) -> float
```

---

## Examples

### Example 1: Basic Maturity Calculation

```python
"""Calculate and display project maturity"""

from socrates_maturity import MaturityCalculator
from socratic_system.models import Project

# Load project
project = Project.load("proj_123")

# Calculate overall maturity
overall = MaturityCalculator.calculate_overall_maturity(
    project.phase_scores
)

print(f"Project: {project.name}")
print(f"Overall Maturity: {overall:.1%}")

# Estimate current phase
current_phase = MaturityCalculator.estimate_current_phase(overall)
print(f"Current Phase: {current_phase}")

# Identify weak areas
weak = MaturityCalculator.identify_weak_categories(
    project.category_scores
)

print(f"Weak Areas: {weak}")
```

### Example 2: Maturity-Driven Agent Selection

```python
"""Select agents based on project maturity"""

from socrates_maturity import MaturityCalculator
from socratic_system.orchestration import OrchestratorService

def get_appropriate_agents(project_id: str) -> List[str]:
    """Get list of agents appropriate for project maturity"""

    project = Project.load(project_id)
    phase = MaturityCalculator.estimate_current_phase(
        project.overall_maturity
    )

    # Map phase to appropriate agents
    phase_agents = {
        "discovery": ["ArchitectureDesigner"],
        "analysis": ["QualityController", "ArchitectureDesigner"],
        "design": [
            "QualityController",
            "ArchitectureDesigner",
            "SkillGenerator"
        ],
        "implementation": [
            "QualityController",
            "SkillGenerator",
            "CodeGenerator"
        ]
    }

    return phase_agents.get(phase, [])

# Usage
project_id = "proj_123"
agents = get_appropriate_agents(project_id)
print(f"Available agents: {agents}")

orchestrator = OrchestratorService.get_orchestrator("user_123")
for agent in agents:
    result = orchestrator.process_request({
        "agent": agent,
        "action": "analyze",
        "project_id": project_id
    })
    print(f"{agent}: {result['status']}")
```

### Example 3: Automatic Skill Generation for Weak Areas

```python
"""Generate skills targeting weak project areas"""

from socrates_maturity import MaturityCalculator
from socratic_system.orchestration import OrchestratorService

def improve_weak_areas(project_id: str, user_id: str) -> dict:
    """Generate skills for weak project areas"""

    project = Project.load(project_id)
    weak = MaturityCalculator.identify_weak_categories(
        project.category_scores
    )

    if not weak:
        return {"status": "no_weak_areas", "message": "All areas strong"}

    orchestrator = OrchestratorService.get_orchestrator(user_id)

    results = {}
    for category in weak:
        result = orchestrator.process_request({
            "agent": "SkillGenerator",
            "action": "generate",
            "project_id": project_id,
            "parameters": {
                "focus_category": category,
                "weak_score": project.category_scores[category]
            }
        })

        results[category] = {
            "status": result["status"],
            "skills": result.get("result", {}).get("skills", [])
        }

    return {
        "project_id": project_id,
        "weak_areas": weak,
        "generated_skills": results
    }

# Usage
result = improve_weak_areas("proj_123", "user_456")
print(f"Weak areas: {result['weak_areas']}")
for area, info in result['generated_skills'].items():
    print(f"{area}: {len(info['skills'])} skills generated")
```

---

## Best Practices

### 1. Use Maturity as a Gating Mechanism

```python
# Good: Gate agent execution by maturity
if current_phase in agent_phase_requirements:
    result = orchestrator.process_request(request)

# Avoid: Allow any agent in any phase
result = orchestrator.process_request(request)
```

### 2. Update Maturity After Agent Execution

```python
# Good: Update scores after improvements
result = orchestrator.process_request(request)
if result["status"] == "success":
    project.category_scores[category] = new_score
    project.save()

# Avoid: Never updating maturity
result = orchestrator.process_request(request)
# Score remains unchanged
```

### 3. Track Maturity Events for History

```python
# Good: Record every significant change
event = MaturityEvent(
    timestamp=datetime.now().isoformat(),
    event_type="category_improvement",
    category="code_quality",
    previous_score=0.60,
    new_score=0.75,
    change=0.15,
    agent_responsible="QualityController",
    description="Code quality improved through refactoring"
)
project.add_event(event)

# Avoid: No historical tracking
project.category_scores["code_quality"] = 0.75  # No history
```

### 4. Check Phase Advancement Conditions

```python
# Good: Validate before advancing phase
can_advance = phase_workflow.can_advance_phase(
    current_phase=phase,
    category_scores=project.category_scores
)
if can_advance:
    project.current_phase = next_phase

# Avoid: Advancing without validation
project.current_phase = next_phase  # May be premature
```

### 5. Use Weak Areas for Skill Focus

```python
# Good: Target skills to weak areas
weak = MaturityCalculator.identify_weak_categories(
    project.category_scores
)
for category in weak:
    # Generate skills for this category
    result = orchestrator.process_request({
        "agent": "SkillGenerator",
        "action": "generate",
        "parameters": {"focus_category": category}
    })

# Avoid: Generating random skills
result = orchestrator.process_request({
    "agent": "SkillGenerator",
    "action": "generate"
    # No focus specified
})
```

---

## Troubleshooting

### Issue 1: Maturity Not Advancing

**Problem:** Project maturity stays at same level despite agent improvements.

**Solution:** Ensure maturity updates after agent execution.

```python
# Check that maturity is being updated
before = project.overall_maturity
result = orchestrator.process_request(request)

# Update maturity
if result["status"] == "success":
    project.category_scores[category] = result["result"]["score"]
    project.overall_maturity = MaturityCalculator.calculate_overall_maturity(
        project.phase_scores
    )
    project.save()

after = project.overall_maturity
print(f"Maturity changed: {before:.1%} → {after:.1%}")
```

### Issue 2: Phase Stuck at Discovery

**Problem:** Project never advances beyond discovery phase.

**Solution:** Verify category score minimums for phase advancement.

```python
from socrates_maturity.workflows import PhaseProgressionWorkflow

workflow = PhaseProgressionWorkflow()

# Check advancement criteria
can_advance = workflow.can_advance_phase(
    current_phase="discovery",
    category_scores=project.category_scores
)

if not can_advance:
    # Identify what's blocking advancement
    requirements = workflow.get_phase_requirements("discovery")
    print(f"Requirements to advance from discovery:")
    for category, min_score in requirements.items():
        current = project.category_scores.get(category, 0)
        print(f"  {category}: {current:.1%} (need {min_score:.1%})")
```

### Issue 3: Weak Area Detection Not Working

**Problem:** Weak areas list is empty or incorrect.

**Solution:** Verify category scores are properly set.

```python
from socrates_maturity import MaturityCalculator

# Check weak areas with different threshold
weak_low = MaturityCalculator.identify_weak_categories(
    project.category_scores,
    threshold=0.5  # Very low threshold
)

weak_high = MaturityCalculator.identify_weak_categories(
    project.category_scores,
    threshold=0.9  # Very high threshold
)

print(f"Weak (threshold 0.5): {weak_low}")
print(f"Weak (threshold 0.9): {weak_high}")

# Check if scores are initialized
for category, score in project.category_scores.items():
    print(f"{category}: {score}")
```

---

## Related Documentation

- [Architecture Overview](../ARCHITECTURE.md)
- [socratic-learning Integration](./SOCRATIC_LEARNING_INTEGRATION.md)
- [Orchestration API](./ORCHESTRATION_API.md)
- [Configuration Guide](./CONFIGURATION_GUIDE.md)

---

## Support

For issues, bugs, or feature requests:
- GitHub: https://github.com/anthropics/socrates-maturity
- Documentation: https://socrates-maturity.readthedocs.io
