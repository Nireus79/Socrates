"""Pytest configuration and fixtures."""

import os

import pytest


@pytest.fixture
def temp_data_dir(tmp_path):
    """Fixture providing a temporary data directory."""
    return str(tmp_path)


@pytest.fixture
def temp_db_path(tmp_path):
    """Fixture providing a temporary database path."""
    return str(tmp_path / "test.db")


@pytest.fixture(autouse=True)
def cleanup_env():
    """Clean up environment variables after tests."""
    # Store original env vars
    original_env = os.environ.copy()

    yield

    # Restore env vars
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_config_dict():
    """Fixture providing a sample configuration dictionary."""
    return {
        "api_key": "test-key",
        "model": "claude-3-sonnet-20240229",
        "data_dir": "/tmp/socrates_test",
        "log_level": "INFO",
        "cache_enabled": True,
    }
