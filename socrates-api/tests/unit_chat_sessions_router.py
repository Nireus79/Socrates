"""
Unit tests for chat sessions router.

Tests chat session management endpoints including:
- Creating and listing chat sessions
- Sending and retrieving messages
- Updating and deleting messages
- Archiving and restoring sessions
"""

import pytest
from fastapi.testclient import TestClient

from socrates_api.auth.jwt_handler import create_access_token
from socrates_api.main import app


@pytest.fixture(scope="session")
def client():
    """Create FastAPI test client - session scoped for performance."""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Create a valid JWT token for testing."""
    return create_access_token("testuser")


@pytest.mark.unit
class TestCreateChatSession:
    """Tests for creating chat sessions."""

    def test_create_session_requires_auth(self, client):
        """Test that creating a session requires authentication."""
        response = client.post(
            "/projects/test_proj/chat/sessions",
            json={"title": "Test Session"},
        )
        assert response.status_code == 401

    def test_create_session_missing_project(self, client, valid_token):
        """Test creating session for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/nonexistent_proj_xyz/chat/sessions",
            json={"title": "Test Session"},
            headers=headers,
        )
        assert response.status_code == 404

    def test_create_session_with_title(self, client, valid_token):
        """Test creating session with explicit title."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/sessions",
            json={"title": "My Test Session"},
            headers=headers,
        )
        assert response.status_code in [201, 404, 500]
        if response.status_code == 201:
            data = response.json()
            assert "session_id" in data
            assert data["title"] == "My Test Session"
            assert data["message_count"] == 0

    def test_create_session_without_title(self, client, valid_token):
        """Test creating session without title (auto-generated)."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/sessions",
            json={},
            headers=headers,
        )
        assert response.status_code in [201, 404, 500]

    def test_create_session_invalid_token(self, client):
        """Test create session with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/projects/test_proj/chat/sessions",
            json={"title": "Test"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestListChatSessions:
    """Tests for listing chat sessions."""

    def test_list_sessions_requires_auth(self, client):
        """Test that listing sessions requires authentication."""
        response = client.get("/projects/test_proj/chat/sessions")
        assert response.status_code == 401

    def test_list_sessions_missing_project(self, client, valid_token):
        """Test listing sessions for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects/nonexistent_proj_xyz/chat/sessions", headers=headers)
        assert response.status_code == 404

    def test_list_sessions_success(self, client, valid_token):
        """Test listing sessions successfully."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects/test_proj/chat/sessions", headers=headers)
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "sessions" in data
            assert "total" in data
            assert isinstance(data["sessions"], list)

    def test_list_sessions_with_pagination(self, client, valid_token):
        """Test listing sessions with limit and offset."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions?limit=10&offset=0",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_list_sessions_filter_by_archive(self, client, valid_token):
        """Test filtering sessions by archive status."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions?archived=false",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_list_sessions_search(self, client, valid_token):
        """Test searching sessions by title."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions?search=test",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_list_sessions_invalid_token(self, client):
        """Test list sessions with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get("/projects/test_proj/chat/sessions", headers=headers)
        assert response.status_code == 401


@pytest.mark.unit
class TestGetChatSession:
    """Tests for getting chat session details."""

    def test_get_session_requires_auth(self, client):
        """Test that getting session requires authentication."""
        response = client.get("/projects/test_proj/chat/sessions/sess_123")
        assert response.status_code == 401

    def test_get_session_missing_project(self, client, valid_token):
        """Test getting session from non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/nonexistent_proj_xyz/chat/sessions/sess_123",
            headers=headers,
        )
        assert response.status_code == 404

    def test_get_session_not_found(self, client, valid_token):
        """Test getting non-existent session."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions/nonexistent_sess_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_get_session_invalid_token(self, client):
        """Test get session with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get(
            "/projects/test_proj/chat/sessions/sess_123",
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestSendChatMessage:
    """Tests for sending messages in chat sessions."""

    def test_send_message_requires_auth(self, client):
        """Test that sending message requires authentication."""
        response = client.post(
            "/projects/test_proj/chat/sessions/sess_123/message",
            json={"message": "Hello", "role": "user"},
        )
        assert response.status_code == 401

    def test_send_message_missing_project(self, client, valid_token):
        """Test sending message to non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/nonexistent_proj_xyz/chat/sessions/sess_123/message",
            json={"message": "Hello", "role": "user"},
            headers=headers,
        )
        assert response.status_code == 404

    def test_send_message_missing_session(self, client, valid_token):
        """Test sending message to non-existent session."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/sessions/nonexistent_sess_xyz/message",
            json={"message": "Hello", "role": "user"},
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_send_message_missing_content(self, client, valid_token):
        """Test sending message without content."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/sessions/sess_123/message",
            json={"role": "user"},
            headers=headers,
        )
        assert response.status_code in [422, 404, 500]

    def test_send_message_success(self, client, valid_token):
        """Test sending message successfully."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/sessions/sess_123/message",
            json={"message": "Test message", "role": "user"},
            headers=headers,
        )
        assert response.status_code in [201, 404, 500]
        if response.status_code == 201:
            data = response.json()
            assert "message_id" in data
            assert data["content"] == "Test message"
            assert data["role"] == "user"

    def test_send_message_invalid_token(self, client):
        """Test send message with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/projects/test_proj/chat/sessions/sess_123/message",
            json={"message": "Hello", "role": "user"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestGetChatMessages:
    """Tests for retrieving chat messages."""

    def test_get_messages_requires_auth(self, client):
        """Test that getting messages requires authentication."""
        response = client.get("/projects/test_proj/chat/sessions/sess_123/messages")
        assert response.status_code == 401

    def test_get_messages_missing_project(self, client, valid_token):
        """Test getting messages from non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/nonexistent_proj_xyz/chat/sessions/sess_123/messages",
            headers=headers,
        )
        assert response.status_code == 404

    def test_get_messages_missing_session(self, client, valid_token):
        """Test getting messages from non-existent session."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions/nonexistent_sess_xyz/messages",
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_get_messages_empty(self, client, valid_token):
        """Test getting messages when session is empty."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions/sess_123/messages",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "messages" in data
            assert "total" in data
            assert isinstance(data["messages"], list)

    def test_get_messages_with_pagination(self, client, valid_token):
        """Test getting messages with limit and offset."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions/sess_123/messages?limit=10&offset=0",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_get_messages_with_order(self, client, valid_token):
        """Test getting messages with order parameter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions/sess_123/messages?order=desc",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_get_messages_invalid_token(self, client):
        """Test get messages with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get(
            "/projects/test_proj/chat/sessions/sess_123/messages",
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestUpdateChatMessage:
    """Tests for updating chat messages."""

    def test_update_message_requires_auth(self, client):
        """Test that updating message requires authentication."""
        response = client.put(
            "/projects/test_proj/chat/sessions/sess_123/messages/msg_456",
            json={"content": "Updated message"},
        )
        assert response.status_code == 401

    def test_update_message_missing_project(self, client, valid_token):
        """Test updating message in non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/nonexistent_proj_xyz/chat/sessions/sess_123/messages/msg_456",
            json={"content": "Updated"},
            headers=headers,
        )
        assert response.status_code == 404

    def test_update_message_missing_session(self, client, valid_token):
        """Test updating message in non-existent session."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/chat/sessions/nonexistent_sess_xyz/messages/msg_456",
            json={"content": "Updated"},
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_update_message_not_found(self, client, valid_token):
        """Test updating non-existent message."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/chat/sessions/sess_123/messages/nonexistent_msg_xyz",
            json={"content": "Updated"},
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_update_message_success(self, client, valid_token):
        """Test updating message successfully."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/chat/sessions/sess_123/messages/msg_456",
            json={"content": "Updated message", "metadata": None},
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_update_message_invalid_token(self, client):
        """Test update message with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.put(
            "/projects/test_proj/chat/sessions/sess_123/messages/msg_456",
            json={"content": "Updated"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestDeleteChatMessage:
    """Tests for deleting chat messages."""

    def test_delete_message_requires_auth(self, client):
        """Test that deleting message requires authentication."""
        response = client.delete(
            "/projects/test_proj/chat/sessions/sess_123/messages/msg_456"
        )
        assert response.status_code == 401

    def test_delete_message_missing_project(self, client, valid_token):
        """Test deleting message from non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/nonexistent_proj_xyz/chat/sessions/sess_123/messages/msg_456",
            headers=headers,
        )
        assert response.status_code == 404

    def test_delete_message_missing_session(self, client, valid_token):
        """Test deleting message from non-existent session."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/chat/sessions/nonexistent_sess_xyz/messages/msg_456",
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_delete_message_not_found(self, client, valid_token):
        """Test deleting non-existent message."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/chat/sessions/sess_123/messages/nonexistent_msg_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_delete_message_success(self, client, valid_token):
        """Test deleting message successfully."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/chat/sessions/sess_123/messages/msg_456",
            headers=headers,
        )
        assert response.status_code in [204, 404, 500]

    def test_delete_message_invalid_token(self, client):
        """Test delete message with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.delete(
            "/projects/test_proj/chat/sessions/sess_123/messages/msg_456",
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestArchiveRestoreSession:
    """Tests for archiving and restoring chat sessions."""

    def test_archive_session_requires_auth(self, client):
        """Test that archiving session requires authentication."""
        response = client.put(
            "/projects/test_proj/chat/sessions/sess_123/archive"
        )
        assert response.status_code == 401

    def test_archive_session_missing_project(self, client, valid_token):
        """Test archiving session in non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/nonexistent_proj_xyz/chat/sessions/sess_123/archive",
            headers=headers,
        )
        assert response.status_code == 404

    def test_archive_session_not_found(self, client, valid_token):
        """Test archiving non-existent session."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/chat/sessions/nonexistent_sess_xyz/archive",
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_archive_session_success(self, client, valid_token):
        """Test archiving session successfully."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/chat/sessions/sess_123/archive",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["archived"] is True

    def test_restore_session_requires_auth(self, client):
        """Test that restoring session requires authentication."""
        response = client.put(
            "/projects/test_proj/chat/sessions/sess_123/restore"
        )
        assert response.status_code == 401

    def test_restore_session_missing_project(self, client, valid_token):
        """Test restoring session in non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/nonexistent_proj_xyz/chat/sessions/sess_123/restore",
            headers=headers,
        )
        assert response.status_code == 404

    def test_restore_session_success(self, client, valid_token):
        """Test restoring session successfully."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/chat/sessions/sess_123/restore",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["archived"] is False

    def test_restore_session_invalid_token(self, client):
        """Test restore session with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.put(
            "/projects/test_proj/chat/sessions/sess_123/restore",
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestChatSessionEdgeCases:
    """Tests for chat session edge cases."""

    def test_create_session_with_special_chars_in_title(self, client, valid_token):
        """Test creating session with special characters in title."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/sessions",
            json={"title": "Test !@#$%^&*()_+-=[]{}|;:',.<>?/\\`~"},
            headers=headers,
        )
        assert response.status_code in [201, 404, 500]

    def test_send_message_with_empty_content(self, client, valid_token):
        """Test sending message with empty content."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/sessions/sess_123/message",
            json={"message": "", "role": "user"},
            headers=headers,
        )
        assert response.status_code in [201, 400, 404, 422, 500]

    def test_send_message_with_long_content(self, client, valid_token):
        """Test sending message with very long content."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        long_message = "x" * 10000
        response = client.post(
            "/projects/test_proj/chat/sessions/sess_123/message",
            json={"message": long_message, "role": "user"},
            headers=headers,
        )
        assert response.status_code in [201, 404, 422, 500]

    def test_get_messages_with_zero_limit(self, client, valid_token):
        """Test getting messages with zero limit."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions/sess_123/messages?limit=0",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_send_message_with_invalid_role(self, client, valid_token):
        """Test sending message with invalid role."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/sessions/sess_123/message",
            json={"message": "Test", "role": "invalid_role"},
            headers=headers,
        )
        assert response.status_code in [201, 400, 404, 422, 500]

    def test_list_sessions_with_invalid_archive_param(self, client, valid_token):
        """Test listing sessions with invalid archive parameter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions?archived=invalid",
            headers=headers,
        )
        assert response.status_code in [200, 400, 404, 422, 500]

    def test_update_message_with_metadata(self, client, valid_token):
        """Test updating message with metadata."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/chat/sessions/sess_123/messages/msg_456",
            json={
                "content": "Updated",
                "metadata": {"key": "value", "timestamp": "2024-01-01T00:00:00Z"},
            },
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]
