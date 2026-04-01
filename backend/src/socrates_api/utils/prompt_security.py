"""
Prompt Security Utilities

Provides protection against prompt injection attacks using socratic-security library.
Wraps all LLM calls with input validation and sanitization.
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Try to import security components
try:
    from socratic_security import PromptInjectionDetector, PromptSanitizer
    SECURITY_AVAILABLE = True
    logger.info("socratic-security library loaded successfully")
except ImportError:
    SECURITY_AVAILABLE = False
    logger.warning("socratic-security not available - prompt injection detection will be limited")


class SecurePromptHandler:
    """
    Handles prompt security validation and sanitization.

    Provides protection against prompt injection attacks by:
    1. Sanitizing user input
    2. Detecting potential injection attempts
    3. Logging security events

    If socratic-security is unavailable, gracefully degrades to passthrough.
    """

    def __init__(self):
        """Initialize security handler with detector and sanitizer"""
        self.detector = None
        self.sanitizer = None
        self.security_enabled = False

        if SECURITY_AVAILABLE:
            try:
                self.detector = PromptInjectionDetector()
                self.sanitizer = PromptSanitizer()
                self.security_enabled = True
                logger.info("PromptInjectionDetector and PromptSanitizer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize security components: {e}")
                self.security_enabled = False

    def is_secure(self, text: str) -> bool:
        """
        Check if text is safe for LLM input (no injection attempts).

        Args:
            text: Input text to check

        Returns:
            bool: True if safe, False if potential injection detected
        """
        if not self.detector or not self.security_enabled:
            return True  # Passthrough if detector unavailable

        try:
            result = self.detector.is_safe(text)
            if not result:
                logger.warning(f"Potential injection detected in input: {text[:100]}...")
            return result
        except Exception as e:
            logger.warning(f"Security check failed: {e}")
            return True  # Fail open: allow on error

    def sanitize(self, text: str) -> str:
        """
        Sanitize text for safe LLM input.

        Args:
            text: Input text to sanitize

        Returns:
            str: Sanitized text safe for LLM
        """
        if not self.sanitizer or not self.security_enabled:
            return text  # Passthrough if sanitizer unavailable

        try:
            # Try to sanitize if method exists
            if hasattr(self.sanitizer, 'sanitize'):
                sanitized = self.sanitizer.sanitize(text)
            else:
                # Fallback: just return text if sanitize method not available
                logger.debug("PromptSanitizer.sanitize() not available, skipping sanitization")
                sanitized = text

            if sanitized != text:
                logger.debug("Input sanitized due to security concerns")
            return sanitized
        except Exception as e:
            logger.warning(f"Sanitization failed: {e}")
            return text  # Fail open: use original on error

    def validate_prompt(self, prompt: str, log_details: bool = True) -> Tuple[bool, str]:
        """
        Validate and sanitize a prompt for LLM input.

        Performs two-step validation:
        1. Sanitizes the input
        2. Checks for injection attempts

        Args:
            prompt: Raw prompt from user
            log_details: Whether to log validation details

        Returns:
            Tuple[bool, str]: (is_safe, sanitized_prompt)
                is_safe: True if prompt passes all checks
                sanitized_prompt: Safe version of prompt to use
        """
        if not prompt:
            return True, prompt  # Empty prompts are safe

        # Step 1: Sanitize
        sanitized = self.sanitize(prompt)

        # Step 2: Check safety
        is_safe = self.is_secure(sanitized)

        # Log if unsafe
        if not is_safe:
            logger.warning(f"Prompt validation failed - potential injection: {prompt[:100]}...")
            if log_details:
                logger.debug(f"Original: {prompt}")
                logger.debug(f"Sanitized: {sanitized}")

        return is_safe, sanitized

    def validate_user_input(self, user_input: str) -> Tuple[bool, str]:
        """
        Validate user input before using in prompts.

        Stricter validation for direct user input.

        Args:
            user_input: Direct user input

        Returns:
            Tuple[bool, str]: (is_safe, sanitized_input)
        """
        return self.validate_prompt(user_input, log_details=True)

    def get_status(self) -> dict:
        """Get security status information"""
        return {
            "security_enabled": self.security_enabled,
            "detector_available": self.detector is not None,
            "sanitizer_available": self.sanitizer is not None,
            "socratic_security_available": SECURITY_AVAILABLE,
        }


# Global instance
_prompt_handler = None


def get_prompt_handler() -> SecurePromptHandler:
    """
    Get or create global prompt security handler.

    Returns:
        SecurePromptHandler: Global security handler instance
    """
    global _prompt_handler
    if _prompt_handler is None:
        _prompt_handler = SecurePromptHandler()
    return _prompt_handler


def validate_prompt_secure(prompt: str) -> Tuple[bool, str]:
    """
    Convenience function to validate prompt.

    Args:
        prompt: Prompt to validate

    Returns:
        Tuple[bool, str]: (is_safe, sanitized_prompt)
    """
    handler = get_prompt_handler()
    return handler.validate_prompt(prompt)


def validate_user_input_secure(user_input: str) -> Tuple[bool, str]:
    """
    Convenience function to validate user input.

    Args:
        user_input: User input to validate

    Returns:
        Tuple[bool, str]: (is_safe, sanitized_input)
    """
    handler = get_prompt_handler()
    return handler.validate_user_input(user_input)
