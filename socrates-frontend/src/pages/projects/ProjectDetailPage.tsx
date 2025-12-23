/**
 * ProjectDetailPage - Detailed project view with phase and team management
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { Users, Settings, TrendingUp, MessageSquare, Code, Github, Zap } from 'lucide-react';
import { useProjectStore } from '../../stores';
import { useCollaborationStore } from '../../stores/collaborationStore';
import { MainLayout, PageHeader } from '../../components/layout';
import {
  Card,
  Button,
  Badge,
  Progress,
  Alert,
  EmptyState,
} from '../../components/common';
import { SyncStatusWidget } from '../../components/github';
import { GitHubImportModal } from '../../components/github';
import { EditProjectModal } from '../../components/project';

export const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { currentProject, isLoading: projectLoading, getProject, updateProject, deleteProject } = useProjectStore();
  const { collaborators, isLoading: collabLoading, loadCollaborators } = useCollaborationStore();
  const [activeTab, setActiveTab] = React.useState('overview');
  const [showGitHubImport, setShowGitHubImport] = React.useState(false);
  const [showEditModal, setShowEditModal] = React.useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [previousProjectName, setPreviousProjectName] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (projectId) {
      getProject(projectId);
      loadCollaborators(projectId);
    }
  }, [projectId, getProject, loadCollaborators]);

  const handleConfirmDelete = async () => {
    if (!projectId) return;
    try {
      setIsDeleting(true);
      await deleteProject(projectId);
      // Redirect to projects page after successful deletion
      window.location.href = '/projects';
    } catch (error) {
      console.error('Failed to delete project:', error);
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const isLoading = projectLoading || collabLoading;

  if (isLoading || !currentProject) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading project...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  const phaseNames: Record<string, string> = {
    'discovery': 'Discovery',
    'analysis': 'Analysis',
    'design': 'Design',
    'implementation': 'Implementation',
    'testing': 'Testing',
    'deployment': 'Deployment',
  };

  const tabs = [
    { label: 'Overview', value: 'overview' },
    { label: 'GitHub', value: 'github' },
    { label: 'Analysis', value: 'analysis' },
    { label: 'Team', value: 'team' },
    { label: 'Settings', value: 'settings' },
  ];

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <PageHeader
          title={currentProject.name}
          description={currentProject.description}
          breadcrumbs={[
            { label: 'Dashboard', onClick: () => window.location.href = '/dashboard' },
            { label: 'Projects', onClick: () => window.location.href = '/projects' },
            { label: currentProject.name },
          ]}
          actions={
            <Button
              variant="secondary"
              icon={<Settings className="h-4 w-4" />}
              onClick={() => setShowEditModal(true)}
            >
              Edit
            </Button>
          }
        />

        {/* Phase and Maturity Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Current Phase
            </h3>
            <div className="space-y-4">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {phaseNames[currentProject.phase]}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Discovery • Analysis • Design • Implementation • Testing • Deployment
              </p>
              <Button
                variant="primary"
                fullWidth
                onClick={() => window.location.href = `/chat/${currentProject.project_id}`}
              >
                Continue Dialogue
              </Button>
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Project Maturity
            </h3>
            <div className="space-y-4">
              <Progress value={0} />
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  0% Complete
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => window.location.href = `/analytics`}
                >
                  View Details
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <Button
              variant="primary"
              icon={<MessageSquare className="h-4 w-4" />}
              fullWidth
              onClick={() => window.location.href = `/chat/${currentProject.project_id}`}
            >
              Dialogue
            </Button>
            <Button
              variant="secondary"
              icon={<Code className="h-4 w-4" />}
              fullWidth
              onClick={() => window.location.href = `/code`}
            >
              Generate Code
            </Button>
            <Button
              variant="outline"
              icon={<Zap className="h-4 w-4" />}
              fullWidth
              onClick={() => setActiveTab('analysis')}
            >
              Analyze
            </Button>
            <Button
              variant="outline"
              icon={<TrendingUp className="h-4 w-4" />}
              fullWidth
              onClick={() => window.location.href = `/analytics`}
            >
              Analytics
            </Button>
          </div>
        </Card>

        {/* Tabs */}
        <Card>
          <div className="flex gap-2 mb-6 border-b border-gray-200 dark:border-gray-700">
            {tabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setActiveTab(tab.value)}
                className={`px-4 py-2 font-medium transition-colors ${
                  activeTab === tab.value
                    ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="mt-6">
            {activeTab === 'overview' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Phase
                  </label>
                  <Badge variant="primary">{phaseNames[currentProject.phase]}</Badge>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Created
                  </label>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {new Date(currentProject.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Last Updated
                  </label>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {new Date(currentProject.updated_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            )}

            {activeTab === 'github' && (
              <div className="space-y-4">
                <SyncStatusWidget projectId={currentProject.project_id} />
                <div>
                  <Button
                    variant="secondary"
                    fullWidth
                    icon={<Github className="h-4 w-4" />}
                    onClick={() => setShowGitHubImport(true)}
                  >
                    Link Repository
                  </Button>
                </div>
              </div>
            )}

            {activeTab === 'analysis' && (
              <div className="space-y-4">
                <Alert type="info" title="Project Analysis">
                  Validate code, run tests, analyze structure, and get code review recommendations.
                </Alert>
                <Button
                  variant="primary"
                  fullWidth
                  onClick={() => window.location.href = `/projects/${projectId}/analysis`}
                >
                  Open Analysis Panel
                </Button>
              </div>
            )}

            {activeTab === 'team' && (
              <div className="space-y-4">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    Team Members ({collaborators.length})
                  </h4>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => window.location.href = `/collaboration`}
                  >
                    Add Member
                  </Button>
                </div>

                {collaborators.length > 0 ? (
                  <div className="space-y-2">
                    {collaborators.map((collab) => (
                      <div
                        key={collab.username}
                        className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                      >
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {collab.username}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Joined {new Date(collab.joined_at).toLocaleDateString()}
                          </p>
                        </div>
                        <Badge variant="secondary">{collab.role}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    icon={<Users className="h-12 w-12" />}
                    title="No team members"
                    description="Add team members to collaborate on this project"
                  />
                )}
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="space-y-6">
                <Card>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Project Details
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Project Name
                      </label>
                      <p className="text-gray-900 dark:text-white font-medium">
                        {currentProject.name}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Created
                      </label>
                      <p className="text-gray-600 dark:text-gray-400">
                        {new Date(currentProject.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Last Updated
                      </label>
                      <p className="text-gray-600 dark:text-gray-400">
                        {new Date(currentProject.updated_at).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Current Phase
                      </label>
                      <Badge variant="primary">{phaseNames[currentProject.phase]}</Badge>
                    </div>
                  </div>
                </Card>

                <Card>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Danger Zone
                  </h3>
                  <div className="space-y-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-sm text-red-700 dark:text-red-200">
                      Deleting this project is permanent and cannot be undone.
                    </p>
                    <Button
                      variant="secondary"
                      className="text-red-600 hover:bg-red-100 dark:hover:bg-red-900"
                      onClick={() => setShowDeleteConfirm(true)}
                    >
                      Delete Project
                    </Button>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </Card>

        {/* GitHub Import Modal */}
        <GitHubImportModal
          isOpen={showGitHubImport}
          onClose={() => setShowGitHubImport(false)}
          onSuccess={() => {
            setShowGitHubImport(false);
            setActiveTab('github');
          }}
        />

        {/* Edit Project Modal */}
        <EditProjectModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          project={currentProject}
          onSubmit={async (data) => {
            if (!projectId) return;
            try {
              await updateProject(projectId, data.name);
              setShowEditModal(false);
            } catch (error) {
              console.error('Failed to update project:', error);
            }
          }}
          isLoading={projectLoading}
        />

        {/* Delete Confirmation */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <Card className="max-w-md">
              <h2 className="text-lg font-bold mb-2">Delete Project</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                This action is permanent. All data will be deleted.
              </p>
              <div className="flex gap-2 justify-end">
                <Button
                  variant="secondary"
                  onClick={() => setShowDeleteConfirm(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="secondary"
                  className="text-red-600"
                  onClick={handleConfirmDelete}
                >
                  Delete
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </MainLayout>
  );
};
