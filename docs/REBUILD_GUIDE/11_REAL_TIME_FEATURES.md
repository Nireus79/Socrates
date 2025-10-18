# REAL-TIME FEATURES
## WebSocket Implementation and Live Updates

---

## WEBSOCKET ARCHITECTURE

### Connection Lifecycle

```
Frontend                          Backend
  │                                 │
  ├─ WS Connect ─────────────────→ │
  │  /ws/sessions/{id}              │
  │                            ┌────▼────┐
  │                            │WebSocket│
  │                            │Handler  │
  │                            └────┬────┘
  │◄─────── Connected ────────────┤
  │                                 │
  ├─ Join Session ───────────────→ │
  │  {action: 'join', ...}          │
  │                                 │
  │◄────── Session State ─────────┤
  │  {messages: [...], ...}         │
  │                                 │
  ├─ Send Message ───────────────→ │
  │  {action: 'message', ...}       │
  │                           Process
  │                           & Emit
  │◄────── User Message ──────────┤
  │  {role: 'user', ...}            │
  │                                 │
  │◄────── Agent Response ────────┤
  │  {role: 'agent', ...}           │
  │                                 │
  └─ Disconnect ──────────────────→│
     /ws/close                       │
```

### Message Types

```typescript
// Client → Server Messages
interface WSMessage {
  action: 'join' | 'message' | 'typing' | 'leave';
  sessionId: string;
  data: any;
  timestamp: string;
}

// Server → Client Messages
interface WSBroadcast {
  type: 'user_message' | 'agent_response' | 'user_typing' | 'system';
  sessionId: string;
  data: any;
  timestamp: string;
}
```

---

## BACKEND WEBSOCKET HANDLER

### FastAPI WebSocket Setup

```python
# src/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Set, Dict
import json
from datetime import datetime

router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active connections per session
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")

    async def send_personal(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Send personal error: {e}")

manager = ConnectionManager()

@router.websocket("/sessions/{session_id}")
async def websocket_endpoint(
    session_id: str,
    websocket: WebSocket,
    services: ServiceContainer = Depends(get_services)
):
    """
    WebSocket endpoint for real-time session updates

    Messages:
    - join: Join session and get current state
    - message: Send message to session
    - typing: Indicate user is typing
    """

    # Authenticate user
    try:
        token = websocket.query_params.get('token')
        user = await verify_token(token, services)
        if not user:
            await websocket.close(code=1008, reason="Unauthorized")
            return
    except Exception as e:
        logger.error(f"Auth error: {e}")
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await manager.connect(session_id, websocket)
    logger.info(f"User {user.id} connected to session {session_id}")

    try:
        while True:
            # Receive message from client
            message_text = await websocket.receive_text()
            message = json.loads(message_text)

            action = message.get('action')

            # Handle 'join' action
            if action == 'join':
                await handle_join(session_id, user, websocket, services)

            # Handle 'message' action
            elif action == 'message':
                await handle_message(session_id, user, message, manager, services)

            # Handle 'typing' action
            elif action == 'typing':
                await handle_typing(session_id, message, manager)

            # Handle 'leave' action
            elif action == 'leave':
                break

    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
        logger.info(f"User disconnected from session {session_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id, websocket)

async def handle_join(session_id: str, user, websocket: WebSocket,
                     services: ServiceContainer):
    """User joining session - send current state"""
    try:
        # Get session from database
        session_repo = SessionRepository(services.database.session)
        session = await session_repo.get_by_id(session_id)

        if not session:
            await manager.send_personal(websocket, {
                'type': 'error',
                'message': 'Session not found'
            })
            return

        # Get message history
        message_repo = MessageRepository(services.database.session)
        messages = await message_repo.get_by_session(session_id)

        # Send session state to user
        await manager.send_personal(websocket, {
            'type': 'session_state',
            'data': {
                'session': session.to_dict(),
                'messages': [msg.to_dict() for msg in messages],
                'connectedUsers': len(manager.active_connections.get(session_id, set()))
            },
            'timestamp': datetime.utcnow().isoformat()
        })

        # Notify others that user joined
        await manager.broadcast(session_id, {
            'type': 'user_joined',
            'data': {
                'userId': user.id,
                'username': user.username,
                'connectedUsers': len(manager.active_connections.get(session_id, set()))
            },
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Join error: {e}")
        await manager.send_personal(websocket, {
            'type': 'error',
            'message': 'Failed to join session'
        })

async def handle_message(session_id: str, user, message: dict,
                        manager: ConnectionManager, services: ServiceContainer):
    """User sending message - process and broadcast"""
    try:
        content = message.get('data', {}).get('content', '').strip()
        if not content:
            return

        # Create user message in database
        message_repo = MessageRepository(services.database.session)
        user_msg = Message(
            session_id=session_id,
            role='user',
            content=content,
            user_id=user.id
        )
        await message_repo.create(user_msg)

        # Broadcast user message
        await manager.broadcast(session_id, {
            'type': 'user_message',
            'data': user_msg.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        })

        # Get user instructions
        instruction_service = InstructionService(services)
        instructions = await instruction_service.get_user_instructions(
            user_id=user.id,
            project_id=message.get('projectId')
        )

        # Route to agent asynchronously
        agent_service = AgentService(services)

        # Determine which agent based on session type
        session_repo = SessionRepository(services.database.session)
        session = await session_repo.get_by_id(session_id)

        if session.type == 'socratic':
            agent_id = 'socratic'
        elif session.type == 'code_review':
            agent_id = 'code'
        else:
            agent_id = 'context'  # Chat/general

        # Call agent (in background)
        import asyncio
        asyncio.create_task(
            process_agent_response(
                session_id, agent_id, user_msg.id, content,
                user, instructions, manager, services
            )
        )

    except Exception as e:
        logger.error(f"Message handling error: {e}")
        await manager.broadcast(session_id, {
            'type': 'error',
            'message': 'Failed to process message'
        })

async def process_agent_response(session_id: str, agent_id: str, user_msg_id: str,
                                content: str, user, instructions, manager: ConnectionManager,
                                services: ServiceContainer):
    """Process agent response in background"""
    try:
        agent_service = AgentService(services)

        # Route to agent
        result = await agent_service.route_request(
            agent_id=agent_id,
            action='process_message' if agent_id == 'socratic' else 'analyze',
            data={
                'sessionId': session_id,
                'userMessage': content,
                'userId': user.id,
                'projectId': None  # Could be passed in
            },
            user_id=user.id
        )

        if result.get('success'):
            response_text = result.get('data', {}).get('response', '')
        else:
            response_text = f"Error: {result.get('error', 'Unknown error')}"

        # Create agent message in database
        message_repo = MessageRepository(services.database.session)
        agent_msg = Message(
            session_id=session_id,
            role='agent',
            agent_id=agent_id,
            content=response_text
        )
        await message_repo.create(agent_msg)

        # Broadcast agent response
        await manager.broadcast(session_id, {
            'type': 'agent_response',
            'data': agent_msg.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Agent response error: {e}")
        await manager.broadcast(session_id, {
            'type': 'error',
            'message': 'Agent failed to respond'
        })

async def handle_typing(session_id: str, message: dict, manager: ConnectionManager):
    """Broadcast typing indicator"""
    try:
        await manager.broadcast(session_id, {
            'type': 'user_typing',
            'data': {
                'userId': message.get('userId'),
                'username': message.get('username')
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Typing broadcast error: {e}")
```

---

## FRONTEND WEBSOCKET CLIENT

### WebSocket Service

```typescript
// src/services/websocket.ts
import { useAppDispatch } from '../redux/hooks';
import {
  addMessage,
  setWsConnected,
  setCurrentSession
} from '../redux/slices/sessionSlice';
import { addNotification } from '../redux/slices/uiSlice';

class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string;
  private dispatch: any;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;

  constructor(url: string, token: string, dispatch: any) {
    this.url = url;
    this.token = token;
    this.dispatch = dispatch;
  }

  connect(sessionId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${this.url}/sessions/${sessionId}?token=${this.token}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.dispatch(setWsConnected(true));

          // Send join message
          this.send({
            action: 'join',
            sessionId,
            timestamp: new Date().toISOString()
          });

          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.dispatch(setWsConnected(false));
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.dispatch(setWsConnected(false));
          this.attemptReconnect(sessionId);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: any) {
    const { type, data, timestamp } = message;

    switch (type) {
      case 'session_state':
        // Initial session state
        this.dispatch(setCurrentSession(data.session));
        data.messages.forEach((msg: any) => {
          this.dispatch(addMessage(msg));
        });
        break;

      case 'user_message':
        this.dispatch(addMessage(data));
        break;

      case 'agent_response':
        this.dispatch(addMessage(data));
        break;

      case 'user_typing':
        // Update UI to show typing indicator
        break;

      case 'user_joined':
        this.dispatch(
          addNotification({
            type: 'info',
            message: `${data.username} joined the session`
          })
        );
        break;

      case 'error':
        this.dispatch(
          addNotification({
            type: 'error',
            message: data.message || 'An error occurred'
          })
        );
        break;

      default:
        console.warn('Unknown message type:', type);
    }
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  sendMessage(sessionId: string, content: string) {
    this.send({
      action: 'message',
      sessionId,
      data: { content },
      timestamp: new Date().toISOString()
    });
  }

  indicateTyping(sessionId: string, userId: string, username: string) {
    this.send({
      action: 'typing',
      sessionId,
      userId,
      username,
      timestamp: new Date().toISOString()
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private attemptReconnect(sessionId: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
      );

      setTimeout(() => {
        this.connect(sessionId).catch((error) => {
          console.error('Reconnection failed:', error);
        });
      }, this.reconnectDelay);
    } else {
      console.error('Max reconnection attempts reached');
      this.dispatch(
        addNotification({
          type: 'error',
          message: 'Connection lost. Please refresh the page.'
        })
      );
    }
  }
}

export const createWebSocketClient = (dispatch: any) => {
  const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/api/ws';
  const token = localStorage.getItem('token') || '';
  return new WebSocketClient(wsUrl, token, dispatch);
};
```

### Custom Hook for WebSocket

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../redux/hooks';
import { createWebSocketClient } from '../services/websocket';

interface UseWebSocketOptions {
  sessionId?: string;
  autoConnect?: boolean;
}

export const useWebSocket = ({ sessionId, autoConnect = true }: UseWebSocketOptions) => {
  const dispatch = useAppDispatch();
  const wsRef = useRef<any>(null);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    if (!autoConnect || !isAuthenticated || !sessionId) {
      return;
    }

    // Create WebSocket client
    wsRef.current = createWebSocketClient(dispatch);

    // Connect
    wsRef.current.connect(sessionId).catch((error: any) => {
      console.error('Failed to connect WebSocket:', error);
    });

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, [sessionId, isAuthenticated, autoConnect, dispatch]);

  const sendMessage = (content: string) => {
    if (wsRef.current && sessionId) {
      wsRef.current.sendMessage(sessionId, content);
    }
  };

  const indicateTyping = (userId: string, username: string) => {
    if (wsRef.current && sessionId) {
      wsRef.current.indicateTyping(sessionId, userId, username);
    }
  };

  return {
    sendMessage,
    indicateTyping,
    disconnect: () => wsRef.current?.disconnect()
  };
};
```

### Chat Component Using WebSocket

```typescript
// src/components/sessions/ChatInterface.tsx
import React, { useState, useRef, useEffect } from 'react';
import { useAppSelector } from '../../redux/hooks';
import { useWebSocket } from '../../hooks/useWebSocket';

interface ChatInterfaceProps {
  sessionId: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ sessionId }) => {
  const { messages, wsConnected } = useAppSelector((state) => state.sessions);
  const { user } = useAppSelector((state) => state.auth);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout>();

  const { sendMessage, indicateTyping } = useWebSocket({
    sessionId,
    autoConnect: true
  });

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !wsConnected) return;

    sendMessage(inputValue);
    setInputValue('');
    setIsTyping(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    setIsTyping(true);

    if (user) {
      indicateTyping(user.id, user.username);
    }

    // Clear typing indicator after 1 second of inactivity
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
    }, 1000);
  };

  if (!wsConnected) {
    return (
      <div className="bg-white rounded-lg shadow p-6 flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Connecting to session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow h-full flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-md p-4 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              {msg.role === 'agent' && (
                <div className="text-sm font-semibold mb-1">{msg.agent_id}</div>
              )}
              <p>{msg.content}</p>
              <div className="text-xs opacity-75 mt-1">
                {new Date(msg.created_at).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSendMessage} className="border-t p-6 bg-gray-50">
        <div className="space-y-4">
          <textarea
            value={inputValue}
            onChange={handleInputChange}
            placeholder="Type your message..."
            className="w-full p-3 border rounded resize-none focus:outline-none focus:border-blue-500"
            rows={3}
            disabled={!wsConnected}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || !wsConnected}
            className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            Send Message
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;
```

---

## PERFORMANCE CONSIDERATIONS

### Message Queue

```typescript
// Implement message queue if WebSocket is temporarily disconnected
class MessageQueue {
  private queue: any[] = [];
  private isConnected = false;

  enqueue(message: any) {
    this.queue.push(message);
  }

  dequeue(): any {
    return this.queue.shift();
  }

  async flushQueue(sendFn: (msg: any) => void) {
    while (this.queue.length > 0) {
      const message = this.dequeue();
      sendFn(message);
      await new Promise((resolve) => setTimeout(resolve, 100)); // Rate limit
    }
  }
}
```

### Connection Pooling

```python
# Limit concurrent connections per user
MAX_CONNECTIONS_PER_USER = 3

async def connect(self, session_id: str, websocket: WebSocket, user_id: str):
    user_connections = [
        s for s, conns in self.active_connections.items()
        if len([c for c in conns if c.user_id == user_id]) > 0
    ]

    if len(user_connections) >= MAX_CONNECTIONS_PER_USER:
        await websocket.close(code=1008, reason="Too many connections")
        return
```

---

## NEXT STEPS

1. Implement WebSocket handler in FastAPI
2. Create WebSocket client in React
3. Integrate with Redux for state management
4. Handle reconnection and error recovery
5. Write comprehensive WebSocket tests
6. Monitor connection health

**Proceed to 12_QUALITY_ASSURANCE.md** for QualityAnalyzer integration
