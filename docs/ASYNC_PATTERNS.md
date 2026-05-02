# Async/Await Patterns Guide

Comprehensive guide to async/await patterns used throughout Socrates, including best practices, common pitfalls, and real-world examples.

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Fundamentals](#fundamentals)
3. [Pattern Catalog](#pattern-catalog)
4. [Common Pitfalls & Solutions](#common-pitfalls--solutions)
5. [Testing Async Code](#testing-async-code)
6. [Performance Optimization](#performance-optimization)
7. [Real-World Examples](#real-world-examples)

---

## Quick Reference

### Async/Await Cheat Sheet

```python
# ✅ ALWAYS AWAIT async functions
result = await async_function()          # Correct
result = async_function()                # ❌ Wrong - ignores result

# ✅ USE await in async context
async def my_function():
    result = await other_async_function()
    return result

# ❌ DON'T use await in sync context
def sync_function():
    result = await async_function()      # ❌ SyntaxError

# ✅ RUN async code from sync
import asyncio
result = asyncio.run(my_async_function())

# ✅ GATHER multiple async operations
results = await asyncio.gather(
    async_func1(),
    async_func2(),
    async_func3()
)

# ✅ SPAWN background task (don't await)
task = asyncio.create_task(background_operation())

# ❌ DON'T mix sync emit() in async context
async def my_handler():
    orchestrator.emit_event(...)         # ❌ Wrong

# ✅ USE emit_async() in async context
async def my_handler():
    await orchestrator.event_emitter.emit_async(...)

# ✅ USE timeout for long operations
try:
    result = await asyncio.wait_for(operation(), timeout=30)
except asyncio.TimeoutError:
    print("Operation timed out")
```

---

## Fundamentals

### What is a Coroutine?

A coroutine is a function that can **pause and resume** execution:

```python
# Coroutine definition
async def fetch_data():
    # Can pause here (I/O operation)
    response = await http_client.get("https://api.example.com")
    # Resume here when response arrives
    return response.json()

# Calling it returns a coroutine object (not the result!)
coro = fetch_data()
type(coro)  # <class 'coroutine'>

# Must await or run with asyncio
result = await fetch_data()  # Inside async function
result = asyncio.run(fetch_data())  # From sync code
```

### Event Loop

The event loop is the heart of async Python:

```python
import asyncio

async def task1():
    print("Task 1 start")
    await asyncio.sleep(1)
    print("Task 1 end")

async def task2():
    print("Task 2 start")
    await asyncio.sleep(0.5)
    print("Task 2 end")

async def main():
    # Run both tasks concurrently
    await asyncio.gather(task1(), task2())

# OUTPUT:
# Task 1 start
# Task 2 start
# Task 2 end      (after 0.5s)
# Task 1 end      (after 1.0s)

asyncio.run(main())
```

**Key Points**:
- Single event loop per thread
- Only one coroutine runs at a time (no true parallelism)
- Tasks are **lightweight** (thousands can run simultaneously)
- I/O operations don't block other tasks

### Async vs Sync Contexts

```python
# ✅ Sync context - can call sync or sync wrapper
def sync_handler():
    # Can call sync functions directly
    result = expensive_computation()

    # Can call async via asyncio.run() (creates new loop)
    # But NOT recommended - creates loop overhead

    # Better: spawn async task if needed
    asyncio.create_task(background_async_work())

# ✅ Async context - can await async functions
async def async_handler():
    # Can await async functions
    result = await async_operation()

    # Can call sync functions directly
    result = sync_computation()

    # For blocking sync I/O, use thread pool
    result = await asyncio.to_thread(blocking_io)

    # ❌ Can't create new event loop
    # asyncio.run(other_async())  # Error!

# ✅ Mixed context - async calling sync
async def mixed_handler():
    # Call sync function
    sync_result = sync_function()

    # Call async function
    async_result = await async_function()

    return sync_result + async_result
```

---

## Pattern Catalog

### Pattern 1: Request/Response with Agent Bus

**Use Case**: Agent calls another agent and waits for response.

```python
async def process_request_async(self, request: dict) -> dict:
    """Agent processing with inter-agent communication"""

    # Send request to another agent
    response = await self.orchestrator.agent_bus.send_request(
        "target_agent",
        {
            "action": "some_action",
            "data": request.get("data")
        },
        timeout=30.0  # Optional timeout
    )

    # Process response
    if response.get("status") == "success":
        return {
            "status": "success",
            "data": response.get("data")
        }
    else:
        return {
            "status": "error",
            "message": response.get("error")
        }
```

### Pattern 2: Event Emission in Async Context

**Use Case**: Emit event from async method.

```python
async def handle_project_creation_async(self, project: ProjectContext) -> None:
    """Create project and emit async event"""

    # Do async work
    result = await self.validate_project_async(project)

    # ✅ Emit event asynchronously
    await self.orchestrator.event_emitter.emit_async(
        EventType.PROJECT_CREATED,
        {
            "project_id": project.project_id,
            "owner": project.owner,
            "timestamp": datetime.now().isoformat()
        }
    )

    return result
```

### Pattern 3: Background Task Spawning

**Use Case**: Start long-running task without blocking.

```python
# Event handler (sync context)
def on_document_uploaded(data: dict) -> None:
    """Handle document upload, spawn async analysis"""

    document_id = data["document_id"]

    # ✅ Spawn background task
    # Task runs independently, handler returns immediately
    asyncio.create_task(
        analyze_document_async(document_id)
    )

    # Handler returns here, task continues in background
    logger.info(f"Document analysis started for {document_id}")

# Background async function
async def analyze_document_async(document_id: str) -> None:
    """Long-running analysis without blocking event system"""

    document = await get_document(document_id)

    # Expensive operation
    embeddings = await generate_embeddings(document.content)

    # Store results
    await save_embeddings(document_id, embeddings)

    logger.info(f"Document analysis completed for {document_id}")
```

### Pattern 4: Concurrent Operations with gather()

**Use Case**: Run multiple async operations in parallel.

```python
async def process_batch_async(self, projects: List[str]) -> dict:
    """Process multiple projects concurrently"""

    # Create list of coroutines
    tasks = [
        process_project_async(project_id)
        for project_id in projects
    ]

    # Run all concurrently, wait for all to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]

    return {
        "processed": len(successful),
        "failed": len(failed),
        "results": successful
    }

async def process_project_async(project_id: str) -> dict:
    """Process single project"""
    project = await load_project(project_id)
    analysis = await analyze_project(project)
    return analysis
```

### Pattern 5: Timeout Handling

**Use Case**: Protect against hanging operations.

```python
async def fetch_with_timeout_async(self, url: str, timeout: float = 10.0) -> Optional[dict]:
    """Fetch with timeout protection"""

    try:
        # Wait for operation but not longer than timeout
        response = await asyncio.wait_for(
            self.http_client.get(url),
            timeout=timeout
        )
        return response.json()

    except asyncio.TimeoutError:
        logger.warning(f"Request to {url} timed out after {timeout}s")
        return None

    except Exception as e:
        logger.error(f"Request failed: {e}")
        return None
```

### Pattern 6: Sync I/O in Async Context

**Use Case**: Call blocking function from async method.

```python
async def read_file_async(self, filepath: str) -> str:
    """Read file without blocking event loop"""

    # ✅ Use asyncio.to_thread() for blocking I/O
    content = await asyncio.to_thread(
        read_file_blocking,  # Blocking function
        filepath              # Arguments
    )

    return content

def read_file_blocking(filepath: str) -> str:
    """Traditional blocking file read"""
    with open(filepath, 'r') as f:
        return f.read()
```

### Pattern 7: Async Context Manager

**Use Case**: Resource management (connections, files) in async code.

```python
class AsyncDatabaseConnection:
    """Async context manager for database"""

    async def __aenter__(self):
        """Connect on enter"""
        self.connection = await create_async_connection()
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Disconnect on exit"""
        await self.connection.close()

# Usage
async def query_database_async(self, sql: str) -> list:
    """Query with automatic connection management"""

    # Connection opened on enter, closed on exit
    async with AsyncDatabaseConnection() as conn:
        results = await conn.execute(sql)
        return results

    # Connection automatically closed here
```

### Pattern 8: Exception Handling in Async

**Use Case**: Handle errors in async operations.

```python
async def process_with_error_handling_async(self, request: dict) -> dict:
    """Process with comprehensive error handling"""

    try:
        # Attempt async operation
        response = await self.agent_bus.send_request("agent_name", request)

        # Check for errors in response
        if response.get("status") == "error":
            logger.error(f"Agent error: {response.get('message')}")
            return {
                "status": "error",
                "message": "Processing failed"
            }

        return response

    except asyncio.TimeoutError:
        logger.error("Request timed out")
        return {"status": "error", "message": "Timeout"}

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {"status": "error", "message": "Internal error"}
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Forgetting await

**Problem**: Coroutine created but not executed.

```python
# ❌ WRONG
async def handler():
    result = some_async_function()  # Returns coroutine, not result!
    print(result)  # Prints: <coroutine object ...>

# ✅ CORRECT
async def handler():
    result = await some_async_function()  # Now actually executes
    print(result)  # Prints: actual result
```

**Solution**: Always `await` async functions.

### Pitfall 2: Blocking Operations in Async

**Problem**: Async code blocks event loop.

```python
# ❌ WRONG - Blocks event loop
async def handler():
    # This blocks for 5 seconds, freezing other tasks!
    time.sleep(5)

# ✅ CORRECT - Non-blocking
async def handler():
    # This pauses task without blocking event loop
    await asyncio.sleep(5)
```

**Solution**: Use async equivalents or `asyncio.to_thread()`.

### Pitfall 3: Mixing sync and async emit

**Problem**: Runtime error when emitting events.

```python
# ❌ WRONG - sync emit in async context
async def handler():
    await orchestrator.agent_bus.send_request(...)
    orchestrator.emit_event(...)  # RuntimeError!

# ✅ CORRECT - async emit in async context
async def handler():
    await orchestrator.agent_bus.send_request(...)
    await orchestrator.event_emitter.emit_async(...)  # OK
```

**Solution**: Use `emit_async()` in async contexts.

### Pitfall 4: Not handling exceptions in tasks

**Problem**: Exceptions in background tasks are silently lost.

```python
# ❌ WRONG - Exception is swallowed
asyncio.create_task(background_task())

# ✅ CORRECT - Exception is visible
task = asyncio.create_task(background_task())

# Later, check for exceptions
if task.done():
    try:
        result = task.result()
    except Exception as e:
        logger.error(f"Task failed: {e}")
```

**Solution**: Always handle exceptions in background tasks.

### Pitfall 5: Creating new event loop in async context

**Problem**: Can't create nested event loops.

```python
# ❌ WRONG - RuntimeError
async def handler():
    result = asyncio.run(other_async_function())

# ✅ CORRECT - Use await
async def handler():
    result = await other_async_function()

# ✅ OR use asyncio.create_task() if not awaiting
async def handler():
    task = asyncio.create_task(other_async_function())
```

**Solution**: Use `await` or `asyncio.create_task()`, never `asyncio.run()` in async context.

### Pitfall 6: Race conditions in concurrent operations

**Problem**: Concurrent tasks access same resource unsafely.

```python
# ❌ WRONG - Race condition
counter = 0

async def increment():
    global counter
    counter += 1  # Not atomic!

# ✅ CORRECT - Use Lock
counter = 0
lock = asyncio.Lock()

async def increment():
    global counter
    async with lock:
        counter += 1  # Atomic
```

**Solution**: Use `asyncio.Lock` for shared resources.

---

## Testing Async Code

### Using pytest-asyncio

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    result = await some_async_function()
    assert result == expected_value

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test multiple concurrent operations"""
    results = await asyncio.gather(
        async_func1(),
        async_func2(),
        async_func3()
    )
    assert len(results) == 3

@pytest.mark.asyncio
async def test_timeout_handling():
    """Test timeout protection"""
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            slow_async_function(),
            timeout=0.1
        )

@pytest.mark.asyncio
async def test_exception_handling():
    """Test exception handling"""
    with pytest.raises(ValueError):
        await async_function_that_raises()
```

### Mocking Async Functions

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_with_mock():
    """Test with mocked async function"""
    mock_agent = AsyncMock()
    mock_agent.send_request.return_value = {"status": "success"}

    result = await mock_agent.send_request("test_action")

    assert result["status"] == "success"
    mock_agent.send_request.assert_called_once()
```

---

## Performance Optimization

### 1. Use gather() for Concurrency

```python
# ❌ SLOW - Sequential (10 seconds)
async def slow_approach():
    r1 = await operation1()  # 2 sec
    r2 = await operation2()  # 2 sec
    r3 = await operation3()  # 2 sec
    # ... more operations
    # Total: 10 seconds

# ✅ FAST - Concurrent (2 seconds)
async def fast_approach():
    r1, r2, r3 = await asyncio.gather(
        operation1(),  # 2 sec
        operation2(),  # 2 sec (parallel)
        operation3()   # 2 sec (parallel)
    )
    # Total: 2 seconds
```

### 2. Connection Pooling

```python
# Create connection pool once
connection_pool = aiohttp.ClientSession()

async def make_request(url: str):
    """Reuse connection from pool"""
    async with connection_pool.get(url) as response:
        return await response.json()

# Close pool when done
await connection_pool.close()
```

### 3. Batch Operations

```python
# ❌ Slow - Individual operations
async def slow_batch():
    for item in items:
        await process_item(item)  # Individual calls

# ✅ Fast - Batched operations
async def fast_batch():
    results = await asyncio.gather(
        *[process_item(item) for item in items]
    )
```

---

## Real-World Examples

### Example 1: Processing Chat Messages

```python
async def handle_chat_message(self, project_id: str, message: str) -> dict:
    """Process chat message with async operations"""

    # Concurrent operations
    project, knowledge = await asyncio.gather(
        self.database.get_project(project_id),
        self.vector_db.search_knowledge(message)
    )

    # Request to another agent
    insights = await self.agent_bus.send_request(
        "socratic_counselor",
        {
            "action": "process_response",
            "project_id": project_id,
            "response": message,
            "context": knowledge
        }
    )

    # Emit async event
    await self.event_emitter.emit_async(
        EventType.MESSAGE_PROCESSED,
        {"project_id": project_id, "insights_count": len(insights)}
    )

    return insights
```

### Example 2: Batch Project Analysis

```python
async def analyze_projects_batch(self, project_ids: list) -> dict:
    """Analyze multiple projects concurrently"""

    try:
        # Process all projects in parallel
        results = await asyncio.gather(
            *[self.analyze_single_project(pid) for pid in project_ids],
            return_exceptions=True
        )

        # Separate successes and failures
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]

        # Emit completion event
        await self.event_emitter.emit_async(
            EventType.BATCH_ANALYSIS_COMPLETE,
            {
                "total": len(project_ids),
                "successful": len(successful),
                "failed": len(failed)
            }
        )

        return {
            "successful": successful,
            "failed": failed
        }

    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise

async def analyze_single_project(self, project_id: str) -> dict:
    """Analyze single project with timeout"""

    try:
        result = await asyncio.wait_for(
            self.agent_bus.send_request(
                "quality_controller",
                {"action": "analyze", "project_id": project_id}
            ),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Analysis timeout for project {project_id}")
        raise
```

### Example 3: Document Import with Background Processing

```python
async def import_document(self, file_path: str, project_id: str) -> dict:
    """Import document and spawn background analysis"""

    # Read file without blocking (in thread pool)
    content = await asyncio.to_thread(
        read_file_from_disk,
        file_path
    )

    # Parse document
    doc_id = await self.vector_db.store_document(project_id, content)

    # Emit event immediately (sync context works too)
    self.event_emitter.emit(
        EventType.DOCUMENT_IMPORTED,
        {"document_id": doc_id, "project_id": project_id}
    )

    # In event handler, spawn background analysis (no await)
    # asyncio.create_task(analyze_document_async(doc_id))

    return {
        "document_id": doc_id,
        "status": "imported",
        "analysis_status": "pending"
    }
```

---

## Summary

**Key Takeaways**:

1. ✅ **Always `await` async functions** in async context
2. ✅ **Use `emit_async()` in async context**, `emit()` in sync context
3. ✅ **Use `asyncio.gather()`** for concurrent operations
4. ✅ **Use `asyncio.create_task()`** for background tasks
5. ✅ **Handle exceptions** in background tasks
6. ✅ **Use `asyncio.to_thread()`** for blocking I/O
7. ✅ **Test async code** with `pytest.mark.asyncio`
8. ❌ **Never call `asyncio.run()`** from async context
9. ❌ **Never use `time.sleep()`** in async code
10. ❌ **Never mix `emit()` in async** context

---

**Last Updated**: May 2026
**Version**: 1.3.3
