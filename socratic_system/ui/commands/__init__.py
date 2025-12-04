"""Command system for Socratic RAG CLI interface"""

from socratic_system.ui.commands.base import BaseCommand
from socratic_system.ui.commands.system_commands import (
    HelpCommand, ExitCommand, BackCommand, MenuCommand, StatusCommand,
    ClearCommand, PromptCommand, InfoCommand,
    NLUEnableCommand, NLUDisableCommand, NLUStatusCommand
)
from socratic_system.ui.commands.user_commands import (
    UserLoginCommand, UserCreateCommand, UserLogoutCommand,
    UserArchiveCommand, UserDeleteCommand, UserRestoreCommand
)
from socratic_system.ui.commands.project_commands import (
    ProjectCreateCommand, ProjectLoadCommand, ProjectListCommand,
    ProjectArchiveCommand, ProjectRestoreCommand, ProjectDeleteCommand
)
from socratic_system.ui.commands.session_commands import (
    ContinueCommand, DoneCommand, AdvanceCommand, HintCommand
)
from socratic_system.ui.commands.code_commands import (
    CodeGenerateCommand, CodeDocsCommand
)
from socratic_system.ui.commands.collab_commands import (
    CollabAddCommand, CollabRemoveCommand, CollabListCommand
)
from socratic_system.ui.commands.doc_commands import (
    DocImportCommand, DocImportDirCommand, DocListCommand
)
from socratic_system.ui.commands.note_commands import (
    NoteAddCommand, NoteListCommand, NoteSearchCommand, NoteDeleteCommand
)
from socratic_system.ui.commands.conv_commands import (
    ConvSearchCommand, ConvSummaryCommand
)
from socratic_system.ui.commands.stats_commands import (
    ProjectStatsCommand, ProjectProgressCommand, ProjectStatusCommand
)
from socratic_system.ui.commands.debug_commands import (
    DebugCommand, LogsCommand
)
from socratic_system.ui.commands.query_commands import (
    AskCommand, ExplainCommand, SearchCommand
)

__all__ = [
    'BaseCommand',
    'HelpCommand', 'ExitCommand', 'BackCommand', 'MenuCommand', 'StatusCommand',
    'ClearCommand', 'PromptCommand', 'InfoCommand',
    'NLUEnableCommand', 'NLUDisableCommand', 'NLUStatusCommand',
    'UserLoginCommand', 'UserCreateCommand', 'UserLogoutCommand',
    'UserArchiveCommand', 'UserDeleteCommand', 'UserRestoreCommand',
    'ProjectCreateCommand', 'ProjectLoadCommand', 'ProjectListCommand',
    'ProjectArchiveCommand', 'ProjectRestoreCommand', 'ProjectDeleteCommand',
    'ContinueCommand', 'DoneCommand', 'AdvanceCommand', 'HintCommand',
    'CodeGenerateCommand', 'CodeDocsCommand',
    'CollabAddCommand', 'CollabRemoveCommand', 'CollabListCommand',
    'DocImportCommand', 'DocImportDirCommand', 'DocListCommand',
    'NoteAddCommand', 'NoteListCommand', 'NoteSearchCommand', 'NoteDeleteCommand',
    'ConvSearchCommand', 'ConvSummaryCommand',
    'AskCommand', 'ExplainCommand', 'SearchCommand',
    'ProjectStatsCommand', 'ProjectProgressCommand', 'ProjectStatusCommand',
    'DebugCommand', 'LogsCommand',
]
