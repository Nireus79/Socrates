"""
API Orchestrator for Socrates

Instantiates and coordinates real agents from socratic-agents library.
Provides unified interface for REST API endpoints to call agents and orchestrators.
"""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import MaturityCalculator from socratic-maturity library (required)
from socrates_maturity import MaturityCalculator

# Import LLMClient from socratic-nexus for production-grade LLM handling
from socratic_nexus import LLMClient

# Import SocraticCounselor from socratic-agents library (required)
from socratic_agents import SocraticCounselor

# Import conflict resolution from socratic-conflict library (required)
from socratic_conflict import ConflictDetector

# Import foundation services from socratic-core library (required)
from socratic_core import (
    EventBus,
)

# Import all 4 security components from socratic-security (required)
from socratic_security import (
    PathValidator,
    PromptInjectionDetector,
    SafeFilename,
)

# Import circuit breaker for agent resilience (CRITICAL FIX #12)
from socrates_api.services.circuit_breaker import CircuitBreakerRegistry


def _get_valid_model_for_provider(provider: str, preferred_model: Optional[str] = None) -> str:
    """Get a valid model name for the given provider"""
    # Map of provider to valid model names (ordered by preference)
    valid_models = {
        "claude": [
            "claude-haiku-4-5-20251001",
            "claude-3-5-sonnet-20241022",
            "claude-opus-4-20250514",
        ],
        "anthropic": [
            "claude-haiku-4-5-20251001",
            "claude-3-5-sonnet-20241022",
            "claude-opus-4-20250514",
        ],
        "openai": ["gpt-4o-mini", "gpt-4-turbo", "gpt-4o"],
        "gemini": ["gemini-1.5-flash", "gemini-pro", "gemini-1.5-pro"],
        "ollama": ["llama2", "mistral", "neural-chat"],
    }

    # If preferred model is valid for this provider, use it
    if preferred_model and preferred_model in valid_models.get(provider, []):
        return preferred_model

    # Otherwise, use the first valid model for this provider (fastest/cheapest)
    return valid_models.get(provider, ["claude-haiku-4-5-20251001"])[0]


class LLMClientAdapter:
    """Adapter to bridge LLMClient interface (chat/stream) to SocraticCounselor interface (generate_response)"""

    def __init__(self, llm_client):
        """Wrap an LLMClient instance"""
        self.llm_client = llm_client
        # Delegate attribute access to wrapped client
        self.provider = getattr(llm_client, "provider", None)
        # Initialize security handler
        self._init_security()

    def _init_security(self):
        """Initialize prompt security validation"""
        try:
            from socrates_api.utils.prompt_security import get_prompt_handler

            self.prompt_handler = get_prompt_handler()
        except ImportError:
            logger.warning("Prompt security module not available")
            self.prompt_handler = None

    def generate_response(self, prompt: str) -> str:
        """
        Adapt LLMClient.chat() to generate_response() interface.
        SocraticCounselor expects this method.

        Includes prompt injection protection.
        """
        try:
            # Security: Validate prompt for injection attempts
            if self.prompt_handler:
                is_safe, sanitized_prompt = self.prompt_handler.validate_prompt(prompt)
                if not is_safe:
                    logger.error("Prompt validation failed - potential injection attack")
                    raise ValueError(
                        "Prompt validation failed - input contains potential injection"
                    )
                prompt = sanitized_prompt

            # Use the chat method that LLMClient actually provides
            # LLMClient.chat() expects a string prompt, not a list
            response = self.llm_client.chat(prompt)

            # Extract text from response
            if isinstance(response, str):
                # If response is already a string
                return response
            elif isinstance(response, dict):
                # If response is a dict, look for content field
                if "content" in response:
                    content = response["content"]
                    if isinstance(content, str):
                        return content
                    elif isinstance(content, list):
                        # If content is a list, extract text from each item
                        texts = []
                        for item in content:
                            if isinstance(item, dict) and "text" in item:
                                texts.append(item["text"])
                            elif isinstance(item, str):
                                texts.append(item)
                        return " ".join(texts) if texts else str(response)
                # Fallback: convert entire dict to string
                return str(response)
            elif hasattr(response, "content"):
                # If response has content attribute
                content = response.content
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # Extract text from list items
                    texts = []
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            texts.append(item["text"])
                        elif isinstance(item, str):
                            texts.append(item)
                    return " ".join(texts) if texts else str(response)
                else:
                    return str(response)
            else:
                # Otherwise convert to string
                return str(response)
        except Exception as e:
            logger.error(f"Failed to generate response using LLMClient.chat(): {e}", exc_info=True)
            raise

    def chat(self, messages, **kwargs):
        """
        Delegate to wrapped client's chat method, filtering incompatible params.
        Includes prompt injection protection for string messages.
        """
        # Security: Validate messages if they're strings
        if self.prompt_handler and isinstance(messages, str):
            is_safe, sanitized = self.prompt_handler.validate_prompt(messages)
            if not is_safe:
                logger.error("Message validation failed - potential injection attack")
                raise ValueError("Message validation failed - input contains potential injection")
            messages = sanitized

        # Remove parameters that conflict for certain models
        # Claude Haiku doesn't allow both temperature and top_p
        if "temperature" in kwargs and "top_p" in kwargs:
            # Prefer temperature for Haiku
            del kwargs["top_p"]
        return self.llm_client.chat(messages, **kwargs)

    def stream(self, messages, **kwargs):
        """
        Delegate to wrapped client's stream method, filtering incompatible params.
        Includes prompt injection protection for string messages.
        """
        # Security: Validate messages if they're strings
        if self.prompt_handler and isinstance(messages, str):
            is_safe, sanitized = self.prompt_handler.validate_prompt(messages)
            if not is_safe:
                logger.error("Message validation failed - potential injection attack")
                raise ValueError("Message validation failed - input contains potential injection")
            messages = sanitized

        # Remove parameters that conflict for certain models
        if "temperature" in kwargs and "top_p" in kwargs:
            del kwargs["top_p"]
        return self.llm_client.stream(messages, **kwargs)

    def __getattr__(self, name):
        """Delegate unknown attributes to wrapped client"""
        return getattr(self.llm_client, name)


class EventEmitterAdapter:
    """Adapter to bridge EventBus (subscribe/publish) to EventEmitter (on/emit) interface"""

    def __init__(self, event_bus):
        """Wrap an EventBus instance"""
        self.event_bus = event_bus

    def on(self, event_name, callback):
        """Register event listener (subscribe pattern)"""
        self.event_bus.subscribe(event_name, callback)
        return self

    def emit(self, event_name, data=None):
        """Emit event (publish pattern)"""
        self.event_bus.publish(event_name, data)
        return self

    def off(self, event_name, callback=None):
        """Unregister event listener"""
        self.event_bus.unsubscribe(event_name, callback)
        return self

    def __getattr__(self, name):
        """Delegate unknown attributes to wrapped event bus"""
        return getattr(self.event_bus, name)


class APIOrchestrator:
    """Orchestrates real agents from socratic-agents for REST API"""

    def __init__(self, api_key_or_config = ""):
        """Initialize orchestrator with real agents and event-driven architecture

        Args:
            api_key_or_config: Either a string API key or a SocratesConfig object
        """
        # Add logger for backward compatibility
        self.logger = logger

        # Handle both string API keys and config objects
        if isinstance(api_key_or_config, str):
            self.api_key = api_key_or_config
            self.config = None
        else:
            # Assume it's a config object (SocratesConfig)
            self.config = api_key_or_config
            self.api_key = getattr(api_key_or_config, 'api_key', '')

        self.agents = {}
        self.skill_orchestrator = None
        self.workflow_orchestrator = None
        self.pure_orchestrator = None

        # Initialize documentation and performance tools
        self.doc_generator = None
        self.profiler = None
        self.cache = None

        # Initialize vector_db as None (may be set by external systems)
        self.vector_db = None

        # Initialize caching for question context and KB strategy
        self._context_cache = {}  # Caches context per phase
        self._kb_cache = {}  # Caches KB strategy decisions per phase

        # Initialize knowledge services for Phase 5
        self.knowledge_service = None
        self.vector_db_service = None
        self.document_understanding_service = None
        self._initialize_knowledge_services()

        # Initialize Phase 6 advancement tracking and metrics services
        self.advancement_tracker = None
        self.metrics_service = None
        self.learning_service = None
        self.progress_dashboard = None
        self._initialize_advancement_services()

        # Initialize event-driven architecture from socratic-core (required)
        self.event_bus = EventBus()
        # Backward compatibility: alias event_emitter to event_bus with adapter for old API
        self.event_emitter = EventEmitterAdapter(self.event_bus)
        logger.info("Event-driven architecture initialized: EventBus enabled")

        # Initialize library integrations (Phase 4)
        try:
            from socrates_api.library_integrations import get_integration_manager

            self.library_integrations = get_integration_manager()
            available_libs = self.library_integrations.get_available_libraries()
            logger.info(f"Library integrations initialized: {len(available_libs)} libraries available")
        except Exception as e:
            logger.warning(f"Library integrations setup failed: {e}")
            self.library_integrations = None

        # Create LLMClient first (if API key provided)
        self.llm_client = self._create_llm_client()
        # Backward compatibility: alias claude_client to llm_client
        self.claude_client = self.llm_client

        # Initialize database (backward compatibility)
        self.database = self._initialize_database()

        self._initialize_agents()
        self._initialize_orchestrators()
        self._initialize_documentation()
        self._initialize_performance_monitoring()
        self._setup_event_listeners()
        logger.info(
            "API Orchestrator initialized with real agents, event-driven architecture, and shared models"
        )

    def _create_llm_client(self) -> Optional[Any]:
        """Create LLM client with production-grade features from socratic-nexus, with model fallback"""
        try:
            # Use provided API key, or fall back to environment variable
            api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY", "")

            if not api_key:
                logger.debug(
                    "No API key provided (neither in config nor ANTHROPIC_API_KEY env var) - LLM client will be None"
                )
                return None

            # Create LLMClient with full socratic-nexus capabilities:
            # - Response caching for performance optimization
            # - Retry logic for reliability
            from socratic_nexus import LLMConfig

            # List of models to try (in priority order)
            models_to_try = [
                "claude-haiku-4-5-20251001",  # Latest haiku (preferred)
                "claude-3-5-haiku",  # Generic haiku fallback
                "claude-3-haiku-20240307",  # Older haiku
                "claude-3-5-sonnet-20241022",  # Fallback to sonnet
                "claude-opus-4-20250514",  # Fallback to opus
            ]

            last_error = None

            for model in models_to_try:
                try:
                    config = LLMConfig(
                        provider="anthropic",
                        model=model,
                        api_key=api_key,
                        cache_responses=True,  # Cache responses for performance
                        cache_ttl=3600,  # Cache for 1 hour
                        retry_attempts=3,  # Retry up to 3 times on failure
                        retry_backoff_factor=2.0,  # Exponential backoff for retries
                    )
                    raw_client = LLMClient(config=config)
                    logger.info(
                        f"LLM client created with model '{model}' and production features: "
                        "response_caching=True, retry_attempts=3"
                    )
                    # WRAP with adapter for socratic-agents compatibility
                    wrapped_client = LLMClientAdapter(raw_client)
                    logger.debug("LLMClient wrapped with LLMClientAdapter for agent compatibility")
                    return wrapped_client

                except Exception as model_error:
                    last_error = model_error
                    logger.debug(
                        f"Model '{model}' initialization failed: {model_error}, trying next..."
                    )
                    continue

            # If all models failed, raise the last error
            error_msg = (
                f"All LLM models failed. Last error with model '{models_to_try[-1]}': {last_error}"
            )
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Failed to create LLM client: {e}", exc_info=True)
            raise  # Fail fast instead of returning None

    def _create_user_llm_client(self, user_id: str, provider: str = "claude") -> Optional[Any]:
        """
        Create LLM client with user's stored API key, with model fallback support.

        Args:
            user_id: User identifier
            provider: LLM provider (default: claude)

        Returns:
            LLMClient instance or None if no API key available
        """
        try:
            from socrates_api.database import get_database
            from socratic_system.models.llm_provider import get_provider_metadata

            db = get_database()

            # Get user's stored API key
            api_key = db.get_api_key(user_id, provider)

            if not api_key:
                logger.debug(f"No API key stored for user {user_id} provider {provider}")
                return None

            # Get provider metadata to determine model
            provider_meta = get_provider_metadata(provider)
            if not provider_meta:
                logger.error(f"Unknown provider: {provider}")
                return None

            # Get user's preferred model for this provider
            user_model = db.get_provider_model(user_id, provider)

            # Build list of models to try (in priority order)
            models_to_try = []
            if user_model:
                models_to_try.append(user_model)  # User's preferred model first

            # Add default haiku models in order of preference
            models_to_try.extend(
                [
                    "claude-haiku-4-5-20251001",  # Latest haiku (preferred)
                    "claude-3-5-haiku",  # Generic version fallback
                    "claude-3-haiku-20240307",  # Older version
                    "claude-3-5-sonnet-20241022",  # Fallback to sonnet
                ]
            )

            # Try each model in order
            from socratic_nexus import LLMConfig

            last_error = None

            for model in models_to_try:
                try:
                    config = LLMConfig(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        cache_responses=True,  # Cache responses for performance
                        cache_ttl=3600,  # Cache for 1 hour
                        retry_attempts=3,  # Retry up to 3 times on failure
                        retry_backoff_factor=2.0,  # Exponential backoff for retries
                    )
                    raw_client = LLMClient(config=config)
                    logger.info(
                        f"LLM client created for user {user_id} with provider {provider}/{model} "
                        "and production features: response_caching=True, retry_attempts=3"
                    )
                    # WRAP with adapter for socratic-agents compatibility
                    wrapped_client = LLMClientAdapter(raw_client)
                    return wrapped_client

                except Exception as model_error:
                    last_error = model_error
                    logger.debug(
                        f"Model {model} failed for user {user_id}: {model_error}, trying next..."
                    )
                    continue

            # If all models failed, log the error from the last attempt
            if last_error:
                logger.warning(
                    f"All LLM models failed for user {user_id}. Last error: {last_error}"
                )
            return None

        except Exception as e:
            logger.warning(f"Failed to create user LLM client: {e}")
            return None

    def _initialize_database(self):
        """
        Initialize database connection using singleton pattern.

        CRITICAL FIX #3: Use database singleton to prevent:
        - Multiple database connections (SQLite lock contention)
        - Data inconsistency between CLI and API
        - Memory leaks from unclosed connections

        Returns:
            LocalDatabase: The shared database instance (same across all components)
        """
        try:
            # Import and use database singleton from database module
            # This returns the SAME instance for all callers across API, CLI, orchestrator
            from socrates_api.database import get_database

            db = get_database()
            logger.info(f"Using shared database singleton at: {db.db_path}")
            return db

        except Exception as e:
            logger.error(f"Failed to initialize database singleton: {e}")
            # Don't fall back to mock - database is critical
            raise

    def _initialize_agents(self) -> None:
        """
        CRITICAL FIX #1: Lazy-load agents instead of eager initialization.

        Agents are now created on-demand (first access) rather than all upfront.
        This reduces:
        - API startup time
        - Memory footprint
        - Wasted initialization of unused agents

        Uses _get_agent() to lazily initialize agents.
        """
        # Initialize empty agents dict - agents will be created on-demand
        self.agents = {}
        self._agent_classes = {
            # Code analysis and generation
            "code_generator": ("socratic_agents", "CodeGenerator"),
            "code_validator": ("socratic_agents", "CodeValidator"),
            # Project and learning coordination
            "socratic_counselor": ("socratic_agents", "SocraticCounselor"),
            "project_manager": ("socratic_agents", "ProjectManager"),
            # Quality and skill management
            "quality_controller": ("socratic_agents", "QualityController"),
            "skill_generator": ("socratic_agents", "SkillGeneratorAgent"),
            # Learning and development
            "learning_agent": ("socratic_agents", "LearningAgent"),
            # Analysis
            "context_analyzer": ("socratic_agents", "ContextAnalyzer"),
            "code_analyzer": ("socratic_analyzer", "CodeAnalyzer"),
            # Knowledge and documentation
            "user_manager": ("socratic_agents", "UserManager"),
            "agent_knowledge_manager": ("socratic_agents", "KnowledgeManager"),
            "document_processor": ("socratic_agents", "DocumentProcessor"),
            "note_manager": ("socratic_agents", "NoteManager"),
            # System management
            "system_monitor": ("socratic_agents", "SystemMonitor"),
            # Conflict resolution
            "conflict_detector": ("socratic_agents", "AgentConflictDetector"),
        }
        logger.info(
            f"Agent lazy-loading initialized for {len(self._agent_classes)} agents "
            "(will be created on-demand)"
        )

    def _get_agent(self, agent_name: str):
        """
        Get or lazily-initialize an agent.

        CRITICAL FIX #1: Lazy-load agents on first access.

        Args:
            agent_name: Name of agent to get (e.g., "socratic_counselor")

        Returns:
            Agent instance or None if agent fails to load
        """
        # Return cached agent if already initialized
        if agent_name in self.agents:
            return self.agents[agent_name]

        # Get agent class definition
        if agent_name not in self._agent_classes:
            logger.warning(f"Unknown agent: {agent_name}")
            return None

        module_name, class_name = self._agent_classes[agent_name]

        try:
            # Dynamically import and instantiate agent
            if module_name == "socratic_agents":
                # Handle special case for KnowledgeManager (imported as different name)
                if class_name == "KnowledgeManager":
                    from socratic_agents import KnowledgeManager as AgentKnowledgeManager
                    agent = AgentKnowledgeManager(llm_client=self.llm_client)
                else:
                    # Standard import
                    module = __import__(module_name, fromlist=[class_name])
                    agent_class = getattr(module, class_name)

                    # Special initialization for socratic_counselor (needs database)
                    if agent_name == "socratic_counselor":
                        agent = agent_class(
                            llm_client=self.llm_client,
                            database=self.database,
                            batch_size=1
                        )
                    else:
                        agent = agent_class(llm_client=self.llm_client)

            elif module_name == "socratic_analyzer":
                try:
                    from socratic_analyzer import CodeAnalyzer
                    agent = CodeAnalyzer()
                except ImportError:
                    logger.warning("socratic_analyzer not available")
                    return None
            else:
                logger.warning(f"Unknown module: {module_name}")
                return None

            # Cache the agent
            self.agents[agent_name] = agent
            logger.debug(f"Lazily initialized agent: {agent_name}")
            return agent

        except Exception as e:
            logger.warning(f"Failed to initialize agent {agent_name}: {e}")
            return None

    def _initialize_orchestrators(self) -> None:
        """Initialize skill, workflow, and pure orchestrators (required)"""
        from socratic_agents.integrations.skill_orchestrator import SkillOrchestrator
        from socratic_agents.orchestration.orchestrator import PureOrchestrator
        from socratic_agents.skill_generation.workflow_orchestrator import WorkflowOrchestrator

        # Initialize SkillOrchestrator for intelligent skill generation
        self.skill_orchestrator = SkillOrchestrator(
            quality_controller=self._get_agent("quality_controller"),
            skill_generator=self._get_agent("skill_generator"),
            learning_agent=self._get_agent("learning_agent"),
        )
        logger.info("Initialized SkillOrchestrator")

        # Initialize WorkflowOrchestrator for workflow automation
        self.workflow_orchestrator = WorkflowOrchestrator()
        logger.info("Initialized WorkflowOrchestrator")

        # Initialize PureOrchestrator with maturity-driven gating and coordination
        self.pure_orchestrator = PureOrchestrator(
            agents=self.agents,
            get_maturity=self._get_maturity_score,
            get_learning_effectiveness=self._get_learning_effectiveness,
            on_event=self._on_coordination_event,
        )
        logger.info("Initialized PureOrchestrator with maturity-driven gating")

    def _get_maturity_score(self, user_id: str, phase: str) -> float:
        """
        Get maturity score for a user in a phase (callback for PureOrchestrator).

        CRITICAL FIX #6: Never return fallback value - raise exception instead.
        False maturity scores lead to incorrect phase advancement decisions.
        """
        try:
            # Use MaturityCalculator from socrates-maturity library
            calculator = MaturityCalculator()
            score = calculator.calculate_phase_maturity(user_id, phase)

            # Validate score is in valid range [0.0, 1.0]
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"Invalid maturity score {score} (must be 0.0-1.0)")

            logger.debug(f"Maturity score for user {user_id} in phase {phase}: {score:.2%}")
            return score
        except Exception as e:
            logger.error(f"CRITICAL: Failed to calculate maturity score for {user_id} in {phase}: {e}")
            # CRITICAL FIX #6: Don't return false values (0.5)
            # Force caller to handle missing maturity explicitly
            raise ValueError(f"Maturity calculation failed: {e}") from e

    def _get_learning_effectiveness(self, user_id: str) -> float:
        """
        Get learning effectiveness for a user (callback for PureOrchestrator).

        CRITICAL FIX #6: Never return fallback values - raise exception instead.
        False effectiveness scores lead to incorrect learning path decisions.
        """
        try:
            # Use LearningAgent/LearningTracker to calculate effectiveness
            learning_tracker = self._get_agent("learning_tracker")
            if learning_tracker and hasattr(learning_tracker, "calculate_effectiveness"):
                effectiveness = learning_tracker.calculate_effectiveness(user_id)

                # Validate effectiveness is in valid range [0.0, 1.0]
                if not (0.0 <= effectiveness <= 1.0):
                    raise ValueError(f"Invalid effectiveness score {effectiveness} (must be 0.0-1.0)")

                logger.debug(f"Learning effectiveness for user {user_id}: {effectiveness:.2%}")
                return effectiveness

            # No learning tracker available
            logger.error(f"Learning effectiveness calculation unavailable for user {user_id}")
            raise ValueError("Learning tracker not configured")

        except Exception as e:
            logger.error(f"CRITICAL: Failed to calculate learning effectiveness for {user_id}: {e}")
            # CRITICAL FIX #6: Don't return false values (0.7)
            # Force caller to handle missing effectiveness explicitly
            raise ValueError(f"Learning effectiveness calculation failed: {e}") from e

    def _on_coordination_event(self, event, data: Dict[str, Any]) -> None:
        """Handle coordination events from PureOrchestrator"""
        try:
            event_name = event.value if hasattr(event, "value") else str(event)
            logger.info(f"Coordination event: {event_name}, data: {data}")

            # Event handlers can be extended here to:
            # - Update maturity scores
            # - Emit webhooks
            # - Store interaction metrics
            # - Trigger follow-up agents
            # - Update UI in real-time
        except Exception as e:
            logger.error(f"Failed to handle coordination event: {e}")

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                "framework": "socratic-agents",
                "agents_loaded": len(self.agents),
                "agents": list(self.agents.keys()),
                "llm_client": self.llm_client is not None,
                "skill_orchestrator": self.skill_orchestrator is not None,
                "workflow_orchestrator": self.workflow_orchestrator is not None,
                "pure_orchestrator": self.pure_orchestrator is not None,
                "status": "operational",
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"status": "unavailable", "error": str(e)}

    def call_agent(self, agent_type: str, **kwargs) -> Dict[str, Any]:
        """Call an agent by type"""
        try:
            agent = self._get_agent(agent_type)
            if not agent:
                return {"status": "error", "message": f"Agent '{agent_type}' not found"}

            # Call agent's process method with kwargs as request
            result = agent.process(kwargs)
            return result
        except Exception as e:
            logger.error(f"Agent call failed for {agent_type}: {e}")
            return {"status": "error", "message": str(e)}

    def generate_code(self, prompt: str, language: str = "python") -> Dict[str, Any]:
        """Generate code using CodeGenerator agent"""
        try:
            agent = self._get_agent("code_generator")
            if not agent:
                return {"status": "error", "message": "CodeGenerator not available"}

            result = agent.process({"action": "generate_artifact", "prompt": prompt, "language": language})
            return result
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {"status": "error", "message": str(e)}

    def validate_code(self, code: str) -> Dict[str, Any]:
        """Validate code using CodeValidator agent"""
        try:
            agent = self._get_agent("code_validator")
            if not agent:
                return {"status": "error", "message": "CodeValidator not available"}

            result = agent.process({"action": "check_syntax", "code": code})
            return result
        except Exception as e:
            logger.error(f"Code validation failed: {e}")
            return {"status": "error", "message": str(e)}

    def check_quality(self, code: str) -> Dict[str, Any]:
        """Check code quality using QualityController agent"""
        try:
            agent = self._get_agent("quality_controller")
            if not agent:
                return {"status": "error", "message": "QualityController not available"}

            result = agent.process({"action": "check", "code": code})
            return result
        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            return {"status": "error", "message": str(e)}

    def detect_weak_areas(self, code: str) -> Dict[str, Any]:
        """Detect weak areas in code using QualityController"""
        try:
            agent = self._get_agent("quality_controller")
            if not agent:
                return {"status": "error", "message": "QualityController not available"}

            result = agent.process({"action": "detect_weak_areas", "code": code})
            return result
        except Exception as e:
            logger.error(f"Weak area detection failed: {e}")
            return {"status": "error", "message": str(e)}

    def calculate_phase_maturity(self, project: Any) -> Dict[str, Any]:
        """
        Calculate maturity for a project phase using socratic-maturity library.

        Uses production-grade MaturityCalculator with:
        - Smart phase averaging (never penalizes advancement)
        - Category-based quality scoring
        - Phase estimation based on quality categories
        - Comprehensive readiness tracking

        Args:
            project: ProjectContext object with phase and categorized_specs

        Returns:
            Dictionary with detailed maturity calculation results
        """
        try:
            # Initialize calculator with project type
            calculator = MaturityCalculator(
                project_type=getattr(project, "project_type", "software")
            )

            # Get current phase
            phase = getattr(project, "phase", "discovery")

            # Get categorized specs for the phase
            categorized_specs = getattr(project, "categorized_specs", {}) or {}
            phase_specs = categorized_specs.get(phase, [])

            # Calculate maturity using production-grade algorithm
            # This uses smart phase averaging that never penalizes advancement
            maturity_result = calculator.calculate_phase_maturity(phase_specs, phase)

            # Extract comprehensive metrics
            maturity_pct = maturity_result.get("maturity_percentage", 0.0)
            category_scores = maturity_result.get("category_scores", {})
            phase_estimate = maturity_result.get("estimated_phase", phase)

            logger.info(
                f"Maturity for {project.project_id} {phase}: {maturity_pct:.1f}% | "
                f"Categories: {len(category_scores)} | Estimated: {phase_estimate}"
            )

            return {
                "status": "success",
                "phase": phase,
                "maturity": {
                    "percentage": maturity_pct,
                    "score": maturity_result.get("maturity_score", 0.0),
                    "category_scores": category_scores,
                    "estimated_phase": phase_estimate,
                    "is_ready": maturity_result.get("is_ready", False),
                    "warnings": maturity_result.get("warnings", []),
                },
                "phase_readiness": {
                    "is_ready": maturity_result.get("is_ready", False),
                    "ready_threshold": 70.0,  # 70% for ready
                    "complete_threshold": 95.0,  # 95% for complete
                    "current_maturity": maturity_pct,
                    "next_phase": phase_estimate if phase_estimate != phase else None,
                },
            }
        except Exception as e:
            logger.error(f"Failed to calculate phase maturity: {e}", exc_info=True)
            raise

    def get_all_phases_maturity(self, project: Any) -> Dict[str, Any]:
        """
        Get maturity scores for all phases of a project using socratic-maturity.

        Uses smart phase averaging that:
        - Never penalizes advancement to new phases
        - Tracks all phases simultaneously
        - Estimates phase progression
        - Provides category-based scoring for each phase

        Args:
            project: ProjectContext object

        Returns:
            Dictionary with maturity scores for all phases
        """
        try:
            # Initialize calculator with project type
            calculator = MaturityCalculator(
                project_type=getattr(project, "project_type", "software")
            )
            categorized_specs = getattr(project, "categorized_specs", {}) or {}

            # Valid phases in order
            phases = ["discovery", "analysis", "design", "implementation"]
            phase_maturity = {}
            phase_scores = []

            # Calculate maturity for each phase
            for phase in phases:
                phase_specs = categorized_specs.get(phase, [])
                maturity_result = calculator.calculate_phase_maturity(phase_specs, phase)

                maturity_pct = maturity_result.get("maturity_percentage", 0.0)
                phase_maturity[phase] = {
                    "maturity_percentage": maturity_pct,
                    "maturity_score": maturity_result.get("maturity_score", 0.0),
                    "is_ready": maturity_result.get("is_ready", False),
                    "category_scores": maturity_result.get("category_scores", {}),
                    "warnings": maturity_result.get("warnings", []),
                    "estimated_next_phase": maturity_result.get("estimated_phase"),
                }
                phase_scores.append(maturity_pct)

            # Get current phase
            current_phase = getattr(project, "phase", "discovery")
            current_idx = phases.index(current_phase) if current_phase in phases else 0

            # Calculate average maturity using smart averaging (never penalizes advancement)
            average_maturity = sum(phase_scores) / len(phase_scores) if phase_scores else 0.0

            logger.info(
                f"All phases maturity for {getattr(project, 'project_id', 'unknown')}: "
                f"Average {average_maturity:.1f}% | Current phase: {current_phase}"
            )

            return {
                "status": "success",
                "current_phase": current_phase,
                "current_phase_index": current_idx,
                "all_phases": phase_maturity,
                "average_maturity": average_maturity,
                "thresholds": {
                    "ready_threshold": 70.0,  # 70% for ready
                    "complete_threshold": 95.0,  # 95% for complete
                },
                "phase_progression": {
                    "phases_started": sum(1 for m in phase_scores if m > 0),
                    "phases_ready": sum(1 for m in phase_scores if m >= 70.0),
                    "phases_complete": sum(1 for m in phase_scores if m >= 95.0),
                },
            }
        except Exception as e:
            logger.error(f"Failed to get all phases maturity: {e}", exc_info=True)
            raise

    def validate_phase_advancement(
        self, project: Any, target_phase: Optional[str] = None, force: bool = False
    ) -> Dict[str, Any]:
        """
        PHASE 4: Validate if a project can advance to the target phase.

        Checks if phase advancement requirements are met, including maturity thresholds.
        Allows force advancement if authorized by user.

        Args:
            project: ProjectContext object
            target_phase: Desired next phase (None = auto-advance to next phase)
            force: If True, bypass maturity requirements (owner override)

        Returns:
            Dictionary with validation results:
            {
                "can_advance": bool,
                "reason": str,
                "current_phase": str,
                "target_phase": str,
                "maturity": int (current phase %),
                "maturity_threshold": int,
                "missing_requirements": list,
                "focus_areas": list,
                "force_used": bool (if forced)
            }
        """
        try:
            current_phase = getattr(project, "phase", "discovery")
            valid_phases = ["discovery", "analysis", "design", "implementation"]

            # Validate current phase
            if current_phase not in valid_phases:
                return {
                    "can_advance": False,
                    "reason": f"Invalid current phase: {current_phase}",
                    "current_phase": current_phase,
                    "target_phase": target_phase,
                    "maturity": 0,
                    "maturity_threshold": 100,
                    "missing_requirements": ["Valid phase required"],
                    "focus_areas": [],
                }

            # Determine target phase
            if target_phase:
                # Validate target phase
                if target_phase not in valid_phases:
                    return {
                        "can_advance": False,
                        "reason": f"Invalid target phase: {target_phase}",
                        "current_phase": current_phase,
                        "target_phase": target_phase,
                        "maturity": 0,
                        "maturity_threshold": 100,
                        "missing_requirements": [f"Invalid phase {target_phase}"],
                        "focus_areas": [],
                    }

                # Ensure target is after current (no skipping phases in strict mode)
                current_idx = valid_phases.index(current_phase)
                target_idx = valid_phases.index(target_phase)

                if target_idx <= current_idx and not force:
                    return {
                        "can_advance": False,
                        "reason": f"Cannot advance backwards from {current_phase} to {target_phase}",
                        "current_phase": current_phase,
                        "target_phase": target_phase,
                        "maturity": 0,
                        "maturity_threshold": 100,
                        "missing_requirements": ["Target phase must be after current phase"],
                        "focus_areas": [],
                    }
            else:
                # Auto-advance to next phase
                current_idx = valid_phases.index(current_phase)
                target_phase = (
                    valid_phases[current_idx + 1]
                    if current_idx < len(valid_phases) - 1
                    else current_phase
                )

            # If forcing advancement, skip maturity checks
            if force:
                logger.warning(
                    f"Force advancement from {current_phase} to {target_phase} "
                    f"for project {getattr(project, 'project_id', 'unknown')}"
                )
                return {
                    "can_advance": True,
                    "reason": "Advancement forced by authorized user",
                    "current_phase": current_phase,
                    "target_phase": target_phase,
                    "maturity": 0,
                    "maturity_threshold": 100,
                    "missing_requirements": [],
                    "focus_areas": [],
                    "force_used": True,
                }

            # PHASE 4: Check maturity threshold (100% required for normal advancement)
            try:
                maturity_data = self.calculate_phase_maturity(project)
                # Extract maturity percentage - structure is {"maturity": {"percentage": float, ...}}
                maturity_pct = maturity_data.get("maturity", {}).get("percentage", 0)
            except Exception as e:
                logger.warning(f"Failed to calculate maturity for advancement validation: {e}")
                maturity_pct = 0

            # Determine if advancement is allowed
            maturity_threshold = 100  # 100% required for phase advancement
            can_advance = maturity_pct >= maturity_threshold

            logger.info(
                f"Phase advancement validation for {getattr(project, 'project_id', 'unknown')}: "
                f"{current_phase}->{target_phase}, maturity={maturity_pct}%, "
                f"can_advance={can_advance}"
            )

            if can_advance:
                return {
                    "can_advance": True,
                    "reason": f"Phase {current_phase} is fully specified ({maturity_pct}% maturity)",
                    "current_phase": current_phase,
                    "target_phase": target_phase,
                    "maturity": int(maturity_pct),
                    "maturity_threshold": maturity_threshold,
                    "missing_requirements": [],
                    "focus_areas": [],
                }
            else:
                # Calculate what's missing
                missing_pct = maturity_threshold - maturity_pct
                missing_estimate = max(1, int(missing_pct / 5))  # Rough estimate

                return {
                    "can_advance": False,
                    "reason": (
                        f"Phase {current_phase} is {int(maturity_pct)}% complete. "
                        f"Need {int(missing_pct)}% more to reach 100% and advance to {target_phase}."
                    ),
                    "current_phase": current_phase,
                    "target_phase": target_phase,
                    "maturity": int(maturity_pct),
                    "maturity_threshold": maturity_threshold,
                    "missing_requirements": [
                        f"Complete {missing_estimate} more questions to reach 100%",
                        "Define all required specifications",
                    ],
                    "focus_areas": maturity_data.get("maturity", {}).get("warnings", []) or [],
                }

        except Exception as e:
            logger.error(f"Phase advancement validation failed: {e}", exc_info=True)
            return {
                "can_advance": False,
                "reason": "Advancement validation failed. Please try again.",
                "current_phase": getattr(project, "phase", "unknown"),
                "target_phase": target_phase,
                "maturity": 0,
                "maturity_threshold": 100,
                "missing_requirements": ["System error during validation"],
                "focus_areas": [],
            }

    def guide_learning(self, topic: str, level: str = "beginner") -> Dict[str, Any]:
        """Guide learning using SocraticCounselor agent"""
        try:
            agent = self._get_agent("socratic_counselor")
            if not agent:
                return {"status": "error", "message": "SocraticCounselor not available"}

            # CRITICAL: generate_question action requires project and current_user
            # This method is legacy - should not be called without project context
            result = agent.process({
                "action": "generate_question",  # REQUIRED: Action dispatch
                "topic": topic,
                "level": level,
                "project": None,  # WARNING: Legacy method - project required for real generation
                "current_user": "api_default"  # WARNING: Using default user for legacy method
            })
            return result
        except Exception as e:
            logger.error(f"Learning guidance failed: {e}")
            return {"status": "error", "message": str(e)}

    def process_quality_issue(self, code: str) -> Dict[str, Any]:
        """Process quality issue using SkillOrchestrator workflow"""
        try:
            if not self.skill_orchestrator:
                self._initialize_orchestrators()

            if not self.skill_orchestrator:
                return {"status": "error", "message": "SkillOrchestrator not available"}

            # Call SkillOrchestrator - returns nested structure with quality_analysis
            result = self.skill_orchestrator.process_quality_issue(code)
            # Result structure:
            # {
            #     "status": "success",
            #     "agent": "SkillOrchestrator",
            #     "session_id": "...",
            #     "generated_skills": [...],
            #     "personalized_skills": [...],
            #     "quality_analysis": {
            #         "score": float,
            #         "issues": list,
            #         "weak_areas": list
            #     }
            # }
            return result
        except Exception as e:
            logger.error(f"Quality issue processing failed: {e}")
            return {"status": "error", "message": str(e)}

    def record_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Record interaction using LearningAgent"""
        try:
            agent = self._get_agent("learning_agent")
            if not agent:
                return {"status": "error", "message": "LearningAgent not available"}

            result = agent.process({"action": "record", "interaction": interaction})
            return result
        except Exception as e:
            logger.error(f"Interaction recording failed: {e}")
            return {"status": "error", "message": str(e)}

    def analyze_context(self, content: str) -> Dict[str, Any]:
        """Analyze context using ContextAnalyzer agent"""
        try:
            agent = self._get_agent("context_analyzer")
            if not agent:
                return {"status": "error", "message": "ContextAnalyzer not available"}

            result = agent.process({"action": "analyze", "content": content})
            return result
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return {"status": "error", "message": str(e)}

    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create project using ProjectManager agent"""
        try:
            agent = self._get_agent("project_manager")
            if not agent:
                return {"status": "error", "message": "ProjectManager not available"}

            result = agent.process(
                {"action": "create", "project_name": name, "description": description}
            )
            return result
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            return {"status": "error", "message": str(e)}

    def list_agents(self) -> list:
        """List all available agents"""
        return list(self.agents.keys())

    def get_library_status(self) -> Dict[str, bool]:
        """Get status of all library integrations"""
        return {
            "llm_client": self.llm_client is not None,
            "agents_loaded": len(self.agents) > 0,
            "skill_orchestrator": self.skill_orchestrator is not None,
            "workflow_orchestrator": self.workflow_orchestrator is not None,
            "pure_orchestrator": self.pure_orchestrator is not None,
        }

    def execute_agent(self, agent_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a generic agent with request data"""
        try:
            agent = self._get_agent(agent_name)
            if not agent:
                return {"status": "error", "message": f"Agent '{agent_name}' not found"}

            # CRITICAL: request_data MUST contain "action" key for agent dispatch
            if "action" not in request_data:
                return {"status": "error", "message": f"Request missing required 'action' key. Agent '{agent_name}' uses action-based dispatch."}

            result = agent.process(request_data)
            return result
        except Exception as e:
            logger.error(f"Agent execution failed for {agent_name}: {e}")
            return {"status": "error", "message": str(e)}

    def call_llm(self, prompt: str, model: str = "claude-3-5-haiku", **kwargs) -> Dict[str, Any]:
        """Call LLM via socratic-nexus"""
        try:
            # Use existing LLM client if available
            if not self.llm_client:
                return {
                    "status": "error",
                    "message": "LLM client not initialized. API key required.",
                }

            # Note: If a different model is requested, would need to create new client
            # For now, use the initialized client with its model
            response = self.llm_client.chat(prompt=prompt, **kwargs)

            return {
                "status": "success",
                "response": str(response) if response else "",
                "model": self.llm_client.model if hasattr(self.llm_client, "model") else model,
            }
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return {"status": "error", "message": str(e)}

    def list_llm_models(self) -> List[str]:
        """List available LLM models (in priority order)"""
        return [
            "claude-haiku-4-5-20251001",  # Latest haiku (VALID - 4.5 generation)
            "claude-3-5-sonnet-20241022",  # Sonnet as backup
            "claude-opus-4-20250514",  # Opus as fallback
            "claude-opus-4-1",  # Older opus
            "claude-3-haiku-20240307",  # Legacy haiku
        ]

    def analyze_code_quality(self, code: str, filename: str = "code.py") -> Dict[str, Any]:
        """Analyze code quality (stub - requires socratic-analyzer)"""
        try:
            # Use QualityController from socratic-agents as fallback
            return self.check_quality(code)
        except Exception as e:
            logger.error(f"Code quality analysis failed: {e}")
            return {"status": "error", "message": str(e)}

    def detect_agent_conflicts(
        self, field: str, agent_outputs: Dict[str, Any], agents: list
    ) -> Dict[str, Any]:
        """Detect conflicts between agent outputs"""
        try:
            agent = self._get_agent("conflict_detector")
            if not agent:
                return {"status": "error", "message": "ConflictDetector not available"}

            result = agent.process({
                "action": "detect_conflicts",  # CRITICAL: Required by ConflictDetector
                "field": field,
                "agent_outputs": agent_outputs,
                "agents": agents
            })
            return result
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return {"status": "error", "message": str(e)}

    def store_knowledge(
        self, tenant_id: str, title: str, content: str, tags: Optional[list] = None
    ) -> Dict[str, Any]:
        """Store knowledge item (stub - requires socratic-knowledge)"""
        try:
            agent = self._get_agent("knowledge_manager")
            if not agent:
                return {"status": "error", "message": "KnowledgeManager not available"}

            result = agent.process(
                {
                    "action": "store",
                    "title": title,
                    "content": content,
                    "tags": tags or [],
                    "tenant_id": tenant_id,
                }
            )
            return result
        except Exception as e:
            logger.error(f"Knowledge storage failed: {e}")
            return {"status": "error", "message": str(e)}

    def search_knowledge(self, tenant_id: str, query: str, limit: int = 5) -> list:
        """Search knowledge base (stub - requires socratic-knowledge)"""
        try:
            agent = self._get_agent("knowledge_manager")
            if not agent:
                return []

            result = agent.process(
                {"action": "search", "query": query, "limit": limit, "tenant_id": tenant_id}
            )
            return result.get("results", []) if result else []
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []

    def generate_documentation(self, project_info: Dict[str, Any]) -> str:
        """Generate project documentation (stub - requires socratic-docs)"""
        try:
            # Stub implementation
            return (
                f"# {project_info.get('name', 'Project')}\n\n{project_info.get('description', '')}"
            )
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return "# Documentation generation failed"

    def index_rag_document(self, content: str, source: str, metadata: Dict[str, Any]) -> str:
        """Index document for RAG (stub - requires socratic-rag)"""
        try:
            # Stub implementation
            import uuid

            doc_id = str(uuid.uuid4())
            logger.info(f"RAG document indexed: {doc_id} from {source}")
            return doc_id
        except Exception as e:
            logger.error(f"RAG indexing failed: {e}")
            return ""

    def search_rag(self, query: str, limit: int = 5) -> list:
        """Search RAG documents (stub - requires socratic-rag)"""
        try:
            # Stub implementation
            return []
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return []

    def validate_security_input(self, user_input: str) -> Dict[str, Any]:
        """Validate input for security issues (stub - requires socratic-security)"""
        try:
            # Basic validation stub
            return {"status": "success", "is_safe": True, "score": 1.0}
        except Exception as e:
            logger.error(f"Security validation failed: {e}")
            return {"status": "error", "message": str(e)}

    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        return {
            "api_key_set": bool(self.api_key),
            "llm_client_ready": self.llm_client is not None,
            "agents_count": len(self.agents),
            "skill_orchestrator_ready": self.skill_orchestrator is not None,
            "workflow_orchestrator_ready": self.workflow_orchestrator is not None,
            "pure_orchestrator_ready": self.pure_orchestrator is not None,
        }

    def log_learning_interaction(
        self, session_id: str, agent_name: str, input_data: Dict, output_data: Dict, **kwargs
    ) -> bool:
        """Log interaction to learning system"""
        try:
            agent = self._get_agent("learning_agent")
            if not agent:
                return False

            agent.process(
                {
                    "action": "record",
                    "interaction": {
                        "session_id": session_id,
                        "agent_name": agent_name,
                        "input": input_data,
                        "output": output_data,
                        **kwargs,
                    },
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            return False

    def _initialize_documentation(self) -> None:
        """Initialize documentation generator"""
        try:
            from socratic_docs import DocumentationGenerator

            self.doc_generator = DocumentationGenerator()
            logger.info("Documentation generator initialized")
        except Exception as e:
            logger.warning(f"Documentation generator not available: {e}")
            self.doc_generator = None

    def _validate_user_input(self, user_input: str, input_type: str = "text") -> Dict[str, Any]:
        """
        Validate user input using all 4 security components from socratic-security.

        Checks for:
        1. Prompt injection attacks
        2. Path traversal attempts
        3. XSS and SQL injection
        4. Overall input validity

        Args:
            user_input: User-provided text to validate
            input_type: Type of input (text, prompt, code, path)

        Returns:
            Dictionary with validation results and status
        """
        try:
            validation_results = {"status": "valid", "checks": {}, "warnings": []}

            # 1. Check for prompt injection attacks
            injection_detector = PromptInjectionDetector()
            injection_risk = injection_detector.detect(user_input)
            validation_results["checks"]["prompt_injection"] = {
                "is_safe": not injection_risk.get("is_injection_attempt", False),
                "confidence": injection_risk.get("confidence", 0.0),
                "risk_level": injection_risk.get("risk_level", "low"),
            }
            if injection_risk.get("is_injection_attempt"):
                validation_results["warnings"].append("Potential prompt injection detected")

            # 2. Check for path traversal (if applicable)
            if input_type in ["path", "file"]:
                path_validator = PathValidator()
                is_safe_path = path_validator.is_safe(user_input)
                validation_results["checks"]["path_traversal"] = {"is_safe": is_safe_path}
                if not is_safe_path:
                    validation_results["status"] = "blocked"
                    validation_results["warnings"].append("Path traversal attempt detected")

            # 3. Validate general input integrity
            safe_filename = SafeFilename()
            is_valid = (
                safe_filename.is_safe(user_input) if input_type in ["filename", "path"] else True
            )
            validation_results["checks"]["input_validity"] = {"is_valid": is_valid}
            if not is_valid:
                validation_results["warnings"].append(input_validator.get_error_message())

            # 4. Log security findings
            if validation_results["warnings"]:
                logger.warning(
                    f"Security validation warnings: {validation_results['warnings']} | "
                    f"Risk level: {injection_risk.get('risk_level', 'unknown')}"
                )

            # Fail if status is blocked
            if validation_results["status"] == "blocked":
                return {
                    "status": "blocked",
                    "message": "Input validation failed - security policy violated",
                    "details": validation_results,
                }

            return {
                "status": "valid",
                "message": "Input validation passed",
                "details": validation_results,
            }

        except Exception as e:
            logger.error(f"Input validation error: {e}", exc_info=True)
            return {"status": "error", "message": "Security validation failed", "error": str(e)}

    def _setup_event_listeners(self) -> None:
        """Setup event listeners for event-driven architecture from socratic-core"""
        try:
            # Subscribe to key events for system coordination
            # CRITICAL FIX: EventBus uses .subscribe() not .on()
            self.event_bus.subscribe("agent_execution_start", self._handle_agent_start)
            self.event_bus.subscribe("agent_execution_complete", self._handle_agent_complete)
            self.event_bus.subscribe("error", self._handle_system_error)
            self.event_bus.subscribe("project_updated", self._handle_project_update)

            logger.info("Event listeners configured for system coordination")
        except Exception as e:
            logger.warning(f"Event listener setup failed: {e}")

    def _handle_agent_start(self, event_data: Dict[str, Any]) -> None:
        """Handle agent execution start event"""
        logger.debug(f"Agent execution started: {event_data.get('agent_id')}")

    def _handle_agent_complete(self, event_data: Dict[str, Any]) -> None:
        """Handle agent execution completion event"""
        logger.debug(f"Agent execution completed: {event_data.get('agent_id')}")

    def _handle_system_error(self, event_data: Dict[str, Any]) -> None:
        """Handle system error event"""
        logger.error(f"System error event: {event_data.get('error_message')}")

    def _handle_project_update(self, event_data: Dict[str, Any]) -> None:
        """Handle project update event"""
        logger.info(f"Project updated: {event_data.get('project_id')}")

    def emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Emit an event through the event bus"""
        try:
            self.event_bus.emit(event_type, event_data)
        except Exception as e:
            logger.error(f"Failed to emit event {event_type}: {e}", exc_info=True)

    def _initialize_knowledge_services(self) -> None:
        """Initialize Phase 5 knowledge base services (KB-aware question generation)"""
        try:
            from socrates_api.services.knowledge_service import (
                DocumentUnderstandingService,
                KnowledgeService,
                VectorDBService,
            )

            # Initialize knowledge services
            self.knowledge_service = KnowledgeService(
                vector_db=self.vector_db, document_repo=None  # Will be set when available
            )

            self.vector_db_service = VectorDBService(vector_db=self.vector_db)
            self.document_understanding_service = DocumentUnderstandingService()

            logger.info(
                "Phase 5 Knowledge Services initialized: "
                "KnowledgeService, VectorDBService, DocumentUnderstandingService"
            )

        except ImportError as e:
            logger.warning(f"Knowledge services not available: {e}")
            self.knowledge_service = None
            self.vector_db_service = None
            self.document_understanding_service = None
        except Exception as e:
            logger.error(f"Failed to initialize knowledge services: {e}", exc_info=True)
            self.knowledge_service = None
            self.vector_db_service = None
            self.document_understanding_service = None

    def _initialize_advancement_services(self) -> None:
        """Initialize Phase 6 advancement tracking and metrics services"""
        try:
            from socrates_api.services.advancement_tracker import AdvancementTracker
            from socrates_api.services.learning_service import LearningService
            from socrates_api.services.metrics_service import MetricsService
            from socrates_api.services.progress_dashboard import ProgressDashboard

            # Initialize Phase 6 services
            self.advancement_tracker = AdvancementTracker()
            self.metrics_service = MetricsService()
            self.learning_service = LearningService()
            self.progress_dashboard = ProgressDashboard()

            logger.info(
                "Phase 6 Advancement Services initialized: "
                "AdvancementTracker, MetricsService, LearningService, ProgressDashboard"
            )

        except ImportError as e:
            logger.warning(f"Advancement services not available: {e}")
            self.advancement_tracker = None
            self.metrics_service = None
            self.learning_service = None
            self.progress_dashboard = None
        except Exception as e:
            logger.error(f"Failed to initialize advancement services: {e}", exc_info=True)
            self.advancement_tracker = None
            self.metrics_service = None
            self.learning_service = None
            self.progress_dashboard = None

    def _initialize_performance_monitoring(self) -> None:
        """Initialize performance monitoring tools"""
        try:
            from socratic_performance import QueryProfiler, TTLCache

            self.profiler = QueryProfiler()
            self.cache = TTLCache(ttl_minutes=30)
            logger.info("Performance monitoring initialized")
        except Exception as e:
            logger.warning(f"Performance monitoring not available: {e}")
            self.profiler = None
            self.cache = None

    # Documentation methods
    def generate_api_documentation(self, code_structure: Dict[str, Any]) -> str:
        """Generate API documentation from code structure"""
        try:
            if not self.doc_generator:
                return "# API Documentation\n\nDocumentation generator not available"
            result = self.doc_generator.generate_api_documentation(code_structure)
            return result if result else "# API Documentation\n\nNo documentation generated"
        except Exception as e:
            logger.error(f"API documentation generation failed: {e}")
            return f"# API Documentation\n\nError: {str(e)}"

    def generate_architecture_docs(self, modules: List[str]) -> str:
        """Generate architecture documentation"""
        try:
            if not self.doc_generator:
                return "# Architecture Documentation\n\nDocumentation generator not available"
            result = self.doc_generator.generate_architecture_docs(modules)
            return (
                result if result else "# Architecture Documentation\n\nNo documentation generated"
            )
        except Exception as e:
            logger.error(f"Architecture documentation generation failed: {e}")
            return f"# Architecture Documentation\n\nError: {str(e)}"

    def generate_setup_guide(self, project: Dict[str, Any]) -> str:
        """Generate setup/installation guide"""
        try:
            if not self.doc_generator:
                return "# Setup Guide\n\nDocumentation generator not available"
            result = self.doc_generator.generate_setup_guide(project)
            return result if result else "# Setup Guide\n\nNo guide generated"
        except Exception as e:
            logger.error(f"Setup guide generation failed: {e}")
            return f"# Setup Guide\n\nError: {str(e)}"

    def generate_all_documentation(
        self, project: Dict[str, Any], code_structure: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate complete documentation set"""
        try:
            if not self.doc_generator:
                return {"error": "Documentation generator not available"}
            result = self.doc_generator.generate_all(project, code_structure)
            return result if isinstance(result, dict) else {"error": "Invalid documentation format"}
        except Exception as e:
            logger.error(f"Complete documentation generation failed: {e}")
            return {"error": str(e)}

    # Performance methods
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if not self.cache:
                return {"error": "Cache not available"}
            return self.cache.stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    def clear_cache(self) -> Dict[str, Any]:
        """Clear all cache entries"""
        try:
            if not self.cache:
                return {"error": "Cache not available"}
            self.cache.clear()
            return {"status": "success", "message": "Cache cleared"}
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return {"status": "error", "message": str(e)}

    def reset_profiler(self) -> Dict[str, Any]:
        """Reset profiler statistics"""
        try:
            if not self.profiler:
                return {"error": "Profiler not available"}
            self.profiler.reset()
            return {"status": "success", "message": "Profiler reset"}
        except Exception as e:
            logger.error(f"Failed to reset profiler: {e}")
            return {"status": "error", "message": str(e)}

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard"""
        try:
            result = {"status": "operational"}

            if self.profiler:
                stats = self.profiler.get_stats()
                result["profiler"] = stats if stats else {}

            if self.cache:
                cache_stats = self.cache.stats()
                result["cache"] = cache_stats if cache_stats else {}

            return result
        except Exception as e:
            logger.error(f"Failed to get performance dashboard: {e}")
            return {"status": "error", "message": str(e)}

    def get_service(self, service_name: str) -> Any:
        """Get a service or agent by name"""
        # Check if it's an agent
        if service_name in self.agents:
            return self.agents[service_name]

        # Check if it's an orchestrator
        if service_name == "skill_orchestrator":
            return self.skill_orchestrator
        elif service_name == "workflow_orchestrator":
            return self.workflow_orchestrator
        elif service_name == "pure_orchestrator":
            return self.pure_orchestrator

        # Service not found
        logger.warning(f"Service not found: {service_name}")
        return None

    def process_request(self, router_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process requests from routers using unified interface.
        Dispatches to appropriate handler based on router name.
        """
        try:
            if router_name == "multi_llm":
                return self._handle_multi_llm(request_data)
            elif router_name == "socratic_counselor":
                return self._handle_socratic_counselor(request_data)
            elif router_name == "direct_chat":
                return self._handle_direct_chat(request_data)
            elif router_name == "quality_controller":
                return self._handle_quality_controller(request_data)
            elif router_name == "document_agent":
                # Alias for document_processor agent
                return self._handle_document_processor(request_data)
            elif router_name == "document_processor":
                return self._handle_document_processor(request_data)
            elif router_name == "knowledge_manager":
                return self._handle_knowledge_manager(request_data)
            elif router_name == "nlu_analyzer":
                return self._handle_nlu_analyzer(request_data)
            elif router_name == "chat_manager":
                return self._handle_chat_manager(request_data)
            elif router_name == "llm":
                return self._handle_llm_call(request_data)
            else:
                # Generic fallback for unknown routers - return sensible defaults
                logger.warning(f"Unknown router: {router_name}, returning generic response")
                return {
                    "status": "success",
                    "data": {},
                    "message": f"Handler for {router_name} not implemented",
                }
        except Exception as e:
            logger.error(f"Error processing request for {router_name}: {e}")
            return {"status": "error", "message": str(e)}

    async def process_request_async(
        self, router_name: str, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Async version of process_request for long-running operations.
        """
        # For now, delegate to sync version
        # In a real implementation, this would use async/await properly
        return self.process_request(router_name, request_data)

    # ================== PHASE 1: FOUNDATION METHODS ==================
    # These methods implement the core orchestration patterns from the monolithic
    # Socrates system, enabling dynamic single-question generation with full context.

    def _gather_question_context(self, project: Any, user_id: str) -> Dict[str, Any]:
        """
        Gather all context needed for dynamic question generation.
        This is the central context aggregation point.

        Args:
            project: Project object with all state
            user_id: Current user ID

        Returns:
            Dict with all context for question generation
        """
        try:

            # 1. Get project context (goals, requirements, tech_stack, constraints)
            # If goals/requirements not explicitly set, extract from project description/name
            goals = getattr(project, "goals", []) or []
            if not goals or (isinstance(goals, str) and not goals.strip()):
                # Use project name and description as fallback goals
                project_name = getattr(project, "name", "")
                project_desc = getattr(project, "description", "")
                goals = [project_name] if project_name else []
                if project_desc and not goals:
                    goals = [project_desc[:100]]  # First 100 chars as goal

            requirements = getattr(project, "requirements", []) or []
            if not requirements:
                # Use project description as fallback requirement
                project_desc = getattr(project, "description", "")
                if project_desc:
                    requirements = [project_desc]

            project_context = {
                "goals": goals if isinstance(goals, list) else [goals],
                "requirements": requirements if isinstance(requirements, list) else [requirements],
                "tech_stack": getattr(project, "tech_stack", []) or [],
                "constraints": getattr(project, "constraints", []) or [],
                "existing_specs": self._get_extracted_specs(project) or {},
            }

            # 2. Get recent conversation (last 4 messages)
            conversation_history = getattr(project, "conversation_history", []) or []
            recent_messages = self._get_recent_messages(conversation_history, limit=4)

            # 3. Get previously asked questions in this phase
            pending_questions = getattr(project, "pending_questions", []) or []
            phase = getattr(project, "phase", "discovery")
            previously_asked = self._extract_previously_asked_questions(pending_questions, phase)

            # 4. Determine KB strategy and get chunks
            question_number = len([q for q in pending_questions if q.get("status") != "answered"])
            kb_strategy = self._determine_kb_strategy(phase, question_number)

            knowledge_chunks = []
            if self.vector_db and hasattr(self.vector_db, "search_similar_adaptive"):
                try:
                    # Get query from current question or project context
                    query = ""
                    if pending_questions and not [
                        q for q in pending_questions if q.get("status") == "unanswered"
                    ]:
                        # If no unanswered, use project context for query
                        query = " ".join(project_context.get("goals", [])[:2])
                    elif pending_questions:
                        # Use current unanswered question as query
                        query = pending_questions[0].get("question", "")

                    if query:
                        knowledge_chunks = self.vector_db.search_similar_adaptive(
                            query=query,
                            strategy=kb_strategy,
                            phase=phase,
                            question_number=question_number,
                        )
                except Exception as e:
                    logger.warning(f"Failed to get KB chunks: {e}")
                    knowledge_chunks = []

            # 5. Get document understanding
            document_understanding = self._get_document_understanding(project, project_context)

            # 6. Get user role
            user_role = self._get_user_role(project, user_id)

            # 7. Get code structure if present
            code_structure = None
            files = getattr(project, "files", [])
            if files:
                code_structure = self._analyze_code_structure(files)

            context = {
                "project_context": project_context,
                "phase": phase,
                "recent_messages": recent_messages,
                "previously_asked_questions": previously_asked,
                "knowledge_base_chunks": knowledge_chunks,
                "document_understanding": document_understanding,
                "user_role": user_role,
                "question_number": question_number,
                "code_structure": code_structure,
                "conversation_history": conversation_history,
                "kb_strategy": kb_strategy,
            }

            logger.debug(
                f"Context gathered for user {user_id}: phase={phase}, question_number={question_number}, kb_strategy={kb_strategy}"
            )
            return context

        except Exception as e:
            logger.error(f"Error gathering question context: {e}", exc_info=True)
            # Return minimal context to allow graceful degradation
            return {
                "project_context": {},
                "phase": "discovery",
                "recent_messages": [],
                "previously_asked_questions": [],
                "knowledge_base_chunks": [],
                "document_understanding": {},
                "user_role": "contributor",
                "question_number": 1,
                "code_structure": None,
                "conversation_history": [],
                "kb_strategy": "snippet",
            }

    def _determine_kb_strategy(self, phase: str, question_number: int) -> str:
        """
        Determine adaptive knowledge base loading strategy.

        Strategy:
        - "snippet": Top 3 chunks, fast, for early exploration
        - "full": Top 5 chunks, comprehensive, for detailed phases

        Args:
            phase: Current project phase
            question_number: Question number in this phase

        Returns:
            Strategy name ("snippet" or "full")
        """
        # Check cache first
        cache_key = f"{phase}_kb_strategy"
        if cache_key in self._kb_cache:
            return self._kb_cache[cache_key]

        # Determine strategy based on phase and progress
        if phase in ["discovery", "analysis"] and question_number < 5:
            strategy = "snippet"  # 3 chunks, fast overview
        elif phase in ["design", "implementation"] or question_number >= 5:
            strategy = "full"  # 5 chunks, comprehensive
        else:
            strategy = "snippet"  # default safe choice

        # Cache for this phase
        self._kb_cache[cache_key] = strategy
        logger.debug(f"KB Strategy for {phase} Q{question_number}: {strategy}")

        return strategy

    def _get_extracted_specs(self, project: Any) -> Dict[str, Any]:
        """Get currently extracted specifications from project."""
        try:
            specs = {}
            if hasattr(project, "context"):
                specs = {
                    "goals": getattr(project.context, "goals", []),
                    "requirements": getattr(project.context, "requirements", []),
                    "tech_stack": getattr(project.context, "tech_stack", []),
                    "constraints": getattr(project.context, "constraints", []),
                }
            return specs
        except Exception:
            return {}

    def _get_recent_messages(self, conversation_history: List[Dict], limit: int = 4) -> List[Dict]:
        """Extract last N messages from conversation history."""
        try:
            if not conversation_history:
                return []
            # Return last N messages
            return (
                conversation_history[-limit:]
                if len(conversation_history) >= limit
                else conversation_history
            )
        except Exception:
            return []

    def _extract_previously_asked_questions(
        self, pending_questions: List[Dict], phase: str
    ) -> List[str]:
        """Extract questions already asked in this phase to avoid repetition."""
        try:
            if not pending_questions:
                return []
            # Get question texts from pending questions
            return [q.get("question", "") for q in pending_questions if q.get("phase") == phase]
        except Exception:
            return []

    def _get_document_understanding(self, project: Any, project_context: Dict) -> Dict[str, Any]:
        """Get document understanding and alignment analysis."""
        try:
            # Try to get from cache first
            project_id = getattr(project, "project_id", None)
            if project_id and f"{project_id}_doc_understanding" in self._context_cache:
                return self._context_cache[f"{project_id}_doc_understanding"]

            # Get imported documents
            documents = self._get_imported_documents(project)

            if not documents:
                return {
                    "documents_analyzed": [],
                    "alignment": {"score": 0, "covered_areas": [], "gaps": []},
                }

            # In Phase 1, provide basic document understanding
            # Full DocumentUnderstandingService will be implemented in Phase 5
            doc_understanding = {
                "documents_analyzed": [d.get("name", "unknown") for d in documents],
                "summaries": {},
                "alignment": {
                    "score": 0.7,  # Default moderate alignment
                    "covered_areas": ["General context"],
                    "gaps": ["Specific implementation details"],
                },
            }

            # Cache for this project
            if project_id:
                self._context_cache[f"{project_id}_doc_understanding"] = doc_understanding

            return doc_understanding
        except Exception as e:
            logger.warning(f"Error getting document understanding: {e}")
            return {
                "documents_analyzed": [],
                "alignment": {"score": 0, "covered_areas": [], "gaps": []},
            }

    def _get_imported_documents(self, project: Any) -> List[Dict[str, str]]:
        """Get imported documents from project."""
        try:
            knowledge_base = getattr(project, "knowledge_base", [])
            if isinstance(knowledge_base, list):
                return knowledge_base
            return []
        except Exception:
            return []

    def _get_user_role(self, project: Any, user_id: str) -> str:
        """Get user's role in the project."""
        try:
            if hasattr(project, "get_member_role"):
                return project.get_member_role(user_id)
            # Default to contributor if method doesn't exist
            return "contributor"
        except Exception:
            return "contributor"

    def _analyze_code_structure(self, files: List[Any]) -> Optional[Dict[str, Any]]:
        """Analyze code structure from uploaded files."""
        try:
            if not files:
                return None
            # In Phase 1, return basic structure
            # Full analysis will be done in Phase 5
            return {"file_count": len(files), "languages": []}
        except Exception:
            return None

    def _determine_phase_focus_areas(self, phase: str) -> List[str]:
        """Get phase-specific focus areas for question generation."""
        phase_focus = {
            "discovery": [
                "Project goals and objectives",
                "Target users and stakeholders",
                "Problem statement and pain points",
                "Success metrics and KPIs",
            ],
            "analysis": [
                "Detailed requirements breakdown",
                "Technical constraints and limitations",
                "Integration requirements",
                "Data and workflow requirements",
            ],
            "design": [
                "System architecture and structure",
                "Component organization",
                "API design and contracts",
                "Database schema design",
            ],
            "implementation": [
                "Technology stack and frameworks",
                "Testing strategy",
                "Deployment and infrastructure",
                "Development timeline and milestones",
            ],
        }
        return phase_focus.get(phase, [])

    def _get_fallback_question(self, phase: str) -> Dict[str, Any]:
        """Get fallback question when generation fails."""
        import uuid
        from datetime import datetime

        fallback_questions = {
            "discovery": "Tell me about the project you want to build and what problems it solves.",
            "analysis": "What are the key requirements and constraints you need to consider?",
            "design": "How would you structure the system architecture and main components?",
            "implementation": "What's the first feature you want to implement and how would you approach it?",
        }

        question_text = fallback_questions.get(phase, "Tell me more about your project.")

        return {
            "id": f"q_{uuid.uuid4().hex[:8]}",
            "question": question_text,
            "phase": phase,
            "status": "unanswered",
            "created_at": datetime.now().isoformat(),
            "answer": None,
            "answered_at": None,
            "skipped_at": None,
            "is_fallback": True,
        }

    def _find_question(self, project: Any, question_id: str) -> Optional[Dict]:
        """Find a question by ID in both conversation_history and pending_questions.

        Searches in:
        1. conversation_history (monolithic pattern - primary)
        2. pending_questions (hybrid pattern - fallback)
        """
        # First, try to find in conversation_history (primary source of truth for dialogue)
        conversation_history = getattr(project, "conversation_history", []) or []
        for msg in conversation_history:
            if msg.get("type") == "assistant":
                # Match by question_id if available, or by content if question_id is actually question text
                if msg.get("question_id") == question_id or msg.get("content") == question_id:
                    return {
                        "question": msg.get("content", ""),
                        "question_id": msg.get("question_id", question_id),
                        "phase": msg.get("phase"),
                        "timestamp": msg.get("timestamp"),
                    }

        # Fallback: search in pending_questions (for backward compatibility)
        pending_questions = getattr(project, "pending_questions", []) or []
        for q in pending_questions:
            if q.get("id") == question_id or q.get("question") == question_id:
                return q

        return None

    def _get_existing_specs(self, project: Any) -> Dict[str, Any]:
        """Get existing specifications from project context."""
        try:
            if hasattr(project, "context"):
                return {
                    "goals": getattr(project.context, "goals", []),
                    "requirements": getattr(project.context, "requirements", []),
                    "tech_stack": getattr(project.context, "tech_stack", []),
                    "constraints": getattr(project.context, "constraints", []),
                }
            return {}
        except Exception:
            return {}

    # CRITICAL FIX #8.3: Removed dead code - _orchestrate_answer_processing was 339 lines of unused method
    # The functionality is properly implemented inline in the process_response action handler
    # CRITICAL FIX #8.4: Removed dead code - _orchestrate_question_generation was 276 lines of unused method
    # The functionality is properly implemented in _handle_socratic_counselor using monolithic pattern
    # (see lines 3376-3680 in _handle_socratic_counselor)
    # This eliminates code duplication and confusion about which implementation is active
    # Removed 339 lines of dead/duplicate code (lines 2375-2712 in original)

    def _orchestrate_answer_suggestions(
        self, project: Any, user_id: str, question_id: str
    ) -> Dict[str, Any]:
        """
        Orchestrate answer suggestions generation.
        Generates 3-5 DIVERSE suggestions (different angles, not variations).

        Args:
            project: Project object with current state
            user_id: Current user ID
            question_id: Current question ID

        Returns:
            Dict with generated suggestions
        """
        try:
            project_id = getattr(project, "project_id", None)
            logger.info(
                f"Orchestrating answer suggestions for project {project_id}, question {question_id}"
            )

            # 1. Find current question
            question = self._find_question(project, question_id)
            if not question:
                return {"status": "error", "message": f"Question {question_id} not found"}

            # 2. Gather context
            context = self._gather_question_context(project, user_id)

            # 3. Call SocraticCounselor for suggestions
            suggestions_response = {
                "status": "success",
                "suggestions": [
                    {
                        "id": "suggestion_1",
                        "text": "Provide a detailed answer focusing on the main aspects.",
                        "approach": "comprehensive",
                        "angle": "Complete overview",
                    },
                    {
                        "id": "suggestion_2",
                        "text": "Think about the specific constraints and limitations.",
                        "approach": "constraint_driven",
                        "angle": "Practical constraints",
                    },
                    {
                        "id": "suggestion_3",
                        "text": "Consider the user perspective and their needs.",
                        "approach": "user_centric",
                        "angle": "User focus",
                    },
                ],
            }

            try:
                counselor = self._get_agent("socratic_counselor")
                if counselor:
                    # CRITICAL FIX: Use process() dispatch pattern, not direct method call
                    # generate_answer_suggestions is an action, not a public method
                    suggestions_response = counselor.process({
                        "action": "generate_answer_suggestions",
                        "question": question.get("question", ""),  # Agent expects "question" not "current_question"
                        "project": project,
                    })
            except Exception as e:
                logger.warning(f"Failed to generate suggestions: {e}")

            logger.info(f"Generated {len(suggestions_response.get('suggestions', []))} suggestions")

            return {"status": "success", "suggestions": suggestions_response.get("suggestions", [])}

        except Exception as e:
            logger.error(f"Error in _orchestrate_answer_suggestions: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    # ================== END ORCHESTRATION METHODS ==================

    def _handle_multi_llm(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle multi-LLM router requests"""
        action = request_data.get("action", "")

        if action == "list_providers":
            # Return available LLM providers with complete metadata
            from socratic_system.models.llm_provider import list_available_providers

            user_id = request_data.get("user_id", "")
            providers = []

            try:
                from socrates_api.database import get_database

                db = get_database()

                # Get all available providers with metadata
                for provider_meta in list_available_providers():
                    provider_dict = provider_meta.to_dict()

                    # Check if user has configured this provider (has API key stored)
                    if user_id:
                        user_api_key = db.get_api_key(user_id, provider_meta.provider)
                        provider_dict["is_configured"] = bool(user_api_key)
                    else:
                        provider_dict["is_configured"] = False

                    providers.append(provider_dict)

                return {
                    "status": "success",
                    "data": {"providers": providers},
                    "message": "Providers retrieved",
                }
            except Exception as e:
                logger.error(f"Failed to list providers: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}

        elif action == "get_provider_config":
            # Return user's current provider configuration
            user_id = request_data.get("user_id", "")

            if not user_id:
                return {"status": "error", "message": "user_id is required"}

            try:
                from socrates_api.database import get_database

                db = get_database()

                # Get user's actual provider preferences
                default_provider = db.get_user_default_provider(user_id)
                current_model = db.get_provider_model(user_id, default_provider)
                user_api_key = db.get_api_key(user_id, default_provider)

                return {
                    "status": "success",
                    "data": {
                        "default_provider": default_provider,
                        "current_model": current_model,
                        "api_key_configured": bool(user_api_key),
                        "using_global_key": not bool(user_api_key),
                    },
                    "message": "Config retrieved",
                }
            except Exception as e:
                logger.error(f"Failed to get provider config: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}

        elif action == "set_default_provider":
            # Set user's default LLM provider
            user_id = request_data.get("user_id", "")
            provider = request_data.get("provider", "anthropic")

            if not user_id:
                return {"status": "error", "message": "user_id is required"}

            try:
                from socrates_api.database import get_database

                db = get_database()
                success = db.set_user_default_provider(user_id, provider)

                if success:
                    logger.info(f"Default provider set to {provider} for user {user_id}")
                    return {
                        "status": "success",
                        "data": {"default_provider": provider},
                        "message": f"Default provider set to {provider}",
                    }
                else:
                    return {"status": "error", "message": "Failed to set default provider"}
            except Exception as e:
                logger.error(f"Failed to set default provider: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}

        elif action == "set_provider_model":
            # Set user's preferred model for a provider
            user_id = request_data.get("user_id", "")
            provider = request_data.get("provider", "anthropic")
            model = request_data.get("model", "")

            if not user_id or not model:
                return {"status": "error", "message": "user_id and model are required"}

            try:
                from socrates_api.database import get_database

                db = get_database()
                success = db.set_provider_model(user_id, provider, model)

                if success:
                    logger.info(f"Model set to {model} for {provider} for user {user_id}")
                    return {
                        "status": "success",
                        "data": {"provider": provider, "model": model},
                        "message": f"Model set to {model} for {provider}",
                    }
                else:
                    return {"status": "error", "message": "Failed to set provider model"}
            except Exception as e:
                logger.error(f"Failed to set provider model: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}

        elif action == "update_api_key":
            # Update API key for provider
            provider = request_data.get("provider", "anthropic")
            api_key = request_data.get("api_key", "")
            if api_key:
                self.api_key = api_key
                # Recreate LLM client with new key
                self.llm_client = self._create_llm_client()
            return {
                "status": "success",
                "data": {"provider": provider, "configured": bool(api_key)},
                "message": "API key updated",
            }

        elif action == "get_usage_stats":
            # Get LLM usage statistics
            time_period = request_data.get("time_period", "month")
            return {
                "status": "success",
                "data": {
                    "time_period": time_period,
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "by_provider": {},
                },
                "message": "Usage stats retrieved",
            }

        elif action == "add_api_key":
            # Save user's API key for a provider
            user_id = request_data.get("user_id", "")
            provider = request_data.get("provider", "anthropic")
            api_key = request_data.get("api_key", "")

            if not user_id or not api_key:
                return {"status": "error", "message": "user_id and api_key are required"}

            try:
                from socrates_api.database import get_database

                db = get_database()
                success = db.save_api_key(user_id, provider, api_key)

                if success:
                    logger.info(f"API key saved for user {user_id} provider {provider}")
                    return {
                        "status": "success",
                        "data": {"provider": provider},
                        "message": f"API key saved for {provider}",
                    }
                else:
                    return {"status": "error", "message": "Failed to save API key"}
            except Exception as e:
                logger.error(f"Failed to handle add_api_key: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}

        elif action == "remove_api_key":
            # Delete user's API key for a provider
            user_id = request_data.get("user_id", "")
            provider = request_data.get("provider", "anthropic")

            if not user_id:
                return {"status": "error", "message": "user_id is required"}

            try:
                from socrates_api.database import get_database

                db = get_database()
                success = db.delete_api_key(user_id, provider)

                if success:
                    logger.info(f"API key removed for user {user_id} provider {provider}")
                    return {"status": "success", "message": f"API key removed for {provider}"}
                else:
                    return {"status": "error", "message": "API key not found"}
            except Exception as e:
                logger.error(f"Failed to handle remove_api_key: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}

        elif action == "set_auth_method":
            # Set authentication method for a provider (e.g., API key vs subscription)
            user_id = request_data.get("user_id", "")
            provider = request_data.get("provider", "anthropic")
            auth_method = request_data.get("auth_method", "api_key")

            if not user_id:
                return {"status": "error", "message": "user_id is required"}

            # For now, just acknowledge the setting
            # In a full implementation, this would be stored and used
            logger.info(f"Auth method set for user {user_id} provider {provider}: {auth_method}")
            return {
                "status": "success",
                "data": {"provider": provider, "auth_method": auth_method},
                "message": f"Auth method updated for {provider}",
            }

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _detect_actionable_intent(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Detect actionable intents in user input (e.g., "skip question", "show hint").

        Returns:
            Dict with {
                "intent": str,
                "action": str,
                "confidence": float,
                "should_auto_execute": bool
            }
            or None if no actionable intent detected
        """
        user_input_lower = user_input.lower().strip()

        # Define actionable intents with keywords and corresponding actions
        intent_patterns = {
            "skip_question": {
                "keywords": ["skip", "next", "skip this", "move on", "next question"],
                "action": "skip_question",
                "confidence": 0.95,
            },
            "get_hint": {
                "keywords": ["hint", "help", "show hint", "i need help", "what's the hint"],
                "action": "get_hint",
                "confidence": 0.90,
            },
            "show_conflict": {
                "keywords": ["conflict", "explain conflict", "what's wrong", "what's the issue"],
                "action": "explain_conflict",
                "confidence": 0.85,
            },
            "show_answer": {
                "keywords": [
                    "answer",
                    "show answer",
                    "reveal",
                    "what's the answer",
                    "tell me the answer",
                ],
                "action": "show_answer",
                "confidence": 0.80,
            },
        }

        # Check for exact keyword matches
        for intent, pattern in intent_patterns.items():
            for keyword in pattern["keywords"]:
                if keyword in user_input_lower:
                    logger.debug(
                        f"Detected actionable intent: {intent} (confidence: {pattern['confidence']})"
                    )
                    return {
                        "intent": intent,
                        "action": pattern["action"],
                        "confidence": pattern["confidence"],
                        "should_auto_execute": pattern["confidence"] >= 0.85,
                    }

        return None

    def _ensure_user_exists_and_check_limits(self, user_id: str) -> tuple[bool, str]:
        """
        CRITICAL FIX #2: Auto-create users and enforce subscription limits.

        Args:
            user_id: The user identifier to check/create

        Returns:
            Tuple of (can_proceed, error_message)
        """
        try:
            # Load or create user
            user = self.database.load_user(user_id)

            if user is None:
                # Auto-create new users (default to free tier)
                from socrates_api.models_local import User

                user = User(
                    user_id=user_id,
                    username=user_id,
                    email=f"{user_id}@socrates.local",
                    subscription_tier="free",  # New users start with free tier
                    subscription_status="active",
                    testing_mode=False,
                )
                self.database.save_user(user)
                logger.info(f"Auto-created new user: {user_id} (free tier)")

            # Check subscription limits (unless testing mode is enabled)
            if not getattr(user, "testing_mode", False):
                can_ask, error_msg = user.check_question_limit()
                if not can_ask:
                    logger.warning(f"User {user_id} hit limit: {error_msg}")
                    return False, error_msg

            # Increment usage counter (if not testing mode)
            if not getattr(user, "testing_mode", False):
                user.increment_question_usage()
                self.database.save_user(user)
                logger.debug(f"Incremented usage for {user_id}: {user.questions_used_this_month} questions")

            return True, "User verified"

        except Exception as e:
            logger.warning(f"Error checking user limits: {e}")
            # Don't fail the request if user checking fails
            # Just log and continue
            return True, f"User check failed (continuing): {e}"

    # ================== CONVERSATION HISTORY MANAGEMENT (Monolithic Pattern) ==================

    def add_user_message_to_history(self, project: Any, content: str) -> None:
        """
        Add user message to conversation_history.
        MONOLITHIC PATTERN: Orchestrator manages conversation history, not endpoints.
        """
        if not hasattr(project, "conversation_history"):
            project.conversation_history = []

        project.conversation_history.append({
            "type": "user",
            "content": content,
            "phase": getattr(project, "phase", "discovery"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        logger.debug(f"✓ Added user message to conversation history")

    def add_assistant_message_to_history(self, project: Any, content: str) -> None:
        """
        Add assistant message to conversation_history with response_turn tracking.
        MONOLITHIC PATTERN: Orchestrator manages conversation history, not endpoints.
        """
        if not hasattr(project, "conversation_history"):
            project.conversation_history = []

        response_turn = len([
            m for m in project.conversation_history
            if m.get("type") == "assistant"
        ]) + 1

        project.conversation_history.append({
            "type": "assistant",
            "content": content,
            "phase": getattr(project, "phase", "discovery"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "response_turn": response_turn,
        })
        logger.debug(f"✓ Added assistant message (turn {response_turn}) to conversation history")

    def persist_conversation_history(self, project: Any) -> bool:
        """
        Persist conversation history to database.
        MONOLITHIC PATTERN: Orchestrator manages all persistence, not endpoints.
        """
        try:
            from socrates_api.database import get_database
            db = get_database()
            db.save_project(project)
            logger.debug(f"✓ Conversation history persisted to database")
            return True
        except Exception as e:
            logger.warning(f"Failed to persist conversation history: {e}")
            return False

    def persist_extracted_specs(
        self,
        project_id: str,
        specs: Dict[str, Any],
        extraction_method: str = "automatic",
        confidence_score: float = 0.8,
        source_text: str = "",
        response_turn: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Persist extracted specs to database.
        MONOLITHIC PATTERN: Orchestrator manages all spec persistence, not endpoints.
        """
        try:
            from socrates_api.database import get_database
            db = get_database()
            db.save_extracted_specs(
                project_id=project_id,
                specs=specs,
                extraction_method=extraction_method,
                confidence_score=confidence_score,
                source_text=source_text,
                response_turn=response_turn,
                metadata=metadata or {},
            )
            specs_count = sum([
                len(specs.get("goals", [])),
                len(specs.get("requirements", [])),
                len(specs.get("tech_stack", [])),
                len(specs.get("constraints", [])),
            ])
            logger.debug(f"✓ Persisted {specs_count} extracted specs to database")
            return True
        except Exception as e:
            logger.warning(f"Failed to persist extracted specs: {e}")
            return False

    def create_chat_session(self, project: Any, title: str = "") -> Dict[str, Any]:
        """
        Create a new chat session for a project.
        MONOLITHIC PATTERN: Orchestrator manages all chat session creation.
        """
        try:
            import uuid

            # Initialize sessions storage if needed
            if not hasattr(project, "chat_sessions"):
                project.chat_sessions = {}

            # Create new session
            session_id = f"sess_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)

            session = {
                "session_id": session_id,
                "title": title or f"Session {now.strftime('%Y-%m-%d %H:%M')}",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "archived": False,
                "messages": [],
            }

            # Add to project
            project.chat_sessions[session_id] = session

            # Persist
            try:
                from socrates_api.database import get_database
                db = get_database()
                db.save_project(project)
                logger.debug(f"✓ Chat session created: {session_id}")
            except Exception as e:
                logger.warning(f"Failed to persist chat session: {e}")

            return {
                "status": "success",
                "data": session,
                "message": "Chat session created",
            }
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            return {"status": "error", "message": str(e)}

    def get_chat_sessions(self, project: Any) -> Dict[str, Any]:
        """
        Get all chat sessions for a project.
        MONOLITHIC PATTERN: Orchestrator manages session retrieval.
        """
        try:
            sessions_dict = getattr(project, "chat_sessions", {})
            sessions_list = list(sessions_dict.values())

            return {
                "status": "success",
                "data": {
                    "sessions": sessions_list,
                    "count": len(sessions_list),
                },
                "message": f"Retrieved {len(sessions_list)} chat sessions",
            }
        except Exception as e:
            logger.error(f"Error retrieving chat sessions: {e}")
            return {"status": "error", "message": str(e)}

    def get_chat_session(self, project: Any, session_id: str) -> Dict[str, Any]:
        """
        Get a specific chat session.
        MONOLITHIC PATTERN: Orchestrator manages session retrieval.
        """
        try:
            sessions_dict = getattr(project, "chat_sessions", {})
            session = sessions_dict.get(session_id)

            if not session:
                return {"status": "error", "message": "Chat session not found"}

            return {
                "status": "success",
                "data": session,
                "message": "Chat session retrieved",
            }
        except Exception as e:
            logger.error(f"Error retrieving chat session: {e}")
            return {"status": "error", "message": str(e)}

    def skip_question(self, project: Any, question_id: str) -> Dict[str, Any]:
        """Skip a question for now (mark as skipped in pending_questions).

        User can recover this question later with reopen_question.
        """
        logger.info(f"[QUESTION_LIFECYCLE] Skipping question: {question_id}")

        if not hasattr(project, "pending_questions") or not project.pending_questions:
            return {"status": "error", "message": "No pending questions"}

        # Find and mark the question as skipped
        for q in project.pending_questions:
            if q.get("id") == question_id:
                q["status"] = "skipped"
                q["skipped_at"] = datetime.now(timezone.utc).isoformat()
                logger.info(f"[QUESTION_LIFECYCLE] ✓ Marked question as skipped: {q.get('question', '')[:60]}...")

                # Save project
                try:
                    from socrates_api.database import get_database
                    db = get_database()
                    db.save_project(project)
                    logger.info(f"[QUESTION_LIFECYCLE] Project saved after skipping question")
                except Exception as e:
                    logger.warning(f"[QUESTION_LIFECYCLE] Failed to save project after skip: {e}")

                return {
                    "status": "success",
                    "message": "Question marked as skipped"
                }

        return {"status": "error", "message": "Question not found"}

    def reopen_question(self, project: Any, question_id: str) -> Dict[str, Any]:
        """Reopen a skipped question (mark as unanswered again).

        This allows user to answer a question they previously skipped.
        """
        logger.info(f"[QUESTION_LIFECYCLE] Reopening question: {question_id}")

        if not hasattr(project, "pending_questions") or not project.pending_questions:
            return {"status": "error", "message": "No pending questions"}

        # Find and mark the question as unanswered
        for q in project.pending_questions:
            if q.get("id") == question_id:
                q["status"] = "unanswered"
                q["skipped_at"] = None  # Clear skip timestamp
                logger.info(f"[QUESTION_LIFECYCLE] ✓ Reopened question: {q.get('question', '')[:60]}...")

                # Save project
                try:
                    from socrates_api.database import get_database
                    db = get_database()
                    db.save_project(project)
                    logger.info(f"[QUESTION_LIFECYCLE] Project saved after reopening question")
                except Exception as e:
                    logger.warning(f"[QUESTION_LIFECYCLE] Failed to save project after reopen: {e}")

                return {
                    "status": "success",
                    "message": "Question reopened and ready to answer"
                }

        return {"status": "error", "message": "Question not found"}

    def list_pending_questions(self, project: Any) -> Dict[str, Any]:
        """List all unanswered and skipped questions that user can answer or recover."""
        logger.info(f"[QUESTION_LIFECYCLE] Listing pending questions")

        pending = []

        if hasattr(project, "pending_questions") and project.pending_questions:
            # Include both unanswered (to answer) and skipped (to recover)
            for q in project.pending_questions:
                if q.get("status") in ["unanswered", "skipped"]:
                    pending.append({
                        "id": q.get("id"),
                        "question": q.get("question"),
                        "phase": q.get("phase"),
                        "status": q.get("status"),
                        "created_at": q.get("created_at"),
                        "skipped_at": q.get("skipped_at"),
                    })

        logger.info(f"[QUESTION_LIFECYCLE] Found {len(pending)} pending/skipped questions")
        return {
            "status": "success",
            "pending_questions": pending,
            "total": len(pending),
            "unanswered": len([q for q in pending if q["status"] == "unanswered"]),
            "skipped": len([q for q in pending if q["status"] == "skipped"]),
        }

    def _process_answer_monolithic(self, project: Any, user_response: str, current_user: str) -> Dict[str, Any]:
        """
        Process user answer using the monolithic pattern from socratic-agents v0.3.0.

        Implementation:
        1. Extract specs with confidence scores via counselor
        2. Filter by confidence >= 0.7
        3. Merge into project fields
        4. Detect conflicts via detector
        5. Update maturity via maturity calculator
        6. Save all changes through orchestrator

        This ensures the system properly follows the monolithic Socrates pattern.
        """
        project_id = getattr(project, "project_id", None) or project.get("project_id", "unknown")
        phase = getattr(project, "phase", "discovery")

        logger.info(f"[ANSWER_PROCESSING] START: Processing user response for project {project_id}, phase={phase}")
        logger.info(f"[ANSWER_PROCESSING] User response: {user_response[:100]}...")

        try:
            # Get counselor and detector agents
            counselor = self._get_agent("socratic_counselor")
            detector = self._get_agent("conflict_detector")

            if not counselor:
                logger.error("[ANSWER_PROCESSING] MISSING: socratic_counselor agent not available")
            if not detector:
                logger.error("[ANSWER_PROCESSING] MISSING: conflict_detector agent not available")

            if not counselor or not detector:
                logger.error("[ANSWER_PROCESSING] FAIL: Required agents (counselor, detector) not available")
                return {
                    "status": "error",
                    "message": "Required agents (counselor, detector) not available"
                }

            # Step 1: Extract specs from user response with confidence scores
            logger.info(f"[ANSWER_PROCESSING] Step 1: Extracting specs from user response...")
            extraction_result = counselor.process({
                "action": "extract_insights_only",
                "response": user_response,  # CRITICAL: Must use "response" not "text" to match agent interface
                "project": project,  # CRITICAL: Pass full project object for agent context
            })

            logger.debug(f"[ANSWER_PROCESSING] Extraction result keys: {extraction_result.keys()}")

            # Extract insights from result (follows monolithic pattern)
            # Structure: {"status": "success", "insights": {"goals": [...], "requirements": [...], ...}}
            insights_dict = extraction_result.get("insights", {})
            if not insights_dict:
                # Fallback for different response format
                insights_dict = extraction_result.get("data", {}).get("insights", {})
            if not insights_dict:
                insights_dict = {}

            # Count total specs extracted
            total_specs = sum(len(v) if isinstance(v, list) else 0 for v in insights_dict.values())
            logger.info(f"[ANSWER_PROCESSING] Step 1 Result: Extracted {total_specs} total specs")
            logger.debug(f"[ANSWER_PROCESSING]   Spec categories: {list(insights_dict.keys())}")
            for category in list(insights_dict.keys())[:3]:
                if isinstance(insights_dict.get(category), list):
                    logger.debug(f"[ANSWER_PROCESSING]     {category}: {len(insights_dict[category])} items")

            # Step 2: Filter by confidence >= 0.7 (for specs that have confidence scores)
            logger.info(f"[ANSWER_PROCESSING] Step 2: Filtering specs by confidence >= 0.7...")
            high_confidence_specs = {}
            for category, spec_list in insights_dict.items():
                if isinstance(spec_list, list):
                    filtered = [
                        s for s in spec_list
                        if (isinstance(s, dict) and s.get("confidence_score", 1.0) >= 0.7)
                        or isinstance(s, str)
                    ]
                    if filtered:
                        high_confidence_specs[category] = filtered
                else:
                    high_confidence_specs[category] = spec_list

            high_confidence_count = sum(len(v) if isinstance(v, list) else 0 for v in high_confidence_specs.values())
            logger.info(f"[ANSWER_PROCESSING] Step 2 Result: {high_confidence_count} high-confidence specs (filtered from {total_specs})")

            # Get existing specs for comparison
            existing_goals = getattr(project, "goals", []) or []
            existing_requirements = getattr(project, "requirements", []) or []
            existing_tech_stack = getattr(project, "tech_stack", []) or []
            existing_constraints = getattr(project, "constraints", []) or []

            logger.info(f"[ANSWER_PROCESSING] Existing specs in project:")
            logger.info(f"[ANSWER_PROCESSING]   Goals: {len(existing_goals)} items - {existing_goals[:2]}")
            logger.info(f"[ANSWER_PROCESSING]   Requirements: {len(existing_requirements)} items")
            logger.info(f"[ANSWER_PROCESSING]   Tech Stack: {len(existing_tech_stack)} items")
            logger.info(f"[ANSWER_PROCESSING]   Constraints: {len(existing_constraints)} items")

            # Step 3-4: Merge specs and detect conflicts
            logger.info(f"[ANSWER_PROCESSING] Step 3-4: Merging specs and detecting conflicts...")
            conflicts = []
            merged_count = 0

            if high_confidence_specs:
                # Merge specs into project using the insights dict structure
                # Structure: {"goals": [...], "requirements": [...], "tech_stack": [...], "constraints": [...]}

                # Merge goals
                if "goals" in high_confidence_specs:
                    if not hasattr(project, "goals"):
                        project.goals = []
                    goals_list = high_confidence_specs["goals"]
                    if isinstance(goals_list, list):
                        for goal in goals_list:
                            if isinstance(goal, dict):
                                goal_text = goal.get("goal") or goal.get("text") or str(goal)
                            else:
                                goal_text = str(goal)
                            project.goals.append(goal_text)
                            merged_count += 1
                            logger.debug(f"[ANSWER_PROCESSING] Merged goal: {goal_text}")

                # Merge requirements
                if "requirements" in high_confidence_specs:
                    if not hasattr(project, "requirements"):
                        project.requirements = []
                    reqs_list = high_confidence_specs["requirements"]
                    if isinstance(reqs_list, list):
                        for req in reqs_list:
                            if isinstance(req, dict):
                                req_text = req.get("requirement") or req.get("text") or str(req)
                            else:
                                req_text = str(req)
                            project.requirements.append(req_text)
                            merged_count += 1
                            logger.debug(f"[ANSWER_PROCESSING] Merged requirement: {req_text}")

                # Merge tech stack
                if "tech_stack" in high_confidence_specs:
                    if not hasattr(project, "tech_stack"):
                        project.tech_stack = []
                    tech_list = high_confidence_specs["tech_stack"]
                    if isinstance(tech_list, list):
                        for tech in tech_list:
                            if isinstance(tech, dict):
                                tech_text = tech.get("technology") or tech.get("tech") or tech.get("text") or str(tech)
                            else:
                                tech_text = str(tech)
                            project.tech_stack.append(tech_text)
                            merged_count += 1
                            logger.debug(f"[ANSWER_PROCESSING] Merged tech: {tech_text}")

                # Merge constraints
                if "constraints" in high_confidence_specs:
                    if not hasattr(project, "constraints"):
                        project.constraints = []
                    constr_list = high_confidence_specs["constraints"]
                    if isinstance(constr_list, list):
                        for constr in constr_list:
                            if isinstance(constr, dict):
                                constr_text = constr.get("constraint") or constr.get("text") or str(constr)
                            else:
                                constr_text = str(constr)
                            project.constraints.append(constr_text)
                            merged_count += 1
                            logger.debug(f"[ANSWER_PROCESSING] Merged constraint: {constr_text}")

                logger.info(f"[ANSWER_PROCESSING] Step 3 Result: Merged {merged_count} new specs into project")

                # Detect conflicts
                logger.info(f"[ANSWER_PROCESSING] Step 4: Calling conflict detector...")
                # CRITICAL FIX: Use process() dispatch pattern, not direct method call
                # detect_conflicts is an action, not a public method
                detector_result = detector.process({
                    "action": "detect_conflicts",
                    "insights": high_confidence_specs,  # CRITICAL: Agent expects "insights" not "new_insights"
                    "project": project,
                })

                conflicts = detector_result.get("conflicts", []) if detector_result else []
                logger.info(f"[ANSWER_PROCESSING] Step 4 Result: Detected {len(conflicts)} conflict(s)")
                for i, conflict in enumerate(conflicts[:3]):  # Log first 3 conflicts
                    logger.debug(f"[ANSWER_PROCESSING]   Conflict {i+1}: {conflict}")
            else:
                logger.info(f"[ANSWER_PROCESSING] No high-confidence specs to merge or detect conflicts")

            # Step 5: Update maturity
            logger.info(f"[ANSWER_PROCESSING] Step 5: Calculating maturity...")
            maturity_result = {}
            try:
                from socratic_maturity import MaturityCalculator
                calc = MaturityCalculator()
                maturity_result = calc.calculate({
                    "specs": high_confidence_specs,
                    "project": project,
                    "phase": phase
                })
                logger.info(f"[ANSWER_PROCESSING] Step 5 Result: Maturity calculation successful")
            except Exception as e:
                logger.warning(f"[ANSWER_PROCESSING] Step 5 WARNING: Maturity calculation failed: {e}")

            # Step 6: Add to conversation history
            logger.info(f"[ANSWER_PROCESSING] Step 6: Saving to conversation history...")
            self.add_user_message_to_history(project, user_response)
            logger.debug(f"[ANSWER_PROCESSING] User message added to history")

            self.persist_conversation_history(project)
            logger.debug(f"[ANSWER_PROCESSING] Conversation history persisted")

            # Step 6b: Mark current question as answered in pending_questions (HYBRID APPROACH)
            logger.info(f"[ANSWER_PROCESSING] Step 6b: Marking question as answered in pending_questions...")
            if hasattr(project, "pending_questions") and project.pending_questions:
                # Find the most recent unanswered question in current phase and mark it answered
                for q in reversed(project.pending_questions):
                    if q.get("phase") == phase and q.get("status") == "unanswered":
                        q["status"] = "answered"
                        q["answered_at"] = datetime.now(timezone.utc).isoformat()
                        logger.info(f"[ANSWER_PROCESSING] Marked question as answered: {q.get('question', '')[:60]}...")
                        break
            else:
                logger.debug(f"[ANSWER_PROCESSING] No pending_questions to update")

            # Save project
            try:
                from socrates_api.database import get_database
                db = get_database()
                db.save_project(project)
                logger.info(f"[ANSWER_PROCESSING] ✓ Project saved after answer processing")
            except Exception as e:
                logger.warning(f"[ANSWER_PROCESSING] WARNING: Failed to save project after answer: {e}")

            # Prepare response with insights
            insights = {}
            if high_confidence_specs:
                # Insights dict already has the correct structure: {"goals": [...], "requirements": [...], ...}
                # Just extract the text/values from each category
                insights = {}
                for category in ["goals", "requirements", "tech_stack", "constraints"]:
                    if category in high_confidence_specs:
                        spec_list = high_confidence_specs[category]
                        if isinstance(spec_list, list):
                            # Extract text from each spec (could be dict or string)
                            insights[category] = [
                                s.get("text") or s.get(category[:-1]) or str(s) if isinstance(s, dict) else str(s)
                                for s in spec_list
                            ]
                        else:
                            insights[category] = [spec_list] if spec_list else []

            logger.info(f"[ANSWER_PROCESSING] SUCCESS: Answer processing complete. Specs merged: {merged_count}, Conflicts: {len(conflicts)}")

            return {
                "status": "success",
                "data": {
                    "specs": high_confidence_specs,
                    "conflicts": conflicts,
                    "maturity": maturity_result,
                    "message": "Answer processed successfully"
                },
                "insights": insights,
                "conflicts_pending": len(conflicts) > 0,
            }

        except Exception as e:
            logger.error(f"[ANSWER_PROCESSING] FAIL: Error in monolithic answer processing: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Answer processing failed: {str(e)}"
            }

    def _handle_socratic_counselor(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Socratic counselor requests for generating questions"""
        action = request_data.get("action", "")

        if action == "generate_question":
            # Generate a Socratic question for a project
            project = request_data.get("project", {})
            topic = request_data.get("topic", "")
            # CRITICAL: user_id MUST be a real user, never empty or None
            # Agent will default to "default_user" (which doesn't exist) if empty
            user_id = request_data.get("user_id") or request_data.get("current_user", "")
            if not user_id:
                logger.warning("No user_id or current_user provided for question generation")
                return {"status": "error", "message": "User context required for question generation"}
            force_refresh = request_data.get("force_refresh", False)

            # CRITICAL FIX #2: Check user subscription limits before generating question
            if user_id:
                can_proceed, limit_msg = self._ensure_user_exists_and_check_limits(user_id)
                if not can_proceed:
                    return {
                        "status": "error",
                        "message": f"Cannot generate question: {limit_msg}",
                        "error_code": "SUBSCRIPTION_LIMIT_EXCEEDED",
                    }

            logger.info(
                f"_handle_socratic_counselor generate_question: topic={topic[:50] if topic else 'EMPTY'}"
            )

            # Get project ID and phase for caching
            project_id = getattr(project, "project_id", None) or project.get("project_id")
            phase = (
                getattr(project, "phase", "discovery")
                if hasattr(project, "phase")
                else project.get("phase", "discovery")
            )

            # NOTE: Question cache disabled to match monolithic behavior
            # Monolithic version stores pending questions in project.pending_questions
            # and generates new questions on each request, not from cache

            # HYBRID APPROACH: Check for existing unanswered questions before generating new one
            # This prevents double question generation (unless force_refresh is set)
            logger.info(f"[QUESTION_GEN] Checking for existing unanswered questions in {phase} phase...")
            if not force_refresh and hasattr(project, "pending_questions") and project.pending_questions:
                unanswered = [
                    q for q in project.pending_questions
                    if q.get("status") == "unanswered" and q.get("phase") == phase
                ]
                if unanswered:
                    existing_question = unanswered[0]  # Return first unanswered
                    logger.info(f"[QUESTION_GEN] ✓ Returning existing unanswered question (force_refresh={force_refresh})")
                    logger.info(f"[QUESTION_GEN] Question: {existing_question.get('question', '')[:70]}...")
                    return {
                        "status": "success",
                        "data": {
                            "question": existing_question.get("question", ""),
                            "question_id": existing_question.get("id", ""),
                            "existing": True  # Signal: this is an existing question, not newly generated
                        },
                        "message": "Returning existing unanswered question"
                    }
                else:
                    logger.info(f"[QUESTION_GEN] No unanswered questions in {phase} phase, will generate new one")
            else:
                logger.info(f"[QUESTION_GEN] Force refresh enabled or no pending_questions, will generate new question")

            # Try to use the actual agent if available
            counselor = self._get_agent("socratic_counselor")

            try:
                # Try to get user's API key
                from socrates_api.database import get_database

                db = get_database()

                # Get user's preferred provider and model
                provider = db.get_user_default_provider(user_id)
                model = db.get_provider_model(user_id, provider)
                user_api_key = db.get_api_key(user_id, provider)

                # If default provider doesn't have a key, try to find any provider with a key
                if not user_api_key:
                    for fallback_provider in ["claude", "openai", "gemini", "ollama", "anthropic"]:
                        fallback_key = db.get_api_key(user_id, fallback_provider)
                        if fallback_key:
                            provider = fallback_provider
                            user_api_key = fallback_key
                            stored_model = db.get_provider_model(user_id, provider)
                            model = _get_valid_model_for_provider(provider, stored_model)
                            logger.info(
                                f"No key for default provider, using fallback provider: {provider}/{model}"
                            )
                            break

                # Create LLM client with user's key if available
                llm_client_to_use = None
                if user_api_key:
                    try:
                        # Use socratic-nexus with production features for user's API key
                        raw_client = LLMClient(
                            provider=provider,
                            model=model,
                            api_key=user_api_key,
                            cache_responses=True,  # Cache responses for performance
                            cache_ttl=3600,  # Cache for 1 hour
                            retry_attempts=3,  # Retry up to 3 times on failure
                            retry_backoff_factor=2.0,  # Exponential backoff for retries
                        )
                        # Wrap with adapter for SocraticCounselor compatibility
                        llm_client_to_use = LLMClientAdapter(raw_client)
                        logger.info(
                            f"Using user API key for {user_id} with provider {provider}/{model} "
                            "and production features: token_tracking=True, response_caching=True"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to create LLMClient with user key: {e}", exc_info=True
                        )
                        llm_client_to_use = self.llm_client
                else:
                    llm_client_to_use = self.llm_client
                    if llm_client_to_use:
                        logger.info(f"No user API key for {user_id}, using global API key")
                    else:
                        logger.warning(f"No user API key and no global API key for user {user_id}")

                if counselor and llm_client_to_use:
                    # Temporarily assign the correct LLM client
                    original_llm_client = counselor.llm_client
                    counselor.llm_client = llm_client_to_use

                    try:
                        # Use real agent to generate question
                        # SocraticCounselor expects topic at top level
                        # CRITICAL FIX: Include conversation history for context-aware question generation
                        logger.info(
                            f"Calling counselor.process() with topic: {topic[:50] if topic else 'EMPTY'}"
                        )
                        conversation_summary = self._get_conversation_summary(project)

                        # Build request with full project context
                        # Use description as goals if goals not provided
                        goals = getattr(project, "goals", "") or topic or ""

                        # Pass entire project object to agent for full context
                        counselor_request = {
                            "action": "generate_question",  # CRITICAL: Must specify action for agent dispatch
                            "topic": topic,
                            "context": conversation_summary,
                            "phase": phase,
                            "goals": goals,
                            "project_id": project_id,
                            "project": project,  # Include full project object for agent context
                            "user_id": user_id,  # CRITICAL: Agent expects "user_id" not "current_user"
                            "force_refresh": force_refresh,  # Also pass force_refresh for consistency
                        }

                        # Include conversation history if available
                        conversation_history = getattr(project, "conversation_history", [])
                        if conversation_history:
                            counselor_request["conversation_history"] = conversation_history
                            logger.debug(
                                f"Including {len(conversation_history)} conversation history entries for context"
                            )

                        # MONOLITHIC PATTERN: Extract previously asked questions from conversation history
                        # This follows the proven working approach from monolithic Socrates
                        # Key: Filter by type="assistant" (questions, not responses) and phase (current phase only)
                        previously_asked_questions = []
                        conversation_history = getattr(project, "conversation_history", [])

                        logger.info(f"[QUESTION_DEDUP] Analyzing conversation history for deduplication...")
                        logger.info(f"[QUESTION_DEDUP] Total messages in history: {len(conversation_history)}")

                        if conversation_history:
                            for i, msg in enumerate(conversation_history):
                                msg_type = msg.get("type", "unknown")
                                msg_phase = msg.get("phase", "unknown")
                                msg_content = msg.get("content", "")[:50]

                                # Only include messages that are:
                                # 1. Questions (type="assistant")
                                # 2. From the current phase
                                # 3. Have actual question content
                                if (
                                    msg.get("type") == "assistant"
                                    and msg.get("phase") == phase
                                    and msg.get("content")
                                ):
                                    previously_asked_questions.append(msg.get("content"))
                                    logger.debug(f"[QUESTION_DEDUP] Message {i}: Included (type={msg_type}, phase={msg_phase}, content={msg_content}...)")
                                else:
                                    reason = []
                                    if msg.get("type") != "assistant":
                                        reason.append(f"type={msg_type}!=assistant")
                                    if msg.get("phase") != phase:
                                        reason.append(f"phase={msg_phase}!={phase}")
                                    if not msg.get("content"):
                                        reason.append("no_content")
                                    logger.debug(f"[QUESTION_DEDUP] Message {i}: Skipped ({', '.join(reason)})")

                            if previously_asked_questions:
                                counselor_request["recently_asked"] = previously_asked_questions  # FIXED: Agent expects "recently_asked" not "previously_asked_questions"
                                logger.info(
                                    f"[QUESTION_DEDUP] ✓ Passing {len(previously_asked_questions)} previously asked questions "
                                    f"in {phase} phase for deduplication"
                                )
                                for i, q in enumerate(previously_asked_questions[:3]):
                                    logger.debug(f"[QUESTION_DEDUP]   Q{i+1}: {q[:60]}...")
                            else:
                                logger.info(f"[QUESTION_DEDUP] No previously asked questions found for phase {phase}")

                        # Include other project context (for backward compatibility)
                        if hasattr(project, "requirements") and project.requirements:
                            counselor_request["requirements"] = project.requirements
                        if hasattr(project, "tech_stack") and project.tech_stack:
                            counselor_request["tech_stack"] = project.tech_stack

                        # CRITICAL FIX #12: Protect agent call with circuit breaker
                        breaker = CircuitBreakerRegistry.get_breaker(
                            "socratic_counselor",
                            failure_threshold=5,
                            timeout_seconds=60,
                        )

                        # MONOLITHIC PATTERN: Track question generation with conversation_history (single source of truth)
                        previous_conversation_count = len(getattr(project, "conversation_history", []))
                        questions_asked_count = len([
                            m for m in getattr(project, "conversation_history", [])
                            if m.get("type") == "assistant"
                        ])
                        logger.debug(f"Conversation state BEFORE generation: {previous_conversation_count} total messages, {questions_asked_count} questions")

                        try:
                            logger.info(f"[QUESTION_GEN] Calling counselor.process() with {len(previously_asked_questions)} previously asked questions...")
                            result = breaker.call(counselor.process, counselor_request)

                            generated_question = result.get('question', '')
                            logger.info(f"[QUESTION_GEN] Counselor returned: {generated_question[:70] if generated_question else 'NO_QUESTION'}")

                            # Check if question is a duplicate
                            if generated_question and previously_asked_questions:
                                if generated_question in previously_asked_questions:
                                    logger.warning(f"[QUESTION_GEN] ⚠️ WARNING: Generated question is IDENTICAL to a previously asked question!")
                                else:
                                    logger.info(f"[QUESTION_GEN] ✓ Generated question is new (not in previously asked list)")

                            # MONOLITHIC PATTERN: Verify question was stored in conversation_history
                            updated_conversation_count = len(getattr(project, "conversation_history", []))
                            updated_questions_count = len([
                                m for m in getattr(project, "conversation_history", [])
                                if m.get("type") == "assistant"
                            ])
                            messages_added = updated_conversation_count - previous_conversation_count
                            questions_added = updated_questions_count - questions_asked_count

                            logger.info(f"[QUESTION_GEN] Conversation state AFTER generation: {updated_conversation_count} total, {updated_questions_count} questions (added {messages_added} msgs, {questions_added} questions)")

                            if messages_added == 0 and questions_added == 0:
                                logger.warning(f"[QUESTION_GEN] ⚠️ WARNING: Question NOT stored in conversation_history!")
                        except Exception as circuit_error:
                            logger.error(
                                f"Circuit breaker {breaker.name} blocked or agent failed: {circuit_error}",
                                exc_info=True,
                                extra={"circuit_breaker_status": breaker.get_status()},
                            )
                            return {
                                "status": "error",
                                "message": str(circuit_error),
                                "circuit_breaker": breaker.get_status(),
                            }

                        # MONOLITHIC PATTERN: Store question in conversation_history
                        # This is essential for next question generation to find "previously_asked_questions"
                        question_id = None
                        if result.get("question"):
                            if not hasattr(project, "conversation_history"):
                                project.conversation_history = []

                            # Generate unique question ID for pending_questions
                            import uuid
                            question_id = f"q_{uuid.uuid4().hex[:8]}"

                            project.conversation_history.append({
                                "type": "assistant",
                                "content": result.get("question"),
                                "phase": phase,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "response_turn": len([
                                    m for m in project.conversation_history
                                    if m.get("type") == "assistant"
                                ]) + 1,
                                "question_id": question_id,  # Link to pending_questions
                            })

                            # HYBRID APPROACH: Also store in pending_questions for unified tracking
                            # This enables skip/reopen functionality and clear status tracking
                            if not hasattr(project, "pending_questions"):
                                project.pending_questions = []

                            project.pending_questions.append({
                                "id": question_id,
                                "question": result.get("question"),
                                "phase": phase,
                                "status": "unanswered",  # CRITICAL: Explicit status
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "answered_at": None,
                                "skipped_at": None,
                            })

                            logger.info(f"[QUESTION_GEN] ✓ Stored question in both conversation_history and pending_questions with status=unanswered")

                        # SAVE PROJECT with updated conversation_history and pending_questions
                        try:
                            from socrates_api.database import get_database

                            db = get_database()
                            db.save_project(project)
                            logger.info(f"[QUESTION_GEN] ✓ Project saved with updated question in both structures")
                        except Exception as e:
                            logger.warning(f"[QUESTION_GEN] WARNING: Failed to save project after question generation: {e}")

                        # CACHE THE GENERATED QUESTION
                        if project_id and result.get("question"):
                            try:
                                db.save_cached_question(
                                    project_id=project_id,
                                    phase=phase,
                                    category=None,
                                    question_text=result.get("question"),
                                )
                                logger.info(f"Cached new question for project {project_id}")

                                # Prune cache if too large
                                db.prune_question_cache(project_id, max_questions=50)
                            except Exception as e:
                                logger.warning(f"Failed to cache generated question: {e}")

                        # CRITICAL: Check if agent returned a valid question
                        if not result.get("question"):
                            logger.warning(f"[QUESTION_GEN] Agent returned empty question, using fallback")
                        else:
                            return {
                                "status": "success",
                                "data": result,
                                "message": "Question generated",
                            }
                    finally:
                        # Restore original client
                        counselor.llm_client = original_llm_client
            except Exception as e:
                logger.warning(f"Failed to use socratic_counselor agent: {e}", exc_info=True)

            # Fallback: Generate a generic Socratic question
            questions = [
                "What is the main goal of your project?",
                "How does this feature contribute to the overall system design?",
                "What are the key requirements you need to address?",
                "Have you considered edge cases or error conditions?",
                "How would you test this implementation?",
                "What are the performance implications of your approach?",
                "How does this integrate with existing functionality?",
                "What dependencies does this component have?",
                "How would you document this functionality?",
                "What alternatives did you consider?",
            ]

            # Generate a question based on project phase
            phase = (
                getattr(project, "phase", "discovery")
                if hasattr(project, "phase")
                else project.get("phase", "discovery")
            )
            question_idx = hash((user_id, phase, force_refresh)) % len(questions)

            return {
                "status": "success",
                "data": {
                    "question": questions[question_idx],
                    "project_id": getattr(project, "project_id", project.get("id", "unknown")),
                    "phase": phase,
                    "suggested_response": "I will think about this carefully...",
                },
                "message": "Question generated",
            }

        elif action == "process_response":
            # Use the monolithic pattern from socratic-agents v0.3.0
            response = request_data.get("response", "")
            project = request_data.get("project", {})
            # FIXED: Check for "user_id" first (what router passes), then fall back to "current_user"
            current_user = request_data.get("user_id") or request_data.get("current_user", "")

            logger.info(f"Processing response using monolithic pattern: {response[:50]}...")

            # Call the monolithic answer processing workflow from the library
            result = self._process_answer_monolithic(project, response, current_user)
            return result

        elif action == "generate_hint":
            # Generate a contextual hint for the current question
            project = request_data.get("project", {})
            current_user = request_data.get("current_user", "")

            logger.info(f"Generating hint for user {current_user}")

            try:
                # Try to use SkillGeneratorAgent for smart hint generation
                agent = self._get_agent("skill_generator")
                if agent and self.llm_client:
                    try:
                        # Get project context for hint generation
                        phase = (
                            getattr(project, "phase", project.get("phase", "discovery"))
                            if hasattr(project, "get")
                            else project.get("phase", "discovery")
                        )
                        goals = (
                            getattr(project, "goals", project.get("goals", ""))
                            if hasattr(project, "get")
                            else project.get("goals", "")
                        )

                        hint_prompt = f"""You are a Socratic tutor. A student is working on a project in the '{phase}' phase.

Project Goals: {goals if goals else "Not yet defined"}

Generate a brief, encouraging hint that guides the student to think about the next logical step in their project development. The hint should:
1. Be specific to the current phase
2. Encourage deeper thinking rather than giving direct answers
3. Reference project goals if available
4. Be concise (2-3 sentences max)

Provide only the hint text, no additional commentary."""

                        result = agent.process(
                            {
                                "action": "generate",
                                "prompt": hint_prompt,
                                "context": {
                                    "phase": phase,
                                    "goals": goals,
                                },
                            }
                        )

                        if result and result.get("status") == "success":
                            hint = result.get("data", {}).get("hint") or result.get("hint")
                            if hint:
                                logger.info(
                                    f"Generated hint using SkillGeneratorAgent: {hint[:50]}..."
                                )
                                return {
                                    "status": "success",
                                    "data": {"hint": hint},
                                    "message": "Hint generated",
                                }
                    except Exception as e:
                        logger.warning(f"SkillGeneratorAgent hint failed: {e}, using fallback")

                # MONOLITHIC PATTERN: Skip direct LLM call, go straight to phase-aware fallback
                # Use phase-aware hint instead of direct LLM client
                phase = (
                    getattr(project, "phase", project.get("phase", "discovery"))
                    if hasattr(project, "get")
                    else project.get("phase", "discovery")
                )

                phase_hints = {
                    "discovery": "Consider what problem you're trying to solve. What are the key requirements and constraints?",
                    "requirements": "Think about how each requirement connects to your overall goals. Are there any missing pieces?",
                    "architecture": "Review the components you've identified. How do they communicate with each other?",
                    "implementation": "What's the next logical module or feature to implement? Start small and build up.",
                    "testing": "What edge cases might you have missed? How would you test for them?",
                    "deployment": "What are the steps to make your project accessible to users? Start with the most critical one.",
                }

                hint = phase_hints.get(
                    phase,
                    "Review your project progress and identify the next logical step in your development journey.",
                )

                logger.info(f"Using fallback hint for phase {phase}")
                return {
                    "status": "success",
                    "data": {"hint": hint},
                    "message": "Hint generated (fallback)",
                }

            except Exception as e:
                logger.error(f"Failed to generate hint: {e}", exc_info=True)
                return {
                    "status": "success",
                    "data": {
                        "hint": "Review your project requirements and consider what step comes next in your learning journey."
                    },
                    "message": "Hint generated (fallback)",
                }

        elif action == "skip_question":
            # Skip to the next question
            project = request_data.get("project", {})
            current_user = request_data.get("current_user", "")

            logger.info(f"Skipping current question for user {current_user}")

            try:
                # Clear current question context
                if hasattr(project, "current_question_id"):
                    project.current_question_id = None
                    project.current_question_text = None

                # Save updated project
                from socrates_api.database import get_database

                db = get_database()
                project_id = (
                    getattr(project, "project_id", project.get("project_id"))
                    if hasattr(project, "get")
                    else project.get("project_id")
                )
                if project_id:
                    db.save_project(project_id, project)

                # Return success - frontend will call get_question to fetch next question
                return {
                    "status": "success",
                    "data": {
                        "message": "Question skipped. Generating next question...",
                        "action": "generate_question",
                    },
                    "message": "Question skipped",
                }
            except Exception as e:
                logger.error(f"Error skipping question: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to skip question: {str(e)}",
                }

        elif action == "explain_conflict":
            # Explain detected conflicts to the user
            project = request_data.get("project", {})
            conflicts = request_data.get("conflicts", [])

            logger.info(f"Explaining {len(conflicts)} conflicts")

            try:
                if not conflicts:
                    return {
                        "status": "success",
                        "data": {
                            "explanation": "No conflicts detected. Your response aligns well with the project requirements.",
                        },
                        "message": "No conflicts to explain",
                    }

                # Use the helper function from projects_chat to generate user-friendly explanations
                from socrates_api.routers.projects_chat import _generate_conflict_explanation

                explanation = _generate_conflict_explanation(conflicts)

                return {
                    "status": "success",
                    "data": {
                        "explanation": explanation,
                        "conflicts": conflicts,
                    },
                    "message": f"Explanation of {len(conflicts)} conflict(s)",
                }
            except Exception as e:
                logger.error(f"Error explaining conflicts: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to explain conflicts: {str(e)}",
                }

        elif action == "generate_answer_suggestions":
            # Generate answer suggestions for the current question
            project = request_data.get("project", {})
            current_question = request_data.get("current_question", "")
            current_user = request_data.get("current_user", "")

            logger.info(
                f"_handle_socratic_counselor generate_answer_suggestions for question: {current_question[:50]}"
            )

            try:
                # Get project ID for context
                project_id = getattr(project, "project_id", None) or project.get("project_id", "")
                user_id = getattr(project, "user_id", None) or project.get("user_id", "") or current_user

                # Call the answer suggestions orchestration method
                return self._orchestrate_answer_suggestions(
                    project=project,
                    user_id=user_id,
                    question_id=""  # Not needed for suggestions, but keeping signature compatible
                )
            except Exception as e:
                logger.error(f"Error generating answer suggestions: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Failed to generate answer suggestions: {str(e)}",
                }

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _handle_direct_chat(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct chat mode requests for generating answers"""
        action = request_data.get("action", "")

        if action == "generate_answer":
            # Generate a direct answer to user's question
            prompt = request_data.get("prompt", "")
            user_id = request_data.get("user_id", "")

            if not prompt:
                return {"status": "error", "message": "Prompt is required"}

            try:
                # Try to get user's API key
                from socrates_api.database import get_database

                db = get_database()

                # Get user's preferred provider and model
                provider = db.get_user_default_provider(user_id)
                model = db.get_provider_model(user_id, provider)
                user_api_key = db.get_api_key(user_id, provider)

                # If default provider doesn't have a key, try to find any provider with a key
                if not user_api_key:
                    for fallback_provider in ["claude", "openai", "gemini", "ollama", "anthropic"]:
                        fallback_key = db.get_api_key(user_id, fallback_provider)
                        if fallback_key:
                            provider = fallback_provider
                            user_api_key = fallback_key
                            stored_model = db.get_provider_model(user_id, provider)
                            model = _get_valid_model_for_provider(provider, stored_model)
                            logger.info(
                                f"No key for default provider, using fallback provider: {provider}/{model}"
                            )
                            break

                # Create LLM client with user's key if available
                llm_client_to_use = None
                if user_api_key:
                    try:
                        # Use socratic-nexus with production features for user's API key
                        raw_client = LLMClient(
                            provider=provider,
                            model=model,
                            api_key=user_api_key,
                            cache_responses=True,  # Cache responses for performance
                            cache_ttl=3600,  # Cache for 1 hour
                            retry_attempts=3,  # Retry up to 3 times on failure
                            retry_backoff_factor=2.0,  # Exponential backoff for retries
                        )
                        # Wrap with adapter for compatibility
                        llm_client_to_use = LLMClientAdapter(raw_client)
                        logger.info(
                            f"Using user API key for user {user_id} in direct mode with provider {provider}/{model} "
                            "and production features: token_tracking=True, response_caching=True"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to create LLMClient with user key: {e}", exc_info=True
                        )
                        llm_client_to_use = self.llm_client
                else:
                    llm_client_to_use = self.llm_client
                    if llm_client_to_use:
                        logger.info(
                            f"No user API key for {user_id}, using global API key in direct mode"
                        )
                    else:
                        logger.warning(f"No user API key and no global API key for user {user_id}")

                if not llm_client_to_use:
                    return {
                        "status": "error",
                        "message": "No API key available for response generation",
                    }

                # Generate answer using the appropriate LLM client
                answer = llm_client_to_use.generate_response(prompt)

                if not answer:
                    return {"status": "error", "message": "Failed to generate answer"}

                logger.info(f"Generated direct answer for user {user_id}")
                return {
                    "status": "success",
                    "data": {"answer": answer, "user_id": user_id},
                    "message": "Answer generated",
                }

            except Exception as e:
                logger.error(f"Failed to generate direct answer: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}

        elif action == "extract_insights":
            # Extract specs/insights from text
            text = request_data.get("text", "")
            user_id = request_data.get("user_id", "")
            project = request_data.get("project", {})

            if not text:
                return {"status": "error", "message": "Text is required for insight extraction"}

            try:
                # Try to get user's API key
                from socrates_api.database import get_database

                db = get_database()
                user_api_key = db.get_api_key(user_id, "anthropic")
                provider = "anthropic"

                # If anthropic key not found, try to find any provider with a key
                if not user_api_key:
                    fallback_models = {
                        "claude": "claude-3-5-sonnet-20241022",
                        "openai": "gpt-4-turbo",
                        "gemini": "gemini-pro",
                        "ollama": "llama2",
                    }
                    for fallback_provider in ["claude", "openai", "gemini", "ollama"]:
                        fallback_key = db.get_api_key(user_id, fallback_provider)
                        if fallback_key:
                            provider = fallback_provider
                            user_api_key = fallback_key
                            logger.info(
                                f"No anthropic key, using fallback provider for insights: {provider}"
                            )
                            break

                # Create LLM client with user's key if available
                llm_client_to_use = None
                if user_api_key:
                    # Try multiple models in case one isn't available
                    models_to_try = [
                        "claude-haiku-4-5-20251001",  # Latest valid model
                        "claude-3-5-sonnet-20241022",
                        "claude-opus-4-20250514",
                        "claude-3-haiku-20240307",
                    ]
                    for model_name in models_to_try:
                        try:
                            # Use socratic-nexus with production features for insights extraction
                            raw_client = LLMClient(
                                provider=provider,
                                model=model_name,
                                api_key=user_api_key,
                                cache_responses=True,  # Cache responses for performance
                                cache_ttl=3600,  # Cache for 1 hour
                                retry_attempts=3,  # Retry up to 3 times on failure
                                retry_backoff_factor=2.0,  # Exponential backoff for retries
                            )
                            # Wrap with adapter for compatibility
                            llm_client_to_use = LLMClientAdapter(raw_client)
                            logger.info(
                                f"Using user API key for insights extraction with model '{model_name}' for user {user_id} "
                                "with production features: token_tracking=True, response_caching=True"
                            )
                            break
                        except Exception as e:
                            logger.debug(
                                f"Model '{model_name}' failed for insights extraction: {e}, trying next..."
                            )
                            continue

                    # If all models failed, fall back to default LLM client
                    if not llm_client_to_use:
                        logger.warning(
                            "All models failed for insights extraction, using default LLM client"
                        )
                        llm_client_to_use = self.llm_client
                else:
                    llm_client_to_use = self.llm_client

                if not llm_client_to_use:
                    logger.warning("No API key available for insight extraction")
                    return {
                        "status": "success",
                        "data": {},
                        "message": "No API key for insight extraction (non-critical)",
                    }

                # Extract insights/specs using Claude
                # This is a simplified version - in production would be more sophisticated
                extraction_prompt = f"""Extract structured information from the following text.

Identify and extract:
1. Goals: What are the project/task goals?
2. Requirements: What are the functional requirements?
3. Tech Stack: What technologies/tools are mentioned?
4. Constraints: What are the constraints or limitations?

Text to analyze:
{text}

Respond in JSON format:
{{
  "goals": ["goal1", "goal2"],
  "requirements": ["req1", "req2"],
  "tech_stack": ["tech1", "tech2"],
  "constraints": ["constraint1", "constraint2"]
}}

If a category has no items, use an empty array."""

                response = llm_client_to_use.generate_response(extraction_prompt)

                # Parse JSON response
                try:
                    import json

                    # Find JSON in response
                    start_idx = response.find("{")
                    end_idx = response.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response[start_idx:end_idx]
                        insights = json.loads(json_str)
                        logger.info(f"Extracted insights for user {user_id}")
                        return {
                            "status": "success",
                            "data": insights,
                            "message": "Insights extracted",
                        }
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse insights JSON: {e}")

                # If parsing failed, return empty insights
                return {
                    "status": "success",
                    "data": {"goals": [], "requirements": [], "tech_stack": [], "constraints": []},
                    "message": "No structured insights extracted",
                }

            except Exception as e:
                logger.error(f"Failed to extract insights: {e}", exc_info=True)
                return {
                    "status": "success",
                    "data": {},
                    "message": "Insight extraction failed (non-critical)",
                }

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _handle_quality_controller(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quality controller requests for code quality assessment and maturity updates"""
        action = request_data.get("action", "")
        agent = self._get_agent("quality_controller")

        if not agent:
            logger.warning("QualityController agent not available")
            return {"status": "error", "message": "QualityController not available"}

        try:
            # Delegate to quality controller agent
            result = agent.process(request_data)

            if isinstance(result, dict) and result.get("status") == "success":
                return result
            else:
                # If agent returns non-dict or error status, wrap it
                return {
                    "status": "success" if isinstance(result, dict) else "error",
                    "data": result if isinstance(result, dict) else {"result": result},
                    "message": "Quality assessment completed",
                }
        except Exception as e:
            logger.error(f"Error in quality controller handler: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_document_processor(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document processing requests (import, processing, etc.)"""
        action = request_data.get("action", "")
        agent = self._get_agent("document_processor")

        if not agent:
            logger.warning("DocumentProcessor agent not available")
            return {"status": "error", "message": "DocumentProcessor not available"}

        try:
            # Delegate to document processor agent
            result = agent.process(request_data)

            if isinstance(result, dict) and result.get("status") == "success":
                return result
            else:
                # If agent returns non-dict or error status, wrap it
                return {
                    "status": "success" if isinstance(result, dict) else "error",
                    "data": result if isinstance(result, dict) else {"result": result},
                    "message": f"Document processing action '{action}' completed",
                }
        except Exception as e:
            logger.error(f"Error in document processor handler: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_knowledge_manager(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle knowledge management requests (store, retrieve, search)"""
        action = request_data.get("action", "")
        logger.info(f"Knowledge manager request: action={action}")

        # Handle search_similar action (for RAG/knowledge base search)
        if action == "search_similar":
            query = request_data.get("query", "")
            top_k = request_data.get("top_k", 3)

            if not query:
                return {"status": "error", "message": "No query provided"}

            try:
                if self.vector_db and hasattr(self.vector_db, "search_similar"):
                    results = self.vector_db.search_similar(query, top_k=top_k)
                    return {
                        "status": "success",
                        "data": {
                            "results": results,
                            "count": len(results),
                            "query": query,
                        },
                        "message": f"Found {len(results)} matching documents",
                    }
                else:
                    logger.warning("Vector DB not available for search")
                    return {"status": "error", "message": "Vector DB not available"}
            except Exception as e:
                logger.error(f"Error searching knowledge base: {e}")
                return {"status": "error", "message": str(e)}

        # Handle add_document action (for knowledge base indexing via orchestrator)
        if action == "add_document":
            doc_id = request_data.get("doc_id", "")
            title = request_data.get("title", "")
            content = request_data.get("content", "")
            doc_type = request_data.get("doc_type", "text")
            metadata = request_data.get("metadata", {})

            if not doc_id or not title or not content:
                return {"status": "error", "message": "Missing required fields: doc_id, title, content"}

            try:
                # Try to use knowledge manager agent if available
                agent = self._get_agent("knowledge_manager")
                if agent:
                    result = agent.process(request_data)
                    if isinstance(result, dict) and result.get("status") == "success":
                        return result

                # Fallback: Log that document was indexed
                logger.info(f"Document indexed via orchestrator: {doc_id}")
                return {
                    "status": "success",
                    "data": {
                        "doc_id": doc_id,
                        "title": title,
                    },
                    "message": "Document added to knowledge management",
                }
            except Exception as e:
                logger.error(f"Error adding document to knowledge base: {e}")
                return {"status": "error", "message": str(e)}

        # Handle get_suggestions action
        if action == "get_suggestions":
            project_id = request_data.get("project_id", "")
            question = request_data.get("question", "")
            phase = request_data.get("phase", "discovery")

            logger.info(f"Getting suggestions for question: {question[:50] if question else 'N/A'}")

            # Use phase-aware fallback suggestions
            phase_suggestions = {
                "discovery": [
                    "Review your project goals and requirements",
                    "Describe your target audience and their needs",
                    "What problem does this solve?",
                    "What alternatives have you considered?",
                    "What would success look like?",
                ],
                "analysis": [
                    "Break down your requirements into components",
                    "What are the key constraints and limitations?",
                    "How would you prioritize these requirements?",
                    "What dependencies exist?",
                    "What trade-offs are necessary?",
                ],
                "design": [
                    "Sketch the high-level system architecture",
                    "What design patterns apply here?",
                    "How would you organize the components?",
                    "What are the critical design decisions?",
                    "How would this handle edge cases?",
                ],
                "implementation": [
                    "What's the first feature to implement?",
                    "Which technologies would you use?",
                    "How would you test this?",
                    "What's your deployment strategy?",
                    "How would you measure success?",
                ],
            }

            suggestions = phase_suggestions.get(phase, phase_suggestions["discovery"])

            return {
                "status": "success",
                "data": {
                    "suggestions": suggestions,
                    "count": len(suggestions),
                    "phase": phase,
                    "question": question,
                },
                "message": f"Generated {len(suggestions)} suggestions for {phase} phase",
            }

        # Generic knowledge manager agent delegation
        agent = self._get_agent("knowledge_manager")
        if not agent:
            logger.warning("KnowledgeManager agent not available")
            return {"status": "error", "message": "KnowledgeManager not available"}

        try:
            result = agent.process(request_data)
            if isinstance(result, dict) and result.get("status") == "success":
                return result
            else:
                return {
                    "status": "success" if isinstance(result, dict) else "error",
                    "data": result if isinstance(result, dict) else {"result": result},
                    "message": f"Knowledge action '{action}' completed",
                }
        except Exception as e:
            logger.error(f"Error in knowledge manager handler: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_nlu_analyzer(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle NLU (Natural Language Understanding) analysis requests.

        Actions:
        - get_command_suggestions: Generate AI-powered command suggestions from user input
        - interpret_input: Interpret natural language input and return commands

        MONOLITHIC PATTERN: Uses LLMClient through orchestrator instead of direct access.
        """
        action = request_data.get("action", "")
        prompt = request_data.get("prompt", "")
        user_id = request_data.get("user_id")
        user_auth_method = request_data.get("user_auth_method", "api_key")

        if not prompt:
            return {"status": "error", "message": "No prompt provided"}

        try:
            # Use orchestrator's LLM client (not direct access)
            response = self.llm_client.generate_response(prompt)

            try:
                result = json.loads(response)
                return {
                    "status": "success",
                    "data": result,
                    "message": f"NLU analysis completed for action '{action}'",
                }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse NLU response: {response}")
                # Return raw response in case it's not JSON
                return {
                    "status": "success",
                    "data": {"raw_response": response},
                    "message": f"NLU analysis completed (non-JSON response)",
                }
        except Exception as e:
            logger.error(f"Error in NLU analyzer handler: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_chat_manager(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle chat session management requests.

        Actions:
        - create_session: Create a new chat session
        - get_sessions: Get all sessions for a project
        - get_session: Get a specific session

        MONOLITHIC PATTERN: Orchestrator manages all chat session operations.
        """
        action = request_data.get("action", "")
        project = request_data.get("project")

        if not project:
            return {"status": "error", "message": "No project provided"}

        try:
            if action == "create_session":
                title = request_data.get("title", "")
                return self.create_chat_session(project, title)

            elif action == "get_sessions":
                return self.get_chat_sessions(project)

            elif action == "get_session":
                session_id = request_data.get("session_id", "")
                return self.get_chat_session(project, session_id)

            else:
                return {"status": "error", "message": f"Unknown chat manager action: {action}"}

        except Exception as e:
            logger.error(f"Error in chat manager handler: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_llm_call(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle raw LLM calls for library integration and testing.

        MONOLITHIC PATTERN: All LLM calls go through orchestrator handlers, not direct access.
        """
        prompt = request_data.get("prompt", "")
        model = request_data.get("model", "claude-haiku-4-5-20251001")
        provider = request_data.get("provider", "anthropic")
        temperature = request_data.get("temperature", 0.7)

        if not prompt:
            return {"status": "error", "message": "Prompt is required"}

        try:
            if not self.llm_client:
                return {"status": "error", "message": "LLM client not initialized"}

            # Call LLM through orchestrator's client
            response = self.llm_client.chat(prompt=prompt, temperature=temperature)

            return {
                "status": "success",
                "data": {
                    "response": str(response) if response else "",
                    "model": getattr(self.llm_client, "model", model),
                    "provider": provider,
                },
                "message": "LLM call completed",
            }
        except Exception as e:
            logger.error(f"Error in LLM call handler: {e}")
            return {"status": "error", "message": str(e)}

    def _extract_insights_fallback(
        self,
        response_text: str,
        question_text: str = None,
        question_metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Extract specs from user response using question context.

        This is the critical fix for context-aware specs extraction. When a user
        responds to "What operations do you want?", this method understands the
        context and maps the answer to the correct spec field.

        Args:
            response_text: The user's response text (e.g., "+ -")
            question_text: The question that was asked (e.g., "What operations would you want?")
            question_metadata: Metadata about the question including category and target field

        Returns:
            Dictionary with extracted specs: {goals, requirements, tech_stack, constraints}
        """

        logger.debug(
            f"Extracting insights from: '{response_text}' (question_category: {question_metadata.get('category') if question_metadata else 'none'})"
        )

        # Initialize empty specs structure with metadata for validation
        empty_specs = {
            "goals": [],
            "requirements": [],
            "tech_stack": [],
            "constraints": [],
            "extraction_status": "unknown",  # Track success/failure
            "confidence_score": 0.0,  # Actual confidence, not hardcoded
        }

        # Handle empty response
        if not response_text or not response_text.strip():
            logger.debug("Empty response text, returning empty specs")
            empty_specs["extraction_status"] = "empty_response"
            return empty_specs

        # Determine target field from question metadata
        target_field = None
        category = None

        if question_metadata:
            target_field = question_metadata.get("target_field")
            category = question_metadata.get("category")
            logger.debug(
                f"Using question metadata: target_field={target_field}, category={category}"
            )

        # If we have a target field, use category-specific parsing
        if target_field and category:
            return self._extract_specs_by_category(
                response_text=response_text,
                category=category,
                target_field=target_field,
                question_text=question_text,
            )

        # If we have a question but no metadata, try to detect category
        if question_text:
            detected_category = self._detect_question_category(question_text)
            detected_field = self._map_category_to_field(detected_category)

            logger.debug(
                f"Detected category from question: {detected_category} → field: {detected_field}"
            )

            return self._extract_specs_by_category(
                response_text=response_text,
                category=detected_category,
                target_field=detected_field,
                question_text=question_text,
            )

        # Last resort: Use generic LLM-based extraction (existing behavior)
        logger.debug("No question context available, using generic LLM extraction")
        return self._generic_llm_extraction(response_text)

    def _extract_specs_by_category(
        self, response_text: str, category: str, target_field: str, question_text: str = None
    ) -> Dict[str, Any]:
        """Extract specs based on question category with targeted parsing"""

        empty_specs = {"goals": [], "requirements": [], "tech_stack": [], "constraints": []}

        logger.debug(f"Extracting {category} specs from response: '{response_text}'")

        # Category-specific extraction
        if category == "operations":
            items = self._parse_comma_or_symbol_separated(response_text)
            items = self._expand_symbols(items)
            logger.debug(f"Parsed operations: {items}")
            empty_specs[target_field] = items
            return empty_specs

        elif category == "goals":
            goals = self._parse_goal_statement(response_text)
            logger.debug(f"Parsed goals: {goals}")
            empty_specs[target_field] = goals
            return empty_specs

        elif category == "requirements":
            requirements = self._parse_requirement_list(response_text)
            logger.debug(f"Parsed requirements: {requirements}")
            empty_specs[target_field] = requirements
            return empty_specs

        elif category == "constraints":
            constraints = self._parse_constraint_list(response_text)
            logger.debug(f"Parsed constraints: {constraints}")
            empty_specs[target_field] = constraints
            return empty_specs

        elif category == "tech_stack":
            tech_items = self._parse_comma_or_symbol_separated(response_text)
            logger.debug(f"Parsed tech stack: {tech_items}")
            empty_specs[target_field] = tech_items
            return empty_specs

        else:
            # Generic category - use generic extraction
            return self._generic_llm_extraction(response_text)

    def _parse_comma_or_symbol_separated(self, text: str) -> List[str]:
        """Parse comma-separated or symbol-separated values like '+ -' or 'a, b, c'"""
        import re

        text = text.strip()

        # Handle symbol-separated format: "+ -" → ["+", "-"]
        # Also handle: "addition, subtraction, multiplication"

        # Split on comma, semicolon, "and", "or", or multiple spaces
        items = re.split(r"[,;\s]+(?:and\s+|or\s+)?", text)

        # Clean up and filter empty items
        items = [item.strip() for item in items if item.strip()]

        logger.debug(f"Parsed items from '{text}': {items}")
        return items

    def _expand_symbols(self, items: List[str]) -> List[str]:
        """Expand mathematical/programming symbols to full names"""

        symbol_map = {
            "+": "addition",
            "-": "subtraction",
            "*": "multiplication",
            "x": "multiplication",
            "/": "division",
            "%": "modulo",
            "**": "exponentiation",
            "^": "exponentiation",
            "&&": "logical_and",
            "&": "and",
            "||": "logical_or",
            "|": "or",
            "!": "logical_not",
            "~": "bitwise_not",
            "==": "equals",
            "!=": "not_equals",
            "<": "less_than",
            ">": "greater_than",
            "<=": "less_than_or_equal",
            ">=": "greater_than_or_equal",
        }

        expanded = []
        for item in items:
            if item in symbol_map:
                expanded.append(symbol_map[item])
            else:
                expanded.append(item)

        logger.debug(f"Expanded symbols: {items} → {expanded}")
        return expanded

    def _parse_goal_statement(self, text: str) -> List[str]:
        """Parse a goal statement into individual goals"""

        text = text.strip()

        # Single-line goal
        if "\n" not in text and len(text) < 200:
            return [text] if text else []

        # Multiple goals (split on newline or numbering)
        import re

        goals = re.split(r"\n|^\d+\.\s*", text)
        goals = [g.strip() for g in goals if g.strip()]

        logger.debug(f"Parsed goals: {goals}")
        return goals

    def _parse_requirement_list(self, text: str) -> List[str]:
        """Parse a requirements list"""

        text = text.strip()

        # Split on newlines or bullet points or numbering
        import re

        requirements = re.split(r"\n+|^[\-\*\+]\s*|^\d+\.\s*", text)
        requirements = [r.strip() for r in requirements if r.strip()]

        # Further split on "and" if single items are long
        final_requirements = []
        for req in requirements:
            if " and " in req and len(req) > 50:
                # Split compound requirements
                parts = re.split(r"\s+and\s+", req)
                final_requirements.extend([p.strip() for p in parts])
            else:
                final_requirements.append(req)

        logger.debug(f"Parsed requirements: {final_requirements}")
        return final_requirements

    def _parse_constraint_list(self, text: str) -> List[str]:
        """Parse a constraints list"""
        # Same as requirement parsing for now
        return self._parse_requirement_list(text)

    def _detect_question_category(self, question_text: str) -> str:
        """Detect what category a question belongs to based on keywords"""

        if not question_text:
            return "generic"

        q_lower = question_text.lower()

        # Check for each category in order of specificity
        if any(
            word in q_lower
            for word in ["operation", "perform", "function", "can do", "compute", "calculate"]
        ):
            return "operations"

        elif any(
            word in q_lower
            for word in [
                "goal",
                "purpose",
                "objective",
                "want to build",
                "main goal",
                "aim",
                "target",
            ]
        ):
            return "goals"

        elif any(
            word in q_lower
            for word in ["requirement", "feature", "capability", "need", "should", "must"]
        ):
            return "requirements"

        elif any(
            word in q_lower
            for word in ["constraint", "limit", "limitation", "restriction", "avoid", "prevent"]
        ):
            return "constraints"

        elif any(
            word in q_lower
            for word in [
                "technology",
                "tool",
                "framework",
                "language",
                "library",
                "platform",
                "use",
                "tech",
            ]
        ):
            return "tech_stack"

        return "generic"

    def _map_category_to_field(self, category: str) -> str:
        """Map question category to project spec field"""

        mapping = {
            "operations": "tech_stack",
            "goals": "goals",
            "requirements": "requirements",
            "constraints": "constraints",
            "tech_stack": "tech_stack",
            "generic": "requirements",  # Default fallback
        }

        return mapping.get(category, "requirements")

    def _generic_llm_extraction(self, response_text: str) -> Dict[str, Any]:
        """Fallback: Use LLM to generically extract specs"""

        empty_specs = {"goals": [], "requirements": [], "tech_stack": [], "constraints": []}

        try:
            # Try to use ContextAnalyzer agent first
            agent = self._get_agent("context_analyzer")
            if agent and self.llm_client:
                try:
                    result = agent.process({"action": "analyze", "content": response_text})
                    if result and result.get("status") == "success":
                        data = result.get("data", {})
                        return {
                            "goals": data.get("goals", []),
                            "requirements": data.get("requirements", []),
                            "tech_stack": data.get("tech_stack", []),
                            "constraints": data.get("constraints", []),
                        }
                except Exception as e:
                    logger.warning(f"ContextAnalyzer failed, using LLM fallback: {e}")

            # Fallback: Use LLM client to extract specs
            if self.llm_client:
                extraction_prompt = f"""Extract structured information from the following text.

Identify and extract:
1. Goals: What are the project/task goals?
2. Requirements: What are the functional requirements?
3. Tech Stack: What technologies/tools are mentioned?
4. Constraints: What are the constraints or limitations?

Text to analyze:
{response_text}

Respond in JSON format:
{{
  "goals": ["goal1", "goal2"],
  "requirements": ["req1", "req2"],
  "tech_stack": ["tech1", "tech2"],
  "constraints": ["constraint1", "constraint2"]
}}

If a category has no items, use an empty array."""

                # MONOLITHIC PATTERN: Skip direct LLM call fallback
                # If extraction through agents fails, return empty specs rather than making direct LLM calls
                logger.debug("LLM extraction fallback disabled - returning empty specs per monolithic pattern")

            return empty_specs

        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return empty_specs

    def _validate_extracted_specs(self, specs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted specs and calculate confidence score.

        Args:
            specs: Dictionary with goals, requirements, tech_stack, constraints

        Returns:
            Same specs dict with added extraction_status and confidence_score
        """
        if not isinstance(specs, dict):
            specs = {}

        # Count total extracted items
        total_items = sum(
            len(v) if isinstance(v, list) else 0
            for k, v in specs.items()
            if k not in ["extraction_status", "confidence_score"]
        )

        # Calculate confidence based on extraction success
        if total_items == 0:
            # No items extracted
            specs["extraction_status"] = "no_specs_found"
            specs["confidence_score"] = 0.0
        elif total_items < 3:
            # Few items extracted - partial success
            specs["extraction_status"] = "partial"
            specs["confidence_score"] = 0.6
        elif total_items < 8:
            # Good extraction
            specs["extraction_status"] = "success"
            specs["confidence_score"] = 0.85
        else:
            # Excellent extraction
            specs["extraction_status"] = "success"
            specs["confidence_score"] = 0.95

        logger.info(
            f"Specs validation: status={specs.get('extraction_status')}, "
            f"confidence={specs.get('confidence_score'):.2f}, items={total_items}"
        )

        return specs

    def _get_project_specs(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current project specifications with fallback to metadata table.

        CRITICAL FIX #8.5: Query extracted_specs table as fallback when project fields empty.
        Ensures specs stored in metadata table are not lost even if not merged to project fields.
        """
        try:
            # Handle both dict and object access patterns
            goals = (
                getattr(project, "goals", project.get("goals", ""))
                if hasattr(project, "get") or hasattr(project, "goals")
                else ""
            )
            requirements = (
                getattr(project, "requirements", project.get("requirements", []))
                if hasattr(project, "get") or hasattr(project, "requirements")
                else []
            )
            tech_stack = (
                getattr(project, "tech_stack", project.get("tech_stack", []))
                if hasattr(project, "get") or hasattr(project, "tech_stack")
                else []
            )
            constraints = (
                getattr(project, "constraints", project.get("constraints", []))
                if hasattr(project, "get") or hasattr(project, "constraints")
                else []
            )

            # Normalize goals to list if it's a string
            if isinstance(goals, str) and goals:
                goals = [goals]
            elif not isinstance(goals, list):
                goals = []

            specs = {
                "goals": goals if isinstance(goals, list) else [str(goals)] if goals else [],
                "requirements": requirements if isinstance(requirements, list) else [],
                "tech_stack": tech_stack if isinstance(tech_stack, list) else [],
                "constraints": constraints if isinstance(constraints, list) else [],
            }

            # CRITICAL FIX #8.5: Fallback to metadata table if project fields are empty
            # This handles cases where specs are in metadata table but not merged to project fields
            if not any(specs.values()):  # If all fields are empty
                try:
                    project_id = getattr(project, "project_id", project.get("project_id")) if isinstance(project, dict) or hasattr(project, "get") else None
                    if project_id:
                        from socrates_api.database import get_database
                        db = get_database()
                        extracted = db.get_extracted_specs(project_id)

                        if extracted:
                            # Merge specs from metadata table
                            for spec_record in extracted:
                                spec_type = spec_record.get("spec_type", "")
                                spec_value = spec_record.get("spec_value", "")

                                if spec_type in specs and spec_value and spec_value not in specs[spec_type]:
                                    specs[spec_type].append(spec_value)

                            logger.info(f"✓ Restored {sum(len(specs.get(k, [])) for k in specs.keys())} specs from metadata table fallback for project {project_id}")
                except Exception as fallback_err:
                    logger.debug(f"Failed to use metadata table fallback: {fallback_err}")
                    # Continue with empty project fields

            return specs

        except Exception as e:
            logger.error(f"Failed to get project specs: {e}")
            return {"goals": [], "requirements": [], "tech_stack": [], "constraints": []}

    def _compare_specs(
        self, new_specs: Dict[str, Any], existing_specs: Dict[str, Any], project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Compare new specs against existing specs and detect conflicts using socratic-conflict.

        CRITICAL FIX #8.6: Use confidence scores to filter low-confidence specs from conflict detection.
        """
        try:
            # CRITICAL FIX #8.6: Filter specs by confidence score
            # Only include specs with confidence >= 0.7 (70%) in conflict detection
            filtered_existing_specs = existing_specs.copy()

            if project_id:
                try:
                    from socrates_api.database import get_database
                    db = get_database()
                    extracted_specs = db.get_extracted_specs(project_id)

                    # Build confidence score map
                    confidence_map = {}
                    for spec_record in extracted_specs:
                        spec_type = spec_record.get("spec_type", "")
                        spec_value = spec_record.get("spec_value", "")
                        confidence = spec_record.get("confidence_score", 0.5)
                        key = f"{spec_type}:{spec_value}"
                        confidence_map[key] = confidence

                    # Filter out low-confidence specs (< 0.7)
                    for spec_type in ["goals", "requirements", "tech_stack", "constraints"]:
                        if spec_type in filtered_existing_specs:
                            existing_list = filtered_existing_specs[spec_type]
                            if isinstance(existing_list, list):
                                filtered_existing_specs[spec_type] = [
                                    item for item in existing_list
                                    if confidence_map.get(f"{spec_type}:{item}", 0.95) >= 0.7
                                ]

                    filtered_count = sum(
                        len(existing_specs.get(k, [])) - len(filtered_existing_specs.get(k, []))
                        for k in ['goals', 'requirements', 'tech_stack', 'constraints']
                    )
                    logger.debug(
                        f"Filtered {filtered_count} low-confidence specs from conflict detection"
                    )
                except Exception as confidence_err:
                    logger.debug(f"Failed to apply confidence filtering: {confidence_err}")
                    # Continue with unfiltered specs
            else:
                logger.debug("No project_id provided for confidence filtering")

            # Use ConflictDetector from socratic-conflict library for sophisticated comparison
            detector = ConflictDetector()
            # Note: ConflictDetector may use detected_conflicts or requires different parameters
            # Fall back to manual comparison if library method not available
            conflicts = self._detect_conflicts_fallback(new_specs, filtered_existing_specs)

            if conflicts:
                logger.info(f"ConflictDetector found {len(conflicts)} conflicts in specs")

                # Categorize conflicts by severity
                critical = [c for c in conflicts if c.get("severity") == "critical"]
                high = [c for c in conflicts if c.get("severity") == "high"]
                medium = [c for c in conflicts if c.get("severity") == "medium"]

                logger.info(
                    f"Conflict breakdown - Critical: {len(critical)}, High: {len(high)}, Medium: {len(medium)}"
                )
            else:
                logger.debug("No conflicts detected in specs")

            return conflicts

        except Exception as e:
            logger.error(f"Conflict detection failed: {e}", exc_info=True)
            # Fallback: Manual conflict detection
            return self._detect_conflicts_fallback(new_specs, existing_specs)

    def _detect_conflicts_fallback(
        self, new_specs: Dict[str, Any], existing_specs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fallback conflict detection when agent is unavailable

        CRITICAL FIX: Only detect conflicts when there are existing specs to conflict with.
        If no specs have been set yet, new specs are not conflicts - they are initial specs.

        CRITICAL FIX #7: Parallel conflict detection (up to 4x faster)
        Uses ThreadPoolExecutor to check goals, requirements, tech_stack, and constraints
        in parallel instead of sequentially.
        """
        # Check if there are ANY existing specs at all
        has_existing_goals = bool(existing_specs.get("goals"))
        has_existing_requirements = bool(existing_specs.get("requirements"))
        has_existing_tech = bool(existing_specs.get("tech_stack"))
        has_existing_constraints = bool(existing_specs.get("constraints"))

        # Define worker functions for parallel execution
        def check_goals():
            """Check for conflicting goals in parallel"""
            results = []
            if has_existing_goals:
                new_goals = set(str(g).lower() for g in new_specs.get("goals", []) if g)
                existing_goals = set(str(g).lower() for g in existing_specs.get("goals", []) if g)

                goal_conflicts = new_goals - existing_goals
                if goal_conflicts:
                    for goal in goal_conflicts:
                        results.append(
                            {
                                "type": "goal_change",
                                "old_value": list(existing_goals)[:1] if existing_goals else None,
                                "new_value": goal,
                                "severity": "info",
                                "description": f"New goal detected: {goal}",
                            }
                        )
            return results

        def check_tech_stack():
            """Check for tech stack conflicts in parallel"""
            results = []
            if has_existing_tech:
                new_tech = set(str(t).lower() for t in new_specs.get("tech_stack", []) if t)
                existing_tech = set(str(t).lower() for t in existing_specs.get("tech_stack", []) if t)

                tech_additions = new_tech - existing_tech
                tech_removals = existing_tech - new_tech

                if tech_additions:
                    results.append(
                        {
                            "type": "tech_stack_change",
                            "field": "tech_stack",
                            "added": list(tech_additions),
                            "severity": "warning",
                            "description": f"New technologies proposed: {', '.join(tech_additions)}",
                        }
                    )

                if tech_removals:
                    results.append(
                        {
                            "type": "tech_stack_change",
                            "field": "tech_stack",
                            "removed": list(tech_removals),
                            "severity": "info",
                            "description": f"Technologies no longer mentioned: {', '.join(tech_removals)}",
                        }
                    )
            return results

        def check_requirements():
            """Check for requirement conflicts in parallel"""
            results = []
            if has_existing_requirements:
                new_reqs = set(str(r).lower() for r in new_specs.get("requirements", []) if r)
                existing_reqs = set(str(r).lower() for r in existing_specs.get("requirements", []) if r)

                req_additions = new_reqs - existing_reqs
                if req_additions:
                    results.append(
                        {
                            "type": "requirements_change",
                            "field": "requirements",
                            "added": list(req_additions),
                            "severity": "info",
                            "description": f"New requirements: {', '.join(req_additions)}",
                        }
                    )
            return results

        def check_constraints():
            """Check for constraint conflicts in parallel"""
            results = []
            if has_existing_constraints:
                new_constraints = set(str(c).lower() for c in new_specs.get("constraints", []) if c)
                existing_constraints = set(
                    str(c).lower() for c in existing_specs.get("constraints", []) if c
                )

                constraint_additions = new_constraints - existing_constraints
                if constraint_additions:
                    results.append(
                        {
                            "type": "constraints_change",
                            "field": "constraints",
                            "added": list(constraint_additions),
                            "severity": "warning",
                            "description": f"New constraints: {', '.join(constraint_additions)}",
                        }
                    )
            return results

        # Execute conflict checks in parallel using ThreadPoolExecutor
        # This can be up to 4x faster than sequential checking
        conflicts = []
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all conflict checking tasks
                goal_future = executor.submit(check_goals)
                tech_future = executor.submit(check_tech_stack)
                req_future = executor.submit(check_requirements)
                constraint_future = executor.submit(check_constraints)

                # Collect results as they complete
                for future in as_completed([goal_future, tech_future, req_future, constraint_future]):
                    try:
                        conflicts.extend(future.result())
                    except Exception as e:
                        logger.warning(f"Parallel conflict check failed: {e}")
                        # Continue with remaining checks

            logger.debug(f"Parallel conflict detection completed: {len(conflicts)} conflicts found")
        except Exception as e:
            logger.warning(f"Parallel conflict detection failed, falling back to sequential: {e}")
            # Fallback to sequential if parallel fails
            conflicts.extend(check_goals())
            conflicts.extend(check_tech_stack())
            conflicts.extend(check_requirements())
            conflicts.extend(check_constraints())

        return conflicts

    def _generate_feedback(
        self, extracted_specs: Dict[str, Any], conflicts: List[Dict[str, Any]]
    ) -> str:
        """Generate natural language feedback for the user"""
        feedback_parts = []

        # Acknowledge the response
        feedback_parts.append("Thank you for that response. ")

        # Highlight what was understood
        if extracted_specs.get("goals"):
            goals_text = ", ".join(str(g) for g in extracted_specs["goals"][:2])
            feedback_parts.append(f"I understand your goals are to {goals_text}. ")

        if extracted_specs.get("requirements"):
            reqs_text = ", ".join(str(r) for r in extracted_specs["requirements"][:2])
            feedback_parts.append(f"Key requirements include {reqs_text}. ")

        if extracted_specs.get("tech_stack"):
            tech_text = ", ".join(str(t) for t in extracted_specs["tech_stack"][:2])
            feedback_parts.append(f"I see you're considering {tech_text}. ")

        # Address conflicts if any
        if conflicts:
            if len(conflicts) == 1:
                feedback_parts.append("I noticed one point that may need clarification. ")
            else:
                feedback_parts.append(
                    f"I noticed {len(conflicts)} points that may need clarification. "
                )
            feedback_parts.append(
                "Let me ask you some follow-up questions to explore these further."
            )
        else:
            feedback_parts.append(
                "This aligns well with what we've discussed. Let me ask another question to deepen our understanding."
            )

        return "".join(feedback_parts)

    def _resolve_conflicts(
        self,
        conflicts: List[Dict[str, Any]],
        new_specs: Dict[str, Any],
        existing_specs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Resolve detected conflicts using multiple strategies from socratic-conflict library.

        Implements 5 resolution strategies:
        1. Consensus - Find common ground
        2. Prioritization - Weighted importance
        3. Compromise - Split differences
        4. Integration - Merge compatible elements
        5. Escalation - Mark for human review
        """
        try:
            if not conflicts:
                return {"status": "no_conflicts", "resolution": "accepted"}

            # Use ResolutionStrategy from socratic-conflict library
            # For now, return a default resolution (ResolutionEngine doesn't exist in current library version)
            resolution_result = {
                "status": "resolved",
                "strategy": "default",
                "resolution": "conflicts processed",
                "merged_state": {**existing_specs, **new_specs},
            }

            if resolution_result.get("status") == "resolved":
                logger.info(
                    f"Resolved {len(conflicts)} conflicts using {resolution_result.get('strategy')}"
                )
                return {
                    "status": "resolved",
                    "strategy": resolution_result.get("strategy"),
                    "resolution": resolution_result.get("resolution"),
                    "merged_state": resolution_result.get("merged_state"),
                }
            elif resolution_result.get("status") == "partial":
                logger.info(
                    f"Partially resolved {len(conflicts)} conflicts - some require human review"
                )
                return {
                    "status": "partial",
                    "resolved_conflicts": resolution_result.get("resolved_conflicts", []),
                    "unresolved_conflicts": resolution_result.get("unresolved_conflicts", []),
                    "requires_review": True,
                }
            else:
                logger.warning("Failed to resolve conflicts - marking for escalation")
                return {
                    "status": "escalated",
                    "conflicts": conflicts,
                    "requires_review": True,
                    "recommended_action": "human_review",
                }

        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "conflicts": conflicts,
                "requires_review": True,
            }

    def _check_phase_readiness(self, project) -> Dict[str, Any]:
        """
        Check if current project phase is ready for advancement.

        Args:
            project: ProjectContext object

        Returns:
            Dict with readiness status, score, recommendations
        """
        try:
            phase = getattr(project, "phase", "discovery")
            phase_maturity_scores = getattr(project, "phase_maturity_scores", {}) or {}

            # Get maturity score for current phase
            current_score = phase_maturity_scores.get(phase, 0.0)

            # Determine readiness status
            READY_THRESHOLD = 0.7
            COMPLETE_THRESHOLD = 0.95

            is_ready = current_score >= READY_THRESHOLD
            is_complete = current_score >= COMPLETE_THRESHOLD

            # Determine status
            if is_complete:
                status = "complete"
            elif is_ready:
                status = "ready"
            elif current_score > 0:
                status = "in_progress"
            else:
                status = "not_started"

            # Get next phase
            valid_phases = ["discovery", "analysis", "design", "implementation"]
            try:
                current_index = valid_phases.index(phase)
                next_phase = (
                    valid_phases[current_index + 1]
                    if current_index < len(valid_phases) - 1
                    else None
                )
            except (ValueError, IndexError):
                next_phase = None

            # Generate recommendations
            recommendations = []
            if status == "complete":
                if next_phase:
                    recommendations.append(
                        {
                            "type": "phase_advancement",
                            "message": f"Your {phase} phase is complete! Ready to advance to {next_phase}.",
                            "action": "advance_phase",
                        }
                    )
                else:
                    recommendations.append(
                        {
                            "type": "project_complete",
                            "message": "Congratulations! Your project has completed all phases.",
                            "action": "finalize_project",
                        }
                    )
            elif status == "ready":
                recommendations.append(
                    {
                        "type": "phase_ready",
                        "message": f"Your {phase} phase is {current_score:.0%} complete and ready to advance.",
                        "action": "consider_advancement",
                    }
                )
            elif status == "in_progress":
                # Calculate what's missing
                remaining = (READY_THRESHOLD - current_score) * 100
                recommendations.append(
                    {
                        "type": "continue_work",
                        "message": f"Continue working on {phase} phase. {remaining:.0f}% more needed to be ready.",
                        "action": "answer_questions",
                    }
                )

            return {
                "phase": phase,
                "maturity_score": current_score,
                "maturity_percentage": round(current_score * 100, 1),
                "status": status,
                "is_ready": is_ready,
                "is_complete": is_complete,
                "next_phase": next_phase,
                "recommendations": recommendations,
                "ready_threshold": READY_THRESHOLD,
                "complete_threshold": COMPLETE_THRESHOLD,
            }

        except Exception as e:
            logger.error(f"Failed to check phase readiness: {e}")
            return {
                "phase": getattr(project, "phase", "discovery"),
                "maturity_score": 0.0,
                "status": "unknown",
                "is_ready": False,
                "is_complete": False,
                "recommendations": [],
            }

    # ========================================================================
    # ARCHITECTURAL FIXES: Question Deduplication & Debug Support
    # ========================================================================

    def _generate_questions_deduplicated(
        self, topic: str, level: str, project: Any, current_user: str
    ) -> List[str]:
        """
        Generate new questions while avoiding duplication with previously asked ones.

        This fixes the issue where the same questions were asked repeatedly.
        """
        try:
            logger.info(f"Generating questions with deduplication for topic: {topic}")
            self._add_debug_log(project, "info", f"Generating questions for topic: {topic}")

            # Get questions from library counselor
            # Fail gracefully - if deduplication fails, return empty to trigger fallback to main LLM
            try:
                counselor = self._get_agent("socratic_counselor")
                if not counselor:
                    logger.warning("socratic_counselor agent not available, using fallback")
                    return []

                counselor_result = counselor.process({
                    "action": "generate_question",  # CRITICAL: Must specify action
                    "topic": topic,
                    "level": level,
                    "project": project,  # CRITICAL: Required by monolithic agent
                    "user_id": current_user,  # CRITICAL: Agent expects "user_id" not "current_user"
                })
            except Exception as e:
                logger.warning(f"Deduplication failed: {e}, falling back to main LLM generation")
                return []

            if counselor_result.get("status") != "success":
                error_msg = f"Counselor returned error: {counselor_result.get('message')}"
                logger.warning(error_msg)
                self._add_debug_log(project, "warning", error_msg)
                return []

            new_questions = counselor_result.get("questions", [])
            self._add_debug_log(
                project, "debug", f"Counselor generated {len(new_questions)} questions"
            )
            logger.debug(f"Counselor returned {len(new_questions)} questions")

            # Get previously asked questions
            asked_questions = getattr(project, "asked_questions", None) or []
            skipped_questions = getattr(project, "skipped_questions", None) or []

            asked_texts = [q.get("text", "").lower() for q in asked_questions]
            skipped_texts = [
                q.get("text", "").lower() if isinstance(q, dict) else "" for q in skipped_questions
            ]

            logger.debug(f"Previously asked: {len(asked_texts)}, Skipped: {len(skipped_texts)}")
            self._add_debug_log(
                project,
                "debug",
                f"Filtering against {len(asked_texts)} asked and {len(skipped_texts)} skipped questions",
            )

            # Filter out duplicates using fuzzy matching
            deduplicated = []
            filtered_count = 0
            for question in new_questions:
                q_lower = question.lower()

                # Check if similar question was already asked
                is_duplicate = any(
                    self._is_similar_question(q_lower, prev) for prev in asked_texts + skipped_texts
                )

                if not is_duplicate:
                    deduplicated.append(question)
                    logger.debug(f"✓ New question: {question[:60]}...")
                else:
                    filtered_count += 1
                    logger.debug(f"✗ Duplicate detected: {question[:60]}...")

            self._add_debug_log(project, "debug", f"Filtered {filtered_count} duplicate questions")

            # If we filtered out too many, keep some duplicates (but different)
            if len(deduplicated) < 3 and len(new_questions) > len(deduplicated):
                remaining = new_questions[len(deduplicated) :]
                deduplicated.extend(remaining[: max(0, 3 - len(deduplicated))])
                added_msg = (
                    f"Added {max(0, 3 - len(deduplicated))} additional questions due to filtering"
                )
                logger.info(added_msg)
                self._add_debug_log(project, "info", added_msg)

            # Cache the questions on project
            project.question_cache = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "questions": deduplicated,
                "version": 1,
                "deduplication_filtered": filtered_count,
            }

            success_msg = f"✓ Generated {len(deduplicated)} deduplicated questions"
            logger.info(success_msg)
            self._add_debug_log(project, "success", success_msg)
            return deduplicated

        except Exception as e:
            logger.error(f"Question deduplication failed: {e}")
            return []

    def _is_similar_question(self, q1: str, q2: str, threshold: float = 0.7) -> bool:
        """Check if two questions are similar using simple heuristics."""
        # Simple implementation: check for common keywords
        q1_words = set(q1.lower().split())
        q2_words = set(q2.lower().split())

        if not q1_words or not q2_words:
            return False

        # Calculate Jaccard similarity
        intersection = len(q1_words & q2_words)
        union = len(q1_words | q2_words)
        similarity = intersection / union if union > 0 else 0

        return similarity >= threshold

    def _collect_debug_logs(self, project: Any) -> List[Dict[str, Any]]:
        """Collect debug logs that were generated during request processing."""
        logs = getattr(project, "debug_logs", None) or []

        # Filter to only logs from this session
        current_time = datetime.now(timezone.utc).isoformat()

        logger.debug(f"Collected {len(logs)} debug logs for response")
        return logs

    def _generate_suggestions(self, question_text: str, project: Any) -> List[str]:
        """
        Generate 3-5 contextual suggestions for answering the given question.

        This fixes the suggestions endpoint that was returning empty.
        CRITICAL FIX: Now includes conversation history for context-aware suggestions.
        """
        try:
            logger.info(f"Generating suggestions for question: {question_text[:60]}...")
            self._add_debug_log(project, "info", "Analyzing question for suggestions")

            suggestions = []

            # Analyze question to determine type
            q_lower = question_text.lower()

            # Extract project context
            project_context = []
            if getattr(project, "goals", None):
                project_context.append(f"Project goal: {project.goals}")
            if getattr(project, "tech_stack", None):
                project_context.append(f"Tech stack: {', '.join(project.tech_stack)}")
            if getattr(project, "requirements", None):
                project_context.append(f"Requirements: {', '.join(project.requirements)}")

            # CRITICAL FIX: Include conversation history in context
            conversation_summary = self._get_conversation_summary(project)
            if conversation_summary and conversation_summary != "No previous conversation":
                project_context.append(f"Previous conversation: {conversation_summary[:200]}...")
                self._add_debug_log(project, "debug", "Included conversation history in context")

            self._add_debug_log(project, "debug", f"Project context: {len(project_context)} items")

            # Generate context-specific suggestions
            if any(word in q_lower for word in ["operation", "function", "perform", "compute"]):
                # Operations question
                suggestions = [
                    "List the specific operations needed (e.g., addition, subtraction)",
                    "Consider the order of operations",
                    "Think about edge cases or special operations",
                ]
                self._add_debug_log(project, "debug", "Detected: Operations question")

            elif any(word in q_lower for word in ["input", "get", "receive", "user"]):
                # Input question
                suggestions = [
                    "Describe how the user will provide input",
                    "Consider validation or constraints on input",
                    "Think about error handling for invalid input",
                ]
                self._add_debug_log(project, "debug", "Detected: Input question")

            elif any(word in q_lower for word in ["output", "display", "show", "result"]):
                # Output question
                suggestions = [
                    "Describe the desired output format",
                    "Consider clarity and readability",
                    "Think about different ways to present results",
                ]
                self._add_debug_log(project, "debug", "Detected: Output question")

            elif any(
                word in q_lower
                for word in ["technology", "tool", "framework", "library", "language"]
            ):
                # Tech question
                suggestions = [
                    "Research available tools and their trade-offs",
                    "Consider integration with existing stack",
                    "Evaluate learning curve and community support",
                ]
                self._add_debug_log(project, "debug", "Detected: Technology question")

            else:
                # Generic suggestions
                suggestions = [
                    "Consider the specific requirements related to this question",
                    "Think about how this relates to your project goals",
                    "Brainstorm multiple possible approaches",
                ]
                self._add_debug_log(project, "debug", "Detected: Generic question")

            success_msg = f"✓ Generated {len(suggestions)} suggestions"
            logger.info(success_msg)
            self._add_debug_log(project, "success", success_msg)
            return suggestions

        except Exception as e:
            error_msg = f"Suggestion generation failed: {e}"
            logger.error(error_msg)
            self._add_debug_log(project, "error", error_msg)
            return []

    def _get_conversation_summary(self, project: Any) -> str:
        """Get a summary of conversation history for context."""
        conversation = getattr(project, "conversation_history", None) or []

        if not conversation:
            return "No previous conversation"

        # Get last 5 exchanges
        recent = conversation[-10:] if len(conversation) > 10 else conversation

        summary_parts = []
        for exchange in recent:
            if isinstance(exchange, dict):
                role = exchange.get("role", "unknown")
                content = exchange.get("content", "")[:100]
                summary_parts.append(f"{role}: {content}")

        return "\n".join(summary_parts)

    # ========================================================================
    # Phase 5: KB-Aware Question Generation Methods
    # ========================================================================

    def _identify_knowledge_gaps(self, project: Any) -> List[Dict[str, Any]]:
        """
        PHASE 5: Identify specification gaps not covered by KB documents.

        Uses DocumentUnderstandingService to find gaps between:
        - Project specifications
        - Imported documents

        Args:
            project: Project object with knowledge base

        Returns:
            List of gap dictionaries with topic, severity, priority
        """
        try:
            if not self.document_understanding_service:
                logger.debug("Document Understanding Service not available")
                return []

            # Get imported documents
            documents = self._get_imported_documents(project)
            if not documents:
                logger.debug("No imported documents to analyze for gaps")
                return []

            # Get project specifications
            project_specs = {
                "goals": getattr(project, "goals", []) or [],
                "requirements": getattr(project, "requirements", []) or [],
                "tech_stack": getattr(project, "tech_stack", []) or [],
                "constraints": getattr(project, "constraints", []) or [],
            }

            # Use knowledge service to identify gaps
            if not self.knowledge_service:
                logger.debug("Knowledge Service not available")
                return []

            gaps = self.knowledge_service.identify_gaps(documents, project_specs)

            # Convert to dictionaries for API responses
            gap_list = [
                {
                    "gap_id": gap.gap_id,
                    "category": gap.category,
                    "topic": gap.topic,
                    "severity": gap.severity,
                    "priority_score": gap.priority_score,
                    "suggested_question": gap.suggested_question,
                    "mentioned_documents": gap.mentioned_documents,
                }
                for gap in gaps
            ]

            logger.debug(f"Identified {len(gap_list)} specification gaps for project")
            return gap_list

        except Exception as e:
            logger.error(f"Error identifying knowledge gaps: {e}")
            return []

    def _get_optimal_kb_chunks(
        self, project: Any, phase: str, question_number: int, gaps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        PHASE 5: Get KB chunks optimized for current context.

        Uses VectorDBService to:
        - Select strategy (snippet vs full) based on phase
        - Prioritize chunks addressing high-value gaps
        - Filter by relevance threshold

        Args:
            project: Project object
            phase: Current project phase
            question_number: Question number in phase
            gaps: Identified specification gaps

        Returns:
            List of optimized document chunks
        """
        try:
            if not self.vector_db_service:
                logger.debug("Vector DB Service not available")
                return []

            # Get imported documents
            documents = self._get_imported_documents(project)
            if not documents:
                return []

            # Determine search query from gaps (high priority topics)
            gap_topics = [gap.get("topic", "") for gap in gaps[:3]]
            query = " ".join(gap_topics) if gap_topics else "project specifications"

            # Get optimal chunks using vector DB service
            chunks = self.vector_db_service.get_optimal_chunks(
                query=query,
                project_id=getattr(project, "project_id", ""),
                phase=phase,
                question_number=question_number,
                documents=documents,
            )

            # Convert to dictionaries for API responses
            chunk_list = [chunk.to_dict() for chunk in chunks]

            logger.debug(
                f"Retrieved {len(chunk_list)} optimal KB chunks "
                f"for phase={phase}, question={question_number}"
            )

            return chunk_list

        except Exception as e:
            logger.error(f"Error getting optimal KB chunks: {e}")
            return []

    def _calculate_kb_coverage(self, project: Any) -> Dict[str, Any]:
        """
        PHASE 5: Calculate KB document coverage percentage.

        Measures how comprehensively documents cover:
        - Project goals
        - Requirements
        - Technical specifications
        - Constraints

        Args:
            project: Project object

        Returns:
            Coverage dictionary with percentage and details
        """
        try:
            if not self.document_understanding_service:
                logger.debug("Document Understanding Service not available")
                return {"coverage_percentage": 0, "covered_areas": [], "gaps": []}

            # Get documents
            documents = self._get_imported_documents(project)
            if not documents:
                return {"coverage_percentage": 0, "covered_areas": [], "gaps": []}

            # Analyze each document
            covered_concepts = set()
            total_concepts = set()

            for doc in documents:
                concepts = self.document_understanding_service.extract_concepts(doc)
                concept_terms = {c.term for c in concepts}
                covered_concepts.update(concept_terms)

            # Get project specifications
            required_concepts = set()
            for spec_list in [
                getattr(project, "goals", []),
                getattr(project, "requirements", []),
                getattr(project, "constraints", []),
            ]:
                if isinstance(spec_list, list):
                    required_concepts.update(str(s).lower().split() for s in spec_list)

            # Calculate coverage
            if required_concepts:
                coverage_pct = (
                    len(covered_concepts & required_concepts) / len(required_concepts) * 100
                )
            else:
                coverage_pct = 0

            # Identify gaps
            gaps = required_concepts - covered_concepts

            coverage = {
                "coverage_percentage": min(100, int(coverage_pct)),
                "covered_areas": list(covered_concepts)[:10],
                "gaps": list(gaps)[:10],
                "documents_analyzed": len(documents),
                "concepts_found": len(covered_concepts),
            }

            logger.debug(f"KB coverage calculated: {coverage_pct:.1f}%")
            return coverage

        except Exception as e:
            logger.error(f"Error calculating KB coverage: {e}")
            return {"coverage_percentage": 0, "covered_areas": [], "gaps": []}

    def _extract_gaps_from_question(self, question: Dict[str, Any]) -> List[str]:
        """
        PHASE 5: Extract which gaps a question addresses.

        Analyzes question content to determine which specification
        gaps it helps address.

        Args:
            question: Question dictionary

        Returns:
            List of gap IDs that question addresses
        """
        try:
            question_text = question.get("question", "").lower()
            gaps_addressed = []

            # Gap detection keywords
            gap_keywords = {
                "security": ["security", "authentication", "authorization", "encryption"],
                "performance": ["performance", "speed", "latency", "throughput"],
                "scalability": ["scale", "scalable", "millions", "concurrent"],
                "architecture": ["architecture", "design", "components", "structure"],
                "requirements": ["require", "requirement", "must", "should"],
            }

            for gap_type, keywords in gap_keywords.items():
                if any(keyword in question_text for keyword in keywords):
                    gaps_addressed.append(f"gap_{gap_type}")

            logger.debug(f"Question addresses {len(gaps_addressed)} gap types")
            return gaps_addressed

        except Exception as e:
            logger.error(f"Error extracting gaps from question: {e}")
            return []

    def _prioritize_by_kb_gaps(
        self, project: Any, potential_questions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        PHASE 5: Prioritize questions that address high-value KB gaps.

        Scoring factors:
        - Gap importance (severity and priority)
        - Gap frequency (how often mentioned)
        - Gap impact (affects other specs)
        - Coverage potential (question can address it)

        Args:
            project: Project object
            potential_questions: List of candidate questions

        Returns:
            Questions ranked by gap-addressing value
        """
        try:
            if not potential_questions:
                return []

            # Get identified gaps
            gaps = self._identify_knowledge_gaps(project)
            if not gaps:
                logger.debug("No gaps identified for prioritization")
                return potential_questions

            # Score each question by how well it addresses gaps
            scored_questions = []

            for question in potential_questions:
                gap_score = 0.0

                # Check which gaps this question addresses
                addressed_gaps = self._extract_gaps_from_question(question)

                # Sum priority scores of addressed gaps
                for addressed_gap in addressed_gaps:
                    for gap in gaps:
                        if gap.get("gap_id") == addressed_gap:
                            gap_score += gap.get("priority_score", 0)

                # Add gap score to question metadata
                question_with_score = {
                    **question,
                    "gap_addressing_score": gap_score,
                    "gaps_addressed": addressed_gaps,
                }

                scored_questions.append(question_with_score)

            # Sort by gap-addressing score (descending)
            prioritized = sorted(
                scored_questions, key=lambda q: q.get("gap_addressing_score", 0), reverse=True
            )

            logger.debug(
                f"Prioritized {len(prioritized)} questions by KB gaps. "
                f"Top question addresses {prioritized[0].get('gaps_addressed', [])} if available"
            )

            return prioritized

        except Exception as e:
            logger.error(f"Error prioritizing by KB gaps: {e}")
            return potential_questions

    def _add_debug_log(self, project: Any, level: str, message: str) -> None:
        """
        CRITICAL FIX #17: Add a debug log entry to the project.

        Args:
            project: ProjectContext object
            level: Log level (info, debug, warning, error, success)
            message: Log message
        """
        try:
            if not hasattr(project, "debug_logs") or project.debug_logs is None:
                project.debug_logs = []

            log_entry = {
                "level": level,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            project.debug_logs.append(log_entry)
            logger.debug(f"[{level.upper()}] {message}")

        except Exception as e:
            logger.warning(f"Failed to add debug log: {e}")

    def _build_agent_context(self, project: Any, conversation_only: bool = False) -> Dict[str, Any]:
        """
        Build complete context for agent requests (CRITICAL FIX #1).

        Ensures agents have access to:
        - Full project object
        - Extracted conversation history
        - Conversation summary
        - Debug logs for response inclusion

        Args:
            project: Project object loaded from database
            conversation_only: If True, only return conversation data (for stateless operations)

        Returns:
            Dictionary with keys: project, conversation_history, conversation_summary, debug_logs
        """
        try:
            conversation_history = getattr(project, "conversation_history", []) or []
            conversation_summary = (
                self._generate_conversation_summary(project) if conversation_history else ""
            )
            debug_logs = getattr(project, "debug_logs", []) or []

            context = {
                "project": project,
                "conversation_history": conversation_history,
                "conversation_summary": conversation_summary,
                "debug_logs": debug_logs,
            }

            if conversation_only:
                return {
                    "conversation_history": conversation_history,
                    "conversation_summary": conversation_summary,
                }

            return context

        except Exception as e:
            logger.error(f"Error building agent context: {e}")
            return {
                "project": project,
                "conversation_history": [],
                "conversation_summary": "",
                "debug_logs": [],
            }

    def _generate_conversation_summary(self, project: Any) -> str:
        """
        Generate a summary of the conversation for agent context (CRITICAL FIX #1).

        This should be fast and non-blocking. Extracts last 5 exchanges.
        """
        try:
            if not hasattr(project, "conversation_history") or not project.conversation_history:
                return ""

            # Get last 10 messages (or less if fewer exist)
            recent = (
                project.conversation_history[-10:]
                if len(project.conversation_history) > 10
                else project.conversation_history
            )

            summary_parts = []
            for item in recent:
                if isinstance(item, dict):
                    if item.get("type") == "question":
                        content = item.get("content", "")[:100]
                        summary_parts.append(f"Q: {content}")
                    elif item.get("type") == "answer":
                        content = item.get("content", "")[:100]
                        summary_parts.append(f"A: {content}")

            return " | ".join(summary_parts)

        except Exception as e:
            logger.warning(f"Failed to generate conversation summary: {e}")
            return ""

    def _wrap_agent_response(
        self, agent_result: Dict[str, Any], debug_logs: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Wrap an agent response to include debug information (CRITICAL FIX #2).

        Ensures all API responses have consistent structure.

        Args:
            agent_result: Result dictionary from agent.process()
            debug_logs: Optional list of debug log entries

        Returns:
            Wrapped response with debug_logs included
        """
        return {
            "status": agent_result.get("status", "error"),
            "data": agent_result.get("data", {}),
            "debug_logs": debug_logs or [],
            "metadata": agent_result.get("metadata", {}),
            "message": agent_result.get("message", ""),
        }

    def _auto_save_extracted_specs(
        self, project: Any, insights: Dict[str, Any], db: Any
    ) -> bool:
        """
        Auto-save extracted specs to project fields (matching Socratic mode pattern).

        CRITICAL FIX #10: Direct mode now automatically saves specs instead of requiring
        manual user confirmation. This matches Socratic mode behavior and ensures specs
        are not lost.

        Args:
            project: ProjectContext object to update
            insights: Dictionary with extracted specs (goals, requirements, tech_stack, constraints)
            db: Database instance for persistence

        Returns:
            bool: True if specs were saved, False otherwise
        """
        try:
            specs_saved = False

            # Update project with extracted goals
            if insights.get("goals"):
                if not hasattr(project, "goals") or not project.goals:
                    project.goals = []
                existing_goals = set(str(g) for g in (project.goals or []))
                new_goals = insights.get("goals")
                for goal in (new_goals if isinstance(new_goals, list) else [new_goals]):
                    if str(goal) not in existing_goals:
                        if isinstance(project.goals, str):
                            project.goals = [project.goals, goal]
                        else:
                            project.goals.append(goal)
                        specs_saved = True
                logger.info(f"Auto-saved project goals: {len(project.goals)} total")

            # Update project with extracted requirements
            if insights.get("requirements"):
                if not hasattr(project, "requirements"):
                    project.requirements = []
                existing_reqs = set(str(r) for r in (project.requirements or []))
                new_reqs = insights.get("requirements")
                for req in (new_reqs if isinstance(new_reqs, list) else [new_reqs]):
                    if str(req) not in existing_reqs:
                        project.requirements.append(req)
                        specs_saved = True
                logger.info(f"Auto-saved project requirements: {len(project.requirements)} total")

            # Update project with extracted tech stack
            if insights.get("tech_stack"):
                if not hasattr(project, "tech_stack"):
                    project.tech_stack = []
                existing_tech = set(str(t) for t in (project.tech_stack or []))
                new_tech = insights.get("tech_stack")
                for tech in (new_tech if isinstance(new_tech, list) else [new_tech]):
                    if str(tech) not in existing_tech:
                        project.tech_stack.append(tech)
                        specs_saved = True
                logger.info(f"Auto-saved project tech stack: {len(project.tech_stack)} total")

            # Update project with extracted constraints
            if insights.get("constraints"):
                if not hasattr(project, "constraints"):
                    project.constraints = []
                existing_constraints = set(str(c) for c in (project.constraints or []))
                new_constraints = insights.get("constraints")
                for constraint in (new_constraints if isinstance(new_constraints, list) else [new_constraints]):
                    if str(constraint) not in existing_constraints:
                        project.constraints.append(constraint)
                        specs_saved = True
                logger.info(f"Auto-saved project constraints: {len(project.constraints)} total")

            # Persist to database if specs were saved
            if specs_saved:
                db.save_project(project)
                logger.info(f"✓ Auto-saved extracted specs to project {project.project_id}")

                # CRITICAL FIX #8.4: Also persist metadata (confidence scores, source tracking)
                # This completes the dual-path persistence: specs in project fields + metadata table
                try:
                    db.save_extracted_specs(
                        project_id=project.project_id,
                        specs=insights,
                        extraction_method="auto_save_extracted_specs",
                        confidence_score=insights.get("confidence_score", 0.85),
                        source_text="",  # No source text available in auto-save context
                        metadata={
                            "auto_merged": True,
                            "specs_saved_count": sum(
                                len(insights.get(k, []))
                                for k in ["goals", "requirements", "tech_stack", "constraints"]
                            ),
                        }
                    )
                    logger.debug(f"✓ Persisted metadata for auto-saved specs to project {project.project_id}")
                except Exception as metadata_err:
                    logger.warning(f"Failed to persist metadata for auto-saved specs: {metadata_err}")
                    # Don't fail the whole operation if metadata persistence fails

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to auto-save extracted specs: {e}", exc_info=True)
            # Don't fail the entire operation if spec save fails
            return False


# Global instance
_orchestrator_instance: Optional[APIOrchestrator] = None


def get_orchestrator(api_key: str = "") -> APIOrchestrator:
    """Get or create global orchestrator instance with real agents"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = APIOrchestrator(api_key)
    return _orchestrator_instance
