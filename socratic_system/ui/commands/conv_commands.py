"""Conversation history management commands"""

from typing import Dict, Any, List
from colorama import Fore, Style
from socratic_system.ui.commands.base import BaseCommand


class ConvSearchCommand(BaseCommand):
    """Search conversation history"""

    def __init__(self):
        super().__init__(
            name="conv search",
            description="Search through conversation history",
            usage="conv search <query>"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conversation search command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        if not args:
            query = input(f"{Fore.WHITE}Search query: ").strip()
        else:
            query = ' '.join(args)

        if not query:
            return self.error("Search query cannot be empty")

        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Search conversations
        result = orchestrator.process_request('context_analyzer', {
            'action': 'search_conversations',
            'project': project,
            'query': query
        })

        if result['status'] == 'success':
            results = result.get('results', [])
            count = result.get('count', 0)

            if count == 0:
                self.print_info(f"No messages found matching '{query}'")
                return self.success()

            self.print_header(f"Search Results for '{query}' ({count} match{'es' if count != 1 else ''})")

            for match in results:
                role = match.get('role', 'unknown')
                role_color = Fore.GREEN if role == 'assistant' else Fore.CYAN
                role_symbol = "[ASSISTANT]" if role == 'assistant' else "[USER]"

                print(f"{role_color}{role_symbol} [{match.get('phase', 'unknown')} phase]{Style.RESET_ALL}")
                print(f"   {match.get('timestamp', 'unknown')}")

                content = match.get('content', '')
                if len(content) > 150:
                    content = content[:150] + "..."

                print(f"   {Fore.WHITE}{content}{Style.RESET_ALL}")
                print()

            return self.success(data={'results': results, 'count': count})
        else:
            return self.error(result.get('message', 'Failed to search conversations'))


class ConvSummaryCommand(BaseCommand):
    """Generate a summary of recent conversations"""

    def __init__(self):
        super().__init__(
            name="conv summary",
            description="Generate an AI-powered summary of recent conversations",
            usage="conv summary [limit]"
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

        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator or not project:
            return self.error("Required context not available")

        print(f"\n{Fore.YELLOW}Generating conversation summary (last {limit} messages)...{Style.RESET_ALL}")

        # Generate summary
        result = orchestrator.process_request('context_analyzer', {
            'action': 'generate_summary',
            'project': project,
            'limit': limit
        })

        if result['status'] == 'success':
            summary = result.get('summary', '')

            self.print_header("Conversation Summary")
            print(f"{Fore.WHITE}{summary}{Style.RESET_ALL}\n")

            return self.success(data={'summary': summary})
        else:
            return self.error(result.get('message', 'Failed to generate summary'))
