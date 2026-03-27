"""
Phase 5 Tests: API Response Serialization

Verify that typed objects (User, ProjectContext) from the database
serialize correctly to JSON responses and maintain backward compatibility.

Tests Phase 4 changes:
- 22 removed dict-to-object conversions
- User and ProjectContext object serialization
- Dict-like access methods (__getitem__, get(), __contains__)
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from socrates_api.models_local import User, ProjectContext
from socrates_api.models import APIResponse
from fastapi.testclient import TestClient


class TestUserObjectSerialization:
    """Test User object serialization in API responses."""

    def test_user_object_has_required_fields(self):
        """User object has all required fields."""
        user = User(
            user_id="user_123",
            username="testuser",
            email="test@example.com",
            subscription_tier="pro"
        )

        assert user.id == "user_123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.subscription_tier == "pro"

    def test_user_dict_compatibility_getitem(self):
        """User object supports dict-like access with __getitem__."""
        user = User(
            user_id="user_123",
            username="testuser",
            email="test@example.com"
        )

        assert user["id"] == "user_123"
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"

    def test_user_dict_compatibility_get(self):
        """User object supports dict get() method."""
        user = User(
            user_id="user_123",
            username="testuser"
        )

        assert user.get("id") == "user_123"
        assert user.get("username") == "testuser"
        assert user.get("nonexistent") is None
        assert user.get("nonexistent", "default") == "default"

    def test_user_dict_compatibility_contains(self):
        """User object supports 'in' operator."""
        user = User(
            user_id="user_123",
            username="testuser"
        )

        assert "id" in user
        assert "username" in user
        assert "email" in user  # None is still present
        assert "nonexistent" not in user

    def test_user_to_dict_conversion(self):
        """User object can be converted to dict."""
        user = User(
            user_id="user_123",
            username="testuser",
            email="test@example.com",
            subscription_tier="pro"
        )

        user_dict = user.to_dict()
        assert isinstance(user_dict, dict)
        assert user_dict["id"] == "user_123"
        assert user_dict["username"] == "testuser"
        assert user_dict["subscription_tier"] == "pro"

    def test_user_pydantic_serialization(self):
        """User object serializes correctly through Pydantic."""
        user = User(
            user_id="user_123",
            username="testuser",
            email="test@example.com"
        )

        # APIResponse should serialize User object
        response = APIResponse(
            success=True,
            status="success",
            message="User retrieved",
            data={"user": user}
        )

        # Serialize to dict (simulating JSON conversion)
        response_dict = response.model_dump(mode='json')
        assert response_dict["success"] is True
        assert "user" in response_dict["data"]


class TestProjectContextSerialization:
    """Test ProjectContext object serialization in API responses."""

    def test_project_context_has_required_fields(self):
        """ProjectContext object has all required fields."""
        project = ProjectContext(
            project_id="proj_123",
            name="Test Project",
            owner="user_123",
            description="Test description",
            phase="implementation"
        )

        assert project.project_id == "proj_123"
        assert project.name == "Test Project"
        assert project.owner == "user_123"
        assert project.phase == "implementation"

    def test_project_context_dict_compatibility(self):
        """ProjectContext supports dict-like access."""
        project = ProjectContext(
            project_id="proj_123",
            name="Test Project",
            owner="user_123"
        )

        # __getitem__ access
        assert project["project_id"] == "proj_123"
        assert project["name"] == "Test Project"
        assert project["owner"] == "user_123"

        # get() method
        assert project.get("project_id") == "proj_123"
        assert project.get("nonexistent") is None

        # in operator
        assert "project_id" in project
        assert "name" in project
        assert "nonexistent" not in project

    def test_project_context_nested_fields(self):
        """ProjectContext handles nested fields correctly."""
        project = ProjectContext(
            project_id="proj_123",
            name="Test Project",
            owner="user_123",
            conversation_history=[
                {"role": "user", "content": "test"},
                {"role": "assistant", "content": "response"}
            ],
            metadata={"key": "value"}
        )

        assert len(project.conversation_history) == 2
        assert project.metadata["key"] == "value"

        # Access through dict interface
        assert len(project["conversation_history"]) == 2
        assert project.get("metadata")["key"] == "value"

    def test_project_context_to_dict_conversion(self):
        """ProjectContext can be converted to dict."""
        project = ProjectContext(
            project_id="proj_123",
            name="Test Project",
            owner="user_123",
            phase="implementation"
        )

        project_dict = project.to_dict()
        assert isinstance(project_dict, dict)
        assert project_dict["project_id"] == "proj_123"
        assert project_dict["name"] == "Test Project"
        assert project_dict["phase"] == "implementation"

    def test_project_context_pydantic_serialization(self):
        """ProjectContext serializes correctly through Pydantic."""
        project = ProjectContext(
            project_id="proj_123",
            name="Test Project",
            owner="user_123"
        )

        response = APIResponse(
            success=True,
            status="success",
            message="Project retrieved",
            data={"project": project}
        )

        response_dict = response.model_dump(mode='json')
        assert response_dict["success"] is True
        assert "project" in response_dict["data"]
        assert response_dict["data"]["project"]["project_id"] == "proj_123"


class TestNestedObjectSerialization:
    """Test serialization of nested objects."""

    def test_project_with_nested_user_serialization(self):
        """Complex response with nested User in ProjectContext serializes."""
        user = User(user_id="user_123", username="testuser")
        project = ProjectContext(
            project_id="proj_123",
            name="Test",
            owner="user_123"
        )

        response = APIResponse(
            success=True,
            status="success",
            data={"project": project, "owner": user}
        )

        response_dict = response.model_dump(mode='json')
        assert response_dict["data"]["project"]["project_id"] == "proj_123"
        assert response_dict["data"]["owner"]["username"] == "testuser"

    def test_list_of_projects_serialization(self):
        """List of ProjectContext objects serializes correctly."""
        projects = [
            ProjectContext(project_id="proj_1", name="Project 1", owner="user_123"),
            ProjectContext(project_id="proj_2", name="Project 2", owner="user_123"),
        ]

        response = APIResponse(
            success=True,
            status="success",
            data={"projects": projects}
        )

        response_dict = response.model_dump(mode='json')
        assert len(response_dict["data"]["projects"]) == 2
        assert response_dict["data"]["projects"][0]["name"] == "Project 1"
        assert response_dict["data"]["projects"][1]["name"] == "Project 2"


class TestBackwardCompatibility:
    """Test backward compatibility with code expecting dicts."""

    def test_isinstance_check_still_works(self):
        """isinstance checks on objects still work for backward compat."""
        user = User(user_id="user_123", username="testuser")
        project = ProjectContext(project_id="proj_123", name="Test", owner="user_123")

        # Objects are instances of themselves
        assert isinstance(user, User)
        assert isinstance(project, ProjectContext)

        # Code that checked isinstance(data, dict) needs updating
        # but objects provide dict-like interface
        assert hasattr(user, 'get')
        assert hasattr(user, '__getitem__')
        assert hasattr(project, 'get')
        assert hasattr(project, '__getitem__')

    def test_dict_unpacking_compatibility(self):
        """Objects work with code that expects dict-like interface."""
        user = User(
            user_id="user_123",
            username="testuser",
            email="test@example.com"
        )

        # Code using .get() still works
        username = user.get("username")
        assert username == "testuser"

        # Code using bracket notation still works
        user_id = user["id"]
        assert user_id == "user_123"

        # Code checking membership still works
        has_email = "email" in user
        assert has_email is True


@pytest.mark.asyncio
class TestAsyncResponseSerialization:
    """Test serialization in async API responses."""

    async def test_async_endpoint_with_typed_object(self):
        """Async endpoint returns typed object correctly."""
        project = ProjectContext(
            project_id="proj_123",
            name="Test Project",
            owner="user_123"
        )

        # Simulate async endpoint return
        response = APIResponse(
            success=True,
            status="success",
            data=project
        )

        # Should serialize correctly
        response_dict = response.model_dump(mode='json')
        assert response_dict["success"] is True
        assert response_dict["data"]["project_id"] == "proj_123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
