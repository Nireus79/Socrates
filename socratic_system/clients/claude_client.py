"""
Claude API client for Socratic RAG System

Provides both synchronous and asynchronous interfaces for calling Claude API,
with automatic token tracking and structured error handling.
"""

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Dict

import anthropic

from socratic_system.events import EventType
from socratic_system.exceptions import APIError
from socratic_system.models import ConflictInfo, ProjectContext

if TYPE_CHECKING:
    from socratic_system.orchestration.orchestrator import AgentOrchestrator


class ClaudeClient:
    """
    Client for interacting with Claude API.

    Supports both synchronous and asynchronous operations with automatic
    token usage tracking and event emission.
    """

    def __init__(self, api_key: str, orchestrator: "AgentOrchestrator"):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key
            orchestrator: Reference to AgentOrchestrator for event emission and token tracking
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.async_client = anthropic.AsyncAnthropic(api_key=api_key)
        self.orchestrator = orchestrator
        self.model = orchestrator.config.claude_model
        self.logger = logging.getLogger("socrates.clients.claude")

    def extract_insights(self, user_response: str, project: ProjectContext) -> Dict:
        """Extract insights from user response using Claude (synchronous)"""
        # Handle empty or non-informative responses
        if not user_response or len(user_response.strip()) < 3:
            return {}

        # Handle common non-informative responses
        non_informative = ["i don't know", "idk", "not sure", "no idea", "dunno", "unsure"]
        if user_response.lower().strip() in non_informative:
            return {"note": "User expressed uncertainty - may need more guidance"}

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
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self._track_token_usage(response.usage, "extract_insights")

            # Try to parse JSON response
            return self._parse_json_response(response.content[0].text.strip())

        except Exception as e:
            self.logger.error(f"Error extracting insights: {e}")
            self.orchestrator.event_emitter.emit(
                EventType.LOG_ERROR, {"message": f"Failed to extract insights: {e}"}
            )
            return {}

    async def extract_insights_async(self, user_response: str, project: ProjectContext) -> Dict:
        """Extract insights from user response asynchronously"""
        # Handle empty or non-informative responses
        if not user_response or len(user_response.strip()) < 3:
            return {}

        if user_response.lower().strip() in [
            "i don't know",
            "idk",
            "not sure",
            "no idea",
            "dunno",
            "unsure",
        ]:
            return {"note": "User expressed uncertainty - may need more guidance"}

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

        IMPORTANT: Return ONLY valid JSON.
        """

        try:
            response = await self.async_client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage asynchronously
            await self._track_token_usage_async(response.usage, "extract_insights_async")

            return self._parse_json_response(response.content[0].text.strip())

        except Exception as e:
            self.logger.error(f"Error extracting insights (async): {e}")
            return {}

    def generate_conflict_resolution_suggestions(
        self, conflict: ConflictInfo, project: ProjectContext
    ) -> str:
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
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text.strip()

        except Exception as e:
            return f"Error generating suggestions: {e}"

    def generate_artifact(self, context: str, project_type: str) -> str:
        """Generate project-type-appropriate artifact"""
        if project_type == "software":
            return self.generate_code(context)
        elif project_type == "business":
            return self.generate_business_plan(context)
        elif project_type == "research":
            return self.generate_research_protocol(context)
        elif project_type == "creative":
            return self.generate_creative_brief(context)
        elif project_type == "marketing":
            return self.generate_marketing_plan(context)
        elif project_type == "educational":
            return self.generate_curriculum(context)
        else:
            return self.generate_code(context)  # Default to code

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
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self.orchestrator.system_monitor.process(
                {
                    "action": "track_tokens",
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "cost_estimate": self._calculate_cost(response.usage),
                }
            )

            return response.content[0].text

        except Exception as e:
            return f"Error generating code: {e}"

    def generate_business_plan(self, context: str) -> str:
        """Generate business plan document"""
        prompt = f"""
        Generate a comprehensive business plan based on this context:

        {context}

        Please create a professional business plan including:
        1. Executive Summary - Brief overview of the business opportunity
        2. Market Analysis & Opportunity - Market size, trends, competitive landscape
        3. Business Model & Revenue Streams - How the business generates revenue
        4. Value Proposition - Unique advantages and customer benefits
        5. Go-to-Market Strategy - Launch and acquisition plan
        6. Financial Projections - Revenue forecasts, profitability timeline
        7. Competitive Advantage - Key differentiators
        8. Risk Analysis & Mitigation - Key risks and mitigation strategies
        9. Implementation Timeline - Phase-by-phase roadmap
        10. Resource Requirements - Team, funding, and operational needs

        Format as a professional business plan document with clear sections and bullet points.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self.orchestrator.system_monitor.process(
                {
                    "action": "track_tokens",
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "cost_estimate": self._calculate_cost(response.usage),
                }
            )

            return response.content[0].text

        except Exception as e:
            return f"Error generating business plan: {e}"

    def generate_research_protocol(self, context: str) -> str:
        """Generate research protocol and methodology document"""
        prompt = f"""
        Generate a detailed research protocol and methodology document based on this context:

        {context}

        Please create a comprehensive research protocol including:
        1. Research Question & Hypothesis - Clear statement of inquiry
        2. Literature Review Summary - Current state of knowledge
        3. Research Gap - What is unknown and why it matters
        4. Methodology & Research Design - Approach and justification
        5. Data Collection Plan - Methods, instruments, and timeline
        6. Analysis Approach - Statistical or qualitative analysis strategy
        7. Ethical Considerations - IRB requirements, informed consent, data protection
        8. Quality Assurance & Validation - Reliability and validity measures
        9. Timeline & Resources - Detailed project schedule and required resources
        10. Expected Outcomes - Anticipated findings and impact

        Format as a formal research protocol document suitable for academic or professional review.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self.orchestrator.system_monitor.process(
                {
                    "action": "track_tokens",
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "cost_estimate": self._calculate_cost(response.usage),
                }
            )

            return response.content[0].text

        except Exception as e:
            return f"Error generating research protocol: {e}"

    def generate_creative_brief(self, context: str) -> str:
        """Generate creative/design brief document"""
        prompt = f"""
        Generate a comprehensive creative brief and design specifications based on this context:

        {context}

        Please create a professional creative brief including:
        1. Project Overview - Purpose and vision
        2. Target Audience - Demographics, psychographics, preferences
        3. Brand Identity - Core values, personality, positioning
        4. Design Principles - Aesthetic direction and guidelines
        5. Visual Style - Color palette, typography, imagery style
        6. Content Strategy - Messaging, tone, key communication points
        7. Brand Guidelines - Logo usage, consistency requirements
        8. Deliverables - Specific outputs and formats needed
        9. Success Metrics - How to measure creative effectiveness
        10. Timeline & Resources - Project schedule and team requirements

        Format as a professional creative brief document with visual style descriptions and clear guidelines.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self.orchestrator.system_monitor.process(
                {
                    "action": "track_tokens",
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "cost_estimate": self._calculate_cost(response.usage),
                }
            )

            return response.content[0].text

        except Exception as e:
            return f"Error generating creative brief: {e}"

    def generate_marketing_plan(self, context: str) -> str:
        """Generate marketing campaign plan document"""
        prompt = f"""
        Generate a comprehensive marketing campaign plan based on this context:

        {context}

        Please create a detailed marketing plan including:
        1. Campaign Overview - Objectives and success criteria
        2. Target Market Analysis - Audience segments, needs, behaviors
        3. Market Positioning - Competitive advantages and differentiation
        4. Campaign Strategy - Key messages and tactical approach
        5. Channel Strategy - Marketing channels and media mix
        6. Content Plan - Content types, themes, and distribution
        7. Campaign Timeline - Launch date, duration, key milestones
        8. Budget Allocation - Resource distribution across channels
        9. Performance Metrics - KPIs and measurement approach
        10. Risk Mitigation - Contingency plans for common challenges

        Format as a professional marketing campaign plan with clear sections and actionable recommendations.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self.orchestrator.system_monitor.process(
                {
                    "action": "track_tokens",
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "cost_estimate": self._calculate_cost(response.usage),
                }
            )

            return response.content[0].text

        except Exception as e:
            return f"Error generating marketing plan: {e}"

    def generate_curriculum(self, context: str) -> str:
        """Generate educational curriculum document"""
        prompt = f"""
        Generate a comprehensive curriculum design document based on this context:

        {context}

        Please create a detailed curriculum including:
        1. Course Overview - Learning objectives and target audience
        2. Curriculum Philosophy - Teaching approach and pedagogical foundation
        3. Learning Outcomes - Specific competencies students will achieve
        4. Content Structure - Topics, units, and learning progression
        5. Module Design - Detailed breakdown of each module or unit
        6. Assessment Strategy - Formative and summative assessment methods
        7. Learning Activities - Instructional activities and engagement strategies
        8. Resources & Materials - Required textbooks, tools, and multimedia
        9. Lesson Plan Template - Framework for individual lessons
        10. Evaluation Plan - How to measure curriculum effectiveness and student progress

        Format as a professional curriculum document suitable for educators and training programs.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self.orchestrator.system_monitor.process(
                {
                    "action": "track_tokens",
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "cost_estimate": self._calculate_cost(response.usage),
                }
            )

            return response.content[0].text

        except Exception as e:
            return f"Error generating curriculum: {e}"

    def generate_documentation(
        self, project: ProjectContext, artifact: str, artifact_type: str = "code"
    ) -> str:
        """Generate documentation for any artifact type"""
        doc_instructions = {
            "code": """
        Please include:
        1. Project overview and purpose
        2. Installation instructions
        3. Usage examples
        4. API documentation (if applicable)
        5. Configuration options
        6. Troubleshooting section
        """,
            "business_plan": """
        Please include:
        1. Implementation roadmap and phases
        2. Resource allocation and team structure
        3. Success metrics and KPIs
        4. Contingency plans
        5. Key stakeholder roles and responsibilities
        6. Quick reference guides for each section
        """,
            "research_protocol": """
        Please include:
        1. Supplementary technical guidance for researchers
        2. Data management best practices
        3. Analysis procedure details and decision trees
        4. Troubleshooting guide for common issues
        5. References and additional resources
        6. Appendices with templates and forms
        """,
            "creative_brief": """
        Please include:
        1. Creative process and workflow
        2. Production guidelines and specifications
        3. Asset organization and file structure
        4. Revision and approval process
        5. Quick reference guides for key assets
        6. Common variations and use cases
        """,
            "marketing_plan": """
        Please include:
        1. Campaign execution roadmap
        2. Content calendar and publishing schedule
        3. Team roles and communication plan
        4. Campaign monitoring and analytics setup
        5. Budget tracking and optimization
        6. Contingency tactics and pivot strategies
        """,
            "curriculum": """
        Please include:
        1. Instructor preparation guidelines
        2. Day-by-day lesson delivery tips
        3. Student assessment rubrics
        4. Resource links and supplementary materials
        5. Troubleshooting common student challenges
        6. Accommodation and differentiation strategies
        """,
        }

        doc_section = doc_instructions.get(artifact_type, doc_instructions["code"])

        # Handle None or missing artifact
        artifact_preview = (
            (artifact[:2000] if artifact else "") + "..."
            if artifact
            else "(No artifact generated yet)"
        )

        prompt = f"""
        Create comprehensive implementation documentation for this {artifact_type} project:

        Project: {project.name}
        Goals: {project.goals}
        Phase: {project.phase}

        {artifact_type.replace('_', ' ').title()}:
        {artifact_preview}

        {doc_section}
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self.orchestrator.system_monitor.process(
                {
                    "action": "track_tokens",
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "cost_estimate": self._calculate_cost(response.usage),
                }
            )

            return response.content[0].text

        except Exception as e:
            return f"Error generating documentation: {e}"

    def test_connection(self) -> bool:
        """Test connection to Claude API"""
        try:
            self.client.messages.create(
                model=self.model,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": "Test"}],
            )
            self.logger.info("Claude API connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"Claude API connection test failed: {e}")
            raise APIError(
                f"Failed to connect to Claude API: {e}", error_type="CONNECTION_ERROR"
            ) from e

    # Helper Methods

    def _track_token_usage(self, usage: Any, operation: str) -> None:
        """Track token usage and emit event"""
        total_tokens = usage.input_tokens + usage.output_tokens
        cost = self._calculate_cost(usage)

        self.orchestrator.system_monitor.process(
            {
                "action": "track_tokens",
                "operation": operation,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": total_tokens,
                "cost_estimate": cost,
            }
        )

        self.orchestrator.event_emitter.emit(
            EventType.TOKEN_USAGE,
            {
                "operation": operation,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": total_tokens,
                "cost_estimate": cost,
            },
        )

    async def _track_token_usage_async(self, usage: Any, operation: str) -> None:
        """Track token usage asynchronously"""
        await asyncio.to_thread(self._track_token_usage, usage, operation)

    def _calculate_cost(self, usage: Any) -> float:
        """Calculate estimated cost based on token usage"""
        # Claude Sonnet 4.5 pricing (approximate - check pricing page for latest)
        input_cost_per_1k = 0.003  # $0.003 per 1K input tokens
        output_cost_per_1k = 0.015  # $0.015 per 1K output tokens

        input_cost = (usage.input_tokens / 1000) * input_cost_per_1k
        output_cost = (usage.output_tokens / 1000) * output_cost_per_1k

        return input_cost + output_cost

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from Claude response with error handling"""
        try:
            # Clean up markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            # Find JSON object in the response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1

            if 0 <= start < end:
                json_text = response_text[start:end]
                parsed_data = json.loads(json_text)

                if isinstance(parsed_data, dict):
                    return parsed_data
                else:
                    return {}
            else:
                self.logger.warning("No JSON object found in response")
                return {}

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            self.orchestrator.event_emitter.emit(
                EventType.LOG_WARNING, {"message": f"Could not parse JSON response: {e}"}
            )
            return {}

    def generate_socratic_question(self, prompt: str) -> str:
        """Generate a Socratic question using Claude"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self._track_token_usage(response.usage, "generate_socratic_question")

            return response.content[0].text.strip()

        except Exception as e:
            self.logger.error(f"Error generating Socratic question: {e}")
            self.orchestrator.event_emitter.emit(
                EventType.LOG_ERROR, {"message": f"Failed to generate Socratic question: {e}"}
            )
            raise APIError(
                f"Error generating Socratic question: {e}", error_type="GENERATION_ERROR"
            ) from e

    def generate_suggestions(self, current_question: str, project: ProjectContext) -> str:
        """Generate helpful suggestions when user can't answer a question"""

        # Get recent conversation for context
        recent_conversation = ""
        if project.conversation_history:
            recent_messages = project.conversation_history[-6:]
            for msg in recent_messages:
                role = "Assistant" if msg["type"] == "assistant" else "User"
                recent_conversation += f"{role}: {msg['content']}\n"

        # Get relevant knowledge from vector database
        relevant_knowledge = ""
        knowledge_results = self.orchestrator.vector_db.search_similar(current_question, top_k=3)
        if knowledge_results:
            relevant_knowledge = "\n".join(
                [result["content"][:300] for result in knowledge_results]
            )

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
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self.orchestrator.system_monitor.process(
                {
                    "action": "track_tokens",
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "cost_estimate": self._calculate_cost(response.usage),
                }
            )

            return response.content[0].text.strip()

        except Exception as e:
            # Fallback suggestions if Claude API fails
            self.logger.warning(f"Error generating suggestions, using fallback: {e}")
            fallback_suggestions = {
                "discovery": """Here are some suggestions to help you think through this:

    • Consider researching similar applications or tools in your problem domain
    • Think about specific pain points you've experienced that this could solve
    • Ask potential users what features would be most valuable to them
    • Look at existing solutions and identify what's missing or could be improved""",
                "analysis": """Here are some suggestions to help you think through this:

    • Break down the technical challenge into smaller, specific problems
    • Research what libraries or frameworks are commonly used for this type of project
    • Consider scalability, security, and performance requirements early
    • Look up case studies of similar technical implementations""",
                "design": """Here are some suggestions to help you think through this:

    • Start with a simple architecture and plan how to extend it later
    • Consider using established design patterns like MVC, Repository, or Factory
    • Think about how different components will communicate with each other
    • Sketch out the data flow and user interaction patterns""",
                "implementation": """Here are some suggestions to help you think through this:

    • Break the project into small, manageable milestones
    • Consider starting with a minimal viable version first
    • Think about your development environment and tooling needs
    • Plan your testing strategy alongside your implementation approach""",
            }

            return fallback_suggestions.get(
                project.phase,
                "Consider breaking the question into smaller parts and researching each "
                "aspect individually.",
            )

    def generate_response(
        self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7
    ) -> str:
        """
        Generate a general response from Claude for any prompt.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response (default: 2000)
            temperature: Temperature for response generation (default: 0.7)

        Returns:
            Claude's response as a string

        Raises:
            APIError: If API call fails
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self._track_token_usage(response.usage, "generate_response")

            return response.content[0].text.strip()

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            self.orchestrator.event_emitter.emit(
                EventType.LOG_ERROR, {"message": f"Failed to generate response: {e}"}
            )
            raise APIError(f"Error generating response: {e}", error_type="GENERATION_ERROR") from e

    async def generate_response_async(
        self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7
    ) -> str:
        """
        Generate a general response from Claude asynchronously.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation

        Returns:
            Claude's response as a string

        Raises:
            APIError: If API call fails
        """
        try:
            response = await self.async_client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            await self._track_token_usage_async(response.usage, "generate_response_async")

            return response.content[0].text.strip()

        except Exception as e:
            self.logger.error(f"Error generating response (async): {e}")
            raise APIError(f"Error generating response: {e}", error_type="GENERATION_ERROR") from e
