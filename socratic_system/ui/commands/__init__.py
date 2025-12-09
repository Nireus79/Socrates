"""Command system for Socratic RAG CLI interface"""

from socratic_system.ui.commands.base import BaseCommand
from socratic_system.ui.commands.code_commands import CodeDocsCommand, CodeGenerateCommand
from socratic_system.ui.commands.collab_commands import (
    CollabAddCommand,
    CollabListCommand,
    CollabRemoveCommand,
)
from socratic_system.ui.commands.conv_commands import ConvSearchCommand, ConvSummaryCommand
from socratic_system.ui.commands.debug_commands import DebugCommand, LogsCommand
from socratic_system.ui.commands.doc_commands import (
    DocImportCommand,
    DocImportDirCommand,
    DocListCommand,
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
from socratic_system.ui.commands.model_commands import ModelCommand
from socratic_system.ui.commands.note_commands import (
    NoteAddCommand,
    NoteDeleteCommand,
    NoteListCommand,
    NoteSearchCommand,
)
from socratic_system.ui.commands.project_commands import (
    ProjectArchiveCommand,
    ProjectCreateCommand,
    ProjectDeleteCommand,
    ProjectListCommand,
    ProjectLoadCommand,
    ProjectRestoreCommand,
)
from socratic_system.ui.commands.query_commands import AskCommand, ExplainCommand, SearchCommand
from socratic_system.ui.commands.session_commands import (
    AdvanceCommand,
    ContinueCommand,
    DoneCommand,
    HintCommand,
)
from socratic_system.ui.commands.stats_commands import (
    ProjectProgressCommand,
    ProjectStatsCommand,
    ProjectStatusCommand,
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
    "ContinueCommand",
    "DoneCommand",
    "AdvanceCommand",
    "HintCommand",
    "CodeGenerateCommand",
    "CodeDocsCommand",
    "CollabAddCommand",
    "CollabRemoveCommand",
    "CollabListCommand",
    "DocImportCommand",
    "DocImportDirCommand",
    "DocListCommand",
    "NoteAddCommand",
    "NoteListCommand",
    "NoteSearchCommand",
    "NoteDeleteCommand",
    "ConvSearchCommand",
    "ConvSummaryCommand",
    "AskCommand",
    "ExplainCommand",
    "SearchCommand",
    "ProjectStatsCommand",
    "ProjectProgressCommand",
    "ProjectStatusCommand",
    "DebugCommand",
    "LogsCommand",
    "KnowledgeAddCommand",
    "KnowledgeListCommand",
    "KnowledgeSearchCommand",
    "KnowledgeExportCommand",
    "KnowledgeImportCommand",
    "KnowledgeRemoveCommand",
    "RememberCommand",
]
