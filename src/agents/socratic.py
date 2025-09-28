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
    from src.core import get_logger, DateTimeHelper, ValidationError, ValidationHelper, get_event_bus
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
    
    def get_event_bus():
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
        ANALYSIS = "analysis"
        DESIGN = "design"
        IMPLEMENTATION = "implementation"
        TESTING = "testing"
        DEPLOYMENT = "deployment"
    
    class ModelValidator:
        @staticmethod
        def validate_project_data(data):
            return []
    
    class ConversationMessage:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class Project:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.conversation_history = getattr(self, 'conversation_history', [])
    
    class BaseAgent:
        def __init__(self, agent_id, name):
            self.agent_id = agent_id
            self.name = name
            self.logger = get_logger(agent_id)
            self.claude_client = None
        
        def _error_response(self, message, error_code=None):
            return {'success': False, 'error': message}
    
    def require_authentication(func):
        return func
    
    def require_project_access(func):
        return func
    
    def log_agent_action(func):
        return func


class SocraticCounselorAgent(BaseAgent):
    """
    Enhanced Socratic questioning agent with role-based intelligence
    
    Absorbs: Role-awareness and management from RoleManagerAgent
    Capabilities: All 7 role types, context-aware questioning, learning
    """

    def __init__(self):
        """Initialize SocraticCounselorAgent with corrected patterns"""
        super().__init__("socratic_counselor", "Socratic Counselor")
        
        # Database service initialization (corrected pattern)
        self.db_service = get_database() if CORE_AVAILABLE else None
        
        # Event bus for conversation events
        self.events = get_event_bus() if CORE_AVAILABLE else None
        
        # Load role definitions and question templates
        self.role_definitions = self._load_role_definitions()
        self.question_templates = self._load_question_templates()
        self.learning_patterns = {}
        
        # Initialize logging
        if self.logger:
            self.logger.info(f"SocraticCounselorAgent initialized successfully")

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            "generate_question", "process_response", "analyze_conversation",
            "role_based_questioning", "context_adaptation", "learning_optimization",
            "conflict_mediation", "insight_extraction", "session_guidance",
            "start_session", "end_session", "switch_role"
        ]

    def _load_role_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load definitions for all 7 role types with comprehensive focus areas"""
        return {
            "project_manager": {
                "focus": ["timeline", "resources", "stakeholders", "risks", "deliverables", "budget", "scope"],
                "question_style": "strategic",
                "priorities": ["feasibility", "scope", "constraints", "roi", "success_metrics"],
                "key_concerns": ["timeline_realism", "resource_allocation", "risk_mitigation"]
            },
            "technical_lead": {
                "focus": ["architecture", "technology", "scalability", "performance", "security", "integration"],
                "question_style": "technical_depth",
                "priorities": ["design_patterns", "best_practices", "integration", "maintainability"],
                "key_concerns": ["technical_debt", "scalability_limits", "security_vulnerabilities"]
            },
            "developer": {
                "focus": ["implementation", "algorithms", "data_structures", "apis", "debugging", "testing"],
                "question_style": "implementation_focused",
                "priorities": ["code_quality", "maintainability", "testing", "documentation"],
                "key_concerns": ["code_complexity", "performance_bottlenecks", "error_handling"]
            },
            "designer": {
                "focus": ["user_experience", "interface_design", "accessibility", "usability", "branding"],
                "question_style": "user_centered",
                "priorities": ["user_flows", "responsive_design", "brand_consistency", "accessibility"],
                "key_concerns": ["user_satisfaction", "design_consistency", "mobile_responsiveness"]
            },
            "tester": {
                "focus": ["quality_assurance", "edge_cases", "validation", "automation", "performance"],
                "question_style": "quality_focused",
                "priorities": ["test_coverage", "edge_cases", "automation", "regression_testing"],
                "key_concerns": ["quality_standards", "test_completeness", "bug_prevention"]
            },
            "business_analyst": {
                "focus": ["requirements", "business_rules", "compliance", "reporting", "stakeholder_needs"],
                "question_style": "requirements_driven",
                "priorities": ["requirement_clarity", "business_value", "compliance", "stakeholder_alignment"],
                "key_concerns": ["requirement_gaps", "business_alignment", "regulatory_compliance"]
            },
            "devops": {
                "focus": ["infrastructure", "deployment", "monitoring", "security", "automation", "scaling"],
                "question_style": "operations_focused",
                "priorities": ["deployment_strategy", "monitoring", "security", "automation"],
                "key_concerns": ["deployment_reliability", "system_monitoring", "security_hardening"]
            }
        }

    def _load_question_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Load question templates organized by role and phase"""
        return {
            "discovery": {
                "project_manager": [
                    "What are the main goals and success criteria for this project?",
                    "Who are the key stakeholders and what are their expectations?",
                    "What is the realistic timeline and budget for this project?",
                    "What are the biggest risks and how will they be mitigated?",
                    "What constraints or limitations should we consider?"
                ],
                "technical_lead": [
                    "What is the expected scale and performance requirements?",
                    "What existing systems need to integrate with this solution?",
                    "What are the security and compliance requirements?",
                    "What technology preferences or constraints exist?",
                    "What is the team's current technical expertise?"
                ],
                "developer": [
                    "What are the core features and user workflows?",
                    "What data needs to be stored and how will it flow?",
                    "What external APIs or services are needed?",
                    "What are the most complex technical challenges?",
                    "How will the system handle errors and edge cases?"
                ],
                "designer": [
                    "Who are the target users and what are their needs?",
                    "What devices and browsers need to be supported?",
                    "Are there existing design guidelines or branding requirements?",
                    "What accessibility requirements must be met?",
                    "How should the user interface feel and behave?"
                ],
                "tester": [
                    "What are the quality standards and acceptance criteria?",
                    "What are the most critical failure scenarios to test?",
                    "What types of testing are required (unit, integration, performance)?",
                    "How will testing be automated and integrated into development?",
                    "What browsers, devices, and environments need testing?"
                ],
                "business_analyst": [
                    "What business problems does this solution address?",
                    "What are the current manual processes that need improvement?",
                    "What reports and analytics are needed?",
                    "What compliance or regulatory requirements apply?",
                    "How will success be measured and monitored?"
                ],
                "devops": [
                    "What is the deployment environment and infrastructure?",
                    "What monitoring and alerting capabilities are needed?",
                    "What are the backup and disaster recovery requirements?",
                    "How will the application scale with increased load?",
                    "What security measures need to be implemented?"
                ]
            },
            "analysis": {
                "project_manager": [
                    "How will project milestones and deliverables be tracked?",
                    "What communication and reporting processes are needed?",
                    "How will scope changes be managed and approved?",
                    "What dependencies exist between different work streams?",
                    "How will team productivity and progress be measured?"
                ],
                "technical_lead": [
                    "What is the overall system architecture and design pattern?",
                    "How will different components interact and communicate?",
                    "What are the data models and storage requirements?",
                    "How will the system handle concurrent users and load?",
                    "What are the key design decisions and trade-offs?"
                ],
                "developer": [
                    "How should the codebase be organized and structured?",
                    "What coding standards and best practices will be followed?",
                    "How will code reviews and quality assurance work?",
                    "What development tools and frameworks will be used?",
                    "How will different features be prioritized and implemented?"
                ],
                "designer": [
                    "What are the key user journeys and interaction patterns?",
                    "How will the interface adapt to different screen sizes?",
                    "What visual design elements and style guide are needed?",
                    "How will user feedback be collected and incorporated?",
                    "What prototyping and design validation methods will be used?"
                ],
                "tester": [
                    "What test cases and scenarios need to be created?",
                    "How will test data be generated and managed?",
                    "What testing tools and frameworks will be used?",
                    "How will bugs be tracked and prioritized?",
                    "What performance and load testing is required?"
                ],
                "business_analyst": [
                    "What are the detailed functional requirements?",
                    "How will business rules and validation logic work?",
                    "What data migration and import processes are needed?",
                    "How will user permissions and access control work?",
                    "What integration points with other systems are required?"
                ],
                "devops": [
                    "What CI/CD pipelines and automation are needed?",
                    "How will different environments be configured and managed?",
                    "What security scanning and compliance checks are required?",
                    "How will database migrations and updates be handled?",
                    "What logging and monitoring strategies will be implemented?"
                ]
            },
            "implementation": [
                "What technologies and frameworks should be used?",
                "How should the codebase be organized and structured?", 
                "What deployment and infrastructure approach is needed?",
                "How will you monitor and maintain the application?",
                "What documentation and support materials are required?"
            ]
        }

    @require_authentication
    @require_project_access
    @log_agent_action
    def _generate_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate context-aware questions based on role and phase"""
        project_id = data.get('project_id')  # Initialize early
        username = data.get('username')      # Initialize early
        
        try:
            role = data.get('role', 'developer')
            phase = data.get('phase', 'discovery')
            mode = data.get('mode', 'dynamic')

            # Validate role
            if role not in self.role_definitions:
                self.logger.warning(f"Invalid role specified: {role}")
                raise ValidationError(f"Invalid role: {role}. Must be one of: {list(self.role_definitions.keys())}")

            # Get project context
            project = self.db_service.projects.get_by_id(project_id)
            if not project:
                self.logger.warning(f"Project not found: {project_id}")
                raise ValidationError("Project not found")

            # Analyze conversation history for context
            conversation_context = self._analyze_conversation_context(project)

            # Generate question based on mode
            if mode == 'dynamic' and self.claude_client:
                question = self._generate_dynamic_question(project, role, phase, conversation_context)
            else:
                question = self._select_static_question(role, phase, conversation_context)

            # Track question for learning optimization
            self._track_question_usage(role, phase, question)

            # Generate follow-up suggestions
            follow_ups = self._generate_follow_ups(role, phase, conversation_context)

            # Emit question generation event
            if self.events:
                self.events.emit('question_generated', 'socratic_counselor', {
                    'project_id': project_id,
                    'role': role,
                    'phase': phase,
                    'mode': mode,
                    'question_length': len(question),
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                })

            self.logger.info(f"Question generated for project {project_id}, role {role}, phase {phase}")

            return {
                'success': True,
                'question': question,
                'role': role,
                'phase': phase,
                'mode': mode,
                'context': conversation_context,
                'follow_up_suggestions': follow_ups,
                'generated_at': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error generating question for project {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to generate question: {str(e)}")

    def _analyze_conversation_context(self, project: Project) -> Dict[str, Any]:
        """Analyze conversation history to understand current context"""
        try:
            context = {
                'project_phase': project.phase.value if hasattr(project.phase, 'value') else str(project.phase),
                'conversation_length': len(getattr(project, 'conversation_history', [])),
                'topics_covered': [],
                'gaps_identified': [],
                'last_role': None,
                'question_count_by_role': {},
                'sentiment': 'neutral'
            }

            conversation_history = getattr(project, 'conversation_history', [])
            
            if not conversation_history:
                context['gaps_identified'] = ['No conversation history available']
                return context

            # Analyze recent conversation patterns
            recent_messages = conversation_history[-10:]  # Last 10 messages
            
            for message in recent_messages:
                # Extract role information
                role = getattr(message, 'role', None) or getattr(message, 'author_role', None)
                if role:
                    context['last_role'] = role
                    context['question_count_by_role'][role] = context['question_count_by_role'].get(role, 0) + 1

                # Extract content insights
                content = getattr(message, 'content', '')
                if content:
                    # Simple keyword analysis for topics
                    if any(keyword in content.lower() for keyword in ['api', 'database', 'data']):
                        if 'technical_architecture' not in context['topics_covered']:
                            context['topics_covered'].append('technical_architecture')
                    
                    if any(keyword in content.lower() for keyword in ['user', 'interface', 'design']):
                        if 'user_experience' not in context['topics_covered']:
                            context['topics_covered'].append('user_experience')
                    
                    if any(keyword in content.lower() for keyword in ['test', 'quality', 'bug']):
                        if 'quality_assurance' not in context['topics_covered']:
                            context['topics_covered'].append('quality_assurance')

            # Identify potential gaps
            role_coverage = set(context['question_count_by_role'].keys())
            all_roles = set(self.role_definitions.keys())
            missing_roles = all_roles - role_coverage
            
            if missing_roles:
                context['gaps_identified'].append(f"Missing perspectives: {', '.join(missing_roles)}")

            if len(context['topics_covered']) < 3:
                context['gaps_identified'].append("Limited topic coverage - consider broader exploration")

            return context

        except Exception as e:
            self.logger.warning(f"Error analyzing conversation context: {e}")
            return {
                'project_phase': 'unknown',
                'conversation_length': 0,
                'topics_covered': [],
                'gaps_identified': ['Context analysis failed'],
                'last_role': None,
                'question_count_by_role': {},
                'sentiment': 'neutral'
            }

    def _generate_dynamic_question(self, project: Project, role: str, phase: str, context: Dict[str, Any]) -> str:
        """Use Claude to generate contextually relevant questions"""
        try:
            role_def = self.role_definitions.get(role, {})

            prompt = f"""
            Generate a thoughtful question as a {role} for a {phase} phase conversation.

            Project Context: {getattr(project, 'description', 'No description available')}
            Current Phase: {phase}
            Role Focus Areas: {role_def.get('focus', [])}
            Question Style: {role_def.get('question_style', 'general')}
            Key Concerns: {role_def.get('key_concerns', [])}

            Conversation Context: {json.dumps(context, indent=2)}

            Generate ONE specific, actionable question that will help gather 
            the most valuable information for moving the project forward.

            Question should be:
            - Specific to the {role} role and {phase} phase
            - Based on the conversation context and gaps identified
            - Designed to uncover important details not yet discussed
            - Clear and easy to understand
            - Actionable and focused

            Return only the question, no explanation.
            """

            try:
                response = self.claude_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                question = response.content[0].text.strip()
                if question:
                    return question
                else:
                    self.logger.warning("Claude returned empty question, falling back to static")
                    return self._select_static_question(role, phase, context)
                    
            except Exception as e:
                self.logger.warning(f"Claude API error, falling back to static questions: {e}")
                return self._select_static_question(role, phase, context)

        except Exception as e:
            self.logger.error(f"Error in dynamic question generation: {e}")
            return self._select_static_question(role, phase, context)

    def _select_static_question(self, role: str, phase: str, context: Dict[str, Any]) -> str:
        """Select appropriate static question based on role, phase, and context"""
        try:
            # Get questions for the role and phase
            phase_questions = self.question_templates.get(phase, {})
            role_questions = phase_questions.get(role, [])
            
            if not role_questions:
                # Fallback to general implementation questions
                role_questions = self.question_templates.get('implementation', [])
            
            if not role_questions:
                # Ultimate fallback
                return f"What are the key {role} considerations for the {phase} phase of this project?"

            # Try to select question based on context
            topics_covered = context.get('topics_covered', [])
            
            # Filter out questions related to already covered topics (simple keyword matching)
            unused_questions = []
            for question in role_questions:
                question_lower = question.lower()
                is_related_to_covered_topic = any(
                    topic.replace('_', ' ') in question_lower 
                    for topic in topics_covered
                )
                if not is_related_to_covered_topic:
                    unused_questions.append(question)
            
            # Use unused questions if available, otherwise use all questions
            available_questions = unused_questions if unused_questions else role_questions
            
            # Select question (random for now, could be made smarter)
            selected_question = random.choice(available_questions)
            
            self.logger.debug(f"Selected static question for {role}/{phase}: {selected_question[:50]}...")
            return selected_question

        except Exception as e:
            self.logger.error(f"Error selecting static question: {e}")
            return f"What are the key {role} considerations for the {phase} phase of this project?"

    def _generate_follow_ups(self, role: str, phase: str, context: Dict[str, Any]) -> List[str]:
        """Generate follow-up question suggestions"""
        try:
            role_def = self.role_definitions.get(role, {})
            focus_areas = role_def.get('focus', [])
            
            follow_ups = []
            
            # Generate role-specific follow-ups
            for focus_area in focus_areas[:3]:  # Limit to top 3 focus areas
                follow_up = f"Can you elaborate on the {focus_area.replace('_', ' ')} requirements?"
                follow_ups.append(follow_up)
            
            # Add phase-specific follow-ups
            if phase == 'discovery':
                follow_ups.extend([
                    "Are there any constraints or limitations we should consider?",
                    "What potential risks or challenges do you foresee?"
                ])
            elif phase == 'analysis':
                follow_ups.extend([
                    "How will this integrate with existing systems?",
                    "What are the success criteria for this component?"
                ])
            elif phase == 'implementation':
                follow_ups.extend([
                    "What documentation will be needed?",
                    "How will this be tested and validated?"
                ])

            return follow_ups[:5]  # Limit to 5 follow-ups

        except Exception as e:
            self.logger.warning(f"Error generating follow-ups: {e}")
            return ["Can you provide more details?", "What other considerations are important?"]

    def _track_question_usage(self, role: str, phase: str, question: str):
        """Track question effectiveness for learning optimization"""
        try:
            key = f"{role}_{phase}"
            if key not in self.learning_patterns:
                self.learning_patterns[key] = {
                    'questions_asked': [],
                    'effectiveness_scores': [],
                    'user_feedback': []
                }

            self.learning_patterns[key]['questions_asked'].append({
                'question': question,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            })

            # Keep only recent entries to prevent memory bloat
            if len(self.learning_patterns[key]['questions_asked']) > 100:
                self.learning_patterns[key]['questions_asked'] = \
                    self.learning_patterns[key]['questions_asked'][-50:]

            self.logger.debug(f"Tracked question usage for {role}/{phase}")

        except Exception as e:
            self.logger.warning(f"Error tracking question usage: {e}")

    @require_authentication
    @require_project_access
    @log_agent_action
    def _process_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user response and generate insights"""
        project_id = data.get('project_id')  # Initialize early
        username = data.get('username')      # Initialize early
        
        try:
            response_text = data.get('response')
            question_context = data.get('question_context', {})

            if not response_text or not response_text.strip():
                self.logger.warning("Empty response text provided")
                raise ValidationError("Response text is required")

            project = self.db_service.projects.get_by_id(project_id)
            if not project:
                self.logger.warning(f"Project not found: {project_id}")
                raise ValidationError("Project not found")

            # Create conversation message
            message = ConversationMessage(
                project_id=project_id,
                timestamp=DateTimeHelper.now(),  # Rule #7: Use DateTimeHelper
                message_type='user',
                content=response_text,
                phase=project.phase.value if hasattr(project.phase, 'value') else str(project.phase),
                author=username,
                role=question_context.get('role'),
                question_number=len(getattr(project, 'conversation_history', [])) + 1,
                insights_extracted={}
            )

            # Analyze response for insights
            insights = self._extract_response_insights(response_text, question_context)
            message.insights_extracted = insights

            # Add to conversation history
            if not hasattr(project, 'conversation_history'):
                project.conversation_history = []
            project.conversation_history.append(message)

            # Update project context based on response
            self._update_project_context(project, response_text, insights)

            # Save updated project
            success = self.db_service.projects.update(project)
            if not success:
                self.logger.error(f"Failed to update project with response: {project_id}")
                raise Exception("Failed to save response to project")

            # Generate next question suggestions
            next_suggestions = self._suggest_next_questions(insights, question_context)

            # Emit response processing event
            if self.events:
                self.events.emit('response_processed', 'socratic_counselor', {
                    'project_id': project_id,
                    'username': username,
                    'response_length': len(response_text),
                    'insights_count': len(insights),
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                })

            self.logger.info(f"Response processed for project {project_id}, insights: {len(insights)}")

            return {
                'success': True,
                'insights': insights,
                'next_question_suggestions': next_suggestions,
                'context_updates': True,
                'message_id': getattr(message, 'id', len(project.conversation_history)),
                'processed_at': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error processing response for project {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to process response: {str(e)}")

    def _extract_response_insights(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from user response using Claude or basic analysis"""
        try:
            if self.claude_client:
                return self._extract_claude_insights(response, context)
            else:
                return self._extract_basic_insights(response)
        except Exception as e:
            self.logger.warning(f"Error extracting insights, using basic analysis: {e}")
            return self._extract_basic_insights(response)

    def _extract_claude_insights(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights using Claude API"""
        try:
            prompt = f"""
            Analyze this user response for key insights and information:

            Response: {response}
            Question Context: {json.dumps(context, indent=2)}

            Extract insights in these categories:
            1. Requirements - specific functional or non-functional requirements mentioned
            2. Technical - technology preferences, constraints, or architectural decisions
            3. Business - business needs, priorities, or constraints
            4. Risks - potential challenges, concerns, or risk factors
            5. Clarifications - areas that need follow-up or are unclear

            Return as JSON with these exact keys: requirements, technical, business, risks, clarifications
            Each should be an array of specific insights extracted from the response.
            """

            response_obj = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            insights_text = response_obj.content[0].text.strip()
            
            # Try to parse as JSON
            try:
                insights = json.loads(insights_text)
                # Validate structure
                required_keys = ['requirements', 'technical', 'business', 'risks', 'clarifications']
                if all(key in insights for key in required_keys):
                    return insights
                else:
                    self.logger.warning("Claude insights missing required keys, using basic analysis")
                    return self._extract_basic_insights(response)
            except json.JSONDecodeError:
                self.logger.warning("Claude insights not valid JSON, using basic analysis")
                return self._extract_basic_insights(response)

        except Exception as e:
            self.logger.warning(f"Claude insight extraction failed: {e}")
            return self._extract_basic_insights(response)

    def _extract_basic_insights(self, response: str) -> Dict[str, Any]:
        """Extract basic insights using keyword analysis"""
        try:
            response_lower = response.lower()
            
            insights = {
                'requirements': [],
                'technical': [],
                'business': [],
                'risks': [],
                'clarifications': []
            }

            # Basic keyword-based insight extraction
            if any(word in response_lower for word in ['need', 'must', 'should', 'require', 'want']):
                insights['requirements'].append("User expressed specific needs or requirements")

            if any(word in response_lower for word in ['api', 'database', 'server', 'framework', 'technology']):
                insights['technical'].append("Technical preferences or constraints mentioned")

            if any(word in response_lower for word in ['business', 'money', 'cost', 'budget', 'revenue']):
                insights['business'].append("Business considerations discussed")

            if any(word in response_lower for word in ['risk', 'problem', 'issue', 'concern', 'worry']):
                insights['risks'].append("Potential risks or concerns identified")

            if any(word in response_lower for word in ['not sure', 'unclear', 'maybe', 'depends']):
                insights['clarifications'].append("Areas needing clarification identified")

            # Add response length insight
            if len(response) < 50:
                insights['clarifications'].append("Response was brief - may need follow-up")
            elif len(response) > 500:
                insights['requirements'].append("Detailed response provided - rich information available")

            return insights

        except Exception as e:
            self.logger.error(f"Error in basic insight extraction: {e}")
            return {
                'requirements': [],
                'technical': [],
                'business': [],
                'risks': [],
                'clarifications': ["Insight extraction failed"]
            }

    def _update_project_context(self, project: Project, response: str, insights: Dict[str, Any]):
        """Update project context based on response insights"""
        try:
            # Update project requirements if insights found
            requirements = insights.get('requirements', [])
            if requirements:
                existing_requirements = getattr(project, 'requirements', [])
                # Add new requirements (simple implementation)
                for req in requirements:
                    if req not in existing_requirements:
                        existing_requirements.append(req)
                project.requirements = existing_requirements

            # Update technology stack if technical insights found
            technical = insights.get('technical', [])
            if technical and 'Technical preferences' in technical[0]:
                # This is a basic implementation - could be more sophisticated
                existing_tech = getattr(project, 'technology_stack', {})
                if not existing_tech:
                    project.technology_stack = {'preferences': 'User provided technical input'}

            # Update constraints if risks identified
            risks = insights.get('risks', [])
            if risks:
                existing_constraints = getattr(project, 'constraints', [])
                for risk in risks:
                    constraint = f"Risk consideration: {risk}"
                    if constraint not in existing_constraints:
                        existing_constraints.append(constraint)
                project.constraints = existing_constraints

            # Update timestamp
            project.updated_at = DateTimeHelper.now()  # Rule #7: Use DateTimeHelper

            self.logger.debug(f"Updated project context based on insights")

        except Exception as e:
            self.logger.warning(f"Error updating project context: {e}")

    def _suggest_next_questions(self, insights: Dict[str, Any], question_context: Dict[str, Any]) -> List[str]:
        """Suggest next questions based on insights and context"""
        try:
            suggestions = []
            
            # Suggest based on clarifications needed
            clarifications = insights.get('clarifications', [])
            if clarifications:
                suggestions.append("Can you provide more details on the areas that were unclear?")
            
            # Suggest based on risks identified
            risks = insights.get('risks', [])
            if risks:
                suggestions.append("How would you like to address the risks and concerns mentioned?")
            
            # Suggest role-specific follow-ups
            current_role = question_context.get('role', 'developer')
            role_def = self.role_definitions.get(current_role, {})
            focus_areas = role_def.get('focus', [])
            
            if focus_areas:
                next_focus = random.choice(focus_areas)
                suggestions.append(f"What are your thoughts on {next_focus.replace('_', ' ')} for this project?")
            
            # Suggest different role perspective
            all_roles = list(self.role_definitions.keys())
            other_roles = [r for r in all_roles if r != current_role]
            if other_roles:
                next_role = random.choice(other_roles)
                suggestions.append(f"From a {next_role.replace('_', ' ')} perspective, what should we consider?")

            return suggestions[:3]  # Limit to 3 suggestions

        except Exception as e:
            self.logger.warning(f"Error generating next question suggestions: {e}")
            return ["What other aspects should we explore?", "Are there any other considerations?"]

    @require_authentication
    @require_project_access
    @log_agent_action
    def _analyze_conversation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze complete conversation for patterns and insights"""
        project_id = data.get('project_id')  # Initialize early
        
        try:
            analysis_type = data.get('type', 'comprehensive')  # comprehensive, patterns, gaps

            project = self.db_service.projects.get_by_id(project_id)
            if not project:
                self.logger.warning(f"Project not found for conversation analysis: {project_id}")
                raise ValidationError("Project not found")

            conversation_history = getattr(project, 'conversation_history', [])
            
            if not conversation_history:
                return {
                    'success': True,
                    'analysis_type': analysis_type,
                    'total_messages': 0,
                    'insights': {'message': 'No conversation history to analyze'},
                    'recommendations': ['Start asking questions to gather requirements']
                }

            # Perform analysis based on type
            if analysis_type == 'comprehensive':
                analysis = self._perform_comprehensive_analysis(conversation_history)
            elif analysis_type == 'patterns':
                analysis = self._analyze_conversation_patterns(conversation_history)
            elif analysis_type == 'gaps':
                analysis = self._identify_conversation_gaps(conversation_history)
            else:
                analysis = self._perform_basic_analysis(conversation_history)

            self.logger.info(f"Conversation analysis completed for project {project_id}: {analysis_type}")

            return {
                'success': True,
                'project_id': project_id,
                'analysis_type': analysis_type,
                'total_messages': len(conversation_history),
                'analysis': analysis,
                'analyzed_at': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error analyzing conversation for project {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to analyze conversation: {str(e)}")

    def _perform_comprehensive_analysis(self, conversation_history: List) -> Dict[str, Any]:
        """Perform comprehensive conversation analysis"""
        try:
            analysis = {
                'message_count': len(conversation_history),
                'role_distribution': {},
                'phase_coverage': {},
                'insight_summary': {
                    'requirements': [],
                    'technical': [],
                    'business': [],
                    'risks': [],
                    'clarifications': []
                },
                'conversation_quality': 'unknown',
                'completeness_score': 0.0,
                'recommendations': []
            }

            # Analyze role distribution
            for message in conversation_history:
                role = getattr(message, 'role', 'unknown')
                analysis['role_distribution'][role] = analysis['role_distribution'].get(role, 0) + 1

            # Analyze phase coverage
            for message in conversation_history:
                phase = getattr(message, 'phase', 'unknown')
                analysis['phase_coverage'][phase] = analysis['phase_coverage'].get(phase, 0) + 1

            # Aggregate insights
            for message in conversation_history:
                insights = getattr(message, 'insights_extracted', {})
                for category, items in insights.items():
                    if category in analysis['insight_summary'] and items:
                        analysis['insight_summary'][category].extend(items)

            # Calculate completeness score
            role_count = len(analysis['role_distribution'])
            phase_count = len(analysis['phase_coverage'])
            insight_count = sum(len(items) for items in analysis['insight_summary'].values())
            
            # Simple scoring algorithm
            analysis['completeness_score'] = min(100.0, (role_count * 10) + (phase_count * 15) + (insight_count * 2))

            # Generate recommendations
            if role_count < 3:
                analysis['recommendations'].append("Consider gathering input from more role perspectives")
            if insight_count < 10:
                analysis['recommendations'].append("Ask more detailed questions to gather comprehensive requirements")
            if analysis['completeness_score'] > 80:
                analysis['recommendations'].append("Good conversation coverage - ready to move to next phase")

            # Determine conversation quality
            if analysis['completeness_score'] > 80:
                analysis['conversation_quality'] = 'excellent'
            elif analysis['completeness_score'] > 60:
                analysis['conversation_quality'] = 'good'
            elif analysis['completeness_score'] > 40:
                analysis['conversation_quality'] = 'fair'
            else:
                analysis['conversation_quality'] = 'needs_improvement'

            return analysis

        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            return {'error': str(e), 'message_count': len(conversation_history)}

    def _analyze_conversation_patterns(self, conversation_history: List) -> Dict[str, Any]:
        """Analyze conversation patterns and trends"""
        try:
            patterns = {
                'question_response_ratio': 0.0,
                'average_response_length': 0.0,
                'role_switching_frequency': 0,
                'engagement_trend': 'stable',
                'topic_progression': []
            }

            if not conversation_history:
                return patterns

            # Calculate basic metrics
            total_length = sum(len(getattr(msg, 'content', '')) for msg in conversation_history)
            patterns['average_response_length'] = total_length / len(conversation_history)

            # Analyze role switching
            roles = [getattr(msg, 'role', 'unknown') for msg in conversation_history]
            role_switches = sum(1 for i in range(1, len(roles)) if roles[i] != roles[i-1])
            patterns['role_switching_frequency'] = role_switches

            # Simple engagement trend analysis
            if len(conversation_history) >= 4:
                recent_lengths = [len(getattr(msg, 'content', '')) for msg in conversation_history[-4:]]
                early_lengths = [len(getattr(msg, 'content', '')) for msg in conversation_history[:4]]
                
                recent_avg = sum(recent_lengths) / len(recent_lengths)
                early_avg = sum(early_lengths) / len(early_lengths)
                
                if recent_avg > early_avg * 1.2:
                    patterns['engagement_trend'] = 'increasing'
                elif recent_avg < early_avg * 0.8:
                    patterns['engagement_trend'] = 'decreasing'

            return patterns

        except Exception as e:
            self.logger.error(f"Error analyzing conversation patterns: {e}")
            return {'error': str(e)}

    def _identify_conversation_gaps(self, conversation_history: List) -> Dict[str, Any]:
        """Identify gaps in conversation coverage"""
        try:
            gaps = {
                'missing_roles': [],
                'missing_phases': [],
                'missing_topics': [],
                'recommendations': []
            }

            # Identify missing roles
            covered_roles = set()
            for message in conversation_history:
                role = getattr(message, 'role', None)
                if role:
                    covered_roles.add(role)
            
            all_roles = set(self.role_definitions.keys())
            gaps['missing_roles'] = list(all_roles - covered_roles)

            # Identify missing phases
            covered_phases = set()
            for message in conversation_history:
                phase = getattr(message, 'phase', None)
                if phase:
                    covered_phases.add(phase)
            
            important_phases = {'discovery', 'analysis', 'design'}
            gaps['missing_phases'] = list(important_phases - covered_phases)

            # Generate recommendations based on gaps
            if gaps['missing_roles']:
                gaps['recommendations'].append(f"Consider input from: {', '.join(gaps['missing_roles'])}")
            
            if gaps['missing_phases']:
                gaps['recommendations'].append(f"Explore phases: {', '.join(gaps['missing_phases'])}")
            
            if not gaps['missing_roles'] and not gaps['missing_phases']:
                gaps['recommendations'].append("Good coverage across roles and phases")

            return gaps

        except Exception as e:
            self.logger.error(f"Error identifying conversation gaps: {e}")
            return {'error': str(e)}

    def _perform_basic_analysis(self, conversation_history: List) -> Dict[str, Any]:
        """Perform basic conversation analysis"""
        try:
            return {
                'message_count': len(conversation_history),
                'total_characters': sum(len(getattr(msg, 'content', '')) for msg in conversation_history),
                'unique_roles': len(set(getattr(msg, 'role', 'unknown') for msg in conversation_history)),
                'summary': f"Conversation contains {len(conversation_history)} messages"
            }
        except Exception as e:
            self.logger.error(f"Error in basic analysis: {e}")
            return {'error': str(e)}

    def _error_response(self, error_message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
        """Create standardized error response"""
        response = {
            'success': False,
            'error': error_message,
            'agent_id': self.agent_id,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }
        
        if error_code:
            response['error_code'] = error_code
            
        return response
