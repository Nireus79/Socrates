"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.User authentication and account management commands
"""

import datetime
from typing import Any, Dict, List

from colorama import Fore, Style

# Import password verification from API module
# This ensures CLI and API use identical password hashing (bcrypt)
from socrates_api.auth.password import hash_password, verify_password

from socratic_system.models import User
from socratic_system.ui.commands.base import BaseCommand
from socratic_system.utils.orchestrator_helper import safe_orchestrator_call


class UserLoginCommand(BaseCommand):
    """Login to an existing account"""

    def __init__(self):
        super().__init__(
            name="user login", description="Login to an existing account", usage="user login"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user login command"""
        orchestrator = context.get("orchestrator")
        app = context.get("app")

        if not orchestrator or not app:
            return self.error("Orchestrator or app not available")

        print(f"\n{Fore.CYAN}Login{Style.RESET_ALL}")

        username = input(f"{Fore.WHITE}Username: ").strip()
        if not username:
            return self.error("Username cannot be empty")

        passcode = input(f"{Fore.WHITE}Passcode: ").strip()
        if not passcode:
            return self.error("Passcode cannot be empty")

        # Load user from database
        user = orchestrator.database.load_user(username)
        if not user:
            return self.error("User not found")

        # Verify passcode using same method as API
        if not verify_password(passcode, user.passcode_hash):
            return self.error("Invalid passcode")

        # Update app context
        app.current_user = user
        app.context_display.set_context(user=user)

        self.print_success(f"Welcome back, {username}!")

        return self.success(data={"user": user})


class UserCreateCommand(BaseCommand):
    """Create a new account"""

    def __init__(self):
        super().__init__(
            name="user create", description="Create a new account", usage="user create"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user create command"""
        orchestrator = context.get("orchestrator")
        app = context.get("app")

        if not orchestrator or not app:
            return self.error("Orchestrator or app not available")

        print(f"\n{Fore.CYAN}Create New Account{Style.RESET_ALL}")

        username = input(f"{Fore.WHITE}Username: ").strip()
        if not username:
            return self.error("Username cannot be empty")

        # Check if user already exists
        existing_user = orchestrator.database.load_user(username)
        if existing_user:
            return self.error("Username already exists")

        email = input(f"{Fore.WHITE}Email: ").strip()
        if not email:
            return self.error("Email cannot be empty")

        passcode = input(f"{Fore.WHITE}Passcode: ").strip()
        if not passcode:
            return self.error("Passcode cannot be empty")

        confirm_passcode = input(f"{Fore.WHITE}Confirm passcode: ").strip()
        if passcode != confirm_passcode:
            return self.error("Passcodes do not match")

        # Create user with same hashing as API
        passcode_hash = hash_password(passcode)
        user = User(
            username=username,
            email=email,
            passcode_hash=passcode_hash,
            created_at=datetime.datetime.now(),
            projects=[],
        )

        orchestrator.database.save_user(user)

        # Update app context
        app.current_user = user
        app.context_display.set_context(user=user)

        self.print_success(f"Account created successfully! Welcome, {username}!")

        return self.success(data={"user": user})


class UserLogoutCommand(BaseCommand):
    """Logout and switch to a different user"""

    def __init__(self):
        super().__init__(
            name="user logout",
            description="Logout current user and switch to another account",
            usage="user logout",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user logout command"""
        app = context.get("app")

        if not app:
            return self.error("App not available")

        current_user = app.current_user
        if current_user:
            self.print_info(f"Logging out {current_user.username}")

        app.current_user = None
        app.current_project = None
        app.context_display.set_context(user=None, project=None)

        return self.success(message="Logged out successfully")


class UserArchiveCommand(BaseCommand):
    """Archive the current user account"""

    def __init__(self):
        super().__init__(
            name="user archive",
            description="Archive your current account (soft delete)",
            usage="user archive",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user archive command"""
        if not self.require_user(context):
            return self.error("No user logged in")

        orchestrator = context.get("orchestrator")
        app = context.get("app")
        user = context.get("user")

        if not orchestrator or not app or not user:
            return self.error("Required context not available")

        print(f"\n{Fore.YELLOW}⚠️  Account Archiving{Style.RESET_ALL}")
        print("This will:")
        print("  • Archive your account (you can restore it later)")
        print("  • Archive all projects you own")
        print("  • Remove you from collaborations")
        print("  • Keep all data for potential restoration")

        confirm = input(f"\n{Fore.RED}Are you sure? (yes/no): ").lower()
        if confirm != "yes":
            self.print_info("Archiving cancelled")
            return self.success()

        try:
            result = safe_orchestrator_call(
                orchestrator,
                "user_manager",
                {"action": "archive_user", "username": user.username, "requester": user.username},
                operation_name="archive user",
            )

            self.print_success(result.get("message"))
            self.print_info("You will be logged out now")

            app.current_user = None
            app.current_project = None
            app.context_display.set_context(user=None, project=None)

            input("Press Enter to continue...")

            return self.success()
        except ValueError as e:
            return self.error(str(e))


class UserDeleteCommand(BaseCommand):
    """Permanently delete the current user account"""

    def __init__(self):
        super().__init__(
            name="user delete",
            description="Permanently delete your account (cannot be undone)",
            usage="user delete",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user delete command"""
        if not self.require_user(context):
            return self.error("No user logged in")

        orchestrator = context.get("orchestrator")
        app = context.get("app")
        user = context.get("user")

        if not orchestrator or not app or not user:
            return self.error("Required context not available")

        print(f"\n{Fore.RED}⚠️  PERMANENT ACCOUNT DELETION{Style.RESET_ALL}")
        print("This will:")
        print("  • PERMANENTLY delete your account")
        print("  • Transfer owned projects to collaborators")
        print("  • Delete projects with no collaborators")
        print("  • Remove all your data FOREVER")
        print(f"\n{Fore.YELLOW}This action CANNOT be undone!{Style.RESET_ALL}")

        confirm1 = input(f"\n{Fore.RED}Type 'I UNDERSTAND' to continue: ").strip()
        if confirm1 != "I UNDERSTAND":
            self.print_info("Deletion cancelled")
            return self.success()

        confirm2 = input(f"{Fore.RED}Type 'DELETE' to confirm permanent deletion: ").strip()
        if confirm2 != "DELETE":
            self.print_info("Deletion cancelled")
            return self.success()

        try:
            result = safe_orchestrator_call(
                orchestrator,
                "user_manager",
                {
                    "action": "delete_user_permanently",
                    "username": user.username,
                    "requester": user.username,
                    "confirmation": "DELETE",
                },
                operation_name="delete user permanently",
            )

            self.print_success(result.get("message"))
            print("Account has been permanently deleted.")
            print("Goodbye.")

            app.current_user = None
            app.current_project = None
            app.context_display.set_context(user=None, project=None)

            return {"status": "exit", "message": "Account deleted"}
        except ValueError as e:
            return self.error(str(e))


class UserRestoreCommand(BaseCommand):
    """Restore an archived user account"""

    def __init__(self):
        super().__init__(
            name="user restore",
            description="Restore an archived user account",
            usage="user restore",
        )

    def _display_archived_users(self, archived_users: List[Dict[str, Any]]) -> None:
        """
        Display archived user accounts with formatted dates.

        Args:
            archived_users: List of archived user dictionaries
        """
        print(f"\n{Fore.CYAN}Archived Accounts:{Style.RESET_ALL}")

        for i, user_info in enumerate(archived_users, 1):
            archived_date = user_info.get("archived_at", "Unknown")
            if isinstance(archived_date, str):
                try:
                    archived_date = datetime.datetime.fromisoformat(archived_date).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                except (ValueError, TypeError):
                    pass

            print(f"{i}. {user_info['username']} (archived: {archived_date})")

    def _restore_selected_user(self, username: str, orchestrator) -> Dict[str, Any]:
        """
        Restore a selected archived user account.

        Args:
            username: Username to restore
            orchestrator: Orchestrator instance

        Returns:
            Result dictionary with success/error status
        """
        confirm = input(f"{Fore.CYAN}Restore account '{username}'? (y/n): ").lower()
        if confirm != "y":
            self.print_info("Restoration cancelled")
            return self.success()

        try:
            result = safe_orchestrator_call(
                orchestrator,
                "user_manager",
                {"action": "restore_user", "username": username},
                operation_name="restore user",
            )

            self.print_success(f"Account '{username}' restored successfully!")
            return self.success()
        except ValueError as e:
            return self.error(str(e))

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user restore command"""
        orchestrator = context.get("orchestrator")

        if not orchestrator:
            return self.error("Orchestrator not available")

        try:
            result = safe_orchestrator_call(
                orchestrator,
                "user_manager",
                {"action": "get_archived_users"},
                operation_name="get archived users",
            )

            archived_users = result.get("archived_users", [])
            if not archived_users:
                self.print_info("No archived accounts found")
                return self.success()
        except ValueError:
            self.print_info("No archived accounts found")
            return self.success()
        self._display_archived_users(archived_users)

        try:
            choice = input(
                f"\n{Fore.WHITE}Select account to restore (1-{len(archived_users)}, or 0 to cancel): "
            ).strip()

            if choice == "0":
                return self.success()

            index = int(choice) - 1
            if 0 <= index < len(archived_users):
                username = archived_users[index]["username"]
                return self._restore_selected_user(username, orchestrator)
            else:
                return self.error("Invalid selection")

        except ValueError:
            return self.error("Invalid input")
