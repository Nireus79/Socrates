/**
 * Collaboration WebSocket Service
 *
 * Handles real-time collaboration features:
 * - User presence (online/offline)
 * - Typing indicators
 * - Activity broadcasts
 * - Heartbeat keep-alive
 * - Auto-reconnect with exponential backoff
 * - Message queue for offline scenarios
 */

type EventCallback = (data: any) => void;
type EventType = 'user_joined' | 'user_left' | 'typing' | 'activity' | 'presence_update' | 'error' | 'connected' | 'disconnected';

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
}

export class CollaborationWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string;
  private projectId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageQueue: WebSocketMessage[] = [];
  private eventListeners: Map<EventType, Set<EventCallback>> = new Map();
  private isConnecting = false;
  private isManualClose = false;

  constructor(token: string, projectId: string, baseUrl = 'ws://localhost:8000') {
    this.token = token;
    this.projectId = projectId;
    this.url = `${baseUrl}/ws/collaboration/${projectId}`;
  }

  /**
   * Connect to WebSocket
   */
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting) {
        reject(new Error('Connection already in progress'));
        return;
      }

      this.isConnecting = true;
      this.isManualClose = false;

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;

          // Send auth message
          this.sendMessage({
            type: 'authenticate',
            data: { token: this.token },
          });

          // Start heartbeat
          this.startHeartbeat();

          // Flush queued messages
          this.flushMessageQueue();

          // Emit connected event
          this.emit('connected', {});

          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data) as WebSocketMessage;
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          this.emit('error', { error: 'WebSocket connection error' });
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket closed');
          this.isConnecting = false;
          this.ws = null;
          this.stopHeartbeat();

          // Emit disconnected event
          this.emit('disconnected', {});

          // Auto-reconnect if not manually closed
          if (!this.isManualClose) {
            this.attemptReconnect();
          }
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket
   */
  public disconnect(): void {
    this.isManualClose = true;
    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Send message through WebSocket
   */
  public sendMessage(message: WebSocketMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message if not connected
      this.messageQueue.push(message);
    }
  }

  /**
   * Send heartbeat keep-alive message
   */
  public sendHeartbeat(): void {
    this.sendMessage({
      type: 'heartbeat',
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Send typing indicator
   */
  public sendTypingIndicator(isTyping: boolean): void {
    this.sendMessage({
      type: 'typing',
      data: { is_typing: isTyping },
    });
  }

  /**
   * Broadcast activity
   */
  public sendActivity(activityType: string, data?: any): void {
    this.sendMessage({
      type: 'activity',
      data: {
        activity_type: activityType,
        activity_data: data,
      },
    });
  }

  /**
   * Listen to WebSocket events
   */
  public on(event: EventType, callback: EventCallback): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event)!.add(callback);
  }

  /**
   * Stop listening to events
   */
  public off(event: EventType, callback: EventCallback): void {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event)!.delete(callback);
    }
  }

  /**
   * Get connection status
   */
  public isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  // ========== Private Methods ==========

  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'user_joined':
        this.emit('user_joined', message.data);
        break;
      case 'user_left':
        this.emit('user_left', message.data);
        break;
      case 'typing':
        this.emit('typing', message.data);
        break;
      case 'activity':
        this.emit('activity', message.data);
        break;
      case 'presence_update':
        this.emit('presence_update', message.data);
        break;
      case 'error':
        this.emit('error', message.data);
        break;
      default:
        console.warn('Unknown message type:', message.type);
    }
  }

  private emit(event: EventType, data: any): void {
    const callbacks = this.eventListeners.get(event);
    if (callbacks) {
      callbacks.forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.sendHeartbeat();
      }
    }, 30000); // Send heartbeat every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.sendMessage(message);
      }
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      this.emit('error', { error: 'Failed to reconnect after multiple attempts' });
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnect failed:', error);
      });
    }, delay);
  }
}

/**
 * Create a singleton instance for the current project
 */
let instance: CollaborationWebSocketClient | null = null;

export function createCollaborationWebSocketClient(token: string, projectId: string): CollaborationWebSocketClient {
  // Clean up old instance if exists
  if (instance) {
    instance.disconnect();
  }

  instance = new CollaborationWebSocketClient(token, projectId);
  return instance;
}

export function getCollaborationWebSocketClient(): CollaborationWebSocketClient | null {
  return instance;
}

export function closeCollaborationWebSocket(): void {
  if (instance) {
    instance.disconnect();
    instance = null;
  }
}
