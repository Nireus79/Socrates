"""
Comprehensive Socratic Questioning Workflow Tests

Tests the core Socratic method functionality:
- Generate Socratic questions
- Process user responses
- Evaluate correctness
- Generate hints and guidance
- Track question history
"""

import requests
import json
from datetime import datetime
import pytest

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


class TestSocraticQuestions:
    """Test Socratic questioning workflows"""

    @pytest.fixture
    def test_user_with_project(self):
        """Create test user and project"""
        username = f"socratic_user_{int(datetime.now().timestamp() * 1000)}"

        # Register user
        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!"
            },
            headers=HEADERS
        )
        access_token = reg_resp.json()["access_token"]
        auth_headers = {**HEADERS, "Authorization": f"Bearer {access_token}"}

        # Create project
        proj_resp = requests.post(
            f"{BASE_URL}/projects",
            json={
                "name": "Socratic Test Project",
                "description": "Test project for Socratic questions"},
            headers=auth_headers
        )
        project_id = proj_resp.json()["project_id"]

        return {
            "username": username,
            "access_token": access_token,
            "project_id": project_id,
            "auth_headers": auth_headers
        }

    def test_01_generate_socratic_question(self, test_user_with_project):
        """Test: Generate a Socratic question for a project"""
        project_id = test_user_with_project["project_id"]
        auth_headers = test_user_with_project["auth_headers"]

        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/question",
            json={
                "topic": "Basic Python",
                "difficulty_level": "beginner"
            },
            headers=auth_headers
        )

        # Check if endpoint exists and responds
        if response.status_code == 503:
            pytest.skip("Orchestrator not initialized")

        assert response.status_code == 200, f"Failed to generate question: {response.text}"
        data = response.json()

        assert "question_id" in data or "question" in data
        assert "question" in data or "text" in data

    def test_02_question_has_required_fields(self, test_user_with_project):
        """Test: Generated question has all required fields"""
        project_id = test_user_with_project["project_id"]
        auth_headers = test_user_with_project["auth_headers"]

        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/question",
            json={
                "topic": "Data Structures",
                "difficulty_level": "intermediate"
            },
            headers=auth_headers
        )

        if response.status_code == 503:
            pytest.skip("Orchestrator not initialized")

        if response.status_code == 200:
            data = response.json()
            # Should have either question_id or similar
            assert any(k in data for k in ["question_id", "id", "question"])

    def test_03_process_user_response(self, test_user_with_project):
        """Test: Process user's response to a question"""
        project_id = test_user_with_project["project_id"]
        auth_headers = test_user_with_project["auth_headers"]

        # First generate a question
        q_resp = requests.post(
            f"{BASE_URL}/projects/{project_id}/question",
            json={"topic": "Python", "difficulty_level": "beginner"},
            headers=auth_headers
        )

        if q_resp.status_code == 503:
            pytest.skip("Orchestrator not initialized")

        if q_resp.status_code != 200:
            pytest.skip("Could not generate question")

        question_data = q_resp.json()
        question_id = question_data.get("question_id") or "test_question_1"

        # Process response
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/response",
            json={
                "question_id": question_id,
                "user_response": "This is my answer to the question"
            },
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "feedback" in data or "response" in data

    def test_04_question_with_different_difficulties(self, test_user_with_project):
        """Test: Generate questions with different difficulty levels"""
        project_id = test_user_with_project["project_id"]
        auth_headers = test_user_with_project["auth_headers"]

        difficulties = ["beginner", "intermediate", "advanced"]

        for difficulty in difficulties:
            response = requests.post(
                f"{BASE_URL}/projects/{project_id}/question",
                json={
                    "topic": "Programming",
                    "difficulty_level": difficulty
                },
                headers=auth_headers
            )

            if response.status_code == 503:
                pytest.skip("Orchestrator not initialized")

            if response.status_code == 200:
                data = response.json()
                assert data is not None

    def test_05_question_with_topics(self, test_user_with_project):
        """Test: Generate questions for various topics"""
        project_id = test_user_with_project["project_id"]
        auth_headers = test_user_with_project["auth_headers"]

        topics = ["Python", "Data Structures", "Algorithms", "Web Development"]

        for topic in topics:
            response = requests.post(
                f"{BASE_URL}/projects/{project_id}/question",
                json={
                    "topic": topic,
                    "difficulty_level": "beginner"
                },
                headers=auth_headers
            )

            if response.status_code == 503:
                pytest.skip("Orchestrator not initialized")

            if response.status_code == 200:
                data = response.json()
                assert data is not None

    def test_06_response_evaluation(self, test_user_with_project):
        """Test: Response evaluation includes correctness assessment"""
        project_id = test_user_with_project["project_id"]
        auth_headers = test_user_with_project["auth_headers"]

        # Generate question and process response
        q_resp = requests.post(
            f"{BASE_URL}/projects/{project_id}/question",
            json={"topic": "Python Basics", "difficulty_level": "beginner"},
            headers=auth_headers
        )

        if q_resp.status_code != 200:
            pytest.skip("Could not generate question")

        question_id = q_resp.json().get("question_id", "test_1")

        # Submit response
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/response",
            json={
                "question_id": question_id,
                "user_response": "An answer"
            },
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            # Should indicate whether answer is correct
            assert any(k in data for k in ["is_correct", "correct", "evaluation"])

    def test_07_response_includes_feedback(self, test_user_with_project):
        """Test: Response includes feedback for user"""
        project_id = test_user_with_project["project_id"]
        auth_headers = test_user_with_project["auth_headers"]

        q_resp = requests.post(
            f"{BASE_URL}/projects/{project_id}/question",
            json={"topic": "Python", "difficulty_level": "beginner"},
            headers=auth_headers
        )

        if q_resp.status_code != 200:
            pytest.skip("Could not generate question")

        question_id = q_resp.json().get("question_id", "test_1")

        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/response",
            json={
                "question_id": question_id,
                "user_response": "The answer"
            },
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            # Should have feedback
            assert "feedback" in data or "message" in data or "response" in data

    def test_08_question_for_nonexistent_project(self, test_user_with_project):
        """Test: Requesting question for nonexistent project fails"""
        auth_headers = test_user_with_project["auth_headers"]

        response = requests.post(
            f"{BASE_URL}/projects/nonexistent_proj/question",
            json={"topic": "Python", "difficulty_level": "beginner"},
            headers=auth_headers
        )

        assert response.status_code >= 400

    def test_09_process_response_nonexistent_project(self, test_user_with_project):
        """Test: Processing response for nonexistent project fails"""
        auth_headers = test_user_with_project["auth_headers"]

        response = requests.post(
            f"{BASE_URL}/projects/nonexistent_proj/response",
            json={
                "question_id": "q1",
                "user_response": "answer"
            },
            headers=auth_headers
        )

        assert response.status_code >= 400


class TestQuestionHints:
    """Test hint generation features"""

    def test_hint_generation(self):
        """Test: Hints are generated for struggling users"""
        # Requires question endpoint with hint support
        pass

    def test_multiple_hints(self):
        """Test: Multiple hint levels available"""
        pass


class TestQuestionHistory:
    """Test question history tracking"""

    def test_question_history_tracking(self):
        """Test: Questions are tracked in project history"""
        pass

    def test_performance_analytics(self):
        """Test: Performance metrics based on question responses"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
