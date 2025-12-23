"""
LLM Provider Management API endpoints for Socrates.

Provides configuration, usage stats, and provider management functionality.
"""

import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends

from socratic_system.database import ProjectDatabaseV2
from socrates_api.models import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm", tags=["llm"])


def get_database() -> ProjectDatabaseV2:
    """Get database instance."""
    data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
    db_path = os.path.join(data_dir, "projects.db")
    return ProjectDatabaseV2(db_path)


@router.get(
    "/providers",
    response_model=list,
    status_code=status.HTTP_200_OK,
    summary="List LLM providers",
    responses={
        200: {"description": "Providers retrieved"},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def list_providers(
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    List available LLM providers and their configuration.

    Returns:
        List of providers and their details
    """
    try:
        # TODO: Get providers from configuration
        # For now, return common providers
        providers = [
            {
                "name": "claude",
                "label": "Anthropic Claude",
                "models": ["claude-opus-4.5", "claude-sonnet-4", "claude-haiku-4.5"],
                "is_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            },
            {
                "name": "openai",
                "label": "OpenAI",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "is_configured": bool(os.getenv("OPENAI_API_KEY")),
            },
            {
                "name": "gemini",
                "label": "Google Gemini",
                "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
                "is_configured": bool(os.getenv("GEMINI_API_KEY")),
            },
            {
                "name": "local",
                "label": "Local LLM",
                "models": ["llama2", "mistral", "neural-chat"],
                "is_configured": False,
            },
        ]

        return providers

    except Exception as e:
        logger.error(f"Error listing providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list providers: {str(e)}",
        )


@router.get(
    "/models/{provider}",
    response_model=list,
    status_code=status.HTTP_200_OK,
    summary="List models for LLM provider",
    responses={
        200: {"description": "Models retrieved"},
        400: {"description": "Invalid provider", "model": ErrorResponse},
    },
)
async def list_provider_models(
    provider: str,
):
    """
    List available models for a specific LLM provider.

    Args:
        provider: Provider name (claude, openai, gemini, local)

    Returns:
        List of available models for the provider
    """
    try:
        # Map of providers to their models
        models_map = {
            "anthropic": ["claude-opus-4.5", "claude-sonnet-4", "claude-haiku-4.5"],
            "claude": ["claude-opus-4.5", "claude-sonnet-4", "claude-haiku-4.5"],
            "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "gemini": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
            "local": ["llama2", "mistral", "neural-chat"],
        }

        if provider.lower() not in models_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown provider: {provider}",
            )

        models = models_map[provider.lower()]
        return [{"name": m, "label": m} for m in models]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}",
        )


@router.get(
    "/config",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get LLM configuration",
    responses={
        200: {"description": "Configuration retrieved"},
    },
)
async def get_llm_config(
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get current LLM configuration including default provider and model.

    Returns:
        SuccessResponse with configuration details
    """
    try:
        # TODO: Get from user preferences or config file
        config = {
            "default_provider": os.getenv("DEFAULT_LLM_PROVIDER", "claude"),
            "default_model": os.getenv("DEFAULT_LLM_MODEL", "claude-opus-4.5"),
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2048")),
        }

        return SuccessResponse(
            success=True,
            message="Configuration retrieved",
            data=config,
        )

    except Exception as e:
        logger.error(f"Error getting LLM config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}",
        )


@router.put(
    "/default-provider",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Set default LLM provider",
    responses={
        200: {"description": "Provider set"},
        400: {"description": "Invalid provider", "model": ErrorResponse},
    },
)
async def set_default_provider(
    provider: str,
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Set the default LLM provider.

    Args:
        provider: Provider name (claude, openai, gemini, local)
        db: Database connection

    Returns:
        SuccessResponse confirming provider change
    """
    try:
        if provider not in ["claude", "openai", "gemini", "local"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown provider: {provider}",
            )

        logger.info(f"Setting default LLM provider: {provider}")

        # TODO: Update user preferences in database
        # For now, just return success
        return SuccessResponse(
            success=True,
            message=f"Default provider set to {provider}",
            data={"provider": provider},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting default provider: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set provider: {str(e)}",
        )


@router.put(
    "/model",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Set LLM model for provider",
    responses={
        200: {"description": "Model set"},
        400: {"description": "Invalid provider or model", "model": ErrorResponse},
    },
)
async def set_provider_model(
    provider: str,
    model: str,
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Set the LLM model for a specific provider.

    Args:
        provider: Provider name
        model: Model identifier
        db: Database connection

    Returns:
        SuccessResponse confirming model change
    """
    try:
        logger.info(f"Setting {provider} model to {model}")

        # TODO: Validate provider and model combination
        # TODO: Update user preferences in database
        return SuccessResponse(
            success=True,
            message=f"Model set to {model} for provider {provider}",
            data={"provider": provider, "model": model},
        )

    except Exception as e:
        logger.error(f"Error setting model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set model: {str(e)}",
        )


@router.post(
    "/api-key",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add or update API key for provider",
    responses={
        201: {"description": "API key added"},
        400: {"description": "Invalid provider", "model": ErrorResponse},
    },
)
async def add_api_key(
    provider: str,
    api_key: str,
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Add or update API key for an LLM provider.

    Args:
        provider: Provider name
        api_key: API key (should be encrypted)
        db: Database connection

    Returns:
        SuccessResponse confirming API key addition
    """
    try:
        if not api_key or len(api_key.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key is required and must be at least 10 characters",
            )

        logger.info(f"Adding API key for provider: {provider}")

        # TODO: Encrypt and store API key in secure storage
        # TODO: Validate API key format for the provider
        return SuccessResponse(
            success=True,
            message=f"API key added for {provider}",
            data={
                "provider": provider,
                "key_last_4": api_key[-4:] if len(api_key) >= 4 else "****",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add API key: {str(e)}",
        )


@router.delete(
    "/api-key/{provider}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove API key for provider",
    responses={
        200: {"description": "API key removed"},
        404: {"description": "Provider not found", "model": ErrorResponse},
    },
)
async def remove_api_key(
    provider: str,
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Remove API key for an LLM provider.

    Args:
        provider: Provider name
        db: Database connection

    Returns:
        SuccessResponse confirming API key removal
    """
    try:
        logger.info(f"Removing API key for provider: {provider}")

        # TODO: Delete API key from secure storage
        return SuccessResponse(
            success=True,
            message=f"API key removed for {provider}",
            data={"provider": provider},
        )

    except Exception as e:
        logger.error(f"Error removing API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove API key: {str(e)}",
        )


@router.get(
    "/models/{provider}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="List models for provider",
    responses={
        200: {"description": "Models retrieved"},
        404: {"description": "Provider not found", "model": ErrorResponse},
    },
)
async def list_provider_models(
    provider: str,
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    List all available models for an LLM provider.

    Args:
        provider: Provider name
        db: Database connection

    Returns:
        SuccessResponse with list of models
    """
    try:
        models_map = {
            "claude": [
                {"id": "claude-opus-4.5", "name": "Claude Opus 4.5", "context": 200000},
                {"id": "claude-sonnet-4", "name": "Claude Sonnet 4", "context": 200000},
                {"id": "claude-haiku-4.5", "name": "Claude Haiku 4.5", "context": 200000},
            ],
            "openai": [
                {"id": "gpt-4", "name": "GPT-4", "context": 8192},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context": 128000},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context": 4096},
            ],
            "gemini": [
                {
                    "id": "gemini-2.0-flash",
                    "name": "Gemini 2.0 Flash",
                    "context": 1000000,
                },
                {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "context": 1000000},
                {
                    "id": "gemini-1.5-flash",
                    "name": "Gemini 1.5 Flash",
                    "context": 1000000,
                },
            ],
            "local": [
                {"id": "llama2", "name": "Llama 2", "context": 4096},
                {"id": "mistral", "name": "Mistral", "context": 8192},
                {"id": "neural-chat", "name": "Neural Chat", "context": 4096},
            ],
        }

        models = models_map.get(provider, [])
        if not models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unknown provider: {provider}",
            )

        return SuccessResponse(
            success=True,
            message=f"Models retrieved for {provider}",
            data={"provider": provider, "models": models, "total": len(models)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}",
        )


@router.get(
    "/usage-stats",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get LLM usage statistics",
    responses={
        200: {"description": "Usage stats retrieved"},
    },
)
async def get_usage_stats(
    time_period: str = "month",
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get LLM usage statistics for current user.

    Args:
        time_period: Time period (day, week, month, all)
        db: Database connection

    Returns:
        SuccessResponse with usage statistics
    """
    try:
        # TODO: Calculate usage stats from database
        stats = {
            "total_requests": 0,
            "total_tokens": {"input": 0, "output": 0},
            "by_provider": {
                "claude": {"requests": 0, "tokens": 0, "cost": 0},
                "openai": {"requests": 0, "tokens": 0, "cost": 0},
                "gemini": {"requests": 0, "tokens": 0, "cost": 0},
            },
            "by_model": {},
            "cost_summary": {"estimated": 0, "period": time_period},
        }

        return SuccessResponse(
            success=True,
            message="Usage statistics retrieved",
            data=stats,
        )

    except Exception as e:
        logger.error(f"Error getting usage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage stats: {str(e)}",
        )
