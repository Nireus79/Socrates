"""
CodeGenerator Agent with Sandbox Integration

Wraps the CodeGeneratorAgent to add safe code execution with resource limits,
security validation, and audit logging.
"""

from typing import Any, Dict, Optional
import logging

from socratic_agents import CodeGeneratorAgent
from socratic_system.security.sandbox import Sandbox, SandboxConfig
from socratic_system.security.audit_logger import AuditLogger


class CodeGeneratorSandboxWrapper:
    """
    Wraps CodeGeneratorAgent with sandbox execution capabilities.

    Provides:
    - Code safety validation before execution
    - Sandboxed execution with resource limits
    - Audit logging of code generation and execution
    - Execution result tracking and error handling
    """

    def __init__(
        self,
        base_agent: CodeGeneratorAgent,
        sandbox: Optional[Sandbox] = None,
        audit_logger: Optional[AuditLogger] = None,
        validate_before_execution: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize sandbox wrapper.

        Args:
            base_agent: CodeGeneratorAgent instance to wrap
            sandbox: Sandbox instance for code execution (created if not provided)
            audit_logger: AuditLogger for logging operations
            validate_before_execution: Whether to validate code before execution
            logger: Python logger instance
        """
        self.base_agent = base_agent
        self.sandbox = sandbox or Sandbox(SandboxConfig())
        self.audit_logger = audit_logger
        self.validate_before_execution = validate_before_execution
        self.logger = logger or logging.getLogger(__name__)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process code generation request with sandbox integration.

        Args:
            request: Request dictionary containing:
                - action: "generate_artifact", "generate_documentation", etc.
                - Other action-specific parameters

        Returns:
            Response dictionary with generation results
        """
        action = request.get("action")

        # Log the request
        if self.audit_logger:
            self.audit_logger.log_agent_action(
                agent_name="CodeGenerator",
                action=action,
                allowed=True,
                reason="Code generation request",
                details={"request_type": action}
            )

        # Generate code using base agent
        result = self.base_agent.process(request)

        # If generation was successful and contains executable code, validate and execute
        if result.get("status") == "success" and self._should_execute(request):
            result = self._execute_generated_code(request, result)

        return result

    def _should_execute(self, request: Dict[str, Any]) -> bool:
        """
        Check if generated code should be executed.

        Args:
            request: Original request

        Returns:
            True if code should be executed, False otherwise
        """
        action = request.get("action")
        execute_flag = request.get("execute_generated_code", False)

        # Only execute if explicitly requested
        return execute_flag and action == "generate_artifact"

    def _execute_generated_code(
        self,
        request: Dict[str, Any],
        generation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute generated code in sandbox.

        Args:
            request: Original request
            generation_result: Result from base agent

        Returns:
            Updated result dictionary with execution details
        """
        try:
            code = generation_result.get("artifact", "")

            if not code:
                self.logger.warning("No code artifact to execute")
                return generation_result

            # Validate code safety
            if self.validate_before_execution:
                is_safe, violations = self.sandbox.validate_code_safety(code)

                if not is_safe:
                    self.logger.warning(f"Code validation failed: {violations}")

                    if self.audit_logger:
                        self.audit_logger.log_security_alert(
                            event_type="CODE_VALIDATION_FAILED",
                            severity="WARNING",
                            trigger_source="CodeGenerator",
                            details={
                                "violations": violations,
                                "action": "Code generation - validation failed"
                            }
                        )

                    generation_result["execution_status"] = "validation_failed"
                    generation_result["validation_violations"] = violations
                    return generation_result

            # Execute code in sandbox
            self.logger.info("Executing generated code in sandbox...")
            execution_result = self.sandbox.execute_python_code(code)

            # Add execution details to result
            generation_result["execution"] = {
                "success": execution_result.success,
                "output": execution_result.output,
                "error": execution_result.error,
                "return_code": execution_result.return_code,
                "execution_time_seconds": execution_result.execution_time_seconds,
                "peak_memory_mb": execution_result.peak_memory_mb,
                "timed_out": execution_result.timed_out,
                "resource_exceeded": execution_result.resource_exceeded,
                "exit_reason": execution_result.exit_reason
            }

            # Log execution
            if self.audit_logger:
                self.audit_logger.log_agent_action(
                    agent_name="CodeGenerator",
                    action="execute_code",
                    allowed=True,
                    reason="Code execution in sandbox",
                    details={
                        "success": execution_result.success,
                        "execution_time_seconds": execution_result.execution_time_seconds,
                        "timed_out": execution_result.timed_out
                    }
                )

            return generation_result

        except Exception as e:
            self.logger.error(f"Error executing generated code: {e}")

            if self.audit_logger:
                self.audit_logger.log_security_alert(
                    event_type="CODE_EXECUTION_ERROR",
                    severity="WARNING",
                    trigger_source="CodeGenerator",
                    details={
                        "error": str(e),
                        "action": "Code generation - execution failed"
                    }
                )

            generation_result["execution_status"] = "error"
            generation_result["execution_error"] = str(e)
            return generation_result

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to base agent for non-overridden methods.

        Args:
            name: Attribute name

        Returns:
            Attribute from base agent
        """
        return getattr(self.base_agent, name)
