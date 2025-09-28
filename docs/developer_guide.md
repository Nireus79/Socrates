# 👩‍💻 Socratic RAG Enhanced - Developer Guide

**Technical Architecture & Development Guide for Contributors and Extenders**

Version 7.3.0 | Last Updated: September 2025

---

## 🎯 Table of Contents

1. [Architecture Overview](#-architecture-overview)
2. [Development Environment](#-development-environment)
3. [Agent Development](#-agent-development)
4. [Database Design](#-database-design)
5. [API Development](#-api-development)
6. [Service Integration](#-service-integration)
7. [Web Interface Development](#-web-interface-development)
8. [Testing Framework](#-testing-framework)
9. [Performance Optimization](#-performance-optimization)
10. [Security Considerations](#-security-considerations)
11. [Deployment & DevOps](#-deployment--devops)
12. [Contributing Guidelines](#-contributing-guidelines)

---

## 🏗️ Architecture Overview

### System Architecture Principles

The Socratic RAG Enhanced system is built on several key architectural principles:

1. **Modular Agent Design**: Each agent is self-contained with clear interfaces
2. **Event-Driven Communication**: Loose coupling through event bus
3. **Layered Architecture**: Clear separation between data, business logic, and presentation
4. **Plugin Architecture**: Extensible design for new agents and services
5. **Microservices Ready**: Components can be distributed across services
6. **Database Agnostic**: Support for multiple database backends

### Core Components

```python
# Core Infrastructure Stack
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface Layer                      │
│  Flask + HTMX + Bootstrap (Presentation & User Interaction) │
├─────────────────────────────────────────────────────────────┤
│                    Agent Orchestration Layer                │
│  AgentOrchestrator + 8 Specialized Agents (Business Logic)  │
├─────────────────────────────────────────────────────────────┤
│                    Service Integration Layer                │
│  Claude API + ChromaDB + Git + IDE Services                │
├─────────────────────────────────────────────────────────────┤
│                    Core Infrastructure Layer                │
│  Config + Logging + Events + Database + Utilities          │
├─────────────────────────────────────────────────────────────┤
│                    Data Persistence Layer                   │
│  SQLite/PostgreSQL + ChromaDB + File System                │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend Technologies**:
- **Python 3.8+**: Primary development language
- **Flask**: Web framework for API and web interface
- **SQLite/PostgreSQL**: Primary data storage
- **ChromaDB**: Vector database for embeddings
- **SQLAlchemy**: Database ORM (future enhancement)
- **Anthropic Claude**: AI language model integration

**Frontend Technologies**:
- **HTML5/CSS3**: Standard web technologies
- **JavaScript ES6+**: Client-side scripting
- **HTMX**: Dynamic web interfaces without complex JavaScript
- **Bootstrap 5**: UI component framework
- **Chart.js**: Data visualization

**Infrastructure**:
- **Docker**: Containerization and deployment
- **Git**: Version control integration
- **VS Code**: IDE integration
- **pytest**: Testing framework
- **GitHub Actions**: CI/CD pipeline

### Design Patterns

**Observer Pattern**: Event system for agent communication
```python
class EventSystem:
    def emit(self, event_type: str, source: str, data: Dict[str, Any]):
        # Notify all subscribers
        for callback in self._subscribers.get(event_type, []):
            callback(Event(event_type, source, data))
```

**Strategy Pattern**: Different questioning strategies
```python
class QuestioningStrategy(ABC):
    @abstractmethod
    def generate_questions(self, context: Dict) -> List[Question]:
        pass

class SequentialStrategy(QuestioningStrategy):
    def generate_questions(self, context: Dict) -> List[Question]:
        # Role-by-role questioning
        pass
```

**Factory Pattern**: Agent creation and management
```python
class AgentFactory:
    @staticmethod
    def create_agent(agent_type: str) -> BaseAgent:
        if agent_type == 'socratic_counselor':
            return SocraticCounselorAgent()
        # ... other agent types
```

**Singleton Pattern**: Core system components
```python
class SystemConfig:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

---

## 🛠️ Development Environment

### Prerequisites

```bash
# Required versions
Python >= 3.8
Node.js >= 14 (for frontend tooling)
Git >= 2.20
Docker >= 20.10 (optional)
VS Code (recommended)
```

### Development Setup

#### 1. Repository Setup
```bash
# Clone the repository
git clone https://github.com/your-org/socratic-rag-enhanced.git
cd socratic-rag-enhanced

# Create development branch
git checkout -b feature/your-feature-name
```

#### 2. Python Environment
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

#### 3. Configuration Setup
```bash
# Copy configuration template
cp config.yaml.example config.yaml

# Set up environment variables
echo "ANTHROPIC_API_KEY=your-api-key" >> .env
echo "FLASK_ENV=development" >> .env
echo "SOCRATIC_DEBUG=true" >> .env
```

#### 4. Database Initialization
```bash
# Initialize development database
python -c "from src.database import init_database; init_database()"

# Load sample data (optional)
python scripts/load_sample_data.py
```

#### 5. Development Server
```bash
# Run in development mode
python run.py --debug

# Or with custom configuration
python run.py --config config-dev.yaml --host 0.0.0.0 --port 8080
```

### Development Tools

#### Code Quality Tools
```bash
# Install development tools
pip install black isort flake8 mypy pytest coverage bandit

# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/
mypy src/

# Security scan
bandit -r src/
```

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### VS Code Setup

#### Recommended Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "ms-vscode.vscode-json",
    "bradlc.vscode-tailwindcss",
    "formulahendry.auto-rename-tag"
  ]
}
```

#### VS Code Settings
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"]
}
```

### Docker Development

#### Development Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: 
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - /app/.venv
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      - SOCRATIC_DEBUG=true
    depends_on:
      - db
      - vector_db
  
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: socratic_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  vector_db:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma

volumes:
  postgres_data:
  chroma_data:
```

---

## 🤖 Agent Development

### Agent Architecture

The agent system is the core of Socratic RAG Enhanced. Each agent is responsible for specific functionality and communicates through a well-defined interface.

#### BaseAgent Class

All agents inherit from the `BaseAgent` class:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from src.core import get_logger, get_config, get_event_bus, get_db_manager

class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.config = get_config()
        self.logger = get_logger(f"agent.{agent_id}")
        self.db_manager = get_db_manager()
        self.events = get_event_bus()
        
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        pass
        
    def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent request with error handling"""
        # Implementation in BaseAgent
        pass
```

#### Creating a New Agent

1. **Create Agent File**: `src/agents/your_agent.py`

```python
from typing import List, Dict, Any
from src.agents.base import BaseAgent, require_authentication, log_agent_action

class YourCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("your_custom", "Your Custom Agent")
        
    def get_capabilities(self) -> List[str]:
        return [
            "custom_capability_1",
            "custom_capability_2",
            "analyze_custom_data"
        ]
    
    @require_authentication
    @log_agent_action
    def _custom_capability_1(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Implement your custom capability"""
        try:
            # Your implementation here
            result = self._process_custom_logic(data)
            
            # Emit event for tracking
            self._emit_event('custom_action_completed', {
                'action': 'custom_capability_1',
                'result_summary': result.get('summary', '')
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Custom capability failed: {e}")
            raise AgentError(f"Custom processing failed: {e}")
    
    def _process_custom_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Your core business logic"""
        # Implement your agent's core functionality
        pass
```

2. **Register Agent**: Add to `src/agents/__init__.py`

```python
from src.agents.your_agent import YourCustomAgent

# Add to get_available_agents function
def get_available_agents() -> Dict[str, Any]:
    agents = {
        # ... existing agents
        'your_custom': YourCustomAgent,
    }
    return agents
```

3. **Update Orchestrator**: Agent will be automatically registered

### Agent Communication

#### Event System
Agents communicate through the event system:

```python
# Emit event
self._emit_event('custom_event', {
    'agent_id': self.agent_id,
    'data': custom_data,
    'timestamp': DateTimeHelper.now()
})

# Subscribe to events (in __init__)
self.events.subscribe('other_agent_event', self._handle_other_agent_event)

def _handle_other_agent_event(self, event: Event):
    """Handle events from other agents"""
    self.logger.info(f"Received event from {event.source}: {event.type}")
    # Process the event
```

#### Direct Agent Communication
```python
# Get other agent through orchestrator
orchestrator = get_orchestrator()
result = orchestrator.route_request(
    'code_generator', 
    'generate_component', 
    {'component_type': 'api_endpoint', 'specification': spec}
)
```

### Agent Capabilities

#### Capability System
Each agent declares its capabilities:

```python
def get_capabilities(self) -> List[str]:
    return [
        "generate_questions",      # Generate Socratic questions
        "analyze_responses",       # Analyze user responses
        "detect_conflicts",        # Identify requirement conflicts
        "suggest_improvements"     # Suggest question improvements
    ]
```

#### Capability Discovery
The orchestrator builds a capability map:

```python
class AgentOrchestrator:
    def _build_capability_map(self):
        """Build map of capabilities to agents"""
        self.capability_map = {}
        
        for agent_id, agent in self.agents.items():
            for capability in agent.get_capabilities():
                if capability not in self.capability_map:
                    self.capability_map[capability] = []
                self.capability_map[capability].append(agent_id)
```

### Agent Testing

#### Unit Testing
```python
import pytest
from unittest.mock import Mock, patch
from src.agents.your_agent import YourCustomAgent

class TestYourCustomAgent:
    @pytest.fixture
    def agent(self):
        return YourCustomAgent()
    
    def test_capabilities(self, agent):
        capabilities = agent.get_capabilities()
        assert "custom_capability_1" in capabilities
        assert len(capabilities) > 0
    
    @patch('src.agents.your_agent.get_db_manager')
    def test_custom_capability_1(self, mock_db, agent):
        # Mock database responses
        mock_db.return_value.execute_query.return_value = [{'id': 1}]
        
        # Test data
        test_data = {
            'username': 'testuser',
            'project_id': 'test-project-123',
            'custom_param': 'test_value'
        }
        
        # Execute
        result = agent._custom_capability_1(test_data)
        
        # Assertions
        assert result['success'] is True
        assert 'data' in result
```

#### Integration Testing
```python
@pytest.mark.integration
class TestAgentIntegration:
    def test_agent_orchestrator_integration(self):
        """Test agent works with orchestrator"""
        orchestrator = get_orchestrator()
        
        result = orchestrator.route_request(
            'your_custom',
            'custom_capability_1',
            {'username': 'testuser', 'project_id': 'test'}
        )
        
        assert result['success'] is True
```

---

## 🗄️ Database Design

### Database Architecture

The system uses a hybrid approach with SQLite for primary data and ChromaDB for vector storage.

#### Primary Database Schema

```sql
-- Users and Authentication
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    roles TEXT, -- JSON array of roles
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    owner TEXT NOT NULL,
    phase TEXT DEFAULT 'discovery', -- discovery, design, development, testing, complete
    status TEXT DEFAULT 'active',   -- active, paused, completed, archived
    technology_stack TEXT,          -- JSON object
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner) REFERENCES users(username)
);

-- Project Collaborators
CREATE TABLE collaborators (
    collaboration_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    username TEXT NOT NULL,
    role TEXT DEFAULT 'collaborator', -- owner, collaborator, reviewer, guest
    permissions TEXT,                 -- JSON array of permissions
    is_active BOOLEAN DEFAULT 1,
    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    joined_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (username) REFERENCES users(username)
);

-- Socratic Sessions
CREATE TABLE socratic_sessions (
    session_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    initiated_by TEXT NOT NULL,
    questioning_mode TEXT DEFAULT 'sequential', -- sequential, dynamic, custom
    active_roles TEXT,                          -- JSON array of active roles
    status TEXT DEFAULT 'active',               -- active, paused, completed
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (initiated_by) REFERENCES users(username)
);

-- Questions and Responses
CREATE TABLE questions (
    question_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role_type TEXT NOT NULL,          -- project_manager, technical_lead, etc.
    question_text TEXT NOT NULL,
    question_category TEXT,           -- requirements, technical, business, etc.
    order_index INTEGER,
    asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES socratic_sessions(session_id)
);

CREATE TABLE responses (
    response_id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL,
    respondent TEXT NOT NULL,
    response_text TEXT NOT NULL,
    confidence_level INTEGER,         -- 1-5 scale
    response_metadata TEXT,           -- JSON for additional data
    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(question_id),
    FOREIGN KEY (respondent) REFERENCES users(username)
);

-- Generated Code
CREATE TABLE generated_codebases (
    codebase_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    version TEXT NOT NULL,
    architecture_type TEXT,           -- mvc, microservices, layered, etc.
    technology_stack TEXT,            -- JSON object
    file_structure TEXT,              -- JSON object
    generation_metadata TEXT,         -- JSON for generation details
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'generating', -- generating, testing, completed, failed
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE generated_files (
    file_id TEXT PRIMARY KEY,
    codebase_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,          -- python, javascript, html, css, etc.
    file_purpose TEXT,                -- model, controller, view, test, config
    content TEXT NOT NULL,
    dependencies TEXT,                -- JSON array of file dependencies
    documentation TEXT,
    generated_by_agent TEXT,
    version TEXT,
    size_bytes INTEGER,
    complexity_score REAL,
    test_coverage REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (codebase_id) REFERENCES generated_codebases(codebase_id)
);

-- Testing Results
CREATE TABLE test_results (
    test_id TEXT PRIMARY KEY,
    codebase_id TEXT NOT NULL,
    test_type TEXT NOT NULL,          -- unit, integration, security, performance
    test_suite TEXT,
    files_tested TEXT,                -- JSON array of tested files
    passed BOOLEAN,
    total_tests INTEGER,
    passed_tests INTEGER,
    failed_tests INTEGER,
    skipped_tests INTEGER,
    coverage_percentage REAL,
    failure_details TEXT,             -- JSON array of failure info
    execution_time REAL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (codebase_id) REFERENCES generated_codebases(codebase_id)
);

-- System Monitoring
CREATE TABLE agent_activities (
    activity_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    project_id TEXT,
    user_id TEXT,
    input_data TEXT,                  -- JSON object
    output_data TEXT,                 -- JSON object
    execution_time REAL,
    success BOOLEAN,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Database Repository Pattern

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.core import get_db_manager, DatabaseError

class BaseRepository(ABC):
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SELECT query"""
        try:
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            raise DatabaseError(f"Query failed: {e}")
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            return self.db_manager.execute_update(query, params)
        except Exception as e:
            raise DatabaseError(f"Update failed: {e}")

class ProjectRepository(BaseRepository):
    def create_project(self, project: Dict[str, Any]) -> str:
        """Create new project"""
        query = """
            INSERT INTO projects (project_id, name, description, owner, technology_stack)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            project['project_id'],
            project['name'],
            project['description'],
            project['owner'],
            json.dumps(project.get('technology_stack', {}))
        )
        
        self.execute_update(query, params)
        return project['project_id']
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        query = "SELECT * FROM projects WHERE project_id = ?"
        results = self.execute_query(query, (project_id,))
        
        if results:
            project = dict(results[0])
            project['technology_stack'] = json.loads(project['technology_stack'] or '{}')
            return project
        return None
    
    def update_project_phase(self, project_id: str, phase: str) -> bool:
        """Update project phase"""
        query = """
            UPDATE projects 
            SET phase = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE project_id = ?
        """
        rows_affected = self.execute_update(query, (phase, project_id))
        return rows_affected > 0
```

### Vector Database Integration

#### ChromaDB Setup
```python
import chromadb
from chromadb.config import Settings

class VectorRepository:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="data/vector_db"
        ))
        self.collection = self.client.get_or_create_collection("socratic_knowledge")
    
    def add_documents(self, documents: List[str], metadata: List[Dict], ids: List[str]):
        """Add documents with embeddings"""
        self.collection.add(
            documents=documents,
            metadatas=metadata,
            ids=ids
        )
    
    def search_similar(self, query: str, n_results: int = 5) -> Dict:
        """Search for similar documents"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
    
    def get_by_metadata(self, where: Dict[str, Any]) -> Dict:
        """Get documents by metadata filter"""
        results = self.collection.get(where=where)
        return results
```

### Database Migrations

#### Migration System
```python
class DatabaseMigration:
    def __init__(self, version: int, description: str):
        self.version = version
        self.description = description
    
    def up(self, db_manager):
        """Apply migration"""
        raise NotImplementedError
    
    def down(self, db_manager):
        """Rollback migration"""
        raise NotImplementedError

class Migration001_InitialSchema(DatabaseMigration):
    def __init__(self):
        super().__init__(1, "Initial database schema")
    
    def up(self, db_manager):
        """Create initial tables"""
        with db_manager.transaction() as conn:
            # Execute CREATE TABLE statements
            conn.execute(CREATE_USERS_TABLE)
            conn.execute(CREATE_PROJECTS_TABLE)
            # ... other tables
    
    def down(self, db_manager):
        """Drop all tables"""
        with db_manager.transaction() as conn:
            conn.execute("DROP TABLE IF EXISTS users")
            conn.execute("DROP TABLE IF EXISTS projects")
            # ... other tables

# Migration runner
def run_migrations():
    migrations = [
        Migration001_InitialSchema(),
        # Add new migrations here
    ]
    
    current_version = get_current_schema_version()
    
    for migration in migrations:
        if migration.version > current_version:
            migration.up(get_db_manager())
            update_schema_version(migration.version)
```

---

## 🌐 API Development

### REST API Design

The system exposes a RESTful API for external integrations and the web interface.

#### API Structure
```
/api/v1/
├── /auth/              # Authentication endpoints
├── /projects/          # Project management
├── /sessions/          # Socratic questioning sessions
├── /agents/            # Agent management and status
├── /codebases/         # Generated code management
├── /users/             # User management
└── /system/            # System information and health
```

#### API Implementation

```python
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.core import get_logger
from src.agents import get_orchestrator

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
logger = get_logger('api')

@api_bp.route('/projects', methods=['POST'])
@login_required
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('name'):
            return jsonify({'error': 'Project name is required'}), 400
        
        # Create project through agent
        orchestrator = get_orchestrator()
        result = orchestrator.route_request('project_manager', 'create_project', {
            'name': data['name'],
            'description': data.get('description', ''),
            'owner': current_user.username,
            'technology_preferences': data.get('technology_preferences', {}),
            'username': current_user.username
        })
        
        if result['success']:
            return jsonify({
                'success': True,
                'project': result['data']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Create project failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/projects/<project_id>', methods=['GET'])
@login_required
def get_project(project_id: str):
    """Get project details"""
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.route_request('project_manager', 'get_project', {
            'project_id': project_id,
            'username': current_user.username
        })
        
        if result['success']:
            return jsonify({
                'success': True,
                'project': result['data']
            })
        else:
            return jsonify({'error': result['error']}), 404
            
    except Exception as e:
        logger.error(f"Get project failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/sessions', methods=['POST'])
@login_required
def start_socratic_session():
    """Start a new Socratic questioning session"""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        
        if not project_id:
            return jsonify({'error': 'Project ID is required'}), 400
        
        orchestrator = get_orchestrator()
        result = orchestrator.route_request('socratic_counselor', 'start_session', {
            'project_id': project_id,
            'username': current_user.username,
            'questioning_mode': data.get('mode', 'sequential'),
            'active_roles': data.get('active_roles', [])
        })
        
        if result['success']:
            return jsonify({
                'success': True,
                'session': result['data']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Start session failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/sessions/<session_id>/questions', methods=['GET'])
@login_required
def get_session_questions(session_id: str):
    """Get questions for a session"""
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.route_request('socratic_counselor', 'get_questions', {
            'session_id': session_id,
            'username': current_user.username
        })
        
        if result['success']:
            return jsonify({
                'success': True,
                'questions': result['data']
            })
        else:
            return jsonify({'error': result['error']}), 404
            
    except Exception as e:
        logger.error(f"Get questions failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/sessions/<session_id>/responses', methods=['POST'])
@login_required
def submit_response():
    """Submit response to a question"""
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        response_text = data.get('response')
        
        if not question_id or not response_text:
            return jsonify({'error': 'Question ID and response are required'}), 400
        
        orchestrator = get_orchestrator()
        result = orchestrator.route_request('socratic_counselor', 'submit_response', {
            'session_id': session_id,
            'question_id': question_id,
            'response_text': response_text,
            'confidence_level': data.get('confidence_level', 3),
            'username': current_user.username
        })
        
        if result['success']:
            return jsonify({
                'success': True,
                'next_question': result['data'].get('next_question'),
                'conflicts': result['data'].get('conflicts', [])
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Submit response failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

#### API Authentication

```python
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

class User(UserMixin):
    def __init__(self, user_id, username, email, password_hash, roles=None, is_active=True):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.roles = roles or []
        self.is_active = is_active
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def create_user(username, email, password, roles=None):
        password_hash = generate_password_hash(password)
        # Save to database
        return User(user_id, username, email, password_hash, roles)

@login_manager.user_loader
def load_user(user_id):
    # Load user from database
    return User.get_by_id(user_id)
```

#### API Documentation

```python
from flask import jsonify

@api_bp.route('/docs', methods=['GET'])
def api_documentation():
    """OpenAPI/Swagger documentation"""
    return jsonify({
        "openapi": "3.0.0",
        "info": {
            "title": "Socratic RAG Enhanced API",
            "version": "7.3.0",
            "description": "AI-Powered Project Development API"
        },
        "paths": {
            "/api/v1/projects": {
                "post": {
                    "summary": "Create new project",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "technology_preferences": {"type": "object"}
                                    },
                                    "required": ["name"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Project created successfully"
                        },
                        "400": {
                            "description": "Invalid input"
                        }
                    }
                }
            }
            # ... more endpoints
        }
    })
```

---

## 🔌 Service Integration

### External Service Architecture

The system integrates with several external services through a unified service layer.

#### Service Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseService(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(f"service.{self.__class__.__name__}")
        self.is_available = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the service"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if service is healthy"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'name': self.__class__.__name__,
            'available': self.is_available,
            'config': {k: v for k, v in self.config.items() if 'key' not in k.lower()}
        }
```

#### Claude API Service

```python
import anthropic
from src.services.base import BaseService

class ClaudeService(BaseService):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        
    def initialize(self) -> bool:
        """Initialize Claude client"""
        try:
            api_key = self.config.get('api_key')
            if not api_key:
                self.logger.warning("Claude API key not configured")
                return False
            
            self.client = anthropic.Anthropic(api_key=api_key)
            self.is_available = True
            
            # Test connection
            if self.health_check():
                self.logger.info("Claude service initialized successfully")
                return True
            else:
                self.is_available = False
                return False
                
        except Exception as e:
            self.logger.error(f"Claude service initialization failed: {e}")
            self.is_available = False
            return False
    
    def health_check(self) -> bool:
        """Check Claude API health"""
        try:
            if not self.client:
                return False
                
            # Simple test request
            response = self.client.messages.create(
                model=self.config.get('model', 'claude-3-sonnet-20240229'),
                max_tokens=10,
                messages=[{"role": "user", "content": "Test"}]
            )
            return bool(response.content)
            
        except Exception as e:
            self.logger.error(f"Claude health check failed: {e}")
            return False
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Claude"""
        try:
            if not self.is_available:
                raise ServiceError("Claude service not available")
            
            model = kwargs.get('model', self.config.get('model'))
            max_tokens = kwargs.get('max_tokens', self.config.get('max_tokens', 4000))
            temperature = kwargs.get('temperature', self.config.get('temperature', 0.7))
            
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            self.logger.error(f"Claude text generation failed: {e}")
            raise ServiceError(f"Text generation failed: {e}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        # Implement usage tracking
        return {
            'requests_made': getattr(self, '_requests_made', 0),
            'tokens_used': getattr(self, '_tokens_used', 0),
            'last_request': getattr(self, '_last_request', None)
        }
```

#### Vector Service (ChromaDB)

```python
import chromadb
from chromadb.config import Settings
from src.services.base import BaseService

class VectorService(BaseService):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self.collection = None
        
    def initialize(self) -> bool:
        """Initialize ChromaDB client"""
        try:
            db_path = self.config.get('path', 'data/vector_db')
            collection_name = self.config.get('collection_name', 'socratic_knowledge')
            
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=db_path
            ))
            
            self.collection = self.client.get_or_create_collection(collection_name)
            self.is_available = True
            
            self.logger.info("Vector service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Vector service initialization failed: {e}")
            self.is_available = False
            return False
    
    def health_check(self) -> bool:
        """Check vector database health"""
        try:
            if not self.client or not self.collection:
                return False
            
            # Test collection access
            count = self.collection.count()
            return True
            
        except Exception as e:
            self.logger.error(f"Vector health check failed: {e}")
            return False
    
    def add_documents(self, documents: List[str], metadata: List[Dict], ids: List[str]):
        """Add documents to vector database"""
        try:
            if not self.is_available:
                raise ServiceError("Vector service not available")
            
            self.collection.add(
                documents=documents,
                metadatas=metadata,
                ids=ids
            )
            
        except Exception as e:
            self.logger.error(f"Adding documents failed: {e}")
            raise ServiceError(f"Document storage failed: {e}")
    
    def search_similar(self, query: str, n_results: int = 5, **kwargs) -> Dict:
        """Search for similar documents"""
        try:
            if not self.is_available:
                raise ServiceError("Vector service not available")
            
            where_filter = kwargs.get('where')
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            return {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadata': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'ids': results['ids'][0] if results['ids'] else []
            }
            
        except Exception as e:
            self.logger.error(f"Vector search failed: {e}")
            raise ServiceError(f"Search failed: {e}")
```

#### Git Service

```python
import git
import os
from pathlib import Path
from src.services.base import BaseService

class GitService(BaseService):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
    def initialize(self) -> bool:
        """Initialize Git service"""
        try:
            # Check if git is available
            git.Git().version()
            self.is_available = True
            self.logger.info("Git service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Git service initialization failed: {e}")
            self.is_available = False
            return False
    
    def health_check(self) -> bool:
        """Check Git availability"""
        try:
            git.Git().version()
            return True
        except Exception:
            return False
    
    def initialize_repository(self, project_path: str) -> bool:
        """Initialize Git repository for project"""
        try:
            if not self.is_available:
                raise ServiceError("Git service not available")
            
            repo_path = Path(project_path)
            repo_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize repo
            repo = git.Repo.init(repo_path)
            
            # Create .gitignore
            gitignore_content = """
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Environment variables
.env
.env.local
.env.*.local
"""
            
            gitignore_path = repo_path / '.gitignore'
            gitignore_path.write_text(gitignore_content.strip())
            
            # Initial commit
            repo.index.add(['.gitignore'])
            
            author_name = self.config.get('commit_author_name', 'Socratic RAG System')
            author_email = self.config.get('commit_author_email', 'noreply@socratic-rag.com')
            
            repo.index.commit(
                'Initial commit',
                author=git.Actor(author_name, author_email),
                committer=git.Actor(author_name, author_email)
            )
            
            self.logger.info(f"Git repository initialized at {project_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Git repository initialization failed: {e}")
            raise ServiceError(f"Repository initialization failed: {e}")
    
    def commit_changes(self, project_path: str, message: str, files: List[str] = None) -> bool:
        """Commit changes to repository"""
        try:
            if not self.is_available:
                raise ServiceError("Git service not available")
            
            repo = git.Repo(project_path)
            
            # Add files
            if files:
                repo.index.add(files)
            else:
                repo.index.add('.')
            
            # Check if there are changes to commit
            if not repo.index.diff("HEAD"):
                self.logger.info("No changes to commit")
                return True
            
            # Commit
            author_name = self.config.get('commit_author_name', 'Socratic RAG System')
            author_email = self.config.get('commit_author_email', 'noreply@socratic-rag.com')
            
            repo.index.commit(
                message,
                author=git.Actor(author_name, author_email),
                committer=git.Actor(author_name, author_email)
            )
            
            self.logger.info(f"Changes committed: {message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Git commit failed: {e}")
            raise ServiceError(f"Commit failed: {e}")
```

#### Service Manager

```python
class ServiceManager:
    def __init__(self):
        self.services = {}
        self.logger = get_logger('service_manager')
    
    def register_service(self, name: str, service: BaseService):
        """Register a service"""
        self.services[name] = service
        self.logger.info(f"Service registered: {name}")
    
    def initialize_all(self) -> Dict[str, bool]:
        """Initialize all registered services"""
        results = {}
        
        for name, service in self.services.items():
            try:
                results[name] = service.initialize()
                self.logger.info(f"Service {name}: {'✓' if results[name] else '✗'}")
            except Exception as e:
                self.logger.error(f"Service {name} initialization failed: {e}")
                results[name] = False
        
        return results
    
    def get_service(self, name: str) -> Optional[BaseService]:
        """Get service by name"""
        return self.services.get(name)
    
    def health_check_all(self) -> Dict[str, bool]:
        """Health check all services"""
        results = {}
        
        for name, service in self.services.items():
            try:
                results[name] = service.health_check()
            except Exception as e:
                self.logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        
        return results
    
    def get_status_all(self) -> Dict[str, Any]:
        """Get status of all services"""
        return {
            name: service.get_status()
            for name, service in self.services.items()
        }
```

---

## 🌐 Web Interface Development

### Frontend Architecture

The web interface uses a modern but simple approach with HTMX for dynamic interactions.

#### HTML Template Structure

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Socratic RAG Enhanced{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="{{ url_for('static', filename='css/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/main.css') }}" rel="stylesheet">
    
    <!-- HTMX -->
    <script src="{{ url_for('static', filename='js/htmx.min.js') }}"></script>
    
    {% block head %}{% endblock %}
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('main.dashboard') }}">
                <img src="{{ url_for('static', filename='img/logo.png') }}" alt="Logo" height="30">
                Socratic RAG Enhanced
            </a>
            
            <div class="navbar-nav ms-auto">
                {% if current_user.is_authenticated %}
                    <a class="nav-link" href="{{ url_for('main.dashboard') }}">Dashboard</a>
                    <a class="nav-link" href="{{ url_for('main.projects') }}">Projects</a>
                    <a class="nav-link" href="{{ url_for('main.profile') }}">Profile</a>
                    <a class="nav-link" href="{{ url_for('auth.logout') }}">Logout</a>
                {% else %}
                    <a class="nav-link" href="{{ url_for('auth.login') }}">Login</a>
                    <a class="nav-link" href="{{ url_for('auth.register') }}">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>
    
    <!-- Main Content -->
    <div class="container-fluid">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="row mt-3">
                    <div class="col-12">
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
    
    <!-- Footer -->
    <footer class="bg-dark text-light mt-5 py-4">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <p>&copy; 2025 Socratic RAG Enhanced. All rights reserved.</p>
                </div>
                <div class="col-md-6 text-end">
                    <p>Version 7.3.0</p>
                </div>
            </div>
        </div>
    </footer>
    
    <!-- Bootstrap JS -->
    <script src="{{ url_for('static', filename='js/bootstrap.bundle.min.js') }}"></script>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

#### HTMX Integration

```html
<!-- Dynamic project creation -->
<div id="project-form">
    <form hx-post="/projects/create" 
          hx-target="#project-list" 
          hx-swap="afterbegin"
          hx-indicator="#loading">
        
        <div class="mb-3">
            <label for="project-name" class="form-label">Project Name</label>
            <input type="text" class="form-control" id="project-name" name="name" required>
        </div>
        
        <div class="mb-3">
            <label for="project-description" class="form-label">Description</label>
            <textarea class="form-control" id="project-description" name="description" rows="3"></textarea>
        </div>
        
        <button type="submit" class="btn btn-primary">
            Create Project
            <span id="loading" class="htmx-indicator spinner-border spinner-border-sm ms-2"></span>
        </button>
    </form>
</div>

<!-- Real-time session updates -->
<div id="session-status" 
     hx-get="/sessions/{{ session.id }}/status" 
     hx-trigger="every 2s"
     hx-swap="innerHTML">
    <!-- Session status will be updated here -->
</div>

<!-- Live questioning interface -->
<div id="question-container" 
     hx-get="/sessions/{{ session.id }}/next-question"
     hx-trigger="response-submitted from:body"
     hx-swap="innerHTML">
    <!-- Questions will be loaded here -->
</div>
```

#### JavaScript Enhancements

```javascript
// static/js/main.js

class SocraticInterface {
    constructor() {
        this.initializeEventHandlers();
        this.setupWebSockets();
    }
    
    initializeEventHandlers() {
        // HTMX event handlers
        document.body.addEventListener('htmx:afterRequest', (event) => {
            if (event.detail.xhr.status >= 400) {
                this.showError('Request failed. Please try again.');
            }
        });
        
        document.body.addEventListener('htmx:beforeRequest', (event) => {
            this.showLoading(true);
        });
        
        document.body.addEventListener('htmx:afterRequest', (event) => {
            this.showLoading(false);
        });
        
        // Custom form validation
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (event) => {
                if (!this.validateForm(form)) {
                    event.preventDefault();
                }
            });
        });
    }
    
    setupWebSockets() {
        // WebSocket for real-time updates
        if (window.WebSocket) {
            this.ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onclose = (event) => {
                // Reconnect after delay
                setTimeout(() => this.setupWebSockets(), 5000);
            };
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'session_update':
                this.updateSessionStatus(data.payload);
                break;
            case 'new_question':
                this.displayNewQuestion(data.payload);
                break;
            case 'conflict_detected':
                this.showConflictAlert(data.payload);
                break;
            case 'generation_progress':
                this.updateGenerationProgress(data.payload);
                break;
        }
    }
    
    validateForm(form) {
        let isValid = true;
        
        // Clear previous errors
        form.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        
        // Validate required fields
        form.querySelectorAll('[required]').forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            }
        });
        
        // Custom validation rules
        const emailFields = form.querySelectorAll('input[type="email"]');
        emailFields.forEach(field => {
            if (field.value && !this.isValidEmail(field.value)) {
                field.classList.add('is-invalid');
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
    
    showLoading(show) {
        const loadingElements = document.querySelectorAll('.htmx-indicator');
        loadingElements.forEach(el => {
            if (show) {
                el.classList.remove('d-none');
            } else {
                el.classList.add('d-none');
            }
        });
    }
    
    updateSessionStatus(status) {
        const statusElement = document.getElementById('session-status');
        if (statusElement) {
            statusElement.innerHTML = this.renderSessionStatus(status);
        }
    }
    
    renderSessionStatus(status) {
        const progressPercentage = (status.answered_questions / status.total_questions) * 100;
        
        return `
            <div class="card">
                <div class="card-body">
                    <h6 class="card-title">Session Progress</h6>
                    <div class="progress mb-3">
                        <div class="progress-bar" style="width: ${progressPercentage}%"></div>
                    </div>
                    <p class="card-text">
                        ${status.answered_questions} of ${status.total_questions} questions answered
                    </p>
                    <p class="card-text">
                        <small class="text-muted">Current role: ${status.current_role}</small>
                    </p>
                </div>
            </div>
        `;
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.socraticInterface = new SocraticInterface();
});
```

#### CSS Styling

```css
/* static/css/main.css */

:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --accent-color: #e74c3c;
    --success-color: #27ae60;
    --warning-color: #f39c12;
    --light-bg: #f8f9fa;
    --dark-bg: #343a40;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: var(--light-bg);
}

/* Custom card styles */
.card {
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: box-shadow 0.3s ease;
}

.card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

/* Agent status indicators */
.agent-status {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 8px;
}

.agent-status.active {
    background-color: var(--success-color);
    animation: pulse 2s infinite;
}

.agent-status.inactive {
    background-color: var(--accent-color);
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

/* Question interface */
.question-card {
    border-left: 4px solid var(--secondary-color);
    margin-bottom: 20px;
}

.role-badge {
    font-size: 0.8em;
    padding: 4px 8px;
    border-radius: 12px;
    text-transform: uppercase;
    font-weight: 600;
}

.role-badge.project-manager { background-color: #e8f4fd; color: #0969da; }
.role-badge.technical-lead { background-color: #f0f9ff; color: #0ea5e9; }
.role-badge.developer { background-color: #ecfdf5; color: #059669; }
.role-badge.designer { background-color: #fef3c7; color: #d97706; }
.role-badge.qa-tester { background-color: #fce7f3; color: #be185d; }
.role-badge.business-analyst { background-color: #f3e8ff; color: #7c3aed; }
.role-badge.devops { background-color: #fee2e2; color: #dc2626; }

/* Progress indicators */
.progress-circle {
    width: 60px;
    height: 60px;
    background: conic-gradient(var(--success-color) var(--progress-angle, 0deg), #e9ecef 0deg);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.progress-circle::before {
    content: '';
    width: 40px;
    height: 40px;
    background-color: white;
    border-radius: 50%;
    position: absolute;
}

.progress-circle span {
    position: relative;
    z-index: 1;
    font-weight: 600;
    font-size: 0.9em;
}

/* Code generation progress */
.generation-progress {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
}

.generation-step {
    display: flex;
    align-items: center;
    margin: 10px 0;
    padding: 10px;
    border-radius: 5px;
    background: rgba(255,255,255,0.1);
}

.generation-step.active {
    background: rgba(255,255,255,0.2);
}

.generation-step.completed {
    background: rgba(39,174,96,0.3);
}

/* Responsive design */
@media (max-width: 768px) {
    .container-fluid {
        padding-left: 15px;
        padding-right: 15px;
    }
    
    .card {
        margin-bottom: 15px;
    }
    
    .progress-circle {
        width: 50px;
        height: 50px;
    }
    
    .progress-circle::before {
        width: 35px;
        height: 35px;
    }
}

/* Loading animations */
.htmx-indicator {
    display: none;
}

.htmx-request .htmx-indicator {
    display: inline-block;
}

.spinner-grow-sm {
    width: 1rem;
    height: 1rem;
}

/* Accessibility improvements */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0,0,0,0);
    white-space: nowrap;
    border: 0;
}

/* Focus indicators */
*:focus {
    outline: 2px solid var(--secondary-color);
    outline-offset: 2px;
}

button:focus,
.btn:focus {
    box-shadow: 0 0 0 0.2rem rgba(52, 144, 220, 0.25);
}
```

---

## 🧪 Testing Framework

### Testing Strategy

The system uses a comprehensive testing approach with multiple levels of testing.

#### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_core.py        # Core system tests
│   ├── test_agents/        # Agent unit tests
│   ├── test_services/      # Service unit tests
│   └── test_utils.py       # Utility function tests
├── integration/             # Integration tests
│   ├── test_agent_integration.py
│   ├── test_api_integration.py
│   └── test_service_integration.py
├── e2e/                    # End-to-end tests
│   ├── test_project_workflow.py
│   ├── test_questioning_session.py
│   └── test_code_generation.py
├── performance/            # Performance tests
│   ├── test_agent_performance.py
│   └── test_api_performance.py
└── conftest.py            # Pytest configuration
```

#### Test Configuration

```python
# conftest.py
import pytest
import tempfile
import shutil
from pathlib import Path
from src.core import SystemConfig, initialize_system
from src.database import init_database

@pytest.fixture(scope="session")
def test_config():
    """Create test configuration"""
    config = SystemConfig()
    config._config = {
        'database': {
            'sqlite': {'path': ':memory:'},
            'vector': {'path': tempfile.mkdtemp()}
        },
        'logging': {
            'level': 'DEBUG',
            'file': {'enabled': False}
        },
        'agents': {
            'global': {'timeout_seconds': 30}
        },
        'services': {
            'claude': {'api_key': 'test-key'},
            'git': {'auto_commit': False}
        }
    }
    return config

@pytest.fixture(scope="session")
def test_system(test_config):
    """Initialize test system"""
    initialize_system("test-config.yaml")
    init_database()
    yield
    # Cleanup

@pytest.fixture
def sample_project():
    """Create sample project data"""
    return {
        'project_id': 'test-project-123',
        'name': 'Test Project',
        'description': 'A test project for unit testing',
        'owner': 'testuser',
        'technology_stack': {
            'backend': 'python',
            'frontend': 'react',
            'database': 'postgresql'
        }
    }

@pytest.fixture
def mock_claude_response():
    """Mock Claude API response"""
    return """
    Based on your requirements, I'll generate a comprehensive project structure.
    
    Here's the recommended architecture:
    - Backend: Flask REST API
    - Frontend: React with TypeScript
    - Database: PostgreSQL with SQLAlchemy ORM
    """

@pytest.fixture
def authenticated_user():
    """Create authenticated test user"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'roles': ['developer', 'project_manager']
    }
```

#### Unit Tests

```python
# tests/unit/test_agents/test_socratic_agent.py
import pytest
from unittest.mock import Mock, patch
from src.agents.socratic import SocraticCounselorAgent

class TestSocraticCounselorAgent:
    @pytest.fixture
    def agent(self):
        return SocraticCounselorAgent()
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.agent_id == "socratic_counselor"
        assert agent.name == "Socratic Counselor"
        assert "generate_questions" in agent.get_capabilities()
    
    def test_get_capabilities(self, agent):
        """Test agent capabilities"""
        capabilities = agent.get_capabilities()
        
        expected_capabilities = [
            "generate_questions",
            "analyze_responses", 
            "detect_conflicts",
            "suggest_improvements",
            "manage_session"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    @patch('src.agents.socratic.get_db_manager')
    def test_start_session(self, mock_db, agent, sample_project, authenticated_user):
        """Test starting a questioning session"""
        # Mock database responses
        mock_db.return_value.execute_query.return_value = [sample_project]
        mock_db.return_value.execute_update.return_value = 1
        
        data = {
            'project_id': sample_project['project_id'],
            'username': authenticated_user['username'],
            'questioning_mode': 'sequential',
            'active_roles': ['project_manager', 'developer']
        }
        
        result = agent._start_session(data)
        
        assert result['success'] is True
        assert 'session_id' in result['data']
        assert result['data']['questioning_mode'] == 'sequential'
    
    @patch('src.agents.socratic.get_db_manager')
    def test_generate_questions(self, mock_db, agent, mock_claude_response):
        """Test question generation"""
        # Mock database and Claude responses
        mock_db.return_value.execute_query.return_value = [{
            'session_id': 'test-session',
            'project_id': 'test-project',
            'active_roles': '["project_manager"]'
        }]
        
        with patch.object(agent, 'call_claude', return_value=mock_claude_response):
            data = {
                'session_id': 'test-session',
                'username': 'testuser'
            }
            
            result = agent._generate_questions(data)
            
            assert result['success'] is True
            assert 'questions' in result['data']
            assert len(result['data']['questions']) > 0
    
    def test_detect_conflicts(self, agent):
        """Test conflict detection"""
        responses = [
            {
                'question_id': 'q1',
                'role_type': 'project_manager',
                'response_text': 'We need this completed in 2 weeks'
            },
            {
                'question_id': 'q2', 
                'role_type': 'technical_lead',
                'response_text': 'This will take at least 6 weeks to implement properly'
            }
        ]
        
        conflicts = agent._detect_conflicts(responses)
        
        assert len(conflicts) > 0
        assert 'timeline' in conflicts[0]['type'].lower()
    
    def test_invalid_session_id(self, agent):
        """Test handling of invalid session ID"""
        data = {
            'session_id': 'invalid-session',
            'username': 'testuser'
        }
        
        result = agent._get_questions(data)
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()
```

#### Integration Tests

```python
# tests/integration/test_agent_integration.py
import pytest
from src.agents import get_orchestrator

@pytest.mark.integration
class TestAgentIntegration:
    def test_orchestrator_agent_communication(self, test_system, sample_project, authenticated_user):
        """Test agents communicate through orchestrator"""
        orchestrator = get_orchestrator()
        
        # Create project through project manager
        create_result = orchestrator.route_request('project_manager', 'create_project', {
            'name': sample_project['name'],
            'description': sample_project['description'],
            'owner': authenticated_user['username'],
            'username': authenticated_user['username']
        })
        
        assert create_result['success'] is True
        project_id = create_result['data']['project_id']
        
        # Start Socratic session
        session_result = orchestrator.route_request('socratic_counselor', 'start_session', {
            'project_id': project_id,
            'username': authenticated_user['username'],
            'questioning_mode': 'sequential'
        })
        
        assert session_result['success'] is True
        session_id = session_result['data']['session_id']
        
        # Generate questions
        questions_result = orchestrator.route_request('socratic_counselor', 'generate_questions', {
            'session_id': session_id,
            'username': authenticated_user['username']
        })
        
        assert questions_result['success'] is True
        assert len(questions_result['data']['questions']) > 0
    
    def test_code_generation_workflow(self, test_system, sample_project):
        """Test complete code generation workflow"""
        orchestrator = get_orchestrator()
        
        # Simulate completed specification
        specification = {
            'project_id': sample_project['project_id'],
            'architecture': 'mvc',
            'technology_stack': sample_project['technology_stack'],
            'features': ['user_auth', 'crud_operations', 'api_endpoints'],
            'requirements': {
                'functional': ['User registration', 'Data management'],
                'non_functional': ['Performance', 'Security']
            }
        }
        
        # Generate code
        result = orchestrator.route_request('code_generator', 'generate_project_files', {
            'specification': specification,
            'username': 'testuser'
        })
        
        assert result['success'] is True
        assert 'codebase_id' in result['data']
        assert len(result['data']['generated_files']) > 0
```

#### End-to-End Tests

```python
# tests/e2e/test_project_workflow.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.mark.e2e
class TestProjectWorkflow:
    @pytest.fixture
    def browser(self):
        """Setup browser for E2E tests"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_complete_project_creation_workflow(self, browser):
        """Test complete project workflow from UI"""
        # Login
        browser.get('http://localhost:5000/login')
        
        browser.find_element(By.ID, 'username').send_keys('testuser')
        browser.find_element(By.ID, 'password').send_keys('testpass')
        browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Wait for dashboard
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, 'dashboard'))
        )
        
        # Create new project
        browser.find_element(By.ID, 'new-project-btn').click()
        
        browser.find_element(By.ID, 'project-name').send_keys('E2E Test Project')
        browser.find_element(By.ID, 'project-description').send_keys('End-to-end test project')
        browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Wait for project creation
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'project-card'))
        )
        
        # Start questioning session
        browser.find_element(By.CLASS_NAME, 'start-session-btn').click()
        
        # Answer first question
        question_element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'question-text'))
        )
        
        response_textarea = browser.find_element(By.ID, 'response-text')
        response_textarea.send_keys('This is a web application for managing tasks.')
        
        browser.find_element(By.ID, 'submit-response-btn').click()
        
        # Wait for next question or completion
        WebDriverWait(browser, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CLASS_NAME, 'question-text')),
                EC.presence_of_element_located((By.CLASS_NAME, 'session-complete'))
            )
        )
        
        # Verify session progress
        progress_bar = browser.find_element(By.CLASS_NAME, 'progress-bar')
        progress_value = progress_bar.get_attribute('style')
        assert 'width:' in progress_value
```

#### Performance Tests

```python
# tests/performance/test_agent_performance.py
import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from src.agents import get_orchestrator

@pytest.mark.performance
class TestAgentPerformance:
    def test_agent_response_time(self, test_system):
        """Test agent response times"""
        orchestrator = get_orchestrator()
        
        start_time = time.time()
        
        result = orchestrator.route_request('project_manager', 'get_capabilities', {})
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert result['success'] is True
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_concurrent_agent_requests(self, test_system):
        """Test concurrent agent processing"""
        orchestrator = get_orchestrator()
        
        def make_request(i):
            return orchestrator.route_request('system_monitor', 'get_system_status', {
                'username': f'testuser{i}'
            })
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [f.result() for f in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should succeed
        assert all(r['success'] for r in results)
        
        # Should handle 50 concurrent requests in reasonable time
        assert total_time < 10.0
        
        # Average response time should be reasonable
        avg_response_time = total_time / len(results)
        assert avg_response_time < 1.0
    
    def test_memory_usage(self, test_system):
        """Test memory usage under load"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        orchestrator = get_orchestrator()
        
        # Create many projects to test memory usage
        for i in range(100):
            result = orchestrator.route_request('project_manager', 'create_project', {
                'name': f'Test Project {i}',
                'description': f'Performance test project {i}',
                'owner': f'testuser{i % 10}',
                'username': f'testuser{i % 10}'
            })
            assert result['success'] is True
        
        # Force garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024
```

### Test Automation

#### GitHub Actions CI/CD

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
    
    - name: Type check with mypy
      run: |
        mypy src/
    
    - name: Security scan with bandit
      run: |
        bandit -r src/
    
    - name: Test with pytest
      env:
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: |
        pytest tests/ --cov=src --cov-report=xml --cov-report=html -v
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false

  integration-tests:
    runs-on: ubuntu-latest
    needs: test
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: socratic_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run integration tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/socratic_test
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: |
        pytest tests/integration/ -v
    
    - name: Run E2E tests
      run: |
        # Start application in background
        python run.py --config config-test.yaml &
        sleep 10
        
        # Run E2E tests
        pytest tests/e2e/ -v
        
        # Stop application
        pkill -f "python run.py"

  performance-tests:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run performance tests
      env:
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: |
        pytest tests/performance/ -v --benchmark-only
```

---

## 🚀 Performance Optimization

### Performance Monitoring

#### Application Performance Monitoring

```python
# src/core/performance.py
import time
import functools
import threading
from typing import Dict, Any, List
from collections import defaultdict, deque
from src.core import get_logger

class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)
        self.active_requests = {}
        self.lock = threading.Lock()
        self.logger = get_logger('performance')
        
    def start_operation(self, operation_id: str, operation_type: str, metadata: Dict = None):
        """Start monitoring an operation"""
        with self.lock:
            self.active_requests[operation_id] = {
                'type': operation_type,
                'start_time': time.time(),
                'metadata': metadata or {}
            }
    
    def end_operation(self, operation_id: str, success: bool = True, error: str = None):
        """End monitoring an operation"""
        with self.lock:
            if operation_id not in self.active_requests:
                return
            
            operation = self.active_requests.pop(operation_id)
            duration = time.time() - operation['start_time']
            
            metric = {
                'operation_type': operation['type'],
                'duration': duration,
                'success': success,
                'error': error,
                'timestamp': time.time(),
                'metadata': operation['metadata']
            }
            
            self.metrics[operation['type']].append(metric)
            
            # Keep only last 1000 metrics per operation type
            if len(self.metrics[operation['type']]) > 1000:
                self.metrics[operation['type']] = self.metrics[operation['type']][-1000:]
    
    def get_statistics(self, operation_type: str = None) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.lock:
            if operation_type:
                metrics = self.metrics.get(operation_type, [])
            else:
                metrics = []
                for op_metrics in self.metrics.values():
                    metrics.extend(op_metrics)
            
            if not metrics:
                return {}
            
            successful_metrics = [m for m in metrics if m['success']]
            durations = [m['duration'] for m in successful_metrics]
            
            if not durations:
                return {'error': 'No successful operations'}
            
            return {
                'total_operations': len(metrics),
                'successful_operations': len(successful_metrics),
                'success_rate': len(successful_metrics) / len(metrics),
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'p95_duration': self._percentile(durations, 95),
                'p99_duration': self._percentile(durations, 99)
            }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

# Global performance monitor
performance_monitor = PerformanceMonitor()

def monitor_performance(operation_type: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            operation_id = f"{func.__name__}_{int(time.time() * 1000000)}"
            
            performance_monitor.start_operation(
                operation_id, 
                operation_type,
                {'function': func.__name__, 'args_count': len(args)}
            )
            
            try:
                result = func(*args, **kwargs)
                performance_monitor.end_operation(operation_id, success=True)
                return result
            except Exception as e:
                performance_monitor.end_operation(operation_id, success=False, error=str(e))
                raise
        
        return wrapper
    return decorator
```

#### Agent Performance Optimization

```python
# Agent request caching
from functools import lru_cache
import hashlib
import json

class AgentCache:
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
    
    def get_cache_key(self, agent_id: str, action: str, data: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        cache_data = {
            'agent_id': agent_id,
            'action': action,
            'data': data
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def get(self, key: str) -> Any:
        """Get cached result"""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Cache result"""
        if len(self.cache) >= self.max_size:
            # Remove least recently used item
            lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[lru_key]
            del self.access_times[lru_key]
        
        self.cache[key] = value
        self.access_times[key] = time.time()

# Update BaseAgent to use caching
class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str):
        # ... existing initialization
        self.cache = AgentCache()
        self.cacheable_actions = set()  # Override in subclasses
    
    @monitor_performance('agent_request')
    def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent request with caching and monitoring"""
        
        # Check cache for cacheable actions
        if action in self.cacheable_actions:
            cache_key = self.cache.get_cache_key(self.agent_id, action, data)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self.logger.debug(f"Cache hit for {action}")
                return cached_result
        
        try:
            # ... existing processing logic
            result = self._process_action(action, data)
            
            # Cache successful results
            if action in self.cacheable_actions and result.get('success'):
                cache_key = self.cache.get_cache_key(self.agent_id, action, data)
                self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            # ... error handling
            pass
```

#### Database Optimization

```python
# Database query optimization
class OptimizedDatabaseManager(DatabaseManager):
    def __init__(self):
        super().__init__()
        self.query_cache = {}
        self.connection_pool = []
        self.max_pool_size = 10
    
    @lru_cache(maxsize=100)
    def get_cached_query(self, query: str, params: tuple) -> List[Dict]:
        """Cache frequent queries"""
        return super().execute_query(query, params)
    
    def execute_batch_update(self, query: str, param_list: List[tuple]) -> int:
        """Execute batch updates for better performance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, param_list)
            conn.commit()
            return cursor.rowcount
    
    def get_connection_pool(self):
        """Connection pooling for better concurrency"""
        if not self.connection_pool:
            for _ in range(self.max_pool_size):
                conn = sqlite3.connect(
                    self._db_path,
                    check_same_thread=False,
                    timeout=30.0
                )
                conn.row_factory = sqlite3.Row
                self.connection_pool.append(conn)
        
        return self.connection_pool.pop() if self.connection_pool else self._create_connection()

# Database indexing
class DatabaseIndexer:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def create_performance_indexes(self):
        """Create indexes for better query performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner)",
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_project ON socratic_sessions(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_questions_session ON questions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_responses_question ON responses(question_id)",
            "CREATE INDEX IF NOT EXISTS idx_files_codebase ON generated_files(codebase_id)",
            "CREATE INDEX IF NOT EXISTS idx_activities_agent ON agent_activities(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON agent_activities(timestamp)"
        ]
        
        for index in indexes:
            try:
                self.db_manager.execute_update(index)
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
```

### Memory Management

#### Memory Optimization

```python
# Memory-efficient data structures
import weakref
from typing import WeakSet

class MemoryOptimizedAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name)
        self._active_sessions = WeakSet()  # Use weak references
        self._temp_data = {}  # Clear after each request
    
    def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Memory-efficient request processing"""
        try:
            # Clear temporary data from previous requests
            self._temp_data.clear()
            
            result = super().process_request(action, data)
            
            # Clean up large objects
            if hasattr(self, '_large_objects'):
                del self._large_objects
            
            return result
        finally:
            # Force garbage collection for large operations
            if action in ['generate_code', 'process_large_document', 'analyze_conversation']:
                import gc
                gc.collect()

# Memory monitoring
class MemoryMonitor:
    def __init__(self):
        self.logger = get_logger('memory')
        self.thresholds = {
            'warning': 500 * 1024 * 1024,  # 500MB
            'critical': 1024 * 1024 * 1024  # 1GB
        }
    
    def check_memory_usage(self):
        """Monitor memory usage and log warnings"""
        import psutil
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        if memory_info.rss > self.thresholds['critical']:
            self.logger.critical(f"Critical memory usage: {memory_info.rss / 1024 / 1024:.1f}MB")
            # Force garbage collection
            import gc
            gc.collect()
        elif memory_info.rss > self.thresholds['warning']:
            self.logger.warning(f"High memory usage: {memory_info.rss / 1024 / 1024:.1f}MB")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get detailed memory statistics"""
        import psutil
        import gc
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss,
            'vms': memory_info.vms,
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available,
            'gc_counts': gc.get_count(),
            'gc_stats': gc.get_stats()
        }

# Global memory monitor
memory_monitor = MemoryMonitor()
```

### Async Processing

#### Asynchronous Agent Operations

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Awaitable

class AsyncAgentOrchestrator(AgentOrchestrator):
    def __init__(self):
        super().__init__()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.background_tasks = set()
    
    async def route_request_async(self, agent_id: str, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous agent request routing"""
        loop = asyncio.get_event_loop()
        
        # Run agent request in thread pool
        result = await loop.run_in_executor(
            self.executor,
            self.route_request,
            agent_id, action, data
        )
        
        return result
    
    def schedule_background_task(self, coro: Awaitable):
        """Schedule background task"""
        task = asyncio.create_task(coro)
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def process_long_running_operation(self, operation_id: str, data: Dict[str, Any]):
        """Handle long-running operations asynchronously"""
        try:
            # Update status to processing
            await self._update_operation_status(operation_id, 'processing')
            
            # Process in chunks to avoid blocking
            for chunk in self._chunk_operation(data):
                result = await self._process_chunk(chunk)
                await self._update_operation_progress(operation_id, result)
                
                # Yield control to other tasks
                await asyncio.sleep(0.1)
            
            # Mark as completed
            await self._update_operation_status(operation_id, 'completed')
            
        except Exception as e:
            await self._update_operation_status(operation_id, 'failed', str(e))
            self.logger.error(f"Background operation {operation_id} failed: {e}")

# Async code generation
class AsyncCodeGeneratorAgent(CodeGeneratorAgent):
    async def generate_project_files_async(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous project file generation"""
        
        # Break down generation into phases
        phases = [
            'analyze_specification',
            'design_architecture', 
            'generate_backend',
            'generate_frontend',
            'generate_tests',
            'generate_documentation'
        ]
        
        results = {}
        
        for phase in phases:
            self.logger.info(f"Starting phase: {phase}")
            
            # Process phase asynchronously
            phase_result = await self._process_phase_async(phase, specification)
            results[phase] = phase_result
            
            # Emit progress event
            self._emit_event('generation_progress', {
                'phase': phase,
                'completed_phases': list(results.keys()),
                'total_phases': len(phases)
            })
            
            # Brief pause to prevent overwhelming the system
            await asyncio.sleep(0.5)
        
        return {
            'success': True,
            'data': {
                'phases': results,
                'generated_files': self._collect_generated_files(results)
            }
        }
```

---

## 🔒 Security Considerations

### Authentication and Authorization

#### Secure Authentication

```python
# src/security/auth.py
import hashlib
import secrets
import jwt
import time
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from src.core import get_config, ValidationError

class AuthenticationManager:
    def __init__(self):
        self.config = get_config()
        self.secret_key = self.config.get('security.secret_key')
        if not self.secret_key:
            raise ValidationError("Secret key not configured")
    
    def hash_password(self, password: str) -> str:
        """Securely hash password"""
        # Validate password strength
        if not self._validate_password_strength(password):
            raise ValidationError("Password does not meet security requirements")
        
        return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return check_password_hash(password_hash, password)
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password meets security requirements"""
        min_length = self.config.get('security.auth.password_min_length', 8)
        require_special = self.config.get('security.auth.password_require_special', True)
        
        if len(password) < min_length:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*(),.?\":{}|<>" for c in password)
        
        basic_requirements = has_upper and has_lower and has_digit
        
        if require_special:
            return basic_requirements and has_special
        else:
            return basic_requirements
    
    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'iat': int(time.time()),
            'exp': int(time.time()) + expires_in
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValidationError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValidationError("Invalid token")
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def verify_csrf_token(self, token: str, session_token: str) -> bool:
        """Verify CSRF token"""
        return secrets.compare_digest(token, session_token)

class RoleBasedAccessControl:
    def __init__(self):
        self.permissions = {
            'admin': [
                'manage_users', 'manage_system', 'view_all_projects',
                'delete_any_project', 'modify_system_config'
            ],
            'project_manager': [
                'create_project', 'manage_own_projects', 'invite_collaborators',
                'generate_code', 'export_projects'
            ],
            'developer': [
                'create_project', 'manage_own_projects', 'generate_code',
                'run_tests', 'view_code'
            ],
            'viewer': [
                'view_projects', 'view_code'
            ]
        }
    
    def has_permission(self, user_roles: List[str], required_permission: str) -> bool:
        """Check if user has required permission"""
        for role in user_roles:
            if required_permission in self.permissions.get(role, []):
                return True
        return False
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Get current user from context
                user = get_current_user()
                if not user:
                    raise ValidationError("Authentication required")
                
                if not self.has_permission(user.roles, permission):
                    raise ValidationError(f"Permission '{permission}' required")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
```

#### Input Validation and Sanitization

```python
# src/security/validation.py
import re
import html
import bleach
from typing import Any, Dict, List
from src.core import ValidationError

class InputValidator:
    def __init__(self):
        self.allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
        self.allowed_attributes = {}
    
    def validate_and_sanitize_input(self, data: Dict[str, Any], schema: Dict[str, Dict]) -> Dict[str, Any]:
        """Validate and sanitize input data according to schema"""
        sanitized = {}
        
        for field, rules in schema.items():
            if field not in data:
                if rules.get('required', False):
                    raise ValidationError(f"Required field '{field}' is missing")
                continue
            
            value = data[field]
            sanitized[field] = self._validate_field(field, value, rules)
        
        return sanitized
    
    def _validate_field(self, field_name: str, value: Any, rules: Dict[str, Any]) -> Any:
        """Validate individual field"""
        field_type = rules.get('type', 'string')
        
        if field_type == 'string':
            return self._validate_string(field_name, value, rules)
        elif field_type == 'integer':
            return self._validate_integer(field_name, value, rules)
        elif field_type == 'email':
            return self._validate_email(field_name, value, rules)
        elif field_type == 'html':
            return self._validate_html(field_name, value, rules)
        else:
            raise ValidationError(f"Unknown field type: {field_type}")
    
    def _validate_string(self, field_name: str, value: str, rules: Dict[str, Any]) -> str:
        """Validate string field"""
        if not isinstance(value, str):
            raise ValidationError(f"Field '{field_name}' must be a string")
        
        # Length validation
        min_length = rules.get('min_length', 0)
        max_length = rules.get('max_length', 10000)
        
        if len(value) < min_length:
            raise ValidationError(f"Field '{field_name}' must be at least {min_length} characters")
        
        if len(value) > max_length:
            raise ValidationError(f"Field '{field_name}' must be no more than {max_length} characters")
        
        # Pattern validation
        pattern = rules.get('pattern')
        if pattern and not re.match(pattern, value):
            raise ValidationError(f"Field '{field_name}' has invalid format")
        
        # Sanitize
        if rules.get('escape_html', True):
            value = html.escape(value)
        
        return value.strip()
    
    def _validate_email(self, field_name: str, value: str, rules: Dict[str, Any]) -> str:
        """Validate email field"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
        
        if not re.match(email_pattern, value):
            raise ValidationError(f"Field '{field_name}' must be a valid email address")
        
        return value.lower().strip()
    
    def _validate_html(self, field_name: str, value: str, rules: Dict[str, Any]) -> str:
        """Validate and sanitize HTML content"""
        # Use bleach to sanitize HTML
        sanitized = bleach.clean(
            value,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            strip=True
        )
        
        return sanitized

# Validation schemas
PROJECT_SCHEMA = {
    'name': {
        'type': 'string',
        'required': True,
        'min_length': 2,
        'max_length': 100,
        'pattern': r'^[a-zA-Z0-9\s\-_]+
    },
    'description': {
        'type': 'string',
        'required': False,
        'max_length': 1000,
        'escape_html': True
    }
}

RESPONSE_SCHEMA = {
    'response_text': {
        'type': 'string',
        'required': True,
        'min_length': 10,
        'max_length': 5000
    },
    'confidence_level': {
        'type': 'integer',
        'required': False,
        'min_value': 1,
        'max_value': 5
    }
}
```

#### Security Headers and CSRF Protection

```python
# src/security/middleware.py
from flask import request, session, abort, g
import secrets

class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Security checks before each request"""
        # CSRF protection for state-changing requests
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            self._check_csrf_token()
        
        # Rate limiting check
        self._check_rate_limit()
        
        # Security headers validation
        self._validate_security_headers()
    
    def after_request(self, response):
        """Add security headers after each request"""
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = self._get_csp_header()
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    def _check_csrf_token(self):
        """Check CSRF token for state-changing requests"""
        if not session.get('csrf_token'):
            session['csrf_token'] = secrets.token_urlsafe(32)
        
        submitted_token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        
        if not submitted_token or not secrets.compare_digest(
            submitted_token, session['csrf_token']
        ):
            abort(403)
    
    def _check_rate_limit(self):
        """Basic rate limiting"""
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        
        # Simple in-memory rate limiting (use Redis in production)
        if not hasattr(g, 'rate_limits'):
            g.rate_limits = {}
        
        current_time = time.time()
        window_size = 60  # 1 minute
        max_requests = 100  # 100 requests per minute
        
        if client_ip in g.rate_limits:
            requests = g.rate_limits[client_ip]
            # Remove old requests outside window
            requests = [req_time for req_time in requests if current_time - req_time < window_size]
            
            if len(requests) >= max_requests:
                abort(429)  # Too Many Requests
            
            requests.append(current_time)
            g.rate_limits[client_ip] = requests
        else:
            g.rate_limits[client_ip] = [current_time]
    
    def _get_csp_header(self) -> str:
        """Generate Content Security Policy header"""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
```

### Code Generation Security

#### Secure Code Generation

```python
# src/security/code_security.py
import ast
import re
from typing import List, Dict, Any
from src.core import ValidationError

class CodeSecurityScanner:
    def __init__(self):
        self.dangerous_patterns = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
            r'subprocess\.',
            r'os\.system',
            r'os\.popen',
            r'shell=True',
            r'pickle\.loads',
            r'marshal\.loads'
        ]
        
        self.allowed_imports = {
            'os': ['path', 'environ'],
            'sys': ['version', 'platform'],
            'json': ['loads', 'dumps'],
            'datetime': ['datetime', 'date', 'time'],
            'typing': ['List', 'Dict', 'Any', 'Optional'],
            'flask': ['Flask', 'request', 'jsonify'],
            'sqlalchemy': ['Column', 'Integer', 'String', 'DateTime']
        }
    
    def scan_code(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Scan code for security vulnerabilities"""
        if language == 'python':
            return self._scan_python_code(code)
        elif language == 'javascript':
            return self._scan_javascript_code(code)
        else:
            return {'safe': True, 'issues': []}
    
    def _scan_python_code(self, code: str) -> Dict[str, Any]:
        """Scan Python code for security issues"""
        issues = []
        
        # Pattern-based scanning
        for pattern in self.dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    'type': 'dangerous_function',
                    'pattern': pattern,
                    'severity': 'high',
                    'message': f'Potentially dangerous pattern detected: {pattern}'
                })
        
        # AST-based analysis
        try:
            tree = ast.parse(code)
            ast_issues = self._analyze_ast(tree)
            issues.extend(ast_issues)
        except SyntaxError as e:
            issues.append({
                'type': 'syntax_error',
                'severity': 'high',
                'message': f'Syntax error: {e}'
            })
        
        return {
            'safe': len(issues) == 0,
            'issues': issues,
            'scanned_lines': len(code.split('\n'))
        }
    
    def _analyze_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Analyze Python AST for security issues"""
        issues = []
        
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.allowed_imports:
                        issues.append({
                            'type': 'unauthorized_import',
                            'severity': 'medium',
                            'message': f'Unauthorized import: {alias.name}',
                            'line': node.lineno
                        })
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                if module and module not in self.allowed_imports:
                    issues.append({
                        'type': 'unauthorized_import',
                        'severity': 'medium',
                        'message': f'Unauthorized import from: {module}',
                        'line': node.lineno
                    })
                elif module and node.names:
                    allowed_names = self.allowed_imports.get(module, [])
                    for alias in node.names:
                        if alias.name != '*' and alias.name not in allowed_names:
                            issues.append({
                                'type': 'unauthorized_function',
                                'severity': 'medium',
                                'message': f'Unauthorized function import: {module}.{alias.name}',
                                'line': node.lineno
                            })
            
            # Check for dangerous function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ['eval', 'exec']:
                    issues.append({
                        'type': 'dangerous_function',
                        'severity': 'high',
                        'message': f'Dangerous function call: {node.func.id}',
                        'line': node.lineno
                    })
        
        return issues
    
    def sanitize_generated_code(self, code: str, language: str = 'python') -> str:
        """Sanitize generated code by removing dangerous patterns"""
        if language == 'python':
            return self._sanitize_python_code(code)
        return code
    
    def _sanitize_python_code(self, code: str) -> str:
        """Sanitize Python code"""
        # Remove dangerous function calls
        for pattern in self.dangerous_patterns:
            code = re.sub(pattern, '# REMOVED: Potentially dangerous code', code, flags=re.IGNORECASE)
        
        return code

class SecureCodeGenerator:
    def __init__(self):
        self.security_scanner = CodeSecurityScanner()
        self.templates = {
            'flask_app': self._get_secure_flask_template(),
            'api_endpoint': self._get_secure_api_template(),
            'database_model': self._get_secure_model_template()
        }
    
    def generate_secure_code(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Generate secure code from template"""
        if template_name not in self.templates:
            raise ValidationError(f"Unknown template: {template_name}")
        
        template = self.templates[template_name]
        
        # Sanitize variables
        sanitized_vars = self._sanitize_variables(variables)
        
        # Generate code
        code = template.format(**sanitized_vars)
        
        # Security scan
        scan_result = self.security_scanner.scan_code(code)
        if not scan_result['safe']:
            raise ValidationError(f"Generated code failed security scan: {scan_result['issues']}")
        
        return code
    
    def _sanitize_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize template variables"""
        sanitized = {}
        
        for key, value in variables.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized[key] = re.sub(r'[<>&"\'`]', '', value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _get_secure_flask_template(self) -> str:
        """Secure Flask application template"""
        return '''
from flask import Flask, request, jsonify, escape
from werkzeug.security import generate_password_hash, check_password_hash
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = '{secret_key}'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/{endpoint}', methods=['POST'])
def {function_name}():
    """Secure endpoint: {description}"""
    try:
        # Validate input
        data = request.get_json()
        if not data:
            return jsonify({{'error': 'No data provided'}}), 400
        
        # Sanitize input
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = escape(value)
        
        # Process request
        result = process_{function_name}(data)
        
        # Log successful request
        logger.info(f"Successful request to {endpoint}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in {function_name}: {{e}}")
        return jsonify({{'error': 'Internal server error'}}), 500

def process_{function_name}(data):
    """Process the request data securely"""
    # Implementation here
    return {{'success': True, 'data': data}}

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1')
'''
```

---

## 🚀 Deployment & DevOps

### Docker Configuration

#### Production Dockerfile

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production

# Create non-root user
RUN groupadd -r socratic && useradd -r -g socratic socratic

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-prod.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/logs data/uploads data/exports data/generated_projects data/vector_db

# Change ownership to non-root user
RUN chown -R socratic:socratic /app

# Switch to non-root user
USER socratic

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "gevent", "run:app"]
```

#### Docker Compose for Development

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - socratic_data:/app/data
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      - SOCRATIC_DEBUG=true
      - DATABASE_URL=postgresql://socratic:socratic@db:5432/socratic_dev
    depends_on:
      - db
      - redis
      - chroma
    networks:
      - socratic-network

  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: socratic_dev
      POSTGRES_USER: socratic
      POSTGRES_PASSWORD: socratic
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - socratic-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - socratic-network

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
    networks:
      - socratic-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.dev.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - app
    networks:
      - socratic-network

volumes:
  socratic_data:
  postgres_data:
  redis_data:
  chroma_data:

networks:
  socratic-network:
    driver: bridge
```

#### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    image: socratic-rag-enhanced:latest
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://socratic:${DB_PASSWORD}@db:5432/socratic_prod
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    networks:
      - socratic-network
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure

  db:
    image: postgres:14-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: socratic_prod
      POSTGRES_USER: socratic
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - socratic-network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_prod_data:/data
    networks:
      - socratic-network

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - socratic-network

  backup:
    image: socratic-rag-enhanced:latest
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://socratic:${DB_PASSWORD}@db:5432/socratic_prod
    volumes:
      - ./backups:/backups
    command: python scripts/backup.py
    networks:
      - socratic-network
    deploy:
      replicas: 1

volumes:
  postgres_prod_data:
  redis_prod_data:

networks:
  socratic-network:
    external: true
```

### Kubernetes Deployment

#### Kubernetes Manifests

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: socratic-rag

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: socratic-config
  namespace: socratic-rag
data:
  config.yaml: |
    app:
      name: "Socratic RAG Enhanced"
      environment: "production"
      debug: false
    database:
      sqlite:
        path: "/app/data/projects.db"
    logging:
      level: "INFO"
      file:
        enabled: true
        path: "/app/data/logs"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: socratic-secrets
  namespace: socratic-rag
type: Opaque
stringData:
  anthropic-api-key: "your-anthropic-api-key"
  secret-key: "your-secret-key"
  db-password: "your-db-password"

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: socratic-app
  namespace: socratic-rag
  labels:
    app: socratic-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: socratic-app
  template:
    metadata:
      labels:
        app: socratic-app
    spec:
      containers:
      - name: socratic-app
        image: socratic-rag-enhanced:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: socratic-secrets
              key: anthropic-api-key
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: socratic-secrets
              key: secret-key
        volumeMounts:
        - name: config-volume
          mountPath: /app/config.yaml
          subPath: config.yaml
        - name: data-volume
          mountPath: /app/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config-volume
        configMap:
          name: socratic-config
      - name: data-volume
        persistentVolumeClaim:
          claimName: socratic-data-pvc

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: socratic-service
  namespace: socratic-rag
spec:
  selector:
    app: socratic-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: socratic-ingress
  namespace: socratic-rag
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - socratic.yourdomain.com
    secretName: socratic-tls
  rules:
  - host: socratic.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: socratic-service
            port:
              number: 80
```

### CI/CD Pipeline

#### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches:
      - main
    tags:
      - 'v*'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Security scan
      run: |
        bandit -r src/
        safety check

  build:
    needs: test
    runs-on: ubuntu-latest
    
    outputs:
      image: ${{ steps.image.outputs.image }}
      digest: ${{ steps.build.outputs.digest }}
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
    
    - name: Build and push Docker image
      id: build
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to staging
      run: |
        # Deploy to staging environment
        echo "Deploying to staging..."
        # Add your staging deployment commands here

  deploy-production:
    needs: [build, deploy-staging]
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
    
    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
    
    - name: Deploy to Kubernetes
      run: |
        # Update image in deployment
        kubectl set image deployment/socratic-app \
          socratic-app=${{ needs.build.outputs.image }}@${{ needs.build.outputs.digest }} \
          --namespace=socratic-rag
        
        # Wait for rollout
        kubectl rollout status deployment/socratic-app --namespace=socratic-rag
    
    - name: Run post-deployment tests
      run: |
        # Run smoke tests against production
        python scripts/smoke_tests.py --env production
```

### Monitoring and Logging

#### Application Monitoring

```python
# src/monitoring/metrics.py
import time
import threading
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from src.core import get_logger

class MetricsCollector:
    def __init__(self):
        self.logger = get_logger('metrics')
        
        # Define metrics
        self.request_count = Counter(
            'socratic_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'socratic_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )
        
        self.agent_operations = Counter(
            'socratic_agent_operations_total',
            'Total agent operations',
            ['agent_id', 'action', 'status']
        )
        
        self.active_sessions = Gauge(
            'socratic_active_sessions',
            'Number of active Socratic sessions'
        )
        
        self.code_generation_duration = Histogram(
            'socratic_code_generation_duration_seconds',
            'Code generation duration in seconds',
            ['project_type']
        )
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        self.request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_agent_operation(self, agent_id: str, action: str, success: bool):
        """Record agent operation metrics"""
        status = 'success' if success else 'failure'
        self.agent_operations.labels(agent_id=agent_id, action=action, status=status).inc()
    
    def set_active_sessions(self, count: int):
        """Set active sessions count"""
        self.active_sessions.set(count)
    
    def record_code_generation(self, project_type: str, duration: float):
        """Record code generation metrics"""
        self.code_generation_duration.labels(project_type=project_type).observe(duration)

# Global metrics collector
metrics = MetricsCollector()

def init_metrics_server(port: int = 8080):
    """Initialize Prometheus metrics server"""
    start_http_server(port)
    get_logger('metrics').info(f"Metrics server started on port {port}")
```

#### Centralized Logging

```python
# src/monitoring/logging_config.py
import logging
import logging.handlers
import json
from datetime import datetime
from src.core import get_config, DateTimeHelper

class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': DateTimeHelper.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        return json.dumps(log_entry)

def setup_production_logging():
    """Setup production logging configuration"""
    config = get_config()
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler for application logs
    app_handler = logging.handlers.RotatingFileHandler(
        'logs/application.log',
        maxBytes=50*1024*1024,  # 50MB
        backupCount=10
    )
    app_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(app_handler)
    
    # Separate handler for errors
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)
```

---

## 🤝 Contributing Guidelines

### Development Workflow

#### Getting Started

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/socratic-rag-enhanced.git
   cd socratic-rag-enhanced
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Code Standards

##### Python Style Guide

```python
# Follow PEP 8 with these specific guidelines:

# 1. Line length: 88 characters (Black default)
# 2. Use type hints for all function parameters and return values
def process_data(items: List[Dict[str, Any]]) -> Dict[str, int]:
    """Process data items and return summary statistics."""
    pass

# 3. Use descriptive variable names
user_sessions = get_active_sessions()
project_count = len(user_projects)

# 4. Document all public functions and classes
class DataProcessor:
    """Process and analyze user-generated data.
    
    This class handles the processing of various data types
    from user interactions and generates insights.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize processor with configuration.
        
        Args:
            config: Configuration dictionary containing processing parameters
        """
        self.config = config

# 5. Use constants for magic numbers
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30
CACHE_EXPIRY_HOURS = 24

# 6. Handle errors explicitly
try:
    result = process_request(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    return error_response("Invalid input data")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    return error_response("Internal server error")
```

##### Documentation Standards

```python
# Use Google-style docstrings

def generate_questions(
    session_id: str, 
    role_type: str, 
    context: Dict[str, Any]
) -> List[Question]:
    """Generate Socratic questions for a given role and context.
    
    This function creates contextually appropriate questions based on the
    specified role type and session context. Questions are designed to
    elicit detailed requirements and uncover potential conflicts.
    
    Args:
        session_id: Unique identifier for the questioning session
        role_type: Role perspective for question generation (e.g., 'project_manager')
        context: Session context including project details and previous responses
    
    Returns:
        List of Question objects ordered by priority and dependency
    
    Raises:
        ValidationError: If session_id is invalid or role_type is not supported
        ServiceError: If external AI service is unavailable
    
    Example:
        >>> questions = generate_questions('sess-123', 'developer', {'project_type': 'web_app'})
        >>> len(questions)
        5
        >>> questions[0].text
        'What are the core features users need most?'
    """
    pass
```

#### Testing Requirements

##### Test Coverage Standards

- **Minimum Coverage**: 80% overall code coverage
- **Agent Tests**: 90% coverage for all agent classes
- **API Tests**: 95% coverage for all API endpoints
- **Security Tests**: 100% coverage for authentication and authorization

##### Test Structure

```python
# tests/unit/test_agents/test_socratic_agent.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agents.socratic import SocraticCounselorAgent

class TestSocraticCounselorAgent:
    """Test suite for SocraticCounselorAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return SocraticCounselorAgent()
    
    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude API response."""
        return """
        Based on your project requirements, here are some key questions:
        1. What is the primary user workflow?
        2. What are the performance requirements?
        """
    
    def test_initialization(self, agent):
        """Test agent initializes with correct properties."""
        assert agent.agent_id == "socratic_counselor"
        assert agent.name == "Socratic Counselor"
        assert "generate_questions" in agent.get_capabilities()
    
    @patch('src.agents.socratic.get_db_manager')
    def test_start_session_success(self, mock_db, agent):
        """Test successful session creation."""
        # Arrange
        mock_db.return_value.execute_update.return_value = 1
        data = {
            'project_id': 'test-project',
            'username': 'testuser',
            'questioning_mode': 'sequential'
        }
        
        # Act
        result = agent._start_session(data)
        
        # Assert
        assert result['success'] is True
        assert 'session_id' in result['data']
        mock_db.return_value.execute_update.assert_called_once()
    
    @pytest.mark.parametrize("mode,expected_roles", [
        ("sequential", ["project_manager", "technical_lead", "developer"]),
        ("dynamic", ["project_manager", "developer"]),
        ("custom", ["project_manager"])
    ])
    def test_questioning_modes(self, agent, mode, expected_roles):
        """Test different questioning modes."""
        # Test implementation here
        pass
    
    def test_error_handling(self, agent):
        """Test agent handles errors gracefully."""
        # Test error scenarios
        pass
```

#### Pull Request Process

##### PR Template

```markdown
## Description
Brief description of the changes in this PR.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All tests pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or breaking changes documented)
- [ ] Security considerations reviewed

## Related Issues
Fixes #(issue number)

## Screenshots (if applicable)
Add screenshots to help explain your changes.
```

##### Review Process

1. **Automated Checks**: All CI/CD checks must pass
2. **Code Review**: At least one maintainer review required
3. **Testing**: All tests must pass with adequate coverage
4. **Documentation**: Updates to docs if functionality changes
5. **Security Review**: Security implications assessed

### Agent Development Guidelines

#### Creating New Agents

```python
# Template for new agent development
# src/agents/your_new_agent.py

from typing import List, Dict, Any
from src.agents.base import BaseAgent, require_authentication, log_agent_action
from src.core import AgentError, ValidationError

class YourNewAgent(BaseAgent):
    """Agent for [specific functionality].
    
    This agent handles [detailed description of agent purpose and capabilities].
    It integrates with [list external services/other agents it works with].
    """
    
    def __init__(self):
        super().__init__("your_new_agent", "Your New Agent")
        
        # Agent-specific configuration
        self.max_concurrent_operations = self.config.get('agents.your_new_agent.max_concurrent', 5)
        self.timeout_seconds = self.config.get('agents.your_new_agent.timeout_seconds', 300)
        
        # Initialize agent-specific resources
        self._initialize_resources()
    
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        return [
            "capability_one",
            "capability_two", 
            "capability_three"
        ]
    
    def _initialize_resources(self):
        """Initialize agent-specific resources."""
        # Setup any required resources, connections, etc.
        pass
    
    @require_authentication
    @log_agent_action
    def _capability_one(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Implement capability one.
        
        Args:
            data: Request data containing required parameters
            
        Returns:
            Dictionary with success status and result data
            
        Raises:
            ValidationError: If input validation fails
            AgentError: If processing fails
        """
        try:
            # Validate input
            self._validate_capability_one_input(data)
            
            # Process request
            result = self._process_capability_one(data)
            
            # Emit success event
            self._emit_event('capability_one_completed', {
                'result_summary': result.get('summary'),
                'processing_time': result.get('processing_time')
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Capability one processing failed: {e}")
            raise AgentError(f"Failed to process capability one: {e}")
    
    def _validate_capability_one_input(self, data: Dict[str, Any]):
        """Validate input for capability one."""
        required_fields = ['field1', 'field2']
        
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Required field '{field}' missing")
    
    def _process_capability_one(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Core processing logic for capability one."""
        # Implement your processing logic here
        return {
            'success': True,
            'data': {'processed': True},
            'summary': 'Processing completed successfully'
        }

# Register the agent
# Add to src/agents/__init__.py:
# from src.agents.your_new_agent import YourNewAgent
```

#### Agent Testing Template

```python
# tests/unit/test_agents/test_your_new_agent.py

import pytest
from unittest.mock import Mock, patch
from src.agents.your_new_agent import YourNewAgent

class TestYourNewAgent:
    """Test suite for YourNewAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return YourNewAgent()
    
    @pytest.fixture
    def valid_input_data(self):
        """Valid input data for testing."""
        return {
            'field1': 'value1',
            'field2': 'value2',
            'username': 'testuser'
        }
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.agent_id == "your_new_agent"
        assert agent.name == "Your New Agent"
        capabilities = agent.get_capabilities()
        assert "capability_one" in capabilities
    
    def test_capability_one_success(self, agent, valid_input_data):
        """Test successful capability one execution."""
        result = agent._capability_one(valid_input_data)
        
        assert result['success'] is True
        assert 'data' in result
    
    def test_capability_one_validation_error(self, agent):
        """Test capability one with invalid input."""
        invalid_data = {'username': 'testuser'}  # Missing required fields
        
        with pytest.raises(ValidationError):
            agent._capability_one(invalid_data)
    
    @patch('src.agents.your_new_agent.external_service_call')
    def test_capability_one_external_service_failure(self, mock_service, agent, valid_input_data):
        """Test handling of external service failures."""
        mock_service.side_effect = Exception("Service unavailable")
        
        with pytest.raises(AgentError):
            agent._capability_one(valid_input_data)
```

### Security Guidelines

#### Security Checklist for Contributors

- [ ] **Input Validation**: All user inputs validated and sanitized
- [ ] **SQL Injection**: No dynamic SQL construction with user input
- [ ] **XSS Prevention**: All output properly escaped
- [ ] **Authentication**: Proper authentication checks in place
- [ ] **Authorization**: Proper authorization checks in place
- [ ] **Secrets**: No hardcoded secrets or API keys
- [ ] **Error Handling**: No sensitive information in error messages
- [ ] **Logging**: No sensitive data logged
- [ ] **Dependencies**: No known vulnerable dependencies

#### Security Review Process

1. **Automated Security Scanning**: All PRs scanned with bandit and safety
2. **Manual Security Review**: Security team reviews security-sensitive changes
3. **Penetration Testing**: Major features undergo penetration testing
4. **Dependency Updates**: Regular updates to address security vulnerabilities

### Documentation Guidelines

#### Documentation Requirements

1. **Code Documentation**: All public APIs documented with docstrings
2. **Architecture Documentation**: Major architectural decisions documented
3. **User Documentation**: User-facing features documented in user guide
4. **API Documentation**: REST API endpoints documented with OpenAPI
5. **Deployment Documentation**: Deployment procedures documented

#### Documentation Style

- Use clear, concise language
- Provide examples for complex concepts
- Keep documentation up-to-date with code changes
- Use diagrams for complex workflows
- Include troubleshooting sections

---

## 📚 Additional Resources

### Further Reading

- **Clean Code** by Robert Martin - Best practices for writing maintainable code
- **Designing Data-Intensive Applications** by Martin Kleppmann - Database and system design
- **Flask Web Development** by Miguel Grinberg - Advanced Flask patterns
- **Test-Driven Development** by Kent Beck - Testing best practices

### External Documentation

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Community Resources

- **GitHub Discussions**: Project discussions and Q&A
- **Discord Server**: Real-time developer chat
- **Blog**: Technical blog with development insights
- **YouTube Channel**: Video tutorials and demos

---

*This developer guide is continuously updated. For the latest version, check the repository documentation.*

**Happy coding! 🚀**