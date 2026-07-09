"""
LLM Environment Configuration and Auto-Detection

Implements Option 4 (Delegation Pattern): Discovers LLM provider locations
across different deployments (local, Docker, Kubernetes, cloud).

Supports:
- Environment variable overrides (OLLAMA_HOST, etc.)
- Auto-detection in common deployment scenarios
- Graceful fallback when providers unavailable
- Clear logging for debugging
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class LLMEnvironmentConfig:
    """
    Discovers and validates LLM provider endpoints across deployment scenarios.

    Priority order:
    1. Environment variables (highest priority - explicit config)
    2. Auto-detection (common deployment patterns)
    3. Graceful fallback (provider unavailable)
    """

    # Common Ollama endpoint patterns by deployment scenario
    OLLAMA_DETECTION_ORDER = [
        # 1. Explicit environment variable (user override)
        ("env_var", "OLLAMA_HOST"),
        # 2. Docker networks
        ("docker_network", "http://ollama:11434"),  # Ollama container on same network
        ("docker_network", "http://host.docker.internal:11434"),  # Docker Desktop host
        # 3. Local development
        ("local", "http://localhost:11434"),
        # 4. Kubernetes service discovery
        ("kubernetes", "http://ollama.default.svc.cluster.local:11434"),
        ("kubernetes", "http://ollama.kube-system.svc.cluster.local:11434"),
        # 5. Common remote scenarios (user provides via env var)
    ]

    @staticmethod
    async def test_endpoint(url: str, timeout: float = 3.0) -> bool:
        """
        Test if LLM endpoint is reachable.

        Args:
            url: Endpoint URL to test (e.g., http://localhost:11434)
            timeout: Connection timeout in seconds

        Returns:
            True if endpoint responds, False otherwise
        """
        try:
            import httpx

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"{url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def get_ollama_host() -> str | None:
        """
        Auto-detect Ollama endpoint across deployment scenarios.

        Returns:
            Ollama endpoint URL if found, None otherwise
        """
        # Skip detection in test environment to avoid timeout during CI
        if os.getenv("PYTEST_CURRENT_TEST"):
            logger.debug("Skipping Ollama detection in test environment")
            return None

        logger.debug("Starting Ollama auto-detection...")

        # 1. Check explicit environment variable (highest priority)
        env_host = os.getenv("OLLAMA_HOST")
        if env_host:
            logger.info(f"Ollama endpoint from OLLAMA_HOST env var: {env_host}")
            return env_host

        # 2. Try detection in order with short timeout
        for scenario, endpoint in LLMEnvironmentConfig.OLLAMA_DETECTION_ORDER:
            if scenario == "env_var":
                continue  # Already checked above

            logger.debug(f"Trying {scenario} endpoint: {endpoint}")
            try:
                # Use sync httpx for detection with minimal timeout (0.5s per endpoint)
                import httpx

                response = httpx.get(f"{endpoint}/api/tags", timeout=0.5)
                if response.status_code == 200:
                    logger.info(f"✓ Detected Ollama at {endpoint} ({scenario})")
                    return endpoint
            except Exception as e:
                logger.debug(f"✗ {scenario} endpoint failed: {type(e).__name__}")
                continue

        # 3. Graceful fallback
        logger.debug(
            "Could not auto-detect Ollama. Set OLLAMA_HOST environment variable if needed."
        )
        return None

    @staticmethod
    def get_provider_config() -> dict[str, Any]:
        """
        Get complete LLM provider configuration for current deployment.

        Returns:
            Dict with provider endpoints and status
        """
        ollama_endpoint = LLMEnvironmentConfig.get_ollama_host()
        config = {
            "deployment_scenario": LLMEnvironmentConfig._detect_scenario(),
            "providers": {
                "ollama": {
                    "endpoint": ollama_endpoint,
                    "status": "available" if ollama_endpoint else "unavailable",
                },
                "claude": {
                    "endpoint": "https://api.anthropic.com",
                    "status": "available" if os.getenv("ANTHROPIC_API_KEY") else "needs_api_key",
                },
                "openai": {
                    "endpoint": "https://api.openai.com",
                    "status": "available" if os.getenv("OPENAI_API_KEY") else "needs_api_key",
                },
            },
        }
        return config

    @staticmethod
    def _detect_scenario() -> str:
        """Detect deployment scenario based on environment."""
        # Check for Kubernetes
        if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount"):
            return "kubernetes"

        # Check for Docker
        if os.path.exists("/.dockerenv"):
            if "host.docker.internal" in os.getenv("OLLAMA_HOST", ""):
                return "docker_desktop"
            return "docker_compose"

        # Default to local development
        return "local_development"


def validate_llm_environment() -> dict:
    """
    Validate LLM configuration for current deployment.

    Returns:
        Status dict with validation results and recommendations
    """
    config = LLMEnvironmentConfig.get_provider_config()

    status = {
        "scenario": config["deployment_scenario"],
        "providers": {},
        "issues": [],
        "recommendations": [],
    }

    # Check each provider
    for provider, info in config["providers"].items():
        status["providers"][provider] = {
            "status": info["status"],
            "endpoint": info["endpoint"],
        }

        if info["status"] == "unavailable":
            status["issues"].append(f"{provider}: endpoint not found")
        elif info["status"] == "needs_api_key":
            status["issues"].append(f"{provider}: API key not configured")

    # Provide scenario-specific recommendations
    scenario = config["deployment_scenario"]
    if scenario == "local_development":
        status["recommendations"].append(
            "For Ollama: Start with `ollama serve` or set OLLAMA_HOST if running elsewhere"
        )
    elif scenario == "docker_compose":
        status["recommendations"].append(
            "For Ollama on host: Set OLLAMA_HOST=http://host.docker.internal:11434 "
            "(Mac) or http://<host-ip>:11434 (Linux)"
        )
        status["recommendations"].append(
            "For Ollama in container: Ensure it's on the same Docker network and use "
            "OLLAMA_HOST=http://ollama:11434 (container name)"
        )
    elif scenario == "docker_desktop":
        status["recommendations"].append(
            "Using host.docker.internal - ensure Ollama is running on host machine"
        )
    elif scenario == "kubernetes":
        status["recommendations"].append(
            "Using Kubernetes service discovery - ensure Ollama is deployed as a service"
        )

    return status
