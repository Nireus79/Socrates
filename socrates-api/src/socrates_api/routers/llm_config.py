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
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager", {"action": "list_providers"}
        )

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
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager", {"action": "get_config", "user_id": current_user}
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
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager",
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
        from socrates_api.database import get_database
        from socrates_api.main import get_orchestrator

        logger.info(f"Setting API key for {provider} for user: {current_user}")

        orchestrator = get_orchestrator()
        db = get_database()

        # Add the API key via agent
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager",
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

        # Ensure provider config exists in database (required for is_configured check)
        # This is needed because simply adding an API key doesn't create the config entry
        try:
            existing_config = db.get_user_llm_config(current_user, provider)
            if not existing_config:
                # Create default provider config
                from socratic_agents.models import get_provider_metadata

                metadata = get_provider_metadata(provider)
                if metadata:
                    default_config = {
                        "id": f"{current_user}:{provider}",
                        "is_default": False,
                        "enabled": True,
                        "settings": {
                            "model": metadata.models[0] if metadata.models else "",
                            "temperature": 0.7,
                            "max_tokens": 4096,
                        },
                    }
                    db.save_llm_config(current_user, provider, default_config)
                    logger.info(f"Created default provider config for {current_user}/{provider}")
        except Exception as config_error:
            logger.warning(
                f"Could not create provider config for {provider}: {config_error}. "
                f"API key was saved but config may not show as configured."
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
    "/status",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get API key configuration status",
)
async def get_api_key_status(
    current_user: str = Depends(get_current_user),
):
    """
    Get the API key configuration status for all providers.

    Shows which providers have API keys configured and which need attention.
    Helps users understand if they need to add or update their API keys.

    Args:
        current_user: Authenticated user

    Returns:
        SuccessResponse with provider status and warnings
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Getting API key status for user: {current_user}")

        orchestrator = get_orchestrator()

        # Get list of providers
        providers_result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager", {"action": "list_providers", "user_id": current_user}
        )

        if providers_result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=providers_result.get("message", "Failed to list providers")
            )

        providers = providers_result.get("data", {}).get("providers", [])

        # Check which ones are configured and which need API keys
        warnings = []
        configured_providers = []
        missing_api_keys = []

        for provider in providers:
            provider_name = provider.get("name", "")
            is_configured = provider.get("is_configured", False)
            requires_api_key = provider.get("requires_api_key", False)

            if is_configured:
                configured_providers.append(provider_name)
            elif requires_api_key:
                missing_api_keys.append(provider_name)
                warnings.append(
                    f"API key missing for {provider_name}. "
                    f"Add or update your API key in Settings > LLM > {provider_name} to use this provider."
                )

        # Check if environment fallback is being used
        import os

        env_key_available = bool(os.getenv("ANTHROPIC_API_KEY"))
        if not configured_providers and env_key_available:
            warnings.insert(
                0,
                "No user API keys configured. Currently using environment variable as fallback. "
                "For better security and control, add your API key in Settings > LLM > Anthropic.",
            )

        return APIResponse(
            success=True,
            status="success",
            message="API key configuration status",
            data={
                "configured_providers": configured_providers,
                "missing_api_keys": missing_api_keys,
                "warnings": warnings,
                "environment_fallback_available": env_key_available,
                "action_required": len(missing_api_keys) > 0,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API key status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API key status: {str(e)}",
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
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager",
            {"action": "get_usage_stats", "user_id": current_user, "days": days},
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
