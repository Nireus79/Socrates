"""
Socrates Configuration System

Supports three initialization methods:
1. From environment variables
2. From dictionary
3. Using ConfigBuilder (fluent API)

Examples:
    >>> config = SocratesConfig.from_env()
    >>> config = SocratesConfig.from_dict({"api_key": "sk-...", "data_dir": "/path"})
    >>> config = ConfigBuilder("sk-...").with_data_dir("/path").build()
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class SocratesConfig:
    """
    Socrates configuration with sensible defaults and flexible customization.

    Attributes:
        api_key: Claude API key (required)
        claude_model: Claude model to use
        data_dir: Directory for storing projects and databases
        projects_db_path: Path to projects database
        vector_db_path: Path to vector database
        knowledge_base_path: Path to knowledge base configuration
        embedding_model: Model for generating embeddings
        max_context_length: Maximum context length for prompts
        max_retries: Maximum number of API retries
        retry_delay: Delay between retries in seconds
        token_warning_threshold: Threshold for token usage warnings (0-1)
        session_timeout: Session timeout in seconds
        log_level: Logging level
        log_file: Path to log file (None = no file logging)
        custom_knowledge: List of custom knowledge entries
    """

    # API Configuration
    api_key: str
    subscription_token: Optional[str] = (
        None  # Alternative: use Claude subscription instead of API key
    )

    # Model Configuration
    claude_model: str = "claude-haiku-4-5-20251001"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Storage Configuration
    data_dir: Path = field(default_factory=lambda: Path.home() / ".socrates")
    projects_db_path: Optional[Path] = None
    vector_db_path: Optional[Path] = None
    knowledge_base_path: Optional[Path] = None

    # Behavior Configuration
    max_context_length: int = 8000
    max_retries: int = 3
    retry_delay: float = 1.0
    token_warning_threshold: float = 0.8
    session_timeout: int = 3600

    # Logging Configuration
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    # Custom Knowledge
    custom_knowledge: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize derived paths and create directories"""
        self._validate_api_key()
        self._ensure_data_dir_is_path()
        self._initialize_derived_paths()
        self._validate_all_paths()
        self._setup_knowledge_base_path()
        self._create_directories()

    def _validate_api_key(self) -> None:
        """Validate that API key is provided and non-empty"""
        if not self.api_key or not self.api_key.strip():
            raise ValueError("api_key is required and cannot be empty")

    def _ensure_data_dir_is_path(self) -> None:
        """Ensure data_dir is a Path object"""
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        elif not isinstance(self.data_dir, Path):
            raise TypeError(f"data_dir must be str or Path, got {type(self.data_dir)}")

    def _initialize_derived_paths(self) -> None:
        """Initialize derived paths if not explicitly set"""
        if self.projects_db_path is None:
            self.projects_db_path = self.data_dir / "projects.db"
        elif isinstance(self.projects_db_path, str):
            self.projects_db_path = Path(self.projects_db_path)

        if self.vector_db_path is None:
            self.vector_db_path = self.data_dir / "vector_db"
        elif isinstance(self.vector_db_path, str):
            self.vector_db_path = Path(self.vector_db_path)

        if self.log_file is None:
            self.log_file = self.data_dir / "logs" / "socrates.log"
        elif isinstance(self.log_file, str):
            self.log_file = Path(self.log_file)

    def _validate_all_paths(self) -> None:
        """Validate all paths are now Path objects"""
        if not isinstance(self.projects_db_path, Path):
            raise TypeError(f"projects_db_path must be Path, got {type(self.projects_db_path)}")
        if not isinstance(self.vector_db_path, Path):
            raise TypeError(f"vector_db_path must be Path, got {type(self.vector_db_path)}")
        if not isinstance(self.log_file, Path):
            raise TypeError(f"log_file must be Path, got {type(self.log_file)}")

    def _setup_knowledge_base_path(self) -> None:
        """Set knowledge_base_path if not explicitly set"""
        if self.knowledge_base_path is None:
            current_dir = Path(__file__).parent
            config_dir = current_dir.parent / "config"
            if config_dir.exists():
                kb_path = config_dir / "knowledge_base.json"
                if kb_path.exists():
                    self.knowledge_base_path = kb_path

    def _create_directories(self) -> None:
        """Create required directories"""
        if not isinstance(self.data_dir, Path):
            raise TypeError(f"data_dir must be a Path object, got {type(self.data_dir)}")

        self.data_dir.mkdir(parents=True, exist_ok=True)

        if self.vector_db_path and isinstance(self.vector_db_path, Path):
            self.vector_db_path.mkdir(parents=True, exist_ok=True)

        if self.log_file and isinstance(self.log_file, Path):
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls, **overrides) -> "SocratesConfig":
        """
        Create configuration from environment variables.

        Environment variables:
            ANTHROPIC_API_KEY or API_KEY_CLAUDE: Claude API key (required)
            ANTHROPIC_SUBSCRIPTION_TOKEN: Optional - Claude subscription token for subscription-based auth
            CLAUDE_MODEL: Model name
            SOCRATES_DATA_DIR: Data directory
            SOCRATES_LOG_LEVEL: Logging level
            SOCRATES_LOG_FILE: Log file path

        Args:
            **overrides: Override specific settings

        Returns:
            Configured SocratesConfig instance

        Raises:
            ValueError: If required API key is not found
        """
        config_dict = {
            "api_key": overrides.get("api_key")
            or os.getenv("ANTHROPIC_API_KEY", os.getenv("API_KEY_CLAUDE")),
            "claude_model": overrides.get("claude_model")
            or os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
            "data_dir": overrides.get("data_dir")
            or Path(os.getenv("SOCRATES_DATA_DIR", Path.home() / ".socrates")),
            "log_level": overrides.get("log_level") or os.getenv("SOCRATES_LOG_LEVEL", "INFO"),
        }

        # Check api_key after considering overrides
        if not config_dict["api_key"]:
            raise ValueError(
                "API key required. Set ANTHROPIC_API_KEY or API_KEY_CLAUDE environment variable"
            )

        # Optional subscription token (alternative auth method)
        subscription_token = overrides.get("subscription_token") or os.getenv(
            "ANTHROPIC_SUBSCRIPTION_TOKEN"
        )
        if subscription_token:
            config_dict["subscription_token"] = subscription_token

        log_file = overrides.get("log_file") or os.getenv("SOCRATES_LOG_FILE")
        if log_file:
            config_dict["log_file"] = Path(log_file)

        config_dict.update(overrides)
        return cls(**config_dict)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SocratesConfig":
        """
        Create configuration from a dictionary.

        Args:
            config_dict: Dictionary with configuration values

        Returns:
            Configured SocratesConfig instance

        Raises:
            ValueError: If required fields are missing
        """
        if "api_key" not in config_dict:
            raise ValueError("api_key is required in configuration")

        return cls(**config_dict)

    def get_legacy_config_dict(self) -> Dict[str, Any]:
        """
        Get configuration in legacy dictionary format for backward compatibility.

        Returns:
            Dictionary with legacy config format
        """
        return {
            "ANTHROPIC_API_KEY": self.api_key,
            "MAX_CONTEXT_LENGTH": self.max_context_length,
            "EMBEDDING_MODEL": self.embedding_model,
            "CLAUDE_MODEL": self.claude_model,
            "MAX_RETRIES": self.max_retries,
            "RETRY_DELAY": self.retry_delay,
            "TOKEN_WARNING_THRESHOLD": self.token_warning_threshold,
            "SESSION_TIMEOUT": self.session_timeout,
            "DATA_DIR": str(self.data_dir),
            "PROJECTS_DB_PATH": str(self.projects_db_path),
            "VECTOR_DB_PATH": str(self.vector_db_path),
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"SocratesConfig("
            f"model={self.claude_model}, "
            f"data_dir={self.data_dir}, "
            f"log_level={self.log_level})"
        )


# Legacy CONFIG dictionary for backward compatibility with existing code
def _get_legacy_config() -> Dict[str, Any]:
    """Get legacy config dictionary - only works if environment is configured"""
    try:
        config = SocratesConfig.from_env()
        return config.get_legacy_config_dict()
    except ValueError:
        # Return defaults if API key not configured
        return {
            "MAX_CONTEXT_LENGTH": 8000,
            "EMBEDDING_MODEL": "all-MiniLM-L6-v2",
            "CLAUDE_MODEL": "claude-haiku-4-5-20251001",
            "MAX_RETRIES": 3,
            "RETRY_DELAY": 1,
            "TOKEN_WARNING_THRESHOLD": 0.8,
            "SESSION_TIMEOUT": 3600,
            "DATA_DIR": str(Path.home() / ".socrates"),
        }


class ConfigBuilder:
    """
    Fluent API for building SocratesConfig instances.

    Example:
        config = (ConfigBuilder("sk-...")
                  .with_data_dir("/path")
                  .with_model("claude-opus-4-5-20251101")
                  .build())
    """

    def __init__(self, api_key: str) -> None:
        """Initialize builder with API key"""
        self._config_dict: Dict[str, Any] = {"api_key": api_key}

    def with_data_dir(self, data_dir: Union[str, Path]) -> "ConfigBuilder":
        """Set data directory"""
        self._config_dict["data_dir"] = data_dir
        return self

    def with_model(self, model: str) -> "ConfigBuilder":
        """Set Claude model"""
        self._config_dict["claude_model"] = model
        return self

    def with_embedding_model(self, model: str) -> "ConfigBuilder":
        """Set embedding model"""
        self._config_dict["embedding_model"] = model
        return self

    def with_log_level(self, level: str) -> "ConfigBuilder":
        """Set log level"""
        self._config_dict["log_level"] = level
        return self

    def with_log_file(self, log_file: Union[str, Path]) -> "ConfigBuilder":
        """Set log file path"""
        self._config_dict["log_file"] = log_file
        return self

    def with_knowledge_base(self, kb_path: Union[str, Path]) -> "ConfigBuilder":
        """Set knowledge base path"""
        self._config_dict["knowledge_base_path"] = kb_path
        return self

    def with_custom_knowledge(self, knowledge: List[str]) -> "ConfigBuilder":
        """Set custom knowledge entries"""
        self._config_dict["custom_knowledge"] = knowledge
        return self

    def with_max_context_length(self, length: int) -> "ConfigBuilder":
        """Set max context length"""
        self._config_dict["max_context_length"] = length
        return self

    def with_max_retries(self, retries: int) -> "ConfigBuilder":
        """Set max retries"""
        self._config_dict["max_retries"] = retries
        return self

    def with_retry_delay(self, delay: float) -> "ConfigBuilder":
        """Set retry delay"""
        self._config_dict["retry_delay"] = delay
        return self

    def with_subscription_token(self, token: str) -> "ConfigBuilder":
        """Set subscription token"""
        self._config_dict["subscription_token"] = token
        return self

    def build(self) -> SocratesConfig:
        """Build and return the SocratesConfig instance"""
        return SocratesConfig(**self._config_dict)


# Backward compatibility - CONFIG will be populated when needed
CONFIG = _get_legacy_config()
