"""
Natural Language Understanding Handler for Command Interpretation

This module provides NLU capabilities for translating natural language input
into structured slash commands without modifying the existing command system.
"""

import json
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from colorama import Fore, Style

if TYPE_CHECKING:
    from socratic_system.clients.claude_client import ClaudeClient
    from socratic_system.ui.command_handler import CommandHandler


class CommandSuggestion:
    """Represents a suggested command interpretation"""

    def __init__(
        self, command: str, confidence: float, reasoning: str, args: Optional[List[str]] = None
    ):
        """
        Initialize a command suggestion.

        Args:
            command: Full slash command (e.g., "/project create")
            confidence: Confidence score 0.0 to 1.0
            reasoning: Explanation for the suggestion
            args: Optional list of extracted arguments
        """
        self.command = command
        self.confidence = confidence
        self.reasoning = reasoning
        self.args = args or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert suggestion to dictionary"""
        return {
            "command": self.command,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "args": self.args,
        }

    def get_full_command(self) -> str:
        """Get the complete command string with arguments"""
        if self.args:
            return f"{self.command} {' '.join(self.args)}"
        return self.command


class NLUHandler:
    """
    Handles Natural Language Understanding for command interpretation.

    This class translates user's natural language input into structured
    slash commands that can be executed by the CommandHandler.
    """

    def __init__(self, claude_client: "ClaudeClient", command_handler: "CommandHandler"):
        """
        Initialize NLU Handler.

        Args:
            claude_client: ClaudeClient instance for API calls
            command_handler: CommandHandler instance to discover available commands
        """
        self.claude_client = claude_client
        self.command_handler = command_handler
        self.enabled = True  # NLU is enabled by default after login

        # Cache for command metadata (populated lazily)
        self._command_metadata: Optional[str] = None

        # Cache for interpretations (avoids repeated API calls)
        self._interpretation_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_max_size = 50

        # Simple phrase patterns for common commands (avoids API calls)
        self.quick_patterns = {
            r"\b(exit|quit|bye|goodbye)\b": "/exit",
            r"\b(help|what can you do|show help)\b": "/help",
            r"\bclear\b": "/clear",
            r"\bback\b": "/back",
            r"\bmenu\b": "/menu",
            r"\bstatus\b": "/status",
        }

    def is_enabled(self) -> bool:
        """Check if NLU is currently enabled"""
        return self.enabled

    def enable(self) -> None:
        """Enable NLU interpretation"""
        self.enabled = True

    def disable(self) -> None:
        """Disable NLU interpretation"""
        self.enabled = False

    def should_skip_nlu(self, user_input: str) -> bool:
        """
        Determine if we should skip NLU processing.

        Args:
            user_input: Raw user input

        Returns:
            True if NLU should be skipped (already a command or empty)
        """
        stripped = user_input.strip()

        # Skip if empty
        if not stripped:
            return True

        # Skip if starts with slash (already a command)
        if stripped.startswith("/"):
            return True

        # Skip if NLU is disabled
        if not self.enabled:
            return True

        return False

    def try_quick_match(self, user_input: str) -> Optional[str]:
        """
        Try to match input against quick pattern rules.

        This avoids API calls for very common phrases.

        Args:
            user_input: User's natural language input

        Returns:
            Matched command string or None
        """
        input_lower = user_input.lower().strip()

        for pattern, command in self.quick_patterns.items():
            if re.search(pattern, input_lower, re.IGNORECASE):
                return command

        return None

    def _get_cached_interpretation(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Get cached interpretation if available"""
        normalized = user_input.lower().strip()
        return self._interpretation_cache.get(normalized)

    def _cache_interpretation(self, user_input: str, result: Dict[str, Any]) -> None:
        """Cache interpretation result for future use"""
        normalized = user_input.lower().strip()

        # Only cache successful high-confidence results
        if result["status"] == "success":
            # Limit cache size (FIFO)
            if len(self._interpretation_cache) >= self._cache_max_size:
                first_key = next(iter(self._interpretation_cache))
                del self._interpretation_cache[first_key]

            self._interpretation_cache[normalized] = result

    def interpret(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret natural language input and return command suggestions.

        Args:
            user_input: User's natural language input
            context: Application context (user, project, etc.)

        Returns:
            Dictionary with:
                - status: 'success', 'suggestions', 'no_match', or 'error'
                - command: Single command to execute (if high confidence)
                - suggestions: List of CommandSuggestion objects (if low confidence)
                - message: Human-readable message
        """
        # Try cache first
        cached = self._get_cached_interpretation(user_input)
        if cached:
            return cached

        # Try quick pattern matching first
        quick_match = self.try_quick_match(user_input)
        if quick_match:
            result = {
                "status": "success",
                "command": quick_match,
                "message": f"{Fore.CYAN}[NLU] Interpreted as: {quick_match}{Style.RESET_ALL}",
            }
            self._cache_interpretation(user_input, result)
            return result

        # Get command metadata
        command_metadata = self._get_command_metadata()

        # Build context summary
        context_summary = self._build_context_summary(context)

        # Generate NLU prompt
        prompt = self._build_nlu_prompt(user_input, command_metadata, context_summary)

        try:
            # Call Claude API for interpretation
            response_text = self.claude_client.generate_response(
                prompt=prompt,
                max_tokens=800,
                temperature=0.3,  # Lower temperature for consistent parsing
            )

            # Parse Claude's JSON response
            parsed_result = self._parse_nlu_response(response_text)

            if not parsed_result or "interpretations" not in parsed_result:
                return {
                    "status": "no_match",
                    "message": f"{Fore.YELLOW}I couldn't understand that. Type '/help' to see available commands.{Style.RESET_ALL}",
                }

            interpretations = parsed_result["interpretations"]

            if not interpretations:
                return {
                    "status": "no_match",
                    "message": f"{Fore.YELLOW}I couldn't find a matching command. Type '/help' to see available commands.{Style.RESET_ALL}",
                }

            # Convert to CommandSuggestion objects, filtering for valid commands
            suggestions = []
            for interp in interpretations[:3]:  # Limit to top 3
                command = interp["command"]
                # Validate that command exists in command handler
                # Try full command name first, then first word if it's a multi-word command
                command_name = command.lstrip("/")
                if not self.command_handler.get_command(command_name):
                    # If full command doesn't exist, try first word (for aliases)
                    command_name = command_name.split()[0]

                if self.command_handler.get_command(command_name):
                    suggestions.append(
                        CommandSuggestion(
                            command=command,
                            confidence=interp["confidence"],
                            reasoning=interp["reasoning"],
                            args=interp.get("args", []),
                        )
                    )

            # If no valid commands found after filtering, return no_match
            if not suggestions:
                return {
                    "status": "no_match",
                    "message": f"{Fore.YELLOW}I couldn't find a matching command. Type '/help' to see available commands.{Style.RESET_ALL}",
                }

            # Determine if we should execute directly or show suggestions
            top_suggestion = suggestions[0]

            # High confidence threshold: execute directly
            if top_suggestion.confidence >= 0.85:
                result = {
                    "status": "success",
                    "command": top_suggestion.get_full_command(),
                    "message": f"{Fore.CYAN}[NLU] Interpreted as: {top_suggestion.get_full_command()}{Style.RESET_ALL}",
                }
                self._cache_interpretation(user_input, result)
                return result

            # Medium confidence: show suggestions
            elif top_suggestion.confidence >= 0.5:
                return {
                    "status": "suggestions",
                    "suggestions": suggestions,
                    "message": f"{Fore.YELLOW}Did you mean one of these?{Style.RESET_ALL}",
                }

            # Low confidence: no match
            else:
                return {
                    "status": "no_match",
                    "message": f"{Fore.YELLOW}I couldn't understand that. Type '/help' to see available commands.{Style.RESET_ALL}",
                }

        except Exception as e:
            print(f"{Fore.RED}NLU Error: {str(e)}{Style.RESET_ALL}")
            return {
                "status": "error",
                "message": f"{Fore.RED}Error interpreting command. Type '/help' for available commands.{Style.RESET_ALL}",
            }

    def _get_command_metadata(self) -> str:
        """
        Get formatted command metadata for the prompt.

        Returns:
            Formatted string describing all available commands
        """
        if self._command_metadata is not None:
            return self._command_metadata

        # Get all commands (must use public API)
        try:
            commands = self.command_handler.commands
        except AttributeError:
            return "No commands available"

        # Organize by category
        from typing import Any

        categories: dict[str, list[dict[str, Any]]] = {}
        for name, cmd in commands.items():
            parts = name.split()
            category = parts[0] if parts else "system"

            if category not in categories:
                categories[category] = []

            categories[category].append(
                {
                    "name": name,
                    "usage": cmd.usage or name,
                    "description": cmd.description or "No description",
                }
            )

        # Format as text
        metadata_parts = []
        for category in sorted(categories.keys()):
            cmds: list[dict[str, Any]] = categories[category]
            metadata_parts.append(f"\n{category.upper()} COMMANDS:")
            for cmd in cmds:
                metadata_parts.append(f"  /{cmd['usage']} - {cmd['description']}")

        self._command_metadata = "\n".join(metadata_parts)
        return self._command_metadata

    def _build_context_summary(self, context: Dict[str, Any]) -> str:
        """
        Build a summary of current application context.

        Args:
            context: Application context dictionary

        Returns:
            Formatted context summary string
        """
        parts = []

        user = context.get("user")
        if user:
            parts.append(f"Logged in as: {user.username}")

        project = context.get("project")
        if project:
            parts.append(f"Current project: {project.name}")
            parts.append(f"Project phase: {project.phase}")
        else:
            parts.append("No project loaded")

        return " | ".join(parts) if parts else "No context"

    def _build_nlu_prompt(
        self, user_input: str, command_metadata: str, context_summary: str
    ) -> str:
        """
        Build the prompt for Claude to interpret natural language.

        Args:
            user_input: User's natural language input
            command_metadata: Formatted list of available commands
            context_summary: Current application context

        Returns:
            Complete prompt string
        """
        return f"""You are a command interpreter for the Socrates AI CLI.

CURRENT CONTEXT:
{context_summary}

AVAILABLE COMMANDS:
{command_metadata}

USER INPUT: "{user_input}"

Your task is to interpret the user's natural language input and match it to one or more available commands.

Return ONLY valid JSON in this exact format:
{{
    "interpretations": [
        {{
            "command": "/exact-command-name",
            "confidence": 0.95,
            "reasoning": "Brief explanation of why this matches",
            "args": ["arg1", "arg2"]
        }}
    ]
}}

IMPORTANT RULES:
1. "command" must be an exact command from the available commands list (including the / prefix)
2. "confidence" must be a float between 0.0 and 1.0
3. "args" should contain any additional arguments extracted from the user input (can be empty list)
4. Include 1-3 interpretations, ordered by confidence (highest first)
5. If no commands match, return {{"interpretations": []}}
6. DO NOT make up commands - only use commands from the available list
7. Consider the current context when interpreting (e.g., user logged in, project loaded)

Examples:
- "I want to create a new project called MyApp" → {{"interpretations": [{{"command": "/project create", "confidence": 0.95, "reasoning": "Clear intent to create a project", "args": ["MyApp"]}}]}}
- "show me help" → {{"interpretations": [{{"command": "/help", "confidence": 0.98, "reasoning": "Direct request for help", "args": []}}]}}
- "what's the status" → {{"interpretations": [{{"command": "/status", "confidence": 0.90, "reasoning": "Asking for status", "args": []}}, {{"command": "/project status", "confidence": 0.75, "reasoning": "Could be project-specific status", "args": []}}]}}

Return only the JSON response, no additional text."""

    def _parse_nlu_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse Claude's JSON response into structured data.

        Args:
            response_text: Raw response text from Claude

        Returns:
            Parsed dictionary or None if parsing fails
        """
        try:
            # Clean up the response
            text = response_text.strip()

            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            elif text.startswith("```"):
                text = text.replace("```", "").strip()

            # Find JSON object
            start = text.find("{")
            end = text.rfind("}") + 1

            if start >= 0 and end > start:
                json_text = text[start:end]
                parsed = json.loads(json_text)
                return parsed

            return None

        except (json.JSONDecodeError, ValueError) as e:
            print(f"{Fore.YELLOW}[WARN] Failed to parse NLU response: {e}{Style.RESET_ALL}")
            return None


class SuggestionDisplay:
    """Helper class for displaying command suggestions to the user"""

    @staticmethod
    def show_suggestions(suggestions: List[CommandSuggestion]) -> Optional[str]:
        """
        Display suggestions to user and get their selection.

        Args:
            suggestions: List of CommandSuggestion objects

        Returns:
            Selected command string or None if cancelled
        """
        print(f"\n{Fore.YELLOW}I found these possible commands:{Style.RESET_ALL}\n")

        for i, suggestion in enumerate(suggestions, 1):
            confidence_display = f"{suggestion.confidence * 100:.0f}%"
            print(
                f"  {Fore.CYAN}[{i}]{Style.RESET_ALL} {suggestion.get_full_command()} "
                f"{Fore.GREEN}({confidence_display}){Style.RESET_ALL}"
            )
            print(f"      {Fore.WHITE}{suggestion.reasoning}{Style.RESET_ALL}\n")

        print(f"  {Fore.CYAN}[0]{Style.RESET_ALL} None of these / Cancel\n")

        # Get user selection
        while True:
            try:
                choice = input(
                    f"{Fore.WHITE}Select option (0-{len(suggestions)}): {Style.RESET_ALL}"
                ).strip()

                if not choice:
                    continue

                choice_num = int(choice)

                if choice_num == 0:
                    print(
                        f"{Fore.YELLOW}Cancelled. Type '/help' to see available commands.{Style.RESET_ALL}"
                    )
                    return None

                if 1 <= choice_num <= len(suggestions):
                    selected = suggestions[choice_num - 1]
                    return selected.get_full_command()

                print(
                    f"{Fore.RED}Invalid choice. Please enter 0-{len(suggestions)}.{Style.RESET_ALL}"
                )

            except ValueError:
                print(f"{Fore.RED}Please enter a number.{Style.RESET_ALL}")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
                return None
