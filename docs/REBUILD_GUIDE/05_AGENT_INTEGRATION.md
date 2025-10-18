# AGENT SYSTEM INTEGRATION
## Coordinating 9 Existing Agents with FastAPI Backend

---

## INTEGRATION OVERVIEW

The existing 9-agent system is preserved as-is and integrated into the FastAPI backend through a clean adapter layer.

```
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Routers                           │
│  /api/agents, /api/code, /api/sessions, etc                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Requests
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   AgentService                              │
│  (Route requests, apply instructions, validate results)     │
└────────────────────┬────────────────────────────────────────┘
                     │ Call with data
                     │
┌────────────────────▼────────────────────────────────────────┐
│              AgentOrchestrator                               │
│  (Route by agent_id or capability)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┬──────────────────┐
        │                         │                  │
        ▼                         ▼                  ▼
   ┌─────────┐  ┌──────────┐  ┌────────────┐   [More agents...]
   │ User    │  │ Project  │  │ Socratic   │
   │ Manager │  │ Manager  │  │ Counselor  │
   └─────────┘  └──────────┘  └────────────┘
        │             │              │
        └─────────────┴──────────────┘
                │ All agents return data
                ▼
        ┌──────────────────┐
        │ QualityAnalyzer  │ (Validation)
        └──────────────────┘
                │
        ┌───────▼──────────┐
        │ InstructionService
        │ (Check compliance)
        └──────────────────┘
                │
        ┌───────▼──────────┐
        │ Response to Client
        └──────────────────┘
```

---

## AGENTS ARCHITECTURE (PRESERVED)

### 9 Core Agents

```python
# src/agents/orchestrator.py
class AgentOrchestrator:
    def __init__(self, services: ServiceContainer):
        self.services = services
        self.logger = services.logger

        # Initialize all 9 agents
        self.agents = {
            'user': UserManagerAgent(services),
            'project': ProjectManagerAgent(services),
            'socratic': SocraticCounselorAgent(services),
            'code': CodeGeneratorAgent(services),
            'context': ContextAnalyzerAgent(services),
            'document': DocumentProcessorAgent(services),
            'services': ServicesAgent(services),
            'monitor': SystemMonitorAgent(services),
            'optimizer': ArchitectureOptimizerAgent(services),  # NEW
        }

        self.agent_failures = {}  # Track failed initializations

    def route_request(self, agent_id: str, action: str,
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route request to specific agent

        Args:
            agent_id: One of 'user', 'project', 'socratic', 'code', etc
            action: Method name on agent (e.g., 'generate_code')
            data: Request data passed to agent

        Returns:
            Agent response with success/error status
        """
        if agent_id not in self.agents:
            return {
                'success': False,
                'error': f'Unknown agent: {agent_id}',
                'timestamp': datetime.utcnow().isoformat()
            }

        agent = self.agents[agent_id]
        if agent is None:
            return {
                'success': False,
                'error': f'Agent {agent_id} failed to initialize',
                'timestamp': datetime.utcnow().isoformat()
            }

        try:
            # Call agent method
            method = getattr(agent, f'_process_{action}', None)
            if method is None:
                method = getattr(agent, action, None)

            if method is None:
                return {
                    'success': False,
                    'error': f'Agent {agent_id} has no action {action}',
                    'timestamp': datetime.utcnow().isoformat()
                }

            result = method(data)
            self.logger.info(f"Agent {agent_id} completed action {action}")
            return result

        except Exception as e:
            self.logger.error(f"Agent {agent_id} error: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': agent_id,
                'timestamp': datetime.utcnow().isoformat()
            }

    def route_by_capability(self, capability: str,
                           data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find and route to agent with specific capability

        Example:
            capability='generate_code' → finds CodeGeneratorAgent
            capability='ask_questions' → finds SocraticCounselorAgent
        """
        for agent_id, agent in self.agents.items():
            if agent and hasattr(agent, 'capabilities'):
                if capability in agent.capabilities:
                    return self.route_request(agent_id, capability, data)

        return {
            'success': False,
            'error': f'No agent with capability: {capability}',
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {}
        for agent_id, agent in self.agents.items():
            if agent is None:
                status[agent_id] = 'FAILED'
            else:
                status[agent_id] = 'READY'
        return status
```

### Agent Base Class (Existing)

```python
# src/agents/base.py
class BaseAgent:
    """Abstract base class for all agents"""

    def __init__(self, services: ServiceContainer):
        self.services = services
        self.logger = services.logger
        self.db = services.database.session
        self.event_system = services.event_system

    def emit_event(self, event_name: str, data: Dict[str, Any]):
        """Emit system event"""
        self.event_system.emit(event_name, self.__class__.__name__, data)

    def log_action(self, action: str, data: Dict[str, Any]):
        """Log agent action"""
        self.logger.info(f"{self.__class__.__name__}.{action}: {data}")

    def handle_error(self, error_code: str, message: str) -> Dict[str, Any]:
        """Standard error response"""
        return {
            'success': False,
            'error_code': error_code,
            'message': message,
            'agent_id': self.__class__.__name__,
            'timestamp': datetime.utcnow().isoformat()
        }

    def handle_success(self, data: Any, message: str = "") -> Dict[str, Any]:
        """Standard success response"""
        return {
            'success': True,
            'message': message,
            'data': data,
            'agent_id': self.__class__.__name__,
            'timestamp': datetime.utcnow().isoformat()
        }
```

---

## INTEGRATION ADAPTER

### AgentService (Integration Point)

```python
# src/services/agent_service.py
class AgentService(BaseService):
    """
    Routes FastAPI requests to agents with instruction enforcement
    and quality validation
    """

    def __init__(self, services: ServiceContainer):
        super().__init__(services, services.logger)
        self.orchestrator = AgentOrchestrator(services)
        self.instruction_service = InstructionService(services)

    async def route_request(
        self,
        agent_id: str,
        action: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main integration point: Route request through instruction
        and quality validation pipeline

        Flow:
        1. Get user's active instructions
        2. Add instructions to request context
        3. Route to agent
        4. Validate result through QualityAnalyzer
        5. Check against user instructions
        6. Log to audit trail
        7. Return response
        """

        try:
            # Step 1: Get user instructions (if user_id provided)
            instructions = []
            project_id = data.get('project_id')

            if user_id:
                instructions = await self.instruction_service.get_user_instructions(
                    user_id=user_id,
                    project_id=project_id
                )
                self.logger.info(
                    f"User {user_id} has {len(instructions)} active instructions"
                )

            # Step 2: Add instructions to context
            if instructions:
                data['_user_instructions'] = instructions
                data['_instruction_rules'] = [
                    rule for inst in instructions for rule in inst.parsed_rules
                ]

            # Step 3: Route to agent
            self.logger.info(f"Routing to agent: {agent_id}, action: {action}")
            result = self.orchestrator.route_request(agent_id, action, data)

            if not result.get('success'):
                self._audit_log(user_id, agent_id, action, data, result)
                return result

            # Step 4: Validate quality
            quality_check = await self._validate_quality(result, instructions)
            if not quality_check['valid']:
                self.logger.warning(f"Quality check failed: {quality_check['reason']}")
                self._audit_log(user_id, agent_id, action, data, result)
                return self.handle_error("QUALITY_CHECK_FAILED", quality_check['reason'])

            # Step 5: Validate against user instructions
            if instructions:
                instruction_check = await self.instruction_service.validate_result(
                    result.get('data', {}),
                    instructions
                )

                if not instruction_check['valid']:
                    violations = instruction_check.get('violations', [])
                    violation_msgs = [v.get('reason', 'Unknown') for v in violations]
                    msg = f"Violates instructions: {'; '.join(violation_msgs)}"

                    self.logger.warning(msg)
                    self._audit_log(
                        user_id, agent_id, action, data,
                        {'success': False, 'error': msg}
                    )

                    return self.handle_error("INSTRUCTION_VIOLATION", msg)

            # Step 6: Log success
            self._audit_log(user_id, agent_id, action, data, result, success=True)

            self.logger.info(f"Agent {agent_id} action {action} completed successfully")
            return result

        except Exception as e:
            self.logger.exception(f"Agent routing error: {e}")
            return self.handle_error("AGENT_ERROR", str(e))

    async def _validate_quality(
        self,
        result: Dict[str, Any],
        instructions: List
    ) -> Dict[str, Any]:
        """
        Validate result using QualityAnalyzer

        Checks:
        - Suggestion quality
        - Bias detection
        - Code quality (if code result)
        """
        try:
            from src.agents.question_analyzer import QualityAnalyzer

            analyzer = QualityAnalyzer()

            # Analyze the result data
            result_data = str(result.get('data', ''))
            analysis = analyzer.analyze_suggestion(result_data)

            # Check quality thresholds
            if analysis.quality_score < 0.4:
                return {
                    'valid': False,
                    'reason': f"Quality score too low: {analysis.quality_score:.2f}"
                }

            # Check bias
            if analysis.bias_score > 0.7:
                return {
                    'valid': False,
                    'reason': f"Bias detected: {analysis.bias_score:.2f}"
                }

            return {'valid': True}

        except Exception as e:
            self.logger.warning(f"Quality check error (non-blocking): {e}")
            return {'valid': True}  # Don't block on quality check errors

    def _audit_log(self, user_id: str, agent_id: str, action: str,
                  request_data: Dict[str, Any],
                  response_data: Dict[str, Any],
                  success: bool = False):
        """Log action to audit trail"""
        try:
            from src.database.repositories import AuditRepository
            repo = AuditRepository(self.services.database.session)

            audit = AuditLog(
                user_id=user_id,
                agent_id=agent_id,
                action=action,
                request_data=request_data,
                response_data=response_data,
                success=success
            )
            repo.create(audit)
        except Exception as e:
            self.logger.error(f"Audit logging failed: {e}")
```

---

## ROUTER INTEGRATION

### Example: Agents Router

```python
# src/routers/agents.py
from fastapi import APIRouter, Depends, HTTPException
from src.services import AgentService
from src.core import get_services

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/route")
async def route_agent_request(
    request: AgentRequest,
    services: ServiceContainer = Depends(get_services)
):
    """
    Route request to agent

    Request format:
    {
        "agent_id": "code",
        "action": "generate_code",
        "data": {...},
        "user_id": "user_123"
    }
    """
    agent_service = AgentService(services)

    result = await agent_service.route_request(
        agent_id=request.agent_id,
        action=request.action,
        data=request.data,
        user_id=request.user_id
    )

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message'))

    return result['data']

@router.get("/status")
async def get_agent_status(
    services: ServiceContainer = Depends(get_services)
):
    """Get status of all agents"""
    orchestrator = AgentOrchestrator(services)
    return {
        "agents": orchestrator.get_agent_status(),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/{agent_id}/capabilities")
async def get_agent_capabilities(
    agent_id: str,
    services: ServiceContainer = Depends(get_services)
):
    """Get capabilities of specific agent"""
    orchestrator = AgentOrchestrator(services)

    if agent_id not in orchestrator.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    agent = orchestrator.agents[agent_id]
    if agent is None:
        raise HTTPException(status_code=503, detail=f"Agent {agent_id} not initialized")

    return {
        "agent_id": agent_id,
        "capabilities": getattr(agent, 'capabilities', []),
        "status": "ready"
    }
```

### Example: Code Router (Uses Agent)

```python
# src/routers/code.py
from fastapi import APIRouter, Depends, HTTPException
from src.schemas import CodeRequest
from src.services import AgentService
from src.core import get_services, require_authentication

router = APIRouter(prefix="/code", tags=["code"])

@router.post("/generate")
@require_authentication
async def generate_code(
    request: CodeRequest,
    current_user = Depends(get_current_user),
    services: ServiceContainer = Depends(get_services)
):
    """
    Generate code using CodeGeneratorAgent

    This is a convenience endpoint that routes to code agent
    """
    agent_service = AgentService(services)

    result = await agent_service.route_request(
        agent_id='code',
        action='generate_code',
        data=request.dict(),
        user_id=current_user.id
    )

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message'))

    return result['data']

@router.post("/refactor")
@require_authentication
async def refactor_code(
    request: CodeRefactorRequest,
    current_user = Depends(get_current_user),
    services: ServiceContainer = Depends(get_services)
):
    """Refactor code using extended CodeGeneratorAgent"""
    agent_service = AgentService(services)

    result = await agent_service.route_request(
        agent_id='code',
        action='refactor_code',
        data=request.dict(),
        user_id=current_user.id
    )

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message'))

    return result['data']

@router.post("/debug")
@require_authentication
async def debug_code(
    request: CodeDebugRequest,
    current_user = Depends(get_current_user),
    services: ServiceContainer = Depends(get_services)
):
    """Debug code using extended CodeGeneratorAgent"""
    agent_service = AgentService(services)

    result = await agent_service.route_request(
        agent_id='code',
        action='debug_code',
        data=request.dict(),
        user_id=current_user.id
    )

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message'))

    return result['data']

@router.post("/fix-bugs")
@require_authentication
async def fix_bugs(
    request: CodeFixRequest,
    current_user = Depends(get_current_user),
    services: ServiceContainer = Depends(get_services)
):
    """Fix bugs using extended CodeGeneratorAgent"""
    agent_service = AgentService(services)

    result = await agent_service.route_request(
        agent_id='code',
        action='fix_bugs',
        data=request.dict(),
        user_id=current_user.id
    )

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message'))

    return result['data']
```

---

## INTEGRATION DATA FLOW EXAMPLE

### User Asks Socratic Question

```
1. Frontend: POST /api/sessions/session-1/ask
   {
     "question": "How should I structure my API?",
     "project_id": "proj_123"
   }

2. Router (sessions.py):
   - Validates input
   - Gets current user from JWT
   - Calls agent_service.route_request()

3. AgentService:
   - Gets user instructions from database
   - Adds to request: data['_user_instructions'] = [...]
   - Calls orchestrator.route_request('socratic', 'ask_question', data)

4. Orchestrator:
   - Finds SocraticCounselorAgent instance
   - Calls agent._process_ask_question(data)

5. SocraticCounselorAgent:
   - Analyzes question
   - Calls Claude API
   - Generates Socratic response
   - Returns: {'success': true, 'data': {...}}

6. AgentService (continued):
   - Validates response quality with QualityAnalyzer
   - Validates against user instructions
   - Creates AuditLog entry
   - Returns result

7. Router:
   - Returns 200 with result data

8. Frontend:
   - Stores in Redux
   - Updates UI with Socratic response

9. WebSocket (optional):
   - Sends real-time update to any connected clients
```

---

## AGENT LIFECYCLE MANAGEMENT

### Graceful Degradation

```python
# src/agents/orchestrator.py
class AgentOrchestrator:
    def __init__(self, services: ServiceContainer):
        self.agents = {}
        self.agent_failures = {}

        # Try to initialize each agent
        agent_classes = [
            ('user', UserManagerAgent),
            ('project', ProjectManagerAgent),
            ('socratic', SocraticCounselorAgent),
            ('code', CodeGeneratorAgent),
            # ... other agents
        ]

        for agent_id, agent_class in agent_classes:
            try:
                self.agents[agent_id] = agent_class(services)
                self.logger.info(f"Initialized agent: {agent_id}")
            except Exception as e:
                self.agents[agent_id] = None
                self.agent_failures[agent_id] = str(e)
                self.logger.warning(f"Failed to initialize {agent_id}: {e}")
                # Continue - system degrades gracefully
```

### Health Monitoring

```python
# src/services/monitoring_service.py
class MonitoringService(BaseService):
    async def check_agent_health(self) -> Dict[str, Any]:
        """Check health of all agents"""
        health = {}

        for agent_id in self.orchestrator.agents.keys():
            try:
                # Quick health check
                result = self.orchestrator.route_request(
                    agent_id, 'health_check', {}
                )
                health[agent_id] = 'healthy' if result.get('success') else 'unhealthy'
            except Exception as e:
                health[agent_id] = 'error'

        return {'agents': health}
```

---

## TESTING AGENT INTEGRATION

### Test Agent with Mock Service

```python
# tests/test_agent_integration.py
import pytest
from src.services import AgentService
from tests.fixtures import mock_services

@pytest.mark.asyncio
async def test_agent_route_with_instructions(mock_services):
    """Test that agent respects user instructions"""
    agent_service = AgentService(mock_services)

    # Create mock instruction
    mock_instruction = MagicMock()
    mock_instruction.parsed_rules = [
        {'type': 'security', 'rule': 'Always use encryption'}
    ]

    mock_services.instruction_service.get_user_instructions.return_value = [
        mock_instruction
    ]

    # Route request
    result = await agent_service.route_request(
        agent_id='code',
        action='generate_code',
        data={'requirements': 'Create auth'},
        user_id='user_123'
    )

    # Verify instruction was retrieved
    mock_services.instruction_service.get_user_instructions.assert_called_once()
    assert result['success']
```

---

## DEPLOYMENT CONSIDERATIONS

### Environment Variables

```bash
# .env for agent configuration
SOCRATIC_AGENT_TIMEOUT=30  # Max time for agent to respond
SOCRATIC_AGENT_RETRY=3     # Retry failed agent calls
SOCRATIC_CLAUDE_API_KEY=sk-...  # API key for Claude
```

### Performance Tuning

```python
# src/core/config.py
class SystemConfig:
    # Agent configuration
    AGENT_TIMEOUT = 30  # seconds
    AGENT_RETRY_COUNT = 3
    AGENT_CACHE_TTL = 3600  # seconds

    # Quality checking
    MIN_QUALITY_SCORE = 0.5  # Block if below this
    MAX_BIAS_SCORE = 0.7     # Block if above this

    # Instruction validation
    ENFORCE_INSTRUCTIONS = True
    INSTRUCTION_CACHE_TTL = 300
```

---

## NEXT STEPS

1. Copy 9 agent implementations to `src/agents/`
2. Create `AgentOrchestrator` in `src/agents/orchestrator.py`
3. Implement `AgentService` in `src/services/agent_service.py`
4. Create routers that use `AgentService`
5. Write comprehensive tests for agent routing
6. Deploy and monitor agent health

**Proceed to 06_FRONTEND_STRUCTURE.md** for React component architecture
