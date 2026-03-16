"""
Composition Module - Skill chaining and composition service.

Provides:
- SkillComposer for creating skill chains
- Sequential, parallel, and conditional execution
- Parameter passing between skills
- Error handling in chains
- Composition metrics and analytics
"""

from modules.composition.service import SkillComposer, SkillComposition

__all__ = [
    "SkillComposer",
    "SkillComposition",
]
