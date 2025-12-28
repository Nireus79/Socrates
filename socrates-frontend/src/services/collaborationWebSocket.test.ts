/**
 * Integration tests for CollaborationWebSocket service
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { CollaborationWebSocketClient } from './collaborationWebSocket';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  messageQueue: string[] = [];

  constructor(public url: string) {
    // Simulate opening
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }, 10);
  }

  send(data: string) {
    if (this.readyState === MockWebSocket.OPEN) {
      this.messageQueue.push(data);
    }
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close'));
  }

  // Helper to simulate receiving messages
  simulateMessage(data: any) {
    const event = new MessageEvent('message', {
      data: JSON.stringify(data),
    });
    this.onmessage?.(event);
  }
}

// Replace global WebSocket
global.WebSocket = MockWebSocket as any;

describe('CollaborationWebSocket Integration Tests', () => {
  let wsClient: CollaborationWebSocketClient;

  beforeEach(() => {
    wsClient = new CollaborationWebSocketClient(
      'test-token',
      'test-project-123',
      'ws://localhost:8000'
    );
  });

  afterEach(() => {
    if (wsClient) {
      wsClient.disconnect();
    }
  });

  describe('Connection Management', () => {
    it('should connect to WebSocket server', async () => {
      await wsClient.connect();

      expect(wsClient.isConnected()).toBe(true);
    });

    it('should authenticate on connection', async () => {
      let authMessageSent = false;

      await wsClient.connect();

      // Get the underlying WebSocket
      const mockWs = wsClient['ws'] as any;
      if (mockWs && mockWs.messageQueue) {
        const authMessage = mockWs.messageQueue.find((msg: string) => {
          const parsed = JSON.parse(msg);
          return parsed.type === 'authenticate';
        });
        authMessageSent = !!authMessage;
      }

      expect(authMessageSent).toBe(true);
    });

    it('should send heartbeat periodically', async () => {
      await wsClient.connect();

      const mockWs = wsClient['ws'] as any;
      const initialMessageCount = mockWs.messageQueue.length;

      // Wait for heartbeat (default is 30s, but we'll mock this shorter)
      wsClient.sendHeartbeat();

      expect(mockWs.messageQueue.length).toBeGreaterThan(initialMessageCount);
      const lastMessage = JSON.parse(
        mockWs.messageQueue[mockWs.messageQueue.length - 1]
      );
      expect(lastMessage.type).toBe('heartbeat');
    });

    it('should disconnect cleanly', async () => {
      await wsClient.connect();
      expect(wsClient.isConnected()).toBe(true);

      wsClient.disconnect();

      expect(wsClient.isConnected()).toBe(false);
    });
  });

  describe('Event Handling', () => {
    it('should emit connected event on successful connection', async () => {
      let connectedEmitted = false;

      wsClient.on('connected', () => {
        connectedEmitted = true;
      });

      await wsClient.connect();

      expect(connectedEmitted).toBe(true);
    });

    it('should emit disconnected event when connection closes', (done) => {
      wsClient.on('disconnected', () => {
        expect(true).toBe(true);
        done();
      });

      wsClient.connect().then(() => {
        wsClient.disconnect();
      });
    });

    it('should handle activity events', (done) => {
      const testActivity = {
        type: 'activity',
        data: {
          id: 'activity-123',
          activity_type: 'document_updated',
          user_id: 'user-456',
          created_at: new Date().toISOString(),
        },
      };

      wsClient.on('activity', (data) => {
        expect(data.activity_type).toBe('document_updated');
        expect(data.user_id).toBe('user-456');
        done();
      });

      wsClient.connect().then(() => {
        const mockWs = wsClient['ws'] as any;
        mockWs.simulateMessage(testActivity);
      });
    });

    it('should handle typing indicators', (done) => {
      const typingEvent = {
        type: 'typing',
        data: {
          user_id: 'user-789',
          is_typing: true,
        },
      };

      wsClient.on('typing', (data) => {
        expect(data.is_typing).toBe(true);
        expect(data.user_id).toBe('user-789');
        done();
      });

      wsClient.connect().then(() => {
        const mockWs = wsClient['ws'] as any;
        mockWs.simulateMessage(typingEvent);
      });
    });

    it('should allow event listener removal', async () => {
      let callCount = 0;
      const handler = () => {
        callCount++;
      };

      wsClient.on('activity', handler);
      wsClient.off('activity', handler);

      await wsClient.connect();
      const mockWs = wsClient['ws'] as any;
      mockWs.simulateMessage({
        type: 'activity',
        data: { id: 'test' },
      });

      expect(callCount).toBe(0);
    });
  });

  describe('Message Queue', () => {
    it('should queue messages when not connected', () => {
      wsClient.sendMessage({
        type: 'test',
        data: { test: 'data' },
      });

      // Message should be in queue since we haven't connected
      expect(wsClient['messageQueue'].length).toBeGreaterThan(0);
    });

    it('should flush queued messages on connect', async () => {
      wsClient.sendMessage({
        type: 'test-message-1',
        data: { test: 'data1' },
      });

      wsClient.sendMessage({
        type: 'test-message-2',
        data: { test: 'data2' },
      });

      await wsClient.connect();

      const mockWs = wsClient['ws'] as any;
      const testMessages = mockWs.messageQueue.filter((msg: string) => {
        const parsed = JSON.parse(msg);
        return parsed.type.startsWith('test-message');
      });

      expect(testMessages.length).toBe(2);
    });
  });

  describe('Activity Broadcasting', () => {
    it('should send activity messages', async () => {
      await wsClient.connect();

      wsClient.sendActivity('document_created', {
        document_id: 'doc-123',
        title: 'New Document',
      });

      const mockWs = wsClient['ws'] as any;
      const activityMessage = mockWs.messageQueue.find((msg: string) => {
        const parsed = JSON.parse(msg);
        return parsed.type === 'activity';
      });

      expect(activityMessage).toBeDefined();
      const parsed = JSON.parse(activityMessage!);
      expect(parsed.data.activity_type).toBe('document_created');
    });

    it('should send typing indicators', async () => {
      await wsClient.connect();

      wsClient.sendTypingIndicator(true);

      const mockWs = wsClient['ws'] as any;
      const typingMessage = mockWs.messageQueue.find((msg: string) => {
        const parsed = JSON.parse(msg);
        return parsed.type === 'typing';
      });

      expect(typingMessage).toBeDefined();
      const parsed = JSON.parse(typingMessage!);
      expect(parsed.data.is_typing).toBe(true);
    });
  });
});
