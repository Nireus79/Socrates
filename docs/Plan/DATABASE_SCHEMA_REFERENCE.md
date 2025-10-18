# SOCRATES 8.0 - DATABASE SCHEMA REFERENCE
**PostgreSQL Complete Schema Design**

---

## MIGRATION SETUP

**File:** `backend/alembic/env.py` (already auto-generated, but configure this)

```python
from sqlalchemy import engine_from_config, pool
from alembic import context
from src.config import settings
from src.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata

# ... rest of standard alembic setup
```

**Create initial migration:**
```bash
cd backend
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## CORE TABLES

### 1. USERS TABLE
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    bio TEXT,
    avatar_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
```

**SQLAlchemy Model:**
```python
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    bio = Column(Text)
    avatar_url = Column(String(500))
    status = Column(String(50), default='ACTIVE')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)

    projects = relationship("Project", back_populates="owner")
    sessions = relationship("Session", back_populates="owner")
    messages = relationship("Message", back_populates="user")
```

---

### 2. PROJECTS TABLE
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'PLANNING' CHECK (status IN ('PLANNING', 'DESIGN', 'DEVELOPMENT', 'TESTING', 'COMPLETE')),
    technology_stack JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created ON projects(created_at);
```

**SQLAlchemy Model:**
```python
class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='PLANNING')
    technology_stack = Column(JSONB, default=list)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="projects")
    sessions = relationship("Session", back_populates="project")
    documents = relationship("Document", back_populates="project")
```

---

### 3. SESSIONS TABLE
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'ARCHIVED', 'PAUSED')),
    mode VARCHAR(50) DEFAULT 'chat' CHECK (mode IN ('chat', 'question', 'teaching', 'review')),
    role VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP
);

CREATE INDEX idx_sessions_owner ON sessions(owner_id);
CREATE INDEX idx_sessions_project ON sessions(project_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_created ON sessions(created_at);
```

**SQLAlchemy Model:**
```python
class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), index=True)
    name = Column(String(255))
    status = Column(String(50), default='ACTIVE')
    mode = Column(String(50), default='chat')
    role = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    archived_at = Column(DateTime)

    owner = relationship("User", back_populates="sessions")
    project = relationship("Project", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
```

---

### 4. MESSAGES TABLE (CRITICAL)
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text' CHECK (message_type IN ('text', 'code', 'question', 'response')),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_user ON messages(user_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created ON messages(created_at);
```

**SQLAlchemy Model:**
```python
class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default='text')
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    session = relationship("Session", back_populates="messages")
    user = relationship("User", back_populates="messages")
```

---

### 5. USER PREFERENCES TABLE
```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(50) DEFAULT 'dark',
    llm_model VARCHAR(255) DEFAULT 'claude-3-sonnet',
    llm_temperature FLOAT DEFAULT 0.7,
    llm_max_tokens INTEGER DEFAULT 2000,
    ide_type VARCHAR(50),
    auto_sync BOOLEAN DEFAULT FALSE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_preferences_user ON user_preferences(user_id);
```

**SQLAlchemy Model:**
```python
class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    theme = Column(String(50), default='dark')
    llm_model = Column(String(255), default='claude-3-sonnet')
    llm_temperature = Column(Float, default=0.7)
    llm_max_tokens = Column(Integer, default=2000)
    ide_type = Column(String(50))
    auto_sync = Column(Boolean, default=False)
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
```

---

### 6. DOCUMENTS TABLE
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    content_summary TEXT,
    vector_id VARCHAR(500),
    status VARCHAR(50) DEFAULT 'PROCESSED' CHECK (status IN ('UPLOADING', 'PROCESSING', 'PROCESSED', 'ERROR')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_owner ON documents(owner_id);
CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_status ON documents(status);
```

**SQLAlchemy Model:**
```python
class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), index=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))
    content_summary = Column(Text)
    vector_id = Column(String(500))
    status = Column(String(50), default='PROCESSED')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    owner = relationship("User", foreign_keys=[owner_id])
    project = relationship("Project", back_populates="documents")
```

---

### 7. AUDIT LOG TABLE
```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    action VARCHAR(50) CHECK (action IN ('CREATE', 'UPDATE', 'DELETE')),
    old_value JSONB,
    new_value JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_created ON audit_log(created_at);
```

**SQLAlchemy Model:**
```python
class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    entity_type = Column(String(100))
    entity_id = Column(UUID(as_uuid=True))
    action = Column(String(50))
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    created_at = Column(DateTime, default=func.now(), index=True)
```

---

## DATABASE CONSTRAINTS

**ACID Compliance:**
- ✅ All foreign keys enforced at database level
- ✅ Cascade delete where appropriate
- ✅ SET NULL for optional relationships
- ✅ Timestamps with automatic updates
- ✅ Status enums enforced

**Data Integrity:**
- ✅ UUIDs for primary keys (no sequential IDs)
- ✅ Proper indexing for common queries
- ✅ Unique constraints on username/email
- ✅ JSONB for flexible metadata
- ✅ Audit trail for all changes

---

## INITIALIZATION SQL

**File:** `backend/alembic/versions/001_initial_schema.py`

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # All tables are auto-generated by Alembic from SQLAlchemy models
    # Just run: alembic upgrade head
    pass

def downgrade():
    pass
```

**Then seed with test data:**

```python
# File: backend/scripts/seed_database.py
from src.database import SessionLocal
from src.models import User
from src.services.user_service import hash_password
import uuid

def seed():
    db = SessionLocal()

    # Create test user
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("Test@1234"),
        first_name="Test",
        last_name="User"
    )
    db.add(user)
    db.commit()
    print(f"Created user: {user.id}")

if __name__ == "__main__":
    seed()
```

---

## MIGRATION WORKFLOW

```bash
# 1. Create migration from model changes
alembic revision --autogenerate -m "Add new column"

# 2. Review migration file
cat alembic/versions/002_add_new_column.py

# 3. Apply migration
alembic upgrade head

# 4. Downgrade if needed (test)
alembic downgrade -1

# 5. View migration history
alembic history

# 6. Current version
alembic current
```

---

## CRITICAL RULES

1. **Never** modify production database directly
2. **Always** create migration before deploying
3. **Always** test downgrade path
4. **Always** add indexes for foreign keys
5. **Always** use UUIDs for primary keys
6. **Never** hardcode user IDs in code
7. **Always** validate data in service layer before saving

---

**Database Version:** 8.0.0
**PostgreSQL Version:** 14+
**Created:** October 17, 2025
