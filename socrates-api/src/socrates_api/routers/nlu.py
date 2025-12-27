"""
Natural Language Understanding (NLU) API endpoints for Socrates.

Provides REST endpoints for interpreting natural language input and translating
it into structured commands. Enables pre-session chat and command discovery.
"""

import logging
from typing import Optional, List
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, status, Depends

from socrates_api.auth import get_current_user
from socrates_api.models import SuccessResponse

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
    input: str
    context: Optional[dict] = None


class NLUInterpretResponse(BaseModel):
    """Response from NLU interpretation"""
    status: str  # "success", "suggestions", "no_match", or "error"
    command: Optional[str] = None
    suggestions: Optional[List[CommandSuggestionResponse]] = None
    message: str


@router.post(
    "/interpret",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Interpret natural language input",
)
async def interpret_input(
    request: NLUInterpretRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Interpret natural language input and return command suggestions.

    This endpoint provides basic command matching and suggestions for user queries.
    For full NLU with Claude interpretation, use from the CLI.

    Args:
        request: NLUInterpretRequest with input string and optional context
        current_user: Authenticated user

    Returns:
        SuccessResponse with interpreted commands or suggestions
    """
    try:
        if not request.input or not request.input.strip():
            return SuccessResponse(
                message="Please enter a command or question.",
                data={
                    "status": "no_match",
                    "message": "Please enter a command or question.",
                }
            )

        user_input = request.input.strip()
        user_input_lower = user_input.lower()
        logger.info(f"NLU interpretation request from user {current_user}: '{request.input}'")

        # Check if input is a direct command (starts with /)
        if user_input.startswith('/'):
            # Direct command - return as-is
            matched_command = user_input
        else:
            # Simple pattern-based command matching
            # Map common phrases to commands
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
                    if phrase in user_input_lower and len(phrase.split()) == len(user_input_lower.split()):
                        # Exact match
                        matched_command = command
                        confidence = 0.95
                    else:
                        # Partial match
                        suggestions.append({
                            "command": command,
                            "confidence": confidence,
                            "reasoning": f"Matched keyword: {phrase}",
                            "args": []
                        })

        # If exact match found, return it
        if matched_command:
            return SuccessResponse(
                message=f"Understood! Executing: {matched_command}",
                data={
                    "status": "success",
                    "command": matched_command,
                    "message": f"Understood! Executing: {matched_command}",
                }
            )

        # If suggestions found, return them
        if suggestions:
            # Sort by confidence
            suggestions.sort(key=lambda x: x["confidence"], reverse=True)
            return SuccessResponse(
                message="Did you mean one of these?",
                data={
                    "status": "suggestions",
                    "suggestions": suggestions[:3],  # Top 3 suggestions
                    "message": "Did you mean one of these?",
                }
            )

        # No match found
        return SuccessResponse(
            message="I didn't understand that. Try describing what you want or typing a command like /help",
            data={
                "status": "no_match",
                "message": "I didn't understand that. Try:\n• Describing what you want (analyze, test, fix, etc.)\n• Typing a command like /help\n• Selecting a project from the dropdown",
            }
        )

    except Exception as e:
        logger.error(f"Error interpreting input: {e}", exc_info=True)
        return SuccessResponse(
            message="Error processing your request. Please try again.",
            data={
                "status": "error",
                "message": "Error processing your request. Please try again.",
            }
        )


@router.get(
    "/commands",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get list of available commands",
)
async def get_available_commands(
    current_user: str = Depends(get_current_user),
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
        logger.info(f"Available commands requested by user: {current_user}")

        # Static list of available commands organized by category
        commands_by_category = {
            "system": [
                {"name": "help", "usage": "/help", "description": "Show help and available commands", "aliases": ["h", "?"]},
                {"name": "status", "usage": "/status", "description": "Show current status", "aliases": []},
                {"name": "info", "usage": "/info", "description": "Show system information", "aliases": []},
            ],
            "project": [
                {"name": "project analyze", "usage": "/project analyze", "description": "Analyze project structure", "aliases": []},
                {"name": "project test", "usage": "/project test", "description": "Run tests", "aliases": []},
                {"name": "project fix", "usage": "/project fix", "description": "Apply fixes", "aliases": []},
                {"name": "project validate", "usage": "/project validate", "description": "Validate project", "aliases": []},
                {"name": "project review", "usage": "/project review", "description": "Code review", "aliases": []},
            ],
            "chat": [
                {"name": "advance", "usage": "/advance", "description": "Advance to next phase", "aliases": []},
                {"name": "done", "usage": "/done", "description": "Finish session", "aliases": []},
                {"name": "ask", "usage": "/ask <question>", "description": "Ask a question", "aliases": []},
                {"name": "hint", "usage": "/hint", "description": "Get a hint", "aliases": []},
                {"name": "explain", "usage": "/explain <topic>", "description": "Explain a concept", "aliases": []},
            ],
            "docs": [
                {"name": "docs import", "usage": "/docs import", "description": "Import file", "aliases": []},
                {"name": "docs import-url", "usage": "/docs import-url <url>", "description": "Import from URL", "aliases": []},
                {"name": "docs list", "usage": "/docs list", "description": "List documents", "aliases": []},
                {"name": "code generate", "usage": "/code generate", "description": "Generate code", "aliases": []},
                {"name": "code docs", "usage": "/code docs", "description": "Generate documentation", "aliases": []},
            ],
            "collaboration": [
                {"name": "collab add", "usage": "/collab add <username>", "description": "Add collaborator", "aliases": []},
                {"name": "collab list", "usage": "/collab list", "description": "List collaborators", "aliases": []},
                {"name": "collab remove", "usage": "/collab remove <username>", "description": "Remove collaborator", "aliases": []},
                {"name": "skills list", "usage": "/skills list", "description": "List skills", "aliases": []},
                {"name": "note list", "usage": "/note list", "description": "List notes", "aliases": []},
            ],
            "subscription": [
                {"name": "subscription status", "usage": "/subscription status", "description": "Show subscription status", "aliases": []},
                {"name": "subscription upgrade", "usage": "/subscription upgrade <plan>", "description": "Upgrade subscription", "aliases": []},
                {"name": "subscription compare", "usage": "/subscription compare", "description": "Compare plans", "aliases": []},
            ],
        }

        return SuccessResponse(
            message="Available commands retrieved successfully",
            data={"commands": commands_by_category}
        )

    except Exception as e:
        logger.error(f"Error retrieving commands: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available commands"
        )
