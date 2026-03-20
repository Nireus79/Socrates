# Socrates Codebase - Best Practices Guide

This guide documents best practices for developing and maintaining the Socrates codebase.

## Code Organization

All commands inherit from `BaseCommand` and are organized by category in `socratic_system/ui/commands/`.

## Naming Conventions

### Files
- Use lowercase with underscores: `project_commands.py`

### Classes
- PascalCase: `ProjectCreateCommand`
- Command classes end with `Command`
- Manager classes end with `Manager`

### Functions
- snake_case: `execute_command()`, `get_api_key()`
- Private methods start with underscore: `_get_api_key()`
- Boolean methods start with `is_` or `has_`

### Constants
- UPPERCASE with underscores: `TOKEN_WARNING_THRESHOLD`
- Group related constants in `socratic_system/config/constants.py`

## Documentation Standards

Every module and class should have a docstring explaining:
- Purpose and responsibilities
- Key design patterns
- Attributes and methods

## Magic String/Number Elimination

Define constants in `config/constants.py` instead of hardcoding values.

Good pattern:
```python
# In config/constants.py
GIT_OPERATION_TIMEOUT_SECONDS = 10

# In code
from socratic_system.config.constants import GIT_OPERATION_TIMEOUT_SECONDS
result = subprocess.run(cmd, timeout=GIT_OPERATION_TIMEOUT_SECONDS)
```

## Exception Handling

Use specific exception types instead of generic `Exception`:

```python
try:
    result = subprocess.run(cmd, timeout=30)
except subprocess.TimeoutExpired as e:
    logger.error("Operation timed out")
    raise GitOperationError("Timeout") from e
except subprocess.CalledProcessError as e:
    logger.error("Command failed")
    raise GitOperationError("Command failed") from e
```

## Timeout Management

Always set timeouts on operations that could hang:
- subprocess calls
- network requests  
- async operations

```python
subprocess.run(cmd, timeout=GIT_OPERATION_TIMEOUT_SECONDS)
await asyncio.wait_for(operation(), timeout=API_REQUEST_TIMEOUT_SECONDS)
requests.get(url, timeout=30)
```

## Async/Await Patterns

Use async/await for non-blocking I/O:

```python
# Async context managers
async with pool.get_session() as session:
    result = await session.execute(query)

# Gather concurrent operations
results = await asyncio.gather(
    operation1(),
    operation2(),
    return_exceptions=True
)

# Timeout protection
try:
    result = await asyncio.wait_for(operation(), timeout=30)
except asyncio.TimeoutError:
    logger.error("Timed out")
```

## Performance Best Practices

### 1. Avoid Blocking Operations
- Use `await asyncio.sleep()` instead of `time.sleep()`
- Set timeouts to prevent indefinite hangs
- Use async I/O instead of blocking calls

### 2. Use Connection Pooling
- Reuse database connections from pool
- Don't create new connection per operation

### 3. Cache Expensive Operations
- Cache configuration loaded from disk
- Cache query results when appropriate
- Implement TTL-based cache invalidation

### 4. Batch Similar Operations
- Group multiple database queries
- Process multiple items in one operation

## Testing Guidelines

Each command should have tests covering:
- Normal operation with valid arguments
- Error cases with invalid arguments
- Interaction with mocked context/orchestrator
- Exception handling and error messages

## Code Review Checklist

- Module has docstring explaining purpose
- Classes have docstrings with responsibilities
- Public methods have docstrings with Args/Returns
- No hardcoded timeouts (use constants)
- No generic Exception catches
- All subprocess calls have timeout
- No blocking operations in async code
- Configuration is in constants.py
- Error messages are user-friendly
- Performance-critical sections are documented

## Related Documentation

- **REFACTORING_IMPROVEMENTS.md** - Large class refactoring details
- **SHELL_COMMAND_ALTERNATIVES.md** - Security and alternatives for shell commands
- **TODO_AND_FIXME_TRACKING.md** - Tracked action items with issue suggestions
- **MAGIC_STRINGS_REPORT.md** - Report of magic strings needing extraction
