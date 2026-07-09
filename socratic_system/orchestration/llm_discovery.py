"""
LLM Provider Discovery and Configuration

Dynamically discovers available models from LLM providers (Ollama, etc.)
and updates provider metadata to reflect actual deployed models.

Implements Option 4 (Delegation Pattern): Orchestrator discovers environment
state and provides it to agents, keeping them environment-agnostic.
"""

import logging

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
