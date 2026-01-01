"""
Unit tests for id_generator utility module.

Tests cover:
- Project ID generation (UUID format)
- User ID generation
- ID format validation
- Consistency across multiple generations
"""

import uuid

from socratic_system.utils.id_generator import ProjectIDGenerator, UserIDGenerator


class TestProjectIDGeneratorUUID:
    """Test ProjectIDGenerator with UUID format"""

    def test_generate_project_id(self):
        """Test basic project ID generation"""
        project_id = ProjectIDGenerator.generate()
        assert isinstance(project_id, str)
        assert project_id.startswith("proj_")

    def test_project_id_format(self):
        """Test that project ID has correct format"""
        project_id = ProjectIDGenerator.generate()
        parts = project_id.split("_", 1)
        assert len(parts) == 2
        assert parts[0] == "proj"

    def test_project_id_contains_valid_uuid(self):
        """Test that project ID contains valid UUID"""
        project_id = ProjectIDGenerator.generate()
        uuid_part = project_id.split("_", 1)[1]
        # Should be able to parse as UUID
        try:
            uuid.UUID(uuid_part)
            valid = True
        except ValueError:
            valid = False
        assert valid

    def test_project_id_uniqueness(self):
        """Test that generated IDs are unique"""
        ids = [ProjectIDGenerator.generate() for _ in range(10)]
        assert len(ids) == len(set(ids))

    def test_project_id_with_owner(self):
        """Test project ID generation with owner parameter"""
        project_id = ProjectIDGenerator.generate(owner="alice")
        assert isinstance(project_id, str)
        assert project_id.startswith("proj_")

    def test_project_id_multiple_owners(self):
        """Test project ID generation with different owners"""
        ids = [
            ProjectIDGenerator.generate("alice"),
            ProjectIDGenerator.generate("bob"),
            ProjectIDGenerator.generate("charlie"),
        ]
        assert len(ids) == len(set(ids))

    def test_project_id_without_owner(self):
        """Test project ID generation without owner"""
        id1 = ProjectIDGenerator.generate()
        id2 = ProjectIDGenerator.generate()
        assert id1 != id2


class TestUserIDGenerator:
    """Test UserIDGenerator"""

    def test_generate_user_id_without_username(self):
        """Test user ID generation without username"""
        user_id = UserIDGenerator.generate()
        assert isinstance(user_id, str)
        assert user_id.startswith("user_")

    def test_generate_user_id_with_username(self):
        """Test user ID generation with username"""
        user_id = UserIDGenerator.generate("alice")
        assert user_id == "alice"

    def test_generate_user_id_returns_username(self):
        """Test that username is returned as-is"""
        usernames = ["alice", "bob@example.com", "user123"]
        for username in usernames:
            user_id = UserIDGenerator.generate(username)
            assert user_id == username

    def test_generate_user_id_without_username_format(self):
        """Test that generated user ID without username has correct format"""
        user_id = UserIDGenerator.generate()
        parts = user_id.split("_", 1)
        assert len(parts) == 2
        assert parts[0] == "user"

    def test_generate_user_id_without_username_uniqueness(self):
        """Test that generated user IDs without username are unique"""
        ids = [UserIDGenerator.generate() for _ in range(5)]
        assert len(ids) == len(set(ids))

    def test_generate_user_id_contains_valid_uuid(self):
        """Test that generated user ID contains valid UUID"""
        user_id = UserIDGenerator.generate()
        uuid_part = user_id.split("_", 1)[1]
        try:
            uuid.UUID(uuid_part)
            valid = True
        except ValueError:
            valid = False
        assert valid

    def test_user_id_with_empty_string(self):
        """Test user ID generation with empty string"""
        user_id = UserIDGenerator.generate("")
        # Empty string should be falsy, so should generate random ID
        assert user_id.startswith("user_")

    def test_user_id_none_parameter(self):
        """Test user ID generation with None parameter"""
        user_id = UserIDGenerator.generate(None)
        assert user_id.startswith("user_")


class TestIDGeneratorConsistency:
    """Test consistency of ID generators"""

    def test_project_id_always_has_prefix(self):
        """Test that all generated project IDs have correct prefix"""
        for _ in range(20):
            project_id = ProjectIDGenerator.generate()
            assert project_id.startswith("proj_")

    def test_user_id_always_has_prefix_or_username(self):
        """Test that user IDs are either prefixed or return username"""
        usernames = ["alice", "bob", "charlie"]
        for username in usernames:
            user_id = UserIDGenerator.generate(username)
            assert user_id == username or user_id.startswith("user_")

    def test_project_id_length_reasonable(self):
        """Test that project ID has reasonable length"""
        project_id = ProjectIDGenerator.generate()
        # proj_ prefix (5 chars) + UUID (36 chars) = ~41 chars
        assert len(project_id) >= 40
        assert len(project_id) <= 50

    def test_user_id_without_username_length(self):
        """Test that generated user ID has reasonable length"""
        user_id = UserIDGenerator.generate()
        # user_ prefix (5 chars) + UUID (36 chars) = ~41 chars
        assert len(user_id) >= 40
        assert len(user_id) <= 50

    def test_user_id_with_username_no_prefix(self):
        """Test that user ID with username doesn't add prefix"""
        username = "alice@example.com"
        user_id = UserIDGenerator.generate(username)
        assert user_id == username


class TestIDGeneratorUseCases:
    """Test real-world use cases"""

    def test_create_multiple_projects_same_user(self):
        """Test creating multiple projects for same user"""
        owner = "alice"
        project_ids = [ProjectIDGenerator.generate(owner) for _ in range(3)]
        assert len(project_ids) == len(set(project_ids))

    def test_create_projects_multiple_users(self):
        """Test creating projects for multiple users"""
        owners = ["alice", "bob", "charlie"]
        project_ids = [ProjectIDGenerator.generate(owner) for owner in owners]
        assert len(project_ids) == len(set(project_ids))

    def test_user_registration_flow(self):
        """Test typical user registration flow"""
        # User with username
        alice_id = UserIDGenerator.generate("alice")
        assert alice_id == "alice"

        # Create project for alice
        alice_project = ProjectIDGenerator.generate("alice")
        assert alice_project.startswith("proj_")

    def test_anonymous_user_flow(self):
        """Test anonymous user flow"""
        # Generate ID for anonymous user
        anon_id = UserIDGenerator.generate()
        assert anon_id.startswith("user_")

        # Create project for anonymous user
        anon_project = ProjectIDGenerator.generate()
        assert anon_project.startswith("proj_")


class TestIDValidation:
    """Test ID validation"""

    def test_project_id_can_be_parsed(self):
        """Test that project ID can be parsed back"""
        project_id = ProjectIDGenerator.generate("test_owner")
        # Should be able to split and get prefix
        prefix, rest = project_id.split("_", 1)
        assert prefix == "proj"

    def test_user_id_string_representation(self):
        """Test user ID string representation"""
        user_id = UserIDGenerator.generate()
        assert isinstance(str(user_id), str)
        assert len(str(user_id)) > 0

    def test_ids_are_strings(self):
        """Test that generated IDs are strings"""
        project_id = ProjectIDGenerator.generate()
        user_id = UserIDGenerator.generate()
        assert isinstance(project_id, str)
        assert isinstance(user_id, str)

    def test_ids_no_whitespace(self):
        """Test that IDs don't contain whitespace"""
        project_id = ProjectIDGenerator.generate()
        user_id = UserIDGenerator.generate()
        assert " " not in project_id
        assert "\n" not in project_id
        assert " " not in user_id
        assert "\n" not in user_id
