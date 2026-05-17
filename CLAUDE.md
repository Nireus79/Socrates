# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Socrates AI** is a production-ready, modular multi-agent orchestration platform that applies the Socratic method to human-AI communication. It solves the "context problem"—where undefined context causes miscommunication—by systematically questioning and extracting explicit project definitions before implementation.

**Key Capabilities:**
- Multi-agent orchestration with constitutional AI governance
- RAG (Retrieval-Augmented Generation) knowledge management
- Socratic dialogue system for project definition refinement
- Production-grade infrastructure (Kubernetes-ready, monitored, secured)
- REST API, Python library, and CLI interfaces
- Modular architecture: 37+ internal modules + 8 specialized external libraries

**Platform Deployments:**
- REST API: FastAPI server with PostgreSQL, Redis, ChromaDB
- Frontend: React-based UI (socrates-frontend)
- CLI: Command-line interface (socrates-cli)
- Python Package: PyPI package for library embedding (socrates-ai)

---

## Architecture & Code Organization

### Core Modules (`socratic_system/`)

The main codebase is organized into functional modules:

| Module | Purpose |
|--------|---------|
| **orchestration, agents** | Multi-agent request routing and agent coordination |
| **knowledge, learning, maturity** | RAG systems, user analytics, project progression tracking |
| **governance, reasoning, conflict** | Constitutional AI, ethical decision-making, requirement validation |
| **api, api_adapter** | REST API endpoints, framework integrations (LangChain, LangGraph) |
| **database, models, repositories** | PostgreSQL, ChromaDB, SQLite persistence layer |
| **auth, security** | JWT authentication, MFA, RBAC |
| **workflow, handlers, jobs** | Background task processing and async operations |
| **config, di_container** | Dependency injection and multi-environment setup |
| **core, utils, exceptions** | Base classes, helpers, error handling |

### External Specialized Libraries

Eight independently-maintained `socratic-*` libraries extend core functionality:
- **socratic-morality**: Constitutional AI and ethical governance
- **socratic-agents**: Agent behavior templates and specialization
- **socratic-nexus**: Real-time collaboration and message streaming
- **socratic-maturity**: Project maturity evaluation
- **socratic-knowledge**: Knowledge extraction and RAG
- Others for specific domains (e.g., workflow, learning, governance)

### Directory Structure

```
socratic_system/          # Main orchestration platform (37 modules)
socrates-api/             # FastAPI server and REST endpoints
socrates-frontend/        # React UI application
socrates-cli/             # Command-line interface
tests/                    # Unit, integration, and e2e test suite
deployment/               # Docker, Kubernetes, and configuration
docs/                     # Documentation and architecture guides
```

---

## Essential Commands

### Setup & Environment

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies (includes dev tools)
pip install -e ".[dev]"
pip install -r requirements-dev.txt  # If exists

# View installed packages
pip list | grep socratic

# Check environment
python3 -c "import socratic_system; print('✓ socratic_system imported')"
```

### Running the Application

```bash
# Start API server (default port 8000)
socrates-api --port 8000

# Or via FastAPI directly
python -m socrates_api.main --port 8000

# Start CLI
socrates --help
socrates run-agent --agent-name socratic_counselor

# Docker Compose (all services: API, frontend, DB, cache)
docker-compose -f deployment/docker/docker-compose.yml up -d
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=socratic_system --cov-report=html

# Run specific test categories
pytest -m unit              # Unit tests only (fast)
pytest -m integration       # Integration tests
pytest -m e2e              # End-to-end tests

# Run specific test file or pattern
pytest tests/test_agents.py                          # Single file
pytest tests/ -k "test_agent_routing"               # Pattern match
pytest tests/test_agents.py::TestAgentOrchestrator  # Specific class

# Run with increased verbosity
pytest -vv

# Run stopping after first failure
pytest -x

# Run with custom timeout (default 60s)
pytest --timeout=120

# Parallel testing (requires pytest-xdist)
pytest -n auto

# Run and display print statements
pytest -s
```

### Code Quality

```bash
# Format code with Black
black socratic_system/ tests/

# Lint with flake8 / ruff
ruff check socratic_system/ tests/
ruff check --fix socratic_system/    # Auto-fix violations

# Type checking with mypy
mypy socratic_system/ --ignore-missing-imports

# Run pre-commit hooks
pre-commit run --all-files

# Check docstring style
pydocstyle socratic_system/
```

### Building & Packaging

```bash
# Build distribution
python -m build

# Build wheel only
python -m build --wheel

# Install in editable mode (for development)
pip install -e .

# Create source distribution
python -m build --sdist
```

---

## Key Development Patterns

### Agent Implementation

Agents in Socrates are specialized AI components with distinct roles. When adding a new agent:

1. **Create agent class** in `socratic_system/agents/` inheriting from base agent
2. **Define capabilities** (what the agent can do)
3. **Implement execute()** method for agent-specific logic
4. **Register in orchestrator** (DI container or agent registry)
5. **Add constitutional constraints** if ethical decisions are involved

**Example:** Look at `socratic_system/agents/` for patterns like `socratic_counselor`, `code_reviewer`, etc.

### Knowledge Management (RAG)

When working with knowledge/RAG features:

1. **Knowledge ingestion** happens in `socratic_system/knowledge/`
2. **Vector embeddings** stored in ChromaDB for semantic search
3. **RAG retrieval** happens during agent decision-making
4. **Learning/feedback** updates knowledge quality over time

**Key class:** `KnowledgeManager` in `socratic_system/knowledge/`

### Constitutional AI & Governance

Agents make decisions that are evaluated against constitutional principles:

1. **Ethical frameworks** from `socratic-morality` library
2. **Governance module** evaluates agent outputs
3. **Reasoning module** provides transparency (why a decision was made)
4. **Conflict resolution** when multiple agents disagree

**Key class:** `GovernanceEngine` in `socratic_system/governance/`

### Database & Persistence

PostgreSQL is the primary database with SQLAlchemy ORM:

1. **Models** defined in `socratic_system/models/`
2. **Repositories** in `socratic_system/repositories/` (data access layer)
3. **Migrations** via Alembic (in `deployment/migrations/`)
4. **ChromaDB** for vector storage (knowledge vectors)
5. **Redis** for caching and sessions

**Connection handling:** Via `socratic_system/database/` with connection pooling

---

## Testing Strategy

### Test Markers (from pytest.ini)

Use markers to categorize and filter tests:

```python
@pytest.mark.unit              # Fast, isolated tests (no external deps)
@pytest.mark.integration       # Tests component interactions
@pytest.mark.e2e              # Full user workflows
@pytest.mark.api              # REST endpoint tests
@pytest.mark.requires_api     # Tests needing valid API keys
@pytest.mark.requires_db      # Tests needing a database
@pytest.mark.async            # Async operation tests
@pytest.mark.slow             # Tests taking >1 second
```

### Test Isolation

- **@pytest.mark.test_isolation**: Use when test order or state affects results
- Database state should be cleaned up between tests
- Async tests use `asyncio_mode = "auto"` (defined in pyproject.toml)
- Mocking is preferred for external dependencies (API calls, file I/O)

### Running Tests Locally

```bash
# Quick smoke test (unit only)
pytest -m unit -q

# Full test suite with coverage
pytest --cov=socratic_system

# Check a specific agent's tests
pytest tests/ -k "agent_name" -v

# Debug test execution
pytest -vv --tb=long tests/test_specific.py::test_name
```

### Adding New Tests

- Place tests in `tests/` matching file structure: `test_module_name.py`
- Follow test class naming: `Test<ModuleName>`
- Use descriptive function names: `test_<behavior>_<condition>_<expected>`
- Mark with appropriate marker (`@pytest.mark.unit`, etc.)

---

## Common Development Tasks

### Adding a New API Endpoint

1. Define request/response models in `socratic_system/models/`
2. Implement handler in `socratic_system/api/handlers/`
3. Register route in `socrates_api/routes.py`
4. Add integration tests in `tests/api/`
5. Update API docs (auto-generated from Pydantic models)

### Modifying Database Schema

1. Create migration: `alembic revision --autogenerate -m "description"`
2. Review and edit migration file in `deployment/migrations/versions/`
3. Apply migration: `alembic upgrade head`
4. Update SQLAlchemy models in `socratic_system/models/`

### Adding Constitutional Constraints

1. Define ethical principle in your agent's code
2. Use `socratic_morality` library (from `socratic-morality` package)
3. Integrate with `GovernanceEngine` to validate decisions
4. Test ethical decision-making via `test_governance`

### Integrating External Data Source

1. Create adapter in `socratic_system/api_adapter/` or `clients/`
2. Implement async client for external API/service
3. Add knowledge ingestion pipeline
4. Register with knowledge manager
5. Test with `@pytest.mark.requires_api` (if external API needed)

---

## Environment & Configuration

### Configuration Files

- **.env.example**: Template for environment variables
- **pyproject.toml**: Project metadata, dependencies, tool configs
- **.pre-commit-config.yaml**: Git hooks for code quality
- **docker-compose.yml**: Local development with all services

### Key Environment Variables

```bash
ANTHROPIC_API_KEY        # Claude API key (required for agents)
DATABASE_URL            # PostgreSQL connection string
REDIS_URL              # Redis cache connection
CHROMADB_PATH          # Path for ChromaDB vector storage
JWT_SECRET_KEY         # Secret for JWT token signing
LOG_LEVEL              # Logging level (DEBUG, INFO, WARNING, ERROR)
```

### Dependency Injection

The `di_container.py` manages dependency resolution. When modifying services:

1. Register new services in `DIContainer`
2. Use `@inject` decorator or container.get() for retrieval
3. Async services use appropriate lifecycle management

---

## Debugging & Troubleshooting

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
socrates-api --port 8000

# Or in Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Database Connection

```python
from socratic_system.database import get_db
async with get_db() as session:
    result = await session.execute("SELECT 1")
    print("✓ Database connected")
```

### Test API Endpoints

```bash
# Interactive API docs (when server running)
curl http://localhost:8000/docs

# Test endpoint
curl -X POST http://localhost:8000/api/agents/request \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "socratic_counselor", "payload": {}}'
```

### Common Issues

- **Import errors**: Ensure `.venv` is activated and dependencies installed (`pip install -e ".[dev]"`)
- **API key missing**: Set `ANTHROPIC_API_KEY` environment variable
- **Database connection fails**: Check `DATABASE_URL` and PostgreSQL is running (or use SQLite)
- **Test timeouts**: Some tests may need more time; use `pytest --timeout=120`

---

## CI/CD Pipeline

The project uses GitHub Actions (in `.github/workflows/`):

- **lint.yml**: Code formatting, type checking, linting
- **test.yml**: Unit, integration, and e2e test suite
- **frontend-tests.yml**: React frontend testing
- **publish.yml**: Publish to PyPI on release
- **docker-publish.yml**: Build and push Docker images
- **release.yml**: Automated release management

**Pre-commit hooks** (`.pre-commit-config.yaml`) enforce code quality locally before commits.

---

## Important Notes

- **Async everywhere**: Most I/O operations (DB, API calls) are async. Use `async`/`await` and `asyncio` patterns
- **Type hints**: Required for new code. Use Python 3.8+ type annotations
- **API versioning**: REST API supports multiple versions (check routes for version info)
- **Backward compatibility**: When modifying schemas, ensure migrations support older clients
- **Logging**: Use Python `logging` module with structured output for production debugging
- **Error handling**: Raise `socratic_system.exceptions.SocratesError` subclasses, not generic Exception

---

## Useful Resources

- **Main README**: Architecture overview and quick start
- **WHAT_SOCRATES_ACTUALLY_DOES_AND_HOW.md**: Deep dive on Socratic method and problem-solving approach
- **ECOSYSTEM.md**: Complete feature breakdown and library descriptions
- **SUBSCRIPTION_SYSTEM.md**: Subscription/user management details (if applicable)
- **GitHub Issues**: For bugs, features, and discussions
- **PyPI Packages**: Each `socratic-*` library has its own documentation on PyPI