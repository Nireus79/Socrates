"""Maturity tracking and phase management - imported from socratic-maturity library."""

from socratic_maturity import CategoryScore, PhaseMaturity, MaturityEvent

# IMPORTANT: The local MaturityCalculator is imported here to support project_type and
# claude_client parameters that are required by quality_controller.py and analytics.py.
# This avoids circular imports by being a minimal bridge module.

_cached_local_calc = None

class MaturityCalculator:
    """
    Proxy class that lazy-imports and returns instances of the local MaturityCalculator.

    This avoids circular imports while maintaining compatibility with code that expects
    the local implementation with project_type and claude_client parameters.
    """

    def __new__(cls, project_type: str = "software", claude_client=None):
        """Create and return an instance of the local MaturityCalculator."""
        global _cached_local_calc

        # Lazy import on first use
        if _cached_local_calc is None:
            try:
                # This import is done here (not at module load time) to avoid circular imports
                import sys
                from importlib import import_module

                # Import just the maturity_calculator file, not through socratic_system
                spec = import_module('socratic_system.core.maturity_calculator')
                _cached_local_calc = spec.MaturityCalculator
            except Exception:
                # If local import fails, use library version as fallback
                from socratic_maturity import MaturityCalculator as LibCalc
                _cached_local_calc = LibCalc

        # Create and return instance
        return _cached_local_calc(project_type, claude_client)

__all__ = [
    "MaturityCalculator",
    "CategoryScore",
    "PhaseMaturity",
    "MaturityEvent",
]
