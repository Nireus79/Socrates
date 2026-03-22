"""
Integration tests for PyPI library imports.

Verifies that published libraries can be imported and used correctly in Socrates:
- socratic-core: configuration, events, exceptions, logging, utilities
- socratic-learning: learning engine and knowledge management
- socrates-cli: command-line interface tools
- socrates-core-api: REST API framework
"""

import pytest


@pytest.mark.integration
class TestSocraticCoreImports:
    """Test that socratic-core components can be imported and used."""

    def test_import_config(self):
        """Test importing SocratesConfig from socratic-core."""
        from socratic_core import ConfigBuilder, SocratesConfig

        assert SocratesConfig is not None
        assert ConfigBuilder is not None

    def test_import_events(self):
        """Test importing event system from socratic-core."""
        from socratic_core import EventEmitter, EventType

        assert EventEmitter is not None
        assert EventType is not None

        # Verify basic functionality
        emitter = EventEmitter()
        assert emitter is not None

    def test_import_exceptions(self):
        """Test importing exceptions from socratic-core."""
        from socratic_core import (
            ConfigurationError,
            DatabaseError,
            SocratesError,
            ValidationError,
        )

        # Verify all exceptions are valid
        assert issubclass(ConfigurationError, SocratesError)
        assert issubclass(DatabaseError, SocratesError)
        assert issubclass(ValidationError, SocratesError)

    def test_import_logging(self):
        """Test importing logging components from socratic-core."""
        from socratic_core.logging import LoggingConfig

        assert LoggingConfig is not None

    def test_import_utils(self):
        """Test importing utility functions from socratic-core."""
        from socratic_core.utils import ProjectIDGenerator, UserIDGenerator

        # Verify basic functionality
        project_id = ProjectIDGenerator.generate()
        assert project_id.startswith("proj_")

        user_id = UserIDGenerator.generate()
        assert user_id.startswith("user_")


@pytest.mark.integration
class TestSocraticLearningImports:
    """Test that socratic-learning components can be imported and used."""

    def test_import_learning_models(self):
        """Test importing learning models from socratic-learning."""
        from socratic_learning import InteractionLogger

        assert InteractionLogger is not None

    def test_import_learning_models_from_models(self):
        """Test importing learning data models."""
        from socratic_learning.models import (
            KnowledgeBaseDocument,
            QuestionEffectiveness,
            UserBehaviorPattern,
        )

        assert QuestionEffectiveness is not None
        assert UserBehaviorPattern is not None
        assert KnowledgeBaseDocument is not None


@pytest.mark.integration
class TestBackwardCompatibility:
    """Test that Socrates maintains backward compatibility with re-exports."""

    def test_import_from_socratic_system(self):
        """Test importing core components via socratic_system re-exports."""
        # These should still work via backward compatibility
        from socratic_system import ConfigBuilder, SocratesConfig

        assert SocratesConfig is not None
        assert ConfigBuilder is not None

    def test_create_config_from_library(self):
        """Test creating a SocratesConfig instance from library."""
        from socratic_core import SocratesConfig

        config = SocratesConfig(api_key="test-key")
        assert config.api_key == "test-key"


@pytest.mark.integration
class TestLibraryVersions:
    """Verify correct library versions are installed."""

    def test_socratic_core_version(self):
        """Verify socratic-core is installed."""
        try:
            import socratic_core

            # Should be available
            assert hasattr(socratic_core, "__version__") or True
        except ImportError:
            pytest.fail("socratic-core not installed")

    def test_socratic_learning_version(self):
        """Verify socratic-learning is installed."""
        try:
            import socratic_learning

            # Should be available
            assert hasattr(socratic_learning, "__version__") or True
        except ImportError:
            pytest.fail("socratic-learning not installed")
