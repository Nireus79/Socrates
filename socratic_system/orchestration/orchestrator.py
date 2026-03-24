"""
Agent Orchestrator for Socrates AI

Coordinates all agents and manages their interactions, including:
- Agent initialization
- Request routing
- Knowledge base management
- Database components
- Event emission for decoupled communication
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# socrates-nexus provides universal LLM client for multi-provider support
from socrates_nexus import LLMClient

try:
    from socratic_agents import (
        CodeGenerator as CodeGeneratorAgent,
    )
    from socratic_agents import (
        CodeValidator as CodeValidationAgent,
    )
    from socratic_agents import (
        ConflictDetector as ConflictDetectorAgent,
    )
    from socratic_agents import (
        ContextAnalyzer as ContextAnalyzerAgent,
    )
    from socratic_agents import (
        DocumentProcessor as DocumentProcessorAgent,
    )
    from socratic_agents import (
        KnowledgeAnalysis as KnowledgeAnalysisAgent,
    )
    from socratic_agents import (
        KnowledgeManager as KnowledgeManagerAgent,
    )
    from socratic_agents import (
        LearningAgent as UserLearningAgent,
    )
    from socratic_agents import (
        MultiLlmAgent as MultiLLMAgent,
    )
    from socratic_agents import (
        NoteManager as NoteManagerAgent,
    )
    from socratic_agents import (
        ProjectManager as ProjectManagerAgent,
    )
    from socratic_agents import (
        QualityController as QualityControllerAgent,
    )
    from socratic_agents import (
        QuestionQueueAgent,
    )
    from socratic_agents import (
        SocraticCounselor as SocraticCounselorAgent,
    )
    from socratic_agents import (
        SystemMonitor as SystemMonitorAgent,
    )
    from socratic_agents import (
        UserManager as UserManagerAgent,
    )
    from socratic_agents import (
        SkillGeneratorAgent,
    )
    from socratic_agents import (
        DocumentContextAnalyzer,
    )
    from socratic_agents import (
        GithubSyncHandler,
    )
except ImportError:
    # Fallback if socratic_agents is not installed
    CodeGeneratorAgent = None  # type: ignore
    CodeValidationAgent = None  # type: ignore
    ConflictDetectorAgent = None  # type: ignore
    ContextAnalyzerAgent = None  # type: ignore
    DocumentProcessorAgent = None  # type: ignore
    KnowledgeAnalysisAgent = None  # type: ignore
    KnowledgeManagerAgent = None  # type: ignore
    UserLearningAgent = None  # type: ignore
    MultiLLMAgent = None  # type: ignore
    NoteManagerAgent = None  # type: ignore
    ProjectManagerAgent = None  # type: ignore
    QualityControllerAgent = None  # type: ignore
    QuestionQueueAgent = None  # type: ignore
    SocraticCounselorAgent = None  # type: ignore
    SystemMonitorAgent = None  # type: ignore
    UserManagerAgent = None  # type: ignore
    SkillGeneratorAgent = None  # type: ignore
    DocumentContextAnalyzer = None  # type: ignore
    GithubSyncHandler = None  # type: ignore
from socratic_core import EventEmitter, EventType, SocratesConfig

from socratic_system.database import VectorDatabase
from socratic_system.models import KnowledgeEntry
from socratic_system.orchestration.library_integrations import SocraticLibraryManager


class AgentOrchestrator:
    """
    Orchestrates all agents and manages system-wide coordination.

    Supports both old-style initialization (api_key string) and new-style (SocratesConfig)
    for backward compatibility.
    """

    def __init__(self, api_key_or_config: str | SocratesConfig):
        """
        Initialize the orchestrator.

        Args:
            api_key_or_config: Either an API key string (old style) or SocratesConfig (new style)
        """
        # Handle both old-style (api_key string) and new-style (SocratesConfig) initialization
        if isinstance(api_key_or_config, str):
            # Old style: create config from API key with defaults
            self.config = SocratesConfig(api_key=api_key_or_config)
        else:
            # New style: use provided config
            self.config = api_key_or_config

        self.api_key = self.config.api_key

        # Initialize logging using the DebugLogger system
        from socratic_system.utils.logger import get_logger as get_debug_logger

        self.logger = get_debug_logger("orchestrator")

        # Initialize event emitter
        self.event_emitter = EventEmitter()

        # Initialize database components with configured paths
        self.logger.info("Initializing database components...")

        # Use unified DatabaseSingleton for both CLI and API
        from socratic_system.database import DatabaseSingleton

        DatabaseSingleton.initialize(str(self.config.projects_db_path))
        self.database = DatabaseSingleton.get_instance()

        # Initialize vector database (optional - continue if RAG dependencies missing)
        self.vector_db: VectorDatabase | None
        try:
            self.vector_db = VectorDatabase(
                str(self.config.vector_db_path), embedding_model=self.config.embedding_model
            )
            self.logger.info("Database components initialized successfully")
        except ImportError as e:
            self.logger.warning(f"Vector database initialization skipped: {e}")
            self.vector_db = None  # Mark as unavailable but don't fail
        except Exception as e:
            self.logger.error(f"Vector database initialization failed: {e}")
            raise  # Re-raise other exceptions

        # Initialize LLM client (using socrates-nexus for multi-provider support)
        # socrates-nexus is now a required dependency providing universal LLM client
        self.llm_client = LLMClient(
            provider="anthropic",  # Default to Claude, configurable via environment
            model=self.config.claude_model,
            api_key=self.config.api_key,
        )
        # Keep claude_client alias for backward compatibility
        self.claude_client = self.llm_client

        # Initialize Socratic Library Manager (all 12 libraries)
        self.library_manager = SocraticLibraryManager(self.config)
        self.logger.info(f"Library integration status: {self.library_manager.get_status()}")

        # Cache for lazy-loaded agents
        self._agents_cache: dict[str, Any] = {}

        # Register conflict detection event handler
        self._setup_conflict_detection()

        # Start background knowledge base loading (non-blocking)
        # Skip in test mode to avoid SQLite deadlocks from multiple threads
        import os
        import threading

        self.knowledge_loaded = False
        self._knowledge_thread = None

        # Only start knowledge loading thread if not in test mode
        # NOTE: Temporarily disabled due to socratic-rag chunker bug with document_id parameter
        # The system works fine without pre-loaded knowledge entries
        if False and "PYTEST_CURRENT_TEST" not in os.environ:
            self._knowledge_thread = threading.Thread(
                target=self._load_knowledge_base_safe, daemon=True
            )
            self._knowledge_thread.start()
        else:
            # Mark as loaded immediately (skip for now due to socratic-rag bug)
            self.knowledge_loaded = True

        # Emit system initialized event
        self.event_emitter.emit(
            EventType.SYSTEM_INITIALIZED,
            {
                "version": "0.5.0",
                "data_dir": str(self.config.data_dir),
                "model": self.config.claude_model,
            },
        )

        # Log initialization summary
        self.logger.info("=" * 70)
        self.logger.info("Socrates AI initialized successfully!")
        self.logger.info(f"  Configuration: {self.config}")
        self.logger.info(f"  Projects DB: {self.config.projects_db_path}")
        self.logger.info(f"  Vector DB: {self.config.vector_db_path}")
        self.logger.info("=" * 70)

    def _load_knowledge_base_safe(self) -> None:
        """Wrapper for knowledge base loading in background thread with error handling"""
        try:
            self._load_knowledge_base()
        except Exception as e:
            self.logger.error(f"Background knowledge loading failed: {e}")

    def wait_for_knowledge(self, timeout: int = 10) -> bool:
        """
        Wait for knowledge base to finish loading (optional blocking method)

        Args:
            timeout: Maximum seconds to wait before returning

        Returns:
            True if knowledge loaded successfully, False if timeout
        """
        if self.knowledge_loaded:
            return True

        # If thread exists, wait for it; otherwise already loaded (test mode)
        if self._knowledge_thread is not None:
            self._knowledge_thread.join(timeout=timeout)
        return self.knowledge_loaded

    def _get_agent(self, agent_name: str, agent_class: Any, fallback_class: Any = None) -> Any:
        """
        Safely get or instantiate an agent with proper error handling.

        Args:
            agent_name: Name of the agent for caching
            agent_class: The agent class (might be None if import failed)
            fallback_class: Optional fallback class to use if primary is unavailable

        Returns:
            Instantiated agent

        Raises:
            ImportError: If agent class is unavailable and no fallback provided
        """
        if agent_name not in self._agents_cache:
            if agent_class is None:
                if fallback_class is not None:
                    agent_class = fallback_class
                else:
                    raise ImportError(
                        f"Agent {agent_name} is not available. "
                        "Please install 'socratic-agents' package."
                    )
            self._agents_cache[agent_name] = agent_class(self)
        return self._agents_cache[agent_name]

    # Lazy-loaded agent properties
    @property
    def project_manager(self) -> ProjectManagerAgent:
        """Lazy-load project manager agent"""
        return self._get_agent("project_manager", ProjectManagerAgent)

    @property
    def socratic_counselor(self) -> SocraticCounselorAgent:
        """Lazy-load socratic counselor agent"""
        return self._get_agent("socratic_counselor", SocraticCounselorAgent)

    @property
    def context_analyzer(self) -> ContextAnalyzerAgent:
        """Lazy-load context analyzer agent"""
        return self._get_agent("context_analyzer", ContextAnalyzerAgent)

    @property
    def code_generator(self) -> CodeGeneratorAgent:
        """Lazy-load code generator agent"""
        return self._get_agent("code_generator", CodeGeneratorAgent)

    @property
    def system_monitor(self) -> SystemMonitorAgent:
        """Lazy-load system monitor agent"""
        return self._get_agent("system_monitor", SystemMonitorAgent)

    @property
    def conflict_detector(self) -> ConflictDetectorAgent:
        """Lazy-load conflict detector agent"""
        return self._get_agent("conflict_detector", ConflictDetectorAgent)

    @property
    def document_processor(self) -> DocumentProcessorAgent:
        """Lazy-load document processor agent"""
        return self._get_agent("document_processor", DocumentProcessorAgent)

    @property
    def user_manager(self) -> UserManagerAgent:
        """Lazy-load user manager agent"""
        return self._get_agent("user_manager", UserManagerAgent)

    @property
    def note_manager(self) -> NoteManagerAgent:
        """Lazy-load note manager agent"""
        return self._get_agent("note_manager", NoteManagerAgent)

    @property
    def knowledge_manager(self) -> KnowledgeManagerAgent:
        """Lazy-load knowledge manager agent"""
        return self._get_agent("knowledge_manager", KnowledgeManagerAgent)

    @property
    def knowledge_analysis(self) -> KnowledgeAnalysisAgent:
        """Lazy-load knowledge analysis agent"""
        return self._get_agent("knowledge_analysis", KnowledgeAnalysisAgent)

    @property
    def quality_controller(self) -> QualityControllerAgent:
        """Lazy-load quality controller agent"""
        return self._get_agent("quality_controller", QualityControllerAgent)

    @property
    def learning_agent(self) -> UserLearningAgent:
        """Lazy-load user learning agent"""
        return self._get_agent("learning_agent", UserLearningAgent)

    @property
    def multi_llm_agent(self) -> MultiLLMAgent:
        """Lazy-load multi-LLM agent"""
        return self._get_agent("multi_llm_agent", MultiLLMAgent)

    @property
    def question_queue(self) -> QuestionQueueAgent:
        """Lazy-load question queue agent"""
        return self._get_agent("question_queue", QuestionQueueAgent)

    @property
    def code_validation_agent(self) -> CodeValidationAgent:
        """Lazy-load code validation agent"""
        return self._get_agent("code_validation_agent", CodeValidationAgent)

    @property
    def skill_generator(self) -> SkillGeneratorAgent:
        """Lazy-load skill generator agent"""
        return self._get_agent("skill_generator", SkillGeneratorAgent)

    @property
    def document_context_analyzer(self) -> DocumentContextAnalyzer:
        """Lazy-load document context analyzer agent"""
        return self._get_agent("document_context_analyzer", DocumentContextAnalyzer)

    @property
    def github_sync_handler(self) -> GithubSyncHandler:
        """Lazy-load GitHub sync handler agent"""
        return self._get_agent("github_sync_handler", GithubSyncHandler)

    @property
    def learning_integration(self) -> Any:
        """Lazy-load learning integration (socratic-learning)"""
        if "learning_integration" not in self._agents_cache:
            from socratic_system.core import LearningIntegration

            self._agents_cache["learning_integration"] = LearningIntegration(
                log_path=str(self.config.data_dir / "learning_logs"), llm_client=self.llm_client
            )
        return self._agents_cache["learning_integration"]

    @property
    def workflow_integration(self) -> Any:
        """Lazy-load workflow integration (socratic-workflow)"""
        if "workflow_integration" not in self._agents_cache:
            from socratic_system.core import WorkflowIntegration

            self._agents_cache["workflow_integration"] = WorkflowIntegration(
                executor_type="sequential"
            )
        return self._agents_cache["workflow_integration"]

    @property
    def analyzer_integration(self) -> Any:
        """Lazy-load analyzer integration (socratic-analyzer)"""
        if "analyzer_integration" not in self._agents_cache:
            from socratic_system.core import AnalyzerIntegration

            self._agents_cache["analyzer_integration"] = AnalyzerIntegration()
        return self._agents_cache["analyzer_integration"]

    def _load_knowledge_base(self) -> None:
        """Load default knowledge base from config file if not already loaded"""
        if self.vector_db is None:
            self.logger.debug("Vector database not available, skipping knowledge base loading")
            return

        if self.vector_db.knowledge_loaded:
            self.logger.debug("Knowledge base already loaded, skipping initialization")
            return

        self.logger.info("Loading knowledge base...")
        self.event_emitter.emit(EventType.LOG_INFO, {"message": "Loading knowledge base..."})

        # Load knowledge data from config file
        knowledge_data = self._load_knowledge_config()

        if not knowledge_data:
            self._emit_no_knowledge_warning()
            return

        # Process and add knowledge entries
        loaded_count, error_count = self._process_knowledge_entries(knowledge_data)

        # Mark knowledge base as loaded
        if self.vector_db is not None:
            self.vector_db.knowledge_loaded = True
        self.knowledge_loaded = True

        # Emit completion event
        self._emit_knowledge_loaded_event(loaded_count, error_count)

    def _load_knowledge_config(self) -> list:
        """Load knowledge configuration from file"""
        # Determine config path
        knowledge_base_path = getattr(self.config, 'knowledge_base_path', None)
        if knowledge_base_path:
            config_path = Path(knowledge_base_path)
            source = "configured path"
        else:
            config_path = Path(__file__).parent.parent / "config" / "knowledge_base.json"
            source = "default location"

        self.logger.debug(f"Attempting to load knowledge base from {source}: {config_path}")

        return self._read_knowledge_config_file(config_path, source)

    def _read_knowledge_config_file(self, config_path: Path, source: str) -> list:
        """Read and parse knowledge config file"""
        try:
            if not config_path.exists():
                self.logger.debug(f"Knowledge config not found at {source}: {config_path}")
                return []

            self.logger.debug(f"Knowledge base file found at: {config_path}")
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)

            knowledge_entries = config.get("default_knowledge", [])
            if knowledge_entries:
                self.logger.info(
                    f"Successfully loaded {len(knowledge_entries)} knowledge entries from {source}"
                )
                return knowledge_entries
            else:
                self.logger.warning(f"No 'default_knowledge' entries found in config at {source}")
                return []

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in knowledge config at {config_path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Failed to load knowledge config from {config_path}: {e}")
            return []

    def _process_knowledge_entries(self, knowledge_data: list) -> tuple:
        """Process and add knowledge entries to database"""
        self.logger.info(f"Found {len(knowledge_data)} knowledge entries to load")

        loaded_count = 0
        error_count = 0

        for entry_data in knowledge_data:
            if self._add_knowledge_entry(entry_data):
                loaded_count += 1
            else:
                error_count += 1

        return loaded_count, error_count

    def _add_knowledge_entry(self, entry_data: dict) -> bool:
        """Add single knowledge entry to both vector and SQL databases"""
        try:
            entry = KnowledgeEntry(**entry_data)
            if self.vector_db is not None:
                self.vector_db.add_knowledge(entry)

            # Also store in SQL database for persistence and querying
            self.database.save_knowledge_document(
                user_id="system",
                project_id="default",
                doc_id=entry.id,
                title=getattr(entry, "category", "Knowledge Entry"),
                content=entry.content,
                source="hardcoded_knowledge_base",
                document_type="knowledge_entry",
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to add knowledge entry '{entry_data.get('id', 'unknown')}': {e}"
            )
            return False

    def _emit_no_knowledge_warning(self) -> None:
        """Emit warning when no knowledge base config found"""
        self.logger.warning(
            "No knowledge base config found - system will run with empty knowledge base"
        )
        self.event_emitter.emit(
            EventType.LOG_WARNING, {"message": "No knowledge base config found"}
        )

    def _emit_knowledge_loaded_event(self, loaded_count: int, error_count: int) -> None:
        """Emit knowledge loaded event with summary"""
        summary = f"Knowledge base loaded: {loaded_count} entries added"
        if error_count > 0:
            summary += f" ({error_count} failed)"
        self.logger.info(summary)

        self.event_emitter.emit(
            EventType.KNOWLEDGE_LOADED,
            {
                "entry_count": loaded_count,
                "error_count": error_count,
                "status": "success" if error_count == 0 else "partial",
            },
        )

    def _setup_conflict_detection(self) -> None:
        """Set up conflict detection event handlers"""
        try:
            # Register handler for detecting conflicts when projects are analyzed
            # This is a placeholder for future event binding
            self.logger.debug("Conflict detection event handlers registered")
        except Exception as e:
            self.logger.debug(f"Conflict detection setup: {e}")

    def detect_project_conflicts(self, project) -> list[dict[str, Any]]:
        """
        Detect and store conflicts in a project.

        Args:
            project: ProjectContext object to analyze

        Returns:
            List of detected conflicts
        """
        if not self.library_manager or not self.library_manager.conflict:
            self.logger.debug("Conflict detection not available")
            return []

        try:
            detected_conflicts = []

            # Check for conflicts in requirements
            if project.requirements and len(project.requirements) > 1:
                conflict_data = self.library_manager.conflict.detect_conflicts(
                    proposals=project.requirements,
                    agents=[f"requirement_{i}" for i in range(len(project.requirements))]
                )
                for conf in conflict_data:
                    detected_conflicts.append({
                        "field": "requirements",
                        "type": conf.get("conflict_type", "data_conflict"),
                        "severity": "medium",
                        "proposal_index": conf.get("proposal_index"),
                    })

            # Check for conflicts in tech stack
            if project.tech_stack and len(project.tech_stack) > 1:
                conflict_data = self.library_manager.conflict.detect_conflicts(
                    proposals=project.tech_stack,
                    agents=[f"tech_{i}" for i in range(len(project.tech_stack))]
                )
                for conf in conflict_data:
                    detected_conflicts.append({
                        "field": "tech_stack",
                        "type": conf.get("conflict_type", "data_conflict"),
                        "severity": "low",
                        "proposal_index": conf.get("proposal_index"),
                    })

            # Save detected conflicts to database
            if detected_conflicts:
                self.logger.debug(f"Detected {len(detected_conflicts)} conflicts in project {project.project_id}")
                for conflict_data in detected_conflicts:
                    try:
                        self.database.save_conflict(project.project_id, conflict_data)
                    except Exception as e:
                        self.logger.error(f"Error saving conflict: {e}")

                # Emit conflict detection event
                self.event_emitter.emit(
                    "conflict.detected",
                    {
                        "project_id": project.project_id,
                        "conflict_count": len(detected_conflicts),
                        "conflicts": detected_conflicts,
                    }
                )

            return detected_conflicts

        except Exception as e:
            self.logger.error(f"Error detecting conflicts: {e}")
            return []

    def set_model(self, model_name: str) -> bool:
        """
        Update the Claude model at runtime.

        Args:
            model_name: The new model name to use

        Returns:
            True if successful, False otherwise
        """
        try:
            self.config.claude_model = model_name
            self.claude_client.model = model_name
            self.logger.info(f"Model updated to {model_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating model: {e}")
            return False

    def _translate_request(self, agent_name: str, request: dict[str, Any]) -> dict[str, Any]:
        """
        Translate request action names to match socratic_agents expected format.

        socratic_agents uses different action names than our CLI.
        This adapter translates between them.
        """
        action = request.get("action", "")

        # Translate ProjectManager actions
        if agent_name == "project_manager":
            if action == "create_project":
                request["action"] = "create"
            elif action == "list_projects":
                request["action"] = "list"
            # load_project, save_project, etc. not supported by socratic_agents

        # Translate NoteManager actions
        elif agent_name == "note_manager":
            if action == "add_note":
                request["action"] = "create"
            elif action == "list_notes":
                request["action"] = "list"
            elif action == "delete_note":
                request["action"] = "update"  # Map to update since delete not supported
            # search_notes not directly supported

        return request

    def process_request(self, agent_name: str, request: dict[str, Any]) -> dict[str, Any]:
        """
        Route a request to the appropriate agent (synchronous).

        Args:
            agent_name: Name of the agent to process the request
            request: Dictionary containing the request parameters

        Returns:
            Dictionary containing the agent's response

        Example:
            >>> result = orchestrator.process_request('project_manager', {
            ...     'action': 'create_project',
            ...     'project_name': 'My Project',
            ...     'owner': 'alice'
            ... })
        """
        agents = {
            "project_manager": self.project_manager,
            "socratic_counselor": self.socratic_counselor,
            "context_analyzer": self.context_analyzer,
            "code_generator": self.code_generator,
            "system_monitor": self.system_monitor,
            "conflict_detector": self.conflict_detector,
            "document_agent": self.document_processor,
            "user_manager": self.user_manager,
            "note_manager": self.note_manager,
            "knowledge_manager": self.knowledge_manager,
            "quality_controller": self.quality_controller,
            "learning": self.learning_agent,
            "multi_llm": self.multi_llm_agent,
            "question_queue": self.question_queue,
            "code_validation": self.code_validation_agent,
            "skill_generator": self.skill_generator,
            "document_context_analyzer": self.document_context_analyzer,
            "github_sync_handler": self.github_sync_handler,
        }

        agent = agents.get(agent_name)
        if agent:
            self.event_emitter.emit(
                EventType.AGENT_START,
                {"agent": agent_name, "action": request.get("action", "unknown")},
            )

            try:
                # Translate action names for socratic_agents compatibility
                translated_request = self._translate_request(agent_name, request.copy())
                result = agent.process(translated_request)

                self.event_emitter.emit(
                    EventType.AGENT_COMPLETE,
                    {"agent": agent_name, "status": result.get("status", "unknown")},
                )

                return result
            except Exception as e:
                self.logger.error(f"Agent {agent_name} error: {e}")
                self.event_emitter.emit(
                    EventType.AGENT_ERROR, {"agent": agent_name, "error": str(e)}
                )
                raise
        else:
            return {"status": "error", "message": f"Unknown agent: {agent_name}"}

    async def process_request_async(
        self, agent_name: str, request: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Route a request to the appropriate agent asynchronously.

        Allows for non-blocking execution of long-running operations. Most useful
        when multiple operations need to run concurrently or when integration with
        async frameworks (FastAPI, etc.) is needed.

        Args:
            agent_name: Name of the agent to process the request
            request: Dictionary containing the request parameters

        Returns:
            Dictionary containing the agent's response

        Raises:
            ValueError: If agent is not found

        Example:
            >>> result = await orchestrator.process_request_async('code_generator', {
            ...     'action': 'generate_code',
            ...     'project': project_context
            ... })

        Concurrent Example:
            >>> results = await asyncio.gather(
            ...     orchestrator.process_request_async('code_generator', code_req),
            ...     orchestrator.process_request_async('socratic_counselor', socratic_req)
            ... )
        """
        agents = {
            "project_manager": self.project_manager,
            "socratic_counselor": self.socratic_counselor,
            "context_analyzer": self.context_analyzer,
            "code_generator": self.code_generator,
            "system_monitor": self.system_monitor,
            "conflict_detector": self.conflict_detector,
            "document_agent": self.document_processor,
            "user_manager": self.user_manager,
            "note_manager": self.note_manager,
            "knowledge_manager": self.knowledge_manager,
            "quality_controller": self.quality_controller,
            "learning": self.learning_agent,
            "multi_llm": self.multi_llm_agent,
            "question_queue": self.question_queue,
            "code_validation": self.code_validation_agent,
            "skill_generator": self.skill_generator,
            "document_context_analyzer": self.document_context_analyzer,
            "github_sync_handler": self.github_sync_handler,
        }

        agent = agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")

        self.event_emitter.emit(
            EventType.AGENT_START,
            {"agent": agent_name, "action": request.get("action", "unknown"), "async": True},
        )

        try:
            result = await agent.process_async(request)

            self.event_emitter.emit(
                EventType.AGENT_COMPLETE,
                {"agent": agent_name, "status": result.get("status", "unknown"), "async": True},
            )

            return result

        except Exception as e:
            self.logger.error(f"Agent {agent_name} async error: {e}")
            self.event_emitter.emit(
                EventType.AGENT_ERROR, {"agent": agent_name, "error": str(e), "async": True}
            )
            raise

    # =========================================================================
    # LIBRARY INTEGRATION METHODS - Using all 12 Socratic ecosystem libraries
    # =========================================================================

    def analyze_code_quality(self, code: str, filename: str = "generated_code.py") -> dict:
        """Analyze generated code using socratic-analyzer"""
        return self.library_manager.analyzer.analyze_code(code, filename)

    def log_learning_interaction(self, session_id: str, agent_name: str,
                                input_data: dict, output_data: dict,
                                tokens: int = 0, cost: float = 0.0,
                                duration_ms: float = 0.0, success: bool = True) -> Optional[dict]:
        """Log interaction for learning analytics using socratic-learning"""
        return self.library_manager.learning.log_interaction(
            session_id=session_id,
            agent_name=agent_name,
            input_data=input_data,
            output_data=output_data,
            tokens_used=tokens,
            cost=cost,
            duration_ms=duration_ms,
            success=success
        )

    def detect_agent_conflicts(self, field: str, agent_outputs: dict,
                             agents: list) -> Optional[dict]:
        """Detect and resolve conflicts between agent outputs using socratic-conflict"""
        return self.library_manager.conflict.detect_and_resolve(field, agent_outputs, agents)

    def store_knowledge(self, tenant_id: str, title: str, content: str,
                       tags: Optional[list] = None) -> Optional[dict]:
        """Store knowledge item using socratic-knowledge"""
        return self.library_manager.knowledge.create_knowledge_item(
            tenant_id=tenant_id,
            title=title,
            content=content,
            tags=tags
        )

    def search_knowledge(self, tenant_id: str, query: str) -> list:
        """Search knowledge base using socratic-knowledge"""
        return self.library_manager.knowledge.search_knowledge(tenant_id, query)

    def generate_documentation(self, project_info: dict) -> Optional[str]:
        """Generate project documentation using socratic-docs"""
        return self.library_manager.docs.generate_readme(project_info)

    # =========================================================================
    # CORE FRAMEWORK METHODS (5 additional libraries)
    # =========================================================================

    def get_system_info(self) -> dict:
        """Get system information from socratic-core"""
        return self.library_manager.core.get_system_info()

    def get_system_config(self) -> dict:
        """Get system configuration from socratic-core"""
        return self.library_manager.core.get_config()

    def call_llm(self, prompt: str, model: str = "claude-opus",
                 provider: str = "anthropic", temperature: float = 0.7,
                 **kwargs) -> Optional[dict]:
        """Call LLM via socrates-nexus with multi-provider support"""
        return self.library_manager.nexus.call_llm(
            prompt=prompt,
            model=model,
            provider=provider,
            temperature=temperature,
            **kwargs
        )

    def list_llm_models(self, provider: Optional[str] = None) -> dict:
        """List available LLM models via socrates-nexus"""
        return self.library_manager.nexus.list_models(provider=provider)

    def execute_agent(self, agent_name: str, request_data: dict) -> Optional[dict]:
        """Execute an agent using socratic-agents"""
        return self.library_manager.agents.execute_agent(agent_name, request_data)

    def list_agents(self) -> list:
        """List all available agents from socratic-agents"""
        return self.library_manager.agents.list_agents()

    def index_rag_document(self, content: str, source: str,
                          metadata: Optional[dict] = None) -> Optional[str]:
        """Index a document for RAG retrieval using socratic-rag"""
        return self.library_manager.rag.index_document(
            content=content,
            source=source,
            metadata=metadata
        )

    def search_rag(self, query: str, limit: int = 5) -> list:
        """Search RAG system using socratic-rag"""
        return self.library_manager.rag.search(query=query, limit=limit)

    def validate_security_input(self, user_input: str) -> dict:
        """Validate user input for security issues using socratic-security"""
        return self.library_manager.security.validate_input(user_input)

    def check_user_mfa(self, user_id: str) -> bool:
        """Check if MFA is enabled for user using socratic-security"""
        return self.library_manager.security.check_mfa(user_id)

    def get_library_status(self) -> dict:
        """Get status of all library integrations"""
        return self.library_manager.get_status()

    def _safe_log(self, level: str, message: str):
        """Safely log messages, suppressing errors during Python shutdown.

        During Python interpreter shutdown, the logging module may be partially
        deinitialized, causing 'sys.meta_path is None' errors. This method
        safely handles those cases.
        """
        try:
            if level == "debug":
                self.logger.debug(message)
            elif level == "info":
                self.logger.info(message)
            elif level == "warning":
                self.logger.warning(message)
            elif level == "error":
                self.logger.error(message)
        except Exception:
            # Silently ignore logging errors during shutdown
            pass

    def close(self):
        """Close all database connections and release resources.

        This method should be called before shutting down the orchestrator
        or before deleting temporary directories to ensure all file handles
        are properly released, especially important on Windows systems.
        """
        try:
            # Wait for knowledge base loading thread to complete if it exists
            if hasattr(self, "_knowledge_thread") and self._knowledge_thread is not None:
                if self._knowledge_thread.is_alive():
                    # Give thread up to 5 seconds to finish
                    self._knowledge_thread.join(timeout=5)
                self._safe_log("debug", "Knowledge base loading thread stopped")
        except Exception as e:
            self._safe_log("warning", f"Error waiting for knowledge thread: {e}")

        try:
            # Close vector database to release ChromaDB file handles
            if hasattr(self, "vector_db") and self.vector_db is not None:
                self.vector_db.close()
                self._safe_log("info", "Vector database closed")
        except Exception as e:
            self._safe_log("warning", f"Error closing vector database: {e}")

        try:
            # Close project database
            if hasattr(self, "database") and self.database is not None:
                if hasattr(self.database, "close"):
                    self.database.close()
                self._safe_log("info", "Project database closed")
        except Exception as e:
            self._safe_log("warning", f"Error closing project database: {e}")

        try:
            # Clear agents cache
            self._agents_cache.clear()
            self._safe_log("debug", "Agents cache cleared")
        except Exception as e:
            self._safe_log("warning", f"Error clearing agents cache: {e}")

    def __del__(self):
        """Destructor to ensure cleanup when orchestrator is destroyed."""
        try:
            self.close()
        except Exception:
            # Silently ignore errors in destructor
            pass
