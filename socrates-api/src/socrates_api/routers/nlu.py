"""
Natural Language Understanding (NLU) API endpoints for Socrates.

Provides REST endpoints for interpreting natural language input and translating
it into structured commands. Enables pre-session chat and command discovery.

Features:
- AI-powered intent recognition via Claude
- Entity extraction from user input
- Context-aware command suggestions
- Semantic understanding beyond keyword matching
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from socrates_api.auth import get_current_user_optional
from socrates_api.models import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nlu", tags=["nlu"])


class CommandSuggestionResponse(BaseModel):
    """Single command suggestion from NLU interpreter"""

    command: str
    confidence: float
    reasoning: str
    args: List[str] = []


class NLUInterpretRequest(BaseModel):
    """Request to interpret natural language input"""

    input: str = Field(..., min_length=1, description="Natural language input to interpret")
    context: Optional[dict] = Field(None, description="Optional context dict")


class NLUInterpretResponse(BaseModel):
    """Response from NLU interpretation"""

    status: str  # "success", "suggestions", "no_match", or "error"
    command: Optional[str] = None
    suggestions: Optional[List[CommandSuggestionResponse]] = None
    message: str
    entities: Optional[Dict[str, Any]] = None
    intent: Optional[str] = None


async def _extract_entities(text: str, context: Optional[dict] = None, user_id: str = None, user_auth_method: str = "api_key") -> Dict[str, Any]:
    """
    Extract entities from user input using Claude AI.

    Args:
        text: User input text
        context: Optional context about the project
        user_id: Optional user ID for user-specific API key
        user_auth_method: User's preferred auth method

    Returns:
        Dictionary of extracted entities (action, object, parameters, etc.)
    """
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()

        prompt = f"""Analyze this user input and extract structured entities.

User input: "{text}"

Extract the following in JSON format:
{{
    "action": "the main action (analyze, create, test, fix, etc.) or null if none",
    "object": "the object being acted upon (project, code, docs, etc.) or null",
    "parameters": ["list of additional parameters or arguments"],
    "intent_category": "one of: project, code, docs, collaboration, chat, system, query",
    "confidence": 0.0-1.0 confidence in the extraction
}}

Respond ONLY with valid JSON."""

        response = orchestrator.claude_client.generate_response(prompt, user_auth_method=user_auth_method, user_id=user_id)

        try:
            entities = json.loads(response)
            logger.debug(f"Extracted entities: {entities}")
            return entities
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse entity extraction response: {response}")
            return {
                "action": None,
                "object": None,
                "parameters": [],
                "intent_category": "query",
                "confidence": 0.0,
            }
    except Exception as e:
        logger.warning(f"Error extracting entities: {str(e)}")
        return {
            "action": None,
            "object": None,
            "parameters": [],
            "intent_category": "query",
            "confidence": 0.0,
        }


async def _get_ai_command_suggestions(
    text: str, context: Optional[dict] = None, user_id: str = None, user_auth_method: str = "api_key"
) -> List[Dict[str, Any]]:
    """
    Get AI-powered command suggestions using Claude.

    Args:
        text: User input text
        context: Optional context about the project
        user_id: Optional user ID for user-specific API key
        user_auth_method: User's preferred auth method

    Returns:
        List of suggested commands with reasoning
    """
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()

        # Build context string for better suggestions
        context_str = ""
        if context:
            if context.get("project_name"):
                context_str += f"Project: {context['project_name']}\n"
            if context.get("current_phase"):
                context_str += f"Current Phase: {context['current_phase']}\n"
            if context.get("recent_actions"):
                context_str += f"Recent Actions: {', '.join(context['recent_actions'])}\n"

        prompt = f"""Based on this user request, suggest the most relevant commands.

{context_str}
User request: "{text}"

Available commands:
- /project analyze: Analyze project structure
- /project test: Run tests
- /project fix: Apply fixes
- /code generate: Generate code
- /code docs: Generate documentation
- /docs import: Import documentation
- /advance: Move to next phase
- /status: Show project status
- /help: Show help
- /hint: Get a hint
- /skipped: View and reopen skipped questions
- /search: Search conversations
- /summary: Get conversation summary

Respond with JSON:
{{
    "suggestions": [
        {{
            "command": "/command_name",
            "confidence": 0.0-1.0,
            "reasoning": "why this command matches",
            "args": ["any", "arguments"]
        }}
    ]
}}

Respond ONLY with valid JSON."""

        response = orchestrator.claude_client.generate_response(prompt, user_auth_method=user_auth_method, user_id=user_id)

        try:
            result = json.loads(response)
            suggestions = result.get("suggestions", [])
            # Sort by confidence and limit to top 5
            suggestions.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            logger.debug(f"AI suggestions: {suggestions[:5]}")
            return suggestions[:5]
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse AI suggestions: {response}")
            return []
    except Exception as e:
        logger.warning(f"Error getting AI suggestions: {str(e)}")
        return []


@router.post(
    "/interpret",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Interpret natural language input with AI",
)
async def interpret_input(
    request: NLUInterpretRequest,
    current_user: Optional[str] = Depends(get_current_user_optional),
):
    """
    Interpret natural language input and return command suggestions using AI.

    This endpoint provides AI-powered intent recognition, entity extraction, and
    context-aware command suggestions. It uses Claude for semantic understanding
    beyond simple keyword matching. Also saves dialogue as project notes if project_id provided.

    Args:
        request: NLUInterpretRequest with input string and optional context
        current_user: Authenticated user

    Returns:
        SuccessResponse with interpreted commands, suggestions, and extracted entities
    """
    try:
        if not request.input or not request.input.strip():
            return APIResponse(
                success=False,
                status="error",
                message="Please enter a command or question.",
                data={
                    "status": "error",
                    "message": "Please enter a command or question.",
                    "entities": None,
                    "intent": None,
                },
            )

        # Save NLU dialogue as project note if project_id provided
        project_id = request.context.get("project_id") if request.context else None
        if project_id and current_user:
            try:
                from socrates_api.database import get_database

                db = get_database()
                project = db.load_project(project_id)
                if project:
                    # Create note from NLU input
                    note_content = f"[NLU] {request.input}"
                    if not project.notes:
                        project.notes = []
                    project.notes.append({"timestamp": str(datetime.now()), "content": note_content})
                    db.save_project(project)
                    logger.debug(f"Saved NLU dialogue as note for project {project_id}")
            except Exception as e:
                logger.debug(f"Could not save NLU dialogue as note: {str(e)}")
                # Don't fail the request if note saving fails

        user_input = request.input.strip()
        user_input_lower = user_input.lower()
        user_id_str = current_user if current_user else "free_session"
        logger.info(f"NLU interpretation request from user {user_id_str}: '{request.input}'")

        # Get user's auth method if logged in
        user_auth_method = "api_key"
        if current_user:
            from socrates_api.database import get_database
            db = get_database()
            user_obj = db.load_user(current_user)
            if user_obj and hasattr(user_obj, 'claude_auth_method'):
                user_auth_method = user_obj.claude_auth_method or "api_key"

        # Check if input is a direct command (starts with /)
        if user_input.startswith("/"):
            # Direct command - return as-is
            logger.debug(f"Direct command detected: {user_input}")
            return APIResponse(
                success=True,
                status="success",
                message=f"Understood! Executing: {user_input}",
                data={
                    "status": "success",
                    "command": user_input,
                    "message": f"Understood! Executing: {user_input}",
                    "entities": None,
                    "intent": "direct_command",
                },
            )

        # Try AI-powered interpretation first
        logger.debug("Using AI-powered NLU interpretation")

        # Extract entities using Claude
        entities = await _extract_entities(user_input, request.context, user_id=current_user, user_auth_method=user_auth_method)
        intent = entities.get("intent_category", "query")
        entity_confidence = entities.get("confidence", 0.0)

        # Get AI suggestions if confidence is moderate or higher
        ai_suggestions = []
        if entity_confidence >= 0.3:
            ai_suggestions = await _get_ai_command_suggestions(user_input, request.context, user_id=current_user, user_auth_method=user_auth_method)

            # Format AI suggestions properly
            if ai_suggestions:
                logger.info(f"AI suggestions for '{user_input}': {len(ai_suggestions)} suggestions")
                return APIResponse(
                    success=True,
                    status="success",
                    message="I found some relevant commands:",
                    data={
                        "status": "suggestions",
                        "suggestions": ai_suggestions[:3],
                        "message": "I found some relevant commands:",
                        "entities": entities,
                        "intent": intent,
                    },
                )

        # Fall back to keyword-based matching if AI confidence is low
        logger.debug("Falling back to keyword-based matching")
        command_map = {
            "analyze": "/project analyze",
            "test": "/project test",
            "fix": "/project fix",
            "validate": "/project validate",
            "review": "/project review",
            "help": "/help",
            "info": "/info",
            "status": "/status",
            "debug": "/debug",
            "hint": "/hint",
            "done": "/done",
            "advance": "/advance",
            "notes": "/note list",
            "documents": "/docs list",
            "docs": "/docs",
            "skills": "/skills list",
            "collaborators": "/collab list",
            "search": "/conversation search",
            "summary": "/conversation summary",
            "generate code": "/code generate",
            "generate docs": "/code docs",
            "subscription": "/subscription",
            "mode": "/mode",
            "model": "/model",
            "nlu": "/nlu",
            "menu": "/menu",
            "clear": "/clear",
            "exit": "/exit",
            "back": "/back",
            "maturity": "/maturity",
            "analytics": "/analytics",
        }

        # Find matching commands
        suggestions = []
        matched_command = None

        for phrase, command in command_map.items():
            if phrase in user_input_lower:
                confidence = 0.9 if phrase in user_input_lower else 0.5
                if phrase in user_input_lower and len(phrase.split()) == len(
                    user_input_lower.split()
                ):
                    # Exact match
                    matched_command = command
                    confidence = 0.95
                else:
                    # Partial match
                    suggestions.append(
                        {
                            "command": command,
                            "confidence": confidence,
                            "reasoning": f"Matched keyword: {phrase}",
                            "args": [],
                        }
                    )

        # If exact match found, return it
        if matched_command:
            logger.info(f"Exact keyword match: {matched_command}")
            return APIResponse(
                success=True,
                status="success",
                message=f"Understood! Executing: {matched_command}",
                data={
                    "status": "success",
                    "command": matched_command,
                    "message": f"Understood! Executing: {matched_command}",
                    "entities": entities,
                    "intent": intent,
                },
            )

        # If suggestions found, return them
        if suggestions:
            # Sort by confidence
            suggestions.sort(key=lambda x: x["confidence"], reverse=True)
            logger.info(f"Found {len(suggestions)} keyword-based suggestions")
            return APIResponse(
                success=True,
                status="success",
                message="Did you mean one of these?",
                data={
                    "status": "suggestions",
                    "suggestions": suggestions[:3],
                    "message": "Did you mean one of these?",
                    "entities": entities,
                    "intent": intent,
                },
            )

        # No match found
        logger.info(f"No match found for input: {user_input}")
        return APIResponse(
            success=False,
            status="error",
            message="I didn't understand that. Try describing what you want or typing a command like /help",
            data={
                "status": "no_match",
                "message": "I didn't understand that. Try:\n• Describing what you want (analyze, test, fix, etc.)\n• Typing a command like /help\n• Selecting a project from the dropdown",
                "entities": entities,
                "intent": intent,
            },
        )

    except Exception as e:
        logger.error(f"Error interpreting input: {str(e)}", exc_info=True)
        return APIResponse(
            success=False,
            status="error",
            message=f"Error processing your request: {str(e)}",
            error_code="nlu_processing_error",
            data={
                "status": "error",
                "message": f"Error processing your request: {str(e)}",
                "entities": None,
                "intent": None,
            },
        )


@router.get(
    "/commands",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get list of available commands",
)
async def get_available_commands(
    current_user: Optional[str] = Depends(get_current_user_optional),
):
    """
    Get list of all available commands for command discovery.

    Returns a structured list of all commands organized by category.
    Useful for showing users what commands are available without needing
    to type '/help'.

    Args:
        current_user: Authenticated user

    Returns:
        SuccessResponse with commands organized by category

    Example:
        Response:
        ```json
        {
            "status": "success",
            "data": {
                "commands": {
                    "system": [
                        {
                            "name": "help",
                            "usage": "help",
                            "description": "Show help and available commands",
                            "aliases": ["h", "?"]
                        }
                    ],
                    "project": [
                        {
                            "name": "project create",
                            "usage": "project create [name]",
                            "description": "Create a new project",
                            "aliases": []
                        }
                    ]
                }
            }
        }
        ```
    """
    try:
        user_id_str = current_user if current_user else "free_session"
        logger.info(f"Available commands requested by user: {user_id_str}")

        # Static list of available commands organized by category
        commands_by_category = {
            "system": [
                {
                    "name": "help",
                    "usage": "/help",
                    "description": "Show help and available commands",
                    "aliases": ["h", "?"],
                },
                {
                    "name": "status",
                    "usage": "/status",
                    "description": "Show current status",
                    "aliases": [],
                },
                {
                    "name": "info",
                    "usage": "/info",
                    "description": "Show system information",
                    "aliases": [],
                },
            ],
            "project": [
                {
                    "name": "project analyze",
                    "usage": "/project analyze",
                    "description": "Analyze project structure",
                    "aliases": [],
                },
                {
                    "name": "project test",
                    "usage": "/project test",
                    "description": "Run tests",
                    "aliases": [],
                },
                {
                    "name": "project fix",
                    "usage": "/project fix",
                    "description": "Apply fixes",
                    "aliases": [],
                },
                {
                    "name": "project validate",
                    "usage": "/project validate",
                    "description": "Validate project",
                    "aliases": [],
                },
                {
                    "name": "project review",
                    "usage": "/project review",
                    "description": "Code review",
                    "aliases": [],
                },
            ],
            "chat": [
                {
                    "name": "advance",
                    "usage": "/advance",
                    "description": "Advance to next phase",
                    "aliases": [],
                },
                {"name": "done", "usage": "/done", "description": "Finish session", "aliases": []},
                {
                    "name": "ask",
                    "usage": "/ask <question>",
                    "description": "Ask a question",
                    "aliases": [],
                },
                {"name": "hint", "usage": "/hint", "description": "Get a hint", "aliases": []},
                {"name": "skipped", "usage": "/skipped", "description": "View and reopen skipped questions", "aliases": []},
                {
                    "name": "explain",
                    "usage": "/explain <topic>",
                    "description": "Explain a concept",
                    "aliases": [],
                },
            ],
            "docs": [
                {
                    "name": "docs import",
                    "usage": "/docs import",
                    "description": "Import file",
                    "aliases": [],
                },
                {
                    "name": "docs import-url",
                    "usage": "/docs import-url <url>",
                    "description": "Import from URL",
                    "aliases": [],
                },
                {
                    "name": "docs list",
                    "usage": "/docs list",
                    "description": "List documents",
                    "aliases": [],
                },
                {
                    "name": "code generate",
                    "usage": "/code generate",
                    "description": "Generate code",
                    "aliases": [],
                },
                {
                    "name": "code docs",
                    "usage": "/code docs",
                    "description": "Generate documentation",
                    "aliases": [],
                },
            ],
            "collaboration": [
                {
                    "name": "collab add",
                    "usage": "/collab add <username>",
                    "description": "Add collaborator",
                    "aliases": [],
                },
                {
                    "name": "collab list",
                    "usage": "/collab list",
                    "description": "List collaborators",
                    "aliases": [],
                },
                {
                    "name": "collab remove",
                    "usage": "/collab remove <username>",
                    "description": "Remove collaborator",
                    "aliases": [],
                },
                {
                    "name": "skills list",
                    "usage": "/skills list",
                    "description": "List skills",
                    "aliases": [],
                },
                {
                    "name": "note list",
                    "usage": "/note list",
                    "description": "List notes",
                    "aliases": [],
                },
            ],
            "subscription": [
                {
                    "name": "subscription status",
                    "usage": "/subscription status",
                    "description": "Show subscription status",
                    "aliases": [],
                },
                {
                    "name": "subscription upgrade",
                    "usage": "/subscription upgrade <plan>",
                    "description": "Upgrade subscription",
                    "aliases": [],
                },
                {
                    "name": "subscription compare",
                    "usage": "/subscription compare",
                    "description": "Compare plans",
                    "aliases": [],
                },
            ],
        }

        return APIResponse(
            success=True,
            status="success",
            message="Available commands retrieved successfully",
            data={"commands": commands_by_category},
        )

    except Exception as e:
        logger.error(f"Error retrieving commands: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available commands",
        )


@router.get(
    "/suggestions",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get context-aware command suggestions",
)

async def get_context_aware_suggestions(
    project_id: Optional[str] = None,
    current_phase: Optional[str] = None,
    current_user: Optional[str] = Depends(get_current_user_optional),
):
    """
    Get command suggestions based on current project context.

    This endpoint uses project context (current phase, recent actions) to
    suggest the most relevant commands for the user's current workflow.

    Args:
        project_id: Optional project ID for context
        current_phase: Optional current phase (specification, analysis, design, etc.)
        current_user: Authenticated user

    Returns:
        SuccessResponse with context-aware command suggestions

    Example:
        Request: GET /nlu/suggestions?project_id=proj-123&current_phase=analysis

        Response:
        ```json
        {
            "status": "success",
            "data": {
                "suggestions": [
                    {
                        "command": "/project analyze",
                        "reasoning": "Relevant for analysis phase",
                        "priority": "high"
                    },
                    {
                        "command": "/code generate",
                        "reasoning": "Common next step after analysis",
                        "priority": "medium"
                    }
                ]
            }
        }
        ```
    """
    try:
        user_id_str = current_user if current_user else "free_session"
        logger.info(
            f"Context-aware suggestions requested by {user_id_str} "
            f"for project {project_id}, phase {current_phase}"
        )

        # Map phases to suggested commands
        phase_command_map = {
            "specification": [
                {
                    "command": "/hint",
                    "reasoning": "Get guidance on project specification",
                    "priority": "high",
                },
                {
                    "command": "/help",
                    "reasoning": "Learn about available features",
                    "priority": "medium",
                },
                {
                    "command": "/advance",
                    "reasoning": "Move to next phase when ready",
                    "priority": "medium",
                },
            ],
            "analysis": [
                {
                    "command": "/project analyze",
                    "reasoning": "Analyze project requirements and structure",
                    "priority": "high",
                },
                {
                    "command": "/code generate",
                    "reasoning": "Generate code templates based on analysis",
                    "priority": "medium",
                },
                {
                    "command": "/summary",
                    "reasoning": "Review conversation summary",
                    "priority": "low",
                },
            ],
            "design": [
                {
                    "command": "/code generate",
                    "reasoning": "Generate design documentation",
                    "priority": "high",
                },
                {
                    "command": "/code docs",
                    "reasoning": "Create API documentation",
                    "priority": "high",
                },
                {
                    "command": "/project review",
                    "reasoning": "Get design review feedback",
                    "priority": "medium",
                },
            ],
            "implementation": [
                {
                    "command": "/project test",
                    "reasoning": "Run tests and validate implementation",
                    "priority": "high",
                },
                {
                    "command": "/project fix",
                    "reasoning": "Apply fixes for issues",
                    "priority": "high",
                },
                {
                    "command": "/code generate",
                    "reasoning": "Generate additional code sections",
                    "priority": "medium",
                },
            ],
            "review": [
                {
                    "command": "/project review",
                    "reasoning": "Conduct code review",
                    "priority": "high",
                },
                {
                    "command": "/project test",
                    "reasoning": "Verify all tests pass",
                    "priority": "high",
                },
                {
                    "command": "/advance",
                    "reasoning": "Move to next phase after review",
                    "priority": "medium",
                },
            ],
            "deployment": [
                {
                    "command": "/project validate",
                    "reasoning": "Validate deployment readiness",
                    "priority": "high",
                },
                {
                    "command": "/status",
                    "reasoning": "Check deployment status",
                    "priority": "medium",
                },
                {"command": "/done", "reasoning": "Complete the project", "priority": "medium"},
            ],
        }

        # Get suggestions for current phase
        suggestions = phase_command_map.get(
            current_phase.lower() if current_phase else "specification", []
        )

        # Always include general commands
        general_commands = [
            {"command": "/help", "reasoning": "View all available commands", "priority": "low"},
            {"command": "/status", "reasoning": "Check current project status", "priority": "low"},
        ]

        # Combine phase-specific and general commands
        all_suggestions = suggestions + general_commands

        logger.info(f"Returning {len(all_suggestions)} context-aware suggestions")

        return APIResponse(
            success=True,
            status="success",
            message=f"Suggestions for {current_phase or 'specification'} phase",
            data={
                "suggestions": all_suggestions,
                "phase": current_phase or "specification",
                "project_id": project_id,
            },
        )

    except Exception as e:
        logger.error(f"Error getting context-aware suggestions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get context-aware suggestions",
        )
