audelaude# Socrates AI - Collaborative Development Platform

A complete project management and vibe coding RAG system.
Comprehensive AI-powered platform for collaborative software project development, with real-time collaboration,
multi-agent orchestration, and production-grade infrastructure.

> **Status**: Beta (v0.2.0)
> **License**: MIT
> **Architecture**: FastAPI Backend + React Frontend + PostgreSQL + Redis + ChromaDB
> **Latest**: All code quality checks passing, PyPI published, integrations ready
> **Package**: [socrates-ai on PyPI](https://pypi.org/project/socrates-ai/)
<img width="1887" height="918" alt="SocratesSS" src="https://github.com/user-attachments/assets/63c74ccb-869d-46c1-ace7-f0ed358acdb9" />

## Key Features

🎓 **Socratic Learning**: AI-guided Socratic questioning to help teams think through complex design and development problems

🤖 **Multi-Agent System**: Specialized agents for project management, code generation, conflict resolution, knowledge management, and more

📚 **Knowledge Management**: RAG (Retrieval-Augmented Generation) with vector embeddings for intelligent knowledge retrieval and synthesis

🔄 **Real-Time Collaboration**: WebSocket-powered real-time presence, cursor tracking, and document synchronization

🔐 **Enterprise Security**: JWT authentication with MFA, OWASP-compliant security headers, role-based access control, encryption

⚡ **High-Performance**: Rate limiting, Redis caching, connection pooling, async database queries, optimized query execution

📊 **Production Monitoring**: Prometheus metrics, Grafana dashboards, health checks, detailed logging, performance tracking

☸️ **Kubernetes-Ready**: Complete Kubernetes manifests, Helm charts, Docker multi-platform builds, CI/CD automation

## 🎯 Latest Release (v0.2.0 Beta)

✨ **Package & Integrations**
- ✅ Published to PyPI as unified `socrates-ai` package
- ✅ Integrated with LangChain, LangGraph, and OpenClaw
- ✅ CLI and REST API as internal modules with entry points
- ✅ Docker build optimized with layer caching

🔧 **Code Quality & Performance**
- ✅ All ruff linting checks passing (0 errors)
- ✅ All docstrings formatted per PEP 257
- ✅ Tests passing, Code quality workflow validated
- ✅ Docker build optimized (first build ~10 min, subsequent ~30 sec)

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](docs/QUICK_START_GUIDE.md)** ⚡ - Get running in 5-10 minutes
- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup for all platforms
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Development & Architecture
- **[Architecture Guide](docs/ARCHITECTURE.md)** - Understand the system design
- **[Architecture Case Studies](docs/ARCHITECTURE_CASE_STUDIES.md)** - Deep design rationale and tradeoffs
- **[System Design](docs/SYSTEM_DESIGN.md)** - High-level architecture with components and patterns
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[GitHub Integration](docs/GITHUB_INTEGRATION.md)** - Advanced GitHub features

### Production & Operations
- **[Docker Deployment](docs/DOCKER_DEPLOYMENT.md)** - Docker & Docker Compose setup with Hub integration
- **[Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)** - Production checklist, scaling, high availability, and runbooks
- **[Observability Guide](docs/OBSERVABILITY.md)** - Monitoring, metrics, logging, alerts, and health checks
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Deploy to production

---

## Quick Start

### PyPI Installation (Recommended)

```bash
# Install from PyPI
pip install socrates-ai

# With LangChain integration
pip install socrates-ai[langchain]

# With LangGraph integration
pip install socrates-ai[langgraph]

# With OpenClaw integration
pip install socrates-ai[openclaw]

# All integrations
pip install socrates-ai[all]

# Start API server
socrates-api

# Or use CLI
socrates --help
```

### Docker Compose (Local Development)

```bash
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Create environment (for local development with SQLite)
cp deployment/configurations/.env.example .env

# Or for production with PostgreSQL:
# cp deployment/configurations/.env.production.example .env

# Start services
docker-compose -f deployment/docker/docker-compose.yml up -d

# Access Frontend at http://localhost:3000 (via Nginx)
# Access API at http://localhost:8000
# API Documentation at http://localhost:8000/docs
```

### Docker Hub (Production)

Pre-built images are available on Docker Hub for fast production deployments:

```bash
# Option 1: Use docker-compose with pre-built images
cp deployment/configurations/.env.example .env.docker
# Edit .env.docker with your settings

docker-compose -f docker-compose.hub.yml up -d

# Option 2: Run single container
docker run -e ANTHROPIC_API_KEY=sk-ant-your-key \
           -p 8000:8000 \
           nireus79/socrates-api:latest
```

See [Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md) for detailed Docker Hub usage, pushing images, and GitHub Actions CI/CD setup.

### Kubernetes (Production)

```bash
# Using Helm
helm install socrates ./helm \
  --namespace production \
  --set api.image.tag=latest \
  --set postgresql.auth.password=$(openssl rand -base64 32)

# Or using kubectl with manifests
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/*.yaml
```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login with JWT
- `POST /auth/logout` - Logout and invalidate session
- `POST /auth/refresh` - Refresh access token
- `POST /auth/mfa/setup` - Setup MFA (TOTP)

### Projects
- `POST /projects` - Create project
- `GET /projects` - List user's projects
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project
- `POST /projects/{id}/advance-phase` - Move to next phase
- `POST /projects/{id}/team-members` - Add team member

### Chat & Knowledge
- `POST /projects/{id}/chat/sessions` - Create chat session
- `POST /projects/{id}/chat/sessions/{sid}/message` - Send message
- `GET /projects/{id}/knowledge` - List knowledge entries
- `POST /projects/{id}/knowledge` - Add knowledge entry
- `GET /projects/{id}/knowledge/search` - Search knowledge

### Analytics & Reports
- `GET /projects/{id}/analytics` - Project analytics
- `GET /projects/{id}/analytics/detail` - Detailed metrics
- `GET /projects/{id}/chat/sessions/{sid}/export` - Export chat

See [API_REFERENCE.md](docs/API_REFERENCE.md) for complete endpoint documentation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Socrates Platform                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (React)          API Server (FastAPI)              │
│  ┌──────────────┐          ┌──────────────────┐              │
│  │ React UI     │◄─────────┤ REST Endpoints   │              │
│  │ WebSocket    │          │ Rate Limiting    │              │
│  │ Real-time    │          │ Security Headers │              │
│  └──────────────┘          │ JWT Auth + MFA   │              │
│                            │ CORS Hardened    │              │
│                            └──────────────────┘              │
│                                      │                       │
│                ┌─────────────────────┼──────────────────┐   │
│                │                     │                  │   │
│        ┌───────▼──────┐     ┌────────▼────────┐  ┌─────▼──┐ │
│        │  PostgreSQL  │     │  Redis Cache    │  │ChromaDB│ │
│        │  - Projects  │     │  - Sessions     │  │ - RAG  │ │
│        │  - Users     │     │  - Rate Limits  │  │Vectors │ │
│        │  - Knowledge │     │  - Embeddings   │  └────────┘ │
│        └──────────────┘     └─────────────────┘             │
│                                                               │
│        ┌──────────────────────────────────────┐             │
│        │        Multi-Agent Orchestrator      │             │
│        ├──────────────────────────────────────┤             │
│        │ - ProjectManager                     │             │
│        │ - CodeGenerator                      │             │
│        │ - SocraticCounselor                  │             │
│        │ - ContextAnalyzer                    │             │
│        │ - ConflictDetector                   │             │
│        │ - KnowledgeManager                   │             │
│        └──────────────────────────────────────┘             │
│                          │                                   │
│                  ┌───────▼────────┐                         │
│                  │  Claude AI API  │                         │
│                  └────────────────┘                         │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│              Kubernetes Orchestration Layer                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Pod Scaling  │  │ Load Balancing│  │ Health Checks│      │
│  │ Auto-Healing │  │ Service Mesh  │  │ Self-Healing│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│              Monitoring & Observability                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Prometheus   │  │ Grafana       │  │ AlertManager │      │
│  │ Metrics      │  │ Dashboards    │  │ Notifications│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Documentation

- [📖 QUICK_START_GUIDE.md](docs/QUICK_START_GUIDE.md) - Get started quickly
- [🏗️ ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture deep-dive
- [📚 API_REFERENCE.md](docs/API_REFERENCE.md) - Complete API documentation
- [🚀 DEPLOYMENT.md](docs/DEPLOYMENT.md) - Production deployment & Docker guide
- [⚙️ CONFIGURATION.md](docs/CONFIGURATION.md) - Environment configuration
- [👨‍💻 DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) - Development setup & patterns
- [🔄 CI_CD.md](docs/CI_CD.md) - GitHub Actions workflows & testing
- [🐛 TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Problem solving guide
- [📋 INSTALLATION.md](docs/INSTALLATION.md) - Setup and installation instructions

## Production Features

✅ **Security**
- JWT authentication with TOTP MFA
- OWASP Top 10 protection
- Rate limiting (5/min free, 100/min pro)
- Input validation & sanitization
- Encrypted database fields
- TLS/HTTPS support
- Request signing and verification

✅ **Performance**
- Connection pooling (20 connections)
- Redis caching with in-memory fallback
- Query optimization & indexing
- Async database operations
- Request compression
- Multi-stage Docker builds for fast deployments

✅ **Reliability**
- Database transactions & rollback
- Automated backups with S3 support
- Health monitoring & self-healing
- Graceful degradation
- Error tracking & logging
- High-availability database setup (read replicas, failover)
- Circuit breaker pattern for external services

✅ **Operations**
- Kubernetes manifests & Helm charts
- Docker pre-built images on Docker Hub
- Docker multi-platform builds
- CI/CD GitHub Actions workflows
- Prometheus metrics & Grafana dashboards
- Structured JSON logging
- Distributed tracing support (OpenTelemetry)
- Complete runbooks for common operations

## Production-Ready Deployment

Socrates is built for production from day one. To deploy to production:

1. **Review the [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)** - Complete checklist covering:
   - Security hardening (encryption keys, TLS, authentication)
   - Database setup (PostgreSQL with replication, backups)
   - Cache configuration (Redis, connection pooling)
   - Resource management (limits, concurrency settings)
   - Monitoring & alerting setup

2. **Follow the [Observability Guide](docs/OBSERVABILITY.md)** for:
   - Structured logging with JSON format
   - Prometheus metrics collection
   - Health checks and readiness probes
   - Distributed tracing with OpenTelemetry
   - Alerting rules and dashboards

3. **Use the [Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md)** for:
   - Pre-built Docker Hub images
   - Multi-stage builds and optimization
   - GitHub Actions CI/CD automation
   - Scaling beyond Docker Compose

### Quick Production Checklist

- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable Redis for distributed caching
- [ ] Generate strong encryption keys
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure HTTPS/TLS with valid certificates
- [ ] Set up database backups (daily minimum)
- [ ] Enable health checks
- [ ] Configure Prometheus metrics
- [ ] Set up log aggregation
- [ ] Configure alerting
- [ ] Load balance across multiple API instances
- [ ] Monitor key metrics (error rate, response time, resource usage)

See [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md) for the full 20-item checklist and detailed instructions.

## Deployment Options

### Local Development (Docker Compose)

Includes PostgreSQL, Redis, ChromaDB, and Nginx:

```bash
cd deployment/docker
docker-compose up -d

# Wait for services to be ready (30-60 seconds)
# Frontend: http://localhost:3000 (via Nginx proxy)
# API: http://localhost:8000
# PostgreSQL: localhost:5432 (user: socrates / pass: socrates_dev_password)
```

### Production Deployment

**Docker Compose with pre-built images**:
```bash
# Use pre-built images from Docker Hub
docker-compose -f docker-compose.hub.yml up -d
```

**Kubernetes** (recommended for high availability):
```bash
# Using Helm
helm install socrates ./helm \
  --namespace production \
  --values production-values.yaml
```

See [Docker Deployment](docs/DOCKER_DEPLOYMENT.md) and [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md) for complete setup instructions.

## Development

### Prerequisites

Before setting up locally, ensure you have:

- **Python**: 3.11+ (recommended) or 3.8+ (minimum)
  - Check: `python --version` or `python3 --version`
  - Download from: https://www.python.org/downloads/

- **Node.js & npm**: 14+ (LTS version recommended)
  - Check: `node --version` and `npm --version`
  - Download from: https://nodejs.org/

- **Anthropic API Key** (required for AI features)
  - Get from: https://console.anthropic.com/api/keys
  - Keep it safe - you'll add it to .env

- **System Requirements**:
  - RAM: 4GB minimum (8GB recommended)
  - Disk: 2GB for dependencies and data
  - Internet: Required for Claude API access

### Setup Development Environment (Local - SQLite)

```bash
# Clone and setup
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Create environment (uses SQLite by default)
cp deployment/configurations/.env.example .env

# Edit .env and add your Anthropic API key (required!)
# Open .env and set: ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
nano .env  # or use your preferred editor

# Create virtual environment (Python)
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows (Command Prompt):
.venv\Scripts\activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd socrates-frontend
npm install
cd ..

# Run development servers
# On Linux/macOS:
bash scripts/start-dev.sh

# On Windows:
scripts\start-dev.bat

# Success! You should see:
# Frontend: http://localhost:5173 (Vite dev server)
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### What's Next After Startup?

1. **Open Frontend**: Visit http://localhost:5173 in your browser
2. **Create Account**: Click "Sign Up" and create your first user account
3. **Add API Key**:
   - Go to Settings > LLM > Anthropic
   - Paste your API key and save
4. **Create a Project**: Click "New Project" and fill in project details
5. **Explore Features**: Try Socratic Questioning, Code Generation, etc.

### Troubleshooting Local Setup

**Port already in use?**
```bash
# Find process using port
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Or modify .env to use different port
# SOCRATES_API_PORT=9000
```

**Module not found errors?**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**API key errors?**
```bash
# Verify API key is set in .env
cat .env | grep ANTHROPIC_API_KEY  # Linux/macOS
type .env | findstr ANTHROPIC_API_KEY  # Windows

# Also verify in UI: Settings > LLM > Anthropic
```

### Run Tests

```bash
# All tests with coverage
pytest tests/ --cov=socratic_system

# Specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# With coverage report
pytest --cov=socratic_system --cov-report=html
```

### Code Quality

```bash
# Format code
black socratic_system/ socrates-api/src/ socrates-cli/src/

# Import sorting
isort socratic_system/ socrates-api/src/ socrates-cli/src/

# Lint with ruff
ruff check socratic_system/ socrates-api/src/ socrates-cli/src/

# Type checking with mypy
mypy socratic_system/ --ignore-missing-imports

# Security scanning with bandit
bandit -r socratic_system/ socrates-api/src/ socrates-cli/src/
```

## ☕ Support Socrates Development

Socrates is free and open-source. If you find it useful, consider supporting development through GitHub Sponsors:

### 🎁 GitHub Sponsors - Premium Tiers

Become a sponsor to unlock premium features and support active development. **Your sponsorship is automatically applied to your Socrates account!**

| Tier | Price | Features | Link |
|------|-------|----------|------|
| **Supporter** | $5/month | 10 projects, 5 team members, 100GB storage | [Sponsor Now](https://github.com/sponsors/Nireus79) |
| **Contributor** | $15/month | Unlimited projects, unlimited members, unlimited storage | [Sponsor Now](https://github.com/sponsors/Nireus79) |
| **Custom** | $25+/month | All Enterprise + priority support | [Sponsor Now](https://github.com/sponsors/Nireus79) |

**How It Works:**
1. Sponsor on [GitHub Sponsors](https://github.com/sponsors/Nireus79)
2. Your Socrates account is **automatically upgraded** (usually within seconds)
3. Start using premium features immediately
4. View payment history and tier details in Socrates Settings

👉 **[Full Sponsorship Guide](SPONSORSHIP.md)** - Learn how to manage your sponsorship and access premium features in Socrates.

### Other Ways to Support
- **Star the repository** ⭐
- **Fork and contribute** code improvements
- **Share feedback** and feature requests
- **Report bugs** to help us improve
- **Write documentation** for new features
- **Spread the word** about Socrates

---

## Contributing



1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit pull request

## Support

- **Bugs & Issues**: [GitHub Issues](https://github.com/Nireus79/Socrates/issues)
- **Documentation**: [Docs Directory](./docs)
- **Sponsorship**: [Sponsorship Guide](SPONSORSHIP.md)
- **GitHub Sponsors**: [Become a Sponsor](https://github.com/sponsors/Nireus79)
- **Email**: support@socrates-ai.dev

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

Built with:
- [Claude AI](https://anthropic.com) by Anthropic
- [FastAPI](https://fastapi.tiangolo.com/) for REST API
- [PostgreSQL](https://www.postgresql.org/) for data persistence
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [Redis](https://redis.io/) for caching
- [Kubernetes](https://kubernetes.io/) for orchestration

---

**Made with ❤️ for teams who believe in collaborative development**
