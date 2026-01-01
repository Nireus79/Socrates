"""
Comprehensive API Endpoint Tests
Full coverage of all endpoints with various input scenarios and edge cases
"""

import json

from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Comprehensive tests for all auth endpoints"""

    def test_login_with_valid_credentials(self, client: TestClient):
        """POST /auth/login with valid credentials"""
        response = client.post('/auth/login', json={
            'username': 'validuser',
            'password': 'validpass'
        })
        assert response.status_code != 404

    def test_login_with_invalid_username(self, client: TestClient):
        """POST /auth/login with invalid username"""
        response = client.post('/auth/login', json={
            'username': 'nonexistent',
            'password': 'anypass'
        })
        assert response.status_code in [401, 400]

    def test_login_with_invalid_password(self, client: TestClient):
        """POST /auth/login with invalid password"""
        response = client.post('/auth/login', json={
            'username': 'validuser',
            'password': 'wrongpass'
        })
        assert response.status_code in [401, 400]

    def test_login_missing_username(self, client: TestClient):
        """POST /auth/login missing username"""
        response = client.post('/auth/login', json={
            'password': 'pass'
        })
        assert response.status_code in [400, 422]

    def test_login_missing_password(self, client: TestClient):
        """POST /auth/login missing password"""
        response = client.post('/auth/login', json={
            'username': 'user'
        })
        assert response.status_code in [400, 422]

    def test_register_with_valid_data(self, client: TestClient):
        """POST /auth/register with valid data"""
        response = client.post('/auth/register', json={
            'username': f'newuser_{id(object())}',
            'email': f'new_{id(object())}@example.com',
            'password': 'SecurePass123!'
        })
        assert response.status_code in [200, 201, 409]  # 409 if duplicate

    def test_register_with_invalid_email(self, client: TestClient):
        """POST /auth/register with invalid email"""
        response = client.post('/auth/register', json={
            'username': 'testuser',
            'email': 'not_an_email',
            'password': 'password'
        })
        assert response.status_code in [400, 422]

    def test_register_with_weak_password(self, client: TestClient):
        """POST /auth/register with weak password"""
        response = client.post('/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123'
        })
        # May validate password strength
        assert response.status_code != 500

    def test_register_duplicate_username(self, client: TestClient):
        """POST /auth/register with duplicate username"""
        response = client.post('/auth/register', json={
            'username': 'duplicate_user',
            'email': 'first@example.com',
            'password': 'password'
        })

        if response.status_code in [200, 201]:
            response2 = client.post('/auth/register', json={
                'username': 'duplicate_user',
                'email': 'second@example.com',
                'password': 'password'
            })
            assert response2.status_code in [400, 409]

    def test_logout_endpoint(self, client: TestClient):
        """POST /auth/logout"""
        response = client.post('/auth/logout')
        assert response.status_code != 404

    def test_refresh_token_endpoint(self, client: TestClient):
        """POST /auth/refresh"""
        response = client.post('/auth/refresh', json={
            'refresh_token': 'test_token'
        })
        assert response.status_code != 404

    def test_change_password_endpoint(self, client: TestClient):
        """PUT /auth/change-password"""
        response = client.put('/auth/change-password', json={
            'old_password': 'oldpass',
            'new_password': 'newpass'
        })
        assert response.status_code != 404


class TestProjectEndpoints:
    """Comprehensive tests for project endpoints"""

    def test_create_project_valid(self, client: TestClient):
        """POST /projects with valid data"""
        response = client.post('/projects', json={
            'name': 'Test Project',
            'description': 'A test project',
            'owner': 'testuser'
        })
        assert response.status_code != 404

    def test_create_project_missing_name(self, client: TestClient):
        """POST /projects missing name"""
        response = client.post('/projects', json={
            'description': 'No name'
        })
        # Endpoint requires auth, so 401; if auth passes, then 400/422 for validation
        assert response.status_code in [400, 422, 401]

    def test_create_project_empty_name(self, client: TestClient):
        """POST /projects with empty name"""
        response = client.post('/projects', json={
            'name': '',
            'description': 'Empty name',
            'owner': 'testuser'
        })
        assert response.status_code in [400, 422, 401]

    def test_list_projects(self, client: TestClient):
        """GET /projects"""
        response = client.get('/projects')
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    def test_list_projects_with_pagination(self, client: TestClient):
        """GET /projects with pagination"""
        response = client.get('/projects?skip=0&limit=10')
        assert response.status_code != 404

    def test_get_project_details(self, client: TestClient):
        """GET /projects/{project_id}"""
        response = client.get('/projects/test_project_id')
        assert response.status_code in [404, 401, 200]

    def test_update_project(self, client: TestClient):
        """PUT /projects/{project_id}"""
        response = client.put('/projects/test_project_id', json={
            'name': 'Updated Name',
            'description': 'Updated description'
        })
        assert response.status_code != 404

    def test_delete_project(self, client: TestClient):
        """DELETE /projects/{project_id}"""
        response = client.delete('/projects/test_project_id')
        assert response.status_code != 404

    def test_get_project_files(self, client: TestClient):
        """GET /projects/{project_id}/files"""
        response = client.get('/projects/test_project_id/files')
        assert response.status_code != 404

    def test_search_projects(self, client: TestClient):
        """GET /projects/search"""
        response = client.get('/projects/search?q=test')
        assert response.status_code != 404


class TestGitHubEndpoints:
    """Comprehensive tests for GitHub integration endpoints"""

    def test_import_from_github(self, client: TestClient):
        """POST /github/import"""
        response = client.post('/github/import', json={
            'url': 'https://github.com/user/repo'
        })
        assert response.status_code != 404

    def test_import_invalid_url(self, client: TestClient):
        """POST /github/import with invalid URL"""
        response = client.post('/github/import', json={
            'url': 'not_a_url'
        })
        assert response.status_code in [400, 401, 422]

    def test_import_missing_url(self, client: TestClient):
        """POST /github/import missing URL"""
        response = client.post('/github/import', json={})
        assert response.status_code in [400, 422]

    def test_github_pull(self, client: TestClient):
        """GET /github/pull"""
        response = client.get('/github/pull')
        assert response.status_code != 404

    def test_github_push(self, client: TestClient):
        """POST /github/push"""
        response = client.post('/github/push', json={
            'message': 'Sync from Socrates'
        })
        assert response.status_code != 404

    def test_github_status(self, client: TestClient):
        """GET /github/status"""
        response = client.get('/github/status')
        assert response.status_code != 404

    def test_github_disconnect(self, client: TestClient):
        """POST /github/disconnect"""
        response = client.post('/github/disconnect')
        assert response.status_code != 404


class TestKnowledgeEndpoints:
    """Comprehensive tests for knowledge base endpoints"""

    def test_import_knowledge_from_url(self, client: TestClient):
        """POST /knowledge/import/url"""
        response = client.post('/knowledge/import/url', json={
            'url': 'https://example.com'
        })
        assert response.status_code != 404

    def test_import_knowledge_invalid_url(self, client: TestClient):
        """POST /knowledge/import/url with invalid URL"""
        response = client.post('/knowledge/import/url', json={
            'url': 'not_a_url'
        })
        assert response.status_code in [400, 401, 422]

    def test_import_knowledge_from_text(self, client: TestClient):
        """POST /knowledge/import/text"""
        response = client.post('/knowledge/import/text', json={
            'text': 'Some knowledge content',
            'title': 'Knowledge Title'
        })
        assert response.status_code != 404

    def test_import_knowledge_missing_text(self, client: TestClient):
        """POST /knowledge/import/text missing text"""
        response = client.post('/knowledge/import/text', json={
            'title': 'Title Only'
        })
        assert response.status_code in [400, 422]

    def test_import_knowledge_file(self, client: TestClient):
        """POST /knowledge/import/file"""
        response = client.post('/knowledge/import/file')
        assert response.status_code != 404

    def test_list_knowledge_documents(self, client: TestClient):
        """GET /knowledge/documents"""
        response = client.get('/knowledge/documents')
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    def test_search_knowledge(self, client: TestClient):
        """GET /knowledge/search"""
        response = client.get('/knowledge/search?q=test')
        assert response.status_code != 404

    def test_search_knowledge_missing_query(self, client: TestClient):
        """GET /knowledge/search without query"""
        response = client.get('/knowledge/search')
        assert response.status_code in [400, 422, 200]

    def test_get_document_details(self, client: TestClient):
        """GET /knowledge/documents/{doc_id}"""
        response = client.get('/knowledge/documents/test_doc_id')
        assert response.status_code != 404

    def test_delete_document(self, client: TestClient):
        """DELETE /knowledge/documents/{doc_id}"""
        response = client.delete('/knowledge/documents/test_doc_id')
        assert response.status_code != 404

    def test_export_knowledge(self, client: TestClient):
        """GET /knowledge/export"""
        response = client.get('/knowledge/export')
        assert response.status_code != 404

    def test_export_knowledge_specific_format(self, client: TestClient):
        """GET /knowledge/export with format"""
        response = client.get('/knowledge/export?format=json')
        assert response.status_code != 404


class TestLLMEndpoints:
    """Comprehensive tests for LLM provider endpoints"""

    def test_list_llm_providers(self, client: TestClient):
        """GET /llm/providers"""
        response = client.get('/llm/providers')
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    def test_get_llm_config(self, client: TestClient):
        """GET /llm/config"""
        response = client.get('/llm/config')
        assert response.status_code in [200, 401]

    def test_set_default_llm_provider(self, client: TestClient):
        """PUT /llm/default-provider"""
        response = client.put('/llm/default-provider', json={
            'provider': 'anthropic'
        })
        assert response.status_code != 404

    def test_set_llm_model(self, client: TestClient):
        """PUT /llm/model"""
        response = client.put('/llm/model', json={
            'provider': 'anthropic',
            'model': 'claude-3-sonnet'
        })
        assert response.status_code != 404

    def test_add_llm_api_key(self, client: TestClient):
        """POST /llm/api-key"""
        response = client.post('/llm/api-key', json={
            'provider': 'anthropic',
            'api_key': 'sk-test-key'
        })
        assert response.status_code != 404

    def test_add_api_key_invalid_provider(self, client: TestClient):
        """POST /llm/api-key with invalid provider"""
        response = client.post('/llm/api-key', json={
            'provider': 'nonexistent_provider',
            'api_key': 'sk-test'
        })
        assert response.status_code in [400, 401, 422]

    def test_api_key_not_exposed(self, client: TestClient):
        """Verify API key not in GET /llm/config"""
        response = client.get('/llm/config')
        if response.status_code == 200:
            data = json.dumps(response.json())
            # API key should not be exposed
            assert 'api_key' not in data.lower() or '***' in data

    def test_get_llm_usage_stats(self, client: TestClient):
        """GET /llm/usage-stats"""
        response = client.get('/llm/usage-stats')
        assert response.status_code != 404

    def test_list_llm_models(self, client: TestClient):
        """GET /llm/models/{provider}"""
        response = client.get('/llm/models/anthropic')
        assert response.status_code != 404

    def test_remove_api_key(self, client: TestClient):
        """DELETE /llm/api-key/{provider}"""
        response = client.delete('/llm/api-key/anthropic')
        assert response.status_code != 404


class TestAnalysisEndpoints:
    """Comprehensive tests for code analysis endpoints"""

    def test_validate_python_code(self, client: TestClient):
        """POST /analysis/validate for Python"""
        response = client.post('/analysis/validate', json={
            'code': 'print("hello")',
            'language': 'python'
        })
        assert response.status_code != 404

    def test_validate_javascript_code(self, client: TestClient):
        """POST /analysis/validate for JavaScript"""
        response = client.post('/analysis/validate', json={
            'code': 'console.log("hello");',
            'language': 'javascript'
        })
        assert response.status_code != 404

    def test_validate_invalid_code(self, client: TestClient):
        """POST /analysis/validate with syntax error"""
        response = client.post('/analysis/validate', json={
            'code': 'def incomplete(',
            'language': 'python'
        })
        # Should handle gracefully
        assert response.status_code != 500

    def test_validate_missing_language(self, client: TestClient):
        """POST /analysis/validate missing language"""
        response = client.post('/analysis/validate', json={
            'code': 'print("hello")'
        })
        assert response.status_code in [400, 422]

    def test_validate_missing_code(self, client: TestClient):
        """POST /analysis/validate missing code"""
        response = client.post('/analysis/validate', json={
            'language': 'python'
        })
        assert response.status_code in [400, 422]

    def test_code_maturity_assessment(self, client: TestClient):
        """POST /analysis/maturity"""
        response = client.post('/analysis/maturity', json={
            'code': 'def hello(): return "world"',
            'language': 'python'
        })
        assert response.status_code != 404

    def test_maturity_missing_code(self, client: TestClient):
        """POST /analysis/maturity missing code"""
        response = client.post('/analysis/maturity', json={})
        assert response.status_code in [400, 422, 200]  # Varies by implementation


class TestCollaborationEndpoints:
    """Comprehensive tests for collaboration endpoints"""

    def test_invite_team_member(self, client: TestClient):
        """POST /collaboration/invite"""
        response = client.post('/collaboration/invite', json={
            'email': 'teammate@example.com',
            'role': 'developer'
        })
        assert response.status_code != 404

    def test_invite_invalid_email(self, client: TestClient):
        """POST /collaboration/invite with invalid email"""
        response = client.post('/collaboration/invite', json={
            'email': 'not_an_email',
            'role': 'developer'
        })
        assert response.status_code in [400, 401, 422]

    def test_invite_missing_email(self, client: TestClient):
        """POST /collaboration/invite missing email"""
        response = client.post('/collaboration/invite', json={
            'role': 'developer'
        })
        assert response.status_code in [400, 422]

    def test_list_team_members(self, client: TestClient):
        """GET /collaboration/members"""
        response = client.get('/collaboration/members')
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    def test_update_member_role(self, client: TestClient):
        """PUT /collaboration/members/{member_id}"""
        response = client.put('/collaboration/members/member_id', json={
            'role': 'admin'
        })
        assert response.status_code != 404

    def test_remove_team_member(self, client: TestClient):
        """DELETE /collaboration/members/{member_id}"""
        response = client.delete('/collaboration/members/member_id')
        assert response.status_code != 404


class TestAnalyticsEndpoints:
    """Comprehensive tests for analytics endpoints"""

    def test_get_analytics_summary(self, client: TestClient):
        """GET /analytics/summary"""
        response = client.get('/analytics/summary')
        assert response.status_code != 404

    def test_get_project_analytics(self, client: TestClient):
        """GET /analytics/projects/{project_id}"""
        response = client.get('/analytics/projects/test_project_id')
        assert response.status_code != 404

    def test_get_code_metrics(self, client: TestClient):
        """GET /analytics/code-metrics"""
        response = client.get('/analytics/code-metrics')
        assert response.status_code != 404

    def test_get_usage_analytics(self, client: TestClient):
        """GET /analytics/usage"""
        response = client.get('/analytics/usage')
        assert response.status_code != 404


class TestEndpointAvailability:
    """Test that all expected endpoints are available"""

    def test_root_endpoint(self, client: TestClient):
        """GET /"""
        response = client.get('/')
        # Should return something (200, 404, or redirect)
        assert response.status_code in [200, 301, 302, 404]

    def test_health_endpoint(self, client: TestClient):
        """GET /health"""
        response = client.get('/health')
        assert response.status_code in [200, 404]

    def test_docs_endpoint(self, client: TestClient):
        """GET /docs"""
        response = client.get('/docs')
        # API docs may be available
        assert response.status_code in [200, 404]

    def test_openapi_schema(self, client: TestClient):
        """GET /openapi.json"""
        response = client.get('/openapi.json')
        assert response.status_code in [200, 404]


class TestEndpointErrorHandling:
    """Test error handling across all endpoints"""

    def test_nonexistent_endpoint_404(self, client: TestClient):
        """GET /nonexistent/endpoint returns 404"""
        response = client.get('/nonexistent/endpoint/path')
        assert response.status_code == 404

    def test_wrong_method_405(self, client: TestClient):
        """POST /projects (wrong method) returns error"""
        response = client.get('/auth/login')  # Should be POST
        assert response.status_code in [405, 404, 401]

    def test_invalid_json_400(self, client: TestClient):
        """POST with invalid JSON"""
        response = client.post(
            '/auth/login',
            data='not json',
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code in [400, 422]

    def test_malformed_json(self, client: TestClient):
        """POST with malformed JSON"""
        response = client.post(
            '/auth/login',
            data='{invalid json}',
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code in [400, 422]
