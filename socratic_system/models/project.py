"""
Project context model for Socrates AI
"""

import datetime
from dataclasses import dataclass

from socratic_system.models.role import TeamMemberRole


@dataclass
class ProjectContext:
    """Represents a project's complete context and metadata"""

    project_id: str
    name: str
    owner: str
    phase: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    collaborators: list[str] = (
        None  # DEPRECATED: Kept for backward compatibility. Use team_members instead.
    )
    description: str = ""
    goals: str = ""
    requirements: list[str] = None
    tech_stack: list[str] = None
    constraints: list[str] = None
    team_structure: str = "individual"
    language_preferences: str = "python"
    deployment_target: str = "local"
    code_style: str = "standard"
    conversation_history: list[dict] = None
    chat_mode: str = "socratic"  # "socratic" or "direct" mode
    is_archived: bool = False
    archived_at: datetime.datetime | None = None
    progress: int = 0  # 0-100 percentage
    status: str = "active"  # active, completed, on-hold
    knowledge_base_content: str = ""  # Imported knowledge base content
    project_type: str = (
        "software"  # Type of project (software, business, creative, research, marketing, educational)
    )

    # System project tracking (for onboarding and special projects)
    is_system_project: bool = False  # Not counted in subscription quotas
    system_project_type: str | None = None  # "onboarding", "sandbox", etc.

    # Team management (NEW)
    team_members: list[TeamMemberRole] | None = (
        None  # Team members with roles (supersedes collaborators)
    )
    pending_questions: list[dict] | None = None  # Question queue for team projects

    # Notes tracking
    notes: list[dict] | None = None  # Project notes list

    # Code history tracking
    code_history: list[dict] | None = None  # History of generated code with metadata

    # Maturity tracking fields
    phase_maturity_scores: dict[str, float] = None  # Per-phase maturity (0-100)
    overall_maturity: float = 0.0  # Overall project maturity (0-100)
    category_scores: dict[str, dict[str, float]] = None  # Category scores by phase
    categorized_specs: dict[str, list[dict[str, any]]] = (
        None  # Specs organized by phase and category
    )
    maturity_history: list[dict[str, any]] = None  # Historical maturity events

    # Analytics tracking fields (real-time metrics updated after each Q&A)
    analytics_metrics: dict[str, any] = None  # Real-time analytics metrics

    # Workflow optimization fields (NEW)
    workflow_definitions: dict[str, any] = None  # Workflow definitions by phase
    workflow_approval_requests: list[dict[str, any]] | None = None  # History of approval requests
    active_workflow_execution: dict[str, any] | None = None  # Current workflow execution state
    workflow_history: list[dict[str, any]] | None = None  # Completed workflows with metrics
    metadata: dict[str, any] | None = (
        None  # Project metadata (use_workflow_optimization flag, etc.)
    )

    # LLM Provider configuration
    llm_configuration: dict[str, any] | None = (
        None  # LLM provider config (provider, model, temperature, etc.)
    )

    # GitHub repository tracking (for imported projects)
    repository_url: str | None = None  # GitHub repository URL
    repository_owner: str | None = None  # Repository owner username
    repository_name: str | None = None  # Repository name
    repository_description: str | None = None  # Repository description
    repository_language: str | None = None  # Primary programming language
    repository_imported_at: datetime.datetime | None = None  # When repo was imported
    repository_file_count: int = 0  # Number of files in repository
    repository_has_tests: bool = False  # Whether repository has tests

    # Export & GitHub Publishing Tracking (NEW)
    last_export_time: datetime.datetime | None = None  # When project was last exported
    last_export_format: str | None = None  # Last export format used (zip, tar, tar.gz, tar.bz2)
    export_count: int = 0  # Total number of exports

    # GitHub Publishing Status (NEW)
    is_published_to_github: bool = False  # Whether project has been published to GitHub
    github_repo_url: str | None = None  # URL of GitHub repository created from this project
    github_clone_url: str | None = None  # Git clone URL (https or ssh)
    github_published_date: datetime.datetime | None = None  # When published to GitHub
    github_repo_private: bool = True  # Whether GitHub repo is private
    github_username: str | None = None  # GitHub username that owns the published repo

    # Git Repository Status (NEW)
    has_git_initialized: bool = False  # Whether git repo has been initialized locally
    git_branch: str | None = None  # Current git branch name
    git_remote_url: str | None = None  # Git remote URL
    uncommitted_changes: bool = False  # Whether there are uncommitted changes

    def __post_init__(self):
        """Initialize default values and migrate legacy collaborators to team_members"""
        self._initialize_list_fields()
        self._initialize_team_members()
        self._initialize_maturity_fields()
        self._initialize_workflow_fields()

    def _initialize_list_fields(self) -> None:
        """Initialize all list fields with empty defaults"""
        if self.collaborators is None:
            self.collaborators = []
        if self.requirements is None:
            self.requirements = []
        if self.tech_stack is None:
            self.tech_stack = []
        if self.constraints is None:
            self.constraints = []
        if self.conversation_history is None:
            self.conversation_history = []
        if self.notes is None:
            self.notes = []
        if self.pending_questions is None:
            self.pending_questions = []

    def _initialize_team_members(self) -> None:
        """Initialize team members, migrating from legacy collaborators if needed"""
        if self.team_members is None:
            self._initialize_team_members_from_collaborators()
            self._ensure_owner_in_team_members()

    def _initialize_team_members_from_collaborators(self) -> None:
        """Migrate legacy collaborators to team_members format"""
        self.team_members = []
        if self.collaborators:
            self._add_owner_to_team_members()
            self._migrate_collaborators_to_team_members()

    def _add_owner_to_team_members(self) -> None:
        """Add project owner to team_members list"""
        if self.owner:
            owner_member = TeamMemberRole(
                username=self.owner,
                role="owner",
                skills=[],
                joined_at=self.created_at,
            )
            self.team_members.append(owner_member)

    def _migrate_collaborators_to_team_members(self) -> None:
        """Convert legacy collaborators list to team members"""
        for collab_username in self.collaborators:
            member = TeamMemberRole(
                username=collab_username,
                role="editor",
                skills=[],
                joined_at=datetime.datetime.now(),
            )
            self.team_members.append(member)

    def _ensure_owner_in_team_members(self) -> None:
        """Ensure owner is in team_members (for new projects without collaborators)"""
        if self.team_members is not None and not self._owner_in_team_members():
            if self.owner:
                owner_member = TeamMemberRole(
                    username=self.owner,
                    role="owner",
                    skills=[],
                    joined_at=self.created_at,
                )
                self.team_members.append(owner_member)

    def _owner_in_team_members(self) -> bool:
        """Check if owner is already in team_members"""
        if not self.team_members:
            return False
        return any(member.username == self.owner for member in self.team_members)

    def _initialize_maturity_fields(self) -> None:
        """Initialize maturity tracking and analytics fields"""
        if self.phase_maturity_scores is None:
            self.phase_maturity_scores = {
                "discovery": 0.0,
                "analysis": 0.0,
                "design": 0.0,
                "implementation": 0.0,
            }
        if self.category_scores is None:
            self.category_scores = {}
        if self.categorized_specs is None:
            self.categorized_specs = {}
        if self.maturity_history is None:
            self.maturity_history = []
        if self.analytics_metrics is None:
            self.analytics_metrics = {
                "velocity": 0.0,
                "total_qa_sessions": 0,
                "avg_confidence": 0.0,
                "weak_categories": [],
                "strong_categories": [],
                "last_updated": None,
            }
        # Calculate overall maturity from phase scores
        self.overall_maturity = self._calculate_overall_maturity()

    def _calculate_overall_maturity(self) -> float:
        """
        Calculate overall project maturity using weighted phase contributions.

        Instead of averaging (which penalizes starting new phases), this uses:
        - All completed phases (with scores) contribute equally
        - Current/active phase (even if just started) contributes its current score
        - Result: advancing to new phases doesn't decrease overall maturity

        Example:
        - Discovery: 100% → overall = 100%
        - Discovery: 100%, Analysis: 0% → overall = 100% (not 50%)
        - Discovery: 100%, Analysis: 30% → overall = (100 + 30) / 2 = 65%
        """
        if not self.phase_maturity_scores:
            return 0.0

        # Get all phases with non-zero scores (these are the ones being worked on)
        scored_phases = [s for s in self.phase_maturity_scores.values() if s > 0]

        if not scored_phases:
            return 0.0

        # Use average of active/completed phases
        # This avoids penalizing users for advancing to new phases
        return sum(scored_phases) / len(scored_phases)

    def _initialize_workflow_fields(self) -> None:
        """Initialize workflow optimization fields"""
        if self.workflow_definitions is None:
            self.workflow_definitions = {}
        if self.workflow_approval_requests is None:
            self.workflow_approval_requests = []
        if self.workflow_history is None:
            self.workflow_history = []
        if self.metadata is None:
            self.metadata = {}
        # Ensure metadata has default optimization flag
        if "use_workflow_optimization" not in self.metadata:
            self.metadata["use_workflow_optimization"] = False

    def get_member_role(self, username: str) -> str | None:
        """Get role for a specific team member."""
        for member in self.team_members or []:
            if member.username == username:
                return member.role
        return None

    def is_solo_project(self) -> bool:
        """Check if this is a solo project (only owner, no other team members)."""
        return len(self.team_members or []) <= 1

    def cleanup_pending_questions(self, max_keep: int = 1) -> None:
        """
        Clean up answered/skipped questions from pending list, maintain FIFO for unanswered.

        Ensures at most max_keep unanswered questions remain in the queue.
        This prevents accumulation of stale questions and maintains single-question-per-generation workflow.

        Args:
            max_keep: Maximum number of unanswered questions to keep (default: 1)
        """
        if not self.pending_questions:
            return

        # Separate questions by status
        unanswered = [q for q in self.pending_questions if q.get("status") == "unanswered"]

        # Keep only the first max_keep unanswered questions (FIFO order)
        # Discard answered/skipped questions to prevent accumulation
        self.pending_questions = unanswered[:max_keep]
