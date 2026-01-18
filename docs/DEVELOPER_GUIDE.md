# Developer Guide - Contributing to Socrates AI

Guide for developers who want to extend, modify, or contribute to Socrates AI.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Creating Custom Components](#creating-custom-components)
5. [Testing](#testing)
6. [Code Style](#code-style)
7. [Contributing](#contributing)

---

## Development Setup

### Clone Repository

```bash
git clone https://github.com/your-org/socrates.git
cd socrates
git checkout develop  # Use develop branch for new features
```

### Create Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
# Includes: pytest, black, ruff, mypy, sphinx
```

### Set Up Pre-Commit Hooks

```bash
pre-commit install
```

This runs linting and formatting checks before each commit.

---

## Project Structure

```
socrates/
├── socratic_system/           # Main package
│   ├── __init__.py
│   ├── agents/               # Agent implementations
│   │   ├── base.py          # Agent base class
│   │   ├── project_manager.py
│   │   ├── socratic_counselor.py
│   │   ├── code_generator.py
│   │   ├── context_analyzer.py
│   │   ├── conflict_detector.py
│   │   ├── system_monitor.py
│   │   ├── document_processor.py
│   │   ├── user_manager.py
│   │   ├── note_manager.py
│   │   └── knowledge_manager.py
│   ├── clients/              # External API clients
│   │   ├── __init__.py
│   │   └── claude_client.py  # Anthropic API wrapper
│   ├── config/              # Configuration files
│   │   ├── knowledge_base.json
│   │   └── __init__.py
│   ├── database/            # Persistence layer
│   │   ├── __init__.py
│   │   ├── project_db.py    # SQLite interface
│   │   └── vector_db.py     # ChromaDB interface
│   ├── events/              # Event system
│   │   ├── __init__.py
│   │   ├── event_emitter.py
│   │   └── event_types.py
│   ├── exceptions/          # Custom exceptions
│   │   ├── __init__.py
│   │   └── errors.py
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── user.py
│   │   ├── knowledge.py
│   │   ├── note.py
│   │   ├── conflict.py
│   │   └── monitoring.py
│   ├── orchestration/       # Agent orchestration
│   │   ├── __init__.py
│   │   └── orchestrator.py
│   ├── ui/                  # User interface
│   │   ├── __init__.py
│   │   ├── main_app.py      # CLI main loop
│   │   ├── command_handler.py
│   │   ├── context_display.py
│   │   ├── navigation.py
│   │   ├── nlu_handler.py   # NLU support
│   │   └── commands/        # Command implementations
│   │       ├── __init__.py
│   │       ├── base.py      # Command base class
│   │       ├── system_commands.py
│   │       ├── user_commands.py
│   │       ├── project_commands.py
│   │       ├── session_commands.py
│   │       ├── code_commands.py
│   │       └── ... (other commands)
│   ├── conflict_resolution/ # Conflict detection
│   │   ├── __init__.py
│   │   ├── base.py         # Checker base class
│   │   └── checkers/       # Pluggable checkers
│   └── utils/              # Utilities
│       ├── __init__.py
│       └── logger.py        # Logging system
├── tests/                   # Test suite
│   ├── conftest.py         # Pytest configuration
│   ├── unit/
│   ├── integration/
│   └── end_to_end/
├── docs/                    # Documentation
├── examples/                # Example scripts
├── Socrates.py             # Entry point
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── pyproject.toml          # Package configuration
├── setup.py                # Setup script
└── README.md               # Project README
```

---

## Development Workflow

### Create Feature Branch

```bash
git checkout -b feature/my-feature develop
```

Branch naming:
- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code improvements
- `docs/` - Documentation
- `test/` - Test improvements

### Write Code

```bash
# Make your changes
# Commit regularly
git add .
git commit -m "Description of changes"
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/unit/test_orchestrator.py

# Run with coverage
pytest --cov=socratic_system
```

### Format Code

```bash
# Auto-format with black
black socratic_system tests

# Lint with ruff
ruff check socratic_system tests

# Type check with mypy
mypy socratic_system
```

### Run Pre-Commit Checks

```bash
# These run automatically before commit
pre-commit run --all-files

# Or manually:
git add .
git commit -m "Your message"  # Runs pre-commit checks
```

### Create Pull Request

```bash
git push origin feature/my-feature

# Create PR on GitHub
# Title: Brief description
# Description: Detailed explanation of changes
#   - What problem does this solve?
#   - How does it work?
#   - What testing was done?
```

---

## Creating Custom Components

### Creating a Custom Agent

```python
# socratic_system/agents/my_agent.py

from socratic_system.agents.base import Agent
from typing import Dict, Any

class MyCustomAgent(Agent):
    """Description of what this agent does."""

    def __init__(self, orchestrator):
        super().__init__("MyCustomAgent", orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request synchronously."""
        action = request.get('action')

        if action == 'my_action':
            try:
                self.log(f"Processing {action}")
                result = self._process_my_action(request)
                self.emit_event('my_event', {'result': result})
                return {
                    'status': 'success',
                    'data': result
                }
            except Exception as e:
                self.log(f"Error: {e}", level='error')
                return {
                    'status': 'error',
                    'message': str(e)
                }

        return {
            'status': 'error',
            'message': f'Unknown action: {action}'
        }

    def _process_my_action(self, request) -> Any:
        """Helper method for action."""
        # Your implementation
        return {"processed": True}

    async def process_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Optional: async implementation."""
        # Implement async version
        return self.process(request)
```

### Register Agent

```python
# In orchestration/orchestrator.py

from socratic_system.agents.my_agent import MyCustomAgent

# In AgentOrchestrator.__init__()
self.agents['my_custom'] = MyCustomAgent(self)
```

### Using Custom Agent

```python
result = orchestrator.process_request('my_custom', {
    'action': 'my_action',
    'param1': 'value1'
})
```

### Creating a Custom Command

```python
# socratic_system/ui/commands/my_command.py

from socratic_system.ui.commands.base import BaseCommand
from typing import Dict, Any, List

class MyCommand(BaseCommand):
    """Description of command."""

    def __init__(self):
        super().__init__(
            name="mycommand",
            description="Does something special",
            usage="mycommand [args]"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command."""
        try:
            # Access context
            orchestrator = context['orchestrator']
            project = context.get('project')
            user = context['user']

            # Your logic here
            result = orchestrator.process_request('agent_name', {...})

            # Return success
            return self.success(
                message="Command completed successfully",
                data=result
            )

        except Exception as e:
            return self.error(str(e))
```

### Register Command

```python
# In ui/command_handler.py, register in command registry
'mycommand': MyCommand()
```

### Using Custom Command

```bash
/mycommand arg1 arg2
```

### Creating Custom Conflict Checker

```python
# socratic_system/conflict_resolution/checkers/my_checker.py

from socratic_system.conflict_resolution.base import ConflictChecker
from typing import Dict, Any

class MyConflictChecker(ConflictChecker):
    """Check for my specific type of conflict."""

    def _extract_values(self, insights: Dict[str, Any]) -> list:
        """Extract relevant values from new insights."""
        # Return list of values to check
        return [insights.get('my_field')]

    def _normalize_values(self, values: list) -> list:
        """Normalize values for comparison."""
        # Ensure consistent format
        return values

    def _get_existing_values(self, project) -> Any:
        """Get current values from project."""
        if hasattr(project, 'my_field'):
            return project.my_field
        return None

    def _find_conflict(self, new_value: Any, existing: Any, project, user) -> Dict:
        """Detect conflict between old and new values."""
        if existing and new_value != existing:
            return {
                'conflict': True,
                'old': existing,
                'new': new_value,
                'description': f'Conflict: {existing} vs {new_value}'
            }
        return {'conflict': False}
```

### Register Checker

```python
# In conflict_detector agent

from my_checker import MyConflictChecker

# In ConflictDetectorAgent.process()
checkers = [
    TechStackConflictChecker(),
    RequirementsConflictChecker(),
    MyConflictChecker()  # Add custom checker
]
```

---

## Testing

For comprehensive testing guidance, see the [Testing Guide](TESTING.md).

This section covers the basics. For detailed patterns, fixtures, and best practices, refer to the dedicated testing documentation.

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── unit/
│   ├── test_orchestrator.py
│   ├── test_agents.py
│   ├── test_database.py
│   └── ...
├── integration/
│   ├── test_agent_workflow.py
│   ├── test_dialogue_flow.py
│   └── ...
└── e2e/journeys/
    ├── test_complete_flow.py
    └── ...
```

### Writing Unit Tests

```python
# tests/unit/test_my_agent.py

import pytest
from socratic_system.agents.my_agent import MyCustomAgent

class MockOrchestrator:
    def __init__(self):
        self.events_emitted = []

    def emit_event(self, event_type, data):
        self.events_emitted.append((event_type, data))

@pytest.fixture
def mock_orchestrator():
    return MockOrchestrator()

@pytest.fixture
def agent(mock_orchestrator):
    return MyCustomAgent(mock_orchestrator)

def test_my_action(agent):
    result = agent.process({
        'action': 'my_action',
        'param': 'value'
    })

    assert result['status'] == 'success'
    assert result['data'] == {'processed': True}

def test_my_action_error(agent):
    result = agent.process({
        'action': 'my_action',
        'param': 'invalid'
    })

    assert result['status'] == 'error'

def test_unknown_action(agent):
    result = agent.process({'action': 'unknown'})
    assert result['status'] == 'error'
```

### Writing Integration Tests

```python
# tests/integration/test_workflow.py

@pytest.mark.asyncio
async def test_complete_project_workflow(orchestrator):
    # Create project
    result = orchestrator.process_request('project_manager', {
        'action': 'create_project',
        'project_name': 'Test Project',
        'owner': 'test_user'
    })
    project_id = result['project']['project_id']

    # Ask questions
    for i in range(3):
        q_result = orchestrator.process_request('socratic_counselor', {
            'action': 'generate_question',
            'project_id': project_id
        })
        assert 'question' in q_result

    # Generate code
    code_result = orchestrator.process_request('code_generator', {
        'action': 'generate_script',
        'project_id': project_id
    })
    assert 'code' in code_result
```

### Run Tests

```bash
# All tests
pytest

# Specific file
pytest tests/unit/test_orchestrator.py

# Specific test
pytest tests/unit/test_orchestrator.py::test_creation

# With coverage
pytest --cov=socratic_system --cov-report=html

# Verbose
pytest -v

# Stop on first failure
pytest -x
```

---

## Code Style

### Python Style Guide

Follow PEP 8 with Black formatter:

```python
# Good
def create_project(name: str, owner: str) -> ProjectContext:
    """Create a new project.

    Args:
        name: Project name
        owner: Project owner username

    Returns:
        ProjectContext instance
    """
    project = ProjectContext(
        name=name,
        owner=owner,
        created_at=datetime.now()
    )
    return project

# Bad
def create_project(name,owner):
    project = ProjectContext(name=name,owner=owner,created_at=datetime.now())
    return project
```

### Type Hints

Always use type hints:

```python
# Good
def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
    pass

# Bad
def process(self, request):
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def process_request(self, agent: str, request: Dict) -> Dict:
    """Process request through specified agent.

    Args:
        agent: Agent name to route to
        request: Request dictionary with action and parameters

    Returns:
        Result dictionary with status, data, and messages

    Raises:
        AgentError: If agent processing fails
        ValueError: If agent not found
    """
```

### Format Code

```bash
# Black for formatting
black socratic_system

# Ruff for linting
ruff check socratic_system --fix

# MyPy for type checking
mypy socratic_system

# Import sorting
isort socratic_system
```

---

## Contributing

### Code Review Checklist

- [ ] Follows PEP 8 and project style
- [ ] All functions have type hints
- [ ] Docstrings present and complete
- [ ] Tests written and passing
- [ ] No breaking changes documented
- [ ] Updated relevant documentation
- [ ] Commit messages are clear and descriptive

### PR Title Format

```
[TYPE] Brief description

Types:
- feat: New feature
- fix: Bug fix
- refactor: Code improvement
- docs: Documentation
- test: Test improvements
- perf: Performance improvement
```

### PR Description Template

```markdown
## Description
Detailed explanation of changes

## Problem Solved
What issue does this address?

## Solution
How does this solve the problem?

## Testing
How was this tested?

## Breaking Changes
Any breaking changes to the API?

## Related Issues
Fixes #123
Related to #456
```

### Commit Message Format

```
type: brief description

Longer explanation of the change and why it was made.

- Bullet point for each logical change
- Another bullet point

Fixes #issue_number
```

Example:
```
feat: add conflict detection for tech stack

Implement pluggable conflict checker system for technology stack
validation. Detects incompatible technology combinations before
proceeding with project.

- Add ConflictChecker base class
- Implement TechStackConflictChecker
- Register in ConflictDetectorAgent
- Add tests

Fixes #42
```

---

## Running the Full Development Cycle

```bash
# 1. Create branch
git checkout -b feature/my-feature develop

# 2. Make changes
# ... edit files ...

# 3. Run tests
pytest

# 4. Format code
black socratic_system
ruff check socratic_system --fix
mypy socratic_system

# 5. Commit
git add .
git commit -m "feat: description of changes"

# 6. Push
git push origin feature/my-feature

# 7. Create PR on GitHub
# ... describe changes, link issues ...

# 8. Review & Merge
# ... address feedback ...
# ... merge when approved ...
```

---

## Debugging Tips

### Use Debug Mode

```python
# Set logging level to DEBUG
config = ConfigBuilder("sk-ant-...") \
    .with_log_level("DEBUG") \
    .build()

orchestrator = AgentOrchestrator(config)
```

### Add Logging

```python
from socratic_system.utils.logger import get_logger

logger = get_logger('my_module')

logger.debug("Detailed debugging info")
logger.info("Important information")
logger.warning("Warning message")
logger.error("Error message")
```

### Use Debugger

```python
import pdb

def my_function():
    x = 1
    pdb.set_trace()  # Debugger will stop here
    y = x + 1
```

### Print Debugging

```python
# Avoid in production, use logging instead
print(f"DEBUG: value = {value}")  # OK for development
logger.debug(f"value = {value}")  # Better
```

---

## Resources

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation
- [Code on GitHub](https://github.com/Nireus79/Socrates)
- [Issues & Discussions](https://github.com/Nireus79/Socrates/issues)

---

**Last Updated**: January 2026
**Version**: 1.3.0
