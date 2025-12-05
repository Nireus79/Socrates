"""Context display for showing current application state"""

from typing import Optional

from colorama import Fore, Style

from socratic_system.models import ProjectContext, User


class ContextDisplay:
    """
    Manages display of current application context.

    Shows user, project, phase, progress, and provides formatted prompts.
    """

    def __init__(self):
        """Initialize context display."""
        self.current_user: Optional[User] = None
        self.current_project: Optional[ProjectContext] = None

    def set_context(
        self, user: Optional[User] = None, project: Optional[ProjectContext] = None
    ) -> None:
        """
        Update the current context to display.

        Args:
            user: Current logged-in user
            project: Current loaded project
        """
        if user is not None:
            self.current_user = user
        if project is not None:
            self.current_project = project

    def get_prompt(self) -> str:
        """
        Get formatted command prompt.

        Returns:
            Formatted prompt string like "[user@project]$ " or "[user]$ "
        """
        parts = []

        if self.current_user:
            parts.append(self.current_user.username)

        if self.current_project:
            parts.append(self.current_project.name)

        if parts:
            context_str = f"{Fore.CYAN}[{Fore.WHITE}{'/'.join(parts)}{Fore.CYAN}]{Style.RESET_ALL}"
        else:
            context_str = f"{Fore.CYAN}[Socratic]{Style.RESET_ALL}"

        return f"{context_str}$ "

    def get_status_bar(self) -> str:
        """
        Get formatted status bar showing current state.

        Returns:
            Multi-line status bar string
        """
        lines = []

        # Title bar
        lines.append(f"{Fore.CYAN}{'═' * 50}")
        lines.append("Socratic RAG System")
        lines.append("═" * 50)

        # User info
        if self.current_user:
            lines.append(f"{Fore.WHITE}User: {self.current_user.username}")
        else:
            lines.append(f"{Fore.YELLOW}User: (not logged in)")

        # Project info
        if self.current_project:
            phase_color = self._get_phase_color(self.current_project.phase)
            lines.append(f"Project: {self.current_project.name}")
            lines.append(f"Phase: {phase_color}{self.current_project.phase}{Fore.WHITE}")

            # Progress bar
            progress = getattr(self.current_project, "progress", 0)
            lines.append(f"Progress: {self._get_progress_bar(progress)} {progress}%")

            # Status
            status = getattr(self.current_project, "status", "active")
            status_color = self._get_status_color(status)
            lines.append(f"Status: {status_color}{status}{Fore.WHITE}")
        else:
            lines.append(f"{Fore.YELLOW}Project: (none selected)")

        lines.append(f"{Fore.CYAN}{'═' * 50}{Style.RESET_ALL}")

        return "\n".join(lines)

    def get_project_summary(self) -> str:
        """
        Get a brief summary of current project.

        Returns:
            Formatted project summary
        """
        if not self.current_project:
            return ""

        lines = []
        project = self.current_project

        # Goals
        if project.goals:
            lines.append(f"{Fore.CYAN}Goals:{Style.RESET_ALL}")
            lines.append(f"  {project.goals}")

        # Requirements
        if project.requirements:
            lines.append(f"\n{Fore.CYAN}Requirements:{Style.RESET_ALL}")
            for req in project.requirements[:3]:  # Show first 3
                lines.append(f"  • {req}")
            if len(project.requirements) > 3:
                lines.append(f"  ... and {len(project.requirements) - 3} more")

        # Tech Stack
        if project.tech_stack:
            lines.append(f"\n{Fore.CYAN}Tech Stack:{Style.RESET_ALL}")
            lines.append(f"  {', '.join(project.tech_stack)}")

        return "\n".join(lines)

    @staticmethod
    def _get_progress_bar(progress: int, width: int = 20) -> str:
        """
        Get a visual progress bar.

        Args:
            progress: Progress percentage (0-100)
            width: Width of the progress bar

        Returns:
            Formatted progress bar
        """
        filled = int(width * progress / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"{Fore.GREEN}{bar}{Style.RESET_ALL}"

    @staticmethod
    def _get_phase_color(phase: str) -> str:
        """Get color code for a project phase."""
        colors = {
            "discovery": Fore.YELLOW,
            "analysis": Fore.CYAN,
            "design": Fore.BLUE,
            "implementation": Fore.GREEN,
        }
        return colors.get(phase, Fore.WHITE)

    @staticmethod
    def _get_status_color(status: str) -> str:
        """Get color code for a project status."""
        colors = {
            "active": Fore.GREEN,
            "completed": Fore.BLUE,
            "on-hold": Fore.YELLOW,
            "archived": Fore.MAGENTA,
        }
        return colors.get(status, Fore.WHITE)

    def print_divider(self, char: str = "─", width: int = 50) -> None:
        """Print a horizontal divider."""
        print(f"{Fore.CYAN}{char * width}{Style.RESET_ALL}")

    def print_header(self, title: str) -> None:
        """Print a section header."""
        print(f"\n{Fore.CYAN}{'═' * 50}")
        print(f"{title:^50}")
        print(f"{'═' * 50}{Style.RESET_ALL}\n")

    def print_subheader(self, title: str) -> None:
        """Print a subsection header."""
        print(f"\n{Fore.YELLOW}{title}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * len(title)}{Style.RESET_ALL}")
