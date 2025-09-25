"""
Socratic RAG Enhanced - Socratic Counselor Agent
===============================================

Enhanced Socratic questioning agent with role-based intelligence.
Handles all 7 role types, context-aware questioning, and learning.
"""

import json
import random
from typing import Any, Dict, List

from src.core import DateTimeHelper
from src.models import ConversationMessage, UserRole
from .base import BaseAgent, require_project_access, log_agent_action


class SocraticCounselorAgent(BaseAgent):
    """
    Enhanced Socratic questioning agent with role-based intelligence

    Absorbs: Role-awareness and management from RoleManagerAgent
    Capabilities: All 7 role types, context-aware questioning, learning
    """

    def __init__(self):
        super().__init__("socratic_counselor", "Socratic Counselor")
        self.role_definitions = self._load_role_definitions()
        self.question_templates = self._load_question_templates()
        self.learning_patterns = {}

    def get_capabilities(self) -> List[str]:
        return [
            "generate_question", "process_response", "analyze_conversation",
            "role_based_questioning", "context_adaptation", "learning_optimization",
            "conflict_mediation", "insight_extraction", "session_guidance"
        ]

    def _load_role_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load definitions for all 7 role types"""
        return {
            "project_manager": {
                "focus": ["timeline", "resources", "stakeholders", "risks", "deliverables"],
                "question_style": "strategic",
                "priorities": ["feasibility", "scope", "constraints"]
            },
            "technical_lead": {
                "focus": ["architecture", "technology", "scalability", "performance", "security"],
                "question_style": "technical_depth",
                "priorities": ["design_patterns", "best_practices", "integration"]
            },
            "developer": {
                "focus": ["implementation", "algorithms", "data_structures", "apis", "debugging"],
                "question_style": "implementation_focused",
                "priorities": ["code_quality", "maintainability", "testing"]
            },
            "designer": {
                "focus": ["user_experience", "interface_design", "accessibility", "usability"],
                "question_style": "user_centered",
                "priorities": ["user_flows", "responsive_design", "brand_consistency"]
            },
            "qa_tester": {
                "focus": ["quality_assurance", "edge_cases", "validation", "automation"],
                "question_style": "quality_focused",
                "priorities": ["test_coverage", "reliability", "performance_testing"]
            },
            "business_analyst": {
                "focus": ["requirements", "business_rules", "compliance", "reporting"],
                "question_style": "requirements_driven",
                "priorities": ["stakeholder_needs", "process_optimization", "metrics"]
            },
            "devops_engineer": {
                "focus": ["deployment", "infrastructure", "monitoring", "automation"],
                "question_style": "operations_focused",
                "priorities": ["scalability", "reliability", "security", "cost_optimization"]
            }
        }

    def _load_question_templates(self) -> Dict[str, List[str]]:
        """Load question templates for different contexts"""
        return {
            "discovery": [
                "What is the primary problem you're trying to solve with this application?",
                "Who are your target users and what are their main pain points?",
                "What would success look like for this project?",
                "What existing solutions have you tried and why didn't they work?",
                "What are your non-negotiable requirements vs. nice-to-have features?"
            ],
            "analysis": [
                "How do you envision users interacting with this application?",
                "What data needs to be stored, processed, and retrieved?",
                "What external systems or services need to be integrated?",
                "What are the performance and scalability requirements?",
                "What security and compliance considerations are important?"
            ],
            "design": [
                "How should the application be structured and organized?",
                "What are the key components and how do they interact?",
                "What design patterns would be most appropriate?",
                "How should errors and edge cases be handled?",
                "What testing strategy should be implemented?"
            ],
            "implementation": [
                "What technologies and frameworks should be used?",
                "How should the codebase be organized and structured?",
                "What deployment and infrastructure approach is needed?",
                "How will you monitor and maintain the application?",
                "What documentation and support materials are required?"
            ]
        }

    @require_project_access
    @log_agent_action
    def _generate_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate context-aware questions based on role and phase"""
        project_id = data.get('project_id')
        role = data.get('role', 'developer')
        phase = data.get('phase', 'discovery')
        mode = data.get('mode', 'dynamic')

        # Get project context
        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        # Analyze conversation history
        conversation_context = self._analyze_conversation_context(project)

        if mode == 'dynamic' and self.claude_client:
            question = self._generate_dynamic_question(project, role, phase, conversation_context)
        else:
            question = self._select_static_question(role, phase, conversation_context)

        # Learn from question effectiveness
        self._track_question_usage(role, phase, question)

        return {
            'question': question,
            'role': role,
            'phase': phase,
            'context': conversation_context,
            'follow_up_suggestions': self._generate_follow_ups(role, phase)
        }

    def _generate_dynamic_question(self, project, role: str, phase: str, context: Dict[str, Any]) -> str:
        """Use Claude to generate contextually relevant questions"""
        role_def = self.role_definitions.get(role, {})

        prompt = f"""
        Generate a thoughtful question as a {role} for a {phase} phase conversation.

        Project Context: {project.description}
        Current Phase: {phase}
        Role Focus Areas: {role_def.get('focus', [])}
        Question Style: {role_def.get('question_style', 'general')}

        Conversation Context: {json.dumps(context, indent=2)}

        Generate ONE specific, actionable question that will help gather 
        the most valuable information for moving the project forward.

        Question should be:
        - Specific to the role and phase
        - Based on the conversation context
        - Designed to uncover important details
        - Clear and easy to understand

        Return only the question, no explanation.
        """

        response = self.call_claude(prompt)
        return response.strip().strip('"\'')

    def _select_static_question(self, role: str, phase: str, context: Dict[str, Any]) -> str:
        """Select from pre-defined question templates"""
        phase_questions = self.question_templates.get(phase, [])
        if not phase_questions:
            return "What would you like to focus on next?"

        # Simple selection based on context or random
        return random.choice(phase_questions)

    def _analyze_conversation_context(self, project) -> Dict[str, Any]:
        """Analyze conversation history for context"""
        recent_entries = project.conversation_history[-10:] if project.conversation_history else []

        context = {
            'total_interactions': len(project.conversation_history),
            'recent_topics': [],
            'answered_questions': [],
            'gaps_identified': [],
            'user_preferences': {}
        }

        for entry in recent_entries:
            if entry.type == 'assistant':
                context['recent_topics'].append(entry.content[:100])
            elif entry.type == 'user':
                context['answered_questions'].append(entry.content[:100])

        return context

    def _generate_follow_ups(self, role: str, phase: str) -> List[str]:
        """Generate potential follow-up questions"""
        role_def = self.role_definitions.get(role, {})
        priorities = role_def.get('priorities', [])

        follow_ups = []
        for priority in priorities[:3]:  # Top 3 priorities
            follow_ups.append(f"Can you elaborate on {priority.replace('_', ' ')} requirements?")

        return follow_ups

    def _track_question_usage(self, role: str, phase: str, question: str):
        """Track question effectiveness for learning"""
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

    @require_project_access
    @log_agent_action
    def _process_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user response and generate insights"""
        project_id = data.get('project_id')
        response_text = data.get('response')
        question_context = data.get('question_context', {})

        if not response_text:
            raise ValueError("Response text is required")

        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        # Create conversation message
        message = ConversationMessage(
            type='user',
            content=response_text,
            phase=project.phase,
            author=project.owner  # Simplified - assume owner is responding
        )

        # Add to conversation history
        project.conversation_history.append(message)

        # Analyze response for insights
        insights = self._extract_response_insights(response_text, question_context)
        message.insights_extracted = insights

        # Update project context based on response
        self._update_project_context(project, response_text, insights)

        # Save updated project
        self.db.projects.update(project)

        return {
            'insights': insights,
            'next_question_suggestions': self._suggest_next_questions(insights),
            'context_updates': True
        }

    def _extract_response_insights(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from user response using Claude"""
        if not self.claude_client:
            return self._extract_basic_insights(response)

        prompt = f"""
        Analyze this user response for key insights and information:

        Response: {response}
        Question Context: {json.dumps(context, indent=2)}

        Extract:
        1. Key requirements mentioned
        2. Technical constraints or preferences  
        3. Business needs and priorities
        4. Potential risks or challenges
        5. Unclear areas needing follow-up

        Return as structured JSON with these categories.
        """

        claude_response = self.call_claude(prompt)

        try:
            return json.loads(claude_response)
        except:
            return self._extract_basic_insights(response)

    def _extract_basic_insights(self, response: str) -> Dict[str, Any]:
        """Basic insight extraction without Claude"""
        return {
            'requirements': [response],
            'constraints': [],
            'priorities': [],
            'risks': [],
            'follow_up_needed': []
        }

    def _suggest_next_questions(self, insights: Dict[str, Any]) -> List[str]:
        """Suggest next questions based on response insights"""
        suggestions = []

        if insights.get('follow_up_needed'):
            suggestions.extend([
                f"Can you clarify: {item}?"
                for item in insights['follow_up_needed'][:2]
            ])

        if insights.get('risks'):
            suggestions.append("How would you like to address the potential risks mentioned?")

        if len(suggestions) < 3:
            suggestions.append("What aspect would you like to explore in more detail?")

        return suggestions

    def _update_project_context(self, project, response: str, insights: Dict[str, Any]):
        """Update project context based on new insights"""
        # Add requirements from insights
        if insights.get('requirements'):
            project.requirements.extend(insights['requirements'])

        # Add constraints
        if insights.get('constraints'):
            project.constraints.extend(insights['constraints'])

        # Update context summary
        project.context_summary.update({
            'last_response_insights': insights,
            'total_responses': len([msg for msg in project.conversation_history if msg.type == 'user']),
            'updated_at': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        })

        project.updated_at = DateTimeHelper.now()

    @require_project_access
    def _analyze_conversation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation patterns and provide insights"""
        project_id = data.get('project_id')

        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        conversation_data = project.conversation_history or []

        analysis = {
            'total_interactions': len(conversation_data),
            'response_quality': self._assess_response_quality(conversation_data),
            'topic_coverage': self._analyze_topic_coverage(conversation_data),
            'user_engagement': self._measure_engagement(conversation_data),
            'information_gaps': self._identify_information_gaps(conversation_data),
            'recommendations': []
        }

        # Generate recommendations
        if analysis['response_quality']['score'] < 50:
            analysis['recommendations'].append("Encourage more detailed responses")

        if len(analysis['information_gaps']) > 0:
            analysis['recommendations'].append("Address identified information gaps")

        return analysis

    def _assess_response_quality(self, conversation_data: List[ConversationMessage]) -> Dict[str, Any]:
        """Assess quality of user responses"""
        if not conversation_data:
            return {'score': 0, 'analysis': 'No conversation data'}

        # Simple quality metrics
        total_responses = len([entry for entry in conversation_data if entry.type == 'user'])
        detailed_responses = len([
            entry for entry in conversation_data
            if entry.type == 'user' and len(entry.content) > 50
        ])

        quality_score = (detailed_responses / total_responses * 100) if total_responses > 0 else 0

        return {
            'score': quality_score,
            'total_responses': total_responses,
            'detailed_responses': detailed_responses,
            'analysis': 'Good detail' if quality_score > 70 else 'Needs more detail'
        }

    def _analyze_topic_coverage(self, conversation_data: List[ConversationMessage]) -> Dict[str, Any]:
        """Analyze topic coverage in conversation"""
        topics = {
            'requirements': 0,
            'technical': 0,
            'design': 0,
            'business': 0
        }

        for message in conversation_data:
            content_lower = message.content.lower()
            if any(word in content_lower for word in ['require', 'need', 'must', 'should']):
                topics['requirements'] += 1
            if any(word in content_lower for word in ['api', 'database', 'framework', 'technology']):
                topics['technical'] += 1
            if any(word in content_lower for word in ['user', 'interface', 'design', 'experience']):
                topics['design'] += 1
            if any(word in content_lower for word in ['business', 'revenue', 'customer', 'market']):
                topics['business'] += 1

        return topics

    def _measure_engagement(self, conversation_data: List[ConversationMessage]) -> Dict[str, Any]:
        """Measure user engagement levels"""
        if not conversation_data:
            return {'score': 0, 'trend': 'none'}

        user_messages = [msg for msg in conversation_data if msg.type == 'user']
        if len(user_messages) < 2:
            return {'score': 50, 'trend': 'insufficient_data'}

        # Simple engagement based on message length and frequency
        avg_length = sum(len(msg.content) for msg in user_messages) / len(user_messages)
        engagement_score = min(100, avg_length / 5000)  # Normalize to 0-100

        return {
            'score': engagement_score,
            'trend': 'increasing' if engagement_score > 60 else 'stable',
            'message_count': len(user_messages)
        }

    def _identify_information_gaps(self, conversation_data: List[ConversationMessage]) -> List[str]:
        """Identify information gaps that need addressing"""
        gaps = []
        topics_covered = self._analyze_topic_coverage(conversation_data)

        if topics_covered['requirements'] < 3:
            gaps.append("Insufficient requirements gathering")
        if topics_covered['technical'] < 2:
            gaps.append("Limited technical discussion")
        if topics_covered['design'] < 1:
            gaps.append("No design considerations mentioned")

        return gaps
