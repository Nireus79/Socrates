"""Command handler for parsing and routing user input"""

import platform
import shlex
from typing import Any, Dict, List, Optional

from colorama import Fore, Style

from socratic_system.subscription.checker import SubscriptionChecker
from socratic_system.ui.commands.base import BaseCommand


class CommandHandler:
    """
    Central command processor for the CLI interface.

    Responsibilities:
    - Parse user input into commands and arguments
    - Maintain registry of available commands
    - Route commands to appropriate handlers
    - Handle errors and provide feedback
    """

    def __init__(self):
        """Initialize command handler and command registry."""
        self.commands: Dict[str, BaseCommand] = {}
        self.aliases: Dict[str, str] = {}  # Map alias to command name

    def register_command(self, command: BaseCommand, aliases: Optional[List[str]] = None) -> None:
        """
        Register a command with the handler.

        Args:
            command: BaseCommand instance to register
            aliases: Optional list of aliases for the command
        """
        self.commands[command.name] = command

        if aliases:
            for alias in aliases:
                self.aliases[alias] = command.name

    def register_commands(self, commands: List[BaseCommand]) -> None:
        """
        Register multiple commands at once.

        Args:
            commands: List of BaseCommand instances
        """
        for command in commands:
            self.register_command(command)

    def execute(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and execute a command from user input.

        Args:
            user_input: Raw user input string (must start with /)
            context: Application context with user, project, orchestrator, etc.

        Returns:
            Command result dictionary with status and optional message/data
        """
        user_input = user_input.strip()

        if not user_input:
            return {"status": "idle", "message": ""}

        # Commands MUST start with /
        if not user_input.startswith("/"):
            return {
                "status": "error",
                "message": f"{Fore.YELLOW}Commands must start with '/' (e.g., /help){Style.RESET_ALL}\n"
                f"Type '/help' to see available commands.",
            }

        return self._execute_command(user_input[1:], context)

    def _match_command(self, parts: List[str]) -> tuple:
        """
        Match user input parts to a registered command.

        Args:
            parts: Parsed command input parts

        Returns:
            Tuple of (command_name, args)
        """
        # Try 3-word command first (e.g., "project archive restore")
        if len(parts) >= 3:
            three_word = " ".join(parts[:3]).lower()
            if three_word in self.commands:
                return three_word, parts[3:]

        # Try 2-word command (e.g., "project list")
        if len(parts) >= 2:
            two_word = " ".join(parts[:2]).lower()
            if two_word in self.commands:
                return two_word, parts[2:]

        # Try 1-word command (e.g., "help")
        command_name = parts[0].lower()
        args = parts[1:]
        return command_name, args

    def _execute_command(self, command_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to parse and execute a command.

        Args:
            command_input: Input string without leading slash
            context: Application context

        Returns:
            Command result dictionary
        """
        # Parse the command and arguments
        # Use posix=False on Windows to prevent backslashes in paths from being
        # interpreted as escape characters (e.g., C:\Users\file.pdf)
        try:
            posix_mode = platform.system() != "Windows"
            parts = shlex.split(command_input, posix=posix_mode)
        except ValueError as e:
            return {
                "status": "error",
                "message": f"{Fore.RED}Parse error: {str(e)}{Style.RESET_ALL}",
            }

        if not parts:
            return {"status": "idle", "message": ""}

        # Match command name and args
        command_name, args = self._match_command(parts)

        # Resolve aliases
        if command_name in self.aliases:
            command_name = self.aliases[command_name]

        # Look up command
        if command_name not in self.commands:
            return {
                "status": "error",
                "message": f"{Fore.RED}Unknown command: {command_name}{Style.RESET_ALL}\n"
                f"Type '/help' for a list of available commands.{Style.RESET_ALL}",
            }

        command = self.commands[command_name]

        # NEW: Check subscription access before executing
        user = context.get("user")
        if user:
            has_access, error_message = SubscriptionChecker.check_command_access(user, command.name)
            if not has_access:
                return {
                    "status": "error",
                    "message": error_message,
                }

        # Execute command
        try:
            result = command.execute(args, context)
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"{Fore.RED}Command error: {str(e)}{Style.RESET_ALL}",
            }

    def get_command(self, name: str) -> Optional[BaseCommand]:
        """
        Get a command by name.

        Args:
            name: Command name

        Returns:
            BaseCommand instance or None if not found
        """
        if name in self.aliases:
            name = self.aliases[name]

        return self.commands.get(name)

    def get_all_commands(self) -> Dict[str, BaseCommand]:
        """
        Get all registered commands.

        Returns:
            Dictionary of command_name -> BaseCommand
        """
        return self.commands.copy()

    def get_commands_by_prefix(self, prefix: str) -> Dict[str, BaseCommand]:
        """
        Get all commands starting with a prefix.

        Args:
            prefix: Command name prefix

        Returns:
            Dictionary of matching command_name -> BaseCommand
        """
        prefix = prefix.lower()
        return {name: cmd for name, cmd in self.commands.items() if name.startswith(prefix)}

    def print_help(self, command_name: Optional[str] = None) -> None:
        """
        Print help for a specific command or all commands.

        Args:
            command_name: Specific command to get help for, or None for all
        """
        if command_name:
            command_name = command_name.lower()

            # Resolve aliases
            if command_name in self.aliases:
                command_name = self.aliases[command_name]

            if command_name in self.commands:
                print(self.commands[command_name].get_help())
            else:
                print(f"{Fore.RED}Command not found: {command_name}{Style.RESET_ALL}")
        else:
            # Print all commands organized by category
            self._print_all_help()

    def _print_help_category(self, category: str, commands_in_category: List[str]) -> None:
        """
        Print help for a single command category.

        Args:
            category: Category name
            commands_in_category: List of command names in the category
        """
        print(f"\n{Fore.GREEN}► {category.upper()} COMMANDS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 68}{Style.RESET_ALL}")

        for command_name in sorted(commands_in_category):
            cmd = self.commands[command_name]
            description = cmd.description or "(no description)"
            usage = cmd.usage or command_name

            cmd_display = f"/{usage}"
            print(f"  {Fore.CYAN}{cmd_display:<40}{Style.RESET_ALL}  {description}")

        print()

    def _print_all_help(self) -> None:
        """Print help for all commands organized by category."""
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(" " * 15 + "SOCRATIC RAG SYSTEM - COMMANDS")
        print("=" * 70)
        print(f"{Style.RESET_ALL}")

        # Organize commands by first part of name (category)
        categories: Dict[str, List[str]] = {}
        category_order = [
            "user",
            "project",
            "session",
            "collab",
            "maturity",
            "analytics",
            "finalize",
            "code",
            "docs",
            "note",
            "conv",
            "help",
            "debug",
        ]

        for name in sorted(self.commands.keys()):
            parts = name.split()
            category = parts[0] if parts else "system"

            if category not in categories:
                categories[category] = []
            categories[category].append(name)

        # Print commands organized by category
        for category in category_order:
            if category not in categories:
                continue
            self._print_help_category(category, categories[category])

        # Print any remaining categories not in the predefined order
        for category in sorted(categories.keys()):
            if category in category_order:
                continue
            self._print_help_category(category, categories[category])

        # Print aliases if any
        if self.aliases:
            print(f"\n{Fore.GREEN}► ALIASES{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-' * 68}{Style.RESET_ALL}")
            for alias, target in sorted(self.aliases.items()):
                print(f"  {Fore.YELLOW}/{alias:<39}{Style.RESET_ALL}  (shortcut for /{target})")
            print()

        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(
            f"Usage: Type a command starting with {Fore.GREEN}'{Style.RESET_ALL} (e.g., {Fore.GREEN}/help project list{Style.RESET_ALL})"
        )
        print(
            f"Help:  Type {Fore.GREEN}/help <command>{Style.RESET_ALL} for more details on a command"
        )
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

    def is_valid_command(self, command_name: str) -> bool:
        """
        Check if a command is registered.

        Args:
            command_name: Command name to check

        Returns:
            True if command exists, False otherwise
        """
        if command_name in self.aliases:
            command_name = self.aliases[command_name]

        return command_name in self.commands
