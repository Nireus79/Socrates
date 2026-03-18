"""Tests for socratic_core.exceptions module."""

import pytest

from socratic_core.exceptions import (
    APIError,
    AgentError,
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    ProjectNotFoundError,
    SocratesError,
    UserNotFoundError,
    ValidationError,
)


class TestSocratesError:
    """Tests for base SocratesError exception."""

    def test_socrates_error_creation(self):
        """Test creating SocratesError."""
        error = SocratesError("Test error")
        assert str(error) == "Test error"

    def test_socrates_error_inheritance(self):
        """Test that SocratesError inherits from Exception."""
        error = SocratesError("Test")
        assert isinstance(error, Exception)

    def test_socrates_error_with_message(self):
        """Test SocratesError with custom message."""
        msg = "Custom error message"
        error = SocratesError(msg)
        assert msg in str(error)

    def test_socrates_error_raise_and_catch(self):
        """Test raising and catching SocratesError."""
        with pytest.raises(SocratesError):
            raise SocratesError("Test error")


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_configuration_error_is_socrates_error(self):
        """Test that ConfigurationError is a SocratesError."""
        error = ConfigurationError("Invalid config")
        assert isinstance(error, SocratesError)

    def test_configuration_error_message(self):
        """Test ConfigurationError message."""
        msg = "Missing API key"
        error = ConfigurationError(msg)
        assert msg in str(error)

    def test_configuration_error_raise(self):
        """Test raising ConfigurationError."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Invalid API key format")

    def test_catch_configuration_error_as_socrates(self):
        """Test catching ConfigurationError as SocratesError."""
        with pytest.raises(SocratesError):
            raise ConfigurationError("Config error")


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error_is_socrates_error(self):
        """Test that ValidationError is a SocratesError."""
        error = ValidationError("Invalid input")
        assert isinstance(error, SocratesError)

    def test_validation_error_message(self):
        """Test ValidationError message."""
        msg = "Field 'name' is required"
        error = ValidationError(msg)
        assert msg in str(error)

    def test_validation_error_raise(self):
        """Test raising ValidationError."""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid project name")


class TestDatabaseError:
    """Tests for DatabaseError exception."""

    def test_database_error_is_socrates_error(self):
        """Test that DatabaseError is a SocratesError."""
        error = DatabaseError("Connection failed")
        assert isinstance(error, SocratesError)

    def test_database_error_message(self):
        """Test DatabaseError message."""
        msg = "Failed to connect to database"
        error = DatabaseError(msg)
        assert msg in str(error)

    def test_database_error_raise(self):
        """Test raising DatabaseError."""
        with pytest.raises(DatabaseError):
            raise DatabaseError("Query failed")


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_authentication_error_is_socrates_error(self):
        """Test that AuthenticationError is a SocratesError."""
        error = AuthenticationError("Invalid token")
        assert isinstance(error, SocratesError)

    def test_authentication_error_message(self):
        """Test AuthenticationError message."""
        msg = "API key is invalid"
        error = AuthenticationError(msg)
        assert msg in str(error)

    def test_authentication_error_raise(self):
        """Test raising AuthenticationError."""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Unauthorized")


class TestProjectNotFoundError:
    """Tests for ProjectNotFoundError exception."""

    def test_project_not_found_error_is_socrates_error(self):
        """Test that ProjectNotFoundError is a SocratesError."""
        error = ProjectNotFoundError("Project not found")
        assert isinstance(error, SocratesError)

    def test_project_not_found_error_message(self):
        """Test ProjectNotFoundError message."""
        msg = "Project 'proj_123' does not exist"
        error = ProjectNotFoundError(msg)
        assert msg in str(error)

    def test_project_not_found_error_raise(self):
        """Test raising ProjectNotFoundError."""
        with pytest.raises(ProjectNotFoundError):
            raise ProjectNotFoundError("Project not found")


class TestUserNotFoundError:
    """Tests for UserNotFoundError exception."""

    def test_user_not_found_error_is_socrates_error(self):
        """Test that UserNotFoundError is a SocratesError."""
        error = UserNotFoundError("User not found")
        assert isinstance(error, SocratesError)

    def test_user_not_found_error_message(self):
        """Test UserNotFoundError message."""
        msg = "User 'john@example.com' does not exist"
        error = UserNotFoundError(msg)
        assert msg in str(error)

    def test_user_not_found_error_raise(self):
        """Test raising UserNotFoundError."""
        with pytest.raises(UserNotFoundError):
            raise UserNotFoundError("User not found")


class TestAPIError:
    """Tests for APIError exception."""

    def test_api_error_is_socrates_error(self):
        """Test that APIError is a SocratesError."""
        error = APIError("API request failed")
        assert isinstance(error, SocratesError)

    def test_api_error_message(self):
        """Test APIError message."""
        msg = "HTTP 500: Internal Server Error"
        error = APIError(msg)
        assert msg in str(error)

    def test_api_error_raise(self):
        """Test raising APIError."""
        with pytest.raises(APIError):
            raise APIError("Request timeout")


class TestAgentError:
    """Tests for AgentError exception."""

    def test_agent_error_is_socrates_error(self):
        """Test that AgentError is a SocratesError."""
        error = AgentError("Agent failed")
        assert isinstance(error, SocratesError)

    def test_agent_error_message(self):
        """Test AgentError message."""
        msg = "Agent 'CodeGenerator' failed to generate code"
        error = AgentError(msg)
        assert msg in str(error)

    def test_agent_error_raise(self):
        """Test raising AgentError."""
        with pytest.raises(AgentError):
            raise AgentError("Agent crashed")


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_all_exceptions_inherit_from_socrates_error(self):
        """Test that all custom exceptions inherit from SocratesError."""
        exceptions = [
            ConfigurationError("test"),
            ValidationError("test"),
            DatabaseError("test"),
            AuthenticationError("test"),
            ProjectNotFoundError("test"),
            UserNotFoundError("test"),
            APIError("test"),
            AgentError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, SocratesError)
            assert isinstance(exc, Exception)

    def test_catch_any_socrates_error(self):
        """Test catching any SocratesError."""
        errors_to_test = [
            ConfigurationError("config"),
            ValidationError("validation"),
            DatabaseError("database"),
            AuthenticationError("auth"),
        ]

        for error in errors_to_test:
            with pytest.raises(SocratesError):
                raise error

    def test_specific_exception_catching(self):
        """Test catching specific exceptions."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Invalid config")

        with pytest.raises(ValidationError):
            raise ValidationError("Invalid input")

        with pytest.raises(DatabaseError):
            raise DatabaseError("DB error")

    def test_exception_details_preserved(self):
        """Test that exception details are preserved."""
        msg = "Detailed error message with context"
        error = SocratesError(msg)

        try:
            raise error
        except SocratesError as e:
            assert str(e) == msg
