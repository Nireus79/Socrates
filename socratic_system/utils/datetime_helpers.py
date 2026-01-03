"""
Datetime serialization utilities for Socrates AI
"""

import datetime


def serialize_datetime(dt: datetime.datetime) -> str:
    """Convert datetime to ISO format string"""
    return dt.isoformat()


def deserialize_datetime(dt_string: str) -> datetime.datetime:
    """Convert ISO format string back to datetime

    Supports both ISO format and legacy datetime format for backwards compatibility.
    """
    try:
        return datetime.datetime.fromisoformat(dt_string)
    except (ValueError, AttributeError):
        # Fallback for older datetime formats
        return datetime.datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S.%f")
