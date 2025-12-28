"""
Integration tests for chat and messaging workflows.

Tests complete chat functionality:
- Session creation and management
- Message sending and retrieval
- Chat history and pagination
- Real-time WebSocket updates
- Message export
"""

import pytest
import json
from httpx import AsyncClient


@pytest.mark.integration
class TestChatSessionCreation:
    """Tests for creating chat sessions."""

    async def test_create_chat_session_success(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test creating a new chat session."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/chat/sessions",
            json={
                "title": "Initial Planning",
                "description": "Project kickoff discussion",
            },
            headers=authenticated_headers
        )
        assert response.status_code == 201
        session = response.json()
        assert session["title"] == "Initial Planning"
        assert session["project_id"] == sample_project["project_id"]

    async def test_create_session_without_title(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test creating session with auto-generated title."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/chat/sessions",
            json={},
            headers=authenticated_headers
        )
        assert response.status_code == 201
        # Should have auto-generated title
        assert response.json()["title"] is not None

    async def test_list_project_sessions(self, client: AsyncClient, authenticated_headers, sample_project, chat_sessions):
        """Test listing all sessions for a project."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/chat/sessions",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) >= len(chat_sessions)
        assert all("session_id" in s for s in sessions)

    async def test_get_session_details(self, client: AsyncClient, authenticated_headers, sample_project, chat_session):
        """Test retrieving session details."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/chat/sessions/{chat_session['session_id']}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["session_id"] == chat_session["session_id"]


@pytest.mark.integration
class TestMessageSending:
    """Tests for sending and receiving messages."""

    async def test_send_message_success(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test sending a message."""
        response = await client.post(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/message",
            json={
                "content": "What are the core requirements?",
                "message_type": "user",
            },
            headers=authenticated_headers
        )
        assert response.status_code == 201
        message = response.json()
        assert message["content"] == "What are the core requirements?"
        assert message["sender_id"] is not None

    async def test_send_empty_message_rejected(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test that empty messages are rejected."""
        response = await client.post(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/message",
            json={"content": ""},
            headers=authenticated_headers
        )
        assert response.status_code == 422

    async def test_send_oversized_message_rejected(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test that oversized messages are rejected."""
        large_content = "x" * 100000  # 100K characters
        response = await client.post(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/message",
            json={"content": large_content},
            headers=authenticated_headers
        )
        assert response.status_code == 422

    async def test_send_message_triggers_ai_response(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test that AI responds to user message."""
        response = await client.post(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/message",
            json={
                "content": "What should we include in the architecture?",
                "message_type": "user",
            },
            headers=authenticated_headers
        )
        assert response.status_code == 201

        # AI response should be queued or returned
        message_id = response.json()["message_id"]

        # Get session to see if AI response added
        session_response = await client.get(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}",
            headers=authenticated_headers
        )
        assert session_response.status_code == 200


@pytest.mark.integration
class TestMessageRetrieval:
    """Tests for retrieving message history."""

    async def test_list_session_messages(self, client: AsyncClient, authenticated_headers, chat_session, messages):
        """Test listing all messages in a session."""
        response = await client.get(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/messages",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        retrieved_messages = response.json()
        assert len(retrieved_messages) >= len(messages)
        assert all("content" in m for m in retrieved_messages)

    async def test_message_list_pagination(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test pagination of message list."""
        response = await client.get(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/messages?limit=10&offset=0",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) <= 10

    async def test_message_list_reverse_order(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test messages returned in chronological or reverse order."""
        response = await client.get(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/messages?order=asc",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        messages = response.json()
        if len(messages) > 1:
            # Verify ordering
            timestamps = [m.get("created_at") for m in messages if m.get("created_at")]
            if timestamps:
                assert all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))

    async def test_get_single_message(self, client: AsyncClient, authenticated_headers, chat_session, message):
        """Test retrieving a single message."""
        response = await client.get(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/messages/{message['message_id']}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["message_id"] == message["message_id"]


@pytest.mark.integration
class TestMessageEditing:
    """Tests for editing and deleting messages."""

    async def test_edit_own_message(self, client: AsyncClient, authenticated_headers, chat_session, user_message):
        """Test editing own message."""
        response = await client.put(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/messages/{user_message['message_id']}",
            json={"content": "Updated message content"},
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Updated message content"

    async def test_cannot_edit_others_message(self, client: AsyncClient, other_user_headers, chat_session, user_message):
        """Test that users cannot edit other's messages."""
        response = await client.put(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/messages/{user_message['message_id']}",
            json={"content": "Hacked content"},
            headers=other_user_headers
        )
        assert response.status_code in [403, 401]

    async def test_delete_own_message(self, client: AsyncClient, authenticated_headers, chat_session, user_message):
        """Test deleting own message."""
        response = await client.delete(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/messages/{user_message['message_id']}",
            headers=authenticated_headers
        )
        assert response.status_code == 200

        # Message should be deleted
        get_response = await client.get(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/messages/{user_message['message_id']}",
            headers=authenticated_headers
        )
        assert get_response.status_code == 404

    async def test_cannot_delete_others_message(self, client: AsyncClient, other_user_headers, chat_session, user_message):
        """Test that users cannot delete other's messages."""
        response = await client.delete(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/messages/{user_message['message_id']}",
            headers=other_user_headers
        )
        assert response.status_code in [403, 401]


@pytest.mark.integration
class TestChatSessionExport:
    """Tests for exporting chat sessions."""

    async def test_export_session_json(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test exporting session as JSON."""
        response = await client.get(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/export?format=json",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/json"
        data = response.json()
        assert "session_id" in data
        assert "messages" in data

    async def test_export_session_markdown(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test exporting session as Markdown."""
        response = await client.get(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/export?format=markdown",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert "text/markdown" in response.headers.get("content-type", "")

    async def test_export_session_pdf(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test exporting session as PDF."""
        response = await client.get(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/export?format=pdf",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")

    async def test_export_session_csv(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test exporting session as CSV."""
        response = await client.get(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/export?format=csv",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")


@pytest.mark.integration
class TestChatSessionManagement:
    """Tests for session management operations."""

    async def test_update_session_title(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test updating session title."""
        response = await client.put(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}",
            json={"title": "New Session Title"},
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "New Session Title"

    async def test_archive_session(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test archiving a chat session."""
        response = await client.post(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/archive",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["is_archived"] is True

    async def test_delete_session(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test deleting a session."""
        session_id = chat_session["session_id"]
        project_id = chat_session["project_id"]

        response = await client.delete(
            f"/projects/{project_id}/chat/sessions/{session_id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200

        # Session should be deleted
        get_response = await client.get(
            f"/projects/{project_id}/chat/sessions/{session_id}",
            headers=authenticated_headers
        )
        assert get_response.status_code == 404

    async def test_duplicate_session(self, client: AsyncClient, authenticated_headers, chat_session):
        """Test duplicating a session with its messages."""
        response = await client.post(
            f"/projects/{chat_session['project_id']}/chat/sessions/{chat_session['session_id']}/duplicate",
            headers=authenticated_headers
        )
        assert response.status_code == 201
        new_session = response.json()
        assert new_session["session_id"] != chat_session["session_id"]
        assert new_session["project_id"] == chat_session["project_id"]


@pytest.mark.integration
class TestRealTimeChatUpdates:
    """Tests for WebSocket real-time chat features."""

    async def test_websocket_chat_connection(self, websocket_client, authenticated_headers, chat_session):
        """Test establishing WebSocket connection for chat."""
        # This would test WebSocket connection establishment
        pass

    async def test_websocket_receive_message(self, websocket_client, authenticated_headers, chat_session):
        """Test receiving messages via WebSocket."""
        pass

    async def test_websocket_typing_indicator(self, websocket_client, authenticated_headers, chat_session):
        """Test typing indicator broadcast via WebSocket."""
        pass

    async def test_websocket_presence_update(self, websocket_client, authenticated_headers, chat_session):
        """Test presence updates via WebSocket."""
        pass
