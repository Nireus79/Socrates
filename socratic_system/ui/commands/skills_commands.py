"""Skills management commands for team members"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class SkillsSetCommand(BaseCommand):
    """Set skills for a team member"""

    def __init__(self):
        super().__init__(
            name="skills set",
            description="Set skills for a team member",
            usage="skills set <username> <skill1,skill2,...>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skills set command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        if len(args) < 2:
            return self.error("Usage: /skills set <username> <skill1,skill2,...>")

        orchestrator = context.get("orchestrator")
        project = context.get("project")
        user = context.get("user")

        if not orchestrator or not project or not user:
            return self.error("Required context not available")

        # Only owner can change skills
        if user.username != project.owner:
            return self.error("Only the project owner can update skills")

        username = args[0]
        skills_str = args[1]
        skills = [s.strip().lower() for s in skills_str.split(",") if s.strip()]

        if not skills:
            return self.error("At least one skill is required")

        # Find team member
        member_found = False
        for member in project.team_members or []:
            if member.username == username:
                member.skills = skills
                member_found = True
                break

        if not member_found:
            return self.error(f"User '{username}' is not a team member in this project")

        # Save project
        orchestrator.database.save_project(project)

        print(
            f"\n{Fore.GREEN}✓ Updated skills for {username}: {', '.join(skills)}{Style.RESET_ALL}\n"
        )

        return self.success(message=f"Skills updated for {username}: {', '.join(skills)}")


class SkillsListCommand(BaseCommand):
    """List skills for all team members"""

    def __init__(self):
        super().__init__(
            name="skills list",
            description="List skills for all team members",
            usage="skills list",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skills list command"""
        project = context.get("project")

        if not project or not project.team_members:
            return self.error("No team members in project")

        print(f"\n{Fore.CYAN}Team Skills{Style.RESET_ALL}\n")

        has_skills = False
        for member in project.team_members:
            if member.skills:
                has_skills = True
                skills_str = ", ".join(member.skills)
                is_owner = " (owner)" if member.username == project.owner else ""
                print(
                    f"{Fore.WHITE}{member.username:<20}{Style.RESET_ALL} [{member.role}]{is_owner}"
                )
                print(f"  {Fore.CYAN}Skills: {skills_str}{Style.RESET_ALL}")
            else:
                is_owner = " (owner)" if member.username == project.owner else ""
                print(
                    f"{Fore.WHITE}{member.username:<20}{Style.RESET_ALL} [{member.role}]{is_owner}"
                )
                print(f"  {Fore.YELLOW}No skills defined{Style.RESET_ALL}")
            print()

        if not has_skills:
            print(f"{Fore.YELLOW}No skills defined for any team members{Style.RESET_ALL}\n")

        return self.success()
