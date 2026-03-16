"""
Marketplace Module - Skill catalog and discovery service.

Provides:
- SkillMarketplace for centralized skill catalog
- Skill discovery and search
- Skill metadata and analytics
- Marketplace metrics and reporting
"""

from modules.marketplace.service import SkillMarketplace

__all__ = [
    "SkillMarketplace",
]
