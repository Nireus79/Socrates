"""LLM Provider API endpoints."""

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from socrates_api.auth import get_current_user
from socrates_api.database import get_database, ProjectDatabase
from socrates_api.models import APIResponse

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ApiKeyRequest(BaseModel):
    """Request model for setting API key."""

    provider: str
    api_key: str


class DefaultProviderRequest(BaseModel):
    """Request model for setting default provider."""

    provider: str


class ModelRequest(BaseModel):
    """Request model for setting model."""

    provider: str
    model: str


class AuthMethodRequest(BaseModel):
    """Request model for setting authentication method."""

    provider: str
    auth_method: str


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/providers", response_model=APIResponse)
async def list_providers(current_user: str = Depends(get_current_user)):
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager", {"action": "list_providers", "user_id": current_user}
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(
            success=True, status="success", message="Providers", data=result.get("data", result)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=APIResponse)
async def get_config(current_user: str = Depends(get_current_user)):
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager", {"action": "get_provider_config", "user_id": current_user}
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(
            success=True, status="success", message="Config", data=result.get("data", result)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/default-provider", response_model=APIResponse)
async def set_default_provider(
    request: DefaultProviderRequest,
    current_user: str = Depends(get_current_user),
):
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager",
            {
                "action": "set_default_provider",
                "user_id": current_user,
                "provider": request.provider,
            },
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(
            success=True, status="success", message="Provider set", data=result.get("data", result)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/model", response_model=APIResponse)
async def set_model(
    request: ModelRequest,
    current_user: str = Depends(get_current_user),
    db: "ProjectDatabase" = Depends(get_database),
):
    try:
        from socratic_system.models import get_provider_metadata
        from socratic_system.orchestration.llm_discovery import discover_provider_models
        from socrates_api.main import get_orchestrator

        logger.info(f"Setting model for user {current_user}: {request.provider}/{request.model}")

        # For providers with dynamic model discovery (empty metadata.models),
        # discover models to validate before sending to agent
        provider_meta = get_provider_metadata(request.provider)
        discovered_models = None

        if provider_meta and len(provider_meta.models) == 0:
            # Get user's API key if available
            api_key = None
            try:
                encrypted_key = db.get_api_key(current_user, request.provider)
                if encrypted_key:
                    from socratic_system.encryption import decrypt_data
                    api_key = decrypt_data(encrypted_key)
            except Exception as e:
                logger.debug(f"Could not fetch/decrypt API key for {request.provider}: {e}")

            # Discover actual models
            discovered = await discover_provider_models(request.provider, api_key)

            # Validate against discovered models
            if not discovered:
                # Discovery failed - could be API error, invalid key, or network issue
                if provider_meta.requires_api_key:
                    # API key is required, so discovery failure is an error
                    if not api_key:
                        raise HTTPException(
                            status_code=400,
                            detail=f"API key required for {request.provider} to validate models. Add API key and try again."
                        )
                    else:
                        raise HTTPException(
                            status_code=503,
                            detail=f"Unable to discover {request.provider} models. Try again or check your API key."
                        )
                else:
                    # Optional provider (like Ollama) - allow model selection even if discovery fails
                    # Just log a warning and let the request proceed
                    logger.warning(f"Could not discover models for {request.provider}, but allowing selection anyway (optional provider)")
            elif request.model not in discovered:
                available = ", ".join(discovered[:10])  # Show first 10
                if len(discovered) > 10:
                    available += f", ... and {len(discovered) - 10} more"
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{request.model}' not available for {request.provider}. Available: {available}"
                )
            else:
                # Store discovered models to pass to agent
                discovered_models = discovered
                logger.debug(f"Discovered {len(discovered)} models for {request.provider}: {discovered}")

        try:
            orchestrator = get_orchestrator()
        except RuntimeError as e:
            logger.error(f"Orchestrator not initialized: {e}")
            raise HTTPException(status_code=503, detail="Service not initialized. Please refresh the page.")

        try:
            # Build request for multi_llm_manager
            agent_request = {
                "action": "set_provider_model",
                "user_id": current_user,
                "provider": request.provider,
                "model": request.model,
            }

            # Pass discovered models to agent for validation (Option A architecture)
            if discovered_models is not None:
                agent_request["available_models"] = discovered_models
                logger.debug(f"Passing {len(discovered_models)} discovered models to multi_llm_manager agent")

            result = await orchestrator.agent_bus.send_request(
                "multi_llm_manager",
                agent_request,
            )
        except HTTPException:
            raise  # Re-raise HTTP exceptions as-is
        except Exception as e:
            logger.error(f"Error sending request to multi_llm_manager: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to set model: {str(e)}")

        if result.get("status") != "success":
            # Check if it's a validation error (400) or server error (500)
            message = result.get("message", "Failed to set model")
            if "not available" in message.lower():
                raise HTTPException(status_code=400, detail=message)
            else:
                raise HTTPException(status_code=500, detail=message)

        logger.info(f"Model set successfully: {request.provider}/{request.model}")
        return APIResponse(
            success=True, status="success", message="Model set", data=result.get("data", result)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in set_model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-key", response_model=APIResponse)
async def set_api_key(
    request: ApiKeyRequest,
    current_user: str = Depends(get_current_user),
):
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager",
            {
                "action": "add_api_key",
                "user_id": current_user,
                "provider": request.provider,
                "api_key": request.api_key,
            },
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(
            success=True,
            status="success",
            message="API key set",
            data={"provider": request.provider},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api-key/{provider}", response_model=APIResponse)
async def remove_api_key(provider: str, current_user: str = Depends(get_current_user)):
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager",
            {"action": "remove_api_key", "user_id": current_user, "provider": provider},
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(
            success=True,
            status="success",
            message="API key removed",
            data={"provider": provider},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/auth-method", response_model=APIResponse)
async def set_auth_method(
    request: AuthMethodRequest,
    current_user: str = Depends(get_current_user),
):
    """Set authentication method for a provider (e.g., Claude subscription vs API key)."""
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager",
            {
                "action": "set_auth_method",
                "user_id": current_user,
                "provider": request.provider,
                "auth_method": request.auth_method,
            },
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=400, detail=result.get("message", "Failed"))
        return APIResponse(
            success=True,
            status="success",
            message="Auth method updated",
            data={"provider": request.provider, "auth_method": request.auth_method},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{provider}", response_model=APIResponse)
async def get_models(provider: str):
    try:
        from socratic_system.models.llm_provider import get_provider_metadata

        metadata = get_provider_metadata(provider)
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

        return APIResponse(
            success=True,
            status="success",
            message="Models",
            data={
                "provider": provider,
                "models": metadata.models,
                "context_window": metadata.context_window,
                "supports_streaming": metadata.supports_streaming,
                "supports_vision": metadata.supports_vision,
                "default_model": metadata.models[0] if metadata.models else None,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage-stats", response_model=APIResponse)
async def get_stats(time_period: str = "month", current_user: str = Depends(get_current_user)):
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        days = 30 if time_period == "month" else 7 if time_period == "week" else 1
        result = await orchestrator.agent_bus.send_request(
            "multi_llm_manager",
            {"action": "get_usage_stats", "user_id": current_user, "days": days},
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(
            success=True, status="success", message="Stats", data=result.get("data", result)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
