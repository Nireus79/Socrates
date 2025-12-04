"""
Claude API client for Socratic RAG System
"""

import json
from typing import Dict, Any

import anthropic
from colorama import Fore

from socratic_system.config import CONFIG
from socratic_system.models import ProjectContext, ConflictInfo


class ClaudeClient:
    """Client for interacting with Claude API"""

    def __init__(self, api_key: str, orchestrator: 'AgentOrchestrator'):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.orchestrator = orchestrator
        self.model = CONFIG['CLAUDE_MODEL']

    def extract_insights(self, user_response: str, project: ProjectContext) -> Dict:
        """Extract insights from user response using Claude"""

        # Handle empty or non-informative responses
        if not user_response or len(user_response.strip()) < 3:
            return {}

        # Handle common non-informative responses
        non_informative = ["i don't know", "idk", "not sure", "no idea", "dunno", "unsure"]
        if user_response.lower().strip() in non_informative:
            return {'note': 'User expressed uncertainty - may need more guidance'}

        # Build prompt
        prompt = f"""
        Analyze this user response in the context of their project and extract structured insights:

        Project Context:
        - Goals: {project.goals or 'Not specified'}
        - Phase: {project.phase}
        - Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}

        User Response: "{user_response}"

        Please extract and return any mentions of:
        1. Goals or objectives
        2. Technical requirements
        3. Technology preferences
        4. Constraints or limitations
        5. Team structure preferences

        IMPORTANT: Return ONLY valid JSON. Each field should be a string or array of strings.
        Example format:
        {{
            "goals": "string describing the goal",
            "requirements": ["requirement 1", "requirement 2"],
            "tech_stack": ["technology 1", "technology 2"],
            "constraints": ["constraint 1", "constraint 2"],
            "team_structure": "description of team structure"
        }}

        If no insights found, return: {{}}
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            # Track token usage
            self.orchestrator.system_monitor.process({
                'action': 'track_tokens',
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
                'cost_estimate': self._calculate_cost(response.usage)
            })

            # Try to parse JSON response
            try:
                response_text = response.content[0].text.strip()

                # Clean up the response
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                elif response_text.startswith('```'):
                    response_text = response_text.replace('```', '').strip()

                # Find JSON object in the response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1

                if 0 <= start < end:
                    json_text = response_text[start:end]
                    parsed_insights = json.loads(json_text)

                    # Validate and clean the insights
                    if isinstance(parsed_insights, dict):
                        cleaned_insights = {}
                        for key, value in parsed_insights.items():
                            if key in ['goals', 'requirements', 'tech_stack', 'constraints', 'team_structure']:
                                if value:
                                    cleaned_insights[key] = value

                        return cleaned_insights
                    else:
                        return {}
                else:
                    return {}

            except (json.JSONDecodeError, ValueError, IndexError) as json_error:
                print(f"{Fore.YELLOW}Warning: Could not parse JSON response: {json_error}")
                return {}

        except Exception as e:
            print(f"{Fore.RED}Error extracting insights: {e}")
            return {}

    def generate_conflict_resolution_suggestions(self, conflict: ConflictInfo, project: ProjectContext) -> str:
        """Generate suggestions for resolving a specific conflict"""

        context_summary = self.orchestrator.context_analyzer.get_context_summary(project)

        prompt = f"""Help resolve this project specification conflict:

    Project: {project.name} ({project.phase} phase)
    Project Context: {context_summary}

    Conflict Details:
    - Type: {conflict.conflict_type}
    - Original: "{conflict.old_value}" (by {conflict.old_author})
    - New: "{conflict.new_value}" (by {conflict.new_author})
    - Severity: {conflict.severity}

    Provide 3-4 specific, actionable suggestions for resolving this conflict. Consider:
    1. Technical implications of each choice
    2. Project goals and constraints
    3. Team collaboration aspects
    4. Potential compromise solutions

    Be specific and practical, not just theoretical."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            return f"Error generating suggestions: {e}"

    def generate_code(self, context: str) -> str:
        """Generate code based on project context"""
        prompt = f"""
        Generate a complete, functional script based on this project context:

        {context}

        Please create:
        1. A well-structured, documented script
        2. Include proper error handling
        3. Follow best practices for the chosen technology
        4. Add helpful comments explaining key functionality
        5. Include basic testing or validation

        Make it production-ready and maintainable.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            # Track token usage
            self.orchestrator.system_monitor.process({
                'action': 'track_tokens',
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
                'cost_estimate': self._calculate_cost(response.usage)
            })

            return response.content[0].text

        except Exception as e:
            return f"Error generating code: {e}"

    def generate_documentation(self, project: ProjectContext, script: str) -> str:
        """Generate documentation for the project and script"""
        prompt = f"""
        Create comprehensive documentation for this project:

        Project: {project.name}
        Goals: {project.goals}
        Tech Stack: {', '.join(project.tech_stack)}

        Script:
        {script[:2000]}...

        Please include:
        1. Project overview and purpose
        2. Installation instructions
        3. Usage examples
        4. API documentation (if applicable)
        5. Configuration options
        6. Troubleshooting section
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )

            # Track token usage
            self.orchestrator.system_monitor.process({
                'action': 'track_tokens',
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
                'cost_estimate': self._calculate_cost(response.usage)
            })

            return response.content[0].text

        except Exception as e:
            return f"Error generating documentation: {e}"

    def test_connection(self):
        """Test connection to Claude API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": "Test"}]
            )
            return True
        except Exception as e:
            raise e

    def _calculate_cost(self, usage) -> float:
        """Calculate estimated cost based on token usage"""
        # Claude 3 Sonnet pricing (approximate)
        input_cost_per_1k = 0.003  # $0.003 per 1K input tokens
        output_cost_per_1k = 0.015  # $0.015 per 1K output tokens

        input_cost = (usage.input_tokens / 1000) * input_cost_per_1k
        output_cost = (usage.output_tokens / 1000) * output_cost_per_1k

        return input_cost + output_cost

    def generate_socratic_question(self, prompt: str) -> str:
        """Generate a Socratic question using Claude"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            # Track token usage
            self.orchestrator.system_monitor.process({
                'action': 'track_tokens',
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
                'cost_estimate': self._calculate_cost(response.usage)
            })

            return response.content[0].text.strip()

        except Exception as e:
            print(f"{Fore.RED}Error generating Socratic question: {e}")
            raise e

    def generate_suggestions(self, current_question: str, project: ProjectContext) -> str:
        """Generate helpful suggestions when user can't answer a question"""

        # Get recent conversation for context
        recent_conversation = ""
        if project.conversation_history:
            recent_messages = project.conversation_history[-6:]
            for msg in recent_messages:
                role = "Assistant" if msg['type'] == 'assistant' else "User"
                recent_conversation += f"{role}: {msg['content']}\n"

        # Get relevant knowledge from vector database
        relevant_knowledge = ""
        knowledge_results = self.orchestrator.vector_db.search_similar(current_question, top_k=3)
        if knowledge_results:
            relevant_knowledge = "\n".join([result['content'][:300] for result in knowledge_results])

        # Build context summary
        context_summary = self.orchestrator.context_analyzer.get_context_summary(project)

        prompt = f"""You are helping a developer who is stuck on a Socratic question about their software project.

    Project Details:
    - Name: {project.name}
    - Phase: {project.phase}
    - Context: {context_summary}

    Current Question They Can't Answer:
    "{current_question}"

    Recent Conversation:
    {recent_conversation}

    Relevant Knowledge:
    {relevant_knowledge}

    The user is having difficulty answering this question. Provide 3-4 helpful suggestions that:

    1. Give concrete examples or options they could consider
    2. Break down the question into smaller, easier parts
    3. Provide relevant industry examples or common approaches
    4. Suggest specific things they could research or think about

    Keep suggestions practical, specific, and encouraging. Don't just ask more questions.
    """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            # Track token usage
            self.orchestrator.system_monitor.process({
                'action': 'track_tokens',
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
                'cost_estimate': self._calculate_cost(response.usage)
            })

            return response.content[0].text.strip()

        except Exception as e:
            # Fallback suggestions if Claude API fails
            fallback_suggestions = {
                'discovery': """Here are some suggestions to help you think through this:

    • Consider researching similar applications or tools in your problem domain
    • Think about specific pain points you've experienced that this could solve
    • Ask potential users what features would be most valuable to them
    • Look at existing solutions and identify what's missing or could be improved""",

                'analysis': """Here are some suggestions to help you think through this:

    • Break down the technical challenge into smaller, specific problems
    • Research what libraries or frameworks are commonly used for this type of project
    • Consider scalability, security, and performance requirements early
    • Look up case studies of similar technical implementations""",

                'design': """Here are some suggestions to help you think through this:

    • Start with a simple architecture and plan how to extend it later
    • Consider using established design patterns like MVC, Repository, or Factory
    • Think about how different components will communicate with each other
    • Sketch out the data flow and user interaction patterns""",

                'implementation': """Here are some suggestions to help you think through this:

    • Break the project into small, manageable milestones
    • Consider starting with a minimal viable version first
    • Think about your development environment and tooling needs
    • Plan your testing strategy alongside your implementation approach"""
            }

            return fallback_suggestions.get(project.phase,
                                            "Consider breaking the question into smaller parts and researching each "
                                            "aspect individually.")

    def generate_response(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """
        Generate a general response from Claude for any prompt.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response (default: 2000)
            temperature: Temperature for response generation (default: 0.7)

        Returns:
            Claude's response as a string

        Raises:
            Exception: If API call fails
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            # Track token usage
            self.orchestrator.system_monitor.process({
                'action': 'track_tokens',
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
                'cost_estimate': self._calculate_cost(response.usage)
            })

            return response.content[0].text.strip()

        except Exception as e:
            print(f"{Fore.RED}Error generating response: {e}")
            raise e
