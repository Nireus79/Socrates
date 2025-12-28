/**
 * InvitationManager Component
 *
 * Displays pending invitations for a project and allows:
 * - Creating new invitations
 * - Canceling pending invitations
 * - Viewing invitation details (email, role, status, expiration)
 */

import React, { useEffect, useState } from 'react';
import { useCollaborationStore } from '../../stores/collaborationStore';
import type { Invitation, CollaboratorRole } from '../../types/models';
import InviteModal from './InviteModal';

interface InvitationManagerProps {
  projectId: string;
  onInvitationCreated?: (invitation: Invitation) => void;
  onInvitationCanceled?: (invitationId: string) => void;
}

export default function InvitationManager({
  projectId,
  onInvitationCreated,
  onInvitationCanceled,
}: InvitationManagerProps) {
  const {
    invitations,
    isLoadingInvitations,
    invitationError,
    loadInvitations,
    cancelInvitation,
    createInvitation,
    clearInvitationError,
  } = useCollaborationStore();

  const [showInviteModal, setShowInviteModal] = useState(false);
  const [cancelingId, setCancelingId] = useState<string | null>(null);
  const [cancelConfirm, setCancelConfirm] = useState(false);

  // Load invitations on mount
  useEffect(() => {
    loadInvitations(projectId);
  }, [projectId, loadInvitations]);

  const handleInviteSubmit = async (email: string, role: CollaboratorRole) => {
    try {
      await createInvitation(projectId, email, role);
      setShowInviteModal(false);
      onInvitationCreated?.(invitations[invitations.length - 1]);
    } catch (error) {
      console.error('Failed to create invitation:', error);
    }
  };

  const handleCancelInvitation = async (invitationId: string) => {
    try {
      await cancelInvitation(projectId, invitationId);
      onInvitationCanceled?.(invitationId);
      setCancelingId(null);
      setCancelConfirm(false);
    } catch (error) {
      console.error('Failed to cancel invitation:', error);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'accepted':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      case 'expired':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner':
        return 'bg-purple-100 text-purple-800';
      case 'editor':
        return 'bg-blue-100 text-blue-800';
      case 'viewer':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return 'N/A';
    }
  };

  return (
    <div className="space-y-4">
      {/* Header with button */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Pending Invitations</h3>
        <button
          onClick={() => setShowInviteModal(true)}
          className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <span className="mr-2">+</span>
          Invite Member
        </button>
      </div>

      {/* Error message */}
      {invitationError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start justify-between">
          <div className="flex-1">
            <h4 className="text-sm font-medium text-red-900">Error</h4>
            <p className="text-sm text-red-700 mt-1">{invitationError}</p>
          </div>
          <button
            onClick={clearInvitationError}
            className="text-red-400 hover:text-red-600 ml-4"
          >
            ✕
          </button>
        </div>
      )}

      {/* Invitations table or empty state */}
      {isLoadingInvitations ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 rounded animate-pulse" />
          ))}
        </div>
      ) : invitations.length === 0 ? (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
            />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No pending invitations</h3>
          <p className="mt-2 text-sm text-gray-500">
            Invite team members to collaborate on this project.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                  Sent On
                </th>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                  Expires
                </th>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {invitations.map((invitation) => (
                <tr key={invitation.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {invitation.invitee_email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(invitation.role)}`}
                    >
                      {invitation.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(invitation.status)}`}
                    >
                      {invitation.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(invitation.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(invitation.expires_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      {invitation.status === 'pending' && (
                        <>
                          {cancelingId === invitation.id && cancelConfirm ? (
                            <>
                              <button
                                onClick={() => handleCancelInvitation(invitation.id)}
                                disabled={isLoadingInvitations}
                                className="inline-flex items-center px-2 py-1 bg-red-100 hover:bg-red-200 text-red-800 rounded text-xs font-medium transition-colors disabled:opacity-50"
                              >
                                {isLoadingInvitations ? 'Canceling...' : 'Confirm'}
                              </button>
                              <button
                                onClick={() => {
                                  setCancelingId(null);
                                  setCancelConfirm(false);
                                }}
                                disabled={isLoadingInvitations}
                                className="inline-flex items-center px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded text-xs font-medium transition-colors disabled:opacity-50"
                              >
                                Cancel
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => {
                                setCancelingId(invitation.id);
                                setCancelConfirm(true);
                              }}
                              disabled={isLoadingInvitations}
                              className="inline-flex items-center px-2 py-1 bg-red-50 hover:bg-red-100 text-red-700 rounded text-xs font-medium transition-colors disabled:opacity-50"
                            >
                              Revoke
                            </button>
                          )}
                        </>
                      )}
                      {invitation.status !== 'pending' && (
                        <span className="text-xs text-gray-500">—</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Invite Modal */}
      {showInviteModal && (
        <InviteModal
          onSubmit={handleInviteSubmit}
          onClose={() => setShowInviteModal(false)}
          isLoading={isLoadingInvitations}
        />
      )}
    </div>
  );
}
