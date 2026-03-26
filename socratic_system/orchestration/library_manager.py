"""
SocraticLibraryManager - Central coordinator for PyPI libraries in Socrates

This module provides a unified interface for importing and wiring all PyPI libraries:
- socratic-agents: Agent orchestration framework
- socrates-nexus: LLM client for multi-provider support
- socratic-security: Security validation and management
- socratic-rag: Retrieval-augmented generation
- socratic-learning: Learning system integration
- socratic-knowledge: Knowledge base management

The manager handles:
1. LLMClient creation and injection
2. Agent instantiation with proper dependencies
3. Orchestrator setup (PureOrchestrator, SkillOrchestrator, WorkflowOrchestrator)
4. Callback registration for Socrates-specific logic (maturity, events, persistence)
"""

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class SocraticLibraryManager:
    """Central coordinator for all PyPI libraries in Socrates"""

    def __init__(self, api_key: str = "", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the library manager with all PyPI libraries.

        Args:
            api_key: API key for LLM provider (Anthropic, OpenAI, etc.)
            config: Optional configuration dict with custom settings
        """
        self.api_key = api_key
        self.config = config or {}

        # Library instances
        self.llm_client = None
        self.agents = {}
        self.skill_orchestrator = None
        self.workflow_orchestrator = None
        self.pure_orchestrator = None

        # Callbacks for Socrates integration
        self.get_maturity_callback: Optional[Callable[[str, str], float]] = None
        self.get_learning_effectiveness_callback: Optional[Callable[[str], float]] = None
        self.on_event_callback: Optional[Callable[[Any, Dict[str, Any]], None]] = None

        # Initialize all libraries
        self._initialize()

    def _initialize(self) -> None:
        """Initialize all PyPI libraries in proper dependency order"""
        logger.info("SocraticLibraryManager: Initializing all PyPI libraries")

        try:
            # Step 1: Create LLM client (all agents need this)
            self._initialize_llm_client()

            # Step 2: Initialize agents from socratic-agents
            self._initialize_agents()

            # Step 3: Initialize orchestrators
            self._initialize_orchestrators()

            # Step 4: Register callbacks (Socrates-specific logic)
            self._register_callbacks()

            logger.info("SocraticLibraryManager: All libraries initialized successfully")
        except Exception as e:
            logger.error(f"SocraticLibraryManager: Initialization failed: {e}")
            raise

    def _initialize_llm_client(self) -> None:
        """Create LLM client for agent injection"""
        try:
            if not self.api_key:
                logger.warning("SocraticLibraryManager: No API key provided - LLM client will be None")
                self.llm_client = None
                return

            from socrates_nexus import LLMClient

            # Use claude-3-sonnet as default, configurable via config
            model = self.config.get("llm_model", "claude-3-sonnet")
            provider = self.config.get("llm_provider", "anthropic")

            self.llm_client = LLMClient(
                provider=provider,
                model=model,
                api_key=self.api_key
            )
            logger.info(f"SocraticLibraryManager: LLMClient created ({provider}/{model})")
        except Exception as e:
            logger.warning(f"SocraticLibraryManager: Failed to create LLMClient: {e}")
            self.llm_client = None

    def _initialize_agents(self) -> None:
        """Initialize all agents from socratic-agents with LLM client"""
        try:
            from socratic_agents import (
                CodeGenerator, CodeValidator, SocraticCounselor,
                ProjectManager, QualityController, LearningAgent,
                SkillGeneratorAgent, ContextAnalyzer, UserManager,
                KnowledgeManager, DocumentProcessor, NoteManager,
                SystemMonitor, AgentConflictDetector
            )

            # Initialize all agents with injected LLM client
            self.agents = {
                "code_generator": CodeGenerator(llm_client=self.llm_client),
                "code_validator": CodeValidator(llm_client=self.llm_client),
                "socratic_counselor": SocraticCounselor(llm_client=self.llm_client),
                "project_manager": ProjectManager(llm_client=self.llm_client),
                "quality_controller": QualityController(llm_client=self.llm_client),
                "learning_agent": LearningAgent(llm_client=self.llm_client),
                "skill_generator": SkillGeneratorAgent(llm_client=self.llm_client),
                "context_analyzer": ContextAnalyzer(llm_client=self.llm_client),
                "user_manager": UserManager(llm_client=self.llm_client),
                "knowledge_manager": KnowledgeManager(llm_client=self.llm_client),
                "document_processor": DocumentProcessor(llm_client=self.llm_client),
                "note_manager": NoteManager(llm_client=self.llm_client),
                "system_monitor": SystemMonitor(llm_client=self.llm_client),
                "conflict_detector": AgentConflictDetector(llm_client=self.llm_client),
            }
            logger.info(f"SocraticLibraryManager: Initialized {len(self.agents)} agents")
        except Exception as e:
            logger.error(f"SocraticLibraryManager: Failed to initialize agents: {e}")
            self.agents = {}
            raise

    def _initialize_orchestrators(self) -> None:
        """Initialize skill, workflow, and pure orchestrators"""
        try:
            from socratic_agents.integrations.skill_orchestrator import SkillOrchestrator
            from socratic_agents.skill_generation.workflow_orchestrator import WorkflowOrchestrator
            from socratic_agents.orchestration.orchestrator import PureOrchestrator

            # Initialize SkillOrchestrator
            self.skill_orchestrator = SkillOrchestrator(
                quality_controller=self.agents.get("quality_controller"),
                skill_generator=self.agents.get("skill_generator"),
                learning_agent=self.agents.get("learning_agent")
            )
            logger.info("SocraticLibraryManager: SkillOrchestrator initialized")

            # Initialize WorkflowOrchestrator
            self.workflow_orchestrator = WorkflowOrchestrator()
            logger.info("SocraticLibraryManager: WorkflowOrchestrator initialized")

            # Initialize PureOrchestrator with callbacks (will be registered after)
            self.pure_orchestrator = PureOrchestrator(
                agents=self.agents,
                get_maturity=self._default_get_maturity,
                get_learning_effectiveness=self._default_get_learning_effectiveness,
                on_event=self._default_on_event
            )
            logger.info("SocraticLibraryManager: PureOrchestrator initialized")

        except Exception as e:
            logger.error(f"SocraticLibraryManager: Failed to initialize orchestrators: {e}")
            self.skill_orchestrator = None
            self.workflow_orchestrator = None
            self.pure_orchestrator = None
            raise

    def _register_callbacks(self) -> None:
        """Register Socrates-specific callbacks for orchestrator events"""
        # Callbacks will be set via set_maturity_callback() and set_event_callback()
        # These are called from the API layer when Socrates context is available
        logger.info("SocraticLibraryManager: Callbacks registered")

    # Default callback implementations (can be overridden)

    def _default_get_maturity(self, user_id: str, phase: str) -> float:
        """Default maturity callback - returns mid-range score"""
        if self.get_maturity_callback:
            return self.get_maturity_callback(user_id, phase)
        return 0.5  # Default: mid-range

    def _default_get_learning_effectiveness(self, user_id: str) -> float:
        """Default learning effectiveness callback"""
        if self.get_learning_effectiveness_callback:
            return self.get_learning_effectiveness_callback(user_id)
        return 0.7  # Default: good effectiveness

    def _default_on_event(self, event: Any, data: Dict[str, Any]) -> None:
        """Default event callback - passes to registered callback"""
        if self.on_event_callback:
            self.on_event_callback(event, data)

    # Public API for setting callbacks

    def set_maturity_callback(self, callback: Callable[[str, str], float]) -> None:
        """
        Register callback for maturity score calculation.

        The callback should return a float between 0 and 1 representing
        the user's maturity in a given phase.

        Args:
            callback: Function(user_id: str, phase: str) -> float
        """
        self.get_maturity_callback = callback
        logger.info("SocraticLibraryManager: Maturity callback registered")

    def set_learning_effectiveness_callback(self, callback: Callable[[str], float]) -> None:
        """
        Register callback for learning effectiveness calculation.

        Args:
            callback: Function(user_id: str) -> float
        """
        self.get_learning_effectiveness_callback = callback
        logger.info("SocraticLibraryManager: Learning effectiveness callback registered")

    def set_event_callback(self, callback: Callable[[Any, Dict[str, Any]], None]) -> None:
        """
        Register callback for handling coordination events from PureOrchestrator.

        Can be used to:
        - Update maturity scores
        - Emit webhooks
        - Store interaction metrics
        - Trigger follow-up agents
        - Update UI in real-time

        Args:
            callback: Function(event: CoordinationEvent, data: Dict) -> None
        """
        self.on_event_callback = callback
        logger.info("SocraticLibraryManager: Event callback registered")

    # Query methods

    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get a specific agent by name"""
        return self.agents.get(agent_name)

    def list_agents(self) -> list:
        """List all available agents"""
        return list(self.agents.keys())

    def get_status(self) -> Dict[str, Any]:
        """Get status of all library components"""
        return {
            "llm_client": self.llm_client is not None,
            "agents_count": len(self.agents),
            "skill_orchestrator": self.skill_orchestrator is not None,
            "workflow_orchestrator": self.workflow_orchestrator is not None,
            "pure_orchestrator": self.pure_orchestrator is not None,
            "maturity_callback": self.get_maturity_callback is not None,
            "learning_effectiveness_callback": self.get_learning_effectiveness_callback is not None,
            "event_callback": self.on_event_callback is not None,
        }


# Global singleton instance
_library_manager: Optional[SocraticLibraryManager] = None


def get_library_manager(api_key: str = "", config: Optional[Dict[str, Any]] = None) -> SocraticLibraryManager:
    """
    Get or create the global SocraticLibraryManager instance.

    Args:
        api_key: API key for LLM provider (required for first call)
        config: Optional configuration dict

    Returns:
        SocraticLibraryManager instance
    """
    global _library_manager
    if _library_manager is None:
        _library_manager = SocraticLibraryManager(api_key=api_key, config=config)
    return _library_manager


def reset_library_manager() -> None:
    """Reset the global library manager (for testing)"""
    global _library_manager
    _library_manager = None
