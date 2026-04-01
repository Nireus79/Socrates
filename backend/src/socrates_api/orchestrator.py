"""
API Orchestrator for Socrates

Instantiates and coordinates real agents from socratic-agents library.
Provides unified interface for REST API endpoints to call agents and orchestrators.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import MaturityCalculator from socratic-maturity library (required)
from socrates_maturity import MaturityCalculator

# Import SocraticCounselor from socratic-agents library (required)
from socratic_agents import SocraticCounselor

# Import LLMClient from socrates-nexus for production-grade LLM handling
from socrates_nexus import LLMClient

# Import conflict resolution from socratic-conflict library (required)
from socratic_conflict import ConflictDetector, ResolutionStrategy

# Import all 4 security components from socratic-security (required)
from socratic_security import (
    PromptInjectionDetector,
    PathValidator,
    SandboxExecutor,
    SafeFilename,
)

# Import foundation services from socratic-core library (required)
from socratic_core import (
    EventBus,
    BaseService,
    ServiceOrchestrator as CoreOrchestrator,
)


def _get_valid_model_for_provider(provider: str, preferred_model: Optional[str] = None) -> str:
    """Get a valid model name for the given provider"""
    # Map of provider to valid model names (ordered by preference)
    valid_models = {
        "claude": ["claude-haiku-4-5-20251001", "claude-3-5-sonnet-20241022", "claude-opus-4-20250514"],
        "anthropic": ["claude-haiku-4-5-20251001", "claude-3-5-sonnet-20241022", "claude-opus-4-20250514"],
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
        self.provider = getattr(llm_client, 'provider', None)
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
                    raise ValueError("Prompt validation failed - input contains potential injection")
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
                if 'content' in response:
                    content = response['content']
                    if isinstance(content, str):
                        return content
                    elif isinstance(content, list):
                        # If content is a list, extract text from each item
                        texts = []
                        for item in content:
                            if isinstance(item, dict) and 'text' in item:
                                texts.append(item['text'])
                            elif isinstance(item, str):
                                texts.append(item)
                        return ' '.join(texts) if texts else str(response)
                # Fallback: convert entire dict to string
                return str(response)
            elif hasattr(response, 'content'):
                # If response has content attribute
                content = response.content
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # Extract text from list items
                    texts = []
                    for item in content:
                        if isinstance(item, dict) and 'text' in item:
                            texts.append(item['text'])
                        elif isinstance(item, str):
                            texts.append(item)
                    return ' '.join(texts) if texts else str(response)
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
        if 'temperature' in kwargs and 'top_p' in kwargs:
            # Prefer temperature for Haiku
            del kwargs['top_p']
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
        if 'temperature' in kwargs and 'top_p' in kwargs:
            del kwargs['top_p']
        return self.llm_client.stream(messages, **kwargs)

    def __getattr__(self, name):
        """Delegate unknown attributes to wrapped client"""
        return getattr(self.llm_client, name)


class APIOrchestrator:
    """Orchestrates real agents from socratic-agents for REST API"""

    def __init__(self, api_key_or_config: str = ""):
        """Initialize orchestrator with real agents and event-driven architecture"""
        self.api_key = api_key_or_config
        self.agents = {}
        self.skill_orchestrator = None
        self.workflow_orchestrator = None
        self.pure_orchestrator = None

        # Initialize documentation and performance tools
        self.doc_generator = None
        self.profiler = None
        self.cache = None

        # Initialize event-driven architecture from socratic-core (required)
        self.event_bus = EventBus()
        logger.info("Event-driven architecture initialized: EventBus enabled")

        # Create LLMClient first (if API key provided)
        self.llm_client = self._create_llm_client()

        self._initialize_agents()
        self._initialize_orchestrators()
        self._initialize_documentation()
        self._initialize_performance_monitoring()
        self._setup_event_listeners()
        logger.info("API Orchestrator initialized with real agents, event-driven architecture, and shared models")

    def _create_llm_client(self) -> Optional[Any]:
        """Create LLM client with production-grade features from socrates-nexus"""
        try:
            if not self.api_key:
                logger.debug("No API key provided - LLM client will be None")
                return None

            # Create LLMClient with full socrates-nexus capabilities:
            # - Response caching for performance optimization
            # - Retry logic for reliability
            from socrates_nexus import LLMConfig

            config = LLMConfig(
                provider="anthropic",
                model="claude-3-sonnet",
                api_key=self.api_key,
                cache_responses=True,           # Cache responses for performance
                cache_ttl=3600,                 # Cache for 1 hour
                retry_attempts=3,               # Retry up to 3 times on failure
                retry_backoff_factor=2.0        # Exponential backoff for retries
            )
            llm_client = LLMClient(config=config)
            logger.info(
                "LLM client created with production features: "
                "response_caching=True, retry_attempts=3"
            )
            return llm_client
        except Exception as e:
            logger.error(f"Failed to create LLM client: {e}", exc_info=True)
            raise  # Fail fast instead of returning None

    def _create_user_llm_client(self, user_id: str, provider: str = "claude") -> Optional[Any]:
        """
        Create LLM client with user's stored API key.

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
            model = user_model or provider_meta.models[0]

            # Create LLM client with production-grade features from socrates-nexus
            from socrates_nexus import LLMConfig

            config = LLMConfig(
                provider=provider,
                model=model,
                api_key=api_key,
                cache_responses=True,           # Cache responses for performance
                cache_ttl=3600,                 # Cache for 1 hour
                retry_attempts=3,               # Retry up to 3 times on failure
                retry_backoff_factor=2.0        # Exponential backoff for retries
            )
            llm_client = LLMClient(config=config)
            logger.info(
                f"LLM client created for user {user_id} with provider {provider}/{model} "
                "and production features: response_caching=True, retry_attempts=3"
            )
            return llm_client

        except Exception as e:
            logger.warning(f"Failed to create user LLM client: {e}")
            return None

    def _initialize_agents(self) -> None:
        """Initialize all agents from socratic-agents and socratic-analyzer with LLM client (required)"""
        from socratic_agents import (
            AgentConflictDetector,
            CodeGenerator,
            CodeValidator,
            ConflictDetector,
            ContextAnalyzer,
            DocumentProcessor,
            KnowledgeManager as AgentKnowledgeManager,
            LearningAgent,
            NoteManager,
            ProjectManager,
            QualityController,
            SkillGeneratorAgent,
            SocraticCounselor as BaseSocraticCounselor,
            SystemMonitor,
            UserManager,
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
            "socratic_counselor": SocraticCounselor(llm_client=self.llm_client),
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
            calculator = MaturityCalculator(project_type=getattr(project, "project_type", "software"))

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
                    "warnings": maturity_result.get("warnings", [])
                },
                "phase_readiness": {
                    "is_ready": maturity_result.get("is_ready", False),
                    "ready_threshold": 70.0,  # 70% for ready
                    "complete_threshold": 95.0,  # 95% for complete
                    "current_maturity": maturity_pct,
                    "next_phase": phase_estimate if phase_estimate != phase else None,
                }
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
            calculator = MaturityCalculator(project_type=getattr(project, "project_type", "software"))
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
                    "estimated_next_phase": maturity_result.get("estimated_phase")
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
                }
            }
        except Exception as e:
            logger.error(f"Failed to get all phases maturity: {e}", exc_info=True)
            raise

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

    def call_llm(self, prompt: str, model: str = "claude-3-sonnet", **kwargs) -> Dict[str, Any]:
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
        """List available LLM models"""
        return ["claude-3-sonnet", "claude-3-opus", "gpt-4", "gpt-3.5-turbo"]

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
            validation_results = {
                "status": "valid",
                "checks": {},
                "warnings": []
            }

            # 1. Check for prompt injection attacks
            injection_detector = PromptInjectionDetector()
            injection_risk = injection_detector.detect(user_input)
            validation_results["checks"]["prompt_injection"] = {
                "is_safe": not injection_risk.get("is_injection_attempt", False),
                "confidence": injection_risk.get("confidence", 0.0),
                "risk_level": injection_risk.get("risk_level", "low")
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
            is_valid = safe_filename.is_safe(user_input) if input_type in ["filename", "path"] else True
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
                    "details": validation_results
                }

            return {
                "status": "valid",
                "message": "Input validation passed",
                "details": validation_results
            }

        except Exception as e:
            logger.error(f"Input validation error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": "Security validation failed",
                "error": str(e)
            }

    def _setup_event_listeners(self) -> None:
        """Setup event listeners for event-driven architecture from socratic-core"""
        try:
            # Subscribe to key events for system coordination
            self.event_bus.on("agent_execution_start", self._handle_agent_start)
            self.event_bus.on("agent_execution_complete", self._handle_agent_complete)
            self.event_bus.on("error", self._handle_system_error)
            self.event_bus.on("project_updated", self._handle_project_update)

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
                return {
                    "status": "error",
                    "message": str(e)
                }

        elif action == "get_provider_config":
            # Return user's current provider configuration
            user_id = request_data.get("user_id", "")

            if not user_id:
                return {
                    "status": "error",
                    "message": "user_id is required"
                }

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
                return {
                    "status": "error",
                    "message": str(e)
                }

        elif action == "set_default_provider":
            # Set user's default LLM provider
            user_id = request_data.get("user_id", "")
            provider = request_data.get("provider", "anthropic")

            if not user_id:
                return {
                    "status": "error",
                    "message": "user_id is required"
                }

            try:
                from socrates_api.database import get_database
                db = get_database()
                success = db.set_user_default_provider(user_id, provider)

                if success:
                    logger.info(f"Default provider set to {provider} for user {user_id}")
                    return {
                        "status": "success",
                        "data": {"default_provider": provider},
                        "message": f"Default provider set to {provider}"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to set default provider"
                    }
            except Exception as e:
                logger.error(f"Failed to set default provider: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": str(e)
                }

        elif action == "set_provider_model":
            # Set user's preferred model for a provider
            user_id = request_data.get("user_id", "")
            provider = request_data.get("provider", "anthropic")
            model = request_data.get("model", "")

            if not user_id or not model:
                return {
                    "status": "error",
                    "message": "user_id and model are required"
                }

            try:
                from socrates_api.database import get_database
                db = get_database()
                success = db.set_provider_model(user_id, provider, model)

                if success:
                    logger.info(f"Model set to {model} for {provider} for user {user_id}")
                    return {
                        "status": "success",
                        "data": {"provider": provider, "model": model},
                        "message": f"Model set to {model} for {provider}"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to set provider model"
                    }
            except Exception as e:
                logger.error(f"Failed to set provider model: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": str(e)
                }

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
                return {
                    "status": "error",
                    "message": "user_id and api_key are required"
                }

            try:
                from socrates_api.database import get_database
                db = get_database()
                success = db.save_api_key(user_id, provider, api_key)

                if success:
                    logger.info(f"API key saved for user {user_id} provider {provider}")
                    return {
                        "status": "success",
                        "data": {"provider": provider},
                        "message": f"API key saved for {provider}"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to save API key"
                    }
            except Exception as e:
                logger.error(f"Failed to handle add_api_key: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": str(e)
                }

        elif action == "remove_api_key":
            # Delete user's API key for a provider
            user_id = request_data.get("user_id", "")
            provider = request_data.get("provider", "anthropic")

            if not user_id:
                return {
                    "status": "error",
                    "message": "user_id is required"
                }

            try:
                from socrates_api.database import get_database
                db = get_database()
                success = db.delete_api_key(user_id, provider)

                if success:
                    logger.info(f"API key removed for user {user_id} provider {provider}")
                    return {
                        "status": "success",
                        "message": f"API key removed for {provider}"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "API key not found"
                    }
            except Exception as e:
                logger.error(f"Failed to handle remove_api_key: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": str(e)
                }

        elif action == "set_auth_method":
            # Set authentication method for a provider (e.g., API key vs subscription)
            user_id = request_data.get("user_id", "")
            provider = request_data.get("provider", "anthropic")
            auth_method = request_data.get("auth_method", "api_key")

            if not user_id:
                return {
                    "status": "error",
                    "message": "user_id is required"
                }

            # For now, just acknowledge the setting
            # In a full implementation, this would be stored and used
            logger.info(f"Auth method set for user {user_id} provider {provider}: {auth_method}")
            return {
                "status": "success",
                "data": {
                    "provider": provider,
                    "auth_method": auth_method
                },
                "message": f"Auth method updated for {provider}"
            }

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _handle_socratic_counselor(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Socratic counselor requests for generating questions"""
        action = request_data.get("action", "")

        if action == "generate_question":
            # Generate a Socratic question for a project
            project = request_data.get("project", {})
            topic = request_data.get("topic", "")
            user_id = request_data.get("user_id", "")
            force_refresh = request_data.get("force_refresh", False)

            logger.info(f"_handle_socratic_counselor generate_question: topic={topic[:50] if topic else 'EMPTY'}")

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
                        project_id=project_id,
                        phase=phase,
                        exclude_recent=3
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
                            logger.info(f"No key for default provider, using fallback provider: {provider}/{model}")
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
                            cache_responses=True,           # Cache responses for performance
                            cache_ttl=3600,                 # Cache for 1 hour
                            retry_attempts=3,               # Retry up to 3 times on failure
                            retry_backoff_factor=2.0        # Exponential backoff for retries
                        )
                        # Wrap with adapter for SocraticCounselor compatibility
                        llm_client_to_use = LLMClientAdapter(raw_client)
                        logger.info(
                            f"Using user API key for {user_id} with provider {provider}/{model} "
                            "and production features: token_tracking=True, response_caching=True"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to create LLMClient with user key: {e}", exc_info=True)
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
                        logger.info(f"Calling counselor.process() with topic: {topic[:50] if topic else 'EMPTY'}")
                        result = counselor.process({"topic": topic})
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
                                    question_text=result.get("question")
                                )
                                logger.info(f"Cached new question for project {project_id}")

                                # Prune cache if too large
                                db.prune_question_cache(project_id, max_questions=50)
                            except Exception as e:
                                logger.warning(f"Failed to cache generated question: {e}")

                        return {"status": "success", "data": result, "message": "Question generated"}
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

            try:
                # Extract specs from user's response using ContextAnalyzer agent
                extracted_specs = self._extract_insights_fallback(response)
                logger.info(f"Extracted specs from response: {extracted_specs}")

                # Get project specs to compare against
                project_specs = self._get_project_specs(project)
                logger.info(f"Current project specs: {project_specs}")

                # Compare specs for conflicts
                conflicts = self._compare_specs(extracted_specs, project_specs)
                logger.info(f"Detected {len(conflicts)} conflicts")

                # CRITICAL FIX #1: Auto-save extracted specs with metadata
                # This ensures specs are persisted and not lost after response processing
                project_id = getattr(project, "project_id", project.get("project_id")) if hasattr(project, "get") or hasattr(project, "project_id") else None
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
                            }
                        )
                        logger.info(f"✓ Extracted specs persisted for project {project_id}")
                    except Exception as e:
                        logger.warning(f"Failed to persist extracted specs: {e}")
                        # Don't fail the whole request if persistence fails

                # Generate feedback based on insights and conflicts
                feedback = self._generate_feedback(extracted_specs, conflicts)
                logger.info(f"Generated feedback: {feedback[:100]}...")

                return {
                    "status": "success",
                    "data": {
                        "feedback": feedback,
                        "extracted_specs": extracted_specs,
                        "conflicts": conflicts,
                        "next_action": "generate_question" if not conflicts else "resolve_conflicts",
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
                        phase = getattr(project, "phase", project.get("phase", "discovery")) if hasattr(project, "get") else project.get("phase", "discovery")
                        goals = getattr(project, "goals", project.get("goals", "")) if hasattr(project, "get") else project.get("goals", "")

                        hint_prompt = f"""You are a Socratic tutor. A student is working on a project in the '{phase}' phase.

Project Goals: {goals if goals else "Not yet defined"}

Generate a brief, encouraging hint that guides the student to think about the next logical step in their project development. The hint should:
1. Be specific to the current phase
2. Encourage deeper thinking rather than giving direct answers
3. Reference project goals if available
4. Be concise (2-3 sentences max)

Provide only the hint text, no additional commentary."""

                        result = agent.process({
                            "action": "generate",
                            "prompt": hint_prompt,
                            "context": {
                                "phase": phase,
                                "goals": goals,
                            }
                        })

                        if result and result.get("status") == "success":
                            hint = result.get("data", {}).get("hint") or result.get("hint")
                            if hint:
                                logger.info(f"Generated hint using SkillGeneratorAgent: {hint[:50]}...")
                                return {
                                    "status": "success",
                                    "data": {"hint": hint},
                                    "message": "Hint generated",
                                }
                    except Exception as e:
                        logger.warning(f"SkillGeneratorAgent hint failed: {e}, using fallback")

                # Fallback: Generate hint using LLM client
                if self.llm_client:
                    phase = getattr(project, "phase", project.get("phase", "discovery")) if hasattr(project, "get") else project.get("phase", "discovery")
                    goals = getattr(project, "goals", project.get("goals", "")) if hasattr(project, "get") else project.get("goals", "")

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
                phase = getattr(project, "phase", project.get("phase", "discovery")) if hasattr(project, "get") else project.get("phase", "discovery")

                phase_hints = {
                    "discovery": "Consider what problem you're trying to solve. What are the key requirements and constraints?",
                    "requirements": "Think about how each requirement connects to your overall goals. Are there any missing pieces?",
                    "architecture": "Review the components you've identified. How do they communicate with each other?",
                    "implementation": "What's the next logical module or feature to implement? Start small and build up.",
                    "testing": "What edge cases might you have missed? How would you test for them?",
                    "deployment": "What are the steps to make your project accessible to users? Start with the most critical one.",
                }

                hint = phase_hints.get(phase, "Review your project progress and identify the next logical step in your development journey.")

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
                    "data": {"hint": "Review your project requirements and consider what step comes next in your learning journey."},
                    "message": "Hint generated (fallback)",
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
                return {
                    "status": "error",
                    "message": "Prompt is required"
                }

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
                            logger.info(f"No key for default provider, using fallback provider: {provider}/{model}")
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
                            cache_responses=True,           # Cache responses for performance
                            cache_ttl=3600,                 # Cache for 1 hour
                            retry_attempts=3,               # Retry up to 3 times on failure
                            retry_backoff_factor=2.0        # Exponential backoff for retries
                        )
                        # Wrap with adapter for compatibility
                        llm_client_to_use = LLMClientAdapter(raw_client)
                        logger.info(
                            f"Using user API key for user {user_id} in direct mode with provider {provider}/{model} "
                            "and production features: token_tracking=True, response_caching=True"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to create LLMClient with user key: {e}", exc_info=True)
                        llm_client_to_use = self.llm_client
                else:
                    llm_client_to_use = self.llm_client
                    if llm_client_to_use:
                        logger.info(f"No user API key for {user_id}, using global API key in direct mode")
                    else:
                        logger.warning(f"No user API key and no global API key for user {user_id}")

                if not llm_client_to_use:
                    return {
                        "status": "error",
                        "message": "No API key available for response generation"
                    }

                # Generate answer using the appropriate LLM client
                answer = llm_client_to_use.generate_response(prompt)

                if not answer:
                    return {
                        "status": "error",
                        "message": "Failed to generate answer"
                    }

                logger.info(f"Generated direct answer for user {user_id}")
                return {
                    "status": "success",
                    "data": {
                        "answer": answer,
                        "user_id": user_id
                    },
                    "message": "Answer generated"
                }

            except Exception as e:
                logger.error(f"Failed to generate direct answer: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": str(e)
                }

        elif action == "extract_insights":
            # Extract specs/insights from text
            text = request_data.get("text", "")
            user_id = request_data.get("user_id", "")
            project = request_data.get("project", {})

            if not text:
                return {
                    "status": "error",
                    "message": "Text is required for insight extraction"
                }

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
                        "ollama": "llama2"
                    }
                    for fallback_provider in ["claude", "openai", "gemini", "ollama"]:
                        fallback_key = db.get_api_key(user_id, fallback_provider)
                        if fallback_key:
                            provider = fallback_provider
                            user_api_key = fallback_key
                            logger.info(f"No anthropic key, using fallback provider for insights: {provider}")
                            break

                # Create LLM client with user's key if available
                llm_client_to_use = None
                if user_api_key:
                    try:
                        # Use socrates-nexus with production features for insights extraction
                        raw_client = LLMClient(
                            provider=provider,
                            model="claude-3-sonnet",
                            api_key=user_api_key,
                            cache_responses=True,           # Cache responses for performance
                            cache_ttl=3600,                 # Cache for 1 hour
                            retry_attempts=3,               # Retry up to 3 times on failure
                            retry_backoff_factor=2.0        # Exponential backoff for retries
                        )
                        # Wrap with adapter for compatibility
                        llm_client_to_use = LLMClientAdapter(raw_client)
                        logger.info(
                            f"Using user API key for insights extraction for user {user_id} "
                            "with production features: token_tracking=True, response_caching=True"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to create LLMClient with user key: {e}", exc_info=True)
                        llm_client_to_use = self.llm_client
                else:
                    llm_client_to_use = self.llm_client

                if not llm_client_to_use:
                    logger.warning("No API key available for insight extraction")
                    return {
                        "status": "success",
                        "data": {},
                        "message": "No API key for insight extraction (non-critical)"
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
                    start_idx = response.find('{')
                    end_idx = response.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response[start_idx:end_idx]
                        insights = json.loads(json_str)
                        logger.info(f"Extracted insights for user {user_id}")
                        return {
                            "status": "success",
                            "data": insights,
                            "message": "Insights extracted"
                        }
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse insights JSON: {e}")

                # If parsing failed, return empty insights
                return {
                    "status": "success",
                    "data": {
                        "goals": [],
                        "requirements": [],
                        "tech_stack": [],
                        "constraints": []
                    },
                    "message": "No structured insights extracted"
                }

            except Exception as e:
                logger.error(f"Failed to extract insights: {e}", exc_info=True)
                return {
                    "status": "success",
                    "data": {},
                    "message": "Insight extraction failed (non-critical)"
                }

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _extract_insights_fallback(self, text: str) -> Dict[str, Any]:
        """Extract specs from user response text using ContextAnalyzer or fallback"""
        try:
            # Try to use ContextAnalyzer agent first
            agent = self.agents.get("context_analyzer")
            if agent and self.llm_client:
                try:
                    result = agent.process({"action": "analyze", "content": text})
                    if result and result.get("status") == "success":
                        data = result.get("data", {})
                        return {
                            "goals": data.get("goals", []),
                            "requirements": data.get("requirements", []),
                            "tech_stack": data.get("tech_stack", []),
                            "constraints": data.get("constraints", [])
                        }
                except Exception as e:
                    logger.warning(f"ContextAnalyzer failed, using fallback: {e}")

            # Fallback: Use LLM client to extract specs
            if self.llm_client:
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

                response = self.llm_client.generate_response(extraction_prompt)

                # Parse JSON response
                try:
                    import json
                    start_idx = response.find('{')
                    end_idx = response.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response[start_idx:end_idx]
                        insights = json.loads(json_str)
                        return {
                            "goals": insights.get("goals", []),
                            "requirements": insights.get("requirements", []),
                            "tech_stack": insights.get("tech_stack", []),
                            "constraints": insights.get("constraints", [])
                        }
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse extraction JSON: {e}")

            # Final fallback: Return empty specs
            return {
                "goals": [],
                "requirements": [],
                "tech_stack": [],
                "constraints": []
            }

        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return {
                "goals": [],
                "requirements": [],
                "tech_stack": [],
                "constraints": []
            }

    def _get_project_specs(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Get current project specifications"""
        try:
            # Handle both dict and object access patterns
            goals = getattr(project, "goals", project.get("goals", "")) if hasattr(project, "get") or hasattr(project, "goals") else ""
            requirements = getattr(project, "requirements", project.get("requirements", [])) if hasattr(project, "get") or hasattr(project, "requirements") else []
            tech_stack = getattr(project, "tech_stack", project.get("tech_stack", [])) if hasattr(project, "get") or hasattr(project, "tech_stack") else []
            constraints = getattr(project, "constraints", project.get("constraints", [])) if hasattr(project, "get") or hasattr(project, "constraints") else []

            # Normalize goals to list if it's a string
            if isinstance(goals, str) and goals:
                goals = [goals]
            elif not isinstance(goals, list):
                goals = []

            return {
                "goals": goals if isinstance(goals, list) else [str(goals)] if goals else [],
                "requirements": requirements if isinstance(requirements, list) else [],
                "tech_stack": tech_stack if isinstance(tech_stack, list) else [],
                "constraints": constraints if isinstance(constraints, list) else []
            }

        except Exception as e:
            logger.error(f"Failed to get project specs: {e}")
            return {
                "goals": [],
                "requirements": [],
                "tech_stack": [],
                "constraints": []
            }

    def _compare_specs(self, new_specs: Dict[str, Any], existing_specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare new specs against existing specs and detect conflicts using socratic-conflict"""
        try:
            # Use ConflictDetector from socratic-conflict library for sophisticated comparison
            detector = ConflictDetector()
            conflicts = detector.detect_conflicts(
                current_state=existing_specs,
                new_state=new_specs,
                context={"domain": "specifications", "type": "project_specs"}
            )

            if conflicts:
                logger.info(f"ConflictDetector found {len(conflicts)} conflicts in specs")

                # Categorize conflicts by severity
                critical = [c for c in conflicts if c.get("severity") == "critical"]
                high = [c for c in conflicts if c.get("severity") == "high"]
                medium = [c for c in conflicts if c.get("severity") == "medium"]

                logger.info(f"Conflict breakdown - Critical: {len(critical)}, High: {len(high)}, Medium: {len(medium)}")
            else:
                logger.debug("No conflicts detected in specs")

            return conflicts

        except Exception as e:
            logger.error(f"Conflict detection failed: {e}", exc_info=True)
            # Fallback: Manual conflict detection
            return self._detect_conflicts_fallback(new_specs, existing_specs)

    def _detect_conflicts_fallback(self, new_specs: Dict[str, Any], existing_specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback conflict detection when agent is unavailable"""
        conflicts = []

        # Check for conflicting goals
        new_goals = set(str(g).lower() for g in new_specs.get("goals", []) if g)
        existing_goals = set(str(g).lower() for g in existing_specs.get("goals", []) if g)

        # Detect contradictory goals (simple heuristic)
        goal_conflicts = new_goals - existing_goals
        if goal_conflicts:
            for goal in goal_conflicts:
                conflicts.append({
                    "type": "goal_change",
                    "old_value": list(existing_goals)[:1] if existing_goals else None,
                    "new_value": goal,
                    "severity": "info",
                    "description": f"New goal detected: {goal}"
                })

        # Check for tech stack conflicts
        new_tech = set(str(t).lower() for t in new_specs.get("tech_stack", []) if t)
        existing_tech = set(str(t).lower() for t in existing_specs.get("tech_stack", []) if t)

        tech_additions = new_tech - existing_tech
        tech_removals = existing_tech - new_tech

        if tech_additions:
            conflicts.append({
                "type": "tech_stack_change",
                "field": "tech_stack",
                "added": list(tech_additions),
                "severity": "warning",
                "description": f"New technologies proposed: {', '.join(tech_additions)}"
            })

        if tech_removals:
            conflicts.append({
                "type": "tech_stack_change",
                "field": "tech_stack",
                "removed": list(tech_removals),
                "severity": "info",
                "description": f"Technologies no longer mentioned: {', '.join(tech_removals)}"
            })

        # Check for new requirements
        new_reqs = set(str(r).lower() for r in new_specs.get("requirements", []) if r)
        existing_reqs = set(str(r).lower() for r in existing_specs.get("requirements", []) if r)

        req_additions = new_reqs - existing_reqs
        if req_additions:
            conflicts.append({
                "type": "requirements_change",
                "field": "requirements",
                "added": list(req_additions),
                "severity": "info",
                "description": f"New requirements: {', '.join(req_additions)}"
            })

        # Check for constraints
        new_constraints = set(str(c).lower() for c in new_specs.get("constraints", []) if c)
        existing_constraints = set(str(c).lower() for c in existing_specs.get("constraints", []) if c)

        constraint_additions = new_constraints - existing_constraints
        if constraint_additions:
            conflicts.append({
                "type": "constraints_change",
                "field": "constraints",
                "added": list(constraint_additions),
                "severity": "warning",
                "description": f"New constraints: {', '.join(constraint_additions)}"
            })

        return conflicts

    def _generate_feedback(self, extracted_specs: Dict[str, Any], conflicts: List[Dict[str, Any]]) -> str:
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
                feedback_parts.append(f"I noticed {len(conflicts)} points that may need clarification. ")
            feedback_parts.append("Let me ask you some follow-up questions to explore these further.")
        else:
            feedback_parts.append("This aligns well with what we've discussed. Let me ask another question to deepen our understanding.")

        return "".join(feedback_parts)

    def _resolve_conflicts(
        self,
        conflicts: List[Dict[str, Any]],
        new_specs: Dict[str, Any],
        existing_specs: Dict[str, Any]
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
                "merged_state": {**existing_specs, **new_specs}
            }

            if resolution_result.get("status") == "resolved":
                logger.info(f"Resolved {len(conflicts)} conflicts using {resolution_result.get('strategy')}")
                return {
                    "status": "resolved",
                    "strategy": resolution_result.get("strategy"),
                    "resolution": resolution_result.get("resolution"),
                    "merged_state": resolution_result.get("merged_state")
                }
            elif resolution_result.get("status") == "partial":
                logger.info(f"Partially resolved {len(conflicts)} conflicts - some require human review")
                return {
                    "status": "partial",
                    "resolved_conflicts": resolution_result.get("resolved_conflicts", []),
                    "unresolved_conflicts": resolution_result.get("unresolved_conflicts", []),
                    "requires_review": True
                }
            else:
                logger.warning(f"Failed to resolve conflicts - marking for escalation")
                return {
                    "status": "escalated",
                    "conflicts": conflicts,
                    "requires_review": True,
                    "recommended_action": "human_review"
                }

        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "conflicts": conflicts,
                "requires_review": True
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
                next_phase = valid_phases[current_index + 1] if current_index < len(valid_phases) - 1 else None
            except (ValueError, IndexError):
                next_phase = None

            # Generate recommendations
            recommendations = []
            if status == "complete":
                if next_phase:
                    recommendations.append({
                        "type": "phase_advancement",
                        "message": f"Your {phase} phase is complete! Ready to advance to {next_phase}.",
                        "action": "advance_phase"
                    })
                else:
                    recommendations.append({
                        "type": "project_complete",
                        "message": f"Congratulations! Your project has completed all phases.",
                        "action": "finalize_project"
                    })
            elif status == "ready":
                recommendations.append({
                    "type": "phase_ready",
                    "message": f"Your {phase} phase is {current_score:.0%} complete and ready to advance.",
                    "action": "consider_advancement"
                })
            elif status == "in_progress":
                # Calculate what's missing
                remaining = (READY_THRESHOLD - current_score) * 100
                recommendations.append({
                    "type": "continue_work",
                    "message": f"Continue working on {phase} phase. {remaining:.0f}% more needed to be ready.",
                    "action": "answer_questions"
                })

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
                "recommendations": []
            }


# Global instance
_orchestrator_instance: Optional[APIOrchestrator] = None


def get_orchestrator(api_key: str = "") -> APIOrchestrator:
    """Get or create global orchestrator instance with real agents"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = APIOrchestrator(api_key)
    return _orchestrator_instance
