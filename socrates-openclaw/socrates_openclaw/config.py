# socrates_openclaw/config.py

"""
Configuration module for Socrates AI OpenClaw integration.

Handles paths, settings, and environment variables.
"""

import os
from pathlib import Path
from typing import Optional


class SocraticConfig:
    """Configuration for Socratic Discovery Skill."""

    def __init__(
            self,
            workspace_root: Optional[Path] = None,
            model: Optional[str] = None,
            temperature: Optional[float] = None,
    ):
        """
        Initialize Socratic configuration.

        Args:
            workspace_root: Root workspace directory (default: ~/.openclaw/workspace)
            model: Claude model to use (default: claude-opus-4-6)
            temperature: Model temperature (default: 0.7)
        """
        # Workspace paths
        if workspace_root is None:
            workspace_root = Path.home() / ".openclaw" / "workspace"

        self.workspace_root = Path(workspace_root)
        self.projects_dir = self.workspace_root / "projects"
        self.vectors_dir = self.workspace_root / ".socrates-vectors"
        self.kb_dir = self.workspace_root / ".socrates-kb"
        self.sessions_file = self.workspace_root / ".socratic-sessions.json"

        # Create directories if they don't exist
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.vectors_dir.mkdir(parents=True, exist_ok=True)
        self.kb_dir.mkdir(parents=True, exist_ok=True)

        # Model settings
        self.model = model or os.getenv("SOCRATIC_MODEL", "claude-opus-4-6")
        self.temperature = temperature or float(os.getenv("SOCRATIC_TEMPERATURE", "0.7"))

        # Discovery parameters
        self.min_responses_for_spec = int(os.getenv("SOCRATIC_MIN_RESPONSES", "4"))
        self.max_responses = int(os.getenv("SOCRATIC_MAX_RESPONSES", "20"))
        self.questions_per_phase = int(os.getenv("SOCRATIC_QUESTIONS_PER_PHASE", "8"))

        # Debug mode
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

    def __repr__(self) -> str:
        """String representation of config."""
        return (
            f"SocraticConfig("
            f"workspace_root={self.workspace_root}, "
            f"model={self.model}, "
            f"temperature={self.temperature}, "
            f"debug={self.debug}"
            ")"
        )


# Global configuration instance
_config: Optional[SocraticConfig] = None


def get_config() -> SocraticConfig:
    """Get or create global configuration instance."""
    global _config
    if _config is None:
        _config = SocraticConfig()
    return _config


def set_config(config: SocraticConfig) -> None:
    """Set global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset global configuration to defaults."""
    global _config
    _config = None


# Export for convenience
__all__ = [
    "SocraticConfig",
    "get_config",
    "set_config",
    "reset_config",
]
