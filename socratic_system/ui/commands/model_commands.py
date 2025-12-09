"""Model selection and switching commands"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand

# Available models mapping
AVAILABLE_MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-3-5-sonnet-20241022",
    "opus": "claude-opus-4-20250514",
}


class ModelCommand(BaseCommand):
    """Select and switch Claude model at runtime"""

    def __init__(self):
        super().__init__(
            name="model",
            description="Select and switch Claude model",
            usage="model [status|list|set <model_name>]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
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

    def _show_status(self, orchestrator) -> Dict[str, Any]:
        """Show current model status"""
        current_model = orchestrator.config.claude_model
        model_name = self._get_model_name_from_full(current_model)

        print(f"\n{Fore.CYAN}Current Model{Style.RESET_ALL}")
        print(f"  Model: {Fore.GREEN}{model_name}{Style.RESET_ALL} ({current_model})")

        return self.success(data={"current_model": current_model})

    def _list_models(self, orchestrator) -> Dict[str, Any]:
        """List available models"""
        print(f"\n{Fore.CYAN}Available Models{Style.RESET_ALL}")
        current_model = orchestrator.config.claude_model

        for short_name, full_name in AVAILABLE_MODELS.items():
            is_current = " " + Fore.GREEN + "✓ (current)" + Style.RESET_ALL if full_name == current_model else ""
            print(f"  {Fore.WHITE}{short_name:<10}{Style.RESET_ALL} {full_name}{is_current}")

        return self.success(data={"models": AVAILABLE_MODELS})

    def _set_model(self, args: List[str], orchestrator, app, context: Dict[str, Any]) -> Dict[str, Any]:
        """Set/switch to a new model"""
        if not args:
            return self.error("Model name required. Usage: /model set <model_name>")

        model_input = args[0].lower()

        # Check if input is a short name
        if model_input in AVAILABLE_MODELS:
            full_model_name = AVAILABLE_MODELS[model_input]
        # Check if input is a full model name
        elif model_input in AVAILABLE_MODELS.values():
            full_model_name = model_input
        else:
            available = ", ".join(AVAILABLE_MODELS.keys())
            return self.error(f"Unknown model: {model_input}. Available: {available}")

        # Update orchestrator
        if orchestrator.set_model(full_model_name):
            # Update user's preferred model if logged in
            if app.current_user:
                orchestrator.database.update_user_model_preference(app.current_user.username, full_model_name)
                app.current_user.preferred_model = full_model_name

            model_short_name = self._get_model_name_from_full(full_model_name)
            self.print_success(f"Model switched to {Fore.GREEN}{model_short_name}{Style.RESET_ALL}")

            return self.success(data={"new_model": full_model_name})
        else:
            return self.error("Failed to switch model")

    @staticmethod
    def _get_model_name_from_full(full_model_name: str) -> str:
        """Get short model name from full model name"""
        for short_name, full_name in AVAILABLE_MODELS.items():
            if full_name == full_model_name:
                return short_name
        return "unknown"
