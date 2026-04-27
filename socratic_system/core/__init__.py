"""
Core calculation and utility modules for Socratic system
"""

from socratic_system.analyzer import InsightCategorizer
from socratic_system.maturity import MaturityCalculator

from .analytics_calculator import AnalyticsCalculator
from .project_categories import (
    PROJECT_TYPE_DESCRIPTIONS,
    VALID_PROJECT_TYPES,
    get_all_project_types,
    get_phase_categories,
    get_project_type_description,
)

__all__ = [
    "MaturityCalculator",
    "InsightCategorizer",
    "AnalyticsCalculator",
    "get_phase_categories",
    "get_all_project_types",
    "get_project_type_description",
    "VALID_PROJECT_TYPES",
    "PROJECT_TYPE_DESCRIPTIONS",
]
