# COMPLETE SYSTEM ARCHITECTURE
## Total Redesign with Existing Agent Integration

---

## HIGH-LEVEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                     REACT FRONTEND                          │
│  (TypeScript, Redux, Tailwind CSS, Modern Components)       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Dashboard │ Projects │ Sessions │ Settings │ Admin  │  │
│  │ (with User Instructions Panel)                      │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ WebSocket / REST API / TypeScript
                     │
        ┌────────────▼────────────┐
        │    FASTAPI BACKEND      │
        │  (Python Type-Safe)     │
        ├────────────────────────┤
        │  Router Layer           │ (routing.py)
        │  ├─ /auth               │
        │  ├─ /projects           │
        │  ├─ /sessions           │
        │  ├─ /agents             │ ◄── Agents
        │  ├─ /code               │ ◄── Code editing
        │  ├─ /instructions       │ ◄── User rules
        │  └─ /ws                 │ ◄── WebSocket
        │                          │
        │  Service Layer           │ (services/)
        │  ├─ AuthService          │
        │  ├─ ProjectService       │
        │  ├─ SessionService       │
        │  ├─ AgentService         │ ◄── Coordinates agents
        │  ├─ InstructionService   │ ◄── Manages rules
        │  └─ QualityService       │ ◄── Validation
        │                          │
        │  Repository Layer        │ (repositories/)
        │  ├─ UserRepository       │
        │  ├─ ProjectRepository    │
        │  ├─ SessionRepository    │
        │  ├─ MessageRepository    │
        │  ├─ InstructionRepository│ ◄── User rules storage
        │  └─ AuditRepository      │
        │                          │
        │  Model Layer             │ (models/)
        │  ├─ User                 │
        │  ├─ Project              │
        │  ├─ Session              │
        │  ├─ Message              │
        │  ├─ UserInstruction      │ ◄── NEW
        │  └─ AuditLog             │
        └────────────┬─────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌────▼────┐   ┌────▼────┐   ┌─────▼──────┐
│PostgreSQL│   │ChromaDB  │   │  Agent     │
│          │   │(Vector)  │   │  System    │
│(Primary) │   │(RAG)     │   │            │
└──────────┘   └──────────┘   │  ┌──────┐ │
                              │  │ 9    │ │
                              │  │Core  │ │
                              │  │Agents│ │
                              │  └──┬───┘ │
                              │     │     │
                              │  ┌──▼───┐ │
                              │  │QA    │ │
                              │  │Valid │ │
                              │  │ator  │ │
                              │  └──────┘ │
                              │           │
                              │  ┌──────┐ │
                              │  │Code  │ │
                              │  │Editor│ │
                              │  └──────┘ │
                              └───────────┘
```

---

## LAYER-BY-LAYER BREAKDOWN

### 1. PRESENTATION LAYER (Frontend - React)

**Responsibilities:**
- User interface rendering
- User input collection
- State management (Redux)
- Real-time updates (WebSocket)
- Error display

**Key Components:**
```
frontend/src/
├── pages/
│   ├── Dashboard.tsx
│   ├── Projects.tsx
│   ├── Sessions.tsx
│   ├── CodeEditor.tsx
│   ├── Settings.tsx
│   └── Admin.tsx (User Instructions Panel)
│
├── components/
│   ├── navigation/
│   ├── forms/
│   ├── panels/ ◄── Instructions Panel
│   ├── modals/
│   └── common/
│
├── redux/
│   ├── store.ts
│   ├── slices/
│   │   ├── authSlice.ts
│   │   ├── projectSlice.ts
│   │   ├── sessionSlice.ts
│   │   ├── instructionSlice.ts ◄── User rules
│   │   └── uiSlice.ts
│   └── middleware/
│
├── services/
│   └── api.ts (Axios instance)
│
└── styles/
    └── tailwind.config.js
```

**User Instructions Panel:**
- Text area for entering rules
- Rule validation
- Save/cancel buttons
- Live preview of rules
- Rule history

---

### 2. API LAYER (FastAPI)

**Responsibilities:**
- HTTP request handling
- Request validation (Pydantic)
- Response formatting
- Error handling
- WebSocket management

**Structure:**
```
backend/src/
├── main.py ◄── FastAPI app creation
│
├── routers/
│   ├── auth.py
│   ├── projects.py
│   ├── sessions.py
│   ├── agents.py ◄── Agent endpoints
│   ├── code.py ◄── Code editing endpoints
│   ├── instructions.py ◄── User rules endpoints
│   └── websocket.py
│
├── schemas/
│   ├── user.py
│   ├── project.py
│   ├── session.py
│   ├── message.py
│   ├── instruction.py ◄── NEW
│   └── responses.py
│
└── middleware/
    ├── auth.py
    ├── error_handler.py
    └── logging.py
```

**Key Endpoints:**
```
Authentication:
  POST   /api/auth/register
  POST   /api/auth/login
  POST   /api/auth/logout
  GET    /api/auth/me

Projects:
  GET    /api/projects
  POST   /api/projects
  GET    /api/projects/{id}
  PUT    /api/projects/{id}
  DELETE /api/projects/{id}

Sessions:
  GET    /api/projects/{id}/sessions
  POST   /api/projects/{id}/sessions
  GET    /api/sessions/{id}
  POST   /api/sessions/{id}/messages
  POST   /api/sessions/{id}/toggle-mode

Agents:
  POST   /api/agents/route (route request to agent)
  GET    /api/agents/status
  GET    /api/agents/{id}/capabilities

Code Editing: ◄── NEW capabilities
  POST   /api/code/edit
  POST   /api/code/refactor
  POST   /api/code/debug
  POST   /api/code/fix-bugs

User Instructions: ◄── NEW endpoints
  GET    /api/instructions
  POST   /api/instructions
  PUT    /api/instructions/{id}
  DELETE /api/instructions/{id}
  GET    /api/instructions/validate

Real-time:
  WS     /ws/sessions/{id}
```

---

### 3. SERVICE LAYER

**Responsibilities:**
- Business logic
- Agent coordination
- User instruction enforcement
- Quality validation
- Data transformation

**Key Services:**
```
backend/src/services/
├── auth_service.py
├── project_service.py
├── session_service.py
├── agent_service.py ◄── Coordinates with 9 agents
├── instruction_service.py ◄── NEW - manages user rules
├── quality_service.py ◄── QualityAnalyzer integration
├── code_service.py ◄── CodeEditor integration
└── websocket_service.py
```

**Agent Service (Orchestrator Integration):**
```python
class AgentService:
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator

    async def route_request(self, agent_id, action, data, instructions=None):
        # 1. Apply user instructions as constraints
        if instructions:
            data['_user_instructions'] = instructions

        # 2. Route to agent
        result = self.orchestrator.route_request(agent_id, action, data)

        # 3. Validate through QualityAnalyzer
        validation = quality_analyzer.validate(result)

        # 4. Check against user instructions
        if not instruction_service.validate_against_rules(result, instructions):
            return {"error": "Result violates user instructions"}

        return result
```

**Instruction Service (NEW):**
```python
class InstructionService:
    async def create_instruction(self, user_id: str, rules: str):
        # Store user-defined rules
        instruction = UserInstruction(
            user_id=user_id,
            rules=rules,
            parsed_rules=self.parse_rules(rules),
            created_at=datetime.now()
        )
        return await repository.save(instruction)

    async def validate_against_rules(self, result, instructions):
        # Check if result violates any rules
        for rule in instructions.parsed_rules:
            if self.violates_rule(result, rule):
                return False
        return True
```

---

### 4. REPOSITORY LAYER

**Responsibilities:**
- Database access
- CRUD operations
- Query building
- Transaction management

**Repositories:**
```
backend/src/repositories/
├── base_repository.py ◄── Abstract base
├── user_repository.py
├── project_repository.py
├── session_repository.py
├── message_repository.py
├── instruction_repository.py ◄── NEW
├── audit_repository.py
└── database.py (connection management)
```

**Base Repository Pattern:**
```python
class BaseRepository:
    async def create(self, obj: T) -> T:
    async def get_by_id(self, id: str) -> Optional[T]:
    async def update(self, id: str, obj: T) -> T:
    async def delete(self, id: str) -> bool:
    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
    async def list_with_filter(self, **filters) -> List[T]:
```

---

### 5. DATA LAYER (PostgreSQL)

**Database Schema:**
```sql
-- Core tables
users
├── id (UUID, PK)
├── username (unique)
├── email (unique)
├── password_hash
└── created_at

projects
├── id (UUID, PK)
├── owner_id (FK users)
├── name
├── description
├── phase (planning/design/dev/testing)
└── created_at

sessions
├── id (UUID, PK)
├── project_id (FK projects)
├── type (socratic/chat/code_review)
├── status (active/completed/archived)
└── created_at

messages
├── id (UUID, PK)
├── session_id (FK sessions)
├── role (user/agent)
├── content
├── agent_id (which agent responded)
└── created_at

-- NEW: User instructions table
user_instructions
├── id (UUID, PK)
├── user_id (FK users)
├── project_id (FK projects, nullable)
├── rules (text)
├── parsed_rules (jsonb)
├── is_active (boolean)
└── created_at

-- Audit table
audit_logs
├── id (UUID, PK)
├── user_id (FK users)
├── action (create/update/delete)
├── resource_type
├── resource_id
├── changes (jsonb)
├── instructions_applied (jsonb)
└── created_at
```

---

### 6. AGENT SYSTEM INTEGRATION

**9 Core Agents (Preserved As-Is):**
```
src/agents/
├── orchestrator.py ◄── Central coordinator
├── base.py
├── user.py
├── project.py
├── socratic.py
├── code.py ◄── Extended with editing capabilities
├── context.py
├── document.py
├── services.py
└── monitor.py

NEW SUPPORTING MODULES:
├── code_validator.py ◄── Validation decorator
├── code_editor.py ◄── Code modification
└── question_analyzer.py ◄── QualityAnalyzer
```

**Agent Integration Flow:**
```
FastAPI Router
    ↓
AgentService
    ↓
InstructionService (apply user rules)
    ↓
AgentOrchestrator (route to agent)
    ↓
Specific Agent (execute action)
    ↓
QualityAnalyzer (validate result)
    ↓
InstructionService (verify compliance)
    ↓
Response to Frontend
```

---

### 7. QUALITY ASSURANCE LAYER

**Components:**
- QualityAnalyzer (existing)
- CodeValidator (existing)
- Instruction validator (NEW)
- Audit logging (NEW)

**Validation Flow:**
```
Input Request
    ↓
[Schema Validation] ◄── Pydantic
    ↓
[User Instruction Check] ◄── NEW
    ↓
[Agent Processing]
    ↓
[QualityAnalyzer Validation]
    ↓
[Instruction Compliance Check] ◄── NEW
    ↓
[Audit Logging]
    ↓
Response
```

---

## DATA FLOW EXAMPLES

### Example 1: Socratic Questioning

```
1. User enters question in UI
2. Frontend sends POST /api/agents/route
3. AgentService receives request
4. InstructionService applies user rules
5. AgentOrchestrator routes to SocraticCounselorAgent
6. Agent generates response
7. QualityAnalyzer validates response
8. InstructionService verifies compliance
9. Response sent to Frontend
10. Frontend updates Redux state
11. UI re-renders with response
12. Audit log created
```

### Example 2: Code Editing with User Rules

```
1. User requests code refactoring
2. Frontend sends POST /api/code/refactor
3. AgentService receives request
4. InstructionService retrieves user rules:
   - "Always include tests"
   - "Maintain backward compatibility"
   - "Document breaking changes"
5. CodeService calls CodeEditor.refactor_code()
6. CodeValidator validates suggestion
7. InstructionService checks against rules:
   ✓ Includes test suggestions
   ✓ No breaking changes detected
   ✓ Documentation generated
8. Response sent to Frontend
9. Frontend displays refactored code and suggestions
10. Audit log created with rules applied
```

### Example 3: User Instruction Enforcement

```
1. User creates instruction: "Always require security review"
2. Instruction stored in database
3. Later, code change requested
4. InstructionService retrieves rules before processing
5. Rules passed to agent processing pipeline
6. Result checked: "Is security review required?"
7. If missing: Request rejected with message
8. User informed: "This violates your instruction: ..."
9. Audit logged: "Instruction enforcement: Rejected"
```

---

## COMMUNICATION PATTERNS

### REST (Request/Response)
```
Frontend ←→ FastAPI Router ←→ Service ←→ Agent ←→ Response
(HTTP, JSON, Pydantic validation)
```

### WebSocket (Real-time)
```
Frontend ←→ WebSocket Handler ←→ Session Manager ←→ Agent Updates
(bi-directional, streaming)
```

### Internal (Service to Agent)
```
AgentService → AgentOrchestrator → Specific Agent → Result
(in-process, same Python runtime)
```

---

## ERROR HANDLING STRATEGY

**HTTP Errors:**
```python
400: Bad Request (validation error)
401: Unauthorized (auth failed)
403: Forbidden (instruction violation)
404: Not Found
500: Server Error
503: Service Unavailable
```

**Application Errors:**
```python
ValidationError ◄── Input validation failed
AuthenticationError ◄── Login failed
AuthorizationError ◄── User lacks permission
InstructionViolationError ◄── NEW - Violates rules
AgentError ◄── Agent processing failed
DatabaseError ◄── Database operation failed
```

---

## SECURITY ARCHITECTURE

**Authentication:**
- JWT tokens (from login)
- Token refresh logic
- Logout invalidation

**Authorization:**
- Role-based (admin, user, viewer)
- Project-level access
- Instruction-level constraints

**Data Protection:**
- Password hashing (bcrypt)
- API key encryption
- Audit logging
- Instruction enforcement

---

## CACHING STRATEGY

**Redis (Optional but Recommended):**
- User sessions
- Project metadata
- Agent status
- Instruction cache

**In-Memory:**
- Agent capabilities
- Service configuration
- QualityAnalyzer patterns

---

## MONITORING & OBSERVABILITY

**Logging:**
- Request/response logging
- Agent execution logging
- Error logging
- Audit logging (rule enforcement)

**Metrics:**
- Request count
- Response time
- Error rate
- Agent success rate
- Instruction violations

**Tracing:**
- Request IDs
- Agent call chains
- Performance profiling

---

## NEXT: Read 02_PROJECT_SETUP.md for implementation details
