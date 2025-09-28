#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Context Analysis Agent
=============================================

Enhanced context analysis agent with conflict detection.

Absorbs: ConflictDetectorAgent functionality
Capabilities: Pattern recognition, conflict resolution, intelligent insights
"""

import json
from typing import Dict, List, Any, Optional

from src.core import get_logger, DateTimeHelper, ValidationError
from src.models import (
    Project, ConversationMessage, UserRole, TechnicalRole,
    ProjectPhase, ModuleStatus, RiskLevel, ConversationStatus
)
from src.database import get_database
from .base import BaseAgent, require_project_access, log_agent_action


class ContextAnalyzerAgent(BaseAgent):
    """
    Enhanced context analysis agent with conflict detection

    Absorbs: ConflictDetectorAgent functionality
    Capabilities: Pattern recognition, conflict resolution, intelligent insights
    """

    def __init__(self):
        super().__init__("context_analyzer", "Context Analyzer")
        self.db_service = get_database()
        self.patterns = {}
        self.conflict_rules = self._load_conflict_rules()

        if self.logger:
            self.logger.info("ContextAnalyzerAgent initialized with conflict detection rules")

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

    @require_project_access
    @log_agent_action
    def _analyze_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive context analysis"""
        project_id = data.get('project_id')
        analysis_type = data.get('type', 'full')

        if self.logger:
            self.logger.info(f"Starting context analysis for project {project_id}, type: {analysis_type}")

        try:
            # Get project data
            project = self.db_service.projects.get_by_id(project_id)
            if not project:
                if self.logger:
                    self.logger.error(f"Project {project_id} not found")
                raise ValidationError("Project not found")

            # Perform analysis based on type
            if analysis_type == 'conversation':
                return self._analyze_conversation_patterns(project)
            elif analysis_type == 'technical':
                return self._analyze_technical_context(project)
            elif analysis_type == 'conflicts':
                return self._detect_all_conflicts(project)
            elif analysis_type == 'health':
                return self._assess_project_health_internal(project)
            else:
                return self._analyze_full_context(project)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Context analysis failed for project {project_id}: {e}")
            raise

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
            project = self.db_service.projects.get_by_id(project_id)
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
            # Get conversation data from Socratic sessions
            sessions = self.db_service.socratic_sessions.get_project_sessions(project.id)
            conversation_count = len(sessions)

            if self.logger:
                self.logger.debug(f"Found {conversation_count} Socratic sessions for project {project.name}")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not retrieve conversation data for project {project.name}: {e}")
            conversation_count = 0
            sessions = []

        patterns = {
            'total_interactions': conversation_count,
            'response_quality': self._assess_response_quality(sessions),
            'topic_coverage': self._analyze_topic_coverage(sessions),
            'user_engagement': self._measure_engagement(sessions),
            'information_gaps': self._identify_information_gaps(project),
            'conversation_flow': self._analyze_conversation_flow(sessions),
            'phase_distribution': self._analyze_phase_distribution(sessions)
        }

        if self.logger:
            quality_score = patterns['response_quality']['score']
            self.logger.info(
                f"Conversation analysis completed - Quality: {quality_score}, Interactions: {conversation_count}")

        return patterns

    def _assess_response_quality(self, sessions: List) -> Dict[str, Any]:
        """Assess quality of user responses"""
        if self.logger:
            self.logger.debug("Assessing response quality from sessions")

        if not sessions:
            if self.logger:
                self.logger.warning("No conversation data available for quality assessment")
            return {
                'score': 0,
                'analysis': 'No conversation data available',
                'total_responses': 0,
                'detailed_responses': 0
            }

        try:
            # Basic quality assessment based on session completion
            completed_sessions = sum(1 for session in sessions if hasattr(session, 'completion_percentage')
                                     and session.completion_percentage >= 80)

            total_sessions = len(sessions)
            quality_score = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0

            if self.logger:
                self.logger.debug(
                    f"Quality assessment: {completed_sessions}/{total_sessions} sessions completed (score: {quality_score:.1f})")

            return {
                'score': quality_score,
                'analysis': f'Quality based on session completion rate',
                'total_responses': total_sessions,
                'detailed_responses': completed_sessions
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error assessing response quality: {e}")
            return {
                'score': 0,
                'analysis': f'Error assessing quality: {str(e)}',
                'total_responses': 0,
                'detailed_responses': 0
            }

    def _analyze_topic_coverage(self, sessions: List) -> Dict[str, Any]:
        """Analyze topic coverage in conversations"""
        if self.logger:
            self.logger.debug("Analyzing topic coverage from sessions")

        if not sessions:
            if self.logger:
                self.logger.warning("No sessions available for topic coverage analysis")
            return {'coverage_score': 0, 'covered_topics': [], 'missing_topics': []}

        try:
            # Basic topic coverage based on roles covered in sessions
            covered_roles = set()
            for session in sessions:
                if hasattr(session, 'completed_roles'):
                    covered_roles.update(session.completed_roles)

            all_roles = list(TechnicalRole)
            coverage_score = (len(covered_roles) / len(all_roles) * 100) if all_roles else 0

            covered_topics = [role.value for role in covered_roles]
            missing_topics = [role.value for role in all_roles if role not in covered_roles]

            if self.logger:
                self.logger.debug(
                    f"Topic coverage: {len(covered_roles)}/{len(all_roles)} roles covered (score: {coverage_score:.1f})")

            return {
                'coverage_score': coverage_score,
                'covered_topics': covered_topics,
                'missing_topics': missing_topics
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error analyzing topic coverage: {e}")
            return {'coverage_score': 0, 'covered_topics': [], 'missing_topics': []}

    def _measure_engagement(self, sessions: List) -> Dict[str, Any]:
        """Measure user engagement levels"""
        if self.logger:
            self.logger.debug("Measuring user engagement from sessions")

        if not sessions:
            if self.logger:
                self.logger.warning("No sessions available for engagement measurement")
            return {'score': 0, 'engagement_level': 'none'}

        try:
            # Calculate engagement based on session activity
            active_sessions = sum(1 for session in sessions if hasattr(session, 'status')
                                  and session.status == ConversationStatus.ACTIVE)

            total_questions = sum(getattr(session, 'total_questions', 0) for session in sessions)
            answered_questions = sum(getattr(session, 'questions_answered', 0) for session in sessions)

            answer_rate = (answered_questions / total_questions * 100) if total_questions > 0 else 0
            engagement_level = 'high' if answer_rate > 70 else 'medium' if answer_rate > 40 else 'low'

            if self.logger:
                self.logger.debug(
                    f"Engagement: {answered_questions}/{total_questions} questions answered (rate: {answer_rate:.1f}%, level: {engagement_level})")

            return {
                'score': answer_rate,
                'engagement_level': engagement_level,
                'active_sessions': active_sessions,
                'total_questions': total_questions,
                'answered_questions': answered_questions
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error measuring engagement: {e}")
            return {'score': 0, 'engagement_level': 'error'}

    def _identify_information_gaps(self, project: Project) -> List[str]:
        """Identify information gaps in project data"""
        if self.logger:
            self.logger.debug(f"Identifying information gaps for project {project.name}")

        gaps = []

        try:
            # Check basic project information gaps
            if not project.description or len(project.description.strip()) < 10:
                gaps.append("Project description is missing or too brief")

            if not project.requirements or len(project.requirements) < 2:
                gaps.append("Insufficient requirements defined")

            if not project.technology_stack or len(project.technology_stack) == 0:
                gaps.append("Technology stack not defined")

            if not project.constraints or len(project.constraints) == 0:
                gaps.append("Project constraints not specified")

            if not project.success_criteria or len(project.success_criteria) == 0:
                gaps.append("Success criteria not defined")

            if not project.team_members or len(project.team_members) == 0:
                gaps.append("No team members assigned")

            if self.logger:
                self.logger.debug(f"Identified {len(gaps)} information gaps for project {project.name}")

            return gaps

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error identifying information gaps: {e}")
            return ["Error analyzing project information"]

    def _analyze_conversation_flow(self, sessions: List) -> Dict[str, Any]:
        """Analyze conversation flow patterns"""
        if self.logger:
            self.logger.debug("Analyzing conversation flow patterns")

        if not sessions:
            if self.logger:
                self.logger.warning("No sessions available for flow analysis")
            return {'flow_quality': 'poor', 'session_count': 0}

        try:
            session_count = len(sessions)
            avg_completion = sum(getattr(session, 'completion_percentage', 0) for session in
                                 sessions) / session_count if session_count > 0 else 0

            flow_quality = 'excellent' if avg_completion > 80 else 'good' if avg_completion > 60 else 'poor'

            if self.logger:
                self.logger.debug(
                    f"Flow analysis: {session_count} sessions, avg completion: {avg_completion:.1f}%, quality: {flow_quality}")

            return {
                'flow_quality': flow_quality,
                'session_count': session_count,
                'average_completion': avg_completion
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error analyzing conversation flow: {e}")
            return {'flow_quality': 'error', 'session_count': 0}

    def _analyze_phase_distribution(self, sessions: List) -> Dict[str, Any]:
        """Analyze distribution across project phases"""
        if self.logger:
            self.logger.debug("Analyzing phase distribution")

        phases = {}
        try:
            for session in sessions:
                # Assume sessions are in discovery phase if not specified
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
                'technology_stack': project.technology_stack,
                'deployment_target': 'not_specified',
                'language_preferences': [],
                'technical_completeness': 0.0
            }

            # Calculate technical completeness score
            completeness_factors = [
                len(project.technology_stack) > 0,
                len(project.constraints) > 0,
                len(project.requirements) > 2,
                bool(project.description and len(project.description) > 20),
                len(project.success_criteria) > 0
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

        if self.logger:
            self.logger.info(f"Starting conflict detection for project {project_id}")

        try:
            project = self.db_service.projects.get_by_id(project_id)
            if not project:
                if self.logger:
                    self.logger.error(f"Project {project_id} not found")
                raise ValidationError("Project not found")

            return self._detect_all_conflicts(project)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Conflict detection failed for project {project_id}: {e}")
            raise

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
            tech_stack = project.technology_stack

            if not tech_stack:
                if self.logger:
                    self.logger.debug("No technology stack defined, skipping technology conflict detection")
                return conflicts

            # Check for database conflicts
            database = tech_stack.get('database', '').lower()
            if database and database in self.conflict_rules['technology_conflicts']['database']:
                conflicting_reqs = self.conflict_rules['technology_conflicts']['database'][database]
                for req in project.requirements:
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
                for req in project.requirements:
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
            requirements = [req.lower() for req in project.requirements]

            # Check for known conflicting requirement pairs using instance rules
            for req1, req2 in self.conflict_rules['requirement_conflicts']:
                req1_present = any(req1 in req for req in requirements)
                req2_present = any(req2 in req for req in requirements)

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
        """Detect timeline-related conflicts"""
        if self.logger:
            self.logger.debug(f"Detecting timeline conflicts for project {project.name}")

        conflicts = []

        try:
            modules = self.db_service.modules.get_project_modules(project.id)

            if not modules:
                if self.logger:
                    self.logger.debug("No modules found, skipping timeline conflict detection")
                return conflicts

            total_estimated_hours = sum(
                getattr(m, 'estimated_hours', 0) for m in modules if hasattr(m, 'estimated_hours'))
            active_modules = len([m for m in modules if hasattr(m, 'status') and
                                  getattr(m, 'status', None) not in [ModuleStatus.COMPLETED, ModuleStatus.NOT_STARTED]])

            # Check for unrealistic timelines
            if total_estimated_hours > 2000:  # More than 50 work weeks for one person
                conflict = {
                    'type': 'timeline_unrealistic',
                    'estimated_hours': total_estimated_hours,
                    'message': f'Total estimated hours ({total_estimated_hours}) may be unrealistic for timeline',
                    'severity': 'high',
                    'suggestion': 'Consider breaking into phases or adding team members'
                }
                conflicts.append(conflict)

                if self.logger:
                    self.logger.warning(f"Unrealistic timeline detected: {total_estimated_hours} hours")

            # Check for too many concurrent modules
            if active_modules > 5:
                conflict = {
                    'type': 'concurrent_complexity',
                    'active_modules': active_modules,
                    'message': f'Too many concurrent modules ({active_modules}) may impact focus and quality',
                    'severity': 'medium',
                    'suggestion': 'Focus on completing modules sequentially or in smaller groups'
                }
                conflicts.append(conflict)

                if self.logger:
                    self.logger.warning(f"Too many concurrent modules: {active_modules}")

            if self.logger:
                self.logger.debug(f"Timeline conflict detection completed: {len(conflicts)} conflicts found")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Timeline conflict detection failed: {e}")

        return conflicts

    def _detect_resource_conflicts(self, project: Project) -> List[Dict[str, Any]]:
        """Detect resource allocation conflicts"""
        if self.logger:
            self.logger.debug(f"Detecting resource conflicts for project {project.name}")

        conflicts = []

        try:
            team_size = len(project.team_members) if project.team_members else 0
            modules = self.db_service.modules.get_project_modules(project.id)

            # Check team capacity vs project complexity
            if team_size < 2 and len(modules) > 8:
                conflict = {
                    'type': 'team_capacity',
                    'team_size': team_size,
                    'module_count': len(modules),
                    'message': f'Small team relative to project scope',
                    'severity': 'medium',
                    'suggestion': 'Consider adding team members or reducing initial scope'
                }
                conflicts.append(conflict)

                if self.logger:
                    self.logger.warning(f"Team capacity conflict: {team_size} team members for {len(modules)} modules")

            if self.logger:
                self.logger.debug(f"Resource conflict detection completed: {len(conflicts)} conflicts found")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Resource conflict detection failed: {e}")

        return conflicts

    @require_project_access
    @log_agent_action
    def _assess_project_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall project health"""
        project_id = data.get('project_id')

        if self.logger:
            self.logger.info(f"Assessing project health for project {project_id}")

        try:
            project = self.db_service.projects.get_by_id(project_id)
            if not project:
                if self.logger:
                    self.logger.error(f"Project {project_id} not found")
                raise ValidationError("Project not found")

            return self._assess_project_health_internal(project)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Project health assessment failed for project {project_id}: {e}")
            raise

    def _assess_project_health_internal(self, project: Project) -> Dict[str, Any]:
        """Internal project health assessment"""
        if self.logger:
            self.logger.debug(f"Assessing project health for {project.name}")

        try:
            health_score = 100
            issues = []
            strengths = []

            # Check conversation activity (using sessions instead of conversation_history)
            try:
                sessions = self.db_service.socratic_sessions.get_project_sessions(project.id)
                session_count = len(sessions)

                if self.logger:
                    self.logger.debug(f"Found {session_count} Socratic sessions for health assessment")

            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Could not retrieve sessions for health assessment: {e}")
                session_count = 0

            if session_count < 1:
                health_score -= 25
                issues.append("No Socratic sessions started - insufficient requirements gathering")
            elif session_count < 3:
                health_score -= 10
                issues.append("Limited Socratic sessions - may need more detailed discussions")
            else:
                strengths.append("Good engagement with multiple Socratic questioning sessions")

            # Check requirements definition
            req_count = len(project.requirements) if project.requirements else 0
            if req_count < 2:
                health_score -= 20
                issues.append("Insufficient requirements - project scope unclear")
            elif req_count < 5:
                health_score -= 10
                issues.append("Limited requirements - consider more detailed specifications")
            else:
                strengths.append("Well-defined requirements with clear project scope")

            # Check technology stack definition
            tech_count = len(project.technology_stack) if project.technology_stack else 0
            if tech_count == 0:
                health_score -= 15
                issues.append("Technology stack not defined - implementation approach unclear")
            elif tech_count < 3:
                health_score -= 8
                issues.append("Technology stack partially defined - consider more specific choices")
            else:
                strengths.append("Technology stack well-defined with clear technical direction")

            # Check team collaboration
            team_size = len(project.team_members) if project.team_members else 0
            if team_size == 1:
                health_score -= 5
                issues.append("Single-person project - consider collaboration or external review")
            else:
                strengths.append("Team collaboration enabled with multiple members")

            # Ensure health score doesn't go below 0
            health_score = max(0, health_score)

            health_result = {
                'score': health_score,
                'status': 'excellent' if health_score > 80 else 'good' if health_score > 60 else 'needs_attention',
                'issues': issues,
                'strengths': strengths,
                'recommendations': self._generate_health_recommendations(health_score, issues)
            }

            if self.logger:
                self.logger.info(
                    f"Project health assessment completed for {project.name}: {health_score}/100 ({health_result['status']})")

            return health_result

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error assessing project health: {e}")
            raise

    def _generate_health_recommendations(self, score: int, issues: List[str]) -> List[str]:
        """Generate recommendations based on health score and issues"""
        if self.logger:
            self.logger.debug(f"Generating health recommendations for score {score}")

        recommendations = []

        try:
            if score < 50:
                recommendations.append("Project health is concerning - address fundamental issues before proceeding")
            elif score < 70:
                recommendations.append("Project health needs improvement - focus on addressing identified issues")

            # Generate specific recommendations based on issues
            for issue in issues[:3]:  # Top 3 issues
                if "requirements" in issue.lower():
                    recommendations.append(
                        "Conduct additional Socratic questioning sessions to gather more requirements")
                elif "technology" in issue.lower():
                    recommendations.append("Define comprehensive technology stack for clear implementation direction")
                elif "team" in issue.lower():
                    recommendations.append("Consider expanding team or establishing collaboration processes")

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
            project = self.db_service.projects.get_by_id(project_id)
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
            # Analyze project complexity
            complexity_score = self._calculate_project_complexity(project)
            if complexity_score > 75:
                insight = {
                    'category': 'complexity',
                    'message': 'High project complexity detected',
                    'impact': 'May increase development time and require experienced team',
                    'recommendation': 'Consider phased approach and ensure adequate technical leadership'
                }
                insights.append(insight)

                if self.logger:
                    self.logger.info(f"High complexity insight added: score {complexity_score}")

            # Analyze scope
            req_count = len(project.requirements) if project.requirements else 0
            if req_count > 15:
                insight = {
                    'category': 'scope',
                    'message': 'Large number of requirements detected',
                    'impact': 'May increase complexity and development time significantly',
                    'recommendation': 'Consider prioritizing requirements and implementing MVP first'
                }
                insights.append(insight)

                if self.logger:
                    self.logger.info(f"Large scope insight added: {req_count} requirements")

            # Analyze team readiness
            team_size = len(project.team_members) if project.team_members else 0
            if team_size < 3 and req_count > 8:
                insight = {
                    'category': 'team',
                    'message': 'Small team relative to project scope',
                    'impact': 'May lead to bottlenecks and longer development cycles',
                    'recommendation': 'Consider adding team members or reducing initial scope'
                }
                insights.append(insight)

                if self.logger:
                    self.logger.info(f"Team capacity insight added: {team_size} members for {req_count} requirements")

            # Technology alignment insight
            tech_count = len(project.technology_stack) if project.technology_stack else 0
            if tech_count < 3:
                insight = {
                    'category': 'technology',
                    'message': 'Limited technology stack defined',
                    'impact': 'May lead to technical decisions being made ad-hoc during development',
                    'recommendation': 'Define comprehensive technology stack including database, backend, and frontend choices'
                }
                insights.append(insight)

                if self.logger:
                    self.logger.info(f"Technology insight added: only {tech_count} technologies defined")

            if self.logger:
                self.logger.debug(f"Extracted {len(insights)} key insights")

            return insights

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error extracting key insights: {e}")
            return []

    def _calculate_project_complexity(self, project: Project) -> float:
        """Calculate a project complexity score"""
        if self.logger:
            self.logger.debug(f"Calculating complexity score for project {project.name}")

        try:
            complexity = 0

            # Requirements complexity
            req_count = len(project.requirements) if project.requirements else 0
            complexity += min(req_count * 3, 30)

            # Technology complexity
            tech_count = len(project.technology_stack) if project.technology_stack else 0
            complexity += tech_count * 2

            # Team complexity
            team_count = len(project.team_members) if project.team_members else 0
            complexity += team_count * 1

            # Constraint complexity
            constraint_count = len(project.constraints) if project.constraints else 0
            complexity += constraint_count * 2

            final_score = min(complexity, 100)

            if self.logger:
                self.logger.debug(
                    f"Complexity calculation: req({req_count}*3) + tech({tech_count}*2) + team({team_count}*1) + constraints({constraint_count}*2) = {final_score}")

            return final_score

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating project complexity: {e}")
            return 0.0

    def _identify_improvements(self, project: Project) -> List[str]:
        """Identify improvement opportunities"""
        if self.logger:
            self.logger.debug(f"Identifying improvements for project {project.name}")

        improvements = []

        try:
            # Check technical completeness
            tech_analysis = self._analyze_technical_context(project)
            if tech_analysis['technical_completeness'] < 80:
                improvements.append("Complete technical specifications including architecture and deployment details")

            # Check for missing constraints
            constraint_count = len(project.constraints) if project.constraints else 0
            if constraint_count < 2:
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
            req_count = len(project.requirements) if project.requirements else 0
            if req_count >= 5:
                success_factors.append("Well-defined requirements provide clear project direction")

            team_count = len(project.team_members) if project.team_members else 0
            if team_count >= 3:
                success_factors.append("Good team size enables collaboration and knowledge sharing")

            tech_count = len(project.technology_stack) if project.technology_stack else 0
            if tech_count >= 3:
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
            team_size = len(project.team_members) if project.team_members else 0
            if team_size == 1:
                mitigations.append("Consider adding team members or establishing external review processes")

            # Scope-related risks
            req_count = len(project.requirements) if project.requirements else 0
            if req_count > 12:
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
