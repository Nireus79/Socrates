# Shell Command Alternatives and Security Considerations

This document provides guidance on using shell commands in Socrates and recommends alternative approaches where applicable.

## Current Shell Command Usage

### Location: `socratic_system/ui/commands/system_commands.py`

The `SystemStatusCommand` uses shell execution:

```python
subprocess.run(["git", "status"], cwd=project_root)
subprocess.run(["npm", "test"], cwd=project_root)
```

## Security Considerations

When executing shell commands, consider these security best practices:

### 1. **Argument Validation**
- **DO:** Use list syntax `subprocess.run(["git", "status"])`
- **DON'T:** Use shell=True with user input `subprocess.run(f"git {user_input}", shell=True)`
- **Impact:** Prevents shell injection attacks

### 2. **Input Sanitization**
- **DO:** Validate and escape all user-provided arguments
- **DON'T:** Pass user input directly to subprocess
- **Implementation:**
```python
from pathlib import Path
# Validate project path exists and is accessible
project_path = Path(user_input).resolve()
if not project_path.exists():
    raise ValueError("Invalid path")
```

### 3. **Timeout Protection**
- **DO:** Always set subprocess timeout
- **DON'T:** Allow indefinite command execution
- **Example:**
```python
try:
    result = subprocess.run(
        ["git", "status"],
        timeout=GIT_OPERATION_TIMEOUT_SECONDS,  # Use constant
        capture_output=True
    )
except subprocess.TimeoutExpired:
    logger.error("Command timed out")
```

### 4. **Output Capture**
- **DO:** Use capture_output=True to capture command output
- **DON'T:** Stream directly to console without filtering
- **Example:**
```python
result = subprocess.run(
    ["git", "status"],
    capture_output=True,
    text=True  # Get string output instead of bytes
)
```

## Recommended Alternatives to Shell Commands

### Alternative 1: Python Libraries

**Instead of:** `subprocess.run(["git", "status"])`
**Use:** `GitPython` library

```python
from git import Repo

repo = Repo(project_path)
status = repo.git.status()
```

**Benefits:**
- Type-safe operations
- Better error handling
- No subprocess overhead
- Cross-platform compatibility

**Implementation Status:** Consider for git operations in future refactoring

### Alternative 2: Native Python Modules

**Instead of:** `subprocess.run(["python", "test.py"])`
**Use:** `pytest` programmatic API

```python
import pytest

# Run tests and get results directly
result = pytest.main(["-v", "tests/"])
```

**Benefits:**
- Direct access to test results
- No process overhead
- Better integration with Python ecosystem

**Current Usage:** Already using pytest in tests

### Alternative 3: Platform-Independent APIs

**Instead of:** Shell-specific commands
**Use:** Python's `pathlib` and standard library

```python
from pathlib import Path
import shutil

# Instead of: subprocess.run(["rm", "-rf", "build/"])
shutil.rmtree(Path("build"))

# Instead of: subprocess.run(["find", ".", "-name", "*.pyc"])
Path(".").rglob("*.pyc")
```

**Benefits:**
- No subprocess calls
- Works on all platforms
- Type-safe
- Better error handling

## Implementation Roadmap

### Phase 1: Current State (✅ Complete)
- Current shell commands documented
- Security guidelines established
- Timeouts implemented with constants

### Phase 2: Recommended (Next)
- **Priority 1:** Replace git operations with GitPython
  - File: `git_initializer.py`
  - Impact: 20+ subprocess calls → library calls
  
- **Priority 2:** Use pytest API for test execution
  - File: `project_commands.py` (ProjectTestCommand)
  - Impact: Better test result handling

### Phase 3: Nice-to-Have
- Implement async subprocess wrappers
- Add progress callbacks for long-running commands
- Create command result caching

## Testing Shell Command Changes

When refactoring away from subprocess calls:

1. **Unit Tests:** Test with mock return values
2. **Integration Tests:** Test with actual repositories
3. **Security Tests:** Test with malicious inputs
4. **Performance Tests:** Compare subprocess vs library calls

```python
def test_git_status_via_library():
    """Test using GitPython instead of subprocess."""
    repo = Repo(".")
    status = repo.git.status()
    assert "branch" in status
```

## Best Practices Checklist

- [ ] Always use list syntax (no shell=True)
- [ ] Always set timeout (use constants)
- [ ] Always capture output (capture_output=True)
- [ ] Always validate input paths
- [ ] Always handle subprocess.TimeoutExpired
- [ ] Always log command execution (for debugging)
- [ ] Always clean up resources (tempfiles, processes)
- [ ] Always document why shell command is needed

## References

- [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html)
- [GitPython documentation](https://gitpython.readthedocs.io/)
- [CWE-78: Improper Neutralization of Special Elements used in an OS Command](https://cwe.mitre.org/data/definitions/78.html)
- [OWASP: Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
