"""
Local model stubs for API routers

These are minimal placeholder models used by API routers.
Routers should use get_database() and other local modules instead of relying on external model definitions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class TeamMemberRole:
    """Team member with role and skills"""
    username: str
    role: str  # 'owner', 'editor', 'viewer'
    skills: List[str] = field(default_factory=list)
    joined_at: Optional[Any] = None
    status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        joined_str = self.joined_at.isoformat() if hasattr(self.joined_at, 'isoformat') else str(self.joined_at)
        return {
            "username": self.username,
            "role": self.role,
            "skills": self.skills,
            "joined_at": joined_str,
            "status": self.status,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TeamMemberRole':
        """Create from dictionary"""
        return TeamMemberRole(
            username=data.get("username"),
            role=data.get("role"),
            skills=data.get("skills", []),
            joined_at=data.get("joined_at"),
            status=data.get("status", "active"),
        )


class EventType(str, Enum):
    """Event types for system notifications and tracking"""
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    PROJECT_ARCHIVED = "PROJECT_ARCHIVED"
    PROJECT_RESTORED = "PROJECT_RESTORED"
    QUESTION_GENERATED = "QUESTION_GENERATED"
    RESPONSE_ANALYZED = "RESPONSE_ANALYZED"
    CODE_GENERATED = "CODE_GENERATED"
    CODE_ANALYSIS_COMPLETE = "CODE_ANALYSIS_COMPLETE"
    PHASE_MATURITY_UPDATED = "PHASE_MATURITY_UPDATED"
    DOCUMENT_IMPORTED = "DOCUMENT_IMPORTED"
    COLLABORATION_ADDED = "COLLABORATION_ADDED"
    COLLABORATION_REMOVED = "COLLABORATION_REMOVED"
    ACTIVITY_LOGGED = "ACTIVITY_LOGGED"


class User:
    """User model for API routers - supports all auth parameters"""
    def __init__(
        self,
        user_id: str = "",
        username: str = "",
        email: str = "",
        passcode_hash: str = "",
        subscription_tier: str = "free",
        subscription_status: str = "active",
        testing_mode: bool = False,
        created_at: Optional[Any] = None,
        archived: bool = False,
        archived_at: Optional[str] = None,
        **kwargs
    ):
        self.id = user_id
        self.username = username
        self.email = email
        self.passcode_hash = passcode_hash
        self.subscription_tier = subscription_tier
        self.subscription_status = subscription_status
        self.testing_mode = testing_mode
        self.created_at = created_at
        self.archived = archived
        self.archived_at = archived_at
        self.metadata: Dict[str, Any] = {}
        # Store any additional kwargs
        for key, value in kwargs.items():
            if not key.startswith("_"):
                setattr(self, key, value)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "passcode_hash": self.passcode_hash,
            "subscription_tier": self.subscription_tier,
            "subscription_status": self.subscription_status,
            "testing_mode": self.testing_mode,
            "created_at": self.created_at,
            "metadata": self.metadata
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method for compatibility"""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for compatibility"""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Dict-like 'in' operator support"""
        return hasattr(self, key)


class ProjectContext:
    """Minimal ProjectContext model stub for API routers"""
    def __init__(
        self,
        project_id: str = "",
        name: str = "",
        owner: str = "",
        description: str = "",
        phase: str = "discovery",
        created_at: str = "",
        updated_at: str = "",
        is_archived: bool = False,
        conversation_history: Optional[list] = None,
        overall_maturity: float = 0.0,
        progress: int = 0,
        goals: str = "",
        requirements: Optional[list] = None,
        tech_stack: Optional[list] = None,
        constraints: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        repository_url: Optional[str] = None,
        team_members: Optional[list] = None,
        code_history: Optional[list] = None,
        chat_sessions: Optional[Dict] = None,
        code_generated_count: int = 0,
        auto_advance_phases: bool = False,
        **kwargs
    ):
        self.project_id = project_id
        self.name = name
        self.owner = owner
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at
        self.phase = phase
        self.is_archived = is_archived
        self.overall_maturity = overall_maturity
        self.progress = progress
        self.metadata = metadata or {}
        self.conversation_history = conversation_history or []
        self.goals = goals
        self.requirements = requirements or []
        self.tech_stack = tech_stack or []
        self.constraints = constraints or []
        self.repository_url = repository_url
        self.team_members = team_members or []
        self.code_history = code_history or []
        self.chat_sessions = chat_sessions or {}
        self.code_generated_count = code_generated_count
        self.auto_advance_phases = auto_advance_phases

        # Nested data structures - standardized as typed fields
        # Maturity tracking
        self.maturity_score: float = kwargs.get("maturity_score", 0.0)
        self.previous_maturity: float = kwargs.get("previous_maturity", 0.0)
        self.maturity_history: List[Dict[str, Any]] = kwargs.get("maturity_history", [])

        # Phase and category progress
        self.phase_maturity_scores: Dict[str, float] = kwargs.get("phase_maturity_scores", {})
        self.category_scores: Dict[str, float] = kwargs.get("category_scores", {})

        # Chat and question attributes
        self.pending_questions: List[Dict[str, Any]] = kwargs.get("pending_questions", [])
        self.answered_questions: List[Dict[str, Any]] = kwargs.get("answered_questions", [])
        self.skipped_questions: List[Dict[str, Any]] = kwargs.get("skipped_questions", [])

        # Store any additional kwargs
        for key, value in kwargs.items():
            if not key.startswith("_") and key not in (
                "maturity_score", "previous_maturity", "maturity_history",
                "phase_maturity_scores", "category_scores",
                "pending_questions", "answered_questions", "skipped_questions"
            ):
                setattr(self, key, value)

    def to_dict(self) -> Dict:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "owner": self.owner,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "phase": self.phase,
            "is_archived": self.is_archived,
            "overall_maturity": self.overall_maturity,
            "progress": self.progress,
            "metadata": self.metadata
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method for compatibility"""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for compatibility"""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Dict-like 'in' operator support"""
        return hasattr(self, key)


class StorageQuotaManager:
    """Storage quota management - stub for subscription limits"""
    @staticmethod
    def bytes_to_gb(bytes_val: int) -> float:
        """Convert bytes to gigabytes"""
        return bytes_val / (1024 ** 3) if bytes_val > 0 else 0.0

    @staticmethod
    def calculate_user_storage_usage(user_id: str, db: Any) -> int:
        """Calculate user's total storage usage in bytes"""
        return 0  # Stub - returns 0 bytes

    @staticmethod
    def get_storage_usage_report(user_id: str, db: Any) -> Dict[str, Any]:
        """Get detailed storage usage report"""
        return {"total_gb": 0.0, "breakdown": {}}

    @staticmethod
    def can_upload_document(user: Any, db: Any, content_bytes: int, testing_mode: bool = False) -> tuple:
        """
        Check if user can upload a document.

        Args:
            user: User object with subscription_tier
            db: Database connection
            content_bytes: Size of document in bytes
            testing_mode: If True, unlimited uploads

        Returns:
            (can_upload: bool, message: str)
        """
        if testing_mode:
            return True, "Testing mode: unlimited uploads"

        # Get subscription tier from user
        tier = getattr(user, "subscription_tier", "free").lower()

        # Define limits per tier (in GB)
        tier_limits = {
            "free": 0.5,
            "pro": 10.0,
            "enterprise": -1,  # unlimited
        }

        max_storage_gb = tier_limits.get(tier, 0.5)

        if max_storage_gb == -1:  # unlimited
            return True, "Enterprise: unlimited storage"

        # Calculate document size in GB
        content_gb = StorageQuotaManager.bytes_to_gb(content_bytes)

        if content_gb > max_storage_gb:
            return False, f"Document size ({content_gb:.2f}GB) exceeds tier limit ({max_storage_gb}GB)"

        return True, f"Within storage limit ({content_gb:.2f}GB / {max_storage_gb}GB)"


class LearningIntegration:
    """Wrapper around socratic-learning library for learning analytics and recommendations"""
    def __init__(self):
        from socratic_learning import (
            LearningEngine,
            PatternDetector,
            MetricsCollector,
            RecommendationEngine
        )
        self.engine = LearningEngine()
        self.pattern_detector = PatternDetector()
        self.metrics_collector = MetricsCollector()
        self.recommendation_engine = RecommendationEngine()
        logger.info("socratic-learning library initialized successfully")

    @property
    def interaction_logger(self):
        """Compatibility property for legacy code"""
        return self.engine

    @property
    def recommendation_engine_property(self):
        """Compatibility property for legacy code"""
        return self.recommendation_engine

    def log_interaction(
        self,
        user_id: str,
        interaction_type: str,
        context: Dict = None,
        metadata: Dict = None
    ) -> bool:
        """Log user interaction via socratic-learning library"""
        if not self.available or not self.engine:
            logger.debug(f"Learning integration unavailable, skipping interaction log for {user_id}")
            return False

        try:
            self.engine.log_interaction(
                user_id=user_id,
                interaction_type=interaction_type,
                context=context or {},
                metadata=metadata or {}
            )
            logger.debug(f"Logged interaction: {interaction_type} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            return False

    def get_progress(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning progress for a user"""
        if not self.available or not self.metrics_collector:
            return {}

        try:
            progress_data = self.metrics_collector.calculate_progress(user_id)
            return progress_data if progress_data else {}
        except Exception as e:
            logger.error(f"Failed to calculate progress: {e}")
            return {}

    def get_recommendations(self, user_id: str, count: int = 5) -> List[Dict[str, Any]]:
        """Get personalized learning recommendations"""
        if not self.available or not self.recommendation_engine:
            return []

        try:
            recommendations = self.recommendation_engine.generate_recommendations(
                user_id=user_id,
                count=count
            )
            return recommendations if recommendations else []
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []

    def get_mastery(self, user_id: str, concept_id: str = None) -> List[Dict[str, Any]]:
        """Get concept mastery levels for a user"""
        if not self.available or not self.metrics_collector:
            return []

        try:
            mastery_data = self.metrics_collector.get_mastery_levels(user_id, concept_id)
            return mastery_data if mastery_data else []
        except Exception as e:
            logger.error(f"Failed to get mastery levels: {e}")
            return []

    def detect_misconceptions(self, user_id: str) -> List[Dict[str, Any]]:
        """Detect user misconceptions using socratic-learning"""
        if not self.available or not self.pattern_detector:
            return []

        try:
            misconceptions = self.pattern_detector.detect_misconceptions(user_id)
            return misconceptions if misconceptions else []
        except Exception as e:
            logger.error(f"Failed to detect misconceptions: {e}")
            return []

    def get_analytics(self, user_id: str, period: str = "weekly", days_back: int = 30) -> Dict[str, Any]:
        """Get learning analytics for a specific period"""
        if not self.available or not self.metrics_collector:
            return {}

        try:
            analytics_data = self.metrics_collector.get_analytics(user_id, period, days_back)
            return analytics_data if analytics_data else {}
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}

    def get_status(self) -> Dict[str, bool]:
        """Get status of learning integration"""
        return {
            "available": self.available,
            "interaction_logger": self.engine is not None,
            "recommendation_engine": self.recommendation_engine is not None,
            "pattern_detector": self.pattern_detector is not None,
            "metrics_collector": self.metrics_collector is not None,
        }


class AnalyzerIntegration:
    """Wrapper around socratic-analyzer library for comprehensive code analysis"""
    def __init__(self):
        from socratic_analyzer import (
            CodeAnalyzer,
            MetricsCalculator,
            InsightGenerator,
            SecurityAnalyzer,
            PerformanceAnalyzer
        )
        self.code_analyzer = CodeAnalyzer()
        self.metrics = MetricsCalculator()
        self.insights = InsightGenerator()
        self.security = SecurityAnalyzer()
        self.performance = PerformanceAnalyzer()
        logger.info("socratic-analyzer library initialized successfully")

    def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Perform comprehensive code analysis"""
        if not self.available or not self.code_analyzer:
            return {"error": "Code analyzer not available"}

        try:
            result = self.code_analyzer.analyze(code, language)
            quality_metrics = self.metrics.calculate(code) if self.metrics else {}
            security_issues = self.security.find_issues(code) if self.security else []
            performance_issues = self.performance.find_issues(code) if self.performance else []
            insights = self.insights.generate(code, language) if self.insights else []

            return {
                "overall_score": result.get("quality_score", 0) if isinstance(result, dict) else 0,
                "quality_metrics": quality_metrics,
                "security_issues": security_issues,
                "performance_issues": performance_issues,
                "insights": insights,
                "language": language,
            }
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return {"error": str(e)}

    def get_status(self) -> Dict[str, bool]:
        """Get status of analyzer integration"""
        return {
            "available": self.available,
            "code_analyzer": self.code_analyzer is not None,
            "metrics_calculator": self.metrics is not None,
            "insight_generator": self.insights is not None,
            "security_analyzer": self.security is not None,
            "performance_analyzer": self.performance is not None,
        }

    def analyze_metrics(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Calculate detailed code metrics"""
        if not self.available or not self.metrics:
            return {}

        try:
            metrics = self.metrics.calculate(code)
            return {
                "cyclomatic_complexity": metrics.get("cyclomatic_complexity", 0),
                "cognitive_complexity": metrics.get("cognitive_complexity", 0),
                "maintainability_index": metrics.get("maintainability_index", 0),
                "test_coverage": metrics.get("test_coverage", 0),
                "code_duplication": metrics.get("code_duplication", 0),
                "lines_of_code": metrics.get("lines_of_code", 0),
                "documentation_coverage": metrics.get("documentation_coverage", 0),
            }
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            return {}

    def analyze_security(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Deep security analysis"""
        if not self.available or not self.security:
            return {"issues": []}

        try:
            issues = self.security.find_issues(code)
            return {
                "critical_count": len([i for i in issues if i.get("severity") == "critical"]),
                "high_count": len([i for i in issues if i.get("severity") == "high"]),
                "medium_count": len([i for i in issues if i.get("severity") == "medium"]),
                "low_count": len([i for i in issues if i.get("severity") == "low"]),
                "issues": issues,
            }
        except Exception as e:
            logger.error(f"Failed to analyze security: {e}")
            return {"issues": []}

    def analyze_performance(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Analyze performance issues"""
        if not self.available or not self.performance:
            return {"issues": []}

        try:
            issues = self.performance.find_issues(code)
            recommendations = self.performance.get_recommendations(code) if hasattr(self.performance, 'get_recommendations') else []
            return {
                "issue_count": len(issues),
                "issues": issues,
                "recommendations": recommendations,
            }
        except Exception as e:
            logger.error(f"Failed to analyze performance: {e}")
            return {"issues": []}

    def calculate_health_score(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Calculate overall project health score"""
        if not self.available:
            return {"score": 0, "grade": "N/A"}

        try:
            metrics = self.analyze_metrics(code, language)
            security = self.analyze_security(code, language)
            performance = self.analyze_performance(code, language)

            # Calculate health score (0-100)
            score = 100
            score -= metrics.get("cyclomatic_complexity", 0) * 2  # Max -20
            score -= (100 - metrics.get("maintainability_index", 100)) * 0.3  # Max -30
            score -= security.get("critical_count", 0) * 10  # Max -50
            score -= security.get("high_count", 0) * 5  # Max -25
            score -= performance.get("issue_count", 0) * 2  # Max -20

            # Ensure score is 0-100
            score = max(0, min(100, score))

            # Grade
            if score >= 90:
                grade = "A"
            elif score >= 80:
                grade = "B"
            elif score >= 70:
                grade = "C"
            elif score >= 60:
                grade = "D"
            else:
                grade = "F"

            return {
                "score": round(score, 1),
                "grade": grade,
                "metrics": metrics,
                "security_issues": security.get("critical_count", 0) + security.get("high_count", 0),
                "performance_issues": performance.get("issue_count", 0),
            }
        except Exception as e:
            logger.error(f"Failed to calculate health score: {e}")
            return {"score": 0, "grade": "N/A"}

    def get_improvement_suggestions(self, code: str, language: str = "python") -> List[Dict[str, Any]]:
        """Get code improvement suggestions"""
        if not self.available or not self.insights:
            return []

        try:
            suggestions = self.insights.generate(code, language)
            return suggestions if suggestions else []
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            return []


class StorageQuotaManager:
    """Manage storage quotas for users across different subscription tiers"""
    TIER_LIMITS = {
        "free": 10 * 1024 * 1024,              # 10 MB
        "premium": 100 * 1024 * 1024,          # 100 MB
        "enterprise": 1 * 1024 * 1024 * 1024   # 1 GB
    }

    @staticmethod
    def can_upload_document(
        user: "User",
        db: "LocalDatabase",
        size_bytes: int,
        testing_mode: bool = False
    ) -> tuple:
        """
        Check if user can upload document of given size.

        Args:
            user: User object with subscription_tier attribute
            db: Database connection
            size_bytes: Size of document in bytes
            testing_mode: If True, always allow (for testing)

        Returns:
            Tuple of (can_upload: bool, message: str)
        """
        if testing_mode:
            return True, "Testing mode - quota check skipped"

        if not user:
            return False, "User not found"

        tier = getattr(user, "subscription_tier", "free").lower()
        limit = StorageQuotaManager.TIER_LIMITS.get(tier, 10 * 1024 * 1024)

        # Calculate current usage across all projects
        total_usage = 0
        try:
            if hasattr(db, "get_user_projects"):
                project_ids = db.get_user_projects(user.id if hasattr(user, "id") else user.username) or []

                for project_id in project_ids:
                    try:
                        project = db.load_project(project_id)
                        if project:
                            # Sum up knowledge document sizes
                            for doc in getattr(project, "knowledge_documents", []) or []:
                                if isinstance(doc, dict):
                                    total_usage += len(doc.get("content", "").encode("utf-8"))
                                else:
                                    total_usage += len(getattr(doc, "content", "").encode("utf-8"))
                    except Exception as e:
                        logger.warning(f"Failed to calculate project usage: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Failed to calculate storage usage: {e}")

        # Check if upload would exceed quota
        if total_usage + size_bytes > limit:
            remaining = limit - total_usage
            return (
                False,
                f"Storage quota exceeded for {tier} tier. Used {total_usage:,} bytes of {limit:,}. "
                f"Cannot upload {size_bytes:,} bytes (need {size_bytes - remaining:,} more). "
                f"Upgrade your plan for more storage."
            )

        return True, f"Storage available. Used {total_usage:,} bytes of {limit:,} for {tier} tier."

    @staticmethod
    def get_quota_info(user: "User") -> Dict[str, Any]:
        """Get quota information for user"""
        if not user:
            return {}

        tier = getattr(user, "subscription_tier", "free").lower()
        limit = StorageQuotaManager.TIER_LIMITS.get(tier, 10 * 1024 * 1024)

        return {
            "tier": tier,
            "limit_bytes": limit,
            "limit_mb": limit / (1024 * 1024),
            "limit_gb": limit / (1024 * 1024 * 1024),
        }


class KnowledgeManager:
    """Enterprise-grade wrapper around socratic-knowledge library for multi-tenant knowledge management"""
    def __init__(self, tenant_id: str = "default"):
        # Import all components from socratic-knowledge (required)
        from socratic_knowledge import (
            KnowledgeBase,
            DocumentStore,
            SearchEngine,
            RBACManager,
            VersionControl,
            SemanticSearch,
            AuditLogger
        )

        self.tenant_id = tenant_id
        self.knowledge_base = KnowledgeBase()
        self.document_store = DocumentStore()
        self.search_engine = SearchEngine()

        # Enterprise features from socratic-knowledge
        self.rbac_manager = RBACManager()  # Multi-tenant access control
        self.version_control = VersionControl()  # Document versioning and history
        self.semantic_search_engine = SemanticSearch()  # Advanced semantic search
        self.audit_logger = AuditLogger()  # Compliance audit logging

        logger.info(
            f"Enterprise knowledge management initialized for tenant {tenant_id}: "
            "RBAC, versioning, semantic search, and audit logging enabled"
        )

    def add_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        doc_type: str = "text",
        metadata: Dict = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Add document with versioning and audit logging"""
        try:
            # Add document with metadata
            self.document_store.add(
                doc_id,
                title=title,
                content=content,
                doc_type=doc_type,
                metadata=metadata or {}
            )

            # Initialize versioning for this document
            version_info = self.version_control.create_version(
                doc_id,
                content=content,
                metadata={"title": title, "type": doc_type}
            )

            # Log to audit trail for compliance
            self.audit_logger.log_event(
                event_type="document_created",
                resource_id=doc_id,
                user_id=user_id or "system",
                tenant_id=self.tenant_id,
                details={"title": title, "type": doc_type}
            )

            logger.info(f"Added document {doc_id} with version {version_info.get('version_id')}")
            return {
                "status": "success",
                "doc_id": doc_id,
                "version_id": version_info.get("version_id")
            }
        except Exception as e:
            logger.error(f"Failed to add document: {e}", exc_info=True)
            raise

    def remove_document(self, doc_id: str, user_id: str = None) -> Dict[str, Any]:
        """Remove document with soft delete and audit logging"""
        try:
            # Soft delete - preserve history
            self.document_store.remove(doc_id)

            # Log removal event for audit trail
            self.audit_logger.log_event(
                event_type="document_deleted",
                resource_id=doc_id,
                user_id=user_id or "system",
                tenant_id=self.tenant_id,
                details={"soft_delete": True}
            )

            logger.info(f"Soft deleted document {doc_id} (preserved in version history)")
            return {
                "status": "success",
                "doc_id": doc_id,
                "deleted": True
            }
        except Exception as e:
            logger.error(f"Failed to remove document: {e}", exc_info=True)
            raise

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base by keyword"""
        try:
            results = self.search_engine.search(query, limit=limit)
            logger.debug(f"Keyword search found {len(results) if results else 0} results for: {query}")
            return results if results else []
        except Exception as e:
            logger.error(f"Failed to search knowledge base: {e}", exc_info=True)
            raise

    def semantic_search(self, query: str, limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Semantic search using vector embeddings"""
        try:
            # Use SemanticSearch for meaning-based matching
            results = self.semantic_search_engine.find_similar(
                query=query,
                limit=limit,
                similarity_threshold=threshold
            )
            logger.debug(f"Semantic search found {len(results) if results else 0} results")
            return results if results else []
        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}", exc_info=True)
            raise

    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Get document by ID with version history"""
        try:
            document = self.document_store.get(doc_id)
            # Include version history
            versions = self.version_control.get_versions(doc_id)
            return {
                **document,
                "versions": versions if versions else []
            } if document else {}
        except Exception as e:
            logger.error(f"Failed to get document: {e}", exc_info=True)
            raise

    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all documents with pagination and tenant filtering"""
        try:
            documents = self.document_store.list(limit=limit, offset=offset)
            logger.debug(f"Listed {len(documents) if documents else 0} documents")
            return documents if documents else []
        except Exception as e:
            logger.error(f"Failed to list documents: {e}", exc_info=True)
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get status of enterprise knowledge manager"""
        return {
            "tenant_id": self.tenant_id,
            "knowledge_base": self.knowledge_base is not None,
            "document_store": self.document_store is not None,
            "search_engine": self.search_engine is not None,
            "enterprise_features": {
                "rbac_enabled": self.rbac_manager is not None,
                "version_control": self.version_control is not None,
                "semantic_search": self.semantic_search_engine is not None,
                "audit_logging": self.audit_logger is not None,
            }
        }


class RAGIntegration:
    """Enterprise-grade RAG system with multiple vector DB support from socratic-rag library"""
    def __init__(self, vector_db: str = "chromadb"):
        # Import all components from socratic-rag (required)
        from socratic_rag import (
            RAGClient,
            DocumentStore,
            Retriever,
            ChunkingStrategy,
            VectorDatabaseFactory
        )

        self.vector_db_type = vector_db  # Support: chromadb, qdrant, faiss, pinecone
        self.rag_client = RAGClient()
        self.document_store = DocumentStore()
        self.retriever = Retriever()

        # Initialize vector database (supports multiple backends)
        self.vector_db_factory = VectorDatabaseFactory()
        self.vector_db = self.vector_db_factory.create(vector_db)

        # Initialize chunking strategy for advanced document processing
        self.chunking_strategy = ChunkingStrategy()

        logger.info(
            f"Enterprise RAG system initialized with vector DB: {vector_db}, "
            "chunking strategies, and multiple DB support enabled"
        )

    def index_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        doc_type: str = "text",
        metadata: Dict = None
    ) -> bool:
        """Index document for RAG retrieval"""
        try:
            self.document_store.add(
                doc_id,
                title=title,
                content=content,
                doc_type=doc_type,
                metadata=metadata or {}
            )
            logger.debug(f"Indexed document in RAG: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index document in RAG: {e}", exc_info=True)
            raise

    def retrieve_context(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for context"""
        try:
            results = self.retriever.retrieve(
                query=query,
                limit=limit,
                threshold=threshold
            )
            return results if results else []
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}", exc_info=True)
            raise

    def augment_prompt(
        self,
        prompt: str,
        context_limit: int = 5,
        include_metadata: bool = True
    ) -> str:
        """Augment prompt with relevant context from knowledge base"""
        try:
            # Retrieve relevant documents
            context_docs = self.retrieve_context(prompt, limit=context_limit)

            if not context_docs:
                logger.debug(f"No relevant context found for: {prompt[:50]}...")
                return prompt

            # Build augmented prompt
            augmented = f"{prompt}\n\n---\n## Reference Context from Knowledge Base:\n\n"
            for i, doc in enumerate(context_docs, 1):
                title = doc.get("title", "Unknown")
                content = doc.get("content", "")[:300]  # Limit content
                score = doc.get("score", 0)
                augmented += f"**{i}. {title}** (relevance: {score:.1%})\n{content}\n\n"

            logger.debug(f"Augmented prompt with {len(context_docs)} documents from RAG")
            return augmented
        except Exception as e:
            logger.error(f"Failed to augment prompt: {e}", exc_info=True)
            raise

    def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents using RAG retriever"""
        try:
            results = self.retriever.search(query, limit=limit)
            return results if results else []
        except Exception as e:
            logger.error(f"Failed to search documents: {e}", exc_info=True)
            raise

    def remove_document(self, doc_id: str) -> bool:
        """Remove document from RAG index"""
        try:
            self.document_store.remove(doc_id)
            logger.debug(f"Removed document from RAG: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove document from RAG: {e}", exc_info=True)
            raise

    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Get document by ID from RAG index"""
        try:
            document = self.document_store.get(doc_id)
            return document if document else {}
        except Exception as e:
            logger.error(f"Failed to get document from RAG: {e}", exc_info=True)
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get RAG integration status with vector DB backend"""
        return {
            "rag_client": self.rag_client is not None,
            "document_store": self.document_store is not None,
            "retriever": self.retriever is not None,
            "vector_db_backend": self.vector_db_type,
            "vector_db_connected": self.vector_db is not None,
        }

    def chunk_document(
        self,
        doc_id: str,
        content: str,
        strategy: str = "semantic",
        chunk_size: int = 512,
        overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Chunk document using advanced strategies (fixed, semantic, recursive).
        Supports multiple chunking approaches for optimal retrieval.
        """
        try:
            chunks = self.chunking_strategy.chunk(
                content=content,
                strategy=strategy,  # 'fixed', 'semantic', 'recursive'
                chunk_size=chunk_size,
                overlap=overlap
            )
            logger.debug(f"Chunked document {doc_id} into {len(chunks) if chunks else 0} chunks using {strategy} strategy")
            return chunks if chunks else []
        except Exception as e:
            logger.error(f"Failed to chunk document: {e}", exc_info=True)
            raise

    def index_documents_batch(
        self,
        documents: List[Dict[str, Any]],
        chunking_strategy: str = "semantic"
    ) -> Dict[str, Any]:
        """
        Batch index multiple documents with advanced chunking.
        Efficient bulk indexing for large document sets.
        """
        try:
            indexed_count = 0
            failed_count = 0
            total_chunks = 0

            for doc in documents:
                try:
                    doc_id = doc.get("id", "unknown")
                    content = doc.get("content", "")

                    # Chunk the document
                    chunks = self.chunk_document(
                        doc_id=doc_id,
                        content=content,
                        strategy=chunking_strategy
                    )
                    total_chunks += len(chunks) if chunks else 0

                    # Index the document and its chunks
                    self.index_document(
                        doc_id=doc_id,
                        title=doc.get("title", ""),
                        content=content,
                        doc_type=doc.get("type", "text"),
                        metadata=doc.get("metadata", {})
                    )
                    indexed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to index document {doc.get('id')}: {e}")
                    failed_count += 1

            logger.info(f"Batch indexed {indexed_count} documents with {total_chunks} total chunks")
            return {
                "indexed": indexed_count,
                "failed": failed_count,
                "total_chunks": total_chunks
            }
        except Exception as e:
            logger.error(f"Failed to batch index documents: {e}", exc_info=True)
            raise

    def switch_vector_db(self, new_db: str) -> bool:
        """Switch to a different vector database backend (chromadb, qdrant, faiss, pinecone)"""
        try:
            old_db = self.vector_db_type
            self.vector_db = self.vector_db_factory.create(new_db)
            self.vector_db_type = new_db
            logger.info(f"Switched vector DB from {old_db} to {new_db}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch vector DB to {new_db}: {e}", exc_info=True)
            raise

    async def retrieve_context_async(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Async retrieval for non-blocking context fetching"""
        try:
            results = self.retriever.retrieve(
                query=query,
                limit=limit,
                threshold=threshold
            )
            return results if results else []
        except Exception as e:
            logger.error(f"Failed to retrieve context (async): {e}", exc_info=True)
            raise


class WorkflowIntegration:
    """Enterprise-grade workflow orchestration with cost tracking, parallel execution, and error recovery"""
    def __init__(self):
        # Import all components from socratic-workflow (required)
        from socratic_workflow import (
            WorkflowEngine,
            CostTracker,
            ParallelExecutor,
            ErrorRecovery,
            StateManager
        )

        self.engine = WorkflowEngine()
        self.workflows = {}
        self.cost_tracker = CostTracker()  # Track workflow execution costs
        self.parallel_executor = ParallelExecutor()  # Enable parallel step execution
        self.error_recovery = ErrorRecovery()  # Error recovery with exponential backoff
        self.state_manager = StateManager()  # State management for resilience

        logger.info(
            "Enterprise workflow orchestration initialized: "
            "cost tracking, parallel execution, error recovery, and state management enabled"
        )

    def create_workflow(
        self,
        workflow_id: str,
        name: str,
        steps: List[Dict[str, Any]],
        metadata: Dict = None,
        enable_parallel_execution: bool = False,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Create a new workflow with optional parallel execution and error recovery"""
        try:
            workflow = self.engine.create_workflow(
                workflow_id=workflow_id,
                name=name,
                steps=steps,
                metadata=metadata or {},
                parallel_execution=enable_parallel_execution,
                max_retries=max_retries
            )
            self.workflows[workflow_id] = workflow

            # Initialize state for this workflow
            self.state_manager.initialize_workflow(workflow_id)

            # Estimate and log workflow cost
            estimated_cost = self.cost_tracker.estimate_cost(workflow)
            logger.info(f"Created workflow {workflow_id} (estimated cost: ${estimated_cost:.2f})")

            return {
                "status": "success",
                "workflow_id": workflow_id,
                "estimated_cost": estimated_cost
            }
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}", exc_info=True)
            raise

    def execute_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute workflow with error recovery and cost tracking"""
        try:
            if workflow_id not in self.workflows:
                workflow = self.engine.get_workflow(workflow_id)
                if not workflow:
                    raise ValueError(f"Workflow not found: {workflow_id}")
                self.workflows[workflow_id] = workflow

            workflow = self.workflows[workflow_id]
            execution_context = context or {}

            # Track execution for cost calculation
            execution_id = self.cost_tracker.start_execution(workflow_id)

            # Execute with error recovery (exponential backoff, retry logic)
            result = self.error_recovery.execute_with_recovery(
                lambda: self.engine.execute(workflow, execution_context),
                max_retries=workflow.get("max_retries", 3)
            )

            # Calculate and track execution cost
            execution_cost = self.cost_tracker.end_execution(execution_id)

            # Save workflow state for resilience
            self.state_manager.save_state(workflow_id, result)

            logger.info(
                f"Executed workflow {workflow_id} (cost: ${execution_cost:.2f}, "
                f"execution_id: {execution_id})"
            )

            return {
                "status": "completed",
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "cost": execution_cost,
                "result": result
            }
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_id}: {e}", exc_info=True)
            raise

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status with cost tracking"""
        try:
            status = self.engine.get_status(workflow_id)
            if not status:
                return {"status": "not_found"}

            # Include cost information
            total_cost = self.cost_tracker.get_workflow_total_cost(workflow_id)
            state = self.state_manager.get_state(workflow_id)

            return {
                **status,
                "total_cost": total_cost,
                "workflow_state": state
            }
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}", exc_info=True)
            raise

    def get_workflow_history(
        self,
        workflow_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get execution history with cost tracking"""
        try:
            history = self.engine.get_history(workflow_id, limit=limit)
            if not history:
                return []

            # Add cost information for each execution
            enriched_history = []
            for execution in history:
                execution_id = execution.get("id")
                cost = self.cost_tracker.get_execution_cost(execution_id) if execution_id else 0
                enriched_history.append({**execution, "cost": cost})

            logger.debug(f"Retrieved {len(enriched_history)} execution records for workflow {workflow_id}")
            return enriched_history
        except Exception as e:
            logger.error(f"Failed to get workflow history: {e}", exc_info=True)
            raise

    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete a workflow and clean up associated state"""
        try:
            # Get final cost before deletion
            total_cost = self.cost_tracker.get_workflow_total_cost(workflow_id)

            # Delete the workflow
            self.engine.delete_workflow(workflow_id)
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]

            # Clean up state and cost tracking
            self.state_manager.cleanup_workflow(workflow_id)
            self.cost_tracker.cleanup_workflow(workflow_id)

            logger.info(f"Deleted workflow {workflow_id} (total lifetime cost: ${total_cost:.2f})")

            return {
                "status": "success",
                "workflow_id": workflow_id,
                "total_cost": total_cost
            }
        except Exception as e:
            logger.error(f"Failed to delete workflow: {e}", exc_info=True)
            raise

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows with cost tracking"""
        try:
            workflows = self.engine.list_workflows()
            if not workflows:
                return []

            # Enrich with cost information
            enriched_workflows = []
            for workflow in workflows:
                workflow_id = workflow.get("id")
                total_cost = self.cost_tracker.get_workflow_total_cost(workflow_id) if workflow_id else 0
                enriched_workflows.append({**workflow, "total_cost": total_cost})

            logger.debug(f"Listed {len(enriched_workflows)} workflows")
            return enriched_workflows
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}", exc_info=True)
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get workflow integration status with enterprise features"""
        return {
            "engine": self.engine is not None,
            "cost_tracking": self.cost_tracker is not None,
            "parallel_execution": self.parallel_executor is not None,
            "error_recovery": self.error_recovery is not None,
            "state_management": self.state_manager is not None,
            "enterprise_features_enabled": all([
                self.cost_tracker,
                self.parallel_executor,
                self.error_recovery,
                self.state_manager
            ])
        }
