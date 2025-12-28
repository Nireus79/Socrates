/**
 * PresencePanel Component
 *
 * Displays real-time online collaborators:
 * - List of online users
 * - User avatars with status indicators
 * - Last activity timestamps
 * - Typing indicators
 */

import React from 'react';
import { useCollaborationStore } from '../../stores/collaborationStore';
import OnlineIndicator from './OnlineIndicator';

interface PresencePanelProps {
  compact?: boolean;
}

export default function PresencePanel({ compact = false }: PresencePanelProps) {
  const { activeUsers, typingUsers } = useCollaborationStore();

  const users = Array.from(activeUsers.values());

  if (compact) {
    // Compact view: just show avatars
    return (
      <div className="flex items-center gap-2">
        {users.map((user) => (
          <div key={user.username} className="relative group">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-xs font-semibold">
              {user.username.charAt(0).toUpperCase()}
            </div>
            <OnlineIndicator status={user.status} />
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 dark:bg-gray-700 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
              {user.username}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Full view
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            Online Users
          </h3>
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
            {users.length} online
          </span>
        </div>

        {users.length === 0 ? (
          <div className="text-center py-6">
            <svg
              className="mx-auto h-8 w-8 text-gray-400 dark:text-gray-500 mb-2"
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
            <p className="text-xs text-gray-500 dark:text-gray-400">No other users online</p>
          </div>
        ) : (
          <div className="space-y-2">
            {users.map((user) => (
              <div
                key={user.username}
                className="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded transition-colors"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  {/* Avatar */}
                  <div className="relative flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-xs font-semibold">
                      {user.username.charAt(0).toUpperCase()}
                    </div>
                    <OnlineIndicator status={user.status} />
                  </div>

                  {/* Username and status */}
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {user.username}
                    </p>
                    {typingUsers.has(user.username) ? (
                      <p className="text-xs text-blue-600 dark:text-blue-400 flex items-center gap-1">
                        <span>typing</span>
                        <span className="flex gap-0.5">
                          <span className="w-1 h-1 bg-blue-600 dark:bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                          <span className="w-1 h-1 bg-blue-600 dark:bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                          <span className="w-1 h-1 bg-blue-600 dark:bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                        </span>
                      </p>
                    ) : (
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {user.last_seen ? `Active ${new Date(user.last_seen).toLocaleTimeString()}` : 'Active'}
                      </p>
                    )}
                  </div>
                </div>

                {/* Status badge */}
                <span
                  className={`ml-2 px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ${
                    user.status === 'active'
                      ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                      : user.status === 'idle'
                      ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                  }`}
                >
                  {user.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
