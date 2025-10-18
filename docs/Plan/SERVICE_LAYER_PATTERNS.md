# SOCRATES 8.0 - SERVICE LAYER PATTERNS
**Clean Architecture - Business Logic Layer**

---

## OVERVIEW

Services handle all business logic and validation. They sit between API routes and data repositories.

```
FastAPI Routes → Service Layer → Repository Layer → Database
```

**Key Principle:** Routes should be thin (just HTTP), Services should be thick (all logic).

---

## BASE SERVICE PATTERN

**File:** `backend/src/services/base_service.py`

```python
from typing import Any, Dict, List, Optional, TypeVar
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from src.utils.logger import logger

T = TypeVar('T')

class BaseService(ABC):
    """Abstract base service with common functionality"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logger

    def commit(self):
        """Commit transaction"""
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Commit failed: {e}")
            raise

    def rollback(self):
        """Rollback transaction"""
        self.db.rollback()

    def handle_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Consistent error handling"""
        self.logger.error(f"{context}: {str(error)}")
        self.rollback()
        raise

    def create_response(self, success: bool, data: Any = None, message: str = None):
        """Standardized response"""
        return {
            "success": success,
            "data": data,
            "message": message or ("Success" if success else "Error")
        }
```

---

## USER SERVICE

**File:** `backend/src/services/user_service.py`

```python
from typing import Optional
from uuid import UUID
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from src.models import User
from src.services.base_service import BaseService
from src.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService(BaseService):
    """User management service"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.repo = UserRepository(db)

    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain, hashed)

    def register_user(self, username: str, email: str, password: str,
                     first_name: str = None, last_name: str = None) -> User:
        """Register new user with validation"""
        # Validate input
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not self._validate_email(email):
            raise ValueError("Invalid email format")

        # Check if username/email exists
        if self.repo.get_by_username(username):
            raise ValueError("Username already exists")

        if self.repo.get_by_email(email):
            raise ValueError("Email already exists")

        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            first_name=first_name,
            last_name=last_name
        )

        self.db.add(user)
        self.commit()
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return if valid"""
        user = self.repo.get_by_username(username)

        if not user:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = func.now()
        self.commit()
        return user

    def update_profile(self, user_id: UUID, first_name: str = None,
                      last_name: str = None, bio: str = None) -> User:
        """Update user profile"""
        user = self.repo.get_by_id(user_id)

        if not user:
            raise ValueError("User not found")

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if bio:
            user.bio = bio

        self.commit()
        return user

    def change_password(self, user_id: UUID, current_password: str,
                       new_password: str) -> bool:
        """Change user password"""
        user = self.repo.get_by_id(user_id)

        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not self.verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        # Update password
        user.password_hash = self.hash_password(new_password)
        self.commit()
        return True

    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
```

---

## PROJECT SERVICE

**File:** `backend/src/services/project_service.py`

```python
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.models import Project
from src.services.base_service import BaseService
from src.repositories.project_repository import ProjectRepository

class ProjectService(BaseService):
    """Project management service"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.repo = ProjectRepository(db)

    def create_project(self, owner_id: UUID, name: str, description: str = None,
                      technology_stack: List[str] = None) -> Project:
        """Create new project"""
        if not name or len(name.strip()) == 0:
            raise ValueError("Project name is required")

        if len(name) > 255:
            raise ValueError("Project name too long")

        project = Project(
            owner_id=owner_id,
            name=name,
            description=description,
            technology_stack=technology_stack or [],
            status='PLANNING'
        )

        self.db.add(project)
        self.commit()
        return project

    def get_user_projects(self, owner_id: UUID, status: str = None) -> List[Project]:
        """Get all projects for user"""
        if status:
            return self.repo.get_by_owner_and_status(owner_id, status)
        return self.repo.get_by_owner(owner_id)

    def update_project(self, project_id: UUID, owner_id: UUID, **kwargs) -> Project:
        """Update project with authorization check"""
        project = self.repo.get_by_id(project_id)

        if not project:
            raise ValueError("Project not found")

        # Verify ownership
        if project.owner_id != owner_id:
            raise PermissionError("Not authorized to update this project")

        # Update allowed fields
        for key, value in kwargs.items():
            if key in ['name', 'description', 'status', 'technology_stack']:
                setattr(project, key, value)

        self.commit()
        return project

    def delete_project(self, project_id: UUID, owner_id: UUID) -> bool:
        """Delete project with authorization"""
        project = self.repo.get_by_id(project_id)

        if not project:
            raise ValueError("Project not found")

        if project.owner_id != owner_id:
            raise PermissionError("Not authorized")

        self.db.delete(project)
        self.commit()
        return True
```

---

## SESSION SERVICE

**File:** `backend/src/services/session_service.py`

```python
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models import Session as SessionModel, Message
from src.services.base_service import BaseService
from src.repositories.session_repository import SessionRepository
from src.repositories.message_repository import MessageRepository

class SessionService(BaseService):
    """Session management service"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.session_repo = SessionRepository(db)
        self.message_repo = MessageRepository(db)

    def create_session(self, owner_id: UUID, project_id: UUID = None,
                      mode: str = 'chat', role: str = None) -> SessionModel:
        """Create new session"""
        if mode not in ['chat', 'question', 'teaching', 'review']:
            raise ValueError(f"Invalid mode: {mode}")

        session = SessionModel(
            owner_id=owner_id,
            project_id=project_id,
            mode=mode,
            role=role,
            status='ACTIVE'
        )

        self.db.add(session)
        self.commit()
        return session

    def get_session(self, session_id: UUID, owner_id: UUID) -> Optional[SessionModel]:
        """Get session with authorization"""
        session = self.session_repo.get_by_id(session_id)

        if not session:
            return None

        if session.owner_id != owner_id:
            raise PermissionError("Not authorized to access this session")

        return session

    def toggle_mode(self, session_id: UUID, owner_id: UUID, new_mode: str) -> SessionModel:
        """Toggle session mode"""
        session = self.get_session(session_id, owner_id)

        if not session:
            raise ValueError("Session not found")

        if new_mode not in ['chat', 'question', 'teaching', 'review']:
            raise ValueError(f"Invalid mode: {new_mode}")

        session.mode = new_mode
        self.commit()
        return session

    def archive_session(self, session_id: UUID, owner_id: UUID) -> SessionModel:
        """Archive session"""
        session = self.get_session(session_id, owner_id)

        if not session:
            raise ValueError("Session not found")

        session.status = 'ARCHIVED'
        session.archived_at = func.now()
        self.commit()
        return session

    def get_session_messages(self, session_id: UUID, owner_id: UUID,
                           limit: int = 50, offset: int = 0) -> List[Message]:
        """Get session messages with pagination"""
        session = self.get_session(session_id, owner_id)

        if not session:
            raise ValueError("Session not found")

        return self.message_repo.get_by_session(session_id, limit, offset)
```

---

## MESSAGE SERVICE

**File:** `backend/src/services/message_service.py`

```python
from typing import Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from src.models import Message
from src.services.base_service import BaseService
from src.repositories.message_repository import MessageRepository
from src.services.session_service import SessionService
from anthropic import Anthropic

class MessageService(BaseService):
    """Message handling and response generation"""

    def __init__(self, db: Session, anthropic_key: str):
        super().__init__(db)
        self.repo = MessageRepository(db)
        self.session_service = SessionService(db)
        self.client = Anthropic(api_key=anthropic_key)

    def send_message(self, session_id: UUID, user_id: UUID, content: str) -> Tuple[Message, Message]:
        """Send user message and generate assistant response"""

        # Validate input
        if not content or len(content.strip()) == 0:
            raise ValueError("Message content cannot be empty")

        if len(content) > 10000:
            raise ValueError("Message too long")

        # Save user message
        user_message = Message(
            session_id=session_id,
            user_id=user_id,
            role='user',
            content=content,
            message_type='text'
        )
        self.db.add(user_message)
        self.commit()

        # Generate response
        try:
            response_text = self._generate_response(session_id, content)
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            raise ValueError("Failed to generate response")

        # Save assistant message
        assistant_message = Message(
            session_id=session_id,
            user_id=user_id,
            role='assistant',
            content=response_text,
            message_type='text'
        )
        self.db.add(assistant_message)
        self.commit()

        return user_message, assistant_message

    def _generate_response(self, session_id: UUID, user_input: str) -> str:
        """Generate response using Claude API"""
        # Get message history for context
        messages_history = self.repo.get_by_session(session_id, limit=10)

        # Build message list for API
        messages = []
        for msg in reversed(messages_history):
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current message
        messages.append({
            "role": "user",
            "content": user_input
        })

        # Call Claude API
        response = self.client.messages.create(
            model="claude-3-sonnet-20241022",
            max_tokens=2000,
            messages=messages
        )

        return response.content[0].text

    def delete_message(self, message_id: UUID, user_id: UUID) -> bool:
        """Delete message (with authorization)"""
        message = self.repo.get_by_id(message_id)

        if not message:
            raise ValueError("Message not found")

        if message.user_id != user_id:
            raise PermissionError("Not authorized")

        self.db.delete(message)
        self.commit()
        return True
```

---

## PREFERENCES SERVICE

**File:** `backend/src/services/preference_service.py`

```python
from uuid import UUID
from sqlalchemy.orm import Session
from src.models import UserPreference
from src.services.base_service import BaseService
from src.repositories.preference_repository import PreferenceRepository

class PreferenceService(BaseService):
    """User preferences/settings management"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.repo = PreferenceRepository(db)

    def get_preferences(self, user_id: UUID) -> UserPreference:
        """Get or create user preferences"""
        prefs = self.repo.get_by_user_id(user_id)

        if not prefs:
            # Create default preferences
            prefs = UserPreference(user_id=user_id)
            self.db.add(prefs)
            self.commit()

        return prefs

    def update_preferences(self, user_id: UUID, **kwargs) -> UserPreference:
        """Update user preferences"""
        prefs = self.get_preferences(user_id)

        allowed_fields = {
            'theme', 'llm_model', 'llm_temperature', 'llm_max_tokens',
            'ide_type', 'auto_sync', 'notifications_enabled'
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(prefs, key, value)

        self.commit()
        return prefs
```

---

## USAGE IN ROUTES

**File:** `backend/src/api/routes/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.services.user_service import UserService
from src.dependencies import get_db
from src.schemas.auth import RegisterRequest, LoginRequest

router = APIRouter()

@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user"""
    try:
        service = UserService(db)
        user = service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name
        )
        return {
            "success": True,
            "data": {"id": str(user.id), "username": user.username},
            "message": "User registered successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""
    try:
        service = UserService(db)
        user = service.authenticate_user(request.username, request.password)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Generate JWT token (implementation in auth utils)
        token = create_access_token(str(user.id))

        return {
            "success": True,
            "data": {
                "user_id": str(user.id),
                "access_token": token,
                "token_type": "bearer"
            },
            "message": "Login successful"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## KEY PRINCIPLES

1. **Single Responsibility:** Each service handles one domain
2. **Error Handling:** All validation happens in services
3. **Database Transactions:** Services manage commit/rollback
4. **Authorization:** Services verify user permissions
5. **Logging:** All operations logged for debugging
6. **No Side Effects:** Services are testable and pure
7. **Dependency Injection:** Services receive dependencies

---

**Service Architecture:** 8.0.0
**Last Updated:** October 17, 2025
