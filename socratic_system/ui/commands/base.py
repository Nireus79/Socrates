"""Base command class for all CLI commands"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from colorama import Fore, Style


class BaseCommand(ABC):
    """
    Abstract base class for all CLI commands.

    All command classes must inherit from this and implement:
    - execute(args, context) - Main command logic
    """

    def __init__(self, name: str, description: str = "", usage: str = ""):
        """
        Initialize base command.

        Args:
            name: Command name (e.g., 'project')
            description: Short description of what the command does
            usage: Usage string (e.g., 'project create <name>')
        """
        self.name = name
        self.description = description
        self.usage = usage
        self.subcommands: Dict[str, 'BaseCommand'] = {}

    @abstractmethod
    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the command with given arguments.

        Args:
            args: List of command arguments (excluding the command name itself)
            context: Application context containing:
                - user: Current User object
                - project: Current ProjectContext object (may be None)
                - orchestrator: AgentOrchestrator instance
                - nav_stack: NavigationStack instance
                - app: SocraticRAGSystem instance

        Returns:
            Dictionary with keys:
                - status: 'success', 'error', 'exit', or other status codes
                - message: Human-readable message (optional)
                - data: Command-specific data (optional)
        """
        pass

    def register_subcommand(self, subcommand: 'BaseCommand') -> None:
        """Register a subcommand."""
        self.subcommands[subcommand.name] = subcommand

    def get_help(self) -> str:
        """
        Get help text for this command.

        Returns:
            Formatted help string
        """
        help_text = f"{Fore.CYAN}{self.name}{Style.RESET_ALL}"
        if self.usage:
            help_text += f"\n  Usage: {self.usage}"
        if self.description:
            help_text += f"\n  {self.description}"

        if self.subcommands:
            help_text += f"\n{Fore.YELLOW}\n  Subcommands:{Style.RESET_ALL}"
            for name, cmd in self.subcommands.items():
                help_text += f"\n    {Fore.CYAN}{name:15}{Style.RESET_ALL} - {cmd.description}"

        return help_text

    def validate_args(self, args: List[str], min_count: int = 0, max_count: Optional[int] = None) -> bool:
        """
        Validate argument count.

        Args:
            args: Arguments to validate
            min_count: Minimum number of arguments required
            max_count: Maximum number of arguments allowed (None for unlimited)

        Returns:
            True if valid, False otherwise
        """
        if len(args) < min_count:
            return False
        if max_count is not None and len(args) > max_count:
            return False
        return True

    def error(self, message: str) -> Dict[str, Any]:
        """
        Create an error response.

        Args:
            message: Error message

        Returns:
            Error response dictionary
        """
        return {
            'status': 'error',
            'message': f"{Fore.RED}Error: {message}{Style.RESET_ALL}"
        }

    def success(self, message: str = "", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a success response.

        Args:
            message: Success message
            data: Additional data to include in response

        Returns:
            Success response dictionary
        """
        response = {'status': 'success'}
        if message:
            response['message'] = f"{Fore.GREEN}{message}{Style.RESET_ALL}"
        if data:
            response['data'] = data
        return response

    def info(self, message: str) -> Dict[str, Any]:
        """
        Create an info response (displays message but doesn't require action).

        Args:
            message: Info message

        Returns:
            Info response dictionary
        """
        return {
            'status': 'info',
            'message': f"{Fore.CYAN}{message}{Style.RESET_ALL}"
        }

    def require_project(self, context: Dict[str, Any]) -> bool:
        """
        Check if a project is currently loaded.

        Args:
            context: Application context

        Returns:
            True if project is loaded, False otherwise
        """
        return context.get('project') is not None

    def require_user(self, context: Dict[str, Any]) -> bool:
        """
        Check if a user is currently logged in.

        Args:
            context: Application context

        Returns:
            True if user is logged in, False otherwise
        """
        return context.get('user') is not None

    def print_header(self, title: str) -> None:
        """Print a formatted section header."""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{title:^50}")
        print(f"{'=' * 50}{Style.RESET_ALL}\n")

    def print_section(self, title: str) -> None:
        """Print a formatted subsection header."""
        print(f"\n{Fore.YELLOW}{title}{Style.RESET_ALL}")
        print(f"{'-' * len(title)}")

    def print_success(self, message: str) -> None:
        """Print a success message."""
        print(f"{Fore.GREEN}[OK] {message}{Style.RESET_ALL}")

    def print_error(self, message: str) -> None:
        """Print an error message."""
        print(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")

    def print_info(self, message: str) -> None:
        """Print an info message."""
        print(f"{Fore.CYAN}[INFO] {message}{Style.RESET_ALL}")

    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        print(f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}")
