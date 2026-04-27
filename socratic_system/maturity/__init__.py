"""Maturity tracking and phase management - imported from socratic-maturity library."""

try:
    from socratic_maturity import (
        CategoryScore,
        MaturityCalculator,
        MaturityEvent,
        PhaseMaturity,
    )

    __all__ = [
        "MaturityCalculator",
        "CategoryScore",
        "PhaseMaturity",
        "MaturityEvent",
    ]
except ImportError:
    # socratic-maturity library not installed
    __all__ = []
