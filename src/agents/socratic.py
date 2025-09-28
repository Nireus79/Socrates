#!/usr/bin/env python3
"""
SocraticCounselorAgent - Enhanced Socratic Questioning with Role-Based Intelligence
====================================================================================

Handles intelligent Socratic questioning across all 7 role types, context-aware
conversation management, learning from user response patterns, and insight extraction.
Fully corrected according to project standards.

Capabilities:
- Role-based question generation (7 role types)
- Context-aware conversation management
- Learning from user response patterns
- Conflict mediation and insight extraction
- Dynamic vs static questioning modes
- Session guidance and flow management
"""

from typing import Dict, List, Any, Optional
from functools import wraps
import json
import random

try:
    from src.core import ServiceContainer, DateTimeHelper, ValidationError, ValidationHelper
    from src.models import ConversationMessage, UserRole, Project, ProjectPhase, ModelValidator
    from src.database import get_database
    from .base import BaseAgent, require_authentication, require_project_access, log_agent_action

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    # Fallback implementations
    import logging
    from datetime import datetime
    from enum import Enum


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


    class DateTimeHelper:
        @staticmethod
        def now():
            return datetime.now()

        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None

        @staticmethod
        def from_iso_string(iso_str):
            return datetime.fromisoformat(iso_str) if iso_str else None


    class ValidationError(Exception):
        pass


    class ValidationHelper:
        @staticmethod
        def validate_email(email):
            return "@" in str(email) if email else False


    class UserRole(Enum):
        PROJECT_MANAGER = "project_manager"
        TECHNICAL_LEAD = "technical_lead"
        DEVELOPER = "developer"
        DESIGNER = "designer"
        TESTER = "tester"
        BUSINESS_ANALYST = "business_analyst"
        DEVOPS = "devops"


    class ProjectPhase(Enum):
        PLANNING = "planning"
        DISCOVERY = "discovery"
        DEVELOPMENT = "development"
        TESTING = "testing"
        DEPLOYMENT = "deployment"


class SocraticCounselorAgent(BaseAgent):
    """
    Enhanced Socratic questioning agent with role-based intelligence

    Absorbs: Multi-role questioning functionality from legacy system
    Capabilities: Intelligent questioning, conflict mediation, insight extraction
    """

    def __init__(self, services: ServiceContainer):
        """Initialize SocraticCounselorAgent with corrected patterns"""
        super().__init__("socratic_counselor", "Socratic Counselor", services)

        # Question types and templates
        self.question_templates = self._initialize_question_templates()
        self.role_strategies = self._initialize_role_strategies()

        # Session state
        self.current_sessions = {}  # Track active questioning sessions
        self.question_history = {}  # Track question patterns and effectiveness

        # Learning parameters
        self.effectiveness_threshold = 0.7
        self.max_questions_per_session = 25
        self.conflict_detection_enabled = True

        if self.logger:
            self.logger.info("SocraticCounselorAgent initialized successfully")

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            "generate_questions", "analyze_responses", "detect_conflicts",
            "suggest_improvements", "facilitate_session", "extract_insights",
            "role_based_questioning", "context_aware_questioning",
            "conflict_mediation", "session_guidance", "learning_adaptation"
        ]

    def _initialize_question_templates(self) -> Dict[str, List[str]]:
        """Initialize question templates for different scenarios"""
        return {
            "requirements_gathering": [
                "What specific problem are you trying to solve?",
                "Who are the primary users of this solution?",
                "What would success look like for this project?",
                "What constraints or limitations should we consider?",
                "How does this align with your business objectives?"
            ],
            "technical_exploration": [
                "What technical challenges do you anticipate?",
                "How will this integrate with existing systems?",
                "What performance requirements do you have?",
                "What security considerations are important?",
                "How will you handle scalability?"
            ],
            "design_thinking": [
                "How will users interact with this feature?",
                "What's the most intuitive way to present this information?",
                "How can we minimize cognitive load for users?",
                "What accessibility requirements should we consider?",
                "How does this fit into the overall user journey?"
            ],
            "risk_assessment": [
                "What could go wrong with this approach?",
                "What dependencies might cause delays?",
                "How would you handle edge cases?",
                "What backup plans do you have?",
                "What impact would failure have?"
            ],
            "validation": [
                "How will you measure success?",
                "What data will you collect to validate this?",
                "How will you know if users are satisfied?",
                "What metrics are most important?",
                "How will you handle negative feedback?"
            ]
        }

    def _initialize_role_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize questioning strategies for different roles"""
        return {
            "project_manager": {
                "focus_areas": ["timeline", "resources", "stakeholders", "risks", "deliverables"],
                "question_style": "strategic",
                "depth_preference": "broad",
                "template_priority": ["requirements_gathering", "risk_assessment", "validation"]
            },
            "developer": {
                "focus_areas": ["implementation", "architecture", "performance", "maintainability"],
                "question_style": "technical",
                "depth_preference": "deep",
                "template_priority": ["technical_exploration", "risk_assessment", "validation"]
            },
            "designer": {
                "focus_areas": ["user_experience", "interface", "accessibility", "usability"],
                "question_style": "user_centric",
                "depth_preference": "empathetic",
                "template_priority": ["design_thinking", "requirements_gathering", "validation"]
            },
            "tester": {
                "focus_areas": ["quality", "edge_cases", "validation", "automation"],
                "question_style": "analytical",
                "depth_preference": "thorough",
                "template_priority": ["validation", "risk_assessment", "technical_exploration"]
            },
            "business_analyst": {
                "focus_areas": ["requirements", "processes", "stakeholders", "value"],
                "question_style": "analytical",
                "depth_preference": "comprehensive",
                "template_priority": ["requirements_gathering", "validation", "risk_assessment"]
            },
            "stakeholder": {
                "focus_areas": ["business_value", "outcomes", "impact", "alignment"],
                "question_style": "outcome_focused",
                "depth_preference": "strategic",
                "template_priority": ["requirements_gathering", "validation", "risk_assessment"]
            }
        }

    @log_agent_action
    def _generate_questions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate role-based Socratic questions"""
        try:
            session_id: str = data.get('session_id', self._generate_session_id())
            role: str = data.get('role', 'developer')
            context: Dict[str, Any] = data.get('context', {})
            question_count: int = data.get('question_count', 5)
            project_phase: str = data.get('project_phase', 'planning')

            # Validate inputs
            if question_count > self.max_questions_per_session:
                question_count = self.max_questions_per_session

            # Get role strategy
            strategy: Dict[str, Any] = self.role_strategies.get(role, self.role_strategies["developer"])

            # Generate context-aware questions
            questions = self._generate_role_based_questions(
                role, strategy, context, question_count, project_phase
            )

            # Track session
            session_data = {
                'session_id': session_id,
                'role': role,
                'questions_generated': len(questions),
                'context': context,
                'timestamp': DateTimeHelper.now(),
                'phase': project_phase
            }
            self.current_sessions[session_id] = session_data

            # Emit question generation event
            if self.events:
                self.events.emit('questions_generated', self.agent_id, {
                    'session_id': session_id,
                    'role': role,
                    'question_count': len(questions),
                    'project_phase': project_phase
                })

            self.logger.info(f"Generated {len(questions)} questions for role {role} in session {session_id}")

            return self._success_response("Questions generated successfully", {
                'session_id': session_id,
                'role': role,
                'questions': questions,
                'strategy': strategy,
                'context_considered': bool(context),
                'generated_at': DateTimeHelper.to_iso_string(session_data['timestamp'])
            })

        except Exception as e:
            error_msg = f"Question generation failed: {e}"
            self.logger.error(error_msg)
            return self._error_response(error_msg)

    def _generate_role_based_questions(self, role: str, strategy: Dict[str, Any],
                                       context: Dict[str, Any], count: int, phase: str) -> List[Dict[str, Any]]:
        """Generate questions based on role strategy and context"""
        questions = []
        focus_areas = strategy.get('focus_areas', [])
        question_style = strategy.get('question_style', 'general')
        template_priority = strategy.get('template_priority', ['requirements_gathering'])

        # Context-aware question selection
        available_templates = []
        for template_type in template_priority:
            if template_type in self.question_templates:
                available_templates.extend([
                    {'question': q, 'type': template_type, 'focus': 'general'}
                    for q in self.question_templates[template_type]
                ])

        # Add phase-specific questions
        phase_questions = self._get_phase_specific_questions(phase, role)
        available_templates.extend(phase_questions)

        # Add context-specific questions
        if context:
            context_questions = self._generate_context_questions(context, role, focus_areas)
            available_templates.extend(context_questions)

        # Select diverse questions
        selected_questions = self._select_diverse_questions(available_templates, count, focus_areas)

        # Format questions with metadata
        for i, q_data in enumerate(selected_questions[:count]):
            question = {
                'id': f"q_{i + 1}",
                'question': q_data['question'],
                'type': q_data.get('type', 'general'),
                'focus_area': q_data.get('focus', 'general'),
                'style': question_style,
                'priority': i + 1,
                'expected_response_type': self._get_expected_response_type(q_data['question']),
                'follow_up_triggers': self._get_follow_up_triggers(q_data['question'])
            }
            questions.append(question)

        return questions

    def _get_phase_specific_questions(self, phase: str, role: str) -> List[Dict[str, Any]]:
        """Get questions specific to project phase"""
        phase_questions: Dict[str, List[str]] = {
            "planning": [
                "What are the key deliverables for this phase?",
                "How will you prioritize the features?",
                "What assumptions are you making?"
            ],
            "development": [
                "How will you ensure code quality?",
                "What testing strategies will you employ?",
                "How will you handle technical debt?"
            ],
            "testing": [
                "What testing scenarios are most critical?",
                "How will you measure test coverage?",
                "What's your bug triage process?"
            ],
            "deployment": [
                "What's your rollback strategy?",
                "How will you monitor system health?",
                "What's your go-live checklist?"
            ]
        }

        questions: List[str] = phase_questions.get(phase, [])
        return [{'question': q, 'type': 'phase_specific', 'focus': phase} for q in questions]

    def _generate_context_questions(self, context: Dict[str, Any], role: str, focus_areas: List[str]) -> List[
        Dict[str, Any]]:
        """Generate questions based on provided context"""
        context_questions = []

        # Technology-specific questions
        if 'technology' in context:
            tech = context['technology']
            context_questions.extend([
                {'question': f"Why did you choose {tech} for this project?", 'type': 'context', 'focus': 'technology'},
                {'question': f"What are the limitations of {tech} we should consider?", 'type': 'context',
                 'focus': 'technology'}
            ])

        # Domain-specific questions
        if 'domain' in context:
            domain = context['domain']
            context_questions.extend([
                {'question': f"What are the unique challenges in the {domain} domain?", 'type': 'context',
                 'focus': 'domain'},
                {'question': f"What industry standards apply to {domain} solutions?", 'type': 'context',
                 'focus': 'domain'}
            ])

        # Scale-specific questions
        if 'scale' in context:
            scale = context['scale']
            context_questions.extend([
                {'question': f"How will you handle {scale} scale requirements?", 'type': 'context', 'focus': 'scale'},
                {'question': f"What infrastructure considerations are needed for {scale}?", 'type': 'context',
                 'focus': 'scale'}
            ])

        return context_questions

    def _select_diverse_questions(self, available_questions: List[Dict[str, Any]],
                                  count: int, focus_areas: List[str]) -> List[Dict[str, Any]]:
        """Select diverse questions covering different focus areas"""
        if len(available_questions) <= count:
            return available_questions

        # Ensure diversity across focus areas
        selected = []
        used_focuses = set()

        # First pass: select one question from each focus area
        for focus in focus_areas:
            focus_questions = [q for q in available_questions if q.get('focus') == focus]
            if focus_questions and focus not in used_focuses:
                selected.append(random.choice(focus_questions))
                used_focuses.add(focus)
                if len(selected) >= count:
                    break

        # Second pass: fill remaining slots with diverse questions
        remaining_questions = [q for q in available_questions if q not in selected]
        while len(selected) < count and remaining_questions:
            # Prefer questions with unused focus areas
            unused_focus_questions = [q for q in remaining_questions
                                      if q.get('focus') not in used_focuses]

            if unused_focus_questions:
                question = random.choice(unused_focus_questions)
                used_focuses.add(question.get('focus'))
            else:
                question = random.choice(remaining_questions)

            selected.append(question)
            remaining_questions.remove(question)

        return selected

    def _get_expected_response_type(self, question: str) -> str:
        """Determine expected response type from question"""
        question_lower = question.lower()

        if any(word in question_lower for word in ['how many', 'how much', 'what percentage']):
            return 'quantitative'
        elif any(word in question_lower for word in ['how', 'what', 'why', 'where', 'when']):
            return 'descriptive'
        elif any(word in question_lower for word in ['would', 'could', 'should', 'might']):
            return 'hypothetical'
        elif '?' in question and any(word in question_lower for word in ['or', 'either']):
            return 'choice'
        else:
            return 'open_ended'

    def _get_follow_up_triggers(self, question: str) -> List[str]:
        """Get potential follow-up question triggers"""
        triggers = []
        question_lower = question.lower()

        if 'why' in question_lower:
            triggers.extend(['elaborate', 'assumptions', 'alternatives'])
        if 'how' in question_lower:
            triggers.extend(['process', 'timeline', 'resources'])
        if 'what' in question_lower:
            triggers.extend(['examples', 'details', 'implications'])
        if any(word in question_lower for word in ['problem', 'challenge', 'issue']):
            triggers.extend(['root_cause', 'solutions', 'impact'])

        return triggers

    @log_agent_action
    def _analyze_responses(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user responses and suggest follow-up questions"""
        try:
            session_id = data.get('session_id')
            responses = data.get('responses', [])

            if not session_id or not responses:
                return self._error_response("Session ID and responses are required")

            if session_id not in self.current_sessions:
                return self._error_response(f"Unknown session: {session_id}")

            session = self.current_sessions[session_id]
            analysis_results = []

            for response_data in responses:
                question_id = response_data.get('question_id')
                response_text = response_data.get('response', '')

                analysis = self._analyze_single_response(question_id, response_text, session)
                analysis_results.append(analysis)

            # Generate overall insights
            overall_insights = self._generate_session_insights(analysis_results, session)

            # Suggest follow-up questions
            follow_ups = self._suggest_follow_up_questions(analysis_results, session)

            # Update session with analysis
            session['responses_analyzed'] = len(responses)
            session['last_analysis'] = DateTimeHelper.now()

            return self._success_response("Response analysis completed", {
                'session_id': session_id,
                'analysis_results': analysis_results,
                'overall_insights': overall_insights,
                'follow_up_questions': follow_ups,
                'analysis_timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            })

        except Exception as e:
            error_msg = f"Response analysis failed: {e}"
            self.logger.error(error_msg)
            return self._error_response(error_msg)

    def _analyze_single_response(self, question_id: str, response: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single response"""
        analysis = {
            'question_id': question_id,
            'response_length': len(response),
            'word_count': len(response.split()),
            'completeness': self._assess_completeness(response),
            'specificity': self._assess_specificity(response),
            'clarity': self._assess_clarity(response),
            'insights': self._extract_insights(response),
            'concerns': self._identify_concerns(response),
            'follow_up_needs': self._identify_follow_up_needs(response)
        }

        return analysis

    def _assess_completeness(self, response: str) -> float:
        """Assess completeness of response (0.0 to 1.0)"""
        if len(response) < 10:
            return 0.1
        elif len(response) < 50:
            return 0.4
        elif len(response) < 150:
            return 0.7
        else:
            return 1.0

    def _assess_specificity(self, response: str) -> float:
        """Assess specificity of response (0.0 to 1.0)"""
        specific_indicators = ['specific', 'exactly', 'precisely', 'particular', 'detailed']
        vague_indicators = ['maybe', 'probably', 'possibly', 'generally', 'usually']

        specific_count = sum(1 for word in specific_indicators if word in response.lower())
        vague_count = sum(1 for word in vague_indicators if word in response.lower())

        if specific_count > vague_count:
            return min(1.0, 0.5 + (specific_count * 0.1))
        else:
            return max(0.1, 0.5 - (vague_count * 0.1))

    def _assess_clarity(self, response: str) -> float:
        """Assess clarity of response (0.0 to 1.0)"""
        # Simple heuristic based on sentence structure and length
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

        if avg_sentence_length > 25:
            return 0.4  # Too complex
        elif avg_sentence_length < 5:
            return 0.3  # Too simple
        else:
            return 0.8  # Good balance

    def _extract_insights(self, response: str) -> List[str]:
        """Extract key insights from response"""
        insights = []

        # Look for explicit statements
        insight_patterns = [
            'I learned', 'I realized', 'I discovered', 'I found',
            'This means', 'This suggests', 'This implies', 'This indicates'
        ]

        for pattern in insight_patterns:
            if pattern.lower() in response.lower():
                insights.append(f"User expressed learning: {pattern}")

        return insights

    def _identify_concerns(self, response: str) -> List[str]:
        """Identify potential concerns in response"""
        concerns = []

        concern_indicators = [
            'problem', 'issue', 'challenge', 'difficulty', 'concern',
            'worried', 'unsure', 'uncertain', 'confused', 'unclear'
        ]

        for indicator in concern_indicators:
            if indicator in response.lower():
                concerns.append(f"Potential concern: {indicator}")

        return concerns

    def _identify_follow_up_needs(self, response: str) -> List[str]:
        """Identify areas needing follow-up questions"""
        needs = []

        if len(response) < 50:
            needs.append('needs_elaboration')

        if 'depends' in response.lower():
            needs.append('needs_clarification_of_dependencies')

        if any(word in response.lower() for word in ['maybe', 'possibly', 'might']):
            needs.append('needs_commitment_or_certainty')

        if '?' in response:
            needs.append('user_has_questions')

        return needs

    def _generate_session_insights(self, analysis_results: List[Dict[str, Any]],
                                   session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall insights for the session"""
        if not analysis_results:
            return {}

        total_responses = len(analysis_results)
        avg_completeness = sum(a['completeness'] for a in analysis_results) / total_responses
        avg_specificity = sum(a['specificity'] for a in analysis_results) / total_responses
        avg_clarity = sum(a['clarity'] for a in analysis_results) / total_responses

        all_concerns = []
        all_insights = []
        for analysis in analysis_results:
            all_concerns.extend(analysis['concerns'])
            all_insights.extend(analysis['insights'])

        return {
            'session_quality': {
                'average_completeness': round(avg_completeness, 2),
                'average_specificity': round(avg_specificity, 2),
                'average_clarity': round(avg_clarity, 2),
                'overall_score': round((avg_completeness + avg_specificity + avg_clarity) / 3, 2)
            },
            'total_concerns': len(all_concerns),
            'total_insights': len(all_insights),
            'session_effectiveness': self._calculate_session_effectiveness(analysis_results),
            'recommendations': self._generate_session_recommendations(analysis_results)
        }

    def _calculate_session_effectiveness(self, analysis_results: List[Dict[str, Any]]) -> float:
        """Calculate overall session effectiveness"""
        if not analysis_results:
            return 0.0

        quality_scores = []
        for analysis in analysis_results:
            quality = (analysis['completeness'] + analysis['specificity'] + analysis['clarity']) / 3
            quality_scores.append(quality)

        return round(sum(quality_scores) / len(quality_scores), 2)

    def _generate_session_recommendations(self, analysis_results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for improving the session"""
        recommendations = []

        low_completeness = [a for a in analysis_results if a['completeness'] < 0.5]
        low_specificity = [a for a in analysis_results if a['specificity'] < 0.5]

        if len(low_completeness) > len(analysis_results) / 2:
            recommendations.append("Consider asking for more detailed responses")

        if len(low_specificity) > len(analysis_results) / 2:
            recommendations.append("Ask for specific examples or concrete details")

        concerns_count = sum(len(a['concerns']) for a in analysis_results)
        if concerns_count > 3:
            recommendations.append("Address identified concerns before proceeding")

        return recommendations

    def _suggest_follow_up_questions(self, analysis_results: List[Dict[str, Any]],
                                     session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest follow-up questions based on analysis"""
        follow_ups = []

        for analysis in analysis_results:
            question_id = analysis['question_id']
            needs = analysis['follow_up_needs']

            for need in needs:
                if need == 'needs_elaboration':
                    follow_ups.append({
                        'original_question_id': question_id,
                        'follow_up_question': "Could you provide more details about that?",
                        'reason': 'Response was too brief',
                        'priority': 'medium'
                    })
                elif need == 'needs_clarification_of_dependencies':
                    follow_ups.append({
                        'original_question_id': question_id,
                        'follow_up_question': "What specific factors does this depend on?",
                        'reason': 'Dependencies mentioned but not clarified',
                        'priority': 'high'
                    })
                elif need == 'user_has_questions':
                    follow_ups.append({
                        'original_question_id': question_id,
                        'follow_up_question': "What specific questions do you have about this?",
                        'reason': 'User expressed questions or uncertainty',
                        'priority': 'high'
                    })

        return follow_ups[:5]  # Limit to top 5 follow-ups

    @log_agent_action
    def _detect_conflicts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect conflicts in requirements or responses"""
        try:
            responses = data.get('responses', [])
            requirements = data.get('requirements', [])

            if not responses and not requirements:
                return self._error_response("Responses or requirements are required for conflict detection")

            conflicts = []

            # Detect response conflicts
            if responses:
                response_conflicts = self._detect_response_conflicts(responses)
                conflicts.extend(response_conflicts)

            # Detect requirement conflicts
            if requirements:
                requirement_conflicts = self._detect_requirement_conflicts(requirements)
                conflicts.extend(requirement_conflicts)

            # Assess conflict severity
            conflict_summary = self._assess_conflict_severity(conflicts)

            return self._success_response("Conflict detection completed", {
                'conflicts_found': len(conflicts),
                'conflicts': conflicts,
                'conflict_summary': conflict_summary,
                'recommendations': self._generate_conflict_recommendations(conflicts)
            })

        except Exception as e:
            error_msg = f"Conflict detection failed: {e}"
            self.logger.error(error_msg)
            return self._error_response(error_msg)

    def _detect_response_conflicts(self, responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicts between responses"""
        conflicts = []

        # Simple conflict detection based on contradictory keywords
        positive_indicators = ['yes', 'definitely', 'absolutely', 'always', 'required']
        negative_indicators = ['no', 'never', 'impossible', 'unnecessary', 'optional']

        for i, response1 in enumerate(responses):
            for j, response2 in enumerate(responses[i + 1:], i + 1):
                text1 = response1.get('response', '').lower()
                text2 = response2.get('response', '').lower()

                # Check for contradictory statements
                has_positive1 = any(indicator in text1 for indicator in positive_indicators)
                has_negative1 = any(indicator in text1 for indicator in negative_indicators)
                has_positive2 = any(indicator in text2 for indicator in positive_indicators)
                has_negative2 = any(indicator in text2 for indicator in negative_indicators)

                if (has_positive1 and has_negative2) or (has_negative1 and has_positive2):
                    conflicts.append({
                        'type': 'response_contradiction',
                        'severity': 'medium',
                        'source1': response1.get('question_id', f'response_{i}'),
                        'source2': response2.get('question_id', f'response_{j}'),
                        'description': 'Potentially contradictory responses detected'
                    })

        return conflicts

    def _detect_requirement_conflicts(self, requirements: List[str]) -> List[Dict[str, Any]]:
        """Detect conflicts between requirements"""
        conflicts = []

        # Simple requirement conflict detection
        for i, req1 in enumerate(requirements):
            for j, req2 in enumerate(requirements[i + 1:], i + 1):
                # Look for contradictory requirements
                if ('must' in req1.lower() and 'must not' in req2.lower()) or \
                        ('required' in req1.lower() and 'optional' in req2.lower()):
                    conflicts.append({
                        'type': 'requirement_contradiction',
                        'severity': 'high',
                        'source1': f'requirement_{i + 1}',
                        'source2': f'requirement_{j + 1}',
                        'description': f'Conflicting requirements: "{req1}" vs "{req2}"'
                    })

        return conflicts

    def _assess_conflict_severity(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall conflict severity"""
        if not conflicts:
            return {'level': 'none', 'risk': 'low'}

        severity_counts = {'low': 0, 'medium': 0, 'high': 0}
        for conflict in conflicts:
            severity = conflict.get('severity', 'medium')
            severity_counts[severity] += 1

        if severity_counts['high'] > 0:
            return {'level': 'high', 'risk': 'high', 'action': 'immediate_attention_required'}
        elif severity_counts['medium'] > 2:
            return {'level': 'medium', 'risk': 'medium', 'action': 'resolution_recommended'}
        else:
            return {'level': 'low', 'risk': 'low', 'action': 'monitor_and_clarify'}

    def _generate_conflict_recommendations(self, conflicts: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for resolving conflicts"""
        if not conflicts:
            return ["No conflicts detected - proceed with confidence"]

        recommendations = []

        high_severity_conflicts = [c for c in conflicts if c.get('severity') == 'high']
        if high_severity_conflicts:
            recommendations.append("Address high-severity conflicts immediately before proceeding")
            recommendations.append("Consider stakeholder meeting to resolve contradictory requirements")

        response_conflicts = [c for c in conflicts if c.get('type') == 'response_contradiction']
        if response_conflicts:
            recommendations.append("Clarify contradictory responses with targeted follow-up questions")

        requirement_conflicts = [c for c in conflicts if c.get('type') == 'requirement_contradiction']
        if requirement_conflicts:
            recommendations.append("Prioritize and reconcile conflicting requirements")

        return recommendations

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import time
        return f"session_{int(time.time() * 1000)}"

    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check for SocraticCounselorAgent"""
        health = super().health_check()

        try:
            # Check question templates
            health['question_templates'] = {
                'total_templates': len(self.question_templates),
                'template_types': list(self.question_templates.keys())
            }

            # Check role strategies
            health['role_strategies'] = {
                'supported_roles': len(self.role_strategies),
                'roles': list(self.role_strategies.keys())
            }

            # Check active sessions
            health['session_status'] = {
                'active_sessions': len(self.current_sessions),
                'max_questions_per_session': self.max_questions_per_session
            }

        except Exception as e:
            health['status'] = 'degraded'
            health['error'] = f"Health check failed: {e}"

        return health
