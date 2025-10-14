#!/usr/bin/env python3
"""
Test Chat Mode Integration
==========================
Verify ChatSession model, repository, and database integration works correctly.
"""

import sys
import os
import uuid
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_chat_mode_integration():
    """Test complete chat mode functionality"""
    print("=" * 70)
    print("CHAT MODE INTEGRATION TEST")
    print("=" * 70)

    try:
        # Import required modules
        from src import initialize_package
        from src.database import get_database, reset_database
        from src.models import ChatSession, ConversationMessage, User, Project, ProjectStatus
        from src.core import DateTimeHelper

        print("[PASS] Imports successful")

        # Initialize system
        services = initialize_package()
        reset_database()
        db = get_database()

        print("[PASS] Database initialized")

        # Test 1: Verify chat_sessions table exists
        print("\n--- TEST 1: Database Schema ---")
        result = db.db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'"
        )
        assert result, "chat_sessions table should exist"
        print("[PASS] chat_sessions table exists")

        # Test 2: Verify conversation_type column exists
        cursor_result = db.db_manager.execute_query("PRAGMA table_info(conversation_messages)")
        columns = [row['name'] for row in cursor_result]
        assert 'conversation_type' in columns, "conversation_type column should exist"
        print("[PASS] conversation_type column exists")

        # Test 3: Verify ChatSessionRepository is available
        print("\n--- TEST 2: Repository Access ---")
        assert hasattr(db, 'chat_sessions'), "db.chat_sessions should be available"
        print("[PASS] ChatSessionRepository registered")

        # Test 4: Create test user and project
        print("\n--- TEST 3: Setup Test Data ---")
        user = User(
            id=str(uuid.uuid4()),
            username="chat_test_user",
            email="test@example.com",
            password_hash="dummy_hash"
        )
        assert db.users.create(user), "User creation should succeed"
        print("[PASS] Test user created")

        project = Project(
            id=str(uuid.uuid4()),
            name="Chat Test Project",
            description="Testing chat mode",
            owner_id=user.id,
            status=ProjectStatus.ACTIVE
        )
        assert db.projects.create(project), "Project creation should succeed"
        print("[PASS] Test project created")

        # Test 5: Create ChatSession
        print("\n--- TEST 4: ChatSession CRUD ---")
        chat_session = ChatSession(
            id=str(uuid.uuid4()),
            project_id=project.id,
            user_id=user.id,
            conversation_context="Testing chat mode functionality",
            chat_mode="project_focused"
        )

        assert db.chat_sessions.create(chat_session), "ChatSession creation should succeed"
        print("[PASS] ChatSession created")

        # Test 6: Retrieve ChatSession
        retrieved_session = db.chat_sessions.get_by_id(chat_session.id)
        assert retrieved_session is not None, "ChatSession retrieval should succeed"
        assert retrieved_session.project_id == project.id, "Project ID should match"
        assert retrieved_session.user_id == user.id, "User ID should match"
        print("[PASS] ChatSession retrieved")

        # Test 7: Update ChatSession
        chat_session.message_count = 5
        chat_session.add_topic("Project Architecture")
        chat_session.add_insight("technical", "User prefers microservices")

        assert db.chat_sessions.update(chat_session), "ChatSession update should succeed"
        print("[PASS] ChatSession updated")

        # Test 8: Verify updates persisted
        updated_session = db.chat_sessions.get_by_id(chat_session.id)
        assert updated_session.message_count == 5, "Message count should be updated"
        assert "Project Architecture" in updated_session.topics_discussed, "Topic should be added"
        assert "technical" in updated_session.insights_extracted, "Insight should be added"
        print("[PASS] Updates persisted")

        # Test 9: Create chat conversation message
        print("\n--- TEST 5: Chat Messages ---")
        chat_message = ConversationMessage(
            id=str(uuid.uuid4()),
            session_id=chat_session.id,
            project_id=project.id,
            message_type="user",
            content="Hello, I'd like to discuss the project architecture",
            conversation_type="chat"  # Unexpected argument
        )

        assert db.conversation_messages.create(chat_message), "Chat message creation should succeed"
        print("[PASS] Chat message created")

        # Test 10: Verify conversation_type filtering
        chat_messages = db.db_manager.execute_query(
            "SELECT * FROM conversation_messages WHERE conversation_type = 'chat'"
        )
        assert len(chat_messages) == 1, "Should have exactly one chat message"
        assert chat_messages[0]['content'] == chat_message.content, "Content should match"
        print("[PASS] Chat message filtering works")

        # Test 11: Test session querying methods
        print("\n--- TEST 6: Query Methods ---")
        user_sessions = db.chat_sessions.get_by_user_id(user.id)
        assert len(user_sessions) == 1, "Should find one session for user"
        print("[PASS] get_by_user_id works")

        project_sessions = db.chat_sessions.get_by_project_id(project.id)
        assert len(project_sessions) == 1, "Should find one session for project"
        print("[PASS] get_by_project_id works")

        active_sessions = db.chat_sessions.get_active_sessions(user_id=user.id)
        assert len(active_sessions) == 1, "Should find one active session"
        print("[PASS] get_active_sessions works")

        # Test 12: Test convenience methods
        print("\n--- TEST 7: Convenience Methods ---")
        assert db.chat_sessions.increment_message_count(chat_session.id), "Increment should succeed"

        incremented_session = db.chat_sessions.get_by_id(chat_session.id)
        assert incremented_session.message_count == 6, "Message count should be incremented"
        print("[PASS] increment_message_count works")

        assert db.chat_sessions.end_session(chat_session.id), "End session should succeed"

        ended_session = db.chat_sessions.get_by_id(chat_session.id)
        assert ended_session.status.value == "completed", "Session should be completed"
        print("[PASS] end_session works")

        # Test 13: Cleanup
        print("\n--- TEST 8: Cleanup ---")
        assert db.conversation_messages.delete(chat_message.id), "Message deletion should succeed"
        assert db.chat_sessions.delete(chat_session.id), "ChatSession deletion should succeed"
        assert db.projects.delete(project.id), "Project deletion should succeed"
        assert db.users.delete(user.id), "User deletion should succeed"
        print("[PASS] Cleanup completed")

        print("\n" + "=" * 70)
        print("[SUCCESS] ALL CHAT MODE INTEGRATION TESTS PASSED!")
        print("Chat mode backend infrastructure is ready for use.")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_chat_mode_integration()
    sys.exit(0 if success else 1)
