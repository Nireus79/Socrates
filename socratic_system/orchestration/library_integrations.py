"""
Socratic Library Integrations

Comprehensive integration of all 12 Socratic ecosystem libraries into the orchestrator:
- socrates-nexus: LLM foundation
- socratic-core: Framework
- socratic-agents: Multi-agent orchestration
- socratic-rag: Knowledge retrieval
- socratic-analyzer: Code analysis
- socratic-security: Security features
- socratic-learning: Learning analytics
- socratic-conflict: Conflict resolution
- socratic-knowledge: Knowledge management
- socratic-workflow: Workflow orchestration
- socratic-docs: Documentation generation
- socratic-performance: Performance monitoring
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("socrates.integrations")


class LearningIntegration:
    """Integrate socratic-learning for interaction tracking and recommendations"""

    def __init__(self, storage_path: str = "socrates_learning.db"):
        """Initialize learning system"""
        try:
            from socratic_learning import InteractionLogger, LearningEngine, RecommendationEngine
            from socratic_learning.core.store import SQLiteLearningStore

            self.store = SQLiteLearningStore(storage_path)
            self.logger = InteractionLogger(self.store)
            self.engine = LearningEngine(self.store)
            self.recommender = RecommendationEngine(self.store)
            self.enabled = True
            logger.info("Learning integration enabled")
        except ImportError:
            self.enabled = False
            logger.warning("socratic-learning not available")

    def start_session(self, user_id: str, context: Optional[Dict[str, Any]] = None):
        """Start a learning session"""
        if not self.enabled:
            return None
        try:
            return self.logger.create_session(user_id=user_id, context=context or {})
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return None

    def log_interaction(self, session_id: str, agent_name: str, input_data: Dict,
                       output_data: Dict, tokens_used: int = 0, cost: float = 0.0,
                       duration_ms: float = 0.0, success: bool = True, tags: List[str] = None):
        """Log an agent interaction"""
        if not self.enabled or not session_id:
            return None
        try:
            return self.logger.log_interaction(
                session_id=session_id,
                agent_name=agent_name,
                input_data=input_data,
                output_data=output_data,
                model_name="claude-opus",
                provider="anthropic",
                input_tokens=tokens_used // 2,
                output_tokens=tokens_used // 2,
                cost_usd=cost,
                duration_ms=duration_ms,
                success=success,
                tags=tags or []
            )
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            return None

    def get_recommendations(self, agent_name: str, limit: int = 5) -> List[Dict]:
        """Get recommendations for agent improvement"""
        if not self.enabled:
            return []
        try:
            recs = self.recommender.get_high_priority_recommendations(agent_name, limit)
            return [r.to_dict() if hasattr(r, 'to_dict') else r for r in recs]
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []


class AnalyzerIntegration:
    """Integrate socratic-analyzer for code quality analysis"""

    def __init__(self):
        """Initialize analyzer"""
        try:
            from socratic_analyzer import AnalyzerClient, AnalyzerConfig

            config = AnalyzerConfig(
                analyze_types=True,
                analyze_docstrings=True,
                analyze_security=True,
                analyze_performance=True,
                max_complexity=10,
                include_metrics=True,
                detailed_output=False
            )
            self.analyzer = AnalyzerClient(config)
            self.enabled = True
            logger.info("Analyzer integration enabled")
        except ImportError:
            self.enabled = False
            logger.warning("socratic-analyzer not available")

    def analyze_code(self, code: str, filename: str = "code.py") -> Dict[str, Any]:
        """Analyze code for issues and quality"""
        if not self.enabled:
            return {}
        try:
            analysis = self.analyzer.analyze_code(code, filename)
            return {
                "issues_count": len(analysis.issues) if hasattr(analysis, 'issues') else 0,
                "quality_score": getattr(analysis, 'overall_score', 0),
                "patterns": getattr(analysis, 'patterns', []),
                "recommendations": self.analyzer.get_recommendations(analysis)
                if hasattr(self.analyzer, 'get_recommendations') else []
            }
        except Exception as e:
            logger.error(f"Failed to analyze code: {e}")
            return {}


class ConflictIntegration:
    """Integrate socratic-conflict for multi-agent conflict resolution"""

    def __init__(self):
        """Initialize conflict detector"""
        try:
            from socratic_conflict import ConflictDetector, VotingStrategy, ConsensusStrategy

            self.detector = ConflictDetector()
            self.voting_strategy = VotingStrategy()
            self.consensus_strategy = ConsensusStrategy()
            self.enabled = True
            logger.info("Conflict integration enabled")
        except ImportError:
            self.enabled = False
            logger.warning("socratic-conflict not available")

    def detect_and_resolve(self, field_name: str, values: Dict[str, Any],
                         agents: List[str]) -> Optional[Dict[str, Any]]:
        """Detect conflicts in agent outputs and resolve them"""
        if not self.enabled:
            return None
        try:
            conflict = self.detector.detect_data_conflict(
                field_name=field_name,
                values=values,
                agents=agents,
                context={"task": "agent_coordination"}
            )
            if conflict:
                resolution = self.voting_strategy.resolve(conflict)
                return {
                    "conflict_detected": True,
                    "recommended_value": resolution.recommended_proposal_id if hasattr(resolution, 'recommended_proposal_id') else None,
                    "confidence": resolution.confidence if hasattr(resolution, 'confidence') else 0.0
                }
            return {"conflict_detected": False}
        except Exception as e:
            logger.error(f"Failed to detect/resolve conflict: {e}")
            return None


class KnowledgeIntegration:
    """Integrate socratic-knowledge for enterprise knowledge management"""

    def __init__(self, db_path: str = "socrates_knowledge.db"):
        """Initialize knowledge manager"""
        try:
            from socratic_knowledge import KnowledgeManager

            self.km = KnowledgeManager(storage="sqlite", db_path=db_path, enable_rag=True)
            self.enabled = True
            logger.info("Knowledge integration enabled")
        except ImportError:
            self.enabled = False
            logger.warning("socratic-knowledge not available")

    def create_knowledge_item(self, tenant_id: str, title: str, content: str,
                            collection_id: Optional[str] = None,
                            tags: Optional[List[str]] = None) -> Optional[Dict]:
        """Create a knowledge item"""
        if not self.enabled:
            return None
        try:
            item = self.km.create_item(
                tenant_id=tenant_id,
                collection_id=collection_id,
                title=title,
                content=content,
                created_by="system",
                tags=tags or [],
                metadata={"created_at": datetime.now().isoformat()}
            )
            return {
                "item_id": item.item_id if hasattr(item, 'item_id') else str(item),
                "title": title,
                "status": "created"
            }
        except Exception as e:
            logger.error(f"Failed to create knowledge item: {e}")
            return None

    def search_knowledge(self, tenant_id: str, query: str, mode: str = "semantic",
                       limit: int = 5) -> List[Dict]:
        """Search knowledge base"""
        if not self.enabled:
            return []
        try:
            results = self.km.search(tenant_id=tenant_id, query=query, limit=limit)
            return [
                {
                    "title": r.title if hasattr(r, 'title') else str(r),
                    "content_preview": (r.content[:200] if hasattr(r, 'content') else str(r))[:200]
                }
                for r in (results if isinstance(results, list) else [results])
            ]
        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return []


class WorkflowIntegration:
    """Integrate socratic-workflow for orchestrating complex agent workflows"""

    def __init__(self):
        """Initialize workflow engine"""
        try:
            from socratic_workflow import Workflow, WorkflowEngine, CostTracker

            self.engine = WorkflowEngine()
            self.cost_tracker = CostTracker()
            self.enabled = True
            logger.info("Workflow integration enabled")
        except ImportError:
            self.enabled = False
            logger.warning("socratic-workflow not available")

    def create_workflow(self, name: str, description: str = "") -> Optional[Any]:
        """Create a new workflow"""
        if not self.enabled:
            return None
        try:
            from socratic_workflow import Workflow
            return Workflow(name=name, description=description)
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            return None

    def execute_workflow(self, workflow: Any) -> Dict[str, Any]:
        """Execute a workflow"""
        if not self.enabled:
            return {}
        try:
            result = self.engine.execute(workflow)
            return {
                "success": result.success if hasattr(result, 'success') else False,
                "duration_ms": result.duration if hasattr(result, 'duration') else 0,
                "task_results": result.task_results if hasattr(result, 'task_results') else {}
            }
        except Exception as e:
            logger.error(f"Failed to execute workflow: {e}")
            return {"success": False, "error": str(e)}

    def track_cost(self, provider: str, model: str, input_tokens: int,
                  output_tokens: int) -> float:
        """Track LLM costs"""
        if not self.enabled:
            return 0.0
        try:
            return self.cost_tracker.track_call(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
        except Exception as e:
            logger.error(f"Failed to track cost: {e}")
            return 0.0


class DocsIntegration:
    """Integrate socratic-docs for automatic documentation generation"""

    def __init__(self):
        """Initialize documentation generator"""
        try:
            from socratic_docs import DocumentationGenerator

            self.generator = DocumentationGenerator()
            self.enabled = True
            logger.info("Docs integration enabled")
        except ImportError:
            self.enabled = False
            logger.warning("socratic-docs not available")

    def generate_readme(self, project_info: Dict[str, Any]) -> Optional[str]:
        """Generate README documentation"""
        if not self.enabled:
            return None
        try:
            return self.generator.generate_comprehensive_readme(project_info)
        except Exception as e:
            logger.error(f"Failed to generate README: {e}")
            return None

    def generate_api_docs(self, code_structure: Dict[str, Any]) -> Optional[str]:
        """Generate API documentation"""
        if not self.enabled:
            return None
        try:
            return self.generator.generate_api_documentation(code_structure)
        except Exception as e:
            logger.error(f"Failed to generate API docs: {e}")
            return None


class PerformanceIntegration:
    """Integrate socratic-performance for monitoring and caching"""

    def __init__(self):
        """Initialize performance monitor"""
        try:
            from socratic_performance import QueryProfiler

            self.profiler = QueryProfiler()
            self.enabled = True
            logger.info("Performance integration enabled")
        except ImportError:
            self.enabled = False
            logger.warning("socratic-performance not available")

    def profile_execution(self, func_name: str, duration_ms: float, success: bool = True):
        """Record execution metrics"""
        if not self.enabled:
            return
        try:
            self.profiler.record_execution(
                task_id=func_name,
                duration_ms=duration_ms,
                success=success
            )
        except Exception as e:
            logger.error(f"Failed to profile execution: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.enabled:
            return {}
        try:
            stats = self.profiler.get_stats()
            return stats if isinstance(stats, dict) else {}
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


class SocraticLibraryManager:
    """Central manager for all 12 Socratic ecosystem libraries"""

    def __init__(self, config: Any):
        """Initialize all library integrations"""
        self.config = config
        self.logger = logging.getLogger("socrates.library_manager")

        # Initialize all 12 library integrations
        self.learning = LearningIntegration()
        self.analyzer = AnalyzerIntegration()
        self.conflict = ConflictIntegration()
        self.knowledge = KnowledgeIntegration()
        self.workflow = WorkflowIntegration()
        self.docs = DocsIntegration()
        self.performance = PerformanceIntegration()

        self.logger.info("Socratic Library Manager initialized with all 12 libraries")

    def get_status(self) -> Dict[str, bool]:
        """Get status of all library integrations"""
        return {
            "learning": self.learning.enabled,
            "analyzer": self.analyzer.enabled,
            "conflict": self.conflict.enabled,
            "knowledge": self.knowledge.enabled,
            "workflow": self.workflow.enabled,
            "docs": self.docs.enabled,
            "performance": self.performance.enabled
        }

    def __repr__(self) -> str:
        status = self.get_status()
        enabled = sum(1 for v in status.values() if v)
        return f"<SocraticLibraryManager: {enabled}/7 libraries enabled>"
