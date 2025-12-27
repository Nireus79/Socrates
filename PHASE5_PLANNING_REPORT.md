# Phase 5: Phase 2 Planning & Architecture

## Executive Summary

Based on Phase 1-4 completion and Phase 4 integration testing results, this document outlines:
- **Feature gaps** from Phase 4 testing
- **Phase 2 feature requirements**
- **Architectural improvements needed**
- **Implementation priorities and dependencies**
- **Timeline and resource allocation**

---

## Part 1: Phase 1 Completion Status

### Fully Implemented ✓
1. **Authentication System** (100%)
   - User registration with validation
   - JWT token generation and validation
   - Login flow with secure tokens
   - Token refresh mechanism

2. **Project Management** (100%)
   - Create projects with metadata
   - List projects with filtering
   - Get project details
   - Update project information
   - Archive/delete projects

3. **User Settings** (100%)
   - Get user preferences
   - Update theme preferences
   - Notification settings
   - Display preferences

4. **Analytics** (100%)
   - Project-level analytics
   - Usage metrics
   - Feature usage tracking
   - Performance metrics

### Partially Implemented (Need Completion)
1. **Chat System** (0%)
   - Missing: Chat session endpoints
   - Missing: Message sending/receiving
   - Missing: WebSocket integration for real-time
   - Impact: Users can't communicate with AI assistant

2. **Collaboration** (20%)
   - Implemented: Backend structure
   - Missing: Collaborator invitation validation
   - Missing: Permission enforcement
   - Missing: Real-time collaboration sync
   - Impact: Team features unusable

3. **Knowledge Base** (0%)
   - Missing: Document upload endpoints
   - Missing: Document search/retrieval
   - Missing: Knowledge base organization
   - Impact: Can't store reference materials

---

## Part 2: Phase 2 Feature Requirements

### Feature 1: Real-Time Chat System

**Requirements**:
```
1. Chat Sessions
   - Create session per project
   - List sessions for project
   - Delete sessions
   - Session history persistence

2. Message Management
   - Send message to AI assistant
   - Receive AI responses
   - Message history
   - Message editing/deletion

3. Real-Time Updates
   - WebSocket connection for live messages
   - Typing indicators
   - Message delivery status
   - Connection state management

4. Message Features
   - Code snippet support
   - File attachment support
   - Message formatting (Markdown)
   - Timestamp and author tracking
```

**Database Schema**:
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL FOREIGN KEY,
    user_id UUID NOT NULL FOREIGN KEY,
    title VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL FOREIGN KEY,
    user_id UUID NOT NULL FOREIGN KEY,
    content TEXT NOT NULL,
    role ENUM('user', 'assistant'),
    metadata JSONB,  -- for code snippets, attachments, etc.
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**API Endpoints**:
```
POST   /projects/{id}/chat/sessions          - Create session
GET    /projects/{id}/chat/sessions          - List sessions
GET    /projects/{id}/chat/sessions/{sid}    - Get session details
DELETE /projects/{id}/chat/sessions/{sid}    - Delete session

POST   /projects/{id}/chat/{sid}/message     - Send message
GET    /projects/{id}/chat/{sid}/messages    - Get message history
PUT    /projects/{id}/chat/{sid}/message/{mid} - Edit message
DELETE /projects/{id}/chat/{sid}/message/{mid} - Delete message
```

**WebSocket Events**:
```
CLIENT -> SERVER:
  - chat:message:send        (send new message)
  - chat:typing:start        (user typing)
  - chat:typing:stop         (user stopped typing)

SERVER -> CLIENT:
  - chat:message:received    (new message from other user)
  - chat:message:updated     (message edited)
  - chat:typing:indicator    (user typing notification)
  - chat:connection:status   (connection state)
```

---

### Feature 2: Enhanced Collaboration

**Requirements**:
```
1. Collaborator Management
   - Invite users by email
   - Accept/reject invitations
   - List project collaborators
   - Manage collaborator roles
   - Remove collaborators

2. Role-Based Access Control
   - Owner: Full access
   - Editor: Read/write access
   - Viewer: Read-only access
   - Custom role support

3. Activity Tracking
   - Track collaborator actions
   - View activity log
   - Mention collaborators (@name)
   - Notifications for mentions

4. Real-Time Sync
   - Sync edits across users
   - Lock mechanism for concurrent edits
   - Merge conflict resolution
```

**Database Schema**:
```sql
CREATE TABLE project_collaborators (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL FOREIGN KEY,
    user_id UUID NOT NULL FOREIGN KEY,
    role ENUM('owner', 'editor', 'viewer'),
    invited_by UUID NOT NULL FOREIGN KEY,
    status ENUM('active', 'pending', 'removed'),
    joined_at TIMESTAMP,
    UNIQUE(project_id, user_id)
);

CREATE TABLE project_activity (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL FOREIGN KEY,
    user_id UUID NOT NULL FOREIGN KEY,
    action_type VARCHAR(50),
    action_details JSONB,
    created_at TIMESTAMP,
    INDEX(project_id, created_at)
);
```

**API Endpoints**:
```
POST   /projects/{id}/collaborators          - Invite collaborator
GET    /projects/{id}/collaborators          - List collaborators
PUT    /projects/{id}/collaborators/{uid}    - Update role
DELETE /projects/{id}/collaborators/{uid}    - Remove collaborator
GET    /projects/{id}/activity               - Get activity log
POST   /projects/{id}/invitations/{iid}/accept - Accept invitation
```

---

### Feature 3: Knowledge Base Management

**Requirements**:
```
1. Document Management
   - Upload documents (PDF, TXT, MD, etc.)
   - Organize by tags/categories
   - Search documents
   - View document details
   - Delete documents

2. Document Processing
   - Extract text from PDFs
   - Parse markdown
   - Generate summaries
   - Extract key entities

3. Knowledge Search
   - Full-text search
   - Semantic search
   - Filter by type/category
   - Sort by relevance

4. Integration with Chat
   - Reference documents in chat
   - Auto-suggest relevant docs
   - Include context in AI responses
```

**Database Schema**:
```sql
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL FOREIGN KEY,
    user_id UUID NOT NULL FOREIGN KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    document_type VARCHAR(50),
    file_path VARCHAR(255),
    file_size INTEGER,
    tags JSONB,  -- ["tag1", "tag2"]
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    INDEX(project_id)
);

CREATE TABLE document_vectors (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL FOREIGN KEY,
    chunk_index INTEGER,
    embedding VECTOR(1536),  -- OpenAI embedding dimension
    content_chunk TEXT,
    UNIQUE(document_id, chunk_index)
);
```

**API Endpoints**:
```
POST   /projects/{id}/knowledge/documents    - Add document
GET    /projects/{id}/knowledge/documents    - List documents
GET    /projects/{id}/knowledge/{did}        - Get document details
DELETE /projects/{id}/knowledge/{did}        - Delete document
POST   /projects/{id}/knowledge/search       - Search documents
```

---

## Part 3: Architecture Improvements

### 1. WebSocket Architecture

**Current Issue**: No real-time communication

**Proposed Solution**:
```
┌─────────────────────────────────────────┐
│           Client (Browser)              │
│  ┌─────────────────────────────────┐    │
│  │  WebSocket Connection           │    │
│  │  - ws://localhost:8000/ws       │    │
│  └─────────────────────────────────┘    │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼─────┐         ┌────▼─────┐
   │ Chat Msg │         │ Activity  │
   │ Manager  │         │ Broadcast │
   └────┬─────┘         └────┬─────┘
        │                     │
   ┌────▼──────────────────────▼─────┐
   │  WebSocket Connection Handler    │
   │  - Authenticate connection       │
   │  - Route events                  │
   │  - Broadcast messages            │
   └────┬──────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐
   │  FastAPI WebSocket Manager        │
   │  - Connection pooling             │
   │  - Event routing                  │
   │  - Error handling                 │
   └────┬──────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐
   │  Message Queue (Redis)            │
   │  - Pub/Sub for broadcasts         │
   │  - Message persistence           │
   │  - Scaling support               │
   └─────────────────────────────────────┘
```

**Implementation**:
```python
# socrates-api/src/socrates_api/websocket/manager.py

from fastapi import WebSocket
from typing import Dict, Set
import redis.asyncio as redis
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.redis_client = None

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)

    async def disconnect(self, session_id: str, websocket: WebSocket):
        self.active_connections[session_id].discard(websocket)

    async def broadcast(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_json(message)

    async def send_personal(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)
```

### 2. Vector Database for Embeddings

**Current Issue**: No semantic search capability

**Proposed Solution**: Integrate with pgvector (PostgreSQL Vector extension)
```sql
-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Store document embeddings
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    embedding vector(1536),  -- OpenAI embedding dimension
    chunk_text TEXT,
    chunk_index INTEGER,
    FOREIGN KEY (document_id) REFERENCES knowledge_documents(id)
);

CREATE INDEX ON document_embeddings USING ivfflat (embedding vector_cosine_ops);
```

**Usage in Chat**:
```python
async def get_relevant_documents(query: str, project_id: str, limit: int = 3):
    # 1. Convert query to embedding
    query_embedding = await openai_client.create_embedding(query)

    # 2. Search similar embeddings
    results = await db.query("""
        SELECT document_id, chunk_text, similarity
        FROM document_embeddings
        WHERE document_embeddings.embedding <=> %s < 0.3
        ORDER BY similarity DESC
        LIMIT %s
    """, (query_embedding, limit))

    return results
```

### 3. Caching Strategy

**Current Issue**: Repeated queries to database

**Proposed Solution**:
```python
# Use Redis for caching
- Cache user settings (TTL: 1 hour)
- Cache project details (TTL: 30 mins)
- Cache collaborator lists (TTL: 15 mins)
- Cache search results (TTL: 5 mins)

# Cache invalidation on updates
@router.post("/projects/{id}")
async def update_project(id: str, data: ProjectUpdate):
    project = await db.update_project(id, data)
    await cache.delete(f"project:{id}")
    return project
```

---

## Part 4: Implementation Roadmap

### Sprint 1: Chat System (Weeks 1-3)

**Tasks**:
1. Implement chat session endpoints (API)
2. Implement message endpoints (API)
3. Add WebSocket connection handling
4. Implement message persistence
5. Create chat UI components
6. Add message history display
7. Test chat flow end-to-end

**Deliverables**:
- Chat functional in development
- 10/10 chat-related tests passing
- Real-time message delivery
- Message history persistence

---

### Sprint 2: Collaboration & Knowledge (Weeks 4-6)

**Tasks**:
1. Fix collaborator invitation validation
2. Implement role-based access control
3. Add activity tracking
4. Implement knowledge document endpoints
5. Add document search functionality
6. Integrate vector embeddings
7. Create knowledge UI components

**Deliverables**:
- Collaborators can be invited and managed
- Documents can be uploaded and searched
- 15/15 integration tests passing
- Semantic search working

---

### Sprint 3: Performance & Optimization (Weeks 7-8)

**Tasks**:
1. Implement Redis caching
2. Optimize database queries
3. Add connection pooling
4. Implement rate limiting
5. Add monitoring/logging
6. Performance testing
7. Load testing

**Deliverables**:
- <100ms response times
- Support 1000+ concurrent users
- Comprehensive monitoring
- Production-ready performance

---

## Part 5: Dependency Analysis

```
Phase 2 Features Dependency Tree:

┌─────────────────────────────────────┐
│   Authentication (COMPLETED)         │
│   - JWT tokens                       │
│   - User validation                  │
└────────────────┬────────────────────┘
                 │
    ┌────────────┴────────────────┐
    │                             │
┌───▼──────────────────┐  ┌──────▼─────────────────┐
│  Chat System         │  │  Collaboration         │
│  - Sessions          │  │  - Role Management     │
│  - Messages          │  │  - Activity Tracking   │
│  - WebSockets        │  │                         │
└────────────────┬─────┘  └──────┬─────────────────┘
                 │                │
        ┌────────┴────────┐       │
        │                 │       │
    ┌───▼───────────┐ ┌──▼───────▼──────┐
    │ Knowledge Base│ │  Notifications  │
    │ - Documents  │ │  - Mentions     │
    │ - Search     │ │  - Activity     │
    │ - Embeddings │ │                 │
    └───┬───────────┘ └──┬──────────────┘
        │                │
        └────────┬───────┘
                 │
        ┌────────▼────────┐
        │ Performance     │
        │ Optimization    │
        │ - Caching       │
        │ - Indexing      │
        └─────────────────┘
```

---

## Part 6: Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| WebSocket scaling | Medium | Medium | Use Redis pub/sub, connection pooling |
| Vector DB performance | High | Low | Pre-index documents, cache results |
| Real-time sync conflicts | Medium | Medium | Implement conflict resolution, locking |
| Token expiration in chat | Low | High | Implement token refresh in WebSocket |
| Document upload size limits | Low | Medium | Validate size, chunk uploads |

---

## Part 7: Success Metrics

### Functionality Metrics
- 90%+ integration test pass rate
- All 6 Phase 1 features fully functional
- Phase 2 features working end-to-end

### Performance Metrics
- Average API response time < 100ms
- WebSocket message latency < 500ms
- Support 1000+ concurrent users

### Quality Metrics
- Code coverage > 80%
- Zero critical bugs
- All security tests passing

---

## Part 8: Resource Requirements

**Backend Development**: 2 developers × 8 weeks
**Frontend Development**: 2 developers × 8 weeks
**QA/Testing**: 1 QA engineer × 8 weeks
**DevOps/Infrastructure**: 0.5 DevOps × 8 weeks

**Total**: ~5 developer weeks (8 weeks calendar time with team)

---

## Conclusion

Phase 2 development focuses on:
1. **Completing chat system** (currently 0%)
2. **Fixing collaboration features** (currently 20%)
3. **Implementing knowledge base** (currently 0%)
4. **Performance optimization** (new)

All features have clear requirements, API specifications, and database schemas defined. The implementation roadmap is organized into 3 sprints with clear deliverables.

**Estimated Completion**: 8 weeks with current team size

**Status**: Ready for Phase 2 implementation sprint planning
