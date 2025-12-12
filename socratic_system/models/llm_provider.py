"""
LLM Provider models for multi-provider LLM management.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class LLMProviderConfig:
    """Configuration for an LLM provider."""

    id: str
    provider: str  # claude, openai, gemini, ollama
    user_id: str
    is_default: bool = False
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())

    # Provider-specific settings
    settings: Dict[str, Any] = field(default_factory=dict)
    # Example settings: {
    #   "model": "claude-3-sonnet-20240229",
    #   "max_tokens": 4096,
    #   "temperature": 0.7,
    #   "api_endpoint": "https://api.openai.com/v1"  (for custom endpoints)
    # }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "LLMProviderConfig":
        """Create from dictionary."""
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return LLMProviderConfig(**data)


@dataclass
class APIKeyRecord:
    """Encrypted API key storage."""

    id: str
    user_id: str
    provider: str  # claude, openai, gemini, ollama
    encrypted_key: str
    key_hash: str  # Hash for verification without decryption
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())
    last_used_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (never include encrypted_key in output)."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provider": self.provider,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "APIKeyRecord":
        """Create from dictionary."""
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("last_used_at") and isinstance(data["last_used_at"], str):
            data["last_used_at"] = datetime.fromisoformat(data["last_used_at"])
        return APIKeyRecord(**data)


@dataclass
class LLMUsageRecord:
    """Tracks LLM usage and costs."""

    id: str
    user_id: str
    provider: str
    model: str
    timestamp: datetime = field(default_factory=lambda: datetime.now())
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    cost: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    request_id: Optional[str] = None  # For tracking

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provider": self.provider,
            "model": self.model,
            "timestamp": self.timestamp.isoformat(),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "cost": self.cost,
            "success": self.success,
            "error_message": self.error_message,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "LLMUsageRecord":
        """Create from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return LLMUsageRecord(**data)


@dataclass
class ProviderMetadata:
    """Metadata about available LLM providers."""

    provider: str
    display_name: str
    models: List[str]
    requires_api_key: bool
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    context_window: int
    supports_streaming: bool = True
    supports_vision: bool = False
    available: bool = True
    description: str = ""
    base_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ProviderMetadata":
        """Create from dictionary."""
        return ProviderMetadata(**data)


# Predefined provider metadata
PROVIDER_METADATA = {
    "claude": ProviderMetadata(
        provider="claude",
        display_name="Anthropic Claude",
        models=[
            "claude-haiku-4-5-20251001",
            "claude-3-5-sonnet-20241022",
            "claude-opus-4-20250514",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
        ],
        requires_api_key=False,  # Uses environment variable
        cost_per_1k_input_tokens=0.000800,  # Haiku: $0.80 per 1M input
        cost_per_1k_output_tokens=0.004000,  # Haiku: $4.00 per 1M output
        context_window=200000,
        supports_streaming=True,
        supports_vision=True,
        available=True,
        description="Fast and efficient Claude models by Anthropic (Haiku is default)",
    ),
    "openai": ProviderMetadata(
        provider="openai",
        display_name="OpenAI",
        models=["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
        requires_api_key=True,
        cost_per_1k_input_tokens=0.01,
        cost_per_1k_output_tokens=0.03,
        context_window=128000,
        supports_streaming=True,
        supports_vision=True,
        available=True,
        description="Advanced OpenAI GPT models",
    ),
    "gemini": ProviderMetadata(
        provider="gemini",
        display_name="Google Gemini",
        models=["gemini-pro", "gemini-pro-vision"],
        requires_api_key=True,
        cost_per_1k_input_tokens=0.0005,
        cost_per_1k_output_tokens=0.0015,
        context_window=32000,
        supports_streaming=True,
        supports_vision=True,
        available=True,
        description="Google's Gemini models",
    ),
    "ollama": ProviderMetadata(
        provider="ollama",
        display_name="Ollama (Local)",
        models=["llama2", "mistral", "neural-chat", "orca-mini"],
        requires_api_key=False,
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        context_window=8000,
        supports_streaming=True,
        supports_vision=False,
        available=True,
        base_url="http://localhost:11434",
        description="Run models locally with Ollama",
    ),
}


def get_provider_metadata(provider: str) -> Optional[ProviderMetadata]:
    """Get metadata for a provider."""
    return PROVIDER_METADATA.get(provider.lower())


def list_available_providers() -> List[ProviderMetadata]:
    """Get all available providers."""
    return list(PROVIDER_METADATA.values())
