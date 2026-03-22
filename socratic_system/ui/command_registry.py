"""
Centralized Command Registry for Socrates

This module provides a unified command registry that consolidates all CLI commands
from the local command system (socratic_system.ui.commands) with the socrates-cli library.

The registry enables:
1. Centralized command discovery and metadata
2. Dynamic command execution through multiple interfaces (REPL, Click CLI, API)
3. Unified help and documentation
4. Command aliasing and shortcuts
5. Command metrics and analytics
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import inspect

from socratic_system.ui.commands import *  # noqa: F401, F403


class CommandCategory(Enum):
    """Command category enumeration"""

    PROJECTS = "Projects"
    CODE = "Code Generation"
    CHAT = "Chat & Conversation"
    KNOWLEDGE = "Knowledge Management"
    COLLABORATION = "Collaboration"
    ANALYTICS = "Analytics & Monitoring"
    DOCUMENTATION = "Documentation"
    USER = "User Management"
    SYSTEM = "System"
    DEBUG = "Debugging"
    WORKFLOW = "Workflow"


@dataclass
class CommandMetadata:
    """Metadata for a command"""

    name: str
    description: str
    category: CommandCategory
    aliases: List[str] = field(default_factory=list)
    args: List[str] = field(default_factory=list)
    options: List[str] = field(default_factory=list)
    example: str = ""
    requires_auth: bool = True
    requires_project: bool = False


class CommandRegistry:
    """
    Centralized registry for all Socrates commands.

    Maps command names to command classes and provides metadata,
    discovery, execution, and help functionality.
    """

    def __init__(self):
        """Initialize the command registry."""
        self._commands: Dict[str, type] = {}
        self._metadata: Dict[str, CommandMetadata] = {}
        self._aliases: Dict[str, str] = {}  # alias -> command_name
        self._category_index: Dict[CommandCategory, List[str]] = {}

        # Register all built-in commands
        self._register_built_in_commands()

    def _register_built_in_commands(self):
        """Register all built-in commands from the command system."""
        # Import all command classes
        from socratic_system.ui.commands import (
            # Projects
            ProjectCreateCommand,
            ProjectLoadCommand,
            ProjectListCommand,
            ProjectArchiveCommand,
            ProjectRestoreCommand,
            ProjectDeleteCommand,
            ProjectAnalyzeCommand,
            ProjectTestCommand,
            ProjectFixCommand,
            ProjectValidateCommand,
            ProjectReviewCommand,
            ProjectDiffCommand,
            # Code
            CodeGenerateCommand,
            CodeDocsCommand,
            # Chat
            ChatCommand,
            DoneCommand,
            AdvanceCommand,
            RollbackCommand,
            HintCommand,
            ModeCommand,
            SkippedCommand,
            # Knowledge
            KnowledgeAddCommand,
            KnowledgeListCommand,
            KnowledgeSearchCommand,
            KnowledgeExportCommand,
            KnowledgeImportCommand,
            KnowledgeRemoveCommand,
            RememberCommand,
            # Collaboration
            CollabAddCommand,
            CollabRemoveCommand,
            CollabListCommand,
            CollabRoleCommand,
            # Analytics
            AnalyticsAnalyzeCommand,
            AnalyticsRecommendCommand,
            AnalyticsTrendsCommand,
            AnalyticsSummaryCommand,
            AnalyticsBreakdownCommand,
            AnalyticsStatusCommand,
            # Documentation
            DocImportCommand,
            DocImportDirCommand,
            DocImportUrlCommand,
            DocListCommand,
            DocPasteCommand,
            DocsCommand,
            FinalizeGenerateCommand,
            FinalizeDocsCommand,
            # User
            UserLoginCommand,
            UserCreateCommand,
            UserLogoutCommand,
            UserArchiveCommand,
            UserDeleteCommand,
            UserRestoreCommand,
            # System
            ClearCommand,
            ExitCommand,
            BackCommand,
            MenuCommand,
            StatusCommand,
            InfoCommand,
            PromptCommand,
            HelpCommand,
            NLUEnableCommand,
            NLUDisableCommand,
            NLUStatusCommand,
            ModelCommand,
            LLMCommand,
            # GitHub
            GithubImportCommand,
            GithubPullCommand,
            GithubPushCommand,
            GithubSyncCommand,
            # Utilities
            SkillsSetCommand,
            SkillsListCommand,
            MaturityCommand,
            MaturitySummaryCommand,
            MaturityHistoryCommand,
            MaturityStatusCommand,
            ConvSearchCommand,
            ConvSummaryCommand,
            ExplainCommand,
            SearchCommand,
            ProjectStatsCommand,
            ProjectProgressCommand,
            ProjectStatusCommand,
            DebugCommand,
            LogsCommand,
            FileDeleteCommand,
            NoteAddCommand,
            NoteListCommand,
            NoteSearchCommand,
            NoteDeleteCommand,
            SubscriptionStatusCommand,
            SubscriptionUpgradeCommand,
            SubscriptionDowngradeCommand,
            SubscriptionCompareCommand,
            SubscriptionTestingModeCommand,
        )

        # Project commands
        self.register(ProjectCreateCommand, CommandCategory.PROJECTS)
        self.register(ProjectLoadCommand, CommandCategory.PROJECTS)
        self.register(ProjectListCommand, CommandCategory.PROJECTS)
        self.register(ProjectArchiveCommand, CommandCategory.PROJECTS)
        self.register(ProjectRestoreCommand, CommandCategory.PROJECTS)
        self.register(ProjectDeleteCommand, CommandCategory.PROJECTS)
        self.register(ProjectAnalyzeCommand, CommandCategory.PROJECTS)
        self.register(ProjectTestCommand, CommandCategory.PROJECTS)
        self.register(ProjectFixCommand, CommandCategory.PROJECTS)
        self.register(ProjectValidateCommand, CommandCategory.PROJECTS)
        self.register(ProjectReviewCommand, CommandCategory.PROJECTS)
        self.register(ProjectDiffCommand, CommandCategory.PROJECTS)

        # Code commands
        self.register(CodeGenerateCommand, CommandCategory.CODE)
        self.register(CodeDocsCommand, CommandCategory.CODE)

        # Chat commands
        self.register(ChatCommand, CommandCategory.CHAT)
        self.register(DoneCommand, CommandCategory.CHAT)
        self.register(AdvanceCommand, CommandCategory.CHAT)
        self.register(RollbackCommand, CommandCategory.CHAT)
        self.register(HintCommand, CommandCategory.CHAT)
        self.register(ModeCommand, CommandCategory.CHAT)
        self.register(SkippedCommand, CommandCategory.CHAT)

        # Knowledge commands
        self.register(KnowledgeAddCommand, CommandCategory.KNOWLEDGE)
        self.register(KnowledgeListCommand, CommandCategory.KNOWLEDGE)
        self.register(KnowledgeSearchCommand, CommandCategory.KNOWLEDGE)
        self.register(KnowledgeExportCommand, CommandCategory.KNOWLEDGE)
        self.register(KnowledgeImportCommand, CommandCategory.KNOWLEDGE)
        self.register(KnowledgeRemoveCommand, CommandCategory.KNOWLEDGE)
        self.register(RememberCommand, CommandCategory.KNOWLEDGE)

        # Collaboration commands
        self.register(CollabAddCommand, CommandCategory.COLLABORATION)
        self.register(CollabRemoveCommand, CommandCategory.COLLABORATION)
        self.register(CollabListCommand, CommandCategory.COLLABORATION)
        self.register(CollabRoleCommand, CommandCategory.COLLABORATION)

        # Analytics commands
        self.register(AnalyticsAnalyzeCommand, CommandCategory.ANALYTICS)
        self.register(AnalyticsRecommendCommand, CommandCategory.ANALYTICS)
        self.register(AnalyticsTrendsCommand, CommandCategory.ANALYTICS)
        self.register(AnalyticsSummaryCommand, CommandCategory.ANALYTICS)
        self.register(AnalyticsBreakdownCommand, CommandCategory.ANALYTICS)
        self.register(AnalyticsStatusCommand, CommandCategory.ANALYTICS)

        # Documentation commands
        self.register(DocImportCommand, CommandCategory.DOCUMENTATION)
        self.register(DocImportDirCommand, CommandCategory.DOCUMENTATION)
        self.register(DocImportUrlCommand, CommandCategory.DOCUMENTATION)
        self.register(DocListCommand, CommandCategory.DOCUMENTATION)
        self.register(DocPasteCommand, CommandCategory.DOCUMENTATION)
        self.register(DocsCommand, CommandCategory.DOCUMENTATION)
        self.register(FinalizeGenerateCommand, CommandCategory.DOCUMENTATION)
        self.register(FinalizeDocsCommand, CommandCategory.DOCUMENTATION)

        # User commands
        self.register(UserLoginCommand, CommandCategory.USER)
        self.register(UserCreateCommand, CommandCategory.USER)
        self.register(UserLogoutCommand, CommandCategory.USER)
        self.register(UserArchiveCommand, CommandCategory.USER)
        self.register(UserDeleteCommand, CommandCategory.USER)
        self.register(UserRestoreCommand, CommandCategory.USER)

        # System commands
        self.register(ClearCommand, CommandCategory.SYSTEM)
        self.register(ExitCommand, CommandCategory.SYSTEM)
        self.register(BackCommand, CommandCategory.SYSTEM)
        self.register(MenuCommand, CommandCategory.SYSTEM)
        self.register(StatusCommand, CommandCategory.SYSTEM)
        self.register(InfoCommand, CommandCategory.SYSTEM)
        self.register(PromptCommand, CommandCategory.SYSTEM)
        self.register(HelpCommand, CommandCategory.SYSTEM)
        self.register(NLUEnableCommand, CommandCategory.SYSTEM)
        self.register(NLUDisableCommand, CommandCategory.SYSTEM)
        self.register(NLUStatusCommand, CommandCategory.SYSTEM)
        self.register(ModelCommand, CommandCategory.SYSTEM)
        self.register(LLMCommand, CommandCategory.SYSTEM)

        # GitHub commands
        self.register(GithubImportCommand, CommandCategory.WORKFLOW)
        self.register(GithubPullCommand, CommandCategory.WORKFLOW)
        self.register(GithubPushCommand, CommandCategory.WORKFLOW)
        self.register(GithubSyncCommand, CommandCategory.WORKFLOW)

        # Utilities
        self.register(SkillsSetCommand, CommandCategory.SYSTEM)
        self.register(SkillsListCommand, CommandCategory.SYSTEM)
        self.register(MaturityCommand, CommandCategory.ANALYTICS)
        self.register(MaturitySummaryCommand, CommandCategory.ANALYTICS)
        self.register(MaturityHistoryCommand, CommandCategory.ANALYTICS)
        self.register(MaturityStatusCommand, CommandCategory.ANALYTICS)
        self.register(ConvSearchCommand, CommandCategory.CHAT)
        self.register(ConvSummaryCommand, CommandCategory.CHAT)
        self.register(ExplainCommand, CommandCategory.CHAT)
        self.register(SearchCommand, CommandCategory.CHAT)
        self.register(ProjectStatsCommand, CommandCategory.ANALYTICS)
        self.register(ProjectProgressCommand, CommandCategory.ANALYTICS)
        self.register(ProjectStatusCommand, CommandCategory.ANALYTICS)
        self.register(DebugCommand, CommandCategory.DEBUG)
        self.register(LogsCommand, CommandCategory.DEBUG)
        self.register(FileDeleteCommand, CommandCategory.SYSTEM)
        self.register(NoteAddCommand, CommandCategory.KNOWLEDGE)
        self.register(NoteListCommand, CommandCategory.KNOWLEDGE)
        self.register(NoteSearchCommand, CommandCategory.KNOWLEDGE)
        self.register(NoteDeleteCommand, CommandCategory.KNOWLEDGE)
        self.register(SubscriptionStatusCommand, CommandCategory.USER)
        self.register(SubscriptionUpgradeCommand, CommandCategory.USER)
        self.register(SubscriptionDowngradeCommand, CommandCategory.USER)
        self.register(SubscriptionCompareCommand, CommandCategory.USER)
        self.register(SubscriptionTestingModeCommand, CommandCategory.USER)

    def register(
        self,
        command_class: type,
        category: CommandCategory,
        aliases: Optional[List[str]] = None,
        metadata: Optional[CommandMetadata] = None,
        command_name: Optional[str] = None,
        description: str = "",
    ) -> None:
        """
        Register a command class.

        Args:
            command_class: The command class to register
            category: The category for this command
            aliases: Optional list of aliases for this command
            metadata: Optional metadata for the command
            command_name: Optional command name (extracted from class docstring if not provided)
            description: Optional description of the command
        """
        if not issubclass(command_class, BaseCommand):
            raise ValueError(f"{command_class} must inherit from BaseCommand")

        # Extract command name from class docstring or parameter
        if command_name is None:
            # Try to extract from docstring
            doc = command_class.__doc__ or ""
            lines = doc.split("\n")
            if lines:
                # First non-empty line typically contains command name
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("\""):
                        command_name = line.replace("/", "").split("[")[0].strip().lower()
                        break

        # Fallback to class name if extraction failed
        if not command_name:
            command_name = command_class.__name__.replace("Command", "").lower()

        cmd_name = command_name.lower()

        self._commands[cmd_name] = command_class

        # Extract description from docstring if not provided
        if not description:
            doc = command_class.__doc__ or ""
            lines = [line.strip() for line in doc.split("\n") if line.strip()]
            # Skip first line (command name) and get second line or first descriptive line
            for line in lines[1:]:
                if line and not line.startswith("/") and not line.startswith("Usage"):
                    description = line
                    break

        # Register metadata
        if metadata is None:
            metadata = CommandMetadata(
                name=cmd_name,
                description=description,
                category=category,
                aliases=aliases or [],
            )
        else:
            metadata.category = category
            if aliases:
                metadata.aliases = aliases
            if description:
                metadata.description = description

        self._metadata[cmd_name] = metadata

        # Register aliases
        for alias in metadata.aliases:
            self._aliases[alias.lower()] = cmd_name

        # Add to category index
        if category not in self._category_index:
            self._category_index[category] = []
        if cmd_name not in self._category_index[category]:
            self._category_index[category].append(cmd_name)

    def get_command(self, name: str) -> Optional[type]:
        """
        Get a command class by name or alias.

        Args:
            name: Command name or alias

        Returns:
            Command class or None if not found
        """
        name = name.lower()

        # Check direct name
        if name in self._commands:
            return self._commands[name]

        # Check aliases
        if name in self._aliases:
            real_name = self._aliases[name]
            return self._commands[real_name]

        return None

    def get_metadata(self, name: str) -> Optional[CommandMetadata]:
        """
        Get command metadata by name or alias.

        Args:
            name: Command name or alias

        Returns:
            CommandMetadata or None if not found
        """
        name = name.lower()

        if name in self._metadata:
            return self._metadata[name]

        if name in self._aliases:
            real_name = self._aliases[name]
            return self._metadata[real_name]

        return None

    def list_commands(self, category: Optional[CommandCategory] = None) -> Dict[str, CommandMetadata]:
        """
        List all commands, optionally filtered by category.

        Args:
            category: Optional category to filter by

        Returns:
            Dictionary of command names to metadata
        """
        if category is None:
            return self._metadata.copy()

        result = {}
        for cmd_name, metadata in self._metadata.items():
            if metadata.category == category:
                result[cmd_name] = metadata

        return result

    def list_categories(self) -> List[CommandCategory]:
        """List all command categories."""
        return list(self._category_index.keys())

    def get_help(self, name: Optional[str] = None) -> str:
        """
        Get help text for a command or all commands.

        Args:
            name: Optional command name to get help for

        Returns:
            Help text
        """
        if name is None:
            # Return all help
            help_text = ["Socrates Commands\n", "================\n"]

            for category in sorted(self._category_index.keys(), key=lambda c: c.value):
                help_text.append(f"\n{category.value}:")
                help_text.append("-" * (len(category.value) + 1))

                for cmd_name in self._category_index[category]:
                    metadata = self._metadata[cmd_name]
                    help_text.append(f"  {cmd_name:<25} {metadata.description}")

                    if metadata.aliases:
                        help_text.append(
                            f"  {'':<25} (aliases: {', '.join(metadata.aliases)})"
                        )

            return "\n".join(help_text)
        else:
            # Return specific help
            metadata = self.get_metadata(name)
            if not metadata:
                return f"Command '{name}' not found"

            help_lines = [
                f"Command: {metadata.name}",
                f"Description: {metadata.description}",
                f"Category: {metadata.category.value}",
            ]

            if metadata.aliases:
                help_lines.append(f"Aliases: {', '.join(metadata.aliases)}")

            if metadata.example:
                help_lines.append(f"Example: {metadata.example}")

            return "\n".join(help_lines)

    def execute(
        self,
        name: str,
        args: List[str],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a command.

        Args:
            name: Command name or alias
            args: Command arguments
            context: Execution context

        Returns:
            Command result dictionary
        """
        command_class = self.get_command(name)
        if not command_class:
            return {"status": "error", "message": f"Command '{name}' not found"}

        try:
            instance = command_class()
            return instance.execute(args, context)
        except Exception as e:
            return {"status": "error", "message": f"Error executing command: {str(e)}"}


# Global registry instance
_registry: Optional[CommandRegistry] = None


def get_registry() -> CommandRegistry:
    """Get or create the global command registry."""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
    return _registry
