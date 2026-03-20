# Async/Await Patterns Guide

This guide documents async/await patterns used in the Socrates codebase.

## Overview

The codebase uses async/await for non-blocking I/O:
- Database access (SQLAlchemy async)
- Network requests (Claude API, GitHub API)
- Concurrent task processing
- Event loop integration

## Core Async Patterns

### Pattern 1: Async Context Managers

Database session management:

```python
async with pool.get_session() as session:
    result = await session.execute(query)
    # Session automatically cleaned up
```

### Pattern 2: Async Task Gathering

Run multiple operations concurrently:

```python
import asyncio

results = await asyncio.gather(
    operation1(),
    operation2(),
    operation3(),
    return_exceptions=True
)
```

Benefits: Concurrent execution, single await, exception handling

### Pattern 3: Timeout Protection

Always add timeouts:

```python
from socratic_system.config.constants import API_REQUEST_TIMEOUT_SECONDS

try:
    result = await asyncio.wait_for(
        operation(),
        timeout=API_REQUEST_TIMEOUT_SECONDS
    )
except asyncio.TimeoutError:
    logger.error("Operation timed out")
    raise OperationError("Timeout")
```

## Database Access Patterns

### Async Connection Pool

```python
async def get_user(user_id: str):
    async with pool.get_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

# Call from async context
user = await get_user("user123")
```

## Orchestrator Patterns

### Concurrent Agent Execution

```python
async def process_with_agents(request: Dict) -> Dict:
    results = await asyncio.gather(
        orchestrator.handle_request("agent1", request),
        orchestrator.handle_request("agent2", request),
        orchestrator.handle_request("agent3", request),
        return_exceptions=True
    )
    
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]
    
    return {
        "successful": successful,
        "failed": failed
    }
```

## Error Handling

### Async Exceptions

```python
try:
    result = await operation()
except asyncio.TimeoutError:
    logger.error("Operation timed out")
    raise OperationTimeout() from e
except asyncio.CancelledError:
    logger.info("Operation cancelled")
    raise
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise OperationError() from e
```

### Cleanup on Error

```python
async def operation_with_cleanup():
    resource = None
    try:
        resource = await acquire_resource()
        result = await process(resource)
        return result
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise
    finally:
        if resource:
            await release_resource(resource)  # Always cleanup
```

## Performance Tips

### Concurrent vs Sequential

Bad:
```python
# Sequential - slow
user = await get_user("user1")
project = await get_project("proj1")
analytics = await get_analytics("proj1")
```

Good:
```python
# Concurrent - fast
user, project, analytics = await asyncio.gather(
    get_user("user1"),
    get_project("proj1"),
    get_analytics("proj1")
)
```

### Event Loop Blocking

```python
# Bad: Blocks event loop
async def bad():
    import time
    time.sleep(1)  # Blocks entire loop

# Good: Non-blocking
async def good():
    await asyncio.sleep(1)  # Yields control
```

## Testing Async Code

### Using pytest-asyncio

```python
import pytest

@pytest.mark.asyncio
async def test_get_user():
    user = await get_user("user123")
    assert user is not None

@pytest.mark.asyncio
async def test_concurrent():
    results = await asyncio.gather(
        get_user("u1"),
        get_user("u2"),
        get_user("u3")
    )
    assert len(results) == 3
```

### Mocking Async Functions

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock():
    with patch('module.async_func', new_callable=AsyncMock) as mock:
        mock.return_value = {"result": "success"}
        
        result = await async_func()
        assert result == {"result": "success"}
        mock.assert_called_once()
```

## Best Practices

1. Always use timeouts on async operations
2. Use gather for concurrent execution
3. Proper cleanup in finally blocks or context managers
4. Log exceptions with exc_info=True
5. Test async code with pytest-asyncio
6. Avoid blocking calls in async code
7. Document async patterns in docstrings
8. Use specific exception types

## Key Points

- Async/await enables non-blocking I/O
- Use await only on coroutines and awaitable objects
- Context managers provide safe resource management
- Timeouts prevent indefinite hangs
- Gather enables efficient concurrent processing
- Always handle exceptions in async code
- Test async code separately with asyncio support
