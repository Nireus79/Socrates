"""
Core calculation and utility modules for Socratic system
"""

try:
    from socratic_learning.analytics.analytics_calculator import AnalyticsCalculator
    from socratic_learning.analytics.maturity_calculator import MaturityCalculator
except ImportError:
    AnalyticsCalculator = None  # type: ignore
    MaturityCalculator = None  # type: ignore

from .analyzer_integration import AnalyzerIntegration
from .insight_categorizer import InsightCategorizer
from .learning_integration import LearningIntegration
from .project_categories import (
    PROJECT_TYPE_DESCRIPTIONS,
    VALID_PROJECT_TYPES,
    get_all_project_types,
    get_phase_categories,
    get_project_type_description,
)
from .workflow_integration import WorkflowIntegration

__all__ = [
    "MaturityCalculator",
    "InsightCategorizer",
    "AnalyticsCalculator",
    "LearningIntegration",
    "WorkflowIntegration",
    "AnalyzerIntegration",
    "get_phase_categories",
    "get_all_project_types",
    "get_project_type_description",
    "VALID_PROJECT_TYPES",
    "PROJECT_TYPE_DESCRIPTIONS",
]
