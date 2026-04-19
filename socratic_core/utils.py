"""
Compatibility module for monolithic socratic_core.utils imports.

This module provides backward compatibility for code that imports from socratic_core.utils,
allowing the monolithic system code to work with the new modularized architecture.
"""

from datetime import datetime
from typing import Optional


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    Serialize a datetime object to ISO format string.

    Args:
        dt: datetime object or None

    Returns:
        ISO format string or None if input is None
    """
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


# Re-export IDGenerator compatibility classes from the new location
try:
    from socrates_api.utils.id_generator import IDGenerator

    # Make the compatibility wrapper available at the old import path
    ProjectIDGenerator = IDGenerator.ProjectIDGenerator

except ImportError:
    # Fallback if the module isn't available yet
    class ProjectIDGenerator:
        @staticmethod
        def generate() -> str:
            """Fallback project ID generator."""
            import uuid
            return f"proj_{uuid.uuid4().hex[:12]}"


__all__ = [
    "ProjectIDGenerator",
    "serialize_datetime",
]
