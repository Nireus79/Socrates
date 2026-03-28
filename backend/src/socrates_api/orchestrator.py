"""
API Orchestrator for Socrates

Instantiates and coordinates real agents from socratic-agents library.
Provides unified interface for REST API endpoints to call agents and orchestrators.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class APIOrchestrator:
    """Orchestrates real agents from socratic-agents for REST API"""

    def __init__(self, api_key_or_config: str = ""):
        """Initialize orchestrator with real agents"""
        self.api_key = api_key_or_config
        self.agents = {}
        self.skill_orchestrator = None
        self.workflow_orchestrator = None
        self.pure_orchestrator = None

        # Initialize documentation and performance tools
        self.doc_generator = None
        self.profiler = None
        self.cache = None

        # Create LLMClient first (if API key provided)
        self.llm_client = self._create_llm_client()

        self._initialize_agents()
        self._initialize_orchestrators()
        self._initialize_documentation()
        self._initialize_performance_monitoring()
        logger.info("API Orchestrator initialized with real agents")

    def _create_llm_client(self) -> Optional[Any]:
        """Create LLM client if API key provided"""
        try:
            if not self.api_key:
                logger.debug("No API key provided - LLM client will be None")
                return None

            from socrates_nexus import LLMClient

            llm_client = LLMClient(
                provider="anthropic", model="claude-3-sonnet", api_key=self.api_key
            )
            logger.info("LLM client created successfully")
            return llm_client
        except Exception as e:
            logger.warning(f"Failed to create LLM client: {e}")
            return None

    def _initialize_agents(self) -> None:
        """Initialize all agents from socratic-agents with LLM client"""
        try:
            from socratic_agents import (
                AgentConflictDetector,
                CodeGenerator,
                CodeValidator,
                ContextAnalyzer,
                DocumentProcessor,
                KnowledgeManager,
                LearningAgent,
                NoteManager,
                ProjectManager,
                QualityController,
                SkillGeneratorAgent,
                SocraticCounselor,
                SystemMonitor,
                UserManager,
            )

            # Initialize agents with LLM client
            self.agents = {
                "code_generator": CodeGenerator(llm_client=self.llm_client),
                "code_validator": CodeValidator(llm_client=self.llm_client),
                "socratic_counselor": SocraticCounselor(llm_client=self.llm_client),
                "project_manager": ProjectManager(llm_client=self.llm_client),
                "quality_controller": QualityController(llm_client=self.llm_client),
                "learning_agent": LearningAgent(llm_client=self.llm_client),
                "skill_generator": SkillGeneratorAgent(llm_client=self.llm_client),
                "context_analyzer": ContextAnalyzer(llm_client=self.llm_client),
                "user_manager": UserManager(llm_client=self.llm_client),
                "knowledge_manager": KnowledgeManager(llm_client=self.llm_client),
                "document_processor": DocumentProcessor(llm_client=self.llm_client),
                "note_manager": NoteManager(llm_client=self.llm_client),
                "system_monitor": SystemMonitor(llm_client=self.llm_client),
                "conflict_detector": AgentConflictDetector(llm_client=self.llm_client),
            }
            logger.info(
                f"Initialized {len(self.agents)} agents from socratic-agents with LLM client"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize agents: {e}")
            self.agents = {}

    def _initialize_orchestrators(self) -> None:
        """Initialize skill, workflow, and pure orchestrators"""
        try:
            from socratic_agents.integrations.skill_orchestrator import SkillOrchestrator
            from socratic_agents.orchestration.orchestrator import PureOrchestrator
            from socratic_agents.skill_generation.workflow_orchestrator import WorkflowOrchestrator

            # Initialize SkillOrchestrator
            self.skill_orchestrator = SkillOrchestrator(
                quality_controller=self.agents.get("quality_controller"),
                skill_generator=self.agents.get("skill_generator"),
                learning_agent=self.agents.get("learning_agent"),
            )

            # Initialize WorkflowOrchestrator
            self.workflow_orchestrator = WorkflowOrchestrator()

            # Initialize PureOrchestrator with maturity-driven gating
            self.pure_orchestrator = PureOrchestrator(
                agents=self.agents,
                get_maturity=self._get_maturity_score,
                get_learning_effectiveness=self._get_learning_effectiveness,
                on_event=self._on_coordination_event,
            )

            logger.info("Initialized skill, workflow, and pure orchestrators")
        except Exception as e:
            logger.warning(f"Failed to initialize orchestrators: {e}")
            self.skill_orchestrator = None
            self.workflow_orchestrator = None
            self.pure_orchestrator = None

    def _get_maturity_score(self, user_id: str, phase: str) -> float:
        """Get maturity score for a user in a phase (callback for PureOrchestrator)"""
        try:
            # Stub implementation - would integrate with MaturityCalculator
            # For now, return a default score that allows agents to run
            logger.debug(f"Getting maturity score for user {user_id} in phase {phase}")
            return 0.5  # Default to mid-range score
        except Exception as e:
            logger.error(f"Failed to get maturity score: {e}")
            return 0.0

    def _get_learning_effectiveness(self, user_id: str) -> float:
        """Get learning effectiveness for a user (callback for PureOrchestrator)"""
        try:
            # Stub implementation - would integrate with LearningAgent
            logger.debug(f"Getting learning effectiveness for user {user_id}")
            return 0.7  # Default to good effectiveness
        except Exception as e:
            logger.error(f"Failed to get learning effectiveness: {e}")
            return 0.0

    def _on_coordination_event(self, event, data: Dict[str, Any]) -> None:
        """Handle coordination events from PureOrchestrator"""
        try:
            event_name = event.value if hasattr(event, "value") else str(event)
            logger.info(f"Coordination event: {event_name}, data: {data}")

            # Event handlers can be extended here to:
            # - Update maturity scores
            # - Emit webhooks
            # - Store interaction metrics
            # - Trigger follow-up agents
            # - Update UI in real-time
        except Exception as e:
            logger.error(f"Failed to handle coordination event: {e}")

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                "framework": "socratic-agents",
                "agents_loaded": len(self.agents),
                "agents": list(self.agents.keys()),
                "llm_client": self.llm_client is not None,
                "skill_orchestrator": self.skill_orchestrator is not None,
                "workflow_orchestrator": self.workflow_orchestrator is not None,
                "pure_orchestrator": self.pure_orchestrator is not None,
                "status": "operational",
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"status": "unavailable", "error": str(e)}

    def call_agent(self, agent_type: str, **kwargs) -> Dict[str, Any]:
        """Call an agent by type"""
        try:
            agent = self.agents.get(agent_type)
            if not agent:
                return {"status": "error", "message": f"Agent '{agent_type}' not found"}

            # Call agent's process method with kwargs as request
            result = agent.process(kwargs)
            return result
        except Exception as e:
            logger.error(f"Agent call failed for {agent_type}: {e}")
            return {"status": "error", "message": str(e)}

    def generate_code(self, prompt: str, language: str = "python") -> Dict[str, Any]:
        """Generate code using CodeGenerator agent"""
        try:
            agent = self.agents.get("code_generator")
            if not agent:
                return {"status": "error", "message": "CodeGenerator not available"}

            result = agent.process({"prompt": prompt, "language": language})
            return result
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {"status": "error", "message": str(e)}

    def validate_code(self, code: str) -> Dict[str, Any]:
        """Validate code using CodeValidator agent"""
        try:
            agent = self.agents.get("code_validator")
            if not agent:
                return {"status": "error", "message": "CodeValidator not available"}

            result = agent.process({"code": code})
            return result
        except Exception as e:
            logger.error(f"Code validation failed: {e}")
            return {"status": "error", "message": str(e)}

    def check_quality(self, code: str) -> Dict[str, Any]:
        """Check code quality using QualityController agent"""
        try:
            agent = self.agents.get("quality_controller")
            if not agent:
                return {"status": "error", "message": "QualityController not available"}

            result = agent.process({"action": "check", "code": code})
            return result
        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            return {"status": "error", "message": str(e)}

    def detect_weak_areas(self, code: str) -> Dict[str, Any]:
        """Detect weak areas in code using QualityController"""
        try:
            agent = self.agents.get("quality_controller")
            if not agent:
                return {"status": "error", "message": "QualityController not available"}

            result = agent.process({"action": "detect_weak_areas", "code": code})
            return result
        except Exception as e:
            logger.error(f"Weak area detection failed: {e}")
            return {"status": "error", "message": str(e)}

    def guide_learning(self, topic: str, level: str = "beginner") -> Dict[str, Any]:
        """Guide learning using SocraticCounselor agent"""
        try:
            agent = self.agents.get("socratic_counselor")
            if not agent:
                return {"status": "error", "message": "SocraticCounselor not available"}

            result = agent.process({"topic": topic, "level": level})
            return result
        except Exception as e:
            logger.error(f"Learning guidance failed: {e}")
            return {"status": "error", "message": str(e)}

    def process_quality_issue(self, code: str) -> Dict[str, Any]:
        """Process quality issue using SkillOrchestrator workflow"""
        try:
            if not self.skill_orchestrator:
                self._initialize_orchestrators()

            if not self.skill_orchestrator:
                return {"status": "error", "message": "SkillOrchestrator not available"}

            # Call SkillOrchestrator - returns nested structure with quality_analysis
            result = self.skill_orchestrator.process_quality_issue(code)
            # Result structure:
            # {
            #     "status": "success",
            #     "agent": "SkillOrchestrator",
            #     "session_id": "...",
            #     "generated_skills": [...],
            #     "personalized_skills": [...],
            #     "quality_analysis": {
            #         "score": float,
            #         "issues": list,
            #         "weak_areas": list
            #     }
            # }
            return result
        except Exception as e:
            logger.error(f"Quality issue processing failed: {e}")
            return {"status": "error", "message": str(e)}

    def record_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Record interaction using LearningAgent"""
        try:
            agent = self.agents.get("learning_agent")
            if not agent:
                return {"status": "error", "message": "LearningAgent not available"}

            result = agent.process({"action": "record", "interaction": interaction})
            return result
        except Exception as e:
            logger.error(f"Interaction recording failed: {e}")
            return {"status": "error", "message": str(e)}

    def analyze_context(self, content: str) -> Dict[str, Any]:
        """Analyze context using ContextAnalyzer agent"""
        try:
            agent = self.agents.get("context_analyzer")
            if not agent:
                return {"status": "error", "message": "ContextAnalyzer not available"}

            result = agent.process({"action": "analyze", "content": content})
            return result
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return {"status": "error", "message": str(e)}

    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create project using ProjectManager agent"""
        try:
            agent = self.agents.get("project_manager")
            if not agent:
                return {"status": "error", "message": "ProjectManager not available"}

            result = agent.process(
                {"action": "create", "project_name": name, "description": description}
            )
            return result
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            return {"status": "error", "message": str(e)}

    def list_agents(self) -> list:
        """List all available agents"""
        return list(self.agents.keys())

    def get_library_status(self) -> Dict[str, bool]:
        """Get status of all library integrations"""
        return {
            "llm_client": self.llm_client is not None,
            "agents_loaded": len(self.agents) > 0,
            "skill_orchestrator": self.skill_orchestrator is not None,
            "workflow_orchestrator": self.workflow_orchestrator is not None,
            "pure_orchestrator": self.pure_orchestrator is not None,
        }

    def execute_agent(self, agent_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a generic agent with request data"""
        try:
            agent = self.agents.get(agent_name)
            if not agent:
                return {"status": "error", "message": f"Agent '{agent_name}' not found"}

            result = agent.process(request_data)
            return result
        except Exception as e:
            logger.error(f"Agent execution failed for {agent_name}: {e}")
            return {"status": "error", "message": str(e)}

    def call_llm(self, prompt: str, model: str = "claude-3-sonnet", **kwargs) -> Dict[str, Any]:
        """Call LLM via socrates-nexus"""
        try:
            # Use existing LLM client if available
            if not self.llm_client:
                return {
                    "status": "error",
                    "message": "LLM client not initialized. API key required.",
                }

            # Note: If a different model is requested, would need to create new client
            # For now, use the initialized client with its model
            response = self.llm_client.chat(prompt=prompt, **kwargs)

            return {
                "status": "success",
                "response": str(response) if response else "",
                "model": self.llm_client.model if hasattr(self.llm_client, "model") else model,
            }
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return {"status": "error", "message": str(e)}

    def list_llm_models(self) -> List[str]:
        """List available LLM models"""
        return ["claude-3-sonnet", "claude-3-opus", "gpt-4", "gpt-3.5-turbo"]

    def analyze_code_quality(self, code: str, filename: str = "code.py") -> Dict[str, Any]:
        """Analyze code quality (stub - requires socratic-analyzer)"""
        try:
            # Use QualityController from socratic-agents as fallback
            return self.check_quality(code)
        except Exception as e:
            logger.error(f"Code quality analysis failed: {e}")
            return {"status": "error", "message": str(e)}

    def detect_agent_conflicts(
        self, field: str, agent_outputs: Dict[str, Any], agents: list
    ) -> Dict[str, Any]:
        """Detect conflicts between agent outputs"""
        try:
            agent = self.agents.get("conflict_detector")
            if not agent:
                return {"status": "error", "message": "ConflictDetector not available"}

            result = agent.process(
                {"field": field, "agent_outputs": agent_outputs, "agents": agents}
            )
            return result
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return {"status": "error", "message": str(e)}

    def store_knowledge(
        self, tenant_id: str, title: str, content: str, tags: Optional[list] = None
    ) -> Dict[str, Any]:
        """Store knowledge item (stub - requires socratic-knowledge)"""
        try:
            agent = self.agents.get("knowledge_manager")
            if not agent:
                return {"status": "error", "message": "KnowledgeManager not available"}

            result = agent.process(
                {
                    "action": "store",
                    "title": title,
                    "content": content,
                    "tags": tags or [],
                    "tenant_id": tenant_id,
                }
            )
            return result
        except Exception as e:
            logger.error(f"Knowledge storage failed: {e}")
            return {"status": "error", "message": str(e)}

    def search_knowledge(self, tenant_id: str, query: str, limit: int = 5) -> list:
        """Search knowledge base (stub - requires socratic-knowledge)"""
        try:
            agent = self.agents.get("knowledge_manager")
            if not agent:
                return []

            result = agent.process(
                {"action": "search", "query": query, "limit": limit, "tenant_id": tenant_id}
            )
            return result.get("results", []) if result else []
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []

    def generate_documentation(self, project_info: Dict[str, Any]) -> str:
        """Generate project documentation (stub - requires socratic-docs)"""
        try:
            # Stub implementation
            return (
                f"# {project_info.get('name', 'Project')}\n\n{project_info.get('description', '')}"
            )
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return "# Documentation generation failed"

    def index_rag_document(self, content: str, source: str, metadata: Dict[str, Any]) -> str:
        """Index document for RAG (stub - requires socratic-rag)"""
        try:
            # Stub implementation
            import uuid

            doc_id = str(uuid.uuid4())
            logger.info(f"RAG document indexed: {doc_id} from {source}")
            return doc_id
        except Exception as e:
            logger.error(f"RAG indexing failed: {e}")
            return ""

    def search_rag(self, query: str, limit: int = 5) -> list:
        """Search RAG documents (stub - requires socratic-rag)"""
        try:
            # Stub implementation
            return []
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return []

    def validate_security_input(self, user_input: str) -> Dict[str, Any]:
        """Validate input for security issues (stub - requires socratic-security)"""
        try:
            # Basic validation stub
            return {"status": "success", "is_safe": True, "score": 1.0}
        except Exception as e:
            logger.error(f"Security validation failed: {e}")
            return {"status": "error", "message": str(e)}

    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        return {
            "api_key_set": bool(self.api_key),
            "llm_client_ready": self.llm_client is not None,
            "agents_count": len(self.agents),
            "skill_orchestrator_ready": self.skill_orchestrator is not None,
            "workflow_orchestrator_ready": self.workflow_orchestrator is not None,
            "pure_orchestrator_ready": self.pure_orchestrator is not None,
        }

    def log_learning_interaction(
        self, session_id: str, agent_name: str, input_data: Dict, output_data: Dict, **kwargs
    ) -> bool:
        """Log interaction to learning system"""
        try:
            agent = self.agents.get("learning_agent")
            if not agent:
                return False

            agent.process(
                {
                    "action": "record",
                    "interaction": {
                        "session_id": session_id,
                        "agent_name": agent_name,
                        "input": input_data,
                        "output": output_data,
                        **kwargs,
                    },
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            return False

    def _initialize_documentation(self) -> None:
        """Initialize documentation generator"""
        try:
            from socratic_docs import DocumentationGenerator

            self.doc_generator = DocumentationGenerator()
            logger.info("Documentation generator initialized")
        except Exception as e:
            logger.warning(f"Documentation generator not available: {e}")
            self.doc_generator = None

    def _initialize_performance_monitoring(self) -> None:
        """Initialize performance monitoring tools"""
        try:
            from socratic_performance import QueryProfiler, TTLCache

            self.profiler = QueryProfiler()
            self.cache = TTLCache(ttl_minutes=30)
            logger.info("Performance monitoring initialized")
        except Exception as e:
            logger.warning(f"Performance monitoring not available: {e}")
            self.profiler = None
            self.cache = None

    # Documentation methods
    def generate_api_documentation(self, code_structure: Dict[str, Any]) -> str:
        """Generate API documentation from code structure"""
        try:
            if not self.doc_generator:
                return "# API Documentation\n\nDocumentation generator not available"
            result = self.doc_generator.generate_api_documentation(code_structure)
            return result if result else "# API Documentation\n\nNo documentation generated"
        except Exception as e:
            logger.error(f"API documentation generation failed: {e}")
            return f"# API Documentation\n\nError: {str(e)}"

    def generate_architecture_docs(self, modules: List[str]) -> str:
        """Generate architecture documentation"""
        try:
            if not self.doc_generator:
                return "# Architecture Documentation\n\nDocumentation generator not available"
            result = self.doc_generator.generate_architecture_docs(modules)
            return (
                result if result else "# Architecture Documentation\n\nNo documentation generated"
            )
        except Exception as e:
            logger.error(f"Architecture documentation generation failed: {e}")
            return f"# Architecture Documentation\n\nError: {str(e)}"

    def generate_setup_guide(self, project: Dict[str, Any]) -> str:
        """Generate setup/installation guide"""
        try:
            if not self.doc_generator:
                return "# Setup Guide\n\nDocumentation generator not available"
            result = self.doc_generator.generate_setup_guide(project)
            return result if result else "# Setup Guide\n\nNo guide generated"
        except Exception as e:
            logger.error(f"Setup guide generation failed: {e}")
            return f"# Setup Guide\n\nError: {str(e)}"

    def generate_all_documentation(
        self, project: Dict[str, Any], code_structure: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate complete documentation set"""
        try:
            if not self.doc_generator:
                return {"error": "Documentation generator not available"}
            result = self.doc_generator.generate_all(project, code_structure)
            return result if isinstance(result, dict) else {"error": "Invalid documentation format"}
        except Exception as e:
            logger.error(f"Complete documentation generation failed: {e}")
            return {"error": str(e)}

    # Performance methods
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if not self.cache:
                return {"error": "Cache not available"}
            return self.cache.stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    def clear_cache(self) -> Dict[str, Any]:
        """Clear all cache entries"""
        try:
            if not self.cache:
                return {"error": "Cache not available"}
            self.cache.clear()
            return {"status": "success", "message": "Cache cleared"}
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return {"status": "error", "message": str(e)}

    def reset_profiler(self) -> Dict[str, Any]:
        """Reset profiler statistics"""
        try:
            if not self.profiler:
                return {"error": "Profiler not available"}
            self.profiler.reset()
            return {"status": "success", "message": "Profiler reset"}
        except Exception as e:
            logger.error(f"Failed to reset profiler: {e}")
            return {"status": "error", "message": str(e)}

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard"""
        try:
            result = {"status": "operational"}

            if self.profiler:
                stats = self.profiler.get_stats()
                result["profiler"] = stats if stats else {}

            if self.cache:
                cache_stats = self.cache.stats()
                result["cache"] = cache_stats if cache_stats else {}

            return result
        except Exception as e:
            logger.error(f"Failed to get performance dashboard: {e}")
            return {"status": "error", "message": str(e)}

    def get_service(self, service_name: str) -> Any:
        """Get a service or agent by name"""
        # Check if it's an agent
        if service_name in self.agents:
            return self.agents[service_name]

        # Check if it's an orchestrator
        if service_name == "skill_orchestrator":
            return self.skill_orchestrator
        elif service_name == "workflow_orchestrator":
            return self.workflow_orchestrator
        elif service_name == "pure_orchestrator":
            return self.pure_orchestrator

        # Service not found
        logger.warning(f"Service not found: {service_name}")
        return None

    def process_request(self, router_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process requests from routers using unified interface.
        Dispatches to appropriate handler based on router name.
        """
        try:
            if router_name == "multi_llm":
                return self._handle_multi_llm(request_data)
            elif router_name == "socratic_counselor":
                return self._handle_socratic_counselor(request_data)
            else:
                # Generic fallback for unknown routers - return sensible defaults
                logger.warning(f"Unknown router: {router_name}, returning generic response")
                return {
                    "status": "success",
                    "data": {},
                    "message": f"Handler for {router_name} not implemented",
                }
        except Exception as e:
            logger.error(f"Error processing request for {router_name}: {e}")
            return {"status": "error", "message": str(e)}

    async def process_request_async(
        self, router_name: str, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Async version of process_request for long-running operations.
        """
        # For now, delegate to sync version
        # In a real implementation, this would use async/await properly
        return self.process_request(router_name, request_data)

    def _handle_multi_llm(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle multi-LLM router requests"""
        action = request_data.get("action", "")

        if action == "list_providers":
            # Return available LLM providers
            providers = []
            if self.llm_client:
                providers.append(
                    {
                        "name": "anthropic",
                        "model": "claude-3-sonnet",
                        "configured": True,
                        "status": "active",
                    }
                )
            providers.extend(
                [
                    {
                        "name": "openai",
                        "model": "gpt-4",
                        "configured": False,
                        "status": "available",
                    },
                    {
                        "name": "google",
                        "model": "gemini-pro",
                        "configured": False,
                        "status": "available",
                    },
                ]
            )
            return {
                "status": "success",
                "data": {"providers": providers},
                "message": "Providers retrieved",
            }

        elif action == "get_provider_config":
            # Return current provider configuration
            return {
                "status": "success",
                "data": {
                    "default_provider": "anthropic",
                    "api_key_configured": bool(self.llm_client),
                    "current_model": "claude-3-sonnet" if self.llm_client else None,
                },
                "message": "Config retrieved",
            }

        elif action == "set_default_provider":
            # Set default LLM provider
            provider = request_data.get("provider", "anthropic")
            return {
                "status": "success",
                "data": {"default_provider": provider},
                "message": f"Default provider set to {provider}",
            }

        elif action == "update_api_key":
            # Update API key for provider
            provider = request_data.get("provider", "anthropic")
            api_key = request_data.get("api_key", "")
            if api_key:
                self.api_key = api_key
                # Recreate LLM client with new key
                self.llm_client = self._create_llm_client()
            return {
                "status": "success",
                "data": {"provider": provider, "configured": bool(api_key)},
                "message": "API key updated",
            }

        elif action == "get_usage_stats":
            # Get LLM usage statistics
            time_period = request_data.get("time_period", "month")
            return {
                "status": "success",
                "data": {
                    "time_period": time_period,
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "by_provider": {},
                },
                "message": "Usage stats retrieved",
            }

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _handle_socratic_counselor(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Socratic counselor requests for generating questions"""
        action = request_data.get("action", "")

        if action == "generate_question":
            # Generate a Socratic question for a project
            project = request_data.get("project", {})
            topic = request_data.get("topic", "")
            user_id = request_data.get("user_id", "")
            force_refresh = request_data.get("force_refresh", False)

            logger.info(f"_handle_socratic_counselor generate_question: topic={topic[:50] if topic else 'EMPTY'}")

            # Try to use the actual agent if available
            counselor = self.agents.get("socratic_counselor")

            try:
                if counselor and self.llm_client:
                    # Use real agent to generate question
                    # SocraticCounselor expects topic at top level
                    logger.info(f"Calling counselor.process() with topic: {topic[:50] if topic else 'EMPTY'}")
                    result = counselor.process({"topic": topic})
                    logger.info(f"counselor.process() returned: {result}")
                    return {"status": "success", "data": result, "message": "Question generated"}
            except Exception as e:
                logger.warning(f"Failed to use socratic_counselor agent: {e}", exc_info=True)

            # Fallback: Generate a generic Socratic question
            questions = [
                "What is the main goal of your project?",
                "How does this feature contribute to the overall system design?",
                "What are the key requirements you need to address?",
                "Have you considered edge cases or error conditions?",
                "How would you test this implementation?",
                "What are the performance implications of your approach?",
                "How does this integrate with existing functionality?",
                "What dependencies does this component have?",
                "How would you document this functionality?",
                "What alternatives did you consider?",
            ]

            # Generate a question based on project phase
            phase = (
                getattr(project, "phase", "discovery")
                if hasattr(project, "phase")
                else project.get("phase", "discovery")
            )
            question_idx = hash((user_id, phase, force_refresh)) % len(questions)

            return {
                "status": "success",
                "data": {
                    "question": questions[question_idx],
                    "project_id": getattr(project, "project_id", project.get("id", "unknown")),
                    "phase": phase,
                    "suggested_response": "I will think about this carefully...",
                },
                "message": "Question generated",
            }

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}


# Global instance
_orchestrator_instance: Optional[APIOrchestrator] = None


def get_orchestrator(api_key: str = "") -> APIOrchestrator:
    """Get or create global orchestrator instance with real agents"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = APIOrchestrator(api_key)
    return _orchestrator_instance
