/**
 * End-to-End Tests for Complete Project Generation, Export, and GitHub Publishing Workflows
 *
 * Tests the complete user journey from project creation to GitHub deployment.
 * Uses Cypress for browser automation and real API interaction.
 */

describe('Complete Project Workflow - Generate, Export, and Publish', () => {
  const baseUrl = Cypress.env('BASE_URL') || 'http://localhost:3000';
  const apiUrl = Cypress.env('API_URL') || 'http://localhost:8000';

  // Test data
  const projectName = `test-project-${Date.now()}`;
  const projectDescription = 'End-to-end test project for GitHub-ready generation';
  const githubToken = Cypress.env('GITHUB_TOKEN') || '';

  let projectId: string;

  beforeEach(() => {
    // Login before each test
    cy.visit(`${baseUrl}/login`);
    cy.get('input[name="email"]').type(Cypress.env('TEST_USER_EMAIL'));
    cy.get('input[name="password"]').type(Cypress.env('TEST_USER_PASSWORD'));
    cy.get('button[type="submit"]').click();

    // Wait for login to complete
    cy.url().should('not.include', '/login');
  });

  describe('Project Generation', () => {
    it('should create a new project with all required fields', () => {
      cy.visit(`${baseUrl}/projects/new`);

      // Fill in project details
      cy.get('input[name="projectName"]').type(projectName);
      cy.get('textarea[name="description"]').type(projectDescription);
      cy.get('select[name="projectType"]').select('software');
      cy.get('input[name="requirement1"]').type('REST API endpoints');
      cy.get('button[aria-label="add-requirement"]').click();
      cy.get('input[name="requirement2"]').type('Database integration');

      // Submit form
      cy.get('button[name="createProject"]').click();

      // Should be redirected to project detail page
      cy.url().should('include', '/projects/');
      cy.contains('Project created successfully').should('be.visible');

      // Extract project ID from URL
      cy.url().then(url => {
        const matches = url.match(/\/projects\/([^/]+)/);
        projectId = matches ? matches[1] : '';
      });
    });

    it('should generate project code and artifacts', () => {
      cy.visit(`${baseUrl}/projects/${projectId}`);

      // Click finalize button
      cy.get('button[name="finalizeProject"]').click();

      // Wait for code generation
      cy.get('[role="progressbar"]').should('be.visible');
      cy.get('button[name="finalizeProject"]', { timeout: 30000 }).should('not.exist');

      // Verify files were generated
      cy.contains('All project files generated').should('be.visible');
      cy.get('div[role="tablist"]').within(() => {
        cy.contains('README.md').should('exist');
        cy.contains('pyproject.toml').should('exist');
        cy.contains('Dockerfile').should('exist');
      });
    });

    it('should display project structure', () => {
      cy.visit(`${baseUrl}/projects/${projectId}`);

      // View project structure
      cy.get('button[name="viewStructure"]').click();

      // Check for expected file structure
      cy.contains('src/').should('be.visible');
      cy.contains('tests/').should('be.visible');
      cy.contains('.github/workflows/').should('be.visible');
      cy.contains('pyproject.toml').should('be.visible');
      cy.contains('Dockerfile').should('be.visible');
    });
  });

  describe('Project Export', () => {
    beforeEach(() => {
      // Skip if projectId not set
      if (!projectId) {
        cy.skip();
      }
      cy.visit(`${baseUrl}/projects/${projectId}`);
    });

    it('should export project as ZIP archive', () => {
      // Click export button
      cy.get('button[name="exportProject"]').click();

      // Verify export dialog
      cy.contains('Export Project').should('be.visible');

      // Select ZIP format (default)
      cy.get('select[name="exportFormat"]').should('have.value', 'zip');

      // Download
      cy.get('button[name="downloadExport"]').click();

      // Check that download started
      cy.readFile(`C:\\Users\\${Cypress.env('USER')}\\Downloads\\${projectName}_*.zip`, { timeout: 10000 })
        .should('exist');
    });

    it('should export project as TAR.GZ archive', () => {
      cy.get('button[name="exportProject"]').click();

      cy.contains('Export Project').should('be.visible');

      // Select TAR.GZ format
      cy.get('select[name="exportFormat"]').select('tar.gz');

      // Download
      cy.get('button[name="downloadExport"]').click();

      // Check that download started
      cy.get('[role="status"]').contains(/download.*complete/i, { timeout: 15000 }).should('be.visible');
    });

    it('should show download progress', () => {
      cy.get('button[name="exportProject"]').click();

      cy.get('button[name="downloadExport"]').click();

      // Progress indicator should appear
      cy.get('[role="progressbar"]').should('be.visible');
      cy.get('[role="status"]').should('contain', 'Preparing archive');

      // Progress should complete
      cy.get('[role="status"]', { timeout: 20000 }).should('contain', /complete/i);
    });

    it('should allow canceling export', () => {
      cy.get('button[name="exportProject"]').click();

      cy.get('button[name="downloadExport"]').click();

      // Cancel should appear after a moment
      cy.get('button[name="cancelExport"]', { timeout: 2000 }).should('exist');

      // Click cancel
      cy.get('button[name="cancelExport"]').click();

      // Should show cancellation message
      cy.contains('Export cancelled').should('be.visible');
    });

    it('should handle export errors gracefully', () => {
      // Simulate export error by intercepting API
      cy.intercept('GET', `${apiUrl}/projects/*/export`, { statusCode: 500 }).as('exportError');

      cy.get('button[name="exportProject"]').click();
      cy.get('button[name="downloadExport"]').click();

      cy.wait('@exportError');

      // Error message should appear
      cy.contains(/failed to export/i).should('be.visible');

      // Retry button should be available
      cy.get('button[name="retryExport"]').should('be.visible');
    });
  });

  describe('GitHub Publishing', () => {
    beforeEach(() => {
      if (!projectId || !githubToken) {
        cy.skip();
      }
      cy.visit(`${baseUrl}/projects/${projectId}`);
    });

    it('should open GitHub publish dialog', () => {
      cy.get('button[name="publishGithub"]').click();

      cy.contains('Publish to GitHub').should('be.visible');
      cy.get('input[name="repoName"]').should('exist');
      cy.get('input[name="githubToken"]').should('exist');
    });

    it('should validate repository name', () => {
      cy.get('button[name="publishGithub"]').click();

      // Try invalid names
      const invalidNames = ['INVALID', 'invalid repo!', ''];

      invalidNames.forEach(name => {
        cy.get('input[name="repoName"]').clear().type(name);
        cy.get('button[name="publishToGithub"]').click();

        if (name === '') {
          cy.contains(/name is required/i).should('be.visible');
        } else if (name.includes('!')) {
          cy.contains(/invalid characters/i).should('be.visible');
        }
      });
    });

    it('should validate GitHub token format', () => {
      cy.get('button[name="publishGithub"]').click();

      // Try invalid token
      cy.get('input[name="githubToken"]').type('invalid_token');

      // Should show validation error
      cy.contains(/must start with ghp_/i).should('be.visible');
    });

    it('should successfully publish to GitHub', () => {
      // Skip if no real GitHub token available
      if (!githubToken || githubToken === 'mock-token') {
        cy.skip();
      }

      cy.get('button[name="publishGithub"]').click();

      // Fill in form
      cy.get('input[name="repoName"]').type(`${projectName}-test`);
      cy.get('textarea[name="description"]').type(projectDescription);
      cy.get('input[name="githubToken"]').type(githubToken);

      // Ensure private repo
      cy.get('input[name="isPrivate"]').should('be.checked');

      // Publish
      cy.get('button[name="publishToGithub"]').click();

      // Wait for publishing
      cy.get('[role="status"]', { timeout: 60000 }).should('contain', /successfully published/i);

      // Verify repository link is shown
      cy.get('a[name="viewRepository"]').should('be.visible');
      cy.get('a[name="viewRepository"]').should('have.attr', 'href').and('include', 'github.com');
    });

    it('should display clone command after publishing', () => {
      if (!githubToken || githubToken === 'mock-token') {
        cy.skip();
      }

      cy.get('button[name="publishGithub"]').click();

      cy.get('input[name="repoName"]').type(`${projectName}-clone-test`);
      cy.get('input[name="githubToken"]').type(githubToken);
      cy.get('button[name="publishToGithub"]').click();

      // Wait for success
      cy.get('[role="status"]', { timeout: 60000 }).should('contain', /successfully published/i);

      // Check for clone command
      cy.contains(/git clone/i).should('be.visible');
      cy.contains(`${projectName}-clone-test.git`).should('be.visible');
    });

    it('should allow copying clone command', () => {
      if (!githubToken || githubToken === 'mock-token') {
        cy.skip();
      }

      cy.get('button[name="publishGithub"]').click();

      cy.get('input[name="repoName"]').type(`${projectName}-copy-test`);
      cy.get('input[name="githubToken"]').type(githubToken);
      cy.get('button[name="publishToGithub"]').click();

      cy.get('[role="status"]', { timeout: 60000 }).should('contain', /successfully published/i);

      // Copy clone command
      cy.get('button[name="copyCloneCommand"]').click();

      // Verify copy feedback
      cy.contains(/copied/i).should('be.visible');
    });

    it('should handle authentication errors', () => {
      cy.get('button[name="publishGithub"]').click();

      cy.get('input[name="repoName"]').type(`${projectName}-auth-test`);
      cy.get('input[name="githubToken"]').type('ghp_invalid_token_12345');

      cy.get('button[name="publishToGithub"]').click();

      // Should show authentication error
      cy.contains(/authentication failed|invalid token/i, { timeout: 10000 }).should('be.visible');

      // Retry should be available
      cy.get('button[name="retryPublish"]').should('be.visible');
    });

    it('should handle repository already exists error', () => {
      if (!githubToken || githubToken === 'mock-token') {
        cy.skip();
      }

      // First, create a repo
      cy.get('button[name="publishGithub"]').click();
      const uniqueRepoName = `${projectName}-duplicate-${Date.now()}`;
      cy.get('input[name="repoName"]').type(uniqueRepoName);
      cy.get('input[name="githubToken"]').type(githubToken);
      cy.get('button[name="publishToGithub"]').click();

      cy.get('[role="status"]', { timeout: 60000 }).should('contain', /successfully published/i);

      // Try to create same repo again
      cy.get('button[name="publishGithub"]').click();
      cy.get('input[name="repoName"]').clear().type(uniqueRepoName);
      cy.get('input[name="githubToken"]').type(githubToken);
      cy.get('button[name="publishToGithub"]').click();

      // Should show already exists error
      cy.contains(/already exists|already created/i, { timeout: 10000 }).should('be.visible');
    });
  });

  describe('Complete Workflow E2E', () => {
    it('should complete full workflow: generate -> export -> publish', () => {
      if (!githubToken || githubToken === 'mock-token') {
        cy.skip();
      }

      // Step 1: Create project
      cy.visit(`${baseUrl}/projects/new`);
      const workflowProjectName = `workflow-test-${Date.now()}`;

      cy.get('input[name="projectName"]').type(workflowProjectName);
      cy.get('textarea[name="description"]').type('Complete workflow test');
      cy.get('select[name="projectType"]').select('api');
      cy.get('button[name="createProject"]').click();

      cy.url().should('include', '/projects/');

      // Extract project ID
      let workflowProjectId: string;
      cy.url().then(url => {
        const matches = url.match(/\/projects\/([^/]+)/);
        workflowProjectId = matches ? matches[1] : '';
      });

      // Step 2: Finalize project
      cy.get('button[name="finalizeProject"]').click();
      cy.get('[role="status"]', { timeout: 30000 }).should('contain', /generated/i);

      // Step 3: Export project
      cy.get('button[name="exportProject"]').click();
      cy.get('button[name="downloadExport"]').click();
      cy.get('[role="status"]', { timeout: 20000 }).should('contain', /complete/i);

      // Step 4: Publish to GitHub
      cy.get('button[name="publishGithub"]').click();
      cy.get('input[name="repoName"]').type(`${workflowProjectName}-final`);
      cy.get('input[name="githubToken"]').type(githubToken);
      cy.get('button[name="publishToGithub"]').click();

      // Verify success
      cy.get('[role="status"]', { timeout: 60000 }).should('contain', /successfully published/i);
      cy.get('a[name="viewRepository"]').should('exist');
    });
  });

  describe('Error Recovery and Retry', () => {
    beforeEach(() => {
      if (!projectId) {
        cy.skip();
      }
      cy.visit(`${baseUrl}/projects/${projectId}`);
    });

    it('should allow retrying failed export', () => {
      // Simulate network error
      cy.intercept('GET', `${apiUrl}/projects/*/export`, { statusCode: 500 }).as('exportFail');

      cy.get('button[name="exportProject"]').click();
      cy.get('button[name="downloadExport"]').click();
      cy.wait('@exportFail');

      cy.contains(/failed to export/i).should('be.visible');

      // Clear the intercept to allow success
      cy.intercept('GET', `${apiUrl}/projects/*/export`, {
        statusCode: 200,
        body: new Blob()
      }).as('exportSuccess');

      cy.get('button[name="retryExport"]').click();
      cy.wait('@exportSuccess');

      cy.get('[role="status"]', { timeout: 20000 }).should('contain', /complete/i);
    });

    it('should allow retrying failed publish', () => {
      if (!githubToken || githubToken === 'mock-token') {
        cy.skip();
      }

      // Simulate auth failure
      cy.intercept('POST', `${apiUrl}/projects/*/publish-to-github`, { statusCode: 401 }).as('publishFail');

      cy.get('button[name="publishGithub"]').click();
      cy.get('input[name="repoName"]').type(`${projectName}-retry`);
      cy.get('input[name="githubToken"]').type('invalid_token');
      cy.get('button[name="publishToGithub"]').click();

      cy.wait('@publishFail');
      cy.contains(/authentication/i).should('be.visible');

      // Clear intercept and retry with valid token
      cy.intercept('POST', `${apiUrl}/projects/*/publish-to-github`, {
        statusCode: 200,
        body: {
          success: true,
          data: {
            repo_url: 'https://github.com/test/repo',
            clone_url: 'https://github.com/test/repo.git'
          }
        }
      }).as('publishSuccess');

      cy.get('input[name="githubToken"]').clear().type(githubToken);
      cy.get('button[name="retryPublish"]').click();

      cy.wait('@publishSuccess');
      cy.get('[role="status"]', { timeout: 10000 }).should('contain', /successfully published/i);
    });
  });

  describe('Concurrent Operations', () => {
    it('should handle multiple exports simultaneously', () => {
      if (!projectId) {
        cy.skip();
      }

      cy.visit(`${baseUrl}/projects/${projectId}`);

      // Start first export
      cy.get('button[name="exportProject"]').click();
      cy.get('button[name="downloadExport"]').click();

      // Open another export dialog before first completes
      cy.get('button[name="closeExportDialog"]').should('not.exist'); // Dialog still open
      cy.get('button[name="downloadExport"]').click();

      // Both should complete
      cy.get('[role="status"]', { timeout: 30000 }).should('contain', /complete/i);
    });
  });
});
