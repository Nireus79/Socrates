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


async def _validate_api_key(provider: str, api_key: str) -> dict:
    """
    Validate that an API key is valid by making a test API call.

    Args:
        provider: LLM provider name (e.g., 'claude', 'openai')
        api_key: API key to validate

    Returns:
        Dict with is_valid (bool), error (str if invalid), and provider info
    """
    try:
        from socrates_api.services.llm_client import LLMClient

        logger.info(f"Testing API key for {provider}...")

        # Create temporary LLM client with the provided key
        test_client = LLMClient(
            provider=provider,
            api_key=api_key,
            model=None,  # Use default model for provider
        )

        # Make a simple test call to validate the key
        test_response = test_client.generate_response(
            prompt="Say 'OK' if you can read this.",
            max_tokens=10,
            temperature=0.1,
        )

        if test_response and len(test_response.strip()) > 0:
            logger.info(f"API key validation successful for {provider}")
            return {
                "is_valid": True,
                "provider": provider,
                "error": None,
            }
        else:
            logger.warning(f"API key validation returned empty response for {provider}")
            return {
                "is_valid": False,
                "provider": provider,
                "error": "API returned empty response - key may be invalid",
            }

    except Exception as e:
        error_msg = str(e)
        logger.warning(f"API key validation failed for {provider}: {error_msg}")

        # Provide user-friendly error messages
        if "unauthorized" in error_msg.lower() or "authentication" in error_msg.lower():
            error_msg = "Invalid API key or authentication failed"
        elif "rate limit" in error_msg.lower():
            error_msg = "API rate limit exceeded - try again later"
        elif "connection" in error_msg.lower():
            error_msg = "Could not connect to API provider"
        else:
            error_msg = "API key validation failed - please verify the key is correct"

        return {
            "is_valid": False,
            "provider": provider,
            "error": error_msg,
        }


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
        from socrates_api.async_orchestrator import get_async_orchestrator

        logger.info(f"Listing LLM providers for user: {current_user}")

        async_orch = get_async_orchestrator()
        result = await async_orch.process_request_async("multi_llm", {"action": "list_providers"})

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
            detail="Operation failed. Please try again later.",
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
        from socrates_api.async_orchestrator import get_async_orchestrator

        logger.info(f"Getting LLM config for user: {current_user}")

        async_orch = get_async_orchestrator()
        result = await async_orch.process_request_async(
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
            detail="Operation failed. Please try again later.",
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
        from socrates_api.async_orchestrator import get_async_orchestrator

        logger.info(f"Setting default provider to {provider} for user: {current_user}")

        async_orch = get_async_orchestrator()
        result = await async_orch.process_request_async(
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
            detail="Operation failed. Please try again later.",
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
        from socrates_api.async_orchestrator import get_async_orchestrator

        # SECURITY: Don't log or expose the API key in any way
        logger.info(f"Setting API key for {provider} for user: {current_user}")

        # Validate provider is not empty
        if not provider or not provider.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider name is required"
            )

        # Validate API key is not empty
        if not api_key or not api_key.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key is required"
            )

        # CRITICAL: Validate API key works before saving
        logger.info(f"Validating API key for {provider}...")
        validation_result = await _validate_api_key(provider, api_key)

        if not validation_result.get("is_valid"):
            error_msg = validation_result.get("error", "API key validation failed")
            logger.warning(f"API key validation failed for {provider}: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid API key for {provider}: {error_msg}"
            )

        async_orch = get_async_orchestrator()
        result = await async_orch.process_request_async(
            "multi_llm",
            {
                "action": "add_api_key",
                "user_id": current_user,
                "provider": provider,
                "api_key": api_key,
            },
        )

        if result["status"] != "success":
            # SECURITY: Don't expose error details that might contain sensitive info
            logger.warning(f"Failed to set API key for {provider}: {result.get('message')}")
            raise HTTPException(
                status_code=500, detail="Failed to set API key. Please verify the provider and try again."
            )

        return APIResponse(
            success=True,
            status="success",
            message=f"API key validated and set for {provider}",
            data={
                "provider": provider,
                "is_valid": True,
                "is_tested": True,
                "ready_for_use": True,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Operation failed")
        # SECURITY: Log the error for debugging but don't expose it to the client
        logger.debug("API key configuration failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set API key. Please try again later.",
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
        from socrates_api.async_orchestrator import get_async_orchestrator

        logger.info(f"Getting usage stats for user: {current_user}")

        async_orch = get_async_orchestrator()
        result = await async_orch.process_request_async(
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
            detail="Operation failed. Please try again later.",
        )
