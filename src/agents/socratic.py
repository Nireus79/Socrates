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


    def require_authentication(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


    def require_project_access(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


    def log_agent_action(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


class SocraticCounselorAgent(BaseAgent):
    """
    Enhanced Socratic questioning agent with role-based intelligence

    Absorbs: Multi-role questioning functionality from legacy system
    Capabilities: Intelligent questioning, conflict mediation, insight extraction
    """

    def __init__(self, services: Optional[ServiceContainer] = None):
        """Initialize SocraticCounselorAgent with ServiceContainer dependency injection"""
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
        # Initialize persistence repositories
        self.session_repo = None
        self.question_repo = None
        self.message_repo = None

        # Get repositories from database service
        if self.db_service:
            try:
                self.session_repo = self.db_service.socratic_sessions
                self.question_repo = self.db_service.questions
                self.message_repo = self.db_service.conversation_messages
                if self.logger:
                    self.logger.info("Session persistence repositories initialized")
            except AttributeError as e:
                if self.logger:
                    self.logger.warning(f"Session repositories not available: {e}")

        if self.logger:
            self.logger.info("SocraticCounselorAgent initialized successfully")

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            "generate_questions", "analyze_responses", "detect_conflicts",
            "suggest_improvements", "facilitate_session", "extract_insights",
            "role_based_questioning", "context_aware_questioning",
            "conflict_mediation", "session_guidance", "learning_adaptation",
            "get_user_sessions", "resume_session"
        ]

    def _initialize_question_templates(self) -> Dict[str, List[str]]:
        """Initialize question templates for different scenarios"""
        return {
            "requirements_gathering": [
                "What specific problem are you trying to solve?",
                "Who are the primary users of this solution?",
                "What would success look like for this project?",
                "What constraints or limitations should we consider?",
                "What is the expected scale and performance needs?"
            ],
            "technical_discovery": [
                "What existing systems need to integrate with this solution?",
                "What are the critical performance requirements?",
                "What security and compliance requirements must we address?",
                "What is the expected user load and concurrent usage?",
                "What data needs to be stored, and what are the retention requirements?"
            ],
            "design_exploration": [
                "What are the key user workflows and interactions?",
                "What accessibility requirements must be supported?",
                "What devices and screen sizes need to be supported?",
                "What is the desired look and feel of the application?",
                "How should errors and edge cases be communicated to users?"
            ],
            "validation": [
                "How will we verify this requirement is met?",
                "What would make this feature successful from the user's perspective?",
                "What edge cases should we consider?",
                "How should the system handle errors in this scenario?",
                "What are the acceptance criteria for this functionality?"
            ],
            "risk_assessment": [
                "What could go wrong with this approach?",
                "What dependencies could impact the timeline?",
                "What technical risks should we mitigate?",
                "What happens if third-party services are unavailable?",
                "What is the backup plan if this approach doesn't work?"
            ],
            "clarification": [
                "Can you elaborate on what you mean by that?",
                "What specific outcome are you expecting?",
                "Can you provide an example of this scenario?",
                "How does this relate to the previous requirement?",
                "What would be different if we didn't have this feature?"
            ]
        }

    def _initialize_role_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize questioning strategies for each role type"""
        return {
            "project_manager": {
                "focus_areas": ["timeline", "resources", "stakeholders", "priorities", "risks"],
                "question_style": "strategic",
                "depth_preference": "high_level",
                "template_priority": ["requirements_gathering", "risk_assessment", "validation"]
            },
            "technical_lead": {
                "focus_areas": ["architecture", "technology", "scalability", "integration", "security"],
                "question_style": "architectural",
                "depth_preference": "technical",
                "template_priority": ["technical_discovery", "risk_assessment", "validation"]
            },
            "developer": {
                "focus_areas": ["implementation", "algorithms", "data_structures", "apis", "testing"],
                "question_style": "detailed",
                "depth_preference": "implementation",
                "template_priority": ["technical_discovery", "validation", "clarification"]
            },
            "designer": {
                "focus_areas": ["user_experience", "interface", "accessibility", "workflows", "branding"],
                "question_style": "user_focused",
                "depth_preference": "interaction",
                "template_priority": ["design_exploration", "requirements_gathering", "validation"]
            },
            "tester": {
                "focus_areas": ["quality", "edge_cases", "validation", "scenarios", "automation"],
                "question_style": "scenario_based",
                "depth_preference": "testing",
                "template_priority": ["validation", "risk_assessment", "clarification"]
            },
            "business_analyst": {
                "focus_areas": ["requirements", "business_rules", "processes", "compliance", "reporting"],
                "question_style": "analytical",
                "depth_preference": "business_logic",
                "template_priority": ["requirements_gathering", "validation", "risk_assessment"]
            },
            "devops": {
                "focus_areas": ["deployment", "infrastructure", "monitoring", "ci_cd", "security"],
                "question_style": "operational",
                "depth_preference": "infrastructure",
                "template_priority": ["technical_discovery", "risk_assessment", "validation"]
            }
        }

    @log_agent_action
    def _generate_questions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate role-based Socratic questions"""
        try:
            session_id = data.get('session_id', self._generate_session_id())
            role = data.get('role', 'developer')
            context = data.get('context', {})
            question_count = data.get('question_count', 5)
            project_phase = data.get('project_phase', 'planning')

            # Validate inputs
            if question_count > self.max_questions_per_session:
                question_count = self.max_questions_per_session

            # Get role strategy
            strategy = self.role_strategies.get(role, self.role_strategies["developer"])

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

            # Persist session to database
            self._persist_session(session_data)

            # Persist all questions to database
            for question in questions:
                self._persist_question(session_id, question)

            self.logger.info(f"Generated {len(questions)} questions for role '{role}' in session {session_id}")

            return self._success_response(
                "Questions generated successfully",
                {
                    'session_id': session_id,
                    'questions': questions,
                    'role': role,
                    'phase': project_phase,
                    'strategy': strategy['question_style']
                }
            )

        except Exception as e:
            error_msg = f"Question generation failed: {e}"
            self.logger.error(error_msg)
            return self._error_response(error_msg)

    def _generate_role_based_questions(self, role: str, strategy: Dict[str, Any],
                                       context: Dict[str, Any], count: int,
                                       phase: str) -> List[Dict[str, Any]]:
        """Generate questions based on role strategy and context"""
        questions = []

        # Get template priorities for this role
        template_priorities = strategy.get('template_priority', ['requirements_gathering'])

        # Generate questions from prioritized templates
        for template_type in template_priorities:
            if len(questions) >= count:
                break

            template_questions = self.question_templates.get(template_type, [])
            remaining = count - len(questions)

            # Select questions from this template type
            selected = template_questions[:remaining]

            for q_text in selected:
                question = {
                    'id': f"q_{len(questions) + 1}",
                    'text': q_text,
                    'role': role,
                    'type': template_type,
                    'phase': phase,
                    'priority': 'high' if len(questions) < 3 else 'medium',
                    'requires_response': True,
                    'metadata': {
                        'focus_area': strategy['focus_areas'][len(questions) % len(strategy['focus_areas'])],
                        'style': strategy['question_style']
                    }
                }
                questions.append(question)

        # Add context-specific questions if needed
        if context and len(questions) < count:
            context_questions = self._generate_context_questions(context, role, count - len(questions))
            questions.extend(context_questions)

        return questions[:count]

    def _generate_context_questions(self, context: Dict[str, Any], role: str,
                                    count: int) -> List[Dict[str, Any]]:
        """Generate questions based on specific context"""
        questions = []

        # Extract context elements
        project_type = context.get('project_type', '')
        technologies = context.get('technologies', [])
        constraints = context.get('constraints', [])

        # Generate context-aware questions
        if project_type and len(questions) < count:
            questions.append({
                'id': f"q_ctx_{len(questions) + 1}",
                'text': f"What specific challenges do you foresee for a {project_type} project?",
                'role': role,
                'type': 'context_specific',
                'phase': 'discovery',
                'priority': 'high',
                'requires_response': True
            })

        if technologies and len(questions) < count:
            tech_list = ', '.join(technologies[:3])
            questions.append({
                'id': f"q_ctx_{len(questions) + 1}",
                'text': f"How familiar is your team with {tech_list}?",
                'role': role,
                'type': 'context_specific',
                'phase': 'discovery',
                'priority': 'medium',
                'requires_response': True
            })

        if constraints and len(questions) < count:
            questions.append({
                'id': f"q_ctx_{len(questions) + 1}",
                'text': "How do these constraints affect your implementation approach?",
                'role': role,
                'type': 'context_specific',
                'phase': 'planning',
                'priority': 'high',
                'requires_response': True
            })

        return questions

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

    def _analyze_single_response(self, question_id: str, response: str,
                                 session: Dict[str, Any]) -> Dict[str, Any]:
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
        sentences = response.split('.')
        if not sentences:
            return 0.1

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
        low_clarity = [a for a in analysis_results if a['clarity'] < 0.5]

        if low_completeness:
            recommendations.append(
                f"{len(low_completeness)} responses need more detail - consider asking for elaboration"
            )

        if low_specificity:
            recommendations.append(
                f"{len(low_specificity)} responses are too vague - ask for specific examples"
            )

        if low_clarity:
            recommendations.append(
                f"{len(low_clarity)} responses are unclear - request clarification"
            )

        return recommendations

    def _suggest_follow_up_questions(self, analysis_results: List[Dict[str, Any]],
                                     session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest follow-up questions based on analysis"""
        follow_ups = []

        for analysis in analysis_results:
            question_id = analysis['question_id']
            needs = analysis.get('follow_up_needs', [])

            for need in needs:
                if need == 'needs_elaboration':
                    follow_ups.append({
                        'original_question_id': question_id,
                        'follow_up_question': "Can you elaborate on that with more details?",
                        'reason': 'Response was too brief',
                        'priority': 'high'
                    })
                elif need == 'needs_clarification_of_dependencies':
                    follow_ups.append({
                        'original_question_id': question_id,
                        'follow_up_question': "What are the specific dependencies you mentioned?",
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

        positive_indicators = ['yes', 'definitely', 'absolutely', 'always', 'required']
        negative_indicators = ['no', 'never', 'impossible', 'unnecessary', 'optional']

        for i, response1 in enumerate(responses):
            for j, response2 in enumerate(responses[i + 1:], i + 1):
                text1 = response1.get('response', '').lower()
                text2 = response2.get('response', '').lower()

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

        for i, req1 in enumerate(requirements):
            for j, req2 in enumerate(requirements[i + 1:], i + 1):
                req1_lower = req1.lower()
                req2_lower = req2.lower()

                # Check for contradictory requirements
                if 'must' in req1_lower and 'must not' in req2_lower:
                    conflicts.append({
                        'type': 'requirement_contradiction',
                        'severity': 'high',
                        'source1': f'requirement_{i}',
                        'source2': f'requirement_{j}',
                        'description': 'Contradictory requirements detected'
                    })

        return conflicts

    def _assess_conflict_severity(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall conflict severity"""
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}

        for conflict in conflicts:
            severity = conflict.get('severity', 'low')
            severity_counts[severity] += 1

        return {
            'total_conflicts': len(conflicts),
            'high_severity': severity_counts['high'],
            'medium_severity': severity_counts['medium'],
            'low_severity': severity_counts['low'],
            'requires_immediate_attention': severity_counts['high'] > 0
        }

    def _generate_conflict_recommendations(self, conflicts: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for resolving conflicts"""
        recommendations = []

        high_severity = [c for c in conflicts if c.get('severity') == 'high']
        if high_severity:
            recommendations.append("Address high-severity conflicts immediately before proceeding")
            recommendations.append("Consider stakeholder meeting to resolve contradictory requirements")

        response_conflicts = [c for c in conflicts if c.get('type') == 'response_contradiction']
        if response_conflicts:
            recommendations.append("Clarify contradictory responses with targeted follow-up questions")

        requirement_conflicts = [c for c in conflicts if c.get('type') == 'requirement_contradiction']
        if requirement_conflicts:
            recommendations.append("Prioritize and reconcile conflicting requirements")

        return recommendations

    @log_agent_action
    def _extract_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from session data"""
        try:
            session_id = data.get('session_id')

            if not session_id:
                return self._error_response("Session ID is required")

            if session_id not in self.current_sessions:
                return self._error_response(f"Unknown session: {session_id}")

            session = self.current_sessions[session_id]

            insights = {
                'session_id': session_id,
                'role': session.get('role'),
                'phase': session.get('phase'),
                'key_insights': [],
                'patterns': [],
                'recommendations': []
            }

            # Extract insights from session data
            if 'responses_analyzed' in session:
                insights['key_insights'].append(
                    f"{session['responses_analyzed']} responses analyzed with quality metrics"
                )

            return self._success_response("Insights extracted successfully", insights)

        except Exception as e:
            error_msg = f"Insight extraction failed: {e}"
            self.logger.error(error_msg)
            return self._error_response(error_msg)

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import time
        return f"session_{int(time.time() * 1000)}"

    def _persist_session(self, session_data: Dict[str, Any]) -> bool:
        """Persist session to database"""
        if not self.session_repo:
            return False

        try:
            from src.models import SocraticSession

            session = SocraticSession(
                id=session_data.get('id'),
                project_id=session_data.get('project_id'),
                user_id=session_data.get('user_id'),
                questioning_mode=session_data.get('questioning_mode', 'sequential'),
                current_phase=session_data.get('current_phase', 'discovery'),
                current_role=session_data.get('current_role', 'project_manager'),
                total_questions=session_data.get('total_questions', 0),
                answered_questions=session_data.get('answered_questions', 0),
                status=session_data.get('status', 'active'),
                quality_score=session_data.get('quality_score', 0.0),
                completion_percentage=session_data.get('completion_percentage', 0.0),
                created_at=DateTimeHelper.from_iso_string(session_data.get('created_at')) if session_data.get(
                    'created_at') else DateTimeHelper.now(),
                updated_at=DateTimeHelper.now()
            )

            success = self.session_repo.create(session)
            if success and self.logger:
                self.logger.info(f"Persisted session {session.id} to database")
            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to persist session: {e}")
            return False

    def _persist_question(self, session_id: str, question_data: Dict[str, Any]) -> bool:
        """Persist question to database"""
        if not self.question_repo:
            return False

        try:
            from src.models import Question

            question = Question(
                id=question_data.get('id'),
                session_id=session_id,
                role=question_data.get('role', 'project_manager'),
                question_text=question_data.get('text', ''),
                context=question_data.get('context', ''),
                is_follow_up=question_data.get('is_follow_up', False),
                parent_question_id=question_data.get('parent_question_id'),
                importance_score=question_data.get('importance_score', 0.5),
                is_answered=question_data.get('is_answered', False),
                answer_text=question_data.get('answer_text', ''),
                answer_quality_score=question_data.get('answer_quality_score', 0.0),
                generated_insights=question_data.get('generated_insights', []),
                detected_conflicts=question_data.get('detected_conflicts', []),
                recommended_follow_ups=question_data.get('recommended_follow_ups', []),
                created_at=DateTimeHelper.from_iso_string(question_data.get('created_at')) if question_data.get(
                    'created_at') else DateTimeHelper.now(),
                updated_at=DateTimeHelper.now()
            )

            success = self.question_repo.create(question)
            if success and self.logger:
                self.logger.debug(f"Persisted question {question.id} to database")
            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to persist question: {e}")
            return False

    def _persist_message(self, session_id: str, message_data: Dict[str, Any]) -> bool:
        """Persist conversation message to database"""
        if not self.message_repo:
            return False

        try:
            from src.models import ConversationMessage

            message = ConversationMessage(
                id=message_data.get('id'),
                session_id=session_id,
                role=message_data.get('role', 'user'),
                content=message_data.get('content', ''),
                metadata=message_data.get('metadata', {}),
                created_at=DateTimeHelper.from_iso_string(message_data.get('created_at')) if message_data.get(
                    'created_at') else DateTimeHelper.now()
            )

            success = self.message_repo.create(message)
            if success and self.logger:
                self.logger.debug(f"Persisted message to database for session {session_id}")
            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to persist message: {e}")
            return False

    def _update_session_in_db(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update existing session in database"""
        if not self.session_repo:
            return False

        try:
            from src.models import SocraticSession

            session = SocraticSession(
                id=session_id,
                project_id=session_data.get('project_id'),
                user_id=session_data.get('user_id'),
                questioning_mode=session_data.get('questioning_mode', 'sequential'),
                current_phase=session_data.get('current_phase'),
                current_role=session_data.get('current_role'),
                total_questions=session_data.get('total_questions', 0),
                answered_questions=session_data.get('answered_questions', 0),
                status=session_data.get('status', 'active'),
                quality_score=session_data.get('quality_score', 0.0),
                completion_percentage=session_data.get('completion_percentage', 0.0),
                created_at=DateTimeHelper.from_iso_string(session_data.get('created_at')),
                updated_at=DateTimeHelper.now()
            )

            success = self.session_repo.update(session)
            if success and self.logger:
                self.logger.debug(f"Updated session {session_id} in database")
            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to update session in database: {e}")
            return False

    def _resume_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Resume session from database

        Loads session, questions, and conversation history from database
        and restores to memory cache.

        Args:
            session_id: ID of session to resume

        Returns:
            Session data dict if successful, None otherwise
        """
        if not self.session_repo:
            if self.logger:
                self.logger.error("Cannot resume session: session repository not available")
            return None

        try:
            # Load session from database
            session = self.session_repo.get_by_id(session_id)
            if not session:
                if self.logger:
                    self.logger.warning(f"Session {session_id} not found in database")
                return None

            # Convert session to dict
            session_data = {
                'id': session.id,
                'project_id': session.project_id,
                'user_id': session.user_id,
                'questioning_mode': session.questioning_mode,
                'current_phase': session.current_phase,
                'current_role': session.current_role,
                'total_questions': session.total_questions,
                'answered_questions': session.answered_questions,
                'status': session.status,
                'quality_score': session.quality_score,
                'completion_percentage': session.completion_percentage,
                'created_at': DateTimeHelper.to_iso_string(session.created_at),
                'updated_at': DateTimeHelper.to_iso_string(session.updated_at),
                'questions': [],
                'conversation_history': []
            }

            # Load questions
            if self.question_repo:
                questions = self.question_repo.get_by_session_id(session_id)
                session_data['questions'] = [
                    {
                        'id': q.id,
                        'role': q.role,
                        'text': q.question_text,
                        'context': q.context,
                        'is_follow_up': q.is_follow_up,
                        'parent_question_id': q.parent_question_id,
                        'importance_score': q.importance_score,
                        'is_answered': q.is_answered,
                        'answer_text': q.answer_text,
                        'answer_quality_score': q.answer_quality_score,
                        'generated_insights': q.generated_insights,
                        'detected_conflicts': q.detected_conflicts,
                        'recommended_follow_ups': q.recommended_follow_ups,
                        'created_at': DateTimeHelper.to_iso_string(q.created_at)
                    }
                    for q in questions
                ]

            # Load conversation messages
            if self.message_repo:
                messages = self.message_repo.get_by_session_id(session_id)
                session_data['conversation_history'] = [
                    {
                        'id': m.id,
                        'role': m.role,
                        'content': m.content,
                        'metadata': m.metadata,
                        'created_at': DateTimeHelper.to_iso_string(m.created_at)
                    }
                    for m in messages
                ]

            # Restore to memory cache
            self.current_sessions[session_id] = session_data

            if self.logger:
                self.logger.info(
                    f"Resumed session {session_id} from database with {len(session_data['questions'])} questions and {len(session_data['conversation_history'])} messages")

            return session_data

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to resume session: {e}")
            return None

    @log_agent_action
    def _get_user_sessions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get all sessions for a specific user

        Args:
            data: {
                'user_id': str,  # Required
                'status': str,   # Optional filter: 'active', 'completed', 'paused'
                'limit': int,    # Optional, default 50
                'offset': int    # Optional, default 0
            }

        Returns:
            Dict with list of user sessions
        """
        try:
            user_id = data.get('user_id')
            status_filter = data.get('status')
            limit = data.get('limit', 50)
            offset = data.get('offset', 0)

            if not user_id:
                return self._error_response("User ID is required")

            # Get sessions from current active sessions (in-memory)
            active_sessions = []
            for session_id, session in self.current_sessions.items():
                if session.get('user_id') == user_id:
                    session_summary = {
                        'session_id': session_id,
                        'project_id': session.get('project_id'),
                        'role': session.get('role'),
                        'status': 'active',
                        'created_at': session.get('created_at'),
                        'questions_count': session.get('questions_asked', 0),
                        'responses_count': session.get('responses_received', 0)
                    }
                    active_sessions.append(session_summary)

            # TODO: Also query database for historical sessions when session repository is implemented
            # For now, return only active in-memory sessions
            all_sessions = active_sessions

            # Apply status filter if provided
            if status_filter:
                all_sessions = [s for s in all_sessions if s.get('status') == status_filter]

            # Apply pagination
            total_count = len(all_sessions)
            paginated_sessions = all_sessions[offset:offset + limit]

            self.logger.info(f"Retrieved {len(paginated_sessions)} sessions for user {user_id}")

            return self._success_response(
                f"Retrieved {len(paginated_sessions)} sessions",
                {
                    'sessions': paginated_sessions,
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + limit) < total_count
                }
            )

        except Exception as e:
            error_msg = f"Failed to get user sessions: {e}"
            self.logger.error(error_msg)
            return self._error_response(error_msg)

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


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = ['SocraticCounselorAgent']

if __name__ == "__main__":
    print("SocraticCounselorAgent module - use via AgentOrchestrator")
