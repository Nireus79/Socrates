"""
Agent Orchestrator for Socratic RAG System

Coordinates all agents and manages their interactions, including:
- Agent initialization
- Request routing
- Knowledge base management
- Database components
"""

import os
import json
from typing import Dict, Any, List
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
        """Load default knowledge base from config file if not already loaded"""
        if self.vector_db.knowledge_loaded:
            return

        print(f"{Fore.YELLOW}Loading knowledge base...")

        # Load knowledge from JSON config file
        knowledge_data = self._load_knowledge_config()

        if not knowledge_data:
            print(f"{Fore.YELLOW}[WARN] No knowledge base config found")
            return

        for entry_data in knowledge_data:
            entry = KnowledgeEntry(**entry_data)
            self.vector_db.add_knowledge(entry)

        self.vector_db.knowledge_loaded = True
        print(f"{Fore.GREEN}[OK] Knowledge base loaded ({len(knowledge_data)} entries)")

    def _load_knowledge_config(self) -> List[Dict[str, Any]]:
        """Load knowledge base from JSON configuration file"""
        config_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'config',
            'knowledge_base.json'
        )

        try:
            if not os.path.exists(config_path):
                print(f"{Fore.YELLOW}[WARN] Knowledge config not found: {config_path}")
                return []

            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            knowledge_entries = config.get('default_knowledge', [])
            if knowledge_entries:
                return knowledge_entries
            else:
                print(f"{Fore.YELLOW}[WARN] No 'default_knowledge' entries in config")
                return []

        except json.JSONDecodeError as e:
            print(f"{Fore.RED}[ERROR] Invalid JSON in knowledge config: {e}")
            return []
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Failed to load knowledge config: {e}")
            return []

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
