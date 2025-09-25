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
    Project, ConversationMessage, UserRole,
    ProjectPhase, ModuleStatus, RiskLevel
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
        self.patterns = {}
        self.conflict_rules = self._load_conflict_rules()

    def get_capabilities(self) -> List[str]:
        return [
            "analyze_context", "detect_conflicts", "generate_insights",
            "pattern_recognition", "suggest_improvements", "risk_assessment",
            "technology_compatibility", "recommendation_engine", "analyze_conversation",
            "assess_project_health", "detect_requirement_conflicts"
        ]

    def _load_conflict_rules(self) -> Dict[str, Any]:
        """Load conflict detection rules"""
        return {
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

    @require_project_access
    @log_agent_action
    def _analyze_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive context analysis"""
        project_id = data.get('project_id')
        analysis_type = data.get('type', 'full')

        # Get project data
        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValidationError("Project not found")

        # Perform analysis based on type
        if analysis_type == 'conversation':
            return self._analyze_conversation_patterns(project)
        elif analysis_type == 'technical':
            return self._analyze_technical_context(project)
        elif analysis_type == 'conflicts':
            return self._detect_all_conflicts(project)
        elif analysis_type == 'health':
            return self._assess_project_health(project)
        else:
            return self._analyze_full_context(project)

    def _analyze_full_context(self, project: Project) -> Dict[str, Any]:
        """Full context analysis including all aspects"""
        analysis = {
            'project_id': project.project_id,
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

        return analysis

    @require_project_access
    @log_agent_action
    def _analyze_conversation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation patterns and user behavior"""
        project_id = data.get('project_id')

        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValidationError("Project not found")

        return self._analyze_conversation_patterns(project)

    def _analyze_conversation_patterns(self, project: Project) -> Dict[str, Any]:
        """Analyze conversation patterns and user behavior"""
        conversation_data = project.conversation_history or []

        patterns = {
            'total_interactions': len(conversation_data),
            'response_quality': self._assess_response_quality(conversation_data),
            'topic_coverage': self._analyze_topic_coverage(conversation_data),
            'user_engagement': self._measure_engagement(conversation_data),
            'information_gaps': self._identify_information_gaps(conversation_data),
            'conversation_flow': self._analyze_conversation_flow(conversation_data),
            'phase_distribution': self._analyze_phase_distribution(conversation_data)
        }

        return patterns

    def _assess_response_quality(self, conversation_data: List[ConversationMessage]) -> Dict[str, Any]:
        """Assess quality of user responses"""
        if not conversation_data:
            return {
                'score': 0,
                'analysis': 'No conversation data',
                'total_responses': 0,
                'detailed_responses': 0
            }

        # Filter user responses
        user_responses = [msg for msg in conversation_data if msg.type == 'user']

        if not user_responses:
            return {
                'score': 0,
                'analysis': 'No user responses found',
                'total_responses': 0,
                'detailed_responses': 0
            }

        # Assess response quality based on length and content
        detailed_responses = 0
        total_length = 0

        for response in user_responses:
            response_length = len(response.content)
            total_length += response_length

            # Consider detailed if response is substantial and has specific information
            if response_length > 50 and any(
                    keyword in response.content.lower()
                    for keyword in ['because', 'need', 'require', 'should', 'want', 'will', 'plan']
            ):
                detailed_responses += 1

        avg_length = total_length / len(user_responses) if user_responses else 0
        quality_score = min(100.0, (detailed_responses / len(user_responses)) * 100)

        return {
            'score': round(quality_score, 1),
            'total_responses': len(user_responses),
            'detailed_responses': detailed_responses,
            'average_length': round(avg_length, 1),
            'analysis': self._get_quality_analysis(quality_score)
        }

    def _get_quality_analysis(self, score: float) -> str:
        """Get textual analysis of response quality"""
        if score >= 80:
            return "Excellent response quality with detailed, thoughtful answers"
        elif score >= 60:
            return "Good response quality with adequate detail"
        elif score >= 40:
            return "Moderate response quality, could use more detail"
        elif score >= 20:
            return "Limited response quality, needs more specific information"
        else:
            return "Poor response quality, responses are too brief or vague"

    def _analyze_topic_coverage(self, conversation_data: List[ConversationMessage]) -> Dict[str, Any]:
        """Analyze topic coverage in conversation"""
        topics = {
            'requirements': 0,
            'technical': 0,
            'design': 0,
            'business': 0,
            'testing': 0,
            'deployment': 0
        }

        topic_keywords = {
            'requirements': ['require', 'need', 'must', 'should', 'feature', 'functionality'],
            'technical': ['api', 'database', 'framework', 'technology', 'code', 'algorithm'],
            'design': ['user', 'interface', 'design', 'experience', 'ui', 'ux', 'layout'],
            'business': ['business', 'revenue', 'customer', 'market', 'profit', 'cost'],
            'testing': ['test', 'quality', 'validation', 'verify', 'check', 'qa'],
            'deployment': ['deploy', 'production', 'server', 'hosting', 'launch', 'live']
        }

        for message in conversation_data:
            content_lower = message.content.lower()

            for topic, keywords in topic_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    topics[topic] += 1

        # Calculate coverage percentage
        total_messages = len(conversation_data)
        topic_coverage = {}

        for topic, count in topics.items():
            coverage_pct = (count / total_messages * 100) if total_messages > 0 else 0
            topic_coverage[topic] = {
                'count': count,
                'coverage_percentage': round(coverage_pct, 1)
            }

        return topic_coverage

    def _measure_engagement(self, conversation_data: List[ConversationMessage]) -> Dict[str, Any]:
        """Measure user engagement levels"""
        if not conversation_data:
            return {'score': 0, 'trend': 'none', 'message_count': 0}

        user_messages = [msg for msg in conversation_data if msg.type == 'user']

        if len(user_messages) < 2:
            return {
                'score': 50 if user_messages else 0,
                'trend': 'insufficient_data',
                'message_count': len(user_messages)
            }

        # Calculate engagement based on multiple factors
        total_length = sum(len(msg.content) for msg in user_messages)
        avg_length = total_length / len(user_messages)

        # Engagement factors
        length_score = min(100.0, (avg_length / 100) * 100)  # Normalize to 100
        frequency_score = min(100.0, len(user_messages) * 10)  # More messages = higher engagement

        # Look for engagement indicators
        engagement_indicators = 0
        for msg in user_messages:
            content = msg.content.lower()
            if any(indicator in content for indicator in [
                'question', '?', 'how', 'what', 'why', 'when', 'where',
                'interested', 'important', 'priority', 'concern'
            ]):
                engagement_indicators += 1

        indicator_score = min(100.0, (engagement_indicators / len(user_messages)) * 100)

        # Overall engagement score
        engagement_score = (length_score + frequency_score + indicator_score) / 3

        # Determine trend
        if len(user_messages) >= 3:
            recent_avg = sum(len(msg.content) for msg in user_messages[-3:]) / 3
            earlier_avg = sum(len(msg.content) for msg in user_messages[:-3]) / max(1, len(user_messages) - 3)

            if recent_avg > earlier_avg * 1.2:
                trend = 'increasing'
            elif recent_avg < earlier_avg * 0.8:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'

        return {
            'score': round(engagement_score, 1),
            'trend': trend,
            'message_count': len(user_messages),
            'avg_message_length': round(avg_length, 1),
            'engagement_indicators': engagement_indicators
        }

    def _identify_information_gaps(self, conversation_data: List[ConversationMessage]) -> List[str]:
        """Identify information gaps that need addressing"""
        gaps = []

        # Analyze topic coverage
        topic_coverage = self._analyze_topic_coverage(conversation_data)

        # Check for insufficient coverage in key areas
        if topic_coverage['requirements']['count'] < 3:
            gaps.append("Insufficient requirements gathering - need more detailed feature specifications")

        if topic_coverage['technical']['count'] < 2:
            gaps.append("Limited technical discussion - architecture and technology choices need clarification")

        if topic_coverage['design']['count'] < 1:
            gaps.append("No design considerations mentioned - user experience needs attention")

        if topic_coverage['testing']['count'] == 0:
            gaps.append("Testing strategy not discussed - quality assurance approach missing")

        if topic_coverage['deployment']['count'] == 0:
            gaps.append("Deployment planning not addressed - production environment needs consideration")

        # Check for business context
        if topic_coverage['business']['count'] == 0:
            gaps.append("Business context missing - stakeholder needs and success criteria unclear")

        return gaps

    def _analyze_conversation_flow(self, conversation_data: List[ConversationMessage]) -> Dict[str, Any]:
        """Analyze the flow and progression of conversation"""
        if not conversation_data:
            return {'flow_quality': 'none', 'progression': 'none'}

        # Analyze phase progression
        phases_seen = set()
        phase_transitions = []

        current_phase = None
        for msg in conversation_data:
            if hasattr(msg, 'phase') and msg.phase:
                if msg.phase != current_phase:
                    phase_transitions.append(msg.phase)
                    current_phase = msg.phase
                phases_seen.add(msg.phase)

        # Assess flow quality
        expected_flow = [ProjectPhase.DISCOVERY, ProjectPhase.ANALYSIS, ProjectPhase.DESIGN,
                         ProjectPhase.IMPLEMENTATION]
        flow_score = 0

        if len(phases_seen) > 1:
            # Check if phases follow logical order
            for i, phase in enumerate(phase_transitions[:-1]):
                next_phase = phase_transitions[i + 1]
                if expected_flow.index(next_phase) > expected_flow.index(phase):
                    flow_score += 1

            flow_score = (flow_score / max(1, len(phase_transitions) - 1)) * 100

        return {
            'phases_covered': len(phases_seen),
            'phase_transitions': [p.value for p in phase_transitions] if phase_transitions else [],
            'flow_quality': 'good' if flow_score > 70 else 'moderate' if flow_score > 40 else 'poor',
            'flow_score': round(flow_score, 1)
        }

    def _analyze_phase_distribution(self, conversation_data: List[ConversationMessage]) -> Dict[str, int]:
        """Analyze distribution of messages across project phases"""
        phase_counts = {phase.value: 0 for phase in ProjectPhase}

        for msg in conversation_data:
            if hasattr(msg, 'phase') and msg.phase:
                phase_counts[msg.phase.value] += 1
            else:
                phase_counts[ProjectPhase.DISCOVERY.value] += 1  # Default to discovery

        return phase_counts

    def _analyze_technical_context(self, project: Project) -> Dict[str, Any]:
        """Analyze technical aspects of the project"""
        tech_analysis = {
            'tech_stack_defined': len(project.tech_stack) > 0,
            'tech_stack_count': len(project.tech_stack),
            'tech_stack': project.tech_stack,
            'architecture_defined': bool(project.architecture_pattern),
            'architecture_pattern': project.architecture_pattern,
            'deployment_target': project.deployment_target,
            'language_preferences': project.language_preferences,
            'technical_completeness': 0.0
        }

        # Calculate technical completeness score
        completeness_factors = [
            len(project.tech_stack) > 0,  # Has technology choices
            bool(project.architecture_pattern),  # Has architecture pattern
            len(project.language_preferences) > 0,  # Has language preferences
            bool(project.deployment_target and project.deployment_target != 'local'),  # Has deployment target
            len(project.constraints) > 0  # Has technical constraints
        ]

        tech_analysis['technical_completeness'] = (sum(completeness_factors) / len(completeness_factors)) * 100

        return tech_analysis

    @require_project_access
    @log_agent_action
    def _detect_conflicts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect all types of conflicts in project"""
        project_id = data.get('project_id')

        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValidationError("Project not found")

        return self._detect_all_conflicts(project)

    def _detect_all_conflicts(self, project: Project) -> Dict[str, Any]:
        """Detect all types of conflicts in project"""
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
            'high_severity_count': high_severity,
            'medium_severity_count': medium_severity,
            'summary': self._generate_conflict_summary(all_conflicts)
        })

        return conflicts

    def _detect_technology_conflicts(self, project: Project) -> List[Dict[str, Any]]:
        """Detect conflicts in technology choices"""
        conflicts = []
        tech_stack = [tech.lower() for tech in project.tech_stack]
        requirements = [req.lower() for req in project.requirements]

        # Check database conflicts
        database_conflicts = self.conflict_rules['technology_conflicts']['database']
        for db_tech, problematic_reqs in database_conflicts.items():
            if db_tech in tech_stack:
                for req_pattern in problematic_reqs:
                    if any(req_pattern in req for req in requirements):
                        conflicts.append({
                            'type': 'database_compatibility',
                            'technology': db_tech,
                            'conflict_with': req_pattern,
                            'message': f'{db_tech.title()} may not handle {req_pattern.replace("_", " ")} well',
                            'severity': 'medium',
                            'suggestion': self._get_database_alternative(db_tech, req_pattern)
                        })

        # Check framework conflicts
        framework_conflicts = self.conflict_rules['technology_conflicts']['frameworks']
        for framework, problematic_reqs in framework_conflicts.items():
            if framework in tech_stack:
                for req_pattern in problematic_reqs:
                    if any(req_pattern in req for req in requirements):
                        conflicts.append({
                            'type': 'framework_limitation',
                            'technology': framework,
                            'conflict_with': req_pattern,
                            'message': f'{framework.title()} may require additional setup for {req_pattern.replace("_", " ")}',
                            'severity': 'low',
                            'suggestion': self._get_framework_alternative(framework, req_pattern)
                        })

        return conflicts

    def _get_database_alternative(self, current_db: str, requirement: str) -> str:
        """Get database alternative suggestion"""
        alternatives = {
            'sqlite': {
                'high_concurrency': 'Consider PostgreSQL or MySQL for high concurrency',
                'large_datasets': 'Consider PostgreSQL for large datasets',
                'concurrent_users': 'Consider PostgreSQL or MySQL for multiple concurrent users'
            },
            'mysql': {
                'simple_deployment': 'Consider SQLite for simple single-user deployment',
                'serverless': 'Consider SQLite or managed database service'
            },
            'postgresql': {
                'simple_setup': 'Consider SQLite for simpler setup requirements',
                'minimal_features': 'Consider SQLite if full PostgreSQL features not needed'
            }
        }

        return alternatives.get(current_db, {}).get(requirement, f'Consider alternatives to {current_db}')

    def _get_framework_alternative(self, current_framework: str, requirement: str) -> str:
        """Get framework alternative suggestion"""
        alternatives = {
            'flask': {
                'complex_orm': 'Consider Django with built-in ORM',
                'enterprise_features': 'Consider Django for enterprise features',
                'admin_panel': 'Consider Django with built-in admin'
            },
            'django': {
                'microservices': 'Consider Flask or FastAPI for microservices',
                'simple_api': 'Consider Flask or FastAPI for simple APIs'
            },
            'fastapi': {
                'traditional_templates': 'Consider Django or Flask with templates',
                'complex_forms': 'Consider Django for complex form handling'
            }
        }

        return alternatives.get(current_framework, {}).get(requirement, f'Consider alternatives to {current_framework}')

    def _detect_requirement_conflicts(self, project: Project) -> List[Dict[str, Any]]:
        """Detect conflicting requirements"""
        conflicts = []
        requirements = [req.lower() for req in project.requirements]

        # Check for conflicting requirement pairs
        for req1, req2 in self.conflict_rules['requirement_conflicts']:
            req1_present = any(req1.replace('_', ' ') in req for req in requirements)
            req2_present = any(req2.replace('_', ' ') in req for req in requirements)

            if req1_present and req2_present:
                conflicts.append({
                    'type': 'requirement_conflict',
                    'conflicting_requirements': [req1.replace('_', ' '), req2.replace('_', ' ')],
                    'message': f'Potential conflict between {req1.replace("_", " ")} and {req2.replace("_", " ")}',
                    'severity': 'medium',
                    'suggestion': f'Prioritize either {req1.replace("_", " ")} or {req2.replace("_", " ")}, or find a balanced approach'
                })

        return conflicts

    def _detect_timeline_conflicts(self, project: Project) -> List[Dict[str, Any]]:
        """Detect timeline-related conflicts"""
        conflicts = []

        try:
            modules = self.db.modules.get_project_modules(project.project_id)

            if not modules:
                return conflicts

            total_estimated_hours = sum(m.estimated_hours for m in modules if m.estimated_hours)
            active_modules = len(
                [m for m in modules if m.status not in [ModuleStatus.COMPLETED, ModuleStatus.NOT_STARTED]])

            # Check for unrealistic timelines
            if total_estimated_hours > 2000:  # More than 50 work weeks for one person
                conflicts.append({
                    'type': 'timeline_unrealistic',
                    'estimated_hours': total_estimated_hours,
                    'message': f'Total estimated hours ({total_estimated_hours}) may be unrealistic for timeline',
                    'severity': 'high',
                    'suggestion': 'Consider breaking into phases or adding team members'
                })

            # Check for too many concurrent modules
            if active_modules > 5:
                conflicts.append({
                    'type': 'concurrent_complexity',
                    'active_modules': active_modules,
                    'message': f'Too many concurrent modules ({active_modules}) may impact focus and quality',
                    'severity': 'medium',
                    'suggestion': 'Focus on completing modules sequentially or in smaller groups'
                })

        except Exception as e:
            self.logger.error(f"Timeline conflict detection failed: {e}")

        return conflicts

    def _detect_resource_conflicts(self, project: Project) -> List[Dict[str, Any]]:
        """Detect resource allocation conflicts"""
        conflicts = []

        try:
            team_size = len(project.get_all_team_members())
            modules = self.db.modules.get_project_modules(project.project_id)

            # Check team capacity vs project complexity
            if team_size < 2 and len(modules) > 8:
                conflicts.append({
                    'type': 'team_capacity',
                    'team_size': team_size,
                    'module_count': len(modules),
                    'message': f'Small team size ({team_size}) relative to project complexity ({len(modules)} modules)',
                    'severity': 'high',
                    'suggestion': 'Consider adding team members or reducing project scope'
                })

            # Check role distribution
            role_distribution = {}
            for collaborator in project.collaborators:
                role = collaborator.role.value
                role_distribution[role] = role_distribution.get(role, 0) + 1

            # Check for missing critical roles
            if len(modules) > 3:
                if 'technical_lead' not in role_distribution:
                    conflicts.append({
                        'type': 'missing_role',
                        'missing_role': 'technical_lead',
                        'message': 'Complex project lacks technical leadership role',
                        'severity': 'medium',
                        'suggestion': 'Consider assigning a technical lead for architectural decisions'
                    })

                if 'qa_tester' not in role_distribution:
                    conflicts.append({
                        'type': 'missing_role',
                        'missing_role': 'qa_tester',
                        'message': 'Project lacks dedicated quality assurance role',
                        'severity': 'medium',
                        'suggestion': 'Consider adding QA role for quality assurance'
                    })

        except Exception as e:
            self.logger.error(f"Resource conflict detection failed: {e}")

        return conflicts

    def _generate_conflict_summary(self, all_conflicts: List[Dict[str, Any]]) -> str:
        """Generate a summary of all conflicts"""
        if not all_conflicts:
            return "No significant conflicts detected"

        high_count = sum(1 for c in all_conflicts if c.get('severity') == 'high')
        medium_count = sum(1 for c in all_conflicts if c.get('severity') == 'medium')
        low_count = len(all_conflicts) - high_count - medium_count

        summary_parts = []
        if high_count > 0:
            summary_parts.append(f"{high_count} high-severity conflict{'s' if high_count != 1 else ''}")
        if medium_count > 0:
            summary_parts.append(f"{medium_count} medium-severity conflict{'s' if medium_count != 1 else ''}")
        if low_count > 0:
            summary_parts.append(f"{low_count} low-severity conflict{'s' if low_count != 1 else ''}")

        return f"Found {', '.join(summary_parts)}. Review and address conflicts before proceeding."

    @require_project_access
    @log_agent_action
    def _assess_project_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall project health"""
        project_id = data.get('project_id')

        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValidationError("Project not found")

        return self._assess_project_health_internal(project)

    def _assess_project_health_internal(self, project: Project) -> Dict[str, Any]:
        """Internal project health assessment"""
        health_score = 100
        issues = []
        strengths = []

        # Check conversation activity
        conversation_count = len(project.conversation_history)
        if conversation_count < 3:
            health_score -= 25
            issues.append("Very limited conversation history - insufficient requirements gathering")
        elif conversation_count < 8:
            health_score -= 10
            issues.append("Limited conversation history - may need more detailed discussions")
        else:
            strengths.append("Good conversation engagement with substantial interaction history")

        # Check requirements definition
        req_count = len(project.requirements)
        if req_count < 2:
            health_score -= 20
            issues.append("Insufficient requirements - project scope unclear")
        elif req_count < 5:
            health_score -= 10
            issues.append("Limited requirements - consider more detailed specifications")
        else:
            strengths.append("Well-defined requirements with clear project scope")

        # Check technology stack definition
        tech_count = len(project.tech_stack)
        if tech_count == 0:
            health_score -= 15
            issues.append("Technology stack not defined - implementation approach unclear")
        elif tech_count < 3:
            health_score -= 8
            issues.append("Technology stack partially defined - consider more specific choices")
        else:
            strengths.append("Technology stack well-defined with clear technical direction")

        # Check team collaboration
        team_size = len(project.get_all_team_members())
        if team_size == 1:
            health_score -= 5
            issues.append("Single-person project - consider collaboration or external review")
        else:
            strengths.append(f"Good team collaboration with {team_size} team members")

        # Check constraints awareness
        if len(project.constraints) == 0:
            health_score -= 10
            issues.append("No constraints identified - potential for scope creep or unrealistic expectations")
        else:
            strengths.append("Project constraints clearly identified and documented")

        # Check progress and risk indicators
        if project.risk_level == RiskLevel.HIGH:
            health_score -= 15
            issues.append("High risk level identified - needs immediate attention")
        elif project.risk_level == RiskLevel.MEDIUM:
            health_score -= 8
            issues.append("Medium risk level - monitor closely")

        # Determine overall health level
        if health_score >= 90:
            health_level = 'excellent'
        elif health_score >= 75:
            health_level = 'good'
        elif health_score >= 60:
            health_level = 'fair'
        elif health_score >= 40:
            health_level = 'poor'
        else:
            health_level = 'critical'

        return {
            'score': max(0.0, health_score),
            'level': health_level,
            'issues': issues,
            'strengths': strengths,
            'recommendations': self._generate_health_recommendations(health_score, issues),
            'assessment_timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

    def _generate_health_recommendations(self, health_score: float, issues: List[str]) -> List[str]:
        """Generate recommendations based on health assessment"""
        recommendations = []

        if health_score < 60:
            recommendations.append("Project needs significant attention - consider project review meeting")

        if any("conversation" in issue.lower() for issue in issues):
            recommendations.append("Schedule more detailed requirements gathering sessions")

        if any("requirements" in issue.lower() for issue in issues):
            recommendations.append("Focus on defining clear, specific, and measurable requirements")

        if any("technology" in issue.lower() for issue in issues):
            recommendations.append("Define technology stack and architecture approach")

        if any("team" in issue.lower() for issue in issues):
            recommendations.append("Consider adding team members or establishing review processes")

        if not recommendations:
            recommendations.append("Project health is good - maintain current approach and monitor progress")

        return recommendations

    @require_project_access
    @log_agent_action
    def _generate_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights from project data"""
        project_id = data.get('project_id')
        focus_area = data.get('focus', 'all')

        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValidationError("Project not found")

        insights = {
            'project_id': project_id,
            'focus_area': focus_area,
            'generated_at': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
            'key_insights': self._extract_key_insights(project),
            'improvement_opportunities': self._identify_improvements(project),
            'success_indicators': self._identify_success_factors(project),
            'risk_mitigation': self._suggest_risk_mitigation(project)
        }

        return insights

    def _extract_key_insights(self, project: Project) -> List[Dict[str, Any]]:
        """Extract key insights about project"""
        insights = []

        # Analyze project complexity
        complexity_score = self._calculate_project_complexity(project)
        if complexity_score > 75:
            insights.append({
                'category': 'complexity',
                'message': 'High project complexity detected',
                'impact': 'May increase development time and require experienced team',
                'recommendation': 'Consider phased approach and ensure adequate technical leadership'
            })

        # Analyze scope
        if len(project.requirements) > 15:
            insights.append({
                'category': 'scope',
                'message': 'Large number of requirements detected',
                'impact': 'May increase complexity and development time significantly',
                'recommendation': 'Consider prioritizing requirements and implementing MVP first'
            })

        # Analyze team readiness
        team_size = len(project.get_all_team_members())
        if team_size < 3 and len(project.requirements) > 8:
            insights.append({
                'category': 'team',
                'message': 'Small team relative to project scope',
                'impact': 'May lead to bottlenecks and longer development cycles',
                'recommendation': 'Consider adding team members or reducing initial scope'
            })

        # Technology alignment insight
        if len(project.tech_stack) < 3:
            insights.append({
                'category': 'technology',
                'message': 'Limited technology stack defined',
                'impact': 'May lead to technical decisions being made ad-hoc during development',
                'recommendation': 'Define comprehensive technology stack including database, backend, and frontend choices'
            })

        return insights

    def _calculate_project_complexity(self, project: Project) -> float:
        """Calculate a project complexity score"""
        complexity = 0

        # Requirements complexity
        complexity += min(len(project.requirements) * 3, 30)

        # Technology complexity
        complexity += len(project.tech_stack) * 2

        # Team complexity
        complexity += len(project.get_all_team_members()) * 1

        # Constraint complexity
        complexity += len(project.constraints) * 2

        # Conversation complexity (more detailed conversations = more complex requirements)
        if project.conversation_history:
            avg_msg_length = sum(len(msg.content) for msg in project.conversation_history) / len(
                project.conversation_history)
            complexity += min(avg_msg_length / 10, 15.0)

        return min(complexity, 100.0)

    def _identify_improvements(self, project: Project) -> List[str]:
        """Identify improvement opportunities"""
        improvements = []

        # Check conversation quality
        if project.conversation_history:
            conv_analysis = self._analyze_conversation_patterns(project)
            if conv_analysis['response_quality']['score'] < 70:
                improvements.append("Improve response quality in conversations with more detailed and specific answers")

        # Check technical completeness
        tech_analysis = self._analyze_technical_context(project)
        if tech_analysis['technical_completeness'] < 80:
            improvements.append("Complete technical specifications including architecture and deployment details")

        # Check for missing constraints
        if len(project.constraints) < 2:
            improvements.append("Document project constraints including budget, timeline, and technical limitations")

        return improvements

    def _identify_success_factors(self, project: Project) -> List[str]:
        """Identify factors contributing to project success"""
        success_factors = []

        if len(project.requirements) >= 5:
            success_factors.append("Well-defined requirements provide clear project direction")

        if len(project.get_all_team_members()) >= 3:
            success_factors.append("Good team size enables collaboration and knowledge sharing")

        if len(project.tech_stack) >= 3:
            success_factors.append("Defined technology stack provides clear implementation path")

        if len(project.conversation_history) >= 10:
            success_factors.append("Extensive conversation history indicates thorough planning")

        return success_factors

    def _suggest_risk_mitigation(self, project: Project) -> List[str]:
        """Suggest risk mitigation strategies"""
        mitigations = []

        # Detect and mitigate conflicts
        conflicts = self._detect_all_conflicts(project)
        if conflicts['total_count'] > 0:
            mitigations.append("Address identified conflicts in requirements and technology choices")

        # Team-related risks
        team_size = len(project.get_all_team_members())
        if team_size == 1:
            mitigations.append("Consider adding team members or establishing external review processes")

        # Scope-related risks
        if len(project.requirements) > 12:
            mitigations.append("Implement phased delivery approach to manage scope and reduce risk")

        # Technical risks
        if not project.architecture_pattern:
            mitigations.append("Define architectural approach early to avoid technical debt")

        return mitigations

    def _generate_context_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comprehensive analysis"""
        recommendations = []

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

        return recommendations[:5]  # Return top 5 recommendations

    def _extract_risk_factors(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract risk factors from analysis"""
        risks = []

        conflicts = analysis.get('conflict_analysis', {})
        if conflicts.get('severity') == 'high':
            risks.append("High-severity conflicts may impact project success")

        health = analysis.get('project_health', {})
        if health.get('score', 100) < 50:
            risks.append("Poor project health indicates fundamental issues")

        conversation = analysis.get('conversation_insights', {})
        if conversation.get('response_quality', {}).get('score', 0) < 40:
            risks.append("Low response quality may indicate unclear requirements")

        return risks

    def _identify_project_strengths(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify project strengths from analysis"""
        strengths = []

        health = analysis.get('project_health', {})
        if health.get('score', 0) > 80:
            strengths.append("Excellent project health with strong foundation")

        conversation = analysis.get('conversation_insights', {})
        if conversation.get('user_engagement', {}).get('score', 0) > 70:
            strengths.append("High user engagement indicates strong project commitment")

        conflicts = analysis.get('conflict_analysis', {})
        if conflicts.get('total_count', 0) == 0:
            strengths.append("No significant conflicts detected - clear project direction")

        return strengths
