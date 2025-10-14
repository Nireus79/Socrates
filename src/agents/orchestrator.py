#!/usr/bin/env python3
"""
AgentOrchestrator - Central Agent Coordination and Routing
==========================================================

Final agent (8/8) that coordinates all other agents.
Routes requests, manages agent lifecycle, and provides unified interface.

Capabilities:
- Agent request routing by ID or capability
- Multi-agent coordination
- Agent health monitoring
- Capability discovery and mapping
- Event system integration
"""
import logging
from typing import Dict, List, Any, Optional

try:
    from src.core import ServiceContainer
except ImportError:
    ServiceContainer = None


# Define get_logger fallback FIRST (always available)
def get_logger(name: str):
    return logging.getLogger(name)


try:
    from src.core import DateTimeHelper

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    from datetime import datetime


    class DateTimeHelper:
        @staticmethod
        def now():
            return datetime.now()

        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None


class AgentOrchestrator:
    """
    Central orchestrator managing all 8 agents with intelligent routing

    Coordinates:
    1. UserManagerAgent - Authentication and user management
    2. ProjectManagerAgent - Project lifecycle management
    3. SocraticCounselorAgent - Socratic questioning
    4. CodeGeneratorAgent - Code generation
    5. ContextAnalyzerAgent - Context analysis
    6. DocumentProcessorAgent - Document processing
    7. ServicesAgent - Git, export, deployment
    8. SystemMonitorAgent - System monitoring
    """

    def __init__(self, services: Optional[ServiceContainer] = None):
        """Initialize orchestrator and all agents

        Args:
            services: Optional ServiceContainer for dependency injection
        """
        # Store services (even if None - agents will handle gracefully)
        self.services = services

        # Get logger from services or fallback
        if services:
            self.logger = services.get_logger("orchestrator")
        else:
            self.logger = get_logger("orchestrator")

        self.agents: Dict[str, Any] = {}
        self.agent_failures: Dict[str, str] = {}
        self.capability_map: Dict[str, str] = {}

        self.logger.info("Starting AgentOrchestrator initialization")

        # Initialize all 8 agents
        self._initialize_agents()

        # Build capability mapping
        self.capability_map = self._build_capability_map()

        self.logger.info(
            f"AgentOrchestrator initialized: "
            f"{len(self.agents)} agents active, "
            f"{len(self.agent_failures)} failed, "
            f"{len(self.capability_map)} capabilities"
        )

    def _initialize_agents(self) -> None:
        """Initialize all 8 agents with graceful error handling"""
        self.logger.info("Initializing agents...")

        # Agent initialization order matters - user manager first
        agent_configs = [
            ('user_manager', 'user', 'UserManagerAgent'),
            ('project_manager', 'project', 'ProjectManagerAgent'),
            ('socratic_counselor', 'socratic', 'SocraticCounselorAgent'),
            ('code_generator', 'code', 'CodeGeneratorAgent'),
            ('context_analyzer', 'context', 'ContextAnalyzerAgent'),
            ('document_processor', 'document', 'DocumentProcessorAgent'),
            ('services_agent', 'services', 'ServicesAgent'),
            ('system_monitor', 'monitor', 'SystemMonitorAgent'),
        ]

        for agent_id, module_name, class_name in agent_configs:
            self._initialize_single_agent(agent_id, module_name, class_name)

        # Log initialization summary
        success_count = len(self.agents)
        failure_count = len(self.agent_failures)
        total = success_count + failure_count

        self.logger.info(
            f"Agent initialization complete: {success_count}/{total} successful"
        )

        if failure_count > 0:
            self.logger.warning(
                f"Failed agents: {list(self.agent_failures.keys())}"
            )

    def _initialize_single_agent(
            self,
            agent_id: str,
            module_name: str,
            class_name: str
    ) -> None:
        """Initialize a single agent with proper error handling"""
        try:
            self.logger.debug(f"Initializing {class_name}...")

            # Import the agent class dynamically
            agent_class = self._import_agent_class(module_name, class_name)

            if agent_class is None:
                raise ImportError(f"Could not import {class_name}")

            # Instantiate the agent
            agent_instance = agent_class(self.services)

            # Store the agent
            self.agents[agent_id] = agent_instance

            self.logger.info(f"✓ {class_name} initialized successfully")

        except ImportError as e:
            error_msg = f"Failed to import {class_name}: {e}"
            self.agent_failures[agent_id] = error_msg
            self.logger.warning(error_msg)

        except (RuntimeError, ValueError, AttributeError, TypeError) as e:
            error_msg = f"Failed to initialize {class_name}: {e}"
            self.agent_failures[agent_id] = error_msg
            self.logger.error(error_msg)

    def _import_agent_class(self, module_name: str, class_name: str) -> Optional[type]:
        """Dynamically import agent class"""
        try:
            # Import from the agents package
            if module_name == 'user':
                from .user import UserManagerAgent
                return UserManagerAgent
            elif module_name == 'project':
                from .project import ProjectManagerAgent
                return ProjectManagerAgent
            elif module_name == 'socratic':
                from .socratic import SocraticCounselorAgent
                return SocraticCounselorAgent
            elif module_name == 'code':
                from .code import CodeGeneratorAgent
                return CodeGeneratorAgent
            elif module_name == 'context':
                from .context import ContextAnalyzerAgent
                return ContextAnalyzerAgent
            elif module_name == 'document':
                from .document import DocumentProcessorAgent
                return DocumentProcessorAgent
            elif module_name == 'services':
                from .services import ServicesAgent
                return ServicesAgent
            elif module_name == 'monitor':
                from .monitor import SystemMonitorAgent
                return SystemMonitorAgent
            else:
                self.logger.warning(f"Unknown module: {module_name}")
                return None

        except ImportError as e:
            self.logger.warning(f"Could not import {class_name}: {e}")
            return None

    def _build_capability_map(self) -> Dict[str, str]:
        """Build mapping of capabilities to agent IDs"""
        self.logger.debug("Building capability map...")

        capability_map: Dict[str, str] = {}

        for agent_id, agent in self.agents.items():
            try:
                # Get capabilities from agent
                if not hasattr(agent, 'get_capabilities'):
                    self.logger.warning(
                        f"Agent {agent_id} does not have get_capabilities method"
                    )
                    continue

                capabilities = agent.get_capabilities()

                self.logger.debug(
                    f"Agent {agent_id} provides {len(capabilities)} capabilities"
                )

                # Map each capability to this agent
                for capability in capabilities:
                    if capability in capability_map:
                        self.logger.warning(
                            f"Capability '{capability}' provided by multiple agents: "
                            f"{capability_map[capability]} and {agent_id}"
                        )
                    capability_map[capability] = agent_id

            except (RuntimeError, AttributeError) as e:
                self.logger.error(
                    f"Failed to get capabilities from {agent_id}: {e}"
                )

        self.logger.info(f"Built capability map with {len(capability_map)} capabilities")
        return capability_map

    def route_request(
            self,
            agent_id: str,
            action: str,
            data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route request to specific agent by ID

        Args:
            agent_id: Target agent identifier
            action: Action/capability to execute
            data: Request data

        Returns:
            Dict with response from agent
        """
        self.logger.debug(f"Routing request: {agent_id}.{action}")

        try:
            # Validate agent exists
            if agent_id not in self.agents:
                available = list(self.agents.keys())

                self.logger.warning(
                    f"Request for unknown agent '{agent_id}'. "
                    f"Available: {available}"
                )

                return {
                    'success': False,
                    'error': f"Unknown agent: {agent_id}",
                    'error_code': 'UNKNOWN_AGENT',
                    'available_agents': available,
                    'requested_agent': agent_id
                }

            agent = self.agents[agent_id]

            # Validate action is supported
            try:
                if hasattr(agent, 'get_capabilities'):
                    capabilities = agent.get_capabilities()
                    if action not in capabilities:

                        self.logger.warning(
                            f"Unsupported action '{action}' for agent '{agent_id}'"
                        )

                        return {
                            'success': False,
                            'error': f"Agent {agent_id} does not support action: {action}",
                            'error_code': 'UNSUPPORTED_ACTION',
                            'supported_actions': capabilities,
                            'requested_action': action,
                            'agent_id': agent_id
                        }

            except (RuntimeError, AttributeError) as e:
                self.logger.warning(
                    f"Could not verify capabilities for {agent_id}: {e}"
                )
                # Continue anyway - agent might still support the action

            # Route to agent
            self.logger.debug(f"Processing request through {agent_id}")

            start_time = DateTimeHelper.now()
            result = agent.process_request(action, data)

            # Add orchestrator metadata
            if isinstance(result, dict):
                result['orchestrator_metadata'] = {
                    'routed_by': 'orchestrator',
                    'agent_id': agent_id,
                    'action': action,
                    'timestamp': DateTimeHelper.to_iso_string(start_time)
                }

            # Log completion
            success = result.get('success', True) if isinstance(result, dict) else True
            self.logger.info(
                f"Request completed: {agent_id}.{action} (success={success})"
            )

            return result

        except (RuntimeError, ValueError, AttributeError, TypeError) as e:
            error_msg = f"Error routing request to {agent_id}.{action}: {str(e)}"
            self.logger.error(error_msg)

            return {
                'success': False,
                'error': f"Error routing request to {agent_id}.{action}: {str(e)}",
                'error_code': 'ROUTING_ERROR',
                'agent_id': agent_id,
                'action': action,
                'exception_type': type(e).__name__
            }

    def route_by_capability(
            self,
            capability: str,
            data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route request by capability instead of agent ID

        Args:
            capability: Capability name to execute
            data: Request data

        Returns:
            Dict with response from appropriate agent
        """
        self.logger.debug(f"Routing by capability: {capability}")

        try:
            # Check if capability is available
            if capability not in self.capability_map:
                available = list(self.capability_map.keys())
                error_msg = f"No agent supports capability: {capability}"

                self.logger.warning(
                    f"Unsupported capability '{capability}'. "
                    f"Available: {len(available)} capabilities"
                )

                return {
                    'success': False,
                    'error': error_msg,
                    'available_capabilities': available,
                    'requested_capability': capability
                }

            # Get agent that provides this capability
            agent_id = self.capability_map[capability]

            self.logger.debug(
                f"Capability '{capability}' mapped to agent '{agent_id}'"
            )

            # Route to the appropriate agent
            return self.route_request(agent_id, capability, data)

        except (RuntimeError, ValueError, KeyError) as e:
            error_msg = f"Error routing by capability '{capability}': {str(e)}"
            self.logger.error(error_msg)

            return {
                'success': False,
                'error': error_msg,
                'capability': capability,
                'exception_type': type(e).__name__
            }

    def get_agent_status(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of one or all agents

        Args:
            agent_id: Optional specific agent ID, or None for all agents

        Returns:
            Dict with agent status information
        """
        try:
            # Get specific agent status
            if agent_id:
                if agent_id not in self.agents:
                    return {
                        'success': False,
                        'error': f"Agent not found: {agent_id}",
                        'available_agents': list(self.agents.keys())
                    }

                agent = self.agents[agent_id]
                return {
                    'success': True,
                    'agent_id': agent_id,
                    'name': getattr(agent, 'name', agent_id),
                    'status': 'active',
                    'capabilities': (
                        agent.get_capabilities()
                        if hasattr(agent, 'get_capabilities')
                        else []
                    ),
                    'agent_type': type(agent).__name__
                }

            # Get all agents status
            status = {
                'orchestrator_status': 'running',
                'total_agents': len(self.agents),
                'failed_agents': len(self.agent_failures),
                'total_capabilities': len(self.capability_map),
                'agents': {},
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            }

            # Add status for each active agent
            for aid, agent in self.agents.items():
                try:
                    status['agents'][aid] = {
                        'name': getattr(agent, 'name', aid),
                        'status': 'active',
                        'capabilities': (
                            agent.get_capabilities()
                            if hasattr(agent, 'get_capabilities')
                            else []
                        ),
                        'agent_type': type(agent).__name__
                    }
                except (RuntimeError, AttributeError) as e:
                    status['agents'][aid] = {
                        'name': aid,
                        'status': 'error',
                        'error': str(e),
                        'capabilities': []
                    }

            # Add failed agents
            if self.agent_failures:
                status['failed_agent_details'] = self.agent_failures

            return status

        except (RuntimeError, ValueError) as e:
            self.logger.error(f"Error getting agent status: {e}")
            return {
                'success': False,
                'error': f"Status check failed: {str(e)}"
            }

    def get_capabilities(self) -> List[str]:
        """
        Get list of all available capabilities across all agents

        Returns:
            List of capability names
        """
        return list(self.capability_map.keys())

    def get_agents_by_capability(self, capability: str) -> List[str]:
        """
        Get list of agents that provide a specific capability

        Args:
            capability: Capability to search for

        Returns:
            List of agent IDs that provide this capability
        """
        agents_with_capability: List[str] = []

        for agent_id, agent in self.agents.items():
            try:
                if hasattr(agent, 'get_capabilities'):
                    capabilities = agent.get_capabilities()
                    if capability in capabilities:
                        agents_with_capability.append(agent_id)
            except (RuntimeError, AttributeError):
                continue

        return agents_with_capability

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on orchestrator and all agents

        Returns:
            Dict with health status of all agents
        """
        self.logger.debug("Performing orchestrator health check")

        health = {
            'orchestrator': 'healthy',
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
            'total_agents': len(self.agents),
            'healthy_agents': 0,
            'unhealthy_agents': 0,
            'agents': {}
        }

        # Check each agent
        for agent_id, agent in self.agents.items():
            try:
                # Initialize agent_health to avoid reference issues
                agent_health = None

                # Check if agent has health_check method
                if hasattr(agent, 'health_check'):
                    agent_health = agent.health_check()
                    agent_status = agent_health.get('status', 'unknown')
                else:
                    # Agent is active but no health check available
                    agent_status = 'active'

                health['agents'][agent_id] = {
                    'status': agent_status,
                    'name': getattr(agent, 'name', agent_id)
                }

                # ADD DETAILED LOGGING HERE
                if agent_status in ['healthy', 'active']:
                    health['healthy_agents'] += 1
                    self.logger.info(f"✓ Agent health: {agent_id} = {agent_status}")
                else:
                    health['unhealthy_agents'] += 1
                    # Log unhealthy agents at WARNING level with details
                    agent_name = getattr(agent, 'name', agent_id)
                    error_info = agent_health.get('error', 'No error details') if agent_health and isinstance(
                        agent_health, dict) else 'No health check details'
                    self.logger.warning(
                        f"✗ Agent health: {agent_id} ({agent_name}) = {agent_status} | Details: {error_info}"
                    )

            except (RuntimeError, AttributeError) as e:
                health['agents'][agent_id] = {
                    'status': 'error',
                    'error': str(e),
                    'name': getattr(agent, 'name', agent_id)
                }
                health['unhealthy_agents'] += 1
                # ADD DETAILED ERROR LOGGING
                self.logger.error(f"✗ Agent health check failed: {agent_id} | Error: {str(e)}")

        # Add failed agents
        for agent_id, error in self.agent_failures.items():
            health['agents'][agent_id] = {
                'status': 'failed',
                'error': error
            }
            # ADD LOGGING FOR FAILED AGENTS
            self.logger.error(f"✗ Agent failed to initialize: {agent_id} | Error: {error}")

        # Determine overall orchestrator health
        if health['unhealthy_agents'] > 0:
            health['orchestrator'] = 'degraded'
        if health['healthy_agents'] == 0:
            health['orchestrator'] = 'critical'

        self.logger.info(
            f"Health check complete: {health['healthy_agents']} healthy, "
            f"{health['unhealthy_agents']} unhealthy"
        )

        return health

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of all agents with basic info

        Returns:
            List of dicts with agent information
        """
        agents_list: List[Dict[str, Any]] = []

        for agent_id, agent in self.agents.items():
            try:
                agents_list.append({
                    'id': agent_id,
                    'name': getattr(agent, 'name', agent_id),
                    'type': type(agent).__name__,
                    'status': 'active',
                    'capabilities_count': (
                        len(agent.get_capabilities())
                        if hasattr(agent, 'get_capabilities')
                        else 0
                    )
                })
            except (RuntimeError, AttributeError):
                agents_list.append({
                    'id': agent_id,
                    'name': agent_id,
                    'type': 'unknown',
                    'status': 'error',
                    'capabilities_count': 0
                })

        # Add failed agents
        for agent_id, error in self.agent_failures.items():
            agents_list.append({
                'id': agent_id,
                'name': agent_id,
                'type': 'unknown',
                'status': 'failed',
                'error': error,
                'capabilities_count': 0
            })

        return agents_list

    def shutdown(self) -> None:
        """Gracefully shutdown all agents"""
        self.logger.info("Shutting down orchestrator and all agents...")

        for agent_id, agent in self.agents.items():
            try:
                if hasattr(agent, 'shutdown'):
                    agent.shutdown()
                    self.logger.debug(f"Agent {agent_id} shutdown complete")
            except (RuntimeError, AttributeError) as e:
                self.logger.warning(f"Error shutting down {agent_id}: {e}")

        self.agents.clear()
        self.capability_map.clear()
        self.logger.info("Orchestrator shutdown complete")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get orchestrator statistics

        Returns:
            Dict with usage and performance statistics
        """
        stats = {
            'total_agents': len(self.agents),
            'failed_agents': len(self.agent_failures),
            'total_capabilities': len(self.capability_map),
            'agent_list': list(self.agents.keys()),
            'failed_agent_list': list(self.agent_failures.keys()),
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

        # Get per-agent statistics
        agent_stats: Dict[str, Any] = {}
        for agent_id, agent in self.agents.items():
            try:
                if hasattr(agent, 'get_stats'):
                    agent_stats[agent_id] = agent.get_stats()
                else:
                    agent_stats[agent_id] = {
                        'status': 'active',
                        'stats_available': False
                    }
            except (RuntimeError, AttributeError) as e:
                agent_stats[agent_id] = {
                    'status': 'error',
                    'error': str(e)
                }

        stats['agents'] = agent_stats
        return stats


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = ['AgentOrchestrator']
