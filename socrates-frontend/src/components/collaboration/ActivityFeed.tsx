/**
 * ActivityFeed Component - Timeline of team activities with real-time updates
 *
 * Features:
 * - Displays team activities in chronological order
 * - Real-time updates via WebSocket
 * - New activity animations
 * - Connection status indicator
 * - Auto-scroll to newest activity
 */

import React, { useEffect, useRef } from 'react';
import {
  MessageSquare,
  Code2,
  FileText,
  Users,
  CheckCircle,
  Zap,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { Card, Badge } from '../common';
import { getCollaborationWebSocketClient } from '../../services/collaborationWebSocket';

export type ActivityType =
  | 'dialogue'
  | 'code'
  | 'note'
  | 'collaboration'
  | 'phase'
  | 'other';

export interface Activity {
  id: string;
  type: ActivityType;
  user: {
    name: string;
    avatar?: string;
  };
  action: string;
  description?: string;
  timestamp: Date;
  isNew?: boolean; // Flag for animations
}

interface ActivityFeedProps {
  activities: Activity[];
  isLoading?: boolean;
  onNewActivity?: (activity: Activity) => void;
  showConnectionStatus?: boolean;
}

const activityIcons = {
  dialogue: MessageSquare,
  code: Code2,
  note: FileText,
  collaboration: Users,
  phase: CheckCircle,
  other: Zap,
};

const activityColors = {
  dialogue: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900',
  code: 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900',
  note: 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900',
  collaboration: 'text-pink-600 dark:text-pink-400 bg-pink-50 dark:bg-pink-900',
  phase: 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900',
  other: 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900',
};

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  activities,
  isLoading = false,
  onNewActivity,
  showConnectionStatus = true,
}) => {
  const feedEndRef = useRef<HTMLDivElement>(null);
  const [wsConnected, setWsConnected] = React.useState(false);

  // Setup WebSocket listeners
  useEffect(() => {
    const ws = getCollaborationWebSocketClient();
    if (!ws) return;

    // Listen for connected event
    const handleConnected = () => {
      setWsConnected(true);
    };

    // Listen for disconnected event
    const handleDisconnected = () => {
      setWsConnected(false);
    };

    // Listen for activity events
    const handleActivityBroadcast = (data: any) => {
      if (onNewActivity) {
        const newActivity: Activity = {
          id: data.id || `activity-${Date.now()}`,
          type: (data.activity_type?.toLowerCase() as ActivityType) || 'other',
          user: { name: data.user_id || 'Unknown' },
          action: data.activity_type || data.description || 'Activity',
          description: data.activity_data?.description,
          timestamp: new Date(data.created_at || new Date()),
          isNew: true,
        };
        onNewActivity(newActivity);

        // Auto-scroll to bottom
        setTimeout(() => {
          feedEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    };

    ws.on('connected', handleConnected);
    ws.on('disconnected', handleDisconnected);
    ws.on('activity', handleActivityBroadcast);

    // Set initial connection status
    setWsConnected(ws.isConnected());

    // Cleanup
    return () => {
      ws.off('connected', handleConnected);
      ws.off('disconnected', handleDisconnected);
      ws.off('activity', handleActivityBroadcast);
    };
  }, [onNewActivity]);

  const getTimeAgo = (date: Date): string => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    const intervals = {
      year: 31536000,
      month: 2592000,
      week: 604800,
      day: 86400,
      hour: 3600,
      minute: 60,
    };

    for (const [name, secondsInInterval] of Object.entries(intervals)) {
      const interval = Math.floor(seconds / secondsInInterval);
      if (interval >= 1) {
        return `${interval} ${name}${interval > 1 ? 's' : ''} ago`;
      }
    }
    return 'just now';
  };

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Activity Feed
        </h3>
        {showConnectionStatus && (
          <div className="flex items-center gap-2">
            {wsConnected ? (
              <>
                <Wifi className="h-4 w-4 text-green-600 dark:text-green-400" />
                <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                  Live
                </span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                  Offline
                </span>
              </>
            )}
          </div>
        )}
      </div>

      {activities.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-600 dark:text-gray-400">
            No activities yet. Start collaborating to see updates here!
          </p>
        </div>
      ) : (
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {activities.map((activity) => {
            const Icon = activityIcons[activity.type];
            const colorClass = activityColors[activity.type];

            return (
              <div
                key={activity.id}
                className={`flex gap-4 pb-4 border-b border-gray-200 dark:border-gray-700 last:border-b-0 last:pb-0 transition-all ${
                  activity.isNew ? 'animate-pulse bg-blue-50 dark:bg-blue-900 p-2 rounded' : ''
                }`}
              >
                {/* Avatar */}
                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${colorClass}`}>
                  <Icon className="h-5 w-5" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-medium text-gray-900 dark:text-white">
                      {activity.user.name}
                    </p>
                    <Badge variant="secondary" size="sm">
                      {activity.type}
                    </Badge>
                    {activity.isNew && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                        New
                      </span>
                    )}
                  </div>

                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">
                    {activity.action}
                  </p>

                  {activity.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      {activity.description}
                    </p>
                  )}

                  <p className="text-xs text-gray-500 dark:text-gray-500">
                    {getTimeAgo(activity.timestamp)}
                  </p>
                </div>
              </div>
            );
          })}
          <div ref={feedEndRef} />
        </div>
      )}
    </Card>
  );
};

ActivityFeed.displayName = 'ActivityFeed';
