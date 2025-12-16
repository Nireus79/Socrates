"""
Main application class for Socratic RAG System - Command-Based CLI Interface
"""

import datetime
import getpass
import os
from typing import Any, Dict, Optional

from colorama import Fore, Style

from socratic_system.models import ProjectContext, User
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.ui.command_handler import CommandHandler
from socratic_system.ui.commands import (  # Analytics commands; Code commands; Finalize commands; Collaboration commands; Skills commands; Session commands; Conversation commands; Debug commands; Document commands; System commands; Note commands; Project commands; Statistics commands; User commands; Subscription commands
    AdvanceCommand,
    AnalyticsAnalyzeCommand,
    AnalyticsBreakdownCommand,
    AnalyticsRecommendCommand,
    AnalyticsStatusCommand,
    AnalyticsSummaryCommand,
    AnalyticsTrendsCommand,
    BackCommand,
    ChatCommand,
    ClearCommand,
    CodeDocsCommand,
    CodeGenerateCommand,
    CollabAddCommand,
    CollabListCommand,
    CollabRemoveCommand,
    CollabRoleCommand,
    ConvSearchCommand,
    ConvSummaryCommand,
    DebugCommand,
    DocImportCommand,
    DocImportDirCommand,
    DocListCommand,
    DoneCommand,
    ExitCommand,
    ExplainCommand,
    FinalizeDocsCommand,
    FinalizeGenerateCommand,
    HelpCommand,
    HintCommand,
    InfoCommand,
    LLMCommand,
    LogsCommand,
    MaturityCommand,
    MaturityHistoryCommand,
    MaturityStatusCommand,
    MaturitySummaryCommand,
    MenuCommand,
    ModeCommand,
    ModelCommand,
    NLUDisableCommand,
    NLUEnableCommand,
    NLUStatusCommand,
    NoteAddCommand,
    NoteDeleteCommand,
    NoteListCommand,
    NoteSearchCommand,
    ProjectArchiveCommand,
    ProjectCreateCommand,
    ProjectDeleteCommand,
    ProjectListCommand,
    ProjectLoadCommand,
    ProjectProgressCommand,
    ProjectRestoreCommand,
    ProjectStatsCommand,
    ProjectStatusCommand,
    PromptCommand,
    SearchCommand,
    SkillsListCommand,
    SkillsSetCommand,
    StatusCommand,
    SubscriptionCompareCommand,
    SubscriptionDowngradeCommand,
    SubscriptionStatusCommand,
    SubscriptionTestingModeCommand,
    SubscriptionUpgradeCommand,
    UserArchiveCommand,
    UserCreateCommand,
    UserDeleteCommand,
    UserLoginCommand,
    UserLogoutCommand,
    UserRestoreCommand,
)
from socratic_system.ui.context_display import ContextDisplay
from socratic_system.ui.navigation import NavigationStack
from socratic_system.ui.nlu_handler import NLUHandler, SuggestionDisplay


class SocraticRAGSystem:
    """Main application class for Socratic RAG System with command-based interface"""

    def __init__(self):
        """Initialize the application"""
        self.orchestrator: Optional[AgentOrchestrator] = None
        self.current_user: Optional[User] = None
        self.current_project: Optional[ProjectContext] = None
        self.session_start: datetime.datetime = datetime.datetime.now()

        # Command system components
        self.command_handler: Optional[CommandHandler] = None
        self.nav_stack: Optional[NavigationStack] = None
        self.context_display: Optional[ContextDisplay] = None
        self.nlu_handler: Optional[NLUHandler] = None

    def start(self) -> None:
        """Start the Socratic RAG System"""
        self._print_banner()

        # Get API key or choose authentication mode
        api_key = self._get_api_key()
        if not api_key:
            print(f"{Fore.RED}No API key provided. Exiting...")
            return

        try:
            # Initialize orchestrator
            print(f"\n{Fore.YELLOW}Initializing system...{Style.RESET_ALL}")
            # In subscription mode, use a placeholder API key - actual auth happens during user login
            if api_key == "subscription_mode":
                # For subscription mode, we'll use a dummy key initially
                # It will be validated during user authentication
                self.orchestrator = AgentOrchestrator("subscription_placeholder_key")
            else:
                self.orchestrator = AgentOrchestrator(api_key)

            # Initialize command system components
            self.command_handler = CommandHandler()
            self.nav_stack = NavigationStack()
            self.context_display = ContextDisplay()

            # Register all commands
            self._register_commands()

            # Authenticate user
            if not self._authenticate_user():
                return

            # Enable NLU after login
            self.nlu_handler = NLUHandler(self.orchestrator.claude_client, self.command_handler)
            print(f"{Fore.GREEN}[OK] Natural language understanding enabled{Style.RESET_ALL}")

            # Start command loop
            self._command_loop()

        except Exception as e:
            print(f"{Fore.RED}System error: {e}{Style.RESET_ALL}")

    def _print_banner(self) -> None:
        """Display the application banner"""
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("╔═══════════════════════════════════════════════╗")
        print("║             Socrates RAG System               ║")
        print("║Ουδέν οίδα, ούτε διδάσκω τι, αλλά διαπορώ μόνον║")
        print("╚═══════════════════════════════════════════════╝")
        print(f"{Style.RESET_ALL}")

    def _get_api_key(self) -> Optional[str]:
        """Get Claude API key from environment or user input"""
        api_key = os.getenv("API_KEY_CLAUDE")
        if not api_key:
            print(f"\n{Fore.CYAN}API Configuration{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Choose how to authenticate with Claude:{Style.RESET_ALL}")
            print("1. Use API Key directly")
            print("2. Use Subscription (requires valid account)")

            choice = input(f"\n{Fore.WHITE}Select option (1 or 2): ").strip()

            if choice == "2":
                # Subscription mode - will be handled by authenticating user first
                print(
                    f"{Fore.CYAN}Using subscription mode - authenticate with your account{Style.RESET_ALL}"
                )
                # Store a marker that we're in subscription mode
                os.environ["SOCRATES_SUBSCRIPTION_MODE"] = "1"
                # Return a placeholder - actual API key will be obtained from orchestrator
                return "subscription_mode"
            else:
                # API Key mode
                print(
                    f"{Fore.CYAN}Paste your Claude API key (or set API_KEY_CLAUDE env var):{Style.RESET_ALL}"
                )
                api_key = getpass.getpass("Claude API Key: ")
                if api_key:
                    os.environ["SOCRATES_SUBSCRIPTION_MODE"] = "0"
        return api_key

    def _authenticate_user(self) -> bool:
        """Handle user login or registration"""
        print(f"\n{Fore.CYAN}Authentication{Style.RESET_ALL}\n")

        while True:
            print(f"{Fore.YELLOW}Options:{Style.RESET_ALL}")
            print("1. Login with existing account (/user login)")
            print("2. Create new account (/user create)")
            print("3. Exit (/exit)")

            choice = input(f"\n{Fore.WHITE}Choose option (1-3): ").strip()

            if choice == "1" or choice.startswith("/user login"):
                result = UserLoginCommand().execute([], self._get_context())
                if result["status"] == "success":
                    self.current_user = result["data"]["user"]
                    self.context_display.set_context(user=self.current_user)
                    self._apply_testing_mode_if_enabled()
                    return True
                else:
                    if result.get("message"):
                        print(result["message"])

            elif choice == "2" or choice.startswith("/user create"):
                result = UserCreateCommand().execute([], self._get_context())
                if result["status"] == "success":
                    self.current_user = result["data"]["user"]
                    self.context_display.set_context(user=self.current_user)
                    self._apply_testing_mode_if_enabled()
                    return True
                else:
                    if result.get("message"):
                        print(result["message"])

            elif choice == "3" or choice == "/exit":
                print(f"\n{Fore.GREEN}Thank you for using Socratic RAG System")
                print("..τω Ασκληπιώ οφείλομεν αλετρυόνα, απόδοτε και μη αμελήσετε..\n")
                return False

            else:
                print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")

    def _apply_testing_mode_if_enabled(self) -> None:
        """Enable testing mode for current user if --testing flag was provided."""
        if os.getenv("SOCRATES_TESTING_MODE") == "1" and self.current_user:
            if not self.current_user.testing_mode:
                self.current_user.testing_mode = True
                self.orchestrator.database.save_user(self.current_user)
                print(f"\n{Fore.GREEN}[OK] Testing mode ENABLED{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}All monetization restrictions bypassed!{Style.RESET_ALL}\n")

    def _register_commands(self) -> None:
        """Register all available commands"""
        # System commands
        self.command_handler.register_command(HelpCommand(), aliases=["h", "?"])
        self.command_handler.register_command(ExitCommand(), aliases=["quit", "q"])
        self.command_handler.register_command(BackCommand())
        self.command_handler.register_command(MenuCommand())
        self.command_handler.register_command(StatusCommand())
        self.command_handler.register_command(ClearCommand(), aliases=["cls"])
        self.command_handler.register_command(PromptCommand())
        self.command_handler.register_command(InfoCommand())
        self.command_handler.register_command(ModelCommand())
        self.command_handler.register_command(LLMCommand(), aliases=["llm"])

        # NLU control commands
        self.command_handler.register_command(NLUEnableCommand())
        self.command_handler.register_command(NLUDisableCommand())
        self.command_handler.register_command(NLUStatusCommand())

        # User commands
        self.command_handler.register_command(UserLoginCommand())
        self.command_handler.register_command(UserCreateCommand())
        self.command_handler.register_command(UserLogoutCommand())
        self.command_handler.register_command(UserArchiveCommand())
        self.command_handler.register_command(UserDeleteCommand())
        self.command_handler.register_command(UserRestoreCommand())

        # Subscription commands
        self.command_handler.register_command(SubscriptionStatusCommand())
        self.command_handler.register_command(SubscriptionUpgradeCommand())
        self.command_handler.register_command(SubscriptionDowngradeCommand())
        self.command_handler.register_command(SubscriptionCompareCommand())
        self.command_handler.register_command(SubscriptionTestingModeCommand())

        # Project commands
        self.command_handler.register_command(ProjectCreateCommand())
        self.command_handler.register_command(ProjectLoadCommand())
        self.command_handler.register_command(ProjectListCommand())
        self.command_handler.register_command(ProjectArchiveCommand())
        self.command_handler.register_command(ProjectRestoreCommand())
        self.command_handler.register_command(ProjectDeleteCommand())

        # Session commands
        self.command_handler.register_command(ChatCommand())
        self.command_handler.register_command(ModeCommand())
        self.command_handler.register_command(DoneCommand())
        self.command_handler.register_command(AdvanceCommand())
        self.command_handler.register_command(HintCommand())

        # Code commands
        self.command_handler.register_command(CodeGenerateCommand())
        self.command_handler.register_command(CodeDocsCommand())

        # Finalize commands (project type-agnostic artifact generation)
        self.command_handler.register_command(FinalizeGenerateCommand())
        self.command_handler.register_command(FinalizeDocsCommand())

        # Collaboration commands
        self.command_handler.register_command(CollabAddCommand())
        self.command_handler.register_command(CollabRemoveCommand())
        self.command_handler.register_command(CollabListCommand())
        self.command_handler.register_command(CollabRoleCommand())

        # Skills commands
        self.command_handler.register_command(SkillsSetCommand())
        self.command_handler.register_command(SkillsListCommand())

        # Document commands
        self.command_handler.register_command(DocImportCommand())
        self.command_handler.register_command(DocImportDirCommand())
        self.command_handler.register_command(DocListCommand())

        # Note commands
        self.command_handler.register_command(NoteAddCommand())
        self.command_handler.register_command(NoteListCommand())
        self.command_handler.register_command(NoteSearchCommand())
        self.command_handler.register_command(NoteDeleteCommand())

        # Conversation commands
        self.command_handler.register_command(ConvSearchCommand())
        self.command_handler.register_command(ConvSummaryCommand())

        # Statistics commands
        self.command_handler.register_command(ProjectStatsCommand())
        self.command_handler.register_command(ProjectProgressCommand())
        self.command_handler.register_command(ProjectStatusCommand())

        # Maturity tracking commands
        self.command_handler.register_command(MaturityCommand())
        self.command_handler.register_command(MaturitySummaryCommand())
        self.command_handler.register_command(MaturityHistoryCommand())
        self.command_handler.register_command(MaturityStatusCommand())

        # Analytics commands
        self.command_handler.register_command(
            AnalyticsAnalyzeCommand(self.orchestrator), aliases=["aa"]
        )
        self.command_handler.register_command(
            AnalyticsRecommendCommand(self.orchestrator), aliases=["ar"]
        )
        self.command_handler.register_command(
            AnalyticsTrendsCommand(self.orchestrator), aliases=["at"]
        )
        self.command_handler.register_command(
            AnalyticsSummaryCommand(self.orchestrator), aliases=["as"]
        )
        self.command_handler.register_command(
            AnalyticsBreakdownCommand(self.orchestrator), aliases=["abd"]
        )
        self.command_handler.register_command(
            AnalyticsStatusCommand(self.orchestrator), aliases=["ast"]
        )

        # Debug commands
        self.command_handler.register_command(DebugCommand())
        self.command_handler.register_command(LogsCommand())

        # Query/Answer commands
        self.command_handler.register_command(ExplainCommand())
        self.command_handler.register_command(SearchCommand())

    def _handle_command_result(self, result: Dict[str, Any]) -> bool:
        """
        Handle command execution result and display appropriate messages.

        Args:
            result: Command result dictionary with status and message

        Returns:
            True if command loop should continue, False if exit requested
        """
        if result["status"] == "exit":
            return False
        elif result["status"] == "error":
            if result.get("message"):
                print(result["message"])
        elif result["status"] == "success":
            if result.get("message"):
                print(result["message"])

            data = result.get("data", {})

            # Handle project entry (push to navigation stack)
            # Note: project_commands.py already sets app.current_project
            project = data.get("project")
            if project:
                # Entering a project context - push to navigation stack
                if self.nav_stack:
                    self.nav_stack.push("project_view", {"project_id": project.project_id})

            # Handle navigation context changes (from /back, /menu commands)
            nav_context = data.get("nav_context")
            if nav_context:
                # Navigation command returned, handle context change
                if nav_context == "main_menu":
                    self.current_project = None
                # State restoration could be added here if needed

            # Check if session ended (done command, menu command, back command)
            if data.get("session_ended"):
                self.current_project = None
        elif result["status"] == "info":
            if result.get("message"):
                print(result["message"])
        elif result["status"] != "idle":
            # Unknown status
            print(f"{Fore.YELLOW}Command executed with status: {result['status']}{Style.RESET_ALL}")
            if result.get("message"):
                print(result["message"])
        return True

    def _command_loop(self) -> None:
        """Main command processing loop"""
        while True:
            try:
                # Display context
                prompt = self.context_display.get_prompt()
                user_input = input(prompt).strip()

                if not user_input:
                    continue

                # Execute command (with NLU support)
                result = self._process_input_with_nlu(user_input, self._get_context())

                # Handle result
                if not self._handle_command_result(result):
                    break

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Interrupted. Type '/exit' to quit.{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")

    def _process_input_with_nlu(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process input with NLU support"""
        # Skip NLU if not initialized or input starts with /
        if not self.nlu_handler or self.nlu_handler.should_skip_nlu(user_input):
            return self.command_handler.execute(user_input, context)

        # Interpret with NLU
        nlu_result = self.nlu_handler.interpret(user_input, context)

        if nlu_result["status"] == "success":
            # High confidence - execute directly
            command = nlu_result["command"]
            if nlu_result.get("message"):
                print(nlu_result["message"])
            return self.command_handler.execute(command, context)

        elif nlu_result["status"] == "suggestions":
            # Medium confidence - show suggestions
            if nlu_result.get("message"):
                print(nlu_result["message"])
            suggestions = nlu_result.get("suggestions", [])
            selected = SuggestionDisplay.show_suggestions(suggestions)

            if selected:
                print(f"{Fore.CYAN}[NLU] Executing: {selected}{Style.RESET_ALL}")
                return self.command_handler.execute(selected, context)
            return {"status": "idle"}

        else:  # no_match or error
            return {
                "status": "error",
                "message": nlu_result.get("message", "Couldn't understand that."),
            }

    def _get_context(self) -> Dict[str, Any]:
        """Get the current application context for commands"""
        return {
            "user": self.current_user,
            "project": self.current_project,
            "orchestrator": self.orchestrator,
            "nav_stack": self.nav_stack,
            "app": self,
        }


def main():
    """Main entry point for the application"""
    app = SocraticRAGSystem()
    app.start()


if __name__ == "__main__":
    main()
