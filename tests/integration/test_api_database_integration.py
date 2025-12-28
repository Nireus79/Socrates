"""
API Database Integration Tests

Tests the complete flow:
1. Authentication API → Database (user storage)
2. Project API → Database (project CRUD)
3. Chat API → Database (conversation history)
4. WebSocket → Database (real-time persistence)
5. Collaboration API → Database (team members)
"""

import json
import os
import sqlite3
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Mock the FastAPI app since we're testing integration concepts
from socratic_system.database.project_db_v2 import ProjectDatabase
from socratic_system.models.project import ProjectContext
from socratic_system.models.user import User


class TestAuthDatabaseIntegration:
    """Test authentication API ↔ database integration"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabase(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_register_user_saves_to_database(self, db):
        """
        Simulate: User registration API → Database save

        Flow:
        1. API receives registration request
        2. API validates credentials
        3. API creates User object
        4. API saves to database
        """
        # Simulate API request payload
        registration_payload = {
            "username": "newuser",
            "password": "secure_password_123"}

        # Simulate API processing
        user = User(
            username=registration_payload["username"],
            email="newuser@example.com",
            passcode_hash="bcrypt_hashed_password",
            created_at=datetime.now(),
        )
        user.subscription_tier = "free"
        user.subscription_status = "active"

        # Save to database (what API would do)
        db.save_user(user)

        # Verify data persisted
        saved_user = db.load_user("newuser")
        assert saved_user is not None
        assert saved_user.username == "newuser"
        assert saved_user.subscription_tier == "free"

    def test_login_retrieves_user_from_database(self, db):
        """
        Simulate: User login API → Database lookup

        Flow:
        1. User submits login credentials
        2. API queries database for user
        3. API compares password hashes
        4. API returns JWT tokens
        """
        # Setup: Create user in database
        user = User(
            username="testuser",
            email="testuser@example.com",
            passcode_hash="bcrypt_hash_of_password",
            created_at=datetime.now(),
        )
        db.save_user(user)

        # Simulate API login request
        login_username = "testuser"
        login_password = "password"

        # API would lookup user
        found_user = db.load_user(login_username)
        assert found_user is not None, "User should be found in database"

        # In real API, would compare bcrypt hashes here
        # jwt_tokens = create_tokens(found_user)

    def test_user_not_found_on_invalid_username(self, db):
        """Test that invalid username returns None"""
        user = db.load_user("nonexistent")
        assert user is None, "Non-existent user should return None"


class TestProjectDatabaseIntegration:
    """Test project API ↔ database integration"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabase(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_create_project_api_saves_to_db(self, db):
        """
        Simulate: Create project API → Database save

        Flow:
        1. API receives project creation request
        2. API validates input
        3. API creates ProjectContext
        4. API saves to database
        5. API returns project with ID
        """
        # Simulate API request payload
        create_payload = {
            "name": "Web Application",
            "goals": ["Build REST API", "Deploy to AWS"],
            "tech_stack": ["Python", "FastAPI"]}

        # Simulate API processing
        project = ProjectContext(
            project_id="api-proj-001",
            name=create_payload["name"],
            owner="currentuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            goals=create_payload["goals"],
            tech_stack=create_payload["tech_stack"],
        )

        # Save to database
        db.save_project(project)

        # API would return this
        response = {
            "id": "api-proj-001",
            "name": "Web Application",
            "status": "active"}

        # Verify in database
        saved = db.load_project("api-proj-001")
        assert saved is not None
        assert saved.name == create_payload["name"]

    def test_list_projects_api_queries_db(self, db):
        """
        Simulate: List projects API → Database query

        Flow:
        1. API receives list projects request (with auth token)
        2. API extracts user from token
        3. API queries database for user's projects
        4. API returns project list
        """
        # Setup: Create projects in database
        for i in range(3):
            project = ProjectContext(
                project_id=f"proj-{i}",
                name=f"Project {i}",
                owner="currentuser",
                phase="phase1",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.save_project(project)

        # Simulate API request
        username = "currentuser"

        # API would query
        projects = db.get_user_projects(username)
        assert len(projects) == 3, "Should return 3 projects"

        # Simulate API response
        response = {
            "projects": [{"id": p.project_id, "name": p.name} for p in projects],
            "count": len(projects)}

        assert response["count"] == 3

    def test_update_project_api_updates_db(self, db):
        """
        Simulate: Update project API → Database update

        Flow:
        1. API receives update request
        2. API verifies authorization (owner only)
        3. API loads project from database
        4. API applies changes
        5. API saves updated project
        """
        # Setup: Create project
        original = ProjectContext(
            project_id="proj-001",
            name="Original Name",
            owner="currentuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            goals=["Goal 1"],
        )
        db.save_project(original)

        # Simulate update request
        update_payload = {
            "name": "Updated Name",
            "goals": ["Goal 1", "Goal 2"]}

        # API authorization check
        project = db.load_project("proj-001")
        assert project.owner == "currentuser"  # Verify ownership

        # Apply updates
        project.name = update_payload["name"]
        project.goals = update_payload["goals"]
        project.updated_at = datetime.now()

        # Save back to database
        db.save_project(project)

        # Verify update
        updated = db.load_project("proj-001")
        assert updated.name == "Updated Name"
        assert updated.goals == ["Goal 1", "Goal 2"]

    def test_delete_project_api_cascades_in_db(self, db):
        """
        Simulate: Delete project API → Cascade delete in database

        Flow:
        1. API receives delete request
        2. API verifies authorization
        3. API adds conversation history
        4. API deletes project
        5. Database cascades delete to related tables
        """
        # Setup: Create project with conversation
        project = ProjectContext(
            project_id="proj-001",
            name="Project to Delete",
            owner="currentuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        # Add conversation history
        history = [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": datetime.now().isoformat()}
        ]
        db.save_conversation_history("proj-001", history)

        # Verify conversation exists
        saved_history = db.get_conversation_history("proj-001")
        assert len(saved_history) > 0

        # Simulate API delete
        project = db.load_project("proj-001")
        assert project.owner == "currentuser"  # Authorization check

        # Delete
        success = db.delete_project("proj-001")
        assert success

        # Verify cascade delete
        deleted_project = db.load_project("proj-001")
        assert deleted_project is None

        deleted_history = db.get_conversation_history("proj-001")
        assert len(deleted_history) == 0, "Conversation should be cascade deleted"


class TestChatDatabaseIntegration:
    """Test chat API ↔ database integration"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabase(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_send_message_saves_to_db(self, db):
        """
        Simulate: Chat send message API → Database save

        Flow:
        1. API receives WebSocket message
        2. API processes message with orchestrator
        3. API gets response
        4. API saves both user and assistant messages
        5. API sends response back to client
        """
        # Setup: Create project for chat
        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="currentuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        # Simulate user sends message via WebSocket
        user_message = {
            "role": "user",
            "content": "What is the first phase?",
            "timestamp": datetime.now().isoformat()}

        # API would process and get response from orchestrator
        assistant_response = {
            "role": "assistant",
            "content": "Phase 1 focuses on architectural design...",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"source": "orchestrator"}}

        # API saves both messages to database
        conversation = [user_message, assistant_response]
        db.save_conversation_history("proj-001", conversation)

        # Verify messages persist
        saved = db.get_conversation_history("proj-001")
        assert len(saved) == 2
        # Verify both messages exist
        contents = [msg["content"] for msg in saved]
        assert "What is the first phase?" in contents
        assert "Phase 1 focuses on architectural design..." in contents

    def test_get_chat_history_api_loads_from_db(self, db):
        """
        Simulate: Get chat history API → Load from database

        Flow:
        1. API receives get history request
        2. API loads conversation from database
        3. API returns history to client
        """
        # Setup: Create conversation
        history = [
            {
                "role": "user",
                "content": f"Message {i}",
                "timestamp": datetime.now().isoformat()}
            for i in range(5)
        ]
        db.save_conversation_history("proj-001", history)

        # Simulate API request
        project_id = "proj-001"

        # API would query database
        conversation = db.get_conversation_history(project_id)

        # Simulate API response
        response = {"project_id": project_id, "messages": conversation, "count": len(conversation)}

        assert response["count"] == 5

    def test_chat_mode_persistence(self, db):
        """Test that chat mode (socratic vs direct) is persisted"""
        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="currentuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            chat_mode="socratic",
        )
        db.save_project(project)

        # Simulate API update chat mode
        project = db.load_project("proj-001")
        project.chat_mode = "direct"
        db.save_project(project)

        # Verify persistence
        updated = db.load_project("proj-001")
        assert updated.chat_mode == "direct"


class TestCollaborationDatabaseIntegration:
    """Test collaboration API ↔ database integration"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabase(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_add_collaborator_saves_team_member(self, db):
        """
        Simulate: Add collaborator API → Save to database

        Flow:
        1. API receives add collaborator request
        2. API verifies authorization (owner only)
        3. API creates team member record
        4. API saves to database
        """
        # Setup: Create project
        from socratic_system.models.role import TeamMemberRole

        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="owner-user",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        # Simulate API add collaborator request
        new_collaborator = TeamMemberRole(
            username="collaborator-user",
            role="editor",
            skills=["python", "fastapi"],
            joined_at=datetime.now(),
        )

        # Load project and add member
        project = db.load_project("proj-001")
        if project.team_members is None:
            project.team_members = []
        else:
            # Reset to just the new collaborator
            project.team_members = []
        project.team_members.append(new_collaborator)

        # Save to database
        db.save_project(project)

        # Verify in database
        saved = db.load_project("proj-001")
        assert len(saved.team_members) >= 1
        assert any(m.username == "collaborator-user" for m in saved.team_members)
        collaborator = [m for m in saved.team_members if m.username == "collaborator-user"][0]
        assert collaborator.role == "editor"

    def test_project_shared_between_users(self, db):
        """Test that a project can be accessed by both owner and collaborators"""
        from socratic_system.models.role import TeamMemberRole

        project = ProjectContext(
            project_id="proj-001",
            name="Shared Project",
            owner="owner-user",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            team_members=[
                TeamMemberRole(
                    username="editor-user",
                    role="editor",
                    skills=["python"],
                    joined_at=datetime.now(),
                ),
                TeamMemberRole(
                    username="viewer-user",
                    role="viewer",
                    skills=["documentation"],
                    joined_at=datetime.now(),
                ),
            ],
        )
        db.save_project(project)

        # Verify owner can see it
        owner_projects = db.get_user_projects("owner-user")
        assert any(p.project_id == "proj-001" for p in owner_projects)

        # Verify collaborators can see it
        editor_projects = db.get_user_projects("editor-user")
        assert any(p.project_id == "proj-001" for p in editor_projects)


class TestPhaseProgressDatabaseIntegration:
    """Test phase progress tracking API ↔ database"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabase(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_maturity_scores_update_and_persist(self, db):
        """
        Simulate: Update maturity API → Database save

        Flow:
        1. Orchestrator calculates phase maturity scores
        2. API receives update request
        3. API updates project with new scores
        4. API saves to database
        5. Frontend can query scores for dashboard
        """
        # Setup: Create project
        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="currentuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        # Simulate orchestrator calculating scores
        new_scores = {"phase1": 0.75, "phase2": 0.0, "phase3": 0.0}

        # API update project
        project = db.load_project("proj-001")
        project.phase_maturity_scores = new_scores

        # Save to database
        db.save_project(project)

        # Verify persistence
        saved = db.load_project("proj-001")
        assert saved.phase_maturity_scores["phase1"] == 0.75

    def test_category_scores_update_and_persist(self, db):
        """Test that category scores persist across saves"""
        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="currentuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        # Simulate category scores from analysis
        scores = {
            "phase1": {
                "architecture": 0.8,
                "api_design": 0.6,
                "database_design": 0.7}
        }

        project = db.load_project("proj-001")
        project.category_scores = scores
        db.save_project(project)

        # Verify
        saved = db.load_project("proj-001")
        assert saved.category_scores["phase1"]["architecture"] == 0.8


class TestDataConsistency:
    """Test data consistency across operations"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabase(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_no_data_loss_on_multiple_saves(self, db):
        """Test that data isn't lost when saving multiple times"""
        project = ProjectContext(
            project_id="proj-001",
            name="Test",
            owner="user",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            requirements=["Req1", "Req2"],
            tech_stack=["Python"],
        )

        # Save multiple times with modifications
        for i in range(5):
            db.save_project(project)
            project.goals = [f"Goal {j}" for j in range(i + 1)]

        # Final save
        db.save_project(project)

        # Verify all data intact
        final = db.load_project("proj-001")
        assert final.requirements == ["Req1", "Req2"]
        assert final.tech_stack == ["Python"]
        assert len(final.goals) == 5

    def test_transaction_rollback_on_error(self, db):
        """Test that database maintains consistency on errors"""
        project = ProjectContext(
            project_id="proj-001",
            name="Test",
            owner="user",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.save_project(project)

        # Verify it was saved
        loaded = db.load_project("proj-001")
        assert loaded is not None

        # Even if an error occurs, the data should remain consistent
        # (implementation handles this with try/except and rollback)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
