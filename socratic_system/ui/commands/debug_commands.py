"""Debug and logging commands"""

from pathlib import Path
from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand
from socratic_system.utils.logger import is_debug_mode, set_debug_mode


class DebugCommand(BaseCommand):
    """Toggle debug mode on/off"""

    def __init__(self):
        super().__init__(
            name="debug",
            description="Toggle debug mode (shows detailed logs in terminal)",
            usage="debug [on|off]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute debug command"""
        current_state = is_debug_mode()

        # Parse argument
        if args:
            mode = args[0].lower()
            if mode == "on":
                set_debug_mode(True)
                self.print_success("Debug mode enabled - logs will be printed to terminal")
                return self.success(message="Debug mode is now ON")
            elif mode == "off":
                set_debug_mode(False)
                self.print_success("Debug mode disabled - only warnings and errors shown")
                return self.success(message="Debug mode is now OFF")
            else:
                return self.error(f"Invalid argument: {mode}. Use 'on' or 'off'")
        else:
            # Toggle
            new_state = not current_state
            set_debug_mode(new_state)
            status = "enabled" if new_state else "disabled"
            self.print_success(f"Debug mode {status}")
            return self.success(message=f"Debug mode is now {'ON' if new_state else 'OFF'}")


class LogsCommand(BaseCommand):
    """View recent logs from the log file"""

    def __init__(self):
        super().__init__(name="logs", description="View recent log entries", usage="logs [lines]")

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute logs command"""
        # Get number of lines to display
        num_lines = 20
        if args:
            try:
                num_lines = int(args[0])
            except ValueError:
                return self.error(f"Invalid number: {args[0]}")

        # Read log file
        log_file = Path("socratic_logs/socratic.log")
        if not log_file.exists():
            return self.info("No log file found yet")

        try:
            with open(log_file) as f:
                lines = f.readlines()

            # Get last N lines
            recent_lines = lines[-num_lines:] if len(lines) > num_lines else lines

            print(
                f"\n{Fore.CYAN}Recent log entries (last {len(recent_lines)} lines):{Style.RESET_ALL}\n"
            )
            for line in recent_lines:
                # Color code by log level
                line = line.strip()
                if "[DEBUG]" in line:
                    print(f"{Fore.BLUE}{line}{Style.RESET_ALL}")
                elif "[INFO]" in line:
                    print(f"{Fore.GREEN}{line}{Style.RESET_ALL}")
                elif "[WARNING]" in line:
                    print(f"{Fore.YELLOW}{line}{Style.RESET_ALL}")
                elif "[ERROR]" in line:
                    print(f"{Fore.RED}{line}{Style.RESET_ALL}")
                else:
                    print(line)

            print()
            return self.success(data={"lines_shown": len(recent_lines)})

        except Exception as e:
            return self.error(f"Failed to read log file: {e}")


class StatusCommand(BaseCommand):
    """Show system status and debug info"""

    def __init__(self):
        super().__init__(
            name="status", description="Show system status and debug information", usage="status"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute status command"""
        debug_state = "ON" if is_debug_mode() else "OFF"
        log_file = Path("socratic_logs/socratic.log")

        print(f"\n{Fore.CYAN}System Status:{Style.RESET_ALL}")
        print(f"  Debug Mode:        {debug_state}")
        print(f"  Log File:          {log_file}")
        if log_file.exists():
            print(f"  Log File Size:     {log_file.stat().st_size / 1024:.1f} KB")
        else:
            print("  Log File Size:     No logs yet")

        # User and project info
        user = context.get("user")
        project = context.get("project")
        print(f"\n{Fore.CYAN}Context:{Style.RESET_ALL}")
        print(f"  Current User:      {user.username if user else 'None'}")
        print(f"  Current Project:   {project.name if project else 'None'}")

        print(f"\n{Fore.CYAN}Available Commands:{Style.RESET_ALL}")
        print("  /debug [on|off]    - Toggle debug mode")
        print("  /logs [lines]      - View recent logs")
        print("  /status            - Show this status")
        print()

        return self.success()
