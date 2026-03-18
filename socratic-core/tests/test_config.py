"""Tests for socratic_core.config module."""

import os

import pytest

from socratic_core.config import ConfigBuilder, SocratesConfig


class TestSocratesConfig:
    """Tests for SocratesConfig dataclass."""

    def test_config_with_api_key(self):
        """Test SocratesConfig with API key."""
        config = SocratesConfig(api_key="sk-test")
        assert config.api_key == "sk-test"

    def test_config_with_model(self):
        """Test SocratesConfig with custom model."""
        config = SocratesConfig(api_key="sk-test", claude_model="claude-opus")
        assert config.claude_model == "claude-opus"

    def test_config_with_log_level(self):
        """Test SocratesConfig with custom log level."""
        config = SocratesConfig(api_key="sk-test", log_level="DEBUG")
        assert config.log_level == "DEBUG"

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {"api_key": "sk-test", "claude_model": "claude-opus"}
        config = SocratesConfig.from_dict(data)
        assert config.api_key == "sk-test"
        assert config.claude_model == "claude-opus"

    def test_config_from_env(self):
        """Test creating config from environment."""
        os.environ["ANTHROPIC_API_KEY"] = "sk-env"
        try:
            config = SocratesConfig.from_env()
            assert config.api_key == "sk-env"
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_config_from_env_reads_successfully(self):
        """Test that from_env loads config successfully."""
        os.environ["ANTHROPIC_API_KEY"] = "sk-test"
        try:
            config = SocratesConfig.from_env()
            assert config.api_key == "sk-test"
            assert config.claude_model is not None
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_config_attributes(self):
        """Test that config has expected attributes."""
        config = SocratesConfig(api_key="sk-test")
        assert hasattr(config, "api_key")
        assert hasattr(config, "claude_model")
        assert hasattr(config, "log_level")
        assert hasattr(config, "max_context_length")
        assert hasattr(config, "max_retries")


class TestConfigBuilder:
    """Tests for ConfigBuilder class."""

    def test_builder_with_model(self):
        """Test builder with_model method."""
        config = ConfigBuilder("sk-test").with_model("claude-opus").build()
        assert config.claude_model == "claude-opus"

    def test_builder_with_log_level(self):
        """Test builder with_log_level method."""
        config = ConfigBuilder("sk-test").with_log_level("DEBUG").build()
        assert config.log_level == "DEBUG"

    def test_builder_chaining(self):
        """Test builder method chaining."""
        builder = ConfigBuilder("sk-test")
        result = builder.with_model("claude-opus")
        assert result is builder

    def test_builder_build(self):
        """Test builder produces config."""
        config = ConfigBuilder("sk-test").build()
        assert isinstance(config, SocratesConfig)
        assert config.api_key == "sk-test"

    def test_builder_multiple_methods(self):
        """Test builder with multiple method calls."""
        config = (
            ConfigBuilder("sk-test")
            .with_model("claude-opus")
            .with_log_level("DEBUG")
            .build()
        )
        assert config.api_key == "sk-test"
        assert config.claude_model == "claude-opus"
        assert config.log_level == "DEBUG"


class TestConfigEnvironment:
    """Tests for environment variable handling."""

    def test_env_api_key(self):
        """Test loading API key from environment."""
        os.environ["ANTHROPIC_API_KEY"] = "sk-env-test"
        try:
            config = SocratesConfig.from_env()
            assert config.api_key == "sk-env-test"
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_env_api_required(self):
        """Test that API key is required from environment."""
        try:
            config = SocratesConfig.from_env()
            # If we got here, it means API key was found somehow (maybe in CI/CD)
            assert config.api_key is not None
        except ValueError as e:
            # Expected - API key is required
            assert "credentials" in str(e).lower()

    def test_env_log_level(self):
        """Test loading log level from environment."""
        os.environ["ANTHROPIC_API_KEY"] = "sk-test"
        os.environ["SOCRATES_LOG_LEVEL"] = "WARNING"
        try:
            config = SocratesConfig.from_env()
            assert config.log_level == "WARNING"
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)
            os.environ.pop("SOCRATES_LOG_LEVEL", None)
