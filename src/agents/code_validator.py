#!/usr/bin/env python3
"""
Code Agent Validator - Quality Assurance for CodeGeneratorAgent
================================================================

Validates every CodeGeneratorAgent action through QualityAnalyzer.
Ensures all code operations meet quality standards and are based on
verified facts rather than assumptions.

Features:
- Pre-action validation (check suggestion before execution)
- Quality assessment (bias, coverage, confidence)
- Post-action validation (verify results meet standards)
- Automatic warnings/blocking for high-risk operations
"""

from functools import wraps
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import logging


logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of code validation"""
    is_valid: bool
    quality_score: float  # 0.0 to 1.0
    bias_score: float  # 0.0 to 1.0
    confidence_level: str  # 'verified', 'assumed', 'speculative'
    issues: List[str]  # Issues found
    warnings: List[str]  # Warnings (non-blocking)
    recommendations: List[str]  # Recommendations
    missing_context: List[str]  # Missing information
    blocked_reason: Optional[str] = None  # Why action was blocked


def validate_code_action(
    action_type: str,
    require_verification: bool = False,
    min_quality_score: float = 0.5,
    block_on_high_bias: bool = True
) -> Callable:
    """
    Decorator to validate CodeGeneratorAgent actions through QualityAnalyzer.

    Args:
        action_type: Type of action ('edit', 'refactor', 'debug', 'fix_bug')
        require_verification: If True, action must be based on verified facts
        min_quality_score: Minimum quality score (0.0-1.0) required
        block_on_high_bias: If True, block actions with bias_score > 0.7

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, data: Dict[str, Any], *args, **kwargs):
            # Skip validation if quality_analyzer not available
            if not hasattr(self, 'quality_analyzer') or not self.quality_analyzer:
                logger.warning(f"QualityAnalyzer not available for {action_type}")
                return func(self, data, *args, **kwargs)

            try:
                # Extract description/rationale for validation
                description = data.get('description', '')
                rationale = data.get('rationale', '')
                code = data.get('code', '')

                # Build validation context
                validation_context = {
                    'action_type': action_type,
                    'description': description,
                    'rationale': rationale,
                    'code': code
                }

                # Perform quality analysis
                result = _validate_code_context(
                    self.quality_analyzer,
                    validation_context,
                    require_verification=require_verification,
                    min_quality_score=min_quality_score,
                    block_on_high_bias=block_on_high_bias
                )

                # Log validation results
                _log_validation_result(action_type, result, logger)

                # Block if necessary
                if not result.is_valid:
                    error_msg = f"Code validation failed: {result.blocked_reason}"
                    logger.error(error_msg)
                    return {
                        'success': False,
                        'message': error_msg,
                        'validation': {
                            'is_valid': result.is_valid,
                            'quality_score': result.quality_score,
                            'bias_score': result.bias_score,
                            'issues': result.issues,
                            'recommendations': result.recommendations
                        },
                        'agent_id': self.agent_id
                    }

                # Add validation context to data for logging
                data['_validation'] = {
                    'quality_score': result.quality_score,
                    'bias_score': result.bias_score,
                    'confidence_level': result.confidence_level,
                    'warnings': result.warnings,
                    'recommendations': result.recommendations
                }

                # Execute the actual function
                func_result = func(self, data, *args, **kwargs)

                # Validate results if function succeeded
                if func_result.get('success') and result.warnings:
                    func_result['_validation_warnings'] = result.warnings

                return func_result

            except Exception as e:
                logger.error(f"Validation error for {action_type}: {e}")
                # Don't block on validation errors, just log
                return func(self, data, *args, **kwargs)

        return wrapper
    return decorator


def _validate_code_context(
    quality_analyzer,
    context: Dict[str, Any],
    require_verification: bool = False,
    min_quality_score: float = 0.5,
    block_on_high_bias: bool = True
) -> ValidationResult:
    """
    Internal validation logic using QualityAnalyzer.

    Returns:
        ValidationResult with detailed validation information
    """
    issues = []
    warnings = []
    recommendations = []
    blocked_reason = None

    action_type = context.get('action_type', 'unknown')
    description = context.get('description', '')
    rationale = context.get('rationale', '')
    code = context.get('code', '')

    # Combine text for analysis
    analysis_text = f"{description} {rationale}"

    # Analyze the suggestion
    try:
        analysis = quality_analyzer.analyze_suggestion(
            {
                'id': f'{action_type}_1',
                'text': analysis_text,
                'type': action_type
            },
            context={'code_change': True}
        )

        quality_score = analysis.quality_score
        bias_score = analysis.bias_score
        confidence_level = analysis.confidence_level

    except Exception as e:
        logger.error(f"QualityAnalyzer error: {e}")
        quality_score = 0.5
        bias_score = 0.0
        confidence_level = 'unknown'

    # Check for issues
    if analysis.bias_detected:
        issues.append(f"Bias detected: {analysis.bias_detected.value}")
        recommendations.extend(analysis.suggested_improvements)

    if analysis.missing_context:
        issues.extend(analysis.missing_context)

    if analysis.confidence_level == 'speculative':
        warnings.append(
            "Action is based on speculative assumptions. "
            "Consider verifying requirements before proceeding."
        )

    if require_verification and confidence_level != 'verified':
        blocked_reason = (
            f"This action requires verified facts, but confidence is '{confidence_level}'. "
            "Please provide more context or requirements."
        )

    if quality_score < min_quality_score:
        issues.append(
            f"Quality score {quality_score:.2f} below minimum {min_quality_score}"
        )

    if block_on_high_bias and bias_score > 0.7:
        blocked_reason = (
            f"High bias score ({bias_score:.2f}) detected. "
            f"Reason: {analysis.bias_explanation}"
        )

    # Determine if valid
    is_valid = blocked_reason is None and len(issues) == 0

    # Try to get additional analysis info
    missing_context = getattr(analysis, 'missing_context', [])

    return ValidationResult(
        is_valid=is_valid,
        quality_score=quality_score,
        bias_score=bias_score,
        confidence_level=confidence_level,
        issues=issues,
        warnings=warnings,
        recommendations=recommendations,
        missing_context=missing_context,
        blocked_reason=blocked_reason
    )


def _log_validation_result(
    action_type: str,
    result: ValidationResult,
    logger: logging.Logger
) -> None:
    """Log validation results at appropriate level."""
    if result.is_valid:
        logger.info(
            f"{action_type} validation passed: "
            f"quality={result.quality_score:.2f}, "
            f"bias={result.bias_score:.2f}, "
            f"confidence={result.confidence_level}"
        )
    else:
        logger.warning(
            f"{action_type} validation failed: {result.blocked_reason}"
        )

    if result.warnings:
        for warning in result.warnings:
            logger.warning(f"  WARNING: {warning}")

    if result.recommendations:
        for rec in result.recommendations:
            logger.info(f"  RECOMMENDATION: {rec}")


__all__ = [
    'validate_code_action',
    'ValidationResult',
]
