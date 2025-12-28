/**
 * AcceptInvitationPage
 *
 * Page for accepting project invitations via token
 * URL: /invitations/accept/:token
 *
 * Handles:
 * - Extracting token from URL
 * - Displaying invitation details
 * - Accepting the invitation
 * - Redirecting to project on success
 * - Error handling if token is invalid/expired
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCollaborationStore } from '../../stores/collaborationStore';
import { useAuthStore } from '../../stores/authStore';
import type { AcceptInvitationResponse } from '../../types/models';

export default function AcceptInvitationPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const { acceptInvitation, isLoadingInvitations, invitationError, clearInvitationError } =
    useCollaborationStore();
  const { user } = useAuthStore();

  const [isAccepting, setIsAccepting] = useState(false);
  const [acceptanceError, setAcceptanceError] = useState<string | null>(null);
  const [acceptanceSuccess, setAcceptanceSuccess] = useState(false);
  const [invitationDetails, setInvitationDetails] = useState<AcceptInvitationResponse | null>(null);

  // Validate token format
  useEffect(() => {
    if (!token) {
      setAcceptanceError('Invalid invitation link. Token is missing.');
    }
  }, [token]);

  // Handle acceptance
  const handleAcceptInvitation = async () => {
    if (!token) return;

    setIsAccepting(true);
    setAcceptanceError(null);

    try {
      const response = await acceptInvitation(token);
      setAcceptanceSuccess(true);
      setInvitationDetails(response as AcceptInvitationResponse);

      // Redirect to project after 2 seconds
      setTimeout(() => {
        if (response?.project?.project_id) {
          navigate(`/projects/${response.project.project_id}`);
        } else {
          navigate('/projects');
        }
      }, 2000);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to accept invitation';
      setAcceptanceError(message);
    } finally {
      setIsAccepting(false);
    }
  };

  // If no token, show error
  if (!token) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-8">
          <div className="flex justify-center mb-6">
            <svg className="h-12 w-12 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4v2m0 0a4 4 0 100-8 4 4 0 000 8z"
              />
            </svg>
          </div>
          <h1 className="text-center text-2xl font-bold text-gray-900 mb-2">Invalid Invitation Link</h1>
          <p className="text-center text-gray-600 mb-6">
            The invitation link is invalid or missing. Please check the link and try again.
          </p>
          <button
            onClick={() => navigate('/projects')}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          >
            Back to Projects
          </button>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoadingInvitations || isAccepting) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-8 text-center">
          <div className="flex justify-center mb-6">
            <div className="animate-spin h-12 w-12 border-4 border-blue-600 border-transparent rounded-full border-t-blue-600" />
          </div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Processing Your Invitation</h1>
          <p className="text-gray-600">Please wait while we process your invitation...</p>
        </div>
      </div>
    );
  }

  // Success state
  if (acceptanceSuccess) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-8">
          <div className="flex justify-center mb-6">
            <svg className="h-12 w-12 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h1 className="text-center text-2xl font-bold text-gray-900 mb-2">Invitation Accepted!</h1>
          <p className="text-center text-gray-600 mb-4">
            {invitationDetails?.project?.name && (
              <>
                You've been added to <strong>{invitationDetails.project.name}</strong> as an{' '}
                <strong>{invitationDetails.member?.role}</strong>.
              </>
            )}
          </p>
          <p className="text-center text-sm text-gray-500 mb-6">
            Redirecting you to the project in a moment...
          </p>
          <button
            onClick={() => {
              if (invitationDetails?.project?.project_id) {
                navigate(`/projects/${invitationDetails.project.project_id}`);
              } else {
                navigate('/projects');
              }
            }}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          >
            Go to Project Now
          </button>
        </div>
      </div>
    );
  }

  // Error state
  if (acceptanceError || invitationError) {
    const error = acceptanceError || invitationError;
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-8">
          <div className="flex justify-center mb-6">
            <svg className="h-12 w-12 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h1 className="text-center text-2xl font-bold text-gray-900 mb-2">Unable to Accept Invitation</h1>
          <p className="text-center text-gray-600 mb-6">{error}</p>
          <div className="space-y-3">
            <button
              onClick={handleAcceptInvitation}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Try Again
            </button>
            <button
              onClick={() => navigate('/projects')}
              className="w-full px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-900 rounded-lg transition-colors font-medium"
            >
              Back to Projects
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Pending acceptance state
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-8">
        <div className="flex justify-center mb-6">
          <svg className="h-12 w-12 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1m2-1v2.5M2 7l2-1 2 1M4 7v2.5M12 15l-2 1m0 0l-2-1m2 1v2.5m6-5l-2 1m2-1l-2-1m2 1v2.5m-6 5l2-1 2 1m-2-1v2.5"
            />
          </svg>
        </div>
        <h1 className="text-center text-2xl font-bold text-gray-900 mb-2">You've Been Invited!</h1>
        <p className="text-center text-gray-600 mb-8">
          {user ? (
            <>
              Click below to accept the invitation and join the project as a collaborator.
            </>
          ) : (
            <>
              You need to be logged in to accept this invitation. Please log in first.
            </>
          )}
        </p>

        <div className="space-y-3">
          <button
            onClick={handleAcceptInvitation}
            disabled={!user || isAccepting}
            className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
          >
            {isAccepting ? 'Accepting...' : 'Accept Invitation'}
          </button>

          {!user && (
            <button
              onClick={() => navigate('/auth/login')}
              className="w-full px-4 py-3 bg-gray-200 hover:bg-gray-300 text-gray-900 rounded-lg transition-colors font-medium"
            >
              Log In First
            </button>
          )}

          <button
            onClick={() => navigate('/projects')}
            className="w-full px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors font-medium"
          >
            Cancel
          </button>
        </div>

        {invitationError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{invitationError}</p>
            <button
              onClick={clearInvitationError}
              className="mt-2 text-xs text-red-600 hover:text-red-800 font-medium"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
