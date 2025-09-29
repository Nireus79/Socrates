#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Agents Module
====================================

Complete 8-agent architecture for enterprise-grade code generation.
Provides unified interface for all agents via orchestrator.

All 8 Agents:
1. UserManagerAgent - Authentication and user management
2. ProjectManagerAgent - Project lifecycle management
3. SocraticCounselorAgent - Socratic questioning
4. CodeGeneratorAgent - Code generation
5. ContextAnalyzerAgent - Context analysis
6. DocumentProcessorAgent - Document processing
7. ServicesAgent - Git, export, deployment
8. SystemMonitorAgent - System monitoring
"""

import logging
from typing import Any, Dict, List, Optional
from src import get_services

# Module metadata
__version__ = "7.3.0"
__author__ = "Socratic RAG Enhanced Team"
__description__ = "Enterprise-grade intelligent agent system"

# Set up module logging
logger = logging.getLogger(__name__)

# ============================================================================
# IMPORT BASE CLASSES
# ============================================================================

try:
    from .base import BaseAgent
    BASE_AVAILABLE = True
except ImportError:
    logger.warning("BaseAgent not available")
    BaseAgent = None
    BASE_AVAILABLE = False

# ============================================================================
# IMPORT ALL 8 AGENTS (with graceful fallbacks)
# ============================================================================

# Agent 1: User Manager
try:
    from .user import UserManagerAgent
    USER_AGENT_AVAILABLE = True
except ImportError:
    logger.warning("UserManagerAgent not available")
    UserManagerAgent = None
    USER_AGENT_AVAILABLE = False

# Agent 2: Project Manager
try:
    from .project import ProjectManagerAgent
    PROJECT_AGENT_AVAILABLE = True
except ImportError:
    logger.warning("ProjectManagerAgent not available")
    ProjectManagerAgent = None
    PROJECT_AGENT_AVAILABLE = False

# Agent 3: Socratic Counselor
try:
    from .socratic import SocraticCounselorAgent
    SOCRATIC_AGENT_AVAILABLE = True
except ImportError:
    logger.warning("SocraticCounselorAgent not available")
    SocraticCounselorAgent = None
    SOCRATIC_AGENT_AVAILABLE = False

# Agent 4: Code Generator
try:
    from .code import CodeGeneratorAgent
    CODE_AGENT_AVAILABLE = True
except ImportError:
    logger.warning("CodeGeneratorAgent not available")
    CodeGeneratorAgent = None
    CODE_AGENT_AVAILABLE = False

# Agent 5: Context Analyzer
try:
    from .context import ContextAnalyzerAgent
    CONTEXT_AGENT_AVAILABLE = True
except ImportError:
    logger.warning("ContextAnalyzerAgent not available")
    ContextAnalyzerAgent = None
    CONTEXT_AGENT_AVAILABLE = False

# Agent 6: Document Processor
try:
    from .document import DocumentProcessorAgent
    DOCUMENT_AGENT_AVAILABLE = True
except ImportError:
    logger.warning("DocumentProcessorAgent not available")
    DocumentProcessorAgent = None
    DOCUMENT_AGENT_AVAILABLE = False

# Agent 7: Services Agent
try:
    from .services import ServicesAgent
    SERVICES_AGENT_AVAILABLE = True
except ImportError:
    logger.warning("ServicesAgent not available")
    ServicesAgent = None
    SERVICES_AGENT_AVAILABLE = False

# Agent 8: System Monitor
try:
    from .monitor import SystemMonitorAgent
    MONITOR_AGENT_AVAILABLE = True
except ImportError:
    logger.warning("SystemMonitorAgent not available")
    SystemMonitorAgent = None
    MONITOR_AGENT_AVAILABLE = False

# Agent Orchestrator
try:
    from .orchestrator import AgentOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    logger.warning("AgentOrchestrator not available")
    AgentOrchestrator = None
    ORCHESTRATOR_AVAILABLE = False

# ============================================================================
# GLOBAL ORCHESTRATOR INSTANCE
# ============================================================================

_orchestrator: Optional[Any] = None


def get_orchestrator() -> Optional[Any]:
    """
    Get or create global orchestrator instance
    
    Returns:
        AgentOrchestrator instance or None if unavailable
    """
    global _orchestrator

    if _orchestrator is None:
        if not ORCHESTRATOR_AVAILABLE or AgentOrchestrator is None:
            logger.warning(
                "AgentOrchestrator not available - agent functionality limited"
            )
            return None

        try:
            _orchestrator = AgentOrchestrator(get_services())
            logger.info("Global orchestrator instance created")
        except (RuntimeError, ValueError, AttributeError) as e:
            logger.error(f"Failed to create orchestrator: {e}")
            return None

    return _orchestrator


def reset_orchestrator() -> None:
    """Reset global orchestrator instance (useful for testing)"""
    global _orchestrator
    
    if _orchestrator is not None:
        try:
            if hasattr(_orchestrator, 'shutdown'):
                _orchestrator.shutdown()
        except (RuntimeError, AttributeError) as e:
            logger.warning(f"Error during orchestrator shutdown: {e}")
        finally:
            _orchestrator = None
            logger.info("Orchestrator instance reset")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def process_agent_request(
    agent_id: str, 
    action: str, 
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process request through orchestrator
    
    Args:
        agent_id: Target agent ID
        action: Action to perform
        data: Request data
        
    Returns:
        Dict with response from agent
    """
    orchestrator = get_orchestrator()

    if orchestrator is None:
        return {
            'success': False,
            'error': 'Agent orchestrator not available',
            'agent_id': agent_id,
            'action': action
        }

    return orchestrator.route_request(agent_id, action, data)


def process_by_capability(
    capability: str, 
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process request by capability name
    
    Args:
        capability: Capability to execute
        data: Request data
        
    Returns:
        Dict with response from appropriate agent
    """
    orchestrator = get_orchestrator()

    if orchestrator is None:
        return {
            'success': False,
            'error': 'Agent orchestrator not available',
            'capability': capability
        }

    return orchestrator.route_by_capability(capability, data)


def get_available_agents() -> Dict[str, type]:
    """
    Get dictionary of available agent classes
    
    Returns:
        Dict mapping agent_id to agent class
    """
    agents: Dict[str, type] = {}

    # Add all available agents
    if USER_AGENT_AVAILABLE and UserManagerAgent is not None:
        agents['user_manager'] = UserManagerAgent

    if PROJECT_AGENT_AVAILABLE and ProjectManagerAgent is not None:
        agents['project_manager'] = ProjectManagerAgent

    if SOCRATIC_AGENT_AVAILABLE and SocraticCounselorAgent is not None:
        agents['socratic_counselor'] = SocraticCounselorAgent

    if CODE_AGENT_AVAILABLE and CodeGeneratorAgent is not None:
        agents['code_generator'] = CodeGeneratorAgent

    if CONTEXT_AGENT_AVAILABLE and ContextAnalyzerAgent is not None:
        agents['context_analyzer'] = ContextAnalyzerAgent

    if DOCUMENT_AGENT_AVAILABLE and DocumentProcessorAgent is not None:
        agents['document_processor'] = DocumentProcessorAgent

    if SERVICES_AGENT_AVAILABLE and ServicesAgent is not None:
        agents['services_agent'] = ServicesAgent

    if MONITOR_AGENT_AVAILABLE and SystemMonitorAgent is not None:
        agents['system_monitor'] = SystemMonitorAgent

    return agents


def get_agent_capabilities() -> Dict[str, List[str]]:
    """
    Get capabilities for all agents
    
    Returns:
        Dict mapping agent_id to list of capabilities
    """
    orchestrator = get_orchestrator()

    if orchestrator is not None:
        # Get capabilities from orchestrator's agents
        try:
            capabilities: Dict[str, List[str]] = {}
            for agent_id, agent in orchestrator.agents.items():
                if hasattr(agent, 'get_capabilities'):
                    capabilities[agent_id] = agent.get_capabilities()
                else:
                    capabilities[agent_id] = []
            return capabilities
        except (RuntimeError, AttributeError) as e:
            logger.warning(f"Error getting capabilities from orchestrator: {e}")

    # Fallback: create temporary instances to get capabilities
    available_agents = get_available_agents()
    capabilities: Dict[str, List[str]] = {}

    for agent_id, agent_class in available_agents.items():
        try:
            temp_agent = agent_class()
            if hasattr(temp_agent, 'get_capabilities'):
                capabilities[agent_id] = temp_agent.get_capabilities()
            else:
                capabilities[agent_id] = []
        except (RuntimeError, ValueError, AttributeError, TypeError) as e:
            logger.warning(f"Could not get capabilities for {agent_id}: {e}")
            capabilities[agent_id] = []

    return capabilities


def create_agent(agent_type: str) -> Optional[Any]:
    """
    Create agent instance by type
    
    Args:
        agent_type: Agent type identifier
        
    Returns:
        Agent instance or None
        
    Raises:
        ValueError: If agent type is unknown
    """
    available_agents = get_available_agents()

    if agent_type not in available_agents:
        available_types = list(available_agents.keys())
        raise ValueError(
            f"Unknown agent type: {agent_type}. "
            f"Available: {available_types}"
        )

    agent_class = available_agents[agent_type]
    
    try:
        return agent_class()
    except (RuntimeError, ValueError, AttributeError, TypeError) as e:
        logger.error(f"Failed to create agent {agent_type}: {e}")
        return None


def get_agent_status() -> Dict[str, Any]:
    """
    Get status of all agents
    
    Returns:
        Dict with status information for all agents
    """
    orchestrator = get_orchestrator()

    # Try to get status from orchestrator first
    if orchestrator is not None:
        try:
            return orchestrator.get_agent_status()
        except (RuntimeError, AttributeError) as e:
            logger.warning(f"Could not get status from orchestrator: {e}")

    # Fallback: manual status check
    available_agents = get_available_agents()

    status = {
        'total_available': len(available_agents),
        'agents': {},
        'orchestrator_available': ORCHESTRATOR_AVAILABLE,
        'module_version': __version__,
        'timestamp': None
    }

    for agent_id, agent_class in available_agents.items():
        try:
            temp_agent = agent_class()
            status['agents'][agent_id] = {
                'name': getattr(temp_agent, 'name', agent_id),
                'capabilities': (
                    temp_agent.get_capabilities() 
                    if hasattr(temp_agent, 'get_capabilities') 
                    else []
                ),
                'status': 'available'
            }
        except (RuntimeError, ValueError, AttributeError, TypeError) as e:
            status['agents'][agent_id] = {
                'name': agent_id,
                'capabilities': [],
                'status': f'error: {str(e)}'
            }

    return status


def list_agents() -> List[str]:
    """
    Get list of available agent IDs
    
    Returns:
        List of agent identifiers
    """
    return list(get_available_agents().keys())


def shutdown_agents() -> None:
    """Shutdown all agents gracefully"""
    global _orchestrator

    if _orchestrator is not None:
        try:
            if hasattr(_orchestrator, 'shutdown'):
                _orchestrator.shutdown()
                logger.info("All agents shutdown complete")
            else:
                logger.warning("Orchestrator does not have shutdown method")
        except (RuntimeError, AttributeError) as e:
            logger.error(f"Error during agent shutdown: {e}")
        finally:
            _orchestrator = None
    else:
        logger.debug("No active orchestrator to shutdown")


def get_system_health() -> Dict[str, Any]:
    """
    Get health status of agent system
    
    Returns:
        Dict with health information
    """
    orchestrator = get_orchestrator()

    if orchestrator is not None and hasattr(orchestrator, 'health_check'):
        try:
            return orchestrator.health_check()
        except (RuntimeError, AttributeError) as e:
            logger.error(f"Health check failed: {e}")

    # Fallback health check
    available_agents = get_available_agents()
    
    return {
        'status': 'limited' if len(available_agents) > 0 else 'unavailable',
        'orchestrator_available': ORCHESTRATOR_AVAILABLE,
        'agents_available': len(available_agents),
        'total_agents': 8,
        'message': (
            f"{len(available_agents)}/8 agents available" 
            if len(available_agents) > 0 
            else "No agents available"
        )
    }


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__description__',
    
    # Base class
    'BaseAgent',
    
    # All 8 Agent classes
    'UserManagerAgent',
    'ProjectManagerAgent',
    'SocraticCounselorAgent',
    'CodeGeneratorAgent',
    'ContextAnalyzerAgent',
    'DocumentProcessorAgent',
    'ServicesAgent',
    'SystemMonitorAgent',
    
    # Orchestrator
    'AgentOrchestrator',
    
    # Primary functions
    'get_orchestrator',
    'reset_orchestrator',
    'process_agent_request',
    'process_by_capability',
    
    # Discovery functions
    'get_available_agents',
    'get_agent_capabilities',
    'list_agents',
    
    # Agent management
    'create_agent',
    'get_agent_status',
    'shutdown_agents',
    'get_system_health',
]

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Log initialization
available_count = len(get_available_agents())
logger.info(
    f"Socratic RAG Agents v{__version__} initialized: "
    f"{available_count}/8 agents available"
)

if available_count < 8:
    logger.warning(
        f"Only {available_count}/8 agents available. "
        "Some functionality may be limited."
    )

if ORCHESTRATOR_AVAILABLE:
    logger.info("AgentOrchestrator available - full functionality enabled")
else:
    logger.warning("AgentOrchestrator not available - limited functionality")
