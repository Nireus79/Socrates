"""
Helper utilities for safe orchestrator request execution with proper validation.

This module provides wrappers around orchestrator calls to ensure:
- All orchestrator results are validated before use
- Errors are properly logged
- Failed requests raise exceptions instead of silently failing
- Consistent error handling across the codebase
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def validate_orchestrator_result(
    result: Dict[str, Any], operation: str, log_errors: bool = True
) -> Dict[str, Any]:
    """
    Validate orchestrator request result.

    Args:
        result: The orchestrator result to validate
        operation: Human-readable description of the operation (for logging)
        log_errors: Whether to log validation failures

    Returns:
        The validated result dictionary

    Raises:
        ValueError: If result indicates failure or is malformed
    """
    if not isinstance(result, dict):
        error_msg = f"Orchestrator {operation} returned non-dict result: {type(result)}"
        if log_errors:
            logger.error(error_msg)
        raise ValueError(error_msg)

    # Check for success status
    status = result.get("status")
    if status != "success":
        error_msg = result.get("error", "Unknown error")
        if log_errors:
            logger.error(f"Orchestrator {operation} failed: {error_msg}")
        raise ValueError(f"Orchestrator {operation} failed: {error_msg}")

    return result


def safe_orchestrator_call(
    orchestrator: Any,
    agent: str,
    request_data: Dict[str, Any],
    operation_name: str,
    async_mode: bool = False,
) -> Dict[str, Any]:
    """
    Execute orchestrator call with validation and error handling.

    This is the recommended way to call orchestrator methods throughout the codebase.
    It ensures proper error handling and logging.

    Args:
        orchestrator: The AgentOrchestrator instance
        agent: Target agent name (e.g., "code_validation", "code_generator")
        request_data: Request payload dictionary
        operation_name: Human-readable name of operation (for logging/errors)
        async_mode: Whether to use async version (default: False)

    Returns:
        Validated orchestrator result as dictionary

    Raises:
        ValueError: If orchestrator returns error status
        Exception: If orchestrator call fails
    """
    try:
        logger.debug(f"Executing orchestrator {agent} for {operation_name}")

        # Call orchestrator (sync or async as appropriate)
        if async_mode:
            # For async calls, the caller should use: await result
            result = orchestrator.process_request_async(agent, request_data)
        else:
            result = orchestrator.process_request(agent, request_data)

        # Validate result before returning
        validated = validate_orchestrator_result(result, operation_name)
        logger.debug(f"Orchestrator {operation_name} completed successfully")
        return validated

    except ValueError:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        error_msg = f"Orchestrator {operation_name} raised exception: {str(e)}"
        logger.error(error_msg)
        raise


def get_or_default(
    result: Dict[str, Any], key: str, default: Any = None, log_missing: bool = True
) -> Any:
    """
    Safely extract value from orchestrator result with logging.

    Args:
        result: The validated orchestrator result
        key: Key to extract (supports nested keys with dots, e.g. "data.code")
        default: Default value if key not found
        log_missing: Whether to log missing keys

    Returns:
        Value at key, or default if not found
    """
    keys = key.split(".")
    current: Any = result

    for k in keys:
        if isinstance(current, dict):
            current = current.get(k)
            if current is None:
                if log_missing:
                    logger.warning(f"Missing orchestrator result key: {k} (full: {key})")
                return default
        else:
            if log_missing:
                logger.warning(f"Cannot traverse orchestrator result at key: {k}")
            return default

    return current
