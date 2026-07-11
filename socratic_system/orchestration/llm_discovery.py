"""
LLM Provider Discovery and Configuration

Dynamically discovers available models from LLM providers (Ollama, etc.)
and updates provider metadata to reflect actual deployed models.

Implements Option 4 (Delegation Pattern): Orchestrator discovers environment
state and provides it to agents, keeping them environment-agnostic.
"""

import logging
from typing import Optional

from socratic_system.config.llm_environment import LLMEnvironmentConfig

logger = logging.getLogger(__name__)


def discover_ollama_models() -> list[str] | None:
    """
    Discover available models from Ollama by querying /api/tags endpoint.

    Implements Option 4: Orchestrator discovers environment, not libraries.
    Uses LLMEnvironmentConfig for auto-detection across deployments.

    Returns:
        List of model names if discovery succeeds, None if Ollama unavailable.
        Gracefully handles connection failures - returns None without crashing.
    """
    try:
        import httpx

        # Get Ollama host via auto-detection (Option 4: environment-aware)
        ollama_host = LLMEnvironmentConfig.get_ollama_host()

        if not ollama_host:
            logger.debug("Ollama endpoint not available - using fallback model list")
            return None

        tags_url = f"{ollama_host}/api/tags"
        logger.debug(f"Querying Ollama models from {tags_url}")

        # Query Ollama's /api/tags endpoint with timeout
        response = httpx.get(tags_url, timeout=5.0)
        response.raise_for_status()

        data = response.json()
        models_data = data.get("models", [])

        if not models_data:
            logger.warning("Ollama returned empty model list")
            return None

        # Extract model names from Ollama response
        # Ollama returns: [{"name": "codellama:latest", ...}, {"name": "mistral:latest", ...}]
        model_names = [model.get("name") for model in models_data if model.get("name")]

        if model_names:
            logger.info(f"✓ Discovered {len(model_names)} Ollama models: {model_names}")
            return model_names

        return None

    except ImportError:
        logger.warning("httpx not available - skipping Ollama discovery")
        return None
    except TimeoutError:
        logger.warning("Ollama discovery timed out - Ollama may not be running")
        return None
    except ConnectionError:
        logger.warning("Could not connect to Ollama - using fallback model list")
        return None
    except Exception as e:
        logger.warning(f"Ollama discovery failed: {e} - using fallback model list")
        return None


async def discover_claude_models(api_key: Optional[str] = None) -> Optional[list[str]]:
    """
    Discover available Claude models from Anthropic.

    Note: Anthropic does not provide a public models API endpoint.
    Always returns None to use fallback (empty list for dynamic discovery).

    Args:
        api_key: Optional API key for the provider (not used).
    """
    logger.debug("Claude discovery skipped - Anthropic has no public models API")
    return None


async def discover_openai_models(api_key: Optional[str] = None) -> Optional[list[str]]:
    """
    Discover available OpenAI models from OpenAI API.
    Filters for GPT models (gpt-4, gpt-3.5-turbo, etc).
    Falls back to empty list if discovery fails.

    Args:
        api_key: Optional API key. If not provided, checks OPENAI_API_KEY env var.
    """
    try:
        import asyncio
        import os
        from openai import OpenAI

        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.debug("OPENAI_API_KEY not set - skipping OpenAI model discovery")
            return None

        client = OpenAI(api_key=api_key)

        # Run sync blocking call in thread pool to avoid blocking event loop
        def _list_models():
            return client.models.list()

        try:
            models_response = await asyncio.wait_for(asyncio.to_thread(_list_models), timeout=10.0)
        except asyncio.TimeoutError:
            logger.debug("OpenAI model discovery timed out")
            return None
        gpt_models = [
            model.id for model in models_response.data
            if 'gpt' in model.id.lower() and not model.id.startswith('text-')
        ]

        if gpt_models:
            logger.info(f"✓ Discovered {len(gpt_models)} OpenAI models")
            return sorted(gpt_models, reverse=True)  # Newest first

        return None

    except ImportError:
        logger.debug("openai library not available - skipping OpenAI model discovery")
        return None
    except Exception as e:
        logger.debug(f"OpenAI model discovery failed: {e}")
        return None


async def discover_gemini_models(api_key: Optional[str] = None) -> Optional[list[str]]:
    """
    Discover available Google Gemini models.
    Queries genai.list_models() to get available models.
    Falls back to empty list if discovery fails.

    Args:
        api_key: Optional API key. If not provided, checks GOOGLE_API_KEY env var.
    """
    try:
        import asyncio
        import os
        import google.generativeai as genai

        if not api_key:
            api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.debug("GOOGLE_API_KEY not set - skipping Gemini model discovery")
            return None

        # Configure genai in a thread pool since it's sync
        def _configure_and_list():
            genai.configure(api_key=api_key)
            return genai.list_models()

        try:
            models = await asyncio.wait_for(asyncio.to_thread(_configure_and_list), timeout=10.0)
        except asyncio.TimeoutError:
            logger.debug("Gemini model discovery timed out")
            return None
        model_names = [
            model.name.replace('models/', '') for model in models
            if 'gemini' in model.name.lower()
        ]

        if model_names:
            logger.info(f"✓ Discovered {len(model_names)} Gemini models")
            return sorted(model_names, reverse=True)  # Newest first

        return None

    except ImportError:
        logger.debug("google.generativeai library not available - skipping Gemini model discovery")
        return None
    except Exception as e:
        logger.debug(f"Gemini model discovery failed: {e}")
        return None


async def discover_provider_models(provider: str, api_key: Optional[str] = None) -> Optional[list[str]]:
    """
    Discover available models for a given provider.
    Dynamically fetches models if possible, falls back to hardcoded list.

    Supports:
    - ollama: Queries local Ollama instance /api/tags
    - claude: Queries Anthropic API (requires api_key or ANTHROPIC_API_KEY env var)
    - openai: Queries OpenAI API (requires api_key or OPENAI_API_KEY env var)
    - gemini: Queries Google API (requires api_key or GOOGLE_API_KEY env var)

    Args:
        provider: Provider name (claude, openai, gemini, ollama)
        api_key: Optional API key for the provider. If not provided, checks env vars.

    Returns:
        List of model names if discovery succeeds, None to use hardcoded list
    """
    provider = provider.lower()

    if provider == "ollama":
        return discover_ollama_models()
    elif provider == "claude":
        return await discover_claude_models(api_key)
    elif provider == "openai":
        return await discover_openai_models(api_key)
    elif provider == "gemini":
        return await discover_gemini_models(api_key)
    else:
        logger.warning(f"Unknown provider: {provider}")
        return None


def update_provider_metadata_with_discovered_models() -> None:
    """
    Update PROVIDER_METADATA with dynamically discovered models from Ollama.

    This function:
    1. Auto-detects Ollama endpoint (local, Docker, Kubernetes, etc.)
    2. Queries Ollama /api/tags to discover actual installed models
    3. Updates the Ollama provider metadata with discovered models
    4. Gracefully falls back to hardcoded list if discovery fails
    5. Logs deployment scenario and configuration for debugging

    Implements Option 4 (Delegation): The orchestrator discovers available
    resources and updates configuration accordingly. Agents consume what
    they're told, not what they assume exists.
    """
    from socratic_system.models.llm_provider import PROVIDER_METADATA

    # Log deployment scenario
    config = LLMEnvironmentConfig.get_provider_config()
    logger.info(f"Deployment scenario: {config['deployment_scenario']}")

    # Attempt to discover actual Ollama models
    discovered_models = discover_ollama_models()

    if discovered_models:
        # Update Ollama provider metadata with discovered models
        if "ollama" in PROVIDER_METADATA:
            ollama_provider = PROVIDER_METADATA["ollama"]
            original_models = ollama_provider.models.copy()

            # Replace with discovered models
            ollama_provider.models = discovered_models

            logger.info(
                f"Updated Ollama provider metadata: "
                f"{len(original_models)} hardcoded → {len(discovered_models)} discovered"
            )
            logger.debug(f"Models: {', '.join(discovered_models)}")
        else:
            logger.warning("Ollama not found in PROVIDER_METADATA")
    else:
        logger.info("Using fallback Ollama model list (discovery unavailable)")
        logger.debug("Tip: Set OLLAMA_HOST environment variable if Ollama is running elsewhere")
