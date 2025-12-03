"""
Socratic counselor agent for guided questioning and response processing
"""

import datetime
from typing import Dict, Any, List

from colorama import Fore

from socratic_system.models import ProjectContext, ConflictInfo
from .base import Agent


class SocraticCounselorAgent(Agent):
    """Core agent that guides users through Socratic questioning about their project"""

    def __init__(self, orchestrator):
        super().__init__("SocraticCounselor", orchestrator)
        self.use_dynamic_questions = True  # Toggle for dynamic vs static questions
        self.max_questions_per_phase = 5

        # Fallback static questions if Claude is unavailable
        self.static_questions = {
            'discovery': [
                "What specific problem does your project solve?",
                "Who is your target audience or user base?",
                "What are the core features you envision?",
                "Are there similar solutions that exist? How will yours differ?",
                "What are your success criteria for this project?"
            ],
            'analysis': [
                "What technical challenges do you anticipate?",
                "What are your performance requirements?",
                "How will you handle user authentication and security?",
                "What third-party integrations might you need?",
                "How will you test and validate your solution?"
            ],
            'design': [
                "How will you structure your application architecture?",
                "What design patterns will you use?",
                "How will you organize your code and modules?",
                "What development workflow will you follow?",
                "How will you handle error cases and edge scenarios?"
            ],
            'implementation': [
                "What will be your first implementation milestone?",
                "How will you handle deployment and DevOps?",
                "What monitoring and logging will you implement?",
                "How will you document your code and API?",
                "What's your plan for maintenance and updates?"
            ]
        }

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process Socratic questioning requests"""
        action = request.get('action')

        if action == 'generate_question':
            return self._generate_question(request)
        elif action == 'process_response':
            return self._process_response(request)
        elif action == 'advance_phase':
            return self._advance_phase(request)
        elif action == 'toggle_dynamic_questions':
            self.use_dynamic_questions = not self.use_dynamic_questions
            return {'status': 'success', 'dynamic_mode': self.use_dynamic_questions}

        return {'status': 'error', 'message': 'Unknown action'}

    def _generate_question(self, request: Dict) -> Dict:
        """Generate the next Socratic question"""
        project = request.get('project')
        context = self.orchestrator.context_analyzer.get_context_summary(project)

        # Count questions already asked in this phase
        phase_questions = [msg for msg in project.conversation_history
                           if msg.get('type') == 'assistant' and msg.get('phase') == project.phase]

        if self.use_dynamic_questions:
            question = self._generate_dynamic_question(project, context, len(phase_questions))
        else:
            question = self._generate_static_question(project, len(phase_questions))

        # Store the question in conversation history
        project.conversation_history.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'type': 'assistant',
            'content': question,
            'phase': project.phase,
            'question_number': len(phase_questions) + 1
        })

        return {'status': 'success', 'question': question}

    def _generate_dynamic_question(self, project: ProjectContext, context: str, question_count: int) -> str:
        """Generate contextual questions using Claude"""

        # Get conversation history for context
        recent_conversation = ""
        if project.conversation_history:
            recent_messages = project.conversation_history[-4:]  # Last 4 messages
            for msg in recent_messages:
                role = "Assistant" if msg['type'] == 'assistant' else "User"
                recent_conversation += f"{role}: {msg['content']}\n"

        # Get relevant knowledge from vector database
        relevant_knowledge = ""
        if context:
            knowledge_results = self.orchestrator.vector_db.search_similar(context, top_k=3)
            if knowledge_results:
                relevant_knowledge = "\n".join([result['content'][:200] + "..." for result in knowledge_results])

        prompt = self._build_question_prompt(project, context, recent_conversation, relevant_knowledge, question_count)

        try:
            question = self.orchestrator.claude_client.generate_socratic_question(prompt)
            self.log(f"Generated dynamic question for {project.phase} phase")
            return question
        except Exception as e:
            self.log(f"Failed to generate dynamic question: {e}, falling back to static", "WARN")
            return self._generate_static_question(project, question_count)

    def _build_question_prompt(self, project: ProjectContext, context: str,
                               recent_conversation: str, relevant_knowledge: str, question_count: int) -> str:
        """Build prompt for dynamic question generation"""

        phase_descriptions = {
            'discovery': "exploring the problem space, understanding user needs, and defining project goals",
            'analysis': "analyzing technical requirements, identifying challenges, and planning solutions",
            'design': "designing architecture, choosing patterns, and planning implementation structure",
            'implementation': "planning development steps, deployment strategy, and maintenance approach"
        }

        phase_focus = {
            'discovery': "problem definition, user needs, market research, competitive analysis",
            'analysis': "technical feasibility, performance requirements, security considerations, integrations",
            'design': "architecture patterns, code organization, development workflow, error handling",
            'implementation': "development milestones, deployment pipeline, monitoring, documentation"
        }

        return f"""You are a Socratic tutor helping a developer think through their software project.

Project Details:
- Name: {project.name}
- Current Phase: {project.phase} ({phase_descriptions.get(project.phase, '')})
- Goals: {project.goals}
- Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}
- Requirements: {', '.join(project.requirements) if project.requirements else 'Not specified'}

Project Context:
{context}

Recent Conversation:
{recent_conversation}

Relevant Knowledge:
{relevant_knowledge}

This is question #{question_count + 1} in the {project.phase} phase. Focus on: {phase_focus.get(project.phase, '')}.

Generate ONE insightful Socratic question that:
1. Builds on what we've discussed so far
2. Helps the user think deeper about their project
3. Is specific to the {project.phase} phase
4. Encourages critical thinking rather than just information gathering
5. Is relevant to their stated goals and tech stack

The question should be thought-provoking but not overwhelming. Make it conversational and engaging.

Return only the question, no additional text or explanation."""

    def _generate_static_question(self, project: ProjectContext, question_count: int) -> str:
        """Generate questions from static predefined lists"""
        questions = self.static_questions.get(project.phase, [])

        if question_count < len(questions):
            return questions[question_count]
        else:
            # Fallback questions when we've exhausted the static list
            fallbacks = {
                'discovery': "What other aspects of the problem space should we explore?",
                'analysis': "What technical considerations haven't we discussed yet?",
                'design': "What design decisions are you still uncertain about?",
                'implementation': "What implementation details would you like to work through?"
            }
            return fallbacks.get(project.phase, "What would you like to explore further?")

    def _process_response(self, request: Dict) -> Dict:
        """Process user response and extract insights"""
        project = request.get('project')
        user_response = request.get('response')
        current_user = request.get('current_user')

        # Add to conversation history with phase information
        project.conversation_history.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'type': 'user',
            'content': user_response,
            'phase': project.phase,
            'author': current_user  # Track who said what
        })

        # Extract insights using Claude
        insights = self.orchestrator.claude_client.extract_insights(user_response, project)

        # REAL-TIME CONFLICT DETECTION
        if insights:
            conflict_result = self.orchestrator.process_request('conflict_detector', {
                'action': 'detect_conflicts',
                'project': project,
                'new_insights': insights,
                'current_user': current_user
            })

            if conflict_result['status'] == 'success' and conflict_result['conflicts']:
                # Handle conflicts before updating context
                conflicts_resolved = self._handle_conflicts_realtime(conflict_result['conflicts'], project)
                if not conflicts_resolved:
                    # User chose not to resolve conflicts, don't update context
                    return {'status': 'success', 'insights': insights, 'conflicts_pending': True}

        # Update context only if no conflicts or conflicts were resolved
        self._update_project_context(project, insights)

        return {'status': 'success', 'insights': insights}

    def _remove_from_project_context(self, project: ProjectContext, value: str, context_type: str):
        """Remove a value from project context"""
        if context_type == 'tech_stack' and value in project.tech_stack:
            project.tech_stack.remove(value)
        elif context_type == 'requirements' and value in project.requirements:
            project.requirements.remove(value)
        elif context_type == 'constraints' and value in project.constraints:
            project.constraints.remove(value)
        elif context_type == 'goals':
            project.goals = ""

    def _manual_resolution(self, conflict: ConflictInfo) -> str:
        """Allow user to manually resolve conflict"""
        print(f"\n{Fore.CYAN}Manual Resolution:")
        print(f"Current options: '{conflict.old_value}' vs '{conflict.new_value}'")

        new_value = input(f"{Fore.WHITE}Enter resolved specification: ").strip()
        if new_value:
            return new_value
        return ""

    def _handle_conflicts_realtime(self, conflicts: List[ConflictInfo], project: ProjectContext) -> bool:
        """Handle conflicts in real-time during conversation"""
        for conflict in conflicts:
            print(f"\n{Fore.RED}⚠️  CONFLICT DETECTED!")
            print(f"{Fore.YELLOW}Type: {conflict.conflict_type}")
            print(f"{Fore.WHITE}Existing: '{conflict.old_value}' (by {conflict.old_author})")
            print(f"{Fore.WHITE}New: '{conflict.new_value}' (by {conflict.new_author})")
            print(f"{Fore.RED}Severity: {conflict.severity}")

            # Get AI-generated suggestions
            suggestions = self.orchestrator.claude_client.generate_conflict_resolution_suggestions(conflict, project)
            print(f"\n{Fore.MAGENTA}{suggestions}")

            print(f"\n{Fore.CYAN}Resolution Options:")
            print("1. Keep existing specification")
            print("2. Replace with new specification")
            print("3. Skip this specification (continue without adding)")
            print("4. Manual resolution (edit both)")

            while True:
                choice = input(f"{Fore.WHITE}Choose resolution (1-4): ").strip()

                if choice == '1':
                    print(f"{Fore.GREEN}✓ Keeping existing: '{conflict.old_value}'")
                    self._remove_from_insights(conflict.new_value, conflict.conflict_type)
                    break
                elif choice == '2':
                    print(f"{Fore.GREEN}✓ Replacing with: '{conflict.new_value}'")
                    self._remove_from_project_context(project, conflict.old_value, conflict.conflict_type)
                    break
                elif choice == '3':
                    print(f"{Fore.YELLOW}⏭️  Skipping specification")
                    self._remove_from_insights(conflict.new_value, conflict.conflict_type)
                    break
                elif choice == '4':
                    resolved_value = self._manual_resolution(conflict)
                    if resolved_value:
                        self._remove_from_project_context(project, conflict.old_value, conflict.conflict_type)
                        self._update_insights_value(conflict.new_value, resolved_value, conflict.conflict_type)
                        print(f"{Fore.GREEN}✓ Updated to: '{resolved_value}'")
                    break
                else:
                    print(f"{Fore.RED}Invalid choice. Please try again.")

        return True

    def _advance_phase(self, request: Dict) -> Dict:
        """Advance project to the next phase"""
        project = request.get('project')
        phases = ['discovery', 'analysis', 'design', 'implementation']

        current_index = phases.index(project.phase)
        if current_index < len(phases) - 1:
            project.phase = phases[current_index + 1]
            self.log(f"Advanced project to {project.phase} phase")

        return {'status': 'success', 'new_phase': project.phase}

    def _update_project_context(self, project: ProjectContext, insights: Dict):
        """Update project context based on extracted insights"""
        if not insights or not isinstance(insights, dict):
            return

        try:
            # Handle goals
            if 'goals' in insights and insights['goals']:
                goals_value = insights['goals']
                if isinstance(goals_value, list):
                    project.goals = ' '.join(str(item) for item in goals_value if item)
                elif isinstance(goals_value, str):
                    project.goals = goals_value.strip()
                else:
                    project.goals = str(goals_value).strip()

            # Handle requirements
            if 'requirements' in insights and insights['requirements']:
                requirements_value = insights['requirements']
                if isinstance(requirements_value, list):
                    for req in requirements_value:
                        req_str = str(req).strip() if req else ""
                        if req_str and req_str not in project.requirements:
                            project.requirements.append(req_str)
                elif isinstance(requirements_value, str):
                    req_str = requirements_value.strip()
                    if req_str and req_str not in project.requirements:
                        project.requirements.append(req_str)
                else:
                    req_str = str(requirements_value).strip()
                    if req_str and req_str not in project.requirements:
                        project.requirements.append(req_str)

            # Handle tech_stack
            if 'tech_stack' in insights and insights['tech_stack']:
                tech_value = insights['tech_stack']
                if isinstance(tech_value, list):
                    for tech in tech_value:
                        tech_str = str(tech).strip() if tech else ""
                        if tech_str and tech_str not in project.tech_stack:
                            project.tech_stack.append(tech_str)
                elif isinstance(tech_value, str):
                    tech_str = tech_value.strip()
                    if tech_str and tech_str not in project.tech_stack:
                        project.tech_stack.append(tech_str)
                else:
                    tech_str = str(tech_value).strip()
                    if tech_str and tech_str not in project.tech_stack:
                        project.tech_stack.append(tech_str)

            # Handle constraints
            if 'constraints' in insights and insights['constraints']:
                constraints_value = insights['constraints']
                if isinstance(constraints_value, list):
                    for constraint in constraints_value:
                        constraint_str = str(constraint).strip() if constraint else ""
                        if constraint_str and constraint_str not in project.constraints:
                            project.constraints.append(constraint_str)
                elif isinstance(constraints_value, str):
                    constraint_str = constraints_value.strip()
                    if constraint_str and constraint_str not in project.constraints:
                        project.constraints.append(constraint_str)
                else:
                    constraint_str = str(constraints_value).strip()
                    if constraint_str and constraint_str not in project.constraints:
                        project.constraints.append(constraint_str)

        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Error updating project context: {e}")
            print(f"Insights received: {insights}")

    def _remove_from_insights(self, value: str, insight_type: str):
        """Remove a value from insights before context update"""
        pass

    def _update_insights_value(self, old_value: str, new_value: str, insight_type: str):
        """Update a value in insights before context update"""
        pass
