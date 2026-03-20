# Error Handling Guide

This guide documents error handling patterns and best practices throughout the Socrates codebase.

## Exception Hierarchy

### Base Exception Classes

All custom exceptions should inherit from a module-specific base exception.

Examples from git_initializer.py:
- GitInitializationError - Raised when git initialization fails
- GitOperationError - Raised when git operation fails  
- GitHubError - Raised when GitHub API operation fails
- GitConfigError - Raised when git configuration fails
- RepositoryInitializationError - Raised when repository initialization fails
- CommitError - Raised when commit operation fails
- RepositoryRemoteError - Raised when remote repository operations fail

### Exception Naming Convention

- Use specific suffixes indicating error category
- *Error - General operation failure
- *Timeout - Operation exceeded time limit
- *Validation - Input validation failure
- *Configuration - Configuration issue
- *NotFound - Resource not found

## Error Handling Patterns

### Pattern 1: Wrap External Exceptions

When catching external library exceptions, wrap them in module-specific exceptions:

```python
try:
    result = subprocess.run(["git", "status"], timeout=10)
except subprocess.TimeoutExpired as e:
    raise GitOperationError("Operation exceeded timeout") from e
except subprocess.CalledProcessError as e:
    raise GitOperationError("Git command failed") from e
except FileNotFoundError as e:
    raise GitInitializationError("Git not installed") from e
```

Benefits:
- Callers don't need to know about subprocess exceptions
- Module provides consistent exception interface
- Original exception preserved (from e)

### Pattern 2: Validation Before Operation

Validate inputs before attempting operation:

```python
def initialize_repository(project_root: Path) -> Tuple[bool, str]:
    if not project_root.is_dir():
        raise ValueError(f"Directory does not exist: {project_root}")
    
    try:
        # Perform git init
    except GitOperationError:
        raise
```

Benefits:
- Fail early with clear error messages
- Separate validation from operation logic
- More specific error messages

### Pattern 3: Command Error Handling

All commands inherit error handling from BaseCommand:

```python
class BaseCommand:
    def error(self, message: str) -> Dict[str, Any]:
        return {"status": "error", "message": message, "data": {}}
    
    def validate_args(self, args: List[str], min_count: int = 0) -> bool:
        return len(args) >= min_count
    
    def require_user(self, context: Dict[str, Any]) -> bool:
        return context.get("user") is not None
```

### Pattern 4: Context Manager for Cleanup

Use context managers to ensure resource cleanup on error:

```python
@asynccontextmanager
async def database_session():
    session = None
    try:
        session = await pool.acquire()
        yield session
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if session:
            await pool.release(session)
```

## Logging Errors

### Logging Levels

- DEBUG: Detailed diagnostic information
- INFO: Successful operations and milestones
- WARNING: Unexpected but recoverable conditions
- ERROR: Serious problems requiring attention
- CRITICAL: Fatal errors preventing continuation

### Error Logging Best Practice

```python
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
```

Key: Use `exc_info=True` to preserve stack trace.

## Testing Error Scenarios

Test both exception raising and error responses:

```python
def test_missing_directory():
    with pytest.raises(ValueError) as exc_info:
        GitInitializer.initialize_repository(Path("/nonexistent"))
    assert "does not exist" in str(exc_info.value)

def test_command_error_response():
    cmd = ProjectCreateCommand()
    result = cmd.execute([], {})
    assert result["status"] == "error"
    assert "message" in result
```

## Common Error Scenarios

### Timeout Handling

Always set timeouts on potentially long-running operations:

```python
try:
    result = subprocess.run(cmd, timeout=GIT_OPERATION_TIMEOUT_SECONDS)
except subprocess.TimeoutExpired:
    raise GitOperationError("Command timed out") from e
```

### Resource Cleanup on Error

Use context managers for automatic cleanup:

```python
with tempfile.TemporaryDirectory() as tmpdir:
    try:
        result = do_work(tmpdir)
        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        # tmpdir automatically cleaned up
        raise
```

## Error Message Guidelines

### Good Error Messages
- Specific: "Project 'MyProject' already exists at /path"
- Actionable: "Invalid project name: must start with letter"
- Contextual: "Git init failed: repository already exists"

### Bad Error Messages
- Generic: "An error occurred"
- Vague: "Operation failed"
- Too technical: "CalledProcessError with returncode 128"

## Summary

Key principles:
1. Use specific exception types
2. Provide clear, actionable error messages
3. Log at appropriate levels with context
4. Clean up resources in finally blocks
5. Test error scenarios thoroughly
6. Preserve exception chains with `from e`
