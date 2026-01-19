"""Universal team role definitions for all project types.

This module defines roles that work across all 6 Socratic project types:
- software, business, creative, research, marketing, educational

Universal roles adapt their focus to the project context, enabling one role
system to work seamlessly across different domains.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class TeamMemberRole:
    """Represents a team member's role and metadata in a project.

    Universal roles allow the same role name to represent different expertise
    depending on project type. E.g., "creator" means developer in software
    projects but writer/artist in creative projects.
    """

    username: str
    role: (
        str  # Universal roles: "lead", "creator", "specialist", "analyst", "coordinator", "tester"
    )
    skills: List[str]  # Domain-specific skills (e.g., "python", "ui-design", "copywriting")
    joined_at: datetime

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "username": self.username,
            "role": self.role,
            "skills": self.skills,
            "joined_at": self.joined_at.isoformat(),
        }

    @staticmethod
    def from_dict(data):
        """Create from dictionary."""
        return TeamMemberRole(
            username=data["username"],
            role=data["role"],
            skills=data.get("skills", []),
            joined_at=datetime.fromisoformat(data["joined_at"]),
        )


# ============================================================================
# Universal Role Definitions
# ============================================================================

# Universal role-specific question focus areas
# These work across ALL project types (software, business, creative, research, marketing, educational)
ROLE_FOCUS_AREAS = {
    "lead": (
        "overall vision, strategic goals, resource allocation, stakeholder management, "
        "final decisions, big picture thinking"
    ),
    "creator": (
        "creating deliverables, building/writing/producing core outputs, "
        "implementation details, execution quality, hands-on work"
    ),
    "specialist": (
        "domain expertise, specialized knowledge, technical/creative depth, "
        "best practices in their area, quality standards"
    ),
    "analyst": (
        "research, analysis, evaluation, data interpretation, requirements gathering, "
        "critical assessment, validation"
    ),
    "coordinator": (
        "timelines, schedules, dependencies, process management, team coordination, "
        "milestone tracking, resource scheduling"
    ),
    "tester": (
        "quality assurance, testing strategies, bug identification and reporting, "
        "edge case validation, user acceptance testing, test coverage, performance testing, "
        "critical assessment of deliverables"
    ),
}

# Valid universal roles that work across all project types
VALID_ROLES = [
    "lead",
    "creator",
    "specialist",
    "analyst",
    "coordinator",
    "tester",  # Universal roles
    "owner",
    "editor",
    "viewer",  # RBAC roles for permission hierarchy
]

# ============================================================================
# How Roles Map Across Project Types (for reference)
# ============================================================================

ROLE_EXAMPLES = {
    "software": {
        "lead": "Architect",
        "creator": "Developer",
        "specialist": "Security Expert",
        "analyst": "Business Analyst",
        "coordinator": "Project Manager",
        "tester": "QA Engineer",
    },
    "business": {
        "lead": "CEO/Owner",
        "creator": "Strategist",
        "specialist": "Financial Expert",
        "analyst": "Market Researcher",
        "coordinator": "Operations Manager",
        "tester": "Quality Auditor",
    },
    "creative": {
        "lead": "Director",
        "creator": "Writer/Artist",
        "specialist": "Genre Expert",
        "analyst": "Critic/Reviewer",
        "coordinator": "Producer",
        "tester": "Quality Reviewer",
    },
    "research": {
        "lead": "Principal Investigator",
        "creator": "Researcher",
        "specialist": "Methodology Expert",
        "analyst": "Data Analyst",
        "coordinator": "Lab Manager",
        "tester": "Research Validator",
    },
    "marketing": {
        "lead": "CMO",
        "creator": "Content Creator",
        "specialist": "SEO Expert",
        "analyst": "Market Analyst",
        "coordinator": "Campaign Manager",
        "tester": "Campaign Tester",
    },
    "educational": {
        "lead": "Lead Instructor",
        "creator": "Curriculum Developer",
        "specialist": "Subject Expert",
        "analyst": "Assessment Specialist",
        "coordinator": "Program Coordinator",
        "tester": "Quality Assurance Reviewer",
    },
}
