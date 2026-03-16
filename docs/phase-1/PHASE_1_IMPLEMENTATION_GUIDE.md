# Phase 1 Implementation Guide - Module Restructuring
## Week 1 of Socrates AI Modular Platform Migration

**Timeline**: 5 working days
**Objective**: Reorganize codebase into logical modules
**Expected Outcome**: Code reorganized, all imports working, tests passing
**No functional changes** - pure restructuring

---

## DAY 1: Planning & Backup

### Morning: Create Feature Branch & Backup

```bash
# Create feature branch
cd /c/Users/themi/PycharmProjects/Socrates
git checkout -b feature/modular-platform-v2
git commit --allow-empty -m "Start: Modular platform migration - Phase 1"

# Tag current state for easy rollback
git tag backup/monolithic-v1.3.3

# Create local backup
cp -r socratic_system socratic_system.backup.phase1
```

### Afternoon: Code Audit

Create a mapping document of what code goes where:

```python
# Create: MIGRATION_MAPPING.md

## Module Mapping

### modules/agents/
Source files:
- socratic_system/agents/base.py → modules/agents/base.py
- socratic_system/agents/*.py (17 agent files) → modules/agents/agents/

### modules/learning/
Source files:
- socratic_system/core/learning_engine.py → modules/learning/learning_engine.py
- socratic_system/agents/user_learning_agent.py → modules/learning/
- NEW: modules/learning/skill_generator.py (wrapper for SkillGeneratorAgent)

### modules/knowledge/
Source files:
- socratic_system/database/vector_db.py → modules/knowledge/vector_db.py
- socratic_system/orchestration/knowledge_base.py → modules/knowledge/knowledge_base.py

### modules/workflow/
Source files:
- socratic_system/core/workflow_builder.py → modules/workflow/builder.py
- socratic_system/core/workflow_executor.py → modules/workflow/executor.py
- socratic_system/core/workflow_optimizer.py → modules/workflow/optimizer.py

### modules/analytics/
Source files:
- socratic_system/core/analytics_calculator.py → modules/analytics/calculator.py

### modules/foundation/
Source files:
- socratic_system/clients/claude_client.py → modules/foundation/llm_service.py
- socratic_system/database/project_db.py → modules/foundation/database_service.py
- socratic_system/database/connection_pool.py → modules/foundation/connection_pool.py
- NEW: modules/foundation/cache_service.py

### core/
Source files:
- NEW: core/base_service.py
- NEW: core/orchestrator.py
- NEW: core/event_bus.py
- NEW: core/shared_models.py
```

---

## DAY 2: Create Directory Structure

### Morning: Create Full Directory Tree

```bash
# Create module directories
mkdir -p modules/{agents,learning,knowledge,workflow,analytics,foundation}/{agents,services,models}
mkdir -p core
mkdir -p interfaces/{api,cli}
mkdir -p config
mkdir -p tests/{unit,integration,e2e}/{agents,learning,knowledge,workflow,analytics}

# Create __init__.py files
touch core/__init__.py
touch modules/__init__.py
touch modules/agents/__init__.py
touch modules/learning/__init__.py
touch modules/knowledge/__init__.py
touch modules/workflow/__init__.py
touch modules/analytics/__init__.py
touch modules/foundation/__init__.py
touch interfaces/__init__.py
touch interfaces/api/__init__.py
touch interfaces/cli/__init__.py
touch config/__init__.py
```

### Afternoon: Create Core Service Files (Scaffolds)

**File 1: core/base_service.py**

```python
# core/base_service.py
"""Base service class for all Socrates AI services"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

class BaseService(ABC):
    """Abstract base class for all services"""

    SERVICE_NAME: str = None
    DEPENDENCIES: list = []

    def __init__(self, config: Dict[str, Any], shared_services: Optional[Dict] = None):
        if self.SERVICE_NAME is None:
            raise ValueError(f"{self.__class__.__name__} must define SERVICE_NAME")

        self.config = config
        self.shared_services = shared_services or {}
        self.logger = self._setup_logger()
        self.is_initialized = False
        self.last_request_time = None

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for this service"""
        logger = logging.getLogger(f"socrates.{self.SERVICE_NAME}")
        return logger

    async def initialize(self) -> None:
        """Initialize service (override in subclasses)"""
        self.logger.info(f"Initializing {self.SERVICE_NAME} service")
        self.is_initialized = True

    async def shutdown(self) -> None:
        """Shutdown service (override in subclasses)"""
        self.logger.info(f"Shutting down {self.SERVICE_NAME} service")

    async def health_check(self) -> Dict[str, Any]:
        """Return health status"""
        return {
            "service": self.SERVICE_NAME,
            "status": "healthy" if self.is_initialized else "not_initialized",
            "initialized": self.is_initialized,
            "last_request": self.last_request_time
        }

    def get_shared_service(self, service_name: str) -> 'BaseService':
        """Get another service"""
        if service_name not in self.shared_services:
            raise ValueError(f"Service '{service_name}' not found in shared services")
        return self.shared_services[service_name]

    def _check_dependencies(self) -> bool:
        """Check if all dependencies are available"""
        for dep in self.DEPENDENCIES:
            if dep not in self.shared_services:
                self.logger.error(f"Missing dependency: {dep}")
                return False
        return True

    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """Main processing method (implemented by subclasses)"""
        pass


# Preserve import path for backwards compatibility
__all__ = ['BaseService']
```

**File 2: core/orchestrator.py**

```python
# core/orchestrator.py
"""Service orchestrator for Socrates AI"""

from typing import Dict, Any, Type
import logging
from .base_service import BaseService

class ServiceOrchestrator:
    """Manages service lifecycle and inter-service communication"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.services: Dict[str, BaseService] = {}
        self.logger = logging.getLogger("socrates.orchestrator")

    async def register_service(self, service_class: Type[BaseService], service_config: Dict[str, Any]) -> None:
        """Register and initialize a service"""
        service_name = service_class.SERVICE_NAME

        # Check dependencies
        for dep in service_class.DEPENDENCIES:
            if dep not in self.services:
                raise ValueError(f"Cannot register {service_name}: missing dependency {dep}")

        # Create and initialize service
        service = service_class(service_config, self.services)
        await service.initialize()

        self.services[service_name] = service
        self.logger.info(f"Registered service: {service_name}")

    def get_service(self, service_name: str) -> BaseService:
        """Get a service"""
        if service_name not in self.services:
            raise ValueError(f"Service '{service_name}' not registered")
        return self.services[service_name]

    async def route_request(self, service_name: str, method: str, *args, **kwargs) -> Any:
        """Route a request to a service"""
        service = self.get_service(service_name)
        return await getattr(service, method)(*args, **kwargs)

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all services"""
        health = {}
        for name, service in self.services.items():
            health[name] = await service.health_check()
        return health

    async def shutdown_all(self) -> None:
        """Graceful shutdown of all services"""
        self.logger.info("Shutting down all services")
        for service in reversed(list(self.services.values())):
            await service.shutdown()


__all__ = ['ServiceOrchestrator']
```

**File 3: core/event_bus.py**

```python
# core/event_bus.py
"""Event bus for inter-service communication"""

from typing import Callable, Dict, List, Any
import asyncio
import logging

class EventBus:
    """Publish-Subscribe event system"""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger("socrates.event_bus")

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"Subscriber added for event: {event_type}")

    async def emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event"""
        if event_type not in self.subscribers:
            return

        tasks = []
        for callback in self.subscribers[event_type]:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(callback(data))
            else:
                callback(data)

        if tasks:
            await asyncio.gather(*tasks)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from an event"""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(callback)


__all__ = ['EventBus']
```

**File 4: core/shared_models.py**

```python
# core/shared_models.py
"""Shared data models used across services"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class InteractionStatus(str, Enum):
    """Status of an interaction"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"

@dataclass
class Interaction:
    """Represents an agent-LLM interaction"""
    interaction_id: str
    agent_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    status: InteractionStatus = InteractionStatus.SUCCESS
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Skill:
    """Represents an agent skill"""
    skill_id: str
    agent_name: str
    skill_name: str
    skill_type: str
    confidence: float = 0.0
    effectiveness: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Metric:
    """Represents a performance metric"""
    metric_id: str
    agent_name: str
    metric_type: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

__all__ = ['Interaction', 'Skill', 'Metric', 'InteractionStatus']
```

---

## DAY 3: Move Code to Modules (Part 1)

### Morning: Move Agent Code

```bash
# Move agent implementations
cp socratic_system/agents/base.py modules/agents/base.py
cp socratic_system/agents/*.py modules/agents/agents/

# Create agents module __init__.py
cat > modules/agents/__init__.py << 'EOF'
"""Agents module - specialized AI components"""

from .base import BaseAgent
from .agents.project_manager_agent import ProjectManagerAgent
from .agents.socratic_counselor_agent import SocraticCounselorAgent
# ... import all 17 agents

__all__ = [
    'BaseAgent',
    'ProjectManagerAgent',
    'SocraticCounselorAgent',
    # ... all agents
]
EOF
```

### Afternoon: Move Learning & Foundation Code

```bash
# Move learning code
cp socratic_system/core/learning_engine.py modules/learning/learning_engine.py
cp socratic_system/agents/user_learning_agent.py modules/learning/

# Move foundation code
cp socratic_system/clients/claude_client.py modules/foundation/llm_service.py
cp socratic_system/database/project_db.py modules/foundation/database_service.py
cp socratic_system/database/connection_pool.py modules/foundation/connection_pool.py

# Create foundation module __init__.py
cat > modules/foundation/__init__.py << 'EOF'
"""Foundation services - shared infrastructure"""

from .llm_service import LLMService
from .database_service import DatabaseService
from .connection_pool import ConnectionPool

__all__ = ['LLMService', 'DatabaseService', 'ConnectionPool']
EOF
```

---

## DAY 4: Move Code to Modules (Part 2) & Create Service Wrappers

### Morning: Move Knowledge & Workflow Code

```bash
# Move knowledge code
cp socratic_system/database/vector_db.py modules/knowledge/vector_db.py
cp socratic_system/orchestration/knowledge_base.py modules/knowledge/knowledge_base.py

# Move workflow code
cp socratic_system/core/workflow_builder.py modules/workflow/builder.py
cp socratic_system/core/workflow_executor.py modules/workflow/executor.py
cp socratic_system/core/workflow_optimizer.py modules/workflow/optimizer.py

# Move analytics code
cp socratic_system/core/analytics_calculator.py modules/analytics/calculator.py
```

### Afternoon: Create Service Wrapper Files

Create a `service.py` file for each module that wraps the existing code:

**File: modules/agents/service.py**

```python
# modules/agents/service.py
"""Agent service - manages all agents"""

from typing import Dict, Any, Optional
from core.base_service import BaseService
from .base import BaseAgent

class AgentService(BaseService):
    """Service for managing and executing agents"""

    SERVICE_NAME = "agents"
    DEPENDENCIES = ["llm", "database"]

    def __init__(self, config: Dict[str, Any], shared_services: Dict[str, Any]):
        super().__init__(config, shared_services)
        self.agents: Dict[str, BaseAgent] = {}

    async def initialize(self) -> None:
        """Initialize all agents"""
        await super().initialize()
        self._load_agents()
        self.logger.info(f"Loaded {len(self.agents)} agents")

    def _load_agents(self) -> None:
        """Load and instantiate all agents"""
        # Import all agent classes
        from .agents import (
            ProjectManagerAgent,
            SocraticCounselorAgent,
            CodeGeneratorAgent,
            # ... import all 17 agents
        )

        agent_classes = [
            ProjectManagerAgent,
            SocraticCounselorAgent,
            CodeGeneratorAgent,
            # ... all agents
        ]

        for agent_class in agent_classes:
            agent_name = agent_class.__name__
            agent = agent_class(self)
            self.agents[agent_name] = agent

    async def process(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")

        agent = self.agents[agent_name]
        self.last_request_time = datetime.now()

        try:
            result = await agent.process(input_data)
            return result
        except Exception as e:
            self.logger.error(f"Agent {agent_name} error: {e}")
            raise

    def get_agent(self, agent_name: str) -> BaseAgent:
        """Get an agent by name"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        return self.agents[agent_name]

    async def health_check(self) -> Dict[str, Any]:
        """Health status"""
        health = await super().health_check()
        health['agents_loaded'] = len(self.agents)
        return health
```

**File: modules/learning/service.py**

```python
# modules/learning/service.py
"""Learning service - tracks learning and generates skills"""

from typing import Dict, Any, Optional, List
from core.base_service import BaseService
from .learning_engine import LearningEngine
from .skill_generator import SkillGenerator
from datetime import datetime

class LearningService(BaseService):
    """Service for learning and skill generation"""

    SERVICE_NAME = "learning"
    DEPENDENCIES = ["database", "llm"]

    def __init__(self, config: Dict[str, Any], shared_services: Dict[str, Any]):
        super().__init__(config, shared_services)
        self.learning_engine = LearningEngine(config, shared_services)
        self.skill_generator = SkillGenerator(config, shared_services)

    async def initialize(self) -> None:
        """Initialize learning service"""
        await super().initialize()
        await self.learning_engine.initialize()
        await self.skill_generator.initialize()

    async def process(self, *args, **kwargs) -> Any:
        """Main process method (not used directly for learning service)"""
        raise NotImplementedError("Use specific methods like track_interaction()")

    async def track_interaction(self, agent_name: str, interaction_data: Dict[str, Any]) -> None:
        """Track an agent interaction"""
        await self.learning_engine.track_interaction(agent_name, interaction_data)

    async def generate_skills(self, agent_name: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate skills for an agent"""
        self.last_request_time = datetime.now()

        # Get maturity and learning data
        maturity = await self._get_maturity_data(agent_name)
        learning_data = await self._get_learning_data(agent_name)

        # Generate skills
        skills = await self.skill_generator.generate(
            agent_name=agent_name,
            maturity_data=maturity,
            learning_data=learning_data,
            context=context or {}
        )

        return skills

    async def get_recommendations(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get skill recommendations for an agent"""
        return await self.skill_generator.get_recommendations(agent_name)

    async def _get_maturity_data(self, agent_name: str) -> Dict[str, Any]:
        """Get maturity data for an agent"""
        # Query database for maturity
        return await self.learning_engine.get_maturity(agent_name)

    async def _get_learning_data(self, agent_name: str) -> Dict[str, Any]:
        """Get learning data for an agent"""
        # Aggregate learning metrics
        return await self.learning_engine.get_metrics(agent_name)

    async def health_check(self) -> Dict[str, Any]:
        """Health status"""
        health = await super().health_check()
        health['learning_engine'] = "ready"
        health['skill_generator'] = "ready"
        return health
```

Similarly create:
- `modules/knowledge/service.py`
- `modules/workflow/service.py`
- `modules/analytics/service.py`
- `modules/foundation/llm_service.py` (wrapper)
- `modules/foundation/database_service.py` (wrapper)

---

## DAY 5: Update Imports & Test

### Morning: Update All Imports

Create a script to update imports:

```bash
# Update imports in moved files
find modules/ -name "*.py" -type f -exec sed -i 's/from socratic_system\./from ../g' {} \;
find modules/ -name "*.py" -type f -exec sed -i 's/import socratic_system\./import ../g' {} \;

# Fix specific imports
# This needs manual review - check each module for correct import paths
```

### Afternoon: Run Tests

```bash
# Run all tests to find import errors
cd /c/Users/themi/PycharmProjects/Socrates
python -m pytest tests/ -v --tb=short

# Fix any import errors
# Re-run until all tests pass
python -m pytest tests/ -v
```

---

## Import Update Checklist

### For each moved file, check and update:

- [ ] Remove `from socratic_system.` and replace with relative imports
- [ ] Update agent imports in `modules/agents/base.py`
- [ ] Update agent imports in `modules/agents/__init__.py`
- [ ] Update learning engine imports in `modules/learning/`
- [ ] Update database imports in `modules/foundation/`
- [ ] Update knowledge base imports in `modules/knowledge/`
- [ ] Update workflow imports in `modules/workflow/`
- [ ] Update analytics imports in `modules/analytics/`

---

## Testing Checklist

```bash
# Test core imports
python -c "from core.base_service import BaseService; print('Core OK')"
python -c "from core.orchestrator import ServiceOrchestrator; print('Orchestrator OK')"
python -c "from core.event_bus import EventBus; print('EventBus OK')"

# Test module imports
python -c "from modules.agents import BaseAgent; print('Agents OK')"
python -c "from modules.learning import LearningService; print('Learning OK')"
python -c "from modules.knowledge import KnowledgeService; print('Knowledge OK')"
python -c "from modules.workflow import WorkflowService; print('Workflow OK')"
python -c "from modules.analytics import AnalyticsService; print('Analytics OK')"
python -c "from modules.foundation import LLMService, DatabaseService; print('Foundation OK')"

# Run full test suite
pytest tests/ -v --tb=short

# Check for import errors
pytest tests/ --collect-only
```

---

## Files Created/Modified Summary

### New Files Created
- ✅ `core/base_service.py` - Base service class
- ✅ `core/orchestrator.py` - Service orchestrator
- ✅ `core/event_bus.py` - Event bus
- ✅ `core/shared_models.py` - Shared data models
- ✅ `core/__init__.py` - Core module exports
- ✅ `modules/agents/service.py` - Agent service
- ✅ `modules/learning/service.py` - Learning service + Skill generation
- ✅ `modules/knowledge/service.py` - Knowledge service
- ✅ `modules/workflow/service.py` - Workflow service
- ✅ `modules/analytics/service.py` - Analytics service
- ✅ `modules/foundation/llm_service.py` - LLM service (wrapper)
- ✅ `modules/foundation/database_service.py` - Database service (wrapper)
- ✅ `modules/foundation/cache_service.py` - Cache service

### Files Moved
- ✅ `socratic_system/agents/` → `modules/agents/agents/`
- ✅ `socratic_system/clients/` → `modules/foundation/`
- ✅ `socratic_system/database/` → `modules/foundation/` + `modules/knowledge/`
- ✅ `socratic_system/core/learning_engine.py` → `modules/learning/`
- ✅ `socratic_system/core/workflow_*.py` → `modules/workflow/`
- ✅ `socratic_system/core/analytics_*.py` → `modules/analytics/`

### Files Modified
- ⚠️ All moved files - imports updated
- ⚠️ `socratic_system/orchestration/` - references to agents updated
- ⚠️ `socratic_system/ui/` - references updated for new imports
- ⚠️ Test files - imports updated

---

## Rollback Plan

If anything goes wrong, rollback is simple:

```bash
# Revert to previous state
git reset --hard backup/monolithic-v1.3.3

# Or restore backup
rm -rf modules
cp -r socratic_system.backup.phase1 socratic_system
```

---

## Success Criteria

After Phase 1:
- ✅ All code moved to correct module directories
- ✅ All imports working and consistent
- ✅ All tests passing (same as before)
- ✅ No functional changes (pure restructuring)
- ✅ Can run `python -m pytest tests/ -v` with 0 failures
- ✅ Git commit: "refactor: Restructure codebase into modules (Phase 1)"

---

## Next Steps

After Phase 1 completes successfully:
- Commit to git: `git commit -am "refactor: Complete Phase 1 - Module Restructuring"`
- Tag: `git tag phase-1-complete`
- Start Phase 2: Implement Service Layer

---

**Version**: 1.0
**Estimated Duration**: 5 working days
**Status**: Ready for Execution
