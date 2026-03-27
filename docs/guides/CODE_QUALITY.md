# Code Quality Standards & Type Safety Guide

## Overview

This guide establishes code quality standards for the Socrates codebase. It covers type hints, error handling, object serialization, and best practices for maintaining a clean, maintainable codebase.

**Last Updated**: 2026-03-27
**Status**: Active - Enforced in Phase 4+
**Audience**: All contributors

---

## Table of Contents

1. [Type Hints](#type-hints)
2. [Function Contracts](#function-contracts)
3. [Error Handling](#error-handling)
4. [Object Serialization](#object-serialization)
5. [Dictionary Operations](#dictionary-operations)
6. [Code Review Checklist](#code-review-checklist)
7. [Examples](#examples)

---

## Type Hints

### Requirements

**All public functions MUST have type hints** for parameters and return values.

```python
# ✅ GOOD: Complete type hints
def create_project(
    project_id: str,
    owner: str,
    name: str,
    description: Optional[str] = None
) -> ProjectContext:
    """Create a new project with full type safety."""
    ...

# ❌ BAD: Missing type hints
def create_project(project_id, owner, name, description=None):
    """Type information is implicit and unclear."""
    ...
```

### Type Hint Syntax

Use modern Python type hints (Python 3.10+ syntax where available):

```python
# ✅ GOOD: Modern syntax
from typing import Optional

def process(value: str | None) -> int:
    """Use | instead of Union for optionals."""
    ...

# ✅ GOOD: Traditional syntax (Python 3.8+)
def process(value: Optional[str]) -> int:
    """Backward compatible with older Python versions."""
    ...

# ❌ BAD: Mixed or unclear
def process(value: Union[str, None]) -> int:
    """Awkward Union syntax - use Optional or |."""
    ...
```

### Specific Type Guidelines

#### Optional Values
```python
# ✅ GOOD: Clear that value can be None
def get_user(user_id: str) -> Optional[User]:
    """Return user or None if not found."""
    ...

# ❌ BAD: Unclear what None means
def get_user(user_id: str) -> User:
    """May raise exception or return None - confusing."""
    ...
```

#### Collections
```python
# ✅ GOOD: Specific collection types
def get_projects(user_id: str) -> List[ProjectContext]:
    """Clear that we return a list of projects."""
    ...

def get_project_map(user_id: str) -> Dict[str, ProjectContext]:
    """Clear that we return a dict mapping."""
    ...

# ❌ BAD: Too generic
def get_projects(user_id: str) -> list:
    """What's in the list?"""
    ...

def get_project_map(user_id: str) -> dict:
    """What are the keys and values?"""
    ...
```

#### Callables
```python
# ✅ GOOD: Clear function signature
def register_handler(
    event: str,
    handler: Callable[[Event], None]
) -> None:
    """Handler receives an Event and returns nothing."""
    ...

# ❌ BAD: Unclear what Callable expects
def register_handler(event: str, handler: Callable) -> None:
    """What are the arguments and return value?"""
    ...
```

#### Literals (for restricted values)
```python
# ✅ GOOD: Clear allowed values
def set_log_level(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]) -> None:
    """Only these log levels are allowed."""
    ...

# ❌ BAD: Too generic
def set_log_level(level: str) -> None:
    """Any string accepted - easy to misuse."""
    ...
```

### Type Aliases

Define reusable type hints for complex types:

```python
# Define at module level
ProjectDict = Dict[str, ProjectContext]
Handler = Callable[[Event], Awaitable[None]]

# Use in functions
def get_all_projects() -> ProjectDict:
    """Returns all projects indexed by ID."""
    ...

def register_handler(handler: Handler) -> None:
    """Register an async event handler."""
    ...
```

---

## Function Contracts

### Clear Intent & Guarantees

Every function should clearly communicate:
1. What it requires (inputs)
2. What it does (description)
3. What it guarantees (outputs)

```python
# ✅ GOOD: Clear contract
def load_project(project_id: str) -> ProjectContext:
    """
    Load a project from the database.

    Args:
        project_id: Unique project identifier

    Returns:
        ProjectContext with all project data

    Raises:
        ProjectNotFoundError: If project doesn't exist
        DatabaseError: If database operation fails
    """
    ...

# ❌ BAD: Unclear contract
def load_project(project_id):
    """Load a project."""
    ...
```

### No Defensive Copies

Don't return copies unless necessary:

```python
# ✅ GOOD: Return object directly
def get_project(project_id: str) -> ProjectContext:
    return self._projects[project_id]

# ❌ BAD: Unnecessary copy
def get_project(project_id: str) -> ProjectContext:
    project = self._projects[project_id]
    return project.copy()  # Why copy if caller expects original?
```

---

## Error Handling

### Exception Hierarchy

Use specific exceptions from `socrates_api.exceptions`:

```python
from socrates_api.exceptions import (
    ProjectNotFoundError,
    UserNotFoundError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    SubscriptionLimitError,
)

# ✅ GOOD: Specific exception
def load_user(username: str) -> User:
    try:
        # ... database query ...
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to load user {username}") from e

# ❌ BAD: Generic Exception
def load_user(username: str) -> User:
    try:
        # ... database query ...
    except Exception:  # Too broad!
        return None  # Caller can't distinguish errors
```

### Structured Error Handling

Never silently swallow exceptions:

```python
# ✅ GOOD: Specific handling, re-raise when appropriate
try:
    project = db.load_project(project_id)
except ProjectNotFoundError:
    # Project specifically not found - OK to handle
    return APIResponse(success=False, data={"error": "Project not found"})
except DatabaseError as e:
    # Database error - should propagate to 500
    logger.error(f"Database error: {e}")
    raise  # Let handler convert to 500

# ❌ BAD: Catch-all and silent failure
try:
    project = db.load_project(project_id)
except Exception:
    return None  # Caller can't distinguish different errors
```

---

## Object Serialization

### Direct Object Returns

Let FastAPI serialize objects directly:

```python
# ✅ GOOD: FastAPI handles serialization
@router.get("/projects/{project_id}")
def get_project(project_id: str) -> ProjectContext:
    project = db.load_project(project_id)
    return project  # ← FastAPI auto-serializes to JSON

# ❌ BAD: Manual serialization
@router.get("/projects/{project_id}")
def get_project(project_id: str) -> Dict:
    project = db.load_project(project_id)
    return project.dict()  # ← Redundant manual conversion

# ❌ BAD: Nested unnecessary conversion
@router.get("/projects/{project_id}")
def get_project(project_id: str) -> APIResponse:
    project = db.load_project(project_id)
    return APIResponse(
        success=True,
        data=project.model_dump()  # ← Already converted by APIResponse serialization
    )
```

### Collections of Objects

```python
# ✅ GOOD: List of typed objects
@router.get("/projects")
def list_projects() -> List[ProjectContext]:
    projects = db.list_projects(current_user.id)
    return projects  # ← FastAPI serializes entire list

# ✅ GOOD: Dict of objects
@router.get("/projects/map")
def get_project_map() -> Dict[str, ProjectContext]:
    projects = db.list_projects(current_user.id)
    return {p.project_id: p for p in projects}

# ❌ BAD: Manual conversion
@router.get("/projects")
def list_projects() -> List[Dict]:
    projects = db.list_projects(current_user.id)
    return [p.dict() for p in projects]  # ← Unnecessary
```

---

## Dictionary Operations

### Prefer Typed Objects

Always use typed objects over dictionaries where possible:

```python
# ✅ GOOD: Typed object with validation
class ProjectContext(BaseModel):
    project_id: str
    name: str
    owner: str
    description: Optional[str] = None

def create_project(ctx: ProjectContext) -> ProjectContext:
    # Type hints provide IDE support and validation
    ...

# ❌ BAD: Untyped dictionary
def create_project(data: Dict[str, Any]) -> Dict[str, Any]:
    # No IDE support, easy to miss required fields
    ...
```

### Dict-like Access (Backward Compatibility)

For compatibility with legacy code, provide dict-like access on objects:

```python
# ProjectContext implements dict-like access
project = ProjectContext(project_id="123", name="Test", owner="alice")

# Attribute access (preferred)
assert project.project_id == "123"

# Dict-like access (legacy support)
assert project["project_id"] == "123"
assert project.get("project_id") == "123"
assert "project_id" in project
```

---

## Code Review Checklist

Use this checklist when reviewing code:

### Type Safety
- [ ] All public functions have parameter type hints
- [ ] All public functions have return type hints
- [ ] Type hints are specific (not `Any` or `dict`)
- [ ] Optional values use `Optional[T]` or `T | None`
- [ ] Collections specify element types (e.g., `List[User]`)

### Error Handling
- [ ] No bare `except Exception:` blocks
- [ ] Specific exceptions from `socrates_api.exceptions`
- [ ] Exceptions documented in docstrings
- [ ] No silent failures (swallowing exceptions)
- [ ] Proper logging before re-raising

### Object Serialization
- [ ] No redundant `.dict()` or `.model_dump()` calls
- [ ] Returning typed objects, not dicts
- [ ] FastAPI auto-serialization used
- [ ] List and dict collections properly typed

### Function Contracts
- [ ] Function docstrings describe what it does
- [ ] Args and Returns documented
- [ ] Raises section lists possible exceptions
- [ ] No surprising None returns (use Optional)

### Code Quality
- [ ] No commented-out code blocks
- [ ] Functions have single responsibility
- [ ] No defensive copies unless needed
- [ ] Consistent naming conventions
- [ ] Passing black, ruff, isort checks

---

## Examples

### Example 1: Database Method

**Before** (Poor type safety):
```python
def get_user(self, username):
    try:
        cursor = self.conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            return None
        return User(*row)
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
```

**After** (Type-safe with proper error handling):
```python
def get_user(self, username: str) -> User:
    """
    Get a user by username.

    Args:
        username: Username to look up

    Returns:
        User object with all user data

    Raises:
        UserNotFoundError: If user doesn't exist
        DatabaseError: If database operation fails
    """
    try:
        cursor = self.conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            raise UserNotFoundError(username)
        return self._row_to_user(row)
    except sqlite3.Error as e:
        logger.error(f"Database error getting user {username}: {e}")
        raise DatabaseError(
            f"Failed to get user {username}"
        ) from e
```

### Example 2: API Endpoint

**Before** (Manual serialization):
```python
@router.get("/projects/{project_id}")
def get_project(project_id: str):
    try:
        project = db.load_project(project_id)
        if not project:
            return {"success": False, "data": None}
        return {
            "success": True,
            "data": project.dict()  # ← Unnecessary
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"success": False, "error": str(e)}
```

**After** (Type-safe, auto-serialized):
```python
@router.get("/projects/{project_id}")
def get_project(project_id: str) -> APIResponse:
    """
    Get a project by ID.

    Returns:
        APIResponse with ProjectContext data

    Raises:
        ProjectNotFoundError: If project not found
    """
    project = db.load_project(project_id)  # Raises if not found
    return APIResponse(
        success=True,
        data=project  # ← FastAPI serializes automatically
    )
```

### Example 3: Collection Return

**Before** (Ambiguous):
```python
def list_projects(user_id: str):
    projects = []
    for p in db.list_projects(user_id):
        projects.append(p.dict())  # Manual conversion
    return {"success": True, "data": projects}
```

**After** (Type-safe, clear):
```python
def list_projects(user_id: str) -> List[ProjectContext]:
    """
    List all projects for a user.

    Args:
        user_id: User's unique identifier

    Returns:
        List of ProjectContext objects
    """
    return db.list_projects(user_id)  # ← Type clearly indicates List[ProjectContext]
```

---

## Tooling

### Type Checking

```bash
# Run mypy on specific files
mypy backend/src/socrates_api/models.py --strict

# Run mypy on entire directory
mypy backend/src/socrates_api/ --show-error-codes

# Generate type coverage report
mypy-coverage backend/src/socrates_api/
```

### Code Formatting

```bash
# Auto-fix formatting
black backend/src/socrates_api/

# Check formatting without changes
black --check backend/src/socrates_api/

# Sort imports
isort backend/src/socrates_api/

# Lint with ruff
ruff check backend/src/socrates_api/
ruff check --fix backend/src/socrates_api/
```

### Pre-commit Hook

Install pre-commit hook to automatically check code:

```bash
pip install pre-commit
pre-commit install

# Now git commit will automatically check your code
```

---

## Migration Guide

### Updating Existing Functions

When updating a function without type hints:

1. **Add parameter type hints**
   ```python
   # Before: def process(value):
   # After:  def process(value: str) -> None:
   ```

2. **Add return type hint**
   ```python
   # Before: def get_data(id):
   # After:  def get_data(id: str) -> Dict[str, Any]:
   ```

3. **Handle None carefully**
   ```python
   # Before: def find(id):  # Might return None
   # After:  def find(id: str) -> Optional[User]:  # Clear it can be None
   ```

4. **Catch specific exceptions**
   ```python
   # Before: except Exception:
   # After:  except (sqlite3.Error, DatabaseError) as e:
   ```

---

## Anti-patterns to Avoid

```python
# ❌ No type hints
def process(data):
    ...

# ❌ Catch-all exceptions
try:
    ...
except Exception:
    return None

# ❌ Redundant serialization
return APIResponse(success=True, data=obj.dict())

# ❌ Too generic types
def process(x: Any) -> Any:
    ...

# ❌ Optional when should be required
def __init__(self, name: Optional[str] = None):
    if not name:
        raise ValueError("name is required")

# ❌ Silent failures
try:
    return db.get_user(username)
except:
    pass  # Silently fails!
```

---

## Common Questions

**Q: Should I add type hints to private functions?**
A: Yes, internal functions benefit from type safety too. If it's a complex function, add hints even if private.

**Q: What about Union types vs |?**
A: Use `|` syntax (Python 3.10+) where available. Use `Optional[T]` for backward compatibility with 3.8-3.9.

**Q: How detailed should type hints be?**
A: More detail is better. `Dict[str, ProjectContext]` is much better than `dict`.

**Q: Should I return None or raise exception?**
A: Raise a specific exception. Explicit errors are better than implicit None returns.

---

## Resources

- [Python Type Hints Documentation](https://docs.python.org/3/library/typing.html)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [PEP 604 - Union as X | Y](https://www.python.org/dev/peps/pep-0604/)
- [mypy Type Checker](https://mypy.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Last Updated**: 2026-03-27
**Maintained By**: Socrates Development Team
**Contributing**: See CONTRIBUTING.md
