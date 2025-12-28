# Socrates Testing Guide

Comprehensive guide for running, writing, and maintaining tests in the Socrates project.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Organization](#test-organization)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Coverage](#test-coverage)
6. [CI/CD Integration](#cicd-integration)
7. [Best Practices](#best-practices)

---

## Quick Start

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov pytest-xdist pytest-mock
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=socrates_api --cov=socratic_system --cov-report=html

# Run in parallel (faster)
pytest -n auto
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/

# Specific test file
pytest tests/unit/routers/test_auth.py

# Specific test class
pytest tests/unit/routers/test_auth.py::TestAuthEndpoints

# Specific test function
pytest tests/unit/routers/test_auth.py::TestAuthEndpoints::test_login_success
```

### Run with Markers

```bash
# Run only fast tests (skip slow)
pytest -m "not slow"

# Run only slow tests
pytest -m slow

# Run only API tests
pytest -m api

# Combine markers
pytest -m "unit and not slow"
```

---

## Test Organization

### Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── pytest.ini                     # Pytest configuration
├── README.md                      # This file
│
├── unit/                          # Unit tests (fast, isolated)
│   ├── conftest.py               # Unit test fixtures
│   ├── models/
│   │   ├── test_user.py
│   │   ├── test_project.py
│   │   ├── test_knowledge.py
│   │   └── test_llm_config.py
│   ├── routers/
│   │   ├── test_auth.py
│   │   ├── test_projects.py
│   │   ├── test_chat_sessions.py
│   │   ├── test_collaboration.py
│   │   ├── test_knowledge.py
│   │   ├── test_analytics.py
│   │   ├── test_code_generation.py
│   │   ├── test_nlu.py
│   │   ├── test_presession.py
│   │   └── ... (one per router)
│   ├── agents/
│   │   ├── test_socratic_counselor.py
│   │   ├── test_code_generator.py
│   │   ├── test_project_manager.py
│   │   └── ... (one per agent)
│   ├── database/
│   │   ├── test_project_db.py
│   │   ├── test_async_db.py
│   │   ├── test_vector_db.py
│   │   └── test_migrations.py
│   ├── middleware/
│   │   ├── test_rate_limit.py
│   │   ├── test_security_headers.py
│   │   ├── test_metrics.py
│   │   └── test_auth.py
│   ├── services/
│   │   ├── test_orchestrator.py
│   │   ├── test_knowledge_base.py
│   │   └── test_document_understanding.py
│   ├── caching/
│   │   ├── test_redis_cache.py
│   │   └── test_embedding_cache.py
│   └── utils/
│       ├── test_validators.py
│       └── test_parsers.py
│
├── integration/                   # Integration tests (slower, test interactions)
│   ├── conftest.py               # Integration test fixtures
│   ├── test_auth_workflows.py
│   ├── test_project_workflows.py
│   ├── test_chat_workflows.py
│   ├── test_collaboration_workflows.py
│   ├── test_knowledge_workflows.py
│   ├── test_github_import_workflows.py
│   ├── test_websocket_workflows.py
│   └── test_subscription_enforcement.py
│
├── e2e/                           # End-to-end tests (full user workflows)
│   ├── conftest.py               # E2E test fixtures
│   ├── test_user_journey_free.py
│   ├── test_user_journey_pro.py
│   ├── test_full_project_lifecycle.py
│   └── test_collaboration_session.py
│
└── performance/                   # Performance and load tests
    ├── test_load_testing.py
    ├── test_database_performance.py
    └── test_cache_performance.py
```

### Test Naming Conventions

- **Test files:** `test_<module>.py` (e.g., `test_auth.py`)
- **Test classes:** `Test<Feature>` (e.g., `TestAuthEndpoints`)
- **Test functions:** `test_<behavior>` (e.g., `test_login_success`)
- **Fixtures:** Descriptive names (e.g., `authenticated_client`, `sample_project`)

# From socrates-cli
pip install -e socrates-cli/[dev]

# From socrates-api
pip install -e socrates-api/[dev]
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_config.py
```

### Run Specific Test Class

```bash
pytest tests/test_config.py::TestSocratesConfig
```

### Run Specific Test

```bash
pytest tests/test_config.py::TestSocratesConfig::test_config_creation_with_api_key
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run slow tests
pytest -m slow

# Run tests excluding slow tests
pytest -m "not slow"

# Run tests requiring API key
pytest -m requires_api
```

### Run Tests with Coverage

```bash
pytest --cov=socratic_system --cov=socrates_cli --cov=socrates_api --cov-report=html
```

The HTML coverage report will be in `htmlcov/index.html`

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers
pytest -n 4
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Output Capture Disabled

```bash
pytest -s
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

Fast tests that don't require external dependencies or complex setup.

Examples:
- Configuration creation and validation
- Event emitter functionality
- Exception creation and hierarchy
- Data model validation

Run with:
```bash
pytest -m unit
```

### Integration Tests (`@pytest.mark.integration`)

Tests that verify component interactions, using mocked dependencies.

Examples:
- Orchestrator with mocked Claude client
- Database operations
- Event forwarding
- Request processing

Run with:
```bash
pytest -m integration
```

### API Tests

Tests for CLI and REST API endpoints.

Examples:
- CLI command invocation
- API endpoint response validation
- Error handling
- Request/response formats

Run with:
```bash
pytest socrates-cli/tests/ socrates-api/tests/
```

## Test Fixtures

Pytest fixtures are defined in `conftest.py` and provide reusable test data:

### Configuration Fixtures

- `mock_api_key` - Valid API key string
- `test_config` - Pre-configured SocratesConfig instance
- `config_builder` - ConfigBuilder for fluent config creation
- `temp_data_dir` - Temporary directory for test data

### Component Fixtures

- `mock_event_emitter` - Initialized EventEmitter
- `mock_anthropic_client` - Mocked Anthropic API client
- `sample_user` - Sample User model
- `sample_project` - Sample ProjectContext model
- `sample_knowledge_entry` - Sample KnowledgeEntry
- `sample_token_usage` - Sample TokenUsage

### Parametrized Fixtures

- `log_levels` - All log level options (DEBUG, INFO, WARNING, ERROR)
- `programming_languages` - Languages (python, javascript, typescript, go, rust)
- `difficulty_levels` - Levels (beginner, intermediate, advanced)

Use in tests:

```python
def test_with_fixture(test_config):
    assert test_config.api_key == "sk-ant-test-key-12345"

def test_with_parametrized(log_levels):
    config = SocratesConfig(api_key="test", log_level=log_levels)
    assert config.log_level == log_levels
```

## Test Examples

### Unit Test Example

```python
@pytest.mark.unit
def test_config_creation(mock_api_key):
    """Test creating config with API key"""
    config = SocratesConfig(api_key=mock_api_key)

    assert config.api_key == mock_api_key
    assert config.log_level == "INFO"
```

### Integration Test Example

```python
@pytest.mark.integration
def test_orchestrator_with_config(test_config):
    """Test orchestrator initialization"""
    with patch('socratic_system.clients.anthropic.Anthropic'):
        orchestrator = AgentOrchestrator(test_config)

        assert orchestrator.config == test_config
        assert orchestrator.event_emitter is not None
```

### CLI Test Example

```python
@pytest.mark.unit
def test_cli_help(cli_runner):
    """Test CLI help output"""
    result = cli_runner.invoke(main, ['--help'])

    assert result.exit_code == 0
    assert 'Socrates AI' in result.output
```

### API Test Example

```python
@pytest.mark.unit
def test_api_health_check(client):
    """Test API health check"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

## Mocking Guidelines

### Mocking External APIs

```python
with patch('socratic_system.clients.anthropic.Anthropic') as mock_client:
    orchestrator = AgentOrchestrator(config)
    # Test without calling actual API
```

### Mocking Methods

```python
mock_obj = Mock()
mock_obj.method.return_value = "expected_value"

# Use mock_obj.method()
```

### Mocking with Side Effects

```python
mock = Mock(side_effect=ValueError("Test error"))

with pytest.raises(ValueError):
    orchestrator.process_request(...)
```

## Coverage Goals

Target coverage levels:

| Component | Target | Current |
|-----------|--------|---------|
| socratic_system | 85% | TBD |
| socrates-cli | 80% | TBD |
| socrates-api | 75% | TBD |
| Overall | 80% | TBD |

Run coverage report:
```bash
pytest --cov --cov-report=html
```

## Continuous Integration

Tests are automatically run on:

1. **Pre-commit**: Local pre-commit hooks
2. **Pull Requests**: GitHub Actions CI/CD
3. **Main Branch**: Automated testing on push

## Writing New Tests

### Test File Naming

- Unit/integration tests: `test_<component>.py`
- Feature tests: `test_<feature>_integration.py`
- End-to-end tests: `test_e2e_<workflow>.py`

### Test Function Naming

```python
def test_<component>_<action>_<expected_result>():
    """Clear description of what is being tested"""
    pass
```

Examples:
- `test_config_creation_with_api_key`
- `test_orchestrator_emits_events`
- `test_cli_project_create_success`

### Test Structure (Arrange-Act-Assert)

```python
@pytest.mark.unit
def test_feature():
    # Arrange: Set up test data
    config = SocratesConfig(api_key="test")

    # Act: Perform the operation
    result = validate_config(config)

    # Assert: Verify the result
    assert result is True
```

### Using Fixtures

```python
@pytest.mark.unit
def test_with_fixture(test_config, sample_project):
    """Test using fixtures"""
    assert test_config.api_key is not None
    assert sample_project.owner == "testuser"
```

### Parametrized Tests

```python
@pytest.mark.parametrize("api_key,expected", [
    ("sk-ant-valid", True),
    ("invalid", False),
    ("", False),
])
def test_api_key_validation(api_key, expected):
    assert validate_api_key(api_key) == expected
```

## Debugging Tests

### Run with Print Statements

```bash
pytest -s tests/test_config.py::TestSocratesConfig::test_config_creation
```

### Run with Debugger

```bash
pytest --pdb tests/test_config.py
```

### Run Single Test in Isolation

```bash
pytest tests/test_config.py::TestSocratesConfig::test_config_creation -v
```

### Check Test Collection

```bash
pytest --collect-only tests/
```

## Troubleshooting

### Import Errors

Ensure `PYTHONPATH` includes the source directories:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/socrates-cli/src:$(pwd)/socrates-api/src"
pytest
```

### Missing Dependencies

Install all test dependencies:

```bash
pip install -e ".[dev]" -e socrates-cli/[dev] -e socrates-api/[dev]
```

### Fixture Not Found

Ensure `conftest.py` is in the correct directory:
- Main tests: `tests/conftest.py` ✓
- CLI tests: `socrates-cli/tests/conftest.py` (optional, uses main conftest)
- API tests: `socrates-api/tests/conftest.py` (optional, uses main conftest)

### Port Already in Use

Some API tests may use local ports. Clear them:

```bash
# On Linux/macOS
lsof -ti:8000 | xargs kill -9

# On Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Test Metrics

Current test suite statistics:

- **Total Tests**: 150+
- **Unit Tests**: 120+
- **Integration Tests**: 20+
- **Lines of Test Code**: 3000+
- **Fixtures**: 15+
- **Parametrized Tests**: 10+

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure tests pass: `pytest`
3. Check coverage: `pytest --cov`
4. Run specific tests: `pytest tests/test_<feature>.py -v`
5. Document tests in docstrings

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)

## Support

For test-related questions:
- Check test examples in `tests/`
- Review pytest documentation
- Open GitHub issue: https://github.com/Nireus79/Socrates/issues
