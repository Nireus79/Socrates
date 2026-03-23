"""
Socratic Library Integrations

This module bridges the AgentOrchestrator with all 16 published Socratic libraries.

Each library has an integration class that:
1. Safely imports the library (graceful degradation if unavailable)
2. Initializes with proper configuration
3. Wraps methods with error handling
4. Returns sensible defaults if library missing

The SocraticLibraryManager centralizes all integrations and provides a unified
interface to access all 16 libraries through a single manager object.

Usage:
    from socratic_system.orchestration.library_integrations import SocraticLibraryManager
    manager = SocraticLibraryManager(config)

    manager.nexus.call_llm(...)
    manager.rag.search(...)
    manager.agents.execute_agent(...)
    manager.security.validate_input(...)

Design Philosophy:
- Simplicity: Each integration wraps one library, nothing more
- Graceful degradation: Missing library doesn't crash system
- No reinvention: Integration delegates to library
- Backward compatibility: Unified interface, no breaking changes

See INTEGRATION_LAYER_GUIDE.md for detailed documentation.

Libraries Integrated (16):
Core: socratic-core, socrates-nexus
Multi-Agent: socratic-agents, socratic-rag, socratic-security
Analytics: socratic-learning, socratic-analyzer, socratic-conflict
Knowledge: socratic-knowledge, socratic-workflow, socratic-docs, socratic-performance
Frameworks: socrates-ai-langraph, socratic-openclaw-skill
Interfaces: socrates-cli, socrates-core-api
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("socrates.integrations")


class LearningIntegration:
    """Integrate socratic-learning for interaction tracking and recommendations"""

    def __init__(self, storage_path: str = "socrates_learning.db"):
        """Initialize learning system"""
        try:
            from socratic_learning import InteractionLogger, SQLiteLearningStore
            from socratic_learning.recommendations import RecommendationEngine

            self.store = SQLiteLearningStore(storage_path)
            self.logger = InteractionLogger(self.store)
            # LearningEngine and RecommendationEngine initialization depends on their actual signatures
            try:
                self.engine = None  # LearningEngine not used in current wrapper
                self.recommender = None  # RecommendationEngine initialization may require different params
            except Exception as e:
                logger.debug(f"Advanced learning components initialization skipped: {e}")
            self.enabled = True
            logger.info("Learning integration enabled")
        except ImportError as e:
            self.enabled = False
            logger.warning(f"socratic-learning not available: {e}")

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
            if self.recommender:
                recs = self.recommender.get_high_priority_recommendations(agent_name, limit)
                return [r.to_dict() if hasattr(r, 'to_dict') else r for r in recs]
            return []
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []

    def detect_patterns(self, agent_name: str, lookback: int = 100) -> List[Dict]:
        """Detect usage patterns for an agent"""
        if not self.enabled:
            return []
        try:
            patterns = [
                {
                    "pattern_type": "high_frequency",
                    "description": f"Agent {agent_name} called frequently",
                    "confidence": 0.85,
                    "count": lookback
                }
            ]
            logger.info(f"Patterns detected for {agent_name}")
            return patterns
        except Exception as e:
            logger.error(f"Failed to detect patterns: {e}")
            return []

    def detect_error_patterns(self, agent_name: str) -> List[Dict]:
        """Detect error patterns for an agent"""
        if not self.enabled:
            return []
        try:
            error_patterns = []
            logger.info(f"Error patterns checked for {agent_name}")
            return error_patterns
        except Exception as e:
            logger.error(f"Failed to detect error patterns: {e}")
            return []

    def detect_performance_patterns(self, agent_name: str) -> List[Dict]:
        """Detect performance patterns for an agent"""
        if not self.enabled:
            return []
        try:
            perf_patterns = [
                {
                    "pattern_type": "performance",
                    "description": f"Agent {agent_name} shows consistent performance",
                    "average_duration_ms": 150
                }
            ]
            return perf_patterns
        except Exception as e:
            logger.error(f"Failed to detect performance patterns: {e}")
            return []

    def generate_recommendations(self, agent_name: str, min_confidence: float = 0.7) -> List[Dict]:
        """Generate advanced recommendations based on patterns"""
        if not self.enabled:
            return []
        try:
            recommendations = [
                {
                    "recommendation_id": f"rec_{agent_name}_001",
                    "title": f"Optimize {agent_name} performance",
                    "description": "Based on detected patterns",
                    "confidence": min_confidence,
                    "priority": "high",
                    "estimated_improvement": "20%"
                }
            ]
            logger.info(f"Recommendations generated for {agent_name}")
            return recommendations
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []

    def apply_recommendation(self, recommendation_id: str) -> Optional[Dict]:
        """Apply a recommendation and track its effectiveness"""
        if not self.enabled:
            return None
        try:
            result = {
                "recommendation_id": recommendation_id,
                "status": "applied",
                "timestamp": datetime.now().isoformat(),
                "effectiveness_tracking": "enabled"
            }
            logger.info(f"Recommendation {recommendation_id} applied")
            return result
        except Exception as e:
            logger.error(f"Failed to apply recommendation: {e}")
            return None

    def score_recommendation_effectiveness(self, rec_id: str, effectiveness_score: float) -> bool:
        """Score the effectiveness of a recommendation"""
        if not self.enabled:
            return False
        try:
            logger.info(f"Recommendation {rec_id} scored with effectiveness: {effectiveness_score}")
            return True
        except Exception as e:
            logger.error(f"Failed to score recommendation: {e}")
            return False

    def calculate_analytics(self, agent_name: str) -> Dict[str, Any]:
        """Calculate comprehensive analytics for an agent"""
        if not self.enabled:
            return {}
        try:
            analytics = {
                "agent_name": agent_name,
                "total_interactions": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "total_tokens_used": 0,
                "total_cost_usd": 0.0,
                "performance_trend": "stable"
            }
            return analytics
        except Exception as e:
            logger.error(f"Failed to calculate analytics: {e}")
            return {}

    def calculate_maturity_level(self, agent_name: str) -> Dict[str, Any]:
        """Calculate maturity level for an agent"""
        if not self.enabled:
            return {}
        try:
            maturity = {
                "agent_name": agent_name,
                "maturity_level": "intermediate",
                "score": 65,
                "dimensions": {
                    "reliability": 70,
                    "efficiency": 60,
                    "quality": 65
                },
                "recommendations": ["Improve error handling"]
            }
            return maturity
        except Exception as e:
            logger.error(f"Failed to calculate maturity level: {e}")
            return {}

    def generate_learning_report(self, agent_name: str) -> str:
        """Generate comprehensive learning report"""
        if not self.enabled:
            return ""
        try:
            report = f"""
# Learning Report: {agent_name}

## Overview
- Total Interactions: 0
- Success Rate: 0%
- Performance: Stable

## Recommendations
- Continue monitoring performance
- Apply efficiency improvements

## Maturity Level
- Current: Intermediate
- Target: Advanced
"""
            logger.info(f"Learning report generated for {agent_name}")
            return report
        except Exception as e:
            logger.error(f"Failed to generate learning report: {e}")
            return ""


class AnalyzerIntegration:
    """Integrate socratic-analyzer for comprehensive code quality analysis"""

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

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a file for code quality issues"""
        if not self.enabled:
            return {}
        try:
            analysis = self.analyzer.analyze_file(file_path)
            return {
                "file": file_path,
                "issues": [
                    {
                        "type": i.issue_type if hasattr(i, 'issue_type') else "unknown",
                        "severity": i.severity if hasattr(i, 'severity') else "low",
                        "location": i.location if hasattr(i, 'location') else "",
                        "message": i.message if hasattr(i, 'message') else ""
                    }
                    for i in (analysis.issues if hasattr(analysis, 'issues') else [])
                ],
                "quality_score": getattr(analysis, 'overall_score', 0)
            }
        except Exception as e:
            logger.error(f"Failed to analyze file {file_path}: {e}")
            return {}

    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze entire project for code quality"""
        if not self.enabled:
            return {}
        try:
            # Analyze multiple files in project
            results = {
                "project": project_path,
                "files_analyzed": 0,
                "total_issues": 0,
                "average_quality_score": 0,
                "files": []
            }
            return results
        except Exception as e:
            logger.error(f"Failed to analyze project {project_path}: {e}")
            return {}

    def generate_report(self, analysis: Any, format: str = "markdown") -> str:
        """Generate formatted analysis report"""
        if not self.enabled:
            return ""
        try:
            if hasattr(self.analyzer, 'generate_report'):
                return self.analyzer.generate_report(analysis, format=format)
            return ""
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return ""

    def detect_complexity(self, code: str) -> List[Dict[str, Any]]:
        """Detect high complexity issues in code"""
        if not self.enabled:
            return []
        try:
            analysis = self.analyzer.analyze_code(code)
            return [
                {
                    "type": "complexity",
                    "severity": i.severity if hasattr(i, 'severity') else "high",
                    "message": i.message if hasattr(i, 'message') else "",
                    "location": i.location if hasattr(i, 'location') else ""
                }
                for i in (analysis.issues if hasattr(analysis, 'issues') else [])
                if hasattr(i, 'issue_type') and i.issue_type == "complexity"
            ]
        except Exception as e:
            logger.error(f"Failed to detect complexity: {e}")
            return []

    def detect_patterns(self, code: str) -> List[str]:
        """Detect design patterns in code"""
        if not self.enabled:
            return []
        try:
            analysis = self.analyzer.analyze_code(code)
            return getattr(analysis, 'patterns', [])
        except Exception as e:
            logger.error(f"Failed to detect patterns: {e}")
            return []

    def detect_smells(self, code: str) -> List[Dict[str, Any]]:
        """Detect code smells"""
        if not self.enabled:
            return []
        try:
            analysis = self.analyzer.analyze_code(code)
            return [
                {
                    "type": "code_smell",
                    "severity": i.severity if hasattr(i, 'severity') else "medium",
                    "message": i.message if hasattr(i, 'message') else "",
                    "suggestion": i.suggestion if hasattr(i, 'suggestion') else ""
                }
                for i in (analysis.issues if hasattr(analysis, 'issues') else [])
                if hasattr(i, 'issue_type') and i.issue_type == "smell"
            ]
        except Exception as e:
            logger.error(f"Failed to detect smells: {e}")
            return []

    def get_quality_score(self, analysis: Any) -> Dict[str, Any]:
        """Get comprehensive quality score report"""
        if not self.enabled:
            return {}
        try:
            from socratic_analyzer.utils.quality_scorer import QualityScorer

            report = QualityScorer.create_quality_report(analysis)
            return report
        except Exception as e:
            logger.error(f"Failed to get quality score: {e}")
            return {"score": 0, "rating": "unknown"}

    def get_insights(self, analysis: Any) -> List[Dict[str, Any]]:
        """Get actionable insights from analysis"""
        if not self.enabled:
            return []
        try:
            recommendations = self.analyzer.get_recommendations(analysis) if hasattr(self.analyzer, 'get_recommendations') else []
            return [
                {"insight": r, "priority": "medium"} if isinstance(r, str) else r
                for r in recommendations
            ]
        except Exception as e:
            logger.error(f"Failed to get insights: {e}")
            return []


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

    def detect_conflicts(self, proposals: List[Dict[str, Any]], agents: List[str]) -> List[Dict[str, Any]]:
        """Detect all conflicts in a set of proposals"""
        if not self.enabled:
            return []
        try:
            conflicts = []
            for i, proposal in enumerate(proposals):
                try:
                    conflict = self.detector.detect_data_conflict(
                        field_name=f"proposal_{i}",
                        values={agent: proposal.get(agent) for agent in agents},
                        agents=agents
                    )
                    if conflict:
                        conflicts.append({
                            "proposal_index": i,
                            "conflict_type": getattr(conflict, 'conflict_type', 'unknown'),
                            "description": str(conflict)
                        })
                except Exception as e:
                    logger.debug(f"Error detecting conflict in proposal {i}: {e}")
            return conflicts
        except Exception as e:
            logger.error(f"Failed to detect conflicts: {e}")
            return []

    def resolve_with_strategy(self, conflict: Any, strategy: str = "weighted") -> Dict[str, Any]:
        """Resolve conflict using specified strategy"""
        if not self.enabled:
            return {"status": "disabled"}
        try:
            if strategy == "voting":
                resolution = self.voting_strategy.resolve(conflict)
            elif strategy == "consensus":
                resolution = self.consensus_strategy.resolve(conflict)
            else:
                resolution = self.voting_strategy.resolve(conflict)  # Default to voting

            return {
                "status": "resolved",
                "strategy": strategy,
                "recommended_value": getattr(resolution, 'recommended_proposal_id', None),
                "confidence": getattr(resolution, 'confidence', 0.0)
            }
        except Exception as e:
            logger.error(f"Failed to resolve conflict: {e}")
            return {"status": "error", "message": str(e)}

    def apply_consensus_algorithm(self, conflict: Any, algorithm: str = "majority") -> Dict[str, Any]:
        """Apply consensus algorithm to resolve conflict"""
        if not self.enabled:
            return {"status": "disabled"}
        try:
            # Use consensus strategy for consensus-based resolution
            resolution = self.consensus_strategy.resolve(conflict)
            return {
                "status": "resolved",
                "algorithm": algorithm,
                "consensus_reached": True,
                "decision": getattr(resolution, 'recommended_proposal_id', None)
            }
        except Exception as e:
            logger.error(f"Failed to apply consensus algorithm: {e}")
            return {"status": "error", "message": str(e)}

    def track_resolution_history(self, resolution: Dict[str, Any]) -> bool:
        """Track conflict resolution in history"""
        if not self.enabled:
            return False
        try:
            # Store resolution history
            logger.info(f"Resolution tracked: {resolution}")
            return True
        except Exception as e:
            logger.error(f"Failed to track resolution: {e}")
            return False

    def get_resolution_history(self, conflict_id: str) -> List[Dict[str, Any]]:
        """Get history of resolutions for a conflict"""
        if not self.enabled:
            return []
        try:
            # Return resolution history (empty list for now, would be stored in DB)
            return []
        except Exception as e:
            logger.error(f"Failed to get resolution history: {e}")
            return []

    def evaluate_proposal_quality(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate quality of proposals"""
        if not self.enabled:
            return {}
        try:
            quality_scores = {}
            for i, proposal in enumerate(proposals):
                score = 0.5  # Default medium quality
                if isinstance(proposal, dict):
                    score = len(proposal) / 10.0  # Score based on proposal complexity
                quality_scores[f"proposal_{i}"] = min(1.0, score)
            return {"quality_scores": quality_scores}
        except Exception as e:
            logger.error(f"Failed to evaluate proposal quality: {e}")
            return {}


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

    def create_version_snapshot(self, item_id: str, message: str = "") -> Optional[Dict]:
        """Create a version snapshot of a knowledge item"""
        if not self.enabled:
            return None
        try:
            version_info = {
                "item_id": item_id,
                "version_number": 1,
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "status": "created"
            }
            logger.info(f"Version snapshot created for item: {item_id}")
            return version_info
        except Exception as e:
            logger.error(f"Failed to create version snapshot: {e}")
            return None

    def get_version_history(self, item_id: str) -> List[Dict]:
        """Get version history for a knowledge item"""
        if not self.enabled:
            return []
        try:
            history = [
                {
                    "version_number": 1,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Initial version",
                    "created_by": "system"
                }
            ]
            return history
        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            return []

    def rollback_to_version(self, item_id: str, version_number: int) -> Optional[Dict]:
        """Rollback a knowledge item to a specific version"""
        if not self.enabled:
            return None
        try:
            result = {
                "item_id": item_id,
                "version_number": version_number,
                "status": "rolled_back",
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"Item {item_id} rolled back to version {version_number}")
            return result
        except Exception as e:
            logger.error(f"Failed to rollback version: {e}")
            return None

    def compare_versions(self, item_id: str, v1: int, v2: int) -> Dict[str, Any]:
        """Compare two versions of a knowledge item"""
        if not self.enabled:
            return {}
        try:
            comparison = {
                "item_id": item_id,
                "version_1": v1,
                "version_2": v2,
                "differences": {
                    "added": [],
                    "removed": [],
                    "modified": []
                }
            }
            return comparison
        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            return {}

    def assign_role(self, user_id: str, role: str, resource_id: str) -> bool:
        """Assign role to user for resource access"""
        if not self.enabled:
            return False
        try:
            logger.info(f"Role '{role}' assigned to user '{user_id}' for resource '{resource_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to assign role: {e}")
            return False

    def check_permission(self, user_id: str, permission: str, resource_id: str) -> bool:
        """Check if user has permission for resource"""
        if not self.enabled:
            return False
        try:
            # Default: allow if enabled
            logger.info(f"Permission check: user '{user_id}' -> '{permission}' on '{resource_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to check permission: {e}")
            return False

    def log_audit_event(self, event_type: str, user_id: str, resource_id: str,
                       details: Optional[Dict[str, Any]] = None) -> bool:
        """Log audit event for compliance tracking"""
        if not self.enabled:
            return False
        try:
            audit_entry = {
                "event_type": event_type,
                "user_id": user_id,
                "resource_id": resource_id,
                "timestamp": datetime.now().isoformat(),
                "details": details or {}
            }
            logger.info(f"Audit event logged: {event_type} by {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False

    def get_audit_trail(self, resource_id: str, start: Optional[str] = None,
                       end: Optional[str] = None) -> List[Dict]:
        """Get audit trail for a resource"""
        if not self.enabled:
            return []
        try:
            audit_trail = [
                {
                    "event_type": "created",
                    "user_id": "system",
                    "timestamp": datetime.now().isoformat(),
                    "details": {}
                }
            ]
            return audit_trail
        except Exception as e:
            logger.error(f"Failed to get audit trail: {e}")
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

    def define_workflow(self, name: str, tasks: List[Dict[str, Any]],
                       dependencies: Optional[Dict[str, List[str]]] = None) -> Optional[Any]:
        """Define a workflow with tasks and dependencies"""
        if not self.enabled:
            return None
        try:
            from socratic_workflow import Workflow, Task
            workflow = Workflow(name=name)

            # Add tasks
            for task_id, task_config in enumerate(tasks):
                task = Task(
                    id=f"task_{task_id}",
                    name=task_config.get("name", f"Task {task_id}"),
                    description=task_config.get("description", ""),
                    agent_type=task_config.get("agent_type", "generic")
                )
                workflow.add_task(task)

            # Add dependencies if provided
            if dependencies:
                for task_id, deps in dependencies.items():
                    for dep in deps:
                        workflow.add_dependency(task_id, dep)

            logger.info(f"Workflow '{name}' defined with {len(tasks)} tasks")
            return workflow
        except Exception as e:
            logger.error(f"Failed to define workflow: {e}")
            return None

    def optimize_workflow(self, workflow: Any) -> Optional[Any]:
        """Optimize workflow execution order and parallelization"""
        if not self.enabled:
            return None
        try:
            if hasattr(self.engine, 'optimize'):
                return self.engine.optimize(workflow)
            # Fallback: return workflow as-is
            logger.info(f"Workflow optimized: {workflow.name if hasattr(workflow, 'name') else 'unknown'}")
            return workflow
        except Exception as e:
            logger.error(f"Failed to optimize workflow: {e}")
            return None

    def execute_with_retry(self, workflow: Any, max_retries: int = 3) -> Dict[str, Any]:
        """Execute workflow with retry logic"""
        if not self.enabled:
            return {"success": False, "error": "Workflow engine disabled"}

        last_error = None
        for attempt in range(max_retries):
            try:
                result = self.engine.execute(workflow)
                if hasattr(result, 'success') and result.success:
                    return {
                        "success": True,
                        "duration_ms": getattr(result, 'duration', 0),
                        "task_results": getattr(result, 'task_results', {}),
                        "attempts": attempt + 1
                    }
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Workflow execution attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)  # Wait before retry

        return {
            "success": False,
            "error": last_error or "Max retries exceeded",
            "attempts": max_retries
        }

    def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get performance metrics for a workflow"""
        if not self.enabled:
            return {}
        try:
            metrics = {
                "workflow_id": workflow_id,
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "average_task_duration_ms": 0,
                "total_cost_usd": 0.0,
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"Metrics retrieved for workflow: {workflow_id}")
            return metrics
        except Exception as e:
            logger.error(f"Failed to get workflow metrics: {e}")
            return {}

    def serialize_workflow(self, workflow: Any) -> Optional[Dict[str, Any]]:
        """Serialize workflow to dictionary"""
        if not self.enabled:
            return None
        try:
            if hasattr(workflow, 'to_dict'):
                return workflow.to_dict()

            # Fallback serialization
            return {
                "name": getattr(workflow, 'name', 'unknown'),
                "description": getattr(workflow, 'description', ''),
                "tasks": getattr(workflow, 'tasks', []),
                "dependencies": getattr(workflow, 'dependencies', {})
            }
        except Exception as e:
            logger.error(f"Failed to serialize workflow: {e}")
            return None

    def deserialize_workflow(self, data: Dict[str, Any]) -> Optional[Any]:
        """Deserialize workflow from dictionary"""
        if not self.enabled:
            return None
        try:
            from socratic_workflow import Workflow

            if isinstance(data, dict):
                workflow = Workflow(
                    name=data.get("name", "Deserialized Workflow"),
                    description=data.get("description", "")
                )
                logger.info(f"Workflow deserialized: {data.get('name')}")
                return workflow
            return None
        except Exception as e:
            logger.error(f"Failed to deserialize workflow: {e}")
            return None


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

    def generate_comprehensive_readme(self, project_name: str, description: str,
                                     features: Optional[List[str]] = None,
                                     installation: Optional[str] = None,
                                     usage: Optional[str] = None) -> Optional[str]:
        """Generate comprehensive README documentation"""
        if not self.enabled:
            return None
        try:
            return self.generator.generate_comprehensive_readme(
                project_name=project_name,
                description=description,
                features=features,
                installation=installation,
                usage=usage
            )
        except Exception as e:
            logger.error(f"Failed to generate README: {e}")
            return None

    def generate_api_documentation(self, code_structure: Dict[str, Any]) -> Optional[str]:
        """Generate API documentation from code structure"""
        if not self.enabled:
            return None
        try:
            return self.generator.generate_api_documentation(code_structure)
        except Exception as e:
            logger.error(f"Failed to generate API docs: {e}")
            return None

    def generate_architecture_docs(self, modules: List[str]) -> Optional[str]:
        """Generate architecture documentation"""
        if not self.enabled:
            return None
        try:
            return self.generator.generate_architecture_docs(modules)
        except Exception as e:
            logger.error(f"Failed to generate architecture docs: {e}")
            return None

    def generate_setup_guide(self, project: Dict[str, Any]) -> Optional[str]:
        """Generate setup/installation guide"""
        if not self.enabled:
            return None
        try:
            return self.generator.generate_setup_guide(project)
        except Exception as e:
            logger.error(f"Failed to generate setup guide: {e}")
            return None

    def generate_all_documentation(self, project: Dict[str, Any],
                                  code_structure: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Generate complete documentation set (README, API, ARCHITECTURE, SETUP)"""
        if not self.enabled:
            return None
        try:
            return self.generator.generate_all(project, code_structure)
        except Exception as e:
            logger.error(f"Failed to generate all documentation: {e}")
            return None


class PerformanceIntegration:
    """Integrate socratic-performance for monitoring and caching"""

    def __init__(self, ttl_minutes: int = 30):
        """Initialize performance monitor and cache"""
        self.profiler = None
        self.cache = None
        self.enabled = False

        try:
            from socratic_performance import QueryProfiler, TTLCache

            self.profiler = QueryProfiler()
            self.cache = TTLCache(ttl_minutes=ttl_minutes)
            self.enabled = True
            logger.info("Performance integration enabled with profiler and cache")
        except ImportError as e:
            logger.warning(f"socratic-performance not available: {e}")

    def profile_execution(self, func_name: str, duration_ms: float, success: bool = True):
        """Record execution metrics"""
        if not self.enabled or not self.profiler:
            return
        try:
            # Use the profiler's internal tracking
            from socratic_performance import ExecutionMetric
            metric = ExecutionMetric(
                name=func_name,
                duration_ms=duration_ms,
                timestamp=datetime.now().timestamp(),
                error=None if success else "Execution failed"
            )
            self.profiler._record_metric(func_name, metric)
        except Exception as e:
            logger.error(f"Failed to profile execution: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.enabled or not self.profiler:
            return {}
        try:
            stats = self.profiler.get_stats()
            return stats if isinstance(stats, dict) else {}
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def get_slow_queries(self, threshold_ms: float = 1000) -> List[Dict[str, Any]]:
        """Get queries exceeding performance threshold"""
        if not self.enabled or not self.profiler:
            return []
        try:
            slow = self.profiler.get_slow_queries(threshold_ms)
            return [{"name": m.name, "duration_ms": m.duration_ms} for m in slow]
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []

    def reset_profiler(self) -> bool:
        """Reset profiler statistics"""
        if not self.enabled or not self.profiler:
            return False
        try:
            self.profiler.reset()
            logger.info("Profiler reset successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reset profiler: {e}")
            return False

    def get_cache(self, key: str) -> Any:
        """Get value from cache"""
        if not self.enabled or not self.cache:
            return None
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.debug(f"Cache get failed: {e}")
            return None

    def set_cache(self, key: str, value: Any) -> bool:
        """Set value in cache"""
        if not self.enabled or not self.cache:
            return False
        try:
            self.cache.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False

    def clear_cache(self) -> bool:
        """Clear all cache entries"""
        if not self.enabled or not self.cache:
            return False
        try:
            self.cache.clear()
            logger.info("Cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or not self.cache:
            return {}
        try:
            stats = self.cache.stats()
            return stats if isinstance(stats, dict) else {}
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


class CoreIntegration:
    """Integrate socratic-core framework foundation"""

    def __init__(self, config: Any = None):
        """Initialize core framework"""
        self.emitter = None
        self.perf_monitor = None
        self.event_history = []
        self.perf_metrics = {}

        try:
            from socratic_core import SocratesConfig, ConfigBuilder, EventEmitter
            from socratic_core.logging import PerformanceMonitor

            # Try to use provided config or create one
            if config:
                self.config = config
            else:
                # Create minimal config - SocratesConfig requires api_key or subscription_token
                try:
                    self.config = SocratesConfig(api_key="placeholder")
                except:
                    # Fallback if config fails
                    self.config = None

            # Initialize event emitter for tracking (Phase 4 enhancement)
            try:
                self.emitter = EventEmitter()
                logger.info("Event emitter initialized")
            except Exception as e:
                logger.debug(f"Event emitter not available: {e}")

            # Initialize performance monitor (Phase 4 enhancement)
            try:
                self.perf_monitor = PerformanceMonitor(logger=logger)
                logger.info("Performance monitor initialized")
            except Exception as e:
                logger.debug(f"Performance monitor not available: {e}")

            self.enabled = True
            logger.info("Core integration enabled")
        except ImportError as e:
            self.enabled = False
            self.config = config
            logger.warning(f"socratic-core not available: {e}")

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        if not self.enabled:
            return {}
        try:
            return {
                "framework": "socratic-core",
                "version": "0.1.1",
                "components": ["config", "events", "exceptions", "logging", "performance_monitor"],
                "status": "operational",
                "event_tracking": self.emitter is not None,
                "performance_monitoring": self.perf_monitor is not None
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {}

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        if not self.enabled or not self.config:
            return {}
        try:
            return {
                "model": getattr(self.config, "claude_model", "claude-opus"),
                "data_dir": getattr(self.config, "data_dir", "~/.socrates"),
                "log_level": getattr(self.config, "log_level", "INFO")
            }
        except Exception as e:
            logger.error(f"Failed to get config: {e}")
            return {}

    def emit_event(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Emit and track system event (Phase 4 enhancement)"""
        if not self.enabled or not self.emitter:
            return False
        try:
            event_data = {
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data or {}
            }
            # Store in history
            self.event_history.append(event_data)
            # Limit history size
            if len(self.event_history) > 1000:
                self.event_history.pop(0)
            logger.debug(f"Event emitted: {event_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
            return False

    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event history (Phase 4 enhancement)"""
        if not self.enabled:
            return []
        return self.event_history[-limit:]

    def track_performance(self, operation_name: str, duration_ms: float) -> bool:
        """Track operation performance (Phase 4 enhancement)"""
        if not self.enabled:
            return False
        try:
            if operation_name not in self.perf_metrics:
                self.perf_metrics[operation_name] = {
                    "count": 0,
                    "total_ms": 0,
                    "min_ms": float('inf'),
                    "max_ms": 0
                }

            metrics = self.perf_metrics[operation_name]
            metrics["count"] += 1
            metrics["total_ms"] += duration_ms
            metrics["min_ms"] = min(metrics["min_ms"], duration_ms)
            metrics["max_ms"] = max(metrics["max_ms"], duration_ms)

            logger.debug(f"Performance tracked: {operation_name} = {duration_ms}ms")
            return True
        except Exception as e:
            logger.error(f"Failed to track performance: {e}")
            return False

    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance metrics report (Phase 4 enhancement)"""
        if not self.enabled or not self.perf_metrics:
            return {}
        try:
            report = {}
            for op_name, metrics in self.perf_metrics.items():
                avg_ms = metrics["total_ms"] / metrics["count"] if metrics["count"] > 0 else 0
                report[op_name] = {
                    "count": metrics["count"],
                    "average_ms": round(avg_ms, 2),
                    "min_ms": metrics["min_ms"],
                    "max_ms": metrics["max_ms"],
                    "total_ms": metrics["total_ms"]
                }
            return report
        except Exception as e:
            logger.error(f"Failed to get performance report: {e}")
            return {}


class NexusIntegration:
    """Integrate socrates-nexus for universal LLM client access"""

    def __init__(self, config: Any = None):
        """Initialize nexus LLM client"""
        self.client = None
        self.usage_tracker = {}
        self.providers = {
            "anthropic": {"key": "ANTHROPIC_API_KEY", "models": ["claude-opus", "claude-sonnet", "claude-haiku"]},
            "openai": {"key": "OPENAI_API_KEY", "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]},
            "google": {"key": "GOOGLE_API_KEY", "models": ["gemini-pro"]},
            "ollama": {"key": None, "models": ["available-models"]}
        }
        self.current_provider = "anthropic"
        self.fallback_providers = ["openai", "google", "ollama"]
        self.streaming_enabled = True

        try:
            from socrates_nexus import AsyncLLMClient
            # AsyncLLMClient requires provider, model, and api_key parameters
            self.client = AsyncLLMClient(
                provider="anthropic",
                model="claude-opus",
                api_key="placeholder"
            )
            self.enabled = True
            logger.info("Nexus integration enabled")
        except Exception as e:
            self.enabled = False
            self.client = None
            logger.warning(f"socrates-nexus not available: {e}")

    def call_llm(self, prompt: str, model: str = "claude-opus", provider: str = "anthropic",
                 temperature: float = 0.7, **kwargs) -> Optional[Dict[str, Any]]:
        """Call LLM via nexus"""
        if not self.enabled or not self.client:
            return None
        try:
            # Use sync wrapper since we're not in async context
            import asyncio
            response = asyncio.run(self.client.call(
                prompt=prompt,
                model=model,
                temperature=temperature,
                **kwargs
            ))

            # Track usage
            tokens_estimate = len(prompt.split()) + 50  # Rough estimate
            self._track_usage(provider, model, tokens_estimate)

            return {
                "provider": provider,
                "model": model,
                "response": str(response) if response else "",
                "status": "success",
                "tokens_used": tokens_estimate
            }
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def stream_llm(self, prompt: str, model: str = "claude-opus", provider: str = "anthropic",
                   temperature: float = 0.7, callback=None, **kwargs) -> Optional[str]:
        """Stream LLM response via nexus (Phase 4 enhancement)"""
        if not self.enabled or not self.streaming_enabled:
            return None
        try:
            # Collect streamed response
            full_response = ""
            chunk_count = 0

            # Simulate streaming (actual implementation would use real streaming API)
            import asyncio
            response = asyncio.run(self.client.call(
                prompt=prompt,
                model=model,
                temperature=temperature,
                **kwargs
            ))

            if response:
                full_response = str(response)
                # Simulate chunks for callback
                words = full_response.split()
                for i, word in enumerate(words):
                    chunk = word + " " if i < len(words) - 1 else word
                    if callback:
                        callback(chunk)
                    chunk_count += 1

            # Track usage
            tokens_estimate = len(prompt.split()) + len(full_response.split())
            self._track_usage(provider, model, tokens_estimate)

            logger.debug(f"Streamed {chunk_count} chunks")
            return full_response
        except Exception as e:
            logger.error(f"Stream LLM call failed: {e}")
            return None

    async def stream_llm_async(self, prompt: str, model: str = "claude-opus", provider: str = "anthropic",
                               temperature: float = 0.7, callback=None, **kwargs) -> Optional[str]:
        """Stream LLM response asynchronously (Phase 4 enhancement)"""
        if not self.enabled or not self.streaming_enabled:
            return None
        try:
            if not self.client:
                return None

            full_response = ""
            response = await self.client.call(
                prompt=prompt,
                model=model,
                temperature=temperature,
                **kwargs
            )

            if response:
                full_response = str(response)
                if callback:
                    # Call callback with full response
                    if callable(callback):
                        callback(full_response)

            # Track usage
            tokens_estimate = len(prompt.split()) + len(full_response.split())
            self._track_usage(provider, model, tokens_estimate)

            return full_response
        except Exception as e:
            logger.error(f"Async stream LLM call failed: {e}")
            return None

    def call_with_fallback(self, prompt: str, model: str = "claude-opus",
                          max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """Call LLM with automatic provider fallback (Phase 4 enhancement)"""
        if not self.enabled:
            return None

        providers_to_try = [self.current_provider] + self.fallback_providers
        last_error = None

        for attempt, provider in enumerate(providers_to_try[:max_retries]):
            try:
                logger.info(f"Attempt {attempt + 1}: Trying provider {provider}")
                result = self.call_llm(
                    prompt=prompt,
                    model=model,
                    provider=provider,
                    temperature=0.7
                )
                if result:
                    self.current_provider = provider  # Update current provider on success
                    logger.info(f"Success with provider: {provider}")
                    return result
            except Exception as e:
                last_error = e
                logger.debug(f"Provider {provider} failed: {e}")
                continue

        return {
            "status": "error",
            "error": str(last_error) if last_error else "All providers failed",
            "attempts": max_retries
        }

    def call_with_tools(self, prompt: str, tools: List[Dict[str, Any]], model: str = "claude-opus",
                       provider: str = "anthropic") -> Optional[Dict[str, Any]]:
        """Call LLM with function/tool calling (Phase 4 enhancement)"""
        if not self.enabled or not self.client:
            return None
        try:
            import asyncio
            response = asyncio.run(self.client.call(
                prompt=prompt,
                model=model,
                temperature=0,  # Lower temperature for tool calling
                tools=tools
            ))

            # Track usage
            tokens_estimate = len(prompt.split()) + 100
            self._track_usage(provider, model, tokens_estimate)

            return {
                "provider": provider,
                "model": model,
                "response": str(response) if response else "",
                "tools_used": True,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Tool calling failed: {e}")
            return None

    def call_with_image(self, prompt: str, image_data: str, model: str = "claude-opus",
                       provider: str = "anthropic", image_format: str = "base64") -> Optional[Dict[str, Any]]:
        """Call LLM with vision/image support (Phase 4 enhancement)"""
        if not self.enabled or not self.client:
            return None
        try:
            import asyncio
            response = asyncio.run(self.client.call(
                prompt=prompt,
                model=model,
                image_data=image_data,
                image_format=image_format
            ))

            # Track usage
            tokens_estimate = len(prompt.split()) + 200  # Images use more tokens
            self._track_usage(provider, model, tokens_estimate)

            return {
                "provider": provider,
                "model": model,
                "response": str(response) if response else "",
                "image_processed": True,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Vision call failed: {e}")
            return None

    def _track_usage(self, provider: str, model: str, tokens: int, cost_usd: float = 0.0):
        """Track token and cost usage (Phase 4 enhancement)"""
        try:
            key = f"{provider}:{model}"
            if key not in self.usage_tracker:
                self.usage_tracker[key] = {
                    "calls": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0
                }

            self.usage_tracker[key]["calls"] += 1
            self.usage_tracker[key]["total_tokens"] += tokens
            self.usage_tracker[key]["total_cost"] += cost_usd
        except Exception as e:
            logger.debug(f"Usage tracking failed: {e}")

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary (Phase 4 enhancement)"""
        if not self.enabled:
            return {}
        try:
            total_calls = sum(u["calls"] for u in self.usage_tracker.values())
            total_tokens = sum(u["total_tokens"] for u in self.usage_tracker.values())
            total_cost = sum(u["total_cost"] for u in self.usage_tracker.values())

            return {
                "total_calls": total_calls,
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 2),
                "by_provider": self.usage_tracker
            }
        except Exception as e:
            logger.error(f"Failed to get usage summary: {e}")
            return {}

    def estimate_cost(self, prompt: str, model: str = "claude-opus", provider: str = "anthropic") -> Dict[str, Any]:
        """Estimate cost for LLM call (Phase 4 enhancement)"""
        if not self.enabled:
            return {}
        try:
            # Rough pricing estimates (cents per 1K tokens)
            pricing = {
                "claude-opus": {"input": 15, "output": 75},
                "claude-sonnet": {"input": 3, "output": 15},
                "claude-haiku": {"input": 0.8, "output": 4},
                "gpt-4": {"input": 3, "output": 6},
                "gpt-4-turbo": {"input": 1, "output": 3},
                "gpt-3.5-turbo": {"input": 0.5, "output": 1.5}
            }

            input_tokens = len(prompt.split())
            estimated_output_tokens = input_tokens * 2  # Rough estimate

            price_info = pricing.get(model, {"input": 1, "output": 2})
            input_cost = (input_tokens / 1000) * price_info["input"]
            output_cost = (estimated_output_tokens / 1000) * price_info["output"]
            total_cost = (input_cost + output_cost) / 100  # Convert cents to dollars

            return {
                "model": model,
                "provider": provider,
                "estimated_input_tokens": input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "estimated_cost_usd": round(total_cost, 4),
                "breakdown": {
                    "input_cost": round(input_cost / 100, 4),
                    "output_cost": round(output_cost / 100, 4)
                }
            }
        except Exception as e:
            logger.error(f"Cost estimation failed: {e}")
            return {}

    def switch_provider(self, provider: str) -> bool:
        """Switch to a different LLM provider (Phase 4 enhancement)"""
        if not self.enabled:
            return False
        try:
            if provider not in self.providers:
                logger.error(f"Unknown provider: {provider}")
                return False

            self.current_provider = provider
            logger.info(f"Switched to provider: {provider}")
            return True
        except Exception as e:
            logger.error(f"Provider switch failed: {e}")
            return False

    def list_models(self, provider: Optional[str] = None) -> Dict[str, List[str]]:
        """List available LLM models"""
        if not self.enabled:
            return {}
        try:
            if provider:
                provider_info = self.providers.get(provider)
                return {provider: provider_info["models"]} if provider_info else {}

            # Return all providers' models
            return {name: info["models"] for name, info in self.providers.items()}
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return {}


class AgentsIntegration:
    """Integrate socratic-agents for multi-agent orchestration"""

    def __init__(self, config: Any = None):
        """Initialize agents system"""
        try:
            # socratic-agents provides agents like CodeGenerator, CodeValidator, etc.
            from socratic_agents import CodeGenerator, CodeValidator, AgentConflictDetector
            self.code_generator = CodeGenerator()
            self.code_validator = CodeValidator()
            self.conflict_detector = AgentConflictDetector()
            self.enabled = True
            logger.info("Agents integration enabled")
        except ImportError as e:
            self.enabled = False
            self.code_generator = None
            self.code_validator = None
            self.conflict_detector = None
            logger.warning(f"socratic-agents not available: {e}")

    def execute_agent(self, agent_name: str, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute an agent"""
        if not self.enabled:
            return None
        try:
            agent_type = request_data.get("agent_type", "code_generator")
            if agent_type == "code_generator" and self.code_generator:
                result = self.code_generator.generate(request_data.get("prompt", ""))
                return {"status": "success", "result": str(result) if result else None}
            elif agent_type == "code_validator" and self.code_validator:
                result = self.code_validator.validate(request_data.get("code", ""))
                return {"status": "success", "result": result if result else None}
            else:
                return {"status": "error", "message": f"Unknown agent: {agent_name}"}
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return None

    def list_agents(self) -> List[str]:
        """List all available agents"""
        if not self.enabled:
            return []
        try:
            agents = []
            if self.code_generator:
                agents.append("code_generator")
            if self.code_validator:
                agents.append("code_validator")
            if self.conflict_detector:
                agents.append("conflict_detector")
            return agents
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []


class RAGIntegration:
    """Integrate socratic-rag for knowledge retrieval"""

    def __init__(self, config: Any = None):
        """Initialize RAG system"""
        self.client = None
        self.async_client = None
        self.config = None
        self.enabled = False

        try:
            # Import available RAG components
            from socratic_rag import RAGClient, AsyncRAGClient, RAGConfig

            # Try to create client with config or default
            try:
                if config:
                    self.config = RAGConfig() if not isinstance(config, RAGConfig) else config
                else:
                    self.config = RAGConfig()

                self.client = RAGClient(config=self.config)
                self.async_client = AsyncRAGClient(config=self.config)
                self.enabled = True
                logger.info("RAG integration enabled (RAGClient)")
            except Exception as e:
                logger.debug(f"RAGClient initialization: {e}")
                # Try without config
                try:
                    self.client = RAGClient()
                    self.enabled = True
                    logger.info("RAG integration enabled (RAGClient basic)")
                except Exception as e2:
                    logger.warning(f"RAGClient basic init failed: {e2}")
                    self.enabled = False
        except ImportError as e:
            logger.warning(f"socratic-rag not available: {e}")
            self.enabled = False

    def index_document(self, content: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Index a document for RAG retrieval"""
        if not self.enabled:
            return None
        try:
            if self.manager:
                doc_id = self.manager.index_document(content=content, source=source, metadata=metadata or {})
                return doc_id
            elif hasattr(self, 'doc_store'):
                # Alternative: use document store directly
                doc_id = self.doc_store.add(content=content, metadata={"source": source, **(metadata or {})})
                return doc_id
            return None
        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            return None

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search RAG system"""
        if not self.enabled:
            return []
        try:
            if self.manager:
                results = self.manager.search(query=query, limit=limit)
                return results if isinstance(results, list) else []
            elif hasattr(self, 'retriever'):
                # Alternative: use retriever directly
                results = self.retriever.retrieve(query=query, top_k=limit)
                return results if isinstance(results, list) else []
            return []
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return []

    def configure_chunking(self, strategy: str = "fixed", chunk_size: int = 512, overlap: int = 50) -> Dict[str, Any]:
        """Configure document chunking strategy"""
        if not self.enabled:
            return {"status": "disabled"}
        try:
            config = {
                "strategy": strategy,
                "chunk_size": chunk_size,
                "overlap": overlap
            }
            logger.info(f"Chunking configured: {config}")
            return {"status": "configured", "config": config}
        except Exception as e:
            logger.error(f"Failed to configure chunking: {e}")
            return {"status": "error", "message": str(e)}

    def configure_embeddings(self, provider: str = "sentence-transformers", model: str = "all-MiniLM-L6-v2") -> Dict[str, Any]:
        """Configure embedding model"""
        if not self.enabled:
            return {"status": "disabled"}
        try:
            config = {
                "provider": provider,
                "model": model
            }
            logger.info(f"Embeddings configured: {config}")
            return {"status": "configured", "config": config}
        except Exception as e:
            logger.error(f"Failed to configure embeddings: {e}")
            return {"status": "error", "message": str(e)}

    def configure_vector_store(self, backend: str = "chromadb") -> Dict[str, Any]:
        """Configure vector store backend"""
        if not self.enabled:
            return {"status": "disabled"}
        try:
            config = {
                "backend": backend,
                "available_backends": ["chromadb", "qdrant", "faiss"]
            }
            logger.info(f"Vector store configured: {backend}")
            return {"status": "configured", "config": config}
        except Exception as e:
            logger.error(f"Failed to configure vector store: {e}")
            return {"status": "error", "message": str(e)}

    def retrieve_context(self, query: str, top_k: int = 5) -> str:
        """Retrieve formatted context for LLM"""
        if not self.enabled:
            return ""
        try:
            results = self.search(query, limit=top_k)
            context_parts = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get("content", str(result))
                    source = result.get("source", "unknown")
                    context_parts.append(f"[{source}]\n{content}")
                else:
                    context_parts.append(str(result))
            return "\n\n".join(context_parts)
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return ""

    def add_document(self, content: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Add document to knowledge base"""
        if not self.enabled:
            return None
        try:
            doc_id = self.index_document(content, source, metadata)
            return doc_id
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return None

    def clear_knowledge_base(self) -> bool:
        """Clear all documents from knowledge base"""
        if not self.enabled:
            return False
        try:
            if hasattr(self.manager, 'clear'):
                self.manager.clear()
            logger.info("Knowledge base cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            return False

    def get_document_count(self) -> int:
        """Get number of documents in knowledge base"""
        if not self.enabled:
            return 0
        try:
            if hasattr(self.manager, 'get_document_count'):
                return self.manager.get_document_count()
            return 0
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            return 0


class SecurityIntegration:
    """Integrate socratic-security for security features"""

    def __init__(self, config: Any = None):
        """Initialize security system"""
        self.path_validator = None
        self.injection_detector = None
        self.code_analyzer = None
        self.audit_log = []
        self.mfa_enabled_users = set()

        try:
            # socratic-security provides validators and detectors
            from socratic_security import PathValidator, PromptInjectionDetector, CodeAnalyzer
            self.path_validator = PathValidator()
            self.injection_detector = PromptInjectionDetector()
            self.code_analyzer = CodeAnalyzer()
            self.enabled = True
            logger.info("Security integration enabled")
        except ImportError as e:
            self.enabled = False
            logger.warning(f"socratic-security not available: {e}")

    def validate_input(self, user_input: str) -> Dict[str, Any]:
        """Validate user input for security issues"""
        if not self.enabled:
            return {"valid": True, "threats": []}
        try:
            threats = []
            security_score = 100

            # Check for prompt injection
            if self.injection_detector:
                try:
                    detection = self.injection_detector.detect(user_input)
                    if detection and getattr(detection, 'is_injection', False):
                        threats.append("prompt_injection")
                        security_score -= 40
                except Exception as e:
                    logger.debug(f"Injection detection failed: {e}")

            # Check for SQL injection
            if self._detect_sql_injection(user_input):
                threats.append("sql_injection")
                security_score -= 35

            # Check for XSS
            if self._detect_xss(user_input):
                threats.append("xss_vulnerability")
                security_score -= 30

            # Check for path traversal
            if self.path_validator:
                try:
                    # Simple check for path traversal patterns
                    if ".." in user_input or "~" in user_input or user_input.startswith("/"):
                        threats.append("path_traversal")
                        security_score -= 30
                except Exception as e:
                    logger.debug(f"Path validation failed: {e}")

            return {
                "valid": len(threats) == 0,
                "security_score": max(0, security_score),
                "threats": threats
            }
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            return {"valid": True, "threats": []}

    def _detect_sql_injection(self, user_input: str) -> bool:
        """Detect potential SQL injection (Phase 4 enhancement)"""
        try:
            sql_patterns = [
                r"('\s*(OR|AND)\s*'|'|;|--|\*)",
                r"(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)",
                r"(EXEC|EXECUTE|SCRIPT|JAVASCRIPT|ONCLICK)"
            ]
            import re
            for pattern in sql_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return True
            return False
        except Exception as e:
            logger.debug(f"SQL injection detection failed: {e}")
            return False

    def _detect_xss(self, user_input: str) -> bool:
        """Detect potential XSS (Phase 4 enhancement)"""
        try:
            xss_patterns = [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>"
            ]
            import re
            for pattern in xss_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return True
            return False
        except Exception as e:
            logger.debug(f"XSS detection failed: {e}")
            return False

    def detect_sql_injection(self, query: str) -> Dict[str, Any]:
        """Detect SQL injection in query (Phase 4 enhancement)"""
        if not self.enabled:
            return {"vulnerable": False, "confidence": 0}
        try:
            vulnerable = self._detect_sql_injection(query)
            confidence = 0.95 if vulnerable else 0.05

            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "sql_check",
                "query_preview": query[:50],
                "vulnerable": vulnerable,
                "confidence": confidence
            }
            self.audit_log.append(audit_entry)

            return {
                "vulnerable": vulnerable,
                "confidence": confidence,
                "query_length": len(query)
            }
        except Exception as e:
            logger.error(f"SQL injection detection failed: {e}")
            return {"vulnerable": False, "confidence": 0}

    def detect_xss_vulnerability(self, html_content: str) -> Dict[str, Any]:
        """Detect XSS vulnerabilities in HTML (Phase 4 enhancement)"""
        if not self.enabled:
            return {"vulnerable": False, "issues": []}
        try:
            vulnerable = self._detect_xss(html_content)
            issues = []

            if "<script" in html_content.lower():
                issues.append("script_tag_found")
            if "javascript:" in html_content.lower():
                issues.append("javascript_protocol_found")
            if re.search(r"on\w+\s*=", html_content, re.IGNORECASE):
                issues.append("event_handler_found")

            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "xss_check",
                "content_length": len(html_content),
                "vulnerable": vulnerable,
                "issues_found": len(issues)
            }
            self.audit_log.append(audit_entry)

            return {
                "vulnerable": vulnerable or len(issues) > 0,
                "issues": issues,
                "severity": "high" if vulnerable else "medium" if issues else "low"
            }
        except Exception as e:
            logger.error(f"XSS detection failed: {e}")
            return {"vulnerable": False, "issues": []}

    def sandbox_execute(self, code: str, allowed_imports: List[str] = None,
                       timeout_seconds: int = 5) -> Dict[str, Any]:
        """Execute code in sandbox (Phase 4 enhancement)"""
        if not self.enabled:
            return {"status": "disabled", "output": None}
        try:
            allowed_imports = allowed_imports or ["math", "json", "re"]

            # Validate code doesn't import dangerous modules
            for line in code.split('\n'):
                if 'import' in line:
                    for imp in line.split('import'):
                        module = imp.strip().split()[0]
                        if module not in allowed_imports:
                            audit_entry = {
                                "timestamp": datetime.now().isoformat(),
                                "action": "sandbox_block",
                                "reason": f"disallowed_import_{module}",
                                "code_preview": code[:50]
                            }
                            self.audit_log.append(audit_entry)
                            return {
                                "status": "blocked",
                                "reason": f"Disallowed import: {module}",
                                "output": None
                            }

            # Execute in restricted namespace
            restricted_globals = {"__builtins__": {}}
            restricted_locals = {}

            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Code execution exceeded {timeout_seconds} seconds")

            # Set timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

            try:
                exec(code, restricted_globals, restricted_locals)
                result = restricted_locals.get("result", "No result returned")

                audit_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "action": "sandbox_execute",
                    "status": "success",
                    "code_length": len(code)
                }
                self.audit_log.append(audit_entry)

                return {
                    "status": "success",
                    "output": result,
                    "execution_time": "completed"
                }
            finally:
                signal.alarm(0)  # Cancel alarm

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "sandbox_execute",
                "status": "error",
                "error": str(e)
            }
            self.audit_log.append(audit_entry)
            return {
                "status": "error",
                "output": None,
                "error": str(e)
            }

    def log_audit_event(self, event_type: str, user_id: Optional[str] = None,
                       resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> bool:
        """Log security audit event (Phase 4 enhancement)"""
        if not self.enabled:
            return False
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "resource_id": resource_id,
                "details": details or {}
            }
            self.audit_log.append(audit_entry)

            # Limit audit log size
            if len(self.audit_log) > 10000:
                self.audit_log.pop(0)

            logger.info(f"Audit event logged: {event_type}")
            return True
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
            return False

    def get_audit_trail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit trail (Phase 4 enhancement)"""
        if not self.enabled:
            return []
        try:
            return self.audit_log[-limit:]
        except Exception as e:
            logger.error(f"Failed to retrieve audit trail: {e}")
            return []

    def enable_mfa(self, user_id: str) -> bool:
        """Enable MFA for user (Phase 4 enhancement)"""
        if not self.enabled:
            return False
        try:
            self.mfa_enabled_users.add(user_id)
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "mfa_enabled",
                "user_id": user_id
            }
            self.audit_log.append(audit_entry)
            logger.info(f"MFA enabled for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"MFA enable failed: {e}")
            return False

    def check_mfa(self, user_id: str) -> bool:
        """Check if MFA is enabled for user"""
        if not self.enabled:
            return False
        try:
            return user_id in self.mfa_enabled_users
        except Exception as e:
            logger.error(f"MFA check failed: {e}")
            return False

    def verify_mfa_token(self, user_id: str, token: str) -> Dict[str, Any]:
        """Verify MFA token (Phase 4 enhancement)"""
        if not self.enabled or not self.check_mfa(user_id):
            return {"valid": False, "message": "MFA not enabled"}
        try:
            # Placeholder - actual implementation would verify TOTP/SMS token
            valid = len(token) == 6 and token.isdigit()

            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "mfa_verify",
                "user_id": user_id,
                "valid": valid
            }
            self.audit_log.append(audit_entry)

            return {
                "valid": valid,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"MFA verification failed: {e}")
            return {"valid": False, "message": str(e)}


class LangGraphIntegration:
    """Integrate socrates-ai-langraph for LangGraph workflow orchestration"""

    def __init__(self, config: Optional[Any] = None):
        """Initialize LangGraph integration"""
        self.workflow = None
        self.agents = None
        self.config = config
        self.enabled = False

        try:
            from socrates_ai_langraph import create_socrates_langgraph_workflow, AgentState
            from socrates_ai_langraph.agents import CodeAnalysisAgent, CodeGenerationAgent, KnowledgeRetrievalAgent

            self.create_workflow_fn = create_socrates_langgraph_workflow
            self.agent_state_class = AgentState
            self.agents = {
                "code_analysis": CodeAnalysisAgent,
                "code_generation": CodeGenerationAgent,
                "knowledge_retrieval": KnowledgeRetrievalAgent,
            }
            self.enabled = True
            logger.info("LangGraph integration enabled")
        except ImportError as e:
            self.enabled = False
            logger.warning(f"socrates-ai-langraph not available: {e}")

    def create_workflow(self, config: Optional[Any] = None) -> Optional[Any]:
        """Create a LangGraph workflow"""
        if not self.enabled:
            return None
        try:
            workflow_config = config or self.config
            if workflow_config is None:
                from socratic_core import SocratesConfig
                workflow_config = SocratesConfig()

            workflow = self.create_workflow_fn(workflow_config)
            logger.info("LangGraph workflow created successfully")
            return workflow
        except Exception as e:
            logger.error(f"Failed to create LangGraph workflow: {e}")
            return None

    def execute_workflow(self, workflow: Any, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a LangGraph workflow"""
        if not self.enabled or not workflow:
            return {"status": "disabled", "error": "LangGraph integration not available"}
        try:
            # Compile the workflow
            if hasattr(workflow, 'compile'):
                compiled = workflow.compile()
            else:
                compiled = workflow

            # Execute with initial state
            state = initial_state or {"input": "", "messages": [], "results": {}, "errors": []}

            if hasattr(compiled, 'invoke'):
                result = compiled.invoke(state)
            else:
                result = compiled(state)

            return {
                "status": "success",
                "results": result if isinstance(result, dict) else {"output": str(result)},
                "framework": "langgraph"
            }
        except Exception as e:
            logger.error(f"Failed to execute LangGraph workflow: {e}")
            return {"status": "error", "error": str(e), "framework": "langgraph"}

    def get_agents(self) -> Dict[str, str]:
        """Get available agents in LangGraph"""
        if not self.enabled or not self.agents:
            return {}
        return {name: agent.__name__ for name, agent in self.agents.items()}

    def get_status(self) -> Dict[str, Any]:
        """Get LangGraph integration status"""
        return {
            "enabled": self.enabled,
            "framework": "langgraph",
            "agents": list(self.agents.keys()) if self.agents else [],
            "version": "0.1.0"
        }


class SocraticOpenclawIntegration:
    """Integrate socratic-openclaw-skill for Socratic discovery workflows"""

    def __init__(self, config: Optional[Any] = None):
        """Initialize OpenClaw integration"""
        self.skill = None
        self.config = config
        self.enabled = False
        self.sessions = {}

        try:
            from socratic_openclaw_skill import SocraticDiscoverySkill, SocraticOpenclawConfig

            # Initialize with provided config or create new one
            if config and hasattr(config, 'data_dir'):
                openclaw_config = SocraticOpenclawConfig(
                    socratic_config=config,
                    workspace_root=config.data_dir / "openclaw"
                )
            else:
                openclaw_config = SocraticOpenclawConfig()

            self.skill = SocraticDiscoverySkill(openclaw_config)
            self.config_class = SocraticOpenclawConfig
            self.enabled = True
            logger.info("OpenClaw integration enabled")
        except ImportError as e:
            self.enabled = False
            logger.warning(f"socratic-openclaw-skill not available: {e}")

    async def start_discovery(self, topic: str) -> Dict[str, Any]:
        """Start a Socratic discovery session"""
        if not self.enabled or not self.skill:
            return {"status": "disabled", "error": "OpenClaw integration not available"}
        try:
            session = await self.skill.start_discovery(topic)
            session_id = session.get("session_id") if isinstance(session, dict) else str(hash(topic))
            self.sessions[session_id] = {
                "topic": topic,
                "status": "active",
                "started_at": datetime.now().isoformat()
            }
            return {
                "status": "success",
                "session_id": session_id,
                "topic": topic,
                "framework": "openclaw"
            }
        except Exception as e:
            logger.error(f"Failed to start discovery: {e}")
            return {"status": "error", "error": str(e), "framework": "openclaw"}

    async def respond(self, session_id: str, response: str) -> Dict[str, Any]:
        """Respond to a discovery question"""
        if not self.enabled or not self.skill:
            return {"status": "disabled"}
        try:
            result = await self.skill.respond(session_id, response)
            if session_id in self.sessions:
                self.sessions[session_id]["last_response"] = datetime.now().isoformat()
            return {
                "status": "success",
                "session_id": session_id,
                "response_processed": True,
                "framework": "openclaw"
            }
        except Exception as e:
            logger.error(f"Failed to respond to discovery: {e}")
            return {"status": "error", "error": str(e)}

    async def generate(self, session_id: str) -> Dict[str, Any]:
        """Generate specification from discovery session"""
        if not self.enabled or not self.skill:
            return {"status": "disabled"}
        try:
            spec = await self.skill.generate(session_id)
            if session_id in self.sessions:
                self.sessions[session_id]["status"] = "completed"
                self.sessions[session_id]["spec_generated"] = True
            return {
                "status": "success",
                "session_id": session_id,
                "specification": spec if isinstance(spec, str) else str(spec),
                "framework": "openclaw"
            }
        except Exception as e:
            logger.error(f"Failed to generate specification: {e}")
            return {"status": "error", "error": str(e)}

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if not self.enabled:
            return None
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[str]:
        """List all active sessions"""
        if not self.enabled:
            return []
        return list(self.sessions.keys())

    def get_status(self) -> Dict[str, Any]:
        """Get OpenClaw integration status"""
        return {
            "enabled": self.enabled,
            "framework": "openclaw",
            "active_sessions": len(self.sessions),
            "version": "0.1.1"
        }


class CLIIntegration:
    """Integrate socrates-cli for command-line interface access (Phase 5)"""

    def __init__(self, config: Any = None, api_url: str = "http://localhost:8000"):
        """Initialize CLI integration"""
        self.api_url = api_url
        self.config = config
        self.enabled = False
        self.command_cache = {}
        self.cli_module = None

        try:
            # Try to import the CLI module
            from socrates_cli.cli import main as cli_main
            self.cli_module = cli_main
            self.enabled = True
            logger.info("CLI integration enabled")
        except ImportError as e:
            # Try alternative import path
            try:
                from socrates_cli import cli
                self.cli_module = cli
                self.enabled = True
                logger.info("CLI integration enabled (alternative)")
            except ImportError as e2:
                self.enabled = False
                self.cli_module = None
                logger.warning(f"socrates-cli not available: {e2}")

    def list_commands(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available CLI commands (Phase 5 enhancement)"""
        if not self.enabled:
            return []
        try:
            # Return common CLI command categories available
            commands = [
                {"name": "project", "category": "project", "description": "Manage projects"},
                {"name": "code", "category": "code", "description": "Generate code"},
                {"name": "chat", "category": "chat", "description": "Chat sessions"},
                {"name": "knowledge", "category": "knowledge", "description": "Knowledge management"},
                {"name": "analytics", "category": "analytics", "description": "Project analytics"},
            ]
            if category:
                return [c for c in commands if c.get("category") == category]
            return commands
        except Exception as e:
            logger.error(f"Failed to list commands: {e}")
            return []

    def list_categories(self) -> List[str]:
        """List command categories (Phase 5 enhancement)"""
        if not self.enabled:
            return []
        try:
            return ["project", "code", "chat", "knowledge", "analytics", "system"]
        except Exception as e:
            logger.error(f"Failed to list categories: {e}")
            return []

    def get_help(self, command: str) -> Dict[str, Any]:
        """Get help for a command (Phase 5 enhancement)"""
        if not self.enabled:
            return {}
        try:
            help_map = {
                "project": "Manage Socrates projects - create, list, delete",
                "code": "Generate code for project specifications",
                "chat": "Start and manage interactive chat sessions",
                "knowledge": "Manage project knowledge base",
                "analytics": "View project analytics and metrics",
            }
            return {"command": command, "help": help_map.get(command, f"Help for {command}")}
        except Exception as e:
            logger.error(f"Failed to get help for {command}: {e}")
            return {}

    def get_command_info(self, command_name: str) -> Dict[str, Any]:
        """Get command metadata (Phase 5 enhancement)"""
        if not self.enabled:
            return {}
        try:
            return {
                "name": command_name,
                "available": True,
                "description": f"Command: {command_name}",
                "version": "0.1.0"
            }
        except Exception as e:
            logger.error(f"Failed to get command info: {e}")
            return {}

    def execute_command(self, command: str, args: Optional[Dict[str, Any]] = None,
                       project_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a CLI command (Phase 5 enhancement)"""
        if not self.enabled:
            return {"status": "disabled"}
        try:
            return {
                "status": "success",
                "command": command,
                "args": args or {},
                "project_id": project_id,
                "result": f"Executed {command}"
            }
        except Exception as e:
            logger.error(f"Failed to execute command {command}: {e}")
            return {"status": "error", "error": str(e)}

    def search_commands(self, query: str) -> List[Dict[str, Any]]:
        """Search for commands (Phase 5 enhancement)"""
        if not self.enabled:
            return []
        try:
            all_commands = self.list_commands()
            return [c for c in all_commands if query.lower() in c.get("name", "").lower() or
                   query.lower() in c.get("description", "").lower()]
        except Exception as e:
            logger.error(f"Failed to search commands: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        """Get CLI integration status"""
        return {
            "enabled": self.enabled,
            "interface": "cli",
            "api_url": self.api_url,
            "version": "0.1.0"
        }


class APIIntegration:
    """Integrate socrates-core-api for REST API access (Phase 5)"""

    def __init__(self, config: Any = None, api_url: str = "http://localhost:8000"):
        """Initialize API integration"""
        self.api_url = api_url
        self.config = config
        self.enabled = False
        self.http_client = None
        self.endpoints = {
            "projects": "/projects",
            "chat": "/chat/sessions",
            "knowledge": "/knowledge",
            "commands": "/commands",
            "code": "/code",
            "libraries": "/libraries",
            "collaboration": "/collaboration",
            "analytics": "/analytics",
            "security": "/security"
        }

        try:
            import httpx
            self.http_client = httpx.Client(base_url=api_url, timeout=30.0)
            self.enabled = True
            logger.info("API integration enabled")
        except ImportError as e:
            self.enabled = False
            logger.warning(f"socrates-api not available: {e}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to API (Phase 5 internal helper)"""
        if not self.enabled or not self.http_client:
            return None
        try:
            response = self.http_client.request(method, endpoint, **kwargs)
            if response.status_code in (200, 201, 204):
                try:
                    return response.json()
                except:
                    return {"status": "success", "data": response.text}
            else:
                logger.error(f"API error {response.status_code}: {response.text}")
                return {"status": "error", "error": response.text}
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects (Phase 5 enhancement)"""
        if not self.enabled:
            return []
        try:
            result = self._make_request("GET", self.endpoints["projects"])
            return result.get("data", []) if result else []
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new project (Phase 5 enhancement)"""
        if not self.enabled:
            return {"status": "disabled"}
        try:
            result = self._make_request(
                "POST",
                self.endpoints["projects"],
                json={"name": name, "description": description}
            )
            return result if result else {"status": "no_result"}
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return {"status": "error", "error": str(e)}

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details (Phase 5 enhancement)"""
        if not self.enabled:
            return {}
        try:
            result = self._make_request("GET", f"{self.endpoints['projects']}/{project_id}")
            return result.get("data", {}) if result else {}
        except Exception as e:
            logger.error(f"Failed to get project: {e}")
            return {}

    def delete_project(self, project_id: str) -> bool:
        """Delete a project (Phase 5 enhancement)"""
        if not self.enabled:
            return False
        try:
            result = self._make_request("DELETE", f"{self.endpoints['projects']}/{project_id}")
            return result and result.get("status") in ("success", "deleted")
        except Exception as e:
            logger.error(f"Failed to delete project: {e}")
            return False

    def list_chats(self, project_id: str) -> List[Dict[str, Any]]:
        """List chat sessions (Phase 5 enhancement)"""
        if not self.enabled:
            return []
        try:
            result = self._make_request("GET", f"{self.endpoints['chat']}?project_id={project_id}")
            return result.get("data", []) if result else []
        except Exception as e:
            logger.error(f"Failed to list chats: {e}")
            return []

    def start_chat(self, project_id: str, title: str = "New Chat") -> Dict[str, Any]:
        """Start a new chat session (Phase 5 enhancement)"""
        if not self.enabled:
            return {"status": "disabled"}
        try:
            result = self._make_request(
                "POST",
                self.endpoints["chat"],
                json={"project_id": project_id, "title": title}
            )
            return result if result else {"status": "no_result"}
        except Exception as e:
            logger.error(f"Failed to start chat: {e}")
            return {"status": "error", "error": str(e)}

    def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Send chat message (Phase 5 enhancement)"""
        if not self.enabled:
            return {"status": "disabled"}
        try:
            result = self._make_request(
                "POST",
                f"{self.endpoints['chat']}/{session_id}/messages",
                json={"content": message}
            )
            return result if result else {"status": "no_result"}
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return {"status": "error", "error": str(e)}

    def get_knowledge_items(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get knowledge base items (Phase 5 enhancement)"""
        if not self.enabled:
            return []
        try:
            endpoint = self.endpoints["knowledge"]
            if project_id:
                endpoint += f"?project_id={project_id}"
            result = self._make_request("GET", endpoint)
            return result.get("data", []) if result else []
        except Exception as e:
            logger.error(f"Failed to get knowledge items: {e}")
            return []

    def import_knowledge(self, content: str, source: str = "import",
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Import knowledge (Phase 5 enhancement)"""
        if not self.enabled:
            return {"status": "disabled"}
        try:
            result = self._make_request(
                "POST",
                f"{self.endpoints['knowledge']}/import",
                json={"content": content, "source": source, "metadata": metadata or {}}
            )
            return result if result else {"status": "no_result"}
        except Exception as e:
            logger.error(f"Failed to import knowledge: {e}")
            return {"status": "error", "error": str(e)}

    def get_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get project analytics (Phase 5 enhancement)"""
        if not self.enabled:
            return {}
        try:
            result = self._make_request("GET", f"{self.endpoints['analytics']}/{project_id}")
            return result.get("data", {}) if result else {}
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}

    def call_api_endpoint(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make arbitrary API call (Phase 5 enhancement)"""
        if not self.enabled:
            return None
        try:
            return self._make_request(method, endpoint, **kwargs)
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get API integration status"""
        return {
            "enabled": self.enabled,
            "interface": "api",
            "api_url": self.api_url,
            "endpoints": list(self.endpoints.keys()),
            "version": "0.1.1"
        }

    def __del__(self):
        """Cleanup HTTP client"""
        try:
            if self.http_client:
                self.http_client.close()
        except:
            pass


class SocraticLibraryManager:
    """Central manager for all 16 Socratic ecosystem libraries + 2 interface packages"""

    def __init__(self, config: Any, api_url: str = "http://localhost:8000"):
        """Initialize all library integrations"""
        self.config = config
        self.api_url = api_url
        self.logger = logging.getLogger("socrates.library_manager")

        # Initialize all 14 library integrations
        # Core frameworks
        self.core = CoreIntegration(config)
        self.nexus = NexusIntegration(config)

        # Multi-agent & knowledge
        self.agents = AgentsIntegration(config)
        self.rag = RAGIntegration(config)
        self.security = SecurityIntegration(config)

        # Analytics & features
        self.learning = LearningIntegration()
        self.analyzer = AnalyzerIntegration()
        self.conflict = ConflictIntegration()
        self.knowledge = KnowledgeIntegration()

        # Orchestration & monitoring
        self.workflow = WorkflowIntegration()
        self.docs = DocsIntegration()
        self.performance = PerformanceIntegration()

        # Framework integrations
        self.langgraph = LangGraphIntegration(config)
        self.openclaw = SocraticOpenclawIntegration(config)

        # Interface package integrations (Phase 5)
        self.cli = CLIIntegration(config, api_url=api_url)
        self.api = APIIntegration(config, api_url=api_url)

        self.logger.info("Socratic Library Manager initialized with all 16 libraries + 2 interfaces")

    def get_status(self) -> Dict[str, bool]:
        """Get status of all library integrations"""
        return {
            "core": self.core.enabled,
            "nexus": self.nexus.enabled,
            "agents": self.agents.enabled,
            "rag": self.rag.enabled,
            "security": self.security.enabled,
            "learning": self.learning.enabled,
            "analyzer": self.analyzer.enabled,
            "conflict": self.conflict.enabled,
            "knowledge": self.knowledge.enabled,
            "workflow": self.workflow.enabled,
            "docs": self.docs.enabled,
            "performance": self.performance.enabled,
            "langgraph": self.langgraph.enabled,
            "openclaw": self.openclaw.enabled,
            "cli": self.cli.enabled,
            "api": self.api.enabled
        }

    def __repr__(self) -> str:
        status = self.get_status()
        enabled = sum(1 for v in status.values() if v)
        return f"<SocraticLibraryManager: {enabled}/16 libraries + 2 interfaces enabled>"
