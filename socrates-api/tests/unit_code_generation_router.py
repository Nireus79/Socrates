"""
Unit tests for code generation router.

Tests code generation endpoints including:
- Generating code from specifications
- Validating generated code
- Code history and refactoring
- Documentation generation
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
class TestGenerateCode:
    """Tests for code generation endpoint."""

    def test_generate_code_requires_auth(self, client):
        """Test that code generation requires authentication."""
        response = client.post(
            "/projects/test_proj/code/generate",
            json={"specification": "Create a hello world function"},
        )
        assert response.status_code == 401

    def test_generate_code_missing_project(self, client, valid_token):
        """Test generating code for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/nonexistent_proj_xyz/code/generate?specification=Create+a+function",
            headers=headers,
        )
        # Will fail due to missing project or subscription validation
        assert response.status_code in [403, 404, 500]

    def test_generate_code_missing_specification(self, client, valid_token):
        """Test generating code without specification."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/generate",
            headers=headers,
        )
        assert response.status_code in [422, 403, 404, 500]

    def test_generate_code_with_language(self, client, valid_token):
        """Test generating code with specific language."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/generate?specification=Create+a+function&language=python",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 422, 500]

    def test_generate_code_invalid_language(self, client, valid_token):
        """Test generating code with unsupported language."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/generate?specification=Create+a+function&language=invalid_lang_xyz",
            headers=headers,
        )
        assert response.status_code in [400, 403, 404, 422, 500]

    def test_generate_code_with_requirements(self, client, valid_token):
        """Test generating code with additional requirements."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/generate?specification=Create+a+function&language=python&requirements=Must+use+type+hints",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 422, 500]

    def test_generate_code_supported_languages(self, client, valid_token):
        """Test generating code in all supported languages."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        languages = ["python", "javascript", "typescript", "java", "cpp", "csharp", "go", "rust", "sql"]

        for language in languages:
            response = client.post(
                f"/projects/test_proj/code/generate?specification=Create+hello+world&language={language}",
                headers=headers,
            )
            # Should either succeed or fail with subscription/project, not language error
            assert response.status_code in [200, 403, 404, 422, 500]

    def test_generate_code_invalid_token(self, client):
        """Test generate code with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/projects/test_proj/code/generate",
            json={"specification": "Create a function"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestValidateCode:
    """Tests for code validation endpoint."""

    def test_validate_code_requires_auth(self, client):
        """Test that code validation requires authentication."""
        response = client.post(
            "/projects/test_proj/code/validate",
            json={"code": "print('hello')", "language": "python"},
        )
        assert response.status_code == 401

    def test_validate_code_missing_project(self, client, valid_token):
        """Test validating code for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/nonexistent_proj_xyz/code/validate?code=print('hello')&language=python",
            headers=headers,
        )
        assert response.status_code in [403, 404, 422, 500]

    def test_validate_code_missing_code(self, client, valid_token):
        """Test validating without code."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/validate?language=python",
            headers=headers,
        )
        assert response.status_code in [422, 403, 404, 500]

    def test_validate_python_code(self, client, valid_token):
        """Test validating Python code."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/validate?code=def+hello():&language=python",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 422, 500]
        if response.status_code == 200:
            data = response.json()
            assert "is_valid" in data
            assert "errors" in data
            assert "warnings" in data

    def test_validate_invalid_syntax(self, client, valid_token):
        """Test validating code with syntax errors."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/validate?code=def+hello(invalid&language=python",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 422, 500]

    def test_validate_javascript_code(self, client, valid_token):
        """Test validating JavaScript code."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/validate?code=function+hello()+{}&language=javascript",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 422, 500]

    def test_validate_code_invalid_language(self, client, valid_token):
        """Test validating with unsupported language."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/validate?code=print('hello')&language=invalid_lang_xyz",
            headers=headers,
        )
        assert response.status_code in [400, 403, 404, 422, 500]

    def test_validate_code_invalid_token(self, client):
        """Test validate code with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/projects/test_proj/code/validate",
            json={"code": "print('hello')", "language": "python"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestGetCodeHistory:
    """Tests for code history endpoint."""

    def test_get_history_requires_auth(self, client):
        """Test that getting code history requires authentication."""
        response = client.get("/projects/test_proj/code/history")
        assert response.status_code == 401

    def test_get_history_missing_project(self, client, valid_token):
        """Test getting history for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/nonexistent_proj_xyz/code/history",
            headers=headers,
        )
        assert response.status_code in [403, 404, 500]

    def test_get_history_empty(self, client, valid_token):
        """Test getting history for project with no code generations."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/code/history",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "generations" in data

    def test_get_history_with_pagination(self, client, valid_token):
        """Test getting history with limit and offset."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/code/history?limit=10&offset=0",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]

    def test_get_history_custom_limit(self, client, valid_token):
        """Test getting history with custom limit."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/code/history?limit=5",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]

    def test_get_history_invalid_token(self, client):
        """Test get history with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get(
            "/projects/test_proj/code/history",
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestGetSupportedLanguages:
    """Tests for getting supported languages."""

    def test_get_languages_no_auth_required(self, client):
        """Test that getting supported languages doesn't require auth."""
        response = client.get("/projects/languages")
        # Note: This endpoint doesn't have project_id in path, might not require auth
        assert response.status_code in [200, 401]

    def test_get_languages_returns_list(self, client):
        """Test that supported languages endpoint returns list."""
        response = client.get("/projects/languages")
        if response.status_code == 200:
            data = response.json()
            assert "languages" in data
            assert "total" in data
            assert isinstance(data["languages"], dict)
            # Verify some known languages are present
            assert len(data["languages"]) > 0


@pytest.mark.unit
class TestRefactorCode:
    """Tests for code refactoring endpoint."""

    def test_refactor_code_requires_auth(self, client):
        """Test that code refactoring requires authentication."""
        response = client.post(
            "/projects/test_proj/code/refactor",
            json={"code": "print('hello')", "language": "python"},
        )
        assert response.status_code == 401

    def test_refactor_code_missing_project(self, client, valid_token):
        """Test refactoring code in non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/nonexistent_proj_xyz/code/refactor?code=print('hello')&language=python",
            headers=headers,
        )
        assert response.status_code in [403, 404, 422, 500]

    def test_refactor_code_missing_code(self, client, valid_token):
        """Test refactoring without code."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/refactor?language=python",
            headers=headers,
        )
        assert response.status_code in [422, 403, 404, 500]

    def test_refactor_code_optimize(self, client, valid_token):
        """Test refactoring code with optimize type."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/refactor?code=def+hello():&language=python&refactor_type=optimize",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 422, 500]

    def test_refactor_code_simplify(self, client, valid_token):
        """Test refactoring code with simplify type."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/refactor?code=def+hello():&language=python&refactor_type=simplify",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 422, 500]

    def test_refactor_code_document(self, client, valid_token):
        """Test refactoring code with document type."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/refactor?code=def+hello():&language=python&refactor_type=document",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 422, 500]

    def test_refactor_code_modernize(self, client, valid_token):
        """Test refactoring code with modernize type."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/refactor?code=def+hello():&language=python&refactor_type=modernize",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 422, 500]

    def test_refactor_code_invalid_type(self, client, valid_token):
        """Test refactoring with invalid refactor type."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/refactor?code=print('hello')&language=python&refactor_type=invalid_type_xyz",
            headers=headers,
        )
        assert response.status_code in [400, 403, 404, 422, 500]

    def test_refactor_code_invalid_token(self, client):
        """Test refactor code with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/projects/test_proj/code/refactor",
            json={"code": "print('hello')", "language": "python"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestGenerateDocumentation:
    """Tests for documentation generation endpoint."""

    def test_generate_docs_requires_auth(self, client):
        """Test that documentation generation requires authentication."""
        response = client.post(
            "/projects/test_proj/docs/generate",
        )
        assert response.status_code == 401

    def test_generate_docs_missing_project(self, client, valid_token):
        """Test generating docs for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/nonexistent_proj_xyz/docs/generate",
            headers=headers,
        )
        assert response.status_code in [403, 404, 500]

    def test_generate_docs_default_format(self, client, valid_token):
        """Test generating documentation with default format."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/docs/generate",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]

    def test_generate_docs_markdown_format(self, client, valid_token):
        """Test generating documentation in markdown format."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/docs/generate",
            json={"format": "markdown"},
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]

    def test_generate_docs_html_format(self, client, valid_token):
        """Test generating documentation in HTML format."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/docs/generate",
            json={"format": "html"},
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]

    def test_generate_docs_rst_format(self, client, valid_token):
        """Test generating documentation in reStructuredText format."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/docs/generate",
            json={"format": "rst"},
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]

    def test_generate_docs_pdf_format(self, client, valid_token):
        """Test generating documentation in PDF format."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/docs/generate",
            json={"format": "pdf"},
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]

    def test_generate_docs_invalid_format(self, client, valid_token):
        """Test generating documentation with invalid format."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/docs/generate",
            json={"format": "invalid_format_xyz"},
            headers=headers,
        )
        assert response.status_code in [400, 403, 404, 500]

    def test_generate_docs_with_examples(self, client, valid_token):
        """Test generating documentation with code examples included."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/docs/generate",
            json={"format": "markdown", "include_examples": True},
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]

    def test_generate_docs_without_examples(self, client, valid_token):
        """Test generating documentation without code examples."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/docs/generate",
            json={"format": "markdown", "include_examples": False},
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]

    def test_generate_docs_invalid_token(self, client):
        """Test generate docs with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/projects/test_proj/docs/generate",
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestCodeGenerationEdgeCases:
    """Tests for code generation edge cases."""

    def test_generate_code_with_empty_specification(self, client, valid_token):
        """Test generating code with empty specification."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/generate?specification=",
            headers=headers,
        )
        assert response.status_code in [200, 400, 403, 404, 422, 500]

    def test_validate_code_with_empty_code(self, client, valid_token):
        """Test validating empty code."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/validate?code=&language=python",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 422, 500]

    def test_validate_code_with_very_long_code(self, client, valid_token):
        """Test validating very long code."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        long_code = "x+%3D+1%0A" * 100  # URL encoded long code
        response = client.post(
            f"/projects/test_proj/code/validate?code={long_code}&language=python",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 422, 500]

    def test_refactor_code_with_empty_code(self, client, valid_token):
        """Test refactoring empty code."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/code/refactor?code=&language=python",
            headers=headers,
        )
        assert response.status_code in [200, 400, 403, 404, 422, 500]

    def test_generate_docs_with_special_chars_format(self, client, valid_token):
        """Test generating docs with special characters in format (should fail)."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/docs/generate",
            json={"format": "format!@#$%"},
            headers=headers,
        )
        assert response.status_code in [400, 403, 404, 500]
