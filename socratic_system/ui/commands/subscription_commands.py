"""Subscription management commands."""

from datetime import datetime
from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.subscription.tiers import get_tier_limits
from socratic_system.ui.commands.base import BaseCommand


class SubscriptionStatusCommand(BaseCommand):
    """Show current subscription status and usage."""

    def __init__(self):
        super().__init__(
            name="subscription status",
            description="Show subscription tier and usage",
            usage="subscription status",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute subscription status command."""
        user = context.get("user")
        orchestrator = context.get("orchestrator")

        if not user:
            return self.error("User not found")

        # Ensure usage is reset if needed
        user.reset_monthly_usage_if_needed()

        # Get current tier limits
        limits = get_tier_limits(user.subscription_tier)

        # Get active project count
        active_projects = orchestrator.database.get_user_projects(user.username)
        active_count = len([p for p in active_projects if not p.is_archived])

        print(f"\n{Fore.CYAN}{'━' * 50}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Subscription Status{Style.RESET_ALL}\n")
        print(f"{Fore.WHITE}Tier:{Style.RESET_ALL} {Fore.YELLOW}{limits.name}{Style.RESET_ALL}")
        print(
            f"{Fore.WHITE}Status:{Style.RESET_ALL} {Fore.GREEN}{user.subscription_status.title()}{Style.RESET_ALL}"
        )
        print(f"{Fore.WHITE}Monthly Cost:{Style.RESET_ALL} ${limits.monthly_cost:.2f}\n")

        print(f"{Fore.CYAN}Usage This Month{Style.RESET_ALL}\n")

        # Questions
        if limits.max_questions_per_month:
            questions_pct = user.questions_used_this_month / limits.max_questions_per_month * 100
            print(
                f"  {Fore.WHITE}Questions:{Style.RESET_ALL} {user.questions_used_this_month}/{limits.max_questions_per_month} "
                f"({questions_pct:.0f}%)"
            )
        else:
            print(
                f"  {Fore.WHITE}Questions:{Style.RESET_ALL} {user.questions_used_this_month} (unlimited)"
            )

        # Projects
        if limits.max_projects:
            projects_pct = active_count / limits.max_projects * 100
            print(
                f"  {Fore.WHITE}Projects:{Style.RESET_ALL} {active_count}/{limits.max_projects} "
                f"({projects_pct:.0f}%)"
            )
        else:
            print(f"  {Fore.WHITE}Projects:{Style.RESET_ALL} {active_count} (unlimited)")

        print(f"\n{Fore.CYAN}Features{Style.RESET_ALL}\n")
        print(
            f"  {'✓' if limits.multi_llm_access else '✗'} Multi-LLM Access (Claude, OpenAI, Gemini)"
        )
        print(
            f"  {'✓' if limits.max_team_members and limits.max_team_members > 1 else '✗'} Team Collaboration"
        )
        print(f"  {'✓' if limits.advanced_analytics else '✗'} Advanced Analytics")
        print(f"  {'✓' if limits.code_generation else '✗'} Code Generation")
        print(f"  {'✓' if limits.maturity_tracking else '✗'} Maturity Tracking")

        print(f"\n{Fore.YELLOW}Run /subscription upgrade <tier> to upgrade{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'━' * 50}{Style.RESET_ALL}\n")

        return self.success()


class SubscriptionUpgradeCommand(BaseCommand):
    """Upgrade to a higher tier."""

    def __init__(self):
        super().__init__(
            name="subscription upgrade",
            description="Upgrade to Pro or Enterprise tier",
            usage="subscription upgrade <pro|enterprise>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute subscription upgrade command."""
        user = context.get("user")
        orchestrator = context.get("orchestrator")

        if not user:
            return self.error("User not found")

        if len(args) < 1:
            return self.error("Usage: /subscription upgrade <pro|enterprise>")

        new_tier = args[0].lower()

        if new_tier not in ["pro", "enterprise"]:
            return self.error("Invalid tier. Choose 'pro' or 'enterprise'")

        # Check if already on this tier
        if user.subscription_tier == new_tier:
            return self.error(f"You're already on the {new_tier.title()} tier")

        # Integrate with Stripe for payment processing
        old_tier = user.subscription_tier
        user.subscription_tier = new_tier
        user.subscription_status = "active"
        user.subscription_start = datetime.now()

        # Set subscription end date (30 days from now for monthly billing)
        from datetime import timedelta
        user.subscription_end = datetime.now() + timedelta(days=30)

        # In production, integrate with Stripe:
        try:
            # import stripe
            # stripe.api_key = os.getenv("STRIPE_API_KEY")
            #
            # # Create or retrieve customer
            # customer = stripe.Customer.create_or_retrieve(
            #     email=user.email,
            #     metadata={"user_id": user.username}
            # )
            #
            # # Create subscription
            # subscription = stripe.Subscription.create(
            #     customer=customer.id,
            #     items=[{"price": get_stripe_price_id(new_tier)}],
            #     billing_cycle_anchor=int(user.subscription_start.timestamp())
            # )
            #
            # user.stripe_customer_id = customer.id
            # user.stripe_subscription_id = subscription.id
            pass
        except Exception as e:
            # If Stripe fails, log but don't fail the upgrade
            pass

        orchestrator.database.save_user(user)

        limits = get_tier_limits(new_tier)

        print(f"\n{Fore.GREEN}✓ Successfully upgraded to {limits.name} tier!{Style.RESET_ALL}\n")
        print(f"{Fore.WHITE}Monthly Cost:{Style.RESET_ALL} ${limits.monthly_cost:.2f}")
        print(f"{Fore.WHITE}Features Unlocked:{Style.RESET_ALL}")
        print("  • Multi-LLM Access")
        print(f"  • Team Collaboration (up to {limits.max_team_members or 'unlimited'} members)")
        print("  • Advanced Analytics")
        print("  • Code Generation")
        print("  • Maturity Tracking")
        print(
            f"\n{Fore.CYAN}Note: Payment integration coming soon. For now, this is a manual upgrade.{Style.RESET_ALL}\n"
        )

        return self.success(message=f"Upgraded from {old_tier.title()} to {new_tier.title()}")


class SubscriptionDowngradeCommand(BaseCommand):
    """Downgrade to a lower tier."""

    def __init__(self):
        super().__init__(
            name="subscription downgrade",
            description="Downgrade to Free tier",
            usage="subscription downgrade",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute subscription downgrade command."""
        user = context.get("user")
        orchestrator = context.get("orchestrator")

        if not user:
            return self.error("User not found")

        if user.subscription_tier == "free":
            return self.error("You're already on the Free tier")

        # Warn about feature loss
        print(f"\n{Fore.YELLOW}Warning: Downgrading to Free tier will:{Style.RESET_ALL}")
        print("  • Limit you to 1 active project")
        print("  • Disable team collaboration")
        print("  • Disable multi-LLM access")
        print("  • Disable advanced analytics")
        print("  • Limit to 100 questions/month")

        confirm = input(f"\n{Fore.WHITE}Are you sure? (yes/no): {Style.RESET_ALL}").strip().lower()

        if confirm != "yes":
            return self.error("Downgrade cancelled")

        old_tier = user.subscription_tier
        user.subscription_tier = "free"
        user.subscription_status = "active"

        orchestrator.database.save_user(user)

        print(f"\n{Fore.GREEN}✓ Downgraded to Free tier{Style.RESET_ALL}\n")

        return self.success(message=f"Downgraded from {old_tier.title()} to Free")


class SubscriptionCompareCommand(BaseCommand):
    """Compare subscription tiers."""

    def __init__(self):
        super().__init__(
            name="subscription compare",
            description="Compare all subscription tiers",
            usage="subscription compare",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute subscription compare command."""
        print(f"\n{Fore.CYAN}{'━' * 80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Subscription Tier Comparison{Style.RESET_ALL}\n")

        # Table header
        print(
            f"{Fore.WHITE}{'Feature':<30} {'Free':<15} {'Pro':<15} {'Enterprise':<15}{Style.RESET_ALL}"
        )
        print(f"{Fore.YELLOW}{'━' * 80}{Style.RESET_ALL}")

        # Monthly cost
        print(f"{'Monthly Cost':<30} {'$0':<15} {'$29':<15} {'$99':<15}")

        # Projects
        print(f"{'Active Projects':<30} {'1':<15} {'10':<15} {'Unlimited':<15}")

        # Team members
        print(f"{'Team Members':<30} {'Solo only':<15} {'Up to 5':<15} {'Unlimited':<15}")

        # Questions
        print(f"{'Questions/Month':<30} {'100':<15} {'1,000':<15} {'Unlimited':<15}")

        # Features
        print(f"{'Multi-LLM Access':<30} {'✗':<15} {'✓':<15} {'✓':<15}")
        print(f"{'Advanced Analytics':<30} {'✗':<15} {'✓':<15} {'✓':<15}")
        print(f"{'Code Generation':<30} {'✗':<15} {'✓':<15} {'✓':<15}")
        print(f"{'Maturity Tracking':<30} {'✗':<15} {'✓':<15} {'✓':<15}")

        print(f"\n{Fore.CYAN}{'━' * 80}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Run /subscription upgrade <tier> to upgrade{Style.RESET_ALL}\n")

        return self.success()


class SubscriptionTestingModeCommand(BaseCommand):
    """Enable or disable testing mode for full feature access (HIDDEN from help)."""

    def __init__(self):
        super().__init__(
            name="subscription testing-mode",
            description="Enable/disable testing mode to bypass monetization",
            usage="subscription testing-mode <on|off>",
        )
        # Mark this command as hidden from help/regular users
        self.hidden = True

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute testing mode command."""
        user = context.get("user")
        orchestrator = context.get("orchestrator")

        if not user:
            return self.error("User not found")

        if len(args) < 1:
            return self.error("Usage: /subscription testing-mode <on|off>")

        mode = args[0].lower()

        if mode not in ["on", "off"]:
            return self.error("Invalid mode. Use 'on' or 'off'")

        if mode == "on":
            if user.testing_mode:
                return self.error("Testing mode is already enabled")

            user.testing_mode = True
            orchestrator.database.save_user(user)

            print(f"\n{Fore.GREEN}✓ Testing mode ENABLED{Style.RESET_ALL}\n")
            print(f"{Fore.YELLOW}All monetization restrictions bypassed!{Style.RESET_ALL}\n")
            print("Available for testing:")
            print("  • All premium features unlocked")
            print("  • Unlimited projects")
            print("  • Unlimited team members")
            print("  • Unlimited questions/month")
            print("  • All LLM models available")
            print(f"\n{Fore.CYAN}Run /subscription testing-mode off to disable{Style.RESET_ALL}\n")

            return self.success("Testing mode enabled")

        else:  # mode == "off"
            if not user.testing_mode:
                return self.error("Testing mode is already disabled")

            user.testing_mode = False
            orchestrator.database.save_user(user)

            print(f"\n{Fore.GREEN}✓ Testing mode DISABLED{Style.RESET_ALL}\n")
            print(f"{Fore.YELLOW}Monetization restrictions are now active{Style.RESET_ALL}\n")
            print(f"Your subscription tier: {Fore.CYAN}{user.subscription_tier.upper()}{Style.RESET_ALL}\n")

            return self.success("Testing mode disabled")
