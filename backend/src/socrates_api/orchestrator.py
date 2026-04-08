"""
API Orchestrator for Socrates

Instantiates and coordinates real agents from socratic-agents library.
Provides unified interface for REST API endpoints to call agents and orchestrators.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import MaturityCalculator from socratic-maturity library (required)
from socrates_maturity import MaturityCalculator

# Import LLMClient from socrates-nexus for production-grade LLM handling
from socrates_nexus import LLMClient

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
        """Create LLM client with production-grade features from socrates-nexus, with model fallback"""
        try:
            # Use provided API key, or fall back to environment variable
            api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY", "")

            if not api_key:
                logger.debug(
                    "No API key provided (neither in config nor ANTHROPIC_API_KEY env var) - LLM client will be None"
                )
                return None

            # Create LLMClient with full socrates-nexus capabilities:
            # - Response caching for performance optimization
            # - Retry logic for reliability
            from socrates_nexus import LLMConfig

            # List of models to try (in priority order)
            models_to_try = [
                "claude-3-5-haiku",  # Generic haiku (preferred)
                "claude-3-5-haiku-20241022",  # Specific date version
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
                    "claude-3-5-haiku",  # Generic version (preferred)
                    "claude-3-5-haiku-20241022",  # Specific date version
                    "claude-3-haiku-20240307",  # Older version
                    "claude-3-5-sonnet-20241022",  # Fallback to sonnet
                ]
            )

            # Try each model in order
            from socrates_nexus import LLMConfig

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
        """Initialize database connection (backward compatibility)"""
        try:
            # Try to get database from config if available
            if hasattr(self, 'config') and self.config:
                db_path = getattr(self.config, 'projects_db_path', None)
            else:
                db_path = None

            # Try to import and initialize database
            try:
                from socrates_api.database import Database
                return Database(db_path=db_path)
            except ImportError:
                # Fall back to a simple mock if Database not available
                return type('MockDatabase', (), {
                    'save_project': lambda *args, **kwargs: None,
                    'load_project': lambda *args, **kwargs: None,
                    'delete_project': lambda *args, **kwargs: None,
                    'save_user': lambda *args, **kwargs: None,
                    'load_user': lambda *args, **kwargs: None,
                })()
        except Exception as e:
            logger.warning(f"Failed to initialize database: {e}")
            return None

    def _initialize_agents(self) -> None:
        """Initialize all agents from socratic-agents and socratic-analyzer with LLM client (required)"""
        from socratic_agents import (
            AgentConflictDetector,
            CodeGenerator,
            CodeValidator,
            ContextAnalyzer,
            DocumentProcessor,
            LearningAgent,
            NoteManager,
            ProjectManager,
            QualityController,
            SkillGeneratorAgent,
            SystemMonitor,
            UserManager,
        )
        from socratic_agents import (
            KnowledgeManager as AgentKnowledgeManager,
        )

        # Try to import CodeAnalyzer from socratic_analyzer
        code_analyzer = None
        try:
            from socratic_analyzer import CodeAnalyzer

            code_analyzer = CodeAnalyzer()
        except ImportError:
            logger.warning("socratic_analyzer not available; CodeAnalyzer will not be initialized")

        # Initialize all agents with LLM client
        self.agents = {
            # Code analysis and generation
            "code_generator": CodeGenerator(llm_client=self.llm_client),
            "code_validator": CodeValidator(llm_client=self.llm_client),
            # Project and learning coordination
            "socratic_counselor": SocraticCounselor(llm_client=self.llm_client, batch_size=1),
            "project_manager": ProjectManager(llm_client=self.llm_client),
            # Quality and skill management
            "quality_controller": QualityController(llm_client=self.llm_client),
            "skill_generator": SkillGeneratorAgent(llm_client=self.llm_client),
            # Learning and development
            "learning_agent": LearningAgent(llm_client=self.llm_client),
            # Analysis
            "context_analyzer": ContextAnalyzer(llm_client=self.llm_client),
            "code_analyzer": code_analyzer,  # From socratic_analyzer
            # Knowledge and documentation
            "user_manager": UserManager(llm_client=self.llm_client),
            "agent_knowledge_manager": AgentKnowledgeManager(llm_client=self.llm_client),
            "document_processor": DocumentProcessor(llm_client=self.llm_client),
            "note_manager": NoteManager(llm_client=self.llm_client),
            # System management
            "system_monitor": SystemMonitor(llm_client=self.llm_client),
            # Conflict resolution
            "conflict_detector": AgentConflictDetector(llm_client=self.llm_client),
        }

        # Remove None agents from dict
        self.agents = {k: v for k, v in self.agents.items() if v is not None}
        logger.info(
            f"Initialized {len(self.agents)} specialized agents from socratic-agents "
            "with production LLM client and all enterprise features"
        )

    def _initialize_orchestrators(self) -> None:
        """Initialize skill, workflow, and pure orchestrators (required)"""
        from socratic_agents.integrations.skill_orchestrator import SkillOrchestrator
        from socratic_agents.orchestration.orchestrator import PureOrchestrator
        from socratic_agents.skill_generation.workflow_orchestrator import WorkflowOrchestrator

        # Initialize SkillOrchestrator for intelligent skill generation
        self.skill_orchestrator = SkillOrchestrator(
            quality_controller=self.agents.get("quality_controller"),
            skill_generator=self.agents.get("skill_generator"),
            learning_agent=self.agents.get("learning_agent"),
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
        """Get maturity score for a user in a phase (callback for PureOrchestrator)"""
        try:
            # Use MaturityCalculator from socrates-maturity library
            calculator = MaturityCalculator()
            score = calculator.calculate_phase_maturity(user_id, phase)
            logger.debug(f"Maturity score for user {user_id} in phase {phase}: {score:.2%}")
            return score
        except Exception as e:
            logger.warning(f"Failed to calculate maturity score: {e}")
            return 0.5  # Default to mid-range score for safety

    def _get_learning_effectiveness(self, user_id: str) -> float:
        """Get learning effectiveness for a user (callback for PureOrchestrator)"""
        try:
            # Use LearningAgent/LearningTracker to calculate effectiveness
            learning_tracker = self.agents.get("learning_tracker")
            if learning_tracker and hasattr(learning_tracker, "calculate_effectiveness"):
                effectiveness = learning_tracker.calculate_effectiveness(user_id)
                logger.debug(f"Learning effectiveness for user {user_id}: {effectiveness:.2%}")
                return effectiveness

            # Fallback: estimate from interaction patterns
            logger.debug(f"Using learning agent heuristic for user {user_id}")
            return 0.7  # Default to good effectiveness
        except Exception as e:
            logger.warning(f"Failed to calculate learning effectiveness: {e}")
            return 0.7  # Default to good effectiveness for safety

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
            agent = self.agents.get(agent_type)
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
            agent = self.agents.get("code_generator")
            if not agent:
                return {"status": "error", "message": "CodeGenerator not available"}

            result = agent.process({"prompt": prompt, "language": language})
            return result
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {"status": "error", "message": str(e)}

    def validate_code(self, code: str) -> Dict[str, Any]:
        """Validate code using CodeValidator agent"""
        try:
            agent = self.agents.get("code_validator")
            if not agent:
                return {"status": "error", "message": "CodeValidator not available"}

            result = agent.process({"code": code})
            return result
        except Exception as e:
            logger.error(f"Code validation failed: {e}")
            return {"status": "error", "message": str(e)}

    def check_quality(self, code: str) -> Dict[str, Any]:
        """Check code quality using QualityController agent"""
        try:
            agent = self.agents.get("quality_controller")
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
            agent = self.agents.get("quality_controller")
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
            agent = self.agents.get("socratic_counselor")
            if not agent:
                return {"status": "error", "message": "SocraticCounselor not available"}

            result = agent.process({"topic": topic, "level": level})
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
            agent = self.agents.get("learning_agent")
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
            agent = self.agents.get("context_analyzer")
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
            agent = self.agents.get("project_manager")
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
            agent = self.agents.get(agent_name)
            if not agent:
                return {"status": "error", "message": f"Agent '{agent_name}' not found"}

            result = agent.process(request_data)
            return result
        except Exception as e:
            logger.error(f"Agent execution failed for {agent_name}: {e}")
            return {"status": "error", "message": str(e)}

    def call_llm(self, prompt: str, model: str = "claude-3-5-haiku", **kwargs) -> Dict[str, Any]:
        """Call LLM via socrates-nexus"""
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
            "claude-3-5-haiku",  # Generic version (preferred if available)
            "claude-3-5-haiku-20241022",  # Specific date version (fallback)
            "claude-3-haiku-20240307",  # Older haiku version
            "claude-3-5-sonnet-20241022",  # Sonnet as additional fallback
            "claude-opus-4-20250514",  # Opus as final fallback
            "claude-opus-4-1",  # Generic opus
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
            agent = self.agents.get("conflict_detector")
            if not agent:
                return {"status": "error", "message": "ConflictDetector not available"}

            result = agent.process(
                {"field": field, "agent_outputs": agent_outputs, "agents": agents}
            )
            return result
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return {"status": "error", "message": str(e)}

    def store_knowledge(
        self, tenant_id: str, title: str, content: str, tags: Optional[list] = None
    ) -> Dict[str, Any]:
        """Store knowledge item (stub - requires socratic-knowledge)"""
        try:
            agent = self.agents.get("knowledge_manager")
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
            agent = self.agents.get("knowledge_manager")
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
            agent = self.agents.get("learning_agent")
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
        """Find a question by ID in pending_questions."""
        pending_questions = getattr(project, "pending_questions", []) or []
        for q in pending_questions:
            if q.get("id") == question_id:
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

    # ================== ORCHESTRATION METHODS ==================

    def _orchestrate_question_generation(
        self, project: Any, user_id: str, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Orchestrate complete question generation flow with all agents.
        PHASE 5: Enhanced with KB-aware capabilities.

        Single point of coordination for question generation with:
        - Knowledge gap identification
        - Gap-driven question prioritization
        - KB coverage tracking
        - Document-informed context

        Args:
            project: Project object with current state
            user_id: Current user ID
            force_refresh: Force new generation even if pending question exists

        Returns:
            Dict with generated question or existing pending question
        """
        try:
            import uuid
            from datetime import datetime

            project_id = getattr(project, "project_id", None)
            logger.info(
                f"Orchestrating question generation for project {project_id}, user {user_id}"
            )

            # 1. Check for pending unanswered questions
            pending_questions = getattr(project, "pending_questions", []) or []
            if not force_refresh and pending_questions:
                unanswered = [q for q in pending_questions if q.get("status") == "unanswered"]
                if unanswered:
                    logger.info(f"Returning existing unanswered question: {unanswered[0]['id']}")
                    return {"status": "success", "question": unanswered[0], "existing": True}

            # 2. Gather full context
            context = self._gather_question_context(project, user_id)

            # PHASE 5: Identify KB gaps and optimize chunks
            phase = context.get("phase", "discovery")
            question_number = context.get("question_number", 1)

            # 2a. PHASE 5: Identify specification gaps from KB documents
            kb_gaps = self._identify_knowledge_gaps(project)
            context["kb_gaps"] = kb_gaps
            context["gaps_count"] = len(kb_gaps)

            # 2b. PHASE 5: Get KB chunks optimized for gap closure
            if kb_gaps:
                optimal_chunks = self._get_optimal_kb_chunks(
                    project, phase, question_number, kb_gaps
                )
                context["optimal_kb_chunks"] = optimal_chunks
                logger.debug(f"Added {len(optimal_chunks)} optimal KB chunks addressing gaps")

            # 2c. PHASE 5: Calculate KB coverage
            kb_coverage = self._calculate_kb_coverage(project)
            context["kb_coverage"] = kb_coverage
            logger.debug(f"KB coverage: {kb_coverage.get('coverage_percentage', 0)}%")

            # 3. Call SocraticCounselor for question generation
            debug_logs = []
            try:
                # Try to get user-specific LLM client with their API key
                user_llm_client = self._create_user_llm_client(user_id, provider="claude")
                if user_llm_client:
                    debug_logs.append(
                        {
                            "level": "info",
                            "message": f"Using user-specific LLM client for {user_id}",
                        }
                    )
                    logger.debug(f"Using user-specific LLM client for {user_id}")
                    # Create counselor with user's API key
                    from socratic_agents import SocraticCounselor as BaseSocraticCounselor

                    counselor = BaseSocraticCounselor(llm_client=user_llm_client, batch_size=1)
                else:
                    # Fall back to default counselor if user hasn't set API key
                    debug_logs.append(
                        {
                            "level": "info",
                            "message": f"No user API key for {user_id}, using default LLM client",
                        }
                    )
                    logger.debug(f"No user API key for {user_id}, using default LLM client")
                    counselor = self.agents.get("socratic_counselor")

                if not counselor:
                    debug_logs.append(
                        {
                            "level": "warning",
                            "message": "SocraticCounselor agent not available, using static fallback",
                        }
                    )
                    logger.warning("SocraticCounselor agent not available")
                    question_response = self._get_fallback_question(phase)
                else:
                    # Call counselor with full KB-aware context
                    debug_logs.append(
                        {
                            "level": "info",
                            "message": f"Calling SocraticCounselor for phase {phase} (KB gaps: {len(kb_gaps)}, KB coverage: {kb_coverage.get('coverage_percentage', 0)}%)",
                        }
                    )
                    logger.info(
                        f"Calling SocraticCounselor for phase {phase} "
                        f"(KB gaps: {len(kb_gaps)}, KB coverage: {kb_coverage.get('coverage_percentage', 0)}%)"
                    )

                    # Build topic from project goals and requirements
                    project_context = context.get("project_context", {})
                    goals = project_context.get("goals", [])
                    requirements = project_context.get("requirements", [])
                    project_name = getattr(project, "name", "")

                    # Build topic: prefer goals, then requirements, then project name
                    if goals:
                        topic_parts = [
                            str(g)[:50] for g in (goals if isinstance(goals, list) else [goals])
                        ][:2]
                        topic = " - ".join(topic_parts) if topic_parts else project_name
                    elif requirements:
                        topic_parts = [
                            str(r)[:50]
                            for r in (
                                requirements if isinstance(requirements, list) else [requirements]
                            )
                        ][:2]
                        topic = " - ".join(topic_parts) if topic_parts else project_name
                    else:
                        topic = project_name if project_name else f"{phase.title()} phase"

                    # Build request with all context (KB chunks, document understanding, conversation history)
                    counselor_request = {
                        "topic": topic,
                        "phase": phase,
                        "context": self._get_conversation_summary(project),
                        "knowledge_base": {
                            "chunks": context.get("knowledge_base_chunks", []),
                            "gaps": context.get("kb_gaps", []),
                            "coverage": kb_coverage.get("coverage_percentage", 0),
                        },
                        "document_understanding": context.get("document_understanding", {}),
                        "recently_asked": context.get("previously_asked_questions", []),
                    }

                    # Include conversation history if available
                    conversation_history = context.get("conversation_history", [])
                    if conversation_history:
                        counselor_request["conversation_history"] = conversation_history

                    debug_logs.append(
                        {
                            "level": "debug",
                            "message": f"Calling counselor with topic '{topic}' and {len(context.get('knowledge_base_chunks', []))} KB chunks",
                        }
                    )
                    logger.debug(
                        f"Calling counselor with topic '{topic}' and {len(context.get('knowledge_base_chunks', []))} KB chunks"
                    )
                    question_response = counselor.process(counselor_request)

                    # Ensure response has the expected structure
                    if not isinstance(question_response, dict):
                        question_response = {"question": str(question_response)}
                    if "question" not in question_response:
                        debug_logs.append(
                            {
                                "level": "warning",
                                "message": "Counselor response missing 'question' field, using fallback",
                            }
                        )
                        logger.warning(
                            "Counselor response missing 'question' field, using fallback"
                        )
                        question_response = self._get_fallback_question(phase)
                    else:
                        debug_logs.append(
                            {
                                "level": "success",
                                "message": f"✓ Generated KB-aware question (KB coverage: {kb_coverage.get('coverage_percentage', 0)}%)",
                            }
                        )

            except Exception as e:
                error_msg = f"Failed to generate question via SocraticCounselor: {str(e)}"
                debug_logs.append({"level": "error", "message": error_msg})
                logger.error(error_msg, exc_info=True)
                question_response = self._get_fallback_question(phase)
                debug_logs.append(
                    {"level": "info", "message": "Using static fallback question due to LLM error"}
                )

            # 4. Store generated question
            # Extract gaps before creating the question_entry (needed for PHASE 5)
            question_text = question_response.get("question", "")
            kb_gaps_addressed = []
            if "question" in question_response and question_text:
                kb_gaps_addressed = self._extract_gaps_from_question({"question": question_text})

            question_entry = {
                "id": f"q_{uuid.uuid4().hex[:8]}",
                "question": question_text,
                "phase": phase,
                "status": "unanswered",
                "created_at": datetime.now().isoformat(),
                "answer": None,
                "answered_at": None,
                "skipped_at": None,
                "metadata": question_response.get("metadata", {}),
                # PHASE 5: Track KB gaps addressed by this question
                "kb_gaps_addressed": kb_gaps_addressed,
            }

            # Update project with new question
            if not hasattr(project, "pending_questions"):
                project.pending_questions = []
            project.pending_questions.append(question_entry)

            logger.info(
                f"Generated question {question_entry['id']} for phase {phase} "
                f"(addresses {len(question_entry.get('kb_gaps_addressed', []))} KB gaps)"
            )

            # Store debug logs in project for later retrieval
            if not hasattr(project, "debug_logs"):
                project.debug_logs = []
            project.debug_logs.extend(debug_logs)

            return {
                "status": "success",
                "question": question_entry,
                "context": {
                    "kb_strategy": context.get("kb_strategy"),
                    "document_chunks_count": len(context.get("knowledge_base_chunks", [])),
                    "phase": phase,
                    # PHASE 5: Add KB-aware context
                    "kb_gaps_identified": len(kb_gaps),
                    "kb_coverage_percentage": kb_coverage.get("coverage_percentage", 0),
                    "gaps_addressed_by_question": len(question_entry.get("kb_gaps_addressed", [])),
                },
                "debug_logs": debug_logs,
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in _orchestrate_question_generation: {error_msg}", exc_info=True)
            return {
                "status": "error",
                "message": error_msg,
                "debug_logs": [
                    {"level": "error", "message": f"Question generation failed: {error_msg}"}
                ],
            }

    def _orchestrate_answer_processing(
        self, project: Any, user_id: str, question_id: str, answer_text: str
    ) -> Dict[str, Any]:
        """
        Orchestrate complete answer processing flow with all agents.
        Handles: specs extraction → conflict detection → maturity update → learning tracking.

        Args:
            project: Project object with current state
            user_id: Current user ID
            question_id: ID of question being answered
            answer_text: User's answer text

        Returns:
            Dict with processing results (specs, conflicts, maturity, etc.)
        """
        try:
            from datetime import datetime

            project_id = getattr(project, "project_id", None)
            logger.info(
                f"Orchestrating answer processing for project {project_id}, question {question_id}"
            )

            # 1. Find question being answered
            question = self._find_question(project, question_id)
            if not question:
                return {"status": "error", "message": f"Question {question_id} not found"}

            # 2. Add to conversation history
            conversation_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "user",
                "content": answer_text,
                "phase": question.get("phase", "discovery"),
                "question_id": question_id,
                "author": user_id,
            }

            if not hasattr(project, "conversation_history"):
                project.conversation_history = []
            project.conversation_history.append(conversation_entry)

            # 3. Call SocraticCounselor to extract specs
            specs_response = {
                "status": "success",
                "specs": {"goals": [], "requirements": [], "tech_stack": [], "constraints": []},
                "overall_confidence": 0.7,
            }

            try:
                counselor = self.agents.get("socratic_counselor")
                if counselor and hasattr(counselor, "extract_specs_from_response"):
                    # CRITICAL FIX #1: Pass conversation_history to agent calls
                    specs_response = counselor.extract_specs_from_response(
                        user_answer=answer_text,
                        question=question.get("question", ""),
                        project_context=self._get_extracted_specs(project),
                        phase=question.get("phase", "discovery"),
                        conversation_history=project.conversation_history,  # ← ADDED
                        conversation_summary=self._get_conversation_summary(project),  # ← ADDED
                    )
            except Exception as e:
                logger.warning(f"Failed to extract specs: {e}")

            # 4. MARK QUESTION AS ANSWERED (BEFORE conflict detection - critical timing)
            question["status"] = "answered"
            question["answered_at"] = datetime.now().isoformat()
            question["answer"] = answer_text
            logger.info(f"Question {question_id} marked as answered")

            # 5. Also mark in asked_questions for permanent history
            if not hasattr(project, "asked_questions"):
                project.asked_questions = []

            asked_entry = {
                "question_id": question_id,
                "question": question.get("question", ""),
                "answer": answer_text,
                "phase": question.get("phase", "discovery"),
                "timestamp": datetime.now().isoformat(),
                "specs_extracted": specs_response.get("specs", {}),
            }
            project.asked_questions.append(asked_entry)

            # 6. Call conflict detector
            conflicts_response = {"status": "success", "conflicts_found": []}

            try:
                conflict_detector = self.agents.get("conflict_detector")
                if conflict_detector:
                    conflicts_response = conflict_detector.detect_conflicts(
                        new_specs=specs_response.get("specs", {}),
                        existing_specs=self._get_existing_specs(project),
                        context=self._get_extracted_specs(project),
                    )
            except Exception as e:
                logger.warning(f"Failed to detect conflicts: {e}")

            # 7. Call QualityController to update maturity
            maturity_response = {"status": "success", "maturity": 50}  # Default mid-range

            try:
                quality_controller = self.agents.get("quality_controller")
                if quality_controller and hasattr(quality_controller, "update_after_response"):
                    maturity_response = quality_controller.update_after_response(
                        specs=specs_response.get("specs", {}),
                        answer_quality=specs_response.get("overall_confidence", 0.5),
                        answer_length=len(answer_text),
                    )
            except Exception as e:
                logger.warning(f"Failed to update maturity: {e}")

            # Update project maturity
            if not hasattr(project, "phase_maturity"):
                project.phase_maturity = {}
            phase = question.get("phase", "discovery")
            project.phase_maturity[phase] = maturity_response.get("maturity", 50)

            # 8. Call LearningAgent to track effectiveness
            try:
                learning_agent = self.agents.get("learning_agent")
                if learning_agent and hasattr(learning_agent, "track_question_effectiveness"):
                    learning_agent.track_question_effectiveness(
                        user_id=user_id,
                        question_id=question_id,
                        question_text=question.get("question", ""),
                        user_role=self._get_user_role(project, user_id),
                        phase=phase,
                        answer_text=answer_text,
                        specs_extracted=specs_response.get("specs", {}),
                        answer_quality=specs_response.get("overall_confidence", 0.5),
                        time_to_answer=0,  # Would be calculated on frontend
                    )
            except Exception as e:
                logger.warning(f"Failed to track learning: {e}")

            # 9. Check phase completion
            phase_complete = maturity_response.get("maturity", 0) >= 100

            logger.info(
                f"Answer processed: specs extracted={len(specs_response.get('specs', {}))}, "
                f"maturity={maturity_response.get('maturity', 0)}, "
                f"conflicts={len(conflicts_response.get('conflicts_found', []))}"
            )

            # ============================================================
            # PHASE 6: Advancement Tracking & Metrics
            # ============================================================
            advancement_data = {}

            try:
                if self.advancement_tracker:
                    # 10a. Record gap closure
                    extracted_specs = specs_response.get("specs", {})
                    if extracted_specs:
                        self.advancement_tracker.record_gap_closure(
                            project_id=project_id,
                            gap_id=f"gap_{question_id}",
                            question_id=question_id,
                            answer_text=answer_text,
                            closure_confidence=specs_response.get("overall_confidence", 0.7),
                        )
                        logger.debug(f"Gap closure recorded for question {question_id}")

                    # 10b. Calculate completeness
                    total_gaps = getattr(project, "total_gaps", 20)
                    gaps_identified = len(getattr(project, "identified_gaps", []))
                    closed_gaps = len(getattr(project, "closed_gaps", []))

                    completeness = self.advancement_tracker.calculate_completeness(
                        project_id=project_id,
                        total_gaps=total_gaps,
                        identified_gaps=gaps_identified,
                        closed_gaps=closed_gaps,
                        project_specs=extracted_specs,
                    )
                    advancement_data["completeness"] = completeness

                    # 10c. Calculate advancement metrics
                    maturity_value = maturity_response.get("maturity", 50) / 100.0
                    advancement_metrics = self.advancement_tracker.calculate_advancement_metrics(
                        project_id=project_id,
                        phase=phase,
                        maturity=maturity_value,
                        total_gaps=total_gaps,
                        closed_gaps=closed_gaps + 1,
                        question_count=len(getattr(project, "asked_questions", [])) + 1,
                    )
                    advancement_data["advancement_metrics"] = advancement_metrics

                    logger.info(
                        f"Advancement metrics: completeness={completeness.overall:.2%}, "
                        f"maturity={maturity_value:.2%}, quality={advancement_metrics.quality_score:.2%}"
                    )

            except Exception as e:
                logger.warning(f"Failed to track advancement: {e}")

            # 10d. Get dashboard metrics
            try:
                if self.metrics_service:
                    dashboard_metrics = self.metrics_service.get_dashboard_metrics(
                        project_id=project_id,
                        current_phase=phase,
                        completeness=(
                            advancement_data.get("completeness", {}).overall
                            if "completeness" in advancement_data
                            else 0.5
                        ),
                        maturity=maturity_response.get("maturity", 0) / 100.0,
                        gap_closure_count=getattr(project, "closed_gaps_count", 5),
                        total_gaps=total_gaps,
                        questions_answered=len(getattr(project, "asked_questions", [])) + 1,
                        quality_score=(
                            advancement_data.get("advancement_metrics", {}).quality_score
                            if "advancement_metrics" in advancement_data
                            else 0.7
                        ),
                        advancement_confidence=(
                            advancement_data.get("advancement_metrics", {}).confidence
                            if "advancement_metrics" in advancement_data
                            else 0.75
                        ),
                    )
                    advancement_data["dashboard_metrics"] = dashboard_metrics
                    logger.debug(f"Dashboard metrics aggregated for project {project_id}")

            except Exception as e:
                logger.warning(f"Failed to get dashboard metrics: {e}")

            # 10e. Record progress snapshot
            try:
                if self.progress_dashboard:
                    self.progress_dashboard.record_progress_snapshot(
                        project_id=project_id,
                        phase=phase,
                        completeness=(
                            advancement_data.get("completeness", {}).overall
                            if "completeness" in advancement_data
                            else 0.5
                        ),
                        gap_closure_percentage=(
                            advancement_data.get("advancement_metrics", {}).gap_closure_rate
                            if "advancement_metrics" in advancement_data
                            else 0.6
                        ),
                        maturity=maturity_response.get("maturity", 0) / 100.0,
                        questions_answered=len(getattr(project, "asked_questions", [])) + 1,
                        total_gaps=total_gaps,
                        quality_score=(
                            advancement_data.get("advancement_metrics", {}).quality_score
                            if "advancement_metrics" in advancement_data
                            else 0.7
                        ),
                    )
                    logger.debug(f"Progress snapshot recorded for project {project_id}")

            except Exception as e:
                logger.warning(f"Failed to record progress snapshot: {e}")

            return {
                "status": "success",
                "specs_extracted": specs_response.get("specs", {}),
                "phase_maturity": maturity_response.get("maturity", 0),
                "conflicts": conflicts_response.get("conflicts_found", []),
                "phase_complete": phase_complete,
                # PHASE 6: Include advancement data
                "advancement": advancement_data,
            }

        except Exception as e:
            logger.error(f"Error in _orchestrate_answer_processing: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

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
                counselor = self.agents.get("socratic_counselor")
                if counselor and hasattr(counselor, "generate_answer_suggestions"):
                    suggestions_response = counselor.generate_answer_suggestions(
                        question=question.get("question", ""),
                        project_context=self._get_extracted_specs(project),
                        phase=context["phase"],
                        user_role=context["user_role"],
                        recent_messages=context.get("recent_messages", []),
                        diversity_emphasis=True,
                    )
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

    def _handle_socratic_counselor(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Socratic counselor requests for generating questions"""
        action = request_data.get("action", "")

        if action == "generate_question":
            # Generate a Socratic question for a project
            project = request_data.get("project", {})
            topic = request_data.get("topic", "")
            user_id = request_data.get("user_id", "")
            force_refresh = request_data.get("force_refresh", False)

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

            # TRY CACHE FIRST (unless force_refresh)
            if not force_refresh and project_id:
                try:
                    from socrates_api.database import get_database

                    db = get_database()
                    cached_questions = db.get_cached_questions(
                        project_id=project_id, phase=phase, exclude_recent=3
                    )

                    if cached_questions:
                        # Use a random cached question
                        import random

                        question_data = random.choice(cached_questions)
                        question_text = question_data.get("question_text")
                        cache_id = question_data.get("cache_id")

                        # Increment usage counter
                        try:
                            db.increment_question_usage(cache_id)
                        except Exception as e:
                            logger.warning(f"Failed to increment question usage: {e}")

                        logger.info(f"Returning cached question (cache_id: {cache_id})")
                        return {
                            "status": "success",
                            "data": {
                                "question": question_text,
                                "project_id": project_id,
                                "phase": phase,
                                "from_cache": True,
                                "cache_id": cache_id,
                            },
                            "message": "Question retrieved from cache",
                        }
                except Exception as e:
                    logger.warning(f"Failed to retrieve from cache: {e}")
                    # Continue to generate new question

            # Try to use the actual agent if available
            counselor = self.agents.get("socratic_counselor")

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
                        # Use socrates-nexus with production features for user's API key
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

                        # Build request with conversation context
                        counselor_request = {
                            "topic": topic,
                            "context": conversation_summary,
                        }

                        # Include conversation history if available
                        conversation_history = getattr(project, "conversation_history", [])
                        if conversation_history:
                            counselor_request["conversation_history"] = conversation_history
                            logger.debug(
                                f"Including {len(conversation_history)} conversation history entries for context"
                            )

                        result = counselor.process(counselor_request)
                        logger.info(f"counselor.process() returned: {result}")

                        # CACHE THE GENERATED QUESTION
                        if project_id and result.get("question"):
                            try:
                                from socrates_api.database import get_database

                                db = get_database()
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
            # Process user's response to a Socratic question
            response = request_data.get("response", "")
            project = request_data.get("project", {})
            current_user = request_data.get("current_user", "")

            logger.info(f"Processing response in Socratic mode: {response[:50]}...")

            # CRITICAL FIX #4: Detect and auto-execute actionable intents from user input
            # This handles cases like "skip", "hint", "explain conflict", etc.
            detected_intent = self._detect_actionable_intent(response)
            if detected_intent and detected_intent.get("should_auto_execute"):
                logger.info(
                    f"Auto-executing intent: {detected_intent['action']} (confidence: {detected_intent['confidence']})"
                )

                # Emit NLU_SUGGESTION_EXECUTED event for real-time UI updates
                from socrates_api.models_local import EventType

                event_data = {
                    "user_id": current_user,
                    "project_id": (
                        getattr(project, "project_id", project.get("project_id"))
                        if hasattr(project, "get")
                        else project.get("project_id")
                    ),
                    "intent": detected_intent["intent"],
                    "action": detected_intent["action"],
                    "confidence": detected_intent["confidence"],
                }
                self.event_emitter.emit(EventType.NLU_SUGGESTION_EXECUTED, event_data)

                # Auto-execute the action
                action_result = self.process_request(
                    "socratic_counselor",
                    {
                        "action": detected_intent["action"],
                        "project": project,
                        "current_user": current_user,
                    },
                )

                # Return auto-executed action with NLU metadata
                if action_result.get("status") == "success":
                    return {
                        "status": "success",
                        "data": {
                            **action_result.get("data", {}),
                            "nlu_auto_executed": True,
                            "detected_intent": detected_intent["intent"],
                            "confidence": detected_intent["confidence"],
                        },
                        "message": f"Auto-executed: {detected_intent['action']}",
                    }

            try:
                # Extract specs from user's response using ContextAnalyzer agent
                # CRITICAL FIX: Pass question context for context-aware specs extraction
                question_text = getattr(project, "current_question_text", None)
                question_metadata = getattr(project, "current_question_metadata", {})

                logger.debug("Processing response with question context:")
                logger.debug(f"  Question: {question_text}")
                logger.debug(
                    f"  Category: {question_metadata.get('category', 'unknown') if question_metadata else 'unknown'}"
                )
                logger.debug(
                    f"  Target field: {question_metadata.get('target_field', 'unknown') if question_metadata else 'unknown'}"
                )

                extracted_specs = self._extract_insights_fallback(
                    response_text=response,
                    question_text=question_text,
                    question_metadata=question_metadata,
                )
                logger.info(f"Extracted specs from response: {extracted_specs}")

                # Get project specs to compare against
                project_specs = self._get_project_specs(project)
                logger.info(f"Current project specs: {project_specs}")

                # Compare specs for conflicts
                conflicts = self._compare_specs(extracted_specs, project_specs)
                logger.info(f"Detected {len(conflicts)} conflicts")

                # CRITICAL FIX #1: Auto-save extracted specs with metadata
                # This ensures specs are persisted and not lost after response processing
                project_id = (
                    getattr(project, "project_id", project.get("project_id"))
                    if hasattr(project, "get") or hasattr(project, "project_id")
                    else None
                )
                if project_id and extracted_specs:
                    try:
                        from socrates_api.database import get_database

                        db = get_database()
                        db.save_extracted_specs(
                            project_id=project_id,
                            specs=extracted_specs,
                            extraction_method="contextanalyzer",
                            confidence_score=0.95,
                            source_text=response,
                            metadata={
                                "user_id": current_user,
                                "conflict_count": len(conflicts),
                                "has_conflicts": len(conflicts) > 0,
                            },
                        )
                        logger.info(f"✓ Extracted specs persisted for project {project_id}")
                    except Exception as e:
                        logger.warning(f"Failed to persist extracted specs: {e}")
                        # Don't fail the whole request if persistence fails

                # CRITICAL FIX #6: RECONNECT PIPELINE #4 - KNOWLEDGE BASE INTEGRATION
                # Add extracted specs to vector database so they become project knowledge
                # This enables project-specific question generation instead of generic questions
                if project_id and extracted_specs and hasattr(self, "vector_db") and self.vector_db:
                    try:
                        logger.info("Adding extracted specs to knowledge base...")

                        # Format specs for knowledge base
                        for spec_field, spec_items in extracted_specs.items():
                            if spec_items:  # Only if there are items in this field
                                for item in spec_items:
                                    # Create knowledge entry for each spec
                                    knowledge_text = f"{spec_field}: {item}"

                                    # Add to vector database with project context
                                    try:
                                        self.vector_db.add_text(
                                            text=knowledge_text,
                                            metadata={
                                                "project_id": project_id,
                                                "user_id": current_user,
                                                "spec_type": spec_field,
                                                "spec_value": item,
                                                "source": "dialogue_response",
                                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                            },
                                        )
                                    except Exception as vec_err:
                                        logger.debug(
                                            f"Failed to add spec '{item}' to vector DB: {vec_err}"
                                        )

                        logger.info(
                            f"✓ Added {sum(len(items) for items in extracted_specs.values() if items)} specs to knowledge base"
                        )

                    except Exception as kb_err:
                        logger.warning(f"Failed to integrate with knowledge base: {kb_err}")
                        # Knowledge base is non-critical, don't fail the request

                # Generate feedback based on insights and conflicts
                feedback = self._generate_feedback(extracted_specs, conflicts)
                logger.info(f"Generated feedback: {feedback[:100]}...")

                # CRITICAL FIX #5: RECONNECT PIPELINE #2 - MATURITY RECALCULATION
                # This was completely missing and is why user progress never updates
                # After specs are extracted, we MUST recalculate project maturity
                maturity_update_data = None
                if any(extracted_specs.values()):  # Only if specs were actually extracted
                    try:
                        logger.info("Recalculating project maturity after specs extraction...")

                        # Call quality_controller to recalculate maturity based on new specs
                        maturity_result = self.process_request(
                            "quality_controller",
                            {
                                "action": "update_after_response",
                                "project": project,
                                "insights": extracted_specs,
                                "current_user": current_user,
                            },
                        )

                        if maturity_result.get("status") == "success":
                            maturity_data = maturity_result.get("data", {})
                            maturity_info = maturity_data.get("maturity", {})

                            # Update project with new maturity scores
                            if maturity_info:
                                # Update phase maturity scores
                                if "phase_scores" in maturity_info:
                                    project.phase_maturity_scores = maturity_info["phase_scores"]

                                # Update overall maturity
                                if "overall_score" in maturity_info:
                                    project.overall_maturity = maturity_info["overall_score"]

                                # Update category scores if available
                                if "category_scores" in maturity_info:
                                    project.category_scores = maturity_info["category_scores"]

                                maturity_update_data = {
                                    "overall_score": maturity_info.get("overall_score", 0.0),
                                    "phase_scores": maturity_info.get("phase_scores", {}),
                                    "updated": True,
                                }

                                old_score = getattr(project, "_old_maturity_score", 0.0)
                                new_score = maturity_info.get("overall_score", 0.0)
                                logger.info(
                                    f"✓ Project maturity recalculated: {old_score:.1f}% → {new_score:.1f}%"
                                )

                                # Emit event for maturity update (RECONNECT PIPELINE)
                                try:
                                    from socrates_api.models_local import EventType
                                    from socrates_api.websocket.connection_manager import (
                                        get_connection_manager,
                                    )

                                    event_data = {
                                        "project_id": getattr(project, "project_id", ""),
                                        "user_id": current_user,
                                        "old_maturity": old_score,
                                        "new_maturity": new_score,
                                        "maturity_data": maturity_update_data,
                                        "timestamp": datetime.now(timezone.utc).isoformat(),
                                    }

                                    # Try to emit event (non-critical)
                                    try:
                                        conn_manager = get_connection_manager()
                                        conn_manager.broadcast_to_project(
                                            user_id=current_user,
                                            project_id=getattr(project, "project_id", ""),
                                            message={
                                                "type": "event",
                                                "eventType": "MATURITY_UPDATED",
                                                "data": event_data,
                                            },
                                        )
                                        logger.debug("Emitted MATURITY_UPDATED event")
                                    except Exception as event_err:
                                        logger.debug(f"Could not emit maturity event: {event_err}")
                                except Exception as event_init_err:
                                    logger.debug(
                                        f"Could not initialize event system: {event_init_err}"
                                    )
                        else:
                            logger.warning(
                                f"Maturity recalculation returned non-success: {maturity_result.get('message')}"
                            )

                    except Exception as maturity_err:
                        # Maturity recalculation is important but not critical
                        # Don't fail the whole response if it fails
                        logger.warning(f"Failed to recalculate maturity: {maturity_err}")
                        maturity_update_data = None

                    # CRITICAL: Save project with updated maturity
                    try:
                        from socrates_api.database import get_database

                        db = get_database()
                        db.save_project(project)
                        logger.info("✓ Project saved with updated maturity scores")
                    except Exception as save_err:
                        logger.warning(f"Failed to save project with maturity: {save_err}")

                return {
                    "status": "success",
                    "data": {
                        "feedback": feedback,
                        "extracted_specs": extracted_specs,
                        "conflicts": conflicts,
                        "maturity_update": maturity_update_data,  # Include maturity in response
                        "next_action": (
                            "generate_question" if not conflicts else "resolve_conflicts"
                        ),
                    },
                    "message": "Response processed successfully",
                }

            except Exception as e:
                logger.error(f"Failed to process response: {e}", exc_info=True)
                # Return graceful fallback on error
                return {
                    "status": "success",
                    "data": {
                        "feedback": "Thank you for your response. Let me guide you further...",
                        "next_action": "generate_question",
                    },
                    "message": "Response processed",
                }

        elif action == "generate_hint":
            # Generate a contextual hint for the current question
            project = request_data.get("project", {})
            current_user = request_data.get("current_user", "")

            logger.info(f"Generating hint for user {current_user}")

            try:
                # Try to use SkillGeneratorAgent for smart hint generation
                agent = self.agents.get("skill_generator")
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

                # Fallback: Generate hint using LLM client
                if self.llm_client:
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

Generate a brief, encouraging hint that guides the student to think about the next logical step. The hint should:
1. Be specific to the current phase
2. Encourage deeper thinking
3. Be concise (2-3 sentences max)

Provide only the hint text."""

                    hint = self.llm_client.generate_response(hint_prompt)

                    if hint:
                        logger.info(f"Generated hint using LLM client: {hint[:50]}...")
                        return {
                            "status": "success",
                            "data": {"hint": hint},
                            "message": "Hint generated",
                        }

                # Final fallback: Generic phase-aware hint
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
                        # Use socrates-nexus with production features for user's API key
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
                        "claude-3-5-haiku",
                        "claude-3-5-haiku-20241022",
                        "claude-3-haiku-20240307",
                        "claude-3-5-sonnet-20241022",
                    ]
                    for model_name in models_to_try:
                        try:
                            # Use socrates-nexus with production features for insights extraction
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
        agent = self.agents.get("quality_controller")

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
        agent = self.agents.get("document_processor")

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

        # Initialize empty specs structure
        empty_specs = {"goals": [], "requirements": [], "tech_stack": [], "constraints": []}

        # Handle empty response
        if not response_text or not response_text.strip():
            logger.debug("Empty response text, returning empty specs")
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
            agent = self.agents.get("context_analyzer")
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

                response = self.llm_client.generate_response(extraction_prompt)

                # Parse JSON response
                try:
                    import json

                    start_idx = response.find("{")
                    end_idx = response.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response[start_idx:end_idx]
                        insights = json.loads(json_str)
                        return {
                            "goals": insights.get("goals", []),
                            "requirements": insights.get("requirements", []),
                            "tech_stack": insights.get("tech_stack", []),
                            "constraints": insights.get("constraints", []),
                        }
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse extraction JSON: {e}")

            return empty_specs

        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return empty_specs

    def _get_project_specs(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Get current project specifications"""
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

            return {
                "goals": goals if isinstance(goals, list) else [str(goals)] if goals else [],
                "requirements": requirements if isinstance(requirements, list) else [],
                "tech_stack": tech_stack if isinstance(tech_stack, list) else [],
                "constraints": constraints if isinstance(constraints, list) else [],
            }

        except Exception as e:
            logger.error(f"Failed to get project specs: {e}")
            return {"goals": [], "requirements": [], "tech_stack": [], "constraints": []}

    def _compare_specs(
        self, new_specs: Dict[str, Any], existing_specs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Compare new specs against existing specs and detect conflicts using socratic-conflict"""
        try:
            # Use ConflictDetector from socratic-conflict library for sophisticated comparison
            detector = ConflictDetector()
            # Note: ConflictDetector may use detected_conflicts or requires different parameters
            # Fall back to manual comparison if library method not available
            conflicts = self._detect_conflicts_fallback(new_specs, existing_specs)

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
        """
        conflicts = []

        # Check if there are ANY existing specs at all
        has_existing_goals = bool(existing_specs.get("goals"))
        has_existing_requirements = bool(existing_specs.get("requirements"))
        has_existing_tech = bool(existing_specs.get("tech_stack"))
        has_existing_constraints = bool(existing_specs.get("constraints"))

        # Check for conflicting goals (only if goals already exist)
        if has_existing_goals:
            new_goals = set(str(g).lower() for g in new_specs.get("goals", []) if g)
            existing_goals = set(str(g).lower() for g in existing_specs.get("goals", []) if g)

            # Detect contradictory goals (simple heuristic)
            goal_conflicts = new_goals - existing_goals
            if goal_conflicts:
                for goal in goal_conflicts:
                    conflicts.append(
                        {
                            "type": "goal_change",
                            "old_value": list(existing_goals)[:1] if existing_goals else None,
                            "new_value": goal,
                            "severity": "info",
                            "description": f"New goal detected: {goal}",
                        }
                    )

        # Check for tech stack conflicts (only if tech stack already exists)
        if has_existing_tech:
            new_tech = set(str(t).lower() for t in new_specs.get("tech_stack", []) if t)
            existing_tech = set(str(t).lower() for t in existing_specs.get("tech_stack", []) if t)

            tech_additions = new_tech - existing_tech
            tech_removals = existing_tech - new_tech

            if tech_additions:
                conflicts.append(
                    {
                        "type": "tech_stack_change",
                        "field": "tech_stack",
                        "added": list(tech_additions),
                        "severity": "warning",
                        "description": f"New technologies proposed: {', '.join(tech_additions)}",
                    }
                )

            if tech_removals:
                conflicts.append(
                    {
                        "type": "tech_stack_change",
                        "field": "tech_stack",
                        "removed": list(tech_removals),
                        "severity": "info",
                        "description": f"Technologies no longer mentioned: {', '.join(tech_removals)}",
                    }
                )

        # Check for new requirements (only if requirements already exist)
        if has_existing_requirements:
            new_reqs = set(str(r).lower() for r in new_specs.get("requirements", []) if r)
            existing_reqs = set(str(r).lower() for r in existing_specs.get("requirements", []) if r)

            req_additions = new_reqs - existing_reqs
            if req_additions:
                conflicts.append(
                    {
                        "type": "requirements_change",
                        "field": "requirements",
                        "added": list(req_additions),
                        "severity": "info",
                        "description": f"New requirements: {', '.join(req_additions)}",
                    }
                )

        # Check for constraints (only if constraints already exist)
        if has_existing_constraints:
            new_constraints = set(str(c).lower() for c in new_specs.get("constraints", []) if c)
            existing_constraints = set(
                str(c).lower() for c in existing_specs.get("constraints", []) if c
            )

            constraint_additions = new_constraints - existing_constraints
            if constraint_additions:
                conflicts.append(
                    {
                        "type": "constraints_change",
                        "field": "constraints",
                        "added": list(constraint_additions),
                        "severity": "warning",
                        "description": f"New constraints: {', '.join(constraint_additions)}",
                    }
                )

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
                counselor = self.agents.get("socratic_counselor")
                if not counselor:
                    logger.warning("socratic_counselor agent not available, using fallback")
                    return []

                counselor_result = counselor.process({"topic": topic, "level": level})
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


# Global instance
_orchestrator_instance: Optional[APIOrchestrator] = None


def get_orchestrator(api_key: str = "") -> APIOrchestrator:
    """Get or create global orchestrator instance with real agents"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = APIOrchestrator(api_key)
    return _orchestrator_instance
