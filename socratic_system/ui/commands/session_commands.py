"""Socratic session commands (conversation, phases, etc.)"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class ChatCommand(BaseCommand):
    """Unified interactive session with toggleable Socratic and direct modes"""

    def __init__(self):
        super().__init__(
            name="chat",
            description="Start interactive chat session (Socratic or direct Q&A mode)",
            usage="chat",
        )

    def _confirm_insights_interactive(self, insights: Dict, orchestrator) -> Dict:
        """Interactive confirmation dialog for insights with detailed options

        Returns:
            Dict: Confirmed/modified insights, or None if all rejected
        """
        confirmed_insights = {}
        insight_categories = [
            ("goals", "Goals", insights.get("goals")),
            ("requirements", "Requirements", insights.get("requirements")),
            ("tech_stack", "Tech Stack", insights.get("tech_stack")),
            ("constraints", "Constraints", insights.get("constraints")),
        ]

        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"Review Extracted Insights{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

        for category_key, category_name, category_values in insight_categories:
            if not category_values:
                continue

            values_str = self._format_category_values(category_values)
            print(f"{Fore.GREEN}{category_name}:{Style.RESET_ALL}")
            print(f"    {values_str}\n")

            confirmed_value = self._process_insight_choice(
                category_name, category_values, orchestrator
            )
            if confirmed_value is not None:
                confirmed_insights[category_key] = confirmed_value

        return self._return_confirmed_insights(confirmed_insights)

    def _format_category_values(self, category_values) -> str:
        """Format category values for display"""
        if isinstance(category_values, list):
            return "\n    ".join([f"• {v}" for v in category_values if v])
        return str(category_values)

    def _process_insight_choice(self, category_name: str, category_values, orchestrator):
        """Process user's choice for a single insight. Returns confirmed value or None."""
        while True:
            choice = self._get_user_choice(category_name)

            if choice in ["y", "yes"]:
                print(f"{Fore.GREEN}✓ {category_name} confirmed{Style.RESET_ALL}\n")
                return category_values

            if choice in ["n", "no"]:
                print(f"{Fore.MAGENTA}✗ {category_name} skipped{Style.RESET_ALL}\n")
                return None

            if choice in ["e", "explain"]:
                explanation = self._get_insight_explanation(
                    category_name, category_values, orchestrator
                )
                print(f"\n{Fore.CYAN}Explanation:{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{explanation}{Style.RESET_ALL}\n")
                continue

            if choice in ["c", "custom"]:
                custom_value = self._get_custom_values(category_name)
                if custom_value is not None:
                    print(f"{Fore.GREEN}✓ Custom {category_name.lower()} added{Style.RESET_ALL}\n")
                    return custom_value
                print(f"{Fore.MAGENTA}✗ No input provided, skipping{Style.RESET_ALL}\n")
                return None

            print(f"{Fore.RED}Invalid choice. Please enter y, n, e, or c{Style.RESET_ALL}\n")

    def _get_user_choice(self, category_name: str) -> str:
        """Get user's choice for insight confirmation"""
        print(f"{Fore.YELLOW}Options:{Style.RESET_ALL}")
        print("  (y)es - Keep this insight")
        print("  (n)o - Skip this insight")
        print("  (e)xplain - Get explanation for this insight")
        print(f"  (c)ustom - Write custom {category_name.lower()}")
        print(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}", end="")
        return input(f"{Fore.WHITE}").strip().lower()

    def _get_custom_values(self, category_name: str):
        """Get custom values from user. Returns list or None."""
        print(
            f"{Fore.CYAN}Enter custom {category_name.lower()} (comma-separated):{Style.RESET_ALL}"
        )
        custom_input = input(f"{Fore.WHITE}> ").strip()
        if custom_input:
            return [item.strip() for item in custom_input.split(",") if item.strip()]
        return None

    def _return_confirmed_insights(self, confirmed_insights: Dict):
        """Return confirmed insights or None if empty"""
        if not confirmed_insights:
            return None

        print(f"{Fore.GREEN}{'='*60}")
        print(
            f"Summary: {len(confirmed_insights)} insight category/categories confirmed{Style.RESET_ALL}"
        )
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
        return confirmed_insights

    def _get_insight_explanation(self, category_name: str, values, orchestrator) -> str:
        """Get explanation for why an insight was extracted"""
        try:
            if isinstance(values, list):
                values_str = ", ".join([str(v) for v in values if v])
            else:
                values_str = str(values)

            prompt = f"""Briefly explain in 1-2 sentences why the following {category_name.lower()} were extracted from the user's question:

{category_name}: {values_str}

Focus on the connection between the user's statement and these insights."""

            explanation = orchestrator.claude_client.generate_response(prompt)
            return explanation
        except Exception as e:
            return f"Could not generate explanation: {str(e)}"

    def _handle_command(self, response: str, context: Dict[str, Any]) -> tuple:
        """Handle / commands. Returns (should_continue, continue_session)"""
        app = context.get("app")
        project = context.get("project")

        # Handle /mode command
        if response.startswith("/mode"):
            parts = response.split()
            if len(parts) > 1 and parts[1] in ["socratic", "direct"]:
                project.chat_mode = parts[1]
                print(f"{Fore.GREEN}✓ Mode switched to: {parts[1]}{Style.RESET_ALL}")
                return True, True  # Continue session
            else:
                print(f"{Fore.YELLOW}Usage: /mode <socratic|direct>{Style.RESET_ALL}")
                return True, True  # Continue session

        # Handle other commands
        app.command_handler.execute(response, context)

        if response.startswith("/done"):
            self.print_info("Finishing session")
            return False, False  # don't continue loop, end session
        elif response.startswith("/advance"):
            print(f"{Fore.YELLOW}Continuing with new phase...{Style.RESET_ALL}")
            return True, True  # continue loop, stay in session
        elif response.startswith("/back") or response.startswith("/exit"):
            return False, False  # don't continue loop, end session
        elif response.startswith("/help"):
            self._show_session_help()
            return True, True  # continue loop, stay in session
        else:
            return True, True  # other commands, continue loop

    def _show_session_help(self) -> None:
        """Show session help menu"""
        print(f"\n{Fore.CYAN}Session Commands:{Style.RESET_ALL}")
        print("  /chat      - Continue this interactive session")
        print("  /mode      - Switch between socratic and direct mode (/mode <socratic|direct>)")
        print("  /done      - Finish this session")
        print("  /advance   - Move to next phase")
        print("  /help      - Show session help")
        print("  /back      - Return to main menu")
        print("  /exit      - Exit application\n")

    def _handle_special_response(self, response: str, orchestrator, project) -> tuple:
        """Handle non-command responses. Returns (handled, should_continue)"""
        if response.lower() == "done":
            self.print_info("Finishing session")
            return True, False  # handled, end session
        elif response.lower() == "advance":
            result = orchestrator.process_request(
                "socratic_counselor", {"action": "advance_phase", "project": project}
            )
            if result["status"] == "success":
                project.phase = result["new_phase"]
                self.print_success(f"Advanced to {result['new_phase']} phase!")
            else:
                self.print_error(result.get("message", "Could not advance phase"))
            return True, True  # handled, continue session
        elif response.lower() in ["help", "suggestions", "hint"]:
            return True, True  # handled by caller, continue session
        elif not response:
            return True, True  # empty response, continue
        return False, True  # not handled

    def _process_user_answer(
        self,
        response: str,
        orchestrator,
        project,
        user,
        mode: str = "socratic",
        session_context: str = "in_session",
        pre_extracted_insights=None,
    ) -> None:
        """Process the user's answer/input and extract insights + detect conflicts

        Args:
            response: User's response/input
            orchestrator: Orchestrator instance
            project: Project context
            user: Current user
            mode: 'socratic' or 'direct'
            session_context: 'in_session' or 'out_of_session'
            pre_extracted_insights: If provided, use these insights instead of extracting
        """
        if session_context == "out_of_session":
            return

        if mode == "direct" and pre_extracted_insights is None:
            pre_extracted_insights = self._handle_direct_mode_insights(
                response, orchestrator, project
            )
            if pre_extracted_insights is None:
                return

        self._process_and_save_response(
            response, orchestrator, project, user, pre_extracted_insights
        )

    def _handle_direct_mode_insights(self, response: str, orchestrator, project):
        """Extract and confirm insights in direct mode. Returns confirmed insights or None."""
        extraction_result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "extract_insights_only",
                "project": project,
                "response": response,
            },
        )

        if extraction_result["status"] != "success" or not extraction_result.get("insights"):
            return None

        insights = extraction_result["insights"]
        pre_extracted_insights = self._confirm_insights_interactive(insights, orchestrator)

        if pre_extracted_insights is None:
            print(f"{Fore.MAGENTA}All insights discarded.{Style.RESET_ALL}")

        return pre_extracted_insights

    def _process_and_save_response(
        self, response: str, orchestrator, project, user, pre_extracted_insights
    ) -> None:
        """Process response and save project. Handles result status and feedback."""
        request_data = {
            "action": "process_response",
            "project": project,
            "response": response,
            "current_user": user.username,
        }

        if pre_extracted_insights is not None:
            request_data["pre_extracted_insights"] = pre_extracted_insights

        result = orchestrator.process_request("socratic_counselor", request_data)

        if result["status"] != "success":
            self.print_error(result.get("message", "Error processing response"))
            return

        if result.get("conflicts_pending"):
            self.print_warning("Some specifications were not added due to conflicts")
        elif result.get("insights"):
            self.print_success("Insights captured and integrated!")

        save_result = orchestrator.process_request(
            "project_manager", {"action": "save_project", "project": project}
        )
        if save_result["status"] != "success":
            self.print_error("Failed to save project")

    def _generate_direct_answer(self, question: str, orchestrator, project) -> str:
        """Generate a direct answer to user's question with vector DB search"""
        try:
            # Search vector database for relevant context
            relevant_context = ""
            if orchestrator.vector_db:
                knowledge_results = orchestrator.vector_db.search_similar(question, top_k=3)
                if knowledge_results:
                    relevant_context = "\n".join(
                        [f"- {result.get('content', '')[:200]}..." for result in knowledge_results]
                    )

            # Build prompt for direct answer
            project_info = f"""
Project Context:
- Name: {project.name}
- Phase: {project.phase}
- Goals: {project.goals}
- Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}
"""

            knowledge_section = ""
            if relevant_context:
                knowledge_section = f"""
Relevant Knowledge:
{relevant_context}
"""

            prompt = f"""You are a helpful assistant for a software development project.

{project_info}
{knowledge_section}

User Question: {question}

Provide a clear, direct answer to the user's question. Be concise but thorough.
If the question relates to the project, use the project context and knowledge base.
If you don't have enough information, say so."""

            # Generate answer
            answer = orchestrator.claude_client.generate_response(prompt)
            return answer

        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute chat command"""
        if not self.require_project(context):
            return self.error("No project loaded. Use /project load to select one.")

        orchestrator = context.get("orchestrator")
        app = context.get("app")
        project = context.get("project")
        user = context.get("user")

        if not orchestrator or not app or not project or not user:
            return self.error("Required context not available")

        self._print_session_header(project)

        # NEW: Auto-load project files into knowledge base
        self._auto_load_project_files(project, orchestrator)

        session_active = True
        while session_active:
            if project.chat_mode == "socratic":
                session_active = self._handle_socratic_mode_turn(
                    orchestrator, project, user, context
                )
            else:
                session_active = self._handle_direct_mode_turn(orchestrator, project, user, context)

        return self.success()

    def _print_session_header(self, project) -> None:
        """Print session header with project details"""
        print(f"\n{Fore.CYAN}Interactive Chat Session{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Project: {project.name}")
        print(f"Phase: {project.phase}")
        print(f"Mode: {project.chat_mode}")
        print(f"{Style.RESET_ALL}\n")

    def _handle_socratic_mode_turn(self, orchestrator, project, user, context) -> bool:
        """Handle one turn of Socratic mode (system asks, user answers)"""
        question_result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "generate_question",
                "project": project,
                "current_user": user.username,
            },
        )

        if question_result["status"] != "success":
            self.print_error(question_result.get("message", "Unknown error"))
            return False

        question = question_result["question"]
        print(f"\n{Fore.BLUE}🤔 {question}")

        print(
            f"\n{Fore.YELLOW}Your response (or use /mode, /done, /advance, /help, /back, /exit):{Style.RESET_ALL}"
        )
        response = input(f"{Fore.WHITE}> ").strip()

        # Handle / commands
        if response.startswith("/"):
            should_continue, session_active = self._handle_command(response, context)
            if not should_continue:
                return False
            return session_active

        # Handle special responses
        handled, should_continue = self._handle_special_response(response, orchestrator, project)
        if handled:
            if not should_continue:
                return False
            if response.lower() in ["help", "suggestions", "hint"]:
                suggestions = orchestrator.claude_client.generate_suggestions(question, project)
                print(f"\n{Fore.MAGENTA}💡 {suggestions}")
                print(
                    f"{Fore.YELLOW}Now, would you like to try answering the question?{Style.RESET_ALL}"
                )
            return True

        # Process normal answer
        self._process_user_answer(
            response, orchestrator, project, user, mode="socratic", session_context="in_session"
        )
        return True

    def _handle_direct_mode_turn(self, orchestrator, project, user, context) -> bool:
        """Handle one turn of Direct mode (user asks, system answers)"""
        print(
            f"\n{Fore.YELLOW}Your question (or use /mode, /done, /advance, /help, /back, /exit):{Style.RESET_ALL}"
        )
        response = input(f"{Fore.WHITE}> ").strip()

        # Check if response is a command
        if response.startswith("/"):
            should_continue, session_active = self._handle_command(response, context)
            if not should_continue:
                return False
            return session_active

        # Check for special responses
        handled, should_continue = self._handle_special_response(response, orchestrator, project)
        if handled:
            return should_continue

        # Generate answer for user question
        if response:
            print(f"\n{Fore.GREEN}Answer:{Style.RESET_ALL}")
            answer = self._generate_direct_answer(response, orchestrator, project)
            print(f"{Fore.WHITE}{answer}{Style.RESET_ALL}\n")

        # Process the user question for insights
        self._process_user_answer(
            response, orchestrator, project, user, mode="direct", session_context="in_session"
        )
        return True

    def _auto_load_project_files(self, project, orchestrator) -> None:
        """
        Auto-load project files into knowledge base when entering chat

        Args:
            project: Project context
            orchestrator: Orchestrator instance
        """
        try:
            from socratic_system.agents.project_file_loader import ProjectFileLoader

            loader = ProjectFileLoader(orchestrator)

            # Check if project has files to load
            if not loader.should_load_files(project):
                return  # No files to load, silently skip

            # Load files into knowledge base
            self.print_info("Loading project code files into knowledge base...")

            result = loader.load_project_files(
                project=project, strategy="priority", max_files=50, show_progress=True
            )

            if result.get("status") == "success":
                files_loaded = result.get("files_loaded", 0)
                chunks = result.get("total_chunks", 0)
                if files_loaded > 0:
                    self.print_success(
                        f"✓ Loaded {files_loaded} files ({chunks} chunks) into knowledge base"
                    )
                else:
                    self.print_info("Files were already loaded in knowledge base")
            else:
                self.print_warning(
                    f"Could not load project files: {result.get('message', 'Unknown error')}"
                )

        except Exception as e:
            self.print_warning(f"Error auto-loading project files: {str(e)}")
            # Don't fail chat session if file loading fails


class DoneCommand(BaseCommand):
    """Finish the current session"""

    def __init__(self):
        super().__init__(
            name="done", description="Finish the current interactive session", usage="done"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute done command"""
        project = context.get("project")

        if not project:
            self.print_info("No active session")
            return self.success()

        self.print_info(f"Session ended for project: {project.name}")
        return self.success(data={"session_ended": True})


class AdvanceCommand(BaseCommand):
    """Advance project to the next phase"""

    def __init__(self):
        super().__init__(
            name="advance", description="Advance current project to the next phase", usage="advance"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute advance command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        result = orchestrator.process_request(
            "socratic_counselor", {"action": "advance_phase", "project": project}
        )

        if result["status"] == "success":
            project.phase = result["new_phase"]
            self.print_success(f"Advanced to {result['new_phase']} phase!")

            # Save project
            orchestrator.process_request(
                "project_manager", {"action": "save_project", "project": project}
            )

            return self.success(data={"new_phase": result["new_phase"]})
        else:
            return self.error(result.get("message", "Could not advance phase"))


class ModeCommand(BaseCommand):
    """Toggle between Socratic and direct chat modes"""

    def __init__(self):
        super().__init__(
            name="mode",
            description="Switch chat mode between socratic and direct Q&A",
            usage="mode <socratic|direct>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mode command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        if not args or args[0] not in ["socratic", "direct"]:
            return self.error("Usage: /mode <socratic|direct>")

        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not project or not orchestrator:
            return self.error("Required context not available")

        project.chat_mode = args[0]

        # Save to database
        save_result = orchestrator.process_request(
            "project_manager", {"action": "save_project", "project": project}
        )

        if save_result["status"] == "success":
            self.print_success(f"Mode switched to: {args[0]}")
            return self.success(data={"mode": args[0]})
        else:
            return self.error("Failed to save mode change")


class HintCommand(BaseCommand):
    """Get a hint for the current question"""

    def __init__(self):
        super().__init__(
            name="hint",
            description="Get a suggestion or hint for the current question",
            usage="hint",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hint command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")
        user = context.get("user")

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Get the last question
        question_result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "generate_question",
                "project": project,
                "current_user": user.username if user else None,
            },
        )

        if question_result["status"] != "success":
            return self.error("Could not generate question")

        question = question_result["question"]

        # Generate suggestions
        suggestions = orchestrator.claude_client.generate_suggestions(question, project)

        print(f"\n{Fore.MAGENTA}💡 Hint for: {Fore.CYAN}{question}{Style.RESET_ALL}\n")
        print(f"{Fore.WHITE}{suggestions}{Style.RESET_ALL}\n")

        return self.success(data={"hint": suggestions})
