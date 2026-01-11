/**
 * Files Page - Browse generated and refactored project files
 *
 * Displays:
 * - Project file listing with metadata
 * - Syntax-highlighted code preview with Monaco Editor
 * - File information panel with download/copy options
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useProjectStore } from '../../stores/projectStore';
import { MainLayout, PageHeader } from '../../components/layout';
import { Card } from '../../components/common';
import FileList from './components/FileList';
import FilePreview from './components/FilePreview';
import FileMetadata from './components/FileMetadata';
import EmptyState from './components/EmptyState';
import { AlertCircle } from 'lucide-react';

export const FilesPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const {
    currentProject,
    projects,
    getProject,
    listProjects,
    files,
    selectedFile,
    fileContent,
    isLoading,
    error,
    fetchProjectFiles,
    selectFile,
    clearFiles,
  } = useProjectStore();
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projectId || '');

  // Load projects on mount
  useEffect(() => {
    listProjects();
  }, [listProjects]);

  // Load project details and files when project selection changes
  useEffect(() => {
    if (selectedProjectId) {
      getProject(selectedProjectId);
      fetchProjectFiles(selectedProjectId);
    } else {
      clearFiles();
    }
  }, [selectedProjectId, getProject, fetchProjectFiles, clearFiles]);

  return (
    <MainLayout>
      {/* Project Selector */}
      {projects.length > 0 && (
        <div className="max-w-6xl mx-auto px-4 py-4">
          <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 dark:from-blue-900 dark:to-indigo-900 dark:border-blue-800">
            <div className="flex items-center gap-3">
              <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">
                Select Project:
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="">-- Choose a Project --</option>
                {projects.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
          </Card>
        </div>
      )}

      {/* Page Header */}
      <PageHeader
        title="Project Files"
        description="Browse and view generated code files with syntax highlighting"
      />

      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-800 dark:text-red-200">Error loading files</p>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* No Project Selected */}
        {!selectedProjectId && (
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8 text-center">
            <p className="text-gray-600 dark:text-gray-400">
              Select a project from the dropdown above to view its files
            </p>
          </div>
        )}

        {/* Files View */}
        {selectedProjectId && (
          <>
            {isLoading ? (
              <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8 text-center">
                <div className="inline-block">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
                <p className="text-gray-600 dark:text-gray-400 mt-4">Loading files...</p>
              </div>
            ) : files.length === 0 ? (
              <EmptyState />
            ) : (
              <div className="grid grid-cols-3 gap-6 items-start">
                {/* File List - Left Column */}
                <div className="col-span-1">
                  <div className="sticky top-4">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Files</h3>
                    <FileList
                      files={files}
                      selectedFile={selectedFile}
                      onFileSelect={(file) => selectFile(file, selectedProjectId)}
                      isLoading={isLoading}
                    />
                  </div>
                </div>

                {/* File Preview & Metadata - Right Column */}
                <div className="col-span-2 space-y-4">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Preview</h3>
                    <FilePreview file={selectedFile} content={fileContent} />
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Details</h3>
                    <FileMetadata
                      file={selectedFile}
                      content={fileContent}
                      projectId={selectedProjectId}
                      onFileDeleted={() => fetchProjectFiles(selectedProjectId)}
                    />
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </MainLayout>
  );
};

export default FilesPage;
