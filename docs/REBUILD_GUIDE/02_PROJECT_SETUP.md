# PROJECT SETUP & INITIALIZATION
## Complete Environment Configuration

---

## PREREQUISITES

Before starting, ensure you have:

```bash
# System requirements
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Git
- Docker (optional but recommended)

# Python packages
- pip, venv
- pipenv (optional)

# Node packages
- npm or yarn
- create-react-app

# Accounts
- Anthropic API key (for Claude)
- GitHub account
- PostgreSQL local/cloud access
```

---

## STEP 1: CREATE PROJECT STRUCTURE

```bash
# Create main directory
mkdir Socrates-Rebuild
cd Socrates-Rebuild
git init

# Create backend
mkdir backend
cd backend
python -m venv venv

# Activate venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Create backend structure
mkdir src
mkdir src/agents
mkdir src/routers
mkdir src/services
mkdir src/repositories
mkdir src/models
mkdir src/schemas
mkdir src/middleware
mkdir tests
mkdir alembic
mkdir alembic/versions

cd ..

# Create frontend
npx create-react-app frontend --template typescript
cd ..
```

---

## STEP 2: BACKEND SETUP

### 2.1 Install Dependencies

```bash
cd backend

# Ensure venv is activated
# Create requirements.txt

cat > requirements.txt << 'EOF'
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
asyncpg==0.29.0

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# External Services
anthropic==0.7.0
chromadb==0.4.18
gitpython==3.1.40

# Utilities
pydantic-extra-types==2.3.0
email-validator==2.1.0
uvloop==0.19.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1

# Development
black==23.12.0
isort==5.13.2
pylint==3.0.3
mypy==1.7.1
EOF

pip install -r requirements.txt
```

### 2.2 Configure Environment

```bash
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://socrates_user:socrates_pass@localhost:5432/socrates_rebuild
DATABASE_ECHO=True

# JWT
JWT_SECRET=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api
DEBUG=True

# External Services
ANTHROPIC_API_KEY=your-api-key
CHROMADB_PATH=./data/chromadb

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/socrates.log
EOF
```

### 2.3 Initialize PostgreSQL

```bash
# Create database user
psql -U postgres
CREATE USER socrates_user WITH PASSWORD 'socrates_pass';
CREATE DATABASE socrates_rebuild OWNER socrates_user;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE socrates_rebuild TO socrates_user;

# Exit psql
\q

# Test connection
psql -U socrates_user -d socrates_rebuild -c "SELECT version();"
```

### 2.4 Create Main FastAPI App

```bash
cat > src/main.py << 'EOF'
"""Main FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging

from src.core.config import settings
from src.core.database import init_db
from src.routers import auth, projects, sessions, agents, code, instructions
from src.middleware.error_handler import setup_exception_handlers
from src.middleware.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Socrates Rebuild",
    description="AI-powered Socratic questioning system",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Add middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup error handlers
setup_exception_handlers(app)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(code.router, prefix="/api/code", tags=["code"])
app.include_router(instructions.router, prefix="/api/instructions", tags=["instructions"])

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
EOF
```

---

## STEP 3: FRONTEND SETUP

### 3.1 Install Dependencies

```bash
cd frontend

npm install --save \
  @reduxjs/toolkit \
  react-redux \
  axios \
  react-router-dom \
  tailwindcss \
  postcss \
  autoprefixer \
  @types/react-dom \
  @types/react-router-dom

npm install --save-dev \
  typescript \
  @types/node
```

### 3.2 Configure Tailwind CSS

```bash
npx tailwindcss init -p

# Edit tailwind.config.js
cat > tailwind.config.js << 'EOF'
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        secondary: '#1e40af',
      }
    },
  },
  plugins: [],
}
EOF
```

### 3.3 Create .env for Frontend

```bash
cat > .env << 'EOF'
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENVIRONMENT=development
EOF
```

### 3.4 Create Redux Store

```bash
mkdir -p src/redux/slices
mkdir -p src/redux/middleware

# Create store.ts
cat > src/redux/store.ts << 'EOF'
import { configureStore } from '@reduxjs/toolkit';

export const store = configureStore({
  reducer: {
    // Add slices here
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
EOF
```

---

## STEP 4: MIGRATE EXISTING AGENTS

### 4.1 Copy Agent System

```bash
# From current Socrates project
cp -r src/agents/ backend/src/agents/

# Expected structure
backend/src/agents/
├── __init__.py
├── base.py
├── orchestrator.py
├── user.py
├── project.py
├── socratic.py
├── code.py (with new methods)
├── context.py
├── document.py
├── services.py
├── monitor.py
├── code_validator.py (NEW)
├── code_editor.py (NEW)
└── question_analyzer.py
```

### 4.2 Copy Supporting Modules

```bash
# Copy models, services, utils
cp -r src/models/ backend/src/models/
cp -r src/services/ backend/src/services/
cp src/core.py backend/src/core.py
cp src/utils.py backend/src/utils.py
```

### 4.3 Create Agent Adapter

```bash
cat > backend/src/services/agent_service.py << 'EOF'
"""Service to coordinate with agent system"""

from typing import Dict, Any, Optional
from src.agents.orchestrator import AgentOrchestrator
from src.services.instruction_service import InstructionService
from src.agents.code_validator import ValidationResult
import logging

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, orchestrator: AgentOrchestrator,
                 instruction_service: InstructionService):
        self.orchestrator = orchestrator
        self.instruction_service = instruction_service

    async def route_request(
        self,
        agent_id: str,
        action: str,
        data: Dict[str, Any],
        user_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route request to appropriate agent with user instruction validation

        Args:
            agent_id: ID of agent to route to
            action: Action to perform
            data: Request data
            user_instructions: User-defined rules to enforce

        Returns:
            Agent response
        """
        try:
            # Apply user instructions as context
            if user_instructions:
                data['_user_instructions'] = user_instructions
                logger.info(f"Applying user instructions for {agent_id}:{action}")

            # Route to agent
            result = self.orchestrator.route_request(agent_id, action, data)

            # Validate result against user instructions
            if user_instructions:
                compliance = await self.instruction_service.validate_result(
                    result,
                    user_instructions
                )
                if not compliance['valid']:
                    logger.warning(
                        f"Result violated user instruction: {compliance['reason']}"
                    )
                    return {
                        'success': False,
                        'error': f"Result violates your instruction: {compliance['reason']}",
                        'instruction_violation': True
                    }

            return result

        except Exception as e:
            logger.error(f"Agent routing error: {e}")
            return {'success': False, 'error': str(e)}
EOF
```

---

## STEP 5: DATABASE MIGRATIONS

### 5.1 Create Alembic Configuration

```bash
cd backend

# Initialize alembic
alembic init alembic

# Edit alembic/env.py to point to your models
# This is auto-configured by alembic init
```

### 5.2 Create Initial Migration

```bash
# Generate migration from models
alembic revision --autogenerate -m "Initial schema with user instructions"

# Review generated migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

### 5.3 Verify Database

```bash
psql -U socrates_user -d socrates_rebuild

# Check tables created
\dt

# Should see:
# - users
# - projects
# - sessions
# - messages
# - user_instructions (NEW)
# - audit_logs (NEW)
```

---

## STEP 6: RUN BOTH SERVERS

### 6.1 Start Backend

```bash
cd backend

# Ensure venv activated
# source venv/bin/activate (Mac/Linux)
# venv\Scripts\activate (Windows)

python -m src.main

# Should see:
# Uvicorn running on http://0.0.0.0:8000
# API docs available at http://localhost:8000/api/docs
```

### 6.2 Start Frontend (New Terminal)

```bash
cd frontend

npm start

# Should see:
# Compiled successfully!
# Local: http://localhost:3000
```

### 6.3 Verify Health

```bash
# Test backend health
curl http://localhost:8000/api/health

# Should return: {"status": "healthy", "version": "2.0.0"}

# Check API docs
# Visit: http://localhost:8000/api/docs
```

---

## STEP 7: CREATE INITIAL TEST DATA

```bash
# Create backend/scripts/seed_database.py

cat > scripts/seed_database.py << 'EOF'
"""Seed database with initial test data"""

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.user import User
from src.models.project import Project
from src.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

async def seed():
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create test user
    test_user = User(
        username="testuser",
        email="test@example.com",
        password_hash=pwd_context.hash("Test@1234")
    )
    session.add(test_user)
    session.commit()

    # Create test project
    test_project = Project(
        owner_id=test_user.id,
        name="Test Project",
        description="Initial test project"
    )
    session.add(test_project)
    session.commit()

    print("Database seeded successfully!")
    print(f"Test user: testuser / Test@1234")
    print(f"Test project created: {test_project.id}")

if __name__ == "__main__":
    asyncio.run(seed())
EOF

# Run seed script
python scripts/seed_database.py
```

---

## STEP 8: PROJECT STRUCTURE VERIFICATION

```
Socrates-Rebuild/
├── backend/
│   ├── venv/
│   ├── src/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── orchestrator.py
│   │   │   ├── code.py (with editing)
│   │   │   ├── code_validator.py (NEW)
│   │   │   ├── code_editor.py (NEW)
│   │   │   └── ... (other agents)
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── projects.py
│   │   │   ├── sessions.py
│   │   │   ├── agents.py
│   │   │   ├── code.py
│   │   │   ├── instructions.py (NEW)
│   │   │   └── websocket.py
│   │   ├── services/
│   │   │   ├── agent_service.py
│   │   │   ├── instruction_service.py (NEW)
│   │   │   ├── auth_service.py
│   │   │   └── ...
│   │   ├── repositories/
│   │   │   ├── base_repository.py
│   │   │   ├── user_repository.py
│   │   │   ├── instruction_repository.py (NEW)
│   │   │   └── ...
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── instruction.py (NEW)
│   │   │   └── ...
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── instruction.py (NEW)
│   │   │   └── ...
│   │   ├── middleware/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── scripts/
│   ├── requirements.txt
│   ├── .env
│   └── .gitignore
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   │   └── InstructionsPanel/ (NEW)
│   │   ├── redux/
│   │   │   └── slices/
│   │   │       └── instructionSlice.ts (NEW)
│   │   ├── services/
│   │   ├── styles/
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── public/
│   ├── package.json
│   ├── .env
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── .gitignore
│
├── docs/
│   └── REBUILD_GUIDE/
│       ├── 00_INDEX.md
│       ├── 01_ARCHITECTURE.md
│       ├── 02_PROJECT_SETUP.md (this file)
│       ├── 03_BACKEND_LAYERS.md
│       ├── 04_USER_INSTRUCTIONS.md (NEW)
│       ├── 05_AGENT_INTEGRATION.md
│       └── ...
│
└── .gitignore
```

---

## TROUBLESHOOTING

### PostgreSQL Connection Issues
```
Error: could not connect to server
Solution: Ensure PostgreSQL is running
- Windows: Check Services for PostgreSQL
- Mac: brew services start postgresql
- Linux: sudo service postgresql start
```

### Port Already in Use
```
Error: Address already in use
Solution:
- Change port in .env: API_PORT=8001
- Or kill process: lsof -i :8000 | grep LISTEN | kill -9 <PID>
```

### Module Import Errors
```
Error: ModuleNotFoundError
Solution: Ensure PYTHONPATH includes backend/ directory
- export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
```

### Database Migration Issues
```
Error: "No such table"
Solution: Run migrations
- alembic upgrade head
```

---

## NEXT STEPS

1. Verify both servers are running
2. Check API documentation at http://localhost:8000/api/docs
3. Proceed to **03_BACKEND_LAYERS.md** for detailed layer implementation
4. Then move to **04_USER_INSTRUCTIONS.md** to implement instruction system

---

**Setup complete! You're ready to build the backend and frontend layers.**
