"""
Foundation Module - Core infrastructure services.

Provides:
- LLM service (Claude client)
- Database service (project and vector DB)
- Connection pooling
- Event emitting system
- Caching services
"""

from modules.foundation.service import FoundationService

__all__ = [
    "FoundationService",
]
