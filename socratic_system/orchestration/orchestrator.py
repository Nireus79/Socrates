"""
Agent Orchestrator for Socratic RAG System

Coordinates all agents and manages their interactions, including:
- Agent initialization
- Request routing
- Knowledge base management
- Database components
"""

import os
from typing import Dict, Any
from colorama import Fore

from socratic_system.config import CONFIG
from socratic_system.models import KnowledgeEntry
from socratic_system.database import ProjectDatabase, VectorDatabase
from socratic_system.clients import ClaudeClient
from socratic_system.agents import (
    ProjectManagerAgent, SocraticCounselorAgent, ContextAnalyzerAgent,
    CodeGeneratorAgent, SystemMonitorAgent, ConflictDetectorAgent,
    DocumentAgent, UserManagerAgent
)
from socratic_system.agents.note_manager import NoteManagerAgent
from .knowledge_base import DEFAULT_KNOWLEDGE


class AgentOrchestrator:
    """Orchestrates all agents and manages system-wide coordination"""

    def __init__(self, api_key: str):
        self.api_key = api_key

        # Initialize database components
        data_dir = CONFIG['DATA_DIR']
        os.makedirs(data_dir, exist_ok=True)

        self.database = ProjectDatabase(os.path.join(data_dir, 'projects.db'))
        self.vector_db = VectorDatabase(os.path.join(data_dir, 'vector_db'))

        # Initialize Claude client
        self.claude_client = ClaudeClient(api_key, self)
        self._initialize_agents()

        # Load default knowledge base
        self._load_knowledge_base()

        print(f"{Fore.GREEN}[OK] Socratic RAG System v7.0 initialized successfully!")

    def _initialize_agents(self):
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

    def _load_knowledge_base(self):
        """Load default knowledge base if not already loaded"""
        if self.vector_db.knowledge_loaded:
            return

        print(f"{Fore.YELLOW}Loading knowledge base...")

        for knowledge_data in DEFAULT_KNOWLEDGE:
            entry = KnowledgeEntry(**knowledge_data)
            self.vector_db.add_knowledge(entry)

        self.vector_db.knowledge_loaded = True
        print(f"{Fore.GREEN}[OK] Knowledge base loaded ({len(DEFAULT_KNOWLEDGE)} entries)")

    def process_request(self, agent_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate agent"""
        agents = {
            'project_manager': self.project_manager,
            'socratic_counselor': self.socratic_counselor,
            'context_analyzer': self.context_analyzer,
            'code_generator': self.code_generator,
            'system_monitor': self.system_monitor,
            'conflict_detector': self.conflict_detector,
            'document_agent': self.document_agent,
            'user_manager': self.user_manager,
            'note_manager': self.note_manager
        }

        agent = agents.get(agent_name)
        if agent:
            return agent.process(request)
        else:
            return {'status': 'error', 'message': f'Unknown agent: {agent_name}'}
