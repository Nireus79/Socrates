# API Reference - Socrates AI

Complete API documentation for programmatic usage and integration.

## Table of Contents

1. [Orchestrator API](#orchestrator-api)
2. [Agent APIs](#agent-apis)
3. [Database APIs](#database-apis)
4. [Event System](#event-system)
5. [Configuration API](#configuration-api)
6. [Models & Data Types](#models--data-types)
7. [Usage Examples](#usage-examples)

---

## Orchestrator API

Central interface for all operations.

### AgentOrchestrator

**Location**: `socratic_system.orchestration.AgentOrchestrator`

#### Constructor

```python
from socratic_system.config import SocratesConfig, ConfigBuilder
from socratic_system.orchestration import AgentOrchestrator

# Method 1: String API key
orchestrator = AgentOrchestrator("sk-ant-...")

# Method 2: Config object
config = SocratesConfig.from_env()
orchestrator = AgentOrchestrator(config)

# Method 3: Builder pattern
config = ConfigBuilder("sk-ant-...") \
    .with_data_dir(Path("/data")) \
    .with_model("claude-opus-4-5-20251101") \
    .with_log_level("DEBUG") \
    .build()
orchestrator = AgentOrchestrator(config)
```

#### Core Methods

##### process_request()

```python
def process_request(agent: str, request: Dict[str, Any]) -> Dict[str, Any]
```

Send synchronous request to agent.

**Parameters**:
- `agent` (str): Agent name
- `request` (Dict): Action and parameters

**Returns**: Dict with status, data, messages

**Example**:
```python
result = orchestrator.process_request('project_manager', {
    'action': 'create_project',
    'project_name': 'My App',
    'owner': 'alice'
})

assert result['status'] == 'success'
project = result['project']
```

##### process_request_async()

```python
async def process_request_async(agent: str, request: Dict[str, Any]) -> Dict[str, Any]
```

Send asynchronous request to agent.

**Example**:
```python
import asyncio

async def main():
    result = await orchestrator.process_request_async('code_generator', {
        'action': 'generate_script',
        'project_id': 'proj_123'
    })
    return result

code = asyncio.run(main())
```

##### emit_event()

```python
def emit_event(event_type: str, data: Optional[Dict] = None) -> None
```

Emit system-wide event.

**Example**:
```python
from socratic_system.events import EventType

orchestrator.emit_event(EventType.KNOWLEDGE_SUGGESTION, {
    'project_id': 'proj_123',
    'topic': 'authentication',
    'content': 'OAuth 2.0 best practices...'
})
```

##### load_knowledge_base()

```python
def load_knowledge_base(path: Optional[Path] = None) -> int
```

Load knowledge base entries into vector database.

**Returns**: Number of knowledge entries loaded

**Example**:
```python
count = orchestrator.load_knowledge_base()
print(f"Loaded {count} knowledge entries")
```

#### Properties

```python
orchestrator.config              # SocratesConfig instance
orchestrator.project_db          # ProjectDatabase instance
orchestrator.vector_db           # VectorDatabase instance
orchestrator.event_emitter       # EventEmitter instance
orchestrator.agents              # Dict of agent instances
```

---

## Agent APIs

### ProjectManagerAgent

**Actions**:

#### create_project
```python
result = orchestrator.process_request('project_manager', {
    'action': 'create_project',
    'project_name': 'My App',
    'owner': 'alice',
    'collaborators': ['bob']
})
```

#### load_project
```python
result = orchestrator.process_request('project_manager', {
    'action': 'load_project',
    'project_id': 'proj_123'
})

project = result['project']  # ProjectContext instance
```

#### save_project
```python
result = orchestrator.process_request('project_manager', {
    'action': 'save_project',
    'project': project_context
})
```

#### add_collaborator
```python
result = orchestrator.process_request('project_manager', {
    'action': 'add_collaborator',
    'project_id': 'proj_123',
    'username': 'charlie'
})
```

#### list_projects
```python
result = orchestrator.process_request('project_manager', {
    'action': 'list_projects',
    'username': 'alice'
})

projects = result['projects']  # List of ProjectContext
```

#### archive_project
```python
result = orchestrator.process_request('project_manager', {
    'action': 'archive_project',
    'project_id': 'proj_123'
})
```

### SocraticCounselorAgent

**Actions**:

#### generate_question
```python
result = orchestrator.process_request('socratic_counselor', {
    'action': 'generate_question',
    'project_id': 'proj_123'
})

question = result['question']
```

#### process_response
```python
result = orchestrator.process_request('socratic_counselor', {
    'action': 'process_response',
    'project_id': 'proj_123',
    'response': 'User response to question',
    'question_number': 1
})

insights = result['insights']  # Extracted: goals, requirements, etc.
```

#### advance_phase
```python
result = orchestrator.process_request('socratic_counselor', {
    'action': 'advance_phase',
    'project_id': 'proj_123'
})

project = result['project']
assert project.phase in ['analysis', 'design', 'implementation']
```

#### get_hint
```python
result = orchestrator.process_request('socratic_counselor', {
    'action': 'get_hint',
    'project_id': 'proj_123'
})

hint = result['hint']
```

### CodeGeneratorAgent

**Actions**:

#### generate_script
```python
result = orchestrator.process_request('code_generator', {
    'action': 'generate_script',
    'project_id': 'proj_123',
    'module': 'authentication',  # Optional
    'language': 'python'
})

code = result['code']
filename = result['filename']
```

#### generate_documentation
```python
result = orchestrator.process_request('code_generator', {
    'action': 'generate_documentation',
    'project_id': 'proj_123'
})

docs = result['documentation']
```

### ContextAnalyzerAgent

**Actions**:

#### analyze_context
```python
result = orchestrator.process_request('context_analyzer', {
    'action': 'analyze_context',
    'project_id': 'proj_123'
})

summary = result['analysis']
```

#### find_similar
```python
result = orchestrator.process_request('context_analyzer', {
    'action': 'find_similar',
    'project_id': 'proj_123',
    'top_k': 5
})

similar_projects = result['similar']
```

#### search_conversations
```python
result = orchestrator.process_request('context_analyzer', {
    'action': 'search_conversations',
    'project_id': 'proj_123',
    'query': 'authentication'
})

results = result['matches']
```

### ConflictDetectorAgent

**Actions**:

#### detect_conflicts
```python
result = orchestrator.process_request('conflict_detector', {
    'action': 'detect_conflicts',
    'project_id': 'proj_123',
    'insights': new_insights
})

conflicts = result['conflicts']  # List of ConflictInfo
```

#### resolve_conflict
```python
result = orchestrator.process_request('conflict_detector', {
    'action': 'resolve_conflict',
    'conflict_id': 'conflict_123',
    'resolution': 'Add explicit consent for face recognition'
})
```

### SystemMonitorAgent

**Actions**:

#### track_tokens
```python
result = orchestrator.process_request('system_monitor', {
    'action': 'track_tokens'
})

stats = result['stats']  # tokens, cost, etc.
```

#### get_stats
```python
result = orchestrator.process_request('system_monitor', {
    'action': 'get_stats'
})

total_tokens = result['total_tokens']
estimated_cost = result['estimated_cost']
```

#### check_limits
```python
result = orchestrator.process_request('system_monitor', {
    'action': 'check_limits'
})

warnings = result['warnings']  # List of limit warnings
```

### KnowledgeManagerAgent

**Actions**:

#### add_knowledge
```python
from socratic_system.models import KnowledgeEntry

result = orchestrator.process_request('knowledge_manager', {
    'action': 'add_knowledge',
    'entry': KnowledgeEntry(
        id='custom_123',
        content='Custom knowledge content',
        category='custom',
        metadata={'topic': 'authentication'}
    )
})
```

#### get_knowledge
```python
result = orchestrator.process_request('knowledge_manager', {
    'action': 'get_knowledge',
    'entry_id': 'custom_123'
})

entry = result['entry']  # KnowledgeEntry
```

#### list_knowledge
```python
result = orchestrator.process_request('knowledge_manager', {
    'action': 'list_knowledge',
    'project_id': 'proj_123'  # Optional filter
})

entries = result['entries']  # List of KnowledgeEntry
```

### DocumentAgent

**Actions**:

#### import_file
```python
result = orchestrator.process_request('document_agent', {
    'action': 'import_file',
    'file_path': '/path/to/document.pdf',
    'project_id': 'proj_123'  # Optional
})

num_entries = result['imported_count']
```

#### import_directory
```python
result = orchestrator.process_request('document_agent', {
    'action': 'import_directory',
    'directory_path': '/path/to/codebase',
    'project_id': 'proj_123'
})

num_entries = result['imported_count']
```

### NoteManagerAgent

**Actions**:

#### add_note
```python
result = orchestrator.process_request('note_manager', {
    'action': 'add_note',
    'project_id': 'proj_123',
    'title': 'Design Decision',
    'content': 'Using React hooks for state management',
    'note_type': 'design'  # design, bug, idea, task, general
})

note_id = result['note_id']
```

#### list_notes
```python
result = orchestrator.process_request('note_manager', {
    'action': 'list_notes',
    'project_id': 'proj_123',
    'note_type': 'task'  # Optional filter
})

notes = result['notes']
```

#### search_notes
```python
result = orchestrator.process_request('note_manager', {
    'action': 'search_notes',
    'project_id': 'proj_123',
    'query': 'authentication'
})

matches = result['matches']
```

---

## Database APIs

### ProjectDatabase

**Location**: `socratic_system.database.ProjectDatabase`

```python
from socratic_system.database import ProjectDatabase

db = ProjectDatabase(db_path)

# Save project
db.save_project(project_context)

# Load project
project = db.load_project(project_id)

# Get user projects
projects = db.get_user_projects(username)

# User management
db.create_user(username, passcode_hash)
user = db.get_user(username)
db.update_user(user)

# Notes
db.save_note(note)
db.get_note(note_id)
db.get_project_notes(project_id)
```

### VectorDatabase

**Location**: `socratic_system.database.VectorDatabase`

```python
from socratic_system.database import VectorDatabase

vector_db = VectorDatabase(db_path)

# Add knowledge
vector_db.add_knowledge(knowledge_entry)

# Search similar
results = vector_db.search_similar(
    query="How do I implement authentication?",
    top_k=5,
    project_id="proj_123"  # Optional filter
)

# Get project knowledge
knowledge = vector_db.get_project_knowledge(project_id)

# Delete
vector_db.delete_entry(entry_id)
```

---

## Event System

### EventEmitter API

**Location**: `socratic_system.events.EventEmitter`

#### Subscribe to Event

```python
def my_handler(data):
    print(f"Project created: {data['project_id']}")

orchestrator.event_emitter.on(EventType.PROJECT_CREATED, my_handler)
```

#### One-Time Listener

```python
def on_first_code(data):
    print(f"Code generated: {data['filename']}")

orchestrator.event_emitter.once(EventType.CODE_GENERATED, on_first_code)
```

#### Remove Listener

```python
orchestrator.event_emitter.remove_listener(EventType.PROJECT_CREATED, my_handler)
```

### Event Types

```python
from socratic_system.events import EventType

# Agent lifecycle
EventType.AGENT_START
EventType.AGENT_COMPLETE
EventType.AGENT_ERROR

# Project events
EventType.PROJECT_CREATED
EventType.PROJECT_SAVED
EventType.PROJECT_LOADED
EventType.PROJECT_ARCHIVED
EventType.PROJECT_RESTORED
EventType.PROJECT_DELETED

# Dialogue
EventType.QUESTION_GENERATED
EventType.RESPONSE_RECEIVED
EventType.PHASE_ADVANCED
EventType.HINT_PROVIDED

# Conflicts
EventType.CONFLICT_DETECTED
EventType.CONFLICT_RESOLVED

# Knowledge
EventType.KNOWLEDGE_LOADED
EventType.KNOWLEDGE_SUGGESTION
EventType.KNOWLEDGE_ADDED
EventType.DOCUMENT_IMPORTED

# Code
EventType.CODE_GENERATED
EventType.CODE_ANALYSIS_COMPLETE
EventType.DOCUMENTATION_GENERATED

# System
EventType.TOKEN_USAGE
EventType.SYSTEM_INITIALIZED
EventType.PROGRESS_UPDATE
EventType.LOG_DEBUG
EventType.LOG_INFO
EventType.LOG_WARNING
EventType.LOG_ERROR
```

---

## Configuration API

### SocratesConfig

**Location**: `socratic_system.config.SocratesConfig`

```python
from socratic_system.config import SocratesConfig
from pathlib import Path

# From environment
config = SocratesConfig.from_env()

# From dictionary
config = SocratesConfig.from_dict({
    "api_key": "sk-ant-...",
    "log_level": "DEBUG",
    "data_dir": "/custom/path"
})
```

### ConfigBuilder

**Location**: `socratic_system.config.ConfigBuilder`

```python
from socratic_system.config import ConfigBuilder
from pathlib import Path

config = ConfigBuilder("sk-ant-...") \
    .with_data_dir(Path("/data")) \
    .with_model("claude-opus-4-5-20251101") \
    .with_embedding_model("all-MiniLM-L6-v2") \
    .with_log_level("DEBUG") \
    .with_log_file(Path("/logs/socratic.log")) \
    .with_max_retries(5) \
    .with_token_warning_threshold(0.7) \
    .with_custom_knowledge(["Knowledge 1", "Knowledge 2"]) \
    .build()
```

---

## Models & Data Types

### ProjectContext

**Location**: `socratic_system.models.ProjectContext`

```python
from socratic_system.models import ProjectContext
from datetime import datetime

project = ProjectContext(
    project_id="proj_123",
    name="My App",
    owner="alice",
    collaborators=["bob"],

    # Specifications
    goals="Create photo sharing app for families",
    requirements=["Auto-organize by date", "Face recognition"],
    tech_stack=["React", "Python", "PostgreSQL"],
    constraints=["$50/month budget", "Launch in 3 months"],

    # Technical
    language_preferences=["Python", "JavaScript"],
    deployment_target="AWS",
    code_style="PEP 8",

    # State
    phase="discovery",  # discovery, analysis, design, implementation
    conversation_history=[],
    status="active",    # active, completed, on-hold
    progress=0,         # 0-100
    archived=False,

    # Metadata
    created_at=datetime.now(),
    updated_at=datetime.now(),
    conflicts=[]
)

# Access/modify
project.goals += " and organize by people"
project.phase = "analysis"
project.save()  # Persist to database
```

### KnowledgeEntry

**Location**: `socratic_system.models.KnowledgeEntry`

```python
from socratic_system.models import KnowledgeEntry

entry = KnowledgeEntry(
    id="auth_oauth",
    content="OAuth 2.0 is an authorization framework...",
    category="authentication",
    metadata={
        "topic": "OAuth",
        "difficulty": "intermediate",
        "domain": "security",
        "tags": ["authentication", "security"]
    },
    embedding=None  # Will be generated automatically
)
```

### User

**Location**: `socratic_system.models.User`

```python
from socratic_system.models import User

user = User(
    username="alice",
    passcode_hash="sha256_hash_here",
    projects=["proj_123", "proj_456"],
    is_archived=False,
    created_at=datetime.now()
)
```

### ProjectNote

**Location**: `socratic_system.models.ProjectNote`

```python
from socratic_system.models import ProjectNote

note = ProjectNote(
    note_id="note_123",
    project_id="proj_123",
    note_type="design",  # design, bug, idea, task, general
    title="Use microservices",
    content="Microservices allow independent scaling",
    created_by="alice",
    tags=["architecture", "scalability"],
    created_at=datetime.now()
)
```

---

## Usage Examples

### Complete Project Workflow

```python
from socratic_system.orchestration import AgentOrchestrator

# Initialize
orchestrator = AgentOrchestrator("sk-ant-...")

# Create project
project_result = orchestrator.process_request('project_manager', {
    'action': 'create_project',
    'project_name': 'My App',
    'owner': 'alice'
})
project_id = project_result['project']['project_id']

# Dialogue - Discovery
for i in range(3):
    # Get question
    q_result = orchestrator.process_request('socratic_counselor', {
        'action': 'generate_question',
        'project_id': project_id
    })
    question = q_result['question']
    print(f"Q: {question}")

    # Get response (simulated)
    response = input("Your answer: ")

    # Process response
    r_result = orchestrator.process_request('socratic_counselor', {
        'action': 'process_response',
        'project_id': project_id,
        'response': response
    })

    # Check for conflicts
    conflicts = r_result.get('conflicts', [])
    if conflicts:
        print(f"⚠️ {len(conflicts)} conflicts detected!")

# Advance to analysis
orchestrator.process_request('socratic_counselor', {
    'action': 'advance_phase',
    'project_id': project_id
})

# Generate code
code_result = orchestrator.process_request('code_generator', {
    'action': 'generate_script',
    'project_id': project_id
})

print(code_result['code'])
```

### Event Monitoring

```python
from socratic_system.events import EventType

# Monitor token usage
def on_token_usage(data):
    print(f"Tokens: {data['total_tokens']}, Cost: ${data['cost_estimate']:.4f}")

orchestrator.event_emitter.on(EventType.TOKEN_USAGE, on_token_usage)

# Monitor code generation
def on_code_generated(data):
    with open(f"/output/{data['filename']}", 'w') as f:
        f.write(data['code'])

orchestrator.event_emitter.on(EventType.CODE_GENERATED, on_code_generated)

# Monitor conflicts
def on_conflict(data):
    print(f"Conflict: {data['description']}")

orchestrator.event_emitter.on(EventType.CONFLICT_DETECTED, on_conflict)
```

### Knowledge Base Integration

```python
from socratic_system.models import KnowledgeEntry

# Add custom knowledge
orchestrator.process_request('knowledge_manager', {
    'action': 'add_knowledge',
    'entry': KnowledgeEntry(
        id='company_standards',
        content='Our company uses Python 3.11+, FastAPI, PostgreSQL, React',
        category='company',
        metadata={'topic': 'tech_stack'}
    )
})

# Import documentation
result = orchestrator.process_request('document_agent', {
    'action': 'import_file',
    'file_path': '/docs/architecture.pdf',
    'project_id': 'proj_123'
})

# Search knowledge
from socratic_system.database import VectorDatabase

vector_db = orchestrator.vector_db
results = vector_db.search_similar(
    query="How should I structure a REST API?",
    project_id='proj_123'
)

for result in results:
    print(f"Topic: {result['metadata']['topic']}")
    print(f"Content: {result['content'][:100]}...")
```

---

## Error Handling

### Exception Hierarchy

```python
from socratic_system.exceptions import (
    SocratesError,
    ConfigurationError,
    AgentError,
    DatabaseError,
    ProjectNotFoundError,
    UserNotFoundError,
    ValidationError,
    APIError
)

try:
    project = db.load_project('nonexistent')
except ProjectNotFoundError:
    print("Project not found")
except DatabaseError as e:
    print(f"Database error: {e}")
except SocratesError as e:
    print(f"System error: {e}")
```

---

## Best Practices

1. **Always use context managers** for database operations
2. **Check result status** before accessing data
3. **Handle events** for observable system behavior
4. **Use async methods** for high-concurrency scenarios
5. **Validate configuration** before creating orchestrator
6. **Monitor token usage** to control costs
7. **Implement error handling** for API calls
8. **Use proper logging** for debugging

---

## Migration Guide

### From CLI to Programmatic API

```python
# Instead of: /project create
orchestrator.process_request('project_manager', {
    'action': 'create_project',
    'project_name': 'My App',
    'owner': 'alice'
})

# Instead of: /code generate
orchestrator.process_request('code_generator', {
    'action': 'generate_script',
    'project_id': 'proj_123'
})

# Instead of: /query ask "..."
vector_db = orchestrator.vector_db
results = vector_db.search_similar(
    query="...",
    top_k=5
)
```

---

**Last Updated**: December 2025
**Version**: 7.0
