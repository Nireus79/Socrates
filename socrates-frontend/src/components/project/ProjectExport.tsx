/**
 * ProjectExport Component
 *
 * Allows users to download generated projects in multiple formats
 * (ZIP, TAR, TAR.GZ, etc.)
 */

import React, { useState } from 'react';
import { AlertCircle, Download, Loader } from 'lucide-react';
import { exportProject } from '@/api/projects';
import type { Project } from '@/types';

interface ProjectExportProps {
  project: Project;
  onSuccess?: () => void;
  onError?: (error: string) => void;
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
  project,
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
      const blob = await exportProject(project.id, selectedFormat);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Determine filename based on format
      const timestamp = new Date().toISOString().split('T')[0];
      const projectName = project.name.toLowerCase().replace(/\s+/g, '_');
      const extension = selectedFormat === 'zip' ? 'zip' : selectedFormat === 'tar' ? 'tar' : selectedFormat;
      link.download = `${projectName}_${timestamp}.${extension}`;

      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccess(true);
      onSuccess?.();

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to export project';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Download Project
        </h3>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Export your generated project as a downloadable archive
        </p>
      </div>

      {/* Format Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select Format
        </label>
        <div className="space-y-2">
          {EXPORT_FORMATS.map((format) => (
            <div key={format.value} className="flex items-start">
              <input
                type="radio"
                id={`format-${format.value}`}
                name="export-format"
                value={format.value}
                checked={selectedFormat === format.value}
                onChange={(e) => setSelectedFormat(e.target.value as ExportFormat)}
                className="mt-1 cursor-pointer"
                disabled={isLoading}
              />
              <label
                htmlFor={`format-${format.value}`}
                className="ml-3 cursor-pointer"
              >
                <div className="font-medium text-gray-900 dark:text-white">
                  {format.label}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {format.description}
                </div>
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800 dark:text-red-200">
            <p className="font-medium">Export Failed</p>
            <p className="mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="rounded-md bg-green-50 dark:bg-green-900/20 p-4">
          <p className="text-sm font-medium text-green-800 dark:text-green-200">
            ✓ Project exported successfully
          </p>
        </div>
      )}

      {/* Export Button */}
      <button
        onClick={handleExport}
        disabled={isLoading}
        className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
      >
        {isLoading ? (
          <>
            <Loader className="h-4 w-4 animate-spin" />
            Preparing Download...
          </>
        ) : (
          <>
            <Download className="h-4 w-4" />
            Download Project
          </>
        )}
      </button>

      {/* Info Box */}
      <div className="rounded-md bg-blue-50 dark:bg-blue-900/20 p-4">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          <strong>Tip:</strong> Your project includes all necessary files for GitHub:
          pyproject.toml, GitHub Actions workflows, Dockerfile, tests, and documentation.
        </p>
      </div>
    </div>
  );
};

export default ProjectExport;
