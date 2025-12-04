"""Socratic session commands (conversation, phases, etc.)"""

from typing import Dict, Any, List
from colorama import Fore, Style
from socratic_system.ui.commands.base import BaseCommand


class ContinueCommand(BaseCommand):
    """Continue a Socratic guidance session"""

    def __init__(self):
        super().__init__(
            name="continue",
            description="Continue a Socratic guidance session with current project",
            usage="continue"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute continue command"""
        if not self.require_project(context):
            return self.error("No project loaded. Use /project load to select one.")

        orchestrator = context.get('orchestrator')
        app = context.get('app')
        project = context.get('project')
        user = context.get('user')

        if not orchestrator or not app or not project or not user:
            return self.error("Required context not available")

        print(f"\n{Fore.CYAN}Socratic Guidance Session{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Project: {project.name}")
        print(f"Phase: {project.phase}")
        print(f"{Style.RESET_ALL}\n")

        session_active = True

        while session_active:
            # Generate question first
            question_result = orchestrator.process_request('socratic_counselor', {
                'action': 'generate_question',
                'project': project
            })

            if question_result['status'] != 'success':
                self.print_error(question_result.get('message', 'Unknown error'))
                break

            question = question_result['question']
            print(f"\n{Fore.BLUE}🤔 {question}")

            # Get user response
            print(f"\n{Fore.YELLOW}Your response (type 'done' to finish, 'advance' to move to next phase, 'help' for suggestions):{Style.RESET_ALL}")
            response = input(f"{Fore.WHITE}> ").strip()

            if response.lower() == 'done':
                self.print_info("Finishing session")
                session_active = False
                break

            elif response.lower() == 'advance':
                result = orchestrator.process_request('socratic_counselor', {
                    'action': 'advance_phase',
                    'project': project
                })
                if result['status'] == 'success':
                    project.phase = result['new_phase']
                    self.print_success(f"Advanced to {result['new_phase']} phase!")
                else:
                    self.print_error(result.get('message', 'Could not advance phase'))
                continue

            elif response.lower() in ['help', 'suggestions', 'hint']:
                # Generate suggestions
                suggestions = orchestrator.claude_client.generate_suggestions(question, project)
                print(f"\n{Fore.MAGENTA}💡 {suggestions}")
                print(f"{Fore.YELLOW}Now, would you like to try answering the question?{Style.RESET_ALL}")
                continue

            elif not response:
                continue

            # Process the user's response
            result = orchestrator.process_request('socratic_counselor', {
                'action': 'process_response',
                'project': project,
                'response': response,
                'current_user': user.username
            })

            if result['status'] == 'success':
                if result.get('conflicts_pending'):
                    self.print_warning("Some specifications were not added due to conflicts")
                elif result.get('insights'):
                    self.print_success("Insights captured and integrated!")

                # Save the updated project
                save_result = orchestrator.process_request('project_manager', {
                    'action': 'save_project',
                    'project': project
                })

                if save_result['status'] != 'success':
                    self.print_error("Failed to save project")
            else:
                self.print_error(result.get('message', 'Error processing response'))

        return self.success()


class DoneCommand(BaseCommand):
    """Finish the current session"""

    def __init__(self):
        super().__init__(
            name="done",
            description="Finish the current Socratic session",
            usage="done"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute done command"""
        project = context.get('project')

        if not project:
            self.print_info("No active session")
            return self.success()

        self.print_info(f"Session ended for project: {project.name}")
        return self.success(data={'session_ended': True})


class AdvanceCommand(BaseCommand):
    """Advance project to the next phase"""

    def __init__(self):
        super().__init__(
            name="advance",
            description="Advance current project to the next phase",
            usage="advance"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute advance command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator or not project:
            return self.error("Required context not available")

        result = orchestrator.process_request('socratic_counselor', {
            'action': 'advance_phase',
            'project': project
        })

        if result['status'] == 'success':
            project.phase = result['new_phase']
            self.print_success(f"Advanced to {result['new_phase']} phase!")

            # Save project
            orchestrator.process_request('project_manager', {
                'action': 'save_project',
                'project': project
            })

            return self.success(data={'new_phase': result['new_phase']})
        else:
            return self.error(result.get('message', 'Could not advance phase'))


class HintCommand(BaseCommand):
    """Get a hint for the current question"""

    def __init__(self):
        super().__init__(
            name="hint",
            description="Get a suggestion or hint for the current question",
            usage="hint"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hint command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Get the last question
        question_result = orchestrator.process_request('socratic_counselor', {
            'action': 'generate_question',
            'project': project
        })

        if question_result['status'] != 'success':
            return self.error("Could not generate question")

        question = question_result['question']

        # Generate suggestions
        suggestions = orchestrator.claude_client.generate_suggestions(question, project)

        print(f"\n{Fore.MAGENTA}💡 Hint for: {Fore.CYAN}{question}{Style.RESET_ALL}\n")
        print(f"{Fore.WHITE}{suggestions}{Style.RESET_ALL}\n")

        return self.success(data={'hint': suggestions})
