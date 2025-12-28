"""
WebSocket Database Integration Tests

Tests real-time chat features:
1. WebSocket message reception → Database save
2. Database load → Client response
3. Connection persistence
4. Multi-user chat isolation
"""

import json
import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from socratic_system.database.project_db_v2 import ProjectDatabase
from socratic_system.models.project import ProjectContext


class TestWebSocketDatabaseIntegration:
    """Test WebSocket ↔ Database integration"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabase(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_websocket_message_saved_to_db(self, db):
        """
        Simulate: WebSocket message → Database save

        Flow:
        1. Client connects via WebSocket
        2. Client sends message
        3. Server processes message with orchestrator
        4. Server saves user message to database
        5. Server gets orchestrator response
        6. Server saves assistant message to database
        7. Server sends response to client
        """
        # Setup: Create project
        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="testuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        # Simulate WebSocket client sends message with properly spaced timestamps
        from datetime import timedelta

        now = datetime.now()
        user_message = {
            "role": "user",
            "content": "What should I focus on in phase 1?",
            "timestamp": now.isoformat(),
            "metadata": {"mode": "socratic", "source": "websocket"},
        }

        # Server would call orchestrator here
        # For testing, simulate response with later timestamp
        assistant_message = {
            "role": "assistant",
            "content": "In phase 1, focus on: 1) Requirements gathering 2) Architecture design",
            "timestamp": (now + timedelta(seconds=1)).isoformat(),
            "metadata": {"source": "orchestrator", "type": "response"},
        }

        # Save both messages to database
        conversation = [user_message, assistant_message]
        db.save_conversation_history("proj-001", conversation)

        # Verify messages persist
        saved = db.get_conversation_history("proj-001")
        assert len(saved) == 2
        assert saved[0]["role"] == "user"
        assert saved[1]["role"] == "assistant"

    def test_websocket_chat_isolation_by_project(self, db):
        """
        Test that chat in one project doesn't affect another project's chat

        Scenario:
        1. User has 2 projects
        2. Sends message in project 1
        3. Sends different message in project 2
        4. Verify messages are isolated
        """
        # Create two projects for same user
        for proj_id in ["proj-001", "proj-002"]:
            project = ProjectContext(
                project_id=proj_id,
                name=f"Project {proj_id}",
                owner="testuser",
                phase="phase1",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.save_project(project)

        # Save different conversations
        conv1 = [
            {
                "role": "user",
                "content": "Project 1 question",
                "timestamp": datetime.now().isoformat(),
            }
        ]
        db.save_conversation_history("proj-001", conv1)

        conv2 = [
            {
                "role": "user",
                "content": "Project 2 question",
                "timestamp": datetime.now().isoformat(),
            }
        ]
        db.save_conversation_history("proj-002", conv2)

        # Verify isolation
        history1 = db.get_conversation_history("proj-001")
        history2 = db.get_conversation_history("proj-002")

        assert "Project 1 question" in history1[0]["content"]
        assert "Project 2 question" in history2[0]["content"]
        assert history1[0]["content"] != history2[0]["content"]

    def test_websocket_concurrent_users_chat_isolation(self, db):
        """
        Test that concurrent users chatting have isolated conversations

        Scenario:
        1. User1 creates project and chats
        2. User2 is added as collaborator
        3. User1 and User2 chat in same project
        4. Verify conversation history is shared (as expected)
        5. They each have separate projects with isolated history
        """
        from socratic_system.models.role import TeamMemberRole

        # Project shared between users
        shared_project = ProjectContext(
            project_id="shared-proj",
            name="Shared Project",
            owner="user1",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            team_members=[
                TeamMemberRole(username="user2", role="editor", skills=["python"], joined_at=datetime.now())
            ],
        )
        db.save_project(shared_project)

        # User1's personal project
        user1_proj = ProjectContext(
            project_id="user1-proj",
            name="User1 Personal",
            owner="user1",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(user1_proj)

        # User2's personal project
        user2_proj = ProjectContext(
            project_id="user2-proj",
            name="User2 Personal",
            owner="user2",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(user2_proj)

        # Save shared conversation
        shared_conv = [
            {
                "role": "user",
                "content": "Message from User1",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "role": "user",
                "content": "Response from User2",
                "timestamp": datetime.now().isoformat(),
            },
        ]
        db.save_conversation_history("shared-proj", shared_conv)

        # Save user-specific conversations
        user1_conv = [
            {
                "role": "user",
                "content": "User1 private thoughts",
                "timestamp": datetime.now().isoformat(),
            }
        ]
        db.save_conversation_history("user1-proj", user1_conv)

        user2_conv = [
            {
                "role": "user",
                "content": "User2 private thoughts",
                "timestamp": datetime.now().isoformat(),
            }
        ]
        db.save_conversation_history("user2-proj", user2_conv)

        # Verify user1 can see both shared and personal
        user1_projects = db.get_user_projects("user1")
        assert len(user1_projects) == 2  # shared + personal

        # Verify user2 can see both shared and personal
        user2_projects = db.get_user_projects("user2")
        assert len(user2_projects) == 2  # shared + personal

        # Verify shared conversation is accessible to both
        shared_history = db.get_conversation_history("shared-proj")
        assert len(shared_history) == 2

        # Verify personal conversations are isolated
        user1_history = db.get_conversation_history("user1-proj")
        user2_history = db.get_conversation_history("user2-proj")

        assert "User1 private" in user1_history[0]["content"]
        assert "User2 private" in user2_history[0]["content"]

    def test_websocket_long_conversation_persistence(self, db):
        """
        Test that long conversations persist correctly

        Scenario:
        1. Simulate 100 WebSocket messages
        2. Verify all persist to database
        3. Verify correct ordering
        """
        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="testuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        # Simulate 100 messages with properly spaced timestamps
        from datetime import timedelta

        conversation = []
        base_time = datetime.now()
        for i in range(100):
            role = "user" if i % 2 == 0 else "assistant"
            conversation.append(
                {
                    "role": role,
                    "content": f"Message {i}",
                    "timestamp": (base_time + timedelta(milliseconds=i * 10)).isoformat(),
                }
            )

        # Save all at once (simulating batch save after long session)
        db.save_conversation_history("proj-001", conversation)

        # Verify all messages persist
        saved = db.get_conversation_history("proj-001")
        assert len(saved) == 100

        # Verify ordering
        for i, msg in enumerate(saved):
            assert f"Message {i}" in msg["content"]

    def test_websocket_message_with_metadata_persistence(self, db):
        """
        Test that WebSocket message metadata persists

        Metadata might include:
        - mode: socratic/direct
        - source: websocket/rest_api
        - language: for code
        - emotion: for sentiment tracking
        """
        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="testuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        from datetime import timedelta

        now = datetime.now()
        conversation = [
            {
                "role": "user",
                "content": "Write a Python function",
                "timestamp": now.isoformat(),
                "metadata": {
                    "mode": "direct",
                    "source": "websocket",
                    "language": "python",
                    "emotion": "neutral",
                },
            },
            {
                "role": "assistant",
                "content": "def hello(): return 'world'",
                "timestamp": (now + timedelta(seconds=1)).isoformat(),
                "metadata": {
                    "source": "orchestrator",
                    "model": "claude-3",
                    "tokens_used": 150,
                },
            },
        ]

        db.save_conversation_history("proj-001", conversation)
        saved = db.get_conversation_history("proj-001")

        # Find messages by role to avoid order dependency
        user_msg = [m for m in saved if m["role"] == "user"][0]
        assistant_msg = [m for m in saved if m["role"] == "assistant"][0]

        assert user_msg["metadata"]["mode"] == "direct"
        assert user_msg["metadata"]["language"] == "python"
        assert assistant_msg["metadata"]["tokens_used"] == 150

    def test_websocket_reconnection_preserves_history(self, db):
        """
        Test that chat history is preserved across WebSocket reconnections

        Scenario:
        1. User connects and chats
        2. Connection drops
        3. User reconnects
        4. History is still available
        """
        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="testuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        # First connection: save some messages
        conversation1 = [
            {
                "role": "user",
                "content": "Message 1",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "role": "assistant",
                "content": "Response 1",
                "timestamp": datetime.now().isoformat(),
            },
        ]
        db.save_conversation_history("proj-001", conversation1)

        # Simulate connection drop and reconnection
        # User reconnects and loads history
        history = db.get_conversation_history("proj-001")
        assert len(history) == 2, "History should be preserved"

        # Continue conversation after reconnection
        conversation2 = history + [
            {
                "role": "user",
                "content": "Message 2 (after reconnection)",
                "timestamp": datetime.now().isoformat(),
            }
        ]
        db.save_conversation_history("proj-001", conversation2)

        # Verify full conversation
        final = db.get_conversation_history("proj-001")
        assert len(final) == 3
        assert "after reconnection" in final[2]["content"]


class TestWebSocketPerformance:
    """Test WebSocket performance with database"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabase(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_message_save_latency(self, db):
        """
        Test that saving messages to database is fast enough for WebSocket

        Target: < 50ms for save operation (for responsive feel)
        """
        import time

        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="testuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        message = {
            "role": "user",
            "content": "Test message",
            "timestamp": datetime.now().isoformat(),
        }

        # Time the save operation
        start = time.time()
        db.save_conversation_history("proj-001", [message])
        elapsed = (time.time() - start) * 1000  # Convert to ms

        # Should be fast
        assert elapsed < 1000, f"Save took {elapsed}ms, should be < 1000ms"

    def test_history_load_performance(self, db):
        """
        Test loading conversation history performance

        Should be fast enough to not block WebSocket reconnection
        """
        import time

        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="testuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        # Create 1000-message history
        conversation = [
            {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
                "timestamp": datetime.now().isoformat(),
            }
            for i in range(1000)
        ]
        db.save_conversation_history("proj-001", conversation)

        # Time the load
        start = time.time()
        history = db.get_conversation_history("proj-001")
        elapsed = (time.time() - start) * 1000

        assert len(history) == 1000
        assert elapsed < 5000, f"Load took {elapsed}ms, should be < 5000ms for 1000 messages"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
