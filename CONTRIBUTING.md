# Contributing to Socrates

**Guidelines for developing and contributing to the Socrates system**

## Development Setup

### Prerequisites

- Python 3.12+
- pip or poetry
- Git
- Claude API key (for AI features)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/anthropics/socrates.git
cd socrates

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run tests to verify setup
pytest backend/src/tests/
```

## Code Style & Standards

### Python Style Guide

We follow **PEP 8** with these modifications:

- Line length: 100 characters (instead of 79)
- Use type hints on all functions
- Use docstrings for all public functions and classes
- Use f-strings (Python 3.6+)

### Formatting

```bash
# Format code with black
black backend/src/

# Check code style
flake8 backend/src/

# Sort imports
isort backend/src/
```

### Type Hints

All functions should have type hints:

```python
def calculate_score(
    user_id: str,
    interactions: List[Dict[str, Any]],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """Calculate user engagement score."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def create_project(
    name: str,
    owner: str,
    description: Optional[str] = None
) -> ProjectContext:
    """Create a new project.

    Args:
        name: Project name (required)
        owner: Project owner user ID
        description: Optional project description

    Returns:
        Created ProjectContext object

    Raises:
        ValueError: If name is empty
        HTTPException: If database error occurs

    Example:
        >>> project = create_project("My Project", "user_abc123")
        >>> project.name
        'My Project'
    """
```

## Making Changes

### Branch Naming

Use descriptive branch names:

```
feature/add-websocket-support
bugfix/fix-id-generation-race-condition
docs/update-api-documentation
test/add-integration-tests
refactor/simplify-auth-module
```

### Commit Messages

Use conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:

```
feat(projects): add project archiving feature

Implement project archiving functionality that:
- Marks projects as archived in database
- Excludes archived from listing
- Allows restoration of archived projects
- Adds audit log entries

Fixes #123
```

### Pull Requests

1. Create feature branch from `develop`
2. Make focused, logical commits
3. Write clear PR description
4. Ensure tests pass
5. Request review from maintainers
6. Address feedback
7. Merge once approved

## Adding New Features

### Adding a New API Endpoint

1. **Define the data model** (`models.py`):

```python
class MyRequest(BaseModel):
    """Request for my endpoint."""
    field1: str = Field(..., description="Field description")
    field2: Optional[int] = Field(None, description="Optional field")

    @field_validator("field1")
    @classmethod
    def validate_field1(cls, v):
        if len(v) < 3:
            raise ValueError("field1 must be at least 3 characters")
        return v
```

2. **Create the router** (`routers/my_feature.py`):

```python
"""My feature endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from socrates_api.auth import get_current_user
from socrates_api.database import get_database, LocalDatabase
from socrates_api.models import APIResponse, MyRequest

router = APIRouter(prefix="/my-feature", tags=["my-feature"])

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=APIResponse,
    summary="Create my resource",
)
async def create_resource(
    request: MyRequest,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
) -> APIResponse:
    """Create a new resource."""
    try:
        # Business logic here
        resource_id = IDGenerator.my_resource()

        # Database operation
        db.add_resource(resource_id, request.dict())

        return APIResponse(
            success=True,
            status="created",
            data={"id": resource_id},
            message="Resource created successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create resource: {str(e)}"
        )
```

3. **Register the router** (`routers/__init__.py`):

```python
my_feature_router = _import_router(
    "my_feature_router", "my_feature"
)
```

4. **Include in main app** (`main.py`):

```python
app.include_router(my_feature_router)
```

### Adding a New Agent

1. **Define agent interface** (in `socratic-agents` library)
2. **Implement agent logic**
3. **Register with orchestrator** (`orchestrator.py`):

```python
def _initialize_agents(self) -> None:
    self.agents = {
        ...
        "my_agent": MyAgent(llm_client=self.llm_client),
    }
```

### Adding Database Tables

1. **Update schema** (`database.py`):

```python
def _initialize(self):
    self.conn.execute("""
        CREATE TABLE IF NOT EXISTS my_table (
            id TEXT PRIMARY KEY,              -- Use IDGenerator
            field1 TEXT NOT NULL,
            field2 TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
```

2. **Add accessor methods** to `LocalDatabase` class

## Testing

### Writing Tests

Use pytest with this pattern:

```python
"""Tests for my feature."""

import pytest
from socrates_api.utils import IDGenerator

class TestMyFeature:
    """Test suite for my feature."""

    def test_resource_creation(self):
        """Should create resource with valid input."""
        resource_id = IDGenerator.my_resource()
        assert resource_id.startswith("my_")
        assert len(resource_id) == 17

    def test_invalid_input(self):
        """Should reject invalid input."""
        with pytest.raises(ValueError):
            create_resource("")

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Should handle async operations."""
        result = await fetch_data()
        assert result is not None
```

### Running Tests

```bash
# Run all tests
pytest backend/src/tests/

# Run specific test file
pytest backend/src/tests/test_my_feature.py

# Run with coverage
pytest --cov=socrates_api backend/src/tests/

# Run in verbose mode
pytest -v backend/src/tests/

# Run specific test
pytest backend/src/tests/test_my_feature.py::TestMyFeature::test_resource_creation
```

## Performance Guidelines

### Database Queries

✅ **Good:**
```python
# Use prepared statements
user = db.get_user_by_id(user_id)

# Use indexes for filtering
projects = db.query_projects(owner_id=owner_id)
```

❌ **Bad:**
```python
# N+1 query problem
for project in db.get_all_projects():
    project.owner = db.get_user(project.owner_id)  # Query inside loop!

# String concatenation for queries
query = f"SELECT * FROM users WHERE id = '{user_id}'"  # SQL injection risk!
```

### Caching

✅ **Good:**
```python
@cache.cached(timeout=300)
def get_user_projects(user_id: str):
    return db.query_projects(owner_id=user_id)
```

❌ **Bad:**
```python
def get_user_projects(user_id: str):
    # Recalculated every time, no caching
    return db.query_projects(owner_id=user_id)
```

### Async Operations

✅ **Good:**
```python
# Use async for concurrent operations
tasks = [fetch_document(doc_id) for doc_id in doc_ids]
results = await asyncio.gather(*tasks)
```

❌ **Bad:**
```python
# Sequential, blocking operations
for doc_id in doc_ids:
    result = fetch_document(doc_id)  # Waits for each one!
```

## Security Guidelines

### Input Validation

Always validate user input:

```python
# ✅ Good - validates input
@router.post("/create")
async def create(request: MyRequest):
    # Pydantic validates request body
    # Type hints enforce types
    # Field validators check constraints
    ...

# ❌ Bad - no validation
@router.post("/create")
async def create(data: dict):
    # Could receive anything!
    name = data.get("name")
    ...
```

### SQL Injection Protection

Never use string concatenation for queries:

```python
# ✅ Good - parameterized query
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# ❌ Bad - string concatenation
cursor.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
```

### XSS Protection

Sanitize output and use appropriate escaping:

```python
# ✅ Good - Pydantic automatically escapes
class MyResponse(BaseModel):
    content: str  # Automatically escaped in JSON

# ❌ Bad - raw HTML
response = f"<div>{user_input}</div>"
```

### Authentication

Always verify authentication:

```python
# ✅ Good - requires authentication
@router.get("/resource")
async def get_resource(current_user: str = Depends(get_current_user)):
    ...

# ❌ Bad - no authentication
@router.get("/resource")
async def get_resource():
    ...
```

## Documentation Standards

### Code Comments

Write comments for **why**, not **what**:

```python
# ✅ Good - explains reasoning
# We use UUID4 instead of sequential IDs to prevent ID enumeration attacks
user_id = IDGenerator.user()

# ❌ Bad - obvious from code
# Set user_id to generated ID
user_id = IDGenerator.user()
```

### Docstring Examples

Include usage examples in docstrings:

```python
def search_documents(
    query: str,
    limit: int = 10
) -> List[Document]:
    """Search knowledge base for documents.

    Args:
        query: Search query string
        limit: Maximum results to return

    Returns:
        List of matching documents

    Example:
        >>> docs = search_documents("FastAPI authentication")
        >>> len(docs) > 0
        True
    """
```

## Deployment Checklist

Before deploying to production:

- [ ] All tests pass
- [ ] Code reviewed and approved
- [ ] No security vulnerabilities
- [ ] Performance tested
- [ ] Database migrations run
- [ ] Environment variables configured
- [ ] Monitoring/alerting set up
- [ ] Rollback plan documented
- [ ] Change log updated
- [ ] Documentation updated

## Common Pitfalls

### 1. Forgetting to use IDGenerator

❌ **Bad:**
```python
new_id = str(uuid.uuid4())  # Inconsistent format!
```

✅ **Good:**
```python
new_id = IDGenerator.project()  # Consistent, testable
```

### 2. Not handling async properly

❌ **Bad:**
```python
async def handle_request():
    data = db.get_data()  # Blocking call!
```

✅ **Good:**
```python
async def handle_request():
    data = await db.get_data_async()  # Non-blocking
```

### 3. Missing error handling

❌ **Bad:**
```python
project = db.get_project(project_id)  # What if not found?
return project.name
```

✅ **Good:**
```python
project = db.get_project(project_id)
if not project:
    raise HTTPException(status_code=404, detail="Project not found")
return project.name
```

### 4. Not logging operations

❌ **Bad:**
```python
user = db.create_user(name, email)
return user
```

✅ **Good:**
```python
user = db.create_user(name, email)
logger.info(f"Created user: {user.id}")
return user
```

## Getting Help

- **Questions?** Open an issue on GitHub
- **Bug reports?** Include steps to reproduce
- **Feature requests?** Explain use case and benefits
- **Documentation issues?** Submit corrections

## Code Review Process

1. **Automated checks**
   - Tests pass
   - Code coverage maintained
   - Linting passes
   - Type checking passes

2. **Human review**
   - Code clarity
   - Design consistency
   - Performance implications
   - Security considerations

3. **Approval**
   - At least 2 approvals required
   - All conversations resolved
   - Ready to merge

## Release Process

1. Update version number
2. Update CHANGELOG.md
3. Create release tag
4. Run full test suite
5. Deploy to staging
6. Verify functionality
7. Deploy to production
8. Monitor for issues

## Questions?

See:
- [Architecture Documentation](ARCHITECTURE.md)
- [Backend README](backend/README.md)
- [API Documentation](docs/api.md)

---

**Last Updated**: 2026-03-26
**Version**: 1.0.0
