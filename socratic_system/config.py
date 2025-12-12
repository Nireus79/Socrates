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

    def _ensure_path(self, path_value: Union[str, Path, None], default_path: Path) -> Path:
        """Convert path value to Path object"""
        if path_value is None:
            return default_path
        elif isinstance(path_value, str):
            return Path(path_value)
        else:
            return path_value

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
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def __post_init__(self) -> None:
        """Initialize derived paths and create directories"""
        # Ensure data_dir is a Path object
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)

        # Initialize derived paths if not explicitly set
        self.projects_db_path = self._ensure_path(
            self.projects_db_path, self.data_dir / "projects.db"
        )
        self.vector_db_path = self._ensure_path(self.vector_db_path, self.data_dir / "vector_db")
        self.log_file = self._ensure_path(self.log_file, self.data_dir / "logs" / "socrates.log")

        # Set knowledge_base_path if not explicitly set
        self._setup_knowledge_base_path()

        # Create directories
        self._create_directories()

    @classmethod
    def from_env(cls, **overrides) -> "SocratesConfig":
        """
        Create configuration from environment variables.

        Environment variables:
            ANTHROPIC_API_KEY or API_KEY_CLAUDE: Claude API key (required)
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
        api_key = os.getenv("ANTHROPIC_API_KEY", os.getenv("API_KEY_CLAUDE"))
        if not api_key:
            raise ValueError(
                "API key required. Set ANTHROPIC_API_KEY or API_KEY_CLAUDE environment variable"
            )

        config_dict = {
            "api_key": api_key,
            "claude_model": os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
            "data_dir": Path(os.getenv("SOCRATES_DATA_DIR", Path.home() / ".socrates")),
            "log_level": os.getenv("SOCRATES_LOG_LEVEL", "INFO"),
        }

        log_file = os.getenv("SOCRATES_LOG_FILE")
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


class ConfigBuilder:
    """
    Fluent builder for SocratesConfig.

    Example:
        >>> config = ConfigBuilder("sk-ant-...") \\
        ...     .with_data_dir("/path/to/data") \\
        ...     .with_model("claude-opus-4-1-20250805") \\
        ...     .with_log_level("DEBUG") \\
        ...     .build()
    """

    def __init__(self, api_key: str):
        """Initialize builder with required API key"""
        self._config_dict: Dict[str, Any] = {"api_key": api_key}

    def with_data_dir(self, path: Path) -> "ConfigBuilder":
        """Set data directory"""
        self._config_dict["data_dir"] = path
        return self

    def with_model(self, model_name: str) -> "ConfigBuilder":
        """Set Claude model"""
        self._config_dict["claude_model"] = model_name
        return self

    def with_embedding_model(self, model_name: str) -> "ConfigBuilder":
        """Set embedding model"""
        self._config_dict["embedding_model"] = model_name
        return self

    def with_knowledge_base(self, path: Path) -> "ConfigBuilder":
        """Set knowledge base path"""
        self._config_dict["knowledge_base_path"] = path
        return self

    def with_custom_knowledge(self, knowledge_list: List[str]) -> "ConfigBuilder":
        """Set custom knowledge entries"""
        self._config_dict["custom_knowledge"] = knowledge_list
        return self

    def with_log_level(self, level: str) -> "ConfigBuilder":
        """Set logging level (DEBUG, INFO, WARNING, ERROR)"""
        self._config_dict["log_level"] = level
        return self

    def with_log_file(self, path: Path) -> "ConfigBuilder":
        """Set log file path"""
        self._config_dict["log_file"] = path
        return self

    def with_max_retries(self, retries: int) -> "ConfigBuilder":
        """Set maximum number of retries"""
        self._config_dict["max_retries"] = retries
        return self

    def build(self) -> SocratesConfig:
        """Build the SocratesConfig instance"""
        return SocratesConfig.from_dict(self._config_dict)


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


# Backward compatibility - CONFIG will be populated when needed
CONFIG = _get_legacy_config()
