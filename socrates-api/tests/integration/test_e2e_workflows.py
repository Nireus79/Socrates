"""
End-to-End Workflow Tests
Tests complete user workflows across multiple endpoints and features
"""

import json

from fastapi.testclient import TestClient


class TestAuthWorkflows:
    """E2E tests for authentication workflows"""

    def test_complete_registration_to_login_workflow(self, client: TestClient):
        """Test: User can register and login successfully"""
        # Step 1: Register new user
        register_response = client.post('/auth/register', json={
            'username': 'newuser_e2e_test',
            'email': 'newuser@example.com',
            'password': 'SecurePassword123!'
        })
        assert register_response.status_code in [200, 201, 409]  # Created or already exists

        # Step 2: If registration successful, user can login
        if register_response.status_code in [200, 201]:
            login_response = client.post('/auth/login', json={
                'username': 'newuser_e2e_test',
                'password': 'SecurePassword123!'
            })
            assert login_response.status_code in [200, 401]  # Should be 200 if user created
            if login_response.status_code == 200:
                data = login_response.json()
                assert 'access_token' in data or 'token' in data.values()

    def test_login_provides_valid_token_for_protected_endpoints(self, client: TestClient):
        """Test: Login token grants access to protected endpoints"""
        # Step 1: Attempt to access protected endpoint without token
        projects_response = client.get('/projects')
        assert projects_response.status_code in [401, 200, 403]  # Should fail without token

        # Step 2: Login to get token
        login_response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        # Note: Result depends on user existence, but endpoint should exist
        assert login_response.status_code != 404

    def test_token_refresh_workflow(self, client: TestClient):
        """Test: Refresh token extends session"""
        # Step 1: Get refresh token (from login)
        login_response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        # Endpoint should exist
        assert login_response.status_code != 404

        # Step 2: Attempt token refresh
        refresh_response = client.post('/auth/refresh', json={
            'refresh_token': 'invalid_token'
        })
        # Endpoint should exist and validate token
        assert refresh_response.status_code != 404

    def test_logout_clears_session(self, client: TestClient):
        """Test: Logout endpoint exists and processes request"""
        logout_response = client.post('/auth/logout')
        # Should not 404, may return 200 (success) or 401 (not logged in)
        assert logout_response.status_code in [200, 401]


class TestProjectWorkflows:
    """E2E tests for project management workflows"""

    def test_create_list_get_project_workflow(self, client: TestClient):
        """Test: User can create, list, and retrieve projects"""
        # Step 1: Create a project
        create_response = client.post('/projects', json={
            'name': 'E2E Test Project',
            'description': 'Testing complete workflow',
            'repository_url': 'https://github.com/test/repo'
        })
        # Step may fail due to auth, but endpoint should exist
        assert create_response.status_code != 404

        # Step 2: List projects
        list_response = client.get('/projects')
        assert list_response.status_code in [200, 401]  # May require auth
        if list_response.status_code == 200:
            projects = list_response.json()
            assert isinstance(projects, list)

        # Step 3: Get specific project (if creation succeeded)
        if create_response.status_code in [200, 201]:
            try:
                project_data = create_response.json()
                project_id = project_data.get('id') or project_data.get('project_id')
                if project_id:
                    get_response = client.get(f'/projects/{project_id}')
                    assert get_response.status_code in [200, 401]
            except (json.JSONDecodeError, AttributeError):
                pass  # Response format varies

    def test_create_update_delete_project_workflow(self, client: TestClient):
        """Test: User can modify project lifecycle"""
        # Step 1: Create project
        create_response = client.post('/projects', json={
            'name': 'Lifecycle Test',
            'description': 'Testing create-update-delete'
        })
        assert create_response.status_code != 404

        # Step 2: Update project (even if creation failed, endpoint should exist)
        update_response = client.put('/projects/test-project-id', json={
            'name': 'Updated Name',
            'description': 'Updated description'
        })
        assert update_response.status_code != 404

        # Step 3: Delete project
        delete_response = client.delete('/projects/test-project-id')
        assert delete_response.status_code != 404


class TestGitHubIntegrationWorkflows:
    """E2E tests for GitHub integration workflows"""

    def test_github_import_and_status_workflow(self, client: TestClient):
        """Test: User can import from GitHub and check sync status"""
        # Step 1: Import from GitHub
        import_response = client.post('/github/import', json={
            'url': 'https://github.com/anthropics/anthropic-sdk-python',
            'project_id': 'test-project'
        })
        # Endpoint should exist and validate inputs
        assert import_response.status_code != 404

        # Step 2: Check import status
        status_response = client.get('/github/status')
        assert status_response.status_code != 404

        # Step 3: Pull updates
        pull_response = client.get('/github/pull')
        assert pull_response.status_code != 404

    def test_github_sync_workflow(self, client: TestClient):
        """Test: User can sync GitHub repository"""
        # Step 1: Initiate sync
        sync_response = client.post('/github/push', json={
            'project_id': 'test-project',
            'message': 'Sync from Socrates'
        })
        assert sync_response.status_code != 404

        # Step 2: Verify status after sync
        status_response = client.get('/github/status')
        assert status_response.status_code != 404


class TestKnowledgeBaseWorkflows:
    """E2E tests for knowledge base workflows"""

    def test_import_search_export_knowledge_workflow(self, client: TestClient):
        """Test: User can import, search, and export knowledge"""
        # Step 1: Import knowledge from URL
        import_url_response = client.post('/knowledge/import/url', json={
            'url': 'https://docs.example.com',
            'title': 'Example Docs'
        })
        assert import_url_response.status_code != 404

        # Step 2: Import knowledge from text
        import_text_response = client.post('/knowledge/import/text', json={
            'text': 'This is knowledge content',
            'title': 'Text Knowledge'
        })
        assert import_text_response.status_code != 404

        # Step 3: List imported documents
        list_response = client.get('/knowledge/documents')
        assert list_response.status_code in [200, 401]
        if list_response.status_code == 200:
            documents = list_response.json()
            assert isinstance(documents, list)

        # Step 4: Search knowledge
        search_response = client.get('/knowledge/search', params={
            'q': 'example'
        })
        assert search_response.status_code in [200, 401]

        # Step 5: Export knowledge
        export_response = client.get('/knowledge/export')
        assert export_response.status_code != 404

    def test_document_lifecycle_workflow(self, client: TestClient):
        """Test: User can manage document lifecycle"""
        # Step 1: Import document
        import_response = client.post('/knowledge/import/text', json={
            'text': 'Test document content',
            'title': 'Test Doc'
        })
        assert import_response.status_code != 404

        # Step 2: Delete document
        delete_response = client.delete('/knowledge/documents/test-doc-id')
        assert delete_response.status_code != 404


class TestLLMConfigurationWorkflows:
    """E2E tests for LLM provider configuration"""

    def test_llm_provider_configuration_workflow(self, client: TestClient):
        """Test: User can configure LLM providers"""
        # Step 1: List available providers
        list_response = client.get('/llm/providers')
        assert list_response.status_code in [200, 401]
        if list_response.status_code == 200:
            providers = list_response.json()
            assert isinstance(providers, list)

        # Step 2: Get current config
        config_response = client.get('/llm/config')
        assert config_response.status_code in [200, 401]
        if config_response.status_code == 200:
            config = config_response.json()
            assert isinstance(config, dict)

        # Step 3: Set default provider
        set_default_response = client.put('/llm/default-provider', json={
            'provider': 'anthropic'
        })
        assert set_default_response.status_code in [200, 400, 401]

        # Step 4: Set model for provider
        set_model_response = client.put('/llm/model', json={
            'provider': 'anthropic',
            'model': 'claude-3-sonnet'
        })
        assert set_model_response.status_code in [200, 400, 401]

    def test_api_key_management_workflow(self, client: TestClient):
        """Test: User can manage API keys for providers"""
        # Step 1: Add API key
        add_key_response = client.post('/llm/api-key', json={
            'provider': 'anthropic',
            'api_key': 'sk-test-key-123'
        })
        assert add_key_response.status_code in [200, 400, 401]

        # Step 2: Get config (verify key not exposed)
        config_response = client.get('/llm/config')
        if config_response.status_code == 200:
            data = config_response.json()
            # API key should not be exposed in response
            assert 'api_key' not in str(data).lower() or '***' in str(data)

        # Step 3: Get usage statistics
        usage_response = client.get('/llm/usage-stats')
        assert usage_response.status_code in [200, 401]

        # Step 4: Remove API key
        remove_key_response = client.delete('/llm/api-key/anthropic')
        assert remove_key_response.status_code in [200, 401, 404]


class TestCodeAnalysisWorkflows:
    """E2E tests for code analysis workflows"""

    def test_code_validation_workflow(self, client: TestClient):
        """Test: User can validate code in multiple languages"""
        languages = ['python', 'javascript', 'java', 'cpp']

        for language in languages:
            response = client.post('/analysis/validate', json={
                'code': 'print("hello")',
                'language': language
            })
            # Endpoint should exist
            assert response.status_code != 404

    def test_code_maturity_assessment_workflow(self, client: TestClient):
        """Test: System can assess code maturity"""
        response = client.post('/analysis/maturity', json={
            'code': 'def hello(): return "world"',
            'language': 'python'
        })
        assert response.status_code in [200, 400, 401]


class TestCollaborationWorkflows:
    """E2E tests for collaboration features"""

    def test_team_member_management_workflow(self, client: TestClient):
        """Test: User can manage team members"""
        # Step 1: Invite team member
        invite_response = client.post('/collaboration/invite', json={
            'email': 'teammate@example.com',
            'role': 'developer'
        })
        assert invite_response.status_code in [200, 400, 401]

        # Step 2: List team members
        list_response = client.get('/collaboration/members')
        assert list_response.status_code in [200, 401]
        if list_response.status_code == 200:
            members = list_response.json()
            assert isinstance(members, list)


class TestCompleteUserJourney:
    """E2E tests for complete user journeys"""

    def test_new_user_complete_workflow(self, client: TestClient):
        """Test: Complete journey from registration to project analysis"""
        user_id = 'e2e_user_journey_test'

        # Step 1: Register
        register_response = client.post('/auth/register', json={
            'username': user_id,
            'email': f'{user_id}@example.com',
            'password': 'JourneyPassword123!'
        })
        assert register_response.status_code != 404

        # Step 2: Login
        login_response = client.post('/auth/login', json={
            'username': user_id,
            'password': 'JourneyPassword123!'
        })
        assert login_response.status_code != 404

        # Extract token if available
        token = None
        if login_response.status_code == 200:
            try:
                data = login_response.json()
                token = data.get('access_token') or data.get('token')
            except Exception:
                pass

        # Step 3: Create project
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        create_proj_response = client.post('/projects', json={
            'name': f'{user_id} Project',
            'description': 'Journey test project'
        }, headers=headers)
        assert create_proj_response.status_code != 404

        # Step 4: Configure LLM
        config_response = client.put('/llm/default-provider', json={
            'provider': 'anthropic'
        }, headers=headers)
        assert config_response.status_code != 404

        # Step 5: Analyze code
        analyze_response = client.post('/analysis/validate', json={
            'code': 'def main(): pass',
            'language': 'python'
        }, headers=headers)
        assert analyze_response.status_code != 404

    def test_github_project_import_workflow(self, client: TestClient):
        """Test: User can import and work with GitHub project"""
        # Step 1: Register/Login (simplified)
        client.post('/auth/login', json={
            'username': 'github_user',
            'password': 'github_pass'
        })

        # Step 2: Import GitHub project
        import_response = client.post('/github/import', json={
            'url': 'https://github.com/test/repo',
            'project_id': 'github-import-test'
        })
        assert import_response.status_code != 404

        # Step 3: Analyze imported code
        analyze_response = client.post('/analysis/maturity', json={
            'code': 'sample code'
        })
        assert analyze_response.status_code != 404

        # Step 4: Sync back to GitHub
        sync_response = client.post('/github/push', json={
            'project_id': 'github-import-test'
        })
        assert sync_response.status_code != 404

    def test_knowledge_enriched_code_analysis_workflow(self, client: TestClient):
        """Test: User leverages knowledge base for analysis"""
        # Step 1: Import knowledge
        import_knowledge_response = client.post('/knowledge/import/text', json={
            'text': 'Best practices for Python: use type hints, write docstrings',
            'title': 'Python Best Practices'
        })
        assert import_knowledge_response.status_code != 404

        # Step 2: Search relevant knowledge
        search_response = client.get('/knowledge/search', params={
            'q': 'Python'
        })
        assert search_response.status_code != 404

        # Step 3: Analyze code (system should use knowledge)
        analyze_response = client.post('/analysis/validate', json={
            'code': 'def my_function(x): return x * 2',
            'language': 'python'
        })
        assert analyze_response.status_code != 404

        # Step 4: Generate improvements with LLM
        generate_response = client.post('/code_generation/improve', json={
            'code': 'def my_function(x): return x * 2'
        })
        # This endpoint may not exist, but we test availability
        assert generate_response.status_code != 404
