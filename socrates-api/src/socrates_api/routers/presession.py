"""
Pre-Session Chat API endpoints.

Provides REST endpoints for free-form conversation with Claude before a project is selected.
Allows users to ask questions, explore the system, track conversation history, and get
project recommendations based on conversation context.

Features:
- Conversation history tracking per session
- Context-aware responses based on conversation history
- Command execution suggestions (e.g., /hint, /help, /create_project)
- Project recommendations based on inferred topics and interests
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, status, Depends

from socrates_api.auth import get_current_user
from socrates_api.models import SuccessResponse

# Import rate limiter if available
try:
    from socrates_api.main import limiter
except ImportError:
    limiter = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/presession", tags=["presession"])


def _get_orchestrator():
    """Get the global orchestrator instance for agent-based processing."""
    # Import here to avoid circular imports
    from socrates_api.main import app_state

    if app_state.get("orchestrator") is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized. Call /initialize first."
        )
    return app_state["orchestrator"]


def _get_database():
    """Get the database instance."""
    from socrates_api.main import app_state

    if app_state.get("database") is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not initialized."
        )
    return app_state["database"]


class PreSessionQuestion(BaseModel):
    """Pre-session Q&A request"""
    question: str
    session_id: Optional[str] = None  # Optional session ID for continuing conversation
    context: Optional[dict] = None


class PreSessionAnswer(BaseModel):
    """Pre-session Q&A response"""
    answer: str
    has_context: bool
    session_id: str
    suggested_commands: Optional[List[str]] = None
    topics_detected: Optional[List[str]] = None


class PresessionSession(BaseModel):
    """Presession session information"""
    session_id: str
    started_at: str
    last_activity: str
    message_count: int
    user_messages: int
    assistant_messages: int


class ProjectRecommendation(BaseModel):
    """Recommended project based on conversation"""
    name: str
    description: str
    suggested_phase: str
    topic_match: float  # 0-1 confidence score
    reason: str


async def _extract_conversation_topics(conversation_history: List[Dict]) -> List[str]:
    """
    Extract topics/intents from conversation history using Claude.

    Args:
        conversation_history: List of messages with role and content

    Returns:
        List of detected topics (e.g., ['web development', 'python', 'database design'])
    """
    try:
        if not conversation_history or len(conversation_history) < 2:
            return []

        # Build conversation text
        conversation_text = "\n".join(
            [f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
             for msg in conversation_history[-10:]]  # Last 10 messages for context
        )

        orchestrator = _get_orchestrator()

        # Extract topics via Claude
        prompt = f"""Analyze this conversation and extract 2-5 main topics or areas of interest.
Focus on technical topics, learning goals, and project types mentioned.

Conversation:
{conversation_text}

Return ONLY a JSON array of topics (strings), like: ["web development", "python", "database design"]"""

        response = orchestrator.claude_client.generate_response(prompt)

        # Parse JSON response
        import json
        try:
            topics = json.loads(response)
            return topics if isinstance(topics, list) else []
        except json.JSONDecodeError:
            # If Claude's response isn't valid JSON, return empty list
            logger.warning(f"Failed to parse topics from Claude response: {response}")
            return []

    except Exception as e:
        logger.warning(f"Could not extract conversation topics: {e}")
        return []


async def _generate_command_suggestions(
    conversation_history: List[Dict], topics: List[str]
) -> List[str]:
    """
    Generate suggested commands based on conversation topics.

    Args:
        conversation_history: User's conversation messages
        topics: Extracted topics from conversation

    Returns:
        List of suggested commands (e.g., ['/create_project', '/hint', '/help'])
    """
    available_commands = {
        "web development": ["/hint web-framework", "/help api-design"],
        "python": ["/hint python-best-practices", "/help python-testing"],
        "database": ["/hint database-design", "/help sql-optimization"],
        "backend": ["/hint backend-architecture", "/help api-design"],
        "frontend": ["/hint ui-patterns", "/help responsive-design"],
        "mobile": ["/hint mobile-architecture", "/help native-vs-cross-platform"],
        "machine learning": ["/hint ml-workflow", "/help model-training"],
        "devops": ["/hint deployment-strategy", "/help docker-kubernetes"],
    }

    suggested = set()

    # Match topics to commands
    for topic in topics:
        topic_lower = topic.lower()
        for command_topic, commands in available_commands.items():
            if command_topic in topic_lower:
                suggested.update(commands)

    # Always include general help commands
    suggested.add("/help")
    suggested.add("/status")

    return list(suggested)[:5]  # Return up to 5 suggestions


@router.post(
    "/ask",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question during pre-session chat with conversation history",
)
@(limiter.limit("20/minute") if limiter else lambda f: f)  # PRESESSION_LIMIT: 20 per minute
async def ask_question(
    request: PreSessionQuestion,
    current_user: str = Depends(get_current_user),
) -> SuccessResponse:
    """
    Ask a question and get an answer with conversation history tracking.

    Features:
    - Tracks conversation history per session
    - Provides context-aware responses based on conversation history
    - Suggests relevant commands based on detected topics
    - Recommends projects based on inferred interests

    Args:
        request: PreSessionQuestion with question text and optional session_id
        current_user: Authenticated username

    Returns:
        SuccessResponse with answer, session_id, suggested_commands, and detected_topics

    Example:
        ```python
        # First message in session
        response = await ask_question(
            PreSessionQuestion(question="How do I build a web app?"),
            current_user="john_doe"
        )
        session_id = response.data["session_id"]

        # Continue session with same session_id
        response = await ask_question(
            PreSessionQuestion(
                question="What framework should I use?",
                session_id=session_id
            ),
            current_user="john_doe"
        )
        ```
    """
    try:
        if not request.question or not request.question.strip():
            return SuccessResponse(
                message="Please provide a question.",
                data={
                    "answer": "I'm ready to help. What would you like to know?",
                    "has_context": False,
                    "session_id": str(uuid.uuid4()),
                    "suggested_commands": [],
                    "topics_detected": []
                }
            )

        question = request.question.strip()

        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(
            f"Pre-session question from user {current_user} in session {session_id}: '{question}'"
        )

        # Get database and orchestrator
        db = _get_database()
        orchestrator = _get_orchestrator()

        # Load conversation history for context
        conversation_history = db.get_presession_conversation(current_user, session_id, limit=50)

        # Search knowledge base for relevant context
        relevant_context = ""
        try:
            if orchestrator.vector_db:
                knowledge_results = orchestrator.vector_db.search_similar(question, top_k=3)
                if knowledge_results:
                    relevant_context = "\n".join(
                        [f"- {result.get('content', '')[:200]}..." for result in knowledge_results]
                    )
        except Exception as e:
            logger.warning(f"Could not search knowledge base: {e}")

        # Build prompt with conversation history context
        prompt = _build_answer_prompt(question, relevant_context, conversation_history)

        # Get answer from Claude
        answer = orchestrator.claude_client.generate_response(prompt)

        # Save user question to conversation history
        db.save_presession_message(
            username=current_user,
            session_id=session_id,
            message_type="user",
            content=question,
            metadata={"has_knowledge_context": bool(relevant_context)},
        )

        # Save assistant answer to conversation history
        db.save_presession_message(
            username=current_user,
            session_id=session_id,
            message_type="assistant",
            content=answer,
            metadata={"has_knowledge_context": bool(relevant_context)},
        )

        # Extract topics and generate command suggestions
        topics = await _extract_conversation_topics(conversation_history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ])
        suggested_commands = await _generate_command_suggestions(
            conversation_history + [{"role": "user", "content": question}],
            topics
        )

        logger.info(
            f"Detected topics in presession: {topics}, "
            f"suggested commands: {suggested_commands}"
        )

        return SuccessResponse(
            message="Answer generated successfully",
            data={
                "answer": answer,
                "has_context": bool(relevant_context),
                "session_id": session_id,
                "suggested_commands": suggested_commands,
                "topics_detected": topics,
            }
        )

    except Exception as e:
        logger.error(f"Error in presession ask_question: {e}", exc_info=True)
        return SuccessResponse(
            message="Error generating answer",
            data={
                "answer": "I encountered an error processing your question. Please try again.",
                "has_context": False,
                "session_id": request.session_id or str(uuid.uuid4()),
                "suggested_commands": [],
                "topics_detected": [],
            }
        )


def _build_answer_prompt(
    question: str, context: str, conversation_history: Optional[List[Dict]] = None
) -> str:
    """
    Build prompt for Claude to answer pre-session questions with conversation context.

    Args:
        question: User's current question
        context: Relevant knowledge base context
        conversation_history: Previous messages in this session

    Returns:
        Formatted prompt for Claude
    """
    relevant_knowledge = ""
    if context:
        relevant_knowledge = f"""
Relevant Knowledge:
{context}
"""

    conversation_context = ""
    if conversation_history and len(conversation_history) > 0:
        # Include last 5 messages for context
        recent_messages = conversation_history[-5:]
        conversation_text = "\n".join(
            [f"{msg.get('role', 'unknown').title()}: {msg.get('content', '')}"
             for msg in recent_messages]
        )
        conversation_context = f"""
Previous conversation context:
{conversation_text}
"""

    return f"""You are a helpful assistant for Socrates - an AI-powered Socratic tutoring system.

You are assisting a user who is exploring the system before starting a project or learning session.
Be aware of the previous conversation context to provide coherent, contextual answers.

{conversation_context}
{relevant_knowledge}

User Question: {question}

Provide a clear, helpful, and concise answer. Be friendly and encouraging.
Reference previous parts of the conversation when relevant.
If you don't have enough information, offer to help in other ways.
Suggest next steps they might take in their learning journey."""


@router.get(
    "/sessions",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="List user's pre-session conversation sessions",
)
async def list_presession_sessions(
    current_user: str = Depends(get_current_user),
) -> SuccessResponse:
    """
    List all presession conversation sessions for the current user.

    Returns sessions with metadata including message counts, timestamps, and activity info.

    Args:
        current_user: Authenticated username

    Returns:
        SuccessResponse with list of PresessionSession objects

    Example:
        ```python
        response = await list_presession_sessions(current_user="john_doe")
        sessions = response.data["sessions"]
        for session in sessions:
            print(f"Session {session.session_id}: {session.message_count} messages")
        ```
    """
    try:
        db = _get_database()

        sessions = db.get_presession_sessions(current_user, limit=50)

        logger.info(f"Retrieved {len(sessions)} presession sessions for user {current_user}")

        return SuccessResponse(
            message="Sessions retrieved successfully",
            data={
                "sessions": [
                    {
                        "session_id": s["session_id"],
                        "started_at": s["started_at"],
                        "last_activity": s["last_activity"],
                        "message_count": s["message_count"],
                        "user_messages": s["user_messages"],
                        "assistant_messages": s["assistant_messages"],
                    }
                    for s in sessions
                ]
            },
        )

    except Exception as e:
        logger.error(f"Error listing presession sessions for {current_user}: {e}", exc_info=True)
        return SuccessResponse(
            message="Error retrieving sessions",
            data={"sessions": []},
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific presession conversation session",
)
async def get_presession_session(
    session_id: str,
    current_user: str = Depends(get_current_user),
) -> SuccessResponse:
    """
    Get a specific presession conversation session with all messages.

    Args:
        session_id: Session identifier
        current_user: Authenticated username

    Returns:
        SuccessResponse with conversation history

    Example:
        ```python
        response = await get_presession_session(session_id="abc-123", current_user="john_doe")
        messages = response.data["messages"]
        for msg in messages:
            print(f"{msg['role']}: {msg['content']}")
        ```
    """
    try:
        db = _get_database()

        conversation = db.get_presession_conversation(current_user, session_id, limit=100)

        logger.info(
            f"Retrieved presession session {session_id} with {len(conversation)} messages "
            f"for user {current_user}"
        )

        return SuccessResponse(
            message="Session retrieved successfully",
            data={
                "session_id": session_id,
                "messages": [
                    {
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg["timestamp"],
                        "metadata": msg.get("metadata", {}),
                    }
                    for msg in conversation
                ],
            },
        )

    except Exception as e:
        logger.error(
            f"Error retrieving presession session {session_id} for {current_user}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving session",
        )


@router.delete(
    "/sessions/{session_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a presession conversation session",
)
async def delete_presession_session(
    session_id: str,
    current_user: str = Depends(get_current_user),
) -> SuccessResponse:
    """
    Delete a presession conversation session and all its messages.

    Args:
        session_id: Session identifier
        current_user: Authenticated username

    Returns:
        SuccessResponse indicating deletion status

    Example:
        ```python
        response = await delete_presession_session(session_id="abc-123", current_user="john_doe")
        ```
    """
    try:
        db = _get_database()

        success = db.delete_presession_session(current_user, session_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        logger.info(f"Deleted presession session {session_id} for user {current_user}")

        return SuccessResponse(
            message="Session deleted successfully",
            data={"session_id": session_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting presession session {session_id} for {current_user}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting session",
        )


@router.get(
    "/recommendations",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project recommendations based on presession conversations",
)
async def get_project_recommendations(
    session_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
) -> SuccessResponse:
    """
    Get project recommendations based on analyzed presession conversation topics.

    Analyzes the user's conversation to extract topics and interests,
    then recommends relevant project templates and starting phases.

    Args:
        session_id: Optional specific session to analyze (analyzes all if not provided)
        current_user: Authenticated username

    Returns:
        SuccessResponse with list of ProjectRecommendation objects

    Example:
        ```python
        response = await get_project_recommendations(
            session_id="abc-123",
            current_user="john_doe"
        )
        for rec in response.data["recommendations"]:
            print(f"{rec['name']}: {rec['reason']}")
        ```
    """
    try:
        db = _get_database()

        # Load conversation history
        if session_id:
            conversation = db.get_presession_conversation(current_user, session_id)
        else:
            # Analyze all recent sessions
            sessions = db.get_presession_sessions(current_user, limit=5)
            conversation = []
            for s in sessions:
                conv = db.get_presession_conversation(current_user, s["session_id"], limit=20)
                conversation.extend(conv)

        if not conversation:
            return SuccessResponse(
                message="No conversation history found",
                data={"recommendations": []},
            )

        # Extract topics from conversation
        topics = await _extract_conversation_topics(conversation)

        logger.info(f"Extracted topics for recommendations: {topics}")

        # Generate recommendations based on topics
        recommendations = _generate_project_recommendations(topics)

        logger.info(
            f"Generated {len(recommendations)} project recommendations for {current_user}"
        )

        return SuccessResponse(
            message="Recommendations generated successfully",
            data={
                "topics_detected": topics,
                "recommendations": [
                    {
                        "name": rec["name"],
                        "description": rec["description"],
                        "suggested_phase": rec["suggested_phase"],
                        "topic_match": rec["topic_match"],
                        "reason": rec["reason"],
                    }
                    for rec in recommendations
                ],
            },
        )

    except Exception as e:
        logger.error(f"Error generating recommendations for {current_user}: {e}", exc_info=True)
        return SuccessResponse(
            message="Error generating recommendations",
            data={"recommendations": []},
        )


def _generate_project_recommendations(topics: List[str]) -> List[Dict[str, Any]]:
    """
    Generate project recommendations based on detected topics.

    Args:
        topics: List of topics extracted from conversation

    Returns:
        List of recommendation dicts with name, description, phase, etc.
    """
    project_templates = {
        "web development": {
            "name": "Personal Blog Platform",
            "description": "Build a full-stack blog with user authentication and commenting",
            "suggested_phase": "specification",
            "reason": "Perfect introduction to web development fundamentals",
        },
        "python": {
            "name": "Data Processing Pipeline",
            "description": "Create a Python pipeline for analyzing and transforming data",
            "suggested_phase": "specification",
            "reason": "Great for learning Python best practices and data handling",
        },
        "database": {
            "name": "E-commerce Database Design",
            "description": "Design and implement a relational database for an online store",
            "suggested_phase": "design",
            "reason": "Comprehensive database design and optimization exercise",
        },
        "backend": {
            "name": "REST API Backend",
            "description": "Build a RESTful API with proper authentication and validation",
            "suggested_phase": "implementation",
            "reason": "Essential backend development skills",
        },
        "frontend": {
            "name": "Interactive Dashboard",
            "description": "Create a responsive dashboard with real-time data visualization",
            "suggested_phase": "implementation",
            "reason": "Learn modern frontend frameworks and UI patterns",
        },
        "mobile": {
            "name": "Mobile Todo App",
            "description": "Develop a cross-platform todo application with sync",
            "suggested_phase": "specification",
            "reason": "Introduction to mobile app development",
        },
        "machine learning": {
            "name": "Sentiment Analysis Model",
            "description": "Train and deploy an ML model for text classification",
            "suggested_phase": "analysis",
            "reason": "Hands-on machine learning project",
        },
        "devops": {
            "name": "CI/CD Pipeline Setup",
            "description": "Configure automated testing and deployment pipeline",
            "suggested_phase": "review",
            "reason": "Learn modern deployment practices",
        },
    }

    recommendations = []
    seen_names = set()

    # Find matching templates based on topics
    for topic in topics:
        topic_lower = topic.lower()
        for template_key, template in project_templates.items():
            if template_key in topic_lower and template["name"] not in seen_names:
                recommendations.append(
                    {
                        **template,
                        "topic_match": 0.8,  # High confidence for exact matches
                    }
                )
                seen_names.add(template["name"])

    # Add fallback recommendations if none matched
    if not recommendations:
        recommendations.append(
            {
                "name": "Hello World Project",
                "description": "Create your first project to learn Socrates workflow",
                "suggested_phase": "specification",
                "topic_match": 0.5,
                "reason": "Great starting point for any learning journey",
            }
        )

    return recommendations[:5]  # Return up to 5 recommendations
