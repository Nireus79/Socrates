/**
 * Files Page - Browse generated, imported, and saved project files
 *
 * Displays:
 * - Directory structure of generated files
 * - File explorer with syntax highlighting preview
 * - File statistics and metadata
 * - Import/export operations
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useProjectStore } from '../../stores/projectStore';
import { MainLayout, PageHeader } from '../../components/layout';
import { Card } from '../../components/common';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  language?: string;
  size?: number;
  children?: FileNode[];
  content?: string;
  createdAt?: string;
  updatedAt?: string;
}

export const FilesPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { currentProject, projects, getProject, listProjects } = useProjectStore();
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projectId || '');

  useEffect(() => {
    listProjects();
  }, [listProjects]);

  useEffect(() => {
    if (selectedProjectId) {
      getProject(selectedProjectId);
    }
  }, [selectedProjectId, getProject]);

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
        description="Browse generated, imported, and saved project files"
      />

      <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          📁 Project Files
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Browse generated, imported, and saved project files
        </p>

        {projectId && (
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              Project: {currentProject?.name || projectId}
            </p>
          </div>
        )}

        <div className="mt-8 text-gray-600 dark:text-gray-400">
          <p className="mb-4">This feature is currently under development.</p>
          <p>The file browser will be available soon.</p>
        </div>
      </div>
      </div>
    </MainLayout>
  );
};

export default FilesPage;
