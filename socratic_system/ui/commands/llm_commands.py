"""Multi-LLM Provider management commands"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class LLMCommand(BaseCommand):
    """Manage multiple LLM providers"""

    def __init__(self):
        super().__init__(
            name="llm",
            description="Manage LLM providers (Claude, OpenAI, Gemini, Ollama)",
            usage="llm [list|config|set|models|usage|key|stats]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM command"""
        orchestrator = context.get("orchestrator")
        user = context.get("user")

        if not orchestrator or not user:
            return self.error("Orchestrator or user not available")

        if not args:
            return self._show_help()

        subcommand = args[0].lower()
        return self._dispatch_subcommand(subcommand, args[1:], orchestrator, user)

    def _dispatch_subcommand(
        self, subcommand: str, args: List[str], orchestrator, user
    ) -> Dict[str, Any]:
        """Dispatch subcommand to appropriate handler"""
        subcommand_map = {
            "list": lambda: self._list_providers(orchestrator),
            "config": lambda: self._show_config(orchestrator, user),
            "set": lambda: self._set_default(args, orchestrator, user),
            "use": lambda: self._set_model(args, orchestrator, user),
            "models": lambda: self._show_models(args, orchestrator),
            "key": lambda: self._manage_key(args, orchestrator, user),
            "auth-method": lambda: self._set_auth_method(args, orchestrator, user),
            "stats": lambda: self._show_stats(args, orchestrator, user),
            "help": lambda: self._show_help(),
        }

        if subcommand in subcommand_map:
            return subcommand_map[subcommand]()
        return self.error(f"Unknown subcommand: {subcommand}\nTry: llm help")

    def _show_help(self) -> Dict[str, Any]:
        """Show help for LLM commands"""
        help_text = f"""
{Fore.CYAN}LLM Provider Management{Style.RESET_ALL}

{Fore.WHITE}Subcommands:{Style.RESET_ALL}
  {Fore.GREEN}list{Style.RESET_ALL}                 List all available LLM providers
  {Fore.GREEN}config{Style.RESET_ALL}               Show your current provider configuration
  {Fore.GREEN}set{Style.RESET_ALL} <provider>       Set default provider (claude, openai, gemini, ollama)
  {Fore.GREEN}use{Style.RESET_ALL} <provider> <model> Set model to use for a provider
  {Fore.GREEN}models{Style.RESET_ALL} <provider>    Show available models for a provider
  {Fore.GREEN}key{Style.RESET_ALL}                  Manage API keys (add, remove, list)
  {Fore.GREEN}auth-method{Style.RESET_ALL} <type>  Set Claude auth method (api_key or subscription)
  {Fore.GREEN}stats{Style.RESET_ALL}                Show usage statistics and costs
  {Fore.GREEN}help{Style.RESET_ALL}                 Show this help message

{Fore.WHITE}Examples:{Style.RESET_ALL}
  /llm list                                - List all providers
  /llm config                              - Show your current configuration
  /llm set claude                          - Set Claude as default provider
  /llm use claude claude-3-5-sonnet-20241022 - Use specific Claude model
  /llm models openai                       - Show OpenAI models
  /llm use openai gpt-4o                   - Use GPT-4o for OpenAI
  /llm key add openai <key>                - Add OpenAI API key
  /llm auth-method subscription            - Use Claude subscription tokens
  /llm auth-method api_key                 - Use Claude API key
  /llm stats                               - Show usage stats (last 30 days)
  /llm stats openai 7                      - Show OpenAI stats (last 7 days)
"""
        print(help_text)
        return self.success(message="Help displayed")

    def _list_providers(self, orchestrator) -> Dict[str, Any]:
        """List all available providers"""
        print(f"\n{Fore.CYAN}Available LLM Providers{Style.RESET_ALL}\n")

        result = orchestrator.process_request("multi_llm", {"action": "list_providers"})

        if result["status"] != "success":
            return self.error(result.get("message", "Failed to list providers"))

        providers = result.get("providers", [])

        for provider in providers:
            available = (
                Fore.GREEN + "Available" + Style.RESET_ALL
                if provider.get("available")
                else Fore.RED + "Unavailable" + Style.RESET_ALL
            )
            requires_key = "API Key Required" if provider.get("requires_api_key") else "No API Key"
            models_count = len(provider.get("models", []))

            print(f"{Fore.WHITE}{provider['display_name']:<30}{Style.RESET_ALL}")
            print(
                f"  Provider: {Fore.CYAN}{provider['provider']:<20}{Style.RESET_ALL} Status: {available}"
            )
            print(f"  Models: {models_count:<20} {requires_key}")
            print(
                f"  Cost: ${provider.get('cost_per_1k_input_tokens', 0):.6f}/1K input, ${provider.get('cost_per_1k_output_tokens', 0):.6f}/1K output"
            )
            print()

        return self.success(data={"providers_count": len(providers)})

    def _show_config(self, orchestrator, user) -> Dict[str, Any]:
        """Show user's provider configuration"""
        print(f"\n{Fore.CYAN}Your LLM Provider Configuration{Style.RESET_ALL}\n")

        result = orchestrator.process_request(
            "multi_llm", {"action": "get_provider_config", "user_id": user.username}
        )

        if result["status"] != "success":
            return self.error(result.get("message", "Failed to get configuration"))

        default_provider = result.get("default_provider", "claude")
        providers = result.get("providers", [])

        print(f"Default Provider: {Fore.GREEN}{default_provider}{Style.RESET_ALL}\n")
        print(f"{Fore.WHITE}Configured Providers:{Style.RESET_ALL}")

        for provider in providers:
            is_default = " (default)" if provider.get("is_default") else ""
            enabled = "Enabled" if provider.get("enabled") else "Disabled"
            model = provider.get("settings", {}).get("model", "N/A")

            print(
                f"  {Fore.CYAN}{provider['provider'].upper():<15}{Style.RESET_ALL} {enabled:<10} Model: {model}{Fore.GREEN}{is_default}{Style.RESET_ALL}"
            )

        return self.success(data={"default_provider": default_provider})

    def _set_default(self, args: List[str], orchestrator, user) -> Dict[str, Any]:
        """Set default provider"""
        if not args:
            return self.error("Provider name required. Usage: /llm set <provider>")

        provider = args[0].lower()

        result = orchestrator.process_request(
            "multi_llm",
            {"action": "set_default_provider", "user_id": user.username, "provider": provider},
        )

        if result["status"] != "success":
            return self.error(result.get("message", "Failed to set default provider"))

        print(f"\n{Fore.GREEN}✓ Default provider set to {provider}{Style.RESET_ALL}\n")
        return self.success(message=f"Default provider set to {provider}")

    def _set_model(self, args: List[str], orchestrator, user) -> Dict[str, Any]:
        """Set model for a provider"""
        if len(args) < 2:
            return self.error(
                "Provider and model name required. Usage: /llm use <provider> <model>"
            )

        provider = args[0].lower()
        model = " ".join(args[1:])  # Allow model names with spaces

        result = orchestrator.process_request(
            "multi_llm",
            {
                "action": "set_provider_model",
                "user_id": user.username,
                "provider": provider,
                "model": model,
            },
        )

        if result["status"] != "success":
            return self.error(result.get("message", "Failed to set model"))

        print(f"\n{Fore.GREEN}✓ Model set to {model} for {provider}{Style.RESET_ALL}\n")
        return self.success(message=f"Model set to {model} for {provider}")

    def _show_models(self, args: List[str], orchestrator) -> Dict[str, Any]:
        """Show available models for a provider"""
        if not args:
            return self.error("Provider name required. Usage: /llm models <provider>")

        provider = args[0].lower()

        result = orchestrator.process_request(
            "multi_llm", {"action": "get_provider_models", "provider": provider}
        )

        if result["status"] != "success":
            return self.error(result.get("message", f"Unknown provider: {provider}"))

        print(f"\n{Fore.CYAN}Models for {provider.upper()}{Style.RESET_ALL}\n")

        models = result.get("models", [])
        default_model = result.get("default_model", "")
        context_window = result.get("context_window", "N/A")

        print(f"Context Window: {Fore.GREEN}{context_window:,} tokens{Style.RESET_ALL}")
        print(
            f"Streaming: {Fore.GREEN}Yes{Style.RESET_ALL if result.get('supports_streaming') else Fore.RED + 'No' + Style.RESET_ALL}"
        )
        print(
            f"Vision: {Fore.GREEN}Yes{Style.RESET_ALL if result.get('supports_vision') else Fore.RED + 'No' + Style.RESET_ALL}\n"
        )

        print(f"{Fore.WHITE}Available Models:{Style.RESET_ALL}")
        for model in models:
            is_default = (
                f" {Fore.GREEN}(default){Style.RESET_ALL}" if model == default_model else ""
            )
            print(f"  • {model}{is_default}")

        return self.success(data={"models": models, "context_window": context_window})

    def _manage_key(self, args: List[str], orchestrator, user) -> Dict[str, Any]:
        """Manage API keys"""
        if not args:
            return self.error("Usage: /llm key [add|remove] <provider> [api_key]")

        action = args[0].lower()

        if action == "add":
            if len(args) < 3:
                return self.error("Usage: /llm key add <provider> <api_key>")

            provider = args[1].lower()
            api_key = args[2]

            result = orchestrator.process_request(
                "multi_llm",
                {
                    "action": "add_api_key",
                    "user_id": user.username,
                    "provider": provider,
                    "api_key": api_key,
                },
            )

            if result["status"] != "success":
                return self.error(result.get("message", "Failed to add API key"))

            print(f"\n{Fore.GREEN}✓ API key added for {provider}{Style.RESET_ALL}\n")
            return self.success(message=f"API key added for {provider}")

        elif action == "remove":
            if len(args) < 2:
                return self.error("Usage: /llm key remove <provider>")

            provider = args[1].lower()

            result = orchestrator.process_request(
                "multi_llm",
                {"action": "remove_api_key", "user_id": user.username, "provider": provider},
            )

            if result["status"] != "success":
                return self.error(result.get("message", "Failed to remove API key"))

            print(f"\n{Fore.GREEN}✓ API key removed for {provider}{Style.RESET_ALL}\n")
            return self.success(message=f"API key removed for {provider}")

        else:
            return self.error(f"Unknown key action: {action}")

    def _show_stats(self, args: List[str], orchestrator, user) -> Dict[str, Any]:
        """Show usage statistics and costs"""
        provider = args[0].lower() if args else None
        days = int(args[1]) if len(args) > 1 else 30

        result = orchestrator.process_request(
            "multi_llm",
            {
                "action": "get_usage_stats",
                "user_id": user.username,
                "provider": provider,
                "days": days,
            },
        )

        if result["status"] != "success":
            return self.error(result.get("message", "Failed to get usage stats"))

        print(f"\n{Fore.CYAN}LLM Usage Statistics (Last {days} Days){Style.RESET_ALL}\n")

        total_tokens = result.get("total_tokens", 0)
        total_cost = result.get("total_cost", 0.0)
        daily_average = result.get("daily_average", 0)
        success_count = result.get("success_count", 0)
        error_count = result.get("error_count", 0)
        avg_latency = result.get("avg_latency_ms", 0)

        print(f"Total Tokens: {Fore.GREEN}{total_tokens:,}{Style.RESET_ALL}")
        print(f"Total Cost: {Fore.GREEN}${total_cost:.4f}{Style.RESET_ALL}")
        print(f"Daily Average: {Fore.GREEN}{daily_average:,} tokens{Style.RESET_ALL}")
        print(
            f"Success Rate: {Fore.GREEN}{success_count}{Style.RESET_ALL} / {success_count + error_count} requests"
        )
        print(f"Avg Latency: {Fore.GREEN}{avg_latency:.0f}ms{Style.RESET_ALL}\n")

        by_provider = result.get("by_provider", {})
        if by_provider:
            print(f"{Fore.WHITE}By Provider:{Style.RESET_ALL}")
            for prov, stats in by_provider.items():
                tokens = stats.get("tokens", 0)
                cost = stats.get("cost", 0.0)
                requests = stats.get("requests", 0)
                print(
                    f"  {prov.upper():<10} {tokens:>10,} tokens  ${cost:>8.4f}  ({requests} requests)"
                )

        return self.success(
            data={
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "by_provider": by_provider,
            }
        )

    def _set_auth_method(
        self, args: List[str], orchestrator, user
    ) -> Dict[str, Any]:
        """Set Claude authentication method (api_key or subscription)"""
        if not args:
            print(f"\n{Fore.CYAN}Claude Authentication Methods{Style.RESET_ALL}\n")
            print(f"Current method: {Fore.WHITE}{user.claude_auth_method}{Style.RESET_ALL}\n")
            print(f"{Fore.WHITE}Available methods:{Style.RESET_ALL}")
            print(f"  {Fore.GREEN}api_key{Style.RESET_ALL}       - Use Anthropic API key (default)")
            print(f"                    Set: {Fore.YELLOW}export ANTHROPIC_API_KEY=sk-...{Style.RESET_ALL}")
            print(f"  {Fore.GREEN}subscription{Style.RESET_ALL}   - Use Claude subscription tokens")
            print(f"                    Set: {Fore.YELLOW}export ANTHROPIC_SUBSCRIPTION_TOKEN=...{Style.RESET_ALL}\n")
            print(f"{Fore.WHITE}Usage:{Style.RESET_ALL}")
            print("  /llm auth-method api_key")
            print("  /llm auth-method subscription\n")
            return self.success(message="Auth method information displayed")

        auth_method = args[0].lower()

        # Validate auth method
        valid_methods = ["api_key", "subscription"]
        if auth_method not in valid_methods:
            return self.error(
                f"Invalid auth method: {auth_method}\n"
                f"Valid options: {', '.join(valid_methods)}"
            )

        # Check if required env var is set
        if auth_method == "subscription":
            import os
            if not os.getenv("ANTHROPIC_SUBSCRIPTION_TOKEN"):
                return self.error(
                    "Subscription token not configured.\n"
                    f"{Fore.YELLOW}Please set: export ANTHROPIC_SUBSCRIPTION_TOKEN=<your-token>{Style.RESET_ALL}"
                )
        else:  # api_key
            import os
            api_key = os.getenv("ANTHROPIC_API_KEY", os.getenv("API_KEY_CLAUDE"))
            if not api_key:
                return self.error(
                    "API key not configured.\n"
                    f"{Fore.YELLOW}Please set: export ANTHROPIC_API_KEY=sk-...{Style.RESET_ALL}"
                )

        # Update user preference
        user.claude_auth_method = auth_method
        orchestrator.database.save_user(user)

        print(f"\n{Fore.GREEN}Success!{Style.RESET_ALL}")
        print(f"Claude authentication method set to: {Fore.WHITE}{auth_method}{Style.RESET_ALL}\n")

        return self.success(
            message=f"Auth method changed to {auth_method}",
            data={"auth_method": auth_method}
        )

    # Utility methods from base
    def success(self, message: str = "Success", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Return success response"""
        return {"status": "success", "message": message, "data": data or {}}

    def error(self, message: str) -> Dict[str, Any]:
        """Return error response"""
        print(f"{Fore.RED}Error: {message}{Style.RESET_ALL}")
        return {"status": "error", "message": message}
