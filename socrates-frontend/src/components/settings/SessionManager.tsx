/**
 * Session Manager - View and manage active sessions
 */

import React from 'react';
import {
  Smartphone,
  Monitor,
  Trash2,
  LogOut,
  MapPin,
  Clock,
} from 'lucide-react';
import { Card, Badge, Button } from '../common';

interface Session {
  id: string;
  device: string;
  ip_address: string;
  last_activity: string;
  created_at: string;
  is_current: boolean;
}

interface SessionManagerProps {
  sessions: Session[];
  isLoading?: boolean;
  onRevokeSession?: (sessionId: string) => Promise<void>;
  onRevokeAllSessions?: () => Promise<void>;
}

export const SessionManager: React.FC<SessionManagerProps> = ({
  sessions,
  isLoading = false,
  onRevokeSession,
  onRevokeAllSessions,
}) => {
  const [revoking, setRevoking] = React.useState<string | null>(null);

  const handleRevokeSession = async (sessionId: string) => {
    if (
      window.confirm(
        'Are you sure? You will be signed out from this device.'
      )
    ) {
      setRevoking(sessionId);
      try {
        await onRevokeSession?.(sessionId);
      } finally {
        setRevoking(null);
      }
    }
  };

  const handleRevokeAll = async () => {
    if (
      window.confirm(
        'This will sign you out from all devices except the current one. Continue?'
      )
    ) {
      try {
        await onRevokeAllSessions?.();
      } catch (err) {
        console.error('Failed to revoke all sessions:', err);
      }
    }
  };

  const getDeviceIcon = (device: string) => {
    if (device.toLowerCase().includes('mobile') || device.toLowerCase().includes('iphone') || device.toLowerCase().includes('android')) {
      return <Smartphone className="h-5 w-5" />;
    }
    return <Monitor className="h-5 w-5" />;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Active Sessions
        </h3>
        {sessions.length > 1 && (
          <Button
            variant="secondary"
            size="sm"
            icon={<LogOut className="h-4 w-4" />}
            onClick={handleRevokeAll}
          >
            Sign Out All
          </Button>
        )}
      </div>

      <div className="space-y-3">
        {sessions.map((session) => (
          <Card
            key={session.id}
            className={
              session.is_current
                ? 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20'
                : ''
            }
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <div className="text-gray-600 dark:text-gray-400">
                    {getDeviceIcon(session.device)}
                  </div>
                  <h4 className="font-semibold text-gray-900 dark:text-white">
                    {session.device}
                  </h4>
                  {session.is_current && (
                    <Badge variant="success">Current</Badge>
                  )}
                </div>

                <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    <span>{session.ip_address}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    <span>
                      Last active: {formatDate(session.last_activity)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">
                      Added {formatDate(session.created_at)}
                    </Badge>
                  </div>
                </div>
              </div>

              {!session.is_current && (
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<Trash2 className="h-4 w-4" />}
                  onClick={() => handleRevokeSession(session.id)}
                  disabled={revoking === session.id || isLoading}
                  isLoading={revoking === session.id}
                  className="text-red-600 hover:text-red-700 dark:text-red-400"
                >
                  Revoke
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>

      {sessions.length === 0 && (
        <Card className="text-center py-8">
          <p className="text-gray-600 dark:text-gray-400">
            No active sessions
          </p>
        </Card>
      )}
    </div>
  );
};
