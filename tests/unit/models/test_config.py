"""
Unit tests for Socrates configuration system
"""

import os
from unittest.mock import patch

import pytest

from socratic_system.config import ConfigBuilder, SocratesConfig


@pytest.mark.unit
class TestSocratesConfig:
    """Tests for SocratesConfig dataclass"""

    def test_config_creation_with_api_key(self, mock_api_key):
        """Test creating config with just API key"""
        config = SocratesConfig(api_key=mock_api_key)

        assert config.api_key == mock_api_key
        assert config.claude_model == "claude-haiku-4-5-20251001"
        assert config.embedding_model == "all-MiniLM-L6-v2"
        assert config.log_level == "INFO"

    def test_config_defaults(self, test_config):
        """Test that config has sensible defaults"""
        assert test_config.max_context_length == 8000
        assert test_config.max_retries == 3
        assert test_config.session_timeout == 3600
        assert test_config.token_warning_threshold == 0.8

    def test_config_data_dir_creation(self, temp_data_dir, mock_api_key):
        """Test that data directories are created"""
        config = SocratesConfig(api_key=mock_api_key, data_dir=temp_data_dir / "test_socrates")

        assert config.data_dir.exists()
        assert config.projects_db_path.parent.exists()  # Check parent directory exists
        assert config.vector_db_path.exists()

    def test_config_custom_paths(self, temp_data_dir, mock_api_key):
        """Test configuration with custom paths"""
        custom_db = temp_data_dir / "custom.db"
        custom_vector = temp_data_dir / "custom_vector"

        config = SocratesConfig(
            api_key=mock_api_key,
            data_dir=temp_data_dir,
            projects_db_path=custom_db,
            vector_db_path=custom_vector,
        )

        assert config.projects_db_path == custom_db
        assert config.vector_db_path == custom_vector

    def test_config_from_env(self, mock_api_key, temp_data_dir):
        """Test loading config from environment variables"""
        with patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": mock_api_key,
                "SOCRATES_DATA_DIR": str(temp_data_dir),
                "SOCRATES_LOG_LEVEL": "DEBUG",
            },
        ):
            config = SocratesConfig.from_env()

            assert config.api_key == mock_api_key
            assert str(config.data_dir) == str(temp_data_dir)
            assert config.log_level == "DEBUG"

    def test_config_from_env_with_overrides(self, mock_api_key, temp_data_dir):
        """Test loading config from env with overrides"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": mock_api_key}):
            config = SocratesConfig.from_env(data_dir=temp_data_dir, log_level="ERROR")

            assert config.api_key == mock_api_key
            assert config.data_dir == temp_data_dir
            assert config.log_level == "ERROR"

    def test_config_from_dict(self, mock_api_key):
        """Test creating config from dictionary"""
        config_dict = {
            "api_key": mock_api_key,
            "claude_model": "claude-opus-4-5-20251101",
            "log_level": "DEBUG",
        }

        config = SocratesConfig.from_dict(config_dict)

        assert config.api_key == mock_api_key
        assert config.claude_model == "claude-opus-4-5-20251101"
        assert config.log_level == "DEBUG"

    def test_config_to_legacy_dict(self, test_config):
        """Test converting config to legacy format"""
        legacy = test_config.get_legacy_config_dict()

        assert "ANTHROPIC_API_KEY" in legacy
        assert "CLAUDE_MODEL" in legacy
        assert "DATA_DIR" in legacy

    def test_config_missing_api_key_raises_error(self):
        """Test that missing API key raises error"""
        with pytest.raises((ValueError, TypeError)):
            SocratesConfig(api_key=None)

    def test_config_invalid_log_level(self, mock_api_key):
        """Test that invalid log level is handled"""
        # Should not raise, but log level might not be validated at dataclass level
        config = SocratesConfig(api_key=mock_api_key, log_level="INVALID")
        assert config.log_level == "INVALID"

    def test_config_custom_knowledge_list(self, mock_api_key, temp_data_dir):
        """Test config with custom knowledge base"""
        knowledge = ["knowledge1.md", "knowledge2.txt"]
        config = SocratesConfig(
            api_key=mock_api_key, data_dir=temp_data_dir, custom_knowledge=knowledge
        )

        assert config.custom_knowledge == knowledge


@pytest.mark.unit
class TestConfigBuilder:
    """Tests for ConfigBuilder fluent API"""

    def test_builder_creates_config(self, mock_api_key):
        """Test basic builder usage"""
        config = ConfigBuilder(mock_api_key).build()

        assert config.api_key == mock_api_key

    def test_builder_with_data_dir(self, mock_api_key, temp_data_dir):
        """Test builder with data directory"""
        config = ConfigBuilder(mock_api_key).with_data_dir(temp_data_dir).build()

        assert config.data_dir == temp_data_dir

    def test_builder_with_model(self, mock_api_key):
        """Test builder with custom model"""
        config = ConfigBuilder(mock_api_key).with_model("claude-opus-4-5-20251101").build()

        assert config.claude_model == "claude-opus-4-5-20251101"

    def test_builder_with_log_level(self, mock_api_key):
        """Test builder with log level"""
        config = ConfigBuilder(mock_api_key).with_log_level("DEBUG").build()

        assert config.log_level == "DEBUG"

    def test_builder_with_knowledge_base(self, mock_api_key, temp_data_dir):
        """Test builder with knowledge base path"""
        kb_path = temp_data_dir / "knowledge_base.md"
        config = ConfigBuilder(mock_api_key).with_knowledge_base(kb_path).build()

        assert kb_path in config.custom_knowledge or kb_path == config.knowledge_base_path

    def test_builder_fluent_chain(self, mock_api_key, temp_data_dir):
        """Test builder method chaining"""
        config = (
            ConfigBuilder(mock_api_key)
            .with_data_dir(temp_data_dir)
            .with_model("claude-opus-4-5-20251101")
            .with_log_level("DEBUG")
            .build()
        )

        assert config.api_key == mock_api_key
        assert config.data_dir == temp_data_dir
        assert config.claude_model == "claude-opus-4-5-20251101"
        assert config.log_level == "DEBUG"

    def test_builder_returns_self(self, mock_api_key):
        """Test that builder methods return self for chaining"""
        builder = ConfigBuilder(mock_api_key)

        assert isinstance(builder.with_model("test"), ConfigBuilder)
        assert isinstance(builder.with_log_level("INFO"), ConfigBuilder)


@pytest.mark.unit
class TestConfigValidation:
    """Tests for config validation"""

    def test_config_with_log_file(self, mock_api_key, temp_data_dir):
        """Test config with log file path"""
        log_file = temp_data_dir / "socrates.log"
        config = SocratesConfig(api_key=mock_api_key, log_file=log_file)

        assert config.log_file == log_file

    def test_config_token_warning_threshold(self, mock_api_key):
        """Test token warning threshold configuration"""
        config = SocratesConfig(api_key=mock_api_key, token_warning_threshold=0.9)

        assert config.token_warning_threshold == 0.9

    def test_config_session_timeout(self, mock_api_key):
        """Test session timeout configuration"""
        config = SocratesConfig(api_key=mock_api_key, session_timeout=7200)

        assert config.session_timeout == 7200

    def test_config_retry_settings(self, mock_api_key):
        """Test retry configuration"""
        config = SocratesConfig(api_key=mock_api_key, max_retries=5, retry_delay=2.0)

        assert config.max_retries == 5
        assert config.retry_delay == 2.0


@pytest.mark.unit
class TestConfigEnvironmentVariables:
    """Tests for environment variable handling"""

    def test_anthropic_api_key_env_var(self, temp_data_dir):
        """Test ANTHROPIC_API_KEY environment variable"""
        test_key = "sk-ant-env-test-key"
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": test_key}):
            config = SocratesConfig.from_env()
            assert config.api_key == test_key

    def test_socrates_data_dir_env_var(self, mock_api_key, temp_data_dir):
        """Test SOCRATES_DATA_DIR environment variable"""
        with patch.dict(os.environ, {"SOCRATES_DATA_DIR": str(temp_data_dir)}):
            config = SocratesConfig.from_env(api_key=mock_api_key)
            assert config.data_dir == temp_data_dir

    def test_socrates_log_level_env_var(self, mock_api_key):
        """Test SOCRATES_LOG_LEVEL environment variable"""
        with patch.dict(os.environ, {"SOCRATES_LOG_LEVEL": "WARNING"}):
            config = SocratesConfig.from_env(api_key=mock_api_key)
            assert config.log_level == "WARNING"

    def test_missing_api_key_env_var(self):
        """Test that missing API key is handled"""
        # Remove ANTHROPIC_API_KEY and API_KEY_CLAUDE from environment
        env_vars_to_remove = ["ANTHROPIC_API_KEY", "API_KEY_CLAUDE", "ANTHROPIC_SUBSCRIPTION_TOKEN"]
        with patch.dict(os.environ, {}, clear=False):
            for var in env_vars_to_remove:
                os.environ.pop(var, None)
            with pytest.raises(ValueError):
                SocratesConfig.from_env()
