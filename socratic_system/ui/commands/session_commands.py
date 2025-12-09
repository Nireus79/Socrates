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

    def _process_user_answer(self, response: str, orchestrator, project, user) -> None:
        """Process the user's answer/input and extract insights + detect conflicts"""
        result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "process_response",
                "project": project,
                "response": response,
                "current_user": user.username,
            },
        )

        if result["status"] == "success":
            if result.get("conflicts_pending"):
                self.print_warning("Some specifications were not added due to conflicts")
            elif result.get("insights"):
                self.print_success("Insights captured and integrated!")

            save_result = orchestrator.process_request(
                "project_manager", {"action": "save_project", "project": project}
            )
            if save_result["status"] != "success":
                self.print_error("Failed to save project")
        else:
            self.print_error(result.get("message", "Error processing response"))

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

        print(f"\n{Fore.CYAN}Interactive Chat Session{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Project: {project.name}")
        print(f"Phase: {project.phase}")
        print(f"Mode: {project.chat_mode}")
        print(f"{Style.RESET_ALL}\n")

        session_active = True

        while session_active:
            # Check current mode and generate question or prompt for answer
            if project.chat_mode == "socratic":
                # Socratic mode: Generate and ask a question
                question_result = orchestrator.process_request(
                    "socratic_counselor", {"action": "generate_question", "project": project}
                )

                if question_result["status"] != "success":
                    self.print_error(question_result.get("message", "Unknown error"))
                    break

                question = question_result["question"]
                print(f"\n{Fore.BLUE}🤔 {question}")

                # Get user response
                print(
                    f"\n{Fore.YELLOW}Your response (or use /mode, /done, /advance, /help, /back, /exit):{Style.RESET_ALL}"
                )
                response = input(f"{Fore.WHITE}> ").strip()

            else:
                # Direct mode: Wait for user's question and answer it
                print(
                    f"\n{Fore.YELLOW}Your question (or use /mode, /done, /advance, /help, /back, /exit):{Style.RESET_ALL}"
                )
                response = input(f"{Fore.WHITE}> ").strip()

                # Check if response is a command
                if response.startswith("/"):
                    should_continue, session_active = self._handle_command(response, context)
                    if not should_continue:
                        break
                    continue

                # Check for special responses
                handled, should_continue = self._handle_special_response(
                    response, orchestrator, project
                )
                if handled:
                    if not should_continue:
                        break
                    continue

                # Generate answer for user question
                if response:
                    print(f"\n{Fore.GREEN}Answer:{Style.RESET_ALL}")
                    answer = self._generate_direct_answer(response, orchestrator, project)
                    print(f"{Fore.WHITE}{answer}{Style.RESET_ALL}\n")

                # Process the user question for insights/conflicts
                self._process_user_answer(response, orchestrator, project, user)
                continue

            # Handle / commands (Socratic mode)
            if response.startswith("/"):
                should_continue, session_active = self._handle_command(response, context)
                if not should_continue:
                    break
                continue

            # Handle special responses (Socratic mode)
            handled, should_continue = self._handle_special_response(
                response, orchestrator, project
            )
            if handled:
                if not should_continue:
                    break
                if response.lower() in ["help", "suggestions", "hint"]:
                    question = question_result["question"]
                    suggestions = orchestrator.claude_client.generate_suggestions(question, project)
                    print(f"\n{Fore.MAGENTA}💡 {suggestions}")
                    print(
                        f"{Fore.YELLOW}Now, would you like to try answering the question?{Style.RESET_ALL}"
                    )
                continue

            # Process normal answer (Socratic mode)
            self._process_user_answer(response, orchestrator, project, user)

        return self.success()


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

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Get the last question
        question_result = orchestrator.process_request(
            "socratic_counselor", {"action": "generate_question", "project": project}
        )

        if question_result["status"] != "success":
            return self.error("Could not generate question")

        question = question_result["question"]

        # Generate suggestions
        suggestions = orchestrator.claude_client.generate_suggestions(question, project)

        print(f"\n{Fore.MAGENTA}💡 Hint for: {Fore.CYAN}{question}{Style.RESET_ALL}\n")
        print(f"{Fore.WHITE}{suggestions}{Style.RESET_ALL}\n")

        return self.success(data={"hint": suggestions})
