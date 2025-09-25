#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Agent Orchestrator
==========================================

Central orchestrator for all agents with intelligent request routing.

Manages all 8 agents and provides unified interface for agent operations.
"""

from typing import Dict, List, Any, Optional

from src.core import get_logger, get_event_bus, DateTimeHelper
from .base import BaseAgent

# Import all agent classes (will be available when other files are created)
from .user import UserManagerAgent
from .monitor import SystemMonitorAgent


class AgentOrchestrator:
    """
    Central orchestrator for all agents with intelligent request routing
    """

    def __init__(self):
        self.logger = get_logger("orchestrator")
        self.events = get_event_bus()

        # Initialize agents (some imports will be available after files are created)
        self.agents = {}
        self._initialize_agents()

        # Agent capability mapping
        self.capability_map = self._build_capability_map()

        self.logger.info(f"Agent orchestrator initialized with {len(self.agents)} agents")

    def _initialize_agents(self) -> None:
        """Initialize all available agents"""
        # Initialize agents that are available
        try:
            self.agents['user_manager'] = UserManagerAgent()
            self.logger.info("UserManagerAgent initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize UserManagerAgent: {e}")

        try:
            self.agents['system_monitor'] = SystemMonitorAgent()
            self.logger.info("SystemMonitorAgent initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize SystemMonitorAgent: {e}")

        try:
            from .socratic import SocraticCounselorAgent
            self.agents['socratic_counselor'] = SocraticCounselorAgent()
            self.logger.info("SocraticCounselorAgent initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize SocraticCounselorAgent: {e}")

        try:
            from .code import CodeGeneratorAgent
            self.agents['code_generator'] = CodeGeneratorAgent()
            self.logger.info("CodeGeneratorAgent initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize CodeGeneratorAgent: {e}")

        try:
            from .project import ProjectManagerAgent
            self.agents['project_manager'] = ProjectManagerAgent()
            self.logger.info("ProjectManagerAgent initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize ProjectManagerAgent: {e}")

        try:
            from .context import ContextAnalyzerAgent
            self.agents['context_analyzer'] = ContextAnalyzerAgent()
            self.logger.info("ContextAnalyzerAgent initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize ContextAnalyzerAgent: {e}")

        try:
            from .document import DocumentProcessorAgent
            self.agents['document_processor'] = DocumentProcessorAgent()
            self.logger.info("DocumentProcessorAgent initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize DocumentProcessorAgent: {e}")

        try:
            from .services import ServicesAgent
            self.agents['services_agent'] = ServicesAgent()
            self.logger.info("ServicesAgent initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize ServicesAgent: {e}")

    def _build_capability_map(self) -> Dict[str, str]:
        """Build mapping of capabilities to agents"""
        capability_map = {}

        for agent_id, agent in self.agents.items():
            try:
                for capability in agent.get_capabilities():
                    if capability in capability_map:
                        self.logger.warning(
                            f"Capability '{capability}' is provided by multiple agents: "
                            f"{capability_map[capability]} and {agent_id}"
                        )
                    capability_map[capability] = agent_id
            except Exception as e:
                self.logger.error(f"Failed to get capabilities from agent {agent_id}: {e}")

        self.logger.info(f"Built capability map with {len(capability_map)} capabilities")
        return capability_map

    def route_request(self, agent_id: str, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate agent"""
        # Validate agent exists
        if agent_id not in self.agents:
            available_agents = list(self.agents.keys())
            self.logger.warning(f"Request for unknown agent: {agent_id}")
            return {
                'success': False,
                'error': f"Unknown agent: {agent_id}",
                'available_agents': available_agents,
                'agent_count': len(available_agents)
            }

        agent = self.agents[agent_id]

        # Validate agent supports the action
        try:
            supported_capabilities = agent.get_capabilities()
            if action not in supported_capabilities:
                self.logger.warning(f"Agent {agent_id} does not support action: {action}")
                return {
                    'success': False,
                    'error': f"Agent {agent_id} does not support action: {action}",
                    'supported_actions': supported_capabilities,
                    'requested_action': action
                }
        except Exception as e:
            self.logger.error(f"Failed to get capabilities from agent {agent_id}: {e}")
            return {
                'success': False,
                'error': f"Failed to validate agent capabilities: {str(e)}"
            }

        # Process request through agent
        try:
            self.logger.debug(f"Routing {action} request to {agent_id}")
            result = agent.process_request(action, data)

            # Emit routing event
            self.events.publish_async('request_routed', 'orchestrator', {
                'agent_id': agent_id,
                'action': action,
                'success': result.get('success', False),
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            })

            return result

        except Exception as e:
            self.logger.error(f"Error routing request to {agent_id}.{action}: {e}")
            return {
                'success': False,
                'error': f"Agent request failed: {str(e)}",
                'agent_id': agent_id,
                'action': action,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            }

    def route_by_capability(self, capability: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Route request by capability to appropriate agent"""
        if capability not in self.capability_map:
            available_capabilities = list(self.capability_map.keys())
            self.logger.warning(f"Request for unknown capability: {capability}")
            return {
                'success': False,
                'error': f"Unknown capability: {capability}",
                'available_capabilities': available_capabilities[:10],  # Limit to first 10
                'total_capabilities': len(available_capabilities)
            }

        agent_id = self.capability_map[capability]
        self.logger.debug(f"Routing capability '{capability}' to agent '{agent_id}'")

        return self.route_request(agent_id, capability, data)

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {
            'total_agents': len(self.agents),
            'total_capabilities': len(self.capability_map),
            'agents': {},
            'system_health': 'healthy',
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

        healthy_agents = 0

        for agent_id, agent in self.agents.items():
            try:
                agent_info = {
                    'name': agent.name,
                    'status': 'active',
                    'capabilities': agent.get_capabilities(),
                    'capability_count': len(agent.get_capabilities()),
                    'has_claude': hasattr(agent, 'claude_client') and agent.claude_client is not None
                }

                status['agents'][agent_id] = agent_info
                healthy_agents += 1

            except Exception as e:
                self.logger.error(f"Failed to get status from agent {agent_id}: {e}")
                status['agents'][agent_id] = {
                    'name': getattr(agent, 'name', 'Unknown'),
                    'status': 'error',
                    'error': str(e),
                    'capabilities': [],
                    'capability_count': 0,
                    'has_claude': False
                }

        # Determine overall system health
        if healthy_agents == 0:
            status['system_health'] = 'critical'
        elif healthy_agents < len(self.agents):
            status['system_health'] = 'degraded'
        else:
            status['system_health'] = 'healthy'

        status['healthy_agents'] = healthy_agents

        return status

    def get_capabilities_overview(self) -> Dict[str, Any]:
        """Get overview of all system capabilities"""
        # Categorize capabilities by agent type
        capabilities_by_category = {
            'user_management': [],
            'project_management': [],
            'code_generation': [],
            'analysis': [],
            'documentation': [],
            'monitoring': [],
            'services': [],
            'socratic': [],
            'other': []
        }

        # Agent to category mapping
        agent_categories = {
            'user_manager': 'user_management',
            'project_manager': 'project_management',
            'code_generator': 'code_generation',
            'context_analyzer': 'analysis',
            'document_processor': 'documentation',
            'system_monitor': 'monitoring',
            'services_agent': 'services',
            'socratic_counselor': 'socratic'
        }

        # Categorize capabilities
        for agent_id, agent in self.agents.items():
            try:
                category = agent_categories.get(agent_id, 'other')
                capabilities = agent.get_capabilities()
                capabilities_by_category[category].extend(capabilities)
            except Exception as e:
                self.logger.error(f"Failed to get capabilities from agent {agent_id}: {e}")

        # Calculate totals
        total_capabilities = sum(len(caps) for caps in capabilities_by_category.values())

        return {
            'total_capabilities': total_capabilities,
            'capabilities_by_category': capabilities_by_category,
            'agent_count': len(self.agents),
            'category_breakdown': {
                category: len(caps)
                for category, caps in capabilities_by_category.items()
                if caps  # Only include non-empty categories
            },
            'most_capable_agent': self._get_most_capable_agent(),
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

    def _get_most_capable_agent(self) -> Optional[Dict[str, Any]]:
        """Find the agent with the most capabilities"""
        max_capabilities = 0
        most_capable = None

        for agent_id, agent in self.agents.items():
            try:
                capability_count = len(agent.get_capabilities())
                if capability_count > max_capabilities:
                    max_capabilities = capability_count
                    most_capable = {
                        'agent_id': agent_id,
                        'name': agent.name,
                        'capability_count': capability_count
                    }
            except Exception as e:
                self.logger.error(f"Failed to count capabilities for agent {agent_id}: {e}")

        return most_capable

    def list_available_agents(self) -> Dict[str, Any]:
        """List all available agents with basic info"""
        agents_info = {}

        for agent_id, agent in self.agents.items():
            try:
                agents_info[agent_id] = {
                    'name': agent.name,
                    'capabilities': agent.get_capabilities(),
                    'status': 'active'
                }
            except Exception as e:
                agents_info[agent_id] = {
                    'name': getattr(agent, 'name', 'Unknown'),
                    'capabilities': [],
                    'status': 'error',
                    'error': str(e)
                }

        return {
            'agents': agents_info,
            'total_count': len(agents_info),
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

    def broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast event to all agents that might be interested"""
        self.events.publish_async(event_type, 'orchestrator', data)
        self.logger.info(f"Broadcasted event: {event_type} to {len(self.agents)} agents")

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of orchestrator and agents"""
        health = {
            'orchestrator_status': 'healthy',
            'agents_initialized': len(self.agents),
            'capabilities_mapped': len(self.capability_map),
            'agent_health': {},
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

        # Check health of agents that support health checking
        for agent_id, agent in self.agents.items():
            if hasattr(agent, 'get_capabilities') and 'check_health' in agent.get_capabilities():
                try:
                    agent_health = agent.process_request('check_health', {})
                    health['agent_health'][agent_id] = {
                        'status': 'healthy' if agent_health.get('success') else 'unhealthy',
                        'details': agent_health.get('data', {})
                    }
                except Exception as e:
                    health['agent_health'][agent_id] = {
                        'status': 'error',
                        'error': str(e)
                    }

        # Determine overall orchestrator health
        unhealthy_count = sum(
            1 for status in health['agent_health'].values()
            if status['status'] != 'healthy'
        )

        if unhealthy_count > len(self.agents) // 2:
            health['orchestrator_status'] = 'degraded'
        elif unhealthy_count > 0:
            health['orchestrator_status'] = 'warning'

        health['unhealthy_agents'] = unhealthy_count

        return health

    def shutdown(self) -> None:
        """Shutdown all agents gracefully"""
        self.logger.info("Shutting down agent orchestrator...")

        shutdown_results = {}

        for agent_id, agent in self.agents.items():
            try:
                # Perform cleanup if agent has shutdown method
                if hasattr(agent, 'shutdown'):
                    agent.shutdown()
                    shutdown_results[agent_id] = 'success'
                    self.logger.info(f"Agent {agent_id} shutdown complete")
                else:
                    shutdown_results[agent_id] = 'no_shutdown_method'
                    self.logger.debug(f"Agent {agent_id} has no shutdown method")
            except Exception as e:
                shutdown_results[agent_id] = f'error: {str(e)}'
                self.logger.error(f"Error shutting down agent {agent_id}: {e}")

        # Emit shutdown event
        self.events.publish_async('orchestrator_shutdown', 'orchestrator', {
            'shutdown_results': shutdown_results,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        })

        self.logger.info(f"Agent orchestrator shutdown complete. Results: {shutdown_results}")

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get statistics about request routing"""
        return {
            'total_agents': len(self.agents),
            'total_capabilities': len(self.capability_map),
            'agents_with_capabilities': len([
                agent_id for agent_id, agent in self.agents.items()
                if len(agent.get_capabilities()) > 0
            ]),
            'capability_distribution': {
                agent_id: len(agent.get_capabilities())
                for agent_id, agent in self.agents.items()
            },
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }


# ============================================================================
# GLOBAL ORCHESTRATOR INSTANCE
# ============================================================================

_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


def shutdown_orchestrator() -> None:
    """Shutdown global orchestrator"""
    global _orchestrator
    if _orchestrator:
        _orchestrator.shutdown()
        _orchestrator = None
