"""Performance monitoring and caching - imported from socratic-performance library."""

try:
    from socratic_performance import (
        QueryProfiler,
        QueryStats,
        SubscriptionChecker,
        TierLimits,
        TTLCache,
        cached,
        get_profiler,
    )

    __all__ = [
        "QueryProfiler",
        "QueryStats",
        "TTLCache",
        "cached",
        "get_profiler",
        "SubscriptionChecker",
        "TierLimits",
    ]
except ImportError:
    # socratic-performance library not installed
    __all__ = []
