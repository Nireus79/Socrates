# Development Setup Guide

Complete guide for setting up Socratic for development and contributing to the project.

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Running Full Stack](#running-full-stack)
3. [Backend Development](#backend-development)
4. [Frontend Development](#frontend-development)
5. [Testing](#testing)
6. [Key Components](#key-components)
7. [Common Development Tasks](#common-development-tasks)
8. [Contributing](#contributing)

---

## Environment Setup

### Clone Repository

```bash
git clone https://github.com/Nireus79/Socrates.git
cd Socrates
```

### Python Virtual Environment

```bash
# Create venv
python -m venv .venv

# Activate
source .venv/bin/activate      # Linux/macOS
# or
.venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### API Key Setup

```bash
# Set Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Node.js Setup (for Frontend)

```bash
# Check versions
node --version    # Should be 18+
npm --version     # Should be 9+

# If not installed:
# macOS: brew install node
# Ubuntu: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install -y nodejs
# Windows: Download from nodejs.org
```

---

## Running Full Stack

### Development Mode (API + Frontend)

```bash
# Terminal 1: Start API with auto-reload
python socrates.py --api --reload

# Terminal 2: Start Frontend dev server
cd socrates-frontend
npm install
npm run dev

# Frontend will be at http://localhost:5173
# API will be at http://localhost:8000
```

### Or Use Full Stack Mode

```bash
# Starts both API and Frontend together
python socrates.py --full

# Press Ctrl+C to stop both servers gracefully
```

### API Documentation

Once running, visit: http://localhost:8000/docs

This shows all API endpoints with auto-generated documentation.

---

## Backend Development

### Project Structure

```
socratic_system/
├── agents/                    # AI agent implementations
│   ├── learning_agent.py     # User learning tracking
│   ├── code_generator.py     # Code generation
│   ├── socratic_counselor.py # Dialogue engine
│   └── ...                   # Other agents
├── clients/
│   └── claude_client.py       # Claude API client
├── core/
│   ├── insight_categorizer.py # Insight classification
│   ├── learning_engine.py    # Learning analytics
│   └── maturity_calculator.py # Project maturity
├── database/
│   ├── vector_db.py          # ChromaDB wrapper
│   ├── project_db.py         # SQLite operations
│   └── search_cache.py       # Search caching
├── models/                    # Data models
├── orchestration/
│   └── orchestrator.py       # Central coordinator
└── ui/
    └── commands/             # CLI commands
```

### Running Backend Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_claude_categorization.py -v

# Run with coverage
pytest tests/ --cov=socratic_system

# Run only core tests (skip async)
pytest tests/ --ignore=tests/async/ -q
```

### Key Backend Components

#### VectorDatabase (vector_db.py)
- Manages ChromaDB connections
- Handles embeddings with SentenceTransformer
- Provides semantic search
- **New**: Added `close()` method for proper cleanup

#### ClaudeClient (claude_client.py)
- Wrapper around Anthropic API
- Provides `generate_response()` method for general responses
- Includes specialized methods (code generation, suggestions, etc.)
- Token usage tracking

#### AgentOrchestrator (orchestrator.py)
- Central hub coordinating 10+ agents
- Manages request routing
- **New**: Added `close()` method for resource cleanup

### Making Code Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** and test frequently:
   ```bash
   pytest tests/ -x  # Stop on first failure
   ```

3. **Format code**:
   ```bash
   black socratic_system/
   isort socratic_system/
   ```

4. **Run linting**:
   ```bash
   ruff check socratic_system/
   mypy socratic_system/
   ```

5. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: Description of changes"
   git push origin feature/your-feature-name
   ```

---

## Frontend Development

### Project Structure

```
socrates-frontend/
├── src/
│   ├── components/         # React components
│   ├── pages/             # Page components
│   ├── stores/            # Zustand state management
│   │   └── authStore.ts   # Authentication state (FIXED)
│   ├── api/
│   │   └── client.ts      # Axios HTTP client
│   └── App.tsx            # Main app component
├── public/                # Static assets
├── package.json           # Dependencies
└── vite.config.ts         # Vite configuration
```

### Running Frontend Dev Server

```bash
cd socrates-frontend
npm install
npm run dev

# Frontend will be at http://localhost:5173
```

### Frontend Changes

#### Authentication (authStore.ts)

The authentication system was recently fixed:

**Key Changes**:
- Token keys now use `access_token` and `refresh_token` (matching API response)
- Added `isAuthenticated` flag for state tracking
- Added `restoreAuthFromStorage()` for persistence on reload
- Proper cleanup on logout

**Before (BROKEN)**:
```typescript
localStorage.setItem('authToken', response.data.token);  // ❌ Wrong key and property
```

**After (FIXED)**:
```typescript
localStorage.setItem('access_token', response.data.access_token);  // ✅ Correct
localStorage.setItem('refresh_token', response.data.refresh_token);  // ✅ Correct
```

#### API Client (client.ts)

- Uses axios with Bearer token injection
- Automatic token refresh on 401
- Request/response interceptors
- Queues requests during token refresh

### Testing Frontend

```bash
cd socrates-frontend

# Run unit tests
npm test

# Run with coverage
npm test -- --coverage

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## Testing

### Test Organization

```
tests/
├── agents/                    # Agent tests
├── caching/                   # Cache system tests
├── clients/                   # Client tests
├── core/                      # Core system tests
├── database/                  # Database tests
├── integration/               # Integration tests
├── async/                     # Async operation tests
├── performance/               # Performance benchmarks
└── conftest.py               # Pytest fixtures
```

### Important Test Updates

#### Test Mocks (conftest.py)

The mock fixtures were updated to include `generate_response`:

```python
@pytest.fixture
def mock_claude_client():
    """Create a mock Claude client for testing."""
    client = MagicMock()
    client.generate_code = MagicMock(return_value="# Generated code")
    client.extract_insights = MagicMock(return_value={"insights": {}})
    client.generate_socratic_question = MagicMock(return_value="What do you think?")
    client.generate_response = MagicMock(return_value="Mock response from Claude")  # ✅ NEW
    return client
```

#### Test Resource Cleanup

Test fixtures now properly close resources:

```python
@pytest.fixture
async def orchestrator():
    """Create orchestrator with proper cleanup"""
    import gc
    with tempfile.TemporaryDirectory() as tmpdir:
        config = SocratesConfig(...)
        orch = AgentOrchestrator(config)
        yield orch
        # ✅ Proper cleanup before temp deletion
        try:
            orch.close()
        except Exception:
            pass
        gc.collect()
```

### Running Tests

```bash
# All core tests
pytest tests/ --ignore=tests/async/ -v

# Specific test file
pytest tests/test_claude_categorization.py -v

# Specific test
pytest tests/test_claude_categorization.py::test_claude_categorization_parsing -v

# With coverage report
pytest tests/ --ignore=tests/async/ --cov=socratic_system

# Stop on first failure
pytest tests/ -x
```

### Test Status

Current test results:
- **Core Tests**: 360/360 passing (100%)
- **Extended Tests**: 434/440 passing (98.6%)
- **Async Tests**: Mostly passing (some Windows file locking edge cases)

---

## Key Components

### Authentication Flow

```
1. User logs in
   ↓
2. API validates credentials and returns JWT tokens
   - access_token (short-lived, 15 minutes)
   - refresh_token (long-lived)
   ↓
3. Frontend stores tokens in localStorage
   - access_token
   - refresh_token
   ↓
4. Frontend adds Authorization header to API requests
   - Authorization: Bearer <access_token>
   ↓
5. API validates token with get_current_user dependency
   ↓
6. If token expired, frontend uses refresh_token to get new access_token
```

### Agent System

The system uses 10+ agents, coordinated by the orchestrator:

- **ProjectManager**: Manages projects and metadata
- **SocraticCounselor**: Generates dialogue questions
- **CodeGenerator**: Generates code from specs
- **ConflictDetector**: Finds contradictions
- **ContextAnalyzer**: Analyzes project context
- **KnowledgeManager**: Manages knowledge base
- **UserLearningAgent**: Tracks user progress
- **MultiLLMAgent**: Routes between LLM models
- **And more...**

All agents inherit from the `Agent` base class and follow the same interface.

---

## Common Development Tasks

### Add a New Agent

1. Create file: `socratic_system/agents/your_agent.py`
2. Inherit from `Agent` base class
3. Implement `process()` and `process_async()` methods
4. Add to `socratic_system/agents/__init__.py`
5. Register in orchestrator

### Add API Endpoint

1. Create router in `socrates-api/src/socrates_api/routers/your_router.py`
2. Use `Depends(get_current_user)` for protected endpoints
3. Register router in `main.py`
4. Add tests in `tests/` directory

### Fix Database Issue

1. ChromaDB issues: Ensure `close()` is called before cleanup
2. SQLite issues: Check database locks
3. Migration issues: Update `schema_v2.sql` and migration runner

### Debug Authentication Issues

```python
# Check token validity
from socrates_api.auth import verify_access_token
payload = verify_access_token("your-token-here")
print(payload)  # Should show user_id in 'sub' field

# Check current user extraction
from socrates_api.auth import get_current_user
from fastapi.security import HTTPAuthorizationCredentials
creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="your-token")
user_id = await get_current_user(creds)
```

---

## Contributing

### Before Submitting PR

1. ✅ All tests pass: `pytest tests/ --ignore=tests/async/ -q`
2. ✅ Code formatted: `black socratic_system/` & `isort socratic_system/`
3. ✅ No linting errors: `ruff check socratic_system/`
4. ✅ Type checking passes: `mypy socratic_system/`
5. ✅ Docstrings added: All public functions documented
6. ✅ Tests added: New features have corresponding tests

### Commit Message Format

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
test: Add tests
refactor: Refactor code
perf: Performance improvement
```

### PR Description Template

```markdown
## Description
What does this PR do?

## Changes
- Specific change 1
- Specific change 2

## Tests
- Test 1 added
- Test 2 added

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No breaking changes
```

---

## Resources

- **Architecture**: See ARCHITECTURE.md
- **API Reference**: See API_REFERENCE.md
- **User Guide**: See USER_GUIDE.md
- **API Docs**: http://localhost:8000/docs (when running)

---

**Last Updated**: December 2025
**Version**: 7.0+
