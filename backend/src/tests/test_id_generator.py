"""
Tests for the IDGenerator utility module.

Verifies that ID generation is consistent, unique, and follows the established format.
"""

import pytest
from socrates_api.utils import IDGenerator


class TestIDGeneratorBasics:
    """Test basic ID generation functionality."""

    def test_project_id_format(self):
        """Project IDs should have correct format: proj_XXXXXXXXXXXX"""
        project_id = IDGenerator.project()
        assert project_id.startswith("proj_")
        assert len(project_id) == 17  # "proj_" (5) + 12 hex chars
        # Verify it's valid hex
        hex_part = project_id.split("_")[1]
        int(hex_part, 16)  # Should not raise

    def test_user_id_format(self):
        """User IDs should have correct format: user_XXXXXXXXXXXX"""
        user_id = IDGenerator.user()
        assert user_id.startswith("user_")
        assert len(user_id) == 17  # "user_" (5) + 12 hex chars

    def test_session_id_format(self):
        """Session IDs should have correct format: sess_XXXXXXXX (shorter)"""
        session_id = IDGenerator.session()
        assert session_id.startswith("sess_")
        assert len(session_id) == 13  # "sess_" (5) + 8 hex chars

    def test_message_id_format(self):
        """Message IDs should have correct format: msg_XXXXXXXXXXXX"""
        message_id = IDGenerator.message()
        assert message_id.startswith("msg_")
        assert len(message_id) == 16  # "msg_" (4) + 12 hex chars

    def test_skill_id_format(self):
        """Skill IDs should have correct format: skill_XXXXXXXXXXXX"""
        skill_id = IDGenerator.skill()
        assert skill_id.startswith("skill_")
        assert len(skill_id) == 18  # "skill_" (6) + 12 hex chars

    def test_note_id_format(self):
        """Note IDs should have correct format: note_XXXXXXXXXXXX"""
        note_id = IDGenerator.note()
        assert note_id.startswith("note_")
        assert len(note_id) == 17  # "note_" (5) + 12 hex chars

    def test_interaction_id_format(self):
        """Interaction IDs should have correct format: int_XXXXXXXXXXXX"""
        interaction_id = IDGenerator.interaction()
        assert interaction_id.startswith("int_")
        assert len(interaction_id) == 16  # "int_" (4) + 12 hex chars

    def test_document_id_format(self):
        """Document IDs should have correct format: doc_XXXXXXXXXXXX"""
        document_id = IDGenerator.document()
        assert document_id.startswith("doc_")
        assert len(document_id) == 16  # "doc_" (4) + 12 hex chars

    def test_token_id_format(self):
        """Token IDs should have correct format: tok_XXXXXXXXXXXX"""
        token_id = IDGenerator.token()
        assert token_id.startswith("tok_")
        assert len(token_id) == 16  # "tok_" (4) + 12 hex chars

    def test_activity_id_format(self):
        """Activity IDs should have correct format: act_XXXXXXXXXXXX"""
        activity_id = IDGenerator.activity()
        assert activity_id.startswith("act_")
        assert len(activity_id) == 16  # "act_" (4) + 12 hex chars

    def test_invitation_id_format(self):
        """Invitation IDs should have correct format: inv_XXXXXXXXXXXX"""
        invitation_id = IDGenerator.invitation()
        assert invitation_id.startswith("inv_")
        assert len(invitation_id) == 16  # "inv_" (4) + 12 hex chars


class TestIDGeneratorUniqueness:
    """Test that generated IDs are unique."""

    def test_project_ids_are_unique(self):
        """Multiple project IDs should be unique."""
        ids = {IDGenerator.project() for _ in range(100)}
        assert len(ids) == 100, "All 100 project IDs should be unique"

    def test_user_ids_are_unique(self):
        """Multiple user IDs should be unique."""
        ids = {IDGenerator.user() for _ in range(100)}
        assert len(ids) == 100, "All 100 user IDs should be unique"

    def test_message_ids_are_unique(self):
        """Multiple message IDs should be unique."""
        ids = {IDGenerator.message() for _ in range(100)}
        assert len(ids) == 100, "All 100 message IDs should be unique"

    def test_cross_type_ids_dont_collide(self):
        """IDs from different types should not collide."""
        # Even with a small sample, IDs from different types should be distinct
        ids = {
            IDGenerator.project(),
            IDGenerator.user(),
            IDGenerator.session(),
            IDGenerator.message(),
            IDGenerator.skill(),
        }
        assert len(ids) == 5, "No IDs should collide across types"


class TestIDGeneratorCustomLength:
    """Test custom length parameter for generate_id."""

    def test_generate_id_custom_length(self):
        """Custom length should be respected."""
        id_8 = IDGenerator.generate_id("test", length=8)
        assert id_8.startswith("test_")
        assert len(id_8) == 13  # "test_" (5) + 8 hex chars

        id_16 = IDGenerator.generate_id("test", length=16)
        assert id_16.startswith("test_")
        assert len(id_16) == 21  # "test_" (5) + 16 hex chars

    def test_generate_id_minimum_length(self):
        """Minimum length of 1 should work."""
        id_1 = IDGenerator.generate_id("test", length=1)
        assert id_1.startswith("test_")
        assert len(id_1) == 6  # "test_" (5) + 1 hex char


class TestIDGeneratorErrorHandling:
    """Test error handling in IDGenerator."""

    def test_empty_prefix_raises_error(self):
        """Empty prefix should raise ValueError."""
        with pytest.raises(ValueError, match="Prefix cannot be empty"):
            IDGenerator.generate_id("", length=12)

    def test_non_string_prefix_raises_error(self):
        """Non-string prefix should raise TypeError."""
        with pytest.raises(TypeError, match="Prefix must be string"):
            IDGenerator.generate_id(123, length=12)


class TestIDGeneratorBackwardCompatibility:
    """Test backward compatibility with monolithic system."""

    def test_project_id_generator_compatibility(self):
        """ProjectIDGenerator.generate() should work."""
        project_id = IDGenerator.ProjectIDGenerator.generate()
        assert project_id.startswith("proj_")
        assert len(project_id) == 17

    def test_backward_compat_generates_unique_ids(self):
        """Backward compat wrapper should generate unique IDs."""
        ids = {IDGenerator.ProjectIDGenerator.generate() for _ in range(50)}
        assert len(ids) == 50

    def test_backward_compat_matches_project_method(self):
        """Both ways of calling should produce same format."""
        id1 = IDGenerator.project()
        id2 = IDGenerator.ProjectIDGenerator.generate()

        # Both should start with proj_
        assert id1.startswith("proj_")
        assert id2.startswith("proj_")

        # Both should have same length
        assert len(id1) == len(id2) == 17


class TestIDGeneratorConsistency:
    """Test consistency of ID generation across calls."""

    def test_prefix_consistency(self):
        """All IDs of same type should use same prefix."""
        for _ in range(20):
            project_id = IDGenerator.project()
            assert project_id.startswith("proj_"), f"Expected proj_ prefix, got {project_id}"

            user_id = IDGenerator.user()
            assert user_id.startswith("user_"), f"Expected user_ prefix, got {user_id}"

            session_id = IDGenerator.session()
            assert session_id.startswith("sess_"), f"Expected sess_ prefix, got {session_id}"

    def test_hex_consistency(self):
        """All IDs should contain only hex characters in suffix."""
        for _ in range(20):
            for id_func in [
                IDGenerator.project,
                IDGenerator.user,
                IDGenerator.message,
                IDGenerator.skill,
            ]:
                entity_id = id_func()
                hex_part = entity_id.split("_")[1]
                # Should not raise if valid hex
                int(hex_part, 16)


class TestIDGeneratorPerformance:
    """Test performance characteristics of ID generation."""

    def test_id_generation_is_fast(self):
        """ID generation should be very fast."""
        import time

        # Generate 1000 IDs and measure time
        start = time.time()
        for _ in range(1000):
            IDGenerator.project()
        elapsed = time.time() - start

        # Should complete in well under 1 second
        assert elapsed < 1.0, f"Generating 1000 IDs took {elapsed}s, should be faster"

    def test_all_types_are_equally_fast(self):
        """All ID types should generate at similar speeds."""
        import time

        id_functions = [
            IDGenerator.project,
            IDGenerator.user,
            IDGenerator.session,
            IDGenerator.message,
            IDGenerator.skill,
            IDGenerator.note,
            IDGenerator.interaction,
            IDGenerator.document,
            IDGenerator.token,
            IDGenerator.activity,
            IDGenerator.invitation,
        ]

        times = {}
        for id_func in id_functions:
            start = time.time()
            for _ in range(100):
                id_func()
            elapsed = time.time() - start
            times[id_func.__name__] = elapsed

        # All should be within a reasonable range of each other
        max_time = max(times.values())
        min_time = min(times.values())
        ratio = max_time / min_time if min_time > 0 else 1

        # Ratio should be close to 1 (all fast)
        assert ratio < 2.0, f"Time variance is too high: {times}"


# Test that all entity types are properly covered
class TestIDGeneratorCoverage:
    """Test that all ID types are documented and working."""

    def test_all_prefixes_defined(self):
        """All documented prefixes should be defined in constants."""
        expected_prefixes = [
            "PROJECT_PREFIX",
            "USER_PREFIX",
            "SESSION_PREFIX",
            "MESSAGE_PREFIX",
            "SKILL_PREFIX",
            "NOTE_PREFIX",
            "INTERACTION_PREFIX",
            "DOCUMENT_PREFIX",
            "TOKEN_PREFIX",
            "ACTIVITY_PREFIX",
            "INVITATION_PREFIX",
        ]

        for prefix_name in expected_prefixes:
            assert hasattr(
                IDGenerator, prefix_name
            ), f"IDGenerator should have {prefix_name}"

    def test_all_methods_defined(self):
        """All documented methods should exist."""
        expected_methods = [
            "project",
            "user",
            "session",
            "message",
            "skill",
            "note",
            "interaction",
            "document",
            "token",
            "activity",
            "invitation",
        ]

        for method_name in expected_methods:
            assert hasattr(
                IDGenerator, method_name
            ), f"IDGenerator should have {method_name} method"
            assert callable(
                getattr(IDGenerator, method_name)
            ), f"{method_name} should be callable"
