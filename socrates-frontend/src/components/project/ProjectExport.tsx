/**
 * ProjectExport Component
 *
 * Allows users to download generated projects in multiple formats
 * (ZIP, TAR, TAR.GZ, etc.)
 */

import React, { useState } from 'react';
import { AlertCircle, Download, Loader, X } from 'lucide-react';
import { Dialog, Button, Alert } from '../common';

interface ProjectExportProps {
  projectId: string;
  projectName: string;
  onClose: () => void;
  onSuccess: () => void;
  onError: (error: string) => void;
}

type ExportFormat = 'zip' | 'tar' | 'tar.gz' | 'tar.bz2';

interface FormatOption {
  value: ExportFormat;
  label: string;
  description: string;
}

const EXPORT_FORMATS: FormatOption[] = [
  {
    value: 'zip',
    label: 'ZIP Archive',
    description: 'Works on all platforms (Windows, Mac, Linux)',
  },
  {
    value: 'tar.gz',
    label: 'TAR.GZ Archive',
    description: 'Compressed TAR format (common on Unix/Linux)',
  },
  {
    value: 'tar.bz2',
    label: 'TAR.BZ2 Archive',
    description: 'Better compression than TAR.GZ',
  },
  {
    value: 'tar',
    label: 'TAR Archive',
    description: 'Uncompressed TAR format',
  },
];

export const ProjectExport: React.FC<ProjectExportProps> = ({
  projectId,
  projectName,
  onClose,
  onSuccess,
  onError,
}) => {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('zip');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleExport = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      // Call the export API endpoint
      const response = await fetch(
        `/api/projects/${projectId}/export?format=${selectedFormat}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      const blob = await response.blob();

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Determine filename based on format
      const timestamp = new Date().toISOString().split('T')[0];
      const formattedName = projectName.toLowerCase().replace(/\s+/g, '_');
      const extension = selectedFormat === 'zip' ? 'zip' : selectedFormat;
      link.download = `${formattedName}_${timestamp}.${extension}`;

      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccess(true);
      onSuccess();

      // Close dialog after 2 seconds
      setTimeout(() => onClose(), 2000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to export project';
      setError(errorMessage);
      onError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog isOpen={true} onClose={onClose}>
      <div className="max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Export Project
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Description */}
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Download your generated project as a complete, GitHub-ready archive with
            all necessary files, configurations, and workflows.
          </p>

          {/* Format Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Select Format
            </label>
            <div className="space-y-2">
              {EXPORT_FORMATS.map((format) => (
                <label
                  key={format.value}
                  className="flex items-start p-3 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <input
                    type="radio"
                    name="export-format"
                    value={format.value}
                    checked={selectedFormat === format.value}
                    onChange={(e) => setSelectedFormat(e.target.value as ExportFormat)}
                    className="mt-1 cursor-pointer"
                    disabled={isLoading}
                  />
                  <div className="ml-3 flex-1">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {format.label}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {format.description}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <Alert type="error" title="Export Failed">
              {error}
            </Alert>
          )}

          {/* Success Message */}
          {success && (
            <Alert type="success" title="Export Successful">
              Your project is being downloaded. Check your downloads folder.
            </Alert>
          )}

          {/* Info Box */}
          <div className="rounded-lg bg-blue-50 dark:bg-blue-900/20 p-4 border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>Included:</strong> All source code, GitHub Actions workflows,
              Docker configuration, tests, and documentation.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              variant="secondary"
              fullWidth
              onClick={onClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              fullWidth
              onClick={handleExport}
              disabled={isLoading}
              icon={isLoading ? <Loader className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            >
              {isLoading ? 'Preparing...' : 'Download'}
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
};

export default ProjectExport;
