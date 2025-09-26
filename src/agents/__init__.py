"""
Socratic RAG Enhanced - Agents Module
Complete 8-agent architecture for enterprise-grade code generation workflow
"""

import logging
from typing import Any, Dict, List, Optional

# Import base classes
from src.agents.base import BaseAgent

# Import all agent implementations
from src.agents.project import ProjectManagerAgent
from src.agents.code import CodeGeneratorAgent
from src.agents.document import DocumentProcessorAgent
from src.agents.services import ServicesAgent

# Import remaining agents (to be implemented)
try:
    from src.agents.orchestrator import AgentOrchestrator
except ImportError:
    AgentOrchestrator = None

try:
    from src.agents.socratic import SocraticCounselorAgent
except ImportError:
    SocraticCounselorAgent = None

try:
    from src.agents.user import UserManagerAgent
except ImportError:
    UserManagerAgent = None

try:
    from src.agents.context import ContextAnalyzerAgent
except ImportError:
    ContextAnalyzerAgent = None

try:
    from src.agents.monitor import SystemMonitorAgent
except ImportError:
    SystemMonitorAgent = None

# Module metadata
__version__ = "7.0.0"
__author__ = "Socratic RAG Enhanced"
__description__ = "Enterprise-grade intelligent agent system for code generation"

# Set up module logging
logger = logging.getLogger(__name__)

# Global orchestrator instance
_orchestrator = None


def get_orchestrator():
    """Get global orchestrator instance"""
    global _orchestrator

    if _orchestrator is None:
        if AgentOrchestrator is None:
            logger.warning("AgentOrchestrator not available - some functionality may be limited")
            return None
        _orchestrator = AgentOrchestrator()

    return _orchestrator


def process_agent_request(agent_id: str, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to process agent requests"""
    orchestrator = get_orchestrator()

    if orchestrator is None:
        return {
            'success': False,
            'error': 'Agent orchestrator not available',
            'agent_id': agent_id
        }

    return orchestrator.route_request(agent_id, action, data)


def get_agent_capabilities() -> Dict[str, List[str]]:
    """Get all agent capabilities"""
    orchestrator = get_orchestrator()

    if orchestrator is None:
        # Return capabilities for available agents only
        available_agents = get_available_agents()
        return {
            agent_id: agent_class().get_capabilities()
            for agent_id, agent_class in available_agents.items()
        }

    return {
        agent_id: agent.get_capabilities()
        for agent_id, agent in orchestrator.agents.items()
    }


def get_available_agents() -> Dict[str, Any]:
    """Get dictionary of available agent classes"""
    agents = {}

    # Always available agents
    agents['project_manager'] = ProjectManagerAgent
    agents['code_generator'] = CodeGeneratorAgent
    agents['document_processor'] = DocumentProcessorAgent
    agents['services_agent'] = ServicesAgent

    # Conditionally available agents
    if SocraticCounselorAgent is not None:
        agents['socratic_counselor'] = SocraticCounselorAgent

    if UserManagerAgent is not None:
        agents['user_manager'] = UserManagerAgent

    if ContextAnalyzerAgent is not None:
        agents['context_analyzer'] = ContextAnalyzerAgent

    if SystemMonitorAgent is not None:
        agents['system_monitor'] = SystemMonitorAgent

    return agents


def create_agent(agent_type: str):
    """Create agent instance by type"""
    available_agents = get_available_agents()

    if agent_type not in available_agents:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(available_agents.keys())}")

    agent_class = available_agents[agent_type]
    return agent_class()


def get_agent_status() -> Dict[str, Any]:
    """Get status of all agents"""
    available_agents = get_available_agents()

    status = {
        'total_available': len(available_agents),
        'agents': {},
        'orchestrator_available': AgentOrchestrator is not None,
        'module_version': __version__
    }

    for agent_id, agent_class in available_agents.items():
        try:
            # Create temporary instance to get capabilities
            temp_agent = agent_class()
            status['agents'][agent_id] = {
                'name': temp_agent.name,
                'capabilities': temp_agent.get_capabilities(),
                'status': 'available'
            }
        except Exception as e:
            status['agents'][agent_id] = {
                'name': agent_id,
                'capabilities': [],
                'status': f'error: {str(e)}'
            }

    return status


def shutdown_agents():
    """Shutdown all agents gracefully"""
    global _orchestrator

    if _orchestrator is not None:
        try:
            # Check if orchestrator has shutdown method
            if hasattr(_orchestrator, 'shutdown'):
                _orchestrator.shutdown()
                logger.info("All agents shutdown complete")
            else:
                logger.warning("Orchestrator does not have shutdown method")
        except Exception as e:
            logger.error(f"Error during agent shutdown: {e}")
        finally:
            _orchestrator = None
    else:
        logger.info("No active orchestrator to shutdown")


# Export public API
__all__ = [
    # Base classes
    'BaseAgent',

    # Agent implementations
    'ProjectManagerAgent',
    'CodeGeneratorAgent',
    'DocumentProcessorAgent',
    'ServicesAgent',
    'SocraticCounselorAgent',  # May be None if not implemented
    'UserManagerAgent',        # May be None if not implemented
    'ContextAnalyzerAgent',    # May be None if not implemented
    'SystemMonitorAgent',      # May be None if not implemented
    'AgentOrchestrator',       # May be None if not implemented

    # Utility functions
    'get_orchestrator',
    'process_agent_request',
    'get_agent_capabilities',
    'get_available_agents',
    'create_agent',
    'get_agent_status',
    'shutdown_agents',

    # Module metadata
    '__version__',
    '__author__',
    '__description__'
]

# Initialize module
logger.info(f"Socratic RAG Enhanced Agents v{__version__} initialized")
logger.info(f"Available agents: {list(get_available_agents().keys())}")
