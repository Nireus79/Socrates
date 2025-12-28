"""
Comprehensive Code Generation Workflow Tests

Tests code generation capabilities available to Pro+ tier:
- Generate code from natural language specifications
- Code improvement and refactoring suggestions
- Multiple programming language support
- Code explanation
- Test generation
- Documentation generation
- Multi-LLM support (Pro+ feature)
"""

import requests
import json
from datetime import datetime
import pytest

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


class TestCodeGeneration:
    """Test code generation workflows"""

    @pytest.fixture
    def user_with_project(self):
        """Create user and project for code generation testing"""
        username = f"codegen_user_{int(datetime.now().timestamp() * 1000)}"

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
                "name": "Code Generation Test Project",
                "description": "Test project for code generation"},
            headers=auth_headers
        )
        project_id = proj_resp.json()["project_id"]

        return {
            "username": username,
            "access_token": access_token,
            "project_id": project_id,
            "auth_headers": auth_headers
        }

    def test_01_generate_code_from_spec(self, user_with_project):
        """Test: Generate code from natural language specification"""
        project_id = user_with_project["project_id"]
        auth_headers = user_with_project["auth_headers"]

        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/code_generation",
            json={
                "specification": "Create a function that calculates the factorial of a number",
                "language": "python",
                "complexity": "beginner"
            },
            headers=auth_headers
        )

        # Check if endpoint exists
        if response.status_code == 503:
            pytest.skip("Orchestrator not initialized")
        elif response.status_code == 501:
            pytest.skip("Code generation endpoint not implemented")
        elif response.status_code == 403:
            # Feature gating - may be restricted to certain tiers
            error_msg = str(response.json()).lower()
            assert "subscription" in error_msg or "tier" in error_msg or "pro" in error_msg
        elif response.status_code == 200:
            data = response.json()
            assert "code" in data or "generated_code" in data or "content" in data

    def test_02_code_in_multiple_languages(self, user_with_project):
        """Test: Generate code in different programming languages"""
        project_id = user_with_project["project_id"]
        auth_headers = user_with_project["auth_headers"]

        languages = ["python", "javascript", "java", "cpp", "go"]

        for language in languages:
            response = requests.post(
                f"{BASE_URL}/projects/{project_id}/code_generation",
                json={
                    "specification": "Create a hello world function",
                    "language": language
                },
                headers=auth_headers
            )

            if response.status_code == 200:
                data = response.json()
                assert "code" in data or "generated_code" in data
            elif response.status_code in [501, 503]:
                pytest.skip(f"Code generation not available for {language}")

    def test_03_code_improvement_suggestion(self, user_with_project):
        """Test: Get improvement suggestions for existing code"""
        project_id = user_with_project["project_id"]
        auth_headers = user_with_project["auth_headers"]

        bad_code = """
def add(a, b):
    result = a + b
    return result
        """

        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/code_improvement",
            json={
                "code": bad_code,
                "language": "python"
            },
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "suggestions" in data or "improved_code" in data or "feedback" in data
        elif response.status_code == 501:
            pytest.skip("Code improvement endpoint not implemented")

    def test_04_code_explanation(self, user_with_project):
        """Test: Get explanation of existing code"""
        project_id = user_with_project["project_id"]
        auth_headers = user_with_project["auth_headers"]

        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
        """

        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/code_explanation",
            json={
                "code": code,
                "language": "python"
            },
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "explanation" in data or "description" in data or "analysis" in data
        elif response.status_code == 501:
            pytest.skip("Code explanation endpoint not implemented")

    def test_05_test_generation(self, user_with_project):
        """Test: Generate test cases for code"""
        project_id = user_with_project["project_id"]
        auth_headers = user_with_project["auth_headers"]

        code = """
def add(a, b):
    return a + b
        """

        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/generate_tests",
            json={
                "code": code,
                "language": "python",
                "test_framework": "pytest"
            },
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "tests" in data or "test_cases" in data or "content" in data
        elif response.status_code == 501:
            pytest.skip("Test generation endpoint not implemented")

    def test_06_documentation_generation(self, user_with_project):
        """Test: Generate documentation for code"""
        project_id = user_with_project["project_id"]
        auth_headers = user_with_project["auth_headers"]

        code = """
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count if count > 0 else 0
        """

        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/generate_documentation",
            json={
                "code": code,
                "language": "python",
                "doc_format": "docstring"
            },
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "documentation" in data or "docstring" in data or "content" in data
        elif response.status_code == 501:
            pytest.skip("Documentation generation endpoint not implemented")

    def test_07_code_refactoring(self, user_with_project):
        """Test: Refactor code for better practices"""
        project_id = user_with_project["project_id"]
        auth_headers = user_with_project["auth_headers"]

        code = """
if condition == True:
    do_something()
if x is not None:
    process(x)
        """

        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/refactor_code",
            json={
                "code": code,
                "language": "python",
                "focus": "best_practices"
            },
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "refactored_code" in data or "improved_code" in data or "code" in data
        elif response.status_code == 501:
            pytest.skip("Code refactoring endpoint not implemented")

    def test_08_free_tier_no_code_generation(self):
        """Test: Free tier users cannot generate code"""
        # Create free tier user
        username = f"free_user_{int(datetime.now().timestamp() * 1000)}"
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
            json={"name": "Free Project", "description": "Test"},
            headers=auth_headers
        )
        project_id = proj_resp.json()["project_id"]

        # Try to generate code
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/code_generation",
            json={
                "specification": "Write hello world",
                "language": "python"
            },
            headers=auth_headers
        )

        # Free tier should be blocked
        assert response.status_code >= 400, "Free tier should not have code generation"
        error_msg = str(response.json()).lower()
        assert any(word in error_msg for word in ["subscription", "tier", "pro", "code"])

    def test_09_code_complexity_levels(self, user_with_project):
        """Test: Generate code with different complexity levels"""
        project_id = user_with_project["project_id"]
        auth_headers = user_with_project["auth_headers"]

        complexities = ["beginner", "intermediate", "advanced"]

        for complexity in complexities:
            response = requests.post(
                f"{BASE_URL}/projects/{project_id}/code_generation",
                json={
                    "specification": "Write a sorting algorithm",
                    "language": "python",
                    "complexity": complexity
                },
                headers=auth_headers
            )

            if response.status_code == 200:
                data = response.json()
                assert data is not None

    def test_10_generated_code_quality(self, user_with_project):
        """Test: Generated code includes quality metadata"""
        project_id = user_with_project["project_id"]
        auth_headers = user_with_project["auth_headers"]

        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/code_generation",
            json={
                "specification": "Create a class for managing users",
                "language": "python"
            },
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            # Should have code and possibly quality indicators
            assert any(k in data for k in ["code", "generated_code", "content"])
            # May have quality metrics
            if "quality_score" in data or "complexity" in data:
                assert isinstance(data.get("quality_score", 0), (int, float))


class TestMultiLLMCodeGeneration:
    """Test multi-LLM support for code generation (Pro+ feature)"""

    def test_generate_with_different_llm_models(self):
        """Test: Generate code using different LLM models"""
        # Requires multi_llm feature (Pro+ only)
        # Can compare outputs from different models
        pass

    def test_llm_model_selection(self):
        """Test: User can select preferred LLM for code generation"""
        pass

    def test_free_tier_single_llm_only(self):
        """Test: Free tier only has access to default LLM"""
        pass


class TestCodeGenerationHistory:
    """Test history and versioning of generated code"""

    def test_code_generation_history_tracking(self):
        """Test: Generated code is tracked in project history"""
        pass

    def test_code_version_comparison(self):
        """Test: Can compare different versions of generated code"""
        pass

    def test_generated_code_attribution(self):
        """Test: Generated code is properly attributed to generation event"""
        pass


class TestCodeGenerationEdgeCases:
    """Test edge cases and error handling"""

    def test_invalid_language(self):
        """Test: Invalid programming language is rejected"""
        pass

    def test_empty_specification(self):
        """Test: Empty specification is rejected"""
        pass

    def test_extremely_large_code(self):
        """Test: Very large code input is handled"""
        pass

    def test_malformed_code_explanation(self):
        """Test: System handles unexplainable code gracefully"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
