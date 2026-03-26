"""
Commands API Router

Provides unified API access to all Socrates commands through the command registry.
This enables:
1. Discovery of available commands
2. Help documentation for commands
3. Command execution through the API
4. Command metrics and analytics
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/commands", tags=["Commands"])

# Local command registry (replaces non-existent socratic_system.ui.command_registry)
class CommandCategory:
    """Simple command category enum"""
    QUERY = "query"
    SYSTEM = "system"
    WORKFLOW = "workflow"
    ANALYSIS = "analysis"

def get_registry():
    """Get local command registry"""
    return {
        "categories": [CommandCategory.QUERY, CommandCategory.SYSTEM, CommandCategory.WORKFLOW, CommandCategory.ANALYSIS],
        "commands": []  # Can be populated with actual commands
    }


# ============================================================================
# MODELS
# ============================================================================


class CommandMetadataResponse(BaseModel):
    """Command metadata"""

    name: str
    description: str
    category: str
    aliases: List[str] = Field(default_factory=list)
    example: Optional[str] = None


class ListCommandsResponse(BaseModel):
    """List of available commands"""

    status: str
    data: Dict[str, CommandMetadataResponse]


class GetHelpResponse(BaseModel):
    """Help text response"""

    status: str
    data: str


class ExecuteCommandRequest(BaseModel):
    """Execute a command"""

    command: str = Field(..., description="Command name or alias")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    project_id: Optional[str] = None
    session_id: Optional[str] = None


class ExecuteCommandResponse(BaseModel):
    """Command execution response"""

    status: str
    data: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None


class CategoriesResponse(BaseModel):
    """List of command categories"""

    status: str
    data: List[str]


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/", response_model=ListCommandsResponse)
def list_commands(
    category: Optional[str] = Query(None, description="Filter by category"),
) -> ListCommandsResponse:
    """
    List all available commands.

    Query Parameters:
    - category: Optional category to filter by (e.g., "Projects", "Code Generation")

    Returns:
    - List of commands with metadata
    """
    try:
        registry = get_registry()

        # Filter by category if provided
        if category:
            try:
                cat = CommandCategory[category.upper().replace(" ", "_")]
                commands_dict = registry.list_commands(cat)
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Unknown category: {category}")
        else:
            commands_dict = registry.list_commands()

        # Convert to response format
        data = {}
        for cmd_name, metadata in commands_dict.items():
            data[cmd_name] = CommandMetadataResponse(
                name=metadata.name,
                description=metadata.description,
                category=metadata.category.value,
                aliases=metadata.aliases,
                example=metadata.example,
            )

        return ListCommandsResponse(status="success", data=data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing commands: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", response_model=CategoriesResponse)
def list_categories() -> CategoriesResponse:
    """
    List all available command categories.

    Returns:
    - List of category names
    """
    try:
        registry = get_registry()
        categories = [cat.value for cat in registry.list_categories()]
        return CategoriesResponse(status="success", data=sorted(categories))
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/help", response_model=GetHelpResponse)
def get_help(command: Optional[str] = Query(None, description="Optional command name")) -> GetHelpResponse:
    """
    Get help documentation.

    Query Parameters:
    - command: Optional command name to get help for (omit for general help)

    Returns:
    - Help text
    """
    try:
        registry = get_registry()
        help_text = registry.get_help(command)
        return GetHelpResponse(status="success", data=help_text)
    except Exception as e:
        logger.error(f"Error getting help: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=ExecuteCommandResponse)
def execute_command(request: ExecuteCommandRequest) -> ExecuteCommandResponse:
    """
    Execute a command.

    Request Body:
    - command: Command name or alias
    - args: List of arguments
    - project_id: Optional project ID for context
    - session_id: Optional session ID for context

    Returns:
    - Command execution result
    """
    try:
        registry = get_registry()

        # Build execution context (simplified - would normally include user, orchestrator, etc.)
        context = {
            "project_id": request.project_id,
            "session_id": request.session_id,
        }

        # Execute command
        result = registry.execute(request.command, request.args, context)

        # Format response
        status = result.get("status", "success")
        message = result.get("message")
        data = {k: v for k, v in result.items() if k not in ["status", "message"]}

        return ExecuteCommandResponse(status=status, data=data, message=message)

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return ExecuteCommandResponse(
            status="error",
            message=str(e),
        )


@router.get("/{command_name}", response_model=CommandMetadataResponse)
def get_command(command_name: str) -> CommandMetadataResponse:
    """
    Get metadata for a specific command.

    Path Parameters:
    - command_name: Command name or alias

    Returns:
    - Command metadata
    """
    try:
        registry = get_registry()
        metadata = registry.get_metadata(command_name)

        if not metadata:
            raise HTTPException(status_code=404, detail=f"Command '{command_name}' not found")

        return CommandMetadataResponse(
            name=metadata.name,
            description=metadata.description,
            category=metadata.category.value,
            aliases=metadata.aliases,
            example=metadata.example,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting command metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))
