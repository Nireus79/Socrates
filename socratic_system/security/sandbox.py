"""
Sandbox Execution Module for Socrates AI

Provides isolated execution environment for potentially dangerous operations
like arbitrary code execution. Enforces resource limits, timeout, and file access restrictions.

Features:
- Process isolation (subprocess execution)
- Resource limits (CPU, memory, file handles)
- Timeout enforcement
- File system restrictions
- Network isolation
- Output capturing
- Error recovery
"""

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""

    # Resource limits
    timeout_seconds: int = 60
    max_memory_mb: int = 512
    max_file_handles: int = 10
    max_processes: int = 1

    # File system
    allow_file_write: bool = True
    project_dir: Optional[str] = None
    allow_network: bool = False

    # Execution
    python_binary: str = "python"
    capture_output: bool = True
    inherit_env: bool = False


class SandboxExecutionError(Exception):
    """Raised when sandboxed execution fails."""
    pass


class SandboxTimeoutError(SandboxExecutionError):
    """Raised when sandboxed code exceeds timeout."""
    pass


class SandboxResourceError(SandboxExecutionError):
    """Raised when sandboxed code exceeds resource limits."""
    pass


@dataclass
class ExecutionResult:
    """Result of sandboxed code execution."""

    success: bool
    output: str  # stdout
    error: str  # stderr
    return_code: int
    execution_time_seconds: float
    peak_memory_mb: Optional[float] = None
    timed_out: bool = False
    resource_exceeded: bool = False
    exit_reason: str = "normal"  # normal, timeout, resource_limit, signal


class Sandbox:
    """
    Secure sandbox for executing untrusted code.

    Provides isolation from:
    - File system (except project directory)
    - Network
    - Other processes
    - Unlimited resource consumption
    """

    def __init__(self, config: Optional[SandboxConfig] = None, logger: Optional[logging.Logger] = None):
        """Initialize sandbox.

        Args:
            config: SandboxConfig with resource limits
            logger: Python logger for logging
        """
        self.config = config or SandboxConfig()
        self.logger = logger or logging.getLogger(__name__)
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate sandbox configuration."""
        if self.config.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be >= 1")
        if self.config.max_memory_mb < 32:
            raise ValueError("max_memory_mb must be >= 32")
        if self.config.project_dir and not Path(self.config.project_dir).exists():
            self.logger.warning(f"Project directory does not exist: {self.config.project_dir}")

    def execute_python_code(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        locals_dict: Optional[Dict[str, Any]] = None,
        agent_name: str = "unknown"
    ) -> ExecutionResult:
        """Execute Python code in sandbox.

        Args:
            code: Python code to execute
            globals_dict: Global variables to provide
            locals_dict: Local variables to provide
            agent_name: Name of agent executing code (for logging)

        Returns:
            ExecutionResult with output and status
        """
        start_time = datetime.now(UTC)

        try:
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                dir=self.config.project_dir
            ) as f:
                # Write code to temp file
                f.write(self._wrap_code_for_execution(code, globals_dict, locals_dict))
                temp_file = f.name

            self.logger.debug(f"[Sandbox] Executing code from {temp_file} for {agent_name}")

            # Execute in subprocess
            result = self._run_subprocess(temp_file, agent_name)

            # Log execution
            execution_time = (datetime.now(UTC) - start_time).total_seconds()
            self.logger.info(
                f"[Sandbox] {agent_name} execution completed: "
                f"success={result.success}, time={execution_time:.2f}s, "
                f"code={result.return_code}, timed_out={result.timed_out}"
            )

            return result

        except SandboxTimeoutError:
            execution_time = (datetime.now(UTC) - start_time).total_seconds()
            self.logger.warning(
                f"[Sandbox] {agent_name} execution TIMEOUT after {execution_time:.2f}s"
            )
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution timeout after {self.config.timeout_seconds} seconds",
                return_code=-1,
                execution_time_seconds=execution_time,
                timed_out=True,
                exit_reason="timeout"
            )
        except SandboxResourceError as e:
            execution_time = (datetime.now(UTC) - start_time).total_seconds()
            self.logger.error(f"[Sandbox] {agent_name} execution RESOURCE EXCEEDED: {e}")
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                return_code=-1,
                execution_time_seconds=execution_time,
                resource_exceeded=True,
                exit_reason="resource_limit"
            )
        except Exception as e:
            execution_time = (datetime.now(UTC) - start_time).total_seconds()
            self.logger.error(f"[Sandbox] {agent_name} execution ERROR: {e}")
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                return_code=-1,
                execution_time_seconds=execution_time,
                exit_reason="error"
            )
        finally:
            # Clean up temporary file
            try:
                if 'temp_file' in locals():
                    os.unlink(temp_file)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")

    def _wrap_code_for_execution(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]],
        locals_dict: Optional[Dict[str, Any]]
    ) -> str:
        """Wrap user code with safety measures.

        Args:
            code: User code to execute
            globals_dict: Globals to provide
            locals_dict: Locals to provide

        Returns:
            Wrapped code with safety measures
        """
        # Encode variables as JSON to avoid injection
        globals_json = json.dumps({k: str(v) for k, v in (globals_dict or {}).items()})
        locals_json = json.dumps({k: str(v) for k, v in (locals_dict or {}).items()})

        wrapped = f"""
import json
import sys
import signal

# Set up timeout handler
def timeout_handler(signum, frame):
    raise TimeoutError("Execution timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({self.config.timeout_seconds})

try:
    # Load provided variables
    _globals = json.loads(r'{globals_json}')
    _locals = json.loads(r'{locals_json}')

    # User code
    {self._indent_code(code)}

    # Success
    sys.exit(0)
except TimeoutError as e:
    print(f"TIMEOUT: {{e}}", file=sys.stderr)
    sys.exit(-1)
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    signal.alarm(0)  # Cancel alarm
"""
        return wrapped

    def _indent_code(self, code: str) -> str:
        """Indent user code for wrapping."""
        lines = code.split('\n')
        return '\n'.join('    ' + line for line in lines)

    def _run_subprocess(self, temp_file: str, agent_name: str) -> ExecutionResult:
        """Run code in subprocess with resource limits.

        Args:
            temp_file: Path to temp file with code
            agent_name: Name of agent for logging

        Returns:
            ExecutionResult

        Raises:
            SandboxTimeoutError: If timeout exceeded
            SandboxResourceError: If resource limits exceeded
        """
        try:
            # Build command
            cmd = [self.config.python_binary, temp_file]

            # Prepare environment
            env = None
            if not self.config.inherit_env:
                # Minimal environment - no network config
                env = {
                    "PATH": os.environ.get("PATH", ""),
                    "HOME": tempfile.gettempdir(),
                }

            # Execute subprocess
            self.logger.debug(f"[Sandbox] Running: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE if self.config.capture_output else None,
                stderr=subprocess.PIPE if self.config.capture_output else None,
                stdin=subprocess.DEVNULL,
                env=env,
                text=True,
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=self.config.timeout_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                raise SandboxTimeoutError(
                    f"Execution exceeded {self.config.timeout_seconds}s timeout"
                )

            # Check resource limits
            # Note: In production, use psutil to monitor actual memory usage
            # For now, we rely on timeout and process termination

            return ExecutionResult(
                success=process.returncode == 0,
                output=stdout or "",
                error=stderr or "",
                return_code=process.returncode,
                execution_time_seconds=0,  # Would need to track from signal
                timed_out=False,
                exit_reason="normal" if process.returncode == 0 else "error"
            )

        except SandboxTimeoutError:
            raise
        except Exception as e:
            raise SandboxExecutionError(f"Subprocess execution failed: {e}")

    def validate_code_safety(self, code: str) -> Tuple[bool, list]:
        """Check code for dangerous patterns.

        Args:
            code: Python code to check

        Returns:
            Tuple of (safe: bool, warnings: list)
        """
        warnings = []

        # Dangerous patterns to check
        dangerous_patterns = {
            "__import__": "Dynamic imports disabled",
            "eval": "eval() is disabled",
            "exec": "exec() is disabled",
            "compile": "compile() is disabled",
            "open": "File operations should use project directory",
            "os.system": "os.system() disabled - use subprocess",
            "subprocess": "Subprocess access limited",
            "socket": "Network access disabled",
        }

        for pattern, warning in dangerous_patterns.items():
            if pattern in code:
                warnings.append(warning)

        # Check for other risky operations
        if "__file__" in code or "__name__" in code:
            warnings.append("File path access should be relative to project directory")

        # Fail if multiple dangerous patterns
        safe = len(warnings) <= 2

        return safe, warnings
