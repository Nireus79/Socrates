"""
Core calculation and utility modules for Socratic system
"""

try:
    from socratic_analyzer import InsightCategorizer
except ImportError:
    InsightCategorizer = None

try:
    from socratic_maturity import MaturityCalculator
except ImportError:
    MaturityCalculator = None

from .analytics_calculator import AnalyticsCalculator
from .project_categories import (
    PROJECT_TYPE_DESCRIPTIONS,
    VALID_PROJECT_TYPES,
    get_all_project_types,
    get_phase_categories,
    get_project_type_description,
)

__all__ = [
    "AnalyticsCalculator",
    "get_phase_categories",
    "get_all_project_types",
    "get_project_type_description",
    "VALID_PROJECT_TYPES",
    "PROJECT_TYPE_DESCRIPTIONS",
]

# Add optional items that were successfully imported
if MaturityCalculator is not None:
    __all__.append("MaturityCalculator")
if InsightCategorizer is not None:
    __all__.append("InsightCategorizer")
