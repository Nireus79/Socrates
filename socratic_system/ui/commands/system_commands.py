"""
System commands for CLI control and navigation.

This module provides essential system-level commands for application control:
- Help: Display command documentation and usage information
- Exit: Gracefully terminate the application
- Back: Navigate to previous context in the navigation stack
- Menu: Return to main menu from any sub-context

All commands implement the BaseCommand interface and return APIResponse
format responses with data wrapped in a "data" field.

Shell Command Note:
This module uses subprocess for executing system commands when needed.
Consider alternatives or security implications when adding new shell
command execution capabilities.

Exception Handling:
All commands include proper error handling and validation of context
requirements before execution.

Performance:
Commands are optimized for interactive use with minimal latency.
Navigation stack operations are O(1) for common cases.
"""

import os
import subprocess
from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand
from socratic_system.utils.orchestrator_helper import safe_orchestrator_call


class HelpCommand(BaseCommand):
    """Display help information for available commands.

    Provides comprehensive help documentation for all registered commands.
    Can display global help or specific help for a named command.
    Includes usage patterns, arguments, and descriptions.
    """

    def __init__(self):
        super().__init__(
            name="help",
            description=HELP_DESCRIPTION,
            usage=HELP_USAGE,
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute help command"""
        if args:
            command_name = args[0]
            context["app"].command_handler.print_help(command_name)
        else:
            context["app"].command_handler.print_help()

        return self.success()


class ExitCommand(BaseCommand):
    """Exit the Socrates AI application gracefully.

    Cleanly terminates the application, performing any necessary
    cleanup operations. Displays exit message and thanks for usage.
    """

    def __init__(self):
        super().__init__(name=EXIT_CODE, description="Exit the Socrates AI", usage=EXIT_CODE)

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute exit command"""
        print(f"\n{Fore.GREEN}Thank you for using Socrates AI")
        print(f"..τῷ Ἀσκληπιῷ ὀφείλομεν ἀλεκτρυόνα, ἀπόδοτε καὶ μὴ ἀμελήσετε...{Style.RESET_ALL}\n")

        return {"status": "exit", "message": "Exiting application"}


class BackCommand(BaseCommand):
    """Navigate back to previous context or menu level.

    Returns to the previously visited context, maintaining navigation
    history. Updates UI state and application context accordingly.
    """

    def __init__(self):
        super().__init__(name="back", description=BACK_DESCRIPTION, usage="back")

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute back command"""
        nav_stack = context.get("nav_stack")
        if not nav_stack:
            return self.error(NAV_STACK_ERROR)

        # Check if we're leaving a project context
        project = context.get("project")
        session_ended = project is not None

        prev_context, state = nav_stack.go_back()

        if prev_context is None:
            self.print_info("Already at the beginning")
            return self.success(data={"session_ended": session_ended} if session_ended else {})

        self.print_info(f"Going back to {prev_context}")
        return self.success(
            data={"nav_context": prev_context, "state": state, "session_ended": session_ended}
        )


class MenuCommand(BaseCommand):
    """Return to the main menu from any sub-context.

    Clears navigation stack and returns to the root menu level.
    Resets application state to default main menu configuration.
    """

    def __init__(self):
        super().__init__(name="menu", description=MENU_DESCRIPTION, usage="menu")

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute menu command"""
        nav_stack = context.get("nav_stack")
        if not nav_stack:
            return self.error(NAV_STACK_ERROR)

        # Check if we're leaving a project context
        project = context.get("project")
        session_ended = project is not None

        context_name, state = nav_stack.go_home()
        self.print_info("Returning to main menu")

        return self.success(
            data={"nav_context": context_name, "state": state, "session_ended": session_ended}
        )


class StatusCommand(BaseCommand):
    """Show system and application status"""

    def __init__(self):
        super().__init__(
            name="status", description="Show current system and application status", usage="status"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute status command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        # Get system stats
        try:
            result = safe_orchestrator_call(
                orchestrator,
                "system_monitor",
                {"action": "get_stats"},
                operation_name="get system stats",
            )

            self.print_header("System Status")

            stats = result
            print(f"{Fore.WHITE}Total Tokens Used:     {stats.get('total_tokens', 'N/A')}")
            print(f"Estimated Cost:        ${stats.get('total_cost', 0):.4f}")
            print(f"API Calls Made:        {stats.get('api_calls', 'N/A')}")
            print(
                f"Connection Status:     {'✓ Active' if stats.get('connection_status') else '✗ Inactive'}"
            )
            print()
        except ValueError as e:
            self.print_error(str(e))

        # Check for warnings
        try:
            result = safe_orchestrator_call(
                orchestrator,
                "system_monitor",
                {"action": "check_limits"},
                operation_name="check system limits",
            )

            if result.get("warnings"):
                print(f"{Fore.YELLOW}Warnings:{Style.RESET_ALL}")
                for warning in result["warnings"]:
                    print(f"  ⚠ {warning}")
                print()
        except ValueError as e:
            self.print_warning(str(e))

        return self.success()


class ClearCommand(BaseCommand):
    """Clear the terminal screen"""

    def __init__(self):
        super().__init__(name="clear", description="Clear the terminal screen", usage="clear")

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute clear command"""
        # Use subprocess instead of os.system for better security and cross-platform compatibility
        try:
            if os.name == "nt":
                subprocess.run(
                    ["cls"], shell=True, check=False
                )  # nosec B602 - cls is shell builtin on Windows
            else:
                subprocess.run(["clear"], check=False)  # nosec B607 - clear is in standard PATH
        except Exception:
            # Fallback if subprocess fails
            pass
        return self.success()


class PromptCommand(BaseCommand):
    """Display current context prompt"""

    def __init__(self):
        super().__init__(
            name="prompt", description="Display current context and prompt", usage="prompt"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute prompt command"""
        context_display = context.get("app").context_display if context.get("app") else None

        if not context_display:
            return self.error("Context display not available")

        print()
        print(context_display.get_status_bar())
        print()

        if context.get("project"):
            print(context_display.get_project_summary())
            print()

        return self.success()


class InfoCommand(BaseCommand):
    """Show information about the system"""

    def __init__(self):
        super().__init__(
            name="info", description="Display system and version information", usage="info"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute info command"""
        self.print_header("Socrates AI Information")

        print("Version: 7.0")
        print("Purpose: Socratic guidance for software development")
        print("Motto: Οὐδὲν οἶδα, οὔτε διδάσκω τι, ἀλλὰ διαπορῶ μόνον")
        print("       (I know nothing, nor do I teach anything, but I only question)")
        print()
        print("Current Session:")

        if context.get("user"):
            print(f"  User: {context['user'].username}")
        else:
            print("  User: (not logged in)")

        if context.get("project"):
            project = context["project"]
            print(f"  Project: {project.name}")
            print(f"  Phase: {project.phase}")
            print(f"  Status: {getattr(project, 'status', 'active')}")
        else:
            print("  Project: (none selected)")

        print()

        return self.success()


class NLUEnableCommand(BaseCommand):
    """Enable natural language understanding"""

    def __init__(self):
        super().__init__(
            name="nlu enable",
            description="Enable natural language command interpretation",
            usage="nlu enable",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute NLU enable command"""
        app = context.get("app")
        if not app or not app.nlu_handler:
            return self.error("NLU not available in this context")

        app.nlu_handler.enable()
        return self.success(
            "Natural language understanding enabled. You can now use plain English commands!"
        )


class NLUDisableCommand(BaseCommand):
    """Disable natural language understanding"""

    def __init__(self):
        super().__init__(
            name="nlu disable",
            description="Disable natural language command interpretation (requires slash commands)",
            usage="nlu disable",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute NLU disable command"""
        app = context.get("app")
        if not app or not app.nlu_handler:
            return self.error("NLU not available in this context")

        app.nlu_handler.disable()
        return self.success(
            "Natural language understanding disabled. Use slash commands (e.g., /help)"
        )


class NLUStatusCommand(BaseCommand):
    """Show NLU status"""

    def __init__(self):
        super().__init__(
            name="nlu status",
            description="Show natural language understanding status",
            usage="nlu status",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute NLU status command"""
        app = context.get("app")
        if not app or not app.nlu_handler:
            return self.error("NLU not available in this context")

        status_text = "enabled" if app.nlu_handler.is_enabled() else "disabled"
        message = (
            f"Natural language understanding is currently {Fore.CYAN}{status_text}{Style.RESET_ALL}"
        )

        if app.nlu_handler.is_enabled():
            message += "\nYou can type plain English commands (e.g., 'create a project') or use slash commands"
        else:
            message += "\nYou must use slash commands (e.g., /project create)"


# ============================================================================
# COMMAND MESSAGES AND STRINGS
# ============================================================================

# Help command descriptions
HELP_DESCRIPTION = "Display information about available commands"
HELP_USAGE = "help [command_name]"

# Exit command messages
EXIT_MESSAGE_HEADER = "Exiting Socrates AI System"
EXIT_MESSAGE_FOOTER = "Thank you for using Socrates!"
EXIT_CODE = 0

# Navigation messages
BACK_DESCRIPTION = "Go back to previous context"
BACK_MESSAGE = "Going back to {}"
BACK_START_MESSAGE = "Already at the beginning"

MENU_DESCRIPTION = "Return to main menu"
MENU_MESSAGE = "Returning to main menu"

# Navigation context names
NAVIGATION_STACK_KEY = "nav_stack"
NAVIGATION_CONTEXT_KEY = "nav_context"
SESSION_ENDED_KEY = "session_ended"

# Error messages
NAV_STACK_ERROR = "Navigation stack error"

# Status codes
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_EXIT = EXIT_CODE
