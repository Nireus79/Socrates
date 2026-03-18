"""Tests for socratic_core.config module."""

import os
import tempfile
from pathlib import Path

import pytest

from socratic_core.config import ConfigBuilder, SocratesConfig


class TestSocratesConfig:
    """Tests for SocratesConfig class."""

    def test_default_config(self):
        """Test SocratesConfig with default values."""
        config = SocratesConfig(api_key="test-key")

        assert config.api_key == "test-key"
        assert config.model == "claude-3-sonnet-20240229"
        assert config.data_dir.endswith("socrates_data")
        assert config.log_level == "INFO"
        assert config.cache_enabled is True

    def test_config_with_custom_values(self):
        """Test SocratesConfig with custom values."""
        config = SocratesConfig(
            api_key="test-key",
            model="claude-3-opus-20240229",
            data_dir="/custom/path",
            log_level="DEBUG",
            cache_enabled=False,
            max_workers=2
        )

        assert config.api_key == "test-key"
        assert config.model == "claude-3-opus-20240229"
        assert config.data_dir == "/custom/path"
        assert config.log_level == "DEBUG"
        assert config.cache_enabled is False
        assert config.max_workers == 2

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "api_key": "test-key",
            "model": "claude-3-sonnet-20240229",
            "log_level": "WARNING"
        }
        config = SocratesConfig.from_dict(config_dict)

        assert config.api_key == "test-key"
        assert config.model == "claude-3-sonnet-20240229"
        assert config.log_level == "WARNING"

    def test_config_from_env(self, monkeypatch):
        """Test creating config from environment variables."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
        monkeypatch.setenv("CLAUDE_MODEL", "claude-3-opus-20240229")
        monkeypatch.setenv("SOCRATES_LOG_LEVEL", "ERROR")

        config = SocratesConfig.from_env()

        assert config.api_key == "env-key"
        assert config.model == "claude-3-opus-20240229"
        assert config.log_level == "ERROR"

    def test_config_missing_api_key(self):
        """Test that missing API key raises error."""
        with pytest.raises((ValueError, KeyError)):
            config = SocratesConfig.from_env()
            # Should fail because API key is required

    def test_config_builder_pattern(self):
        """Test ConfigBuilder fluent API."""
        config = (ConfigBuilder("test-key")
                  .with_model("claude-3-opus-20240229")
                  .with_log_level("DEBUG")
                  .with_cache_enabled(False)
                  .build())

        assert config.api_key == "test-key"
        assert config.model == "claude-3-opus-20240229"
        assert config.log_level == "DEBUG"
        assert config.cache_enabled is False

    def test_config_builder_chaining(self):
        """Test ConfigBuilder method chaining."""
        builder = ConfigBuilder("key1")
        builder2 = builder.with_log_level("INFO")

        assert builder is builder2  # Should return self for chaining

    def test_config_data_dir_expansion(self):
        """Test that data_dir expands ~ to home directory."""
        config = SocratesConfig(
            api_key="test",
            data_dir="~/.socrates"
        )

        assert "~" not in str(config.data_dir)
        assert str(config.data_dir).startswith(str(Path.home()))

    def test_config_with_custom_db_path(self):
        """Test custom database path configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            config = SocratesConfig(
                api_key="test",
                db_path=db_path
            )

            assert config.db_path == db_path

    def test_config_validation(self):
        """Test config validation."""
        config = SocratesConfig(api_key="test")

        # Should have required fields
        assert config.api_key
        assert config.model
        assert config.data_dir
        assert config.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_config_json_serialization(self):
        """Test that config can be serialized."""
        config = SocratesConfig(
            api_key="test",
            model="claude-3-sonnet-20240229",
            log_level="INFO"
        )

        # Should be serializable (pydantic model)
        data = config.model_dump()
        assert data["api_key"] == "test"
        assert data["model"] == "claude-3-sonnet-20240229"


class TestConfigBuilder:
    """Tests for ConfigBuilder class."""

    def test_builder_init(self):
        """Test ConfigBuilder initialization."""
        builder = ConfigBuilder("test-key")
        config = builder.build()

        assert config.api_key == "test-key"

    def test_builder_with_model(self):
        """Test setting model via builder."""
        builder = (ConfigBuilder("test")
                   .with_model("claude-3-opus-20240229"))
        config = builder.build()

        assert config.model == "claude-3-opus-20240229"

    def test_builder_with_log_level(self):
        """Test setting log level via builder."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            builder = (ConfigBuilder("test")
                       .with_log_level(level))
            config = builder.build()

            assert config.log_level == level

    def test_builder_with_cache(self):
        """Test enabling/disabling cache."""
        builder_with_cache = (ConfigBuilder("test")
                              .with_cache_enabled(True))
        assert builder_with_cache.build().cache_enabled is True

        builder_without_cache = (ConfigBuilder("test")
                                 .with_cache_enabled(False))
        assert builder_without_cache.build().cache_enabled is False

    def test_builder_with_data_dir(self):
        """Test setting data directory."""
        builder = (ConfigBuilder("test")
                   .with_data_dir("/custom/path"))
        config = builder.build()

        assert config.data_dir == "/custom/path"

    def test_builder_with_max_workers(self):
        """Test setting max workers."""
        builder = (ConfigBuilder("test")
                   .with_max_workers(8))
        config = builder.build()

        assert config.max_workers == 8


class TestConfigEnvironment:
    """Tests for environment variable handling."""

    def test_env_api_key_priority(self, monkeypatch):
        """Test that env API key takes priority."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
        config = SocratesConfig.from_env()
        assert config.api_key == "env-key"

    def test_env_model_override(self, monkeypatch):
        """Test model can be overridden via env."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
        monkeypatch.setenv("CLAUDE_MODEL", "claude-3-opus-20240229")

        config = SocratesConfig.from_env()
        assert config.model == "claude-3-opus-20240229"

    def test_env_log_level_override(self, monkeypatch):
        """Test log level can be overridden via env."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
        monkeypatch.setenv("SOCRATES_LOG_LEVEL", "DEBUG")

        config = SocratesConfig.from_env()
        assert config.log_level == "DEBUG"

    def test_env_data_dir_override(self, monkeypatch):
        """Test data dir can be overridden via env."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
        monkeypatch.setenv("SOCRATES_DATA_DIR", "/custom")

        config = SocratesConfig.from_env()
        assert config.data_dir == "/custom"
