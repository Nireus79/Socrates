/**
 * Server Control Buttons - Shutdown and status display
 *
 * Displays server status (online/offline) and provides a shutdown button
 * with confirmation modal.
 */
import { useState, useEffect } from 'react';
import { Power, X, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from './interactive/Button';
import { Modal } from './dialog/Modal';
import { apiClient } from '../../api/client';

interface ServerControlsProps {
  className?: string;
}

interface ShutdownStatus {
  scheduled: boolean;
  remaining_seconds: number | null;
}

type ServerStatus = 'online' | 'offline' | 'unknown';

export function ServerControls({ className }: ServerControlsProps) {
  const [isShutdownModalOpen, setIsShutdownModalOpen] = useState(false);
  const [isShuttingDown, setIsShuttingDown] = useState(false);
  const [serverStatus, setServerStatus] = useState<ServerStatus>('unknown');
  const [shutdownRemaining, setShutdownRemaining] = useState<number | null>(null);

  // Check server status periodically
  useEffect(() => {
    const checkStatus = async () => {
      try {
        // Check if server is online
        await apiClient.get('/health');
        setServerStatus('online');

        // Check if shutdown is scheduled
        try {
          const shutdownStatus = await apiClient.get<ShutdownStatus>(
            '/system/shutdown/status'
          );
          if (shutdownStatus.scheduled) {
            setShutdownRemaining(shutdownStatus.remaining_seconds);
          } else {
            setShutdownRemaining(null);
          }
        } catch (error) {
          // Shutdown status endpoint might fail if auth not available
          setShutdownRemaining(null);
        }
      } catch (error) {
        setServerStatus('offline');
        setShutdownRemaining(null);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 5000); // Check every 5 seconds

    return () => clearInterval(interval);
  }, []);

  const handleShutdownClick = () => {
    setIsShutdownModalOpen(true);
  };

  const handleConfirmShutdown = async () => {
    setIsShuttingDown(true);
    try {
      await apiClient.post('/system/shutdown', null, {
        params: { delay_seconds: 5 },
      });
      setIsShutdownModalOpen(false);
      // Update status to show shutdown is scheduled
      setShutdownRemaining(5);
    } catch (error) {
      console.error('Failed to shutdown server:', error);
      alert('Failed to shutdown server');
    } finally {
      setIsShuttingDown(false);
    }
  };

  /**
   * Status indicator showing server status with appropriate icon
   */
  const StatusIndicator = () => {
    if (shutdownRemaining !== null && shutdownRemaining > 0) {
      return (
        <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400">
          <AlertCircle size={16} />
          <span className="text-sm font-medium">
            Shutdown in {shutdownRemaining}s
          </span>
        </div>
      );
    }

    if (serverStatus === 'online') {
      return (
        <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
          <CheckCircle size={16} />
          <span className="text-sm font-medium">Server Online</span>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
        <X size={16} />
        <span className="text-sm font-medium">Server Offline</span>
      </div>
    );
  };

  return (
    <div className={`flex items-center gap-4 ${className || ''}`}>
      <StatusIndicator />

      <Button
        variant="danger"
        size="sm"
        icon={<Power size={16} />}
        onClick={handleShutdownClick}
        disabled={serverStatus !== 'online'}
      >
        Shutdown Server
      </Button>

      {/* Confirmation Modal */}
      <Modal
        isOpen={isShutdownModalOpen}
        onClose={() => setIsShutdownModalOpen(false)}
        title="Confirm Server Shutdown"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-700 dark:text-gray-300">
            Are you sure you want to shutdown the Socrates server?
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            The server will shutdown after 5 seconds. You'll need to restart it
            manually from the command line.
          </p>

          <div className="flex gap-3 justify-end pt-4">
            <Button
              variant="secondary"
              onClick={() => setIsShutdownModalOpen(false)}
              disabled={isShuttingDown}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleConfirmShutdown}
              isLoading={isShuttingDown}
            >
              Shutdown
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
