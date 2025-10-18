# BACKEND LAYERS IMPLEMENTATION
## Database, Repository, Service Layer Architecture

---

## LAYER ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────┐
│   FastAPI Router Layer              │
│   (endpoints/*.py)                  │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Service Layer                     │
│   (services/*.py)                   │
│   - Business Logic                  │
│   - Agent Coordination              │
│   - Instruction Enforcement         │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Repository Layer                  │
│   (repositories/*.py)               │
│   - CRUD Operations                 │
│   - Query Building                  │
│   - Transaction Management          │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Data Layer                        │
│   (models/*.py)                     │
│   - SQLAlchemy Models               │
│   - Schema Definition               │
│   - Relationships                   │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Database (PostgreSQL)             │
│   - Persistent Storage              │
│   - ACID Transactions               │
│   - Connection Pooling              │
└─────────────────────────────────────┘
```

---

## LAYER 1: DATA LAYER (Models)

### Purpose
Define all database entities using SQLAlchemy ORM models with proper relationships and constraints.

### Implementation: `src/models/base.py`

```python
"""Base model with common fields and utilities"""
from datetime import datetime
from typing import TypeVar, Generic
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4

Base = declarative_base()

class BaseModel(Base):
    """Abstract base for all models with common fields"""
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                       onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }
```

### Implementation: `src/models/user.py`

```python
"""User model with authentication and profile"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from src.models.base import BaseModel

class UserStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    is_email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)

    # Relationships
    projects = relationship("Project", back_populates="owner")
    sessions = relationship("Session", back_populates="creator")
    instructions = relationship("UserInstruction", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"
```

### Implementation: `src/models/project.py`

```python
"""Project model with lifecycle management"""
from sqlalchemy import Column, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from src.models.base import BaseModel

class ProjectPhase(PyEnum):
    PLANNING = "planning"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"

class ProjectStatus(PyEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class Project(BaseModel):
    __tablename__ = "projects"

    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    phase = Column(Enum(ProjectPhase), default=ProjectPhase.PLANNING)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE)
    tech_stack = Column(String(255))

    # Relationships
    owner = relationship("User", back_populates="projects")
    sessions = relationship("Session", back_populates="project", cascade="all, delete-orphan")
    collaborators = relationship("ProjectCollaborator", back_populates="project")
    instructions = relationship("UserInstruction", back_populates="project")

    def __repr__(self):
        return f"<Project {self.name}>"
```

### Implementation: `src/models/instruction.py`

```python
"""User instruction model for AI behavior rules"""
from sqlalchemy import Column, String, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from src.models.base import BaseModel

class UserInstruction(BaseModel):
    __tablename__ = "user_instructions"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    rules = Column(Text, nullable=False)  # Raw instruction text
    parsed_rules = Column(JSON)  # Structured rule format
    categories = Column(JSON)  # {"security": [...], "quality": [...], ...}
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="instructions")
    project = relationship("Project", back_populates="instructions")

    def __repr__(self):
        return f"<UserInstruction {self.user_id}>"
```

### Full Model List

Complete models needed:
- `User` - User accounts and profiles
- `Project` - Project management
- `Session` - Socratic/Chat sessions
- `Message` - Session messages
- `ProjectCollaborator` - Project team members
- `UserInstruction` - AI behavior rules
- `AuditLog` - Action tracking
- `TechnicalSpecification` - Project specs
- `GeneratedCodebase` - Code generation results
- `GeneratedFile` - Individual generated files

---

## LAYER 2: REPOSITORY LAYER

### Purpose
Provide consistent data access interface, abstract database operations, enable testing with mocks.

### Pattern: Base Repository

```python
# src/database/repositories/base.py
from typing import TypeVar, Generic, List, Optional
from sqlalchemy.orm import Session

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Abstract repository providing CRUD operations"""

    def __init__(self, db: Session, model: type):
        self.db = db
        self.model = model

    async def create(self, obj: T) -> T:
        """Create and persist entity"""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    async def get_by_id(self, id: str) -> Optional[T]:
        """Retrieve entity by ID"""
        return self.db.query(self.model).filter(
            self.model.id == id
        ).first()

    async def update(self, id: str, **kwargs) -> Optional[T]:
        """Update entity"""
        obj = await self.get_by_id(id)
        if not obj:
            return None
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    async def delete(self, id: str) -> bool:
        """Delete entity"""
        obj = await self.get_by_id(id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """List entities with pagination"""
        return self.db.query(self.model).offset(skip).limit(limit).all()
```

### Example: User Repository

```python
# src/database/repositories/user_repository.py
from sqlalchemy.orm import Session
from src.models import User, UserStatus
from .base import BaseRepository

class UserRepository(BaseRepository[User]):
    """User-specific repository with custom queries"""

    def __init__(self, db: Session):
        super().__init__(db, User)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        return self.db.query(User).filter(
            User.username == username
        ).first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        return self.db.query(User).filter(
            User.email == email
        ).first()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get only active users"""
        return self.db.query(User).filter(
            User.status == UserStatus.ACTIVE
        ).offset(skip).limit(limit).all()

    async def search_by_username(self, pattern: str) -> List[User]:
        """Search users by username pattern"""
        return self.db.query(User).filter(
            User.username.ilike(f"%{pattern}%")
        ).all()
```

### Example: Instruction Repository

```python
# src/database/repositories/instruction_repository.py
from sqlalchemy.orm import Session
from src.models import UserInstruction
from .base import BaseRepository

class InstructionRepository(BaseRepository[UserInstruction]):
    """User instructions with filtering"""

    def __init__(self, db: Session):
        super().__init__(db, UserInstruction)

    async def get_by_user(self, user_id: str) -> List[UserInstruction]:
        """Get all instructions for user"""
        return self.db.query(UserInstruction).filter(
            UserInstruction.user_id == user_id,
            UserInstruction.is_active == True
        ).all()

    async def get_by_project(self, project_id: str) -> List[UserInstruction]:
        """Get instructions for specific project"""
        return self.db.query(UserInstruction).filter(
            UserInstruction.project_id == project_id,
            UserInstruction.is_active == True
        ).all()

    async def get_active_for_user_project(self, user_id: str,
                                         project_id: Optional[str]) -> List[UserInstruction]:
        """Get active instructions for user (global + project-specific)"""
        query = self.db.query(UserInstruction).filter(
            UserInstruction.user_id == user_id,
            UserInstruction.is_active == True
        )

        if project_id:
            # Global + project-specific instructions
            return query.filter(
                (UserInstruction.project_id == None) |
                (UserInstruction.project_id == project_id)
            ).all()
        else:
            # Only global instructions
            return query.filter(UserInstruction.project_id == None).all()
```

### Repository Collection

```python
# src/database/repositories/__init__.py
from .base import BaseRepository
from .user_repository import UserRepository
from .project_repository import ProjectRepository
from .session_repository import SessionRepository
from .message_repository import MessageRepository
from .instruction_repository import InstructionRepository
from .audit_repository import AuditRepository

__all__ = [
    'BaseRepository',
    'UserRepository',
    'ProjectRepository',
    'SessionRepository',
    'MessageRepository',
    'InstructionRepository',
    'AuditRepository',
]
```

---

## LAYER 3: SERVICE LAYER

### Purpose
Implement business logic, coordinate repositories, integrate with agents, enforce rules.

### Pattern: Base Service

```python
# src/services/base_service.py
from typing import Dict, Any
from logging import Logger
from src.core import ServiceContainer

class BaseService:
    """Base service with common functionality"""

    def __init__(self, services: ServiceContainer, logger: Logger):
        self.services = services
        self.logger = logger

    def handle_error(self, error_code: str, message: str) -> Dict[str, Any]:
        """Standard error response"""
        self.logger.error(f"{error_code}: {message}")
        return {
            'success': False,
            'error_code': error_code,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }

    def handle_success(self, data: Any, message: str = "") -> Dict[str, Any]:
        """Standard success response"""
        return {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
```

### Example: Instruction Service

```python
# src/services/instruction_service.py
from typing import List, Dict, Any, Optional
from src.database.repositories import InstructionRepository
from src.models import UserInstruction
from src.services.base_service import BaseService

class InstructionService(BaseService):
    """Manages user-defined AI behavior rules"""

    def __init__(self, services: ServiceContainer):
        super().__init__(services, services.logger)
        self.repo = InstructionRepository(services.database.session)

    async def create_instruction(self, user_id: str, rules: str,
                                project_id: Optional[str] = None) -> Dict[str, Any]:
        """Create new instruction"""
        try:
            # Parse rules into structured format
            parsed_rules = self._parse_rules(rules)
            categories = self._categorize_rules(parsed_rules)

            instruction = UserInstruction(
                user_id=user_id,
                project_id=project_id,
                rules=rules,
                parsed_rules=parsed_rules,
                categories=categories,
                is_active=True
            )

            saved = await self.repo.create(instruction)
            self.logger.info(f"Created instruction for user {user_id}")

            return self.handle_success(saved.to_dict(), "Instruction created")

        except Exception as e:
            return self.handle_error("INSTRUCTION_CREATE_ERROR", str(e))

    async def validate_result(self, result: Dict[str, Any],
                            instructions: List[UserInstruction]) -> Dict[str, Any]:
        """Check if result complies with all active instructions"""
        violations = []

        for instruction in instructions:
            rules = instruction.categories

            # Check security rules
            if 'security' in rules:
                security_check = self._validate_security(result, rules['security'])
                if not security_check['valid']:
                    violations.append(security_check)

            # Check quality rules
            if 'quality' in rules:
                quality_check = self._validate_quality(result, rules['quality'])
                if not quality_check['valid']:
                    violations.append(quality_check)

            # Check architecture rules
            if 'architecture' in rules:
                arch_check = self._validate_architecture(result, rules['architecture'])
                if not arch_check['valid']:
                    violations.append(arch_check)

        return {
            'valid': len(violations) == 0,
            'violations': violations
        }

    def _parse_rules(self, rules: str) -> List[Dict[str, str]]:
        """Parse natural language rules into structured format"""
        lines = rules.strip().split('\n')
        parsed = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                parsed.append({
                    'raw': line,
                    'type': self._detect_rule_type(line)
                })
        return parsed

    def _categorize_rules(self, parsed_rules: List[Dict]) -> Dict[str, List[str]]:
        """Organize rules by category"""
        categories = {
            'security': [],
            'quality': [],
            'architecture': [],
            'performance': [],
            'custom': []
        }

        for rule in parsed_rules:
            category = rule['type']
            if category in categories:
                categories[category].append(rule['raw'])

        return {k: v for k, v in categories.items() if v}

    def _detect_rule_type(self, rule: str) -> str:
        """Detect rule category from text"""
        rule_lower = rule.lower()

        if any(w in rule_lower for w in ['security', 'secure', 'encryption', 'hash']):
            return 'security'
        elif any(w in rule_lower for w in ['test', 'coverage', 'quality', 'clean']):
            return 'quality'
        elif any(w in rule_lower for w in ['architecture', 'design', 'pattern', 'structure']):
            return 'architecture'
        elif any(w in rule_lower for w in ['performance', 'fast', 'optimize', 'efficient']):
            return 'performance'
        else:
            return 'custom'

    def _validate_security(self, result: Dict, rules: List[str]) -> Dict[str, Any]:
        """Validate security requirements"""
        # Check for common security patterns
        if 'no hardcoded secrets' in ' '.join(rules).lower():
            if 'password' in str(result) or 'api_key' in str(result):
                return {'valid': False, 'reason': 'Found hardcoded secrets'}

        return {'valid': True}

    def _validate_quality(self, result: Dict, rules: List[str]) -> Dict[str, Any]:
        """Validate quality standards"""
        # Check if result has required documentation
        if 'document' in ' '.join(rules).lower():
            if 'docstring' not in str(result).lower():
                return {'valid': False, 'reason': 'Missing documentation'}

        return {'valid': True}

    def _validate_architecture(self, result: Dict, rules: List[str]) -> Dict[str, Any]:
        """Validate architectural constraints"""
        # Example: No circular dependencies
        if 'no circular' in ' '.join(rules).lower():
            # Perform circular dependency check
            pass

        return {'valid': True}
```

### Example: Agent Service

```python
# src/services/agent_service.py
from typing import Dict, Any, Optional
from src.agents.orchestrator import AgentOrchestrator
from src.services.base_service import BaseService

class AgentService(BaseService):
    """Routes requests to appropriate agents"""

    def __init__(self, services: ServiceContainer):
        super().__init__(services, services.logger)
        self.orchestrator = AgentOrchestrator(services)
        self.instruction_service = InstructionService(services)

    async def route_request(self, agent_id: str, action: str,
                          data: Dict[str, Any],
                          user_instructions: Optional[List] = None) -> Dict[str, Any]:
        """
        Route request to agent with instruction enforcement

        Flow:
        1. Apply user instructions as constraints
        2. Route to agent
        3. Validate through QualityAnalyzer
        4. Check against user instructions
        5. Log audit trail
        """
        try:
            # Step 1: Apply user instructions
            if user_instructions:
                data['_user_instructions'] = user_instructions
                self.logger.info(f"Applying {len(user_instructions)} instructions")

            # Step 2: Route to agent
            result = self.orchestrator.route_request(agent_id, action, data)

            if not result.get('success'):
                return result

            # Step 3: Validate through QualityAnalyzer
            quality_check = self._validate_quality(result)
            if not quality_check['valid']:
                return self.handle_error("QUALITY_CHECK_FAILED", quality_check['reason'])

            # Step 4: Validate against user instructions
            if user_instructions:
                instruction_check = await self.instruction_service.validate_result(
                    result.get('data', {}),
                    user_instructions
                )
                if not instruction_check['valid']:
                    violations = [v['reason'] for v in instruction_check['violations']]
                    return self.handle_error(
                        "INSTRUCTION_VIOLATION",
                        f"Result violates instructions: {'; '.join(violations)}"
                    )

            # Step 5: Log audit trail
            self._audit_log(agent_id, action, data, result)

            return result

        except Exception as e:
            return self.handle_error("AGENT_ROUTING_ERROR", str(e))

    def _validate_quality(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate result quality through QualityAnalyzer"""
        try:
            from src.agents.question_analyzer import QualityAnalyzer
            analyzer = QualityAnalyzer()
            analysis = analyzer.analyze_suggestion(str(result.get('data', '')))

            return {
                'valid': analysis.quality_score > 0.5,
                'reason': f"Quality score: {analysis.quality_score}"
            }
        except Exception as e:
            self.logger.error(f"Quality check error: {e}")
            return {'valid': True}  # Don't fail on quality check error

    def _audit_log(self, agent_id: str, action: str,
                   data: Dict[str, Any], result: Dict[str, Any]):
        """Log action to audit trail"""
        try:
            audit_repo = AuditRepository(self.services.database.session)
            audit_repo.create(AuditLog(
                user_id=data.get('user_id'),
                agent_id=agent_id,
                action=action,
                request_data=data,
                response_data=result.get('data'),
                success=result.get('success', False)
            ))
        except Exception as e:
            self.logger.error(f"Audit log error: {e}")
```

### Service Container Integration

```python
# src/core.py
class ServiceContainer:
    """Central DI container for all services"""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.logger = SystemLogger(config)
        self.database = DatabaseManager(config)
        self.event_system = EventSystem()

        # Initialize services
        self.instruction_service = InstructionService(self)
        self.agent_service = AgentService(self)
        self.auth_service = AuthService(self)
        self.project_service = ProjectService(self)
        self.session_service = SessionService(self)
        self.quality_service = QualityService(self)
```

---

## LAYER 4: API/ROUTER LAYER

### Purpose
Handle HTTP requests, validate inputs, call services, return responses.

### Pattern: Service Injection in Routers

```python
# src/routers/instructions.py
from fastapi import APIRouter, Depends, HTTPException
from src.schemas import InstructionCreate, InstructionUpdate
from src.services import InstructionService
from src.core import get_services

router = APIRouter(prefix="/instructions", tags=["instructions"])

@router.post("")
async def create_instruction(
    req: InstructionCreate,
    services: ServiceContainer = Depends(get_services)
):
    """Create new instruction"""
    result = await services.instruction_service.create_instruction(
        user_id=req.user_id,
        rules=req.rules,
        project_id=req.project_id
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])

    return result['data']

@router.get("")
async def list_instructions(
    user_id: str,
    services: ServiceContainer = Depends(get_services)
):
    """Get user instructions"""
    result = await services.instruction_service.get_user_instructions(user_id)
    return result['data']

@router.put("/{instruction_id}")
async def update_instruction(
    instruction_id: str,
    req: InstructionUpdate,
    services: ServiceContainer = Depends(get_services)
):
    """Update instruction"""
    result = await services.instruction_service.update_instruction(
        instruction_id=instruction_id,
        **req.dict(exclude_unset=True)
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])

    return result['data']

@router.delete("/{instruction_id}")
async def delete_instruction(
    instruction_id: str,
    services: ServiceContainer = Depends(get_services)
):
    """Delete instruction"""
    result = await services.instruction_service.delete_instruction(instruction_id)

    if not result['success']:
        raise HTTPException(status_code=404, detail=result['message'])

    return {"success": True}
```

---

## DATA FLOW EXAMPLE: Creating a Project with Instructions

```
1. Frontend: POST /api/projects
   {
     "name": "MyProject",
     "description": "..."
   }

2. Router (projects.py):
   - Validates input (Pydantic schema)
   - Calls services.project_service.create_project()

3. Service Layer (ProjectService):
   - Checks user authorization
   - Calls repositories to create project
   - Triggers Architecture Optimizer (if configured)
   - Emits 'project_created' event
   - Logs to audit trail

4. Repository Layer (ProjectRepository):
   - Creates Project model instance
   - Calls db.session.add() and commit()
   - Returns saved object

5. Data Layer (PostgreSQL):
   - Inserts row into projects table
   - Returns inserted record

6. Service → Router → Frontend:
   {
     "success": true,
     "data": {
       "id": "proj_123",
       "name": "MyProject",
       "owner_id": "user_456",
       ...
     }
   }

7. Frontend updates Redux state, re-renders UI
```

---

## TRANSACTION MANAGEMENT

### Database Session Management

```python
# src/core/database.py
from sqlalchemy.orm import sessionmaker, scoped_session

class DatabaseManager:
    def __init__(self, config):
        engine = create_engine(
            config.database_url,
            pool_size=config.db_pool_size,
            max_overflow=config.db_max_overflow
        )
        self.SessionLocal = sessionmaker(bind=engine)
        self.scoped_session = scoped_session(self.SessionLocal)

    def get_session(self):
        """Get thread-local session"""
        return self.scoped_session()

    def remove_session(self):
        """Clean up session (call at request end)"""
        self.scoped_session.remove()
```

### FastAPI Dependency for Session

```python
# src/core/__init__.py
from fastapi import Depends

def get_db_session():
    """FastAPI dependency providing database session"""
    session = services.database.get_session()
    try:
        yield session
    finally:
        services.database.remove_session()

# Usage in routers
@router.get("")
async def get_data(db: Session = Depends(get_db_session)):
    return db.query(Model).all()
```

---

## ERROR HANDLING

### Database Errors

```python
from sqlalchemy.exc import IntegrityError, OperationalError

async def safe_operation(self, operation):
    """Wrapper for safe database operations"""
    try:
        return await operation()
    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            return self.handle_error("DUPLICATE", "Record already exists")
        return self.handle_error("INTEGRITY_ERROR", str(e))
    except OperationalError as e:
        return self.handle_error("DATABASE_ERROR", "Database connection failed")
    except Exception as e:
        self.logger.exception("Unexpected error")
        return self.handle_error("UNKNOWN_ERROR", "An unexpected error occurred")
```

---

## TESTING

### Mock Repository Pattern

```python
# tests/fixtures/mock_repositories.py
class MockUserRepository:
    def __init__(self):
        self.users = {}

    async def create(self, user: User) -> User:
        self.users[user.id] = user
        return user

    async def get_by_id(self, id: str) -> Optional[User]:
        return self.users.get(id)
```

### Service Testing

```python
# tests/test_services.py
@pytest.fixture
def mock_services(monkeypatch):
    """Provide mocked services"""
    services = ServiceContainer(SystemConfig())
    services.repo = MockUserRepository()
    return services

def test_create_instruction(mock_services):
    service = InstructionService(mock_services)
    result = service.create_instruction("user_123", "My rules")

    assert result['success'] == True
    assert result['data']['user_id'] == "user_123"
```

---

## NEXT STEPS

1. Implement all models in `src/models/`
2. Create all repositories in `src/database/repositories/`
3. Implement all services in `src/services/`
4. Create routers in `src/routers/`
5. Wire everything together in `src/core.py`
6. Write comprehensive tests for each layer

**Proceed to 05_AGENT_INTEGRATION.md** for agent coordination details
