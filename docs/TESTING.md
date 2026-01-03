# Testing Guide - Socrates AI

Comprehensive guide for writing tests that maintain data isolation and prevent production data loss.

## Table of Contents

1. [Overview](#overview)
2. [Test Isolation Principles](#test-isolation-principles)
3. [Database Testing](#database-testing)
4. [Vector Database Testing](#vector-database-testing)
5. [Configuration Testing](#configuration-testing)
6. [Environment Variables](#environment-variables)
7. [Common Patterns](#common-patterns)
8. [Anti-patterns to Avoid](#anti-patterns-to-avoid)
9. [Running Tests](#running-tests)

---

## Overview

Socrates AI tests are organized to maintain strict isolation between test and production environments. This prevents data loss and ensures tests don't affect your development work.

Test Structure:
```
tests/
├── conftest.py              # Shared fixtures for all tests
├── unit/                    # Unit tests
├── integration/             # Integration tests
└── e2e/journeys/           # End-to-end tests

socrates-api/tests/
├── conftest.py             # API-specific fixtures
├── unit/                   # API unit tests
└── integration/            # API integration tests
```

---

## Test Isolation Principles

### Core Rules

1. **Never touch production directories** (`~/.socrates/`)
   - Not in setup
   - Not in teardown
   - Not during tests

2. **Use pytest fixtures for temporary resources**
   - Fixtures handle cleanup automatically
   - No manual cleanup needed
   - Perfectly isolated from other tests

3. **Never modify global environment variables**
   - Use `monkeypatch` fixture
   - Changes automatically revert
   - No pollution between tests

4. **Each test gets its own database**
   - No shared state
   - Parallel test execution safe
   - No race conditions

---

## Database Testing

### Using Test Database Fixtures

The `test_db` fixture provides an isolated database for each test:

```python
# Use the test_db fixture
def test_save_project(test_db):
    """Test project saving with isolated database."""
    from socratic_system.models import ProjectContext

    project = ProjectContext(
        project_id="test-123",
        name="Test Project",
        owner="testuser",
        # ... other fields
    )

    # Save to test database (not production!)
    test_db.save_project(project)

    # Verify
    loaded = test_db.load_project("test-123")
    assert loaded.name == "Test Project"
    # Cleanup happens automatically
```

### For Ultra-Fast Tests

Use the in-memory database for tests that don't need persistence:

```python
def test_user_validation(test_db_inmemory):
    """Fast test using in-memory database."""
    from socratic_system.models import User

    user = User(
        username="testuser",
        email="test@example.com",
        passcode_hash="hash123"
    )

    # No disk I/O - very fast
    test_db_inmemory.save_user(user)
    assert test_db_inmemory.load_user("testuser") is not None
```

### Database Fixture Reference

```python
@pytest.fixture
def test_db(tmp_path):
    """
    Isolated test database using temporary directory.

    Each test gets its own database file.
    Automatically cleaned up after test.
    Safe for parallel test execution.
    """
    from socratic_system.database import ProjectDatabase
    test_db_path = tmp_path / "test_projects.db"
    db = ProjectDatabase(str(test_db_path))
    yield db
    # Cleanup automatic


@pytest.fixture
def test_db_inmemory():
    """
    Ultra-fast in-memory database.

    No disk I/O.
    Perfect for unit tests that don't need persistence.
    Cannot test file I/O behavior.
    """
    from socratic_system.database import ProjectDatabase
    db = ProjectDatabase(":memory:")
    return db
```

---

## Vector Database Testing

### Using Test Vector Database

```python
def test_vector_search(test_vector_db):
    """Test vector database operations."""
    # Add document
    doc_id = test_vector_db.add_document(
        "Python REST API design best practices",
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5]
    )

    # Search
    results = test_vector_db.search(
        query_embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        top_k=5
    )

    assert len(results) > 0
    # Cleanup automatic
```

### Vector Database Fixture Reference

```python
@pytest.fixture
def test_vector_db(tmp_path):
    """
    Isolated vector database in temporary directory.

    Each test gets its own vector database.
    No interference with production data in ~/.socrates/vector_db/
    Automatically cleaned up.
    """
    from socratic_system.database.vector_db import VectorDatabase

    test_vector_db_path = tmp_path / "test_vector_db"
    vector_db = VectorDatabase(str(test_vector_db_path))

    yield vector_db
    # Cleanup automatic
```

---

## Configuration Testing

### Testing with Isolated Configuration

```python
def test_config_from_env(test_socrates_config):
    """Test configuration with isolated temp directory."""
    # test_socrates_config has:
    # - api_key: "sk-test-key-12345"
    # - data_dir: tmp_path / "socrates"
    # - projects_db_path: tmp_path / "socrates" / "projects.db"
    # - vector_db_path: tmp_path / "socrates" / "vector_db"

    assert test_socrates_config.api_key == "sk-test-key-12345"
    assert "socrates" in str(test_socrates_config.data_dir)
    assert "~" not in str(test_socrates_config.data_dir)  # Not home directory
```

### Complete Isolated Configuration

For tests needing explicit control over all paths:

```python
def test_orchestrator_initialization(isolated_socrates_config):
    """Test orchestrator with fully isolated config."""
    from socratic_system.orchestration import AgentOrchestrator

    orchestrator = AgentOrchestrator(isolated_socrates_config)

    # Verify databases are in temp directory, not production
    assert "socrates" in str(orchestrator.config.projects_db_path)
    assert "~" not in str(orchestrator.config.projects_db_path)
    assert "~" not in str(orchestrator.config.vector_db_path)

    # Safe to run - no production impact
```

### Configuration Fixture Reference

```python
@pytest.fixture
def test_socrates_config(tmp_path):
    """
    Isolated test configuration.

    Auto-generates:
    - projects.db in temp directory
    - vector_db in temp directory
    - Never touches ~/.socrates/
    """
    from socratic_system.config import SocratesConfig

    return SocratesConfig(
        api_key="sk-test-key-12345",
        data_dir=tmp_path / "socrates",
    )


@pytest.fixture
def isolated_socrates_config(tmp_path):
    """
    Explicit test configuration with all paths specified.

    Use when you need:
    - Custom database locations
    - Multiple databases in same test
    - Direct control over paths
    """
    from socratic_system.config import SocratesConfig

    test_data_dir = tmp_path / "socrates"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    return SocratesConfig(
        api_key="sk-test-key-12345",
        data_dir=test_data_dir,
        projects_db_path=test_data_dir / "projects.db",
        vector_db_path=test_data_dir / "vector_db",
    )
```

---

## Environment Variables

### Protection Against Variable Leakage

The `protect_production_environment` fixture (autouse) prevents test environment variables from persisting:

```python
def test_with_custom_env(monkeypatch):
    """
    Using monkeypatch ensures env vars revert after test.

    This test runs with SOCRATES_DATA_DIR set, but it reverts
    automatically when the test ends.
    """
    monkeypatch.setenv("SOCRATES_DATA_DIR", "/tmp/test_socrates")

    # Test code here
    # SOCRATES_DATA_DIR is set during test

    # After test: SOCRATES_DATA_DIR automatically reverts
```

### Anti-pattern: Don't Do This

```python
# BAD - Environment variable persists between tests
os.environ["SOCRATES_DATA_DIR"] = "/tmp/test_socrates"
# This affects subsequent tests and production code!

# GOOD - Use monkeypatch, automatically reverts
def test_something(monkeypatch):
    monkeypatch.setenv("SOCRATES_DATA_DIR", "/tmp/test_socrates")
    # Automatically reverts after test
```

---

## Common Patterns

### Pattern 1: Test Database Operations

```python
def test_project_crud_operations(test_db):
    """Test Create, Read, Update, Delete operations."""
    from socratic_system.models import ProjectContext
    import datetime

    # Create
    project = ProjectContext(
        project_id="test-proj-1",
        name="Test Project",
        owner="testuser",
        goals="Test goal",
        requirements=["Req1"],
        tech_stack=["Python"],
        constraints=[],
        team_structure="individual",
        language_preferences="python",
        deployment_target="cloud",
        code_style="documented",
        phase="discovery",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )

    test_db.save_project(project)

    # Read
    loaded = test_db.load_project("test-proj-1")
    assert loaded.name == "Test Project"
    assert loaded.owner == "testuser"

    # Update
    loaded.phase = "implementation"
    test_db.save_project(loaded)

    updated = test_db.load_project("test-proj-1")
    assert updated.phase == "implementation"

    # Delete
    assert test_db.delete_project("test-proj-1")
    assert test_db.load_project("test-proj-1") is None
```

### Pattern 2: Test with Configuration

```python
def test_orchestrator_with_config(test_socrates_config):
    """Test orchestrator initialization with test config."""
    from socratic_system.orchestration import AgentOrchestrator
    from unittest.mock import patch

    # Mock external dependencies
    with patch("socratic_system.orchestration.orchestrator.ClaudeClient"):
        with patch("socratic_system.orchestration.orchestrator.VectorDatabase"):
            orchestrator = AgentOrchestrator(test_socrates_config)

            # Verify
            assert orchestrator.config == test_socrates_config
            assert "~" not in str(orchestrator.config.data_dir)
```

### Pattern 3: Test Multiple Databases

```python
def test_data_migration(test_db, test_vector_db):
    """Test operations involving both databases."""
    from socratic_system.models import ProjectContext, KnowledgeEntry
    import datetime

    # Create data in relational database
    project = ProjectContext(
        project_id="migrate-test",
        name="Migration Test",
        owner="testuser",
        goals="Migrate knowledge",
        requirements=[],
        tech_stack=[],
        constraints=[],
        team_structure="individual",
        language_preferences="python",
        deployment_target="cloud",
        code_style="documented",
        phase="analysis",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )
    test_db.save_project(project)

    # Create knowledge in vector database
    test_vector_db.add_document(
        "Knowledge for migration test",
        embedding=[0.1] * 384  # Typical embedding size
    )

    # Test interaction between databases
    loaded_project = test_db.load_project("migrate-test")
    assert loaded_project is not None

    # Both databases isolated and clean
```

### Pattern 4: Test with Mocks

```python
def test_api_endpoint(test_db, mock_orchestrator):
    """Test API endpoint with mocked orchestrator."""
    from socrates_api.routers.projects import get_projects

    # Mock returns test data
    mock_orchestrator.database.get_projects.return_value = []

    # Test
    projects = get_projects(orchestrator=mock_orchestrator)

    # Verify
    assert projects == []
    mock_orchestrator.database.get_projects.assert_called_once()
```

---

## Anti-patterns to Avoid

### Anti-pattern 1: Modifying Production Paths

```python
# BAD - Touches production database
from pathlib import Path

db_path = Path.home() / ".socrates" / "projects.db"
# Never do this in tests!

# GOOD - Use fixture
def test_something(test_db):
    # test_db is in temporary directory
    pass
```

### Anti-pattern 2: Global Environment Variables

```python
# BAD - Persists between tests
import os
os.environ["SOCRATES_DATA_DIR"] = "/tmp/test_data"
# Other tests are now affected!

# GOOD - Use monkeypatch
def test_something(monkeypatch):
    monkeypatch.setenv("SOCRATES_DATA_DIR", "/tmp/test_data")
    # Automatically reverts after test
```

### Anti-pattern 3: Manual Cleanup

```python
# BAD - Manual cleanup is error-prone
import tempfile
import shutil

temp_dir = tempfile.mkdtemp()
# ... test code ...
shutil.rmtree(temp_dir)  # Easy to forget!

# GOOD - Fixture handles cleanup
def test_something(tmp_path):
    temp_dir = tmp_path / "test_data"
    # ... test code ...
    # Automatically cleaned up
```

### Anti-pattern 4: Deleting Production Data

```python
# BAD - This kills user data!
db_path = Path.home() / ".socrates" / "projects.db"
if db_path.exists():
    db_path.unlink()  # Never ever do this in tests!

# GOOD - Only touch test files
def cleanup_test_database():
    """Never modify production database."""
    yield
    # No production cleanup
```

### Anti-pattern 5: Shared Test State

```python
# BAD - Tests affect each other
class TestProjects:
    @classmethod
    def setup_class(cls):
        cls.shared_db = ProjectDatabase(":memory:")

    def test_one(self):
        self.shared_db.save_project(project1)

    def test_two(self):
        # test_one's data is still here!
        projects = self.shared_db.get_all_projects()  # Includes test_one's data

# GOOD - Each test gets isolated database
def test_one(test_db):
    test_db.save_project(project1)

def test_two(test_db):
    # Fresh, empty database
    projects = test_db.get_all_projects()  # Empty
```

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/unit/test_config.py
```

### Run Specific Test

```bash
pytest tests/unit/test_config.py::test_config_initialization
```

### Run with Coverage

```bash
pytest --cov=socratic_system --cov=socrates_api --cov-report=html
```

### Run Only Fast Tests

```bash
pytest -m "not slow"
```

### Run Tests in Parallel

```bash
pytest -n auto
```

### Run API Tests Only

```bash
pytest socrates-api/tests/
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Print Statements

```bash
pytest -s
```

---

## Best Practices Summary

1. Always use pytest fixtures for temporary resources
2. Use `monkeypatch` for environment variables
3. Use `tmp_path` for temporary directories
4. Never touch `~/.socrates/` in tests
5. Test in isolation - each test independent
6. Clean up automatically - don't do manual cleanup
7. Use provided fixtures: `test_db`, `test_vector_db`, `test_socrates_config`
8. Run tests frequently during development
9. Keep tests fast - use in-memory databases where possible
10. Document complex test scenarios

---

## Troubleshooting

### Test Fails with "Permission Denied"

Tests are trying to modify production directories. Use the provided fixtures instead.

```python
# BAD
test_db_path = Path.home() / ".socrates" / "test.db"

# GOOD
def test_something(test_db):
    # Temporary directory handled
```

### Test Leaves Files Behind

Manual cleanup didn't run. Use fixture cleanup instead.

```python
# BAD
temp_dir = tempfile.mkdtemp()
# ... test ...
# Forgot to clean up!

# GOOD
def test_something(tmp_path):
    # Auto-cleaned after test
```

### Tests Interfere with Each Other

Shared state between tests. Use isolated fixtures.

```python
# BAD
global_db = ProjectDatabase(":memory:")

def test_one():
    global_db.save_project(...)  # Affects test_two

# GOOD
def test_one(test_db):
    test_db.save_project(...)  # Isolated

def test_two(test_db):
    test_db.save_project(...)  # Different database
```

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Python unittest mock](https://docs.python.org/3/library/unittest.mock.html)
- [Test Isolation Best Practices](https://testingjavas.com/test-isolation/)
