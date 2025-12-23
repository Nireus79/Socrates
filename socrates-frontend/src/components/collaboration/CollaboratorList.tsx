/**
 * CollaboratorList Component - Display and manage team members
 */

import React from 'react';
import { MoreVertical, Crown, Edit2, Trash2, Circle } from 'lucide-react';
import { Card, Badge, Button, Dropdown } from '../common';
import type { Collaborator } from '../../types/models';

interface CollaboratorListProps {
  collaborators: Collaborator[];
  isLoading?: boolean;
  canManage?: boolean;
  onChangeRole?: (username: string, newRole: string) => void;
  onRemove?: (username: string) => void;
}

const roleColors = {
  owner: 'primary',
  editor: 'secondary',
  viewer: 'outline',
};

const statusColors = {
  active: 'bg-green-500',
  pending: 'bg-yellow-500',
  inactive: 'bg-gray-400',
};

export const CollaboratorList: React.FC<CollaboratorListProps> = ({
  collaborators,
  isLoading = false,
  canManage = false,
  onChangeRole,
  onRemove,
}) => {
  const [expandedId, setExpandedId] = React.useState<string | null>(null);

  return (
    <Card>
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Team Members ({collaborators.length})
        </h3>

        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {collaborators.map((collaborator) => (
            <div
              key={collaborator.username}
              className="py-3 px-0 flex items-center justify-between gap-3 hover:bg-gray-50 dark:hover:bg-gray-800 -mx-0 px-0 py-3"
            >
              {/* Collaborator Info */}
              <div className="flex items-center gap-3 flex-1 min-w-0">
                {/* Avatar */}
                <div className="relative flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-semibold text-sm">
                    {collaborator.username.charAt(0).toUpperCase()}
                  </div>
                  {/* Status Indicator */}
                  <Circle
                    className={`absolute bottom-0 right-0 h-3 w-3 ${statusColors[collaborator.status]}`}
                    fill="currentColor"
                  />
                </div>

                {/* Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-medium text-gray-900 dark:text-white truncate">
                      {collaborator.username}
                    </p>
                    {collaborator.role === 'owner' && (
                      <Crown className="h-4 w-4 text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
                    )}
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                    Joined {new Date(collaborator.joined_at).toLocaleDateString()}
                  </p>
                  {collaborator.last_activity && (
                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                      Last active {new Date(collaborator.last_activity).toLocaleTimeString()}
                    </p>
                  )}
                </div>
              </div>

              {/* Role Badge */}
              <Badge variant={roleColors[collaborator.role] as any} size="sm" className="flex-shrink-0">
                {collaborator.role}
              </Badge>

              {/* Actions */}
              {canManage && collaborator.role !== 'owner' && (
                <div className="flex-shrink-0">
                  <Dropdown
                    isOpen={expandedId === collaborator.username}
                    onClose={() => setExpandedId(null)}
                    trigger={
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedId(expandedId === collaborator.username ? null : collaborator.username);
                        }}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      >
                        <MoreVertical className="h-4 w-4" />
                      </button>
                    }
                  >
                    {onChangeRole && (
                      <>
                        <button
                          onClick={() => {
                            onChangeRole(collaborator.username, 'editor');
                            setExpandedId(null);
                          }}
                          className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                          <Edit2 className="h-3 w-3 inline mr-2" />
                          Make Editor
                        </button>
                        <button
                          onClick={() => {
                            onChangeRole(collaborator.username, 'viewer');
                            setExpandedId(null);
                          }}
                          className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                          <Edit2 className="h-3 w-3 inline mr-2" />
                          Make Viewer
                        </button>
                      </>
                    )}
                    {onRemove && (
                      <>
                        <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                        <button
                          onClick={() => {
                            onRemove(collaborator.username);
                            setExpandedId(null);
                          }}
                          className="w-full text-left px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900"
                        >
                          <Trash2 className="h-3 w-3 inline mr-2" />
                          Remove
                        </button>
                      </>
                    )}
                  </Dropdown>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

CollaboratorList.displayName = 'CollaboratorList';
