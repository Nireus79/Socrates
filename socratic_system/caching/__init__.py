"""Caching module for Phase 3 event-driven background processing.

Provides result caching infrastructure for analysis results.
"""

from .analysis_cache import AnalysisCache, InMemoryAnalysisCache

__all__ = [
    "AnalysisCache",
    "InMemoryAnalysisCache",
]
