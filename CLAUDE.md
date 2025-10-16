# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Socratic RAG Enhanced v7.4.0** - An AI-powered Socratic questioning and code generation system using Anthropic's Claude API. The system employs RAG (Retrieval-Augmented Generation) with ChromaDB for context-aware interactions, project management with multi-user collaboration, automated code generation with IDE integration, and **architecture optimization with greedy algorithm prevention**.

**Current Development Phase:** Phase B - Extensions (C6 Architecture Optimizer ✅ COMPLETE! Moving to C2)
**See:** `docs/TODO.md` and `docs/MASTER_PLAN.md` for detailed roadmap
**Priority Order:** ✅ C6 (DONE) → C2 → C1 → C4 → C3 → C5 → UI → Tests

## Architecture

### Core Components

**Service Container Pattern (Dependency Injection)**
- `src/core.py` - Central system infrastructure with `ServiceContainer` that manages all configured service instances
- Services are initialized via `ServiceFactory.create_services()` which returns a `ServiceContainer` containing:
  - `SystemConfig` - Configuration management with YAML file and environment variable support
  - `SystemLogger` - Centralized logging with file rotation
  - `EventSystem` - Event bus for system-wide async communication
  - `DatabaseManager` - SQLite connection pooling and transaction management
- All agents and services receive the `ServiceContainer` via dependency injection in their constructors

**Agent System (9 Core Agents)** ⭐ NEW: Architecture Optimizer Added!
- `src/agents/orchestrator.py` - `AgentOrchestrator` coordinates all other agents with intelligent routing by agent ID or capability
- `src/agents/base.py` - `BaseAgent` abstract class provides common functionality (logging, events, stats, Claude API client)
- Agent hierarchy:
  1. `UserManagerAgent` (user) - Authentication and user management
  2. `ProjectManagerAgent` (project) - Project lifecycle management
  3. `SocraticCounselorAgent` (socratic) - Socratic questioning methodology
  4. `CodeGeneratorAgent` (code) - Code generation with testing/security scanning
  5. `ContextAnalyzerAgent` (context) - Context analysis with conflict detection
  6. `DocumentProcessorAgent` (document) - Document processing (PDF, DOCX, etc.)
  7. `ServicesAgent` (services) - Git, IDE, and export services
  8. `SystemMonitorAgent` (monitor) - System health monitoring
  9. **`ArchitectureOptimizerAgent` (optimizer) - Meta-level optimization and greedy algorithm prevention** ⭐ NEW!

**Database Layer**
- `src/database/` - Repository pattern with models/repositories separation
- `src/models.py` - SQLAlchemy models for all domain entities
- All repositories follow CRUD pattern: `create()`, `get_by_id()`, `update()`, `delete()`
- Main repositories: users, projects, modules, tasks, socratic_sessions, questions, conversation_messages, technical_specifications, generated_codebases, generated_files

**External Services**
- `src/services/claude_service.py` - Anthropic Claude API integration with rate limiting, cost tracking
- `src/services/git_service.py` - Git operations integration
- `src/services/ide_service.py` - IDE file synchronization (VSCode, PyCharm)
- `src/services/vector_service.py` - ChromaDB vector database for RAG

### Configuration

**Main Configuration: config.yaml**
- All settings centralized in `config.yaml` at project root
- Environment variables override config: prefix with `SOCRATIC_` (e.g., `SOCRATIC_DEBUG=true`)
- Critical environment variables:
  - `ANTHROPIC_API_KEY` or `API_KEY_CLAUDE` - Required for Claude API
  - `SOCRATIC_DB_PATH` - Override database path
  - `SOCRATIC_DATA_PATH` - Override data directory

## Common Development Tasks

### Running the Application

```bash
# Standard run (Flask web application)
python run.py

# With custom port
python run.py --port 8000

# Debug mode with auto-reload
python run.py --debug

# Don't auto-open browser
python run.py --no-browser
```

### Testing

**Test Suite Overview:**
- All tests have proper database isolation - each test gets a fresh database
- Tests use pytest fixtures for setup/teardown
- Mock services are used for agent testing to avoid full system dependencies

```bash
# Run all agent system tests (40 tests)
python tests/test_agents_.py

# Run authorization tests (11 tests - pytest)
python tests/test_authorization.py
# Or with pytest for more control:
python -m pytest tests/test_authorization.py -v

# Run chat mode integration tests
python tests/test_chat_mode_integration.py

# Run conflict persistence tests
python tests/test_conflict_persistence.py

# Run all integration tests
python tests/test_integration.py

# Run with verbose output
python tests/test_integration.py --verbose

# Run specific test
python tests/test_integration.py --test=user_repository

# Run Flask tests
python tests/test_flask.py
```

**Test Database Isolation:**
- Tests automatically delete and recreate `data/socratic.db` before each test
- Use `reset_database()` to clear singleton instances
- Test fixtures use `scope="function"` for proper isolation

**Writing New Tests:**
```python
# Example test with proper database isolation
import pytest
from src.database import get_database, init_database, reset_database

@pytest.fixture(scope="function")
def clean_db():
    """Fixture providing clean database for each test"""
    import os
    db_path = 'data/socratic.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    reset_database()
    init_database()
    return get_database()

def test_something(clean_db):
    db = clean_db
    # Your test code here
    assert db is not None
```

### Database Operations

```bash
# Initialize fresh database (WARNING: destructive)
python -c "from src.database import init_database, reset_database; reset_database(); init_database('data/socratic.db')"

# Get database instance in code
from src.database import get_database
db = get_database()

# Access repositories
users = db.users.get_all()
projects = db.projects.get_by_owner_id(user_id)
```

### Code Generation and Agent Usage

```python
# Initialize service container
from src.core import initialize_system
services = initialize_system('config.yaml')

# Initialize orchestrator
from src.agents.orchestrator import AgentOrchestrator
orchestrator = AgentOrchestrator(services)

# Route request to specific agent
result = orchestrator.route_request(
    agent_id='code_generator',
    action='generate_code',
    data={'requirements': 'Create a REST API', 'project_id': 'proj_123'}
)

# Route by capability (auto-finds correct agent)
result = orchestrator.route_by_capability(
    capability='generate_questions',
    data={'topic': 'API design', 'role': 'developer'}
)
```

### Architecture Optimizer Usage (C6 - NEW!)

The Architecture Optimizer automatically analyzes projects at key workflow points:

**Automatic Triggers:**
1. After technical specification is created (CodeGeneratorAgent)
2. When project phase changes to DESIGN (ProjectManagerAgent)
3. Before code generation begins

**Manual Analysis:**
```python
# Direct optimizer usage
from src.agents.optimizer import ArchitectureOptimizerAgent
optimizer = ArchitectureOptimizerAgent(services)

# Analyze project architecture
result = optimizer.process_request('analyze_architecture', {
    'project_id': 'proj_123',
    'technical_spec': tech_spec_data,
    'analysis_depth': 'deep',  # 'quick', 'deep', or 'comprehensive'
    'user_id': 'user_456'
})

# Result includes:
# - risk_level: 'low', 'medium', 'high', or 'critical'
# - issues_found: List of architectural issues
# - recommendations: Prioritized recommendations
# - tco_analysis: 5-year cost projections
# - alternatives: Alternative approaches with ROI
# - c6_enhanced_tco: Detailed cost breakdown
# - c6_pattern_validation: Design pattern analysis
```

**What C6 Detects:**
- **Greedy Patterns**: MongoDB for relational data, missing scalability requirements, over/under-engineering
- **Anti-Patterns**: God Object, Circular Dependencies, Spaghetti Code, Tight Coupling (13 total)
- **Missing Requirements**: Security, testing, monitoring, performance targets
- **Cost Issues**: High technical debt, maintenance burden, burnout risk
- **Design Smells**: Missing separation of concerns, no error handling strategy

**Enhanced TCO Calculation:**
- Team velocity factors (solo, small, medium, large teams with experience levels)
- Cloud costs (AWS, Azure, GCP, Heroku, DigitalOcean)
- Maintenance burden with complexity multipliers
- Technical debt with compound interest (5-15% per year)
- 5-year projections with refactoring probability

**Example Output:**
```python
{
    'success': True,
    'risk_level': 'medium',
    'issues_found': 3,
    'issues': [
        {
            'type': 'greedy_algorithm',
            'severity': 'high',
            'title': 'MongoDB chosen for relational data',
            'description': '...',
            'estimated_waste_hours': 40,
            'recommendation': 'Consider PostgreSQL for relational requirements'
        }
    ],
    'tco_analysis': {
        'development_hours': 80,
        'maintenance_hours_per_year': 240,
        'technical_debt_hours': 150,
        'c6_enhanced_tco': {
            'year_1_cost_usd': 22560,
            'year_3_cost_usd': 81280,
            'year_5_cost_usd': 156000,
            'risk_factors': ['High maintenance burden: 487h/year'],
            'cost_optimization_opportunities': [...]
        }
    },
    'alternatives': [
        {
            'title': 'Use PostgreSQL instead of MongoDB',
            'estimated_time_savings_hours': 40,
            'recommendation_strength': 'strong'
        }
    ]
}
```

## Important Patterns and Conventions

### Agent Request/Response Pattern

All agents follow standardized request/response format:
- Request: `{'action': str, 'data': Dict[str, Any]}`
- Success response: `{'success': True, 'message': str, 'data': Dict, 'agent_id': str, 'timestamp': str}`
- Error response: `{'success': False, 'message': str, 'error_code': str, 'agent_id': str, 'timestamp': str}`

### Authentication and Authorization Decorators

```python
from src.agents.base import require_authentication, require_project_access

# Requires valid user_id in data, adds _authenticated_user to data
@require_authentication
def _some_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
    user = data['_authenticated_user']
    # ...

# Requires authentication + project access, adds _project and _project_role
@require_project_access
def _project_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
    project = data['_project']
    role = data['_project_role']  # 'owner' or collaborator role
    # ...
```

### Model Status and Enum Usage

Models use enums for status fields. When comparing, use `.value`:
```python
from src.models import UserStatus, ProjectStatus

# Correct enum usage
if user.status == UserStatus.ACTIVE:
    # Handle as enum
    status_str = user.status.value  # Convert to string

# Database queries use .value
active_projects = db.projects.get_by_status(ProjectStatus.ACTIVE.value)
```

### Event System

```python
# Subscribe to events
def on_code_generated(event):
    logger.info(f"Code generated: {event.data}")

services.event_system.subscribe('code_generated', on_code_generated)

# Emit events
services.event_system.emit('code_generated', 'code_agent', {
    'project_id': project_id,
    'files_count': 10
})
```

## File Structure

```
Socrates/
├── config.yaml              # Main configuration file
├── run.py                   # Application entry point
├── src/
│   ├── core.py             # Service container and core infrastructure
│   ├── models.py           # SQLAlchemy database models
│   ├── utils.py            # Utility functions
│   ├── agents/             # 9 core agents + orchestrator
│   │   ├── base.py         # BaseAgent abstract class
│   │   ├── orchestrator.py # Agent coordination
│   │   ├── user.py         # UserManagerAgent
│   │   ├── project.py      # ProjectManagerAgent
│   │   ├── socratic.py     # SocraticCounselorAgent
│   │   ├── code.py         # CodeGeneratorAgent
│   │   ├── context.py      # ContextAnalyzerAgent
│   │   ├── document.py     # DocumentProcessorAgent
│   │   ├── services.py     # ServicesAgent
│   │   ├── monitor.py      # SystemMonitorAgent
│   │   ├── optimizer.py    # ArchitectureOptimizerAgent ⭐ NEW!
│   │   ├── pattern_validator.py  # Design pattern validation ⭐ NEW!
│   │   └── cost_calculator.py    # Enhanced TCO calculation ⭐ NEW!
│   ├── database/           # Database layer
│   │   ├── base.py         # Base repository
│   │   ├── manager.py      # Database manager
│   │   ├── repositories.py # All repository implementations
│   │   └── service.py      # Database service
│   └── services/           # External service integrations
│       ├── claude_service.py   # Anthropic Claude API
│       ├── git_service.py      # Git operations
│       ├── ide_service.py      # IDE integration
│       └── vector_service.py   # ChromaDB vector DB
├── web/                    # Flask web application
│   └── app.py             # Flask app factory
├── tests/                  # Test suites
│   ├── test_integration.py # Main integration tests
│   ├── test_flask.py       # Flask/web tests
│   └── test_agents_.py     # Agent tests
└── data/                   # Runtime data (created automatically)
    ├── socratic.db        # SQLite database
    ├── logs/              # Application logs
    ├── vector_db/         # ChromaDB storage
    ├── uploads/           # User uploads
    ├── exports/           # Exported files
    └── generated_projects/ # Generated code projects
```

## Key Technical Decisions

**Why Service Container?**
- Centralized dependency management avoids circular imports
- Agents can gracefully handle missing services with fallbacks
- Easy to mock services for testing

**Why Agent Orchestrator?**
- Single entry point for all agent interactions
- Capability-based routing allows swapping agent implementations
- Health monitoring and statistics collection
- Graceful degradation when agents fail to initialize

**Why Repository Pattern?**
- Clear separation between database operations and business logic
- Easy to test with mock repositories
- Consistent CRUD interface across all entities

**Why ChromaDB?**
- Embedded vector database requires no separate server
- Automatic embedding generation
- Efficient similarity search for RAG context retrieval

## Troubleshooting

**Import Errors:** The codebase uses fallback imports extensively. If `src.core` is not available, agents create minimal fallback classes. This allows partial functionality even if core system fails.

**Database Errors:** SQLite database is created automatically in `data/socratic.db`. Ensure the `data` directory is writable. Use `reset_database()` to start fresh (WARNING: deletes all data).

**Claude API Errors:** Ensure `ANTHROPIC_API_KEY` environment variable is set. The service includes rate limiting (50 requests per 60 seconds by default) and cost tracking.

**Agent Initialization Failures:** Check logs in `data/logs/socratic.log` and `data/logs/errors.log`. The orchestrator tracks failed agents in `agent_failures` dict and continues with available agents.

**Test Failures - UNIQUE Constraint Errors:** If tests fail with `UNIQUE constraint failed`, the database file wasn't properly deleted. Manually delete `data/socratic.db` and rerun tests. This has been fixed in recent test updates with automatic database cleanup.

**Test Failures - Authentication Required:** Agent methods that use `@require_authentication` or `@require_project_access` decorators need `user_id` in the request data. Always provide a valid `user_id` when testing agent actions.

**ProjectCollaborator Access Issues:** The `require_project_access` decorator checks the `is_active` field (boolean), not a `status` field. Ensure collaborators have `is_active=True` for access.
