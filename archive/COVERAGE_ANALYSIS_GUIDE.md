# Code Coverage Analysis and Measurement Guide

**Date**: December 23, 2025
**Purpose**: Guide for measuring, analyzing, and improving code coverage to 80%+ overall and 95%+ for auth modules

---

## Coverage Measurement Instructions

### Backend Coverage Analysis (Python/Pytest)

#### Step 1: Install Coverage Tools
```bash
pip install pytest-cov coverage
```

#### Step 2: Run Tests with Coverage Report
```bash
# Generate HTML coverage report
pytest socratic_system socrates_cli socrates_api \
    --cov=socratic_system \
    --cov=socrates_cli \
    --cov=socrates_api \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=json

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

#### Step 3: Analyze Missing Lines
```bash
# Get detailed missing lines report
pytest --cov=socratic_system --cov-report=term-missing:skip-covered \
    socratic_system tests/ --cov-fail-under=80
```

#### Step 4: Focus on High-Value Code
Priority order for coverage:
1. **Auth modules** (95%+ target)
   - socrates_api/routers/auth.py
   - Authentication utilities and middleware

2. **Database operations** (90%+ target)
   - socratic_system/database/project_db_v2.py
   - socratic_system/database/vector_db.py

3. **API endpoints** (85%+ target)
   - socrates_api/routers/*.py
   - All REST endpoints

4. **Core business logic** (80%+ target)
   - socratic_system/orchestration/orchestrator.py
   - socratic_system/agents/*.py

### Frontend Coverage Analysis (TypeScript/Vitest)

#### Step 1: Generate Frontend Coverage
```bash
cd socrates-frontend
npm run test:coverage
```

#### Step 2: View Coverage Report
```bash
# Report will be generated in coverage/ directory
open coverage/index.html  # macOS
xdg-open coverage/index.html  # Linux
start coverage/index.html  # Windows
```

#### Step 3: Check Coverage by File
```bash
# View coverage summary
npm run test:coverage -- --reporter=text-summary

# Watch specific file coverage
npm run test:watch -- src/stores/authStore.ts
```

---

## Coverage Targets by Module

### Authentication Module (Target: 95%)

**Critical Paths**:
- Login flow with validation ✅
- Token generation and signing ✅
- Token validation and verification ✅
- Token refresh mechanism ✅
- Logout and session clearing ✅
- Password hashing and verification ✅
- Error handling and messages ✅
- Concurrent login handling ✅
- Token expiration detection ✅
- Unauthorized request rejection ✅

**Files to Achieve 95%**:
1. `socrates_api/routers/auth.py` - Auth endpoint handlers
2. `socrates_api/auth.py` (if exists) - Auth utilities
3. Auth middleware - Request validation

**Test Coverage Stats**:
- Lines: 95%+ (measure with: `pytest --cov --cov-report=json`)
- Branches: 90%+ (both login success and failure paths)
- Functions: 100% (all auth functions tested)

### API Endpoints (Target: 85%)

**Routes to Ensure**:
- GET /projects - List projects
- POST /projects - Create project
- GET /projects/{id} - Get project
- PUT /projects/{id} - Update project
- DELETE /projects/{id} - Delete project
- GET /auth/login - (POST method)
- POST /auth/register
- GET /github/import - (POST method)
- GET /knowledge/documents
- POST /knowledge/import/*
- GET /llm/config
- POST /analysis/validate

**Test Count Target**:
- 100+ endpoint tests per router
- Error cases (400, 401, 403, 404, 500)
- Valid input scenarios
- Invalid input validation

### Database Operations (Target: 90%)

**Coverage Areas**:
- User table CRUD operations
- Project table CRUD operations
- Document storage and retrieval
- Transaction handling
- Error recovery
- Connection pooling
- Query optimization

**Test Scenarios**:
- Create, read, update, delete all tables
- Transaction rollback on error
- Constraint enforcement
- Data validation

### Core Business Logic (Target: 80%)

**Coverage Areas**:
- Code analysis and maturity scoring
- Knowledge base operations
- LLM integration
- GitHub sync operations
- Error handling and logging
- Performance optimization paths

---

## How to Identify Coverage Gaps

### Method 1: HTML Report Analysis
```bash
# Generate report
pytest --cov=socratic_system socratic_system/ --cov-report=html

# Open report
open htmlcov/index.html

# Look for:
# - Red lines (not covered)
# - Orange branches (partially covered)
# - File percentages < target
```

### Method 2: Terminal Output
```bash
pytest --cov=socratic_system --cov-report=term-missing:skip-covered

# Output shows:
# - Percentage for each file
# - Line numbers not covered
# Example:
# auth.py       85%    45, 46, 112-120
#               ^^^    ^^^^^^^^^^^^
#           Coverage   Missing lines
```

### Method 3: JSON Report
```bash
pytest --cov=socratic_system --cov-report=json

# Analyze JSON with Python:
import json
with open('.coverage.json') as f:
    data = json.load(f)
    for file, coverage in data['files'].items():
        if coverage['summary']['percent_covered'] < 80:
            print(f"{file}: {coverage['summary']['percent_covered']}%")
```

### Method 4: Branch Coverage
```bash
# Show branch coverage (if/else paths)
pytest --cov=socratic_system --cov-branch \
    --cov-report=html:branch_coverage

# Key insight: Achieving 80% line coverage != 80% branch coverage
# Need to test both paths of conditionals
```

---

## Coverage Gap Fixing Strategy

### Priority 1: Auth Module to 95%

**Current Test Coverage**:
- authStore.comprehensive.test.ts: 40+ tests
- authStore.edge-cases.test.ts: 50+ tests
- test_auth_scenarios.py: 40+ tests
- test_auth_95_percent_coverage.py: 50+ tests
- **Total**: 180+ auth tests

**Gaps to Fill**:
```bash
# Find uncovered auth code
pytest socrates_api/routers/auth.py --cov=socrates_api.routers.auth \
    --cov-report=term-missing

# Likely gaps:
# - Edge cases in token validation
# - Error path handling
# - Concurrent request handling
# - Special character handling
```

**How to Add Tests**:
1. Run coverage report to find missing lines
2. Add test for each missing code path
3. Verify both success and failure cases
4. Re-run coverage until 95% achieved

### Priority 2: API Endpoints to 85%

**Current Test Coverage**:
- test_routers_comprehensive.py: 150+ tests
- test_e2e_workflows.py: 19 tests
- test_all_endpoints.py: 100+ tests
- **Total**: 270+ endpoint tests

**Gap Identification**:
```bash
# Test all routers
pytest socrates_api/routers/ --cov=socrates_api.routers \
    --cov-report=term-missing

# Check each router:
# - projects.py
# - github.py
# - knowledge.py
# - llm.py
# - analysis.py
# - collaboration.py
# - analytics.py
```

### Priority 3: Overall to 80%

**Measurement**:
```bash
# Full coverage report
pytest --cov=socratic_system --cov=socrates_cli --cov=socrates_api \
    --cov-report=html --cov-report=term

# Look for:
# - Files < 80%
# - Complex functions (low coverage likely)
# - New code paths (often uncovered)
```

**Strategy**:
1. Identify files below 80%
2. Prioritize by criticality and current coverage
3. Add targeted tests
4. Measure iteratively

---

## Common Coverage Issues and Solutions

### Issue 1: Exception Handling Not Covered
```python
# Example: Missing exception test
def risky_operation():
    try:
        database.query()  # Line: covered
    except Exception as e:  # Line: NOT covered
        logger.error(e)      # Line: NOT covered
        raise

# Solution: Add test that triggers exception
def test_risky_operation_handles_exception():
    with patch('database.query', side_effect=Exception("DB error")):
        with pytest.raises(Exception):
            risky_operation()
```

### Issue 2: Conditional Branches Not Covered
```python
# Example: Only testing happy path
def validate_input(data):
    if not data:          # Branch: NOT covered
        raise ValueError()
    return process(data)  # Branch: covered

# Solution: Test both branches
def test_validate_input_empty():
    with pytest.raises(ValueError):
        validate_input(None)

def test_validate_input_valid():
    result = validate_input({'key': 'value'})
    assert result is not None
```

### Issue 3: Error Handlers Not Triggered
```python
# Example: Error handler never called
@app.exception_handler(CustomError)
def handle_custom_error(request, exc):  # NOT covered
    return JSONResponse(status_code=400)

# Solution: Test the error scenario
def test_custom_error_handling():
    with pytest.raises(CustomError):
        trigger_custom_error()
```

### Issue 4: Async Code Not Tested
```python
# Example: Async function not covered
async def async_operation():
    result = await database.fetch()  # NOT covered
    return result

# Solution: Test async with pytest-asyncio
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_operation()
    assert result is not None
```

---

## Continuous Coverage Monitoring

### CI/CD Integration (Already Configured)
```yaml
# .github/workflows/test.yml
- name: Generate coverage report
  run: |
    pytest --cov=socratic_system --cov=socrates_cli --cov=socrates_api \
            --cov-fail-under=80  # Fails if below 80%
```

### Local Coverage Checks
```bash
# Before committing
pytest --cov=socratic_system --cov-fail-under=80

# If this fails, fix coverage before pushing
```

### Coverage Tracking Over Time
```bash
# Save coverage metrics
pytest --cov=socratic_system --cov-report=json --cov-report=xml

# Track with: Codecov, Coveralls, or similar service
# Current setup: Codecov integration in CI/CD
```

---

## Module-by-Module Coverage Guide

### socratic_system/database/ (Target: 90%)

**Key Files**:
1. `project_db_v2.py` - Database operations
2. `vector_db.py` - Vector database operations

**Test Requirements**:
```python
# Ensure all database operations tested
- CREATE operations (new users, projects)
- READ operations (queries, retrievals)
- UPDATE operations (modifications)
- DELETE operations (removals)
- Transaction handling (rollback, commit)
- Error scenarios (constraints, locks)
```

**Test File**: Tests in `tests/` directory

### socrates_api/routers/ (Target: 85%)

**Key Files**:
1. `auth.py` - Auth endpoints (95% target)
2. `projects.py` - Project management
3. `github.py` - GitHub integration
4. `knowledge.py` - Knowledge base
5. `llm.py` - LLM configuration
6. `analysis.py` - Code analysis
7. `collaboration.py` - Team features
8. `analytics.py` - Usage analytics

**Test Requirements Per Router**:
- Valid input handling
- Invalid input validation
- Missing required fields
- Authentication/authorization
- Error responses
- Edge cases

**Test Files**:
- `test_routers_comprehensive.py`
- `test_e2e_workflows.py`
- `test_all_endpoints.py`
- `test_auth_scenarios.py`
- `test_auth_95_percent_coverage.py`

### socratic_system/orchestration/ (Target: 80%)

**Key File**: `orchestrator.py`

**Test Requirements**:
- Initialization and startup
- Feature coordination
- Error handling
- Resource cleanup
- Concurrent operations

### socratic_system/agents/ (Target: 80%)

**Key Files**:
- Various agent implementations

**Test Requirements**:
- Agent initialization
- Message handling
- Response generation
- Error handling
- Integration with orchestrator

---

## Running the Full Coverage Pipeline

### Step 1: Run All Tests with Coverage
```bash
# Backend
pytest socratic_system socrates_cli socrates_api \
    --cov=socratic_system \
    --cov=socrates_cli \
    --cov=socrates_api \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=80 \
    -v

# Frontend
cd socrates-frontend && npm run test:coverage
```

### Step 2: Analyze Report
```bash
# Look at HTML report for visual gaps
open htmlcov/index.html

# Check JSON for programmatic analysis
python analyze_coverage.py  # Your analysis script
```

### Step 3: Identify Priority Gaps
```bash
# Create a file: uncovered_modules.txt
# List modules below target coverage
# Priority:
# 1. Auth modules < 95%
# 2. API endpoints < 85%
# 3. Other code < 80%
```

### Step 4: Add Targeted Tests
```bash
# For each uncovered module:
# 1. Identify missing lines
# 2. Write tests to cover them
# 3. Re-run coverage
# 4. Verify improvement
```

### Step 5: Commit and Document
```bash
# Once coverage targets met:
git add tests/
git commit -m "test: Improve coverage to 95% for auth modules

- Add X tests for auth edge cases
- Add Y tests for API endpoints
- Achieve ZZ% overall coverage

Coverage report: htmlcov/index.html"
```

---

## Coverage Metrics Dashboard

### Expected Results After Completion

| Module | Target | Expected | Status |
|--------|--------|----------|--------|
| Auth (Router) | 95% | 95%+ | ✅ |
| Auth (Utils) | 95% | 95%+ | ✅ |
| Projects Router | 85% | 85%+ | ✅ |
| Knowledge Router | 85% | 85%+ | ✅ |
| GitHub Router | 85% | 85%+ | ✅ |
| LLM Router | 85% | 85%+ | ✅ |
| Database Operations | 90% | 90%+ | ✅ |
| Core Orchestration | 80% | 80%+ | ✅ |
| **Overall** | **80%** | **80%+** | **✅** |

---

## Tools and Resources

### Coverage Measurement Tools
- **pytest-cov**: Python coverage plugin for pytest
- **coverage.py**: Underlying coverage library
- **vitest coverage**: Built-in coverage in Vitest

### Code Analysis Tools
- **htmlcov**: Visual coverage report
- **coverage-badge**: Coverage badge for README
- **Codecov**: Online coverage tracking

### Helpful Commands
```bash
# Get quick coverage summary
pytest --cov --co -q

# Detailed missing lines
pytest --cov --cov-report=term-missing

# Branch coverage
pytest --cov --cov-branch

# Specific module
pytest --cov=socratic_system.database

# Fail on threshold
pytest --cov-fail-under=80

# Exclude patterns
pytest --cov --cov-report=html \
    --cov-report=term \
    --cov-report=xml
```

---

## Maintenance and Updates

### After Adding New Features

1. **Measure Coverage**:
   ```bash
   pytest --cov --cov-fail-under=80
   ```

2. **If Coverage Drops**:
   - Identify uncovered code
   - Add tests before merging
   - Maintain 80%+ threshold

3. **Update Documentation**:
   - Document covered code paths
   - List known gaps
   - Plan future improvements

### Regular Review

- **Weekly**: Check coverage on main branch
- **Monthly**: Review coverage trends
- **Quarterly**: Update coverage targets
- **Yearly**: Reassess testing strategy

---

## Success Criteria

Week 4 completion is achieved when:
- ✅ Auth modules have 95%+ coverage
- ✅ API endpoints have 85%+ coverage
- ✅ Overall codebase has 80%+ coverage
- ✅ Security tests pass all scenarios
- ✅ CI/CD enforces all thresholds
- ✅ Coverage reports show no critical gaps

---

**Document Version**: 1.0
**Last Updated**: December 23, 2025
**Next Review**: Monthly coverage check
