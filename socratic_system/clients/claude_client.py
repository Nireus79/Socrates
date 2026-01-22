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
        self, api_key: str = None, orchestrator: "AgentOrchestrator" = None, subscription_token: str = None
    ):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (optional - can be None for API server mode using database keys)
            orchestrator: Reference to AgentOrchestrator for event emission and token tracking
            subscription_token: Optional - Claude subscription token for subscription-based auth
        """
        self.api_key = api_key
        self.subscription_token = subscription_token
        self.orchestrator = orchestrator
        self.model = orchestrator.config.claude_model if orchestrator else "claude-haiku-4-5-20251001"
        self.logger = logging.getLogger("socrates.clients.claude")

        # Initialize clients for both authentication methods
        # Lazy initialization - only create if api_key is valid
        self.client = None
        self.async_client = None
        self.subscription_client = None
        self.subscription_async_client = None

        # Initialize default clients only if we have a non-placeholder API key
        if api_key and not api_key.startswith("placeholder"):
            try:
                self.client = anthropic.Anthropic(api_key=api_key)
                self.async_client = anthropic.AsyncAnthropic(api_key=api_key)
                self.logger.info("Default API key clients initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize default API key clients: {e}")

        # Subscription token based clients (if available)
        if subscription_token:
            try:
                self.subscription_client = anthropic.Anthropic(api_key=subscription_token)
                self.subscription_async_client = anthropic.AsyncAnthropic(api_key=subscription_token)
                self.logger.info("Subscription-based clients initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize subscription clients: {e}")

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
            "No API key configured. Please set your API key in Settings > LLM > Anthropic or set ANTHROPIC_API_KEY environment variable.",
            error_type="MISSING_API_KEY",
        )

    def _decrypt_api_key_from_db(self, encrypted_key: str) -> str:
        """
        Decrypt an API key stored in the database.

        Supports multiple encryption methods for compatibility:
        1. SHA256-Fernet (current default)
        2. PBKDF2-Fernet (for legacy keys)
        3. Base64 (for simple encoding)

        Args:
            encrypted_key: The encrypted API key from database

        Returns:
            Decrypted API key string, or None if decryption fails

        Note:
            For production, set SOCRATES_ENCRYPTION_KEY environment variable
            to a secure key. Currently using: default-insecure-key-change-in-production
        """
        import base64
        import hashlib
        import os

        from cryptography.fernet import Fernet

        # Get encryption key from environment or use default
        encryption_key_base = os.getenv(
            "SOCRATES_ENCRYPTION_KEY", "default-insecure-key-change-in-production"
        )

        # Log which key is being used (without revealing the actual key)
        key_source = (
            "SOCRATES_ENCRYPTION_KEY env var (SECURE)"
            if os.getenv("SOCRATES_ENCRYPTION_KEY")
            else "default insecure key (CHANGE IN PRODUCTION)"
        )
        self.logger.info(f"Decrypting API key using: {key_source}")

        # Method 1: Try SHA256-based Fernet decryption (simple, reliable, doesn't require PBKDF2)
        try:
            key_bytes = hashlib.sha256(encryption_key_base.encode()).digest()
            derived_key = base64.urlsafe_b64encode(key_bytes)
            cipher = Fernet(derived_key)
            decrypted = cipher.decrypt(encrypted_key.encode())
            self.logger.info("API key decrypted successfully using SHA256-Fernet")
            return decrypted.decode()
        except Exception as e:
            self.logger.debug(f"SHA256-Fernet decryption failed: {e}")

        # Method 2: Try PBKDF2-based Fernet decryption (for older keys encrypted with PBKDF2)
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

            salt = b"socrates-salt"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend(),
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(encryption_key_base.encode()))
            cipher = Fernet(derived_key)
            decrypted = cipher.decrypt(encrypted_key.encode())
            self.logger.info("API key decrypted successfully using PBKDF2-Fernet")
            return decrypted.decode()
        except ImportError:
            self.logger.debug("PBKDF2 not available, skipping PBKDF2 decryption")
        except Exception as e:
            self.logger.debug(f"PBKDF2-Fernet decryption failed: {e}")

        # Method 3: Try base64 fallback (for keys saved with base64 encoding)
        try:
            self.logger.info("Attempting base64 decoding as fallback...")
            decrypted = base64.b64decode(encrypted_key.encode()).decode()
            self.logger.info("API key decoded successfully using base64 fallback")
            return decrypted
        except Exception as e:
            self.logger.debug(f"Base64 decoding failed: {e}")

        # All methods failed
        self.logger.error("All decryption methods failed for API key")
        self.logger.error(
            "If key was encrypted with custom SOCRATES_ENCRYPTION_KEY, ensure it's set."
        )
        return None

    def _get_client(self, user_auth_method: str = "api_key", user_id: str = None):
        """
        Get the appropriate sync client based on user's auth method and user-specific API key.

        Priority order:
        1. User-specific API key from database
        2. Default API key from config/environment (if valid and not placeholder)
        3. Raise error if no valid key available

        Args:
            user_auth_method: User's preferred auth method (only 'api_key' is supported)
            user_id: Optional user ID to fetch user-specific API key

        Returns:
            Anthropic sync client instance

        Raises:
            APIError: If no valid API key is available
        """
        # Subscription mode is not supported - always use api_key
        if user_auth_method == "subscription":
            self.logger.warning("Subscription mode is not supported. Defaulting to api_key")
            user_auth_method = "api_key"

        # Try to get user-specific or default API key
        try:
            api_key, is_user_specific = self._get_user_api_key(user_id)
            if api_key and not api_key.startswith("placeholder"):
                # Create a new client with the API key
                key_source = "user-specific" if is_user_specific else "default"
                self.logger.debug(f"Creating client with {key_source} API key")
                return anthropic.Anthropic(api_key=api_key)
            else:
                # No valid key found
                raise APIError(
                    "No API key configured. Please set your API key in Settings > LLM > Anthropic",
                    error_type="MISSING_API_KEY",
                )
        except APIError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting API key: {e}")
            raise APIError(
                "No API key configured. Please set your API key in Settings > LLM > Anthropic",
                error_type="MISSING_API_KEY",
            )

    def _get_async_client(self, user_auth_method: str = "api_key", user_id: str = None):
        """
        Get the appropriate async client based on user's auth method and user-specific API key.

        Priority order:
        1. User-specific API key from database
        2. Default API key from config/environment (if valid and not placeholder)
        3. Raise error if no valid key available

        Args:
            user_auth_method: User's preferred auth method (only 'api_key' is supported)
            user_id: Optional user ID to fetch user-specific API key

        Returns:
            Anthropic async client instance

        Raises:
            APIError: If no valid API key is available
        """
        # Subscription mode is not supported - always use api_key
        if user_auth_method == "subscription":
            self.logger.warning("Subscription mode is not supported. Defaulting to api_key")
            user_auth_method = "api_key"

        # Try to get user-specific or default API key
        try:
            api_key, is_user_specific = self._get_user_api_key(user_id)
            if api_key and not api_key.startswith("placeholder"):
                # Create a new async client with the API key
                key_source = "user-specific" if is_user_specific else "default"
                self.logger.debug(f"Creating async client with {key_source} API key")
                return anthropic.AsyncAnthropic(api_key=api_key)
            else:
                # No valid key found
                raise APIError(
                    "No API key configured. Please set your API key in Settings > LLM > Anthropic",
                    error_type="MISSING_API_KEY",
                )
        except APIError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting API key: {e}")
            raise APIError(
                "No API key configured. Please set your API key in Settings > LLM > Anthropic",
                error_type="MISSING_API_KEY",
            )

    def extract_insights(
        self,
        user_response: str,
        project: ProjectContext,
        user_auth_method: str = "api_key",
        user_id: str = None,
    ) -> Dict:
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

    async def extract_insights_async(
        self, user_response: str, project: ProjectContext, user_auth_method: str = "api_key"
    ) -> Dict:
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
            async_client = self._get_async_client(user_auth_method, user_id=None)
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
        self,
        conflict: ConflictInfo,
        project: ProjectContext,
        user_auth_method: str = "api_key",
        user_id: str = None,
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

    def generate_artifact(
        self,
        context: str,
        project_type: str,
        user_auth_method: str = "api_key",
        user_id: str = None,
    ) -> str:
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

    def generate_code(
        self, context: str, user_auth_method: str = "api_key", user_id: str = None
    ) -> str:
        """Generate code based on project context"""
        # Enhanced prompt engineering: extract and emphasize key project details
        prompt = f"""
You are a software architect generating code for a specific project phase.

PROJECT CONTEXT:
{context}

CODE GENERATION GUIDELINES:

1. UNDERSTAND THE PROJECT:
   - Identify the core problem to solve in this phase
   - Determine if this integrates with existing systems
   - Check for architectural constraints and dependencies
   - Note any partner systems, APIs, or data models that must be integrated with

2. ARCHITECTURE & INTEGRATION:
   - If this is part of a larger system, design it as a MODULE/COMPONENT, not standalone
   - Identify integration points with existing systems
   - Use existing data models and database schemas, don't reimplements them
   - Follow the project's established patterns and conventions
   - Design REST/gRPC endpoints where appropriate

3. IMPLEMENTATION REQUIREMENTS:
   - Include DETAILED docstrings explaining module purpose and usage
   - Implement proper error handling and logging
   - Add type hints for all function parameters and returns
   - Write defensive code that validates inputs
   - Include configuration management for settings

4. CODE STRUCTURE:
   - Organize into logical modules/classes
   - Keep functions/methods focused and single-purpose
   - Use appropriate design patterns for the problem domain
   - Make the code testable and mockable

5. DOCUMENTATION:
   - Add module-level docstring with purpose
   - Document key classes and functions with examples
   - Include setup/installation instructions if needed
   - Add comments for non-obvious logic

REQUIREMENTS:
- Generate COMPLETE, WORKING code (not just templates or placeholders)
- Make it production-ready for this phase
- Ensure it integrates properly with existing systems
- Include all necessary imports and dependencies
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

    def generate_business_plan(
        self, context: str, user_auth_method: str = "api_key", user_id: str = None
    ) -> str:
        """Generate business plan document"""
        prompt = f"""
You are a business strategist creating a comprehensive business plan for a specific venture.

PROJECT CONTEXT:
{context}

BUSINESS PLAN REQUIREMENTS:

1. UNDERSTAND THE OPPORTUNITY:
   - Identify the core business problem being solved
   - Understand the target market and customer segments
   - Evaluate competitive landscape and positioning
   - Assess market size and growth potential

2. STRUCTURE & CLARITY:
   - Create a professional, actionable document
   - Use clear sections with compelling headers
   - Include data-driven insights where applicable
   - Provide realistic financial projections
   - Make assumptions explicit and justify them

3. CONTENT SECTIONS:
   1. Executive Summary
      - One-page overview of the business opportunity
      - Key financial metrics and timeline
      - Why this business will succeed

   2. Market Analysis & Opportunity
      - Total addressable market (TAM) size
      - Market trends and growth drivers
      - Customer segments and personas
      - Competitive landscape analysis
      - Market entry barriers and opportunities

   3. Business Model & Revenue Streams
      - How the business generates revenue
      - Pricing strategy and justification
      - Unit economics
      - Revenue projections by stream

   4. Value Proposition
      - Unique advantages and differentiators
      - Customer benefits and outcomes
      - Why customers will choose this solution
      - Competitive positioning

   5. Go-to-Market Strategy
      - Launch plan and timeline
      - Customer acquisition strategy
      - Sales and marketing approach
      - Channel strategy
      - Key partnerships and relationships

   6. Operations & Execution
      - Operational workflows
      - Key processes and systems
      - Scaling strategy
      - Quality assurance and risk management

   7. Financial Projections
      - 3-5 year revenue forecasts
      - Cost structure and burn rate
      - Profitability timeline
      - Break-even analysis
      - Sensitivity analysis for key assumptions

   8. Competitive Advantage
      - Sustainable competitive moats
      - Key differentiators
      - Technology or IP advantages
      - Team and organizational advantages

   9. Risk Analysis & Mitigation
      - Key business risks
      - Market and competitive risks
      - Operational and execution risks
      - Financial and funding risks
      - Mitigation strategies for each

   10. Implementation Timeline
       - Phase-by-phase roadmap
       - Key milestones and deliverables
       - Funding milestones and requirements
       - Success metrics per phase

   11. Resource Requirements
       - Team structure and roles needed
       - Funding requirements and use of funds
       - Equipment, technology, and facilities
       - Key talent and hiring priorities

4. QUALITY STANDARDS:
   - Use professional business language
   - Include realistic, data-driven projections
   - Make financial models transparent
   - Address potential objections proactively
   - Provide supporting evidence for claims
   - Include appendices with detailed data if needed

Create a business plan that is compelling to investors, realistic in projections, and actionable for execution.
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

    def generate_research_protocol(
        self, context: str, user_auth_method: str = "api_key", user_id: str = None
    ) -> str:
        """Generate research protocol and methodology document"""
        prompt = f"""
You are a research methodologist creating a rigorous, IRB-compliant research protocol.

PROJECT CONTEXT:
{context}

RESEARCH PROTOCOL REQUIREMENTS:

1. ESTABLISH THE RESEARCH FOUNDATION:
   - Clearly articulate the research question and hypothesis
   - Justify why this research matters and is timely
   - Define key constructs and variables
   - Identify the research gap in existing literature
   - Establish theoretical framework

2. METHODOLOGY RIGOR:
   - Design an approach that properly addresses the research question
   - Justify all methodological choices
   - Ensure reproducibility and transparency
   - Address potential biases and limitations
   - Plan for peer review and validation

3. PROTOCOL SECTIONS:

   1. Research Question & Hypothesis
      - Specific, measurable research questions
      - Directional or non-directional hypotheses
      - Primary and secondary research objectives
      - Variable definitions and operationalization

   2. Literature Review & Background
      - State of current knowledge
      - Relevant prior findings
      - Theoretical frameworks
      - Identified gaps in research
      - How this study will advance knowledge

   3. Research Design & Methodology
      - Study design type (RCT, observational, qualitative, mixed-methods, etc.)
      - Participant population and sampling strategy
      - Sample size and power analysis
      - Inclusion/exclusion criteria
      - Treatment or intervention protocols
      - Control conditions (if applicable)
      - Justification for design choices

   4. Data Collection Plan
      - Data collection methods and instruments
      - Measurement tools, scales, surveys
      - Interview or focus group protocols
      - Data collection timeline and procedures
      - Quality control and standardization
      - Privacy and data security measures

   5. Data Analysis Approach
      - Statistical or qualitative analysis strategy
      - Software and analytical tools
      - Pre-planned analyses and decision trees
      - Handling missing data
      - Sensitivity analyses
      - Subgroup analyses (if applicable)

   6. Quality Assurance & Validation
      - Reliability and validity measures
      - Inter-rater reliability if applicable
      - Triangulation methods
      - Pilot testing procedures
      - Contingency protocols

   7. Ethical Considerations
      - IRB/ethics committee requirements
      - Informed consent procedures
      - Data protection and confidentiality
      - Risk assessment and mitigation
      - Participant recruitment safeguards
      - Conflict of interest declarations

   8. Study Timeline & Milestones
      - Detailed project schedule
      - Key milestones and deliverables
      - Resource allocation
      - Personnel roles and qualifications
      - Required funding and budget

   9. Expected Outcomes & Impact
      - Anticipated findings and their implications
      - Significance for the field
      - Plans for dissemination and publication
      - Potential limitations and generalizability
      - Future research directions

4. QUALITY STANDARDS:
   - Use precise scientific language
   - Provide sufficient detail for reproducibility
   - Justify all methodological decisions
   - Address potential threats to validity
   - Anticipate and plan for implementation challenges
   - Ensure compliance with ethical standards
   - Make the protocol suitable for IRB submission

Create a research protocol that is scientifically rigorous, ethically sound, and ready for peer review.
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

    def generate_creative_brief(
        self, context: str, user_auth_method: str = "api_key", user_id: str = None
    ) -> str:
        """Generate creative/design brief document"""
        prompt = f"""
You are a creative director developing a comprehensive design brief for a creative project.

PROJECT CONTEXT:
{context}

CREATIVE BRIEF REQUIREMENTS:

1. UNDERSTAND THE CREATIVE CHALLENGE:
   - Identify the creative problem to solve
   - Understand the target audience and their preferences
   - Determine the competitive landscape
   - Define what success looks like for this project
   - Note any brand constraints, guidelines, or visual systems to follow

2. CREATIVE STRATEGY & VISION:
   - Develop a clear creative vision that aligns with project goals
   - Define the unique value proposition and differentiation
   - Establish the tone, voice, and personality
   - Create a memorable concept that resonates with the target audience

3. BRIEF SECTIONS:

   1. Project Overview & Vision
      - What is the creative challenge?
      - What does success look like?
      - What is the core creative concept?

   2. Target Audience Deep-Dive
      - Demographics and psychographics
      - Values, desires, pain points
      - How they consume content and make decisions
      - What resonates with them emotionally

   3. Brand Identity & Positioning
      - Brand personality and voice
      - Core values and mission
      - Visual identity and aesthetic
      - Competitive positioning

   4. Creative Direction & Vision
      - Overall aesthetic direction
      - Visual style and mood
      - Design philosophy and approach
      - What feelings/reactions should this evoke?

   5. Visual Specifications
      - Color palette with specific hex codes/Pantone references
      - Typography guidelines (font families, sizes, weights)
      - Imagery style (photography, illustration, abstract, etc.)
      - Design elements and visual patterns
      - Layout and composition principles

   6. Brand & Design Guidelines
      - Logo usage and sizing rules
      - Visual hierarchy guidelines
      - Spacing, margins, and grid systems
      - Do's and don'ts for visual consistency
      - Accessibility and inclusivity requirements

   7. Content & Messaging Strategy
      - Key messages to communicate
      - Tone and language style
      - How to adapt messaging across channels
      - Content formats and priorities

   8. Asset Specifications & Deliverables
      - Specific assets to create (logos, patterns, templates, etc.)
      - File formats and dimensions for each
      - Quality standards and file naming conventions
      - Version control and file organization

   9. Workflow & Production Guidelines
      - Ideation and concept development process
      - Review and approval workflows
      - Revision procedures and feedback loops
      - Tools and software to use
      - Timeline for production and delivery

   10. Success Metrics & Evaluation
      - How will creative effectiveness be measured?
      - KPIs for design and branding impact
      - User testing and feedback procedures
      - Optimization and iteration plan

4. QUALITY STANDARDS:
   - Use concrete, specific language and examples
   - Include visual descriptions that are actionable
   - Provide reference images or mood boards when helpful
   - Ensure guidelines are comprehensive but not restrictive
   - Make it a brief that empowers creative teams to create excellent work

Create a professional creative brief that inspires creative work while providing clear strategic direction and practical guidelines.
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

    def generate_marketing_plan(
        self, context: str, user_auth_method: str = "api_key", user_id: str = None
    ) -> str:
        """Generate marketing campaign plan document"""
        prompt = f"""
You are a marketing strategist developing a comprehensive marketing and campaign plan.

PROJECT CONTEXT:
{context}

MARKETING PLAN REQUIREMENTS:

1. UNDERSTAND THE MARKETING CHALLENGE:
   - Identify the target market and audience segments
   - Understand customer pain points and motivations
   - Determine the competitive landscape and positioning opportunities
   - Define marketing objectives and success metrics
   - Note any market constraints, regulations, or strategic requirements

2. MARKETING STRATEGY DEVELOPMENT:
   - Develop a clear go-to-market strategy
   - Define unique value proposition and differentiation
   - Identify customer journey and touchpoints
   - Plan channel strategy and marketing mix
   - Create financial projections for marketing ROI

3. PLAN SECTIONS:

   1. Executive Summary & Campaign Overview
      - Campaign objectives and KPIs
      - Target audience definition
      - Key messages and value proposition
      - Expected outcomes and success metrics
      - Budget overview and timeline

   2. Market Analysis & Segmentation
      - Target market size and growth potential
      - Customer segments with specific characteristics
      - Customer needs, pain points, and behaviors
      - Market trends and opportunities
      - Competitive analysis and positioning

   3. Campaign Strategy & Messaging
      - Core campaign message and theme
      - Value proposition for each segment
      - Key marketing messages and talking points
      - Tone and brand voice
      - Customer journey and touchpoints

   4. Channel Strategy & Media Plan
      - Marketing channels to use (digital, traditional, social, etc.)
      - Media mix and allocation rationale
      - Channel-specific tactics and approaches
      - Integration across channels
      - Channel performance benchmarks

   5. Content Plan & Calendar
      - Content types and formats (blog, video, social, email, etc.)
      - Content themes aligned with campaign
      - Content calendar with publishing schedule
      - Asset requirements and production timelines
      - Content distribution and promotion strategy

   6. Customer Acquisition & Conversion
      - Acquisition channels and tactics
      - Lead generation strategy
      - Conversion funnel and optimization points
      - Sales enablement materials
      - Customer retention and advocacy strategies

   7. Campaign Timeline & Execution
      - Campaign phases and launch strategy
      - Key milestones and deliverables
      - Staffing and team responsibilities
      - External vendor coordination
      - Dependencies and critical path items

   8. Budget & Financial Planning
      - Total budget allocation
      - Spend by channel and tactic
      - Cost per acquisition (CPA) targets
      - Expected revenue impact and ROI
      - Budget contingency reserve
      - Payment terms and vendor agreements

   9. Performance Measurement & Analytics
      - KPIs and metrics for each channel
      - Data collection and tracking methods
      - Reporting cadence and dashboard design
      - Analysis frequency and decision-making processes
      - Attribution model for multi-touch campaigns
      - A/B testing and optimization plan

   10. Risk Management & Contingency
      - Market risks and mitigation strategies
      - Execution risks and contingency plans
      - Performance shortfall responses
      - Competitor response scenarios
      - Communication and escalation procedures

4. QUALITY STANDARDS:
   - Provide specific, actionable tactics with clear ownership
   - Include realistic budget estimates with assumptions
   - Ensure financial projections are grounded in market data
   - Make metrics trackable and reportable
   - Create a plan that can be executed within resource constraints
   - Consider market dynamics and competitive responses
   - Design for flexibility and optimization as market conditions change

Create a professional marketing plan that drives customer acquisition, builds brand awareness, and achieves measurable business results.
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

    def generate_curriculum(
        self, context: str, user_auth_method: str = "api_key", user_id: str = None
    ) -> str:
        """Generate educational curriculum document"""
        prompt = f"""
You are a curriculum designer and instructional specialist developing comprehensive educational curriculum.

PROJECT CONTEXT:
{context}

CURRICULUM DESIGN REQUIREMENTS:

1. UNDERSTAND THE EDUCATIONAL CHALLENGE:
   - Identify the learning domain and target student population
   - Understand student prior knowledge, skills, and learning styles
   - Determine learning goals and aspirations for students
   - Identify constraints (time, resources, infrastructure)
   - Note any standards or accreditation requirements
   - Understand the educational context and environment

2. CURRICULUM STRATEGY & PEDAGOGY:
   - Develop a coherent pedagogical philosophy
   - Align instruction with learning science principles
   - Plan for inclusive and differentiated instruction
   - Design for engagement and student motivation
   - Create pathways for skill development and mastery

3. CURRICULUM SECTIONS:

   1. Course Overview & Context
      - Course title, code, and level
      - Target audience and prerequisites
      - Course duration and instructional hours
      - Learning context and delivery method
      - Connection to larger program or pathway

   2. Curriculum Philosophy & Approach
      - Pedagogical philosophy and teaching approach
      - Core values and beliefs about learning
      - How students will learn best in this content area
      - Connection to real-world applications
      - Inclusivity and accessibility principles

   3. Learning Goals & Outcomes
      - Overall learning goals for the course
      - Specific, measurable learning outcomes (by level: course, unit, lesson)
      - Competencies and skills to develop
      - Alignment with standards or frameworks
      - Success criteria for student learning

   4. Content Structure & Progression
      - Major topics and units with scope
      - Logical sequence and learning progression
      - Prerequisite relationships between units
      - Spiral curriculum design (if appropriate)
      - Content boundaries and depth expectations
      - Integration across disciplines (if applicable)

   5. Unit & Module Design
      - Detailed breakdown of each major unit
      - Learning outcomes for each unit
      - Key concepts and essential questions
      - Estimated duration and pacing
      - Assessment and performance indicators
      - Connections to other units and curriculum

   6. Instructional Strategies & Activities
      - Active learning strategies and pedagogies
      - Variety of instructional approaches
      - Engagement tactics and student motivation
      - Collaborative and individual learning opportunities
      - Technology integration (if applicable)
      - Accommodations for diverse learners

   7. Assessment & Evaluation Strategy
      - Formative assessment methods (ongoing)
      - Summative assessment methods (final)
      - Performance tasks and authentic assessments
      - Rubrics and scoring criteria
      - How feedback will be provided
      - Grade determination and weighting
      - Alignment of assessments with learning outcomes

   8. Materials, Resources & Technologies
      - Required textbooks and readings
      - Digital resources and online platforms
      - Instructional materials and media
      - Laboratory or hands-on resources
      - Technology tools and software
      - Open educational resources (OER)
      - Where to obtain materials and budget

   9. Differentiation & Accessibility
      - Strategies for diverse learning needs
      - Scaffolding and support levels
      - Enrichment opportunities for advanced learners
      - English language learner (ELL) support
      - Students with disabilities accommodations
      - Culturally responsive teaching strategies

   10. Lesson Plan Framework & Pacing
      - Standard lesson structure and components
      - Pacing guide and unit timeline
      - Sample detailed lesson plan
      - Time allocation by topic
      - Flexibility and contingency planning

   11. Teacher Resources & Support
      - Teacher's guide or manual
      - Background content knowledge and resources
      - Common student misconceptions and how to address them
      - Answer keys and assessment solutions
      - Professional development resources
      - Troubleshooting guide for common challenges

   12. Evaluation & Improvement
      - How curriculum effectiveness will be measured
      - Student learning data collection methods
      - Curriculum review and revision cycle
      - Feedback mechanisms (student, parent, peer)
      - Continuous improvement process

4. QUALITY STANDARDS:
   - Ensure learning outcomes are clear, specific, and measurable
   - Align all assessments directly with learning outcomes
   - Provide sufficient detail for teachers to implement effectively
   - Include diverse instructional strategies and learning modalities
   - Design for student engagement and motivation
   - Address equity and accessibility throughout
   - Ground design in learning science and research
   - Create curriculum that is practical and implementable
   - Prepare students for success beyond the course

Create a comprehensive, well-structured curriculum that guides learning, supports student success, and can be effectively implemented by educators.
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
        self,
        project: ProjectContext,
        artifact: str,
        artifact_type: str = "code",
        user_auth_method: str = "api_key",
        user_id: str = None,
    ) -> str:
        """Generate comprehensive documentation for any artifact type"""
        doc_instructions = {
            "code": """
DOCUMENTATION STRUCTURE FOR CODE:
1. Project Overview & Purpose
   - What problem does this solve
   - Key features and capabilities
   - Architecture overview

2. Installation & Setup
   - Prerequisites and dependencies
   - Step-by-step installation
   - Configuration and environment setup

3. Usage Guide
   - Quick start guide
   - Common use cases with examples
   - API/Function reference

4. Integration Points
   - How this integrates with other systems
   - Required data models and schemas
   - External dependencies and APIs

5. Configuration & Customization
   - All available configuration options
   - Environment variables
   - Performance tuning

6. Troubleshooting & FAQ
   - Common issues and solutions
   - Debugging tips
   - Performance optimization

7. Contributing & Development
   - Development setup
   - Code style and conventions
   - Testing procedures
        """,
            "business_plan": """
DOCUMENTATION STRUCTURE FOR BUSINESS PLAN:
1. Executive Summary Expansion
   - Key assumptions and dependencies
   - Critical success factors

2. Detailed Implementation Roadmap
   - Phase-by-phase execution plan
   - Milestones and success metrics
   - Resource requirements per phase

3. Operational Procedures
   - Daily/weekly operational workflows
   - Decision-making processes
   - Communication protocols

4. Financial Management
   - Budget tracking procedures
   - Cash flow management
   - Financial reporting schedule

5. Risk Management
   - Risk register with mitigation strategies
   - Contingency budgets
   - Escalation procedures

6. Performance Monitoring
   - KPI dashboard definitions
   - Reporting cadence and structure
   - Review and adjustment processes
        """,
            "research_protocol": """
DOCUMENTATION STRUCTURE FOR RESEARCH:
1. Methodology Deep Dive
   - Detailed step-by-step procedures
   - Decision trees for complex processes
   - Statistical analysis specifications

2. Data Management Procedures
   - Data collection workflows
   - Quality assurance and validation
   - Storage, backup, and security

3. Research Personnel
   - Role descriptions and qualifications
   - Training requirements
   - Responsibility matrix

4. Compliance & Ethics
   - IRB requirements and documentation
   - Informed consent procedures
   - Data protection and privacy

5. Troubleshooting Guide
   - Common methodological challenges
   - Solutions and workarounds
   - When to escalate issues

6. Resource Library
   - Templates and forms
   - Software and tool guides
   - Reference materials and literature
        """,
            "creative_brief": """
DOCUMENTATION STRUCTURE FOR CREATIVE:
1. Creative Vision & Strategy
   - Brand voice and tone guidelines
   - Visual style specifications
   - Target audience deep-dive

2. Production Standards
   - Format specifications and sizes
   - Quality standards and review process
   - File naming and organization

3. Asset Management
   - File structure and hierarchy
   - Version control procedures
   - Archive and retention policy

4. Workflow & Processes
   - Ideation to delivery pipeline
   - Stakeholder approval process
   - Revision and feedback procedures

5. Guidelines & Examples
   - Design specifications with examples
   - Copy guidelines with samples
   - Do's and don'ts

6. Tools & Resources
   - Required software and plugins
   - Template libraries
   - Design asset repositories
        """,
            "marketing_plan": """
DOCUMENTATION STRUCTURE FOR MARKETING:
1. Campaign Strategy Detail
   - Campaign timeline with key dates
   - Success metrics and KPIs
   - Audience segmentation

2. Content Calendar
   - Publishing schedule
   - Content ownership matrix
   - Platform-specific guidelines

3. Execution Procedures
   - Content creation workflow
   - Review and approval process
   - Publishing and distribution steps

4. Performance Tracking
   - Analytics and measurement setup
   - Reporting frequency and format
   - Performance thresholds and alerts

5. Budget Management
   - Budget allocation by channel
   - Spend tracking procedures
   - ROI calculation methodology

6. Contingency & Optimization
   - Pivot strategies if targets not met
   - A/B testing procedures
   - Optimization decision-making
        """,
            "curriculum": """
DOCUMENTATION STRUCTURE FOR CURRICULUM:
1. Learning Objectives Detail
   - Learning outcomes per module
   - Assessment criteria
   - Skill progression mapping

2. Instructional Materials
   - Lesson plans with timing
   - Lecture notes and slides
   - Student handouts and worksheets

3. Assessment & Evaluation
   - Assessment rubrics
   - Grading procedures
   - Student feedback mechanisms

4. Differentiation Strategies
   - Modifications for different learning styles
   - Support for struggling students
   - Extensions for advanced learners

5. Resources & References
   - Recommended readings
   - Multimedia resources
   - Supplementary materials

6. Instructor Support
   - Common student misconceptions
   - Frequently asked questions
   - Troubleshooting difficult concepts
        """,
        }

        doc_section = doc_instructions.get(artifact_type, doc_instructions["code"])

        # Handle None or missing artifact
        artifact_preview = (
            (artifact[:2000] if artifact else "") + "..."
            if artifact
            else "(No artifact generated yet)"
        )

        # Build detailed context for documentation
        project_context = f"""
PROJECT CONTEXT:
- Name: {project.name}
- Type: {project.project_type}
- Current Phase: {project.phase}
- Goals: {project.goals if project.goals else 'Not specified'}
- Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}
- Target Deployment: {project.deployment_target if project.deployment_target else 'Not specified'}
- Code Style: {project.code_style if project.code_style else 'Not specified'}
"""

        prompt = f"""
You are creating professional, comprehensive documentation for a {artifact_type} artifact.

{project_context}

THE ARTIFACT TO DOCUMENT:
{artifact_type.replace('_', ' ').title()}:
{artifact_preview}

DOCUMENTATION REQUIREMENTS:
- Create clear, well-organized documentation
- Use professional language suitable for the audience
- Include concrete examples and code samples where applicable
- Make procedures step-by-step and easy to follow
- Anticipate user questions and common issues
- Provide enough detail for someone unfamiliar with the project to understand it
- Include references to relevant sections
- Add table of contents for longer documents

{doc_section}

Create documentation that will enable others to successfully understand, implement, and maintain this work.
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
            client = self._get_client(user_auth_method)
            client.messages.create(
                model=self.model,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": "Test"}],
            )
            self.logger.info("Claude API connection test successful")
            return True
        except APIError:
            self.logger.warning("Claude API connection test skipped - no valid API key configured")
            return False
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

    def generate_socratic_question(
        self,
        prompt: str,
        cache_key: str = None,
        user_auth_method: str = "api_key",
        user_id: str = None,
    ) -> str:
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

    def generate_suggestions(
        self, current_question: str, project: ProjectContext, user_auth_method: str = "api_key"
    ) -> str:
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
            client = self._get_client(user_auth_method, user_id=None)

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
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        user_auth_method: str = "api_key",
        user_id: str = None,
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
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        user_auth_method: str = "api_key",
        user_id: str = None,
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

    async def generate_code_async(
        self, context: str, user_auth_method: str = "api_key", user_id: str = None
    ) -> str:
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

    async def generate_socratic_question_async(
        self,
        prompt: str,
        cache_key: str = None,
        user_auth_method: str = "api_key",
        user_id: str = None,
    ) -> str:
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

    async def detect_conflicts_async(
        self, requirements: list, user_auth_method: str = "api_key"
    ) -> list:
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

    async def analyze_context_async(
        self, project: ProjectContext, user_auth_method: str = "api_key"
    ) -> str:
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

    async def generate_business_plan_async(
        self, context: str, user_auth_method: str = "api_key"
    ) -> str:
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

    async def generate_documentation_async(
        self, context: str, doc_type: str = "technical", user_auth_method: str = "api_key"
    ) -> str:
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
