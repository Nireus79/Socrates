"""LLM Provider API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from socrates_api.auth import get_current_user
from socrates_api.models import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/providers", response_model=APIResponse)
async def list_providers(current_user: str = Depends(get_current_user)):
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "multi_llm", {"action": "list_providers", "user_id": current_user}
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(success=True,
        status="success", message="Providers", data=result.get("data", result))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=APIResponse)
async def get_config(current_user: str = Depends(get_current_user)):
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "multi_llm", {"action": "get_provider_config", "user_id": current_user}
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(success=True,
        status="success", message="Config", data=result.get("data", result))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/default-provider", response_model=APIResponse)
async def set_default_provider(provider: str, current_user: str = Depends(get_current_user)):
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "multi_llm",
            {"action": "set_default_provider", "user_id": current_user, "provider": provider},
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(
            success=True,
        status="success", message="Provider set", data=result.get("data", result)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/model", response_model=APIResponse)
async def set_model(provider: str, model: str, current_user: str = Depends(get_current_user)):
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "multi_llm",
            {
                "action": "set_provider_model",
                "user_id": current_user,
                "provider": provider,
                "model": model,
            },
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(success=True,
        status="success", message="Model set", data=result.get("data", result))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-key", response_model=APIResponse)
async def set_api_key(provider: str, api_key: str, current_user: str = Depends(get_current_user)):
    try:
        from socrates_api.main import get_orchestrator

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
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(
        success=True,
        status="success",
        message="API key set",
        data={"provider": provider},
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
        result = orchestrator.process_request(
            "multi_llm", {"action": "remove_api_key", "user_id": current_user, "provider": provider}
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
async def set_auth_method(provider: str, auth_method: str, current_user: str = Depends(get_current_user)):
    """Set authentication method for a provider (e.g., Claude subscription vs API key)."""
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "multi_llm",
            {
                "action": "set_auth_method",
                "user_id": current_user,
                "provider": provider,
                "auth_method": auth_method,
            },
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=400, detail=result.get("message", "Failed"))
        return APIResponse(
            success=True,
            status="success",
            message="Auth method updated",
            data={"provider": provider, "auth_method": auth_method},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{provider}", response_model=APIResponse)
async def get_models(provider: str, current_user: str = Depends(get_current_user)):
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "multi_llm", {"action": "get_provider_models", "provider": provider}
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(success=True,
        status="success", message="Models", data=result.get("data", result))
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
        result = orchestrator.process_request(
            "multi_llm", {"action": "get_usage_stats", "user_id": current_user, "days": days}
        )
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed"))
        return APIResponse(success=True,
        status="success", message="Stats", data=result.get("data", result))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
