"""
Unit tests for Socrates exception system
"""

import pytest

import socrates
from socratic_system.exceptions import (
    SocratesError,
    ConfigurationError,
    AgentError,
    DatabaseError,
    AuthenticationError,
    ProjectNotFoundError,
    UserNotFoundError,
    ValidationError,
    APIError
)


@pytest.mark.unit
class TestSocratesError:
    """Tests for base SocratesError"""

    def test_error_creation(self):
        """Test creating a SocratesError"""
        error = SocratesError("Test error message")

        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_error_with_error_code(self):
        """Test error with error code"""
        error = SocratesError("Test error", error_code="TEST_ERROR")

        assert error.error_code == "TEST_ERROR"

    def test_error_with_context(self):
        """Test error with context dictionary"""
        context = {"project_id": "test_proj", "user": "testuser"}
        error = SocratesError("Test error", context=context)

        assert error.context == context

    def test_error_to_dict(self):
        """Test converting error to dictionary"""
        context = {"key": "value"}
        error = SocratesError(
            "Test message",
            error_code="TEST",
            context=context
        )

        error_dict = error.to_dict()

        assert error_dict["message"] == "Test message"
        assert error_dict["error_code"] == "TEST"
        assert error_dict["context"] == context

    def test_error_inheritance(self):
        """Test that SocratesError inherits from Exception"""
        error = SocratesError("Test")

        assert isinstance(error, Exception)
        assert issubclass(SocratesError, Exception)


@pytest.mark.unit
class TestConfigurationError:
    """Tests for ConfigurationError"""

    def test_configuration_error_creation(self):
        """Test creating ConfigurationError"""
        error = ConfigurationError("Invalid configuration")

        assert isinstance(error, SocratesError)
        assert str(error) == "Invalid configuration"

    def test_configuration_error_with_code(self):
        """Test ConfigurationError with code"""
        error = ConfigurationError(
            "Missing API key",
            error_code="MISSING_API_KEY"
        )

        assert error.error_code == "MISSING_API_KEY"

    def test_configuration_error_with_context(self):
        """Test ConfigurationError with context"""
        context = {"missing_key": "ANTHROPIC_API_KEY"}
        error = ConfigurationError(
            "Missing required config",
            context=context
        )

        assert error.context == context


@pytest.mark.unit
class TestAgentError:
    """Tests for AgentError"""

    def test_agent_error_creation(self):
        """Test creating AgentError"""
        error = AgentError("Agent processing failed")

        assert isinstance(error, SocratesError)

    def test_agent_error_with_agent_info(self):
        """Test AgentError with agent information"""
        context = {"agent_name": "code_generator", "action": "generate_code"}
        error = AgentError(
            "Code generation failed",
            context=context
        )

        assert error.context["agent_name"] == "code_generator"


@pytest.mark.unit
class TestDatabaseError:
    """Tests for DatabaseError"""

    def test_database_error_creation(self):
        """Test creating DatabaseError"""
        error = DatabaseError("Database connection failed")

        assert isinstance(error, SocratesError)

    def test_database_error_context(self):
        """Test DatabaseError with context"""
        context = {"operation": "save_project", "table": "projects"}
        error = DatabaseError(
            "Failed to save project",
            context=context
        )

        assert error.context["operation"] == "save_project"


@pytest.mark.unit
class TestProjectNotFoundError:
    """Tests for ProjectNotFoundError"""

    def test_project_not_found_error(self):
        """Test ProjectNotFoundError"""
        error = ProjectNotFoundError(
            "Project not found",
            context={"project_id": "invalid_id"}
        )

        assert isinstance(error, DatabaseError)
        assert "invalid_id" in str(error.context)

    def test_project_not_found_is_database_error(self):
        """Test that ProjectNotFoundError is a DatabaseError"""
        error = ProjectNotFoundError("Project not found")

        assert isinstance(error, DatabaseError)
        assert isinstance(error, SocratesError)


@pytest.mark.unit
class TestUserNotFoundError:
    """Tests for UserNotFoundError"""

    def test_user_not_found_error(self):
        """Test UserNotFoundError"""
        error = UserNotFoundError(
            "User not found",
            context={"username": "nonexistent"}
        )

        assert isinstance(error, DatabaseError)

    def test_user_not_found_is_database_error(self):
        """Test that UserNotFoundError is a DatabaseError"""
        error = UserNotFoundError("User not found")

        assert isinstance(error, DatabaseError)


@pytest.mark.unit
class TestAuthenticationError:
    """Tests for AuthenticationError"""

    def test_authentication_error_creation(self):
        """Test creating AuthenticationError"""
        error = AuthenticationError("Invalid API key")

        assert isinstance(error, SocratesError)

    def test_authentication_error_context(self):
        """Test AuthenticationError with context"""
        error = AuthenticationError(
            "Invalid credentials",
            context={"auth_method": "api_key"}
        )

        assert error.context["auth_method"] == "api_key"


@pytest.mark.unit
class TestValidationError:
    """Tests for ValidationError"""

    def test_validation_error_creation(self):
        """Test creating ValidationError"""
        error = ValidationError("Invalid project name")

        assert isinstance(error, SocratesError)

    def test_validation_error_with_field(self):
        """Test ValidationError with field information"""
        context = {"field": "project_name", "reason": "too_short"}
        error = ValidationError(
            "Validation failed",
            context=context
        )

        assert error.context["field"] == "project_name"


@pytest.mark.unit
class TestAPIError:
    """Tests for APIError"""

    def test_api_error_creation(self):
        """Test creating APIError"""
        error = APIError("API request failed")

        assert isinstance(error, SocratesError)

    def test_api_error_with_status(self):
        """Test APIError with HTTP status"""
        context = {"status_code": 429, "message": "Rate limited"}
        error = APIError(
            "Claude API error",
            context=context
        )

        assert error.context["status_code"] == 429

    def test_api_error_with_retry_info(self):
        """Test APIError with retry information"""
        context = {
            "status_code": 500,
            "retries_remaining": 2,
            "retry_after": 10
        }
        error = APIError(
            "API server error",
            context=context
        )

        assert error.context["retries_remaining"] == 2


@pytest.mark.unit
class TestErrorHierarchy:
    """Tests for exception hierarchy"""

    def test_all_errors_inherit_from_socrates_error(self):
        """Test that all custom errors inherit from SocratesError"""
        errors = [
            ConfigurationError("test"),
            AgentError("test"),
            DatabaseError("test"),
            AuthenticationError("test"),
            ProjectNotFoundError("test"),
            UserNotFoundError("test"),
            ValidationError("test"),
            APIError("test")
        ]

        for error in errors:
            assert isinstance(error, SocratesError)

    def test_error_catching_hierarchy(self):
        """Test catching errors at different hierarchy levels"""
        def raise_project_error():
            raise ProjectNotFoundError("Project not found")

        # Should be catchable as DatabaseError
        with pytest.raises(DatabaseError):
            raise_project_error()

        # Should be catchable as SocratesError
        with pytest.raises(SocratesError):
            raise_project_error()

        # Should be catchable as Exception
        with pytest.raises(Exception):
            raise_project_error()


@pytest.mark.unit
class TestErrorMessages:
    """Tests for error message handling"""

    def test_error_message_preservation(self):
        """Test that error messages are preserved"""
        message = "This is a test error message with special chars: !@#$%"
        error = SocratesError(message)

        assert str(error) == message

    def test_error_message_with_newlines(self):
        """Test error message with newlines"""
        message = "Error on line 1\nError on line 2\nError on line 3"
        error = SocratesError(message)

        assert "line 1" in str(error)
        assert "line 2" in str(error)

    def test_error_to_dict_includes_all_info(self):
        """Test that to_dict includes all error information"""
        context = {"key1": "value1", "key2": {"nested": "value"}}
        error = SocratesError(
            "Test message",
            error_code="TEST_CODE",
            context=context
        )

        error_dict = error.to_dict()

        assert "message" in error_dict
        assert "error_code" in error_dict
        assert "context" in error_dict
        assert error_dict["message"] == "Test message"
        assert error_dict["error_code"] == "TEST_CODE"


@pytest.mark.unit
class TestErrorRaising:
    """Tests for raising and catching errors"""

    def test_raise_and_catch_socrates_error(self):
        """Test raising and catching SocratesError"""
        with pytest.raises(SocratesError):
            raise SocratesError("Test error")

    def test_raise_specific_error(self):
        """Test raising specific error types"""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Config error")

        with pytest.raises(AgentError):
            raise AgentError("Agent error")

    def test_error_with_exception_chaining(self):
        """Test error exception chaining"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise SocratesError("Wrapped error") from e
        except SocratesError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)


@pytest.mark.unit
class TestErrorContextData:
    """Tests for error context data"""

    def test_context_is_optional(self):
        """Test that context is optional"""
        error1 = SocratesError("Message")
        error2 = SocratesError("Message", context=None)
        error3 = SocratesError("Message", context={})

        assert error1.context is None
        assert error2.context is None
        assert error3.context == {}

    def test_context_with_various_types(self):
        """Test context with different data types"""
        context = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "bool": True,
            "none": None
        }

        error = SocratesError("Message", context=context)

        assert error.context == context
