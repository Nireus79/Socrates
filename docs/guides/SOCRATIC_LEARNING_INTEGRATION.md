# Socratic Learning Integration Guide

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
8. [Common Issues](#common-issues)

---

## Overview

The **socratic-learning** library provides a pure, analytics-driven system for tracking and improving AI agent learning behaviors. It integrates with Socrates to:

- **Track interactions** between users and agents
- **Calculate learning metrics** for behavior analysis
- **Detect patterns** in user learning trajectories
- **Generate recommendations** for personalization
- **Store learning data** persistently

### Key Capabilities

| Capability | Purpose | Use Case |
|------------|---------|----------|
| **Interaction Tracking** | Record every user-agent interaction | Build learning history |
| **Learning Metrics** | Calculate engagement and velocity | Measure user progress |
| **Pattern Detection** | Identify user behavior patterns | Personalize guidance |
| **Recommendations** | Generate learning suggestions | Improve user outcomes |
| **Analytics** | Aggregate and analyze data | Report on effectiveness |

### Architecture

```
socratic-learning
├── Interaction Tracking (Sessions, interactions)
├── Learning Analytics (Metrics, patterns, recommendations)
├── Storage Backend (SQLite, custom backends)
└── Integrations (LangChain tools, OpenClaw skills)
```

---

## Installation

### Prerequisites

- Python 3.8+
- socratic-core >= 0.1.0

### From PyPI

```bash
pip install socratic-learning
```

### From Source

```bash
git clone https://github.com/anthropics/socratic-learning.git
cd socratic-learning
pip install -e .
```

### Verify Installation

```python
from socratic_learning import LearningEngine, InteractionLogger, Session

engine = LearningEngine()
logger = InteractionLogger()
session = Session(user_id="test_user")

print(f"LearningEngine initialized: {engine}")
print(f"InteractionLogger initialized: {logger}")
print(f"Session created: {session.session_id}")
```

---

## Core Concepts

### 1. Sessions and Interactions

A **Session** represents a user's work period. Each **Interaction** is a single agent-user exchange.

```python
from socratic_learning.tracking import Session
from socratic_learning.core import Interaction

# Create session
session = Session(user_id="user_123")

# Create interaction
interaction = Interaction(
    session_id=session.session_id,
    user_id="user_123",
    agent="QualityController",
    action="analyze",
    question="Is the code quality sufficient?",
    response="Code quality needs improvement in testing",
    effectiveness_score=0.85,
    timestamp="2026-03-24T10:30:45Z"
)

# Log interaction
session.add_interaction(interaction)
```

### 2. Learning Metrics

**Metrics** quantify learning progress and behavior.

```python
from socratic_learning.core import Metric

# Create metric
metric = Metric(
    metric_type="engagement",
    value=0.75,
    timestamp="2026-03-24T10:30:45Z",
    metadata={
        "questions_asked": 42,
        "questions_answered_well": 35,
        "topics_explored": 8
    }
)
```

### 3. Patterns

**Patterns** identify recurring behaviors in user interactions.

```python
from socratic_learning.core import Pattern

# Create pattern
pattern = Pattern(
    pattern_type="learning_velocity",
    confidence=0.92,
    description="User is progressing rapidly through basic topics",
    affected_interactions=45,
    recommendation="Advance to intermediate topics"
)
```

### 4. Recommendations

**Recommendations** suggest improvements based on detected patterns.

```python
from socratic_learning.core import Recommendation

# Create recommendation
recommendation = Recommendation(
    recommendation_type="personalization",
    priority="high",
    description="Focus on testing practices",
    affected_area="testing",
    expected_impact=0.85,
    implementation_hint="Generate testing-focused exercises"
)
```

### 5. Analytics Calculator

The **AnalyticsCalculator** aggregates metrics and generates reports.

```python
from socratic_learning.analytics import AnalyticsCalculator

calculator = AnalyticsCalculator(logger_instance=None)

# Calculate metrics
metrics = calculator.calculate_learning_metrics(
    interactions=session.interactions,
    depth="detailed"
)
print(f"Engagement: {metrics['engagement_score']}")
print(f"Learning Velocity: {metrics['learning_velocity']}")
print(f"Topics Explored: {metrics['topics_explored']}")
```

---

## Integration Patterns

### Pattern 1: Post-Agent-Execution Tracking

Log interactions immediately after agent execution.

```python
from socratic_system.orchestration import AgentOrchestrator
from socratic_learning.tracking import Session, InteractionLogger
from socratic_learning.core import Interaction

class TrackedOrchestrator:
    def __init__(self, orchestrator: AgentOrchestrator, user_id: str):
        self.orchestrator = orchestrator
        self.session = Session(user_id=user_id)
        self.logger = InteractionLogger()

    def process_request(self, request: dict) -> dict:
        # Execute agent request
        result = self.orchestrator.process_request(request)

        # Log interaction
        interaction = Interaction(
            session_id=self.session.session_id,
            user_id=self.session.user_id,
            agent=request["agent"],
            action=request["action"],
            question=request.get("parameters", {}).get("query", ""),
            response=result.get("result", {}),
            effectiveness_score=0.8 if result["status"] == "success" else 0.3,
            timestamp=result["metadata"]["timestamp"]
        )

        self.session.add_interaction(interaction)
        return result

# Usage
orchestrator = AgentOrchestrator(config)
tracked = TrackedOrchestrator(orchestrator, user_id="user_123")
result = tracked.process_request({
    "agent": "QualityController",
    "action": "analyze",
    "project_id": "proj_456"
})
```

### Pattern 2: Analytics in Event Handlers

Monitor agent performance through event listeners.

```python
from socratic_learning.analytics import AnalyticsCalculator
from socratic_core import EventType

class AnalyticsMonitor:
    def __init__(self, orchestrator, user_id: str):
        self.orchestrator = orchestrator
        self.calculator = AnalyticsCalculator()
        self.logger = InteractionLogger()
        self.session = Session(user_id=user_id)

        # Subscribe to events
        orchestrator.on_event(EventType.AGENT_COMPLETED, self.on_agent_completed)

    def on_agent_completed(self, event: dict):
        # Extract interaction data
        interaction = Interaction(
            session_id=self.session.session_id,
            user_id=self.session.user_id,
            agent=event["agent"],
            action="process",
            question="agent_execution",
            response=event.get("result", {}),
            effectiveness_score=1.0 if event["status"] == "success" else 0.0,
            timestamp=event["timestamp"]
        )

        self.session.add_interaction(interaction)

        # Calculate metrics
        metrics = self.calculator.calculate_learning_metrics(
            interactions=self.session.interactions
        )

        print(f"Current engagement: {metrics['engagement_score']}")

# Usage
monitor = AnalyticsMonitor(orchestrator, user_id="user_123")
orchestrator.process_request({...})
```

### Pattern 3: Learning-Driven Agent Selection

Use learning metrics to select which agents to activate.

```python
from socratic_learning.analytics import LearningEngine
from socratic_system.orchestration import OrchestratorService

class AdaptiveOrchestrator:
    def __init__(self, base_orchestrator, user_id: str):
        self.orchestrator = base_orchestrator
        self.learning_engine = LearningEngine()
        self.session = Session(user_id=user_id)
        self.user_id = user_id

    def process_adaptive_request(self, base_request: dict) -> dict:
        # Analyze current learning state
        metrics = self.learning_engine.calculate_learning_metrics(
            profile=self._build_profile()
        )

        # Adjust request based on learning level
        experience_level = metrics["experience_level"]

        adjusted_request = base_request.copy()
        if experience_level == "beginner":
            adjusted_request["parameters"] = {
                **base_request.get("parameters", {}),
                "depth": "shallow",
                "include_examples": True
            }
        elif experience_level == "advanced":
            adjusted_request["parameters"] = {
                **base_request.get("parameters", {}),
                "depth": "thorough",
                "include_advanced_patterns": True
            }

        return self.orchestrator.process_request(adjusted_request)

    def _build_profile(self):
        from socratic_learning.analytics.learning_engine import UserProfile

        return UserProfile(
            user_id=self.user_id,
            total_questions_asked=len(self.session.interactions),
            total_answered_well=sum(
                1 for i in self.session.interactions
                if i.effectiveness_score > 0.7
            ),
            overall_response_quality=sum(
                i.effectiveness_score for i in self.session.interactions
            ) / len(self.session.interactions) if self.session.interactions else 0.5,
            topics_explored=len(set(
                i.agent for i in self.session.interactions
            )),
            projects_completed=1,
            topic_interactions=[i.agent for i in self.session.interactions]
        )

# Usage
base_orchestrator = OrchestratorService.get_orchestrator("user_123")
adaptive = AdaptiveOrchestrator(base_orchestrator, "user_123")
result = adaptive.process_adaptive_request({
    "agent": "SkillGenerator",
    "action": "generate",
    "project_id": "proj_456"
})
```

### Pattern 4: Periodic Report Generation

Generate learning reports at scheduled intervals.

```python
from socratic_learning.analytics import AnalyticsCalculator
from socratic_learning.tracking import InteractionLogger
import datetime

class ReportGenerator:
    def __init__(self, logger: InteractionLogger):
        self.logger = logger
        self.calculator = AnalyticsCalculator()

    def generate_daily_report(self, user_id: str) -> dict:
        """Generate learning report for past 24 hours"""

        # Get interactions from past 24 hours
        since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        interactions = self.logger.get_interactions(
            user_id=user_id,
            since=since.isoformat()
        )

        # Calculate metrics
        metrics = self.calculator.calculate_learning_metrics(
            interactions=interactions
        )

        # Generate report
        report = {
            "user_id": user_id,
            "date": datetime.date.today().isoformat(),
            "metrics": metrics,
            "interactions_count": len(interactions),
            "key_patterns": self._identify_patterns(interactions),
            "recommendations": self._generate_recommendations(metrics)
        }

        return report

    def _identify_patterns(self, interactions):
        patterns = []
        if len(interactions) > 10:
            patterns.append("High activity level")

        success_rate = sum(
            1 for i in interactions if i.effectiveness_score > 0.7
        ) / len(interactions) if interactions else 0

        if success_rate > 0.8:
            patterns.append("High success rate")
        elif success_rate < 0.5:
            patterns.append("Struggling with concepts")

        return patterns

    def _generate_recommendations(self, metrics):
        recommendations = []

        if metrics["engagement_score"] < 0.3:
            recommendations.append("Increase practice frequency")

        if metrics["learning_velocity"] > 0.7:
            recommendations.append("Ready for advanced topics")

        return recommendations

# Usage
logger = InteractionLogger()
generator = ReportGenerator(logger)
report = generator.generate_daily_report("user_123")
print(f"Daily Report for {report['date']}")
print(f"Engagement: {report['metrics']['engagement_score']}")
print(f"Patterns: {report['key_patterns']}")
print(f"Recommendations: {report['recommendations']}")
```

---

## API Reference

### Session

```python
from socratic_learning.tracking import Session

session = Session(user_id: str)

# Properties
session.session_id      # Unique session identifier
session.user_id         # Associated user
session.created_at      # Session creation time
session.interactions    # List of interactions in session

# Methods
session.add_interaction(interaction: Interaction) -> None
session.get_interactions() -> List[Interaction]
```

### InteractionLogger

```python
from socratic_learning.tracking import InteractionLogger

logger = InteractionLogger()

# Methods
logger.log_interaction(interaction: Interaction) -> None
logger.get_interactions(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    since: Optional[str] = None
) -> List[Interaction]

logger.get_session(session_id: str) -> Session
logger.delete_session(session_id: str) -> None
```

### LearningEngine

```python
from socratic_learning.analytics import LearningEngine
from socratic_learning.analytics.learning_engine import UserProfile

engine = LearningEngine(logger_instance: Optional[Any] = None)

# Methods
profile = engine.build_user_profile(
    user_id: str,
    questions_asked: List[Dict[str, Any]],
    responses_quality: List[float],
    topic_interactions: List[str],
    projects_completed: int
) -> UserProfile

metrics = engine.calculate_learning_metrics(profile: UserProfile) -> Dict[str, Any]
# Returns: {
#     "engagement_score": float,
#     "learning_velocity": float,
#     "experience_level": str,  # "beginner", "intermediate", "advanced"
#     "success_rate": float,
#     "topics_explored": int,
#     "projects_completed": int
# }

hints = engine.get_personalization_hints(
    profile: UserProfile,
    metrics: Dict[str, Any]
) -> List[str]

score = engine.score_question_effectiveness(
    times_asked: int,
    times_answered_well: int
) -> float
```

### AnalyticsCalculator

```python
from socratic_learning.analytics import AnalyticsCalculator

calculator = AnalyticsCalculator(logger_instance: Optional[Any] = None)

# Methods
metrics = calculator.calculate_learning_metrics(
    interactions: List[Interaction],
    depth: str = "summary"  # "summary" or "detailed"
) -> Dict[str, Any]

report = calculator.generate_report(
    interactions: List[Interaction],
    format: str = "dict"  # "dict", "json", or "html"
) -> Union[Dict, str]
```

---

## Examples

### Example 1: Basic Integration Setup

```python
"""Setup socratic-learning in Socrates application"""

from socratic_system.orchestration import AgentOrchestrator
from socratic_learning.tracking import InteractionLogger, Session
from socratic_learning.analytics import AnalyticsCalculator
from socratic_core import SocratesConfig

# Initialize components
config = SocratesConfig(api_key="sk-...")
orchestrator = AgentOrchestrator(config)

logger = InteractionLogger()
calculator = AnalyticsCalculator(logger)

# Start session for user
user_id = "user_123"
session = Session(user_id=user_id)

# Process request and track
result = orchestrator.process_request({
    "agent": "QualityController",
    "action": "analyze",
    "project_id": "proj_456"
})

# Log interaction
from socratic_learning.core import Interaction
interaction = Interaction(
    session_id=session.session_id,
    user_id=user_id,
    agent="QualityController",
    action="analyze",
    question="Analyze code quality",
    response=result["result"],
    effectiveness_score=0.85,
    timestamp=result["metadata"]["timestamp"]
)

session.add_interaction(interaction)

# Calculate metrics
metrics = calculator.calculate_learning_metrics(
    interactions=[interaction],
    depth="detailed"
)

print(f"Engagement: {metrics['engagement_score']}")
print(f"Success Rate: {metrics['success_rate']}")
```

### Example 2: Persistent Storage

```python
"""Use SQLite storage for persistence"""

from socratic_learning.storage import SQLiteLearningStore
from socratic_learning.tracking import InteractionLogger
import os

# Create storage
db_path = "./learning_data.db"
store = SQLiteLearningStore(db_path=db_path)

# Create logger with storage
logger = InteractionLogger()
logger.set_storage(store)

# Log interactions (persisted to database)
for i in range(10):
    interaction = Interaction(
        session_id="sess_123",
        user_id="user_456",
        agent="QualityController",
        action="analyze",
        question=f"Question {i+1}",
        response={"quality_score": 0.7 + i*0.02},
        effectiveness_score=0.7 + i*0.02,
        timestamp="2026-03-24T10:00:00Z"
    )
    logger.log_interaction(interaction)

# Retrieve later
stored_interactions = logger.get_interactions(user_id="user_456")
print(f"Retrieved {len(stored_interactions)} interactions")
```

### Example 3: Custom Storage Backend

```python
"""Implement custom storage backend for specific requirements"""

from socratic_learning.storage import BaseLearningStore
from socratic_learning.core import Interaction
from socratic_learning.tracking import Session
from typing import List, Optional
import json

class RedisLearningStore(BaseLearningStore):
    """Redis-backed learning storage"""

    def __init__(self, redis_client):
        self.redis = redis_client

    def save_interaction(self, interaction: Interaction) -> None:
        """Store interaction in Redis"""
        key = f"interaction:{interaction.interaction_id}"
        self.redis.set(
            key,
            json.dumps(interaction.to_dict()),
            ex=86400*30  # 30 day expiry
        )

    def get_interactions(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Interaction]:
        """Retrieve interactions from Redis"""
        pattern = "interaction:*"
        keys = self.redis.keys(pattern)

        interactions = []
        for key in keys:
            data = json.loads(self.redis.get(key))
            if user_id and data.get("user_id") != user_id:
                continue
            if session_id and data.get("session_id") != session_id:
                continue
            interactions.append(Interaction.from_dict(data))

        return interactions

    def save_session(self, session: Session) -> None:
        """Store session in Redis"""
        key = f"session:{session.session_id}"
        self.redis.set(
            key,
            json.dumps(session.to_dict()),
            ex=86400*7  # 7 day expiry
        )

# Usage
import redis
redis_client = redis.Redis(host='localhost', port=6379)
store = RedisLearningStore(redis_client)
logger = InteractionLogger()
logger.set_storage(store)
```

---

## Best Practices

### 1. Always Include Effectiveness Scores

```python
# Good: Track effectiveness explicitly
interaction = Interaction(
    session_id=session.session_id,
    user_id=user_id,
    agent="QualityController",
    action="analyze",
    question="What improvements are needed?",
    response=result["result"],
    effectiveness_score=0.85,  # Explicit score
    timestamp=result["metadata"]["timestamp"]
)

# Avoid: Missing effectiveness data
interaction = Interaction(
    session_id=session.session_id,
    user_id=user_id,
    agent="QualityController",
    action="analyze",
    question="What improvements are needed?",
    response=result["result"],
    # Missing effectiveness_score
    timestamp=result["metadata"]["timestamp"]
)
```

### 2. Maintain Session Lifecycle

```python
# Good: Proper session management
sessions = {}

def get_or_create_session(user_id: str) -> Session:
    if user_id not in sessions:
        sessions[user_id] = Session(user_id=user_id)
    return sessions[user_id]

def process_user_request(user_id: str, request: dict):
    session = get_or_create_session(user_id)
    result = orchestrator.process_request(request)

    # Log with session
    interaction = Interaction(
        session_id=session.session_id,
        user_id=user_id,
        # ... other fields
    )
    session.add_interaction(interaction)

# Avoid: Creating new session per request
def process_request_bad(user_id: str, request: dict):
    session = Session(user_id=user_id)  # New session every time!
    result = orchestrator.process_request(request)
```

### 3. Use Appropriate Analytics Depth

```python
# Good: Summary metrics for high-throughput scenarios
metrics = calculator.calculate_learning_metrics(
    interactions=interactions,
    depth="summary"  # Faster, less detail
)

# Good: Detailed metrics for reporting
report = calculator.generate_report(
    interactions=interactions,
    depth="detailed"  # More comprehensive
)

# Avoid: Using detailed metrics for every request
for request in requests:
    # This is inefficient
    metrics = calculator.calculate_learning_metrics(
        interactions=all_interactions,
        depth="detailed"
    )
```

### 4. Batch Interaction Logging

```python
# Good: Batch multiple interactions
interactions = []
for result in agent_results:
    interaction = Interaction(
        session_id=session.session_id,
        user_id=user_id,
        # ... fields
    )
    interactions.append(interaction)

# Log all at once
for interaction in interactions:
    logger.log_interaction(interaction)

# Avoid: Logging one at a time
for result in agent_results:
    interaction = Interaction(...)
    logger.log_interaction(interaction)  # Inefficient
```

### 5. Handle Storage Failures Gracefully

```python
# Good: Fallback for storage errors
from socratic_learning.exceptions import StorageException

try:
    logger.log_interaction(interaction)
except StorageException as e:
    print(f"Failed to log interaction: {e}")
    # Fallback: keep in memory or queue for retry
    pending_interactions.append(interaction)

# Avoid: Crashing on storage error
logger.log_interaction(interaction)  # May crash
```

---

## Common Issues

### Issue 1: Sessions Not Persisting

**Problem:** Sessions created but lost when restarting application.

**Solution:** Use persistent storage backend.

```python
from socratic_learning.storage import SQLiteLearningStore

store = SQLiteLearningStore(db_path="./learning.db")
logger.set_storage(store)

# Sessions will now be persisted
session = Session(user_id="user_123")
logger.save_session(session)  # Explicit save
```

### Issue 2: Memory Growing with Interactions

**Problem:** Keeping all sessions in memory causes memory leak.

**Solution:** Implement session cleanup strategy.

```python
import datetime

class SessionManager:
    def __init__(self, logger: InteractionLogger):
        self.logger = logger
        self.sessions = {}
        self.ttl_minutes = 60

    def cleanup_expired_sessions(self):
        """Remove sessions older than TTL"""
        now = datetime.datetime.now(datetime.timezone.utc)
        expired = []

        for user_id, session in self.sessions.items():
            age = (now - session.created_at).total_seconds() / 60
            if age > self.ttl_minutes:
                # Save to storage before removing
                self.logger.save_session(session)
                expired.append(user_id)

        for user_id in expired:
            del self.sessions[user_id]

# Use in background task
manager = SessionManager(logger)
# Call periodically
manager.cleanup_expired_sessions()
```

### Issue 3: Ineffective Metrics

**Problem:** Metrics not reflecting actual learning progress.

**Solution:** Ensure comprehensive interaction data.

```python
# Good: Rich interaction data
interaction = Interaction(
    session_id=session.session_id,
    user_id=user_id,
    agent="QualityController",
    action="analyze",
    question="Analyze code quality",
    response={
        "quality_score": 0.75,
        "issues": [...],
        "recommendations": [...]
    },
    effectiveness_score=0.75,  # Reflects actual outcome
    metadata={
        "complexity": "medium",
        "domain": "code_quality",
        "feedback": "user_agreed"
    },
    timestamp=timestamp
)

# Avoid: Minimal data
interaction = Interaction(
    session_id=session.session_id,
    user_id=user_id,
    agent="QualityController",
    action="analyze",
    question="Analyze",
    response={"result": "done"},
    effectiveness_score=0.5,  # Unclear
    timestamp=timestamp
)
```

### Issue 4: Storage Performance

**Problem:** SQLite storage becomes slow with large datasets.

**Solution:** Implement data archival or use optimized backend.

```python
# Archive old interactions
def archive_old_interactions(logger: InteractionLogger, days: int = 90):
    import datetime
    cutoff = (
        datetime.datetime.now(datetime.timezone.utc) -
        datetime.timedelta(days=days)
    ).isoformat()

    old_interactions = logger.get_interactions(since=cutoff)

    # Save to archive storage
    archive_store = SQLiteLearningStore(db_path="./archive.db")
    for interaction in old_interactions:
        archive_store.save_interaction(interaction)

    # Remove from main storage
    for interaction in old_interactions:
        logger.delete_interaction(interaction.interaction_id)
```

---

## Related Documentation

- [Architecture Overview](../ARCHITECTURE.md)
- [Orchestration API](./ORCHESTRATION_API.md)
- [socratic-core API](./SOCRATIC_CORE_API.md)
- [Configuration Guide](./CONFIGURATION_GUIDE.md)

---

## Support

For issues, bugs, or feature requests:
- GitHub: https://github.com/anthropics/socratic-learning
- Documentation: https://socratic-learning.readthedocs.io
