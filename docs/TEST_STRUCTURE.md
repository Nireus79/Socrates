# Project Test Structure

## Overview
Tests are organized by type (unit, integration, e2e) rather than by phase. This document describes the test hierarchy.

## Backend Tests

### Unit Tests (`tests/unit/`)
- **database/**: Database operations, queries, persistence
- **models/**: Data model validation and types
- **orchestration/**: Orchestrator initialization and basic flows
- **routers/**: Individual API endpoint functionality
- **services/**: Business logic services
- **utils/**: Utility functions and helpers

### Integration Tests (`tests/integration/`)
- **api/**: Full API workflows and endpoint interactions
- **auth/**: Authentication and authorization flows
- **collaboration/**: Team collaboration features
- **database/**: Cross-module database operations
- **knowledge/**: Knowledge base integration
- **workflows/**: Multi-component workflows

### End-to-End Tests (`tests/e2e/`)
- Complete user journeys
- Full application workflows
- Real-world usage scenarios

### Backend-Specific Tests (`tests/backend/`)
- Tests isolated from main test suite
- Comprehensive system tests
- ID generator tests

### Phase Tests (Legacy) (`tests/phase3/`, `tests/phase5/`)
- Legacy phase-based tests
- For reference and validation of phase implementations

## Frontend Tests

### Unit Tests (`socrates-frontend/src/__tests__/unit/`)
- **stores/**: State management tests (auth, projects, collaboration, etc.)
- **services/**: Service logic tests (API clients, WebSocket, etc.)
- **api/**: API client tests
- **utils/**: Utility function tests

### Integration Tests (`socrates-frontend/src/__tests__/integration/`)
- Collaboration flows
- Knowledge workflows
- Invitation workflows

### End-to-End Tests (`socrates-frontend/src/__tests__/e2e/`)
- Complete application workflows
- User journey tests

## Scripts

### Verification Scripts (`scripts/verify/`)
- `verify_installation.py`: Verify Python environment and dependencies
- `verify_phase1_integrations.py`: Phase 1 library integrations
- `verify_phase2_agents.py`: Phase 2 agent functionality
- `verify_phase3_frameworks.py`: Phase 3 framework functionality
- `verify_phase4_cores.py`: Phase 4 core functionality
- `verify_phase5_interfaces.py`: Phase 5 interface functionality

### Development Scripts (`scripts/dev/`)
- `start-dev.py/sh`: Start development environment
- `generate_docs.py`: Generate project documentation
- `coverage_report.py`: Generate test coverage reports

### Database Scripts (`scripts/database/`)
- `backup_database.sh`: Backup project databases
- `restore_database.sh`: Restore from backup

## Test Naming Conventions

### Python Tests
- File pattern: `test_<feature>.py`
- Test function pattern: `def test_<specific_scenario>()`
- Example: `test_orchestrator_basic.py::test_orchestrator_initializes_with_api_key`

### TypeScript Tests
- File pattern: `<feature>.test.ts` or `<feature>.spec.ts`
- Test function pattern: `test('<specific scenario>', () => {})`
- Example: `authStore.test.ts::test('initializes with valid token')`

## Running Tests

### All Backend Tests
```bash
pytest tests/
```

### Specific Test Categories
```bash
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/e2e/               # End-to-end tests only
pytest tests/phase3/            # Legacy phase tests
```

### Specific Test File
```bash
pytest tests/unit/routers/test_auth.py
```

### With Coverage
```bash
python scripts/dev/coverage_report.py
```

### Frontend Tests
```bash
npm test                         # Run all tests
npm test -- --watch            # Watch mode
npm test -- --coverage         # With coverage
```

## Continuous Integration

All test categories are run in CI/CD:
1. Unit tests first (fastest feedback)
2. Integration tests (component interactions)
3. E2E tests (full workflows)
4. Coverage report generation

## Adding New Tests

1. **Unit Test**: Create in `tests/unit/<category>/test_<feature>.py`
2. **Integration Test**: Create in `tests/integration/<category>/test_<feature>.py`
3. **E2E Test**: Create in `tests/e2e/test_<journey>.py`
4. **Frontend Test**: Create in `socrates-frontend/src/__tests__/<type>/<feature>.test.ts`

Follow existing naming patterns and use descriptive test names.
