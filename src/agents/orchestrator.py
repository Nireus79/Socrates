#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Agent Orchestrator
==========================================

Central orchestrator for all agents with intelligent request routing.
Manages all agents and provides unified interface for agent operations.
"""

from typing import Dict, List, Any, Optional
import logging

# Import core system components with fallbacks
try:
    from src.core import get_logger, get_event_bus, DateTimeHelper

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    get_logger = lambda x: logging.getLogger(x)
    get_event_bus = lambda: None
    DateTimeHelper = None

from .base import BaseAgent


class AgentOrchestrator:
    """
    Central orchestrator for all agents with intelligent request routing
    """

    def __init__(self):
        self.logger = get_logger("orchestrator") if CORE_AVAILABLE else logging.getLogger("orchestrator")
        self.events = get_event_bus() if CORE_AVAILABLE else None

        # Initialize agents dictionary
        self.agents = {}
        self._initialize_agents()

        # Agent capability mapping
        self.capability_map = self._build_capability_map()

        self.logger.info(f"Agent orchestrator initialized with {len(self.agents)} agents")

    def _initialize_agents(self) -> None:
        """Initialize all available agents with graceful fallbacks"""

        # Initialize UserManagerAgent (priority for authentication)
        try:
            from .user import UserManagerAgent
            self.agents['user_manager'] = UserManagerAgent()
            self.logger.info("UserManagerAgent initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize UserManagerAgent: {e}")

        # Initialize other agents with individual try/catch blocks
        agent_configs = [
            ('socratic_counselor', 'socratic', 'SocraticCounselorAgent'),
            ('code_generator', 'code', 'CodeGeneratorAgent'),
            ('project_manager', 'project', 'ProjectManagerAgent'),
            ('context_analyzer', 'context', 'ContextAnalyzerAgent'),
            ('document_processor', 'document', 'DocumentProcessorAgent'),
            ('services_agent', 'services', 'ServicesAgent'),
            ('system_monitor', 'monitor', 'SystemMonitorAgent'),
        ]

        for agent_id, module_name, class_name in agent_configs:
            try:
                module = __import__(f'.{module_name}', package='src.agents', level=0)
                agent_class = getattr(module, class_name)
                self.agents[agent_id] = agent_class()
                self.logger.info(f"{class_name} initialized")
            except ImportError as e:
                self.logger.warning(f"Module {module_name} not available: {e}")
            except AttributeError as e:
                self.logger.warning(f"Class {class_name} not found in module {module_name}: {e}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {class_name}: {e}")

    def _build_capability_map(self) -> Dict[str, str]:
        """Build mapping of capabilities to agents"""
        capability_map = {}

        for agent_id, agent in self.agents.items():
            try:
                capabilities = agent.get_capabilities()
                for capability in capabilities:
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
        try:
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
                # Continue anyway - agent might support the action

            # Process request through agent
            self.logger.debug(f"Routing {action} request to {agent_id}")
            result = agent.process_request(action, data)

            # Emit routing event if events are available
            if self.events:
                try:
                    timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
                    event_data = {
                        'agent_id': agent_id,
                        'action': action,
                        'success': result.get('success', False),
                        'timestamp': timestamp
                    }

                    if hasattr(self.events, 'publish_async'):
                        self.events.publish_async('request_routed', 'orchestrator', event_data)
                    elif hasattr(self.events, 'emit'):
                        self.events.emit('request_routed', 'orchestrator', event_data)
                except Exception as e:
                    self.logger.warning(f"Failed to emit routing event: {e}")

            return result

        except Exception as e:
            self.logger.error(f"Error routing request to {agent_id}.{action}: {e}")
            timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            return {
                'success': False,
                'error': f"Agent request failed: {str(e)}",
                'agent_id': agent_id,
                'action': action,
                'timestamp': timestamp
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

    def get_agent_status(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of specific agent or all agents"""
        timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

        if agent_id:
            # Get status of specific agent
            if agent_id not in self.agents:
                return {
                    'success': False,
                    'error': f"Unknown agent: {agent_id}",
                    'available_agents': list(self.agents.keys()),
                    'timestamp': timestamp
                }

            agent = self.agents[agent_id]
            try:
                return {
                    'agent_id': agent_id,
                    'name': getattr(agent, 'name', 'Unknown'),
                    'status': 'active',
                    'capabilities': agent.get_capabilities(),
                    'capability_count': len(agent.get_capabilities()),
                    'has_claude': hasattr(agent, 'claude_client') and agent.claude_client is not None,
                    'timestamp': timestamp
                }
            except Exception as e:
                return {
                    'agent_id': agent_id,
                    'name': getattr(agent, 'name', 'Unknown'),
                    'status': 'error',
                    'error': str(e),
                    'timestamp': timestamp
                }

        # Get status of all agents
        status = {
            'total_agents': len(self.agents),
            'total_capabilities': len(self.capability_map),
            'agents': {},
            'system_health': 'healthy',
            'timestamp': timestamp
        }

        healthy_agents = 0

        for aid, agent in self.agents.items():
            try:
                agent_info = {
                    'name': getattr(agent, 'name', 'Unknown'),
                    'status': 'active',
                    'capabilities': agent.get_capabilities(),
                    'capability_count': len(agent.get_capabilities()),
                    'has_claude': hasattr(agent, 'claude_client') and agent.claude_client is not None
                }

                status['agents'][aid] = agent_info
                healthy_agents += 1

            except Exception as e:
                self.logger.error(f"Failed to get status from agent {aid}: {e}")
                status['agents'][aid] = {
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

        timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

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
            'timestamp': timestamp
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
                        'name': getattr(agent, 'name', 'Unknown'),
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
                    'name': getattr(agent, 'name', 'Unknown'),
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

        timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

        return {
            'agents': agents_info,
            'total_count': len(agents_info),
            'timestamp': timestamp
        }

    def broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast event to all agents that might be interested"""
        if self.events:
            try:
                if hasattr(self.events, 'publish_async'):
                    self.events.publish_async(event_type, 'orchestrator', data)
                elif hasattr(self.events, 'emit'):
                    self.events.emit(event_type, 'orchestrator', data)
                self.logger.info(f"Broadcasted event: {event_type} to {len(self.agents)} agents")
            except Exception as e:
                self.logger.error(f"Failed to broadcast event {event_type}: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of orchestrator and agents"""
        timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

        health = {
            'orchestrator_status': 'healthy',
            'agents_initialized': len(self.agents),
            'capabilities_mapped': len(self.capability_map),
            'agent_health': {},
            'timestamp': timestamp
        }

        # Check health of agents that support health checking
        for agent_id, agent in self.agents.items():
            try:
                if hasattr(agent, 'get_capabilities') and 'health_check' in agent.get_capabilities():
                    agent_health = agent.process_request('health_check', {})
                    health['agent_health'][agent_id] = {
                        'status': 'healthy' if agent_health.get('success') else 'unhealthy',
                        'details': agent_health.get('data', {})
                    }
                else:
                    # Agent doesn't support health check, assume healthy if it responds
                    health['agent_health'][agent_id] = {
                        'status': 'healthy',
                        'details': {'note': 'No health check capability'}
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

    def shutdown_all(self) -> None:
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
        if self.events:
            try:
                timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
                event_data = {
                    'shutdown_results': shutdown_results,
                    'timestamp': timestamp
                }

                if hasattr(self.events, 'publish_async'):
                    self.events.publish_async('orchestrator_shutdown', 'orchestrator', event_data)
                elif hasattr(self.events, 'emit'):
                    self.events.emit('orchestrator_shutdown', 'orchestrator', event_data)
            except Exception as e:
                self.logger.error(f"Failed to emit shutdown event: {e}")

        self.logger.info(f"Agent orchestrator shutdown complete. Results: {shutdown_results}")

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get statistics about request routing"""
        timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

        try:
            capability_distribution = {}
            for agent_id, agent in self.agents.items():
                try:
                    capability_distribution[agent_id] = len(agent.get_capabilities())
                except Exception:
                    capability_distribution[agent_id] = 0

            agents_with_capabilities = len([
                agent_id for agent_id, count in capability_distribution.items()
                if count > 0
            ])

            return {
                'total_agents': len(self.agents),
                'total_capabilities': len(self.capability_map),
                'agents_with_capabilities': agents_with_capabilities,
                'capability_distribution': capability_distribution,
                'timestamp': timestamp
            }
        except Exception as e:
            self.logger.error(f"Error getting routing statistics: {e}")
            return {
                'total_agents': len(self.agents),
                'total_capabilities': 0,
                'agents_with_capabilities': 0,
                'capability_distribution': {},
                'error': str(e),
                'timestamp': timestamp
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
        _orchestrator.shutdown_all()
        _orchestrator = None
