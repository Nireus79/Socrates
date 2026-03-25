"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.Conversation history management commands
"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class ConvSearchCommand(BaseCommand):
    """Search conversation history"""

    def __init__(self):
        super().__init__(
            name="conv search",
            description="Search through conversation history",
            usage="conv search <query>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conversation search command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        if not args:
            query = input(f"{Fore.WHITE}Search query: ").strip()
        else:
            query = " ".join(args)

        if not query:
            return self.error("Search query cannot be empty")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        try:
            # Search conversations in project history
            conversation_history = getattr(project, "conversation_history", []) or []
            query_lower = query.lower()

            # Filter messages matching query
            results = [
                msg for msg in conversation_history if query_lower in msg.get("content", "").lower()
            ]
            count = len(results)

            if count == 0:
                self.print_info(f"No messages found matching '{query}'")
                return self.success()

            self.print_header(
                f"Search Results for '{query}' ({count} match{'es' if count != 1 else ''})"
            )

            for match in results:
                role = match.get("role", "unknown")
                role_color = Fore.GREEN if role == "assistant" else Fore.CYAN
                role_symbol = "[ASSISTANT]" if role == "assistant" else "[USER]"

                print(
                    f"{role_color}{role_symbol} [{match.get('phase', 'unknown')} phase]{Style.RESET_ALL}"
                )
                print(f"   {match.get('timestamp', 'unknown')}")

                content = match.get("content", "")
                if len(content) > 150:
                    content = content[:150] + "..."

                print(f"   {Fore.WHITE}{content}{Style.RESET_ALL}")
                print()

            return self.success(data={"results": results, "count": count})
        except ValueError as e:
            return self.error(str(e))


class ConvSummaryCommand(BaseCommand):
    """Generate a summary of recent conversations"""

    def __init__(self):
        super().__init__(
            name="conv summary",
            description="Generate an AI-powered summary of recent conversations",
            usage="conv summary [limit]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conversation summary command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        # Get limit from args or use default
        limit = 10
        if args:
            try:
                limit = int(args[0])
                if limit < 1 or limit > 100:
                    return self.error("Limit must be between 1 and 100")
            except ValueError:
                return self.error("Invalid limit. Must be a number")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        print(
            f"\n{Fore.YELLOW}Generating conversation summary (last {limit} messages)...{Style.RESET_ALL}"
        )

        try:
            # Generate summary from recent conversations
            conversation_history = getattr(project, "conversation_history", []) or []

            # Get the last 'limit' messages
            recent_messages = (
                conversation_history[-limit:]
                if len(conversation_history) > limit
                else conversation_history
            )

            # Generate summary text
            summary = "Conversation Summary:\n"
            if recent_messages:
                for msg in recent_messages:
                    role = msg.get("role", "unknown").capitalize()
                    content = msg.get("content", "")[:100]  # First 100 chars
                    summary += f"- {role}: {content}\n"
            else:
                summary = "No conversation history available."

            self.print_header("Conversation Summary")
            print(f"{Fore.WHITE}{summary}{Style.RESET_ALL}\n")

            return self.success(data={"summary": summary})
        except ValueError as e:
            return self.error(str(e))
