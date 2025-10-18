# COMPLETE ACTION FLOW MAP
## User Actions → Agent Execution → Response

**This document maps every user interaction to agent execution and back**

---

## TABLE OF CONTENTS

1. Authentication Flows
2. Project Management Flows
3. Socratic Session Flows
4. Code Editing Flows
5. Settings & Instructions Flows
6. Real-time Flows

---

## 1. AUTHENTICATION FLOWS

### Flow 1.1: User Registration

```
UI ACTION: User fills registration form
│
├─ Input: {email, username, password, full_name}
│
└─→ Frontend: POST /api/auth/register
   │
   └─→ API Router: auth.register()
      │
      ├─ Validate input (Pydantic schema)
      ├─ Check duplicate email/username
      ├─ Hash password
      │
      └─→ AuthService.create_user()
         │
         └─→ UserRepository.create()
            │
            └─→ PostgreSQL: INSERT INTO users
               │
               └─→ Return: user object
         │
         ├─ Generate JWT token
         └─→ Return: {user, token, refresh_token}
   │
   └─→ Frontend Redux: setAuthUser(user)
      │
      └─→ UI: Redirect to Dashboard

RESPONSE: {"success": true, "user": {...}, "token": "..."}
```

### Flow 1.2: User Login

```
UI ACTION: User enters credentials
│
├─ Input: {email/username, password}
│
└─→ Frontend: POST /api/auth/login
   │
   └─→ AuthService.authenticate()
      │
      ├─ UserRepository.get_by_email()
      ├─ Verify password hash
      │
      └─→ Generate JWT token
         │
         └─→ AuditRepository.log({action: "login"})
   │
   └─→ Frontend Redux: setAuthUser(user)
      │
      └─→ UI: Dashboard

RESPONSE: {"success": true, "user": {...}, "token": "..."}
```

---

## 2. PROJECT MANAGEMENT FLOWS

### Flow 2.1: Create New Project

```
UI ACTION: User clicks "New Project" → fills form
│
├─ Input: {name, description, type}
│
└─→ Frontend: POST /api/projects
   │
   └─→ ProjectService.create_project()
      │
      ├─ ProjectRepository.create()
      │  └─→ PostgreSQL: INSERT INTO projects
      │
      ├─ Create initial session
      │  └─→ SessionRepository.create()
      │
      └─→ AuditRepository.log({action: "create_project"})
   │
   └─→ Frontend Redux: addProject(project)
      │
      └─→ UI: Navigate to project dashboard

RESPONSE: {
  "success": true,
  "project": {
    "id": "proj_123",
    "name": "...",
    "status": "planning",
    "created_at": "..."
  }
}
```

### Flow 2.2: List User Projects

```
UI ACTION: User navigates to Projects page
│
└─→ Frontend: GET /api/projects?skip=0&limit=20
   │
   └─→ ProjectService.list_projects()
      │
      └─→ ProjectRepository.get_by_owner()
         │
         └─→ PostgreSQL: SELECT * FROM projects
   │
   └─→ Frontend Redux: setProjects([...])
      │
      └─→ UI: Render projects list

RESPONSE: {
  "success": true,
  "projects": [...],
  "total": 5,
  "skip": 0,
  "limit": 20
}
```

---

## 3. SOCRATIC SESSION FLOWS

### Flow 3.1: Start Socratic Session

```
UI ACTION: User clicks "Start Socratic Mode"
│
├─ Input: {project_id}
│
└─→ Frontend: POST /api/sessions
   │
   └─→ SessionService.create_session()
      │
      ├─ SessionRepository.create()
      │  └─→ PostgreSQL: INSERT INTO sessions
      │
      ├─ InstructionService.get_user_instructions()
      │  └─→ Retrieve user rules for project
      │
      └─→ AuditRepository.log({
         action: "session_start",
         rules_applied: [...]
      })
   │
   └─→ Frontend Redux: setCurrentSession(session)
      │
      ├─ Connect WebSocket
      └─→ UI: Show Socratic interface

RESPONSE: {
  "success": true,
  "session": {
    "id": "sess_123",
    "type": "socratic",
    "project_id": "proj_456",
    "status": "active"
  }
}
```

### Flow 3.2: Ask Question in Socratic Mode

```
UI ACTION: User types question + clicks Send
│
├─ Input: {question_text}
│
└─→ Frontend: POST /api/sessions/{id}/messages
   │
   ├─ Store message in Redux (optimistic)
   └─→ API: POST with question
      │
      └─→ SessionService.handle_message()
         │
         ├─ MessageRepository.create({
            role: "user",
            content: question
         })
         │
         ├─ InstructionService.get_instructions()
         │
         └─→ AgentService.route_request()
            │
            ├─ Apply user instructions
            │  └─→ data['_user_instructions'] = rules
            │
            ├─ AgentOrchestrator.route_request()
            │  └─→ agent_id = 'socratic'
            │     action = 'generate_question'
            │
            ├─ SocraticCounselorAgent._generate_question()
            │  │
            │  ├─ QuestionQualityAnalyzer.analyze_question()
            │  │  └─→ Check for bias, coverage gaps
            │  │
            │  ├─ Call Claude API (via ClaudeService)
            │  │
            │  └─→ Generate follow-up questions
            │
            ├─ QualityAnalyzer.validate_result()
            │  └─→ Check against user rules
            │
            ├─ InstructionService.validate_result()
            │  └─→ Verify compliance
            │
            ├─ MessageRepository.create({
            │  role: "agent",
            │  content: response,
            │  agent_id: "socratic"
            │ })
            │
            └─→ AuditRepository.log({
               action: "socratic_question",
               quality_score: 0.85,
               rules_applied: 3
            })
   │
   └─→ WebSocket: Emit message to client
      │
      └─→ Frontend Redux: addMessage(response)
         │
         └─→ UI: Display response with quality indicators

RESPONSE (WebSocket): {
  "success": true,
  "message": {
    "id": "msg_789",
    "role": "agent",
    "content": "Based on your requirements...",
    "metadata": {
      "quality_score": 0.85,
      "bias_detected": false,
      "coverage_areas": ["security", "scalability", ...],
      "rules_applied": 3
    }
  }
}
```

### Flow 3.3: Toggle Chat Mode

```
UI ACTION: User clicks "Switch to Chat Mode"
│
├─ Input: {session_id}
│
└─→ Frontend: POST /api/sessions/{id}/toggle-mode
   │
   └─→ SessionService.toggle_mode()
      │
      ├─ SessionRepository.update(
         session_id,
         {mode: "chat"}
      )
      │
      ├─ InstructionService.get_instructions()
      │
      └─→ AuditRepository.log({
         action: "mode_toggle",
         from: "socratic",
         to: "chat",
         rules_applied: [...]
      })
   │
   └─→ Frontend Redux: updateSessionMode("chat")
      │
      └─→ UI: Switch to chat interface

RESPONSE: {
  "success": true,
  "session": {
    "id": "sess_123",
    "mode": "chat",
    "rules_applied": 3
  }
}
```

---

## 4. CODE EDITING FLOWS

### Flow 4.1: Request Code Refactoring

```
UI ACTION: User pastes code + selects "Refactor for Readability"
│
├─ Input: {code_text, refactoring_type}
│
└─→ Frontend: POST /api/code/refactor
   │
   └─→ CodeService.refactor_code()
      │
      ├─ InstructionService.get_instructions()
      │  └─→ Retrieve user rules (e.g., "Use TypeScript")
      │
      ├─ AgentService.route_request()
      │  │
      │  ├─ Apply user instructions
      │  │
      │  └─→ AgentOrchestrator.route_request()
      │     │
      │     └─→ agent_id = 'code'
      │        action = 'refactor_code'
      │
      ├─ CodeGeneratorAgent._refactor_code()
      │  │
      │  ├─ CodeValidator.validate_code_action()
      │  │  └─→ Check bias, quality, instructions
      │  │
      │  ├─ CodeEditor.refactor_code()
      │  │  ├─ Detect patterns
      │  │  ├─ Apply refactoring
      │  │  └─→ Generate report
      │  │
      │  └─→ Return: {refactored_code, transformations}
      │
      ├─ QualityAnalyzer.validate_result()
      │  └─→ Check output quality
      │
      ├─ InstructionService.validate_result()
      │  └─→ Verify: "Uses TypeScript" ✓
      │
      └─→ AuditRepository.log({
         action: "code_refactor",
         type: "readability",
         transformations: 5,
         rules_verified: 3
      })
   │
   └─→ Frontend Redux: setRefactoredCode(...)
      │
      └─→ UI: Display diff + transformations list

RESPONSE: {
  "success": true,
  "refactored_code": "...",
  "transformations": [
    "Added type hints to functions",
    "Renamed variables for clarity",
    ...
  ],
  "quality_score": 0.92
}
```

### Flow 4.2: Detect and Fix Bugs

```
UI ACTION: User pastes code + clicks "Fix Bugs"
│
├─ Input: {code_text, language}
│
└─→ Frontend: POST /api/code/fix-bugs
   │
   └─→ CodeService.fix_bugs()
      │
      ├─ InstructionService.get_instructions()
      │
      └─→ AgentService.route_request()
         │
         ├─ CodeGeneratorAgent._fix_bugs()
         │  │
         │  ├─ CodeValidator.validate_code_action()
         │  │
         │  ├─ CodeEditor.debug_code()
         │  │  └─→ Detect: bare except, SQL injection, hardcoded values
         │  │
         │  ├─ CodeEditor.fix_bugs()
         │  │  └─→ Auto-fix detected issues
         │  │
         │  └─→ Return: {fixed_code, bug_reports}
         │
         ├─ InstructionService.validate_result()
         │  └─→ Verify compliance with rules
         │
         └─→ AuditRepository.log({
            action: "bug_fix",
            bugs_fixed: 3,
            severity_levels: ["critical", "high"],
            rules_compliance: true
         })
   │
   └─→ Frontend Redux: setFixedCode(...)
      │
      └─→ UI: Display bugs fixed + code diff

RESPONSE: {
  "success": true,
  "fixed_code": "...",
  "bugs": [
    {
      "type": "sql_injection",
      "severity": "critical",
      "location": "line 45",
      "description": "...",
      "suggested_fix": "..."
    },
    ...
  ],
  "bug_count": 3
}
```

---

## 5. SETTINGS & INSTRUCTIONS FLOWS

### Flow 5.1: Create User Instructions

```
UI ACTION: User opens Settings → Instructions Tab → Enters rules
│
├─ Input: {rules_text}
│
└─→ Frontend: POST /api/instructions
   │
   └─→ InstructionService.create_instruction()
      │
      ├─ Parse rules text
      │  └─→ Split by newlines, extract rules
      │
      ├─ Categorize rules
      │  └─→ Security / Quality / Architecture / Performance
      │
      ├─ InstructionRepository.create()
      │  └─→ PostgreSQL: INSERT INTO user_instructions
      │
      └─→ AuditRepository.log({
         action: "instruction_created",
         rule_count: 5,
         categories: ["security": 2, "quality": 3]
      })
   │
   └─→ Frontend Redux: setUserInstructions(...)
      │
      └─→ UI: Show confirmation + rule count

RESPONSE: {
  "success": true,
  "instruction": {
    "id": "inst_123",
    "rule_count": 5,
    "parsed_rules": [...],
    "created_at": "..."
  }
}
```

### Flow 5.2: Validate Instruction Compliance (on every agent call)

```
INTERNAL: AgentService.route_request() with user instructions

Step 1: Get instructions
   └─→ InstructionService.get_user_instructions(user_id, project_id)

Step 2: Pass to agent
   └─→ data['_user_instructions'] = instructions['parsed_rules']

Step 3: Agent processes
   └─→ Agent executes action

Step 4: Validate result
   └─→ InstructionService.validate_result(result, instructions)
       ├─ Check each rule against result
       ├─ Verify security compliance
       ├─ Verify quality requirements
       ├─ Verify architectural constraints
       └─ Return: (is_valid, violation_reason)

Step 5: Log compliance
   └─→ AuditRepository.log({
       action: result['success'] ? "action_completed" : "action_rejected",
       rules_applied: rule_count,
       compliance: "passed" | "violated",
       violation_reason: "..."
   })

Step 6: Return to user
   └─→ If violated: Return error with rule violation message
   └─→ If passed: Return normal result
```

---

## 6. REAL-TIME FLOWS

### Flow 6.1: WebSocket Connection (Session Active)

```
UI ACTION: User opens session → UI connects WebSocket
│
└─→ Frontend: WS /ws/sessions/{session_id}
   │
   └─→ WebSocket Router: websocket_handler()
      │
      ├─ Authenticate user
      ├─ Verify session access
      │
      └─→ WebSocketManager.register(user_id, session_id, connection)
         │
         └─→ Broadcast to other clients:
            {"type": "user_joined", "user": ...}

CONNECTION: WebSocket established ✓
```

### Flow 6.2: Real-time Message Updates (while agent is processing)

```
BACKGROUND: Agent is processing user's request
│
├─ Emit: {"type": "processing", "agent": "socratic"}
│
├─ Process in agent
│  └─→ Call Claude API (may take 2-5 seconds)
│
├─ Emit: {"type": "progress", "percent": 50}
│
├─ Complete processing
│  └─→ Generate response
│
├─ Emit: {"type": "message", "content": "...", "metadata": {...}}
│
└─→ All connected clients receive updates via WebSocket
   │
   └─→ Frontend Redux: updateMessage()
      │
      └─→ UI: Real-time display of response as it arrives
```

---

## COMPLETE FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────┐
│             USER INTERFACE (React)                  │
│  Dashboard | Projects | Sessions | Settings        │
└────────────────┬────────────────────────────────────┘
                 │
                 │ HTTP POST/GET/PUT
                 │ WebSocket (bi-directional)
                 ↓
┌─────────────────────────────────────────────────────┐
│          FASTAPI ROUTERS                            │
│  auth.py | projects.py | sessions.py | code.py    │
│  instructions.py | websocket.py                    │
└────────────────┬────────────────────────────────────┘
                 │
                 ↓ Delegate to service layer
┌─────────────────────────────────────────────────────┐
│          SERVICE LAYER                              │
│  AuthService | ProjectService | SessionService     │
│  AgentService | CodeService | InstructionService   │
└────────────┬────────────┬────────────┬──────────────┘
             │            │            │
             ↓            ↓            ↓
    ┌──────────────┐ ┌──────────────┐ ┌────────────────┐
    │ Repository   │ │ Agent System │ │ QualityAnalyzer│
    │ Layer        │ │              │ │ + CodeValidator│
    └──────────────┘ │ ┌──────────┐ │ │ + Instruction  │
                     │ │ 9 Agents │ │ │   Validation   │
                     │ └──────────┘ │ └────────────────┘
                     └──────────────┘
             │            │
             ↓            ↓
    ┌──────────────┐ ┌──────────────┐
    │ PostgreSQL   │ │ ChromaDB     │
    │ (Relational) │ │ (Vector DB)  │
    └──────────────┘ └──────────────┘
```

---

## TYPICAL REQUEST LIFECYCLE (Complete)

```
1. USER INPUT (100ms)
   └─→ User interaction in UI

2. API REQUEST (10ms)
   └─→ HTTP POST to FastAPI router
      └─→ Router validates request (Pydantic schema)

3. SERVICE PROCESSING (100-200ms)
   └─→ Service layer retrieves user instructions
   └─→ AgentService prepares request with rules
   └─→ Calls AgentOrchestrator

4. AGENT EXECUTION (1-5 seconds)
   └─→ Route to appropriate agent
   └─→ Agent processes request
   └─→ May call external APIs (Claude, etc.)

5. QUALITY VALIDATION (50-100ms)
   └─→ QualityAnalyzer validates result
   └─→ InstructionService checks compliance
   └─→ AuditRepository logs action

6. RESPONSE DELIVERY (10ms)
   └─→ Format response
   └─→ Return to client via HTTP or WebSocket

7. UI UPDATE (50-100ms)
   └─→ Redux updates state
   └─→ React re-renders components

TOTAL TYPICAL TIME: 1.5-6 seconds
```

---

## ERROR HANDLING IN FLOWS

```
At any point in flow, error can occur:

1. Validation Error (10ms)
   └─→ Return 400 Bad Request
   └─→ Include field-specific errors

2. Authentication Error (10ms)
   └─→ Return 401 Unauthorized
   └─→ Redirect to login

3. Authorization Error (10ms)
   └─→ Return 403 Forbidden
   └─→ Include missing permission

4. Instruction Violation (100ms)
   └─→ Return 403 with rule violation
   └─→ Include violated rule text

5. Agent Error (50-100ms)
   └─→ Return 500 Server Error
   └─→ Include error details in audit log

6. External Service Error (timeout)
   └─→ Return 503 Service Unavailable
   └─→ Include retry suggestion
```

---

## NEXT: Read 10_API_INTEGRATION.md for endpoint specifications
