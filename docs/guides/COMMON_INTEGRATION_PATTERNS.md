# Common Integration Patterns

**Version:** 1.0
**Status:** Complete
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [Overview](#overview)
2. [Core Patterns](#core-patterns)
3. [Multi-Library Workflows](#multi-library-workflows)
4. [Advanced Patterns](#advanced-patterns)
5. [Performance Patterns](#performance-patterns)
6. [Error Handling Patterns](#error-handling-patterns)

---

## Overview

This document describes common patterns that emerge when integrating multiple Socrates libraries. Each pattern addresses real-world scenarios developers encounter.

### Pattern Categories

- **Core Patterns** - Fundamental integration approaches
- **Multi-Library Workflows** - Combining 2+ libraries
- **Advanced Patterns** - Complex, sophisticated integrations
- **Performance Patterns** - Optimization techniques
- **Error Handling Patterns** - Robust error management

---

## Core Patterns

### Pattern 1: Sequential Agent Processing with Maturity Gating

**Use Case:** Execute multiple agents in sequence, respecting project maturity.

**Libraries:** socratic-core, socrates-maturity, orchestration

```python
from socratic_system.orchestration import OrchestratorService
from socrates_maturity import MaturityCalculator
from socratic_system.models import Project

class SequentialAgentWorkflow:
    """Execute agents sequentially with maturity-aware gating"""

    def __init__(self, project_id: str, user_id: str):
        self.project = Project.load(project_id)
        self.orchestrator = OrchestratorService.get_orchestrator(user_id)
        self.calculator = MaturityCalculator()

    def execute_workflow(self, agent_sequence: list) -> dict:
        """Execute agents in sequence, checking maturity gate"""

        results = {}

        for agent_config in agent_sequence:
            agent_name = agent_config["agent"]
            action = agent_config["action"]

            # Check if agent is appropriate for current maturity
            phase = self.calculator.estimate_current_phase(
                self.project.overall_maturity
            )

            if not self._is_agent_allowed_in_phase(agent_name, phase):
                results[agent_name] = {
                    "status": "skipped",
                    "reason": f"Not available in {phase} phase"
                }
                continue

            # Execute agent
            result = self.orchestrator.process_request({
                "agent": agent_name,
                "action": action,
                "project_id": self.project.project_id,
                "parameters": agent_config.get("parameters", {})
            })

            results[agent_name] = result

            # Stop on first error
            if result["status"] == "error":
                results["workflow_status"] = "halted"
                break

            # Update maturity if there were improvements
            self._update_maturity(result)

        results["final_maturity"] = self.project.overall_maturity
        return results

    def _is_agent_allowed_in_phase(self, agent: str, phase: str) -> bool:
        """Check if agent is appropriate for phase"""
        allowed = {
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
        return agent in allowed.get(phase, [])

    def _update_maturity(self, result: dict):
        """Update project maturity based on agent result"""
        if result["status"] != "success":
            return

        improvements = result["result"].get("quality_improvements", {})
        for category, score in improvements.items():
            if category in self.project.category_scores:
                self.project.category_scores[category] = max(
                    self.project.category_scores[category],
                    score
                )

        self.project.overall_maturity = (
            self.calculator.calculate_overall_maturity(
                self.project.phase_scores
            )
        )
        self.project.save()

# Usage
workflow = SequentialAgentWorkflow("proj_123", "user_456")
results = workflow.execute_workflow([
    {"agent": "QualityController", "action": "analyze"},
    {"agent": "SkillGenerator", "action": "generate"},
    {"agent": "CodeGenerator", "action": "generate"}
])

for agent, result in results.items():
    print(f"{agent}: {result['status']}")
```

### Pattern 2: Learning-Enhanced Maturity Tracking

**Use Case:** Combine learning metrics with maturity progression.

**Libraries:** socratic-learning, socrates-maturity

```python
from socratic_learning.tracking import Session, InteractionLogger
from socratic_learning.analytics import AnalyticsCalculator
from socrates_maturity import MaturityCalculator
from socratic_system.models import Project
import datetime

class LearningMaturityTracker:
    """Track both learning progress and project maturity"""

    def __init__(self, project_id: str, user_id: str):
        self.project = Project.load(project_id)
        self.user_id = user_id
        self.session = Session(user_id=user_id)
        self.learning_logger = InteractionLogger()
        self.learning_calculator = AnalyticsCalculator()
        self.maturity_calculator = MaturityCalculator()

    def track_interaction_and_update_maturity(
        self,
        interaction_data: dict
    ) -> dict:
        """Log interaction and update maturity if needed"""

        from socratic_learning.core import Interaction

        # Create and log interaction
        interaction = Interaction(
            session_id=self.session.session_id,
            user_id=self.user_id,
            agent=interaction_data["agent"],
            action=interaction_data["action"],
            question=interaction_data.get("question", ""),
            response=interaction_data["result"],
            effectiveness_score=interaction_data.get(
                "effectiveness_score", 0.5
            ),
            timestamp=datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat()
        )

        self.session.add_interaction(interaction)
        self.learning_logger.log_interaction(interaction)

        # Calculate learning metrics
        learning_metrics = self.learning_calculator.calculate_learning_metrics(
            interactions=self.session.interactions
        )

        # Map learning metrics to maturity improvements
        maturity_improvements = self._map_learning_to_maturity(
            learning_metrics,
            interaction_data
        )

        # Update project maturity
        for category, score in maturity_improvements.items():
            self.project.category_scores[category] = max(
                self.project.category_scores[category],
                score
            )

        self.project.overall_maturity = (
            self.maturity_calculator.calculate_overall_maturity(
                self.project.phase_scores
            )
        )
        self.project.save()

        # Check if phase can advance based on learning velocity
        phase_advancement = self._check_phase_advancement(learning_metrics)

        return {
            "interaction": interaction,
            "learning_metrics": learning_metrics,
            "maturity_improvements": maturity_improvements,
            "phase_advanced": phase_advancement["advanced"],
            "new_phase": phase_advancement.get("new_phase")
        }

    def _map_learning_to_maturity(self, learning_metrics: dict, interaction: dict) -> dict:
        """Map learning metrics to maturity category improvements"""

        mapping = {
            "engagement_score": [
                ("code_quality", 0.1),
                ("testing", 0.05)
            ],
            "learning_velocity": [
                ("documentation", 0.1),
                ("architecture", 0.05)
            ],
            "success_rate": [
                ("code_quality", 0.15),
                ("performance", 0.10)
            ]
        }

        improvements = {}
        for metric, categories in mapping.items():
            metric_value = learning_metrics.get(metric, 0)
            if metric_value > 0:
                for category, weight in categories:
                    if category not in improvements:
                        improvements[category] = 0
                    improvements[category] += metric_value * weight

        return {k: min(v, 1.0) for k, v in improvements.items()}

    def _check_phase_advancement(self, learning_metrics: dict) -> dict:
        """Check if learning velocity supports phase advancement"""

        velocity = learning_metrics.get("learning_velocity", 0)
        current_phase = self.maturity_calculator.estimate_current_phase(
            self.project.overall_maturity
        )

        # High learning velocity may indicate readiness for next phase
        if velocity > 0.75:
            phases = ["discovery", "analysis", "design", "implementation"]
            current_idx = phases.index(current_phase)

            if current_idx < len(phases) - 1:
                return {
                    "advanced": True,
                    "new_phase": phases[current_idx + 1]
                }

        return {"advanced": False}

# Usage
tracker = LearningMaturityTracker("proj_123", "user_456")
result = tracker.track_interaction_and_update_maturity({
    "agent": "QualityController",
    "action": "analyze",
    "question": "How is code quality?",
    "result": {"quality_score": 0.85},
    "effectiveness_score": 0.85
})

print(f"Learning metrics: {result['learning_metrics']}")
print(f"Maturity improvements: {result['maturity_improvements']}")
if result['phase_advanced']:
    print(f"Phase advanced to: {result['new_phase']}")
```

### Pattern 3: User-Scoped Orchestration with Learning Context

**Use Case:** Maintain per-user orchestrators with learning history.

**Libraries:** socratic-core, socratic-learning

```python
from socratic_system.orchestration import OrchestratorService
from socratic_learning.tracking import Session, InteractionLogger
from socratic_learning.analytics import LearningEngine
from socratic_learning.analytics.learning_engine import UserProfile

class UserContextOrchestrator:
    """Per-user orchestrator with learning-driven personalization"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.orchestrator = OrchestratorService.get_orchestrator(user_id)
        self.session = Session(user_id=user_id)
        self.learning_logger = InteractionLogger()
        self.learning_engine = LearningEngine()

    def process_request_with_personalization(self, request: dict) -> dict:
        """Process request with learning-based personalization"""

        # Get user's learning profile
        profile = self._build_user_profile()

        # Adjust request parameters based on profile
        personalized_request = self._personalize_request(request, profile)

        # Execute with orchestrator
        result = self.orchestrator.process_request(personalized_request)

        # Log interaction for future personalization
        from socratic_learning.core import Interaction
        interaction = Interaction(
            session_id=self.session.session_id,
            user_id=self.user_id,
            agent=request["agent"],
            action=request["action"],
            question=request.get("parameters", {}).get("query", ""),
            response=result.get("result", {}),
            effectiveness_score=0.8 if result["status"] == "success" else 0.2,
            timestamp=result["metadata"]["timestamp"]
        )

        self.session.add_interaction(interaction)
        self.learning_logger.log_interaction(interaction)

        # Enhance result with personalization metadata
        result["personalization"] = {
            "user_level": profile.experience_level,
            "engagement_score": profile.overall_response_quality,
            "topics_explored": profile.topics_explored
        }

        return result

    def _build_user_profile(self) -> UserProfile:
        """Build user profile from interaction history"""

        interactions = self.learning_logger.get_interactions(
            user_id=self.user_id
        )

        if not interactions:
            # Default profile for new users
            return UserProfile(
                user_id=self.user_id,
                total_questions_asked=0,
                total_answered_well=0,
                overall_response_quality=0.5,
                topics_explored=0,
                projects_completed=0,
                topic_interactions=[]
            )

        # Build from history
        topics = list(set(i.agent for i in interactions))
        answered_well = sum(
            1 for i in interactions if i.effectiveness_score > 0.7
        )

        return UserProfile(
            user_id=self.user_id,
            total_questions_asked=len(interactions),
            total_answered_well=answered_well,
            overall_response_quality=sum(
                i.effectiveness_score for i in interactions
            ) / len(interactions),
            topics_explored=len(topics),
            projects_completed=len(set(
                i.metadata.get("project_id") for i in interactions
                if i.metadata.get("project_id")
            )),
            topic_interactions=topics
        )

    def _personalize_request(self, request: dict, profile: UserProfile) -> dict:
        """Adjust request based on user profile"""

        personalized = request.copy()

        # Get personalization hints
        metrics = self.learning_engine.calculate_learning_metrics(profile)
        hints = self.learning_engine.get_personalization_hints(profile, metrics)

        # Apply hints to parameters
        if profile.experience_level == "beginner":
            personalized["parameters"] = {
                **request.get("parameters", {}),
                "depth": "shallow",
                "include_examples": True,
                "step_by_step": True
            }
        elif profile.experience_level == "advanced":
            personalized["parameters"] = {
                **request.get("parameters", {}),
                "depth": "thorough",
                "include_edge_cases": True,
                "performance_focus": True
            }

        personalized["context"] = {
            **request.get("context", {}),
            "user_profile": {
                "experience_level": profile.experience_level,
                "topics_explored": profile.topics_explored,
                "success_rate": metrics["success_rate"]
            }
        }

        return personalized

# Usage
user_orch = UserContextOrchestrator("user_123")
result = user_orch.process_request_with_personalization({
    "agent": "SkillGenerator",
    "action": "generate",
    "project_id": "proj_456",
    "parameters": {
        "query": "Generate Python skills"
    }
})

print(f"Result: {result['status']}")
print(f"User level: {result['personalization']['user_level']}")
```

---

## Multi-Library Workflows

### Workflow 1: Complete Project Improvement Cycle

**Libraries:** orchestration, socrates-maturity, socratic-learning, socratic-agents

```python
"""
Complete cycle:
1. Analyze project (QualityController)
2. Track learning (socratic-learning)
3. Update maturity (socrates-maturity)
4. Generate skills (SkillGenerator)
5. Generate code (CodeGenerator)
6. Report improvements
"""

from socratic_system.orchestration import OrchestratorService
from socratic_learning.tracking import InteractionLogger, Session
from socrates_maturity import MaturityCalculator
from socratic_system.models import Project
import datetime

class ProjectImprovementCycle:
    def __init__(self, project_id: str, user_id: str):
        self.project = Project.load(project_id)
        self.user_id = user_id
        self.orchestrator = OrchestratorService.get_orchestrator(user_id)
        self.logger = InteractionLogger()
        self.session = Session(user_id=user_id)
        self.maturity_calc = MaturityCalculator()

    def execute_improvement_cycle(self) -> dict:
        """Execute one complete improvement cycle"""

        cycle_results = {
            "project_id": self.project.project_id,
            "start_maturity": self.project.overall_maturity,
            "phases": {}
        }

        # Phase 1: Quality Analysis
        analysis_result = self._phase_analysis()
        cycle_results["phases"]["analysis"] = analysis_result

        # Phase 2: Skill Generation
        if analysis_result["status"] == "success":
            skill_result = self._phase_skill_generation(analysis_result)
            cycle_results["phases"]["skills"] = skill_result

        # Phase 3: Code Generation
        if skill_result["status"] == "success":
            code_result = self._phase_code_generation(skill_result)
            cycle_results["phases"]["code"] = code_result

        # Phase 4: Report
        cycle_results["end_maturity"] = self.project.overall_maturity
        cycle_results["maturity_improvement"] = (
            cycle_results["end_maturity"] - cycle_results["start_maturity"]
        )

        return cycle_results

    def _phase_analysis(self) -> dict:
        """Analyze code quality"""
        result = self.orchestrator.process_request({
            "agent": "QualityController",
            "action": "analyze",
            "project_id": self.project.project_id
        })

        # Log interaction
        from socratic_learning.core import Interaction
        self._log_interaction(
            agent="QualityController",
            action="analyze",
            result=result,
            effectiveness=0.8 if result["status"] == "success" else 0.2
        )

        return result

    def _phase_skill_generation(self, analysis_result: dict) -> dict:
        """Generate skills for weak areas"""
        weak = self.maturity_calc.identify_weak_categories(
            self.project.category_scores
        )

        skills = {}
        for category in weak:
            result = self.orchestrator.process_request({
                "agent": "SkillGenerator",
                "action": "generate",
                "project_id": self.project.project_id,
                "parameters": {"focus_category": category}
            })

            self._log_interaction(
                agent="SkillGenerator",
                action="generate",
                result=result,
                effectiveness=0.8 if result["status"] == "success" else 0.2
            )

            skills[category] = result

        return {
            "status": "success" if all(s["status"] == "success" for s in skills.values()) else "partial",
            "skills": skills
        }

    def _phase_code_generation(self, skill_result: dict) -> dict:
        """Generate code based on skills"""
        result = self.orchestrator.process_request({
            "agent": "CodeGenerator",
            "action": "generate",
            "project_id": self.project.project_id,
            "parameters": {
                "skills": [
                    s.get("result", {}).get("skills", [])
                    for s in skill_result["skills"].values()
                ]
            }
        })

        self._log_interaction(
            agent="CodeGenerator",
            action="generate",
            result=result,
            effectiveness=0.7 if result["status"] == "success" else 0.2
        )

        return result

    def _log_interaction(self, agent: str, action: str, result: dict, effectiveness: float):
        """Helper to log interaction"""
        from socratic_learning.core import Interaction

        interaction = Interaction(
            session_id=self.session.session_id,
            user_id=self.user_id,
            agent=agent,
            action=action,
            question=f"{agent} - {action}",
            response=result.get("result", {}),
            effectiveness_score=effectiveness,
            timestamp=datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat()
        )

        self.session.add_interaction(interaction)
        self.logger.log_interaction(interaction)

# Usage
cycle = ProjectImprovementCycle("proj_123", "user_456")
results = cycle.execute_improvement_cycle()

print(f"Project: {results['project_id']}")
print(f"Maturity: {results['start_maturity']:.1%} → {results['end_maturity']:.1%}")
print(f"Improvement: +{results['maturity_improvement']:.1%}")
```

---

## Advanced Patterns

### Pattern: Parallel Agent Execution with Result Aggregation

**Use Case:** Execute multiple agents in parallel and aggregate results.

**Libraries:** orchestration, asyncio

```python
import asyncio
from socratic_system.orchestration import OrchestratorService

class ParallelAgentExecutor:
    """Execute multiple agents in parallel"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.orchestrator = OrchestratorService.get_orchestrator(user_id)

    async def execute_parallel(self, requests: list) -> dict:
        """Execute multiple requests in parallel"""

        tasks = [
            self._execute_request(req) for req in requests
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "requests": len(requests),
            "completed": len([r for r in results if not isinstance(r, Exception)]),
            "failed": len([r for r in results if isinstance(r, Exception)]),
            "results": results
        }

    async def _execute_request(self, request: dict) -> dict:
        """Execute single request (stub)"""
        # In real implementation, would use async client
        result = self.orchestrator.process_request(request)
        return result

# Usage
executor = ParallelAgentExecutor("user_123")
results = asyncio.run(executor.execute_parallel([
    {"agent": "QualityController", "action": "analyze", "project_id": "proj_1"},
    {"agent": "SkillGenerator", "action": "generate", "project_id": "proj_2"},
    {"agent": "CodeGenerator", "action": "generate", "project_id": "proj_3"}
]))

print(f"Executed {results['completed']}/{results['requests']} requests")
```

---

## Performance Patterns

### Pattern: Caching with TTL

**Use Case:** Cache expensive computations.

**Libraries:** socratic-core (utilities)

```python
from socratic_core.utils import TTLCache, cached

class CachedAnalytics:
    def __init__(self):
        self.result_cache = TTLCache(ttl_minutes=30)

    @cached(ttl_minutes=60)
    def analyze_project(self, project_id: str) -> dict:
        """Analyze project (cached for 60 minutes)"""
        # Expensive computation
        return {
            "project_id": project_id,
            "quality_score": 0.85,
            "analysis_time_ms": 1234
        }

# Usage
analytics = CachedAnalytics()

# First call: computes
result1 = analytics.analyze_project("proj_123")

# Second call within 60 min: returns cached
result2 = analytics.analyze_project("proj_123")

assert result1 == result2
```

---

## Error Handling Patterns

### Pattern: Graceful Degradation with Fallbacks

**Use Case:** Continue processing even if some agents fail.

```python
class RobustWorkflow:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def process_with_fallbacks(self, request: dict) -> dict:
        """Process with fallback agents if primary fails"""

        fallback_map = {
            "CodeGenerator": ["SkillGenerator"],
            "SkillGenerator": ["QualityController"],
            "QualityController": ["ArchitectureDesigner"]
        }

        primary_agent = request["agent"]
        result = self.orchestrator.process_request(request)

        # If primary failed, try fallback
        if result["status"] == "error":
            for fallback_agent in fallback_map.get(primary_agent, []):
                fallback_request = request.copy()
                fallback_request["agent"] = fallback_agent

                result = self.orchestrator.process_request(fallback_request)

                if result["status"] == "success":
                    result["used_fallback"] = True
                    result["fallback_agent"] = fallback_agent
                    break

        return result

# Usage
workflow = RobustWorkflow(orchestrator)
result = workflow.process_with_fallbacks({
    "agent": "CodeGenerator",
    "action": "generate",
    "project_id": "proj_123"
})

if result.get("used_fallback"):
    print(f"Used fallback agent: {result['fallback_agent']}")
```

---

## Related Documentation

- [Orchestration API](./ORCHESTRATION_API.md)
- [socratic-learning Integration](./SOCRATIC_LEARNING_INTEGRATION.md)
- [socrates-maturity Integration](./SOCRATES_MATURITY_INTEGRATION.md)
- [Configuration Guide](./CONFIGURATION_GUIDE.md)

