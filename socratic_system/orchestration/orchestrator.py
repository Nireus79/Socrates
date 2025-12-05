"""
Agent Orchestrator for Socratic RAG System

Coordinates all agents and manages their interactions, including:
- Agent initialization
- Request routing
- Knowledge base management
- Database components
- Event emission for decoupled communication
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import asyncio

from socratic_system.config import SocratesConfig, CONFIG
from socratic_system.events import EventEmitter, EventType
from socratic_system.models import KnowledgeEntry
from socratic_system.database import ProjectDatabase, VectorDatabase
from socratic_system.clients import ClaudeClient
from socratic_system.agents import (
    ProjectManagerAgent, SocraticCounselorAgent, ContextAnalyzerAgent,
    CodeGeneratorAgent, SystemMonitorAgent, ConflictDetectorAgent,
    DocumentAgent, UserManagerAgent
)
from socratic_system.agents.note_manager import NoteManagerAgent
from socratic_system.agents.knowledge_manager import KnowledgeManagerAgent


class AgentOrchestrator:
    """
    Orchestrates all agents and manages system-wide coordination.

    Supports both old-style initialization (api_key string) and new-style (SocratesConfig)
    for backward compatibility.
    """

    def __init__(self, api_key_or_config: Union[str, SocratesConfig]):
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

        # Initialize logging
        logging.basicConfig(
            level=self.config.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("socrates.orchestrator")

        # Initialize event emitter
        self.event_emitter = EventEmitter()

        # Initialize database components with configured paths
        self.database = ProjectDatabase(str(self.config.projects_db_path))
        self.vector_db = VectorDatabase(str(self.config.vector_db_path))

        # Initialize Claude client
        self.claude_client = ClaudeClient(self.config.api_key, self)

        # Initialize agents
        self._initialize_agents()

        # Load default knowledge base
        self._load_knowledge_base()

        # Emit system initialized event
        self.event_emitter.emit(EventType.SYSTEM_INITIALIZED, {
            "version": "0.5.0",
            "data_dir": str(self.config.data_dir),
            "model": self.config.claude_model,
        })

        self.logger.info("Socratic RAG System initialized successfully!")

    def _initialize_agents(self) -> None:
        """Initialize agents after orchestrator is fully set up"""
        self.project_manager = ProjectManagerAgent(self)
        self.socratic_counselor = SocraticCounselorAgent(self)
        self.context_analyzer = ContextAnalyzerAgent(self)
        self.code_generator = CodeGeneratorAgent(self)
        self.system_monitor = SystemMonitorAgent(self)
        self.conflict_detector = ConflictDetectorAgent(self)
        self.document_agent = DocumentAgent(self)
        self.user_manager = UserManagerAgent(self)
        self.note_manager = NoteManagerAgent("note_manager", self)
        self.knowledge_manager = KnowledgeManagerAgent("knowledge_manager", self)

    def _load_knowledge_base(self) -> None:
        """Load default knowledge base from config file if not already loaded"""
        if self.vector_db.knowledge_loaded:
            return

        self.logger.info("Loading knowledge base...")
        self.event_emitter.emit(EventType.LOG_INFO, {"message": "Loading knowledge base..."})

        # Load knowledge from JSON config file
        knowledge_data = self._load_knowledge_config()

        if not knowledge_data:
            self.logger.warning("No knowledge base config found")
            self.event_emitter.emit(
                EventType.LOG_WARNING,
                {"message": "No knowledge base config found"}
            )
            return

        for entry_data in knowledge_data:
            try:
                entry = KnowledgeEntry(**entry_data)
                self.vector_db.add_knowledge(entry)
            except Exception as e:
                self.logger.error(f"Failed to add knowledge entry: {e}")

        self.vector_db.knowledge_loaded = True

        self.event_emitter.emit(EventType.KNOWLEDGE_LOADED, {
            "entry_count": len(knowledge_data),
            "status": "success"
        })

        self.logger.info(f"Knowledge base loaded ({len(knowledge_data)} entries)")

    def _load_knowledge_config(self) -> List[Dict[str, Any]]:
        """Load knowledge base from JSON configuration file"""
        # Try the configured knowledge base path first
        if self.config.knowledge_base_path:
            config_path = Path(self.config.knowledge_base_path)
        else:
            # Fall back to default location
            config_path = Path(__file__).parent.parent / 'config' / 'knowledge_base.json'

        try:
            if not config_path.exists():
                self.logger.debug(f"Knowledge config not found: {config_path}")
                return []

            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            knowledge_entries = config.get('default_knowledge', [])
            if knowledge_entries:
                return knowledge_entries
            else:
                self.logger.warning("No 'default_knowledge' entries in config")
                return []

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in knowledge config: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Failed to load knowledge config: {e}")
            return []

    def process_request(self, agent_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
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
            'project_manager': self.project_manager,
            'socratic_counselor': self.socratic_counselor,
            'context_analyzer': self.context_analyzer,
            'code_generator': self.code_generator,
            'system_monitor': self.system_monitor,
            'conflict_detector': self.conflict_detector,
            'document_agent': self.document_agent,
            'user_manager': self.user_manager,
            'note_manager': self.note_manager,
            'knowledge_manager': self.knowledge_manager
        }

        agent = agents.get(agent_name)
        if agent:
            self.event_emitter.emit(EventType.AGENT_START, {
                'agent': agent_name,
                'action': request.get('action', 'unknown')
            })

            try:
                result = agent.process(request)

                self.event_emitter.emit(EventType.AGENT_COMPLETE, {
                    'agent': agent_name,
                    'status': result.get('status', 'unknown')
                })

                return result
            except Exception as e:
                self.logger.error(f"Agent {agent_name} error: {e}")
                self.event_emitter.emit(EventType.AGENT_ERROR, {
                    'agent': agent_name,
                    'error': str(e)
                })
                raise
        else:
            return {'status': 'error', 'message': f'Unknown agent: {agent_name}'}

    async def process_request_async(
        self,
        agent_name: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
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
            'project_manager': self.project_manager,
            'socratic_counselor': self.socratic_counselor,
            'context_analyzer': self.context_analyzer,
            'code_generator': self.code_generator,
            'system_monitor': self.system_monitor,
            'conflict_detector': self.conflict_detector,
            'document_agent': self.document_agent,
            'user_manager': self.user_manager,
            'note_manager': self.note_manager,
            'knowledge_manager': self.knowledge_manager
        }

        agent = agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")

        self.event_emitter.emit(EventType.AGENT_START, {
            'agent': agent_name,
            'action': request.get('action', 'unknown'),
            'async': True
        })

        try:
            result = await agent.process_async(request)

            self.event_emitter.emit(EventType.AGENT_COMPLETE, {
                'agent': agent_name,
                'status': result.get('status', 'unknown'),
                'async': True
            })

            return result

        except Exception as e:
            self.logger.error(f"Agent {agent_name} async error: {e}")
            self.event_emitter.emit(EventType.AGENT_ERROR, {
                'agent': agent_name,
                'error': str(e),
                'async': True
            })
            raise
