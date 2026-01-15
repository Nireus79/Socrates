/**
 * Tests for ProjectExport component
 *
 * Tests UI rendering, user interactions, and API integration
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { ProjectExport } from '../../src/components/project/ProjectExport';
import * as projectAPI from '../../src/api/projects';

// Mock the API
jest.mock('../../src/api/projects');

describe('ProjectExport Component', () => {
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
    it('should render export button', () => {
      render(<ProjectExport projectId={mockProjectId} />);
      expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument();
    });

    it('should render format selector', async () => {
      render(<ProjectExport projectId={mockProjectId} />);
      const button = screen.getByRole('button', { name: /export/i });
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText(/zip/i)).toBeInTheDocument();
      });
    });

    it('should show loading state during export', async () => {
      (projectAPI.exportProject as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(new Blob()), 1000))
      );

      render(<ProjectExport projectId={mockProjectId} />);
      const button = screen.getByRole('button', { name: /export/i });
      fireEvent.click(button);

      expect(screen.getByText(/exporting/i)).toBeInTheDocument();
    });

    it('should display format options', async () => {
      render(<ProjectExport projectId={mockProjectId} />);
      const button = screen.getByRole('button', { name: /format/i });
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('ZIP')).toBeInTheDocument();
        expect(screen.getByText('TAR.GZ')).toBeInTheDocument();
        expect(screen.getByText('TAR.BZ2')).toBeInTheDocument();
      });
    });
  });

  describe('Format Selection', () => {
    it('should default to ZIP format', () => {
      render(<ProjectExport projectId={mockProjectId} />);
      expect(screen.getByText(/zip/i)).toBeInTheDocument();
    });

    it('should allow changing format', async () => {
      render(<ProjectExport projectId={mockProjectId} />);
      const formatButton = screen.getByRole('button', { name: /format/i });
      fireEvent.click(formatButton);

      const tarGzOption = await screen.findByText('TAR.GZ');
      fireEvent.click(tarGzOption);

      expect(screen.getByText('TAR.GZ')).toBeInTheDocument();
    });

    it('should call API with correct format', async () => {
      (projectAPI.exportProject as jest.Mock).mockResolvedValue(new Blob());

      render(<ProjectExport projectId={mockProjectId} />);

      // Change format to tar.gz
      const formatButton = screen.getByRole('button', { name: /format/i });
      fireEvent.click(formatButton);
      const tarOption = await screen.findByText('TAR.GZ');
      fireEvent.click(tarOption);

      // Click export
      const exportButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(projectAPI.exportProject).toHaveBeenCalledWith(
          mockProjectId,
          'tar.gz'
        );
      });
    });
  });

  describe('Download Functionality', () => {
    it('should trigger download on success', async () => {
      const mockBlob = new Blob(['test content'], { type: 'application/zip' });
      (projectAPI.exportProject as jest.Mock).mockResolvedValue(mockBlob);

      // Mock window.URL.createObjectURL
      const mockCreateObjectURL = jest.spyOn(window.URL, 'createObjectURL');
      mockCreateObjectURL.mockReturnValue('blob:mock-url');

      render(<ProjectExport projectId={mockProjectId} />);
      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob);
      });

      mockCreateObjectURL.mockRestore();
    });

    it('should generate correct filename with date', async () => {
      const mockBlob = new Blob(['test'], { type: 'application/zip' });
      (projectAPI.exportProject as jest.Mock).mockResolvedValue(mockBlob);

      render(<ProjectExport projectId={mockProjectId} projectName="my-project" />);
      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        // Filename should be like: my-project_20260115.zip
        expect(screen.getByText(/downloading.*my-project/i)).toBeInTheDocument();
      });
    });

    it('should complete download successfully', async () => {
      const mockBlob = new Blob(['test content'], { type: 'application/zip' });
      (projectAPI.exportProject as jest.Mock).mockResolvedValue(mockBlob);

      render(<ProjectExport projectId={mockProjectId} />);
      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(screen.getByText(/download complete/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message on API failure', async () => {
      const errorMessage = 'Failed to export project';
      (projectAPI.exportProject as jest.Mock).mockRejectedValue(
        new Error(errorMessage)
      );

      render(<ProjectExport projectId={mockProjectId} />);
      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(screen.getByText(new RegExp(errorMessage, 'i'))).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      (projectAPI.exportProject as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      render(<ProjectExport projectId={mockProjectId} />);
      let downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });

      // Mock successful retry
      (projectAPI.exportProject as jest.Mock).mockResolvedValueOnce(
        new Blob(['content'])
      );

      const retryButton = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText(/download complete/i)).toBeInTheDocument();
      });
    });

    it('should handle network errors', async () => {
      (projectAPI.exportProject as jest.Mock).mockRejectedValue(
        new Error('Network timeout')
      );

      render(<ProjectExport projectId={mockProjectId} />);
      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(screen.getByText(/network/i)).toBeInTheDocument();
      });
    });

    it('should handle authentication errors', async () => {
      (projectAPI.exportProject as jest.Mock).mockRejectedValue(
        new Error('Unauthorized')
      );

      render(<ProjectExport projectId={mockProjectId} />);
      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(screen.getByText(/not authorized/i)).toBeInTheDocument();
      });
    });

    it('should handle project not found error', async () => {
      (projectAPI.exportProject as jest.Mock).mockRejectedValue(
        new Error('Project not found')
      );

      render(<ProjectExport projectId={mockProjectId} />);
      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(screen.getByText(/not found/i)).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('should disable button while exporting', async () => {
      (projectAPI.exportProject as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(new Blob()), 500))
      );

      render(<ProjectExport projectId={mockProjectId} />);
      const downloadButton = screen.getByRole('button', { name: /download/i });

      fireEvent.click(downloadButton);

      expect(downloadButton).toBeDisabled();

      await waitFor(() => {
        expect(downloadButton).not.toBeDisabled();
      });
    });

    it('should show progress indicator', async () => {
      (projectAPI.exportProject as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(new Blob()), 500))
      );

      render(<ProjectExport projectId={mockProjectId} />);
      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(screen.getByRole('progressbar')).toBeInTheDocument();
      });
    });

    it('should allow canceling export', async () => {
      (projectAPI.exportProject as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(new Blob()), 2000))
      );

      render(<ProjectExport projectId={mockProjectId} />);
      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      const cancelButton = await screen.findByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(screen.getByText(/cancelled/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<ProjectExport projectId={mockProjectId} />);

      const downloadButton = screen.getByRole('button', { name: /download/i });
      expect(downloadButton).toHaveAttribute('aria-label');
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      render(<ProjectExport projectId={mockProjectId} />);

      const downloadButton = screen.getByRole('button', { name: /download/i });

      // Tab to button
      await user.tab();
      expect(downloadButton).toHaveFocus();

      // Press Enter to activate
      await user.keyboard('{Enter}');
      expect(projectAPI.exportProject).toHaveBeenCalled();
    });
  });

  describe('Props Validation', () => {
    it('should accept projectId prop', () => {
      render(<ProjectExport projectId={mockProjectId} />);
      expect(screen.getByRole('button', { name: /download/i })).toBeInTheDocument();
    });

    it('should accept optional projectName prop', () => {
      render(<ProjectExport projectId={mockProjectId} projectName="my-project" />);
      expect(screen.getByText(/my-project/i)).toBeInTheDocument();
    });

    it('should accept optional onSuccess callback', async () => {
      const mockOnSuccess = jest.fn();
      (projectAPI.exportProject as jest.Mock).mockResolvedValue(new Blob());

      render(
        <ProjectExport
          projectId={mockProjectId}
          onSuccess={mockOnSuccess}
        />
      );

      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it('should accept optional onError callback', async () => {
      const mockOnError = jest.fn();
      const error = new Error('Test error');
      (projectAPI.exportProject as jest.Mock).mockRejectedValue(error);

      render(
        <ProjectExport
          projectId={mockProjectId}
          onError={mockOnError}
        />
      );

      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith(error);
      });
    });
  });
});
