# Common Recipes and Examples

**Version:** 1.0
**Status:** Complete
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [Quick Start Recipes](#quick-start-recipes)
2. [Project Setup](#project-setup)
3. [Common Tasks](#common-tasks)
4. [Analysis and Reporting](#analysis-and-reporting)
5. [Advanced Workflows](#advanced-workflows)

---

## Quick Start Recipes

### Recipe 1: Minimal Socrates Setup

**Goal:** Get Socrates running with minimal configuration.

```python
"""Minimal Socrates setup (5 minutes)"""

from socratic_system.orchestration import AgentOrchestrator
from socratic_core import SocratesConfig

# 1. Create config
config = SocratesConfig(api_key="sk-your-key-here")

# 2. Create orchestrator
orchestrator = AgentOrchestrator(config)

# 3. Process request
result = orchestrator.process_request({
    "agent": "QualityController",
    "action": "analyze",
    "project_id": "proj_123"
})

print(f"Status: {result['status']}")
print(f"Result: {result['result']}")
```

### Recipe 2: Setup with Learning Tracking

**Goal:** Initialize Socrates with learning persistence.

```python
"""Setup with learning tracking"""

from socratic_system.orchestration import AgentOrchestrator
from socratic_learning.storage import SQLiteLearningStore
from socratic_learning.tracking import InteractionLogger
from socratic_core import SocratesConfig

# 1. Create config
config = SocratesConfig(api_key="sk-your-key-here")

# 2. Setup learning storage
store = SQLiteLearningStore(db_path="./learning.db")

# 3. Create logger with storage
logger = InteractionLogger()
logger.set_storage(store)

# 4. Create orchestrator
orchestrator = AgentOrchestrator(config)

# 5. Ready to use!
result = orchestrator.process_request({...})
```

### Recipe 3: Multi-Project Setup

**Goal:** Manage multiple projects in one session.

```python
"""Setup for managing multiple projects"""

from socratic_system.orchestration import OrchestratorService
from socratic_system.models import Project
from socratic_core import SocratesConfig

# 1. Create config once
config = SocratesConfig(api_key="sk-your-key-here")

# 2. Get orchestrator for user
user_id = "user_123"
orchestrator = OrchestratorService.get_orchestrator(user_id)

# 3. Process multiple projects
projects = ["proj_abc", "proj_def", "proj_ghi"]

for project_id in projects:
    result = orchestrator.process_request({
        "agent": "QualityController",
        "action": "analyze",
        "project_id": project_id
    })

    print(f"{project_id}: {result['status']}")

# 4. Reuse same orchestrator instance automatically
orchestrator2 = OrchestratorService.get_orchestrator(user_id)
assert orchestrator is orchestrator2  # Same object!
```

---

## Project Setup

### Recipe 4: Create New Project with Maturity Tracking

**Goal:** Initialize a new project and start tracking maturity.

```python
"""Create new project with maturity system"""

from socratic_system.models import Project
from socrates_maturity import MaturityCalculator
from datetime import datetime, timezone

# 1. Create project
project = Project(
    project_id="proj_123",
    name="My Python Project",
    owner_id="user_456",
    created_at=datetime.now(timezone.utc).isoformat(),
    category_scores={
        "code_quality": 0.0,
        "testing": 0.0,
        "documentation": 0.0,
        "architecture": 0.0,
        "performance": 0.0
    },
    phase_scores={
        "discovery": 0.0,
        "analysis": 0.0,
        "design": 0.0,
        "implementation": 0.0
    }
)

# 2. Save project
project.save()

# 3. Calculate initial maturity
overall = MaturityCalculator.calculate_overall_maturity(
    project.phase_scores
)

print(f"Project created: {project.project_id}")
print(f"Initial maturity: {overall:.1%}")

# 4. Load and verify
loaded_project = Project.load("proj_123")
print(f"Loaded: {loaded_project.name}")
```

### Recipe 5: Batch Import Projects

**Goal:** Import multiple projects at once.

```python
"""Batch import projects"""

from socratic_system.models import Project
import json
from datetime import datetime, timezone

# 1. Load project definitions
projects_data = [
    {"name": "FastAPI Service", "owner_id": "user_123"},
    {"name": "ML Pipeline", "owner_id": "user_123"},
    {"name": "Mobile App", "owner_id": "user_456"}
]

# 2. Create and save
created_projects = []

for i, data in enumerate(projects_data):
    project = Project(
        project_id=f"proj_{i:03d}",
        name=data["name"],
        owner_id=data["owner_id"],
        created_at=datetime.now(timezone.utc).isoformat(),
        category_scores={cat: 0.0 for cat in [
            "code_quality", "testing", "documentation",
            "architecture", "performance"
        ]},
        phase_scores={phase: 0.0 for phase in [
            "discovery", "analysis", "design", "implementation"
        ]}
    )

    project.save()
    created_projects.append(project)

print(f"Imported {len(created_projects)} projects")
```

---

## Common Tasks

### Recipe 6: Analyze Project Quality

**Goal:** Run comprehensive quality analysis on a project.

```python
"""Comprehensive project quality analysis"""

from socratic_system.orchestration import OrchestratorService
from socratic_system.models import Project

def analyze_project_quality(project_id: str, user_id: str) -> dict:
    """Analyze project quality comprehensively"""

    # 1. Get orchestrator
    orchestrator = OrchestratorService.get_orchestrator(user_id)

    # 2. Load project
    project = Project.load(project_id)

    # 3. Run analysis
    result = orchestrator.process_request({
        "agent": "QualityController",
        "action": "analyze",
        "project_id": project_id,
        "parameters": {
            "depth": "thorough",
            "include_metrics": True
        }
    })

    # 4. Parse results
    if result["status"] == "success":
        return {
            "project": project.name,
            "quality_score": result["result"]["quality_score"],
            "issues": result["result"].get("issues", []),
            "recommendations": result["result"].get("recommendations", []),
            "timestamp": result["metadata"]["timestamp"]
        }
    else:
        return {
            "project": project.name,
            "error": result["error"]
        }

# Usage
quality = analyze_project_quality("proj_123", "user_456")
print(f"Quality Score: {quality['quality_score']}/10")
print(f"Issues: {len(quality['issues'])}")
```

### Recipe 7: Generate Improvement Skills

**Goal:** Generate skills to improve weak project areas.

```python
"""Generate skills for improvement areas"""

from socratic_system.orchestration import OrchestratorService
from socratic_system.models import Project
from socrates_maturity import MaturityCalculator

def generate_improvement_skills(project_id: str, user_id: str) -> dict:
    """Generate skills for weak areas"""

    # 1. Load project and calculate maturity
    project = Project.load(project_id)
    weak = MaturityCalculator.identify_weak_categories(
        project.category_scores
    )

    if not weak:
        return {"status": "no_weak_areas", "skills": {}}

    # 2. Get orchestrator
    orchestrator = OrchestratorService.get_orchestrator(user_id)

    # 3. Generate skills for each weak area
    skills = {}
    for category in weak:
        result = orchestrator.process_request({
            "agent": "SkillGenerator",
            "action": "generate",
            "project_id": project_id,
            "parameters": {
                "focus_category": category,
                "weak_score": project.category_scores[category],
                "current_phase": project.current_phase
            }
        })

        if result["status"] == "success":
            skills[category] = result["result"]["skills"]

    return {
        "project_id": project_id,
        "weak_areas": weak,
        "generated_skills": skills
    }

# Usage
result = generate_improvement_skills("proj_123", "user_456")
print(f"Weak areas: {result['weak_areas']}")
for area, skills in result['generated_skills'].items():
    print(f"  {area}: {len(skills)} skills")
```

### Recipe 8: Update Project Status

**Goal:** Update project maturity after improvements.

```python
"""Update project maturity after improvements"""

from socratic_system.models import Project, MaturityEvent
from socrates_maturity import MaturityCalculator
from datetime import datetime, timezone

def update_project_maturity(
    project_id: str,
    category_improvements: dict
) -> dict:
    """Update project maturity with improvements"""

    # 1. Load project
    project = Project.load(project_id)

    # 2. Apply improvements
    for category, new_score in category_improvements.items():
        old_score = project.category_scores.get(category, 0)

        if new_score > old_score:
            project.category_scores[category] = new_score

            # 3. Record event
            event = MaturityEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="category_improvement",
                category=category,
                previous_score=old_score,
                new_score=new_score,
                change=new_score - old_score,
                agent_responsible="QualityController",
                description=f"{category} improved"
            )

            project.add_event(event)

    # 4. Recalculate overall maturity
    project.overall_maturity = (
        MaturityCalculator.calculate_overall_maturity(
            project.phase_scores
        )
    )

    # 5. Save
    project.save()

    return {
        "project_id": project_id,
        "improvements": category_improvements,
        "new_overall_maturity": project.overall_maturity
    }

# Usage
improvements = {
    "code_quality": 0.75,
    "testing": 0.65,
    "documentation": 0.70
}

result = update_project_maturity("proj_123", improvements)
print(f"New maturity: {result['new_overall_maturity']:.1%}")
```

---

## Analysis and Reporting

### Recipe 9: Generate Daily Learning Report

**Goal:** Generate summary report of daily learning progress.

```python
"""Generate daily learning report"""

from socratic_learning.tracking import InteractionLogger
from socratic_learning.analytics import AnalyticsCalculator
from datetime import datetime, timezone, timedelta

def generate_daily_report(user_id: str) -> dict:
    """Generate daily learning report"""

    # 1. Get interactions from past 24 hours
    logger = InteractionLogger()
    since = (
        datetime.now(timezone.utc) - timedelta(days=1)
    ).isoformat()

    interactions = logger.get_interactions(
        user_id=user_id,
        since=since
    )

    if not interactions:
        return {
            "user_id": user_id,
            "date": datetime.now(timezone.utc).date().isoformat(),
            "interactions": 0,
            "status": "no_data"
        }

    # 2. Calculate metrics
    calculator = AnalyticsCalculator()
    metrics = calculator.calculate_learning_metrics(
        interactions=interactions,
        depth="detailed"
    )

    # 3. Analyze patterns
    success_count = sum(
        1 for i in interactions if i.effectiveness_score > 0.7
    )

    agents_used = list(set(i.agent for i in interactions))

    # 4. Generate report
    return {
        "user_id": user_id,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "summary": {
            "total_interactions": len(interactions),
            "successful_interactions": success_count,
            "success_rate": success_count / len(interactions) if interactions else 0
        },
        "metrics": metrics,
        "agents_used": agents_used,
        "learning_curve": "improving" if metrics["learning_velocity"] > 0.5 else "stable"
    }

# Usage
report = generate_daily_report("user_123")
print(f"Date: {report['date']}")
print(f"Interactions: {report['summary']['total_interactions']}")
print(f"Success rate: {report['summary']['success_rate']:.1%}")
print(f"Learning curve: {report['learning_curve']}")
```

### Recipe 10: Compare Project Maturity Over Time

**Goal:** Track maturity changes over a period.

```python
"""Compare project maturity over time"""

from socratic_system.models import Project
from datetime import datetime, timezone, timedelta

def compare_maturity_over_time(
    project_id: str,
    days: int = 7
) -> dict:
    """Compare maturity progression over time"""

    # 1. Load project
    project = Project.load(project_id)

    # 2. Get events from period
    since = (
        datetime.now(timezone.utc) - timedelta(days=days)
    ).isoformat()

    events = project.get_maturity_events(since=since)

    if not events:
        return {
            "project_id": project_id,
            "period_days": days,
            "status": "no_events"
        }

    # 3. Organize by date
    by_date = {}
    for event in events:
        date = event.timestamp[:10]
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(event)

    # 4. Calculate daily changes
    daily_changes = {}
    for date, day_events in by_date.items():
        daily_changes[date] = {
            "improvements": len([e for e in day_events if e.change > 0]),
            "total_change": sum(e.change for e in day_events),
            "categories_improved": list(set(e.category for e in day_events))
        }

    # 5. Overall stats
    total_improvement = sum(e.change for e in events if e.change > 0)

    return {
        "project_id": project_id,
        "period_days": days,
        "total_events": len(events),
        "total_improvement": total_improvement,
        "current_maturity": project.overall_maturity,
        "daily_changes": daily_changes
    }

# Usage
comparison = compare_maturity_over_time("proj_123", days=7)
print(f"Period: {comparison['period_days']} days")
print(f"Total improvement: +{comparison['total_improvement']:.1%}")
print(f"Current maturity: {comparison['current_maturity']:.1%}")
```

---

## Advanced Workflows

### Recipe 11: Multi-Agent Workflow with Fallbacks

**Goal:** Execute complex workflow with error handling.

```python
"""Multi-agent workflow with fallbacks"""

from socratic_system.orchestration import OrchestratorService
from socratic_system.models import Project

def execute_improvement_workflow(project_id: str, user_id: str) -> dict:
    """
    Execute workflow:
    1. Analyze quality
    2. Generate skills (fallback to analysis if fails)
    3. Generate code (fallback to skills if fails)
    """

    orchestrator = OrchestratorService.get_orchestrator(user_id)
    project = Project.load(project_id)

    workflow = {
        "project_id": project_id,
        "steps": {}
    }

    # Step 1: Analyze
    print("Step 1: Analyzing...")
    analysis = orchestrator.process_request({
        "agent": "QualityController",
        "action": "analyze",
        "project_id": project_id
    })

    workflow["steps"]["analysis"] = {
        "agent": "QualityController",
        "status": analysis["status"],
        "duration_ms": analysis["metadata"]["duration_ms"]
    }

    if analysis["status"] != "success":
        return workflow

    # Step 2: Generate skills
    print("Step 2: Generating skills...")
    skills = orchestrator.process_request({
        "agent": "SkillGenerator",
        "action": "generate",
        "project_id": project_id,
        "parameters": {"focus": analysis["result"].get("weak_areas", [])}
    })

    workflow["steps"]["skills"] = {
        "agent": "SkillGenerator",
        "status": skills["status"],
        "duration_ms": skills["metadata"]["duration_ms"]
    }

    # Fallback if skills failed
    if skills["status"] != "success":
        print("  Fallback: Re-running analysis...")
        skills = analysis  # Use analysis results as fallback
        workflow["steps"]["skills"]["fallback_used"] = True

    # Step 3: Generate code
    print("Step 3: Generating code...")
    code = orchestrator.process_request({
        "agent": "CodeGenerator",
        "action": "generate",
        "project_id": project_id,
        "parameters": {
            "skills": skills.get("result", {}).get("skills", [])
        }
    })

    workflow["steps"]["code"] = {
        "agent": "CodeGenerator",
        "status": code["status"],
        "duration_ms": code["metadata"]["duration_ms"]
    }

    # Fallback if code generation failed
    if code["status"] != "success":
        print("  Fallback: Using generated skills directly...")
        code["status"] = "partial"
        code["result"] = skills.get("result", {})
        workflow["steps"]["code"]["fallback_used"] = True

    return workflow

# Usage
workflow = execute_improvement_workflow("proj_123", "user_456")
for step, result in workflow["steps"].items():
    status = result["status"]
    fallback = " (with fallback)" if result.get("fallback_used") else ""
    print(f"{step}: {status}{fallback}")
```

### Recipe 12: Batch Process Multiple Projects

**Goal:** Process a list of projects sequentially.

```python
"""Batch process multiple projects"""

from socratic_system.orchestration import OrchestratorService
from socratic_system.models import Project

def batch_analyze_projects(
    project_ids: list,
    user_id: str,
    action: str = "analyze"
) -> dict:
    """Analyze multiple projects"""

    orchestrator = OrchestratorService.get_orchestrator(user_id)
    results = {
        "user_id": user_id,
        "total_projects": len(project_ids),
        "results": {}
    }

    for project_id in project_ids:
        try:
            # Load project
            project = Project.load(project_id)

            # Process
            result = orchestrator.process_request({
                "agent": "QualityController",
                "action": action,
                "project_id": project_id
            })

            results["results"][project_id] = {
                "name": project.name,
                "status": result["status"],
                "score": result["result"].get("quality_score") if result["status"] == "success" else None
            }

        except Exception as e:
            results["results"][project_id] = {
                "status": "error",
                "error": str(e)
            }

    # Summary
    successful = len([r for r in results["results"].values() if r["status"] == "success"])
    results["successful"] = successful
    results["failed"] = len(project_ids) - successful

    return results

# Usage
projects = ["proj_001", "proj_002", "proj_003"]
batch_results = batch_analyze_projects(projects, "user_123")

print(f"Processed: {batch_results['successful']}/{batch_results['total_projects']}")
for project_id, result in batch_results["results"].items():
    status_emoji = "✓" if result["status"] == "success" else "✗"
    print(f"  {status_emoji} {project_id}: {result['status']}")
```

---

## Related Documentation

- [Orchestration API](./ORCHESTRATION_API.md)
- [socratic-learning Integration](./SOCRATIC_LEARNING_INTEGRATION.md)
- [socrates-maturity Integration](./SOCRATES_MATURITY_INTEGRATION.md)
- [Common Integration Patterns](./COMMON_INTEGRATION_PATTERNS.md)

