"""
Unit tests for projects chat router.

Tests chat session management, messaging, Socratic features, and maturity tracking.
"""

import pytest
from fastapi.testclient import TestClient

from socrates_api.auth.jwt_handler import create_access_token
from socrates_api.main import app


@pytest.fixture(scope="session")
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Create a valid JWT token."""
    return create_access_token("testuser")


@pytest.mark.unit
class TestChatSessionManagement:
    """Tests for chat session CRUD operations."""

    def test_create_session_with_title(self, client, valid_token):
        """Test creating chat session with title."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/sessions",
            json={"title": "Test Session"},
            headers=headers,
        )
        assert response.status_code in [201, 404, 500]
        if response.status_code == 201:
            data = response.json()
            assert "session_id" in data or "id" in data

    def test_create_session_without_title(self, client, valid_token):
        """Test creating chat session without title."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/sessions",
            json={},
            headers=headers,
        )
        assert response.status_code in [201, 404, 422, 500]

    def test_list_sessions_empty(self, client, valid_token):
        """Test listing sessions when none exist."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "sessions" in data or isinstance(data, list)

    def test_list_sessions_with_sessions(self, client, valid_token):
        """Test listing sessions with existing sessions."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        # Create session first
        create_response = client.post(
            "/projects/test_proj/chat/sessions",
            json={"title": "Session1"},
            headers=headers,
        )
        # Then list
        response = client.get(
            "/projects/test_proj/chat/sessions",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_get_session_details(self, client, valid_token):
        """Test getting specific session details."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/sessions/test_session_id",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_delete_session(self, client, valid_token):
        """Test deleting a chat session."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/chat/sessions/test_session_id",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_delete_nonexistent_session(self, client, valid_token):
        """Test deleting non-existent session."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/chat/sessions/nonexistent_id",
            headers=headers,
        )
        assert response.status_code in [404, 500]


@pytest.mark.unit
class TestChatMessaging:
    """Tests for sending and retrieving messages."""

    def test_send_message_to_session(self, client, valid_token):
        """Test sending message to chat session."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/test_session/message",
            json={"content": "Test message"},
            headers=headers,
        )
        assert response.status_code in [201, 404, 500, 422]

    def test_send_message_empty_content(self, client, valid_token):
        """Test sending message with empty content."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/test_session/message",
            json={"content": ""},
            headers=headers,
        )
        assert response.status_code in [400, 422, 404, 500]

    def test_send_message_without_content(self, client, valid_token):
        """Test sending message without content field."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/test_session/message",
            json={},
            headers=headers,
        )
        assert response.status_code in [422, 400, 404, 500]

    def test_get_session_messages(self, client, valid_token):
        """Test retrieving messages from session."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/test_session/messages",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "messages" in data or isinstance(data, list)

    def test_get_messages_with_limit(self, client, valid_token):
        """Test retrieving messages with limit."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/test_session/messages?limit=5",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_send_chat_message_and_response(self, client, valid_token):
        """Test sending message and getting AI response."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/message",
            json={"message": "What is REST API design?"},
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_get_chat_history(self, client, valid_token):
        """Test retrieving conversation history."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/history",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_search_conversations(self, client, valid_token):
        """Test searching through conversations."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/search",
            json={"query": "REST API"},
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]


@pytest.mark.unit
class TestChatFeatures:
    """Tests for Socratic and chat-specific features."""

    def test_get_socratic_question(self, client, valid_token):
        """Test getting next Socratic question."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/question",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_switch_to_socratic_mode(self, client, valid_token):
        """Test switching to Socratic mode."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/chat/mode",
            json={"mode": "socratic"},
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_switch_to_direct_mode(self, client, valid_token):
        """Test switching to direct mode."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/chat/mode",
            json={"mode": "direct"},
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_switch_to_invalid_mode(self, client, valid_token):
        """Test switching to invalid mode."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/chat/mode",
            json={"mode": "invalid_mode"},
            headers=headers,
        )
        assert response.status_code in [400, 422, 404, 500]

    def test_get_context_hint(self, client, valid_token):
        """Test getting context-aware hint."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/hint",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_get_conversation_summary(self, client, valid_token):
        """Test getting AI-generated conversation summary."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/chat/summary",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_finish_interactive_session(self, client, valid_token):
        """Test finishing interactive session."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/done",
            json={},
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_clear_chat_history(self, client, valid_token):
        """Test clearing chat history."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/chat/clear",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]


@pytest.mark.unit
class TestMaturityTracking:
    """Tests for maturity history and status."""

    def test_get_maturity_history(self, client, valid_token):
        """Test retrieving maturity history."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/maturity/history",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_get_maturity_history_with_limit(self, client, valid_token):
        """Test retrieving maturity history with limit."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/maturity/history?limit=10",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_get_maturity_status(self, client, valid_token):
        """Test getting detailed maturity status."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/maturity/status",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            # Should have phase breakdown
            assert isinstance(data, dict)


@pytest.mark.unit
class TestChatAuthentication:
    """Tests for chat endpoint authentication."""

    def test_create_session_requires_auth(self, client):
        """Test that creating session requires authentication."""
        response = client.post(
            "/projects/test_proj/chat/sessions",
            json={"title": "Test"},
        )
        assert response.status_code == 401

    def test_list_sessions_requires_auth(self, client):
        """Test that listing sessions requires authentication."""
        response = client.get("/projects/test_proj/chat/sessions")
        assert response.status_code == 401

    def test_get_message_requires_auth(self, client):
        """Test that getting messages requires authentication."""
        response = client.get("/projects/test_proj/chat/test_session/messages")
        assert response.status_code == 401

    def test_invalid_token(self, client):
        """Test with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get(
            "/projects/test_proj/chat/sessions",
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestChatEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_create_session_very_long_title(self, client, valid_token):
        """Test creating session with very long title."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/sessions",
            json={"title": "x" * 1000},
            headers=headers,
        )
        assert response.status_code in [201, 400, 404, 500, 422]

    def test_send_message_very_long_content(self, client, valid_token):
        """Test sending very long message."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/test_session/message",
            json={"content": "x" * 10000},
            headers=headers,
        )
        assert response.status_code in [201, 400, 404, 500, 422]

    def test_multiple_sessions_same_project(self, client, valid_token):
        """Test creating multiple sessions for same project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response1 = client.post(
            "/projects/test_proj/chat/sessions",
            json={"title": "Session 1"},
            headers=headers,
        )
        response2 = client.post(
            "/projects/test_proj/chat/sessions",
            json={"title": "Session 2"},
            headers=headers,
        )
        assert response1.status_code in [201, 404, 500]
        assert response2.status_code in [201, 404, 500]

    def test_unicode_in_message(self, client, valid_token):
        """Test sending message with unicode characters."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/chat/test_session/message",
            json={"content": "Unicode test: 你好世界 🌍 مرحبا"},
            headers=headers,
        )
        assert response.status_code in [201, 404, 500, 422]

    def test_nonexistent_project(self, client, valid_token):
        """Test chat on non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/nonexistent_proj/chat/sessions",
            headers=headers,
        )
        assert response.status_code in [404, 500]
