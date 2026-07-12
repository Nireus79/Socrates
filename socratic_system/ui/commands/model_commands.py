"""Model selection and switching commands"""

import asyncio
from typing import Any

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class ModelCommand(BaseCommand):
    """Select and switch Claude model at runtime"""

    def __init__(self):
        super().__init__(
            name="model",
            description="Select and switch Claude model",
            usage="model [status|list|set <model_name>]",
        )

    def execute(self, args: list[str], context: dict[str, Any]) -> dict[str, Any]:
        """Execute model command"""
        orchestrator = context.get("orchestrator")
        app = context.get("app")

        if not orchestrator or not app:
            return self.error("Orchestrator or app not available")

        if not args:
            return self._show_status(orchestrator)

        subcommand = args[0].lower()

        if subcommand == "status":
            return self._show_status(orchestrator)
        elif subcommand == "list":
            return self._list_models(orchestrator)
        elif subcommand == "set":
            return self._set_model(args[1:], orchestrator, app, context)
        else:
            return self.error(f"Unknown subcommand: {subcommand}")

    def _show_status(self, orchestrator) -> dict[str, Any]:
        """Show current model status"""
        current_model = orchestrator.config.claude_model

        print(f"\n{Fore.CYAN}Current Claude Model{Style.RESET_ALL}")
        print(f"  Model: {Fore.GREEN}{current_model}{Style.RESET_ALL}")

        return self.success(data={"current_model": current_model})

    def _list_models(self, orchestrator) -> dict[str, Any]:
        """List available Claude models from Anthropic API"""
        print(f"\n{Fore.CYAN}Available Claude Models{Style.RESET_ALL}")
        current_model = orchestrator.config.claude_model

        try:
            # Discover models dynamically
            from socratic_system.orchestration.llm_discovery import discover_claude_models

            models = asyncio.run(discover_claude_models())
            if not models:
                print(
                    f"{Fore.YELLOW}  No models discovered - check ANTHROPIC_API_KEY{Style.RESET_ALL}"
                )
                return self.error("Failed to discover Claude models")

            for model in models:
                is_current = (
                    " " + Fore.GREEN + "✓ (current)" + Style.RESET_ALL
                    if model == current_model
                    else ""
                )
                print(f"  {Fore.WHITE}{model}{Style.RESET_ALL}{is_current}")

            return self.success(data={"models": models})
        except Exception as e:
            print(f"{Fore.RED}Error discovering models: {e}{Style.RESET_ALL}")
            return self.error(f"Failed to discover models: {e}")

    def _set_model(
        self, args: list[str], orchestrator, app, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Set/switch to a Claude model"""
        if not args:
            return self.error("Model name required. Usage: /model set <model_name>")

        model_input = args[0]

        try:
            # Discover available models dynamically
            from socratic_system.orchestration.llm_discovery import discover_claude_models

            available_models = asyncio.run(discover_claude_models())
            if not available_models:
                return self.error("Failed to discover Claude models - check ANTHROPIC_API_KEY")

            # Case-insensitive search
            matching_model = None
            for model in available_models:
                if model.lower() == model_input.lower():
                    matching_model = model
                    break

            if not matching_model:
                print("Available models:")
                for model in available_models:
                    print(f"  - {model}")
                return self.error(f"Model not found: {model_input}")

            # Update orchestrator
            if orchestrator.set_model(matching_model):
                # Update user's preferred model if logged in
                if app.current_user:
                    app.current_user.preferred_model = matching_model
                    orchestrator.database.save_user(app.current_user)

                self.print_success(
                    f"Model switched to {Fore.GREEN}{matching_model}{Style.RESET_ALL}"
                )
                return self.success(data={"new_model": matching_model})
            else:
                return self.error("Failed to switch model")
        except Exception as e:
            return self.error(f"Error setting model: {e}")
