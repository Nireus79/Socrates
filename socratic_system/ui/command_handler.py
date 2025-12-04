"""Command handler for parsing and routing user input"""

import shlex
from typing import Dict, Any, List, Optional, Type
from colorama import Fore, Style
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
            user_input: Raw user input string
            context: Application context with user, project, orchestrator, etc.

        Returns:
            Command result dictionary with status and optional message/data
        """
        user_input = user_input.strip()

        if not user_input:
            return {'status': 'idle', 'message': ''}

        # Handle slash commands
        if user_input.startswith('/'):
            return self._execute_command(user_input[1:], context)
        else:
            # Try parsing without slash
            return self._execute_command(user_input, context)

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
        try:
            parts = shlex.split(command_input)
        except ValueError as e:
            return {
                'status': 'error',
                'message': f"{Fore.RED}Parse error: {str(e)}{Style.RESET_ALL}"
            }

        if not parts:
            return {'status': 'idle', 'message': ''}

        # Try to match multi-word commands (up to 3 words)
        command_name = None
        args = parts

        # Try 3-word command first (e.g., "project archive restore")
        if len(parts) >= 3:
            three_word = ' '.join(parts[:3]).lower()
            if three_word in self.commands:
                command_name = three_word
                args = parts[3:]

        # Try 2-word command (e.g., "project list")
        if command_name is None and len(parts) >= 2:
            two_word = ' '.join(parts[:2]).lower()
            if two_word in self.commands:
                command_name = two_word
                args = parts[2:]

        # Try 1-word command (e.g., "help")
        if command_name is None:
            command_name = parts[0].lower()
            args = parts[1:]

        # Resolve aliases
        if command_name in self.aliases:
            command_name = self.aliases[command_name]

        # Look up command
        if command_name not in self.commands:
            return {
                'status': 'error',
                'message': f"{Fore.RED}Unknown command: {command_name}{Style.RESET_ALL}\n"
                           f"Type '/help' for a list of available commands.{Style.RESET_ALL}"
            }

        command = self.commands[command_name]

        # Execute command
        try:
            result = command.execute(args, context)
            return result
        except Exception as e:
            return {
                'status': 'error',
                'message': f"{Fore.RED}Command error: {str(e)}{Style.RESET_ALL}"
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
        return {
            name: cmd for name, cmd in self.commands.items()
            if name.startswith(prefix)
        }

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

    def _print_all_help(self) -> None:
        """Print help for all commands organized by category."""
        print(f"\n{Fore.CYAN}{'═' * 60}")
        print("Socratic RAG System - Available Commands")
        print('═' * 60)
        print(f"{Style.RESET_ALL}\n")

        # Organize commands by first part of name (category)
        categories: Dict[str, List[str]] = {}

        for name in sorted(self.commands.keys()):
            parts = name.split()
            category = parts[0] if parts else 'system'

            if category not in categories:
                categories[category] = []
            categories[category].append(name)

        # Print organized commands
        for category in sorted(categories.keys()):
            print(f"{Fore.YELLOW}{category.upper()} Commands:{Style.RESET_ALL}")

            for command_name in sorted(categories[category]):
                cmd = self.commands[command_name]
                description = cmd.description or "(no description)"
                usage = cmd.usage or command_name

                # Format with proper alignment
                print(f"  {Fore.CYAN}{usage:30}{Style.RESET_ALL} - {description}")

            print()

        # Print aliases if any
        if self.aliases:
            print(f"{Fore.YELLOW}Aliases:{Style.RESET_ALL}")
            for alias, target in sorted(self.aliases.items()):
                print(f"  {Fore.CYAN}{alias:15}{Style.RESET_ALL} → {target}")
            print()

        print(f"For detailed help on a command, use: {Fore.GREEN}/help <command>{Style.RESET_ALL}")

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
