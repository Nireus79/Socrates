/**
 * Tests for GitHubPublish component
 *
 * Tests GitHub repository creation form, validation, and API integration
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { GitHubPublish } from '../../src/components/project/GitHubPublish';
import * as projectAPI from '../../src/api/projects';

jest.mock('../../src/api/projects');

describe('GitHubPublish Component', () => {
  const mockProjectId = 'proj_test123';
  const mockProject = {
    id: mockProjectId,
    name: 'test-project',
    description: 'Test project'
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render publish button', () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      expect(screen.getByRole('button', { name: /publish/i })).toBeInTheDocument();
    });

    it('should render form dialog on button click', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /publish to github/i })).toBeInTheDocument();
      });
    });

    it('should display form fields', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/repository name/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/github token/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    it('should validate empty repository name', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const submitButton = await screen.findByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/repository name is required/i)).toBeInTheDocument();
      });
    });

    it('should validate empty GitHub token', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      fireEvent.change(repoInput, { target: { value: 'test-repo' } });

      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/github token is required/i)).toBeInTheDocument();
      });
    });

    it('should validate GitHub token format', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const tokenInput = await screen.findByLabelText(/github token/i);
      fireEvent.change(tokenInput, { target: { value: 'invalid-token' } });

      await waitFor(() => {
        expect(screen.getByText(/token must start with ghp_/i)).toBeInTheDocument();
      });
    });

    it('should validate repository name format', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      fireEvent.change(repoInput, { target: { value: 'INVALID REPO!' } });

      await waitFor(() => {
        expect(screen.getByText(/invalid repository name/i)).toBeInTheDocument();
      });
    });

    it('should accept valid repository names', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);

      const validNames = ['test-repo', 'test_repo', 'testrepo123'];
      for (const name of validNames) {
        fireEvent.change(repoInput, { target: { value: name } });
        expect(screen.queryByText(/invalid repository name/i)).not.toBeInTheDocument();
      }
    });
  });

  describe('Visibility Toggle', () => {
    it('should render private/public toggle', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const visibilityToggle = await screen.findByRole('checkbox', { name: /private/i });
      expect(visibilityToggle).toBeInTheDocument();
    });

    it('should default to private repository', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const privateToggle = await screen.findByRole('checkbox', { name: /private/i });
      expect(privateToggle).toBeChecked();
    });

    it('should allow toggling visibility', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const privateToggle = await screen.findByRole('checkbox', { name: /private/i });
      expect(privateToggle).toBeChecked();

      fireEvent.click(privateToggle);
      expect(privateToggle).not.toBeChecked();
    });
  });

  describe('GitHub Token Input', () => {
    it('should not display token in plain text', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const tokenInput = (await screen.findByLabelText(/github token/i)) as HTMLInputElement;
      expect(tokenInput.type).toBe('password');
    });

    it('should show token visibility toggle', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const visibilityButton = await screen.findByRole('button', { name: /show.*token/i });
      expect(visibilityButton).toBeInTheDocument();
    });

    it('should toggle token visibility', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const tokenInput = (await screen.findByLabelText(/github token/i)) as HTMLInputElement;
      const visibilityButton = screen.getByRole('button', { name: /show.*token/i });

      expect(tokenInput.type).toBe('password');

      fireEvent.click(visibilityButton);
      expect(tokenInput.type).toBe('text');

      fireEvent.click(visibilityButton);
      expect(tokenInput.type).toBe('password');
    });

    it('should show token generation link', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const generateLink = await screen.findByRole('link', { name: /generate.*token/i });
      expect(generateLink).toHaveAttribute('href', expect.stringContaining('github.com'));
    });
  });

  describe('Form Submission', () => {
    it('should submit form with valid data', async () => {
      (projectAPI.publishToGitHub as jest.Mock).mockResolvedValue({
        success: true,
        data: {
          repo_url: 'https://github.com/user/test-repo',
          clone_url: 'https://github.com/user/test-repo.git'
        }
      });

      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      const tokenInput = screen.getByLabelText(/github token/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      fireEvent.change(repoInput, { target: { value: 'test-repo' } });
      fireEvent.change(tokenInput, { target: { value: 'ghp_validtoken123' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(projectAPI.publishToGitHub).toHaveBeenCalledWith(
          mockProjectId,
          expect.objectContaining({
            repo_name: 'test-repo',
            github_token: 'ghp_validtoken123'
          })
        );
      });
    });

    it('should include visibility setting in submission', async () => {
      (projectAPI.publishToGitHub as jest.Mock).mockResolvedValue({
        success: true,
        data: {}
      });

      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      const tokenInput = screen.getByLabelText(/github token/i);
      const privateToggle = screen.getByRole('checkbox', { name: /private/i });

      fireEvent.change(repoInput, { target: { value: 'test-repo' } });
      fireEvent.change(tokenInput, { target: { value: 'ghp_token123' } });
      fireEvent.click(privateToggle); // Toggle to public

      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(projectAPI.publishToGitHub).toHaveBeenCalledWith(
          mockProjectId,
          expect.objectContaining({
            private: false
          })
        );
      });
    });

    it('should disable submit button while publishing', async () => {
      (projectAPI.publishToGitHub as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 500))
      );

      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      const tokenInput = screen.getByLabelText(/github token/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      fireEvent.change(repoInput, { target: { value: 'test-repo' } });
      fireEvent.change(tokenInput, { target: { value: 'ghp_token123' } });
      fireEvent.click(submitButton);

      expect(submitButton).toBeDisabled();

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });
  });

  describe('Success Handling', () => {
    it('should display success message', async () => {
      (projectAPI.publishToGitHub as jest.Mock).mockResolvedValue({
        success: true,
        data: {
          repo_url: 'https://github.com/user/test-repo',
          clone_url: 'https://github.com/user/test-repo.git'
        }
      });

      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      const tokenInput = screen.getByLabelText(/github token/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      fireEvent.change(repoInput, { target: { value: 'test-repo' } });
      fireEvent.change(tokenInput, { target: { value: 'ghp_token123' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/successfully published/i)).toBeInTheDocument();
      });
    });

    it('should display repository URL', async () => {
      const repoUrl = 'https://github.com/user/test-repo';
      (projectAPI.publishToGitHub as jest.Mock).mockResolvedValue({
        success: true,
        data: {
          repo_url: repoUrl,
          clone_url: 'https://github.com/user/test-repo.git'
        }
      });

      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      const tokenInput = screen.getByLabelText(/github token/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      fireEvent.change(repoInput, { target: { value: 'test-repo' } });
      fireEvent.change(tokenInput, { target: { value: 'ghp_token123' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /view on github/i });
        expect(link).toHaveAttribute('href', repoUrl);
      });
    });

    it('should display clone command', async () => {
      (projectAPI.publishToGitHub as jest.Mock).mockResolvedValue({
        success: true,
        data: {
          repo_url: 'https://github.com/user/test-repo',
          clone_url: 'https://github.com/user/test-repo.git'
        }
      });

      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      const tokenInput = screen.getByLabelText(/github token/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      fireEvent.change(repoInput, { target: { value: 'test-repo' } });
      fireEvent.change(tokenInput, { target: { value: 'ghp_token123' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/git clone/i)).toBeInTheDocument();
      });
    });

    it('should allow copying clone command', async () => {
      (projectAPI.publishToGitHub as jest.Mock).mockResolvedValue({
        success: true,
        data: {
          repo_url: 'https://github.com/user/test-repo',
          clone_url: 'https://github.com/user/test-repo.git'
        }
      });

      const mockClipboard = jest.spyOn(navigator.clipboard, 'writeText').mockResolvedValue();

      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      const tokenInput = screen.getByLabelText(/github token/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      fireEvent.change(repoInput, { target: { value: 'test-repo' } });
      fireEvent.change(tokenInput, { target: { value: 'ghp_token123' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        const copyButton = screen.getByRole('button', { name: /copy/i });
        fireEvent.click(copyButton);
        expect(mockClipboard).toHaveBeenCalled();
      });

      mockClipboard.mockRestore();
    });
  });

  describe('Error Handling', () => {
    it('should display authentication error', async () => {
      (projectAPI.publishToGitHub as jest.Mock).mockRejectedValue(
        new Error('Invalid GitHub token')
      );

      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      const tokenInput = screen.getByLabelText(/github token/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      fireEvent.change(repoInput, { target: { value: 'test-repo' } });
      fireEvent.change(tokenInput, { target: { value: 'ghp_invalid' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/invalid.*token/i)).toBeInTheDocument();
      });
    });

    it('should handle repository already exists error', async () => {
      (projectAPI.publishToGitHub as jest.Mock).mockRejectedValue(
        new Error('Repository already exists')
      );

      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      const tokenInput = screen.getByLabelText(/github token/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      fireEvent.change(repoInput, { target: { value: 'existing-repo' } });
      fireEvent.change(tokenInput, { target: { value: 'ghp_token123' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/already exists/i)).toBeInTheDocument();
      });
    });

    it('should handle network errors', async () => {
      (projectAPI.publishToGitHub as jest.Mock).mockRejectedValue(
        new Error('Network error')
      );

      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      const tokenInput = screen.getByLabelText(/github token/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      fireEvent.change(repoInput, { target: { value: 'test-repo' } });
      fireEvent.change(tokenInput, { target: { value: 'ghp_token123' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/network/i)).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      (projectAPI.publishToGitHub as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      const tokenInput = screen.getByLabelText(/github token/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      fireEvent.change(repoInput, { target: { value: 'test-repo' } });
      fireEvent.change(tokenInput, { target: { value: 'ghp_token123' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper form structure', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const form = await screen.findByRole('form');
      expect(form).toBeInTheDocument();
    });

    it('should have accessible labels', async () => {
      render(<GitHubPublish projectId={mockProjectId} />);
      const publishButton = screen.getByRole('button', { name: /publish/i });
      fireEvent.click(publishButton);

      const repoInput = await screen.findByLabelText(/repository name/i);
      expect(repoInput).toBeInTheDocument();

      const tokenInput = screen.getByLabelText(/github token/i);
      expect(tokenInput).toBeInTheDocument();
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      render(<GitHubPublish projectId={mockProjectId} />);

      const publishButton = screen.getByRole('button', { name: /publish/i });
      await user.tab();
      expect(publishButton).toHaveFocus();

      await user.keyboard('{Enter}');
      expect(screen.getByRole('heading', { name: /publish to github/i })).toBeInTheDocument();
    });
  });
});
