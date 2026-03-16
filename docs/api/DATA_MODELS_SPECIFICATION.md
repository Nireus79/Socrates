# Data Models Specification
## Pydantic Models for Socrates AI Modular Platform

---

## DIRECTORY STRUCTURE

```
modules/
├── agents/models.py
├── learning/models.py
├── knowledge/models.py
├── workflow/models.py
├── analytics/models.py
└── foundation/models.py

core/
└── shared_models.py
```

---

## SHARED MODELS (core/shared_models.py)

```python
# core/shared_models.py
"""Shared data models used across all services"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid

# ============================================================================
# ENUMS
# ============================================================================

class InteractionStatus(str, Enum):
    """Status of an interaction"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"

class SkillType(str, Enum):
    """Type of skill"""
    ENHANCEMENT = "enhancement"
    OPTIMIZATION = "optimization"
    RECOVERY = "recovery"
    ANALYSIS = "analysis"
    SAFETY = "safety"

class WorkflowStatus(str, Enum):
    """Status of a workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class TaskStatus(str, Enum):
    """Status of a task within a workflow"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

# ============================================================================
# BASE MODELS
# ============================================================================

class TimestampedModel(BaseModel):
    """Base model with timestamps"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True

class IdentifiedModel(TimestampedModel):
    """Base model with ID and timestamps"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    class Config:
        orm_mode = True

# ============================================================================
# CORE MODELS
# ============================================================================

class Interaction(IdentifiedModel):
    """Represents an agent-LLM interaction"""
    agent_name: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    status: InteractionStatus = InteractionStatus.SUCCESS
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Skill(IdentifiedModel):
    """Represents an agent skill"""
    agent_name: str
    skill_name: str
    skill_type: SkillType
    confidence: float = Field(ge=0.0, le=1.0)
    effectiveness: float = Field(ge=0.0, le=1.0)
    description: str = ""
    last_applied: Optional[datetime] = None
    application_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Metric(IdentifiedModel):
    """Represents a performance metric"""
    agent_name: Optional[str] = None
    metric_type: str
    metric_name: str
    value: float
    unit: str = ""
    period: str = "instant"  # instant, hourly, daily, weekly
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Recommendation(IdentifiedModel):
    """Represents a recommendation"""
    agent_name: str
    title: str
    description: str
    suggested_action: str
    priority: str = Field(default="medium")  # high, medium, low
    confidence: float = Field(ge=0.0, le=1.0)
    expected_impact: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

```

---

## AGENT SERVICE MODELS (modules/agents/models.py)

```python
# modules/agents/models.py
"""Models for Agent Service"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.shared_models import IdentifiedModel, InteractionStatus

class ExecutionRequest(BaseModel):
    """Request to execute an agent"""
    input_data: Dict[str, Any]
    apply_skills: bool = True
    timeout_seconds: int = 300
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExecutionResult(BaseModel):
    """Result of agent execution"""
    execution_id: str
    agent_name: str
    status: InteractionStatus
    result: Dict[str, Any]
    duration_ms: float
    skills_applied: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentInfo(BaseModel):
    """Information about an agent"""
    name: str
    description: str
    category: str
    enabled: bool = True
    version: str
    dependencies: List[str] = Field(default_factory=list)
    current_skills: List[str] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)

class AgentSkillInfo(BaseModel):
    """Information about an agent's skill"""
    skill_id: str
    name: str
    skill_type: str
    confidence: float
    effectiveness: float
    last_applied: Optional[datetime] = None
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExecutionHistory(IdentifiedModel):
    """Historical record of agent execution"""
    agent_name: str
    execution_id: str
    status: InteractionStatus
    duration_ms: float
    input_size: int
    output_size: int
    skills_used: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    error_message: Optional[str] = None

```

---

## LEARNING SERVICE MODELS (modules/learning/models.py)

```python
# modules/learning/models.py
"""Models for Learning Service"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.shared_models import IdentifiedModel, SkillType

class TrackingRequest(BaseModel):
    """Request to track an interaction"""
    agent_name: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    status: str = "success"  # success, failure, partial
    duration_ms: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SkillGenerationRequest(BaseModel):
    """Request to generate skills"""
    force: bool = False
    context: Dict[str, Any] = Field(default_factory=dict)

class GeneratedSkill(BaseModel):
    """A generated skill"""
    skill_id: str
    name: str
    skill_type: SkillType
    confidence: float
    effectiveness: float
    description: str
    recommended_application: str  # immediate, next_execution, scheduled
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SkillGenerationResult(BaseModel):
    """Result of skill generation"""
    agent_name: str
    skills_generated: int
    skills: List[GeneratedSkill]
    generation_reason: str
    next_regeneration_in_hours: int
    generated_at: datetime

class SkillRecommendation(IdentifiedModel):
    """Recommendation for skill application"""
    agent_name: str
    title: str
    priority: str  # high, medium, low
    suggested_action: str
    expected_impact: str
    confidence: float

class AgentMetrics(BaseModel):
    """Metrics for an agent"""
    agent_name: str
    period: str
    total_executions: int
    success_rate: float
    avg_duration_ms: float
    success_count: int
    failure_count: int
    skill_effectiveness: Dict[str, float] = Field(default_factory=dict)
    trend: Dict[str, str] = Field(default_factory=dict)
    generated_at: datetime

class UserLearningProfile(BaseModel):
    """Learning profile for a user"""
    user_id: str
    total_interactions: int
    learning_style: Dict[str, Any] = Field(default_factory=dict)
    patterns: List[Dict[str, Any]] = Field(default_factory=list)
    weak_areas: List[Dict[str, Any]] = Field(default_factory=list)
    strengths: List[Dict[str, Any]] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)

class LearningStatus(BaseModel):
    """System-wide learning status"""
    total_tracked_interactions: int
    agents_with_skills: int
    total_skills_generated: int
    last_skill_generation: Optional[datetime] = None
    next_scheduled_generation: Optional[datetime] = None
    learning_engine_status: str  # healthy, degraded, offline
    skill_generator_status: str  # ready, processing, offline

```

---

## KNOWLEDGE SERVICE MODELS (modules/knowledge/models.py)

```python
# modules/knowledge/models.py
"""Models for Knowledge Service"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.shared_models import IdentifiedModel

class SearchRequest(BaseModel):
    """Request to search knowledge"""
    query: str
    top_k: int = 5
    filters: Dict[str, Any] = Field(default_factory=dict)
    include_content: bool = False

class SearchResult(BaseModel):
    """Single search result"""
    item_id: str
    title: str
    content_preview: str
    relevance_score: float
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

class SearchResults(BaseModel):
    """Results of knowledge search"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float

class KnowledgeItem(IdentifiedModel):
    """A knowledge item"""
    title: str
    content: str
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source: str = "internal"
    version: int = 1
    embedding_updated: Optional[datetime] = None
    access_stats: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AddItemsRequest(BaseModel):
    """Request to add knowledge items"""
    items: List[Dict[str, Any]]

class UpdateItemRequest(BaseModel):
    """Request to update a knowledge item"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class KnowledgeStats(BaseModel):
    """Statistics about the knowledge base"""
    total_items: int
    categories: Dict[str, int] = Field(default_factory=dict)
    total_embeddings: int
    embedding_model: str
    last_reindexed: Optional[datetime] = None
    search_index_size_mb: float
    avg_retrieval_time_ms: float

```

---

## WORKFLOW SERVICE MODELS (modules/workflow/models.py)

```python
# modules/workflow/models.py
"""Models for Workflow Service"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.shared_models import IdentifiedModel, WorkflowStatus, TaskStatus

class WorkflowTask(BaseModel):
    """Task within a workflow"""
    task_id: str
    agent_name: str
    input: Dict[str, Any]
    depends_on: List[str] = Field(default_factory=list)
    retry_count: int = 0
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowOptimization(BaseModel):
    """Optimization settings for a workflow"""
    enable: bool = True
    priority: str = "balanced"  # cost, speed, balanced
    parallelization: bool = True
    caching: bool = True

class CreateWorkflowRequest(BaseModel):
    """Request to create a workflow"""
    name: str
    description: Optional[str] = None
    tasks: List[WorkflowTask]
    optimization: WorkflowOptimization = Field(default_factory=WorkflowOptimization)

class WorkflowInfo(IdentifiedModel):
    """Information about a workflow"""
    workflow_id: str
    name: str
    description: Optional[str] = None
    tasks: List[WorkflowTask]
    task_count: int
    execution_count: int = 0
    last_executed: Optional[datetime] = None
    optimization: Dict[str, Any] = Field(default_factory=dict)

class ExecuteWorkflowRequest(BaseModel):
    """Request to execute a workflow"""
    input_data: Dict[str, Any]
    timeout_seconds: Optional[int] = None

class TaskResult(BaseModel):
    """Result of a task execution"""
    task_id: str
    status: TaskStatus
    duration_ms: float
    cost: str = "$0.00"
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: datetime

class WorkflowExecution(IdentifiedModel):
    """Execution of a workflow"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    actual_cost: str = "$0.00"
    tasks: List[TaskResult] = Field(default_factory=list)
    error_message: Optional[str] = None

class OptimizationResult(BaseModel):
    """Result of workflow optimization"""
    workflow_id: str
    original: Dict[str, Any]
    optimized: Dict[str, Any]
    savings: Dict[str, float]  # percentage improvements

class WorkflowList(BaseModel):
    """List of workflows"""
    total_workflows: int
    page: int
    per_page: int
    workflows: List[WorkflowInfo]

```

---

## ANALYTICS SERVICE MODELS (modules/analytics/models.py)

```python
# modules/analytics/models.py
"""Models for Analytics Service"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.shared_models import IdentifiedModel

class SystemMetrics(BaseModel):
    """System-wide metrics"""
    period: str
    timestamp: datetime
    metrics: Dict[str, Any] = {
        "total_interactions": 0,
        "total_workflows_executed": 0,
        "overall_success_rate": 0.0,
        "avg_response_time_ms": 0.0,
        "total_cost": "$0.00",
        "unique_users": 0,
        "unique_agents_used": 0
    }

class AgentMetricsEntry(BaseModel):
    """Metrics for a single agent"""
    agent_name: str
    executions: int
    success_rate: float
    avg_duration_ms: float
    total_cost: str
    skill_effectiveness: float

class AgentMetricsResponse(BaseModel):
    """Response with agent metrics"""
    period: str
    agents: List[AgentMetricsEntry]

class Insight(IdentifiedModel):
    """An insight about the system"""
    insight_id: str
    title: str
    description: str
    severity: str  # critical, warning, info, positive
    confidence: float
    recommendation: str
    focus_area: str  # agents, workflows, users, performance, costs
    generated_at: datetime

class InsightsResponse(BaseModel):
    """Response with insights"""
    insights: List[Insight]

class ChartData(BaseModel):
    """Data for a chart"""
    name: str
    data: List[Dict[str, Any]]

class DashboardData(BaseModel):
    """Dashboard data"""
    summary: Dict[str, Any]
    charts: Dict[str, List[Any]]
    insights: List[Insight] = Field(default_factory=list)
    generated_at: datetime

```

---

## FOUNDATION SERVICE MODELS (modules/foundation/models.py)

```python
# modules/foundation/models.py
"""Models for Foundation Services"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

class LLMConfig(BaseModel):
    """Configuration for LLM service"""
    provider: str  # anthropic, openai, google, ollama
    model: str
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout_seconds: int = 60

class LLMRequest(BaseModel):
    """Request to LLM service"""
    messages: List[Dict[str, str]]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout_seconds: Optional[int] = None

class LLMResponse(BaseModel):
    """Response from LLM"""
    content: str
    tokens_used: int
    cost: str
    model: str
    provider: str
    timestamp: datetime

class DatabaseConfig(BaseModel):
    """Configuration for database service"""
    type: str = "sqlite"
    path: str
    connection_pool_size: int = 10
    timeout_seconds: int = 30

class CacheConfig(BaseModel):
    """Configuration for cache service"""
    type: str = "redis"  # redis, memcached, in_memory
    host: str = "localhost"
    port: int = 6379
    ttl_seconds: int = 3600

class HealthStatus(BaseModel):
    """Health status of a service"""
    service: str
    status: str  # healthy, degraded, offline
    response_time_ms: Optional[float] = None
    last_checked: datetime

class SystemHealth(BaseModel):
    """Overall system health"""
    status: str  # healthy, degraded, offline
    timestamp: datetime
    services: Dict[str, HealthStatus]

class SystemInfo(BaseModel):
    """System information"""
    platform_version: str
    deployment_mode: str  # microservices, single_process
    uptime_seconds: int
    services_running: int
    database: Dict[str, Any]
    cache: Dict[str, Any]

class ConfigStatus(BaseModel):
    """Configuration status"""
    environment: str
    debug_mode: bool
    log_level: str
    services: Dict[str, Any]

```

---

## USAGE EXAMPLES

### Example 1: Using Shared Models

```python
from core.shared_models import Interaction, InteractionStatus, Skill, SkillType
from datetime import datetime

# Create an interaction
interaction = Interaction(
    agent_name="CodeGeneratorAgent",
    session_id="sess_abc123",
    user_id="user_123",
    input_data={"query": "Generate a Python function"},
    output_data={"code": "def func(): pass"},
    status=InteractionStatus.SUCCESS,
    duration_ms=2345
)

# Create a skill
skill = Skill(
    agent_name="CodeGeneratorAgent",
    skill_name="error_handling",
    skill_type=SkillType.ENHANCEMENT,
    confidence=0.92,
    effectiveness=0.87
)
```

### Example 2: Using Service Models

```python
from modules.agents.models import ExecutionRequest, ExecutionResult
from modules.learning.models import TrackingRequest

# Create execution request
request = ExecutionRequest(
    input_data={"query": "Generate code"},
    apply_skills=True,
    timeout_seconds=300
)

# Track interaction
tracking = TrackingRequest(
    agent_name="CodeGeneratorAgent",
    session_id="sess_abc123",
    input_data={"query": "Generate code"},
    output_data={"code": "..."},
    status="success",
    duration_ms=2345
)
```

### Example 3: Validation

```python
from pydantic import ValidationError
from modules.agents.models import ExecutionRequest

try:
    # This will fail - missing required field
    request = ExecutionRequest()
except ValidationError as e:
    print(f"Validation error: {e}")
    # {
    #   "input_data": ["field required"]
    # }
```

---

## MIGRATION FROM EXISTING MODELS

### Step 1: Update Imports

```python
# OLD
from socratic_system.models import Interaction

# NEW
from core.shared_models import Interaction
```

### Step 2: Update Validation

```python
# OLD
interaction = Interaction(...)
interaction.save()  # Manual persistence

# NEW
interaction = Interaction(...)
# Validation happens automatically
# Persist in service layer
await db_service.save(interaction)
```

### Step 3: API Response Serialization

```python
# OLD
return interaction.dict()

# NEW
return interaction.model_dump()  # Pydantic v2
# or
return interaction.dict()  # Pydantic v1 compatibility
```

---

## VALIDATION RULES

### Required Fields
- All required fields must be provided
- Defaults are provided where appropriate

### Type Validation
- String enums must match defined values
- Float ranges: 0.0-1.0 for confidence/effectiveness
- Positive numbers for durations and counts

### Custom Validators

```python
from pydantic import validator

class Metric(BaseModel):
    value: float
    unit: str

    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError('Value must be positive')
        return v
```

---

**Version**: 1.0
**Status**: Complete
**Total Models**: 50+
**Pydantic Version**: v2 (v1 compatible)
