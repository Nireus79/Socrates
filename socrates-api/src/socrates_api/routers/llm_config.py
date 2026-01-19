"""
LLM Configuration API endpoints for Socrates.

Provides REST endpoints for managing LLM providers and configurations.
"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.models import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm-config", tags=["llm-config"])


@router.get(
    "/providers",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="List available LLM providers",
)
async def list_providers(
    current_user: str = Depends(get_current_user),
):
    """
    Get list of available LLM providers and their configuration status.

    Args:
        current_user: Authenticated user

    Returns:
        SuccessResponse with list of available providers
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Listing LLM providers for user: {current_user}")

        orchestrator = get_orchestrator()
        result = orchestrator.process_request("multi_llm", {"action": "list_providers"})

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to list providers")
            )

        return APIResponse(
            success=True,
        status="success",
            message="Available LLM providers",
            data=result.get("data", result),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list providers: {str(e)}",
        )


@router.get(
    "/config",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get LLM configuration",
)
async def get_config(
    current_user: str = Depends(get_current_user),
):
    """
    Get current LLM provider configuration for the user.

    Args:
        current_user: Authenticated user

    Returns:
        SuccessResponse with current LLM configuration
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Getting LLM config for user: {current_user}")

        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "multi_llm", {"action": "get_config", "user_id": current_user}
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to get config")
            )

        return APIResponse(
            success=True,
        status="success",
            message="LLM configuration",
            data=result.get("data", result),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config: {str(e)}",
        )


@router.post(
    "/default-provider",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Set default LLM provider",
)
async def set_default_provider(
    provider: str = Body(..., embed=True),
    current_user: str = Depends(get_current_user),
):
    """
    Set the default LLM provider.

    Args:
        provider: Provider name (claude, openai, gemini, ollama)
        current_user: Authenticated user

    Returns:
        SuccessResponse with updated configuration
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Setting default provider to {provider} for user: {current_user}")

        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "multi_llm",
            {"action": "set_default_provider", "user_id": current_user, "provider": provider},
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to set provider")
            )

        return APIResponse(
            success=True,
        status="success",
            message=f"Default provider set to {provider}",
            data=result.get("data", result),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting provider: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set provider: {str(e)}",
        )


@router.post(
    "/api-key",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Set API key for provider",
)
async def set_api_key(
    provider: str = Body(..., embed=True),
    api_key: str = Body(..., embed=True),
    current_user: str = Depends(get_current_user),
):
    """
    Set API key for a specific LLM provider.

    Args:
        provider: Provider name
        api_key: API key for the provider
        current_user: Authenticated user

    Returns:
        SuccessResponse with confirmation
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Setting API key for {provider} for user: {current_user}")

        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "multi_llm",
            {
                "action": "add_api_key",
                "user_id": current_user,
                "provider": provider,
                "api_key": api_key,
            },
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to set API key")
            )

        return APIResponse(
            success=True,
        status="success",
            message=f"API key set for {provider}",
            data={"provider": provider},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set API key: {str(e)}",
        )


@router.get(
    "/usage-stats",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get LLM usage statistics",
)
async def get_usage_stats(
    days: int = 30,
    current_user: str = Depends(get_current_user),
):
    """
    Get LLM usage statistics for the user.

    Args:
        days: Number of days to include in stats (default: 30)
        current_user: Authenticated user

    Returns:
        SuccessResponse with usage statistics
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Getting usage stats for user: {current_user}")

        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "multi_llm", {"action": "get_usage_stats", "user_id": current_user, "days": days}
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to get stats")
            )

        return APIResponse(
            success=True,
        status="success",
            message="Usage statistics",
            data=result.get("data", result),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage stats: {str(e)}",
        )
