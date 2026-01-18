# Socrates AI - Architecture Guide

This document provides a comprehensive technical overview of Socrates AI's architecture, design patterns, and internal systems.

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Multi-Agent Architecture](#multi-agent-architecture)
4. [Data Management](#data-management)
5. [Event-Driven System](#event-driven-system)
6. [Workflow & Data Flow](#workflow--data-flow)
7. [Design Patterns](#design-patterns)
8. [Extension Points](#extension-points)
9. [Performance Considerations](#performance-considerations)

---

## System Overview

Socrates AI is built on these fundamental principles:

1. **Multi-Agent Orchestration** - Specialized agents handle distinct responsibilities
2. **Event-Driven Communication** - Loose coupling between components
3. **Persistent Storage** - Both relational (SQLite) and vector (ChromaDB) databases
4. **Retrieval-Augmented Generation** - Semantic search powers intelligent responses
5. **Async-First Design** - Support for concurrent operations and scaling

```
┌─────────────────────────────────────────────────┐
│              User Interface Layer               │
│  ┌───────────────────────────────────────────┐  │
│  │  CLI / Web / Programmatic API            │  │
│  └───────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  AgentOrchestrator (Request Router & Manager)  │
│  ┌───────────────────────────────────────────┐  │
│  │ • Routes requests to agents              │  │
│  │ • Manages initialization                 │  │
│  │ • Handles databases                      │  │
│  │ • Emits system-wide events              │  │
│  └───────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
   │ Agents  │  │ Events │  │ Config │
   │ (10)    │  │Emitter │  │System  │
   └─────────┘  └────────┘  └────────┘
        │
        └────────────┬────────────┐
                     │            │
          ┌──────────▼─┐   ┌─────▼──────┐
          │ Databases  │   │  Claude    │
          │  SQLite    │   │  API       │
          │  ChromaDB  │   │  Client    │
          └────────────┘   └────────────┘
```

---

## Core Components

### 1. AgentOrchestrator

**Location**: `orchestration/orchestrator.py`

The central hub that coordinates all system activity.

**Key Responsibilities**:
- Initialize and manage 10 specialized agents
- Route incoming requests to appropriate agents
- Manage database connections (SQLite and ChromaDB)
- Load and maintain knowledge base
- Emit system-wide events
- Track metrics and token usage

**Key Methods**:
```python
# Request processing
def process_request(agent: str, request: Dict) -> Dict
async def process_request_async(agent: str, request: Dict) -> Dict

# Resource management
def __init__(config: Union[str, SocratesConfig, Dict])
def load_knowledge_base(path: Optional[Path]) -> int
def emit_event(event_type: str, data: Dict) -> None
```

**Initialization Flow**:
```
SocratesConfig → Orchestrator
  ├─ Create ProjectDatabase
  ├─ Create VectorDatabase
  ├─ Load knowledge base
  ├─ Initialize all 10 agents (with orchestrator reference)
  ├─ Set up event listeners
  └─ Return ready orchestrator
```

### 2. Configuration System

**Location**: `config.py`

Flexible, multi-method configuration supporting various initialization patterns.

**Three Initialization Methods**:

```python
# Method 1: Environment variables
config = SocratesConfig.from_env()

# Method 2: Dictionary
config = SocratesConfig.from_dict({
    "api_key": "sk-ant-...",
    "log_level": "DEBUG"
})

# Method 3: Builder pattern (fluent API)
config = ConfigBuilder("sk-ant-...") \
    .with_data_dir(Path("/data")) \
    .with_model("claude-opus-4-5-20251101") \
    .with_log_level("DEBUG") \
    .build()
```

**Configuration Hierarchy** (highest to lowest priority):
1. Explicit `SocratesConfig` instance
2. Environment variables
3. `ConfigBuilder` fluent API
4. Configuration dictionary
5. Default values

**Environment Variables**:
```bash
ANTHROPIC_API_KEY          # Required
CLAUDE_MODEL               # Default: claude-haiku-4-5-20251001
SOCRATES_DATA_DIR          # Default: ~/.socrates
SOCRATES_LOG_LEVEL         # Default: INFO
SOCRATES_LOG_FILE          # Default: {DATA_DIR}/logs/socrates.log
```

**Configurable Parameters**:
```python
@dataclass
class SocratesConfig:
    # API & Model
    api_key: str                                    # Required
    claude_model: str                              # Default: claude-haiku-4-5-20251001
    embedding_model: str                           # Default: all-MiniLM-L6-v2

    # Storage
    data_dir: Path                                 # Default: ~/.socrates
    projects_db_path: Optional[Path]
    vector_db_path: Optional[Path]
    knowledge_base_path: Optional[Path]

    # Behavior
    max_context_length: int = 8000
    max_retries: int = 3
    retry_delay: float = 1.0
    token_warning_threshold: float = 0.8          # 80%
    session_timeout: int = 3600                    # 1 hour

    # Logging
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    # Knowledge
    custom_knowledge: List[str] = []
```

### 3. Claude API Client

**Location**: `clients/claude_client.py`

Wrapper around Anthropic's API with enhanced features.

**Key Features**:
- Automatic token counting and cost estimation
- Structured response parsing (JSON, Markdown code blocks)
- Retry logic with exponential backoff
- Both sync and async support
- Request validation

**Core Methods**:
```python
def extract_insights(response: str, project: ProjectContext) -> Dict
def generate_code(context: ProjectContext) -> str
def generate_documentation(context: ProjectContext) -> str
def analyze_conflicts(insights: Dict, project: ProjectContext) -> Dict
def generate_socratic_questions(project: ProjectContext) -> List[str]
```

**Token Tracking**:
- Monitors input/output tokens per request
- Maintains running total for session
- Estimates cost at current OpenAI rates
- Emits TOKEN_USAGE events for monitoring

---

## Multi-Agent Architecture

The system uses 10 specialized agents coordinated by the orchestrator.

### Agent Base Class

**Location**: `agents/base.py`

```python
class Agent(ABC):
    def __init__(self, name: str, orchestrator: AgentOrchestrator):
        self.name = name
        self.orchestrator = orchestrator
        self.logger = get_logger(name.lower())

    @abstractmethod
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous processing"""
        pass

    async def process_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous processing (optional override)"""
        return self.process(request)

    def log(self, message: str, level: str = "info"):
        """Event-based logging"""
        self.logger.log(message, level)

    def emit_event(self, event_type: str, data: Dict = None):
        """Emit system event"""
        self.orchestrator.emit_event(event_type, data)

    def suggest_knowledge_addition(self, topic: str, content: str):
        """Suggest knowledge enrichment"""
        self.emit_event(EventType.KNOWLEDGE_SUGGESTION, {...})
```

### The 10 Agents

#### 1. **ProjectManagerAgent**
**Purpose**: Create, load, save, and manage projects

**Actions**:
- `create_project` - Create new project with owner
- `load_project` - Load existing project
- `save_project` - Persist project to database
- `add_collaborator` - Add team member
- `list_projects` - List user's projects
- `archive_project` - Archive for later
- `restore_project` - Restore archived project
- `delete_project_permanently` - Permanent deletion

**Data**:
```python
# Input: Request with action and parameters
{
    "action": "create_project",
    "project_name": "My App",
    "owner": "alice",
    "collaborators": ["bob"]
}

# Output: Result with status and project data
{
    "status": "success",
    "project_id": "proj_abc123",
    "project": ProjectContext(...)
}
```

#### 2. **SocraticCounselorAgent**
**Purpose**: Conduct Socratic dialogue through project phases

**Actions**:
- `generate_question` - Create contextual question
- `process_response` - Extract insights from answer
- `advance_phase` - Move to next project phase
- `get_hint` - Provide phase-specific hint

**Dialogue Phases**:
1. Discovery - What problem? Who are users?
2. Analysis - What are requirements? Constraints?
3. Design - How will we build it? Architecture?
4. Implementation - Generate code and docs

**Features**:
- Claude-powered dynamic questions (or static fallback)
- Automatic insight extraction from responses
- Conflict detection after each response
- Phase-aware prompts and hints

#### 3. **CodeGeneratorAgent**
**Purpose**: Generate production-ready code

**Actions**:
- `generate_script` - Generate code file
- `generate_documentation` - Auto-generate docs

**Input**:
```python
{
    "action": "generate_script",
    "project_id": "proj_abc123",
    "module": "authentication",  # Optional: specific module
    "language": "python"         # From project.language_preferences
}
```

**Process**:
1. Load full project context
2. Build comprehensive prompt with requirements, architecture, examples
3. Call Claude with streaming
4. Parse and validate generated code
5. Emit CODE_GENERATED event

#### 4. **ContextAnalyzerAgent**
**Purpose**: Analyze and extract patterns from project context

**Actions**:
- `analyze_context` - Generate analysis summary
- `get_summary` - Get project summary
- `find_similar` - Find similar projects via RAG
- `search_conversations` - Search dialogue history
- `generate_summary` - Markdown summary
- `get_statistics` - Project metrics

#### 5. **ConflictDetectorAgent**
**Purpose**: Identify contradictions in specifications

**Conflict Types**:
- Tech Stack conflicts (incompatible technologies)
- Requirements conflicts (contradictory features)
- Goals conflicts (conflicting objectives)
- Constraints conflicts (violated constraints)

**Process**:
```
New Insights → Pluggable Checkers → Conflicts Found
                    ├─ TechStackChecker
                    ├─ RequirementsChecker
                    ├─ GoalsChecker
                    └─ ConstraintsChecker
                         ↓
              Emit CONFLICT_DETECTED event
                         ↓
              Store ConflictInfo in project
```

#### 6. **SystemMonitorAgent**
**Purpose**: Track system health and usage

**Actions**:
- `track_tokens` - Monitor API usage
- `check_health` - Verify API connectivity
- `get_stats` - System statistics
- `check_limits` - Check token/cost limits

**Metrics Tracked**:
- Total tokens used (input + output)
- Estimated cost
- API calls made
- Connection status
- Warning thresholds

#### 7. **DocumentAgentAgent**
**Purpose**: Import and process external documents

**Actions**:
- `import_file` - Import single document
- `import_directory` - Batch import folder
- `list_documents` - Show imported docs

**Supported Formats**:
- PDF (via PyPDF2)
- Plain text (.txt, .md)
- Code files (.py, .js, .java, etc.)

**Processing**:
```
Document → Extract Text → Split into Chunks (500 char, 50 overlap)
         → Generate Embeddings → Store in ChromaDB → Make searchable
```

#### 8. **UserManagerAgent**
**Purpose**: Manage user accounts and lifecycle

**Actions**:
- `archive_user` - Archive account
- `restore_user` - Restore archived account
- `delete_user_permanently` - Permanent deletion
- `get_archived_users` - List archived accounts

#### 9. **NoteManagerAgent**
**Purpose**: Manage project notes and annotations

**Actions**:
- `add_note` - Create note
- `list_notes` - List with filtering
- `search_notes` - Search by content/tags
- `delete_note` - Remove note

**Note Types**:
- Design decisions
- Bug reports
- Feature ideas
- Tasks/TODOs
- General notes

#### 10. **KnowledgeManagerAgent**
**Purpose**: Manage knowledge base entries

**Actions**:
- `add_knowledge` - Add to knowledge base
- `get_knowledge` - Retrieve entries
- `list_knowledge` - List all entries
- `get_suggestions` - Get pending suggestions

**Event Listeners**:
- Listens for `KNOWLEDGE_SUGGESTION` events
- Maintains suggestion queue per project
- Auto-processes approved suggestions

---

## Data Management

### SQLite Database (Project Data)

**Schema**:

```sql
-- Projects
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    data BLOB,              -- Pickled ProjectContext
    created_at TEXT,
    updated_at TEXT
);

-- Users
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    passcode_hash TEXT,     -- SHA256
    data BLOB,              -- Pickled User
    created_at TEXT
);

-- Project Notes
CREATE TABLE project_notes (
    note_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    data BLOB,              -- Pickled ProjectNote
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

**Why Pickle?**
- Full object serialization (includes method state)
- Preserves all Python types and structures
- Used for convenience in development
- Note: Not production-safe with untrusted data (local use only)

**Location**: `~/.socrates/projects.db`

### ChromaDB Vector Database

**Collection**: `socratic_knowledge`

**Storage**:
```
~/.socrates/vector_db/
├── chroma.sqlite3                           # Metadata
└── {collection_uuid}/
    ├── data_level0.bin                      # Embeddings
    └── length.bin                           # Index info
```

**Document Structure**:
```python
{
    "ids": ["knowledge_entry_123", ...],
    "documents": ["Content text here", ...],
    "metadatas": [
        {
            "category": "architecture",      # Knowledge type
            "topic": "microservices",        # Topic
            "difficulty": "intermediate",    # Difficulty level
            "project_id": "proj_abc",        # (Optional) Project scope
            "source": "documentation",       # Where it came from
            "tags": ["scalability"],         # Search tags
            "imported_at": "2025-01-01"      # Timestamp
        },
        ...
    ],
    "embeddings": [                          # Vector representations
        [0.123, 0.456, ...],                 # 384-dim for MiniLM-L6-v2
        ...
    ]
}
```

**Search Methods**:

```python
# Semantic similarity search
results = vector_db.search_similar(
    query="How do I implement authentication?",
    top_k=5,
    project_id="proj_abc"  # Optional: filter to project
)

# Get project knowledge
knowledge = vector_db.get_project_knowledge(project_id)

# Delete project knowledge
deleted_count = vector_db.delete_project_knowledge(project_id)
```

### Data Models

**ProjectContext**:
```python
@dataclass
class ProjectContext:
    project_id: str
    name: str
    owner: str
    collaborators: List[str]

    # Specifications
    goals: str                      # What problem does it solve?
    requirements: List[str]         # What features?
    tech_stack: List[str]          # What technologies?
    constraints: List[str]         # What limitations?
    team_structure: str            # Who's on the team?

    # Technical
    language_preferences: List[str] # Python, JavaScript, etc.
    deployment_target: str         # Cloud, on-premise, etc.
    code_style: str               # Style guide or standards

    # Project State
    phase: str                     # discovery/analysis/design/implementation
    conversation_history: List[Dict] # Full dialogue history
    status: str                    # active/completed/on-hold
    progress: int                  # 0-100%
    archived: bool

    # Metadata
    created_at: datetime
    updated_at: datetime

    # Detected Issues
    conflicts: List[ConflictInfo]
```

**User**:
```python
@dataclass
class User:
    username: str
    passcode_hash: str              # SHA256 of passcode
    projects: List[str]             # Project IDs
    is_archived: bool
    archived_at: Optional[datetime]
    created_at: datetime
```

**KnowledgeEntry**:
```python
@dataclass
class KnowledgeEntry:
    id: str
    content: str                    # Text content
    category: str                   # Type of knowledge
    metadata: Dict[str, Any]        # Custom metadata
    embedding: Optional[List[float]]  # Vector representation
```

---

## Event-Driven System

### Event Emitter

**Location**: `events/event_emitter.py`

Thread-safe pub/sub system with no external dependencies.

**Architecture**:
```python
class EventEmitter:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._once_listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()

    def on(self, event_type: str, listener: Callable) -> None:
        """Subscribe to event"""

    def once(self, event_type: str, listener: Callable) -> None:
        """Subscribe to single occurrence"""

    def remove_listener(self, event_type: str, listener: Callable) -> None:
        """Unsubscribe"""

    def emit(self, event_type: str, data: Optional[Dict] = None) -> None:
        """Emit event to all listeners"""
```

**Usage**:
```python
# Subscribe
def on_project_created(data):
    print(f"Project created: {data['project_id']}")

orchestrator.event_emitter.on(EventType.PROJECT_CREATED, on_project_created)

# Emit
orchestrator.emit_event(EventType.PROJECT_CREATED, {
    "project_id": "proj_123",
    "owner": "alice"
})

# One-time listener
def on_first_question(data):
    print(f"First question: {data['question']}")

orchestrator.event_emitter.once(EventType.QUESTION_GENERATED, on_first_question)
```

### Event Types

**Location**: `events/event_types.py`

```python
# Agent lifecycle
AGENT_START = "agent.start"                 # Agent begins processing
AGENT_COMPLETE = "agent.complete"           # Agent completes successfully
AGENT_ERROR = "agent.error"                 # Agent encounters error

# Project management
PROJECT_CREATED = "project.created"
PROJECT_SAVED = "project.saved"
PROJECT_LOADED = "project.loaded"
PROJECT_ARCHIVED = "project.archived"
PROJECT_RESTORED = "project.restored"
PROJECT_DELETED = "project.deleted"

# Dialogue
QUESTION_GENERATED = "dialogue.question_generated"
RESPONSE_RECEIVED = "dialogue.response_received"
PHASE_ADVANCED = "dialogue.phase_advanced"
HINT_PROVIDED = "dialogue.hint_provided"

# Conflict management
CONFLICT_DETECTED = "conflict.detected"
CONFLICT_RESOLVED = "conflict.resolved"

# Knowledge
KNOWLEDGE_LOADED = "knowledge.loaded"
KNOWLEDGE_SUGGESTION = "knowledge.suggestion"
KNOWLEDGE_ADDED = "knowledge.added"
DOCUMENT_IMPORTED = "knowledge.document_imported"

# Code generation
CODE_GENERATED = "code.generated"
CODE_ANALYSIS_COMPLETE = "code.analysis_complete"
DOCUMENTATION_GENERATED = "code.documentation_generated"

# System monitoring
TOKEN_USAGE = "system.token_usage"
SYSTEM_INITIALIZED = "system.initialized"
PROGRESS_UPDATE = "system.progress_update"

# Logging
LOG_DEBUG = "log.debug"
LOG_INFO = "log.info"
LOG_WARNING = "log.warning"
LOG_ERROR = "log.error"
```

---

## Workflow & Data Flow

### Complete Socratic Dialogue Workflow

```
1. PROJECT CREATION
   └─ User requests project creation
   └─ ProjectManagerAgent.create_project()
   └─ ProjectContext created with initial values
   └─ Saved to SQLite
   └─ Emit: PROJECT_CREATED

2. DISCOVERY PHASE
   └─ SocraticCounselorAgent.generate_question()
   └─ Claude generates question based on empty context
   └─ Question: "What problem does this solve?"
   └─ Emit: QUESTION_GENERATED

   └─ User provides answer
   └─ SocraticCounselorAgent.process_response()
   └─ Claude extracts: goals, target_users, success_criteria
   └─ ConflictDetectorAgent.detect_conflicts()
   └─ Update ProjectContext with extracted insights
   └─ Emit: RESPONSE_RECEIVED, [CONFLICT_DETECTED]

3. ANALYSIS PHASE
   └─ SocraticCounselorAgent.advance_phase()
   └─ ProjectContext.phase = "analysis"
   └─ Next question: "What features are needed?"
   └─ Process response → Extract requirements
   └─ Detect conflicts → Flag tech stack issues
   └─ Emit: PHASE_ADVANCED, [CONFLICT_DETECTED]

4. DESIGN PHASE
   └─ Architecture-focused questions
   └─ Extract: tech_stack, deployment_target, constraints
   └─ Detect: Technology compatibility conflicts
   └─ Emit: PHASE_ADVANCED

5. IMPLEMENTATION PHASE
   └─ User asks: /code generate
   └─ CodeGeneratorAgent.generate_script()
   └─ Build comprehensive prompt from ProjectContext
   └─ Claude generates production-ready code
   └─ Store result
   └─ Emit: CODE_GENERATED

6. PROJECT SAVED
   └─ ProjectManagerAgent.save_project()
   └─ Serialize ProjectContext to pickle
   └─ Insert/update in SQLite
   └─ Emit: PROJECT_SAVED
```

### Knowledge Enrichment Workflow

```
1. KNOWLEDGE SUGGESTION DETECTED
   └─ Agent processes request
   └─ Detects knowledge gap
   └─ suggest_knowledge_addition("topic", "content")
   └─ Emit: KNOWLEDGE_SUGGESTION event

2. KNOWLEDGE MANAGER RECEIVES SUGGESTION
   └─ KnowledgeManagerAgent listening for KNOWLEDGE_SUGGESTION
   └─ Queue suggestion for user review
   └─ Create ProjectNote with suggestion details

3. USER APPROVES SUGGESTION
   └─ User: /knowledge add
   └─ KnowledgeManagerAgent.add_knowledge()
   └─ Create KnowledgeEntry with metadata
   └─ Generate embedding using SentenceTransformer
   └─ Store in ChromaDB
   └─ Emit: KNOWLEDGE_ADDED

4. KNOWLEDGE AVAILABLE FOR RAG
   └─ Next context-building phase
   └─ ContextAnalyzerAgent.find_similar()
   └─ Vector search finds relevant knowledge
   └─ Included in Claude prompts
```

### Token Tracking Workflow

```
1. USER INITIATES REQUEST
   └─ Example: "generate_question"
   └─ SocraticCounselorAgent.process(request)

2. AGENT CALLS CLAUDE API
   └─ ClaudeClient.generate_socratic_questions()
   └─ Anthropic API returns response + token counts
   └─ input_tokens, output_tokens recorded

3. TOKEN USAGE TRACKED
   └─ SystemMonitorAgent.track_tokens()
   └─ Calculate cost at current rates
   └─ Compare against warning threshold
   └─ Emit: TOKEN_USAGE event

4. MONITORING
   └─ App listens for TOKEN_USAGE events
   └─ Display warning if over 80% budget
   └─ User can check: /status
```

---

## Design Patterns

### 1. **Multi-Agent Pattern**
Specialized, autonomous components with single responsibility. Orchestrator coordinates.

```python
# Each agent handles specific domain
class ProjectManagerAgent(Agent): pass      # Project CRUD
class SocraticCounselorAgent(Agent): pass   # Dialogue
class CodeGeneratorAgent(Agent): pass       # Code generation
```

### 2. **Orchestrator Pattern**
Central router that manages all requests and inter-component communication.

```python
result = orchestrator.process_request('project_manager', {
    'action': 'create_project',
    'project_name': 'My App'
})
```

### 3. **Template Method Pattern**
Conflict checkers use template method for extensible conflict detection.

```python
class ConflictChecker(ABC):
    def check(self, ...):
        values = self._extract_values(...)
        normalized = self._normalize_values(values)
        existing = self._get_existing_values(...)
        return self._find_conflict(...)
```

### 4. **Pub/Sub Pattern**
Event emitter enables loose coupling between components.

```python
# Publish
orchestrator.emit_event(EventType.CODE_GENERATED, {"code": "..."})

# Subscribe
orchestrator.event_emitter.on(EventType.CODE_GENERATED, handler)
```

### 5. **Builder Pattern**
Fluent API for flexible configuration creation.

```python
config = ConfigBuilder("api_key") \
    .with_data_dir(path) \
    .with_model("claude-opus-4-5-20251101") \
    .with_log_level("DEBUG") \
    .build()
```

### 6. **Adapter Pattern**
Multiple initialization methods for configuration.

```python
# All adapt to same SocratesConfig
SocratesConfig.from_env()
SocratesConfig.from_dict(dict)
ConfigBuilder(key).build()
```

### 7. **Repository Pattern**
Database abstraction for data access.

```python
# ProjectDatabase hides SQLite details
db.save_project(project)
project = db.load_project(project_id)
```

### 8. **Strategy Pattern**
Pluggable conflict checkers for different conflict types.

```python
checkers = [
    TechStackConflictChecker(),
    RequirementsConflictChecker(),
    GoalsConflictChecker(),
    ConstraintsConflictChecker()
]
```

---

## Extension Points

### 1. Custom Agents

Add new specialized agent:

```python
from socratic_system.agents.base import Agent

class MyCustomAgent(Agent):
    def __init__(self, orchestrator):
        super().__init__("MyCustomAgent", orchestrator)

    def process(self, request):
        action = request.get('action')

        if action == 'my_action':
            self.log("Processing my action")
            result = self.do_something()
            self.emit_event(EventType.CUSTOM, {"result": result})
            return {"status": "success", "data": result}

        return {"status": "error", "message": "Unknown action"}

# Register in orchestrator
orchestrator.agents['my_custom'] = MyCustomAgent(orchestrator)
```

### 2. Event Listeners

Listen for and react to system events:

```python
def on_code_generated(data):
    code = data['code']
    # Do something with generated code
    save_to_file(code)
    run_linter(code)

orchestrator.event_emitter.on(EventType.CODE_GENERATED, on_code_generated)
```

### 3. Custom Commands

Add new CLI command:

```python
from socratic_system.ui.commands.base import BaseCommand

class MyCommand(BaseCommand):
    def __init__(self):
        super().__init__(
            name="mycommand",
            description="Does something special",
            usage="mycommand [args]"
        )

    def execute(self, args, context):
        orchestrator = context['orchestrator']
        result = orchestrator.process_request('my_custom', {
            'action': 'my_action',
            'args': args
        })
        return self.success(message=f"Done: {result}")
```

### 4. Conflict Checkers

Add new conflict detection logic:

```python
from socratic_system.conflict_resolution.base import ConflictChecker

class CustomConflictChecker(ConflictChecker):
    def _extract_values(self, insights):
        # Extract relevant values from new insights
        return [insights.get('my_field')]

    def _get_existing_values(self, project):
        # Get current values from project
        return project.my_field if hasattr(project, 'my_field') else None

    def _find_conflict(self, new_value, existing, project, user):
        # Detect conflict between old and new
        if existing and new_value != existing:
            return {
                "conflict": True,
                "old": existing,
                "new": new_value
            }
        return {"conflict": False}
```

### 5. Knowledge Base Extensions

Add custom knowledge:

```python
# Via configuration
config = ConfigBuilder(api_key) \
    .with_custom_knowledge([
        "Python best practices: ...",
        "Django patterns: ...",
        "REST API design: ..."
    ]) \
    .build()

# Via API
orchestrator.process_request('knowledge_manager', {
    'action': 'add_knowledge',
    'entry': KnowledgeEntry(
        id='custom_123',
        content='Your knowledge',
        category='custom',
        metadata={'topic': 'python'}
    )
})
```

---

## Performance Considerations

### 1. Vector Search Performance

**ChromaDB Optimization**:
- Embedding generation is cached
- Queries use approximate nearest neighbor search (HNSW)
- Metadata filtering reduces search space
- Project-level filtering makes queries more targeted

**Optimization Tips**:
```python
# Good: Filter by project before search
results = vector_db.search_similar(
    query="How do I handle auth?",
    project_id="proj_abc"  # Filters search space
)

# Less efficient: Search all knowledge
results = vector_db.search_similar(query="How do I handle auth?")
```

### 2. Token Usage Optimization

**Cost Control**:
- Set `token_warning_threshold` in config (default: 0.8 = 80%)
- Monitor via `/status` command
- Implement token budgets for projects

```python
config = ConfigBuilder(api_key) \
    .with_token_warning_threshold(0.7) \  # Warn at 70%
    .build()
```

### 3. Database Performance

**SQLite Optimization**:
- Projects table properly indexed on project_id
- Queries use pickle serialization (fast for complex objects)
- Consider connection pooling for high concurrency

**ChromaDB Optimization**:
- HNSW algorithm provides O(log N) search
- Batch operations more efficient than single inserts

### 4. Concurrent Requests

**Async Support**:
```python
# For high throughput
results = await asyncio.gather(
    orchestrator.process_request_async('agent1', request1),
    orchestrator.process_request_async('agent2', request2),
    orchestrator.process_request_async('agent3', request3)
)
```

### 5. Memory Management

**Large Projects**:
- ProjectContext includes full conversation history
- Consider archiving old conversations for large projects
- Knowledge base loaded once at startup

---

## Security Considerations

### 1. API Key Management

```bash
# Never commit API keys
export ANTHROPIC_API_KEY="sk-ant-..."
# Use environment variables or .env files (not tracked in git)
```

### 2. Password Security

```python
# Passwords hashed with SHA256
import hashlib
passcode_hash = hashlib.sha256(passcode.encode()).hexdigest()
```

### 3. Database Isolation

- SQLite file-based (local security)
- No network exposure by default
- ChromaDB local-only initialization
- Deployment: Use containerization and secrets management

### 4. Input Validation

- All user inputs sanitized before Claude API calls
- File uploads validated for type and size
- SQL injection prevention (using ORM layer)

---

## Scaling Considerations

### Single Node Scaling

1. **Increase worker processes**: Run multiple orchestrator instances
2. **Optimize vector DB**: Consider managed ChromaDB service
3. **Async/await**: Leverage `process_request_async()` for concurrency

### Multi-Node Scaling

1. **Shared databases**:
   - PostgreSQL instead of SQLite
   - Managed vector DB (Pinecone, Weaviate)

2. **REST API wrapper**:
   - Use provided FastAPI wrapper in `socrates-api/`
   - Stateless architecture enables horizontal scaling

3. **Event streaming**:
   - Replace in-memory EventEmitter with message broker
   - Kafka/Redis for distributed event propagation

### Example: Multi-Process Setup

```python
# orchestrator_worker.py
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.config import SocratesConfig

config = SocratesConfig.from_env()
orchestrator = AgentOrchestrator(config)

# Handle requests from queue/API
while True:
    request = get_from_queue()
    result = orchestrator.process_request(request['agent'], request['data'])
    send_to_response_queue(result)
```

---

## Testing Architecture

### Unit Tests

Test individual agents and components in isolation:

```python
def test_project_manager_create_project():
    orchestrator = MockOrchestrator()
    agent = ProjectManagerAgent(orchestrator)

    result = agent.process({
        'action': 'create_project',
        'project_name': 'Test',
        'owner': 'alice'
    })

    assert result['status'] == 'success'
    assert result['project']['name'] == 'Test'
```

### Integration Tests

Test agent interactions and workflows:

```python
def test_full_dialogue_workflow():
    orchestrator = AgentOrchestrator(test_config)

    # Create project
    result = orchestrator.process_request('project_manager', {...})
    project_id = result['project_id']

    # Ask question
    result = orchestrator.process_request('socratic_counselor', {
        'action': 'generate_question',
        'project_id': project_id
    })
    assert 'question' in result
```

### Event Testing

Test event emission and handling:

```python
def test_conflict_detection_event():
    orchestrator = AgentOrchestrator(test_config)
    detected_events = []

    orchestrator.event_emitter.on(
        EventType.CONFLICT_DETECTED,
        lambda data: detected_events.append(data)
    )

    # Trigger conflict
    orchestrator.process_request('socratic_counselor', {...})

    assert len(detected_events) > 0
```

---

## Monitoring & Observability

### Logging

```python
# Configure log level
config = ConfigBuilder(api_key) \
    .with_log_level("DEBUG") \
    .build()

# Log file at: ~/.socrates/logs/socrates.log
```

### Events as Observability

```python
# Hook into events for monitoring
def monitor_token_usage(data):
    log_to_monitoring_system({
        'timestamp': datetime.now(),
        'tokens_used': data['total_tokens'],
        'estimated_cost': data['cost_estimate']
    })

orchestrator.event_emitter.on(EventType.TOKEN_USAGE, monitor_token_usage)
```

### System Status

```bash
# Check system health
/status
```

---

## References

- [API Reference](API_REFERENCE.md)
- [User Guide](USER_GUIDE.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Configuration Guide](CONFIGURATION.md)

---

**Last Updated**: January 2026
**Version**: 1.3.0
