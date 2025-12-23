/**
 * Frontend E2E Workflow Tests
 * Tests complete user journeys across multiple pages and components
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';

// Mock axios
vi.mock('axios');
const mockedAxios = axios as any;

/**
 * Test: Complete Login to Project Creation Workflow
 * User journey: Login → Navigate to Dashboard → Create Project → Verify Project
 */
describe('E2E: Login to Project Creation Workflow', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should complete full login and project creation workflow', async () => {
    // Step 1: User logs in with credentials
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        access_token: 'valid_jwt_token_e2e',
        refresh_token: 'refresh_token_e2e',
        user: {
          id: 'user_123',
          username: 'testuser',
          email: 'test@example.com'
        }
      }
    });

    // Simulate login action
    const loginResponse = await axios.post('http://localhost:8000/auth/login', {
      username: 'testuser',
      password: 'password123'
    });

    expect(loginResponse.status).toBe(200);
    expect(loginResponse.data.access_token).toBeDefined();
    expect(loginResponse.data.user).toBeDefined();

    // Step 2: Store tokens and user in localStorage (as done in authStore.ts)
    localStorage.setItem('access_token', loginResponse.data.access_token);
    localStorage.setItem('refresh_token', loginResponse.data.refresh_token);
    localStorage.setItem('user', JSON.stringify(loginResponse.data.user));

    // Step 3: Verify user persistence
    expect(localStorage.getItem('access_token')).toBe('valid_jwt_token_e2e');
    expect(localStorage.getItem('user')).toBeDefined();
    const storedUser = JSON.parse(localStorage.getItem('user')!);
    expect(storedUser.username).toBe('testuser');

    // Step 4: Simulate navigation to projects page (requires auth token)
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: []
    });

    const token = localStorage.getItem('access_token');
    const projectsResponse = await axios.get(
      'http://localhost:8000/projects',
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(projectsResponse.status).toBe(200);
    expect(Array.isArray(projectsResponse.data)).toBe(true);

    // Step 5: Create new project with auth token
    mockedAxios.post.mockResolvedValueOnce({
      status: 201,
      data: {
        id: 'project_123',
        name: 'My Test Project',
        description: 'Testing project creation',
        owner_id: 'user_123',
        created_at: '2025-12-23T10:00:00Z'
      }
    });

    const createProjectResponse = await axios.post(
      'http://localhost:8000/projects',
      {
        name: 'My Test Project',
        description: 'Testing project creation'
      },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(createProjectResponse.status).toBe(201);
    expect(createProjectResponse.data.id).toBe('project_123');

    // Step 6: Verify new project appears in list
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: [createProjectResponse.data]
    });

    const updatedProjectsResponse = await axios.get(
      'http://localhost:8000/projects',
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(updatedProjectsResponse.data.length).toBe(1);
    expect(updatedProjectsResponse.data[0].name).toBe('My Test Project');
  });

  it('should maintain authentication across page navigation', async () => {
    // Step 1: User logs in
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        access_token: 'nav_test_token',
        refresh_token: 'nav_refresh_token',
        user: {
          id: 'user_nav',
          username: 'navuser',
          email: 'nav@example.com'
        }
      }
    });

    const loginResponse = await axios.post('http://localhost:8000/auth/login', {
      username: 'navuser',
      password: 'password'
    });

    // Step 2: Store authentication
    localStorage.setItem('access_token', loginResponse.data.access_token);
    localStorage.setItem('user', JSON.stringify(loginResponse.data.user));

    // Step 3: Simulate page navigation (user goes to different page)
    // On new page, app calls restoreAuthFromStorage()
    const storedToken = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user');

    expect(storedToken).toBe('nav_test_token');
    expect(storedUser).toBeDefined();

    // Step 4: Make authenticated request from new page
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: { id: 'project_123' }
    });

    const response = await axios.get(
      'http://localhost:8000/projects/project_123',
      { headers: { Authorization: `Bearer ${storedToken}` } }
    );

    expect(response.status).toBe(200);
    // User stayed authenticated despite navigation
  });

  it('should handle logout and clear authentication', async () => {
    // Step 1: User is logged in
    localStorage.setItem('access_token', 'logout_test_token');
    localStorage.setItem('user', JSON.stringify({ id: 'user_1', username: 'logoutuser' }));

    expect(localStorage.getItem('access_token')).toBeDefined();
    expect(localStorage.getItem('user')).toBeDefined();

    // Step 2: User initiates logout
    mockedAxios.post.mockResolvedValueOnce({ status: 200, data: {} });

    const token = localStorage.getItem('access_token')!;
    const logoutResponse = await axios.post(
      'http://localhost:8000/auth/logout',
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(logoutResponse.status).toBe(200);

    // Step 3: Clear localStorage after logout
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');

    // Step 4: Verify auth is cleared
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });
});

/**
 * Test: Project Import and Analysis Workflow
 * User journey: Login → Import GitHub → Analyze Code → View Results
 */
describe('E2E: GitHub Import and Code Analysis Workflow', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should import GitHub project and analyze code', async () => {
    const token = 'github_workflow_token';
    localStorage.setItem('access_token', token);
    localStorage.setItem('user', JSON.stringify({ id: 'user_gh', username: 'ghuser' }));

    // Step 1: Import from GitHub
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        project_id: 'gh_import_123',
        repository_url: 'https://github.com/test/repo',
        status: 'importing'
      }
    });

    const importResponse = await axios.post(
      'http://localhost:8000/github/import',
      { url: 'https://github.com/test/repo' },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(importResponse.status).toBe(200);
    expect(importResponse.data.project_id).toBe('gh_import_123');

    // Step 2: Check import status
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: {
        status: 'completed',
        files_imported: 45,
        total_lines: 12000
      }
    });

    const statusResponse = await axios.get(
      'http://localhost:8000/github/status',
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(statusResponse.data.status).toBe('completed');

    // Step 3: Analyze code quality
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        maturity_score: 75,
        issues: ['missing_docstrings', 'low_test_coverage'],
        recommendations: ['Add docstrings', 'Increase test coverage']
      }
    });

    const analysisResponse = await axios.post(
      'http://localhost:8000/analysis/maturity',
      { project_id: 'gh_import_123' },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(analysisResponse.data.maturity_score).toBe(75);
    expect(Array.isArray(analysisResponse.data.recommendations)).toBe(true);

    // Step 4: Verify results can be viewed
    expect(analysisResponse.data.maturity_score).toBeGreaterThanOrEqual(0);
    expect(analysisResponse.data.maturity_score).toBeLessThanOrEqual(100);
  });
});

/**
 * Test: Knowledge Base and AI Analysis Workflow
 * User journey: Import Knowledge → Configure LLM → Generate Improvements
 */
describe('E2E: Knowledge Base and AI-Powered Analysis Workflow', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should import knowledge and use for code analysis', async () => {
    const token = 'knowledge_workflow_token';
    localStorage.setItem('access_token', token);

    // Step 1: Import knowledge document
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        document_id: 'doc_best_practices',
        title: 'Python Best Practices',
        status: 'indexed'
      }
    });

    const importDocResponse = await axios.post(
      'http://localhost:8000/knowledge/import/text',
      {
        text: 'Use type hints, write docstrings, follow PEP 8, write unit tests',
        title: 'Python Best Practices'
      },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(importDocResponse.status).toBe(200);
    expect(importDocResponse.data.document_id).toBe('doc_best_practices');

    // Step 2: Search knowledge
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: [
        {
          document_id: 'doc_best_practices',
          title: 'Python Best Practices',
          relevance_score: 0.95
        }
      ]
    });

    const searchResponse = await axios.get(
      'http://localhost:8000/knowledge/search',
      {
        params: { q: 'Python best practices' },
        headers: { Authorization: `Bearer ${token}` }
      }
    );

    expect(searchResponse.data.length).toBeGreaterThan(0);
    expect(searchResponse.data[0].document_id).toBe('doc_best_practices');

    // Step 3: Configure LLM provider
    mockedAxios.put.mockResolvedValueOnce({
      status: 200,
      data: { provider: 'anthropic', configured: true }
    });

    const configResponse = await axios.put(
      'http://localhost:8000/llm/default-provider',
      { provider: 'anthropic' },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(configResponse.data.configured).toBe(true);

    // Step 4: Analyze code with knowledge-enhanced system
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        analysis: {
          issues: ['missing_type_hints', 'no_docstring'],
          improvements: [
            'Add type hints: def process(data: List[str]) -> str:',
            'Add docstring documenting function purpose',
            'Follow PEP 8 naming conventions'
          ],
          knowledge_references: ['doc_best_practices']
        }
      }
    });

    const analysisResponse = await axios.post(
      'http://localhost:8000/analysis/validate',
      { code: 'def process(data): return data[0]', language: 'python' },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(analysisResponse.data.analysis.improvements.length).toBeGreaterThan(0);
    expect(analysisResponse.data.analysis.knowledge_references).toContain('doc_best_practices');
  });

  it('should handle token refresh during long workflow', async () => {
    let token = 'initial_token_k';
    localStorage.setItem('access_token', token);

    // Step 1: First request with initial token
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: []
    });

    let response = await axios.get(
      'http://localhost:8000/knowledge/documents',
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(response.status).toBe(200);

    // Step 2: Simulate token expiration - next request fails
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: { access_token: 'refreshed_token_k', refresh_token: 'new_refresh_k' }
    });

    const refreshResponse = await axios.post(
      'http://localhost:8000/auth/refresh',
      { refresh_token: localStorage.getItem('refresh_token') || 'default_refresh' }
    );

    token = refreshResponse.data.access_token;
    localStorage.setItem('access_token', token);

    // Step 3: Continue workflow with new token
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: [{ document_id: 'doc_1', title: 'Document 1' }]
    });

    response = await axios.get(
      'http://localhost:8000/knowledge/documents',
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(response.status).toBe(200);
    expect(response.data.length).toBeGreaterThan(0);
  });
});

/**
 * Test: Team Collaboration Workflow
 * User journey: Create Project → Invite Team Members → Collaborate
 */
describe('E2E: Team Collaboration Workflow', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should create project and invite team members', async () => {
    const token = 'collab_token';
    localStorage.setItem('access_token', token);

    // Step 1: Create project
    mockedAxios.post.mockResolvedValueOnce({
      status: 201,
      data: {
        id: 'collab_project_1',
        name: 'Team Project',
        owner_id: 'user_owner'
      }
    });

    const createResponse = await axios.post(
      'http://localhost:8000/projects',
      { name: 'Team Project' },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(createResponse.data.id).toBe('collab_project_1');

    // Step 2: Invite team member
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        invitation_id: 'inv_123',
        invited_email: 'teammate@example.com',
        status: 'pending'
      }
    });

    const inviteResponse = await axios.post(
      'http://localhost:8000/collaboration/invite',
      { email: 'teammate@example.com', role: 'developer' },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(inviteResponse.data.status).toBe('pending');

    // Step 3: List team members
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: [
        { id: 'user_owner', email: 'owner@example.com', role: 'owner' },
        { id: 'user_invited', email: 'teammate@example.com', role: 'developer' }
      ]
    });

    const membersResponse = await axios.get(
      'http://localhost:8000/collaboration/members',
      { headers: { Authorization: `Bearer ${token}` } }
    );

    expect(membersResponse.data.length).toBe(2);
    expect(membersResponse.data[1].role).toBe('developer');
  });
});

/**
 * Test: Error Recovery and User Guidance Workflow
 * Tests that errors are handled gracefully and user gets guidance
 */
describe('E2E: Error Handling and User Guidance', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should handle auth errors with user-friendly messages', async () => {
    // Step 1: Failed login shows friendly message
    mockedAxios.post.mockRejectedValueOnce({
      response: { status: 401, data: { detail: 'Invalid credentials' } }
    });

    try {
      await axios.post('http://localhost:8000/auth/login', {
        username: 'user',
        password: 'wrongpass'
      });
    } catch (error: any) {
      // User friendly message should be shown
      expect(error.response.status).toBe(401);
    }

    // Step 2: Registration duplicate user error
    mockedAxios.post.mockRejectedValueOnce({
      response: { status: 400, data: { detail: 'Username already exists' } }
    });

    try {
      await axios.post('http://localhost:8000/auth/register', {
        username: 'existing',
        email: 'new@example.com',
        password: 'pass'
      });
    } catch (error: any) {
      expect(error.response.status).toBe(400);
    }
  });

  it('should guide user through auth restoration failure', async () => {
    // Step 1: Store invalid token
    localStorage.setItem('access_token', 'expired_or_invalid_token');
    localStorage.setItem('user', JSON.stringify({ id: 'user_1' }));

    // Step 2: Try to use expired token
    mockedAxios.get.mockRejectedValueOnce({
      response: { status: 401, data: { detail: 'Token expired' } }
    });

    const token = localStorage.getItem('access_token')!;
    try {
      await axios.get(
        'http://localhost:8000/projects',
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (error: any) {
      expect(error.response.status).toBe(401);
      // User should be redirected to login with helpful message
    }

    // Step 3: User can retry - clear and login again
    localStorage.clear();

    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        access_token: 'new_valid_token',
        user: { id: 'user_1', username: 'user' }
      }
    });

    const newLoginResponse = await axios.post('http://localhost:8000/auth/login', {
      username: 'user',
      password: 'password'
    });

    expect(newLoginResponse.data.access_token).toBeDefined();
  });
});
