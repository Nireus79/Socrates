# Phase 2: Service Layer Implementation

**Phase**: Phase 2 (Week 2)
**Duration**: 5 working days
**Start Date**: March 17, 2026
**Status**: READY TO START
**Reference**: NEXT_STEPS.md

---

## Objective

Implement the complete Service Layer with:
- Full BaseService pattern across all services
- ServiceOrchestrator wiring and coordination
- EventBus publish-subscribe implementation
- Inter-service communication
- Service initialization and lifecycle management
- Complete service testing

---

## Deliverables

By end of Phase 2:
- [ ] BaseService fully implemented in all 5 services
- [ ] ServiceOrchestrator wired with all services
- [ ] EventBus event handlers implemented
- [ ] Service-to-service communication working
- [ ] Initialization and shutdown sequence complete
- [ ] All service tests passing
- [ ] Ready for Phase 3 (Skill Generation)

---

## Phase 2 Daily Breakdown

### Day 1: Service Implementation & Wiring

**Morning**:
1. Complete each service's `__init__` method
2. Implement all abstract methods in each service
3. Add service-specific functionality

**Services to Complete**:

**AgentsService** (modules/agents/service.py)
```python
async def initialize(self):
    """Load all 20 agents"""
    # Scan modules/agents/agents/ for Agent subclasses
    # Dynamically import and instantiate each agent
    # Register with service

async def shutdown(self):
    """Cleanup agent resources"""

async def health_check(self):
    """Check agent service health"""
    return {
        "service": "agents",
        "agents_loaded": len(self.agents),
        "status": "healthy"
    }

async def execute_agent(self, agent_name, task, context):
    """Execute named agent with task and context"""
    agent = self.agents[agent_name]
    result = await agent.process_async({"task": task, **context})
    return result
```

**LearningService** (modules/learning/service.py)
```python
async def initialize(self):
    """Load learning engine"""
    from modules.learning.learning_engine import LearningEngine
    self.engine = LearningEngine()

async def track_interaction(self, agent_name, result):
    """Track agent interaction for learning"""
    self.engine.track_interaction(agent_name, result)

async def generate_skills(self, agent_name):
    """Generate skills for agent based on history"""
    data = self.engine.get_agent_data(agent_name)
    skills = self.engine.generate_skills(data)
    return skills
```

**FoundationService** (modules/foundation/service.py)
```python
async def initialize(self):
    """Initialize all foundation services"""
    from modules.foundation.llm_service import ClaudeClient
    from modules.foundation.database_service import ProjectDatabase

    self.llm = ClaudeClient()
    self.db = ProjectDatabase()
    self.cache = {}

async def get_llm_service(self):
    return self.llm

async def get_database_service(self):
    return self.db
```

**KnowledgeService** (modules/knowledge/service.py)
```python
async def initialize(self):
    """Initialize vector database"""
    from modules.knowledge.vector_db import VectorDB
    from modules.knowledge.knowledge_base import KnowledgeBase

    self.vector_db = VectorDB()
    self.kb = KnowledgeBase()

async def search_knowledge(self, query):
    """Semantic search in knowledge base"""
    results = self.vector_db.search(query)
    return results
```

**WorkflowService** (modules/workflow/service.py)
```python
async def initialize(self):
    """Initialize workflow components"""
    from modules.workflow.builder import WorkflowBuilder
    from modules.workflow.optimizer import WorkflowOptimizer

    self.builder = WorkflowBuilder()
    self.optimizer = WorkflowOptimizer()

async def create_workflow(self, definition):
    """Create workflow from definition"""
    workflow = self.builder.build(definition)
    return workflow

async def optimize_workflow(self, workflow_id):
    """Optimize workflow"""
    optimization = self.optimizer.optimize(workflow_id)
    return optimization
```

**AnalyticsService** (modules/analytics/service.py)
```python
async def initialize(self):
    """Initialize analytics engine"""
    from modules.analytics.calculator import AnalyticsCalculator

    self.calculator = AnalyticsCalculator()

async def get_system_metrics(self):
    """Get current system metrics"""
    return self.calculator.calculate_metrics()
```

**Afternoon**:
- [ ] Implement complete service lifecycle (initialize → run → shutdown)
- [ ] Add error handling and logging
- [ ] Create service factories for instantiation
- [ ] Write unit tests for each service

---

### Day 2: ServiceOrchestrator Implementation

**Morning**:
1. Complete ServiceOrchestrator with full wiring
2. Implement startup sequence
3. Implement shutdown sequence
4. Add health check aggregation

**Code to Add**:

```python
# core/orchestrator.py - Complete implementation

class ServiceOrchestrator:
    def __init__(self, config=None):
        self._services: Dict[str, BaseService] = {}
        self.event_bus = EventBus()
        self.config = config or {}
        self.running = False

    def register_service(self, service: BaseService):
        """Register service with orchestrator"""
        self._services[service.service_name] = service
        # Subscribe service to events it cares about
        self._subscribe_service_to_events(service)

    async def start(self):
        """Start all services in dependency order"""
        startup_order = [
            "foundation",    # No dependencies
            "knowledge",     # Depends on foundation
            "learning",      # Depends on foundation
            "agents",        # Depends on foundation, learning
            "workflow",      # Depends on foundation, agents
            "analytics",     # Depends on foundation
        ]

        for service_name in startup_order:
            service = self._services.get(service_name)
            if service:
                await service.start()
                print(f"Started {service_name} service")

        self.running = True
        await self.event_bus.publish(
            "system_started",
            "orchestrator",
            {"services": list(self._services.keys())}
        )

    async def stop(self):
        """Stop all services in reverse order"""
        shutdown_order = [
            "analytics",     # No dependents
            "workflow",      # Others don't depend on it
            "agents",        # Learning might need cleanup
            "learning",      # Knowledge doesn't depend on it
            "knowledge",     # Foundation doesn't depend on it
            "foundation",    # Stop last
        ]

        for service_name in shutdown_order:
            service = self._services.get(service_name)
            if service:
                await service.stop()
                print(f"Stopped {service_name} service")

        self.running = False

    async def get_service(self, service_name: str) -> BaseService:
        """Get service by name"""
        return self._services.get(service_name)

    async def call_service(
        self,
        service_name: str,
        method_name: str,
        *args,
        **kwargs
    ):
        """Call method on another service"""
        service = self._services.get(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found")

        method = getattr(service, method_name)
        if not method:
            raise ValueError(f"Method {method_name} not found on {service_name}")

        return await method(*args, **kwargs)

    async def health_check_all(self) -> Dict[str, Any]:
        """Check health of all services"""
        health = {}
        for name, service in self._services.items():
            try:
                service_health = await service.health_check()
                health[name] = {"status": "healthy", **service_health}
            except Exception as e:
                health[name] = {"status": "unhealthy", "error": str(e)}
        return health

    def _subscribe_service_to_events(self, service: BaseService):
        """Subscribe service to events based on its type"""
        event_map = {
            "agents": ["skill_generated", "agent_executed"],
            "learning": ["agent_executed"],
            "knowledge": ["knowledge_added"],
            "workflow": ["agent_executed"],
            "analytics": ["agent_executed", "skill_generated"],
        }

        events = event_map.get(service.service_name, [])
        for event in events:
            async def handler(event_obj, svc=service):
                await svc.on_event(event_obj)
            self.event_bus.subscribe(event, handler)
```

**Afternoon**:
- [ ] Implement startup/shutdown sequence
- [ ] Add dependency checking
- [ ] Implement health check aggregation
- [ ] Write integration tests

---

### Day 3: EventBus Implementation

**Morning**:
1. Complete EventBus with handlers
2. Implement event routing
3. Add event logging and history

**Code to Add**:

```python
# core/event_bus.py - Complete implementation

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._logger = logging.getLogger("event_bus")

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        self._logger.debug(f"Subscribed handler to {event_type}")

    async def publish(self, event_type: str, source: str, data: Dict):
        """Publish event to all subscribers"""
        event = Event(
            event_type=event_type,
            source_service=source,
            data=data
        )

        # Store in history
        self._event_history.append(event)
        self._logger.info(f"Event: {event_type} from {source}")

        # Notify subscribers
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                self._logger.error(f"Error in handler: {e}")

    def get_event_history(self, event_type=None, limit=100):
        """Get event history, optionally filtered"""
        events = self._event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]
```

**Key Events to Implement**:
- `agent_executed` - Agent finished execution
- `skill_generated` - New skill created
- `knowledge_added` - Knowledge item added
- `workflow_started` - Workflow execution started
- `workflow_completed` - Workflow execution completed
- `system_started` - All services started
- `system_stopped` - All services stopped

**Afternoon**:
- [ ] Implement event handlers in each service
- [ ] Test event publishing and subscription
- [ ] Add event filtering and routing
- [ ] Write EventBus tests

---

### Day 4: Inter-Service Communication

**Morning**:
1. Implement service-to-service calls
2. Test service dependencies
3. Implement fallback mechanisms

**Example Communication Patterns**:

```python
# Agents Service calling Learning Service
async def execute_agent(self, agent_name, task):
    result = await agent.process_async({"task": task})

    # Call learning service to track
    learning = await self.orchestrator.get_service("learning")
    await learning.track_interaction(agent_name, result)

    # Publish event for other services
    await self.orchestrator.event_bus.publish(
        "agent_executed",
        "agents",
        {"agent": agent_name, "result": result}
    )

    return result

# Learning Service generating skills
async def generate_skills(self, agent_name):
    # Get agent history
    agents = await self.orchestrator.get_service("agents")
    history = await agents.get_history(agent_name)

    # Generate skills
    skills = self.engine.generate_skills(history)

    # Publish event
    await self.orchestrator.event_bus.publish(
        "skill_generated",
        "learning",
        {"agent": agent_name, "skills": skills}
    )

    return skills
```

**Afternoon**:
- [ ] Implement all service-to-service calls
- [ ] Test service communication
- [ ] Add timeout and retry logic
- [ ] Write integration tests

---

### Day 5: Testing & Documentation

**Morning**:
1. Run full test suite
2. Fix any failures
3. Add integration tests
4. Update documentation

**Testing Checklist**:
```bash
# Unit tests for each service
pytest tests/unit/agents/ -v
pytest tests/unit/learning/ -v
pytest tests/unit/foundation/ -v
pytest tests/unit/knowledge/ -v
pytest tests/unit/workflow/ -v
pytest tests/unit/analytics/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v
```

**Documentation to Create**:
- [ ] Service API documentation
- [ ] Inter-service communication guide
- [ ] EventBus event catalog
- [ ] Troubleshooting guide

**Afternoon**:
- [ ] Fix any failing tests
- [ ] Verify all services healthy
- [ ] Create Phase 2 completion summary
- [ ] Commit Phase 2 work

---

## Key Files to Create/Update

### New Files
- `tests/integration/test_orchestrator.py` - Orchestrator tests
- `tests/integration/test_event_bus.py` - EventBus tests
- `tests/integration/test_service_communication.py` - Service interaction tests

### Files to Update
- `modules/agents/service.py` - Complete implementation
- `modules/learning/service.py` - Complete implementation
- `modules/foundation/service.py` - Complete implementation
- `modules/knowledge/service.py` - Complete implementation
- `modules/workflow/service.py` - Complete implementation
- `modules/analytics/service.py` - Complete implementation
- `core/orchestrator.py` - Complete wiring
- `core/event_bus.py` - Complete implementation
- `core/base_service.py` - May need minor updates

---

## Service Implementation Checklist

### AgentsService
- [ ] Load all 20 agents from modules/agents/agents/
- [ ] Implement agent execution
- [ ] Implement skill application
- [ ] Implement interaction tracking
- [ ] Add error handling

### LearningService
- [ ] Load learning engine
- [ ] Implement interaction tracking
- [ ] Implement skill generation
- [ ] Implement recommendations
- [ ] Add metrics collection

### FoundationService
- [ ] Initialize LLM service
- [ ] Initialize database service
- [ ] Initialize cache layer
- [ ] Provide access to other services
- [ ] Health checks

### KnowledgeService
- [ ] Load vector database
- [ ] Implement semantic search
- [ ] Implement knowledge management
- [ ] Version tracking
- [ ] RBAC support

### WorkflowService
- [ ] Load workflow builder
- [ ] Load workflow optimizer
- [ ] Implement DAG execution
- [ ] Implement cost tracking
- [ ] Performance optimization

### AnalyticsService
- [ ] Load analytics calculator
- [ ] Implement metrics collection
- [ ] Implement insights generation
- [ ] Dashboard data generation
- [ ] Performance monitoring

---

## Testing Strategy

### Unit Tests
- Each service's methods tested independently
- Mocked dependencies
- Error cases covered

### Integration Tests
- Services working together
- EventBus communication
- Orchestrator coordination

### End-to-End Tests
- Full workflow execution
- All services involved
- Real data flows

---

## Success Criteria

By end of Phase 2:
- ✅ All 5 services fully implemented
- ✅ ServiceOrchestrator wired and working
- ✅ EventBus publishing and subscribing
- ✅ Service-to-service communication working
- ✅ 150+ tests passing
- ✅ 0 new failures
- ✅ Ready for Phase 3

---

## Rollback Plan

If issues occur:
```bash
# Reset to Phase 1 complete
git reset --hard phase-1-complete
git clean -fd
```

---

## Expected Timeline

- **Day 1**: Service implementations (4-6 hours)
- **Day 2**: Orchestrator (4-6 hours)
- **Day 3**: EventBus (4-6 hours)
- **Day 4**: Inter-service communication (4-6 hours)
- **Day 5**: Testing & documentation (4-6 hours)

**Total**: 20-30 hours of focused development

---

## Next Phase Preview

Phase 3 will integrate SkillGeneratorAgent and implement:
- Skill generation from learned patterns
- Agent enhancement with skills
- Recommendation system
- Effectiveness tracking

---

**Status**: Ready to begin Phase 2
**Date**: March 17, 2026
**Prepared By**: Claude Haiku 4.5
