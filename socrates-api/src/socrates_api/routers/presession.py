"""
Pre-Session Chat API endpoints.

Provides REST endpoints for free-form conversation with Claude before a project is selected.
Allows users to ask questions and explore the system without project commitment.
"""

import logging
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, status, Depends

from socrates_api.auth import get_current_user
from socrates_api.models import SuccessResponse

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


class PreSessionQuestion(BaseModel):
    """Pre-session Q&A request"""
    question: str
    context: Optional[dict] = None


class PreSessionAnswer(BaseModel):
    """Pre-session Q&A response"""
    answer: str
    has_context: bool


@router.post(
    "/ask",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question during pre-session chat",
)
async def ask_question(
    request: PreSessionQuestion,
    current_user: str = Depends(get_current_user),
):
    """
    Ask a direct question and get an answer from Claude.

    Works without a project - allows free-form conversation before project selection.

    Args:
        request: PreSessionQuestion with question text
        current_user: Authenticated user

    Returns:
        SuccessResponse with answer
    """
    try:
        if not request.question or not request.question.strip():
            return SuccessResponse(
                message="Please provide a question.",
                data={"answer": "I'm ready to help. What would you like to know?", "has_context": False}
            )

        question = request.question.strip()
        logger.info(f"Pre-session question from user {current_user}: '{question}'")

        # Get orchestrator for Claude access
        orchestrator = _get_orchestrator()

        # Search knowledge base for relevant context (optional)
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

        # Build prompt for Claude
        prompt = _build_answer_prompt(question, relevant_context)

        # Get answer from Claude
        answer = orchestrator.claude_client.generate_response(prompt)

        return SuccessResponse(
            message="Answer generated successfully",
            data={
                "answer": answer,
                "has_context": bool(relevant_context)
            }
        )

    except Exception as e:
        logger.error(f"Error generating answer: {e}", exc_info=True)
        return SuccessResponse(
            message="Error generating answer",
            data={
                "answer": "I encountered an error processing your question. Please try again.",
                "has_context": False
            }
        )


def _build_answer_prompt(question: str, context: str) -> str:
    """Build prompt for Claude to answer pre-session questions"""
    relevant_knowledge = ""
    if context:
        relevant_knowledge = f"""
Relevant Knowledge:
{context}
"""

    return f"""You are a helpful assistant for Socrates - an AI-powered Socratic tutoring system.

You are assisting a user who is exploring the system before starting a project or learning session.

{relevant_knowledge}

User Question: {question}

Provide a clear, helpful, and concise answer. Be friendly and encouraging.
If you don't have enough information, offer to help in other ways."""
