"""Code analysis and insights - imported from socratic-analyzer library."""

try:
    from socratic_analyzer import (
        InsightCategorizer,
        WorkflowCostCalculator,
        WorkflowPathFinder,
        WorkflowRiskCalculator,
    )

    __all__ = [
        "InsightCategorizer",
        "WorkflowCostCalculator",
        "WorkflowPathFinder",
        "WorkflowRiskCalculator",
    ]
except ImportError:
    # socratic-analyzer library not installed
    __all__ = []
