"""
Agent Orchestrator for Socratic RAG System

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

from socratic_system.agents import (
    CodeGeneratorAgent,
    CodeValidationAgent,
    ConflictDetectorAgent,
    ContextAnalyzerAgent,
    DocumentProcessorAgent,
    ProjectManagerAgent,
    QualityControllerAgent,
    SocraticCounselorAgent,
    SystemMonitorAgent,
    UserManagerAgent,
)
from socratic_system.agents.knowledge_analysis import KnowledgeAnalysisAgent
from socratic_system.agents.knowledge_manager import KnowledgeManagerAgent
from socratic_system.agents.learning_agent import UserLearningAgent
from socratic_system.agents.multi_llm_agent import MultiLLMAgent
from socratic_system.agents.note_manager import NoteManagerAgent
from socratic_system.agents.question_queue_agent import QuestionQueueAgent
from socratic_system.clients import ClaudeClient
from socratic_system.config import SocratesConfig
from socratic_system.database import VectorDatabase
from socratic_system.events import EventEmitter, EventType
from socratic_system.models import KnowledgeEntry


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
        from socrates_api.database import DatabaseSingleton
        DatabaseSingleton.initialize(str(self.config.projects_db_path))
        self.database = DatabaseSingleton.get_instance()

        self.vector_db = VectorDatabase(
            str(self.config.vector_db_path), embedding_model=self.config.embedding_model
        )
        self.logger.info("Database components initialized successfully")

        # Initialize Claude client
        self.claude_client = ClaudeClient(
            self.config.api_key, self, subscription_token=self.config.subscription_token
        )

        # Cache for lazy-loaded agents
        self._agents_cache = {}

        # Start background knowledge base loading (non-blocking)
        # Skip in test mode to avoid SQLite deadlocks from multiple threads
        import os
        import threading

        self.knowledge_loaded = False
        self._knowledge_thread = None

        # Only start knowledge loading thread if not in test mode
        if "PYTEST_CURRENT_TEST" not in os.environ:
            self._knowledge_thread = threading.Thread(
                target=self._load_knowledge_base_safe,
                daemon=True
            )
            self._knowledge_thread.start()
        else:
            # In test mode, mark as loaded immediately (tests use mocks)
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
        self.logger.info("Socratic RAG System initialized successfully!")
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

    # Lazy-loaded agent properties
    @property
    def project_manager(self) -> ProjectManagerAgent:
        """Lazy-load project manager agent"""
        if "project_manager" not in self._agents_cache:
            from socratic_system.agents.project_manager import ProjectManagerAgent
            self._agents_cache["project_manager"] = ProjectManagerAgent(self)
        return self._agents_cache["project_manager"]

    @property
    def socratic_counselor(self) -> SocraticCounselorAgent:
        """Lazy-load socratic counselor agent"""
        if "socratic_counselor" not in self._agents_cache:
            from socratic_system.agents.socratic_counselor import SocraticCounselorAgent
            self._agents_cache["socratic_counselor"] = SocraticCounselorAgent(self)
        return self._agents_cache["socratic_counselor"]

    @property
    def context_analyzer(self) -> ContextAnalyzerAgent:
        """Lazy-load context analyzer agent"""
        if "context_analyzer" not in self._agents_cache:
            from socratic_system.agents.context_analyzer import ContextAnalyzerAgent
            self._agents_cache["context_analyzer"] = ContextAnalyzerAgent(self)
        return self._agents_cache["context_analyzer"]

    @property
    def code_generator(self) -> CodeGeneratorAgent:
        """Lazy-load code generator agent"""
        if "code_generator" not in self._agents_cache:
            from socratic_system.agents.code_generator import CodeGeneratorAgent
            self._agents_cache["code_generator"] = CodeGeneratorAgent(self)
        return self._agents_cache["code_generator"]

    @property
    def system_monitor(self) -> SystemMonitorAgent:
        """Lazy-load system monitor agent"""
        if "system_monitor" not in self._agents_cache:
            from socratic_system.agents import SystemMonitorAgent
            self._agents_cache["system_monitor"] = SystemMonitorAgent(self)
        return self._agents_cache["system_monitor"]

    @property
    def conflict_detector(self) -> ConflictDetectorAgent:
        """Lazy-load conflict detector agent"""
        if "conflict_detector" not in self._agents_cache:
            from socratic_system.agents import ConflictDetectorAgent
            self._agents_cache["conflict_detector"] = ConflictDetectorAgent(self)
        return self._agents_cache["conflict_detector"]

    @property
    def document_processor(self) -> DocumentProcessorAgent:
        """Lazy-load document processor agent"""
        if "document_processor" not in self._agents_cache:
            from socratic_system.agents.document_processor import DocumentProcessorAgent
            self._agents_cache["document_processor"] = DocumentProcessorAgent(self)
        return self._agents_cache["document_processor"]

    @property
    def user_manager(self) -> UserManagerAgent:
        """Lazy-load user manager agent"""
        if "user_manager" not in self._agents_cache:
            from socratic_system.agents import UserManagerAgent
            self._agents_cache["user_manager"] = UserManagerAgent(self)
        return self._agents_cache["user_manager"]

    @property
    def note_manager(self) -> NoteManagerAgent:
        """Lazy-load note manager agent"""
        if "note_manager" not in self._agents_cache:
            from socratic_system.agents import NoteManagerAgent
            self._agents_cache["note_manager"] = NoteManagerAgent(self)
        return self._agents_cache["note_manager"]

    @property
    def knowledge_manager(self) -> KnowledgeManagerAgent:
        """Lazy-load knowledge manager agent"""
        if "knowledge_manager" not in self._agents_cache:
            from socratic_system.agents.knowledge_manager import KnowledgeManagerAgent
            self._agents_cache["knowledge_manager"] = KnowledgeManagerAgent("knowledge_manager", self)
        return self._agents_cache["knowledge_manager"]

    @property
    def knowledge_analysis(self) -> KnowledgeAnalysisAgent:
        """Lazy-load knowledge analysis agent"""
        if "knowledge_analysis" not in self._agents_cache:
            from socratic_system.agents.knowledge_analysis import KnowledgeAnalysisAgent
            self._agents_cache["knowledge_analysis"] = KnowledgeAnalysisAgent(self)
        return self._agents_cache["knowledge_analysis"]

    @property
    def quality_controller(self) -> QualityControllerAgent:
        """Lazy-load quality controller agent"""
        if "quality_controller" not in self._agents_cache:
            from socratic_system.agents import QualityControllerAgent
            self._agents_cache["quality_controller"] = QualityControllerAgent(self)
        return self._agents_cache["quality_controller"]

    @property
    def learning_agent(self) -> UserLearningAgent:
        """Lazy-load user learning agent"""
        if "learning_agent" not in self._agents_cache:
            from socratic_system.agents import UserLearningAgent
            self._agents_cache["learning_agent"] = UserLearningAgent(self)
        return self._agents_cache["learning_agent"]

    @property
    def multi_llm_agent(self) -> MultiLLMAgent:
        """Lazy-load multi-LLM agent"""
        if "multi_llm_agent" not in self._agents_cache:
            from socratic_system.agents import MultiLLMAgent
            self._agents_cache["multi_llm_agent"] = MultiLLMAgent(self)
        return self._agents_cache["multi_llm_agent"]

    @property
    def question_queue(self) -> QuestionQueueAgent:
        """Lazy-load question queue agent"""
        if "question_queue" not in self._agents_cache:
            from socratic_system.agents import QuestionQueueAgent
            self._agents_cache["question_queue"] = QuestionQueueAgent(self)
        return self._agents_cache["question_queue"]

    @property
    def code_validation_agent(self) -> CodeValidationAgent:
        """Lazy-load code validation agent"""
        if "code_validation_agent" not in self._agents_cache:
            from socratic_system.agents.code_validation_agent import CodeValidationAgent
            self._agents_cache["code_validation_agent"] = CodeValidationAgent(self)
        return self._agents_cache["code_validation_agent"]

    def _load_knowledge_base(self) -> None:
        """Load default knowledge base from config file if not already loaded"""
        if self.vector_db.knowledge_loaded:
            self.logger.debug("Knowledge base already loaded, skipping initialization")
            return

        self.logger.info("Loading knowledge base...")
        self.event_emitter.emit(EventType.LOG_INFO, {"message": "Loading knowledge base..."})

        # Load knowledge from JSON config file (inline _load_knowledge_config logic)
        if self.config.knowledge_base_path:
            config_path = Path(self.config.knowledge_base_path)
            source = "configured path"
        else:
            # Fall back to default location
            config_path = Path(__file__).parent.parent / "config" / "knowledge_base.json"
            source = "default location"

        self.logger.debug(f"Attempting to load knowledge base from {source}: {config_path}")

        knowledge_data = []
        try:
            if config_path.exists():
                self.logger.debug(f"Knowledge base file found at: {config_path}")
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)

                knowledge_entries = config.get("default_knowledge", [])
                if knowledge_entries:
                    self.logger.info(
                        f"Successfully loaded {len(knowledge_entries)} knowledge entries from {source}"
                    )
                    knowledge_data = knowledge_entries
                else:
                    self.logger.warning(f"No 'default_knowledge' entries found in config at {source}")
            else:
                self.logger.debug(f"Knowledge config not found at {source}: {config_path}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in knowledge config at {config_path}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load knowledge config from {config_path}: {e}")

        if not knowledge_data:
            self.logger.warning(
                "No knowledge base config found - system will run with empty knowledge base"
            )
            self.event_emitter.emit(
                EventType.LOG_WARNING, {"message": "No knowledge base config found"}
            )
            return

        self.logger.info(f"Found {len(knowledge_data)} knowledge entries to load")

        loaded_count = 0
        error_count = 0

        for entry_data in knowledge_data:
            try:
                entry = KnowledgeEntry(**entry_data)
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

                loaded_count += 1
            except Exception as e:
                self.logger.error(
                    f"Failed to add knowledge entry '{entry_data.get('id', 'unknown')}': {e}"
                )
                error_count += 1

        self.vector_db.knowledge_loaded = True
        self.knowledge_loaded = True  # Also mark orchestrator's flag as loaded

        # Log summary
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
        }

        agent = agents.get(agent_name)
        if agent:
            self.event_emitter.emit(
                EventType.AGENT_START,
                {"agent": agent_name, "action": request.get("action", "unknown")},
            )

            try:
                result = agent.process(request)

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
            if hasattr(self, '_knowledge_thread') and self._knowledge_thread is not None:
                if self._knowledge_thread.is_alive():
                    # Give thread up to 5 seconds to finish
                    self._knowledge_thread.join(timeout=5)
                self._safe_log("debug", "Knowledge base loading thread stopped")
        except Exception as e:
            self._safe_log("warning", f"Error waiting for knowledge thread: {e}")

        try:
            # Close vector database to release ChromaDB file handles
            if hasattr(self, 'vector_db') and self.vector_db is not None:
                self.vector_db.close()
                self._safe_log("info", "Vector database closed")
        except Exception as e:
            self._safe_log("warning", f"Error closing vector database: {e}")

        try:
            # Close project database
            if hasattr(self, 'database') and self.database is not None:
                if hasattr(self.database, 'close'):
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
