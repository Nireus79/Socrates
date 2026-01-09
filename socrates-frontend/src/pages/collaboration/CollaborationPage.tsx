/**
 * CollaborationPage - Team collaboration and activity tracking with real-time features
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { useCollaborationStore, useProjectStore, useSubscriptionStore, useAuthStore } from '../../stores';
import { showSuccess, showError, showInfo } from '../../stores/notificationStore';
import { MainLayout, PageHeader } from '../../components/layout';
import {
  CollaboratorList,
  AddCollaboratorModal,
  ActivityFeed,
} from '../../components/collaboration';
import InvitationManager from '../../components/collaboration/InvitationManager';
import PresencePanel from '../../components/collaboration/PresencePanel';
import type {
  Activity,
} from '../../components/collaboration';
import type { Collaborator } from '../../types/models';
import { Card, Button, Tab, Alert, LoadingSpinner, SkeletonList, SkeletonCard, ErrorBoundary } from '../../components/common';
import {
  createCollaborationWebSocketClient,
  closeCollaborationWebSocket,
} from '../../services/collaborationWebSocket';

export const CollaborationPage: React.FC = () => {
  const { projectId } = useParams<{ projectId?: string }>();
  const { currentProject, projects, getProject, listProjects, isLoading: projectLoading } = useProjectStore();
  const { hasFeature } = useSubscriptionStore();
  const [selectedProjectId, setSelectedProjectId] = React.useState(projectId || '');
  const {
    collaborators,
    invitations,
    isLoading: collabLoading,
    error: collabError,
    loadCollaborators,
    addCollaborator,
    updateCollaboratorRole,
    removeCollaborator,
    clearError,
  } = useCollaborationStore();

  // Check if collaboration feature is available
  if (!hasFeature('collaboration')) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-screen">
          <Card className="max-w-md text-center">
            <h2 className="text-2xl font-bold mb-2">Premium Feature</h2>
            <p className="text-gray-600 mb-4">
              Team collaboration is available on Pro and Enterprise plans.
            </p>
            <Button variant="primary" onClick={() => window.location.href = '/settings?tab=subscription'}>
              Upgrade Now
            </Button>
          </Card>
        </div>
      </MainLayout>
    );
  }

  const [showAddModal, setShowAddModal] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState('team');
  const [collabToRemove, setCollabToRemove] = React.useState<string | null>(null);
  const [showRemoveConfirm, setShowRemoveConfirm] = React.useState(false);
  const [isRemoving, setIsRemoving] = React.useState(false);
  const { activities, fetchActivities } = useCollaborationStore();

  // Load projects list on mount
  React.useEffect(() => {
    listProjects();
  }, [listProjects]);

  // Load collaboration data
  React.useEffect(() => {
    if (selectedProjectId) {
      getProject(selectedProjectId);
      loadCollaborators(selectedProjectId);
      fetchActivities(selectedProjectId);
    }
  }, [selectedProjectId, getProject, loadCollaborators, fetchActivities]);

  // WebSocket connection management
  React.useEffect(() => {
    if (!selectedProjectId || !hasFeature('collaboration')) {
      closeCollaborationWebSocket();
      return;
    }

    const { token } = useAuthStore.getState();
    if (!token) return;

    try {
      const wsClient = createCollaborationWebSocketClient(token, selectedProjectId);
      wsClient.connect().catch((error) => {
        console.error('Failed to connect to collaboration WebSocket:', error);
      });

      // Listen for activity broadcasts and update feed
      const handleActivityBroadcast = (data: any) => {
        fetchActivities(selectedProjectId);
      };

      wsClient.on('activity', handleActivityBroadcast);

      // Cleanup on unmount or project change
      return () => {
        wsClient.off('activity', handleActivityBroadcast);
        closeCollaborationWebSocket();
      };
    } catch (error) {
      console.error('Error setting up WebSocket:', error);
    }
  }, [selectedProjectId, hasFeature('collaboration'), fetchActivities]);

  // Handle project selection change
  const handleProjectChange = (newProjectId: string) => {
    setSelectedProjectId(newProjectId);
  };

  const pendingInvitationCount = invitations.filter((inv) => inv.status === 'pending').length;

  const tabs = [
    { label: 'Team Members', value: 'team' },
    { label: 'Activity', value: 'activity' },
    { label: 'Presence', value: 'presence' },
    { label: `Invitations (${pendingInvitationCount})`, value: 'invitations' },
  ];

  const handleAddCollaborator = async (email: string, role: string) => {
    if (!selectedProjectId) return;
    try {
      await addCollaborator(selectedProjectId, email, role as any);
      setShowAddModal(false);
      // Refresh activities from backend
      await fetchActivities(selectedProjectId);
      showSuccess('Collaborator Added', `${email} has been invited to the project`);
    } catch (error) {
      console.error('Failed to add collaborator:', error);
      showError('Failed to Add Collaborator', 'There was an error adding the collaborator. Please try again.');
    }
  };

  const handleChangeRole = async (username: string, newRole: string) => {
    if (!selectedProjectId) return;
    try {
      await updateCollaboratorRole(selectedProjectId, username, newRole as any);
      showSuccess('Role Updated', `${username}'s role has been changed to ${newRole}`);
    } catch (error) {
      console.error('Failed to change role:', error);
      showError('Failed to Update Role', 'There was an error updating the role. Please try again.');
    }
  };

  const handleRemoveClick = (username: string) => {
    setCollabToRemove(username);
    setShowRemoveConfirm(true);
  };

  const handleConfirmRemove = async () => {
    if (!selectedProjectId || !collabToRemove) return;
    try {
      setIsRemoving(true);
      await removeCollaborator(selectedProjectId, collabToRemove);
      // Refresh activities from backend
      await fetchActivities(selectedProjectId);
      setShowRemoveConfirm(false);
      const removedUser = collabToRemove;
      setCollabToRemove(null);
      showSuccess('Collaborator Removed', `${removedUser} has been removed from the project`);
    } catch (error) {
      console.error('Failed to remove collaborator:', error);
      showError('Failed to Remove Collaborator', 'There was an error removing the collaborator. Please try again.');
    } finally {
      setIsRemoving(false);
    }
  };

  const isLoading = projectLoading || collabLoading;
  // Filter out undefined/null collaborators
  const validCollaborators = collaborators.filter((c) => c !== undefined && c !== null);
  const onlineCount = validCollaborators.filter((c) => c.status === 'active').length;

  if (collabError) {
    return (
      <MainLayout>
        <Alert type="error" title="Collaboration Error">
          <p className="mb-3">{collabError}</p>
          <button
            onClick={() => clearError()}
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            Dismiss
          </button>
        </Alert>
      </MainLayout>
    );
  }

  if (isLoading && validCollaborators.length === 0) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <LoadingSpinner size="lg" />
        </div>
      </MainLayout>
    );
  }

  return (
    <ErrorBoundary>
      <MainLayout>
        <div className="space-y-6">
        {/* Project Selector */}
        {projects.length > 0 && (
          <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 dark:from-blue-900 dark:to-indigo-900 dark:border-blue-800">
            <div className="flex items-center gap-3">
              <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">
                Select Project:
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => handleProjectChange(e.target.value)}
                disabled={projectLoading}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
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
        )}

        {/* Header */}
        <PageHeader
          title={currentProject ? `${currentProject.name} - Collaboration` : 'Collaboration'}
          description="Manage your team and track project activity"
          breadcrumbs={[
            { label: 'Dashboard', onClick: () => window.location.href = '/dashboard' },
            { label: 'Collaboration' },
          ]}
          actions={
            <Button
              variant="primary"
              icon={<Plus className="h-4 w-4" />}
              onClick={() => setShowAddModal(true)}
              disabled={!selectedProjectId}
            >
              Add Member
            </Button>
          }
        />

        {/* Presence Summary */}
        <Card>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Members</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {validCollaborators.length}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Online Now</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {onlineCount}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Pending Invites</p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {pendingInvitationCount}
              </p>
            </div>
          </div>
        </Card>

        {/* Tabs */}
        <Card>
          <Tab
            tabs={tabs}
            activeTab={activeTab}
            onChange={setActiveTab}
            variant="default"
          />
        </Card>

        {/* Team Members Tab */}
        {activeTab === 'team' && (
          <>
            {isLoading && validCollaborators.length === 0 ? (
              <SkeletonList count={3} height="80px" />
            ) : (
              <CollaboratorList
                collaborators={validCollaborators as Collaborator[]}
                isLoading={isLoading}
                canManage={true}
                onChangeRole={(username: string, role: string) => handleChangeRole(username, role)}
                onRemove={(username: string) => handleRemoveClick(username)}
              />
            )}
          </>
        )}

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <>
            {isLoading && activities.length === 0 ? (
              <SkeletonList count={5} height="100px" />
            ) : (
              <ActivityFeed activities={activities as Activity[]} isLoading={isLoading} />
            )}
          </>
        )}

        {/* Presence Tab */}
        {activeTab === 'presence' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Member Status
                  </h3>

                  {validCollaborators.map((collab: any) => (
                    <div
                      key={collab.username}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div className="relative">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-semibold text-sm">
                            {collab.username.charAt(0).toUpperCase()}
                          </div>
                          <div className={`absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white dark:border-gray-800 ${
                            collab.status === 'active' ? 'bg-green-500' : collab.status === 'idle' ? 'bg-yellow-500' : 'bg-gray-400'
                          }`} />
                        </div>

                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {collab.username}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            {collab.role}
                          </p>
                        </div>
                      </div>

                      <p className="text-xs text-gray-500 dark:text-gray-500">
                        {collab.joined_at ? new Date(collab.joined_at).toLocaleTimeString() : 'Just joined'}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            {/* Online Users Sidebar */}
            <div>
              <PresencePanel compact={false} />
            </div>
          </div>
        )}

        {/* Invitations Tab */}
        {activeTab === 'invitations' && selectedProjectId && (
          <InvitationManager projectId={selectedProjectId} />
        )}

        {/* Info Alert */}
        <Alert type="info" title="Real-time Collaboration">
          Changes made by team members are synced in real-time when WebSocket connection is enabled.
        </Alert>
      </div>

      {/* Add Collaborator Modal */}
      <AddCollaboratorModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSubmit={handleAddCollaborator}
        isLoading={isLoading}
      />

      {/* Remove Collaborator Confirmation */}
      {showRemoveConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="max-w-md">
            <h2 className="text-lg font-bold mb-2">Remove Collaborator</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to remove {collabToRemove}? They will lose access.
            </p>
            <div className="flex gap-2 justify-end">
              <Button
                variant="secondary"
                onClick={() => setShowRemoveConfirm(false)}
              >
                Cancel
              </Button>
              <Button
                variant="secondary"
                className="text-red-600"
                onClick={handleConfirmRemove}
              >
                Remove
              </Button>
            </div>
          </Card>
        </div>
      )}
      </MainLayout>
    </ErrorBoundary>
  );
};
