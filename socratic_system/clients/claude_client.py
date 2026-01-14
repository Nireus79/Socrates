"""
Claude API client for Socrates AI

Provides both synchronous and asynchronous interfaces for calling Claude API,
with automatic token tracking and structured error handling.
"""

import asyncio
import hashlib
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

    def __init__(
        self, api_key: str, orchestrator: "AgentOrchestrator", subscription_token: str = None
    ):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (required fallback)
            orchestrator: Reference to AgentOrchestrator for event emission and token tracking
            subscription_token: Optional - Claude subscription token for subscription-based auth
        """
        self.api_key = api_key
        self.subscription_token = subscription_token
        self.orchestrator = orchestrator
        self.model = orchestrator.config.claude_model
        self.logger = logging.getLogger("socrates.clients.claude")

        # Initialize clients for both authentication methods
        # API key based clients
        self.client = anthropic.Anthropic(api_key=api_key)
        self.async_client = anthropic.AsyncAnthropic(api_key=api_key)

        # Subscription token based clients (if available)
        self.subscription_client = None
        self.subscription_async_client = None
        if subscription_token:
            self.subscription_client = anthropic.Anthropic(api_key=subscription_token)
            self.subscription_async_client = anthropic.AsyncAnthropic(api_key=subscription_token)
            self.logger.info("Subscription-based clients initialized")

        # Cache for insights extraction to avoid redundant Claude API calls
        # Maps message hash -> extracted insights
        self._insights_cache: Dict[str, Dict[str, Any]] = {}

        # Cache for question generation to avoid redundant Claude API calls
        # Maps question_cache_key (project_id:phase:question_count) -> generated question
        self._question_cache: Dict[str, str] = {}

    def get_auth_credential(self, user_auth_method: str = "api_key") -> str:
        """
        Get the appropriate credential based on user's preferred auth method.

        Args:
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')

        Returns:
            The appropriate credential (API key or subscription token)

        Raises:
            ValueError: If the requested auth method is not configured
        """
        if user_auth_method == "subscription":
            if not self.subscription_token:
                raise ValueError(
                    "Subscription token not configured. "
                    "Set ANTHROPIC_SUBSCRIPTION_TOKEN environment variable."
                )
            return self.subscription_token
        else:  # api_key
            if not self.api_key:
                raise ValueError(
                    "API key not configured. "
                    "Set ANTHROPIC_API_KEY or API_KEY_CLAUDE environment variable."
                )
            return self.api_key

    def _get_user_api_key(self, user_id: str = None) -> tuple:
        """
        Get API key for a user, trying in order:
        1. User's stored API key from database (decrypted)
        2. Environment variable (fallback for all users)
        3. Return None if nothing available

        Args:
            user_id: The user ID to fetch key for

        Returns:
            tuple: (api_key, is_user_specific) - api_key is the key to use, is_user_specific indicates if it's from user settings
                   Returns (None, False) if no key found

        Raises:
            APIError: If user has no key and env variable is not set
        """
        # Try to get user's stored API key from database
        if user_id:
            try:
                stored_key = self.orchestrator.database.get_api_key(user_id, "claude")
                if stored_key:
                    # Decrypt the stored key
                    decrypted_key = self._decrypt_api_key_from_db(stored_key)
                    if decrypted_key:
                        self.logger.info(f"Using user-specific API key for user {user_id}")
                        return decrypted_key, True
            except Exception as e:
                self.logger.warning(f"Error fetching user API key for {user_id}: {e}")

        # Fall back to environment variable (but not placeholder)
        env_key = self.api_key
        if env_key and not env_key.startswith("placeholder"):
            self.logger.debug("Using environment variable API key as fallback")
            return env_key, False

        # No key available - raise error with helpful message
        raise APIError(
            f"No API key configured. Please set your API key in Settings > LLM > Anthropic or set ANTHROPIC_API_KEY environment variable.",
            error_type="MISSING_API_KEY"
        )

    def _decrypt_api_key_from_db(self, encrypted_key: str) -> str:
        """
        Decrypt an API key stored in the database.

        Args:
            encrypted_key: The encrypted API key from database

        Returns:
            Decrypted API key string, or None if decryption fails
        """
        try:
            from cryptography.fernet import Fernet
            import os

            # Get encryption key from environment or use default
            encryption_key_base = os.getenv("SOCRATES_ENCRYPTION_KEY", "default-insecure-key-change-in-production")

            # Log which key is being used (without revealing the actual key)
            key_source = "SOCRATES_ENCRYPTION_KEY env var" if os.getenv("SOCRATES_ENCRYPTION_KEY") else "default insecure key"
            self.logger.info(f"Decrypting API key using: {key_source}")

            # Derive the encryption key (must match what was used to encrypt)
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
            import base64

            salt = b"socrates-salt"
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(encryption_key_base.encode()))

            cipher = Fernet(derived_key)
            decrypted = cipher.decrypt(encrypted_key.encode())
            self.logger.info("API key decrypted successfully")
            return decrypted.decode()

        except Exception as e:
            self.logger.error(f"Error decrypting API key: {e}")
            self.logger.error(f"This usually means the encryption key doesn't match. "
                            f"Set SOCRATES_ENCRYPTION_KEY env variable if key was encrypted with a specific key.")
            return None

    def _get_client(self, user_auth_method: str = "api_key", user_id: str = None):
        """
        Get the appropriate sync client based on user's auth method and user-specific API key.

        Args:
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID to fetch user-specific API key

        Returns:
            Anthropic sync client instance

        Raises:
            APIError: If auth method requires API key but none is available
        """
        if user_auth_method == "subscription":
            if self.subscription_client:
                return self.subscription_client
            raise APIError(
                "Subscription token not configured. Set ANTHROPIC_SUBSCRIPTION_TOKEN environment variable.",
                error_type="MISSING_SUBSCRIPTION_TOKEN"
            )

        # For api_key auth method, try to get user-specific key
        try:
            api_key, _ = self._get_user_api_key(user_id)
            if api_key and not api_key.startswith("placeholder"):
                # Create a new client with the user's API key
                return anthropic.Anthropic(api_key=api_key)
            elif api_key and api_key.startswith("placeholder"):
                # Placeholder key detected - user hasn't set their API key yet
                raise APIError(
                    f"No API key configured. Please set your API key in Settings > LLM > Anthropic or set ANTHROPIC_API_KEY environment variable.",
                    error_type="MISSING_API_KEY"
                )
        except APIError:
            raise
        except Exception as e:
            self.logger.warning(f"Error getting user API key: {e}")
            raise APIError(
                f"No API key configured. Please set your API key in Settings > LLM > Anthropic or set ANTHROPIC_API_KEY environment variable.",
                error_type="MISSING_API_KEY"
            )

        # Default client should not be used if it has placeholder key
        if self.api_key and self.api_key.startswith("placeholder"):
            raise APIError(
                f"No API key configured. Please set your API key in Settings > LLM > Anthropic or set ANTHROPIC_API_KEY environment variable.",
                error_type="MISSING_API_KEY"
            )

        # Fallback to default client if it has a real key
        return self.client

    def _get_async_client(self, user_auth_method: str = "api_key", user_id: str = None):
        """
        Get the appropriate async client based on user's auth method and user-specific API key.

        Args:
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID to fetch user-specific API key

        Returns:
            Anthropic async client instance

        Raises:
            APIError: If auth method requires API key but none is available
        """
        if user_auth_method == "subscription":
            if self.subscription_async_client:
                return self.subscription_async_client
            raise APIError(
                "Subscription token not configured. Set ANTHROPIC_SUBSCRIPTION_TOKEN environment variable.",
                error_type="MISSING_SUBSCRIPTION_TOKEN"
            )

        # For api_key auth method, try to get user-specific key
        try:
            api_key, _ = self._get_user_api_key(user_id)
            if api_key and not api_key.startswith("placeholder"):
                # Create a new async client with the user's API key
                return anthropic.AsyncAnthropic(api_key=api_key)
            elif api_key and api_key.startswith("placeholder"):
                # Placeholder key detected - user hasn't set their API key yet
                raise APIError(
                    f"No API key configured. Please set your API key in Settings > LLM > Anthropic or set ANTHROPIC_API_KEY environment variable.",
                    error_type="MISSING_API_KEY"
                )
        except APIError:
            raise
        except Exception as e:
            self.logger.warning(f"Error getting user API key: {e}")
            raise APIError(
                f"No API key configured. Please set your API key in Settings > LLM > Anthropic or set ANTHROPIC_API_KEY environment variable.",
                error_type="MISSING_API_KEY"
            )

        # Default client should not be used if it has placeholder key
        if self.api_key and self.api_key.startswith("placeholder"):
            raise APIError(
                f"No API key configured. Please set your API key in Settings > LLM > Anthropic or set ANTHROPIC_API_KEY environment variable.",
                error_type="MISSING_API_KEY"
            )

        # Fallback to default async client if it has a real key
        return self.async_client

    def extract_insights(self, user_response: str, project: ProjectContext, user_auth_method: str = "api_key", user_id: str = None) -> Dict:
        """
        Extract insights from user response using Claude (synchronous) with caching.

        Args:
            user_response: The user's response text
            project: The project context
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID for fetching user-specific API key

        Returns:
            Dictionary of extracted insights
        """
        # Handle empty or non-informative responses
        if not user_response or len(user_response.strip()) < 3:
            return {}

        # Handle common non-informative responses
        non_informative = ["i don't know", "idk", "not sure", "no idea", "dunno", "unsure"]
        if user_response.lower().strip() in non_informative:
            return {"note": "User expressed uncertainty - may need more guidance"}

        # Check cache first to avoid redundant Claude API calls
        cache_key = self._get_cache_key(user_response)
        if cache_key in self._insights_cache:
            self.logger.debug("Cache hit for insights extraction")
            return self._insights_cache[cache_key]

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
            # Get the appropriate client based on user's auth method and user-specific API key
            client = self._get_client(user_auth_method, user_id)
            response = client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self._track_token_usage(response.usage, "extract_insights")

            # Try to parse JSON response
            insights = self._parse_json_response(response.content[0].text.strip())

            # Cache the result for future identical messages
            self._insights_cache[cache_key] = insights

            return insights

        except Exception as e:
            self.logger.error(f"Error extracting insights: {e}")
            self.orchestrator.event_emitter.emit(
                EventType.LOG_ERROR, {"message": f"Failed to extract insights: {e}"}
            )
            return {}

    async def extract_insights_async(self, user_response: str, project: ProjectContext, user_auth_method: str = "api_key") -> Dict:
        """
        Extract insights from user response asynchronously with caching.

        Args:
            user_response: The user's response text
            project: The project context
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')

        Returns:
            Dictionary of extracted insights
        """
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

        # Check cache first to avoid redundant Claude API calls
        cache_key = self._get_cache_key(user_response)
        if cache_key in self._insights_cache:
            self.logger.debug("Cache hit for insights extraction")
            return self._insights_cache[cache_key]

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
            # Get the appropriate async client based on user's auth method
            async_client = self._get_async_client(user_auth_method, user_id)
            response = await async_client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage asynchronously
            await self._track_token_usage_async(response.usage, "extract_insights_async")

            insights = self._parse_json_response(response.content[0].text.strip())

            # Cache the result for future identical messages
            self._insights_cache[cache_key] = insights

            return insights

        except Exception as e:
            self.logger.error(f"Error extracting insights (async): {e}")
            return {}

    def generate_conflict_resolution_suggestions(
        self, conflict: ConflictInfo, project: ProjectContext, user_auth_method: str = "api_key"
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
            client = self._get_client(user_auth_method, user_id)
            response = client.messages.create(
                model=self.model,
                max_tokens=600,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text.strip()

        except Exception as e:
            return f"Error generating suggestions: {e}"

    def generate_artifact(self, context: str, project_type: str, user_auth_method: str = "api_key", user_id: str = None) -> str:
        """Generate project-type-appropriate artifact"""
        if project_type == "software":
            return self.generate_code(context, user_auth_method, user_id)
        elif project_type == "business":
            return self.generate_business_plan(context, user_auth_method, user_id)
        elif project_type == "research":
            return self.generate_research_protocol(context, user_auth_method, user_id)
        elif project_type == "creative":
            return self.generate_creative_brief(context, user_auth_method, user_id)
        elif project_type == "marketing":
            return self.generate_marketing_plan(context, user_auth_method, user_id)
        elif project_type == "educational":
            return self.generate_curriculum(context, user_auth_method, user_id)
        else:
            return self.generate_code(context, user_auth_method, user_id)  # Default to code

    def generate_code(self, context: str, user_auth_method: str = "api_key", user_id: str = None) -> str:
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
            client = self._get_client(user_auth_method, user_id)

            response = client.messages.create(
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

    def generate_business_plan(self, context: str, user_auth_method: str = "api_key", user_id: str = None) -> str:
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
            client = self._get_client(user_auth_method, user_id)

            response = client.messages.create(
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

    def generate_research_protocol(self, context: str, user_auth_method: str = "api_key", user_id: str = None) -> str:
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
            client = self._get_client(user_auth_method, user_id)

            response = client.messages.create(
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

    def generate_creative_brief(self, context: str, user_auth_method: str = "api_key", user_id: str = None) -> str:
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
            client = self._get_client(user_auth_method, user_id)

            response = client.messages.create(
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

    def generate_marketing_plan(self, context: str, user_auth_method: str = "api_key", user_id: str = None) -> str:
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
            client = self._get_client(user_auth_method, user_id)

            response = client.messages.create(
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

    def generate_curriculum(self, context: str, user_auth_method: str = "api_key", user_id: str = None) -> str:
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
            client = self._get_client(user_auth_method, user_id)

            response = client.messages.create(
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
        self, project: ProjectContext, artifact: str, artifact_type: str = "code", user_auth_method: str = "api_key", user_id: str = None
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
            client = self._get_client(user_auth_method, user_id)

            response = client.messages.create(
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

    def test_connection(self, user_auth_method: str = "api_key") -> bool:
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

    def _get_cache_key(self, message: str) -> str:
        """Generate cache key for a message using SHA256 hash"""
        return hashlib.sha256(message.encode()).hexdigest()

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

    def _parse_json_response(self, response_text: str) -> any:
        """Parse JSON from Claude response with error handling. Returns dict or list."""
        try:
            # Clean up markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            # Try to find JSON array first [...]
            start_array = response_text.find("[")
            end_array = response_text.rfind("]") + 1

            # Then try to find JSON object {...}
            start_obj = response_text.find("{")
            end_obj = response_text.rfind("}") + 1

            # Prefer whichever starts first (appears earlier in the response)
            json_text = None
            if start_array >= 0 and end_array > start_array:
                if start_obj >= 0 and start_obj < start_array:
                    # Object starts before array
                    if 0 <= start_obj < end_obj:
                        json_text = response_text[start_obj:end_obj]
                else:
                    # Array starts first or no object
                    json_text = response_text[start_array:end_array]
            elif 0 <= start_obj < end_obj:
                # Only object found
                json_text = response_text[start_obj:end_obj]

            if json_text:
                parsed_data = json.loads(json_text)
                # Return the parsed data as-is (could be dict or list)
                return parsed_data
            else:
                self.logger.warning("No JSON object or array found in response")
                return {}

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            self.orchestrator.event_emitter.emit(
                EventType.LOG_WARNING, {"message": f"Could not parse JSON response: {e}"}
            )
            return {}

    def generate_socratic_question(self, prompt: str, cache_key: str = None, user_auth_method: str = "api_key", user_id: str = None) -> str:
        """
        Generate a Socratic question using Claude with optional caching.

        Note: Cache is disabled for question generation to prevent repeated questions
        when conversation history changes. Each question is generated fresh.

        Args:
            prompt: The prompt for question generation
            cache_key: Optional cache key (not used, for backward compatibility)
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID for fetching user-specific API key

        Returns:
            Generated Socratic question

        Raises:
            APIError: If API call fails
        """
        # Cache is intentionally disabled for questions to ensure variety and avoid
        # returning stale cached questions when conversation history changes

        try:
            # Get the appropriate client based on user's auth method and user-specific API key
            client = self._get_client(user_auth_method, user_id)
            response = client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            # Track token usage
            self._track_token_usage(response.usage, "generate_socratic_question")

            question = response.content[0].text.strip()
            return question

        except Exception as e:
            self.logger.error(f"Error generating Socratic question: {e}")
            self.orchestrator.event_emitter.emit(
                EventType.LOG_ERROR, {"message": f"Failed to generate Socratic question: {e}"}
            )
            raise APIError(
                f"Error generating Socratic question: {e}", error_type="GENERATION_ERROR"
            ) from e

    def generate_suggestions(self, current_question: str, project: ProjectContext, user_auth_method: str = "api_key") -> str:
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
            client = self._get_client(user_auth_method, user_id)

            response = client.messages.create(
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
        self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7, user_auth_method: str = "api_key", user_id: str = None
    ) -> str:
        """
        Generate a general response from Claude for any prompt.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response (default: 2000)
            temperature: Temperature for response generation (default: 0.7)
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID for fetching user-specific API key

        Returns:
            Claude's response as a string

        Raises:
            APIError: If API call fails
        """
        try:
            # Get the appropriate client based on user's auth method and user-specific API key
            client = self._get_client(user_auth_method, user_id)
            response = client.messages.create(
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
        self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7, user_auth_method: str = "api_key", user_id: str = None
    ) -> str:
        """
        Generate a general response from Claude asynchronously.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID for fetching user-specific API key

        Returns:
            Claude's response as a string

        Raises:
            APIError: If API call fails
        """
        try:
            # Get the appropriate async client based on user's auth method and user-specific API key
            async_client = self._get_async_client(user_auth_method, user_id)
            response = await async_client.messages.create(
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

    # =====================================================================
    # PHASE 2: ADDITIONAL ASYNC METHODS FOR HIGH-TRAFFIC OPERATIONS
    # =====================================================================

    async def generate_code_async(self, context: str, user_auth_method: str = "api_key", user_id: str = None) -> str:
        """Generate code asynchronously (high-traffic for code_generator agent)."""
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
            client = self._get_async_client(user_auth_method)

            response = await client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            await self._track_token_usage_async(response.usage, "generate_code_async")
            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Error generating code (async): {e}")
            return f"Error generating code: {e}"

    async def generate_socratic_question_async(self, prompt: str, cache_key: str = None, user_auth_method: str = "api_key", user_id: str = None) -> str:
        """
        Generate socratic question asynchronously (high-frequency operation).

        This is called very frequently by socratic_counselor agent.
        Async implementation enables concurrent question generation.

        Note: Cache is disabled for question generation to prevent repeated questions
        when conversation history changes. Each question is generated fresh.

        Args:
            prompt: The prompt for question generation
            cache_key: Optional cache key (not used, for backward compatibility)
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID for fetching user-specific API key

        Returns:
            Generated Socratic question
        """
        try:
            # Get the appropriate async client based on user's auth method and user-specific API key
            async_client = self._get_async_client(user_auth_method, user_id)
            response = await async_client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=0.7,
            )

            await self._track_token_usage_async(response.usage, "generate_socratic_question_async")
            question = response.content[0].text.strip()
            return question

        except Exception as e:
            self.logger.error(f"Error generating socratic question (async): {e}")
            return "I'd like to understand your thinking better. Can you elaborate?"

    async def detect_conflicts_async(self, requirements: list, user_auth_method: str = "api_key") -> list:
        """
        Detect conflicts in requirements asynchronously.

        Used by conflict_detector agent for analyzing requirement consistency.
        """
        prompt = f"""
        Analyze these project requirements for potential conflicts or inconsistencies:

        Requirements:
        {json.dumps(requirements, indent=2)}

        Please identify:
        1. Direct conflicts between requirements
        2. Potential technical conflicts (e.g., scalability vs. low-latency)
        3. Resource/timeline conflicts
        4. Team capability conflicts

        For each conflict, provide:
        - Requirement IDs involved
        - Type of conflict
        - Severity (high/medium/low)
        - Suggested resolution

        Return as JSON array of conflict objects.
        """

        try:
            client = self._get_async_client(user_auth_method)

            response = await client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            await self._track_token_usage_async(response.usage, "detect_conflicts_async")
            return self._parse_json_response(response.content[0].text.strip())

        except Exception as e:
            self.logger.error(f"Error detecting conflicts (async): {e}")
            return []

    async def analyze_context_async(self, project: ProjectContext, user_auth_method: str = "api_key") -> str:
        """
        Analyze project context asynchronously.

        Used by context_analyzer agent for building context summaries.
        """
        prompt = f"""
        Provide a concise analysis of this project context:

        Project: {project.name}
        Phase: {project.phase}
        Goals: {project.goals or 'Not specified'}
        Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}
        Team Structure: {getattr(project, 'team_structure', 'Not specified')}
        Status: {project.status}
        Progress: {project.progress}%

        Please provide:
        1. Key project focus areas
        2. Technical considerations
        3. Team dynamics implications
        4. Progress assessment
        5. Recommended next focus areas

        Keep response concise (200-300 words).
        """

        try:
            client = self._get_async_client(user_auth_method)

            response = await client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}],
            )

            await self._track_token_usage_async(response.usage, "analyze_context_async")
            return response.content[0].text.strip()

        except Exception as e:
            self.logger.error(f"Error analyzing context (async): {e}")
            return ""

    async def generate_business_plan_async(self, context: str, user_auth_method: str = "api_key") -> str:
        """Generate business plan asynchronously."""
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
            client = self._get_async_client(user_auth_method)

            response = await client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            await self._track_token_usage_async(response.usage, "generate_business_plan_async")
            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Error generating business plan (async): {e}")
            return f"Error generating business plan: {e}"

    async def generate_documentation_async(self, context: str, doc_type: str = "technical", user_auth_method: str = "api_key") -> str:
        """
        Generate documentation asynchronously.

        Used by document_processor agent for creating various documentation types.
        """
        prompt = f"""
        Generate comprehensive {doc_type} documentation based on this context:

        {context}

        Create clear, well-organized documentation including:
        - Overview and purpose
        - Key components or sections
        - Usage instructions or guidelines
        - Examples or case studies
        - Troubleshooting or FAQs
        - References or resources

        Use professional markdown formatting.
        """

        try:
            client = self._get_async_client(user_auth_method)

            response = await client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}],
            )

            await self._track_token_usage_async(response.usage, "generate_documentation_async")
            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Error generating documentation (async): {e}")
            return f"Error generating documentation: {e}"

    async def extract_tech_recommendations_async(
        self, project: ProjectContext, query: str, user_auth_method: str = "api_key"
    ) -> Dict[str, Any]:
        """
        Extract technology recommendations asynchronously.

        Used by multi_llm_agent for analyzing tech stack recommendations.
        """
        prompt = f"""
        Based on this project context, provide technology recommendations for: {query}

        Project Context:
        - Name: {project.name}
        - Phase: {project.phase}
        - Current Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}
        - Goals: {project.goals}
        - Constraints: {', '.join(project.constraints) if hasattr(project, 'constraints') else 'None specified'}

        Please provide:
        1. Recommended technologies (with brief justification)
        2. Pros and cons of each recommendation
        3. Integration considerations
        4. Learning curve assessment
        5. Cost implications

        Return as JSON with structured recommendations.
        """

        try:
            client = self._get_async_client(user_auth_method)

            response = await client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}],
            )

            await self._track_token_usage_async(
                response.usage, "extract_tech_recommendations_async"
            )
            return self._parse_json_response(response.content[0].text.strip())

        except Exception as e:
            self.logger.error(f"Error extracting tech recommendations (async): {e}")
            return {}

    async def evaluate_quality_async(
        self, content: str, content_type: str = "code", user_auth_method: str = "api_key"
    ) -> Dict[str, Any]:
        """
        Evaluate quality of generated content asynchronously.

        Used by quality_controller agent for assessing output quality.
        """
        prompt = f"""
        Evaluate the quality of this {content_type}:

        {content}

        Please assess:
        1. Code/content quality (structure, clarity, best practices)
        2. Completeness (does it cover all requirements?)
        3. Correctness (any obvious errors or issues?)
        4. Maintainability (easy to understand and modify?)
        5. Overall score (1-10)

        Provide specific feedback and suggestions for improvement.
        Return as JSON with scores and feedback.
        """

        try:
            client = self._get_async_client(user_auth_method)

            response = await client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            await self._track_token_usage_async(response.usage, "evaluate_quality_async")
            return self._parse_json_response(response.content[0].text.strip())

        except Exception as e:
            self.logger.error(f"Error evaluating quality (async): {e}")
            return {"score": 0, "feedback": str(e)}

    async def generate_suggestions_async(
        self, current_question: str, project: ProjectContext, user_auth_method: str = "api_key"
    ) -> str:
        """
        Generate follow-up suggestions asynchronously.

        Used by socratic_counselor for suggesting related questions.
        """
        prompt = f"""
        Based on this question in the context of the user's project, suggest 2-3 related follow-up questions:

        Current Question: {current_question}

        Project Context:
        - Phase: {project.phase}
        - Status: {project.status}
        - Progress: {project.progress}%

        The follow-up questions should:
        1. Build on the current question
        2. Help deepen understanding
        3. Move the project forward
        4. Be appropriate for the current phase

        Format each suggestion on a new line starting with "- "
        """

        try:
            client = self._get_async_client(user_auth_method)

            response = await client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.6,
                messages=[{"role": "user", "content": prompt}],
            )

            await self._track_token_usage_async(response.usage, "generate_suggestions_async")
            return response.content[0].text.strip()

        except Exception as e:
            self.logger.error(f"Error generating suggestions (async): {e}")
            return ""

    async def generate_conflict_resolution_async(
        self, conflict: Any, project: ProjectContext, user_auth_method: str = "api_key"
    ) -> str:
        """Generate conflict resolution suggestions asynchronously."""
        prompt = f"""Help resolve this project specification conflict:

    Project: {project.name} ({project.phase} phase)

    Conflict Details:
    - Type: {conflict.get('type', 'Unknown')}
    - Description: {conflict.get('description', 'No description')}
    - Severity: {conflict.get('severity', 'Medium')}

    Provide 3-4 specific, actionable suggestions for resolving this conflict. Consider:
    1. Technical implications of each choice
    2. Project goals and constraints
    3. Team collaboration aspects
    4. Potential compromise solutions

    Be specific and practical, not just theoretical."""

        try:
            client = self._get_async_client(user_auth_method)

            response = await client.messages.create(
                model=self.model,
                max_tokens=600,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            await self._track_token_usage_async(
                response.usage, "generate_conflict_resolution_async"
            )
            return response.content[0].text.strip()

        except Exception as e:
            self.logger.error(f"Error generating conflict resolution (async): {e}")
            return f"Error generating resolution: {e}"

    async def test_connection_async(self, user_auth_method: str = "api_key") -> bool:
        """Test Claude API connection asynchronously."""
        try:
            client = self._get_async_client(user_auth_method)

            response = await client.messages.create(
                model=self.model, max_tokens=10, messages=[{"role": "user", "content": "Hi"}]
            )
            return response.content[0].text is not None
        except Exception as e:
            self.logger.error(f"Connection test failed (async): {e}")
            return False
