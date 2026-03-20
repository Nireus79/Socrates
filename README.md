# Socrates AI - Socratic Method Tutoring System

**Self-hosted platform for AI-guided collaborative projects development using the Socratic method with multi-agent orchestration, RAG, and knowledge management.**

![SocratesSS](https://github.com/user-attachments/assets/233891d6-b983-42a7-8e85-1040e99024f1)

## What is Socrates?

Socrates is a production-ready Python framework that implements the Socratic method using Claude AI to help software development teams think through complex architectural and design decisions. Rather than providing direct answers, Socrates asks carefully crafted questions to guide teams toward their own solutions, promoting deeper understanding and better decision-making.

**Key insight**: Socrates uses Claude AI not to solve problems directly, but to ask better questions.

## Core Features

### 🤔 Socratic Method
- AI-guided questioning to help teams think through design problems
- Guides users toward better solutions through dialogue
- Promotes collaborative problem-solving
- Context-aware questions based on project state

### 🤖 Multi-Agent Orchestration
Specialized agents for different development tasks:
- **Code Generator**: Generates code with explanations
- **Conflict Detector**: Identifies design/specification conflicts
- **Context Analyzer**: Analyzes project context and dependencies
- **Document Processor**: Processes and indexes documents
- **Learning Agent**: Tracks user interactions and learning patterns
- **And more**: 10+ specialized agents

### 📚 Knowledge Management (RAG)
- Vector-based document search using ChromaDB
- Retrieval-Augmented Generation for intelligent context
- Multi-document indexing and querying
- Semantic search across knowledge base

### 💾 Persistent Storage
- Project management and tracking
- User sessions and history
- Knowledge base with versioning
- Team member and access control

### 🔐 Production Features
- JWT authentication
- Multi-factor authentication (TOTP)
- Role-based access control (RBAC)
- API rate limiting
- Comprehensive logging and monitoring
- Error tracking and reporting

### ⚡ Performance & Scale
- Async/await support for concurrent operations
- Redis caching with in-memory fallback
- Connection pooling for databases
- Optimized vector search
- Cross-platform compatible (Windows, Linux, macOS)

## Architecture

Socrates is built on a modular library architecture:

```
┌─────────────────────────────────────────┐
│     socratic-core (Configuration,       │
│     Events, Exceptions, Logging, Utils) │
└────────────┬────────────────────────────┘
             │
    ┌────────┼────────┬────────────┐
    │        │        │            │
    ▼        ▼        ▼            ▼
 socratic- socratic- socratic-   socratic-
 rag       agents    analyzer    knowledge
 (RAG)     (Agents)  (Analysis)  (Storage)
    │        │        │            │
    └────────┼────────┼────────────┘
             │
    ┌────────▼────────────────────┐
    │ Specialized Libraries:       │
    │ - socratic-learning         │
    │ - socratic-workflow         │
    │ - socratic-conflict         │
    └────────┬────────────────────┘
             │
    ┌────────┴──────────┬──────────┐
    │                   │          │
    ▼                   ▼          ▼
 socrates-cli      socrates-api   Socrates
 (CLI Tool)        (REST API)     (Main App)
```

### Component Overview

**socratic-core**: Foundation library providing configuration, event system, exceptions, logging, and utilities

**socratic-rag**: Retrieval-Augmented Generation system for intelligent document search and context

**socratic-agents**: Multi-agent system with specialized agents for different tasks

**socratic-knowledge**: Knowledge base management with versioning and access control

**socratic-learning**: User interaction tracking, learning pattern detection, maturity calculation

**socratic-analyzer**: Code and context analysis with LLM-powered insights

**socratic-workflow**: Workflow orchestration with cost tracking

**socratic-conflict**: Conflict detection and resolution

**socrates-cli**: Command-line interface for Socrates

**socrates-api**: REST API server built with FastAPI

**Socrates**: Main application integrating all components with orchestration layer

---

## Published Libraries on PyPI

All Socrates components are available as standalone PyPI packages. You can install only what you need.

### Core & Framework

| Package | Version | PyPI | Purpose |
|---------|---------|------|---------|
| **socratic-core** | 0.1.1+ | [socratic-core](https://pypi.org/project/socratic-core/) | Foundation: config, events, exceptions, logging, utils |
| **socratic-learning** | 0.1.1+ | [socratic-learning](https://pypi.org/project/socratic-learning/) | Learning engine, interaction tracking, maturity calculation |

### Agent & RAG

| Package | Version | PyPI | Purpose |
|---------|---------|------|---------|
| **socratic-agents** | 0.1.0+ | [socratic-agents](https://pypi.org/project/socratic-agents/) | Multi-agent orchestration with specialized agents |
| **socratic-rag** | 0.1.0+ | [socratic-rag](https://pypi.org/project/socratic-rag/) | Retrieval-Augmented Generation with vector search |
| **socratic-analyzer** | 0.1.0+ | [socratic-analyzer](https://pypi.org/project/socratic-analyzer/) | Code analysis with LLM-powered insights |

### Specialized & Utilities

| Package | Version | PyPI | Purpose |
|---------|---------|------|---------|
| **socratic-knowledge** | 0.1.0+ | [socratic-knowledge](https://pypi.org/project/socratic-knowledge/) | Knowledge base management with versioning |
| **socratic-workflow** | 0.1.0+ | [socratic-workflow](https://pypi.org/project/socratic-workflow/) | Workflow orchestration with cost tracking |
| **socratic-conflict** | 0.1.0+ | [socratic-conflict](https://pypi.org/project/socratic-conflict/) | Conflict detection and resolution |

### Integration & Tools

| Package | Version | PyPI | Purpose |
|---------|---------|------|---------|
| **socratic-openclaw-skill** | 0.1.0+ | [socratic-openclaw-skill](https://pypi.org/project/socratic-openclaw-skill/) | OpenClaw skill for Socratic discovery |
| **socrates-ai-langraph** | 0.1.0+ | [socrates-ai-langraph](https://pypi.org/project/socrates-ai-langraph/) | LangGraph integration framework |
| **socrates-cli** | 0.1.0+ | [socrates-cli](https://pypi.org/project/socrates-cli/) | Command-line interface tools |
| **socrates-core-api** | 0.1.0+ | [socrates-core-api](https://pypi.org/project/socrates-core-api/) | REST API base framework |

### Installation by Use Case

```bash
# Minimal installation (just the framework)
pip install socratic-core>=0.1.1

# Learning system (recommended for most users)
pip install socratic-core>=0.1.1 socratic-learning>=0.1.1

# Full RAG capabilities
pip install socratic-core>=0.1.1 socratic-rag>=0.1.0

# Multi-agent orchestration
pip install socratic-core>=0.1.1 socratic-agents>=0.1.0

# OpenClaw integration
pip install socratic-openclaw-skill>=0.1.0

# LangGraph integration
pip install socrates-ai-langraph>=0.1.0

# Everything (kitchen sink)
pip install socratic-core socratic-learning socratic-agents socratic-rag socratic-analyzer socratic-knowledge socratic-workflow socratic-conflict socrates-cli socrates-core-api
```

---

## Quick Start

### Installation

```bash
# Install the main package
pip install socrates-ai

# OR install specific components
pip install socratic-core                      # Just the framework
pip install socratic-core socrates-cli         # Framework + CLI
pip install socratic-core socratic-rag         # Framework + RAG
```

### Basic Usage

```python
import socrates
from socratic_core import EventType

# Create a config
config = socrates.SocratesConfig(
    api_key="your-anthropic-key",
    data_dir="/path/to/data"
)

# Create orchestrator
orchestrator = socrates.create_orchestrator(config)

# Listen to events
def on_question_generated(data):
    print(f"Question: {data.get('question')}")

orchestrator.event_emitter.on(
    EventType.QUESTION_GENERATED,
    on_question_generated
)

# Process request
result = await orchestrator.process_request_async(
    agent_name="socratic_counselor",
    action_data={
        "project_id": "proj_123",
        "context": "We need to decide between microservices and monolith",
        "constraints": ["team size: 5", "2-year timeline"]
    }
)

print(result["question"])
```

### CLI Usage

```bash
# Create a new project
socrates project create --name "My API" --owner "alice"

# Start interactive session
socrates project chat proj_123

# Search knowledge base
socrates knowledge search proj_123 "authentication"

# View project details
socrates project info proj_123
```

### REST API

```bash
# Start the API server
socrates-api --port 8000

# Create a project via API
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "My Project", "owner": "alice"}'

# Ask a Socratic question
curl -X POST http://localhost:8000/projects/proj_123/question \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"context": "Monolith vs microservices"}'
```

## Use Cases

### 1. Architectural Decision Making
Help teams evaluate different architecture approaches by asking targeted questions about requirements, constraints, and trade-offs.

### 2. Code Review & Design Discussion
Use agents to analyze code, detect potential conflicts, and guide teams through resolution discussions.

### 3. Team Learning & Onboarding
Track team members' learning patterns and provide personalized guidance based on their interaction history.

### 4. Knowledge Management
Maintain a searchable knowledge base of project decisions, patterns, and best practices with RAG.

### 5. Project Documentation
Automatically generate documentation and decision records from project interactions.

## Production Deployment

### Docker

```bash
# Build Docker image
docker build -t socrates:latest .

# Run with Docker Compose
docker-compose up -d

# Access API at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Kubernetes

```bash
# Deploy with Kubernetes manifests
kubectl apply -f k8s/

# Or use Helm chart
helm install socrates ./helm/socrates
```

## Configuration

Socrates can be configured via:

1. **Environment Variables**
```bash
ANTHROPIC_API_KEY=sk-ant-...
SOCRATES_DATA_DIR=/data/socrates
SOCRATES_DB_URL=postgresql://user:pass@localhost/socrates
SOCRATES_REDIS_URL=redis://localhost:6379
```

2. **Configuration File** (YAML/JSON)
```yaml
api_key: sk-ant-...
data_dir: /data/socrates
database:
  url: postgresql://user:pass@localhost/socrates
  pool_size: 20
redis:
  url: redis://localhost:6379
logging:
  level: INFO
```

3. **Python Code**
```python
config = socrates.SocratesConfig(
    api_key="sk-ant-...",
    data_dir="/data/socrates",
    log_level="DEBUG",
    database_url="postgresql://..."
)
```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login with JWT
- `POST /auth/logout` - Logout
- `POST /auth/mfa/setup` - Setup MFA

### Projects
- `POST /projects` - Create project
- `GET /projects` - List user's projects
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project
- `POST /projects/{id}/advance-phase` - Move to next phase

### Socratic Interaction
- `POST /projects/{id}/question` - Get Socratic question
- `POST /projects/{id}/question/answer` - Submit answer
- `GET /projects/{id}/question/history` - Get question history

### Knowledge Management
- `POST /projects/{id}/knowledge` - Add knowledge entry
- `GET /projects/{id}/knowledge` - List knowledge entries
- `GET /projects/{id}/knowledge/search` - Search knowledge

### Analytics
- `GET /projects/{id}/analytics` - Project analytics
- `GET /projects/{id}/insights` - Generated insights

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for complete documentation.

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Setup pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# All tests
pytest tests/ -v --cov=socratic_system

# Specific categories
pytest tests/unit/ -v
pytest tests/integration/ -v

# With coverage report
pytest --cov=socratic_system --cov-report=html
```

### Code Quality

```bash
# Format code
black socratic_system/ socrates-api/ socrates-cli/

# Lint
ruff check socratic_system/ socrates-api/ socrates-cli/

# Type checking
mypy socratic_system/ --ignore-missing-imports

# Security scan
bandit -r socratic_system/ socrates-api/
```

## Documentation

- **[Installation Guide](INSTALL.md)** - Complete setup instructions
- **[Quick Start Guide](QUICKSTART.md)** - 5-minute tutorial
- **[Architecture Documentation](ARCHITECTURE.md)** - System design and components
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[CLI Reference](socrates-cli/README.md)** - Command-line tool guide
- **[Configuration Guide](docs/CONFIGURATION.md)** - Configuration options
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Development guidelines
- **[Contributing](docs/CONTRIBUTING.md)** - Contribution guidelines

## Technology Stack

- **Language**: Python 3.11+
- **LLM**: Claude (via Anthropic API)
- **API Framework**: FastAPI
- **Databases**: PostgreSQL, SQLite
- **Vector Store**: ChromaDB
- **Caching**: Redis
- **Frontend**: React (if included)
- **Deployment**: Docker, Kubernetes, Helm
- **Testing**: pytest, pytest-cov
- **Code Quality**: ruff, mypy, black, bandit

## 🔄 Latest Updates

### Recent Changes (March 2026)
- ✅ Fixed MaturityCalculator import issue - now correctly imports from `socratic_learning` package
- ✅ Improved module resolution for external dependencies
- ✅ Enhanced API stability and reliability

### 🎯 Open for Review & Contributions

**I'm actively seeking:**
- **Code Reviews** - Feedback on architecture, design patterns, and code quality
- **Bug Reports** - Issues, edge cases, or unexpected behaviors
- **Corrections** - Grammar, documentation, or technical inaccuracies
- **Suggestions** - Improvements, optimizations, or new features
- **Pull Requests** - Contributions to fix bugs or add features

This is a collaborative learning project. All feedback, whether critical or constructive, helps improve the codebase. Don't hesitate to open issues or PRs!

## Community & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/Nireus79/Socrates/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/Nireus79/Socrates/discussions)
- **Pull Requests**: [Submit code reviews and contributions](https://github.com/Nireus79/Socrates/pulls)
- **Documentation**: [Full docs](docs/)
- **Contributing**: [Contribution guide](docs/CONTRIBUTING.md)

## Sponsorship

Socrates is free and open-source. Support development through GitHub Sponsors:

- **Supporter ($5/month)**: 10 projects, 5 team members
- **Contributor ($15/month)**: Unlimited projects, members, storage
- **Custom ($25+/month)**: Enterprise features + priority support

[Become a Sponsor](https://github.com/sponsors/Nireus79)

## License

MIT License - see [LICENSE](LICENSE) for details

## Acknowledgments

Built with:
- [Claude AI](https://anthropic.com) by Anthropic
- [FastAPI](https://fastapi.tiangolo.com/) for REST API
- [PostgreSQL](https://www.postgresql.org/) for data persistence
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [Redis](https://redis.io/) for caching
- And the open-source community
