/**
 * ProjectsPage - Manage projects with filtering and searching
 */

import React from 'react';
import { Plus, Search, Filter, Github } from 'lucide-react';
import { useProjectStore, useAuthStore } from '../../stores';
import { showSuccess, showError } from '../../stores/notificationStore';
import { MainLayout, PageHeader } from '../../components/layout';
import {
  Card,
  Button,
  Input,
  EmptyState,
  Dialog,
} from '../../components/common';
import { ProjectCard, CreateProjectModal, FilterModal } from '../../components/project';
import { GitHubImportModal } from '../../components/github';

export const ProjectsPage: React.FC = () => {
  const { projects, isLoading, listProjects, deleteProject, restoreProject } = useProjectStore();
  const { user } = useAuthStore();
  const [searchTerm, setSearchTerm] = React.useState('');
  const [filterType, setFilterType] = React.useState('all');
  const [showCreateModal, setShowCreateModal] = React.useState(false);
  const [showGitHubImport, setShowGitHubImport] = React.useState(false);
  const [showFilterModal, setShowFilterModal] = React.useState(false);
  const [projectToDelete, setProjectToDelete] = React.useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);

  // Fetch projects on component mount
  React.useEffect(() => {
    listProjects();
  }, [listProjects]);

  // Filter and search projects
  const filteredProjects = React.useMemo(() => {
    let filtered = projects;

    // Apply archive filter
    if (filterType === 'active') {
      filtered = filtered.filter((p) => !p.is_archived);
    } else if (filterType === 'archived') {
      filtered = filtered.filter((p) => p.is_archived);
    }

    // Apply search term
    if (searchTerm) {
      const query = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.description?.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [projects, filterType, searchTerm]);

  const tabs = [
    { label: 'All Projects', value: 'all' },
    { label: 'Active', value: 'active' },
    { label: 'Archived', value: 'archived' },
  ];

  const handleOpenProject = (projectId: string) => {
    window.location.href = `/projects/${projectId}`;
  };

  const handleArchiveProject = (projectId: string) => {
    setProjectToDelete(projectId);
    setShowDeleteDialog(true);
  };

  const handleConfirmDelete = async () => {
    if (!projectToDelete) return;
    try {
      setIsDeleting(true);
      const deletedProject = projects.find(p => p.project_id === projectToDelete);
      await deleteProject(projectToDelete);
      showSuccess('Project Archived', `${deletedProject?.name} has been archived successfully`);
      setShowDeleteDialog(false);
      setProjectToDelete(null);
    } catch (error) {
      console.error('Failed to archive project:', error);
      showError('Failed to Archive Project', 'Unable to archive the project. Please try again.');
      setShowDeleteDialog(false);
      setProjectToDelete(null);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleToggleArchive = async (projectId: string) => {
    const project = projects.find(p => p.project_id === projectId);
    if (!project) return;

    if (project.is_archived) {
      // Restore the project
      try {
        await restoreProject(projectId);
        showSuccess('Project Restored', `${project.name} has been restored successfully`);
      } catch (error) {
        console.error('Failed to restore project:', error);
        showError('Failed to Restore Project', 'Unable to restore the project. Please try again.');
      }
    } else {
      // Archive the project
      handleArchiveProject(projectId);
    }
  };

  const handleDeleteProjectPermanently = async (projectId: string) => {
    if (window.confirm('Are you sure you want to permanently delete this project? This action cannot be undone.')) {
      try {
        setIsDeleting(true);
        const deletedProject = projects.find(p => p.project_id === projectId);
        await deleteProject(projectId);
        // Refresh the projects list after deletion
        await listProjects();
        showSuccess('Project Deleted', `${deletedProject?.name} has been permanently deleted`);
      } catch (error) {
        console.error('Failed to delete project:', error);
        showError('Failed to Delete Project', 'Unable to delete the project. Please try again.');
      } finally {
        setIsDeleting(false);
      }
    }
  };

  const handleCreateProject = async (formData: any) => {
    try {
      await useProjectStore.getState().createProject(
        formData.name,
        formData.description,
        formData.knowledgeBase  // Pass initial knowledge base content
      );
      setShowCreateModal(false);
    } catch (error) {
      console.error('Failed to create project:', error);
      throw error;
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <PageHeader
          title="Projects"
          description="Manage your projects and track progress"
          breadcrumbs={[
            { label: 'Dashboard', onClick: () => window.location.href = '/dashboard' },
            { label: 'Projects' },
          ]}
          actions={
            <div className="flex gap-2">
              <Button
                variant="secondary"
                icon={<Github className="h-4 w-4" />}
                onClick={() => setShowGitHubImport(true)}
              >
                Import from GitHub
              </Button>
              <Button
                variant="primary"
                icon={<Plus className="h-4 w-4" />}
                onClick={() => setShowCreateModal(true)}
              >
                New Project
              </Button>
            </div>
          }
        />

        {/* Search and Filter */}
        <Card>
          <div className="flex gap-3 flex-col sm:flex-row">
            <div className="flex-1">
              <Input
                placeholder="Search projects..."
                icon={<Search className="h-4 w-4" />}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button
              variant="secondary"
              icon={<Filter className="h-4 w-4" />}
              onClick={() => setShowFilterModal(true)}
            >
              Filter
            </Button>
          </div>
        </Card>

        {/* Filter Tabs */}
        <Card>
          <div className="flex gap-2">
            {tabs.map((tab) => (
              <Button
                key={tab.value}
                variant={filterType === tab.value ? 'primary' : 'secondary'}
                onClick={() => setFilterType(tab.value)}
              >
                {tab.label}
              </Button>
            ))}
          </div>
        </Card>

        {/* Projects List/Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Loading projects...</p>
            </div>
          </div>
        ) : filteredProjects.length === 0 ? (
          <Card>
            <EmptyState
              icon={<Plus className="h-12 w-12" />}
              title={searchTerm ? 'No projects found' : 'No projects yet'}
              description={
                searchTerm
                  ? 'Try adjusting your search terms'
                  : 'Create your first project to start your Socratic learning journey'
              }
              action={{
                label: 'Create Project',
                onClick: () => setShowCreateModal(true),
              }}
            />
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => (
              <ProjectCard
                key={project.project_id}
                project={project}
                maturity={0}
                teamCount={1}
                onOpen={handleOpenProject}
                onArchive={handleToggleArchive}
                onDelete={project.is_archived ? handleDeleteProjectPermanently : undefined}
              />
            ))}
          </div>
        )}

        {/* Create Project Modal */}
        <CreateProjectModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateProject}
          isLoading={isLoading}
        />

        {/* GitHub Import Modal */}
        <GitHubImportModal
          isOpen={showGitHubImport}
          onClose={() => setShowGitHubImport(false)}
          onSuccess={() => {
            setShowGitHubImport(false);
            listProjects();
          }}
        />

        {/* Archive Project Confirmation Dialog */}
        <Dialog
          isOpen={showDeleteDialog}
          onClose={() => setShowDeleteDialog(false)}
          title="Archive Project?"
          description="This will archive the project. You can restore it later from the Archived tab. All data will be preserved."
          confirmLabel="Archive Project"
          cancelLabel="Cancel"
          onConfirm={handleConfirmDelete}
          variant="warning"
          isLoading={isDeleting}
        />

        {/* Filter Modal */}
        <FilterModal
          isOpen={showFilterModal}
          onClose={() => setShowFilterModal(false)}
          onApply={(filters) => {
            // Apply filter logic - for now just close
            // In a full implementation, you could apply more complex filtering
            setShowFilterModal(false);
          }}
          onReset={() => {
            setFilterType('all');
            setSearchTerm('');
          }}
        />
      </div>
    </MainLayout>
  );
};
