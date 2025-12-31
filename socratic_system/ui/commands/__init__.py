"""Command system for Socratic RAG CLI interface"""

from socratic_system.ui.commands.analytics_commands import (
    AnalyticsAnalyzeCommand,
    AnalyticsBreakdownCommand,
    AnalyticsRecommendCommand,
    AnalyticsStatusCommand,
    AnalyticsSummaryCommand,
    AnalyticsTrendsCommand,
)
from socratic_system.ui.commands.base import BaseCommand
from socratic_system.ui.commands.code_commands import CodeDocsCommand, CodeGenerateCommand
from socratic_system.ui.commands.collab_commands import (
    CollabAddCommand,
    CollabListCommand,
    CollabRemoveCommand,
    CollabRoleCommand,
)
from socratic_system.ui.commands.conv_commands import ConvSearchCommand, ConvSummaryCommand
from socratic_system.ui.commands.debug_commands import DebugCommand, LogsCommand
from socratic_system.ui.commands.doc_commands import (
    DocImportCommand,
    DocImportDirCommand,
    DocImportUrlCommand,
    DocListCommand,
    DocPasteCommand,
)
from socratic_system.ui.commands.finalize_commands import (
    FinalizeDocsCommand,
    FinalizeGenerateCommand,
)
from socratic_system.ui.commands.github_commands import (
    GithubImportCommand,
    GithubPullCommand,
    GithubPushCommand,
    GithubSyncCommand,
)
from socratic_system.ui.commands.knowledge_commands import (
    KnowledgeAddCommand,
    KnowledgeExportCommand,
    KnowledgeImportCommand,
    KnowledgeListCommand,
    KnowledgeRemoveCommand,
    KnowledgeSearchCommand,
    RememberCommand,
)
from socratic_system.ui.commands.llm_commands import LLMCommand
from socratic_system.ui.commands.maturity_commands import (
    MaturityCommand,
    MaturityHistoryCommand,
    MaturityStatusCommand,
    MaturitySummaryCommand,
)
from socratic_system.ui.commands.model_commands import ModelCommand
from socratic_system.ui.commands.note_commands import (
    NoteAddCommand,
    NoteDeleteCommand,
    NoteListCommand,
    NoteSearchCommand,
)
from socratic_system.ui.commands.project_commands import (
    ProjectAnalyzeCommand,
    ProjectArchiveCommand,
    ProjectCreateCommand,
    ProjectDeleteCommand,
    ProjectDiffCommand,
    ProjectFixCommand,
    ProjectListCommand,
    ProjectLoadCommand,
    ProjectRestoreCommand,
    ProjectReviewCommand,
    ProjectTestCommand,
    ProjectValidateCommand,
)
from socratic_system.ui.commands.query_commands import ExplainCommand, SearchCommand
from socratic_system.ui.commands.session_commands import (
    AdvanceCommand,
    ChatCommand,
    DoneCommand,
    HintCommand,
    ModeCommand,
)
from socratic_system.ui.commands.skills_commands import (
    SkillsListCommand,
    SkillsSetCommand,
)
from socratic_system.ui.commands.stats_commands import (
    ProjectProgressCommand,
    ProjectStatsCommand,
    ProjectStatusCommand,
)
from socratic_system.ui.commands.subscription_commands import (
    SubscriptionCompareCommand,
    SubscriptionDowngradeCommand,
    SubscriptionStatusCommand,
    SubscriptionTestingModeCommand,
    SubscriptionUpgradeCommand,
)
from socratic_system.ui.commands.system_commands import (
    BackCommand,
    ClearCommand,
    ExitCommand,
    HelpCommand,
    InfoCommand,
    MenuCommand,
    NLUDisableCommand,
    NLUEnableCommand,
    NLUStatusCommand,
    PromptCommand,
    StatusCommand,
)
from socratic_system.ui.commands.user_commands import (
    UserArchiveCommand,
    UserCreateCommand,
    UserDeleteCommand,
    UserLoginCommand,
    UserLogoutCommand,
    UserRestoreCommand,
)

__all__ = [
    "BaseCommand",
    "HelpCommand",
    "ExitCommand",
    "BackCommand",
    "MenuCommand",
    "StatusCommand",
    "ClearCommand",
    "PromptCommand",
    "InfoCommand",
    "ModelCommand",
    "LLMCommand",
    "NLUEnableCommand",
    "NLUDisableCommand",
    "NLUStatusCommand",
    "UserLoginCommand",
    "UserCreateCommand",
    "UserLogoutCommand",
    "UserArchiveCommand",
    "UserDeleteCommand",
    "UserRestoreCommand",
    "ProjectCreateCommand",
    "ProjectLoadCommand",
    "ProjectListCommand",
    "ProjectArchiveCommand",
    "ProjectRestoreCommand",
    "ProjectDeleteCommand",
    "ProjectAnalyzeCommand",
    "ProjectTestCommand",
    "ProjectFixCommand",
    "ProjectValidateCommand",
    "ProjectReviewCommand",
    "ProjectDiffCommand",
    "GithubImportCommand",
    "GithubPullCommand",
    "GithubPushCommand",
    "GithubSyncCommand",
    "ChatCommand",
    "DoneCommand",
    "AdvanceCommand",
    "HintCommand",
    "ModeCommand",
    "CodeGenerateCommand",
    "CodeDocsCommand",
    "FinalizeGenerateCommand",
    "FinalizeDocsCommand",
    "CollabAddCommand",
    "CollabRemoveCommand",
    "CollabListCommand",
    "CollabRoleCommand",
    "SkillsSetCommand",
    "SkillsListCommand",
    "DocImportCommand",
    "DocImportDirCommand",
    "DocImportUrlCommand",
    "DocListCommand",
    "DocPasteCommand",
    "NoteAddCommand",
    "NoteListCommand",
    "NoteSearchCommand",
    "NoteDeleteCommand",
    "ConvSearchCommand",
    "ConvSummaryCommand",
    "ExplainCommand",
    "SearchCommand",
    "ProjectStatsCommand",
    "ProjectProgressCommand",
    "ProjectStatusCommand",
    "DebugCommand",
    "LogsCommand",
    "MaturityCommand",
    "MaturitySummaryCommand",
    "MaturityHistoryCommand",
    "MaturityStatusCommand",
    "AnalyticsAnalyzeCommand",
    "AnalyticsRecommendCommand",
    "AnalyticsTrendsCommand",
    "AnalyticsSummaryCommand",
    "AnalyticsBreakdownCommand",
    "AnalyticsStatusCommand",
    "KnowledgeAddCommand",
    "KnowledgeListCommand",
    "KnowledgeSearchCommand",
    "KnowledgeExportCommand",
    "KnowledgeImportCommand",
    "KnowledgeRemoveCommand",
    "RememberCommand",
    "SubscriptionStatusCommand",
    "SubscriptionUpgradeCommand",
    "SubscriptionDowngradeCommand",
    "SubscriptionCompareCommand",
    "SubscriptionTestingModeCommand",
]
