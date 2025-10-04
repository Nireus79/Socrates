#!/usr/bin/env python3
"""
ContextAnalyzerAgent - Enhanced Context Analysis with Conflict Detection
=========================================================================

Handles comprehensive context analysis including pattern recognition, conflict detection,
and intelligent insights. Fully corrected according to project standards.

Capabilities:
- Advanced conversation pattern analysis
- Multi-dimensional conflict detection
- Project health assessment
- Technology compatibility checking
- Risk identification and mitigation
- Context-aware recommendations
"""
import uuid
from typing import Dict, List, Any, Optional

try:
    from src.core import ServiceContainer, DateTimeHelper, ValidationError
    from src.models import (
        Project, ConversationMessage, UserRole, TechnicalRole,
        ProjectPhase, ModuleStatus, RiskLevel, ConversationStatus,
        ProjectContext, ModuleContext, TaskContext, Conflict, ConflictType
    )
    from src.database import get_database
    from .base import BaseAgent, require_project_access, log_agent_action

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    # Fallback implementations
    import logging
    from datetime import datetime
    from enum import Enum


    class ConflictType(Enum):
        TECHNICAL = "technical"
        BUSINESS = "business"
        SCOPE = "scope"
        RESOURCE = "resource"
        TIMELINE = "timeline"


    class Conflict:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


    def get_logger(name):
        return logging.getLogger(name)


    class ServiceContainer:
        def get_logger(self, name):
            import logging
            return logging.getLogger(name)

        def get_config(self):
            return {}

        def get_event_bus(self):
            return None

        def get_db_manager(self):
            return None


    def get_database():
        return None


    class ProjectContext:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


    class ModuleContext:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


    class TaskContext:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


    class DateTimeHelper:
        @staticmethod
        def now():
            return datetime.now()

        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None


    class ValidationError(Exception):
        pass


    class UserRole(Enum):
        PROJECT_MANAGER = "project_manager"
        TECHNICAL_LEAD = "technical_lead"
        DEVELOPER = "developer"


    class TechnicalRole(Enum):
        PROJECT_MANAGER = "project_manager"
        TECHNICAL_LEAD = "technical_lead"
        DEVELOPER = "developer"


    class ProjectPhase(Enum):
        PLANNING = "planning"
        DEVELOPMENT = "development"
        TESTING = "testing"


    class ModuleStatus(Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"


    class RiskLevel(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"


    class ConversationStatus(Enum):
        ACTIVE = "active"
        PAUSED = "paused"
        COMPLETED = "completed"


    class Project:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


    class ConversationMessage:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


    class BaseAgent:
        def __init__(self, agent_id, name, services=None):
            self.agent_id = agent_id
            self.name = name
            self.services = services
            self.logger = get_logger(agent_id)
            self.db_service = get_database()
            self.events = None

        def _error_response(self, message, error_code=None):
            return {'success': False, 'error': message}

        def _success_response(self, message, data=None):
            return {'success': True, 'message': message, 'data': data or {}}


    def require_project_access(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


    def log_agent_action(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


class ContextAnalyzerAgent(BaseAgent):
    """
    Enhanced context analysis agent with conflict detection

    Absorbs: ConflictDetectorAgent functionality
    Capabilities: Pattern recognition, conflict resolution, intelligent insights
    """

    def __init__(self, services: Optional[ServiceContainer] = None):
        """Initialize ContextAnalyzerAgent with ServiceContainer dependency injection"""
        super().__init__("context_analyzer", "Context Analyzer", services)

        self.patterns = {}
        self.conflict_rules = self._load_conflict_rules()

        # Initialize context repositories via database service
        from src.database import get_database
        db = get_database()
        if db:
            self.project_context_repo = db.project_contexts
            self.module_context_repo = db.module_contexts
            self.task_context_repo = db.task_contexts
            self.conflict_repo = db.conflicts
        else:
            self.project_context_repo = None
            self.module_context_repo = None
            self.task_context_repo = None
            self.conflict_repo = None

        # Context cache settings
        self.context_refresh_threshold_minutes = 60

        if self.logger:
            self.logger.info("ContextAnalyzerAgent initialized with conflict detection rules and context persistence")

    def get_capabilities(self) -> List[str]:
        return [
            "analyze_context", "detect_conflicts", "generate_insights",
            "pattern_recognition", "suggest_improvements", "risk_assessment",
            "technology_compatibility", "recommendation_engine", "analyze_conversation",
            "assess_project_health", "detect_requirement_conflicts"
        ]

    def _load_conflict_rules(self) -> Dict[str, Any]:
        """Load conflict detection rules"""
        if self.logger:
            self.logger.debug("Loading conflict detection rules")

        rules = {
            "technology_conflicts": {
                "database": {
                    "sqlite": ["high_concurrency", "large_datasets", "concurrent_users"],
                    "mysql": ["simple_deployment", "serverless", "single_user"],
                    "postgresql": ["simple_setup", "sqlite_compatibility", "minimal_features"]
                },
                "frameworks": {
                    "flask": ["complex_orm", "enterprise_features", "admin_panel"],
                    "django": ["microservices", "simple_api", "minimal_features"],
                    "fastapi": ["traditional_templates", "django_admin", "complex_forms"]
                }
            },
            "requirement_conflicts": [
                ("high_performance", "simple_development"),
                ("enterprise_features", "minimal_dependencies"),
                ("real_time", "eventual_consistency"),
                ("security_focus", "development_speed"),
                ("scalability", "simplicity"),
                ("rich_features", "fast_loading")
            ]
        }

        if self.logger:
            self.logger.debug(f"Loaded {len(rules['requirement_conflicts'])} requirement conflict rules")

        return rules

    def _needs_refresh(self, context, force_refresh: bool = False) -> bool:
        """Check if context needs to be refreshed"""
        if force_refresh:
            return True

        if not context or not context.last_analyzed_at:
            return True

        # Check if context is older than threshold
        now = DateTimeHelper.now()
        last_analyzed = context.last_analyzed_at

        # Handle timezone mismatch between aware and naive datetimes
        if now.tzinfo is not None and last_analyzed.tzinfo is None:
            # Make last_analyzed timezone-aware (assume UTC)
            from datetime import timezone
            last_analyzed = last_analyzed.replace(tzinfo=timezone.utc)
        elif now.tzinfo is None and last_analyzed.tzinfo is not None:
            # Make now timezone-aware (assume UTC)
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)

        age_minutes = (now - last_analyzed).total_seconds() / 60

        return age_minutes > self.context_refresh_threshold_minutes

    def _project_context_to_analysis(self, context: ProjectContext) -> Dict[str, Any]:
        """Convert ProjectContext model to analysis dictionary"""
        return {
            'business_domain': context.business_domain,
            'target_audience': context.target_audience,
            'business_goals': context.business_goals,
            'existing_systems': context.existing_systems,
            'integration_requirements': context.integration_requirements,
            'performance_requirements': context.performance_requirements,
            'team_structure': context.team_structure,
            'budget_constraints': context.budget_constraints,
            'timeline_constraints': context.timeline_constraints,
            'last_analyzed_at': DateTimeHelper.to_iso_string(context.last_analyzed_at),
            'cached': True
        }

    def _analysis_to_project_context(self, project_id: str, analysis: Dict[str, Any]) -> ProjectContext:
        """Convert analysis dictionary to ProjectContext model"""
        return ProjectContext(
            id=str(uuid.uuid4()),
            project_id=project_id,
            business_domain=analysis.get('business_domain', ''),
            target_audience=analysis.get('target_audience', ''),
            business_goals=analysis.get('business_goals', []),
            existing_systems=analysis.get('existing_systems', []),
            integration_requirements=analysis.get('integration_requirements', []),
            performance_requirements=analysis.get('performance_requirements', {}),
            team_structure=analysis.get('team_structure', {}),
            budget_constraints=analysis.get('budget_constraints', {}),
            timeline_constraints=analysis.get('timeline_constraints', {}),
            last_analyzed_at=DateTimeHelper.now(),
            created_at=DateTimeHelper.now(),
            updated_at=DateTimeHelper.now()
        )

    @require_project_access
    @log_agent_action
    def _analyze_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive context analysis with caching"""
        project_id = data.get('project_id')
        force_refresh = data.get('force_refresh', False)

        if self.logger:
            self.logger.info(f"Analyzing context for project {project_id} (force_refresh={force_refresh})")

        try:
            # Check for cached context
            if self.project_context_repo and not force_refresh:
                cached_context = self.project_context_repo.get_by_project_id(project_id)

                if cached_context and not self._needs_refresh(cached_context, force_refresh):
                    if self.logger:
                        self.logger.info(f"Using cached context for project {project_id}")

                    # Return cached analysis
                    analysis = self._project_context_to_analysis(cached_context)
                    analysis['project_id'] = project_id
                    analysis['analysis_timestamp'] = DateTimeHelper.to_iso_string(DateTimeHelper.now())

                    return self._success_response("Context retrieved from cache", {
                        'context': analysis,
                        'cached': True
                    })

            # No cache or refresh needed - perform full analysis
            if self.logger:
                self.logger.info(f"Performing fresh context analysis for project {project_id}")

            db = get_database()
            project = db.projects.get_by_id(project_id) if db else None
            if not project:
                return self._error_response(f"Project not found: {project_id}")

            # Perform analysis (use existing logic)
            # Simplified analysis for now
            analysis = self._analyze_full_context(project)

            # Save context to database
            if self.project_context_repo:
                try:
                    context = self._analysis_to_project_context(project_id, analysis)
                    self.project_context_repo.upsert(context)
                    if self.logger:
                        self.logger.info(f"Saved context to database for project {project_id}")
                except Exception as e:
                    # Don't fail analysis if save fails
                    if self.logger:
                        self.logger.warning(f"Failed to save context: {e}")

            analysis['cached'] = False
            return self._success_response("Context analysis complete", {
                'context': analysis
            })

        except Exception as e:
            error_msg = f"Context analysis failed: {e}"
            if self.logger:
                self.logger.error(error_msg)
            return self._error_response(error_msg)

    def _analyze_full_context(self, project: Project) -> Dict[str, Any]:
        """Full context analysis including all aspects"""
        if self.logger:
            self.logger.info(f"Performing full context analysis for project {project.name}")

        try:
            analysis = {
                'project_id': project.id,
                'project_name': project.name,
                'analysis_timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'project_health': self._assess_project_health_internal(project),
                'conversation_insights': self._analyze_conversation_patterns(project),
                'technical_assessment': self._analyze_technical_context(project),
                'conflict_analysis': self._detect_all_conflicts(project),
                'recommendations': [],
                'risk_factors': [],
                'strengths': []
            }

            # Generate comprehensive recommendations
            analysis['recommendations'] = self._generate_context_recommendations(analysis)
            analysis['risk_factors'] = self._extract_risk_factors(analysis)
            analysis['strengths'] = self._identify_project_strengths(analysis)

            if self.logger:
                self.logger.info(f"Full context analysis completed for project {project.name}")

            return analysis

        except Exception as e:
            if self.logger:
                self.logger.error(f"Full context analysis failed for project {project.name}: {e}")
            raise

    @require_project_access
    @log_agent_action
    def _analyze_conversation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation patterns and user behavior"""
        project_id = data.get('project_id')

        if self.logger:
            self.logger.info(f"Analyzing conversation patterns for project {project_id}")

        try:
            from src.database import get_database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")
            project = db.projects.get_by_id(project_id)
            if not project:
                if self.logger:
                    self.logger.error(f"Project {project_id} not found")
                raise ValidationError("Project not found")

            return self._analyze_conversation_patterns(project)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Conversation analysis failed for project {project_id}: {e}")
            raise

    def _analyze_conversation_patterns(self, project: Project) -> Dict[str, Any]:
        """Analyze conversation patterns and user behavior"""
        if self.logger:
            self.logger.debug(f"Analyzing conversation patterns for project {project.name}")

        try:
            conversation_insights = {
                'total_sessions': 0,
                'user_engagement': {'score': 0, 'level': 'unknown'},
                'response_quality': {'score': 0, 'level': 'unknown'},
                'phase_distribution': {},
                'role_coverage': [],
                'conversation_depth': 0
            }

            # Try to get conversation data from Socratic sessions
            try:
                from src.database import get_database
                db = get_database()
                sessions = db.socratic_sessions.get_by_project_id(project.id) if db else []
                conversation_insights['total_sessions'] = len(sessions)

                if sessions:
                    # Calculate engagement metrics
                    total_questions = sum(getattr(s, 'total_questions', 0) for s in sessions)
                    total_answered = sum(getattr(s, 'questions_answered', 0) for s in sessions)

                    if total_questions > 0:
                        engagement_score = (total_answered / total_questions) * 100
                        conversation_insights['user_engagement'] = {
                            'score': round(engagement_score, 1),
                            'level': 'high' if engagement_score > 70 else 'medium' if engagement_score > 40 else 'low'
                        }

                    # Analyze phase distribution
                    conversation_insights['phase_distribution'] = self._analyze_phase_distribution(sessions)

            except AttributeError:
                if self.logger:
                    self.logger.debug("Socratic sessions repository not available")

            if self.logger:
                self.logger.debug(f"Conversation analysis completed for project {project.name}")

            return conversation_insights

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error analyzing conversation patterns: {e}")
            return {
                'total_sessions': 0,
                'user_engagement': {'score': 0, 'level': 'unknown'},
                'response_quality': {'score': 0, 'level': 'unknown'},
                'phase_distribution': {},
                'role_coverage': [],
                'conversation_depth': 0
            }

    def _analyze_phase_distribution(self, sessions: List[Any]) -> Dict[str, int]:
        """Analyze distribution of conversation phases"""
        phases = {}

        try:
            for session in sessions:
                phase = 'discovery'
                if phase in phases:
                    phases[phase] += 1
                else:
                    phases[phase] = 1

            if self.logger:
                self.logger.debug(f"Phase distribution: {phases}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error analyzing phase distribution: {e}")

        return phases

    def _analyze_technical_context(self, project: Project) -> Dict[str, Any]:
        """Analyze technical context and completeness"""
        if self.logger:
            self.logger.debug(f"Analyzing technical context for project {project.name}")

        try:
            tech_analysis = {
                'architecture_pattern': 'not_specified',
                'technology_stack': project.technology_stack if hasattr(project, 'technology_stack') else {},
                'deployment_target': 'not_specified',
                'language_preferences': [],
                'technical_completeness': 0.0
            }

            # Calculate technical completeness score
            completeness_factors = [
                bool(hasattr(project, 'technology_stack') and project.technology_stack),
                bool(hasattr(project, 'constraints') and project.constraints),
                bool(hasattr(project, 'requirements') and len(project.requirements) > 2),
                bool(hasattr(project, 'description') and project.description and len(project.description) > 20),
                bool(hasattr(project, 'success_criteria') and project.success_criteria)
            ]

            tech_analysis['technical_completeness'] = (sum(completeness_factors) / len(completeness_factors)) * 100

            if self.logger:
                completeness_score = tech_analysis['technical_completeness']
                self.logger.debug(f"Technical analysis completed - Completeness: {completeness_score:.1f}%")

            return tech_analysis

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error analyzing technical context: {e}")
            return {
                'architecture_pattern': 'error',
                'technology_stack': {},
                'deployment_target': 'error',
                'language_preferences': [],
                'technical_completeness': 0.0
            }

    @require_project_access
    @log_agent_action
    def _detect_conflicts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect all types of conflicts in project"""
        project_id = data.get('project_id')
        session_id = data.get('session_id', '')

        if self.logger:
            self.logger.info(f"Starting conflict detection for project {project_id}")

        try:
            from src.database import get_database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")
            project = db.projects.get_by_id(project_id)
            if not project:
                if self.logger:
                    self.logger.error(f"Project {project_id} not found")
                raise ValidationError("Project not found")

            # Detect all conflicts
            conflicts = self._detect_all_conflicts(project)

            # Save conflicts to database
            conflict_ids = self._save_conflicts_to_db(project_id, session_id, conflicts)

            # Add conflict IDs to response
            conflicts['saved_conflict_ids'] = conflict_ids
            conflicts['conflicts_persisted'] = len(conflict_ids)

            if self.logger:
                self.logger.info(f"Detected and saved {len(conflict_ids)} conflicts for project {project_id}")

            return self._success_response("Conflict detection complete", conflicts)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Conflict detection failed for project {project_id}: {e}")
            return self._error_response(f"Conflict detection failed: {e}")

    def _detect_all_conflicts(self, project: Project) -> Dict[str, Any]:
        """Detect all types of conflicts in project"""
        if self.logger:
            self.logger.debug(f"Detecting all conflicts for project {project.name}")

        try:
            conflicts = {
                'technology_conflicts': self._detect_technology_conflicts(project),
                'requirement_conflicts': self._detect_requirement_conflicts(project),
                'timeline_conflicts': self._detect_timeline_conflicts(project),
                'resource_conflicts': self._detect_resource_conflicts(project)
            }

            # Calculate overall conflict assessment
            all_conflicts = []
            for conflict_list in conflicts.values():
                if isinstance(conflict_list, list):
                    all_conflicts.extend(conflict_list)

            total_conflicts = len(all_conflicts)

            # Determine severity
            high_severity = sum(1 for c in all_conflicts if c.get('severity') == 'high')
            medium_severity = sum(1 for c in all_conflicts if c.get('severity') == 'medium')

            if high_severity > 0:
                overall_severity = 'high'
            elif medium_severity > 2:
                overall_severity = 'high'
            elif medium_severity > 0 or total_conflicts > 3:
                overall_severity = 'medium'
            else:
                overall_severity = 'low'

            conflicts.update({
                'total_count': total_conflicts,
                'severity': overall_severity,
                'summary': f"Found {total_conflicts} conflicts with {overall_severity} severity. " +
                           "Review and address conflicts before proceeding." if total_conflicts > 0 else "No conflicts detected."
            })

            if self.logger:
                self.logger.info(
                    f"Conflict detection completed for project {project.name}: {total_conflicts} conflicts ({overall_severity} severity)")

            return conflicts

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error detecting conflicts for project {project.name}: {e}")
            raise

    def _detect_technology_conflicts(self, project: Project) -> List[Dict[str, Any]]:
        """Detect technology stack conflicts"""
        if self.logger:
            self.logger.debug(f"Detecting technology conflicts for project {project.name}")

        conflicts = []

        try:
            tech_stack = getattr(project, 'technology_stack', {})
            requirements = getattr(project, 'requirements', [])

            if not tech_stack:
                if self.logger:
                    self.logger.debug("No technology stack defined, skipping technology conflict detection")
                return conflicts

            # Check for database conflicts
            database = tech_stack.get('database', '').lower()
            if database and database in self.conflict_rules['technology_conflicts']['database']:
                conflicting_reqs = self.conflict_rules['technology_conflicts']['database'][database]
                for req in requirements:
                    req_lower = req.lower()
                    for conflict_req in conflicting_reqs:
                        if conflict_req in req_lower:
                            conflict = {
                                'type': 'technology_database',
                                'database': database,
                                'conflicting_requirement': req,
                                'message': f'Database choice "{database}" may conflict with requirement: {req}',
                                'severity': 'medium',
                                'suggestion': f'Consider alternative database or modify requirement'
                            }
                            conflicts.append(conflict)

                            if self.logger:
                                self.logger.warning(f"Technology conflict detected: {database} vs {req}")

            # Check for framework conflicts
            framework = tech_stack.get('backend', '').lower() or tech_stack.get('framework', '').lower()
            if framework and framework in self.conflict_rules['technology_conflicts']['frameworks']:
                conflicting_reqs = self.conflict_rules['technology_conflicts']['frameworks'][framework]
                for req in requirements:
                    req_lower = req.lower()
                    for conflict_req in conflicting_reqs:
                        if conflict_req in req_lower:
                            conflict = {
                                'type': 'technology_framework',
                                'framework': framework,
                                'conflicting_requirement': req,
                                'message': f'Framework choice "{framework}" may conflict with requirement: {req}',
                                'severity': 'medium',
                                'suggestion': f'Consider alternative framework or adjust requirement'
                            }
                            conflicts.append(conflict)

                            if self.logger:
                                self.logger.warning(f"Framework conflict detected: {framework} vs {req}")

            if self.logger:
                self.logger.debug(f"Technology conflict detection completed: {len(conflicts)} conflicts found")

            return conflicts

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error detecting technology conflicts: {e}")
            return []

    def _detect_requirement_conflicts(self, project: Project) -> List[Dict[str, Any]]:
        """Detect conflicting requirements"""
        if self.logger:
            self.logger.debug(f"Detecting requirement conflicts for project {project.name}")

        conflicts = []

        try:
            requirements = getattr(project, 'requirements', [])
            requirements_lower = [req.lower() for req in requirements]

            # Check for known conflicting requirement pairs
            for req1, req2 in self.conflict_rules['requirement_conflicts']:
                req1_present = any(req1 in req for req in requirements_lower)
                req2_present = any(req2 in req for req in requirements_lower)

                if req1_present and req2_present:
                    conflict = {
                        'type': 'requirement_conflict',
                        'requirement_1': req1,
                        'requirement_2': req2,
                        'message': f'Conflicting requirements detected: {req1} vs {req2}',
                        'severity': 'medium',
                        'suggestion': f'Prioritize either {req1.replace("_", " ")} or {req2.replace("_", " ")}, or find a balanced approach'
                    }
                    conflicts.append(conflict)

                    if self.logger:
                        self.logger.warning(f"Requirement conflict detected: {req1} vs {req2}")

            if self.logger:
                self.logger.debug(f"Requirement conflict detection completed: {len(conflicts)} conflicts found")

            return conflicts

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error detecting requirement conflicts: {e}")
            return []

    def _detect_timeline_conflicts(self, project: Project) -> List[Dict[str, Any]]:
        """Detect timeline and scheduling conflicts"""
        if self.logger:
            self.logger.debug(f"Detecting timeline conflicts for project {project.name}")

        conflicts = []

        try:
            # TODO TASK 6.2: Add ModuleRepository and TaskRepository to DatabaseService
            # Currently disabled because DatabaseService doesn't have .modules or .tasks repositories
            # See: src/database/service.py - ModuleRepository and TaskRepository are missing
            #
            # Original code attempted:
            # db = get_database()
            # modules = db.modules.get_by_project_id(project.id)  # AttributeError: no 'modules'
            #
            # To fix:
            # 1. Create ModuleRepository(BaseRepository[Module]) in src/database/repositories.py
            # 2. Create TaskRepository(BaseRepository[Task]) in src/database/repositories.py
            # 3. Add self.modules and self.tasks to DatabaseService._init_repositories()
            # 4. Export repositories in src/database/__init__.py
            # 5. Re-enable this conflict detection logic

            if self.logger:
                self.logger.warning(
                    "Timeline conflict detection disabled - ModuleRepository not yet implemented. "
                    "See TODO in _detect_timeline_conflicts method."
                )

            # Return empty conflicts until repositories are added
            return []

        except Exception as e:
            if self.logger:
                self.logger.error(f"Timeline conflict detection failed: {e}")
            return []

    def _detect_resource_conflicts(self, project: Project) -> List[Dict[str, Any]]:
        """Detect resource allocation conflicts"""
        if self.logger:
            self.logger.debug(f"Detecting resource conflicts for project {project.name}")

        conflicts = []

        try:
            # TODO TASK 6.2: Add ModuleRepository and TaskRepository to DatabaseService
            # Currently disabled because DatabaseService doesn't have .modules repository
            # See: src/database/service.py - ModuleRepository missing
            #
            # Original code attempted:
            # db = get_database()
            # modules = db.modules.get_by_project_id(project.id)  # AttributeError: no 'modules'
            # team_members = getattr(project, 'team_members', [])
            # team_size = len(team_members)
            #
            # Conflict logic would check:
            # - if team_size < 2 and len(modules) > 8: too few team members for scope
            #
            # To fix:
            # 1. Create ModuleRepository in src/database/repositories.py
            # 2. Add self.modules to DatabaseService
            # 3. Re-enable this conflict detection logic

            if self.logger:
                self.logger.warning(
                    "Resource conflict detection disabled - ModuleRepository not yet implemented. "
                    "See TODO in _detect_resource_conflicts method."
                )

            # Return empty conflicts until repositories are added
            return []

        except Exception as e:
            if self.logger:
                self.logger.error(f"Resource conflict detection failed: {e}")
            return []

    def _save_conflicts_to_db(self, project_id: str, session_id: str, conflict_data: Dict[str, Any]) -> List[str]:
        """
        Save detected conflicts to database

        Args:
            project_id: Project ID
            session_id: Session ID (optional)
            conflict_data: Dict with conflict categories (technology_conflicts, requirement_conflicts, etc.)

        Returns:
            List of created conflict IDs
        """
        if not self.conflict_repo:
            return []

        conflict_ids = []

        try:
            # Process each conflict type
            for conflict_type_key, conflicts_list in conflict_data.items():
                if not isinstance(conflicts_list, list):
                    continue

                for conflict_dict in conflicts_list:
                    # Create Conflict model from dict
                    conflict = Conflict(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        session_id=session_id if session_id else "",
                        conflict_type=self._map_conflict_type(conflict_dict.get('type', 'technical')),
                        description=conflict_dict.get('message', conflict_dict.get('description', '')),
                        severity=conflict_dict.get('severity', 'medium'),
                        first_requirement=conflict_dict.get('first_requirement', conflict_dict.get('source1', '')),
                        second_requirement=conflict_dict.get('second_requirement', conflict_dict.get('source2', '')),
                        conflicting_roles=[],
                        is_resolved=False,
                        resolution_strategy='',
                        resolution_notes='',
                        resolved_by=None,
                        resolved_at=None,
                        affected_modules=[],
                        estimated_impact_hours=None,
                        created_at=DateTimeHelper.now(),
                        updated_at=DateTimeHelper.now()
                    )

                    # Save to database
                    if self.conflict_repo.create(conflict):
                        conflict_ids.append(conflict.id)
                        if self.logger:
                            self.logger.info(f"Saved conflict {conflict.id} to database")
                    else:
                        if self.logger:
                            self.logger.warning(f"Failed to save conflict to database")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving conflicts to database: {e}")

        return conflict_ids

    @require_project_access
    @log_agent_action
    def _get_conflicts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get conflicts for a project"""
        project_id = data.get('project_id')
        unresolved_only = data.get('unresolved_only', False)

        if self.logger:
            self.logger.info(f"Retrieving conflicts for project {project_id}")

        try:
            if not self.conflict_repo:
                return self._error_response("Conflict repository not available")

            if unresolved_only:
                conflicts = self.conflict_repo.get_unresolved(project_id)
            else:
                conflicts = self.conflict_repo.get_by_project_id(project_id)

            # Convert to dicts for response
            conflicts_data = [self._conflict_to_dict(c) for c in conflicts]

            return self._success_response(
                f"Found {len(conflicts)} conflicts",
                {'conflicts': conflicts_data}
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error retrieving conflicts: {e}")
            return self._error_response(f"Failed to retrieve conflicts: {e}")

    def _conflict_to_dict(self, conflict: Conflict) -> Dict[str, Any]:
        """Convert Conflict model to dictionary"""
        return {
            'id': conflict.id,
            'project_id': conflict.project_id,
            'session_id': conflict.session_id,
            'conflict_type': conflict.conflict_type.value if hasattr(conflict.conflict_type, 'value') else str(
                conflict.conflict_type),
            'description': conflict.description,
            'severity': conflict.severity,
            'first_requirement': conflict.first_requirement,
            'second_requirement': conflict.second_requirement,
            'is_resolved': conflict.is_resolved,
            'resolution_notes': conflict.resolution_notes,
            'resolved_by': conflict.resolved_by,
            'resolved_at': DateTimeHelper.to_iso_string(conflict.resolved_at) if conflict.resolved_at else None,
            'affected_modules': conflict.affected_modules,
            'created_at': DateTimeHelper.to_iso_string(conflict.created_at),
            'updated_at': DateTimeHelper.to_iso_string(conflict.updated_at)
        }

    @require_project_access
    @log_agent_action
    def _resolve_conflict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mark a conflict as resolved"""
        conflict_id = data.get('conflict_id')
        resolution_notes = data.get('resolution_notes', '')
        resolved_by = data.get('resolved_by')

        if not conflict_id:
            return self._error_response("Conflict ID required")

        if self.logger:
            self.logger.info(f"Resolving conflict {conflict_id}")

        try:
            if not self.conflict_repo:
                return self._error_response("Conflict repository not available")

            success = self.conflict_repo.mark_resolved(conflict_id, resolution_notes, resolved_by)

            if success:
                return self._success_response("Conflict marked as resolved")
            else:
                return self._error_response("Failed to mark conflict as resolved")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error resolving conflict: {e}")
            return self._error_response(f"Failed to resolve conflict: {e}")

    def _map_conflict_type(self, conflict_type_str: str) -> ConflictType:
        """Map string conflict type to ConflictType enum"""
        type_mapping = {
            'technology_database': ConflictType.TECHNICAL,
            'technology_framework': ConflictType.TECHNICAL,
            'technical': ConflictType.TECHNICAL,
            'requirement_contradiction': ConflictType.BUSINESS,
            'requirement': ConflictType.BUSINESS,
            'timeline': ConflictType.TIMELINE,
            'resource': ConflictType.RESOURCE,
            'scope': ConflictType.SCOPE
        }
        return type_mapping.get(conflict_type_str, ConflictType.TECHNICAL)

    @require_project_access
    @log_agent_action
    def _assess_project_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall project health"""
        project_id = data.get('project_id')

        if self.logger:
            self.logger.info(f"Assessing project health for project {project_id}")

        try:
            from src.database import get_database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")
            project = db.projects.get_by_id(project_id)
            if not project:
                if self.logger:
                    self.logger.error(f"Project {project_id} not found")
                raise ValidationError("Project not found")

            return self._assess_project_health_internal(project)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Project health assessment failed: {e}")
            raise

    def _assess_project_health_internal(self, project: Project) -> Dict[str, Any]:
        """Internal project health assessment"""
        if self.logger:
            self.logger.debug(f"Assessing health for project {project.name}")

        try:
            health = {
                'score': 0,
                'status': 'unknown',
                'factors': [],
                'issues': [],
                'recommendations': []
            }

            # Calculate health score based on multiple factors
            score_factors = []

            # Requirements completeness
            requirements = getattr(project, 'requirements', [])
            if len(requirements) >= 3:
                score_factors.append(20)
                health['factors'].append('Requirements defined')
            else:
                health['issues'].append('Insufficient requirements')

            # Technology stack
            tech_stack = getattr(project, 'technology_stack', {})
            if tech_stack and len(tech_stack) > 0:
                score_factors.append(20)
                health['factors'].append('Technology stack defined')
            else:
                health['issues'].append('Technology stack not defined')

            # Team composition
            team_members = getattr(project, 'team_members', [])
            if len(team_members) >= 2:
                score_factors.append(20)
                health['factors'].append('Team assembled')
            else:
                health['issues'].append('Team composition needs attention')

            # Project description
            description = getattr(project, 'description', '')
            if description and len(description) > 20:
                score_factors.append(20)
                health['factors'].append('Clear project description')
            else:
                health['issues'].append('Project description incomplete')

            # Success criteria
            success_criteria = getattr(project, 'success_criteria', [])
            if success_criteria and len(success_criteria) > 0:
                score_factors.append(20)
                health['factors'].append('Success criteria defined')
            else:
                health['issues'].append('Success criteria not defined')

            # Calculate final score
            health['score'] = sum(score_factors)

            # Determine status
            if health['score'] >= 80:
                health['status'] = 'excellent'
            elif health['score'] >= 60:
                health['status'] = 'good'
            elif health['score'] >= 40:
                health['status'] = 'fair'
            else:
                health['status'] = 'needs_improvement'

            # Generate recommendations
            health['recommendations'] = self._generate_health_recommendations(health['issues'])

            if self.logger:
                self.logger.debug(f"Project health: {health['score']}/100 - {health['status']}")

            return health

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error assessing project health: {e}")
            return {
                'score': 0,
                'status': 'error',
                'factors': [],
                'issues': ['Error during assessment'],
                'recommendations': []
            }

    def _generate_health_recommendations(self, issues: List[str]) -> List[str]:
        """Generate health improvement recommendations"""
        if self.logger:
            self.logger.debug(f"Generating health recommendations for {len(issues)} issues")

        try:
            recommendations = []

            for issue in issues:
                if 'requirements' in issue.lower():
                    recommendations.append("Define detailed functional and non-functional requirements")
                elif 'technology' in issue.lower():
                    recommendations.append("Define comprehensive technology stack for clear implementation direction")
                elif 'team' in issue.lower():
                    recommendations.append("Consider expanding team or establishing collaboration processes")
                elif 'description' in issue.lower():
                    recommendations.append("Expand project description with goals, context, and objectives")
                elif 'success' in issue.lower():
                    recommendations.append("Define measurable success criteria and key performance indicators")

            if self.logger:
                self.logger.debug(f"Generated {len(recommendations)} health recommendations")

            return recommendations

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error generating health recommendations: {e}")
            return ["Error generating recommendations"]

    @require_project_access
    @log_agent_action
    def _generate_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights from project data"""
        project_id = data.get('project_id')
        focus_area = data.get('focus', 'all')

        if self.logger:
            self.logger.info(f"Generating insights for project {project_id}, focus: {focus_area}")

        try:
            from src.database import get_database
            db = get_database()
            if not db:
                return self._error_response("Database service not available", "DB_UNAVAILABLE")
            project = db.projects.get_by_id(project_id)
            if not project:
                if self.logger:
                    self.logger.error(f"Project {project_id} not found")
                raise ValidationError("Project not found")

            insights = {
                'project_id': project.id,
                'focus_area': focus_area,
                'generated_at': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'key_insights': self._extract_key_insights(project),
                'improvement_opportunities': self._identify_improvements(project),
                'success_indicators': self._identify_success_factors(project),
                'risk_mitigation': self._suggest_risk_mitigation(project)
            }

            if self.logger:
                insight_count = len(insights['key_insights'])
                self.logger.info(f"Generated {insight_count} key insights for project {project.name}")

            return insights

        except Exception as e:
            if self.logger:
                self.logger.error(f"Insight generation failed for project {project_id}: {e}")
            raise

    def _extract_key_insights(self, project: Project) -> List[Dict[str, Any]]:
        """Extract key insights about project"""
        if self.logger:
            self.logger.debug(f"Extracting key insights for project {project.name}")

        insights = []

        try:
            # Analyze project maturity
            requirements = getattr(project, 'requirements', [])
            if len(requirements) >= 5:
                insights.append({
                    'category': 'maturity',
                    'insight': 'Project has well-defined requirements indicating good planning',
                    'impact': 'positive'
                })

            # Analyze team structure
            team_members = getattr(project, 'team_members', [])
            if len(team_members) < 2:
                insights.append({
                    'category': 'resources',
                    'insight': 'Single-person team may face knowledge sharing and velocity challenges',
                    'impact': 'risk'
                })

            if self.logger:
                self.logger.debug(f"Extracted {len(insights)} key insights")

            return insights

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error extracting key insights: {e}")
            return []

    def _identify_improvements(self, project: Project) -> List[str]:
        """Identify improvement opportunities"""
        if self.logger:
            self.logger.debug(f"Identifying improvements for project {project.name}")

        improvements = []

        try:
            # Check for missing success criteria
            success_criteria = getattr(project, 'success_criteria', [])
            if not success_criteria or len(success_criteria) == 0:
                improvements.append("Define measurable success criteria to track project outcomes")

            # Check for missing constraints
            constraints = getattr(project, 'constraints', [])
            if not constraints or len(constraints) < 2:
                improvements.append(
                    "Document project constraints including budget, timeline, and technical limitations")

            if self.logger:
                self.logger.debug(f"Identified {len(improvements)} improvement opportunities")

            return improvements

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error identifying improvements: {e}")
            return []

    def _identify_success_factors(self, project: Project) -> List[str]:
        """Identify factors contributing to project success"""
        if self.logger:
            self.logger.debug(f"Identifying success factors for project {project.name}")

        success_factors = []

        try:
            requirements = getattr(project, 'requirements', [])
            if len(requirements) >= 5:
                success_factors.append("Well-defined requirements provide clear project direction")

            team_members = getattr(project, 'team_members', [])
            if len(team_members) >= 3:
                success_factors.append("Good team size enables collaboration and knowledge sharing")

            tech_stack = getattr(project, 'technology_stack', {})
            if tech_stack and len(tech_stack) >= 3:
                success_factors.append("Defined technology stack provides clear implementation path")

            if self.logger:
                self.logger.debug(f"Identified {len(success_factors)} success factors")

            return success_factors

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error identifying success factors: {e}")
            return []

    def _suggest_risk_mitigation(self, project: Project) -> List[str]:
        """Suggest risk mitigation strategies"""
        if self.logger:
            self.logger.debug(f"Suggesting risk mitigation for project {project.name}")

        mitigations = []

        try:
            # Detect and mitigate conflicts
            conflicts = self._detect_all_conflicts(project)
            if conflicts['total_count'] > 0:
                mitigations.append("Address identified conflicts in requirements and technology choices")

            # Team-related risks
            team_members = getattr(project, 'team_members', [])
            if len(team_members) == 1:
                mitigations.append("Consider adding team members or establishing external review processes")

            # Scope-related risks
            requirements = getattr(project, 'requirements', [])
            if len(requirements) > 12:
                mitigations.append("Implement phased delivery approach to manage scope and reduce risk")

            if self.logger:
                self.logger.debug(f"Suggested {len(mitigations)} risk mitigation strategies")

            return mitigations

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error suggesting risk mitigation: {e}")
            return []

    def _generate_context_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comprehensive analysis"""
        if self.logger:
            self.logger.debug("Generating context recommendations from analysis")

        recommendations = []

        try:
            # Health-based recommendations
            health = analysis.get('project_health', {})
            if health.get('score', 100) < 70:
                recommendations.append(
                    "Focus on improving project health through better requirement definition and team coordination")

            # Conflict-based recommendations
            conflicts = analysis.get('conflict_analysis', {})
            if conflicts.get('total_count', 0) > 3:
                recommendations.append("Address identified conflicts before proceeding with implementation")

            # Conversation-based recommendations
            conversation = analysis.get('conversation_insights', {})
            engagement_score = conversation.get('user_engagement', {}).get('score', 0)
            if engagement_score < 60:
                recommendations.append("Encourage more detailed and engaged responses in project discussions")

            # Technical recommendations
            technical = analysis.get('technical_assessment', {})
            if technical.get('technical_completeness', 0) < 70:
                recommendations.append("Complete technical architecture and technology stack definitions")

            # Limit to top 5 recommendations
            final_recommendations = recommendations[:5]

            if self.logger:
                self.logger.debug(f"Generated {len(final_recommendations)} context recommendations")

            return final_recommendations

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error generating context recommendations: {e}")
            return []

    def _extract_risk_factors(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract risk factors from analysis"""
        if self.logger:
            self.logger.debug("Extracting risk factors from analysis")

        risks = []

        try:
            conflicts = analysis.get('conflict_analysis', {})
            if conflicts.get('severity') == 'high':
                risks.append("High-severity conflicts may impact project success")

            health = analysis.get('project_health', {})
            if health.get('score', 100) < 50:
                risks.append("Poor project health indicates fundamental issues")

            conversation = analysis.get('conversation_insights', {})
            if conversation.get('response_quality', {}).get('score', 0) < 40:
                risks.append("Low response quality may indicate unclear requirements")

            if self.logger:
                self.logger.debug(f"Extracted {len(risks)} risk factors")

            return risks

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error extracting risk factors: {e}")
            return []

    def _identify_project_strengths(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify project strengths from analysis"""
        if self.logger:
            self.logger.debug("Identifying project strengths from analysis")

        strengths = []

        try:
            health = analysis.get('project_health', {})
            if health.get('score', 0) > 80:
                strengths.append("Excellent project health with strong foundation")

            conversation = analysis.get('conversation_insights', {})
            if conversation.get('user_engagement', {}).get('score', 0) > 70:
                strengths.append("High user engagement indicates strong project commitment")

            conflicts = analysis.get('conflict_analysis', {})
            if conflicts.get('total_count', 0) == 0:
                strengths.append("No significant conflicts detected - clear project direction")

            if self.logger:
                self.logger.debug(f"Identified {len(strengths)} project strengths")

            return strengths

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error identifying project strengths: {e}")
            return []

    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check for ContextAnalyzerAgent"""
        health = super().health_check()

        try:
            # Check conflict rules
            health['conflict_rules'] = {
                'technology_conflicts': len(self.conflict_rules.get('technology_conflicts', {})),
                'requirement_conflicts': len(self.conflict_rules.get('requirement_conflicts', []))
            }

            # Check patterns
            health['patterns'] = {
                'loaded_patterns': len(self.patterns)
            }

        except Exception as e:
            health['status'] = 'degraded'
            health['error'] = f"Health check failed: {e}"

        return health


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = ['ContextAnalyzerAgent']

if __name__ == "__main__":
    print("ContextAnalyzerAgent module - use via AgentOrchestrator")
