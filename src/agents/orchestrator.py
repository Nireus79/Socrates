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
    from src.core import get_logger, get_event_bus, DateTimeHelper, get_config
    from src.database import get_database

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False


    def get_logger(name: str):
        return logging.getLogger(name)


    def get_event_bus():
        return None


    def get_database():
        return None


    def get_config():
        return {}


    DateTimeHelper = None

from .base import BaseAgent


class AgentOrchestrator:
    """
    Central orchestrator for all agents with intelligent request routing
    """

    def __init__(self):
        self.logger = get_logger("orchestrator") if CORE_AVAILABLE else logging.getLogger("orchestrator")
        self.events = get_event_bus() if CORE_AVAILABLE else None
        self.db_service = get_database() if CORE_AVAILABLE else None
        self.config = get_config() if CORE_AVAILABLE else {}

        # Initialize agents dictionary
        self.agents = {}
        self.agent_failures = {}  # Track failed agent initializations

        if self.logger:
            self.logger.info("Starting AgentOrchestrator initialization")

        self._initialize_agents()

        # Agent capability mapping
        self.capability_map = self._build_capability_map()

        if self.logger:
            self.logger.info(f"Agent orchestrator initialized with {len(self.agents)} agents")

    def _initialize_agents(self) -> None:
        """Initialize all available agents with graceful fallbacks"""
        if self.logger:
            self.logger.debug("Beginning agent initialization process")

        # Initialize UserManagerAgent (priority for authentication)
        self._initialize_single_agent('user_manager', 'user', 'UserManagerAgent')

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
            self._initialize_single_agent(agent_id, module_name, class_name)

        # Log final initialization summary
        if self.logger:
            successful_count = len(self.agents)
            failed_count = len(self.agent_failures)
            total_attempted = successful_count + failed_count

            self.logger.info(f"Agent initialization complete: {successful_count}/{total_attempted} successful")
            if failed_count > 0:
                self.logger.warning(f"Failed to initialize {failed_count} agents: {list(self.agent_failures.keys())}")

    def _initialize_single_agent(self, agent_id: str, module_name: str, class_name: str) -> None:
        """Initialize a single agent with proper error handling"""
        if self.logger:
            self.logger.debug(f"Attempting to initialize {class_name}")

        try:
            # Fixed import logic - use proper relative imports
            if module_name == 'user':
                from .user import UserManagerAgent
                agent_class = UserManagerAgent
            elif module_name == 'socratic':
                from .socratic import SocraticCounselorAgent
                agent_class = SocraticCounselorAgent
            elif module_name == 'code':
                from .code import CodeGeneratorAgent
                agent_class = CodeGeneratorAgent
            elif module_name == 'project':
                from .project import ProjectManagerAgent
                agent_class = ProjectManagerAgent
            elif module_name == 'context':
                from .context import ContextAnalyzerAgent
                agent_class = ContextAnalyzerAgent
            elif module_name == 'document':
                from .document import DocumentProcessorAgent
                agent_class = DocumentProcessorAgent
            elif module_name == 'services':
                from .services import ServicesAgent
                agent_class = ServicesAgent
            elif module_name == 'monitor':
                from .monitor import SystemMonitorAgent
                agent_class = SystemMonitorAgent
            else:
                raise ImportError(f"Unknown agent module: {module_name}")

            # Create agent instance
            agent_instance = agent_class()
            self.agents[agent_id] = agent_instance

            if self.logger:
                self.logger.info(f"{class_name} initialized successfully as {agent_id}")

        except ImportError as e:
            error_msg = f"Module {module_name} not available: {e}"
            self.agent_failures[agent_id] = error_msg
            if self.logger:
                self.logger.warning(error_msg)
        except AttributeError as e:
            error_msg = f"Class {class_name} not found in module {module_name}: {e}"
            self.agent_failures[agent_id] = error_msg
            if self.logger:
                self.logger.warning(error_msg)
        except Exception as e:
            error_msg = f"Failed to initialize {class_name}: {e}"
            self.agent_failures[agent_id] = error_msg
            if self.logger:
                self.logger.error(error_msg)

    def _build_capability_map(self) -> Dict[str, str]:
        """Build mapping of capabilities to agents"""
        if self.logger:
            self.logger.debug("Building agent capability map")

        capability_map = {}

        for agent_id, agent in self.agents.items():
            try:
                capabilities = agent.get_capabilities()

                if self.logger:
                    self.logger.debug(f"Agent {agent_id} provides {len(capabilities)} capabilities")

                for capability in capabilities:
                    if capability in capability_map:
                        if self.logger:
                            self.logger.warning(
                                f"Capability '{capability}' is provided by multiple agents: "
                                f"{capability_map[capability]} and {agent_id}"
                            )
                    capability_map[capability] = agent_id

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to get capabilities from agent {agent_id}: {e}")

        if self.logger:
            self.logger.info(f"Built capability map with {len(capability_map)} capabilities")

        return capability_map

    def route_request(self, agent_id: str, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate agent"""
        if self.logger:
            self.logger.debug(f"Routing request: {agent_id}.{action}")

        try:
            # Validate agent exists
            if agent_id not in self.agents:
                available_agents = list(self.agents.keys())
                error_msg = f"Unknown agent: {agent_id}"

                if self.logger:
                    self.logger.warning(f"Request for unknown agent: {agent_id}. Available: {available_agents}")

                return {
                    'success': False,
                    'error': error_msg,
                    'available_agents': available_agents,
                    'agent_count': len(available_agents),
                    'requested_agent': agent_id
                }

            agent = self.agents[agent_id]

            # Validate agent supports the action
            try:
                supported_capabilities = agent.get_capabilities()
                if action not in supported_capabilities:
                    error_msg = f"Agent {agent_id} does not support action: {action}"

                    if self.logger:
                        self.logger.warning(f"Unsupported action: {agent_id}.{action}")

                    return {
                        'success': False,
                        'error': error_msg,
                        'supported_actions': supported_capabilities,
                        'requested_action': action,
                        'agent_id': agent_id
                    }

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to get capabilities from agent {agent_id}: {e}")
                # Continue anyway - agent might support the action

            # Process request through agent
            if self.logger:
                self.logger.debug(f"Processing request through agent {agent_id}")

            start_time = DateTimeHelper.now() if DateTimeHelper else None
            result = agent.process_request(action, data)

            # Add orchestrator metadata to result
            if isinstance(result, dict):
                result['orchestrator_metadata'] = {
                    'routed_by': 'orchestrator',
                    'agent_id': agent_id,
                    'action': action,
                    'timestamp': DateTimeHelper.to_iso_string(start_time) if start_time else None
                }

            # Emit routing event if events are available
            self._emit_routing_event(agent_id, action, result)

            if self.logger:
                success = result.get('success', True) if isinstance(result, dict) else True
                self.logger.info(f"Request completed: {agent_id}.{action} (success: {success})")

            return result

        except Exception as e:
            error_msg = f"Error routing request to {agent_id}.{action}: {str(e)}"

            if self.logger:
                self.logger.error(error_msg)

            return {
                'success': False,
                'error': error_msg,
                'agent_id': agent_id,
                'action': action,
                'exception_type': type(e).__name__
            }

    def _emit_routing_event(self, agent_id: str, action: str, result: Dict[str, Any]) -> None:
        """Emit routing event if event system is available"""
        if not self.events:
            return

        try:
            timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            event_data = {
                'agent_id': agent_id,
                'action': action,
                'success': result.get('success', False) if isinstance(result, dict) else True,
                'timestamp': timestamp
            }

            if hasattr(self.events, 'publish_async'):
                self.events.publish_async('request_routed', 'orchestrator', event_data)
            elif hasattr(self.events, 'emit'):
                self.events.emit('request_routed', 'orchestrator', event_data)
            else:
                if self.logger:
                    self.logger.debug("Event system available but no known publish method")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to emit routing event: {e}")

    def route_by_capability(self, capability: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Route request by capability instead of specific agent"""
        if self.logger:
            self.logger.debug(f"Routing by capability: {capability}")

        try:
            if capability not in self.capability_map:
                available_capabilities = list(self.capability_map.keys())
                error_msg = f"No agent supports capability: {capability}"

                if self.logger:
                    self.logger.warning(f"Unsupported capability: {capability}")

                return {
                    'success': False,
                    'error': error_msg,
                    'available_capabilities': available_capabilities,
                    'requested_capability': capability
                }

            agent_id = self.capability_map[capability]

            if self.logger:
                self.logger.debug(f"Capability {capability} mapped to agent {agent_id}")

            return self.route_request(agent_id, capability, data)

        except Exception as e:
            error_msg = f"Error routing by capability {capability}: {str(e)}"

            if self.logger:
                self.logger.error(error_msg)

            return {
                'success': False,
                'error': error_msg,
                'capability': capability,
                'exception_type': type(e).__name__
            }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        if self.logger:
            self.logger.debug("Getting agent status")

        try:
            status = {
                'orchestrator_status': 'running',
                'total_agents': len(self.agents),
                'failed_agents': len(self.agent_failures),
                'agents': {},
                'capabilities': len(self.capability_map),
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            }

            # Get status for each active agent
            for agent_id, agent in self.agents.items():
                try:
                    agent_status = {
                        'name': getattr(agent, 'name', agent_id),
                        'status': 'active',
                        'capabilities': agent.get_capabilities() if hasattr(agent, 'get_capabilities') else [],
                        'agent_type': type(agent).__name__
                    }
                    status['agents'][agent_id] = agent_status

                except Exception as e:
                    status['agents'][agent_id] = {
                        'name': agent_id,
                        'status': 'error',
                        'error': str(e),
                        'capabilities': []
                    }

            # Add failed agent information
            for agent_id, error_msg in self.agent_failures.items():
                status['agents'][agent_id] = {
                    'name': agent_id,
                    'status': 'failed',
                    'error': error_msg,
                    'capabilities': []
                }

            if self.logger:
                self.logger.debug(
                    f"Agent status compiled: {status['total_agents']} active, {status['failed_agents']} failed")

            return status

        except Exception as e:
            error_msg = f"Error getting agent status: {str(e)}"

            if self.logger:
                self.logger.error(error_msg)

            return {
                'orchestrator_status': 'error',
                'error': error_msg,
                'exception_type': type(e).__name__
            }

    def get_available_capabilities(self) -> List[str]:
        """Get list of all available capabilities across agents"""
        if self.logger:
            self.logger.debug("Getting available capabilities")

        try:
            capabilities = list(self.capability_map.keys())

            if self.logger:
                self.logger.debug(f"Found {len(capabilities)} available capabilities")

            return sorted(capabilities)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting capabilities: {e}")
            return []

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on orchestrator and all agents"""
        if self.logger:
            self.logger.debug("Performing orchestrator health check")

        try:
            health = {
                'status': 'healthy',
                'orchestrator': {
                    'status': 'healthy',
                    'agents_loaded': len(self.agents),
                    'agents_failed': len(self.agent_failures),
                    'capabilities_mapped': len(self.capability_map)
                },
                'agents': {},
                'overall_score': 0,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            }

            agent_health_scores = []

            # Check each agent
            for agent_id, agent in self.agents.items():
                try:
                    # Basic agent health check
                    agent_health = {
                        'status': 'healthy',
                        'responsive': True,
                        'capabilities_count': len(agent.get_capabilities()) if hasattr(agent, 'get_capabilities') else 0
                    }

                    # Try to call a basic method to test responsiveness
                    if hasattr(agent, 'get_capabilities'):
                        agent.get_capabilities()

                    health['agents'][agent_id] = agent_health
                    agent_health_scores.append(100)

                except Exception as e:
                    health['agents'][agent_id] = {
                        'status': 'unhealthy',
                        'responsive': False,
                        'error': str(e),
                        'capabilities_count': 0
                    }
                    agent_health_scores.append(0)

                    if self.logger:
                        self.logger.warning(f"Agent {agent_id} failed health check: {e}")

            # Calculate overall health score (as percentage)
            if agent_health_scores:
                health['overall_score'] = float(sum(agent_health_scores) / len(agent_health_scores))
            else:
                health['overall_score'] = 0.0

            # Determine overall status
            if health['overall_score'] >= 80:
                health['status'] = 'healthy'
            elif health['overall_score'] >= 50:
                health['status'] = 'degraded'
            else:
                health['status'] = 'unhealthy'

            if self.logger:
                self.logger.info(f"Health check complete: {health['status']} (score: {health['overall_score']:.1f})")

            return health

        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"

            if self.logger:
                self.logger.error(error_msg)

            return {
                'status': 'error',
                'error': error_msg,
                'exception_type': type(e).__name__
            }

    def shutdown(self) -> Dict[str, Any]:
        """Gracefully shutdown all agents"""
        if self.logger:
            self.logger.info("Starting orchestrator shutdown")

        try:
            shutdown_results = {}

            for agent_id, agent in self.agents.items():
                try:
                    # If agent has shutdown method, call it
                    if hasattr(agent, 'shutdown'):
                        agent.shutdown()
                        shutdown_results[agent_id] = 'success'
                        if self.logger:
                            self.logger.debug(f"Agent {agent_id} shutdown successfully")
                    else:
                        shutdown_results[agent_id] = 'no_shutdown_method'
                        if self.logger:
                            self.logger.debug(f"Agent {agent_id} has no shutdown method")

                except Exception as e:
                    shutdown_results[agent_id] = f'error: {str(e)}'
                    if self.logger:
                        self.logger.error(f"Error shutting down agent {agent_id}: {e}")

            # Clear internal state
            self.agents.clear()
            self.capability_map.clear()
            self.agent_failures.clear()

            result = {
                'status': 'shutdown_complete',
                'agents_shutdown': len(shutdown_results),
                'shutdown_results': shutdown_results,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            }

            if self.logger:
                self.logger.info("Orchestrator shutdown complete")

            return result

        except Exception as e:
            error_msg = f"Error during shutdown: {str(e)}"

            if self.logger:
                self.logger.error(error_msg)

            return {
                'status': 'shutdown_error',
                'error': error_msg,
                'exception_type': type(e).__name__
            }
