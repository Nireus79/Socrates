"""Subscription checking and enforcement logic."""

from typing import Optional, Tuple

from colorama import Fore, Style

from socratic_system.models.user import User
from socratic_system.subscription.tiers import (
    COMMAND_FEATURE_MAP,
    FEATURE_TIER_REQUIREMENTS,
    get_tier_limits,
)


class SubscriptionChecker:
    """Checks subscription status and enforces tier limits."""

    @staticmethod
    def check_command_access(user: User, command_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user has access to a command.

        Returns:
            (has_access: bool, error_message: Optional[str])
        """
        if user and user.testing_mode:
            return True, None

        if user is None:
            return False, "User not found. Please log in to access commands."

        # Check if command requires specific feature
        required_feature = COMMAND_FEATURE_MAP.get(command_name)

        if not required_feature:
            # Command not gated, allow access
            return True, None

        # Check if user's tier has access to this feature
        user_tier = user.subscription_tier.lower()
        required_tier = FEATURE_TIER_REQUIREMENTS.get(required_feature)

        if not required_tier:
            # Feature not gated, allow access
            return True, None

        # Check tier hierarchy: free < pro < enterprise
        tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
        user_tier_level = tier_hierarchy.get(user_tier, 0)
        required_tier_level = tier_hierarchy.get(required_tier, 0)

        if user_tier_level >= required_tier_level:
            # User has sufficient tier
            return True, None

        # User doesn't have access - generate upgrade message
        upgrade_message = SubscriptionChecker._generate_upgrade_message(
            command_name, required_feature, required_tier, user_tier
        )
        return False, upgrade_message

    @staticmethod
    def check_project_limit(
        user: User, current_project_count: int, testing_mode: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user can create another project.

        Args:
            user: User object
            current_project_count: Current number of projects
            testing_mode: Whether testing mode is enabled (from headers)

        Returns:
            (can_create: bool, error_message: Optional[str])
        """
        # Check both user model and header-based testing mode
        if (user and user.testing_mode) or testing_mode:
            return True, None

        if user is None:
            return False, "User not found. Please log in to create projects."

        user_tier = user.subscription_tier.lower()
        limits = get_tier_limits(user_tier)

        # None means unlimited
        if limits.max_projects is None:
            return True, None

        if current_project_count >= limits.max_projects:
            message = (
                f"\n{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n"
                f"{Fore.RED}Project Limit Reached{Style.RESET_ALL}\n\n"
                f"Your {limits.name} tier allows {limits.max_projects} active project(s).\n"
                f"You currently have {current_project_count} active project(s).\n\n"
                f"{Fore.CYAN}💡 Upgrade to Pro for 10 projects or Enterprise for unlimited projects.{Style.RESET_ALL}\n"
                f"{Fore.WHITE}Run: /subscription upgrade pro{Style.RESET_ALL}\n"
                f"{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n"
            )
            return False, message

        return True, None

    @staticmethod
    def check_team_member_limit(
        user: User, current_team_size: int, testing_mode: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user can add another team member.

        Args:
            user: User object
            current_team_size: Current team size
            testing_mode: Whether testing mode is enabled (from headers)

        Returns:
            (can_add: bool, error_message: Optional[str])
        """
        # Check both user model and header-based testing mode
        if (user and user.testing_mode) or testing_mode:
            return True, None

        user_tier = user.subscription_tier.lower()
        limits = get_tier_limits(user_tier)

        # None means unlimited
        if limits.max_team_members is None:
            return True, None

        # If max is 1, it's solo-only (free tier)
        if limits.max_team_members == 1:
            message = (
                f"\n{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n"
                f"{Fore.RED}Team Collaboration Not Available{Style.RESET_ALL}\n\n"
                f"Your {limits.name} tier only supports solo projects.\n\n"
                f"{Fore.CYAN}💡 Upgrade to Pro to collaborate with up to 5 team members!{Style.RESET_ALL}\n"
                f"{Fore.WHITE}Run: /subscription upgrade pro{Style.RESET_ALL}\n"
                f"{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n"
            )
            return False, message

        if current_team_size >= limits.max_team_members:
            message = (
                f"\n{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n"
                f"{Fore.RED}Team Member Limit Reached{Style.RESET_ALL}\n\n"
                f"Your {limits.name} tier allows {limits.max_team_members} team member(s).\n"
                f"You currently have {current_team_size} team member(s).\n\n"
                f"{Fore.CYAN}💡 Upgrade to Enterprise for unlimited team members.{Style.RESET_ALL}\n"
                f"{Fore.WHITE}Run: /subscription upgrade enterprise{Style.RESET_ALL}\n"
                f"{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n"
            )
            return False, message

        return True, None

    @staticmethod
    def check_question_limit(user: User) -> Tuple[bool, Optional[str]]:
        """
        Check if user can ask another question this month.

        Returns:
            (can_ask: bool, error_message: Optional[str])
        """
        if user and user.testing_mode:
            return True, None

        if user is None:
            return False, "User not found. Please log in to ask questions."

        # Reset usage if needed
        user.reset_monthly_usage_if_needed()

        user_tier = user.subscription_tier.lower()
        limits = get_tier_limits(user_tier)

        # None means unlimited
        if limits.max_questions_per_month is None:
            return True, None

        if user.questions_used_this_month >= limits.max_questions_per_month:
            message = (
                f"\n{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n"
                f"{Fore.RED}Monthly Question Limit Reached{Style.RESET_ALL}\n\n"
                f"Your {limits.name} tier allows {limits.max_questions_per_month} questions per month.\n"
                f"You've used {user.questions_used_this_month} questions this month.\n\n"
                f"{Fore.CYAN}💡 Upgrade to Pro for 1,000 questions/month or Enterprise for unlimited.{Style.RESET_ALL}\n"
                f"{Fore.WHITE}Run: /subscription upgrade pro{Style.RESET_ALL}\n"
                f"{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n"
            )
            return False, message

        return True, None

    @staticmethod
    def _generate_upgrade_message(
        command_name: str, feature: str, required_tier: str, user_tier: str
    ) -> str:
        """Generate a friendly upgrade message."""
        feature_names = {
            "team_collaboration": "Team Collaboration",
            "multi_llm": "Multi-LLM Access",
            "advanced_analytics": "Advanced Analytics",
            "code_generation": "Code Generation",
            "maturity_tracking": "Maturity Tracking",
        }

        feature_display = feature_names.get(feature, feature.replace("_", " ").title())

        message = (
            f"\n{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n"
            f"{Fore.RED}Premium Feature Required{Style.RESET_ALL}\n\n"
            f"The command '{command_name}' requires {Fore.CYAN}{feature_display}{Style.RESET_ALL}.\n"
            f"Your current tier: {Fore.YELLOW}{user_tier.upper()}{Style.RESET_ALL}\n"
            f"Required tier: {Fore.GREEN}{required_tier.upper()}{Style.RESET_ALL}\n\n"
            f"{Fore.CYAN}💡 Upgrade to unlock this feature!{Style.RESET_ALL}\n"
            f"{Fore.WHITE}Run: /subscription upgrade {required_tier}{Style.RESET_ALL}\n"
            f"{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n"
        )
        return message
