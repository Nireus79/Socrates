/**
 * CollaborationPage - Team collaboration and activity tracking
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { useCollaborationStore, useProjectStore, useSubscriptionStore } from '../../stores';
import { MainLayout, PageHeader } from '../../components/layout';
import {
  CollaboratorList,
  AddCollaboratorModal,
  ActivityFeed,
} from '../../components/collaboration';
import type {
  Activity,
} from '../../components/collaboration';
import type { Collaborator } from '../../types/models';
import { Card, Button, Tab, Alert, LoadingSpinner } from '../../components/common';

export const CollaborationPage: React.FC = () => {
  const { projectId } = useParams<{ projectId?: string }>();
  const { currentProject, getProject, isLoading: projectLoading } = useProjectStore();
  const { hasFeature } = useSubscriptionStore();
  const {
    collaborators,
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

  // Load collaboration data
  React.useEffect(() => {
    if (projectId) {
      getProject(projectId);
      loadCollaborators(projectId);
      fetchActivities(projectId);
    }
  }, [projectId, getProject, loadCollaborators, fetchActivities]);

  const tabs = [
    { label: 'Team Members', value: 'team' },
    { label: 'Activity', value: 'activity' },
    { label: 'Presence', value: 'presence' },
  ];

  const handleAddCollaborator = async (email: string, role: string) => {
    if (!projectId) return;
    try {
      await addCollaborator(projectId, email.split('@')[0], role as any);
      setShowAddModal(false);
      // Refresh activities from backend
      await fetchActivities(projectId);
    } catch (error) {
      console.error('Failed to add collaborator:', error);
    }
  };

  const handleChangeRole = async (username: string, newRole: string) => {
    if (!projectId) return;
    try {
      await updateCollaboratorRole(projectId, username, newRole as any);
    } catch (error) {
      console.error('Failed to change role:', error);
    }
  };

  const handleRemoveClick = (username: string) => {
    setCollabToRemove(username);
    setShowRemoveConfirm(true);
  };

  const handleConfirmRemove = async () => {
    if (!projectId || !collabToRemove) return;
    try {
      setIsRemoving(true);
      await removeCollaborator(projectId, collabToRemove);
      // Refresh activities from backend
      await fetchActivities(projectId);
      setShowRemoveConfirm(false);
      setCollabToRemove(null);
    } catch (error) {
      console.error('Failed to remove collaborator:', error);
    } finally {
      setIsRemoving(false);
    }
  };

  const isLoading = projectLoading || collabLoading;
  const onlineCount = collaborators.filter((c) => c.status === 'active').length;

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

  if (isLoading && collaborators.length === 0) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <LoadingSpinner size="lg" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
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
                {collaborators.length}
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
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">0</p>
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
          <CollaboratorList
            collaborators={collaborators as Collaborator[]}
            isLoading={isLoading}
            canManage={true}
            onChangeRole={(username: string, role: string) => handleChangeRole(username, role)}
            onRemove={(username: string) => handleRemoveClick(username)}
          />
        )}

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <ActivityFeed activities={activities as Activity[]} isLoading={isLoading} />
        )}

        {/* Presence Tab */}
        {activeTab === 'presence' && (
          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Member Status
              </h3>

              {collaborators.map((collab: any) => (
                <div
                  key={collab.username}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-semibold text-sm">
                        {collab.username.charAt(0).toUpperCase()}
                      </div>
                      <div className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white dark:border-gray-800 bg-green-500" />
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
  );
};
