"""
Main application class for Socratic RAG System - Command-Based CLI Interface
"""

import os
import getpass
import datetime
from typing import Optional, Dict, Any
from colorama import Fore, Style

from socratic_system.models import User, ProjectContext
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.ui.command_handler import CommandHandler
from socratic_system.ui.navigation import NavigationStack
from socratic_system.ui.context_display import ContextDisplay
from socratic_system.ui.commands import (
    # System commands
    HelpCommand, ExitCommand, BackCommand, MenuCommand, StatusCommand,
    ClearCommand, PromptCommand, InfoCommand,
    # User commands
    UserLoginCommand, UserCreateCommand, UserLogoutCommand,
    UserArchiveCommand, UserDeleteCommand, UserRestoreCommand,
    # Project commands
    ProjectCreateCommand, ProjectLoadCommand, ProjectListCommand,
    ProjectArchiveCommand, ProjectRestoreCommand, ProjectDeleteCommand,
    # Session commands
    ContinueCommand, DoneCommand, AdvanceCommand, HintCommand,
    # Code commands
    CodeGenerateCommand, CodeDocsCommand,
    # Collaboration commands
    CollabAddCommand, CollabRemoveCommand, CollabListCommand,
    # Document commands
    DocImportCommand, DocImportDirCommand, DocListCommand,
    # Note commands
    NoteAddCommand, NoteListCommand, NoteSearchCommand, NoteDeleteCommand,
    # Conversation commands
    ConvSearchCommand, ConvSummaryCommand,
    # Statistics commands
    ProjectStatsCommand, ProjectProgressCommand, ProjectStatusCommand,
    # Debug commands
    DebugCommand, LogsCommand,
)


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

    def start(self) -> None:
        """Start the Socratic RAG System"""
        self._print_banner()

        # Get API key
        api_key = self._get_api_key()
        if not api_key:
            print(f"{Fore.RED}No API key provided. Exiting...")
            return

        try:
            # Initialize orchestrator
            print(f"\n{Fore.YELLOW}Initializing system...{Style.RESET_ALL}")
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
        api_key = os.getenv('API_KEY_CLAUDE')
        if not api_key:
            print(f"{Fore.YELLOW}Claude API key not found in environment.")
            api_key = getpass.getpass("Please enter your Claude API key: ")
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

            if choice == '1' or choice.startswith('/user login'):
                result = UserLoginCommand().execute([], self._get_context())
                if result['status'] == 'success':
                    self.current_user = result['data']['user']
                    self.context_display.set_context(user=self.current_user)
                    return True
                else:
                    if result.get('message'):
                        print(result['message'])

            elif choice == '2' or choice.startswith('/user create'):
                result = UserCreateCommand().execute([], self._get_context())
                if result['status'] == 'success':
                    self.current_user = result['data']['user']
                    self.context_display.set_context(user=self.current_user)
                    return True
                else:
                    if result.get('message'):
                        print(result['message'])

            elif choice == '3' or choice == '/exit':
                print(f"\n{Fore.GREEN}Thank you for using Socratic RAG System")
                print("..τω Ασκληπιώ οφείλομεν αλετρυόνα, απόδοτε και μη αμελήσετε..\n")
                return False

            else:
                print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")

    def _register_commands(self) -> None:
        """Register all available commands"""
        # System commands
        self.command_handler.register_command(HelpCommand(), aliases=['h', '?'])
        self.command_handler.register_command(ExitCommand(), aliases=['quit', 'q'])
        self.command_handler.register_command(BackCommand())
        self.command_handler.register_command(MenuCommand())
        self.command_handler.register_command(StatusCommand())
        self.command_handler.register_command(ClearCommand(), aliases=['cls'])
        self.command_handler.register_command(PromptCommand())
        self.command_handler.register_command(InfoCommand())

        # User commands
        self.command_handler.register_command(UserLoginCommand())
        self.command_handler.register_command(UserCreateCommand())
        self.command_handler.register_command(UserLogoutCommand())
        self.command_handler.register_command(UserArchiveCommand())
        self.command_handler.register_command(UserDeleteCommand())
        self.command_handler.register_command(UserRestoreCommand())

        # Project commands
        self.command_handler.register_command(ProjectCreateCommand())
        self.command_handler.register_command(ProjectLoadCommand())
        self.command_handler.register_command(ProjectListCommand())
        self.command_handler.register_command(ProjectArchiveCommand())
        self.command_handler.register_command(ProjectRestoreCommand())
        self.command_handler.register_command(ProjectDeleteCommand())

        # Session commands
        self.command_handler.register_command(ContinueCommand())
        self.command_handler.register_command(DoneCommand())
        self.command_handler.register_command(AdvanceCommand())
        self.command_handler.register_command(HintCommand())

        # Code commands
        self.command_handler.register_command(CodeGenerateCommand())
        self.command_handler.register_command(CodeDocsCommand())

        # Collaboration commands
        self.command_handler.register_command(CollabAddCommand())
        self.command_handler.register_command(CollabRemoveCommand())
        self.command_handler.register_command(CollabListCommand())

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

        # Debug commands
        self.command_handler.register_command(DebugCommand())
        self.command_handler.register_command(LogsCommand())

    def _command_loop(self) -> None:
        """Main command processing loop"""
        while True:
            try:
                # Display context
                prompt = self.context_display.get_prompt()
                user_input = input(prompt).strip()

                if not user_input:
                    continue

                # Execute command
                result = self.command_handler.execute(user_input, self._get_context())

                # Handle result
                if result['status'] == 'exit':
                    break
                elif result['status'] == 'error':
                    if result.get('message'):
                        print(result['message'])
                elif result['status'] == 'success':
                    if result.get('message'):
                        print(result['message'])
                    # Handle navigation context changes
                    if result.get('data', {}).get('nav_context'):
                        nav_context = result['data']['nav_context']
                        # Could implement navigation here if needed
                elif result['status'] == 'info':
                    if result.get('message'):
                        print(result['message'])
                elif result['status'] != 'idle':
                    # Unknown status
                    print(f"{Fore.YELLOW}Command executed with status: {result['status']}{Style.RESET_ALL}")
                    if result.get('message'):
                        print(result['message'])

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Interrupted. Type '/exit' to quit.{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")

    def _get_context(self) -> Dict[str, Any]:
        """Get the current application context for commands"""
        return {
            'user': self.current_user,
            'project': self.current_project,
            'orchestrator': self.orchestrator,
            'nav_stack': self.nav_stack,
            'app': self
        }


def main():
    """Main entry point for the application"""
    app = SocraticRAGSystem()
    app.start()


if __name__ == '__main__':
    main()
