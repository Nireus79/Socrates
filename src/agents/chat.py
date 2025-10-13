#!/usr/bin/env python3
"""
Chat Agent - Free-form Conversation Handler
============================================
Handles chat-mode conversations with context-aware responses and project insights.
"""

from typing import Dict, List, Any, Optional

try:
    from src.core import ServiceContainer, DateTimeHelper, ValidationError, ValidationHelper
    from src.models import ChatSession, ConversationMessage, Project, ConversationStatus
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


    class DateTimeHelper:
        @staticmethod
        def now():
            return datetime.now()


    class ValidationError(Exception):
        pass


    class ConversationStatus(Enum):
        ACTIVE = "active"
        PAUSED = "paused"
        COMPLETED = "completed"


class ChatAgent(BaseAgent):
    """
    Free-form chat conversation handler with project context awareness.

    Unlike SocraticCounselor which follows structured Q&A, ChatAgent provides:
    - Natural conversation flow
    - Context-aware responses
    - Project insight extraction
    - Flexible topic switching
    """

    def __init__(self, services: Optional[ServiceContainer] = None):
        super().__init__("chat_agent", "Chat Agent", services)
        self.chat_repo = self.db.chat_sessions if self.db else None
        self.message_repo = self.db.conversation_messages if self.db else None

        # Chat-specific configuration
        self.max_context_messages = 10  # Number of previous messages to include in context
        self.insight_extraction_enabled = True
        self.topic_tracking_enabled = True

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            "start_chat",
            "continue_chat",
            "end_chat",
            "get_chat_history",
            "extract_insights",
            "switch_topic",
            "get_chat_sessions",
            "export_chat_summary"
        ]

    @require_authentication
    @require_project_access
    @log_agent_action
    def _start_chat(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a new chat session

        Args:
            data: {
                'project_id': str,
                'user_id': str,
                'chat_mode': str,  # 'project_focused', 'general', 'brainstorming'
                'initial_context': str,
                'initial_message': str (optional)
            }

        Returns:
            Dict with chat session info and initial response
        """
        try:
            project_id = data.get('project_id')
            user_id = data.get('user_id')
            chat_mode = data.get('chat_mode', 'project_focused')
            initial_context = data.get('initial_context', '')
            initial_message = data.get('initial_message', '')

            if not all([project_id, user_id]):
                return self._error_response("Missing required parameters", "MISSING_PARAMS")

            # Create chat session
            chat_session = ChatSession(
                project_id=project_id,
                user_id=user_id,
                chat_mode=chat_mode,
                conversation_context=initial_context or f"Chat session for project {project_id}"
            )

            if not self.chat_repo.create(chat_session):
                return self._error_response("Failed to create chat session", "CREATION_FAILED")

            # Process initial message if provided
            initial_response = None
            if initial_message:
                # Create user message
                user_message = ConversationMessage(
                    session_id=chat_session.id,
                    project_id=project_id,
                    message_type="user",
                    content=initial_message,
                    conversation_type="chat"
                )
                self.message_repo.create(user_message)

                # Generate AI response
                response_data = self._generate_chat_response(
                    chat_session, initial_message, []
                )
                initial_response = response_data.get('response', '')

                # Create AI message
                ai_message = ConversationMessage(
                    session_id=chat_session.id,
                    project_id=project_id,
                    message_type="assistant",
                    content=initial_response,
                    conversation_type="chat"
                )
                self.message_repo.create(ai_message)

                # Update session
                chat_session.message_count = 2
                chat_session.last_activity = DateTimeHelper.now()
                self.chat_repo.update(chat_session)

            self.logger.info(f"Chat session started: {chat_session.id}")

            return self._success_response(
                "Chat session started successfully",
                {
                    'session_id': chat_session.id,
                    'chat_mode': chat_mode,
                    'initial_response': initial_response,
                    'session_info': {
                        'project_id': project_id,
                        'user_id': user_id,
                        'created_at': DateTimeHelper.to_iso_string(chat_session.created_at),
                        'status': chat_session.status.value if hasattr(chat_session.status, 'value') else str(
                            chat_session.status)
                    }
                }
            )

        except Exception as e:
            self.logger.error(f"Error starting chat session: {e}")
            return self._error_response(f"Failed to start chat: {str(e)}")

    @require_authentication
    @log_agent_action
    def _continue_chat(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Continue an existing chat session

        Args:
            data: {
                'session_id': str,
                'message': str,
                'user_id': str
            }

        Returns:
            Dict with AI response and updated session info
        """
        try:
            session_id = data.get('session_id')
            message = data.get('message')
            user_id = data.get('user_id')

            if not all([session_id, message, user_id]):
                return self._error_response("Missing required parameters", "MISSING_PARAMS")

            # Get chat session
            chat_session = self.chat_repo.get_by_id(session_id)
            if not chat_session:
                return self._error_response("Chat session not found", "SESSION_NOT_FOUND")

            if chat_session.status != ConversationStatus.ACTIVE:
                return self._error_response("Chat session is not active", "SESSION_INACTIVE")

            # Get recent conversation history
            recent_messages = self._get_recent_messages(session_id, self.max_context_messages)

            # Create user message
            user_message = ConversationMessage(
                session_id=session_id,
                project_id=chat_session.project_id,
                message_type="user",
                content=message,
                conversation_type="chat"
            )
            self.message_repo.create(user_message)

            # Generate AI response
            response_data = self._generate_chat_response(
                chat_session, message, recent_messages
            )
            ai_response = response_data.get('response', '')
            insights = response_data.get('insights', {})
            topics = response_data.get('topics', [])

            # Create AI message
            ai_message = ConversationMessage(
                session_id=session_id,
                project_id=chat_session.project_id,
                message_type="assistant",
                content=ai_response,
                conversation_type="chat",
                insights_extracted=insights
            )
            self.message_repo.create(ai_message)

            # Update chat session
            self._update_chat_session(chat_session, insights, topics)

            self.logger.info(f"Chat continued: {session_id}")

            return self._success_response(
                "Chat response generated successfully",
                {
                    'response': ai_response,
                    'session_id': session_id,
                    'message_count': chat_session.message_count,
                    'insights_extracted': len(insights) > 0,
                    'new_topics': topics,
                    'engagement_score': chat_session.engagement_score
                }
            )

        except Exception as e:
            self.logger.error(f"Error continuing chat: {e}")
            return self._error_response(f"Failed to continue chat: {str(e)}")

    @require_authentication
    @log_agent_action
    def _end_chat(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        End a chat session with summary generation

        Args:
            data: {
                'session_id': str,
                'user_id': str,
                'generate_summary': bool (optional)
            }

        Returns:
            Dict with session summary and final status
        """
        try:
            session_id = data.get('session_id')
            user_id = data.get('user_id')
            generate_summary = data.get('generate_summary', True)

            if not all([session_id, user_id]):
                return self._error_response("Missing required parameters", "MISSING_PARAMS")

            # Get and end session
            if not self.chat_repo.end_session(session_id):
                return self._error_response("Failed to end session", "UPDATE_FAILED")

            chat_session = self.chat_repo.get_by_id(session_id)
            if not chat_session:
                return self._error_response("Session not found", "SESSION_NOT_FOUND")

            # Generate summary if requested
            summary = None
            if generate_summary:
                summary = self._generate_chat_summary(chat_session)

            self.logger.info(f"Chat session ended: {session_id}")

            return self._success_response(
                "Chat session ended successfully",
                {
                    'session_id': session_id,
                    'final_message_count': chat_session.message_count,
                    'duration_minutes': chat_session.duration_minutes,
                    'topics_discussed': chat_session.topics_discussed,
                    'insights_generated': len(chat_session.insights_extracted),
                    'summary': summary,
                    'engagement_score': chat_session.engagement_score
                }
            )

        except Exception as e:
            self.logger.error(f"Error ending chat: {e}")
            return self._error_response(f"Failed to end chat: {str(e)}")

    def _generate_chat_response(self, session: ChatSession, message: str,
                                history: List[ConversationMessage]) -> Dict[str, Any]:
        """Generate contextual chat response"""
        try:
            # Build conversation context
            context = self._build_conversation_context(session, history)

            # Create chat prompt
            prompt = self._create_chat_prompt(session, message, context)

            # Get AI response
            # Get Claude service from ServiceContainer
            claude_service = None
            if self.services:
                # Assuming ServiceContainer provides Claude service access
                claude_service = getattr(self.services, 'claude_service', None)

            if claude_service:
                response = claude_service.send_message(
                    message=prompt,
                    conversation_history=[],  # Context is in the prompt
                    temperature=0.7  # More creative for chat
                )
                ai_response = response.content
            else:
                # Fallback response
                ai_response = f"I understand you're asking about: {message}. Let me help you with that in the context of your project."

            # Extract insights and topics
            insights = self._extract_insights_from_response(ai_response) if self.insight_extraction_enabled else {}
            topics = self._extract_topics_from_message(message) if self.topic_tracking_enabled else []

            return {
                'response': ai_response,
                'insights': insights,
                'topics': topics
            }

        except Exception as e:
            self.logger.error(f"Error generating chat response: {e}")
            return {
                'response': "I apologize, but I'm having trouble generating a response right now. Please try again.",
                'insights': {},
                'topics': []
            }

    def _build_conversation_context(self, session: ChatSession,
                                    history: List[ConversationMessage]) -> str:
        """Build conversation context from session and history"""
        context_parts = []

        # Add session context
        if session.conversation_context:
            context_parts.append(f"Session Context: {session.conversation_context}")

        # Add chat mode context
        mode_context = {
            'project_focused': "Focus on helping with project planning, development, and problem-solving.",
            'general': "Engage in open conversation while being helpful and informative.",
            'brainstorming': "Encourage creative thinking and idea generation."
        }
        context_parts.append(mode_context.get(session.chat_mode, mode_context['project_focused']))

        # Add recent conversation history
        if history:
            context_parts.append("Recent conversation:")
            for msg in history[-5:]:  # Last 5 messages for context
                role = "User" if msg.message_type == "user" else "Assistant"
                context_parts.append(f"{role}: {msg.content}")

        return "\n".join(context_parts)

    def _create_chat_prompt(self, session: ChatSession, message: str, context: str) -> str:
        """Create chat prompt for AI"""
        return f"""You are an AI assistant helping with software project development. You're having a natural conversation with a user about their project.

{context}

Current topics discussed: {', '.join(session.topics_discussed) if session.topics_discussed else 'None yet'}

User's current message: {message}

Provide a helpful, conversational response that:
1. Directly addresses the user's message
2. Stays relevant to the project context when appropriate
3. Asks follow-up questions to keep the conversation productive
4. Provides actionable insights when possible

Response:"""

    def _extract_insights_from_response(self, response: str) -> Dict[str, Any]:
        """Extract structured insights from AI response"""
        insights = {}

        # Simple keyword-based insight extraction
        # In production, this could use more sophisticated NLP

        if any(word in response.lower() for word in ['architecture', 'design', 'structure']):
            insights['architecture'] = [{'insight': 'Architecture discussion', 'confidence': 0.7}]

        if any(word in response.lower() for word in ['requirements', 'features', 'functionality']):
            insights['requirements'] = [{'insight': 'Requirements discussion', 'confidence': 0.7}]

        if any(word in response.lower() for word in ['technology', 'framework', 'library', 'stack']):
            insights['technology'] = [{'insight': 'Technology discussion', 'confidence': 0.7}]

        return insights

    def _extract_topics_from_message(self, message: str) -> List[str]:
        """Extract topics from user message"""
        # Simple topic extraction - could be enhanced with NLP
        topics = []

        topic_keywords = {
            'architecture': ['architecture', 'design', 'structure', 'patterns'],
            'database': ['database', 'storage', 'data', 'sql', 'nosql'],
            'frontend': ['frontend', 'ui', 'interface', 'react', 'vue', 'angular'],
            'backend': ['backend', 'api', 'server', 'microservices'],
            'testing': ['testing', 'tests', 'qa', 'quality'],
            'deployment': ['deployment', 'deploy', 'production', 'hosting'],
            'security': ['security', 'authentication', 'authorization', 'encryption']
        }

        message_lower = message.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)

        return topics

    def _update_chat_session(self, session: ChatSession, insights: Dict[str, Any], topics: List[str]) -> None:
        """Update chat session with new insights and topics"""
        try:
            # Update message count and activity
            session.message_count += 2  # User message + AI response
            session.last_activity = DateTimeHelper.now()

            # Add new topics
            for topic in topics:
                session.add_topic(topic)

            # Add insights
            for category, insight_list in insights.items():
                for insight_data in insight_list:
                    session.add_insight(category, insight_data.get('insight', ''))

            # Update engagement score (simple heuristic)
            if topics or insights:
                session.engagement_score = min(1.0, session.engagement_score + 0.1)

            # Save updates
            self.chat_repo.update(session)

        except Exception as e:
            self.logger.error(f"Error updating chat session: {e}")

    def _get_recent_messages(self, session_id: str, limit: int) -> List[ConversationMessage]:
        """Get recent messages for context"""
        try:
            if not self.message_repo:
                return []

            all_messages = self.message_repo.get_by_session_id(session_id)
            return all_messages[-limit:] if all_messages else []

        except Exception as e:
            self.logger.error(f"Error getting recent messages: {e}")
            return []

    def _generate_chat_summary(self, session: ChatSession) -> Dict[str, Any]:
        """Generate summary of chat session"""
        try:
            return {
                'session_id': session.id,
                'duration_minutes': session.duration_minutes,
                'message_count': session.message_count,
                'topics_discussed': session.topics_discussed,
                'key_insights': session.insights_extracted,
                'action_items': session.action_items,
                'decisions_made': session.decisions_made,
                'engagement_score': session.engagement_score,
                'chat_mode': session.chat_mode
            }
        except Exception as e:
            self.logger.error(f"Error generating chat summary: {e}")
            return {'error': 'Failed to generate summary'}
